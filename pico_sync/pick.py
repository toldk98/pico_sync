# pico_sync/pick.py
"""Interactive pick UI: menus, browser, device/config submenus, project selector."""

import os
import shlex
import shutil
import subprocess
import sys

from typing import Optional

from . import projects
from .constants import C
from .config import (
    init_project, load_config, project_root, save_config,
)
from .settings import check_for_updates
from .delta import (
    delete_empty_dirs, mp_check_output, mp_exec, pico_cat, pico_list_files,
    pico_edit, sync_tree,
)
from .filter import filter_description
from .lang import _, get_language, set_language
from .port import (
    ensure_port, find_pico_by_name, find_pico_ports, interactive_select_port,
    serial_monitor,
)


def _uinput(prompt: str = "") -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return sys.stdin.buffer.readline().decode("utf-8", errors="replace").strip()


def _build_preview(mapping: dict) -> str:
    """Build an fzf preview shell command from an option->description mapping.

    Args:
        mapping: Dict of {option_label: description_text}.

    Returns:
        Shell case..esac string for fzf --preview.
    """
    parts = ["case {} in"]
    for opt, desc in mapping.items():
        desc_esc = desc.replace("'", "'\\''")
        parts.append(f"'{opt}') echo '{desc_esc}';;")
    parts.append("esac")
    return " ".join(parts)


def _pick_item(items: list, prompt: str = "> ", header: Optional[str] = None, preview: Optional[str] = None) -> Optional[str]:
    """Show interactive picker via fzf, fall back to numbered input.

    Args:
        items: List of option strings.
        prompt: Input prompt string.
        header: Optional header shown above items.
        preview: Optional fzf preview shell command.

    Returns:
        Selected item string, or None if cancelled.
    """
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
        inp = _uinput(prompt)
        if inp == "":
            return None
        if not inp.isdigit():
            continue
        idx = int(inp)
        if 0 <= idx < len(items):
            return items[idx]


def _build_tree(file_paths: list) -> list:
    """Build a nested dict tree from a list of file paths.

    Directories end with / in keys, files are True values.

    Args:
        file_paths: List of file path strings.

    Returns:
        Nested dict representing the file tree.
    """
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


def _pick_ls_browser(all_files: Optional[list] = None) -> None:
    """Interactive directory browser for files on Pico.

    Args:
        all_files: Cached file list, or None to fetch fresh.

    No return value. Prints file content on selection.
    """
    if all_files is None:
        all_files = pico_list_files()
    if not all_files:
        print(_("pico_empty"))
        return

    root = _build_tree(all_files)

    def _file_context_menu(node, name, file_path):
        while True:
            action = _pick_item(
                ["..", "cat", "edit", "rm"],
                prompt=f"file: {name}> ",
                header=_("file_actions"),
                preview=_build_preview({
                    "..": _("back_to_files"),
                    "cat": _("cat_file"),
                    "edit": _("edit_file"),
                    "rm": _("rm_file"),
                }),
            )
            if action is None or action == "..":
                return

            if action == "cat":
                pico_cat(file_path)
                _uinput(_("press_enter"))

            elif action == "edit":
                pico_edit(file_path)

            elif action == "rm":
                confirm = _uinput(_("confirm_delete", name=name)).strip().lower()
                if confirm == "y":
                    mp_exec(f"import os; os.remove({repr(file_path)})")
                    print(f"{C.GREEN}{_('deleted_ok', name=name)}{C.RESET}")
                    if node is not None:
                        node.pop(name, None)
                    return

    def _find_file():
        items = [".."] + all_files
        selected = _pick_item(items, prompt="find> ", header=_("find_header"))
        if selected and selected != "..":
            name = os.path.basename(selected)
            _file_context_menu(None, name, selected)

    def _browse(node, display_path):
        while True:
            dirs = sorted(k for k in node if k.endswith("/"))
            files = sorted(k for k in node if not k.endswith("/"))

            choices = [".."]
            if display_path == "/":
                choices.append("[r] refresh")
            choices.append("[*] find")
            choices += [f"d {d}" for d in dirs]
            choices += [f"- {f}" for f in files]

            selected = _pick_item(choices, prompt=f"ls {display_path}> ")
            if selected is None:
                return None

            if selected == "..":
                return None

            if selected == "[r] refresh":
                return "refresh"

            if selected == "[*] find":
                _find_file()
                continue

            if selected.startswith("d "):
                dir_name = selected[2:]
                sub_path = display_path.rstrip("/") + "/" + dir_name.rstrip("/")
                result = _browse(node[dir_name], sub_path)
                if result == "refresh":
                    return "refresh"
                continue

            if selected.startswith("- "):
                name = selected[2:]
                file_path = (display_path.rstrip("/") + "/" + name).replace("//", "/")
                _file_context_menu(node, name, file_path)

    while True:
        result = _browse(root, "/")
        if result != "refresh":
            break
        all_files = pico_list_files()
        if not all_files:
            print(_("pico_empty"))
            return
        root = _build_tree(all_files)


def _pick_files_menu(all_files: Optional[list] = None) -> None:
    """Open interactive file browser for Pico files.

    Args:
        all_files: Cached file list, or None to fetch fresh.
    """
    _pick_ls_browser(all_files)


def _pick_device_menu(port: str, src_root: str, piconame: Optional[str] = None) -> tuple:
    """Interactive submenu for device operations (sync, monitor, reboot).

    Args:
        port: Current port string.
        src_root: Source directory path.
        piconame: Optional .piconame for precise port detection.

    Returns:
        Tuple of (port, needs_refresh). port may change if reconfigured.
        needs_refresh is True if sync or reboot was performed.
    """
    port = ensure_port(port, piconame=piconame)
    if not port:
        print(_("device_not_found"))
        return port, False

    needs_refresh = False
    p_root = project_root(src_root)
    config = load_config(p_root)
    current_filter = config.get("filter", "all")

    while True:
        action = _pick_item(
            ["..", "sync", "monitor", "reboot"],
            prompt="device> ",
            header=_("device_header"),
            preview=_build_preview({
                "..": _("back_to_main"),
                "sync": _("device_sync"),
                "monitor": _("device_monitor"),
                "reboot": _("device_reboot"),
            }),
        )
        if action is None or action == "..":
            save_config(p_root, {"filter": current_filter})
            return port, needs_refresh

        if action == "sync":
            filter_ = _pick_item(
                ["all", "py", "py+", "nopy", "custom"],
                prompt="filter> ",
                header=_("current_filter", filter=current_filter),
                preview=_build_preview({
                    "all": _("filter_all"),
                    "py": _("filter_py"),
                    "py+": _("filter_py_plus"),
                    "nopy": _("filter_nopy"),
                    "custom": _("filter_custom"),
                }),
            )
            if filter_ is None:
                continue
            if filter_ == "custom":
                ext = _uinput(_("ext_prompt")).strip()
                filter_ = ext if ext else "all"
            current_filter = filter_
            save_config(p_root, {"filter": current_filter})
            sync_tree(src_root, filter=current_filter)
            delete_empty_dirs()
            needs_refresh = True
            _uinput(_("press_enter"))

        elif action == "monitor":
            serial_monitor(port)

        elif action == "reboot":
            print(f"{C.BLUE}{_('rebooting')}{C.RESET}")
            subprocess.run(["mpremote", "reset"])
            needs_refresh = True


def _pick_port_settings_menu(port: Optional[str], src_root: str) -> Optional[str]:
    p_root = project_root(src_root)
    while True:
        action = _pick_item(
            ["..", "port", "piconame"],
            prompt="port> ",
            header=_("device_header"),
            preview=_build_preview({
                "..": _("back_to_config"),
                "port": _("port_settings_port"),
                "piconame": _("port_settings_piconame"),
            }),
        )
        if action is None or action == "..":
            return port

        if action == "port":
            chosen = interactive_select_port()
            if chosen:
                port = chosen
                os.environ["MPREMOTE_PORT"] = port
                save_config(p_root, {"port": port})
                print(f"{C.GREEN}{_('config_port_set', port=port)}{C.RESET}")
            _uinput(_("press_enter"))

        elif action == "piconame":
            config = load_config(p_root)
            current = config.get("piconame", "")
            sub_action = _pick_item(
                ["..", "detect", "set", "clear"],
                prompt="piconame> ",
                header=_("piconame_current", name=current) if current else _("piconame_not_set"),
                preview=_build_preview({
                    "..": _("back_to_config"),
                    "detect": _("piconame_detect"),
                    "set": _("piconame_set"),
                    "clear": _("piconame_clear"),
                }),
            )
            if sub_action is None or sub_action == "..":
                continue

            if sub_action == "detect":
                p = ensure_port(config.get("port"))
                if not p:
                    from .port import find_pico_port_auto
                    p = find_pico_port_auto()
                if not p:
                    print(f"{C.RED}{_('port_not_found')}{C.RESET}")
                    _uinput(_("press_enter"))
                    continue
                os.environ["MPREMOTE_PORT"] = p
                from .port import _read_piconame_from_port
                name = _read_piconame_from_port(p)
                if name:
                    save_config(p_root, {"piconame": name})
                    print(f"{C.GREEN}{_('piconame_detected', name=name)}{C.RESET}")
                else:
                    print(f"{C.YELLOW}{_('piconame_not_on_pico')}{C.RESET}")
                _uinput(_("press_enter"))

            elif sub_action == "set":
                new_name = _uinput(_("piconame_prompt")).strip()
                if new_name:
                    p = ensure_port(config.get("port"))
                    if not p:
                        from .port import find_pico_port_auto
                        p = find_pico_port_auto()
                    if not p:
                        print(f"{C.RED}{_('port_not_found')}{C.RESET}")
                        _uinput(_("press_enter"))
                        continue
                    os.environ["MPREMOTE_PORT"] = p
                    mp_exec(f'with open("/.piconame", "w") as f: f.write({repr(new_name)})')
                    save_config(p_root, {"piconame": new_name})
                    print(f"{C.GREEN}{_('piconame_set', name=new_name)}{C.RESET}")
                _uinput(_("press_enter"))

            elif sub_action == "clear":
                save_config(p_root, {"piconame": ""})
                print(f"{C.GREEN}{_('piconame_cleared')}{C.RESET}")
                _uinput(_("press_enter"))


def _pick_config_menu(port: Optional[str], src_root: str) -> tuple:
    while True:
        action = _pick_item(
            ["..", "port_settings", "src", "init"],
            prompt="config> ",
            header=_("device_header"),
            preview=_build_preview({
                "..": _("back_to_main"),
                "port_settings": _("config_port_settings"),
                "src": _("config_src"),
                "init": _("config_init"),
            }),
        )
        if action is None or action == "..":
            return port, src_root

        if action == "port_settings":
            port = _pick_port_settings_menu(port, src_root)
        elif action == "src":
            new_src = _uinput(_("config_src_change", root=src_root)).strip()
            if new_src:
                abs_src = os.path.abspath(new_src)
                if os.path.isdir(abs_src):
                    src_root = abs_src
                    print(f"{C.GREEN}{_('config_src_ok', root=src_root)}{C.RESET}")
                else:
                    print(f"{C.RED}{_('config_src_not_found', path=abs_src)}{C.RESET}")
            _uinput(_("press_enter"))
        elif action == "init":
            init_project(src_root)
            _uinput(_("press_enter"))


def _pick_preview_cmd() -> str:
    """Return fzf preview shell command that shows project info.

    Uses `pico_sync project preview` which receives the fzf-selected line.
    """
    py = sys.executable or "python3"
    return f"{py} -m pico_sync project preview {{}} 2>/dev/null"


def _pick_project_or_action() -> tuple:
    """Show project list with actions (add/remove/quit), return selected project.

    Returns:
        Tuple of (project_dict, action_str).
        action_str is "select" when a project is chosen, "quit" to exit.
    """
    while True:
        proj_list = projects.list_projects()
        items = []
        for p in proj_list:
            items.append(f"{p['name']}  ({p['root']})")
        items.append("[+] add project")
        items.append("[-] remove project")
        items.append("[s] settings")
        items.append("[q] quit")

        choice = _pick_item(
            items,
            prompt="pico> ",
            header=_("project_selector_header"),
            preview=_pick_preview_cmd(),
        )
        if choice is None or choice == "[q] quit":
            return None, "quit"

        if choice == "[+] add project":
            try:
                raw = input(_("project_prompt"))
            except UnicodeDecodeError:
                print(f"{C.RED}{_('project_read_error')}{C.RESET}")
                continue
            path = raw.strip()
            if not path:
                path = os.getcwd()
            path = os.path.abspath(os.path.expanduser(path))
            if os.path.isdir(path):
                projects.add_project(path)
                name = os.path.basename(path)
                print(f"{C.GREEN}{_('project_added', name=name)}{C.RESET}")
            else:
                print(f"{C.RED}{_('project_not_found', path=path)}{C.RESET}")
            continue

        if choice == "[-] remove project":
            if not proj_list:
                print(f"{C.YELLOW}{_('project_no_projects')}{C.RESET}")
                continue
            remove_items = [f"{p['name']}  ({p['root']})" for p in proj_list]
            remove_items.append("..")
            to_remove = _pick_item(remove_items, prompt="remove> ", header=_("project_selector_header"), preview=_pick_preview_cmd())
            if to_remove and to_remove != ".." and to_remove in remove_items:
                idx = remove_items.index(to_remove)
                name = proj_list[idx]["name"]
                if projects.remove_project(name):
                    print(f"{C.GREEN}{_('project_removed', name=name)}{C.RESET}")
            continue

        if choice == "[s] settings":
            settings_choice = _pick_item(
                ["..", "[~] lang", "[!] check update"],
                prompt="settings> ",
                header=_("config_settings"),
                preview=_build_preview({
                    "..": _("back_to_main"),
                    "[~] lang": _("config_lang"),
                    "[!] check update": _("config_check_update"),
                }),
            )
            if settings_choice == "[~] lang":
                lang_choice = _pick_item(
                    ["..", "ua", "en"],
                    prompt="lang> ",
                    header=_("lang_select"),
                    preview=_build_preview({
                        "..": _("back_to_settings"),
                        "ua": _("lang_ua"),
                        "en": _("lang_en"),
                    }),
                )
                if lang_choice and lang_choice in ("ua", "en"):
                    set_language(lang_choice)
                    lang_name = _("lang_ua") if lang_choice == "ua" else _("lang_en")
                    print(f"{C.GREEN}{_('lang_set', lang=lang_name)}{C.RESET}")
                    _uinput(_("press_enter"))
            elif settings_choice == "[!] check update":
                check_for_updates()
                _uinput(_("press_enter"))
            continue

        if choice in items:
            idx = items.index(choice)
            if idx < len(proj_list):
                return proj_list[idx], "select"

        continue


def _show_project_info(port: Optional[str], src_root: str, project: Optional[dict]) -> None:
    """Display read-only project info panel.

    Args:
        port: Current port string.
        src_root: Current source directory path.
        project: Project dict from projects list, or None.
    """
    p_root = project_root(src_root)
    config = load_config(p_root)
    current_filter = config.get("filter", "all")
    piconame = config.get("piconame", "")
    pico_ports = find_pico_ports()
    detected_devices = {p.device for p in pico_ports}

    if piconame:
        from .port import find_pico_by_name
        pico_port = find_pico_by_name(piconame)
        configured = pico_port or _("port_not_set")
    else:
        configured = port or config.get("port") or _("port_not_set")

    status_icon = "⚡" if configured in detected_devices else "✘"
    status_label = _("info_connected") if configured in detected_devices else _("info_not_found")

    print(f"\n{C.BLUE}── {_('info_read_only')} ──{C.RESET}")
    if project:
        print(f" {C.GREEN}{_('info_project', name=project['name'])}{C.RESET}")
        print(f" {C.GREEN}{_('info_root', path=project['root'])}{C.RESET}")
    print(f" {C.GREEN}{_('info_source', path=src_root)}{C.RESET}")
    print()
    print(f" {C.GREEN}{_('info_device', port=configured, status=status_label)}{C.RESET}  {status_icon}")
    if piconame:
        print(f" {C.GREEN}{_('info_piconame', name=piconame)}{C.RESET}")
        if configured != _("port_not_set") and configured not in detected_devices:
            print(f" {C.YELLOW}{_('info_piconame_not_found')}{C.RESET}")
    if detected_devices:
        print(f" {C.GREEN}{_('info_detected')}{C.RESET}")
        for d in sorted(detected_devices):
            mark = _("info_configured") if d == configured else ""
            print(f"     ⚡ {d}{mark}")
    print()
    print(f" {C.GREEN}{_('info_filter', filter=filter_description(current_filter))}{C.RESET}")
    print(f"{C.BLUE}──────────────────────────────────────{C.RESET}\n")

    input(f"{C.YELLOW}{_('info_back_hint')}{C.RESET}")


def _main_preview_cmd(root: str) -> str:
    """Return fzf preview command for main project menu.

    Uses `pico_sync project preview-main` to show live project info
    when the user hovers over `[i] info`.

    Args:
        root: Project root path.

    Returns:
        Shell command string for fzf --preview.
    """
    py = sys.executable or "python3"
    return f"{py} -m pico_sync project preview-main {{}} {shlex.quote(root)} 2>/dev/null"


def pick_mode(src_root: str, project: Optional[dict] = None) -> None:
    """Main interactive menu loop for a project.

    Shows options: info, files, device, config, and back.

    Args:
        src_root: Source directory path.
        project: Project dict from projects list, or None.
    """
    if project:
        src_root = os.path.join(project["root"], project["src"])
    p_root = project_root(src_root)
    config = load_config(p_root)
    port = config.get("port")
    piconame = config.get("piconame", "")
    files_cache = None

    while True:
        action = _pick_item(
            ["..", "[i] info", "[f] files", "[d] device", "[c] config"],
            prompt="pico> ",
            header=" Esc=back  /=search",
            preview=_main_preview_cmd(p_root),
        )
        if action is None or action == "..":
            break

        if action == "[i] info":
            _show_project_info(port, src_root, project)
        elif action == "[f] files":
            if files_cache is None:
                files_cache = pico_list_files()
            _pick_files_menu(files_cache)
        elif action == "[d] device":
            port, needs_refresh = _pick_device_menu(port, src_root, piconame=piconame)
            if needs_refresh:
                files_cache = None
        elif action == "[c] config":
            port, src_root = _pick_config_menu(port, src_root)
