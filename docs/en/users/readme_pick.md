# Pico Sync Tool — Interactive mode

**Pico Sync** — a compact CLI tool for working with Raspberry Pi Pico / Pico W running MicroPython.
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
- 📂 **Interactive file browser** — view, read, edit, delete on Pico
- 🔍 **Auto-detect port** — find Pico among serial ports and by name
- 🔌 **Serial monitor** — live log viewer from Pico
- 🔁 **Reboot** — software board reset
- 🌐 **Interface language** — Ukrainian / English
- 📦 **Project management** — save projects with settings

The tool takes <1 MB, split into modules for easier maintenance and testing.

🌐 [Українська версія](../ua/users/readme_pick.md)

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

---

## Usage

### Launch

Interactive mode starts with no arguments:

```bash
picosync
```

Or explicitly with `--pick`:

```bash
picosync --pick
```

**As a Python module:**

```bash
python -m pico_sync
```

### Menu navigation

The menu works in two modes depending on `fzf` availability:

**With fzf:** full-screen list with search (type to filter), navigation `↑↓`, select `Enter`, cancel `Esc`. Preview panel on the right with additional info about the selected item.

**Without fzf:** numbered list. Enter the item number and press `Enter`. Empty input = cancel.

### Start screen — project selection

On launch, a list of saved projects is displayed:

```
<project_name>  (<project_root>)
...
[+] add project
[-] remove project
[s] settings
[q] quit
```

**Select project** — enter the project's main menu.

**`[+] add project`** — enter the project directory path (or Enter for current directory). The project is added to `~/.config/pico_sync/projects.json`.

**`[-] remove project`** — select a project from the list to remove.

**`[s] settings`** — global program settings (see below).

**`[q] quit`** — exit the program.

### Global settings (`[s] settings`)

```
..              -> back
[~] lang        -> language selection
[!] check update -> check for updates
```

**`[~] lang`** — switch interface language:
- `ua` — Ukrainian
- `en` — English

Saved in `~/.config/pico_sync/settings.json`. Language can also be set via `LANG=ua` / `LANG=en` environment variable or `--lang ua` / `--lang en` flag.

**`[!] check update`** — fetches `meta/latest_version.json` from GitHub (`toldk98/pico_sync`), compares version with current. If a newer version is available, shows version, changelog, links to PyPI and GitHub, and the `pip install --upgrade pico_sync` command.

### Project main menu

After selecting a project, the main menu opens:

```
..          -> back to project list
[i] info    -> project info
[f] files   -> file browser on Pico
[d] device  -> sync, monitor, reboot
[c] config  -> port settings, baud, piconame, init
```

#### `[i] info` — project information

Shows:
- Project name and root directory
- Sync source (src/ or root)
- Configured device (port or piconame) and its status (⚡ connected / ✘ not found)
- List of all found Pico devices
- Current sync filter

Read-only mode: press Enter to go back.

#### `[f] files` — file browser

Opens an interactive browser of the Pico file system. On first entry, checks device connection.

```
..              -> go up one level
[r] refresh     -> refresh list (root only)
[*] find        -> search all files
d <dirname>/    -> enter directory
- <filename>    -> file actions
```

**Navigation:** `..` exits the current directory. `/` in fzf activates search.

**`[*] find`** — shows all files on Pico as a flat list. Selecting a file opens the context menu.

**File context menu:**

```
..     -> back
cat    -> display file content
edit   -> edit file
rm     -> delete file
```

- **cat** — outputs file content to terminal
- **edit** — downloads file to a temp file, opens system editor (nano/vim/vi on Linux, TextEdit on macOS, notepad on Windows). After saving, automatically uploads the modified version back to Pico
- **rm** — asks for confirmation (`y/N`), then deletes the file from Pico

#### `[d] device` — device menu

```
..       -> back
sync     -> synchronization
monitor  -> serial monitor
reboot   -> reboot Pico
```

##### sync — synchronization

**Step 1: Filter selection**

```
all       -> all files (deletes extra files on Pico)
py        -> only .py
py+       -> .py, .txt, .json
nopy      -> everything except .py
custom    -> custom extensions (comma-separated)
```

**Step 2: Execution**

Sync algorithm:

1. Loads `.picoignore` from project root
2. Takes a snapshot of all files on Pico
3. Walks the local directory (src/ or root), collects files for sync (skips ignored and `.piconame`)
4. Runs SHA-256 on all Pico files in one request
5. Compares hashes: match → skip, missing on Pico → upload, different hash → update
6. Deletes files on Pico that don't exist locally (respecting filter)
7. Cleans empty directories on Pico

##### monitor — serial monitor

Opens a live log viewer from Pico (115200 baud). Auto-reconnects on:
- Pico reboot
- USB port change
- temporary disconnection

Exit: `Ctrl+C`.

##### reboot — reboot

Performs a software reset of Pico via `mpremote reset`.

#### `[c] config` — project settings menu

```
..              -> back
port_settings   -> Pico connection settings
baud            -> port speed
init            -> create .picoignore, .picosyncconfig
```

##### port_settings — port and piconame

```
..         -> back
port       -> manual COM port selection
piconame   -> auto-search by device name
```

**port** — shows a list of all serial ports (Pico marked with ⭐). Select a port number. Saved to project config.

**piconame** — device name management:

- **detect** — read `/.piconame` from connected Pico and save to config
- **set** — write a new name to Pico and save to config
- **clear** — remove `/.piconame` from Pico and clear config

##### baud — port speed

Shows a list of common values (9600, 19200, 38400, 57600, 115200, 230400, 921600) + custom. Selection is saved in `.picosyncconfig` and used when opening the monitor. Default: 115200.

##### init — project initialization

Creates in project root:
- `.picoignore` — default ignore patterns (if not exists)
- `.picosyncconfig` — project config file (if not exists)

### Example session

```
$ picosync

  [1] my-project  (/home/user/projects/my-project)
  [+] add project
  [s] settings

> 1                         # selected project

  ..  — back to project list
  [i] info    — project info
  [f] files   — file browser on Pico
  [d] device  — sync, monitor, reboot
  [c] config  — settings

> d                         # device menu

  sync
  monitor
  reboot

> sync                      # synchronization
  filter (all):
  Files: 12, synced: 3, skipped: 9
```

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

- **language** — interface language: `"ua"` or `"en"`. Auto-detected: first from file, then from `$LANG` (if `uk*` → `"ua"`, otherwise → `"en"`). Changed via `[s] settings → [~] lang`, `--lang ua/en`, or `LANG=ua`/`LANG=en`.

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

Projects are sorted by `last_used` descending in the start menu.

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

Created via `[c] config → init`.

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

Default `.picoignore` on init:
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
4. If nothing found — suggests `port` in settings for manual selection

The found port is stored in `os.environ["MPREMOTE_PORT"]` — an environment variable that `mpremote` reads. It exists only within the current pico_sync session and is automatically used by all subsequent `mpremote` calls without re-searching. The variable disappears when the program exits.

### Piconame

Optional device name stored in `/.piconame` on the Pico itself. Allows identifying a specific board when multiple Picos are connected.

Management:
- **detect** — read `/.piconame` from connected Pico and save to config
- **set** — write a new name to Pico and save to config
- **clear** — remove `/.piconame` from Pico and clear config

`.piconame` is automatically excluded from sync (not deleted, not uploaded).

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

Make sure Pico is connected with a USB cable (not just power). If auto-detect fails — use `[c] config → port_settings → port` for manual selection.

### Two Picos connected simultaneously

Auto-detect picks the first one found. To work with a specific device — set `.piconame` via `[c] config → port_settings → piconame → set`.

### How to install fzf?

`fzf` is an optional tool for convenient menu navigation in interactive mode. Without it, numbered input works.

- **Linux:** `sudo apt install fzf` (or your package manager — `pacman -S fzf`, `dnf install fzf`)
- **macOS:** `brew install fzf`
- **Windows:** download binary from https://github.com/junegunn/fzf/releases

### Files not syncing

Check `.picoignore` — the file might match an ignore rule. If `src/` exists in root, it is synced; otherwise, the root.

### Error "No module named 'pyserial' / 'mpremote'"

Install dependencies: `pip install pyserial mpremote` (only relevant for portable version).

### How to update Pico Sync?

Check fetches `meta/latest_version.json` from GitHub and compares versions — available via `[s] settings → [!] check update`.

- **Via pipx:** `pipx upgrade pico_sync`
- **Via pip:** `pip install --upgrade pico_sync`

---

## License

AGPL-3.0
