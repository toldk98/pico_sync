import pytest
from unittest.mock import MagicMock, patch

from pico_sync.port import is_pico_port, find_pico_ports, find_pico_port_auto, print_ports_with_numbers, interactive_select_port


class TestIsPicoPort:
    def test_pico_by_vid(self):
        mock_port = MagicMock()
        mock_port.vid = 0x2E8A
        mock_port.description = ""
        mock_port.product = None
        assert is_pico_port(mock_port) is True

    def test_pico_by_description(self):
        mock_port = MagicMock()
        mock_port.vid = None
        mock_port.description = "Pico"
        mock_port.product = None
        assert is_pico_port(mock_port) is True

    def test_not_pico(self):
        mock_port = MagicMock()
        mock_port.vid = 0x0403
        mock_port.description = "FTDI Device"
        mock_port.product = None
        assert is_pico_port(mock_port) is False


class TestFindPicoPorts:
    @patch("pico_sync.port.list_ports.comports")
    def test_find_pico_ports_returns_matching(self, mock_comports):
        mock_pico = MagicMock()
        mock_pico.vid = 0x2E8A
        mock_pico.description = ""
        mock_pico.product = None
        mock_pico.device = "/dev/ttyACM0"
        mock_other = MagicMock()
        mock_other.vid = 0x0403
        mock_other.description = "FTDI"
        mock_other.product = None
        mock_other.device = "/dev/ttyUSB0"
        mock_comports.return_value = [mock_pico, mock_other]
        result = find_pico_ports()
        assert len(result) == 1
        assert result[0].device == "/dev/ttyACM0"

    @patch("pico_sync.port.list_ports.comports")
    def test_find_pico_ports_empty(self, mock_comports):
        mock_comports.return_value = []
        assert len(find_pico_ports()) == 0


class TestFindPicoPortAuto:
    @patch("pico_sync.port.list_ports.comports")
    def test_auto_finds_first(self, mock_comports):
        mock_pico = MagicMock()
        mock_pico.vid = 0x2E8A
        mock_pico.description = ""
        mock_pico.product = None
        mock_pico.device = "/dev/ttyACM0"
        mock_comports.return_value = [mock_pico]
        assert find_pico_port_auto() == "/dev/ttyACM0"

    @patch("pico_sync.port.list_ports.comports")
    def test_auto_returns_none(self, mock_comports):
        mock_comports.return_value = []
        assert find_pico_port_auto() is None


class TestPrintPorts:
    def test_print_ports(self, capsys):
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyACM0"
        mock_port.description = "Pico"
        print_ports_with_numbers([mock_port], {"/dev/ttyACM0"})
        captured = capsys.readouterr()
        assert "/dev/ttyACM0" in captured.out


class TestInteractiveSelectPort:
    @patch("pico_sync.port.list_ports.comports")
    @patch("pico_sync.pick._uinput")
    def test_select_valid(self, mock_uinput, mock_comports):
        mock_port = MagicMock()
        mock_port.vid = 0x2E8A
        mock_port.description = "Pico"
        mock_port.product = None
        mock_port.device = "/dev/ttyACM0"
        mock_comports.return_value = [mock_port]
        mock_uinput.return_value = "0"
        result = interactive_select_port()
        assert result == "/dev/ttyACM0"
