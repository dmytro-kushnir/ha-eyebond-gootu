#!/usr/bin/env python3
"""Send a Companion-style message via Home Assistant REST (notify.send_message)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", required=True)
    parser.add_argument(
        "--entity",
        default=os.environ.get("HA_NOTIFY_ENTITY") or "notify.dk_ha_bd",
    )
    args = parser.parse_args()

    base = (os.environ.get("HA_URL") or "").rstrip("/")
    token = (os.environ.get("HA_TOKEN") or "").strip()
    if not base or not token:
        print("HA_URL/HA_TOKEN not set — skip notify", file=sys.stderr)
        return 0

    url = f"{base}/api/services/notify/send_message"
    body = json.dumps(
        {"entity_id": args.entity, "message": args.message},
        ensure_ascii=False,
    ).encode("utf-8")
    req = Request(
        url=url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as resp:
            print(f"HA notify HTTP {resp.status}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        print(f"HA notify failed HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"HA notify unreachable: {exc.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
