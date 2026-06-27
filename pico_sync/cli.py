import os
import sys
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

from . import projects

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

DEFAULT_PICOIGNORE = """\
# Pico Sync — default ignore patterns
__pycache__/
*.pyc
.git/
.DS_Store
Thumbs.db
dist/
*.egg-info/
build/
.idea/
*.swp
*.swo
"""


def init_project(src_root):
    root = _project_root(src_root)
    picoignore = os.path.join(root, ".picoignore")
    if not os.path.exists(picoignore):
        with open(picoignore, "w") as f:
            f.write(DEFAULT_PICOIGNORE)
        print(f"{C.GREEN}.picoignore створено{C.RESET}")
    else:
        print(f"{C.YELLOW}.picoignore вже існує{C.RESET}")

    meta_dir = os.path.join(root, "meta")
    if not os.path.exists(meta_dir):
        os.makedirs(meta_dir)
        print(f"{C.GREEN}meta/ створено{C.RESET}")

    config_path = os.path.join(root, CONFIG_FILE)
    if not os.path.exists(config_path):
        save_config(root, DEFAULT_CONFIG)
        print(f"{C.GREEN}{CONFIG_FILE} створено{C.RESET}")
    else:
        print(f"{C.YELLOW}{CONFIG_FILE} вже існує{C.RESET}")


CONFIG_FILE = ".picosyncconfig"
DEFAULT_CONFIG = {
    "port": "/dev/ttyACM0",
    "filter": "all",
}


def load_config(project_root):
    path = os.path.join(project_root, CONFIG_FILE)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}


def save_config(project_root, data):
    path = os.path.join(project_root, CONFIG_FILE)
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                existing = json.load(f)
            if not isinstance(existing, dict):
                existing = {}
        except:
            existing = {}
    existing.update(data)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
        f.write("\n")


def _project_root(src_root):
    return os.path.dirname(os.path.abspath(src_root))


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

        # Директорія: "dir/" → має збігатися з "dir" або "dir/..."
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

        # Directory rule: "dir/" → matches "dir" or "dir/..."
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
        f"_sha256({repr(path)})"
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
            f"p={repr(dir_path)}\n"
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
        f"open({repr(remote_path)},'wb').write("
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


def sync_tree(src_root, filter="all"):
    project_root = _project_root(src_root)
    raw_patterns = load_ignore_list(project_root)
    compiled_patterns = compile_ignore_patterns(raw_patterns)
    print(f"Ignore patterns: {raw_patterns}")
    print(f"Delete filter: {filter}")

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
            if _match_filter(filter, remote_file):
                print(f"{C.RED}[DELETE]{C.RESET} {remote_file}")
                subprocess.run(
                    ["mpremote", "exec", f"import os; os.remove({repr(remote_file)})"]
                )

    print("=== Sync complete ===")


# -----------------------------------------
# CLI COMMANDS
# -----------------------------------------
def pico_ls(path):
    code = (
        "import os\n"
        f"p={repr(path)}\n"
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
    code = "import sys\n" f"f=open({repr(path)},'r')\n" "sys.stdout.write(f.read())\n"
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
        f"    f=open({repr(path)},'r')\n"
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


# -----------------------------
# PICK MODE
# -----------------------------
def _pick_item(items, prompt="> ", header=None, preview=None):
    """Try fzf with optional header and preview, fall back to numbered input."""
    import shutil
    fzf = shutil.which("fzf")
    if fzf:
        try:
            fzf_args = [fzf, "--border", "--prompt", prompt]
            if header:
                fzf_args += ["--header", header]
            if preview:
                fzf_args += ["--preview", preview, "--preview-window", "right:50%:border"]
            r = subprocess.run(
                fzf_args,
                input="\n".join(items),
                capture_output=True, text=True
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except:
            pass

    print()
    if header:
        print(f"  {header}")
    for i, item in enumerate(items):
        print(f"  {i}) {item}")
    print()
    while True:
        inp = input(prompt).strip()
        if inp == "":
            return None
        if not inp.isdigit():
            continue
        idx = int(inp)
        if 0 <= idx < len(items):
            return items[idx]


def _match_filter(filter_, remote_path):
    if filter_ == "all":
        return True
    if filter_ == "py":
        return remote_path.endswith(".py")
    if filter_ == "py+":
        return remote_path.endswith((".py", ".txt", ".json"))
    if filter_ == "nopy":
        return not remote_path.endswith(".py")
    exts = [e.strip() for e in filter_.split(",")]
    return any(
        remote_path.endswith(e) if e.startswith(".") else remote_path.endswith("." + e)
        for e in exts
    )


def _build_tree(file_paths):
    tree = {}
    for fp in file_paths:
        fp = fp.strip("/")
        if not fp:
            continue
        parts = fp.split("/")
        current = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = True
            else:
                dir_key = part + "/"
                if dir_key not in current:
                    current[dir_key] = {}
                current = current[dir_key]
    return tree


def _pick_ls_browser():
    all_files = pico_list_files()
    if not all_files:
        print("⚠️ Pico empty or not accessible.")
        return

    root = _build_tree(all_files)

    def _browse(node, display_path):
        while True:
            dirs = sorted(k for k in node if k.endswith("/"))
            files = sorted(k for k in node if not k.endswith("/"))

            choices = [".."]
            choices += [f"d {d}" for d in dirs]
            choices += [f"- {f}" for f in files]

            selected = _pick_item(choices, prompt=f"ls {display_path}> ")
            if selected is None:
                return

            if selected == "..":
                return

            if selected.startswith("d "):
                dir_name = selected[2:]
                sub_path = display_path.rstrip("/") + "/" + dir_name.rstrip("/")
                _browse(node[dir_name], sub_path)
                continue

            if selected.startswith("- "):
                name = selected[2:]
                file_path = (display_path.rstrip("/") + "/" + name).replace("//", "/")
                pico_cat(file_path)
                input("\nPress Enter to continue...")

    _browse(root, "/")


def _ensure_port(port):
    if port is not None:
        return port
    port = find_pico_port_auto()
    if port:
        os.environ["MPREMOTE_PORT"] = port
    return port


def _pick_files_menu():
    while True:
        action = _pick_item(
            ["..", "ls", "cat", "nano"],
            prompt="files> ",
            header=" Esc=back  /=search",
            preview="case {} in '..') echo 'Повернутись до головного меню';; 'ls') echo 'Переглянути вміст директорії на Pico';; 'cat') echo 'Вивести вміст файлу на Pico';; 'nano') echo 'Редагувати файл на Pico в nano';; esac"
        )
        if action is None or action == "..":
            return

        if action == "ls":
            _pick_ls_browser()
        elif action == "cat":
            path = input("File path: ").strip()
            if path:
                pico_cat(path)
                input("\nPress Enter to continue...")
        elif action == "nano":
            path = input("File path: ").strip()
            if path:
                pico_nano(path)


def _pick_device_menu(port, src_root):
    port = _ensure_port(port)
    if not port:
        print("❌ Не знайдено Pico. Спочатку обери порт у [config].")
        return port

    project_root = _project_root(src_root)
    config = load_config(project_root)
    current_filter = config.get("filter", "all")

    while True:
        action = _pick_item(
            ["..", "sync", "monitor", "reboot"],
            prompt="device> ",
            header=" Esc=back  /=search",
            preview="case {} in '..') echo 'Повернутись до головного меню';; 'sync') echo 'Синхронізувати файли з Pico (із вибором фільтра)';; 'monitor') echo 'Відкрити серійний монітор Pico';; 'reboot') echo 'Перезавантажити Pico';; esac"
        )
        if action is None or action == "..":
            save_config(project_root, {"filter": current_filter})
            return port

        if action == "sync":
            filter_ = _pick_item(
                ["all", "py", "py+", "nopy", "custom"],
                prompt="filter> ",
                header=f" Current filter: {current_filter}",
                preview="case {} in 'all') echo 'Видалити всі файли на Pico і залити src/';; 'py') echo 'Тільки .py файли';; 'py+') echo '.py, .txt, .json файли';; 'nopy') echo 'Все крім .py';; 'custom') echo 'Вказати власні розширення (через кому)';; esac"
            )
            if filter_ is None:
                continue
            if filter_ == "custom":
                ext = input("Extensions (comma-sep, e.g. .py,.txt): ").strip()
                filter_ = ext if ext else "all"
            current_filter = filter_
            save_config(project_root, {"filter": current_filter})
            sync_tree(src_root, filter=current_filter)
            delete_empty_dirs()
            input("\nPress Enter to continue...")

        elif action == "monitor":
            serial_monitor(port)

        elif action == "reboot":
            print(f"{C.BLUE}Rebooting Pico...{C.RESET}")
            subprocess.run(["mpremote", "reset"])


def _pick_config_menu(port, src_root):
    while True:
        action = _pick_item(
            ["..", "port", "src", "check_update", "init .picoignore"],
            prompt="config> ",
            header=" Esc=back  /=search",
            preview="case {} in '..') echo 'Повернутись до головного меню';; 'port') echo 'Обрати COM-порт Pico (автовизначення)';; 'src') echo 'Змінити вихідну теку для синхронізації';; 'check_update') echo 'Перевірити наявність оновлень Pico Sync';; 'init .picoignore') echo 'Створити .picoignore, meta/, .picosyncconfig';; esac"
        )
        if action is None or action == "..":
            return port, src_root

        if action == "port":
            chosen = interactive_select_port()
            if chosen:
                port = chosen
                os.environ["MPREMOTE_PORT"] = port
                project_root = _project_root(src_root)
                save_config(project_root, {"port": port})
                print(f"{C.GREEN}Port set: {port} (saved){C.RESET}")
        elif action == "src":
            new_src = input(f"Current src: {src_root}\nNew src path (Enter to keep): ").strip()
            if new_src:
                abs_src = os.path.abspath(new_src)
                if os.path.isdir(abs_src):
                    src_root = abs_src
                    print(f"{C.GREEN}Src changed to: {src_root}{C.RESET}")
                else:
                    print(f"{C.RED}Directory not found: {abs_src}{C.RESET}")
            input("\nPress Enter to continue...")
        elif action == "check_update":
            check_for_updates()
            input("\nPress Enter to continue...")
        elif action == "init .picoignore":
            init_project(src_root)
            input("\nPress Enter to continue...")


def _pick_preview_cmd():
    py = sys.executable or "python3"
    return f"{py} -m pico_sync project preview {{}} 2>/dev/null"


def _pick_project_or_action():
    while True:
        proj_list = projects.list_projects()
        items = []
        for p in proj_list:
            items.append(f"{p['name']}  ({p['root']})")
        items.append("[+] add project")
        items.append("[-] remove project")
        items.append("[q] quit")

        choice = _pick_item(
            items,
            prompt="pico> ",
            header=" Esc=back  /=search   Оберіть проект",
            preview=_pick_preview_cmd(),
        )
        if choice is None or choice == "[q] quit":
            return None, "quit"

        if choice == "[+] add project":
            try:
                raw = input("Шлях до кореня проекту (Enter — поточна тека): ")
            except UnicodeDecodeError:
                print(f"{C.RED}Помилка читання вводу. Спробуйте ще раз.{C.RESET}")
                continue
            path = raw.strip()
            if not path:
                path = os.getcwd()
            path = os.path.abspath(os.path.expanduser(path))
            if os.path.isdir(path):
                projects.add_project(path)
                name = os.path.basename(path)
                print(f"{C.GREEN}Проект додано: {name}{C.RESET}")
            else:
                print(f"{C.RED}Директорія не знайдена: {path}{C.RESET}")
            continue

        if choice == "[-] remove project":
            if not proj_list:
                print(f"{C.YELLOW}Немає проектів для видалення.{C.RESET}")
                continue
            remove_items = [f"{p['name']}  ({p['root']})" for p in proj_list]
            remove_items.append("..")
            to_remove = _pick_item(remove_items, prompt="remove> ", header=" Оберіть проект для видалення")
            if to_remove and to_remove != ".." and to_remove in remove_items:
                idx = remove_items.index(to_remove)
                name = proj_list[idx]["name"]
                if projects.remove_project(name):
                    print(f"{C.GREEN}Проект видалено: {name}{C.RESET}")
            continue

        if choice in items:
            idx = items.index(choice)
            if idx < len(proj_list):
                return proj_list[idx], "select"

        continue


def _filter_description(filter_):
    desc = {
        "all": "Всі файли (видаляє все на Pico перед заливкою)",
        "py": "Тільки .py файли",
        "py+": ".py, .txt, .json файли",
        "nopy": "Все крім .py",
    }
    return desc.get(filter_, f"Розширення: {filter_}")


def _show_project_info(port, src_root, project):
    project_root = _project_root(src_root)
    config = load_config(project_root)
    current_filter = config.get("filter", "all")
    pico_ports = find_pico_ports()
    detected_devices = {p.device for p in pico_ports}
    configured = port if port else config.get("port", "/dev/ttyACM0")

    print(f"\n{C.BLUE}── Info ──────────────────────────────{C.RESET}")
    if project:
        print(f" {C.GREEN}Project:{C.RESET}  {project['name']}")
        print(f" {C.GREEN}Root:{C.RESET}     {project['root']}")
    print(f" {C.GREEN}Source:{C.RESET}    {src_root}")
    print()
    status = "⚡ connected" if configured in detected_devices else "✘ not found"
    print(f" {C.GREEN}Device:{C.RESET}     {configured}  {status}")
    if detected_devices:
        print(f" {C.GREEN}Detected:{C.RESET}")
        for d in sorted(detected_devices):
            mark = " (configured)" if d == configured else ""
            print(f"     ⚡ {d}{mark}")
    print()
    print(f" {C.GREEN}Filter:{C.RESET}    {_filter_description(current_filter)}")
    print(f"{C.BLUE}──────────────────────────────────────{C.RESET}\n")

    action = _pick_item(["..", "[p] change port"], prompt="info> ", header=" Esc=back")
    if action == "[p] change port":
        chosen = interactive_select_port()
        if chosen:
            port = chosen
            os.environ["MPREMOTE_PORT"] = port
            save_config(project_root, {"port": port})
            print(f"{C.GREEN}Port set: {port}{C.RESET}")
        input("\nPress Enter to continue...")
    return port


def pick_mode(src_root, project=None):
    if project:
        src_root = os.path.join(project["root"], project["src"])
    project_root = _project_root(src_root)
    config = load_config(project_root)
    port = config.get("port")

    while True:
        action = _pick_item(
            ["..", "[i] info", "[f] files", "[d] device", "[c] config"],
            prompt="pico> ",
            header=" Esc=back  /=search",
            preview="case {} in '..') echo 'Повернутись до списку проектів';; '[i] info') echo 'Інформація про проект, пристрій, фільтр';; '[f] files') echo 'Огляд, перегляд та редагування файлів';; '[d] device') echo 'Синхронізація, моніторинг, перезавантаження';; '[c] config') echo 'Вибір порту, перевірка оновлень, ініціалізація';; esac"
        )
        if action is None or action == "..":
            break

        if action == "[i] info":
            port = _show_project_info(port, src_root, project)
        elif action == "[f] files":
            _pick_files_menu()
        elif action == "[d] device":
            port = _pick_device_menu(port, src_root)
        elif action == "[c] config":
            port, src_root = _pick_config_menu(port, src_root)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Pico Sync Tool — sync/ls/cat/nano for Raspberry Pi Pico",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--port", default="/dev/ttyACM0", help="Pico COM port")
    parser.add_argument("--src", default="src", help="Source directory to sync")

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
    parser.add_argument(
        "--pick", action="store_true", help="Interactive pick mode"
    )
    parser.add_argument(
        "--filter", default="all",
        help="Delete filter: all, py, py+, nopy, or .ext,.ext2"
    )
    parser.add_argument(
        "--init", action="store_true",
        help="Create default .picoignore and meta/ in current directory"
    )

    subparsers = parser.add_subparsers(dest="command")
    proj = subparsers.add_parser("project", help="Керування проектами")
    proj_sub = proj.add_subparsers(dest="project_action")

    proj_add = proj_sub.add_parser("add", help="Додати теку проекту")
    proj_add.add_argument("path", nargs="?", default=".", help="Шлях до кореня проекту")

    proj_sub.add_parser("list", help="Список збережених проектів")

    proj_rm = proj_sub.add_parser("remove", help="Видалити проект зі списку")
    proj_rm.add_argument("name", help="Ім'я або шлях проекту")

    proj_preview = proj_sub.add_parser("preview", help="Показати інформацію про проект (для fzf preview)")
    proj_preview.add_argument("line", help="Рядок зі списку проектів")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "project":
        if args.project_action == "add":
            path = os.path.abspath(args.path)
            if not os.path.isdir(path):
                print(f"{C.RED}Директорія не знайдена: {path}{C.RESET}")
                exit(1)
            is_new = projects.add_project(path)
            name = os.path.basename(path)
            if is_new:
                print(f"{C.GREEN}Проект додано: {name}{C.RESET}")
            else:
                print(f"{C.YELLOW}Проект оновлено: {name}{C.RESET}")
        elif args.project_action == "list":
            proj_list = projects.list_projects()
            if not proj_list:
                print(f"{C.YELLOW}Немає збережених проектів.{C.RESET}")
            else:
                print(f"\n{C.BLUE}Збережені проекти:{C.RESET}\n")
                for p in proj_list:
                    print(f"  {p['name']:20}  {p['root']}")
                print()
        elif args.project_action == "remove":
            if projects.remove_project(args.name):
                print(f"{C.GREEN}Проект видалено: {args.name}{C.RESET}")
            else:
                print(f"{C.RED}Проект не знайдено: {args.name}{C.RESET}")
        elif args.project_action == "preview":
            line = args.line
            if line.startswith("["):
                exit(0)
            m = re.search(r'\((.+)\)$', line)
            root = m.group(1) if m else line
            proj_list = projects.list_projects()
            for p in proj_list:
                if os.path.abspath(p["root"]) == os.path.abspath(root):
                    src_root = os.path.join(p["root"], p["src"])
                    config = load_config(p["root"])
                    port = config.get("port")
                    current_filter = config.get("filter", "all")
                    pico_ports = find_pico_ports()
                    detected = {dev.device for dev in pico_ports}
                    configured = port if port else "/dev/ttyACM0"
                    status = "connected" if configured in detected else "not found"
                    print(f"Project:  {p['name']}")
                    print(f"Root:     {p['root']}")
                    print(f"Source:   {src_root}")
                    print(f"Device:   {configured}  ({status})")
                    if detected:
                        for d in sorted(detected):
                            mark = " <<<" if d == configured else ""
                            print(f"            {d}{mark}")
                    print(f"Filter:   {_filter_description(current_filter)}")
                    break
        exit(0)

    if args.init:
        init_project(os.path.join(os.getcwd(), args.src))
        exit(0)

    if args.pick:
        while True:
            project, action = _pick_project_or_action()
            if action == "quit":
                exit(0)
            if project:
                projects.touch_project(project["root"])
                src_root = os.path.join(project["root"], project["src"])
            else:
                src_root = os.path.join(os.getcwd(), args.src)
                projects.add_project(os.getcwd(), src=args.src)
            pick_mode(src_root, project=project)
        exit(0)

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

    if args.check_update:
        check_for_updates()
        exit(0)

    if args.search_port:
        chosen = interactive_select_port()
        if not chosen:
            print("Скасовано.")
            exit(0)

        print(f"\n{C.GREEN}Вибрано порт: {chosen}{C.RESET}\n")

        args.port = chosen

    if args.port == "/dev/ttyACM0":
        project_root = _project_root(os.path.join(os.getcwd(), args.src))
        config = load_config(project_root)
        if config.get("port") and config["port"] != "/dev/ttyACM0":
            args.port = config["port"]
            print(f"{C.BLUE}Port from config: {args.port}{C.RESET}")

    os.environ["MPREMOTE_PORT"] = args.port

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
        sync_tree(os.path.join(os.getcwd(), args.src), filter=args.filter)
        delete_empty_dirs()
        exit()

    if args.monitor:
        port = None if args.port == "/dev/ttyACM0" else args.port
        serial_monitor(port)
        exit()

    parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exit.")
