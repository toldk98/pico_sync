import pytest
from pico_sync.cli import build_parser
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
