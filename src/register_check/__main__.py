"""Allow `python -m register_check` to behave as the console script."""

import sys

from register_check.cli import main

if __name__ == "__main__":
    sys.exit(main())
