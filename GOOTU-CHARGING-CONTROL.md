# Gootu charging priority (CPR)

## Recommended: GitHub Actions schedule + optional HA on Pi

Timed CPR writes run in **GitHub Actions** (same ValueClouds API as the website). Home Assistant on the Pi stays useful for **WoL**, **Companion notifies**, and **manual** CPR — not for the clock schedule.

See [patches/valuecloud/README.md](patches/valuecloud/README.md) and [`.github/workflows/valuecloud-cpr.yml`](.github/workflows/valuecloud-cpr.yml).

| Piece | Role |
|---|---|
| GitHub Actions `ValueCloud CPR` | Clock schedule (Europe/Kyiv) + manual dispatch |
| `patches/valuecloud/valuecloud_schedule_gate.py` | Kyiv hour gate; reads Actions variables |
| Actions variables `VALUECLOUD_CPR_*` | Pause / edit schedule in GitHub UI (no commit) |
| `patches/valuecloud/valuecloud_set_cpr.py` | Login → `ctrlDevice` → result |
| Actions secrets `VALUECLOUD_*` | SmartValue credentials + device `pn` / `sn` |
| Pi `script.valuecloud_set_charging_priority` | Manual CPR from HA |
| Pi `sensor.valuecloud_cpr_last` + notify automation | Companion on **local** manual CPR result file |
| Pi WoL | Unrelated; keep as-is |

**Keep** HA automation `gootu_cpr_schedule` in YAML but **disabled** in the UI while Actions owns the clock — re-enable only if Actions is paused.

### CPR schedule (Europe/Kyiv)

| Time | Mode | Why |
|---|---|---|
| **08:00** | Utility first | Morning top-up from grid |
| **11:00** | PV only | Rest from grid float |
| **13:00** | Utility first | Midday grid charge |
| **15:00** | PV only | Rest again |
| **17:00** | Utility first | Late-day top-up |
| **21:00** | PV only | Night quiet until morning |

Do **not** drive CPR from battery % — ValueClouds SoC is wrong while in PV only.

```text
GitHub Actions (hourly) or workflow_dispatch
        → valuecloud_schedule_gate.py (Europe/Kyiv)
        → valuecloud_set_cpr.py
        → login api.valueclouds.com
        → ctrlDevice cltd_charging_priority
        → inverter ACK via DTU cloud link
```

DTU must stay on **cloud**.

---

## EyeBond Local path (optional / backward compatible)

**Patch:** `patches/eybond_local/gootu.patch.json`

```bash
bash patches/eybond_local/apply.sh
```

Local CPR examples: `patches/eybond_local/automations.yaml` (uses `select.*_charging_priority`).  
Extras (callback, local notifies): `patches/eybond_local/automations_extra.yaml`.
