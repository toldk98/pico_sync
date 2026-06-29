import json

import pytest

from pico_sync.settings import check_for_updates
from pico_sync.constants import PICO_SYNC_VERSION


class TestCheckForUpdates:
    def test_check_update_available(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.read.return_value.decode.return_value = json.dumps({
            "version": "99.99.99",
            "changelog": "Major update",
            "url": "https://example.com",
        })
        mocker.patch("pico_sync.settings.urllib.request.urlopen").return_value.__enter__.return_value = mock_resp
        check_for_updates()

    def test_check_update_current(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.read.return_value.decode.return_value = json.dumps({
            "version": PICO_SYNC_VERSION,
            "changelog": "",
            "url": "",
        })
        mocker.patch("pico_sync.settings.urllib.request.urlopen").return_value.__enter__.return_value = mock_resp
        check_for_updates()

    def test_check_update_network_error(self, mocker):
        mocker.patch("pico_sync.settings.urllib.request.urlopen", side_effect=Exception("Network error"))
        check_for_updates()
