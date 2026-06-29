import pytest
from unittest.mock import patch

from pico_sync.delta import _find_editor


class TestFindEditor:
    @patch("pico_sync.delta.sys.platform", "linux")
    @patch("pico_sync.delta.shutil.which")
    def test_finds_nano(self, mock_which):
        mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x == "nano" else None
        result = _find_editor()
        assert result == ["/usr/bin/nano"]

    @patch("pico_sync.delta.sys.platform", "linux")
    @patch("pico_sync.delta.shutil.which")
    def test_finds_vim_fallback(self, mock_which):
        mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x == "vim" else None
        result = _find_editor()
        assert result == ["/usr/bin/vim"]

    @patch("pico_sync.delta.sys.platform", "linux")
    @patch("pico_sync.delta.shutil.which")
    def test_no_editor(self, mock_which):
        mock_which.return_value = None
        result = _find_editor()
        assert result is None

    @patch("pico_sync.delta.sys.platform", "darwin")
    @patch("pico_sync.delta.shutil.which")
    def test_macos_uses_open(self, mock_which):
        result = _find_editor()
        assert result == ["open", "-t"]
