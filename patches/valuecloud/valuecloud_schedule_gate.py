#!/usr/bin/env python3
"""Kyiv-local CPR schedule gate for GitHub Actions (UTC cron is DST-unsafe).

Prints the mode to set, or SKIP:<reason> when nothing should run.

Schedule / pause without commits — GitHub Actions *variables* (not secrets):
  VALUECLOUD_CPR_ENABLED   true|false  (default true; cron only)
  VALUECLOUD_CPR_SCHEDULE  JSON object hour→mode, e.g.
    {"8":"Utility first","11":"PV only","13":"Utility first",
     "15":"PV only","17":"Utility first","21":"PV only"}

Manual workflow_dispatch (--force-mode) always runs even when ENABLED=false.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Kyiv")

# Fallback when VALUECLOUD_CPR_SCHEDULE is unset / empty
DEFAULT_HOUR_TO_MODE = {
    8: "Utility first",
    11: "PV only",
    13: "Utility first",
    15: "PV only",
    17: "Utility first",
    21: "PV only",
}

VALID_MODES = {
    "Utility first",
    "PV first",
    "Utility + PV",
    "PV only",
}


def env_enabled() -> bool:
    raw = (os.environ.get("VALUECLOUD_CPR_ENABLED") or "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


def load_schedule() -> dict[int, str]:
    raw = (os.environ.get("VALUECLOUD_CPR_SCHEDULE") or "").strip()
    if not raw:
        return dict(DEFAULT_HOUR_TO_MODE)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"VALUECLOUD_CPR_SCHEDULE invalid JSON: {exc}") from exc
    if not isinstance(data, dict) or not data:
        raise SystemExit("VALUECLOUD_CPR_SCHEDULE must be a non-empty JSON object")
    out: dict[int, str] = {}
    for key, value in data.items():
        hour = int(key)
        if hour < 0 or hour > 23:
            raise SystemExit(f"invalid hour {key!r} in VALUECLOUD_CPR_SCHEDULE")
        mode = str(value).strip()
        if mode not in VALID_MODES:
            allowed = ", ".join(sorted(VALID_MODES))
            raise SystemExit(f"invalid mode {mode!r} for hour {hour}; use one of: {allowed}")
        out[hour] = mode
    return out


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
        if forced.upper() == "SKIP" or forced.upper().startswith("SKIP"):
            print("SKIP:forced")
            return 0
        if forced not in VALID_MODES:
            raise SystemExit(f"unknown mode {forced!r}")
        print(forced)
        return 0

    if not env_enabled():
        print(
            "SKIP paused (VALUECLOUD_CPR_ENABLED is false)",
            file=sys.stderr,
        )
        print("SKIP:paused")
        return 0

    schedule = load_schedule()
    now = datetime.now(TZ)
    mode = schedule.get(now.hour)
    if mode is None:
        print(
            f"SKIP not a schedule hour (Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')})",
            file=sys.stderr,
        )
        print("SKIP:not_schedule_hour")
        return 0

    print(
        f"Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')} → {mode}",
        file=sys.stderr,
    )
    print(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
