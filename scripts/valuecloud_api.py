#!/usr/bin/env python3
"""Shared ValueClouds web API helpers (login, session cache, signed GET/POST)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
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
LOG_MAX_BYTES = 50_000


def shell_dir() -> Path:
    """HA default `/config/shell`; CI uses `VALUECLOUD_SHELL_DIR` (e.g. runner temp)."""
    return Path(os.environ.get("VALUECLOUD_SHELL_DIR") or "/config/shell")


# Back-compat for callers that read vc.SHELL_DIR (resolved at import — prefer shell_dir()).
SHELL_DIR = shell_dir()


def session_cache_path() -> Path:
    return shell_dir() / ".valuecloud_session.json"


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


def secrets_from_env() -> dict[str, Any] | None:
    username = clean(os.environ.get("VALUECLOUD_USERNAME"))
    password = clean(os.environ.get("VALUECLOUD_PASSWORD"))
    if not username or not password:
        return None
    # Strip BOM / zero-width chars from copy-paste into GitHub secrets.
    for bad in ("\ufeff", "\u200b", "\u200c", "\u200d"):
        username = username.replace(bad, "")
        password = password.replace(bad, "")
    return {
        "valuecloud_username": username,
        "valuecloud_password": password,
        "valuecloud_pn": clean(os.environ.get("VALUECLOUD_PN")).replace("\ufeff", ""),
        "valuecloud_sn": clean(os.environ.get("VALUECLOUD_SN")).replace("\ufeff", ""),
        "valuecloud_devcode": clean(os.environ.get("VALUECLOUD_DEVCODE")) or "2506",
        "valuecloud_devaddr": clean(os.environ.get("VALUECLOUD_DEVADDR")) or "1",
    }


def credential_fingerprint(username: str, password: str) -> str:
    """Safe debug line — lengths + short hashes, never the secret itself."""
    u_sha = hashlib.sha256(username.encode("utf-8")).hexdigest()[:12]
    p_sha = hashlib.sha256(password.encode("utf-8")).hexdigest()[:12]
    api12 = password_for_api(password)[:12]
    return (
        f"cred_fp username_len={len(username)} user_sha256_12={u_sha} "
        f"has_at={('@' in username)} password_len={len(password)} "
        f"pass_sha256_12={p_sha} api_sha1_12={api12}"
    )


def resolve_secrets(secrets_path: Path | None = None) -> dict[str, Any]:
    """Prefer env vars (CI); else HA secrets.yaml."""
    env = secrets_from_env()
    if env is not None:
        return env
    path = secrets_path or Path("/config/secrets.yaml")
    if not path.is_file():
        raise SystemExit(
            "Need VALUECLOUD_* env vars or a secrets.yaml "
            f"(missing {path})"
        )
    return load_secrets(path)


def device_ids(secrets: dict[str, Any]) -> tuple[str, str, str, str, int, int]:
    username = clean(secrets.get("valuecloud_username"))
    password = clean(secrets.get("valuecloud_password"))
    pn = clean(secrets.get("valuecloud_pn"))
    sn = clean(secrets.get("valuecloud_sn"))
    devcode = int(clean(secrets.get("valuecloud_devcode")) or "2506")
    devaddr = int(clean(secrets.get("valuecloud_devaddr")) or "1")
    if not username or not password:
        raise SystemExit("need valuecloud_username and valuecloud_password")
    if not pn or not sn:
        raise SystemExit("need valuecloud_pn and valuecloud_sn")
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
    shell_dir().mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def load_session(account: str) -> dict[str, str] | None:
    cache = session_cache_path()
    try:
        raw = json.loads(cache.read_text(encoding="utf-8"))
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
    cache = session_cache_path()
    shell_dir().mkdir(parents=True, exist_ok=True)
    cache.write_text(
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
        cache.chmod(0o600)
    except OSError:
        pass


def clear_session() -> None:
    try:
        session_cache_path().unlink(missing_ok=True)
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
