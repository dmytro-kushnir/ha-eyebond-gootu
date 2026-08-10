# ValueClouds / SmartValue — cloud CPR helper for Home Assistant + GitHub Actions
#
# Small shell + Python helper (not a full HACS integration).

## CPR schedule owner: GitHub Actions

Clock schedule runs in [`.github/workflows/valuecloud-cpr.yml`](../../.github/workflows/valuecloud-cpr.yml) (not HA), so the Pi is not required for timed writes.

| Time (Europe/Kyiv) | Mode |
|---|---|
| 08:00, 13:00, 17:00 | Utility first |
| 11:00, 15:00, 21:00 | PV only |

Edit hours/modes in [`valuecloud_schedule_gate.py`](valuecloud_schedule_gate.py) (`HOUR_TO_MODE`), push, done.

**Control from GitHub**

- Change schedule → edit `HOUR_TO_MODE` / workflow, commit + push
- Pause schedule → Actions → **ValueCloud CPR** → ⋯ → Disable workflow
- One-off write → Actions → **ValueCloud CPR** → Run workflow → pick mode
- See last result → open a run → **Summary** tab (OK / FAILED / skipped + mode)

**Repo secrets** (Settings → Secrets and variables → Actions):

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

- **Schedule:** GitHub Actions hourly cron + Kyiv gate (DST-safe)
- **Manual CPR:** HA script or Actions workflow_dispatch
- **Notifies:** Actions run status in GitHub UI; HA file-sensor notify for local manual CPR only
- **Grid/line poll:** disabled by default (`valuecloud_poll_status.*` kept if you re-enable later)

DTU must stay on **cloud**. EyeBond Local remains optional under `patches/eybond_local/`.
