# pico_sync/filter.py
"""Delete filter logic for file sync."""


def match_filter(filter_, remote_path):
    """Check if a remote file path matches the delete filter.

    Args:
        filter_: Filter name (all, py, py+, nopy) or comma-separated extensions.
        remote_path: File path on Pico.

    Returns:
        True if the file should be included for deletion.
    """
    if filter_ == "all":
        return True
    if filter_ == "py":
        return remote_path.endswith(".py")
    if filter_ == "py+":
        return remote_path.endswith((".py", ".txt", ".json"))
    if filter_ == "nopy":
        return not remote_path.endswith(".py")
    exts = [e.strip() for e in filter_.split(",")]
    return any(
        remote_path.endswith(e) if e.startswith(".") else remote_path.endswith("." + e)
        for e in exts
    )


from .lang import _


def filter_description(filter_):
    """Return a human-readable description of a filter value.

    Args:
        filter_: Filter name (all, py, py+, nopy) or custom extensions.

    Returns:
        Descriptive string in current language.
    """
    desc = {
        "all": _("filter_desc_all"),
        "py": _("filter_desc_py"),
        "py+": _("filter_desc_py_plus"),
        "nopy": _("filter_desc_nopy"),
    }
    return desc.get(filter_, _("filter_desc_custom", ext=filter_))
