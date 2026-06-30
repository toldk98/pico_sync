# CLI mode — full description

## 1. Launch and general structure

CLI mode — one-shot commands without an interactive menu. Executed in `main()` from `cli.py`.

The argument parser is built in `build_parser()`. `--lang` is extracted BEFORE `build_parser()` to translate the help text.

If no action flag is passed — the interactive mode starts.

---

## 2. `picosync --help` / `-h`

Full output:
```
usage: picosync [-h] [--port PORT] [--sync] [--ls PATH]
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

---

## 3. `picosync --version`

Prints `PICO_SYNC_VERSION` (`"1.1.2"`) and exits. No other actions.

---

## 4. `picosync --sync`

### 4.1 Basic sync

```bash
picosync --sync
```

Algorithm is identical to sync in interactive mode (same `sync_tree()` function):

1. Load `.picoignore` from project root, compile regex
2. Print active ignore patterns and filter (default `all`)
3. `pico_list_files()` — snapshot of all files on Pico
4. Walk local `src/`:
   - Skip ignored directories
   - Skip `.piconame`
   - Skip ignored files
   - Collect `(remote_path, local_path, data)` + `remote_paths`
5. `pico_batch_sha256(remote_paths)` — SHA-256 of all Pico files in one `mpremote exec`
6. For each local file:
   - hash matches → `skip_same` (yellow)
   - not on Pico → `upload_new` (green)
   - different hash → `upload_diff` (green)
   - upload: base64 + `mpremote exec ubinascii.a2b_base64`
7. For each file on Pico without a local match:
   - Skip `/.piconame`
   - `match_filter(filter, path)` — if matches → `delete_file` (red)
8. `delete_empty_dirs()`
9. Print `sync_complete`

### 4.2 With filter

```bash
picosync --sync --filter py         # only .py
picosync --sync --filter .wav,.mpy  # specific extensions
picosync --sync --filter nopy       # everything except .py
```

Filter affects deletion. Values:
- `all` — all files without local match
- `py` — only `.py`
- `py+` — `.py`, `.txt`, `.json`
- `nopy` — everything except `.py`
- `.ext,.ext2` — specific extensions

### 4.3 With port

```bash
picosync --port /dev/ttyACM0 --sync
```

If port not specified — auto-detect.

---

## 5. `picosync --ls PATH`

```bash
picosync --ls /
picosync --ls /spm
```

Calls `pico_ls(path)`.

Algorithm:
1. Function builds Python code to execute on Pico:
```python
import os
p = "{path}"
for f in os.listdir(p):
    fp = p.rstrip('/') + '/' + f
    try:
        s = os.stat(fp)[0]
        if s & 0x4000:
            print('d ' + f)
        else:
            print('- ' + f)
    except:
        pass
```
2. Executes via `mpremote exec`
3. Prints result: `"d <dirname>"` for directories, `"- <filename>"` for files

Supports `--port` for specifying a port.

---

## 6. `picosync --cat FILE`

```bash
picosync --cat /main.py
```

Calls `pico_cat(file_path)`.

Algorithm:
1. `mpremote exec 'print(open("{path}").read())'`
2. Output file content to stdout

Supports `--port`.

---

## 7. `picosync --edit FILE`

```bash
picosync --edit /config/settings.py
```

Calls `pico_edit(file_path)`.

Algorithm:
1. Read file from Pico via `mpremote exec`
2. Write to temp file (suffix `.py`)
3. Find editor:
   - **macOS:** `open -t` (TextEdit)
   - **Linux:** `nano` → `vim` → `vi` (first found)
   - **Windows:** `notepad`
4. If not found:
   - Print `edit_no_editor` with temp file path
   - Pause, delete temp, exit
5. Launch editor as subprocess, wait for completion
6. Read modified file
7. Upload to Pico via `mp_write_file(path, data)` (base64 + mpremote exec)
8. Delete temp file

Supports `--port`.

---

## 8. `picosync --search_port`

```bash
picosync --search_port
```

Calls `interactive_select_port()`.

Algorithm:
1. `list_ports.comports()` — all serial ports on system
2. `find_pico_ports()` — only Pico (VID 0x2E8A or keywords)
3. If no ports — `no_serial_ports`, exit
4. Print numbered list:
   ```
   Available ports:
   0)  /dev/ttyACM0    USB Serial Device  ⭐ (Pico)
   1)  /dev/ttyUSB0    USB2.0-Serial
   ```
   Pico ports marked with `"⭐"`
5. Prompt: `"Select port number (or Enter to cancel): "`
6. Validation:
   - Empty → exit
   - Not a number → `enter_number`
   - Out of range → `invalid_number`
7. On selection:
   - Sets `MPREMOTE_PORT` in environment
   - Print `config_port_set`

---

## 9. `picosync --check_update`

```bash
picosync --check_update
```

Calls `check_for_updates()`.

Algorithm:
1. HTTP GET `https://raw.githubusercontent.com/toldk98/pico_sync/main/meta/latest_version.json` (2s timeout)
2. Parse JSON:
   ```json
   {
     "version": "1.1.2",
     "changelog": "...",
     "url": "https://github.com/..."
   }
   ```
3. Compare with `PICO_SYNC_VERSION` (`"1.1.2"`):
   - **Different:** print:
     - `update_available` (green)
     - `latest_version: X.Y.Z`
     - `current_version: 1.1.2`
     - changelog (if present)
     - `download_url: https://...`
   - **Same:** print `already_latest` (green)
4. Any exception (network error, JSON parse error) — silent skip

---

## 10. `picosync --reboot`

```bash
picosync --reboot
```

1. Print `rebooting` (blue)
2. `subprocess.run(["mpremote", "reset"])`
3. Software reset — equivalent to pressing RUN on the board

Supports `--port`.

---

## 11. `picosync --monitor`

```bash
picosync --monitor
```

Calls `serial_monitor(port)`.

Algorithm:
1. If port not set — `find_pico_port_auto()`
2. If not found — `port_not_found`, exit
3. Print `opening_port` (path + 115200 baud)
4. Print `waiting_data`

**Outer loop (auto-reconnect):**
- `serial.Serial(port, 115200, timeout=0.5)`
- **Inner loop:**
  - `readline()` — read line
  - UTF-8 decode with `replace` for invalid characters
  - Output to stdout in green (`\033[92m`)
  - `sleep(0.05)` if `len(data) == 0`
  - `SerialException` or `OSError` → print `device_disconnected`, exit to outer loop
- On open error: print `pico_not_ready`, `sleep(1)`
- After disconnect: scan for new Pico ports
  - If `new_port != port` → `switching_port`, update `port`

Exit: `Ctrl+C` → `KeyboardInterrupt` → finish

Auto-reconnect on:
- Pico reboot
- USB port change
- Temporary disconnection

Supports `--port`.

---

## 12. `picosync --pick`

```bash
picosync --pick
```

Explicitly launches interactive mode. Detailed in `pick_function.md`.

Fully equivalent to `picosync` without arguments.

---

## 13. `picosync --filter FILTER`

```bash
picosync --sync --filter py
picosync --sync --filter .wav,.mpy
```

Only works in combination with `--sync`. Does nothing on its own.

Values:
- `all` — all files
- `py` — only `.py`
- `py+` — `.py`, `.txt`, `.json`
- `nopy` — everything except `.py`
- `.ext,.ext2` — custom comma-separated extensions (e.g. `.bin,.hex`)

`match_filter(filter, path)` logic:
- `all` → always True
- `py` → path ends with `.py`
- `py+` → path ends with `.py` or `.txt` or `.json`
- `nopy` → True if NOT ending with `.py`
- `.ext,.ext2` → True if ending with any of the listed extensions

---

## 14. `picosync --init`

```bash
picosync --init
```

Calls `init_project(os.getcwd())`.

Creates in current directory:

| File | Content | Condition |
|------|---------|-----------|
| `.picoignore` | Default patterns | If not exists |
| `.picosyncconfig` | `{"port": "", "filter": "all", "piconame": ""}` | If not exists |

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

Print: `created` (green) or `already exists` (yellow) for each item.

---

## 15. `picosync --set-name NAME`

```bash
picosync --set-name my-pico
```

1. Find Pico (auto-detect or `--port`)
2. If not found — `port_not_found`, exit
3. `mpremote exec 'with open("/.piconame", "w") as f: f.write("{name}")'`
4. Save `{"piconame": name}` to `.picosyncconfig` of current project
5. Print `piconame_set`

---

## 16. `picosync --lang {ua,en}`

```bash
picosync --lang ua
picosync --lang en
```

- Extracted BEFORE `build_parser()` (to translate help)
- Calls `set_language(value)`
- Affects all text messages in current run
- Can be combined with any other command

Language priority:
1. `--lang ua/en` (highest)
2. `~/.config/pico_sync/settings.json` → `language`
3. `$LANG` (if `uk*` → `ua`, otherwise → `en`)

---

## 17. `picosync --port PORT`

```bash
picosync --port /dev/ttyACM0 --sync
picosync --port /dev/ttyACM48 --monitor
```

Sets COM port explicitly. Works with any action flag:
- `--sync`
- `--ls`
- `--cat`
- `--edit`
- `--monitor`
- `--reboot`
- `--set-name`
- `--search_port` (sets `MPREMOTE_PORT` in environment)
- `--check_update` (doesn't use port, ignored)

If not set — auto-detect:
1. By `.piconame` from config (if set)
2. By saved `port` from config
3. Auto-detect first Pico
4. Not found → error

---

## 18. `picosync project`

Subcommands for project management.

### 18.1 `picosync project --help`

```
usage: picosync project [-h] {list,add,remove} ...

positional arguments:
  {list,add,remove}
    list      List all saved projects
    add       Add project directory
    remove    Remove project by name

options:
  -h, --help   show this help message and exit
```

### 18.2 `picosync project list`

```bash
picosync project list
```

Output: numbered list of all saved projects:
```
1) my-project  (/home/user/projects/my-project)
2) other-project  (/home/user/other)
```

If no projects — `project_no_projects`.

### 18.3 `picosync project add PATH`

```bash
picosync project add /home/user/my-project
```

1. `os.path.abspath(os.path.expanduser(path))`
2. If directory exists:
   - `add_project(path)` — add/update in `~/.config/pico_sync/projects.json`
   - `project_added`
3. If not exists: `project_not_found`

### 18.4 `picosync project remove NAME`

```bash
picosync project remove my-project
```

1. Find project by `name`
2. If found: `remove_project(name)`, `project_removed`
3. If not found: `project_not_found_remove`

---

## 19. `picosync project preview` (internal, for fzf)

```bash
picosync project preview {line}
picosync project preview-main {item} {root}
```

Used only by the fzf preview panel in interactive mode. Not intended for direct invocation.

### `project preview`

Parses a line from the project selector, extracts `root`, calls `_print_project_preview()`.

### `project preview-main`

Parses item and root from the main menu:
- `..` → `preview_back_projects`
- `[i] info` → `_print_project_preview()` with detailed info
- `[f] files` → `preview_browse_files`
- `[d] device` → `preview_device_menu`
- `[c] config` → `preview_config_menu`

---

## 20. Interaction --port and environment

When using `--port`:
- Sets `os.environ["MPREMOTE_PORT"] = port`
- mpremote automatically uses `MPREMOTE_PORT` for connection
- Subsequent `mpremote` calls in the same session use this port

On auto-detect:
- `find_pico_by_name()` — iterates all Pico, reads `/.piconame`
- `find_pico_port_auto()` — first Pico port
- `ensure_port()` — combines logic: piconame → configured port → auto

---

## 21. Error handling

| Situation | Behavior | Exit code |
|-----------|----------|-----------|
| mpremote not found (`FileNotFoundError`) | Print `mpremote_not_found` | 1 |
| Pico not found | Print `device_not_found` or `port_not_found` | 1 |
| `CalledProcessError` from mpremote | Print error, exit command | 1 |
| Unknown error | Print traceback | 1 |
| `--edit` without editor | Print `edit_no_editor` + temp path | 0 |
| `--cat` file doesn't exist | mpremote error → `CalledProcessError` | 1 |
| `--check_update` network error | Silent skip | 0 |
| `project add` non-existent path | Print `project_not_found` | 0 |
| `project remove` not found | Print `project_not_found_remove` | 0 |
