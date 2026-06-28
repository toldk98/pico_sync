# pico_sync/projects.py
"""Project management: add, list, remove, global config (~/.config/pico_sync/)."""

import os
from datetime import datetime

from .config import json_load, json_save

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pico_sync")
PROJECTS_FILE = os.path.join(CONFIG_DIR, "projects.json")


def _load_projects():
    """Read projects list from ~/.config/pico_sync/projects.json.

    Returns:
        List of project dicts, or empty list if file missing or malformed.
    """
    data = json_load(PROJECTS_FILE)
    if data is None:
        return []
    return data.get("projects", []) if isinstance(data, dict) else []


def _save_projects(projects):
    """Write projects list to ~/.config/pico_sync/projects.json.

    Args:
        projects: List of project dicts to persist.

    No return value.
    """
    json_save(PROJECTS_FILE, {"projects": projects})


def add_project(root, name=None, src="src"):
    """Add or update a project in the global projects list.

    Args:
        root: Project root directory path.
        name: Display name (defaults to basename of root).
        src: Source subdirectory relative to root (default: 'src').

    Returns:
        True if a new project was added, False if an existing one was updated.
    """
    projects = _load_projects()
    abs_root = os.path.abspath(root)
    if name is None:
        name = os.path.basename(abs_root)

    for p in projects:
        if os.path.abspath(p["root"]) == abs_root:
            p["name"] = name
            p["src"] = src
            p["last_used"] = datetime.now().isoformat()
            _save_projects(projects)
            return False

    projects.append({
        "name": name,
        "root": abs_root,
        "src": src,
        "last_used": datetime.now().isoformat(),
    })
    _save_projects(projects)
    return True


def remove_project(name_or_root):
    """Remove a project from the global projects list.

    Args:
        name_or_root: Project name or root path to identify the project.

    Returns:
        True if a project was removed, False if not found.
    """
    projects = _load_projects()
    abs_path = os.path.abspath(name_or_root) if os.path.exists(name_or_root) else None

    filtered = []
    removed = False
    for p in projects:
        if p["name"] == name_or_root or (abs_path and os.path.abspath(p["root"]) == abs_path):
            removed = True
            continue
        filtered.append(p)

    if removed:
        _save_projects(filtered)
    return removed


def list_projects():
    """Return all saved projects sorted by last_used descending.

    Returns:
        List of project dicts, newest last_used first.
    """
    return sorted(_load_projects(), key=lambda p: p.get("last_used", ""), reverse=True)


def touch_project(root):
    """Update last_used timestamp for a project.

    Args:
        root: Project root path.

    Returns:
        True if the project was found and updated, False otherwise.
    """
    projects = _load_projects()
    abs_root = os.path.abspath(root)
    for p in projects:
        if os.path.abspath(p["root"]) == abs_root:
            p["last_used"] = datetime.now().isoformat()
            _save_projects(projects)
            return True
    return False
