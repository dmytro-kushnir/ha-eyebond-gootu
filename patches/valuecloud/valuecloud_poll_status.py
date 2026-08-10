#!/usr/bin/env python3
"""Poll ValueClouds operating mode (sy_status) for grid-lost / restored notifies."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import valuecloud_api as vc

STATUS_PATH = "ppe/api/auth/web/queryDeviceOneDataxxx"
RETRIES = 3
def mode_file() -> Path:
    return vc.shell_dir() / "valuecloud_operating_mode.txt"


def event_file() -> Path:
    return vc.shell_dir() / "valuecloud_mode_event.txt"


def status_json() -> Path:
    return vc.shell_dir() / "valuecloud_last_status.json"


def log_file() -> Path:
    return vc.shell_dir() / "valuecloud_status.log"


def field_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        field_id = vc.clean(row.get("id"))
        if field_id:
            out[field_id] = vc.clean(row.get("val"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--secrets",
        default=None,
        help="HA secrets.yaml path (optional when VALUECLOUD_* env is set)",
    )
    args = parser.parse_args()

    secrets_path = Path(args.secrets) if args.secrets else None
    secrets = vc.resolve_secrets(secrets_path)
    username, password, pn, sn, devcode, devaddr = vc.device_ids(secrets)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    session = vc.load_session(username)
    last_error: Exception | None = None
    rows: list[dict[str, Any]] | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            if session is None:
                session = vc.login(username, password)
                vc.save_session(username, session)
            payload = vc.signed_get(
                session=session,
                path=STATUS_PATH,
                params={
                    "pn": pn,
                    "sn": sn,
                    "devcode": devcode,
                    "devaddr": devaddr,
                    "i18n": "en_US",
                },
            )
            data = payload.get("data")
            if not isinstance(data, list):
                raise RuntimeError("api_failed:missing_data_list")
            rows = [item for item in data if isinstance(item, dict)]
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            vc.append_log(log_file(), f"{stamp} attempt {attempt}/{RETRIES} failed: {exc}")
            vc.clear_session()
            session = None

    if last_error is not None or rows is None:
        raise RuntimeError(str(last_error or "status_failed"))

    fields = field_map(rows)
    mode = fields.get("sy_status") or "unknown"
    grid_v = fields.get("gd_grid_voltage") or ""
    soc = fields.get("bt_battery_capacity") or ""

    vc.shell_dir().mkdir(parents=True, exist_ok=True)
    mf, ef, sj, lf = mode_file(), event_file(), status_json(), log_file()
    previous = mf.read_text(encoding="utf-8").strip() if mf.is_file() else ""
    mf.write_text(mode + "\n", encoding="utf-8")

    changed = bool(previous and previous != mode)
    # Only rewrite status JSON / log when something useful changed (SD wear).
    if changed or not sj.is_file():
        sj.write_text(
            json.dumps(
                {
                    "sy_status": mode,
                    "gd_grid_voltage": grid_v,
                    "bt_battery_capacity": soc,
                    "previous_sy_status": previous,
                    "changed": changed,
                    "polled_at": stamp,
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    if changed:
        if mode == "Battery mode":
            event = (
                f"{stamp} Gootu on battery (grid lost). "
                f"{previous} → {mode} (grid {grid_v} V)"
            )
        elif mode == "Mains mode":
            event = (
                f"{stamp} Gootu grid restored. "
                f"{previous} → {mode} (grid {grid_v} V)"
            )
        else:
            event = f"{stamp} Gootu mode changed: {previous} → {mode}"
        ef.write_text(event + "\n", encoding="utf-8")
        vc.append_log(lf, event)
        print(f"CHANGED {previous!r} -> {mode!r}")
        print(event)
    else:
        # Quiet on unchanged polls — no log append.
        print(f"OK unchanged sy_status={mode!r}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}", file=sys.stderr)
        vc.append_log(
            log_file(),
            f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} FAILED: {exc}",
        )
        raise SystemExit(1) from exc
