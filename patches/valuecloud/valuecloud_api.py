#!/usr/bin/env python3
"""Shared ValueClouds web API helpers (login, session cache, signed GET/POST)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.valueclouds.com/"
LOGIN_PATH = "ppr/web/login/login"
TIMEOUT = 20.0
SESSION_TTL = 25 * 60
SHELL_DIR = Path("/config/shell")
SESSION_CACHE = SHELL_DIR / ".valuecloud_session.json"
LOG_MAX_BYTES = 50_000


def clean(value: Any) -> str:
    return str(value or "").strip()


def password_for_api(password: str) -> str:
    cleaned = password.strip()
    if len(cleaned) == 40 and all(c in "0123456789abcdefABCDEF" for c in cleaned):
        return cleaned.lower()
    return hashlib.sha1(cleaned.encode("utf-8")).hexdigest()


def load_secrets(path: Path) -> dict[str, Any]:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError("secrets.yaml must be a mapping")
    return data


def device_ids(secrets: dict[str, Any]) -> tuple[str, str, str, str, int, int]:
    username = clean(secrets.get("valuecloud_username"))
    password = clean(secrets.get("valuecloud_password"))
    pn = clean(secrets.get("valuecloud_pn"))
    sn = clean(secrets.get("valuecloud_sn"))
    devcode = int(clean(secrets.get("valuecloud_devcode")) or "2506")
    devaddr = int(clean(secrets.get("valuecloud_devaddr")) or "1")
    if not username or not password:
        raise SystemExit("secrets.yaml needs valuecloud_username and valuecloud_password")
    if not pn or not sn:
        raise SystemExit("secrets.yaml needs valuecloud_pn and valuecloud_sn")
    return username, password, pn, sn, devcode, devaddr


def web_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
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


def http_json(
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


def envelope_ok(payload: dict[str, Any]) -> bool:
    if payload.get("success") is True:
        return True
    try:
        return int(payload.get("code")) in (0, 200)
    except (TypeError, ValueError):
        return False


def sign(secret: str, path: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        ("/" + path.lstrip("/")).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def rotate_log(path: Path, max_bytes: int = LOG_MAX_BYTES) -> None:
    try:
        if path.is_file() and path.stat().st_size > max_bytes:
            text = path.read_text(encoding="utf-8", errors="replace")
            path.write_text(text[-max_bytes // 2 :], encoding="utf-8")
    except OSError:
        pass


def append_log(path: Path, line: str) -> None:
    rotate_log(path)
    SHELL_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def load_session(account: str) -> dict[str, str] | None:
    try:
        raw = json.loads(SESSION_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict) or clean(raw.get("account")) != account:
        return None
    try:
        if time.time() - float(raw.get("saved_at") or 0) > SESSION_TTL:
            return None
    except (TypeError, ValueError):
        return None
    token, secret = clean(raw.get("token")), clean(raw.get("secret"))
    if not token or not secret:
        return None
    return {"token": token, "secret": secret}


def save_session(account: str, session: dict[str, str]) -> None:
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
    try:
        SESSION_CACHE.chmod(0o600)
    except OSError:
        pass


def clear_session() -> None:
    try:
        SESSION_CACHE.unlink(missing_ok=True)
    except OSError:
        pass


def login(username: str, password: str) -> dict[str, str]:
    payload = http_json(
        method="POST",
        url=BASE_URL.rstrip("/") + "/" + LOGIN_PATH,
        headers=web_headers(),
        body={
            "account": username,
            "password": password_for_api(password),
            "project": "IOT",
        },
    )
    if not envelope_ok(payload):
        raise RuntimeError(
            f"login_failed:{payload.get('errorMessage') or payload.get('message') or payload}"
        )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token, secret = clean(data.get("token")), clean(data.get("secret"))
    if not token or not secret:
        raise RuntimeError("login_failed:missing_token_or_secret")
    return {"token": token, "secret": secret}


def signed_get(
    *,
    session: dict[str, str],
    path: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/") + "?" + urlencode(params)
    payload = http_json(
        method="GET",
        url=url,
        headers=web_headers(
            {
                "token": session["token"],
                "sign": sign(session["secret"], path),
                "vw": "device",
            }
        ),
    )
    if not envelope_ok(payload):
        detail = payload.get("errorMessage") or payload.get("message") or payload
        raise RuntimeError(f"api_failed:{detail}")
    return payload
