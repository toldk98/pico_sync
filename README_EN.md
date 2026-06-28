# Pico Sync Tool

**Pico Sync** is a compact CLI tool for working with Raspberry Pi Pico / Pico W running MicroPython.
It provides file synchronization, filesystem browsing, remote file operations, live serial monitoring,
and device reboot.

Built on top of `mpremote`. Supports interactive mode with menus, fzf, and language switching (UA/EN).

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
- `mpremote` — MicroPython remote execution
- `fzf` (optional) — fuzzy finder for menus

---

## Usage

Three ways to run:

```bash
# 1. After pip install
picosync

# 2. As Python module
python -m pico_sync

# 3. As script (legacy)
python pico_sync.py
```

---

## 📁 1. Features

| Feature | Description |
|---|---|
| 🔄 Sync `src/` to Pico | Upload files to the device |
| 🧠 Delta-sync | Only changed files are uploaded (SHA-256) |
| 🗑 Auto-delete | Remove files from Pico not present locally |
| 🧼 Clean empty dirs | After sync |
| ⛔ `.picoignore` | Ignore rules (`.gitignore`-like syntax) |
| 📂 Interactive file browser | View, read, edit, delete files on Pico |
| 🔍 Auto-detect port | Find Pico among serial ports |
| 🔌 Serial monitor | Live log output from Pico |
| 🔁 Reboot | Software reset |
| 🌐 Language | Ukrainian / English |
| 📦 Project management | Save projects with settings |

---

## 📂 2. Project Structure

```
project_root/
│
├── .picoignore           # ignore rules
├── .picosyncconfig       # project configuration (port, filter)
├── meta/                 # metadata (updates, etc.)
│
└── src/                  # files synced to Pico
```

⚠️ **Important:**
1. `.picoignore` only affects files inside `src/`
2. Only `src/` is synced — files outside never reach Pico

---

## 📜 3. .picoignore file

Ignore rules follow `.gitignore` syntax.

**Examples:**

```
# Ignore caches
__pycache__/
*.pyc

# Recursively all .log
**/*.log

# Specific file
config/local_settings.py

# Directory
tests/
```

**Supported patterns:**

| Pattern | Description |
|---------|-------------|
| `*` | Any chars inside a directory |
| `**` | Recursive multi-level match |
| `?` | Single character |
| `dir/` | Entire directory |
| `*.ext` | File mask |

---

## 4. 🔧 Technical Details

### Delta-sync (SHA-256)

1. SHA-256 is computed for each local file
2. Remote SHA-256 checks are batched into a single mpremote call
3. Matching hashes → file is skipped
4. Different hash or missing file → file is uploaded
5. Files on Pico not present locally are deleted
6. Empty directories are cleaned

### Port

Port is auto-detected. On first run:
1. Checks `.picosyncconfig` for saved port
2. If not configured — auto-detects among connected devices
3. Port is stored in `os.environ["MPREMOTE_PORT"]`

### BAUD = 115200

Default serial speed for MicroPython on RP2040.
Used in monitor mode (`--monitor`).

---

## 5. Interactive Mode

Running without arguments (or with `--pick`) starts interactive mode.

### Main Menu

```
..          — back to project list
[i] info    — project info (read-only)
[f] files   — file browser on Pico
[d] device  — sync, monitor, reboot
[c] config  — port, src, updates, init
```

### File Browser

Browse the Pico filesystem tree. File actions:
- `cat` — display contents
- `edit` — edit in system editor
- `rm` — delete
- `[r] refresh` — refresh file list
- `[*] find` — search all files

### Device

- `sync` — sync with filter selection
- `monitor` — serial monitor
- `reboot` — reboot Pico

### Settings

- `port` — select COM port
- `src` — change source directory
- `check_update` — check for updates
- `init` — create `.picoignore`, `meta/`, `.picosyncconfig`

### Language

Use `[~] lang` in the project list to switch language.

### Sync Filters

| Filter | Description |
|--------|-------------|
| `all` | All files (deletes extras on Pico) |
| `py` | Only `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Everything except `.py` |
| `.ext,.ext2` | Custom extensions (comma-separated) |

---

## 6. CLI Reference & Examples

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
  --port PORT           Pico COM port (auto-detect if omitted)
  --src SRC             Source directory (default: src)
  --sync                Sync src → Pico
  --ls PATH             List directory on Pico
  --cat FILE            Print file contents
  --edit FILE           Edit file
  --search_port         Interactive serial port search
  --check_update        Check for updates
  --reboot              Reboot Pico
  --monitor             Serial monitor
  --pick                Interactive mode
  --filter FILTER       Sync filter (default: all)
  --init                Create .picoignore and meta/
  --lang {ua,en}        Interface language
  --version             Show version
```

### Sync

```bash
picosync --sync                          # all files
picosync --sync --filter py              # only .py
picosync --sync --filter .wav,.mpy       # custom extensions
picosync --src my_src --sync             # custom src directory
```

### Browse Files

```bash
picosync --ls /
picosync --ls /spm
picosync --cat /main.py
```

### Edit

```bash
picosync --edit /config/settings.py
```

Downloads the file to a temp file, opens the system editor, uploads back on save.

### Find Port

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
- temporary disconnect

### Reboot

```bash
picosync --reboot
```

Software reset via `mpremote reset`.

### Version

```bash
picosync --version
```

---

## 7. 👤 Quick Start

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

Add your project or select from the list.

### ✔ Step 5. Configure port

`[c] config → port`

### ✔ Step 6. Sync

`[d] device → sync` — choose filter and sync.

### ✔ Step 7. Browse & edit

`[f] files` — view, edit, delete files.

---

## License

AGPL-3.0
