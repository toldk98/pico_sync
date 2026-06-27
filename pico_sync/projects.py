import os
import json
from datetime import datetime

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pico_sync")
PROJECTS_FILE = os.path.join(CONFIG_DIR, "projects.json")


def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    try:
        with open(PROJECTS_FILE, "r") as f:
            data = json.load(f)
            return data.get("projects", [])
    except (json.JSONDecodeError, OSError):
        return []


def _save_projects(projects):
    _ensure_config_dir()
    with open(PROJECTS_FILE, "w") as f:
        json.dump({"projects": projects}, f, indent=2)
        f.write("\n")


def add_project(root, name=None, src="src"):
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
    return sorted(_load_projects(), key=lambda p: p.get("last_used", ""), reverse=True)


def touch_project(root):
    projects = _load_projects()
    abs_root = os.path.abspath(root)
    for p in projects:
        if os.path.abspath(p["root"]) == abs_root:
            p["last_used"] = datetime.now().isoformat()
            _save_projects(projects)
            return True
    return False
