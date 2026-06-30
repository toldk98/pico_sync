# Pico Sync Tool

**Pico Sync** — a compact CLI tool for convenient work with Raspberry Pi Pico / Pico W running MicroPython.
Provides commands for file synchronization, file system browsing, basic file operations on the device,
log monitoring, and board reset.

Works on top of `mpremote`. Supports interactive mode with menus, fzf, language selection (UA/EN).

The tool's goal is to make MicroPython development feel as close to working with a local project as possible.

**Features:**

- 🔄 **Sync** — upload files to Pico (src/ or root)
- 🧠 **SHA-sync** — only changed files are uploaded (SHA-256)
- 🗑 **Auto-delete extra files** — files on Pico that don't exist locally are removed
- 🧼 **Empty directory cleanup** — after sync
- ⛔ **`.picoignore`** — file ignoring (like `.gitignore`)
- 📂 **File viewing and editing** — interactive browser (pick) or `--ls`/`--cat`/`--edit` (CLI)
- 🔍 **Auto-detect port** — find Pico among serial ports: first by device name (if `.piconame` is set), then by saved port, otherwise — first available Pico
- 🔌 **Serial monitor** — live log viewer from Pico
- 🔁 **Reboot** — software board reset
- 🌐 **Interface language** — Ukrainian / English
- 📦 **Project management** — save projects with settings

🌐 [Українська версія](https://github.com/toldk98/pico_sync/blob/main/README.md)

📖 **Details:** [interactive mode (pick)](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_pick.md) · [CLI mode](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_cli.md)

[![PyPI version](https://img.shields.io/pypi/v/pico-sync)](https://pypi.org/project/pico-sync/)
[![CI](https://github.com/toldk98/pico_sync/actions/workflows/ci.yml/badge.svg)](https://github.com/toldk98/pico_sync/actions/workflows/ci.yml)

---

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [FAQ](#faq)
- [License](#license)

---

## Installation

### Linux

**Recommended (pipx):**
```bash
pipx install pico_sync
```
Isolation in a separate environment, doesn't pollute the system.

**Alternative (pip):**
```bash
pip install pico_sync
```
Can use `--user`:
```bash
pip install --user pico_sync
```

### Windows

**Via pip:**
```powershell
pip install pico_sync
```
Requires Python 3.7+ installed and added to PATH.

**Via pipx:**
```powershell
pipx install pico_sync
```

### macOS

**Via pip:**
```bash
pip3 install pico_sync
```

**Via pipx:**
```bash
pipx install pico_sync
```

### From GitHub (any OS)

```bash
git clone https://github.com/toldk98/pico_sync.git
cd pico_sync
pip install .
```

### Portable version (no installation)

```bash
git clone https://github.com/toldk98/pico_sync.git
cd pico_sync
pip install pyserial mpremote
python pico_sync_portable.py
```

### Dependencies

- Python 3.7+
- `pyserial` — serial port communication
- `mpremote` — execute commands on Pico

### Optional dependencies (for interactive mode)

- **[fzf](https://github.com/junegunn/fzf)** — convenient menu selection. If not installed, numbered selection is used.

## Usage

### Launch

- **Pick:** `picosync` or `picosync --pick`. Opens a menu with fzf (or numbered selection). [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_pick.md)
- **CLI:** `picosync <options>`. Action flags without interactivity. [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_cli.md)

### Start screen / Help

- **Pick:** list of saved projects + `[+] add project`, `[-] remove project`, `[s] settings`, `[q] quit`. Select project → main menu.
- **CLI:** `picosync --help` — all options; `picosync project --help` — project management.

### Sync

- **Pick:** `[d] device → sync` → filter selection from menu (all/py/py+/nopy/custom).
- **CLI:** `picosync --sync [--filter py|py+|nopy|.ext,.ext2]`.

Algorithm (shared by both modes):
1. Load `.picoignore` from project root
2. Take a snapshot of all files on Pico
3. Walk the local directory (src/ or root), collect files for sync (skip ignored and `.piconame`)
4. Run SHA-256 on all Pico files in one request
5. Compare hashes: match → skip, missing → upload, different → update
6. Delete files on Pico without local match (respecting filter)
7. Clean empty directories

### Files (view, edit, delete)

- **Pick:** `[f] files` — browser with directory navigation, `[*] find` — search all files; cat/edit/rm in file context menu. Editor: nano/vim (Linux), TextEdit (macOS), notepad (Windows). [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_pick.md)
- **CLI:** `picosync --ls /` — list root; `picosync --ls /spm` — list directory; `picosync --cat /main.py` — content; `picosync --edit /config.py` — editing. [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_cli.md)

### Serial monitor

- **Pick:** `[d] device → monitor`
- **CLI:** `picosync --monitor`

Exit: `Ctrl+C`. Auto-reconnect on reboot/port change.

### Reboot

- **Pick:** `[d] device → reboot`
- **CLI:** `picosync --reboot`

Software reset via `mpremote reset`.

### Device name (piconame)

- **Pick:** `[c] config → port_settings → piconame` → detect (read from Pico), set (write new), clear (delete + clear config).
- **CLI:** `picosync --set-name <name>` — writes `/.piconame` to Pico and saves to config.

### Project settings

- **Pick:** `[c] config` → port_settings/baud/piconame/init.
- **CLI:** `picosync --port /dev/ttyACM0 --sync`, `picosync --init`, `picosync --search_port`.

### Project management

- **Pick:** start screen — `[+] add project` (enter path), `[-] remove project` (select from list). [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_pick.md)
- **CLI:** `picosync project list`, `picosync project add /path`, `picosync project remove <name>`. [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_cli.md)

### Global settings

- **Pick:** `[s] settings` → `[~] lang` (switch UA/EN), `[!] check update` (check for updates). [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_pick.md)
- **CLI:** `picosync --lang ua/en`, `picosync --check_update`, `LANG=ua` / `LANG=en` — environment variable. [→ details](https://github.com/toldk98/pico_sync/blob/main/docs/en/users/readme_cli.md)

## Configuration

### Global settings

File: `~/.config/pico_sync/settings.json`

```json
{
  "language": "ua"
}
```

- **language** — interface language: `"ua"` or `"en"`. Auto-detected: first from file, then from `$LANG` (if `uk*` → `"ua"`, otherwise → `"en"`). Changed:
  - **Pick:** `[s] settings → [~] lang`
  - **CLI:** `--lang ua/en`
  - **Shared:** `LANG=ua` / `LANG=en`

### Project system

File: `~/.config/pico_sync/projects.json`

```json
{
  "projects": [
    {
      "name": "my-project",
      "root": "/home/user/projects/my-project",
      "last_used": "2026-06-29T12:00:00"
    }
  ]
}
```

Each project contains:
- `name` — name (basename of root directory)
- `root` — absolute path to root
- `last_used` — last used date (ISO 8601)

Projects are sorted by `last_used` descending.

### Project file `.picosyncconfig`

File: `<project_root>/.picosyncconfig`

```json
{
  "port": "",
  "filter": "all",
  "piconame": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `port` | `str` | Pico port (e.g. `/dev/ttyACM0`). Empty = auto-detect |
| `filter` | `str` | Sync filter: all, py, py+, nopy, .ext,.ext2 |
| `piconame` | `str` | Device name for name-based search. Empty = not used |

Created:
- **Pick:** `[c] config → init`
- **CLI:** `picosync --init`

### `.picoignore`

Works like `.gitignore`. Examples:

```gitignore
# ignore secret.py
secret.py

# ignore entire directory
data/

# ignore by extension
*.mpy
```

Supports:
- `*` — any number of characters
- `?` — single character
- `[abc]` — character from set
- `**` — any nesting level
- `!` — negation (don't ignore)
- Lines without `/` apply to all levels; with `/` — to a specific path

Default `.picoignore`:
```
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
```

### Port

The tool finds Pico in this order:
1. By **.piconame** (if set) — iterates all Pico ports, reads `/.piconame` from each
2. By **port** from config — uses saved port
3. **Auto-detect** — finds first device with Raspberry Pi USB ID (0x2E8A)
4. If nothing found:
   - **Pick:** `[c] config → port_settings → port` for manual selection
   - **CLI:** `picosync --search_port` for manual selection

### Piconame

Optional device name stored in `/.piconame` on Pico. Allows identifying a specific board when multiple Picos are connected.

Management:
- **Pick:** `[c] config → port_settings → piconame` with options detect (read from Pico), set (write new), clear (delete from Pico and clear config)
- **CLI:** `picosync --set-name <name>` — write name to Pico and save to config

`.piconame` is automatically excluded from sync (not deleted, not uploaded).

### Sync filters

Only affect **deletion** of extra files from Pico. All files are uploaded regardless of filter.

| Filter | Description |
|--------|-------------|
| `all` | All files (deletes extras on Pico) |
| `py` | Only `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Everything except `.py` |
| `.ext,.ext2` | Custom comma-separated extensions |

## FAQ

### Pico not found / port not detected

Make sure Pico is connected with a USB cable (not just power). If auto-detect fails:

- **Pick:** `[c] config → port_settings → port` for manual selection from serial port list
- **CLI:** `picosync --search_port` for interactive selection from serial port list

### Two Picos connected simultaneously

Auto-detect picks the first one found. To work with a specific device:

- **Pick:** `[c] config → port_settings → piconame → set`, give it a unique name
- **CLI:** `picosync --set-name <name>`, give it a unique name

### How to install fzf?

`fzf` is an optional tool for convenient menu navigation in interactive mode. Without it, numbered input works. Not needed for CLI mode.

- **Linux:** `sudo apt install fzf` (or `pacman -S fzf`, `dnf install fzf`)
- **macOS:** `brew install fzf`
- **Windows:** download binary from https://github.com/junegunn/fzf/releases

### Files not syncing

Check `.picoignore` — the file might match an ignore rule. If `src/` exists in root, it is synced; otherwise, the root.

### Error "No module named 'pyserial' / 'mpremote'"

Install dependencies: `pip install pyserial mpremote` (only relevant for portable version without package installation).

### How to update Pico Sync?

**Check for updates:** `[s] settings → [!] check update` (pick) or `picosync --check_update` (CLI). Shows newer version, changelog, and links but does not update automatically.

**Install update:**
- **Via pipx:** `pipx upgrade pico_sync`
- **Via pip:** `pip install --upgrade pico_sync`

### How to get full help?

**CLI:** `picosync --help`, `picosync project --help`

In pick mode, all available actions are shown in the menu.

## License

[AGPL-3.0](https://github.com/toldk98/pico_sync/blob/main/LICENSE)
