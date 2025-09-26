#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add makinishop folder to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "makinishop"))
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "makinishop.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate venv and check PYTHONPATH."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
