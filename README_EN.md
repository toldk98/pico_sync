# Pico Sync

A CLI tool for file synchronization and management on Raspberry Pi Pico / Pico W running MicroPython.

Built on top of `mpremote` — connect your Pico via USB and manage files from the terminal.

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

## Usage

Interactive mode (recommended):

```bash
picosync
```

Or via module:

```bash
python -m pico_sync
```

---

## Features

| Command | Description |
|---------|-------------|
| `--pick` | Interactive mode with project management |
| `--sync` | Synchronize `src/` to Pico |
| `--ls PATH` | List files on Pico |
| `--cat FILE` | Print file contents |
| `--nano FILE` | Edit file via nano |
| `--monitor` | Serial monitor |
| `--search_port` | Interactive port selection |
| `--reboot` | Reboot Pico |
| `--filter` | Sync filter (all, py, py+, nopy, .ext) |
| `--lang {ua,en}` | Interface language |
| `--version` | Show version |
| `--init` | Create .picoignore and meta/ |

## Interactive Mode

`picosync` (no arguments) starts interactive mode with:

- **Project list** — add/remove projects, switch language
- **Project info** — device, port, filter (read-only)
- **File browser** — view, read, edit, delete files on Pico
- **Device** — sync with filter selection, monitor, reboot
- **Settings** — port, src directory, check updates, init

If `fzf` is installed, it is used for menu selection. Falls back to numbered input.

## Project Structure

```
project_root/
├── .picoignore        # ignore rules
├── .picosyncconfig    # project config
├── meta/              # metadata (updates, etc.)
└── src/               # files to sync
```

## Configuration

`.picoignore` — syntax similar to `.gitignore`. Supports `*`, `**`, `?`, `dir/`, `*.ext`.

`.picosyncconfig` — auto-created via `[c] config → init`:
```json
{"port": "/dev/ttyACM0", "filter": "all"}
```

Sync filters:
- `all` — all files (removes extra files on Pico)
- `py` — only .py
- `py+` — .py, .txt, .json
- `nopy` — everything except .py
- custom extensions (comma-separated)

## License

AGPL-3.0
