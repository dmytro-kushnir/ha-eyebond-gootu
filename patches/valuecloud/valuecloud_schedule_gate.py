#!/usr/bin/env python3
"""Kyiv-local CPR schedule gate for GitHub Actions (UTC cron is DST-unsafe).

Prints the mode to set, or SKIP:<reason> when nothing should run.
Also writes mode/reason/slot to $GITHUB_OUTPUT when set.

Variables (Settings → Actions → Variables):
  VALUECLOUD_CPR_ENABLED   true|false  (cron only; default true)
  VALUECLOUD_CPR_SCHEDULE  JSON hour→mode (Europe/Kyiv)

Manual --force-mode always runs even when ENABLED=false.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Kyiv")

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


def emit(mode: str, reason: str, slot: str) -> None:
    print(mode)
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"mode={mode}\n")
        handle.write(f"reason={reason}\n")
        handle.write(f"slot={slot}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-mode",
        default="",
        help="Bypass clock gate (workflow_dispatch); print this mode",
    )
    args = parser.parse_args()
    now = datetime.now(TZ)
    slot = now.strftime("%Y-%m-%dT%H")

    forced = (args.force_mode or "").strip()
    if forced:
        if forced.upper() == "SKIP" or forced.upper().startswith("SKIP"):
            emit("SKIP", "forced", f"manual-{slot}")
            return 0
        if forced not in VALID_MODES:
            raise SystemExit(f"unknown mode {forced!r}")
        # Unique slot so cache never blocks a manual run
        emit(forced, "", f"manual-{now.strftime('%Y%m%d%H%M%S')}")
        return 0

    if not env_enabled():
        print("SKIP paused (VALUECLOUD_CPR_ENABLED is false)", file=sys.stderr)
        emit("SKIP", "paused", slot)
        return 0

    schedule = load_schedule()
    mode = schedule.get(now.hour)
    if mode is None:
        print(
            f"SKIP not a schedule hour (Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')})",
            file=sys.stderr,
        )
        emit("SKIP", "not_schedule_hour", slot)
        return 0

    print(f"Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')} → {mode}", file=sys.stderr)
    emit(mode, "", slot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
