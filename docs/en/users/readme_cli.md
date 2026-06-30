# Pico Sync Tool — CLI mode

**Pico Sync** — a compact CLI tool for working with Raspberry Pi Pico / Pico W running MicroPython.
Provides commands for file synchronization, file system browsing, basic file operations on the device,
log monitoring, and board reset.

Works on top of `mpremote`. Supports interactive mode with menus, fzf, language selection (UA/EN) — see `readme_pick.md`.

The tool's goal is to make MicroPython development feel as close to working with a local project as possible.

**Features:**

- 🔄 **Sync** — upload files to Pico (src/ or root)
- 🧠 **SHA-sync** — only changed files are uploaded (SHA-256)
- 🗑 **Auto-delete extra files** — files on Pico that don't exist locally are removed
- 🧼 **Empty directory cleanup** — after sync
- ⛔ **`.picoignore`** — file ignoring (like `.gitignore`)
- 📂 **CLI file viewing** — `--ls`, `--cat`, `--edit` for files on Pico
- 🔍 **Auto-detect port** — find Pico among serial ports and by name
- 🔌 **Serial monitor** — live log viewer from Pico
- 🔁 **Reboot** — software board reset
- 🌐 **Interface language** — Ukrainian / English
- 📦 **Project management** — CLI commands `project list/add/remove`

The tool takes <1 MB, split into modules for easier maintenance and testing.

🌐 [Українська версія](../ua/users/readme_cli.md)

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

---

## Usage

### General syntax

```bash
picosync [options] [project <command>]
python -m pico_sync [options] [project <command>]
```

Without arguments, launches interactive mode. For CLI commands, action flags are passed. Both variants (`picosync` and `python -m pico_sync`) are equivalent.

### Help

```bash
picosync --help
```

```
usage: picosync [-h] [--port PORT] [--baud BAUD] [--sync] [--ls PATH]
                [--cat FILE] [--edit FILE] [--search_port] [--check_update]
                [--reboot] [--monitor] [--pick] [--filter FILTER] [--init]
                [--set-name NAME] [--lang {ua,en}] [--version]
                {project} ...

Pico Sync Tool — sync/ls/cat/edit for Raspberry Pi Pico

positional arguments:
  {project}
    project        Manage projects

options:
  -h, --help       show this help message and exit
  --port PORT      Pico COM port (auto-detect if omitted)
  --baud BAUD      Port baud rate (default 115200)
  --sync           Synchronize project → Pico
  --ls PATH        List directory on Pico
  --cat FILE       Output file content from Pico
  --edit FILE      Edit file on Pico
  --search_port    Interactively search serial ports and choose Pico port
  --check_update   Check for newer version of Pico Sync Tool
  --reboot         Reboot Pico (software reset)
  --monitor        Live serial log monitor for Pico
  --pick           Interactive pick mode
  --filter FILTER  Delete filter: all, py, py+, nopy, or .ext,.ext2
  --init           Create default .picoignore and .picosyncconfig
  --set-name NAME  Write NAME to /.piconame on Pico and save to config
  --lang {ua,en}   Interface language (ua/en)
  --version        Show version and exit
```

### Version

```bash
picosync --version
```

Shows the current tool version.

### Check for updates

```bash
picosync --check_update
```

Fetches `meta/latest_version.json` from GitHub (`toldk98/pico_sync`), compares version with current. If a newer version is available — shows version, changelog, links to PyPI and GitHub, and the `pip install --upgrade pico_sync` command.

### Language

```bash
picosync --lang ua
picosync --lang en
```

Sets the language for the current run. Can also be set via `LANG=ua` / `LANG=en`.

### Sync

```bash
picosync --sync                          # all files
picosync --sync --filter py              # only .py
picosync --sync --filter .wav,.mpy       # specific extensions
picosync --port /dev/ttyACM0 --sync      # specify port
```

Algorithm:
1. Loads `.picoignore` from project root
2. Takes a snapshot of all files on Pico
3. Walks the local directory (src/ or root), collects files for sync (skips ignored and `.piconame`)
4. Runs SHA-256 on all Pico files in one request
5. Compares hashes: match → skip, missing → upload, different → update
6. Deletes files on Pico without local match (respecting filter)
7. Cleans empty directories

### File viewing

```bash
picosync --ls /                 # list root directory
picosync --ls /spm              # list directory
picosync --cat /main.py         # display file content
```

### File editing

```bash
picosync --edit /config/settings.py
```

File is downloaded from Pico to a temp file, opened in system editor:
- **macOS:** `open -t` (TextEdit)
- **Linux:** `nano` → `vim` → `vi` (first found)
- **Windows:** `notepad`

After saving, the file is automatically uploaded back to Pico.

### Port search

```bash
picosync --search_port
```

Shows a numbered list of all serial ports (Pico marked with ⭐). Select a number to use.

### Serial monitor

```bash
picosync --monitor
```

Opens a live log viewer from Pico (115200 baud). Auto-reconnects on:
- Pico reboot
- USB port change
- temporary disconnection

Exit: `Ctrl+C`.

### Reboot

```bash
picosync --reboot
```

Software reset of Pico via `mpremote reset`.

### Device name

```bash
picosync --set-name my-pico
```

Writes `/.piconame` to Pico and saves to project config.

### Project initialization

```bash
picosync --init
```

Creates in the current directory:
- `.picoignore` — default patterns
- `.picosyncconfig` — project config

### Port

```bash
picosync --port /dev/ttyACM0 --sync
picosync --port COM3 --monitor
```

Sets COM port explicitly. Works with all action flags. If not set — auto-detect.

### Baud rate

```bash
picosync --baud 9600 --monitor
picosync --baud 115200 --monitor
```

Sets serial port speed for the monitor. Default: 115200. If MicroPython on Pico is configured for a different speed, the monitor won't work without the correct `--baud`.

### Filter

```bash
picosync --sync --filter py
picosync --sync --filter .wav,.mpy
```

Values: `all`, `py`, `py+`, `nopy`, `.ext,.ext2`. Only affects deletion of extra files.

### Project management

```bash
picosync project list                        # list all projects
picosync project add /home/user/my-project   # add project
picosync project remove my-project           # remove project
```

Projects are stored in `~/.config/pico_sync/projects.json`.

---

## Project structure

```
project_root/
│
├── .picoignore           # ignore rules
├── .picosyncconfig       # project config (port, filter, baud)
│
└── ...                   # project files (synced to Pico)
```

⚠️ **Important:**
1. `.picoignore` applies to all files in the project root
2. If a `src/` directory exists, it is synced (backward compatibility); otherwise, the project root

## Configuration

### Global settings

File: `~/.config/pico_sync/settings.json`

```json
{
  "language": "ua"
}
```

- **language** — interface language: `"ua"` or `"en"`. Auto-detected: first from file, then from `$LANG` (if `uk*` → `"ua"`, otherwise → `"en"`). Changed via `--lang ua/en`, `LANG=ua`/`LANG=en`, or in interactive mode.

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
- `last_used` — last used date

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

Created via `picosync --init`.

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
4. If nothing found — use `--search_port` for manual selection

The found port is stored in `os.environ["MPREMOTE_PORT"]` — an environment variable that `mpremote` reads. It exists only within the current pico_sync session and is automatically used by all subsequent `mpremote` calls without re-searching. The variable disappears when the program exits.

### Piconame

Optional device name stored in `/.piconame` on Pico. Allows identifying a specific board when multiple Picos are connected.

Management via `--set-name <name>` or in interactive mode.

`.piconame` is automatically excluded from sync.

### Sync filters

Only affect **deletion** of extra files on Pico. All files are uploaded regardless of filter.

| Filter | Description |
|--------|-------------|
| `all` | All files (deletes extras on Pico) |
| `py` | Only `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Everything except `.py` |
| `.ext,.ext2` | Custom comma-separated extensions |

---

## FAQ

### Pico not found / port not detected

Make sure Pico is connected with a USB cable (not just power). If auto-detect fails — use `picosync --search_port` for manual selection.

### Two Picos connected simultaneously

Auto-detect picks the first one found. To work with a specific device — set `.piconame` via `picosync --set-name <name>`.

### Files not syncing

Check `.picoignore` — the file might match an ignore rule. If `src/` exists in root, it is synced; otherwise, the root.

### Error "No module named 'pyserial' / 'mpremote'"

Install dependencies: `pip install pyserial mpremote` (only relevant for portable version).

### How to update Pico Sync?

Check fetches `meta/latest_version.json` from GitHub and compares versions — available via `picosync --check_update`.

- **Via pipx:** `pipx upgrade pico_sync`
- **Via pip:** `pip install --upgrade pico_sync`

### How to get full help?

```bash
picosync --help
picosync project --help     # help for project subcommands
```

---

## License

AGPL-3.0
