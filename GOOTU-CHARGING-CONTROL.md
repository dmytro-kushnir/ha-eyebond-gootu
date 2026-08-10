# Gootu charging priority (CPR)

## Recommended: Home Assistant on the Pi (primary)

Timed CPR runs from **HA automations** (Europe/Kyiv clock). GitHub Actions can stay as a paused backup — its `schedule` event is often late or skipped.

See [patches/valuecloud/README.md](patches/valuecloud/README.md).

| Piece | Role |
|---|---|
| HA `gootu_cpr_schedule` | Primary clock: 08/14/17 Utility first, 11/15/21 PV only |
| `patches/valuecloud/valuecloud_set_cpr.py` | Login → `ctrlDevice` (treats Device unresponsive as soft OK) |
| Pi secrets + shell scripts | Credentials on the HA host |
| `sensor.valuecloud_cpr_last` + notify | Companion on HA CPR result |
| GitHub Actions (optional) | Manual/backup only — keep disabled or `VALUECLOUD_CPR_ENABLED=false` |

**Do not** run HA schedule and Actions cron at the same time — double writes.

### CPR schedule (Europe/Kyiv)

| Time | Mode | Why |
|---|---|---|
| **08:00** | Utility first | Morning top-up from grid |
| **11:00** | PV only | Rest from grid float |
| **14:00** | Utility first | Afternoon grid charge |
| **15:00** | PV only | Rest again |
| **17:00** | Utility first | Late-day top-up |
| **21:00** | PV only | Night quiet until morning |

Do **not** drive CPR from battery % — ValueClouds SoC is wrong while in PV only.

```text
HA time trigger (or manual script)
        → shell_command → valuecloud_set_cpr.sh
        → login api.valueclouds.com
        → ctrlDevice cltd_charging_priority
        → inverter via DTU cloud link
        → valuecloud_last_result.txt → notify
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
