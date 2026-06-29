# Pico Sync Tool

**Pico Sync** — a compact CLI tool for working with Raspberry Pi Pico / Pico W running MicroPython.
Provides commands for file synchronization, filesystem browsing, basic file operations on the device,
serial monitoring, and device reboot.

Works on top of `mpremote`. Supports interactive mode with menus, fzf, language selection (UA/EN).

---

## Installation

```bash
pip install pico_sync
```

Or from GitHub:

```bash
git clone https://github.com/toldk98/pico_sync.git
cd pico_sync
pip install -r requirements.txt
```

### Dependencies

- Python 3.7+
- `pyserial` — serial port communication
- `mpremote` — running commands on Pico
- `fzf` (optional) — fast search and menus

---

## 1. Purpose

The goal is to make MicroPython development feel as close as possible to working with a local project.

**Features:**

- 🔄 **Sync** — upload files from `src/` to Pico (see [Interactive mode](#6-interactive-mode) or [CLI](#7-cli-reference-and-examples))
- 🧠 **SHA-sync** — only changed files are uploaded (SHA-256)
- 🗑 **Auto-removal** — files on Pico not present locally are deleted
- 🧼 **Empty directory cleanup** — after sync
- ⛔ **`.picoignore`** — ignore rules (like `.gitignore`)
- 📂 **Interactive file browser** — view, read, edit, delete on Pico
- 🔍 **Auto-detect port** — search for Pico among serial ports
- 🔌 **Serial monitor** — live log output from Pico
- 🔁 **Reboot** — software reset
- 🌐 **Language** — Ukrainian / English
- 📦 **Project management** — save projects with settings

The tool is ~246 KB, split into modules for maintainability and testing. Unneeded modules can be removed if desired.

---

## 2. Usage

The tool can be run in different modes:

```bash
# Interactive mode (menus, browser, sync) — [section 6](#6-interactive-mode)
picosync

# CLI mode (one-shot commands) — [section 7](#7-cli-reference-and-examples)
picosync --sync
picosync --ls /main.py
picosync --monitor

# As a Python module
python -m pico_sync
```

---

## 3. Project structure

```
project_root/
│
├── .picoignore           # ignore rules
├── .picosyncconfig       # project config (port, filter)
├── meta/                 # metadata (updates, etc.)
│
└── src/                  # files synced to Pico
```

⚠️ **Important:**
1. `.picoignore` only affects files inside `src/`
2. Only `src/` is synced — files outside never reach Pico

---

## 4. The .picoignore file

Ignore rules follow a syntax similar to `.gitignore`.

**Examples:**

```
# Ignore caches
__pycache__/
*.pyc

# Recursively ignore all .log files
**/*.log

# Specific file
config/local_settings.py

# Directory
tests/
```

**Supported patterns:**

| Pattern | Description |
|---------|-------------|
| `*` | Any characters within a directory |
| `**` | Recursive multi-level match |
| `?` | Single character |
| `dir/` | Entire directory |
| `*.ext` | File mask |

---

## 5. Technical details

### SHA-sync

1. Each local file gets its SHA-256 calculated
2. Pico computes SHA-256 of all remote files via a single mpremote exec
3. If hashes match → file is skipped
4. If hashes differ or file is missing → file is uploaded
5. Files on Pico not present locally are deleted
6. Empty directories are removed

### Port

Port detection order:
1. If `piconame` is configured in `.picosyncconfig` — find Pico whose `/.piconame` matches
2. Value from `.picosyncconfig` `port` field (if set)
3. Auto-detect: scan serial devices by USB VID. If multiple Picos found — the first one is used
4. If nothing found — a message about missing port is shown

The port is stored in `os.environ["MPREMOTE_PORT"]`.

#### .piconame

`/.piconame` is an optional text file identifier on the Pico itself.
It can be created manually or via `picosync --set-name my-device`. When `piconame` is set in the project config, pico_sync will find the exact Pico with the matching name, even when multiple devices are connected.

### BAUD = 115200

Standard MicroPython serial speed on RP2040.
Used in monitor mode (`--monitor`).

---

## 6. Interactive mode

Without arguments (or with `--pick`) the interactive mode starts.

On first launch you will see a list of saved projects. If no projects exist yet — a prompt to add the current directory. After selecting a project (or adding a new one), you enter the project's main menu.

### Main menu

```
..          — back to project list
[i] info    — project info (read-only)
[f] files   — Pico file browser
[d] device  — sync, monitor, reboot
[c] config  — port, src, update settings, init
```

### File browser

Browse the Pico file tree. Actions per file:
- `cat` — print contents
- `edit` — edit in system editor
- `rm` — delete
- `[r] refresh` — refresh file list
- `[*] find` — search all files

### Device

- `sync` — sync with filter selection
- `monitor` — serial monitor
- `reboot` — reboot Pico

### Config

- `port_settings` — Pico connection settings: manual port selection or auto-find by device name
- `check_update` — check for updates
- `init` — create `.picoignore`, `meta/`, `.picosyncconfig`

### Language

`[~] lang` in the project list switches language.

### Sync filters

| Filter | Description |
|--------|-------------|
| `all` | All files (removes extras on Pico) |
| `py` | Only `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Everything except `.py` |
| `.ext,.ext2` | Custom comma-separated extensions |

### Example session

```
$ picosync

  [1] my-project  (/home/user/projects/my-project)
  [+] add project
  [~] lang

> 1                         # select project

  ..  — back to project list
  [i] info    — project information
  [f] files   — Pico file browser
  [d] device  — sync, monitor, reboot
  [c] config  — settings

> d                         # device menu

  sync
  monitor
  reboot

> sync                      # sync files
  filter (all):
  Files: 12, synced: 3, skipped: 9
```

---

## 7. CLI reference and examples

### Help

```bash
picosync --help
```

```
usage: picosync [-h] [--port PORT] [--src SRC] [--sync] [--ls PATH]
                [--cat FILE] [--edit FILE] [--search_port] [--check_update]
                [--reboot] [--monitor] [--pick] [--filter FILTER] [--init]
                [--lang {ua,en}] [--version]
                {project} ...

Pico Sync Tool — sync/ls/cat/edit for Raspberry Pi Pico

options:
  -h, --help            Show help
  --port PORT           Pico COM port (auto-detect if not set)
  --src SRC             Sync directory (default: src)
  --sync                Sync src → Pico
  --ls PATH             List files in a Pico directory
  --cat FILE            Print file contents
  --edit FILE           Edit a remote file
  --search_port         Interactive serial port search
  --check_update        Check for updates
  --reboot              Reboot Pico
  --monitor             Serial monitor
  --pick                Interactive mode
  --filter FILTER       Sync filter (default: all)
  --init                Create .picoignore and meta/
  --set-name NAME       Write /.piconame to Pico and save to config
  --lang {ua,en}        Interface language
  --version             Version
```

### Sync

```bash
picosync --sync                          # all files
picosync --sync --filter py              # .py only
picosync --sync --filter .wav,.mpy       # custom extensions
picosync --src my_src --sync             # custom src
```

### File listing

```bash
picosync --ls /
picosync --ls /spm
picosync --cat /main.py
```

### Editing

```bash
picosync --edit /config/settings.py
```

The file is downloaded to a temp file, opened in an editor, and uploaded back on save.

### Port search

```bash
picosync --search_port
```

### Monitor

```bash
picosync --monitor
```

Auto-reconnects on:
- Pico reboot
- USB port change
- temporary disconnection

### Reboot

```bash
picosync --reboot
```

Software reset via `mpremote reset` — equivalent to pressing RUN.

### Version

```bash
picosync --version
```

---

## 8. Project system

Projects are stored in `~/.config/pico_sync/projects.json`.
Each project stores its path, port setting, sync filter, and last used src.

### Managing projects

```bash
picosync project list          # list projects
picosync project add /path     # add an existing directory
picosync project remove name   # remove project from list
```

In interactive mode, projects are shown on the start screen.
`[+] add project` adds the current directory, `[~] lang` switches language.

---

## 9. User guide

### ✔ Step 1. Install

```bash
pip install pico_sync
```

### ✔ Step 2. Prepare project

```
project/
├── .picoignore
└── src/
    └── main.py
```

### ✔ Step 3. Connect Pico via USB

### ✔ Step 4. Run

```bash
picosync
```

The project list will appear. If no projects exist yet — a prompt to add the current directory.
Select a project or add a new one — you enter the main menu.

### ✔ Step 5. Configure port (optional)

Pico_sync automatically detects Pico among serial ports. If only one device is connected — no configuration needed.

If auto-detect fails or multiple Picos are connected — `[c] config → port` for manual selection.

### ✔ Step 6. Sync

`[d] device → sync` — select a filter and sync.

### ✔ Step 7. Work with files

`[f] files` — browse, edit, delete.

---

## 10. FAQ

### Pico not found / port not detected
Make sure Pico is connected via USB data cable (power-only cables won't work). If auto-detect fails — use `picosync --search_port` for manual selection.

### Two Picos connected at once
Auto-detect picks the first one found. To work with a specific device — configure `.piconame` via `picosync --set-name <name>` or `[c] config → piconame → set`.

### Files not syncing / not all files on Pico
Check `.picoignore` — the file might match an ignore rule. By default the `src/` directory is synced.

### Error "No module named 'pyserial' / 'mpremote'"
Install dependencies: `pip install pyserial mpremote`

### How to update Pico Sync?
```bash
pip install --upgrade pico_sync
```
Or `[c] config → check_update` in interactive mode.

---

## License

AGPL-3.0
