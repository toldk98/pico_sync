"""Global pico_sync settings: config dir, check for updates, language persistence."""

import json
import os
import urllib.request

from typing import Any

from .constants import C, PICO_SYNC_VERSION, VERSION_CHECK_URL

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pico_sync")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


def _load_settings() -> dict:
    """Load settings from ~/.config/pico_sync/settings.json."""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_settings(data: dict) -> None:
    """Save settings to ~/.config/pico_sync/settings.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    existing = _load_settings()
    existing.update(data)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
        f.write("\n")


def check_for_updates() -> None:
    """Check GitHub for a newer version. Prints result, fails silently on error.

    No return value.
    """
    from .lang import _
    try:
        with urllib.request.urlopen(VERSION_CHECK_URL, timeout=2) as r:
            data = json.loads(r.read().decode())
            latest = data.get("version")
            changelog = data.get("changelog", "")
            url = data.get(
                "url", "https://github.com/toldk98/pico_sync/releases/latest"
            )

            if not latest:
                return

            if latest != PICO_SYNC_VERSION:
                print(f"{C.YELLOW}{_('update_available')}{C.RESET}")
                print(f"  {_('latest_version', version=latest)}")
                print(f"  {_('current_version', version=PICO_SYNC_VERSION)}")

                if changelog:
                    print(f"{C.BLUE}{_('changelog', text=changelog)}{C.RESET}")

                print(_("download_url", url=url))
            else:
                print(
                    f"{C.GREEN}{_('already_latest', version=PICO_SYNC_VERSION)}{C.RESET}"
                )
    except Exception as e:
        pass  # fail silently
