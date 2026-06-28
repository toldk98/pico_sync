import pytest

from pico_sync.filter import match_filter, filter_description


class TestMatchFilter:
    def test_all(self):
        assert match_filter("all", "any/file.py") is True
        assert match_filter("all", "main.txt") is True

    def test_py(self):
        assert match_filter("py", "main.py") is True
        assert match_filter("py", "main.txt") is False
        assert match_filter("py", "noext") is False

    def test_py_plus(self):
        assert match_filter("py+", "main.py") is True
        assert match_filter("py+", "data.txt") is True
        assert match_filter("py+", "config.json") is True
        assert match_filter("py+", "image.png") is False

    def test_nopy(self):
        assert match_filter("nopy", "main.py") is False
        assert match_filter("nopy", "main.txt") is True
        assert match_filter("nopy", "image.png") is True

    def test_custom_ext_with_dot(self):
        assert match_filter(".wav,.mp3", "song.wav") is True
        assert match_filter(".wav,.mp3", "song.mp3") is True
        assert match_filter(".wav,.mp3", "main.py") is False

    def test_custom_ext_without_dot(self):
        assert match_filter("wav,mp3", "song.wav") is True
        assert match_filter("wav,mp3", "song.mp3") is True

    def test_edge_empty_ext(self):
        assert match_filter(",", "file") is False

    def test_substring_not_match(self):
        assert match_filter("py", "maincpy.py") is True
        assert match_filter("py", "main.pyc") is False


class TestFilterDescription:
    def test_all_desc(self):
        d = filter_description("all")
        assert isinstance(d, str) and len(d) > 0

    def test_custom_desc(self):
        d = filter_description(".xyz")
        assert ".xyz" in d
