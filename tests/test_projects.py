import os
import tempfile

import pytest

from pico_sync import projects


@pytest.fixture(autouse=True)
def temp_projects_file(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setattr(projects, "PROJECTS_FILE", os.path.join(td, "projects.json"))
        monkeypatch.setattr(projects, "CONFIG_DIR", td)
        yield


class TestProjects:
    def test_empty_list(self):
        assert projects.list_projects() == []

    def test_add_project(self):
        with tempfile.TemporaryDirectory() as td:
            is_new = projects.add_project(td)
            assert is_new is True
            lst = projects.list_projects()
            assert len(lst) == 1
            assert lst[0]["root"] == os.path.abspath(td)

    def test_add_duplicate_updates(self):
        with tempfile.TemporaryDirectory() as td:
            projects.add_project(td, name="first")
            is_new = projects.add_project(td, name="second")
            assert is_new is False
            lst = projects.list_projects()
            assert len(lst) == 1
            assert lst[0]["name"] == "second"

    def test_remove_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            projects.add_project(td, name="myproj")
            assert projects.remove_project("myproj") is True
            assert projects.list_projects() == []

    def test_remove_by_path(self):
        with tempfile.TemporaryDirectory() as td:
            projects.add_project(td, name="myproj")
            assert projects.remove_project(td) is True
            assert projects.list_projects() == []

    def test_remove_nonexistent(self):
        assert projects.remove_project("nonexistent") is False

    def test_touch_project(self):
        with tempfile.TemporaryDirectory() as td:
            projects.add_project(td)
            assert projects.touch_project(td) is True

    def test_touch_nonexistent(self):
        assert projects.touch_project("/nonexistent") is False

    def test_add_multiple_and_order(self):
        with tempfile.TemporaryDirectory() as td1:
            with tempfile.TemporaryDirectory() as td2:
                projects.add_project(td1, name="second")
                import time
                time.sleep(0.01)
                projects.add_project(td2, name="first")
                lst = projects.list_projects()
                assert lst[0]["name"] == "first"  # newest first

    def test_add_project_with_src(self):
        with tempfile.TemporaryDirectory() as td:
            projects.add_project(td, src="firmware")
            lst = projects.list_projects()
            assert lst[0]["src"] == "firmware"

    def test_add_project_custom_name(self):
        with tempfile.TemporaryDirectory() as td:
            projects.add_project(td, name="CustomName")
            lst = projects.list_projects()
            assert lst[0]["name"] == "CustomName"
