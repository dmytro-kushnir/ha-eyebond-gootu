#!/usr/bin/env bash
# Apply the single Gootu local patch (gootu.patch.json) onto installed ha-eybond-local.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CC="$ROOT/config/custom_components/eybond_local"
PATCH="$(cd "$(dirname "$0")" && pwd)/gootu.patch.json"

if [[ ! -f "$PATCH" ]]; then
  echo "Missing $PATCH" >&2
  exit 1
fi
if [[ ! -d "$CC/protocol_catalogs" ]]; then
  echo "EyeBond Local not found at $CC — install via HACS first." >&2
  exit 1
fi

python3 - "$PATCH" "$CC" <<'PY'
import json, sys
from pathlib import Path

patch = json.loads(Path(sys.argv[1]).read_text())
cc = Path(sys.argv[2])
models = cc / "protocol_catalogs/profiles/eybond_g_ascii/models"
models.mkdir(parents=True, exist_ok=True)
profile_name = patch.get("profile_filename", "gootu_hybrid_24v.json")
(models / profile_name).write_text(json.dumps(patch["profile"], indent=2, ensure_ascii=False) + "\n")

catalog_path = cc / "protocol_catalogs/inverter_catalog.json"
data = json.loads(catalog_path.read_text())
surface = patch["catalog"]["surface"]
device = patch["catalog"]["device"]

surfaces = [s for s in data.get("surfaces", []) if s.get("key") != surface["key"]]
devices = [d for d in data.get("devices", []) if d.get("entry_key") != device["entry_key"]]
insert_at = next((i for i, s in enumerate(surfaces) if s.get("key") == "eybond_g_ascii_read_only"), len(surfaces))
surfaces.insert(insert_at, surface)
insert_at = next((i for i, d in enumerate(devices) if d.get("entry_key") == "eybond_g_ascii_family"), len(devices))
devices.insert(insert_at, device)
data["surfaces"] = surfaces
data["devices"] = devices
catalog_path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")

sched = patch.get("schedule", {})
print(f"Applied profile -> {models / profile_name}")
print(f"Applied catalog surface/device into {catalog_path}")
print(
  "Schedule hint: "
  f"{sched.get('day_start')} → {sched.get('day_option')!r}; "
  f"{sched.get('quiet_start')} → {sched.get('quiet_option')!r} "
  f"on {sched.get('entity_id')}"
)
PY

echo "Done. Reload EyeBond Local (or: docker compose restart)."
