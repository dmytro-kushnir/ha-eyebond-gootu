#!/usr/bin/env python3
"""Set Gootu charging priority (CPR) via ValueClouds ctrlDevice."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import valuecloud_api as vc

CTRL_PATH = "ppe/api/auth/web/ctrlDevice"
FIELD_ID = "cltd_charging_priority"
DATATYPE = 3
RETRIES = 3
RESULT_FILE = vc.SHELL_DIR / "valuecloud_last_result.txt"
LOG_FILE = vc.SHELL_DIR / "valuecloud_cpr.log"

MODE_TO_VAL = {
    "utility first": 12336,
    "utility_first": 12336,
    "pv first": 12337,
    "pv_first": 12337,
    "utility + pv": 12338,
    "utility_pv": 12338,
    "pv only": 12339,
    "pv_only": 12339,
}
VAL_TO_LABEL = {
    12336: "Utility first",
    12337: "PV first",
    12338: "Utility + PV",
    12339: "PV only",
}


def resolve_mode(mode: str) -> int:
    key = mode.strip().lower()
    if key not in MODE_TO_VAL:
        allowed = ", ".join(VAL_TO_LABEL.values())
        raise SystemExit(f"unknown mode {mode!r}; use one of: {allowed}")
    return MODE_TO_VAL[key]


def write_result(line: str) -> None:
    vc.SHELL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(line.strip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--secrets", default="/config/secrets.yaml")
    args = parser.parse_args()

    secrets = vc.load_secrets(Path(args.secrets))
    username, password, pn, sn, devcode, devaddr = vc.device_ids(secrets)
    val = resolve_mode(args.mode)
    label = VAL_TO_LABEL[val]
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    session = vc.load_session(username)
    last_error: Exception | None = None
    write_payload = None
    for attempt in range(1, RETRIES + 1):
        try:
            if session is None:
                session = vc.login(username, password)
                vc.save_session(username, session)
            write_payload = vc.signed_get(
                session=session,
                path=CTRL_PATH,
                params={
                    "datatype": DATATYPE,
                    "pn": pn,
                    "sn": sn,
                    "devcode": devcode,
                    "devaddr": devaddr,
                    "id": FIELD_ID,
                    "val": val,
                    "i18n": "en_US",
                },
            )
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            vc.append_log(LOG_FILE, f"{stamp} attempt {attempt}/{RETRIES} failed: {exc}")
            vc.clear_session()
            session = None

    if last_error is not None or write_payload is None:
        write_result(f"{stamp} FAILED {label} :: {last_error}")
        raise RuntimeError(str(last_error or "write_failed"))

    write_result(f"{stamp} OK {label}")
    vc.append_log(LOG_FILE, f"{stamp} OK {label} val={val}")
    print(f"OK write {FIELD_ID}={val} ({label})")
    print(json.dumps({"write": write_payload}, ensure_ascii=False)[:300])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}", file=sys.stderr)
        try:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            write_result(f"{stamp} FAILED :: {exc}")
        except Exception:
            pass
        raise SystemExit(1) from exc
