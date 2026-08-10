#!/usr/bin/env python3
"""Kyiv-local CPR schedule gate for GitHub Actions (UTC cron is DST-unsafe).

Prints the mode to set, or SKIP when this hour is not a schedule slot.
Edit HOUR_TO_MODE to change the clock schedule.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Kyiv")

# Hour (0-23, Europe/Kyiv) → charging priority label
HOUR_TO_MODE = {
    8: "Utility first",
    11: "PV only",
    13: "Utility first",
    15: "PV only",
    17: "Utility first",
    21: "PV only",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-mode",
        default="",
        help="Bypass clock gate (workflow_dispatch); print this mode",
    )
    args = parser.parse_args()

    forced = (args.force_mode or "").strip()
    if forced:
        if forced.upper() == "SKIP":
            print("SKIP")
            return 0
        print(forced)
        return 0

    now = datetime.now(TZ)
    mode = HOUR_TO_MODE.get(now.hour)
    if mode is None:
        print(
            f"SKIP not a schedule hour (Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')})",
            file=sys.stderr,
        )
        print("SKIP")
        return 0

    print(
        f"Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')} → {mode}",
        file=sys.stderr,
    )
    print(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
