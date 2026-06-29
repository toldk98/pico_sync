import pytest

from pico_sync.pick import _build_preview, _build_tree


class TestBuildPreview:
    def test_build_preview_basic(self):
        result = _build_preview({"a": "A", "b": "B"})
        assert "'a') echo 'A'" in result
        assert "'b') echo 'B'" in result

    def test_build_preview_empty(self):
        result = _build_preview({})
        assert result == "case {} in esac"


class TestBuildTree:
    def test_build_tree_empty(self):
        assert _build_tree([]) == {}

    def test_build_tree_single(self):
        result = _build_tree(["/src/main.py"])
        assert "src/" in result
        assert result["src/"] == {"main.py": True}

    def test_build_tree_nested(self):
        result = _build_tree(["/src/a.py", "/src/sub/b.py"])
        assert "src/" in result
        assert "sub/" in result["src/"]
        assert result["src/"]["a.py"] is True
        assert result["src/"]["sub/"] == {"b.py": True}
