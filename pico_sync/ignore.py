# pico_sync/ignore.py
"""Gitignore-style pattern matching for file sync exclusion."""

import os
import re


def compile_ignore_patterns(patterns):
    """Convert gitignore-like patterns to compiled regex list.

    Supports **, *, ?, and directory-only (trailing /) patterns.

    Args:
        patterns: List of gitignore-style pattern strings.

    Returns:
        List of compiled regex objects.
    """
    regex_list = []

    for pat in patterns:
        pat = pat.replace("\\", "/")

        directory_only = pat.endswith("/")
        if directory_only:
            pat = pat[:-1]

        pat_escaped = re.escape(pat)
        pat_escaped = pat_escaped.replace(r"\*\*", "####DOUBLESTAR####")
        pat_escaped = pat_escaped.replace(r"\*", "[^/]*")
        pat_escaped = pat_escaped.replace(r"\?", ".")
        pat_escaped = pat_escaped.replace("####DOUBLESTAR####", ".*")

        if directory_only:
            regex = r"^" + pat_escaped + r"(/.*)?$"
        else:
            regex = r"^" + pat_escaped + r"$"

        regex_list.append(re.compile(regex))

    return regex_list


def load_ignore_list(root):
    """Read .picoignore patterns from project root.

    Args:
        root: Project root directory.

    Returns:
        List of non-empty, non-comment pattern strings.
    """
    ignore_file = os.path.join(root, ".picoignore")
    patterns = []

    if os.path.exists(ignore_file):
        with open(ignore_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)

    return patterns


def should_ignore(path, compiled_patterns, src_root):
    """Check if a file path matches any ignore pattern.

    Args:
        path: Absolute path to the file or directory.
        compiled_patterns: List of compiled regex objects.
        src_root: Source directory root for relative path calculation.

    Returns:
        True if the path should be ignored.
    """
    rel = os.path.relpath(path, src_root).replace("\\", "/")
    basename = os.path.basename(rel)

    for regex in compiled_patterns:
        if regex.match(rel) or regex.match(basename):
            return True

    return False
