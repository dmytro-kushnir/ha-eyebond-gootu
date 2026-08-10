#!/usr/bin/env python3
"""Print safe credential fingerprints for CI (lengths + short hashes only)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def clean(value: str | None) -> str:
    text = (value or "").strip()
    for bad in ("\ufeff", "\u200b", "\u200c", "\u200d"):
        text = text.replace(bad, "")
    return text


def main() -> int:
    u = clean(os.environ.get("VALUECLOUD_USERNAME"))
    p = clean(os.environ.get("VALUECLOUD_PASSWORD"))
    user_sha = hashlib.sha256(u.encode()).hexdigest()[:12]
    pass_sha = hashlib.sha256(p.encode()).hexdigest()[:12]
    api_sha = hashlib.sha1(p.encode()).hexdigest()[:12]

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).open("a", encoding="utf-8").write(
            "\n".join(
                [
                    "## ValueCloud credential fingerprint",
                    f"- username_len: `{len(u)}`",
                    f"- user_sha256_12: `{user_sha}`",
                    f"- password_len: `{len(p)}`",
                    f"- pass_sha256_12: `{pass_sha}`",
                    f"- api_sha1_12: `{api_sha}`",
                    "",
                    "Expected (Pi): user `1e1536ac9384` / pass `c74385263420` / api `7b70c7ddeb59`",
                    "",
                ]
            )
        )

    # Field-by-field notices — full cred_fp lines often get fully masked in the log.
    print(f"::notice title=username_len::{len(u)}")
    print(f"::notice title=user_sha256_12::{user_sha}")
    print(f"::notice title=password_len::{len(p)}")
    print(f"::notice title=pass_sha256_12::{pass_sha}")
    print(f"::notice title=api_sha1_12::{api_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
