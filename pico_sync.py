# pico_sync.py
"""Legacy entry point script — delegates to pico_sync.cli.main."""

from pico_sync.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exit.")
