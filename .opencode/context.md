Project: Pico Sync — PC-side tool for syncing files to Raspberry Pi Pico

Purpose:

- tool synchronizes local source files to Raspberry Pi Pico over USB serial
- runs on host PC (Linux/macOS/Windows), NOT on the Pico itself
- provides CLI for sync, file listing, editing, serial monitoring, and device management
- uses mpremote as the transport layer for communicating with the Pico

Platform:

- target platform is the host PC running Python 3
- communicates with Raspberry Pi Pico / RP2040 running MicroPython
- NOT embedded firmware — this is a development tool
- requires Python 3.7+ with pyserial

Runtime:

- project runs on CPython (host), not MicroPython
- uses standard Python libraries: os, hashlib, base64, subprocess, argparse, json, urllib, tempfile, re
- depends on: pyserial, mpremote (called as subprocess)
- DO NOT use MicroPython-specific APIs in this codebase

Project Structure:

- / (project root)
    - pico_sync.py — main CLI tool entry point (sync, ls, cat, nano, reboot, monitor, search_port, check_update)
    - serial_monitor.py — standalone serial monitor with auto-reconnect
    - meta/ (link to remote version check data)

Dependencies:

- pyserial — serial port communication
- mpremote — MicroPython remote control tool (called via subprocess)
- all dependencies are standard pip packages

Sync Logic:

- delta-based sync using SHA-256 comparison
- reads .picoignore from project root for exclusion patterns
- supports gitignore-style patterns (**, *, ?, directory-only)
- walks source directory, uploads new/changed files, deletes files not present locally
- auto-creates directories on Pico before file upload
- files transferred via base64-encoded mpremote exec commands

Serial Monitor:

- auto-detects Pico port by VID (0x2E8A) or description keywords
- handles reconnection after device reset/disconnect
- non-blocking read with timeout
- green-colored output for readability
- graceful Ctrl+C exit

File Operations:

- pico_ls — list directory contents on Pico (with d/- prefix)
- pico_cat — print file content from Pico to stdout
- pico_nano — download file, edit in nano, upload changes back
- all operations go through mpremote exec

CLI:

- argparse-based command interface
- commands: --sync, --ls, --cat, --nano, --monitor, --reboot, --search_port, --check_update
- --port argument to specify Pico serial port (default: /dev/ttyACM0)
- --src argument to specify source directory (default: src/)
- environment variable MPREMOTE_PORT used to pass port to mpremote

Safety Rules:

- DO NOT introduce MicroPython-specific code in host-side scripts
- DO NOT hardcode port paths beyond the default
- DO NOT remove files from Pico without printing what is being deleted
- DO NOT add dependencies without checking they are standard or widely available
- always handle serial disconnection gracefully
- always handle missing Pico gracefully with clear error message
- fail silently for non-critical operations (e.g., version check)

Validation:

- always consider that Pico may be disconnected or in bootloader mode
- test serial operations with graceful fallbacks
