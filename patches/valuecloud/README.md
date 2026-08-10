# ValueClouds / SmartValue — cloud CPR helper for Home Assistant (+ optional Actions backup)
#
# Small shell + Python helper (not a full HACS integration).

## Primary: Home Assistant on the Pi (recommended)

HA timezone clock is reliable for on-the-hour CPR. Merge [`automations.yaml`](automations.yaml):

| Time (Europe/Kyiv) | Mode |
|---|---|
| 08:00, 14:00, 17:00 | Utility first |
| 11:00, 15:00, 21:00 | PV only |

Keep GitHub Actions **disabled** or `VALUECLOUD_CPR_ENABLED=false` so you do not double-write.

```bash
mkdir -p config/shell
cp patches/valuecloud/valuecloud_api.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.sh config/shell/
chmod +x config/shell/valuecloud_set_cpr.sh
```

Merge [`configuration.snippet.yaml`](configuration.snippet.yaml) + [`scripts.yaml`](scripts.yaml) + [`automations.yaml`](automations.yaml); fill `secrets.yaml`.  
Phone notify: `valuecloud_notify` when manual/HA CPR updates the result file.

## Optional backup: GitHub Actions

Workflow [`.github/workflows/valuecloud-cpr.yml`](../../.github/workflows/valuecloud-cpr.yml) can still run timed CPR, but GitHub `schedule` is often late/skipped. Use only if the Pi is down:

1. Disable HA automation `gootu_cpr_schedule`
2. Enable the workflow + set `VALUECLOUD_CPR_ENABLED=true`
3. Edit `VALUECLOUD_CPR_SCHEDULE` JSON if needed

## Repo secrets (Actions only)

- `VALUECLOUD_USERNAME`, `VALUECLOUD_PASSWORD`, `VALUECLOUD_PN`, `VALUECLOUD_SN`
- Optional: `VALUECLOUD_DEVCODE` / `VALUECLOUD_DEVADDR`

## Behaviour

- **Schedule:** HA time triggers (primary)
- **Manual CPR:** HA script or Actions workflow_dispatch
- **Notifies:** HA Companion on local CPR result file
- **Grid/line poll:** disabled by default

DTU must stay on **cloud**. EyeBond Local remains optional under `patches/eybond_local/`.
