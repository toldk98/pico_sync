# pico_sync/port.py
"""Serial port detection, selection, and monitor for Raspberry Pi Pico."""

import os
import subprocess
import time
import serial
import serial.tools.list_ports as list_ports

from .constants import PICO_USB_VID, PICO_KEYWORDS, BAUD, C
from .lang import _


def is_pico_port(port):
    """Check if a serial port matches a Raspberry Pi Pico by VID or description.

    Args:
        port: serial.tools.list_ports.comport object.

    Returns:
        True if the port looks like a Pico.
    """
    if port.vid == PICO_USB_VID:
        return True

    desc = (port.description or "") + " " + (port.product or "")
    return any(key in desc for key in PICO_KEYWORDS)


def find_pico_ports():
    """Return list of all comports that match is_pico_port()."""
    return [p for p in list_ports.comports() if is_pico_port(p)]


def find_pico_port_auto():
    """Return device path of first Pico found, or None."""
    for p in list_ports.comports():
        if is_pico_port(p):
            return p.device
    return None


def _read_piconame_from_port(device):
    old = os.environ.get("MPREMOTE_PORT")
    os.environ["MPREMOTE_PORT"] = device
    try:
        result = subprocess.check_output(
            ["mpremote", "exec",
             'import os; print(open("/.piconame").read().strip())'],
            stderr=subprocess.DEVNULL, timeout=3
        ).decode().strip()
        return result if result else None
    except:
        return None
    finally:
        if old:
            os.environ["MPREMOTE_PORT"] = old
        else:
            os.environ.pop("MPREMOTE_PORT", None)


def find_pico_by_name(name):
    for p in find_pico_ports():
        try:
            dev_name = _read_piconame_from_port(p.device)
            if dev_name == name:
                return p.device
        except:
            continue
    return None


def serial_monitor(port=None, baud=BAUD):
    """Open serial monitor with auto-reconnect on Pico disconnect.

    Args:
        port: Device path (auto-detected if None).
        baud: Baud rate (default 115200).

    No return value. Loops until Ctrl+C.
    """
    if port is None:
        port = find_pico_port_auto()

    if not port:
        print(_("port_not_found"))
        return

    print(_("opening_port", port=port, baud=baud))
    print(_("waiting_data"))

    while True:
        try:
            with serial.Serial(port, baud, timeout=0.5) as ser:
                while True:
                    try:
                        line = ser.readline()
                        if line:
                            try:
                                text = line.decode("utf-8", errors="replace").rstrip()
                            except Exception:
                                text = str(line)

                            print(f"\033[92m{text}\033[0m")
                        else:
                            time.sleep(0.05)

                    except (serial.SerialException, OSError):
                        print(_("device_disconnected"))
                        break

        except serial.SerialException:
            print(_("pico_not_ready"))
            time.sleep(1)

        new_port = find_pico_port_auto()
        if new_port and new_port != port:
            print(_("switching_port", port=new_port))
            port = new_port


def print_ports_with_numbers(ports, pico_devs):
    """Print numbered port list with Pico marker.

    Args:
        ports: List of comports.
        pico_devs: Set of Pico device paths to mark with ⭐.

    No return value.
    """
    print(_("available_ports"))
    for i, p in enumerate(ports):
        mark = "⭐" if p.device in pico_devs else " "
        print(f" {i}) {mark}  {p.device:15}  {p.description}")

    print("")


def interactive_select_port():
    """Show numbered port list and let user pick one interactively.

    Returns:
        Selected device path string, or None if cancelled.
    """
    ports = list_ports.comports()
    pico_ports = find_pico_ports()
    pico_devs = {p.device for p in pico_ports}

    if not ports:
        print(_("no_serial_ports"))
        return None

    print_ports_with_numbers(ports, pico_devs)

    while True:
        inp = input(_("select_port_prompt")).strip()
        if inp == "":
            return None
        if not inp.isdigit():
            print(_("enter_number"))
            continue

        idx = int(inp)
        if 0 <= idx < len(ports):
            return ports[idx].device

        print(_("invalid_number"))


def ensure_port(port, piconame=None):
    if piconame:
        found = find_pico_by_name(piconame)
        if found:
            os.environ["MPREMOTE_PORT"] = found
            return found
    if port is not None:
        return port
    port = find_pico_port_auto()
    if port:
        os.environ["MPREMOTE_PORT"] = port
    return port
