# pico_sync/__main__.py
"""Module entry point for `python -m pico_sync`."""

from .cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exit.")
