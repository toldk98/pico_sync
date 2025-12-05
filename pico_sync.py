import os
import base64
import subprocess
import hashlib
import re
import argparse
import tempfile
import json
import urllib.request
import serial
import serial.tools.list_ports as list_ports
import time

# info for pico
PICO_USB_VID = 0x2E8A  # Raspberry Pi (RP2040)
PICO_KEYWORDS = ("Pico", "RP2", "MicroPython", "USB Serial Device")

# info for Pico Sync Tools
PICO_SYNC_VERSION = "1.0"
VERSION_CHECK_URL = (
    "https://raw.githubusercontent.com/toldk98/pico_sync/main/meta/latest_version.json"
)
# info for Serial
BAUD = 115200


def check_for_updates():
    try:
        with urllib.request.urlopen(VERSION_CHECK_URL, timeout=2) as r:
            data = json.loads(r.read().decode())
            latest = data.get("version")
            changelog = data.get("changelog", "")
            url = data.get(
                "url", "https://github.com/toldk98/pico_sync/releases/latest"
            )

            if not latest:
                return  # некоректний JSON

            if latest != PICO_SYNC_VERSION:
                print(f"{C.YELLOW}⚠ Update available:{C.RESET}")
                print(f"  Latest version : {latest}")
                print(f"  Current version: {PICO_SYNC_VERSION}\n")

                if changelog:
                    print(f"{C.BLUE}Changelog:{C.RESET} {changelog}")

                print(f"\n🔗 Download: {url}\n")
            else:
                print(
                    f"{C.GREEN}✔ You already have the latest version ({PICO_SYNC_VERSION}){C.RESET}"
                )
    except Exception as e:
        pass  # fail silently


# -----------------------------
# COLORS
# -----------------------------
class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def is_pico_port(port):
    """Перевірка, чи схожий порт на Raspberry Pi Pico."""
    if port.vid == PICO_USB_VID:
        return True

    desc = (port.description or "") + " " + (port.product or "")
    return any(key in desc for key in PICO_KEYWORDS)


def find_pico_ports():
    return [p for p in list_ports.comports() if is_pico_port(p)]


def find_pico_port_auto():
    for p in list_ports.comports():
        if is_pico_port(p):
            return p.device
    return None


def serial_monitor(port=None, baud=BAUD):
    if port is None:
        port = find_pico_port_auto()

    if not port:
        print("❌ Не знайдено Pico у системі.")
        return

    print(f"🔌  Opening port: {port} @ {baud} baud")
    print("📡  Waiting for data... (Ctrl+C to exit)\n")

    while True:
        try:
            with serial.Serial(port, baud, timeout=0.5) as ser:
                while True:
                    try:
                        line = ser.readline()
                        if line:
                            try:
                                text = line.decode("utf-8", errors="replace").rstrip()
                            except Exception:
                                text = str(line)

                            print(f"\033[92m{text}\033[0m")  # Зеленим
                        else:
                            time.sleep(0.05)

                    except (serial.SerialException, OSError):
                        print("⚠️  Device disconnected, reconnecting...")
                        break

        except serial.SerialException:
            print("⏳  Pico not ready — retrying in 1 sec...")
            time.sleep(1)

        # Пошук нового порта (наприклад, після reset)
        new_port = find_pico_port_auto()
        if new_port and new_port != port:
            print(f"🔄  Switching to new port: {new_port}")
            port = new_port


def print_ports_with_numbers(ports, pico_devs):
    print("\nДоступні серійні порти:\n")
    for i, p in enumerate(ports):
        mark = "⭐" if p.device in pico_devs else " "
        print(f" {i}) {mark}  {p.device:15}  {p.description}")

    print("")


# -----------------------------
# LOAD IGNORE
# -----------------------------
def compile_ignore_patterns(patterns):
    """Convert gitignore-like patterns to regular expressions."""
    regex_list = []

    for pat in patterns:
        pat = pat.replace("\\", "/")

        # Директорія: "dir/" → має збігатися з "dir" або "dir/...”
        directory_only = pat.endswith("/")

        # Escape except our wildcards
        pat_escaped = re.escape(pat)

        # Process double star
        pat_escaped = pat_escaped.replace(r"\*\*", "####DOUBLESTAR####")

        # Convert wildcard *
        pat_escaped = pat_escaped.replace(r"\*", "[^/]*")

        # Convert wildcard ?
        pat_escaped = pat_escaped.replace(r"\?", ".")

        # Convert ** after all other processing
        pat_escaped = pat_escaped.replace("####DOUBLESTAR####", ".*")

        # Directory rule: "dir/" → matches "dir" or "dir/...”
        if directory_only:
            regex = r"^" + pat_escaped[:-2] + r"(/.*)?$"
        else:
            regex = r"^" + pat_escaped + r"$"

        regex_list.append(re.compile(regex))

    return regex_list


def load_ignore_list(root):
    """Read .picoignore and convert patterns."""
    ignore_file = os.path.join(root, ".picoignore")
    patterns = []

    if os.path.exists(ignore_file):
        with open(ignore_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)

    return patterns


def should_ignore(path, compiled_patterns, src_root):
    """
    Check using compiled regex patterns.
    rel = шлях всередині src/
    basename = тільки ім'я файлу
    """
    rel = os.path.relpath(path, src_root).replace("\\", "/")
    basename = os.path.basename(rel)

    for regex in compiled_patterns:
        if regex.match(rel) or regex.match(basename):
            return True

    return False


# -----------------------------
# SHA FUNCTIONS
# -----------------------------
def local_sha256(data: bytes):
    return hashlib.sha256(data).hexdigest()


def pico_file_sha256(path):
    """Return SHA256 hex digest of a file on Pico, or None if file missing."""
    code = (
        "import ubinascii, uhashlib\n"
        "def _sha256(p):\n"
        "    try:\n"
        "        h = uhashlib.sha256()\n"
        "        with open(p, 'rb') as f:\n"
        "            while True:\n"
        "                b = f.read(2048)\n"
        "                if not b: break\n"
        "                h.update(b)\n"
        "        print(ubinascii.hexlify(h.digest()).decode())\n"
        "    except OSError:\n"
        "        print('NONE')\n"
        f"_sha256('{path}')"
    )

    out = subprocess.check_output(["mpremote", "exec", code]).decode().strip()
    return None if out == "NONE" else out


# -----------------------------
# CREATE DIRS + UPLOAD
# -----------------------------
def mp_write_file(remote_path, data: bytes):
    # Auto-create directories
    dir_path = os.path.dirname(remote_path).replace("\\", "/")
    if dir_path and dir_path != "/":
        mkdir_cmd = (
            "import os\n"
            f"p='{dir_path}'\n"
            "parts=p.strip('/').split('/')\n"
            "cur=''\n"
            "for part in parts:\n"
            "    cur += '/' + part\n"
            "    try: os.mkdir(cur)\n"
            "    except OSError: pass\n"
        )
        subprocess.run(["mpremote", "exec", mkdir_cmd], check=True)

    # Write file
    b64 = base64.b64encode(data).decode("ascii")
    cmd = (
        "import ubinascii;"
        f"open('{remote_path}','wb').write("
        f"ubinascii.a2b_base64(b'{b64}'))"
    )
    subprocess.run(["mpremote", "exec", cmd], check=True)


# -----------------------------
# LIST FILES ON PICO
# -----------------------------
def pico_list_files():
    """Return list of all files on Pico with their full paths."""
    code = (
        "import os\n"
        "res=[]\n"
        "def walk(p):\n"
        "    for f in os.listdir(p):\n"
        "        fp=p+'/'+f if p!='/' else '/'+f\n"
        "        try:\n"
        "            st=os.stat(fp)[0]\n"
        "            if st & 0x4000: walk(fp)\n"
        "            else: res.append(fp)\n"
        "        except: pass\n"
        "walk('/')\n"
        "print('\\n'.join(res))"
    )
    out = subprocess.check_output(["mpremote", "exec", code]).decode().splitlines()
    return sorted(out)


def sync_tree(src_root):
    project_root = os.getcwd()
    raw_patterns = load_ignore_list(project_root)
    compiled_patterns = compile_ignore_patterns(raw_patterns)
    print("Ignore patterns:", raw_patterns)

    local_files = []
    pico_files_before = pico_list_files()

    # -----------------------------------
    # UPLOAD / SKIP
    # -----------------------------------
    for root, dirs, files in os.walk(src_root):
        dirs[:] = [
            d
            for d in dirs
            if not should_ignore(os.path.join(root, d), compiled_patterns, src_root)
        ]

        for fname in files:
            local = os.path.join(root, fname)

            if should_ignore(local, compiled_patterns, src_root):
                print(f"[SKIP] {local}")
                continue

            rpath = root.replace(src_root, "").strip("/")
            rdir = f"/{rpath}" if rpath else "/"
            remote = os.path.join(rdir, fname).replace("\\", "/")

            local_files.append(remote)
            with open(local, "rb") as f:
                data = f.read()

            # -------------------------------
            # DELTA CHECK (SHA-256 Compare)
            # -------------------------------
            local_hash = local_sha256(data)
            remote_hash = pico_file_sha256(remote)

            if remote_hash == local_hash:
                print(f"{C.YELLOW}[SKIP same]{C.RESET} {local}")
                continue

            if remote_hash is None:
                print(f"{C.GREEN}[UPLOAD new]{C.RESET} {local} → {remote}")
            else:
                print(f"{C.GREEN}[UPLOAD diff]{C.RESET} {local} → {remote}")

            mp_write_file(remote, data)

    # -----------------------------------
    # DELETE FILES THAT DO NOT EXIST LOCALLY
    # -----------------------------------
    for remote_file in pico_files_before:
        if remote_file not in local_files:
            if remote_file.endswith(".py") or remote_file.endswith(".txt") or True:
                print(f"{C.RED}[DELETE]{C.RESET} {remote_file}")
                subprocess.run(
                    ["mpremote", "exec", f"import os; os.remove('{remote_file}')"]
                )

    print("=== Sync complete ===")


# -----------------------------------------
# CLI COMMANDS
# -----------------------------------------
def pico_ls(path):
    code = (
        "import os\n"
        f"p='{path}'\n"
        "files=[]\n"
        "try:n=os.listdir(p)\n"
        "except:n=[]\n"
        "for a in n:\n"
        " fp=p+'/'+a if p!='/' else '/'+a\n"
        " try: m=os.stat(fp)[0]; d=bool(m&0x4000); files.append(('d ' if d else '- ')+a)\n"
        " except: pass\n"
        "print('\\n'.join(files))\n"
    )

    print(subprocess.check_output(["mpremote", "exec", code]).decode())


def pico_cat(path):
    code = "import sys\n" f"f=open('{path}','r')\n" "sys.stdout.write(f.read())\n"
    out = subprocess.check_output(["mpremote", "exec", code])
    print(out.decode())


def pico_nano(path):
    """
    1. Download file to temp
    2. Open nano
    3. Upload back
    """
    # 1. Download content
    code = (
        "import sys\n"
        f"try:\n"
        f"    f=open('{path}','r')\n"
        f"    sys.stdout.write(f.read())\n"
        "except:\n"
        "    pass\n"
    )
    original = subprocess.check_output(["mpremote", "exec", code]).decode()

    # 2. Create temporary file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    tmp_path = tmp.name
    tmp.write(original.encode())
    tmp.close()

    # 3. Run nano
    subprocess.run(["nano", tmp_path])

    # 4. Upload back
    with open(tmp_path, "rb") as f:
        data = f.read()

    print(f"{C.GREEN}[UPLOAD from nano]{C.RESET} {path}")
    mp_write_file(path, data)

    os.remove(tmp_path)


def delete_empty_dirs():
    """
    Recursively remove empty directories on Pico.
    """
    code = (
        "import os\n"
        "def clean(p):\n"
        "    removed=False\n"
        "    for f in os.listdir(p):\n"
        "        fp = p+'/'+f if p!='/' else '/' + f\n"
        "        try:\n"
        "            st=os.stat(fp)[0]\n"
        "            if st & 0x4000:  # dir\n"
        "                if clean(fp): removed=True\n"
        "        except: pass\n"
        "    # if empty\n"
        "    try:\n"
        "        if len(os.listdir(p))==0 and p!='/':\n"
        "            os.rmdir(p)\n"
        "            print('RMDIR ' + p)\n"
        "            return True\n"
        "    except: pass\n"
        "    return False\n"
        "clean('/')\n"
    )

    out = subprocess.check_output(["mpremote", "exec", code]).decode()
    if out.strip():
        print(out)


def interactive_select_port():
    ports = list_ports.comports()
    pico_ports = find_pico_ports()
    pico_devs = {p.device for p in pico_ports}

    if not ports:
        print("⚠️ Серійних портів не знайдено.")
        return None

    print_ports_with_numbers(ports, pico_devs)

    while True:
        inp = input("Оберіть номер порту (або Enter для скасування): ").strip()
        if inp == "":
            return None
        if not inp.isdigit():
            print("❌ Введіть номер.")
            continue

        idx = int(inp)
        if 0 <= idx < len(ports):
            return ports[idx].device

        print("❌ Невірний номер. Спробуйте ще раз.")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Pico Sync Tool — sync/ls/cat/nano for Raspberry Pi Pico",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--port", default="/dev/ttyACM0", help="Pico COM port")
    parser.add_argument("--src", default="src", help="Source directory to sync")

    # Основні команди
    parser.add_argument("--sync", action="store_true", help="Synchronize src → Pico")
    parser.add_argument("--ls", metavar="PATH", help="List directory on Pico")
    parser.add_argument("--cat", metavar="FILE", help="Output file content from Pico")
    parser.add_argument("--nano", metavar="FILE", help="Edit file on Pico using nano")
    parser.add_argument(
        "--search_port",
        action="store_true",
        help="Interactively search serial ports and choose Pico port",
    )
    parser.add_argument(
        "--check_update",
        action="store_true",
        help="Check for newer version of Pico Sync Tool",
    )
    parser.add_argument(
        "--reboot",
        action="store_true",
        help="Reboot Pico (software reset)",
    )
    parser.add_argument(
        "--monitor", action="store_true", help="Live serial log monitor for Pico"
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Якщо нема команд
    # (sys.argv містить сам файл, тому args без дій → допомога)
    no_actions = not (
            args.reboot
            or args.sync
            or args.ls
            or args.cat
            or args.nano
            or args.search_port
            or args.check_update
            or args.monitor
    )

    if no_actions:
        parser.print_help()
        exit(0)

    if args.reboot:
        print(f"{C.BLUE}Rebooting Pico...{C.RESET}")
        subprocess.run(["mpremote", "reset"])
        exit(0)

    # Update checker
    if args.check_update:
        check_for_updates()
        exit(0)

    # Пошук порту
    if args.search_port:
        chosen = interactive_select_port()
        if not chosen:
            print("Скасовано.")
            exit(0)

        print(f"\n{C.GREEN}Вибрано порт: {chosen}{C.RESET}\n")

        # оновлюємо порт
        args.port = chosen

    # Встановлюємо порт для mpremote
    os.environ["MPREMOTE_PORT"] = args.port

    # ------------ COMMANDS -----------------
    if args.ls:
        pico_ls(args.ls)
        exit()

    if args.cat:
        pico_cat(args.cat)
        exit()

    if args.nano:
        pico_nano(args.nano)
        exit()

    if args.sync:
        sync_tree(os.path.join(os.getcwd(), args.src))
        delete_empty_dirs()
        exit()

    if args.monitor:
        serial_monitor(args.port)
        exit()

    # Якщо щось дивне — показати help
    parser.print_help()


if __name__ == "__main__":
    main()
