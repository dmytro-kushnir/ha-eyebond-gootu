#!/usr/bin/env python3
"""Set Gootu charging priority (CPR) via ValueClouds ctrlDevice.

Credentials: /config/secrets.yaml (valuecloud_username / valuecloud_password).
Session cache: /config/shell/.valuecloud_session.json (chmod 600, ~25 min TTL).
Result file:  /config/shell/valuecloud_last_result.txt (HA sensor + notify).

Example:
  python3 /config/shell/valuecloud_set_cpr.py --mode "PV only"
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.valueclouds.com/"
LOGIN_PATH = "ppr/web/login/login"
CTRL_PATH = "ppe/api/auth/web/ctrlDevice"
FIELD_ID = "cltd_charging_priority"
DATATYPE = 3
TIMEOUT = 20.0
RETRIES = 3
SESSION_TTL = 25 * 60
LOG_MAX_BYTES = 100_000

SHELL_DIR = Path("/config/shell")
SESSION_CACHE = SHELL_DIR / ".valuecloud_session.json"
RESULT_FILE = SHELL_DIR / "valuecloud_last_result.txt"
LOG_FILE = SHELL_DIR / "valuecloud_cpr.log"

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


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _password_for_api(password: str) -> str:
    cleaned = password.strip()
    if len(cleaned) == 40 and all(c in "0123456789abcdefABCDEF" for c in cleaned):
        return cleaned.lower()
    return hashlib.sha1(cleaned.encode("utf-8")).hexdigest()


def _load_secrets(path: Path) -> dict[str, Any]:
    import yaml  # HA image includes PyYAML

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError("secrets.yaml must be a mapping")
    return data


def _web_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        ),
        "Origin": "https://www.valueclouds.com",
        "Referer": "https://www.valueclouds.com/",
        "i18n": "en_US",
        "project": "IOT",
    }
    if extra:
        headers.update(extra)
    return headers


def _http_json(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
    timeout: float = TIMEOUT,
) -> dict[str, Any]:
    data = None
    req_headers = dict(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    request = Request(url=url, data=data, headers=req_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"http_{exc.code}:{detail[:300]}") from exc
    except URLError as exc:
        raise RuntimeError(f"network:{exc.reason}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid_json:{type(payload).__name__}")
    return payload


def _envelope_ok(payload: dict[str, Any]) -> bool:
    if payload.get("success") is True:
        return True
    try:
        return int(payload.get("code")) in (0, 200)
    except (TypeError, ValueError):
        return False


def _sign(secret: str, path: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        ("/" + path.lstrip("/")).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _chmod_private(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _rotate_log_if_needed() -> None:
    try:
        if LOG_FILE.is_file() and LOG_FILE.stat().st_size > LOG_MAX_BYTES:
            text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
            LOG_FILE.write_text(text[-LOG_MAX_BYTES // 2 :], encoding="utf-8")
    except OSError as exc:
        print(f"WARN log rotate failed: {exc}", file=sys.stderr)


def _write_result(line: str) -> None:
    SHELL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(line.strip() + "\n", encoding="utf-8")


def _load_session(account: str) -> dict[str, str] | None:
    try:
        raw = json.loads(SESSION_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict) or _clean(raw.get("account")) != account:
        return None
    try:
        if time.time() - float(raw.get("saved_at") or 0) > SESSION_TTL:
            return None
    except (TypeError, ValueError):
        return None
    token, secret = _clean(raw.get("token")), _clean(raw.get("secret"))
    if not token or not secret:
        return None
    return {"token": token, "secret": secret}


def _save_session(account: str, session: dict[str, str]) -> None:
    SHELL_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_CACHE.write_text(
        json.dumps(
            {
                "account": account,
                "token": session["token"],
                "secret": session["secret"],
                "saved_at": time.time(),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _chmod_private(SESSION_CACHE)


def _clear_session() -> None:
    try:
        SESSION_CACHE.unlink(missing_ok=True)
    except OSError:
        pass


def login(username: str, password: str) -> dict[str, str]:
    payload = _http_json(
        method="POST",
        url=BASE_URL.rstrip("/") + "/" + LOGIN_PATH,
        headers=_web_headers(),
        body={
            "account": username,
            "password": _password_for_api(password),
            "project": "IOT",
        },
    )
    if not _envelope_ok(payload):
        raise RuntimeError(
            f"login_failed:{payload.get('errorMessage') or payload.get('message') or payload}"
        )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token, secret = _clean(data.get("token")), _clean(data.get("secret"))
    if not token or not secret:
        raise RuntimeError("login_failed:missing_token_or_secret")
    return {"token": token, "secret": secret}


def ctrl_device(
    *,
    session: dict[str, str],
    pn: str,
    sn: str,
    devcode: int,
    devaddr: int,
    val: int,
) -> dict[str, Any]:
    params = {
        "datatype": DATATYPE,
        "pn": pn,
        "sn": sn,
        "devcode": devcode,
        "devaddr": devaddr,
        "id": FIELD_ID,
        "val": val,
        "i18n": "en_US",
    }
    url = (
        BASE_URL.rstrip("/")
        + "/"
        + CTRL_PATH
        + "?"
        + urlencode(params)
    )
    payload = _http_json(
        method="GET",
        url=url,
        headers=_web_headers(
            {
                "token": session["token"],
                "sign": _sign(session["secret"], CTRL_PATH),
                "vw": "device",
            }
        ),
    )
    if not _envelope_ok(payload):
        detail = payload.get("errorMessage") or payload.get("message") or payload
        raise RuntimeError(f"api_failed:{detail}")
    return payload


def resolve_mode(mode: str) -> int:
    key = mode.strip().lower()
    if key not in MODE_TO_VAL:
        allowed = ", ".join(VAL_TO_LABEL.values())
        raise SystemExit(f"unknown mode {mode!r}; use one of: {allowed}")
    return MODE_TO_VAL[key]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--secrets", default="/config/secrets.yaml")
    args = parser.parse_args()

    _rotate_log_if_needed()
    secrets_path = Path(args.secrets)
    if not secrets_path.is_file():
        raise SystemExit(f"missing secrets file: {secrets_path}")

    secrets = _load_secrets(secrets_path)
    username = _clean(secrets.get("valuecloud_username"))
    password = _clean(secrets.get("valuecloud_password"))
    pn = _clean(secrets.get("valuecloud_pn"))
    sn = _clean(secrets.get("valuecloud_sn"))
    devcode = int(_clean(secrets.get("valuecloud_devcode")) or "2506")
    devaddr = int(_clean(secrets.get("valuecloud_devaddr")) or "1")
    if not username or not password:
        raise SystemExit("secrets.yaml needs valuecloud_username and valuecloud_password")
    if not pn or not sn:
        raise SystemExit("secrets.yaml needs valuecloud_pn and valuecloud_sn")

    val = resolve_mode(args.mode)
    label = VAL_TO_LABEL[val]
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    session = _load_session(username)
    if session:
        print("using cached ValueCloud session", file=sys.stderr)

    last_error: Exception | None = None
    write_payload: dict[str, Any] | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            if session is None:
                session = login(username, password)
                _save_session(username, session)
            write_payload = ctrl_device(
                session=session,
                pn=pn,
                sn=sn,
                devcode=devcode,
                devaddr=devaddr,
                val=val,
            )
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"attempt {attempt}/{RETRIES} failed: {exc}", file=sys.stderr)
            msg = str(exc).lower()
            if "login_failed" in msg or "api_failed" in msg or "http_401" in msg:
                _clear_session()
                session = None
            elif "network:" in msg and session is not None:
                _clear_session()
                session = None

    if last_error is not None or write_payload is None:
        _write_result(f"{stamp} FAILED {label} :: {last_error}")
        raise RuntimeError(str(last_error or "write_failed"))

    print(f"OK write {FIELD_ID}={val} ({label})")
    print(json.dumps({"write": write_payload}, ensure_ascii=False)[:500])
    _write_result(f"{stamp} OK {label}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}", file=sys.stderr)
        try:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            _write_result(f"{stamp} FAILED :: {exc}")
        except Exception:
            pass
        raise SystemExit(1) from exc
