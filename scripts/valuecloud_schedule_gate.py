#!/usr/bin/env python3
"""Kyiv-local CPR schedule gate for GitHub Actions (UTC cron is DST-unsafe).

Prints SKIP:<reason> or a mode name. Also writes mode/reason/slot to $GITHUB_OUTPUT.

Variables (Settings → Actions → Variables) — no reload/commit needed; next cron picks them up:
  VALUECLOUD_CPR_ENABLED   true|false  (cron only; default true)
  VALUECLOUD_CPR_SCHEDULE  JSON time→mode (Europe/Kyiv), e.g.
    {"8:00":"Utility first","11:00":"PV only","13:50":"Utility first",
     "15:00":"PV only","17:00":"Utility first","21:00":"PV only"}

Hour-only keys like "8" mean 08:00. A slot fires in [time, time+55min) so late Actions cron can still hit it.
Manual --force-mode always runs even when ENABLED=false.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Kyiv")
SLOT_GRACE = timedelta(minutes=55)

DEFAULT_SCHEDULE = {
    "8:00": "Utility first",
    "11:00": "PV only",
    "13:00": "Utility first",
    "15:00": "PV only",
    "17:00": "Utility first",
    "21:00": "PV only",
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


def parse_clock(key: object) -> tuple[int, int]:
    """Return (hour, minute). Accepts 8, '8', '8:00', '13:50'."""
    text = str(key).strip()
    if ":" in text:
        hour_s, minute_s = text.split(":", 1)
        hour, minute = int(hour_s), int(minute_s)
    else:
        hour, minute = int(text), 0
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise SystemExit(f"invalid schedule time {key!r}")
    return hour, minute


def load_schedule() -> dict[tuple[int, int], str]:
    raw = (os.environ.get("VALUECLOUD_CPR_SCHEDULE") or "").strip()
    if raw:
        try:
            source = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"VALUECLOUD_CPR_SCHEDULE invalid JSON: {exc}") from exc
    else:
        source = dict(DEFAULT_SCHEDULE)
    if not isinstance(source, dict) or not source:
        raise SystemExit("VALUECLOUD_CPR_SCHEDULE must be a non-empty JSON object")

    out: dict[tuple[int, int], str] = {}
    for key, value in source.items():
        hour, minute = parse_clock(key)
        mode = str(value).strip()
        if mode not in VALID_MODES:
            allowed = ", ".join(sorted(VALID_MODES))
            raise SystemExit(f"invalid mode {mode!r} for {key!r}; use one of: {allowed}")
        out[(hour, minute)] = mode
    return out


def due_slot(
    now: datetime, schedule: dict[tuple[int, int], str]
) -> tuple[str, str] | None:
    """Latest schedule time still inside [slot, slot+grace)."""
    best: tuple[datetime, str] | None = None
    for (hour, minute), mode in schedule.items():
        slot_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if slot_at <= now < slot_at + SLOT_GRACE:
            if best is None or slot_at > best[0]:
                best = (slot_at, mode)
    if best is None:
        return None
    slot_at, mode = best
    return mode, slot_at.strftime("%Y-%m-%dT%H%M")


def emit(mode: str, reason: str, slot: str) -> None:
    if mode == "SKIP":
        print(f"SKIP:{reason}" if reason else "SKIP")
    else:
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
    slot_now = now.strftime("%Y-%m-%dT%H%M")

    forced = (args.force_mode or "").strip()
    if forced:
        if forced.upper() == "SKIP" or forced.upper().startswith("SKIP"):
            emit("SKIP", "forced", f"manual-{slot_now}")
            return 0
        if forced not in VALID_MODES:
            raise SystemExit(f"unknown mode {forced!r}")
        emit(forced, "", f"manual-{now.strftime('%Y%m%d%H%M%S')}")
        return 0

    if not env_enabled():
        print("SKIP paused (VALUECLOUD_CPR_ENABLED is false)", file=sys.stderr)
        emit("SKIP", "paused", slot_now)
        return 0

    schedule = load_schedule()
    due = due_slot(now, schedule)
    if due is None:
        print(
            f"SKIP not in a schedule window (Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')})",
            file=sys.stderr,
        )
        emit("SKIP", "not_schedule_hour", slot_now)
        return 0

    mode, slot = due
    print(f"Kyiv {now.strftime('%Y-%m-%d %H:%M %Z')} → {mode} (slot {slot})", file=sys.stderr)
    emit(mode, "", slot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
