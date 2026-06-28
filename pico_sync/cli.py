# pico_sync/cli.py
"""CLI entry point: argument parsing, dispatch, and project preview."""

import argparse
import os
import re
import subprocess
import sys

from . import projects
from .constants import C, PICO_SYNC_VERSION
from .config import load_config, project_root, save_config, init_project
from .delta import (
    delete_empty_dirs, pico_cat, pico_edit, pico_ls, sync_tree,
)
from .filter import filter_description
from .lang import _, get_language, set_language
from .pick import pick_mode, _pick_project_or_action
from .port import (
    ensure_port, find_pico_ports, interactive_select_port, serial_monitor,
)


def build_parser():
    """Build and return the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        description="Pico Sync Tool — sync/ls/cat/edit for Raspberry Pi Pico",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--port", default=None, help="Pico COM port (auto-detect if omitted)")
    parser.add_argument("--src", default="src", help="Source directory to sync")

    parser.add_argument("--sync", action="store_true", help="Synchronize src → Pico")
    parser.add_argument("--ls", metavar="PATH", help="List directory on Pico")
    parser.add_argument("--cat", metavar="FILE", help="Output file content from Pico")
    parser.add_argument("--edit", metavar="FILE", help="Edit file on Pico")
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
    parser.add_argument(
        "--lang", default=None, choices=["ua", "en"],
        help="Interface language (ua/en)"
    )
    parser.add_argument(
        "--version", action="store_true",
        help="Show version and exit"
    )

    subparsers = parser.add_subparsers(dest="command")
    proj = subparsers.add_parser("project", help="Керування проектами")
    proj_sub = proj.add_subparsers(dest="project_action")

    proj_add = proj_sub.add_parser("add", help="Додати теку проекту")
    proj_add.add_argument("path", nargs="?", default=".", help="Шлях до кореня проекту")

    proj_sub.add_parser("list", help="Список збережених проектів")

    proj_rm = proj_sub.add_parser("remove", help="Видалити проект зі списку")
    proj_rm.add_argument("name", help="Ім'я або шлях проекту")

    proj_preview = proj_sub.add_parser("preview", help="Показати інформацію про проект")
    proj_preview.add_argument("line", help="Рядок зі списку проектів")

    proj_preview_main = proj_sub.add_parser("preview-main", help="Показати preview для головного меню (для fzf)")
    proj_preview_main.add_argument("item", help="Вибраний пункт меню")
    proj_preview_main.add_argument("root", help="Корінь проекту")

    return parser


def _print_project_preview(proj):
    """Print plain-text project summary for fzf preview panels.

    Args:
        proj: Project dict with name, root, src keys.
    """
    src_root = os.path.join(proj["root"], proj["src"])
    config = load_config(proj["root"])
    port = config.get("port")
    current_filter = config.get("filter", "all")
    pico_ports = find_pico_ports()
    detected = {dev.device for dev in pico_ports}
    configured = port or _("port_not_set")
    status = _("info_connected") if configured in detected else _("info_not_found")
    print(f"{_('info_project', name=proj['name'])}")
    print(f"{_('info_root', path=proj['root'])}")
    print(f"{_('info_source', path=src_root)}")
    print(f"{_('info_device', port=configured, status=status)}")
    if detected:
        print(f"{_('info_detected')}")
        for d in sorted(detected):
            mark = _("info_configured") if d == configured else ""
            print(f"            {d}{mark}")
    print(f"{_('info_filter', filter=filter_description(current_filter))}")


def main():
    """Parse args and dispatch to the appropriate command or interactive mode."""
    parser = build_parser()
    args = parser.parse_args()

    if args.lang:
        set_language(args.lang)

    if args.version:
        print(f"pico_sync {PICO_SYNC_VERSION}")
        exit(0)

    if args.command == "project":
        if args.project_action == "add":
            path = os.path.abspath(args.path)
            if not os.path.isdir(path):
                print(f"{C.RED}{_('project_not_found', path=path)}{C.RESET}")
                exit(1)
            is_new = projects.add_project(path)
            name = os.path.basename(path)
            if is_new:
                print(f"{C.GREEN}{_('project_added', name=name)}{C.RESET}")
            else:
                print(f"{C.YELLOW}{_('project_updated', name=name)}{C.RESET}")
        elif args.project_action == "list":
            proj_list = projects.list_projects()
            if not proj_list:
                print(f"{C.YELLOW}{_('project_empty')}{C.RESET}")
            else:
                print(f"{C.BLUE}{_('project_list_header')}{C.RESET}")
                for p in proj_list:
                    print(f"  {p['name']:20}  {p['root']}")
                print()
        elif args.project_action == "remove":
            if projects.remove_project(args.name):
                print(f"{C.GREEN}{_('project_removed', name=args.name)}{C.RESET}")
            else:
                print(f"{C.RED}{_('project_not_found_remove', name=args.name)}{C.RESET}")
        elif args.project_action == "preview":
            line = args.line
            if line.startswith("["):
                if "[+] add project" in line:
                    print(_("preview_add_project"))
                elif "[-] remove project" in line:
                    print(_("preview_remove_project"))
                elif "[~] lang" in line:
                    lang = get_language()
                    lang_name = _("lang_ua") if lang == "ua" else _("lang_en")
                    print(_("preview_lang", lang=lang_name))
                else:
                    print(_("preview_quit"))
                exit(0)
            m = re.search(r'\((.+)\)$', line)
            root = m.group(1) if m else line
            proj_list = projects.list_projects()
            for p in proj_list:
                if os.path.abspath(p["root"]) == os.path.abspath(root):
                    _print_project_preview(p)
                    break
        elif args.project_action == "preview-main":
            if args.item == "..":
                print(_("preview_back_projects"))
            elif args.item in ("[f] files", "[d] device", "[c] config"):
                hints = {
                    "[f] files": "preview_browse_files",
                    "[d] device": "preview_device_menu",
                    "[c] config": "preview_config_menu",
                }
                print(_(hints[args.item]))
            elif args.item == "[i] info":
                print(_("info_read_only"))
                print()
                proj_list = projects.list_projects()
                for p in proj_list:
                    if os.path.abspath(p["root"]) == os.path.abspath(args.root):
                        _print_project_preview(p)
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
            or args.edit
            or args.search_port
            or args.check_update
            or args.monitor
    )

    if no_actions:
        parser.print_help()
        exit(0)

    if args.reboot:
        print(f"{C.BLUE}{_('rebooting_cli')}{C.RESET}")
        subprocess.run(["mpremote", "reset"])
        exit(0)

    if args.check_update:
        from .config import check_for_updates
        check_for_updates()
        exit(0)

    if args.search_port:
        chosen = interactive_select_port()
        if not chosen:
            print(_("cancelled"))
            exit(0)

        print(f"\n{C.GREEN}{_('port_selected', port=chosen)}{C.RESET}")

        args.port = chosen

    if not args.port:
        p_root = project_root(os.path.join(os.getcwd(), args.src))
        config = load_config(p_root)
        if config.get("port"):
            args.port = config["port"]
            print(f"{C.BLUE}{_('port_auto_config', port=args.port)}{C.RESET}")
        else:
            from .port import find_pico_port_auto
            auto = find_pico_port_auto()
            if auto:
                args.port = auto
                print(f"{C.BLUE}{_('port_auto_detect', port=args.port)}{C.RESET}")

    os.environ["MPREMOTE_PORT"] = args.port

    if args.ls:
        pico_ls(args.ls)
        exit()

    if args.cat:
        pico_cat(args.cat)
        exit()

    if args.edit:
        pico_edit(args.edit)
        exit()

    if args.sync:
        sync_tree(os.path.join(os.getcwd(), args.src), filter=args.filter)
        delete_empty_dirs()
        exit()

    if args.monitor:
        serial_monitor(args.port)
        exit()

    parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(_("exit_msg"))
