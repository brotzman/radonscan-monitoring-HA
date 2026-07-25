#!/usr/bin/env python3
import sys

PACKAGE_ROOT = "/usr/local/lib"
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from radonscan3.service import main

if __name__ == "__main__":
    raise SystemExit(main())
