"""Allow `python -m standard_check` to behave as the console script."""

import sys

from standard_check.cli import main

if __name__ == "__main__":
    sys.exit(main())
