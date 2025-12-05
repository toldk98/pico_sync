 ```
  ⚠️ Notice:
This file is an automatic English translation of the original documentation README.md (Ukrainian).
In case of differences or ambiguity, the Ukrainian version takes precedence.
```

# Pico Sync Tool (pico_sync.py)

`pico_sync.py` is a compact CLI tool designed to simplify development workflow with Raspberry Pi Pico / Pico W running
MicroPython.
It provides convenient commands for file synchronization, filesystem browsing, basic remote file operations, live serial
monitoring, and device reboot.

---

## 📁 1. Purpose of pico_sync.py

The tool aims to make MicroPython development feel as close as possible to working with a regular local project.

### 🔹 Features:

* 🔄 Synchronize the `src/` directory to the Pico

* 🧠 Delta-sync: only changed files are uploaded

* 🗑 Auto-removal of extra files on the Pico

* 🧼 Automatic cleanup of empty directories

* ⛔ Ignore rules via `.picoignore` (supports `*`, `**`, `dir/` — only inside `src/`)

* 📂 Browse Pico filesystem (`--ls`)

* 📄 Read files (`--cat`)

* ✏️ Edit files via nano (`--nano`)

* 🔍 Interactive Pico USB-port detection (`--search_port`)

* 🔌 Live serial monitor (`--monitor`)

* 🔁 Software reboot of the Pico (`--reboot`)

The tool automatically creates missing directories on the device and operates using `mpremote`.

---

## 📂 2. Recommended project structure

To ensure smooth operation, the following project layout is recommended:

```
project_root/
│
├── pico_sync.py          # the tool itself
├── .picoignore           # ignore rules
│
└── src/                  # files that will be synchronized to Pico
```

⚠️ Important:

1. `.picoignore` affects **only files inside `src/`**
2. **Only `src/` is synchronized** — files outside this directory are never uploaded.

---

## 📜 3. The .picoignore file

Ignore rules follow a syntax similar to `.gitignore`.

Examples:

### Ignore caches

```
__pycache__/
*.pyc
```

### Recursively ignore all `.log` files

```
**/*.log
```

### Ignore a specific file

```
config/local_settings.py
```

### Ignore a directory

```
tests/
```

Supported patterns:

| Pattern | Description                  |
|---------|------------------------------|
| `*`     | any chars inside a directory |
| `**`    | recursive multi-level match  |
| `?`     | single character             |
| `dir/`  | ignore entire directory      |
| `*.ext` | file mask                    |

---

## 4. 🔧 Technical details

### Delta-sync (intelligent synchronization)

Delta-sync uses SHA-256 hashing:

1. Each local file gets its SHA-256 calculated.
2. Pico computes SHA-256 of the remote file via `mpremote`.
3. If hashes match → file is skipped.
4. If hashes differ or file is missing → file is uploaded.
5. After upload, any file on Pico that is not present locally in `src/` is deleted.
6. Empty directories are removed as well.

This ensures extremely fast syncing even with large projects.

---

### Using the `--port` option

The selected port is stored in an environment variable:

```
os.environ["MPREMOTE_PORT"] = args.port
```

`mpremote` automatically uses this port for all subsequent commands, eliminating the need to specify it every time.

---

### BAUD = 115200 — explanation

`115200` is the **default serial speed of MicroPython on RP2040**.

It is not related to `mpremote` but is used by the live serial monitor (`--monitor`) because Pico prints REPL output at
this baud rate unless explicitly changed by the user.

---

## 5. Help & usage examples

### 📘 Show help

```
python pico_sync.py --help
```

Example output:

```
usage: pico_sync.py [-h] [--port PORT] [--src SRC]
                    [--sync] [--ls PATH] [--cat FILE]
                    [--nano FILE] [--search_port]
                    [--check_update] [--reboot]
                    [--monitor]

Pico Sync Tool — sync/ls/cat/nano for Raspberry Pi Pico

options:
  -h, --help      Show help
  --port PORT     USB port for Pico (also used by mpremote)
  --src SRC       Local directory to synchronize (default: src)
  --sync          Synchronize src → Pico
  --ls PATH       List files in a Pico directory
  --cat FILE      Print contents of a Pico file
  --nano FILE     Edit a remote file using nano
  --search_port   Interactive Pico serial-port search
  --check_update  Check for updates to the tool
  --reboot        Software reset of the Pico via mpremote
  --monitor       Real-time Pico serial port monitor
```

---

### 🔍 Find the Pico port

```
python pico_sync.py --search_port
```

Example:

```
Available serial ports:

0) ⭐ /dev/ttyACM0 USB Serial Device [VID=0x2E8A]
1) /dev/ttyUSB0 CP2102 USB-UART

Select port number:
```

When selected, the port is automatically applied to all tool operations.

---

### 🔄 Synchronize project

Standard sync:

```
python pico_sync.py --sync
```

Specify a custom source directory:

```
python pico_sync.py --src my_src --sync
```

---

### 📂 List Pico filesystem

```
python pico_sync.py --ls /
python pico_sync.py --ls /spm
```

---

### 📄 Read a file

```
python pico_sync.py --cat /main.py
```

---

### ✏️ Edit a file via nano

```
python pico_sync.py --nano /config/settings.py
```

Mechanism:

1. file is downloaded into a temporary file
2. opened in nano
3. saved back to Pico automatically

---

### 🗑 Auto-deleting remote files

During `--sync`:

* files not present locally are removed
* empty directories are also removed

---

### 🔌 Serial monitor

```
python pico_sync.py --monitor
```

The monitor automatically reconnects if Pico:

* reboots
* changes USB port
* temporarily disconnects

---

### 🔁 Reboot the Pico

```
python pico_sync.py --reboot
```

This performs a software reset via `mpremote reset`, acting like pressing the RUN button without physical access.

---

## 📘 6. User guide

### ✔ Step 1 — Install dependencies

```
pip install pyserial mpremote
```

### ✔ Step 2 — Prepare project structure

```
project/
├── pico_sync.py
├── .picoignore
└── src/
```

### ✔ Step 3 — Connect the Pico via USB

### ✔ Step 4 — Detect port (recommended)

```
python pico_sync.py --search_port
```

### ✔ Step 5 — Sync project

```
python pico_sync.py --sync
```

### ✔ Step 6 — Browse or edit files

```
python pico_sync.py --ls /
python pico_sync.py --nano /main.py
```

### ✔ Step 7 — Update changes

```
python pico_sync.py --sync
```