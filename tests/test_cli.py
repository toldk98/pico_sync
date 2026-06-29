import os
import tempfile

import pytest

from pico_sync.cli import build_parser, main
from pico_sync.constants import PICO_SYNC_VERSION
from pico_sync.lang import set_language


class TestBuildParser:
    def test_parser_creates(self):
        parser = build_parser()
        assert parser is not None

    def test_parser_defaults(self):
        parser = build_parser()
        ns = parser.parse_args([])
        assert ns.src == "src"
        assert ns.filter == "all"
        assert ns.lang is None
        assert ns.port is None

    def test_parser_flags(self):
        parser = build_parser()
        ns = parser.parse_args(["--sync", "--reboot", "--monitor", "--pick", "--version"])
        assert ns.sync is True
        assert ns.reboot is True
        assert ns.monitor is True
        assert ns.pick is True
        assert ns.version is True

    def test_parser_options(self):
        parser = build_parser()
        ns = parser.parse_args(["--port", "COM3", "--src", "firmware", "--filter", "py", "--lang", "en"])
        assert ns.port == "COM3"
        assert ns.src == "firmware"
        assert ns.filter == "py"
        assert ns.lang == "en"

    def test_parser_lang_choices(self):
        parser = build_parser()
        ns = parser.parse_args(["--lang", "ua"])
        assert ns.lang == "ua"
        with pytest.raises(SystemExit):
            parser.parse_args(["--lang", "fr"])

    def test_parser_project_subcommand(self):
        parser = build_parser()
        ns = parser.parse_args(["project", "list"])
        assert ns.command == "project"
        assert ns.project_action == "list"

    def test_parser_project_add(self):
        parser = build_parser()
        ns = parser.parse_args(["project", "add", "/some/path"])
        assert ns.command == "project"
        assert ns.project_action == "add"
        assert ns.path == "/some/path"

    def test_parser_project_remove(self):
        parser = build_parser()
        ns = parser.parse_args(["project", "remove", "myproj"])
        assert ns.command == "project"
        assert ns.project_action == "remove"
        assert ns.name == "myproj"

    def test_parser_help_does_not_crash(self):
        parser = build_parser()
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            pass

    def test_parser_lang_affects_help_text(self):
        set_language("ua")
        parser_ua = build_parser()
        set_language("en")
        parser_en = build_parser()
        assert parser_ua.description != parser_en.description

    def test_parser_init_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["--init"])
        assert ns.init is True

    def test_parser_set_name(self):
        parser = build_parser()
        ns = parser.parse_args(["--set-name", "MyPico"])
        assert ns.set_name == "MyPico"

    def test_parser_ls(self):
        parser = build_parser()
        ns = parser.parse_args(["--ls", "/"])
        assert ns.ls == "/"

    def test_parser_cat(self):
        parser = build_parser()
        ns = parser.parse_args(["--cat", "/boot.py"])
        assert ns.cat == "/boot.py"

    def test_parser_edit(self):
        parser = build_parser()
        ns = parser.parse_args(["--edit", "/main.py"])
        assert ns.edit == "/main.py"

    def test_parser_search_port(self):
        parser = build_parser()
        ns = parser.parse_args(["--search_port"])
        assert ns.search_port is True

    def test_parser_check_update(self):
        parser = build_parser()
        ns = parser.parse_args(["--check_update"])
        assert ns.check_update is True


class TestMainDispatch:
    def test_main_version(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["picosync", "--version"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0

    def test_main_project_list(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["picosync", "project", "list"])
        with tempfile.TemporaryDirectory() as td:
            monkeypatch.setattr("pico_sync.projects.PROJECTS_FILE", os.path.join(td, "projects.json"))
            monkeypatch.setattr("pico_sync.projects.CONFIG_DIR", td)
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

    def test_main_no_args(self, monkeypatch, mocker):
        monkeypatch.setattr("sys.argv", ["picosync"])
        mock_run = mocker.patch("pico_sync.cli._run_interactive", side_effect=SystemExit(0))
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        mock_run.assert_called_once()

    def test_main_init(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["picosync", "--init"])
        with tempfile.TemporaryDirectory() as td:
            src_dir = os.path.join(td, "src")
            os.makedirs(src_dir)
            monkeypatch.chdir(td)
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
            assert os.path.exists(os.path.join(td, ".picoignore"))
