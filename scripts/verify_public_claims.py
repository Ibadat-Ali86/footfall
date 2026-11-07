#!/usr/bin/env python3
"""Public Claims & Number Verifier CLI script (Task T1.9)."""

from __future__ import annotations

import sys

from footfall.export.claims import verify_all_claims

if __name__ == "__main__":
    sys.exit(verify_all_claims())
