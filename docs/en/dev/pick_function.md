# Pick (interactive mode) — full description

## 1. Launch

Interactive mode is started by:
- `picosync` — without arguments
- `picosync --pick` — explicit launch
- `picosync --lang ua` — only language, no other action flags
- Also when none of the action flags (`--sync`, `--ls`, `--cat`, `--edit`, `--search_port`, `--check_update`, `--reboot`, `--monitor`) are passed

On launch, `_run_interactive(args)` is called, entering an infinite loop:
```
while True:
    project, action = _pick_project_or_action()
    if action == "quit": exit(0)
    if project:
        projects.touch_project(project["root"])  # updates last_used
        root = project["root"]
    else:
        root = os.getcwd()
        projects.add_project(root)
    pick_mode(root, project=project)
```

After exiting `pick_mode()` (user selected `..`), the loop repeats — showing the project list again.

### 1.1 General menu operation (fzf vs numbered fallback)

Each menu in interactive mode goes through `_fzf_pick()` or `_uinput_pick()`.

**If fzf is installed** (`shutil.which("fzf") is not None`):
- List items passed via stdin (newline-separated)
- fzf launched with `--border`, `--prompt="> "`, `--header="..."`, `--preview` and `--preview-window right:50%:border`
- User can filter the list by typing — fzf shows only matches
- Navigation: `↑↓` or `Ctrl+N/Ctrl+P`
- Selection: `Enter` → selected line to stdout, return code 0
- Cancel: `Esc` or `Ctrl+C` → empty stdout, return code 1 → interpreted as `None` (cancel)
- If fzf crashes (e.g. wrong version) — automatic fallback to numbered

**If fzf is not installed (numbered fallback):**
- Items printed as numbered list to stdout: `0) item1`, `1) item2`, ...
- Header printed above the list as plain text
- Input via `_uinput()`:
  - Empty line → `None` (cancel)
  - Not a number → retry prompt
  - Number out of range → `invalid_number`, retry
  - Valid number → returns corresponding item

---

## 2. Start screen — project selection

Function `_pick_project_or_action()`.

### 2.1 Display

Item list:
```
<project_name>  (<project_root>)    — each saved project
[+] add project                      — add new project
[-] remove project                   — remove project
[s] settings                         — global settings
[q] quit                             — exit
```

**Interface (fzf):** full-screen list with header `" Esc=back  /=search   Select project"`. Preview panel on the right calls `pico_sync project preview {line}` — shows project info under cursor or description of special items. `/` activates fuzzy search. `Esc` or `Ctrl+C` → cancel (equivalent to `[q] quit`).

**Interface (without fzf):** numbered list, header printed separately. Enter number to select, Enter with no input = cancel.

Projects sorted by `last_used` (newest first). If no projects — only `[+] add project` and `[q] quit` shown.

### 2.2 Item: select project

- User selects a project line
- Returns `(project_dict, "select")`
- Then `_run_interactive` calls `pick_mode(root, project=project)`

### 2.3 Item: `[+] add project`

1. Prompt: `"Path to project root (Enter — current directory): "`
2. Read input via `_uinput()` — protection against `UnicodeDecodeError`
3. If empty — use `os.getcwd()`
4. `os.path.abspath(os.path.expanduser(path))`
5. If path is an existing directory:
   - Calls `projects.add_project(path)` — adds/updates in `~/.config/pico_sync/projects.json`
   - Print `project_added`
6. If not a directory: print `project_not_found`
7. Return to project list

### 2.4 Item: `[-] remove project`

1. If no projects — print `project_no_projects`, return
2. Shows sub-menu with project list + `..` at end.
   **Interface (fzf):** header `" Esc=back  /=search"`, preview same as main selector.
   **Interface (without fzf):** numbered list.
3. If `..` or cancel (Esc/empty input) selected — return
4. If a project is selected:
   - Calls `projects.remove_project(name)`
   - Print `project_removed` or `project_not_found_remove`
5. Return to project list

### 2.5 Item: `[s] settings` — global settings

Sub-menu:
```
..              -> back to project list
[~] lang        -> language selection
[!] check update -> check for updates
```

**Interface (fzf):** header, preview panel shows item description.
**Interface (without fzf):** numbered list.
Cancel (Esc/empty input) → back to project list.

### 2.5.1 `[~] lang`

Sub-menu:
```
..   -> back
ua   -> Ukrainian
en   -> English
```

**Interface (fzf):** header, preview shows current language.
**Interface (without fzf):** numbered list.
Cancel → back to settings.

- Selecting `ua` or `en`:
  - Calls `set_language(code)` — updates `lang.py` and saves to `~/.config/pico_sync/settings.json`
  - Print `lang_set`
  - Pause `press_enter`
  - Return to settings menu

### 2.5.2 `[!] check update`

- Calls `check_for_updates()`
- Pause `press_enter`
- Return to settings menu

Details:
1. Fetch `https://raw.githubusercontent.com/toldk98/pico_sync/main/meta/latest_version.json` (2s timeout)
2. Parse JSON: `version`, `changelog`, `url`
3. Compare with `PICO_SYNC_VERSION` (`"1.1.2"`):
   - Different: print `update_available`, `latest_version`, `current_version`, changelog, url
   - Same: print `already_latest`
4. Any error — silent skip

### 2.6 Item: `[q] quit`

- Returns `(None, "quit")`
- `_run_interactive` calls `exit(0)`

---

## 3. Project main menu

Function `pick_mode(root, project=None)`.

### 3.1 Display

```
..          -> back to project list
[i] info    -> project info (read-only)
[f] files   -> file browser on Pico
[d] device  -> sync, monitor, reboot
[c] config  -> port settings, src, piconame, init
```

**Interface (fzf):** header `" Esc=back  /=search"`. Preview panel calls `pico_sync project preview-main {item} {p_root}`:
- `..` → `preview_back_projects`
- `[i] info` → full project info
- `[f] files` → `preview_browse_files`
- `[d] device` → `preview_device_menu`
- `[c] config` → `preview_config_menu`

**Interface (without fzf):** numbered list, header printed as text. Cancel (empty input) → back to project list.

### 3.2 Item: `..`

- Exit `pick_mode()`, return to project list

### 3.3 Item: `[i] info` — project info

Function `_show_project_info()`.

Collects and displays:
1. **Project name** and **root directory**
3. **Configured device**: if `piconame` is set — `find_pico_by_name(piconame)`; otherwise `port` from config or `"not set"`
4. **Found devices**: `find_pico_ports()` — list of all connected Picos
5. **Status icon**: `"⚡"` if configured device is found, otherwise `"✘"`
6. **Status**: `"connected"` or `"not found"`
7. **Current filter**: `filter_description(current_filter)`
8. If `piconame` is set but device not found — yellow warning `info_piconame_not_found`
9. List of all found Pico ports with `"⚡"` marker; configured one marked with `" (configured)"`

Ends with `"Press Enter to go back"`. Read Enter, return to main menu.

### 3.4 Item: `[f] files` — file browser

1. Call `ensure_port(port, piconame=piconame)`
2. If port not found — print `device_not_found`, pause, return to main menu
3. If `files_cache is None` — load file list via `pico_list_files()`
4. Call `_pick_files_menu(files_cache)` → `_pick_ls_browser()`

#### 3.4.1 Browser display

```
..              -> go up one level
[r] refresh     -> refresh list (root only "/")
[*] find        -> search (all files as flat list)
d <dirname>/    -> enter directory
- <filename>    -> file actions
```

**Interface (fzf):** header `" Esc=back  /=search"`, preview panel shows file content or directory listing.
**Interface (without fzf):** numbered list.
Cancel → up one level or exit browser.

#### 3.4.2 `..` — exit or go up
- If not in root — go to parent directory
- If in root — exit browser

#### 3.4.3 `[r] refresh` — refresh
- Returns `"refresh"` signal
- Outer loop reloads all files, rebuilds tree, re-enters

#### 3.4.4 `[*] find` — search
- Shows flat sorted list of all files on Pico (prefix `..` at top)
- **Interface (fzf):** header `" Esc=back  /=search   All files on Pico"`, preview shows file content under cursor
- **Interface (without fzf):** numbered list
- Select file → file context menu
- Select `..` or cancel → return to browser

#### 3.4.5 `d <dirname>/` — enter directory
- Recursive entry into `_browse(node[dir_name], sub_path)`
- If recursion returns `"refresh"` — propagate upward

#### 3.4.6 `- <filename>` — file context menu

Sub-menu:
```
..     -> back to file list
cat    -> view content
edit   -> edit
rm     -> delete
```

**Interface (fzf):** header `" Esc=back  /=search   File actions"`, preview short action description.
**Interface (without fzf):** numbered list.
Cancel → back to file list.

##### cat
- Call `pico_cat(file_path)` — `mpremote exec 'print(open("{path}").read())'`
- Print content
- Pause `press_enter`

##### edit
- Call `pico_edit(file_path)`
- Algorithm:
  1. Read file from Pico via `mpremote exec`
  2. Write to temp file (suffix `.py`)
  3. Find editor:
     - macOS: `open -t`
     - Linux: `nano` → `vim` → `vi`
     - Windows: `notepad`
  4. If no editor found — print `edit_no_editor` with temp file path, pause, delete, exit
  5. Launch editor, wait for close
  6. Read modified file
  7. Upload to Pico via `mp_write_file(path, data)`
  8. Delete temp file
- Return to context menu

##### rm
- Prompt: `"Delete {name}? (y/N): "`
- If `"y"` (lowercase):
  - `mpremote exec 'import os; os.remove("{path}")'`
  - Print `deleted_ok`
  - Remove from tree (if not in find mode)
  - Exit to parent directory

### 3.5 Item: `[d] device` — device menu

Function `_pick_device_menu(port, piconame=None)`.

1. Call `ensure_port(port, piconame=piconame)` on entry
2. If port not found — print `device_not_found`, return `(port, False)`
3. Read `current_filter` from config

Display:
```
..       -> back
sync     -> synchronization
monitor  -> serial monitor
reboot   -> reboot
```

**Interface (fzf):** header, preview describes each action.
**Interface (without fzf):** numbered list.
Cancel → save filter, return to main menu.

#### 3.5.1 `..` — back
- Save `{"filter": current_filter}` to config
- Return `(port, needs_refresh)`

#### 3.5.2 `sync` — synchronization

**Step 1: Filter selection**

Sub-menu:
```
all       -> all files (deletes extras on Pico)
py        -> only .py
py+       -> .py, .txt, .json
nopy      -> everything except .py
custom    -> custom extensions (comma-separated)
```

**Interface (fzf):** header `" Current filter: {filter}"`, preview describes filter.
**Interface (without fzf):** numbered list with current filter in header.
Cancel → back to device menu.

- Cancel → back to device menu
- `custom` → prompt `"Extensions (comma-sep, e.g. .py,.txt): "`, empty = `"all"`
- Save `current_filter` to config

**Step 2: Execute sync_tree**

1. Load `.picoignore` from project root, compile regex
2. Print active ignore patterns and filter
3. `pico_list_files()` — snapshot of all files on Pico
4. Walk local directory `root` (auto-detect `src/` if exists):
   - Skip directories matching ignore
   - Skip `.piconame` files
   - Skip files matching ignore (`skip_ignored`)
   - Collect `(remote_path, local_path, data)` for all files
   - Collect all `remote_paths` for SHA-256
5. `pico_batch_sha256(remote_paths)` — one `mpremote exec` computes SHA-256 of all files at once
6. For each local file:
   - `local_hash == remote_hash` → `skip_same` (yellow)
   - `remote_hash is None` → `upload_new` (green)
   - `remote_hash != local_hash` → `upload_diff` (green)
   - Upload via `mp_write_file(remote, data)` — base64 + mpremote exec with auto-directory creation
7. For each file on Pico without a local match:
   - Skip `/.piconame`
   - Check `match_filter(filter, remote_file)`
   - If matches — `delete_file` (red), delete via `mpremote exec os.remove`
8. `delete_empty_dirs()` — remove empty directories on Pico
9. Print `sync_complete`
10. `needs_refresh = True`
11. Pause `press_enter`

#### 3.5.3 `monitor` — serial monitor

Function `serial_monitor(port)`:

1. If port not set — `find_pico_port_auto()`
2. If still none — print `port_not_found`, exit
3. Print `opening_port` with port and BAUD (115200)
4. Print `waiting_data`

**Outer loop (auto-reconnect):**
- Try `serial.Serial(port, BAUD, timeout=0.5)`
- **Inner loop:**
  - `readline()` — read lines
  - UTF-8 decode, print in green
  - `sleep(0.05)` if no data
  - `SerialException` or `OSError` → print `device_disconnected`, exit to outer loop
- On open error → print `pico_not_ready`, `sleep(1)`
- After disconnect: check if a new Pico port appeared
  - If `new_port != port` → print `switching_port`, update `port`, reconnect

Exit: `Ctrl+C` → `KeyboardInterrupt` → return to device menu

#### 3.5.4 `reboot` — reboot

- Print `rebooting` in blue
- `subprocess.run(["mpremote", "reset"])`
- `needs_refresh = True`
- Return to device menu (no pause)

### 3.6 Item: `[c] config` — settings menu

Function `_pick_config_menu(port)`.

Display:
```
..              -> back to main menu
port_settings   -> Pico connection settings
init            -> create .picoignore, .picosyncconfig
```

**Interface (fzf):** header, preview describes action.
**Interface (without fzf):** numbered list.
Cancel → return to main menu.

#### 3.6.1 `..` — back
- Return `port`

#### 3.6.2 `port_settings` — port and piconame

Function `_pick_port_settings_menu(port)`.

Display:
```
..         -> back to config
port       -> manual COM port selection
piconame   -> auto-search by device name (.piconame)
```

**Interface (fzf):** header, preview.
**Interface (without fzf):** numbered list.
Cancel → back to config.

##### `port` — manual port selection

1. Call `interactive_select_port()`:
   - Get all serial ports via `list_ports.comports()`
   - Get Pico ports via `find_pico_ports()`
   - If no ports — print `no_serial_ports`
   - Print: `available_ports` + numbered list with `"⭐"` for Pico
   - Prompt: `"Select port number (or Enter to cancel): "`
   - Validation: empty → `None`, not a digit → `enter_number`, out of range → `invalid_number`
2. If port selected:
   - `port = chosen`
   - `os.environ["MPREMOTE_PORT"] = port`
   - Save `{"port": port}` to `.picosyncconfig`
   - Print `config_port_set` in green
3. Pause `press_enter`

##### `piconame` — device name management

Shows current name (or `"Name not set"`).

Sub-menu:
```
..       -> back
detect   -> read /.piconame from Pico and save to config
set      -> write new name to Pico and save
clear    -> delete /.piconame from Pico and clear config
```

**Interface (fzf):** header shows `"Current name: {name}"`, preview.
**Interface (without fzf):** header printed as text, numbered list.
Cancel → back to port settings.

**detect:**
1. `ensure_port(config.get("port"))`. If fails — `find_pico_port_auto()`
2. If port not found — print `port_not_found`, pause, exit
3. `os.environ["MPREMOTE_PORT"] = p`
4. `_read_piconame_from_port(p)` — `mpremote exec 'import os; print(open("/.piconame").read().strip())'`
5. If name found — save `{"piconame": name}` to config, print `piconame_detected` in green
6. If not found — print `piconame_not_on_pico` in yellow
7. Pause `press_enter`

**set:**
1. Prompt: `"New name for Pico: "`
2. If not empty:
   - `ensure_port(config.get("port"))`, on failure — `find_pico_port_auto()`
   - If port not found — print `port_not_found`, pause, exit
   - `os.environ["MPREMOTE_PORT"] = p`
   - `mpremote exec 'with open("/.piconame", "w") as f: f.write("{name}")'`
   - Save `{"piconame": new_name}` to config
   - Print `piconame_set` in green
3. Pause `press_enter`

**clear:**
1. `ensure_port(config.get("port"))`, on failure — `find_pico_port_auto()`
2. If port found:
   - `os.environ["MPREMOTE_PORT"] = p`
   - `mpremote exec 'import os; os.remove("/.piconame")'`
3. Save `{"piconame": ""}` to config
4. Print `piconame_cleared` in green
5. Pause `press_enter`

#### 3.6.3 `init` — project initialization

Function `init_project(project_root)`.

Creates in project root:

| File | Content | Condition |
|------|---------|-----------|
| `.picoignore` | Default patterns | Only if not exists |
| `.picosyncconfig` | `{"port": "", "filter": "all", "piconame": ""}` | Only if not exists |

For each file/directory print `created` (green) or `already exists` (yellow).

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

Pause `press_enter`.

---

## 4. Pico file system

### 4.1 `pico_list_files()`

Recursive walk of all files on Pico via one `mpremote exec`:
```python
import os
res = []
def walk(p):
    for f in os.listdir(p):
        fp = p + '/' + f if p != '/' else '/' + f
        try:
            st = os.stat(fp)[0]
            if st & 0x4000:
                walk(fp)
            else:
                res.append(fp)
        except:
            pass
walk('/')
print('\n'.join(res))
```
Returns sorted list of paths.

### 4.2 `pico_ls(path)`

List single directory. Prefix `"d "` for directories, `"- "` for files.

### 4.3 `pico_cat(path)`

`mpremote exec 'print(open("{path}").read())'` — output file content.

### 4.4 `pico_batch_sha256(paths)`

One `mpremote exec` for all paths:
```python
import ubinascii, uhashlib
paths = [...]
for p in paths:
    try:
        h = uhashlib.sha256()
        f = open(p, 'rb')
        while True:
            b = f.read(2048)
            if not b: break
            h.update(b)
        f.close()
        print('OK', ubinascii.hexlify(h.digest()).decode(), p)
    except OSError:
        print('--', p)
```
Returns `{path: sha256_hex}` or `{path: None}` for missing files.

### 4.5 `mp_write_file(remote_path, data)`

1. Auto-create parent directories via `os.mkdir`
2. Base64-encode data
3. `mpremote exec 'ubinascii.a2b_base64(b"...")'` with same directory structure

### 4.6 `delete_empty_dirs()`

Recursive walk on Pico, remove empty directories. Print `"RMDIR <path>"` for each.

---

## 5. Ports

### 5.1 `is_pico_port(port)`

Returns True if:
- `port.vid == 0x2E8A` (Raspberry Pi)
- Or any of `("Pico", "RP2", "MicroPython", "USB Serial Device")` in `description + " " + product`

### 5.2 `find_pico_ports()`

Returns list of all COM ports satisfying `is_pico_port()`.

### 5.3 `find_pico_port_auto()`

Returns `device` of first Pico port or `None`.

### 5.4 `find_pico_by_name(name)`

Iterates all Pico ports, on each executes `mpremote exec 'import os; print(open("/.piconame").read().strip())'` and compares with name. Returns device path of first match or `None`.

### 5.5 `ensure_port(port, piconame=None)`

1. If `piconame` is set — `find_pico_by_name(piconame)`. If found — set `MPREMOTE_PORT` and return
2. If `port` is set (not None) — return as-is
3. Otherwise — `find_pico_port_auto()`. If found — set `MPREMOTE_PORT` and return

### 5.6 `interactive_select_port()`

1. `list_ports.comports()` — all serial ports
2. `find_pico_ports()` — only Pico
3. If no ports — `no_serial_ports`, return `None`
4. Print numbered list, Pico marked with `"⭐"`
5. Input number, validate
6. Return `ports[idx].device` or `None`

---

## 6. Projects

Stored in `~/.config/pico_sync/projects.json`:
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

- `name` — basename of root directory
- `root` — absolute path
- `last_used` — ISO 8601, updated on each `touch_project`

Sorting in selector: by `last_used` descending.

---

## 7. Global settings

`~/.config/pico_sync/settings.json`:
```json
{
  "language": "ua"
}
```

- `language` — `"ua"` or `"en"`. Auto-detect: first from settings.json, then from `$LANG` (if `uk*` → `"ua"`, otherwise → `"en"`)

---

## 8. Project configuration

`<project_root>/.picosyncconfig` (JSON):
```json
{
  "port": "",
  "filter": "all",
  "piconame": ""
}
```

- `port` — saved COM port
- `filter` — current sync filter
- `piconame` — device name

---

## 9. Sync filters

| Filter | What gets deleted from Pico |
|--------|-----------------------------|
| `all` | All files not present locally |
| `py` | Only `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Everything except `.py` |
| `.ext,.ext2` | Files with specified extensions |

Filter only affects **deletion** of extra files from Pico. All files are uploaded regardless of filter.

---

## 10. `_uinput()` — protected input

Replaces `input()` everywhere. Uses `sys.stdin.readline()` instead of `input()` to avoid `UnicodeDecodeError` on Windows with certain encodings.

Used in:
- Number selection in fallback menu
- Project path input
- Piconame input
- Custom filter extension input
- Port selection
- Delete confirmation (y/N)
- `press_enter`

---

## 11. ANSI colors (C class)

| Attribute | Code | Color |
|-----------|------|-------|
| `C.GREEN` | `\033[92m` | Green |
| `C.YELLOW` | `\033[93m` | Yellow |
| `C.RED` | `\033[91m` | Red |
| `C.BLUE` | `\033[94m` | Blue |
| `C.RESET` | `\033[0m` | Reset |

On Windows: `os.system("")` activates ANSI processing in terminal.

---

## 12. Error handling

| Situation | Behavior |
|-----------|----------|
| Pico not found in `[f] files` | Print `device_not_found`, pause, return to main menu |
| Pico not found in `[d] device` | Print `device_not_found`, return to device menu |
| Pico not found on piconame detect/set/clear | Print `port_not_found`, pause, return |
| No serial ports | Print `no_serial_ports`, return `None` |
| File list error | Empty list, print `pico_list_error` |
| mpremote not installed | Print `mpremote_not_found`, `sys.exit(1)` |
| Editor not found for edit | Print `edit_no_editor` with temp path, cleanup |
| Upload error during sync | Print error, exit sync |
| UnicodeDecodeError on project path input | Print `project_read_error`, retry |
| check_for_updates error | Silent skip |
