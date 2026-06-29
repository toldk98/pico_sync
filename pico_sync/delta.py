# pico_sync/delta.py
"""SHA-256 delta helpers and file operations for Pico sync."""

import sys
import base64
import hashlib
import os
import subprocess
import tempfile
import shutil

from typing import Optional

from .constants import C
from .config import project_root
from .filter import match_filter
from .ignore import compile_ignore_patterns, load_ignore_list, should_ignore
from .lang import _


def mp_exec(code: str) -> None:
    """Run MicroPython code on Pico via mpremote exec.

    Args:
        code: MicroPython code string.

    No return value.
    """
    subprocess.run(["mpremote", "exec", code], check=True)


def mp_check_output(code: str) -> str:
    """Run MicroPython code on Pico via mpremote exec, return stdout.

    Args:
        code: MicroPython code string.

    Returns:
        Decoded stdout string.
    """
    return subprocess.check_output(["mpremote", "exec", code]).decode()


def local_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest of local data.

    Args:
        data: Bytes to hash.

    Returns:
        Hex digest string.
    """
    return hashlib.sha256(data).hexdigest()


def pico_file_sha256(path: str) -> Optional[str]:
    """Return SHA-256 hex digest of a file on Pico, or None if missing.

    Args:
        path: Remote file path on Pico.

    Returns:
        Hex digest string, or None if file doesn't exist on Pico.
    """
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

    out = mp_check_output(code).strip()
    return None if out == "NONE" else out


def mp_write_file(remote_path: str, data: bytes) -> None:
    """Write data to a file on Pico, auto-creating parent directories.

    Args:
        remote_path: Destination path on Pico.
        data: File content as bytes.

    No return value.
    """
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
        mp_exec(mkdir_cmd)

    b64 = base64.b64encode(data).decode("ascii")
    cmd = (
        "import ubinascii;"
        f"open({repr(remote_path)},'wb').write("
        f"ubinascii.a2b_base64(b'{b64}'))"
    )
    mp_exec(cmd)


def pico_list_files() -> Optional[list]:
    """Recursively list all files on Pico.

    Returns:
        Sorted list of full remote paths, or empty list on error.
    """
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
    try:
        out = mp_check_output(code)
    except subprocess.CalledProcessError:
        print(f"{C.RED}{_('pico_list_error')}{C.RESET}")
        return []
    return sorted(out.splitlines())


def pico_batch_sha256(paths: list) -> dict:
    """Compute SHA-256 of multiple files on Pico in one mpremote call.

    Args:
        paths: List of remote file paths.

    Returns:
        Dict of {path: sha_hex or None} — None means file missing on Pico.
    """
    if not paths:
        return {}

    paths_repr = ", ".join(repr(p) for p in paths)
    code = (
        "import ubinascii, uhashlib\n"
        f"paths = [{paths_repr}]\n"
        "for p in paths:\n"
        "    try:\n"
        "        h = uhashlib.sha256()\n"
        "        f = open(p, 'rb')\n"
        "        while True:\n"
        "            b = f.read(2048)\n"
        "            if not b: break\n"
        "            h.update(b)\n"
        "        f.close()\n"
        "        print('OK', ubinascii.hexlify(h.digest()).decode(), p)\n"
        "    except OSError:\n"
        "        print('--', p)\n"
    )
    out = mp_check_output(code)
    result = {}
    for line in out.splitlines():
        if line.startswith("OK "):
            rest = line[3:]
            sha, path = rest.split(" ", 1)
            result[path] = sha
        elif line.startswith("-- "):
            result[line[3:]] = None
    return result


def delete_empty_dirs() -> None:
    """Recursively remove empty directories on Pico.

    No return value. Prints removed dirs to stdout.
    """
    code = (
        "import os\n"
        "def clean(p):\n"
        "    removed=False\n"
        "    for f in os.listdir(p):\n"
        "        fp = p+'/'+f if p!='/' else '/' + f\n"
        "        try:\n"
        "            st=os.stat(fp)[0]\n"
        "            if st & 0x4000:\n"
        "                if clean(fp): removed=True\n"
        "        except: pass\n"
        "    try:\n"
        "        if len(os.listdir(p))==0 and p!='/':\n"
        "            os.rmdir(p)\n"
        "            print('RMDIR ' + p)\n"
        "            return True\n"
        "    except: pass\n"
        "    return False\n"
        "clean('/')\n"
    )

    out = mp_check_output(code)
    if out.strip():
        print(out)


def sync_tree(src_root: str, filter: str = "all") -> None:
    """Sync src_root to Pico: upload new/changed files, delete missing ones.

    Uses SHA-256 delta comparison. Respects .picoignore and delete filter.

    Args:
        src_root: Local source directory path.
        filter: Delete filter — all, py, py+, nopy, or custom extensions.

    No return value.
    """
    p_root = project_root(src_root)
    raw_patterns = load_ignore_list(p_root)
    compiled_patterns = compile_ignore_patterns(raw_patterns)
    print(_("ignore_patterns", patterns=raw_patterns))
    print(_("delete_filter", filter=filter))

    local_files = []
    pico_files_before = pico_list_files()

    to_check = []

    for root, dirs, files in os.walk(src_root):
        dirs[:] = [
            d
            for d in dirs
            if not should_ignore(os.path.join(root, d), compiled_patterns, src_root)
        ]

        for fname in files:
            local = os.path.join(root, fname)

            if should_ignore(local, compiled_patterns, src_root):
                print(_("skip_ignored", path=local))
                continue

            rpath = root.replace(src_root, "").replace("\\", "/").strip("/")
            rdir = f"/{rpath}" if rpath else "/"
            remote = os.path.join(rdir, fname).replace("\\", "/")

            local_files.append(remote)
            with open(local, "rb") as f:
                data = f.read()
            to_check.append((remote, local, data))

    remote_paths = [entry[0] for entry in to_check]
    sha_map = pico_batch_sha256(remote_paths)

    for remote, local, data in to_check:
        local_hash = local_sha256(data)
        remote_hash = sha_map.get(remote)

        if remote_hash == local_hash:
            print(f"{C.YELLOW}{_('skip_same', path=local)}{C.RESET}")
            continue

        if remote_hash is None:
            print(f"{C.GREEN}{_('upload_new', local=local, remote=remote)}{C.RESET}")
        else:
            print(f"{C.GREEN}{_('upload_diff', local=local, remote=remote)}{C.RESET}")

        mp_write_file(remote, data)

    for remote_file in pico_files_before:
        if remote_file not in local_files:
            if match_filter(filter, remote_file):
                print(f"{C.RED}{_('delete_file', path=remote_file)}{C.RESET}")
                mp_exec(f"import os; os.remove({repr(remote_file)})")

    print(_("sync_complete"))


def pico_ls(path: str) -> None:
    """List directory contents on Pico (d/ prefix for directories).

    Args:
        path: Remote directory path on Pico.

    No return value. Prints to stdout.
    """
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

    print(mp_check_output(code))


def pico_cat(path: str) -> None:
    """Print file content from Pico to stdout.

    Args:
        path: Remote file path on Pico.

    No return value.
    """
    code = "import sys\n" f"f=open({repr(path)},'r')\n" "sys.stdout.write(f.read())\n"
    out = mp_check_output(code)
    print(out)


def _find_editor() -> Optional[list]:
    """Return editor command list or None."""
    if sys.platform == "darwin":
        return ["open", "-t"]
    for editor in ["nano", "vim", "vi", "notepad"]:
        path = shutil.which(editor)
        if path:
            return [path]
    return None


def pico_edit(path: str) -> None:
    """Download a file from Pico, edit in editor, upload changes back.

    Args:
        path: Remote file path on Pico.

    No return value.
    """
    code = (
        "import sys\n"
        f"try:\n"
        f"    f=open({repr(path)},'r')\n"
        f"    sys.stdout.write(f.read())\n"
        "except:\n"
        "    pass\n"
    )
    original = mp_check_output(code)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    tmp_path = tmp.name
    tmp.write(original.encode())
    tmp.close()

    editor_cmd = _find_editor()
    if editor_cmd:
        subprocess.run(editor_cmd + [tmp_path])
    else:
        print(f"{C.YELLOW}{_('edit_no_editor', path=tmp_path)}{C.RESET}")
        input(_("press_enter"))
        os.remove(tmp_path)
        return

    with open(tmp_path, "rb") as f:
        data = f.read()

    print(f"{C.GREEN}{_('upload_from_edit', path=path)}{C.RESET}")
    mp_write_file(path, data)

    os.remove(tmp_path)
