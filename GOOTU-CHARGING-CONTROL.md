# Gootu charging priority (CPR)

Two ways to drive CPR from Home Assistant:

1. **ValueClouds cloud (recommended when LAN polls stall)** — `patches/valuecloud/`  
   See below and [patches/valuecloud/README.md](patches/valuecloud/README.md).
2. **EyeBond Local (LAN)** — `patches/eybond_local/`  
   Local select entity; kept for backward compatibility.

---

## ValueClouds via Home Assistant (cloud write-only)

HA switches charging priority by calling the same **ValueClouds / SmartValue** API as the website. No EyeBond Local required. No live cloud sensors — **write-only**.

| Piece | Role |
|---|---|
| `secrets.yaml` | SmartValue email + password + device `pn` / `sn` |
| `config/shell/valuecloud_set_cpr.sh` | HA entry; runs writer in **background** (HA 60s shell limit) |
| `config/shell/valuecloud_set_cpr.py` | Login → `ctrlDevice` → result file + log |
| Script **ValueCloud — set charging priority** | Manual / automation trigger |
| `sensor.valuecloud_cpr_last` | Last OK/FAILED line |
| Notify automation | Phone when result changes |
| 09:00 / 21:00 automations | Utility first / PV only |

```text
Automation or manual script
        → shell_command → valuecloud_set_cpr.sh (returns immediately)
        → (background) login api.valueclouds.com
        → ctrlDevice cltd_charging_priority
        → inverter ACK via DTU cloud link
        → valuecloud_last_result.txt → sensor → notify
```

DTU must stay on **cloud**. Install steps: [patches/valuecloud/README.md](patches/valuecloud/README.md).

Debug:

```bash
docker exec homeassistant tail -40 /config/shell/valuecloud_cpr.log
docker exec homeassistant cat /config/shell/valuecloud_last_result.txt
```

---

## EyeBond Local path (optional / backward compatible)

**Patch:** `patches/eybond_local/gootu.patch.json`

```bash
bash patches/eybond_local/apply.sh
```

Local CPR examples: `patches/eybond_local/automations.yaml` (uses `select.*_charging_priority`).  
Extras (callback, local notifies): `patches/eybond_local/automations_extra.yaml`.
