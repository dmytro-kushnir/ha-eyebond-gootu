# ValueClouds / SmartValue — cloud CPR helper for Home Assistant + GitHub Actions
#
# Small shell + Python helper (not a full HACS integration).

## CPR schedule owner: GitHub Actions

Clock schedule runs in [`.github/workflows/valuecloud-cpr.yml`](../../.github/workflows/valuecloud-cpr.yml) (not HA).

Default Kyiv map (used when the variable is empty):

| Time (Europe/Kyiv) | Mode |
|---|---|
| 08:00, 13:00, 17:00 | Utility first |
| 11:00, 15:00, 21:00 | PV only |

### Control without commits (recommended)

Repo → **Settings** → **Secrets and variables** → **Actions** → **Variables**:

| Variable | Purpose |
|---|---|
| `VALUECLOUD_CPR_ENABLED` | `true` / `false` — pause **cron** only (`false` = no timed writes) |
| `VALUECLOUD_CPR_SCHEDULE` | JSON hour→mode (Europe/Kyiv). Example below |

```json
{"8":"Utility first","11":"PV only","13":"Utility first","15":"PV only","17":"Utility first","21":"PV only"}
```

Allowed modes: `Utility first`, `PV first`, `Utility + PV`, `PV only`.

- **Pause timed CPR:** set `VALUECLOUD_CPR_ENABLED=false` (manual **Run workflow** still works)
- **Change times:** edit `VALUECLOUD_CPR_SCHEDULE`, save — next hourly cron picks it up
- **One-off write:** Actions → **ValueCloud CPR** → Run workflow → pick mode
- **Hard stop everything:** Actions → workflow → Disable
- **See result:** open a run → **Summary** tab

### Repo secrets

- `VALUECLOUD_USERNAME`, `VALUECLOUD_PASSWORD`, `VALUECLOUD_PN`, `VALUECLOUD_SN`
- Optional: `VALUECLOUD_DEVCODE` (default 2506), `VALUECLOUD_DEVADDR` (default 1)

## Pi / Home Assistant role

Keep HA for WoL, Companion notify on **manual** CPR, and optional one-off script runs. Leave HA automation `gootu_cpr_schedule` **disabled** in the UI while Actions owns the clock (kept in YAML as fallback).

```bash
mkdir -p config/shell
cp patches/valuecloud/valuecloud_api.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.sh config/shell/
chmod +x config/shell/valuecloud_set_cpr.sh
```

Merge [`configuration.snippet.yaml`](configuration.snippet.yaml) + [`scripts.yaml`](scripts.yaml) + [`automations.yaml`](automations.yaml) (notify only); fill `secrets.yaml`.

## Behaviour

- **Schedule:** GitHub Actions every **15 minutes** + Kyiv gate (DST-safe); at most one write per schedule hour (cache)
- **Manual CPR:** HA script or Actions workflow_dispatch
- **Notifies:** Actions run Summary; HA file-sensor notify for local manual CPR only
- **Grid/line poll:** disabled by default (`valuecloud_poll_status.*` kept if you re-enable later)

DTU must stay on **cloud**. EyeBond Local remains optional under `patches/eybond_local/`.
