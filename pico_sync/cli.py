# pico_sync/cli.py
"""CLI entry point: argument parsing, dispatch, and project preview."""

import argparse
import os
import re
import subprocess
import sys

from . import projects
from .constants import C, PICO_SYNC_VERSION
from .config import load_config, save_config, init_project
from .delta import (
    delete_empty_dirs, mp_exec, pico_cat, pico_edit, pico_ls, sync_tree,
)
from .filter import filter_description
from .lang import _, get_language, set_language
from .pick import pick_mode, _pick_project_or_action
from .port import (
    ensure_port, find_pico_ports, interactive_select_port, serial_monitor,
)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        description=_("cli_desc"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--port", default=None, help=_("cli_port_help"))
    parser.add_argument("--baud", type=int, default=None, help=_("cli_baud_help"))

    parser.add_argument("--sync", action="store_true", help=_("cli_sync_help"))
    parser.add_argument("--ls", metavar="PATH", help=_("cli_ls_help"))
    parser.add_argument("--cat", metavar="FILE", help=_("cli_cat_help"))
    parser.add_argument("--edit", metavar="FILE", help=_("cli_edit_help"))
    parser.add_argument(
        "--search_port",
        action="store_true",
        help=_("cli_search_port_help"),
    )
    parser.add_argument(
        "--check_update",
        action="store_true",
        help=_("cli_check_update_help"),
    )
    parser.add_argument(
        "--reboot",
        action="store_true",
        help=_("cli_reboot_help"),
    )
    parser.add_argument(
        "--monitor", action="store_true", help=_("cli_monitor_help")
    )
    parser.add_argument(
        "--pick", action="store_true", help=_("cli_pick_help")
    )
    parser.add_argument(
        "--filter", default="all",
        help=_("cli_filter_help")
    )
    parser.add_argument(
        "--init", action="store_true",
        help=_("cli_init_help")
    )
    parser.add_argument(
        "--set-name", metavar="NAME",
        help=_("cli_set_name_help")
    )
    parser.add_argument(
        "--lang", default=None, choices=["ua", "en"],
        help=_("cli_lang_help")
    )
    parser.add_argument(
        "--version", action="store_true",
        help=_("cli_version_help")
    )

    subparsers = parser.add_subparsers(dest="command")
    proj = subparsers.add_parser("project", help=_("cli_project_help"))
    proj_sub = proj.add_subparsers(dest="project_action")

    proj_add = proj_sub.add_parser("add", help=_("cli_project_add_help"))
    proj_add.add_argument("path", nargs="?", default=".", help=_("cli_project_add_path_help"))

    proj_sub.add_parser("list", help=_("cli_project_list_help"))

    proj_rm = proj_sub.add_parser("remove", help=_("cli_project_remove_help"))
    proj_rm.add_argument("name", help=_("cli_project_remove_name_help"))

    proj_preview = proj_sub.add_parser("preview", help=_("cli_project_preview_help"))
    proj_preview.add_argument("line", help=_("cli_project_preview_line_help"))

    proj_preview_main = proj_sub.add_parser("preview-main", help=_("cli_project_preview_main_help"))
    proj_preview_main.add_argument("item", help=_("cli_project_preview_main_item_help"))
    proj_preview_main.add_argument("root", help=_("cli_project_preview_main_root_help"))

    return parser


def _print_project_preview(proj: dict) -> None:
    """Print plain-text project summary for fzf preview panels.

    Args:
        proj: Project dict with name, root keys.
    """
    config = load_config(proj["root"])
    port = config.get("port")
    piconame = config.get("piconame", "")
    current_baud = config.get("baud", 115200)
    current_filter = config.get("filter", "all")
    pico_ports = find_pico_ports()
    detected = {dev.device for dev in pico_ports}

    if piconame:
        from .port import find_pico_by_name
        pico_port = find_pico_by_name(piconame)
        configured = pico_port or _("port_not_set")
    else:
        configured = port or _("port_not_set")

    status = _("info_connected") if configured in detected else _("info_not_found")
    print(f"{_('info_project', name=proj['name'])}")
    print(f"{_('info_root', path=proj['root'])}")
    src_path = os.path.join(proj["root"], "src")
    if os.path.isdir(src_path):
        print(f"{_('info_source', path=src_path)}")
    else:
        print(f"{_('info_source', path=proj['root'])}")
    print(f"{_('info_device', port=configured, status=status)}")
    if piconame:
        print(f"{_('info_piconame', name=piconame)}")
    if detected:
        print(f"{_('info_detected')}")
        for d in sorted(detected):
            mark = _("info_configured") if d == configured else ""
            print(f"            {d}{mark}")
    print(f"{_('info_filter', filter=filter_description(current_filter))}")
    print(f"{_('info_baud', baud=current_baud)}")


def _run_interactive(args: argparse.Namespace) -> None:
    while True:
        project, action = _pick_project_or_action()
        if action == "quit":
            exit(0)
        if project:
            projects.touch_project(project["root"])
            root = project["root"]
        else:
            root = os.getcwd()
            projects.add_project(root)
        pick_mode(root, project=project)


def main() -> None:
    """Parse args and dispatch to the appropriate command or interactive mode."""
    raw_lang = None
    for i, a in enumerate(sys.argv):
        if a == "--lang" and i + 1 < len(sys.argv):
            raw_lang = sys.argv[i + 1]
            break
        if a.startswith("--lang="):
            raw_lang = a.split("=", 1)[1]
            break
    if raw_lang:
        set_language(raw_lang)

    parser = build_parser()
    args = parser.parse_args()

    if args.baud is not None:
        save_config(os.getcwd(), {"baud": args.baud})

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
                elif "[s] settings" in line:
                    print(_("config_settings"))
                elif "[~] lang" in line:
                    lang = get_language()
                    lang_name = _("lang_ua") if lang == "ua" else _("lang_en")
                    print(_("preview_lang", lang=lang_name))
                elif "[!] check update" in line:
                    print(_("config_check_update"))
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
        init_project(os.getcwd())
        exit(0)

    if args.set_name:
        from .config import load_config, save_config
        from .port import ensure_port, find_pico_port_auto
        config = load_config(os.getcwd())
        port = config.get("port") or find_pico_port_auto()
        if not port:
            print(f"{C.RED}{_('port_not_found')}{C.RESET}")
            exit(1)
        os.environ["MPREMOTE_PORT"] = port
        mp_exec(f'with open("/.piconame", "w") as f: f.write({repr(args.set_name)})')
        save_config(os.getcwd(), {"piconame": args.set_name})
        name = args.set_name
        print(f"{C.GREEN}{_('piconame_set', name=name)}{C.RESET}")
        exit(0)

    if args.pick:
        _run_interactive(args)
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
        _run_interactive(args)

    if args.reboot:
        print(f"{C.BLUE}{_('rebooting_cli')}{C.RESET}")
        subprocess.run([sys.executable, "-m", "mpremote", "reset"])
        exit(0)

    if args.check_update:
        from .settings import check_for_updates
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
        config = load_config(os.getcwd())
        if config.get("port"):
            args.port = config["port"]
            print(f"{C.BLUE}{_('port_auto_config', port=args.port)}{C.RESET}")
        else:
            from .port import find_pico_port_auto
            auto = find_pico_port_auto()
            if auto:
                args.port = auto
                print(f"{C.BLUE}{_('port_auto_detect', port=args.port)}{C.RESET}")

    if args.port:
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
        sync_tree(os.getcwd(), filter=args.filter)
        delete_empty_dirs()
        exit()

    if args.monitor:
        baud = args.baud
        if baud is None:
            config = load_config(os.getcwd())
            baud = config.get("baud", 115200)
        serial_monitor(args.port, baud=baud)
        exit()

    parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(_("exit_msg"))
