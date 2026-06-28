import os
import tempfile

import pytest

from pico_sync.ignore import compile_ignore_patterns, load_ignore_list, should_ignore


class TestCompileIgnorePatterns:
    def test_empty(self):
        assert compile_ignore_patterns([]) == []

    def test_simple_filename(self):
        regexes = compile_ignore_patterns(["main.py"])
        assert regexes[0].match("main.py")
        assert not regexes[0].match("other.py")

    def test_wildcard(self):
        regexes = compile_ignore_patterns(["*.pyc"])
        assert regexes[0].match("foo.pyc")
        assert not regexes[0].match("foo.py")

    def test_double_star(self):
        regexes = compile_ignore_patterns(["**/__pycache__"])
        assert regexes[0].match("dir/__pycache__")
        assert regexes[0].match("a/b/c/__pycache__")

    def test_directory_only(self):
        regexes = compile_ignore_patterns(["build/"])
        assert regexes[0].match("build")
        assert regexes[0].match("build/some_file")
        assert not regexes[0].match("foo/build/bar")

    def test_question_mark(self):
        regexes = compile_ignore_patterns(["file.?xt"])
        assert regexes[0].match("file.txt")
        assert regexes[0].match("file.xxt")
        assert not regexes[0].match("file.xxxt")


class TestLoadIgnoreList:
    def test_no_file(self):
        with tempfile.TemporaryDirectory() as td:
            assert load_ignore_list(td) == []

    def test_load_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, ".picoignore"), "w") as f:
                f.write("# comment\n*.pyc\n__pycache__/\n  \n\n*.log\n")
            patterns = load_ignore_list(td)
            assert patterns == ["*.pyc", "__pycache__/", "*.log"]


class TestShouldIgnore:
    def test_ignore_simple(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "src")
            os.makedirs(src)
            filepath = os.path.join(src, "main.pyc")
            with open(filepath, "w") as f:
                f.write("x")

            regexes = compile_ignore_patterns(["*.pyc"])
            assert should_ignore(filepath, regexes, src) is True

    def test_not_ignore(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "src")
            os.makedirs(src)
            filepath = os.path.join(src, "main.py")
            with open(filepath, "w") as f:
                f.write("x")

            regexes = compile_ignore_patterns(["*.pyc"])
            assert should_ignore(filepath, regexes, src) is False

    def test_ignore_directory(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "src")
            os.makedirs(os.path.join(src, "build"))
            filepath = os.path.join(src, "build", "output.o")
            with open(filepath, "w") as f:
                f.write("x")

            regexes = compile_ignore_patterns(["build/"])
            assert should_ignore(filepath, regexes, src) is True
