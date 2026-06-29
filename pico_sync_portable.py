# pico_sync_portable.py
"""Portable entry point — run directly without pip install: python pico_sync_portable.py"""

from pico_sync.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exit.")
