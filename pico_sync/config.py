# pico_sync/config.py
"""Configuration management: .picosyncconfig, project init, shared JSON helpers."""

import json
import os

from typing import Any

from .constants import CONFIG_FILE, DEFAULT_CONFIG, DEFAULT_PICOIGNORE, C
from .lang import _


def json_load(path: str, default: Any = None) -> Any:
    """Load JSON from file, returning default on error or missing file.

    Args:
        path: Path to JSON file.
        default: Value to return if file missing or corrupt.

    Returns:
        Parsed JSON data, or default.
    """
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def json_save(path: str, data: dict) -> None:
    """Write data as JSON to file, creating parent dirs if needed.

    Args:
        path: Path to JSON file.
        data: Serializable data to write.

    No return value.
    """
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")



def load_config(project_root_path: str) -> dict:
    """Load .picosyncconfig from project root.

    Args:
        project_root_path: Project root directory.

    Returns:
        Dict with config values, or empty dict if file missing or corrupt.
    """
    path = os.path.join(project_root_path, CONFIG_FILE)
    result = json_load(path)
    return result if isinstance(result, dict) else {}


def save_config(project_root_path: str, data: dict) -> None:
    """Merge data into .picosyncconfig at project root and save.

    Args:
        project_root_path: Project root directory.
        data: Dict of config values to merge.

    No return value.
    """
    path = os.path.join(project_root_path, CONFIG_FILE)
    existing = load_config(project_root_path)
    existing.update(data)
    json_save(path, existing)


def init_project(root: str) -> None:
    """Create .picoignore and .picosyncconfig in project root.

    Skips creation if files already exist.

    Args:
        root: Project root directory path.

    No return value.
    """
    picoignore = os.path.join(root, ".picoignore")
    if not os.path.exists(picoignore):
        with open(picoignore, "w") as f:
            f.write(DEFAULT_PICOIGNORE)
        print(f"{C.GREEN}{_('picoignore_created')}{C.RESET}")
    else:
        print(f"{C.YELLOW}{_('picoignore_exists')}{C.RESET}")

    config_path = os.path.join(root, CONFIG_FILE)
    if not os.path.exists(config_path):
        save_config(root, DEFAULT_CONFIG)
        print(f"{C.GREEN}{_('config_created', file=CONFIG_FILE)}{C.RESET}")
    else:
        print(f"{C.YELLOW}{_('config_exists', file=CONFIG_FILE)}{C.RESET}")



