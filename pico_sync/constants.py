# pico_sync/constants.py
"""Static constants and default values for pico_sync."""

import os

# Enable ANSI color codes in Windows console (10+)
if os.name == "nt":
    os.system("")

# USB identification for Raspberry Pi Pico
PICO_USB_VID = 0x2E8A
PICO_KEYWORDS = ("Pico", "RP2", "MicroPython", "USB Serial Device")

# Version
PICO_SYNC_VERSION = "1.1.2"
VERSION_CHECK_URL = (
    "https://raw.githubusercontent.com/toldk98/pico_sync/main/meta/latest_version.json"
)

# Serial defaults
BAUD = 115200

# Per-project config
CONFIG_FILE = ".picosyncconfig"
DEFAULT_CONFIG = {
    "port": "",
    "filter": "all",
    "piconame": "",
}

# Default .picoignore content
DEFAULT_PICOIGNORE = """\
# Pico Sync — default ignore patterns
__pycache__/
*.pyc
.git/
.DS_Store
Thumbs.db
dist/
*.egg-info/
build/
.idea/
*.swp
*.swo
"""


class C:
    """ANSI terminal color codes."""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
