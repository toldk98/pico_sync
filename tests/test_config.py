import json
import os
import tempfile

import pytest

from pico_sync.config import json_load, json_save, project_root, load_config, save_config, init_project


class TestJsonIO:
    def test_json_load_missing(self):
        assert json_load("/nonexistent/path.json") is None

    def test_json_load_custom_default(self):
        assert json_load("/nonexistent/path.json", default={}) == {}

    def test_json_save_and_load(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test.json")
            data = {"key": "value", "num": 42}
            json_save(path, data)
            loaded = json_load(path)
            assert loaded == data

    def test_json_load_corrupt(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "bad.json")
            with open(path, "w") as f:
                f.write("{corrupt")
            assert json_load(path) is None

    def test_json_save_creates_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "sub", "nested", "file.json")
            json_save(path, {"a": 1})
            assert os.path.exists(path)

    def test_json_save_empty_dict(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "empty.json")
            json_save(path, {})
            loaded = json_load(path)
            assert loaded == {}

    def test_json_load_empty_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "empty.json")
            with open(path, "w") as f:
                f.write("")
            assert json_load(path) is None


class TestProjectRoot:
    def test_project_root(self):
        assert project_root("/home/user/project/src") == "/home/user/project"

    def test_project_root_trailing(self):
        assert project_root("/home/user/project/src/") == "/home/user/project"


class TestLoadSaveConfig:
    def test_load_missing(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = load_config(td)
            assert cfg == {}

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as td:
            save_config(td, {"port": "COM3", "filter": "py"})
            cfg = load_config(td)
            assert cfg["port"] == "COM3"
            assert cfg["filter"] == "py"

    def test_save_merges(self):
        with tempfile.TemporaryDirectory() as td:
            save_config(td, {"port": "COM3"})
            save_config(td, {"filter": "py"})
            cfg = load_config(td)
            assert cfg["port"] == "COM3"
            assert cfg["filter"] == "py"

    def test_save_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            save_config(td, {"port": "COM3"})
            save_config(td, {"port": "COM5"})
            cfg = load_config(td)
            assert cfg["port"] == "COM5"


class TestInitProject:
    def test_init_creates_all(self):
        with tempfile.TemporaryDirectory() as td:
            src_dir = os.path.join(td, "src")
            os.makedirs(src_dir)
            init_project(src_dir)
            assert os.path.exists(os.path.join(td, ".picoignore"))
            assert os.path.isdir(os.path.join(td, "meta"))
            assert os.path.exists(os.path.join(td, ".picosyncconfig"))

    def test_init_skips_existing(self):
        with tempfile.TemporaryDirectory() as td:
            src_dir = os.path.join(td, "src")
            os.makedirs(src_dir)
            open(os.path.join(td, ".picoignore"), "w").close()
            os.makedirs(os.path.join(td, "meta"), exist_ok=True)
            init_project(src_dir)
            assert os.path.exists(os.path.join(td, ".picoignore"))
            assert os.path.isdir(os.path.join(td, "meta"))



