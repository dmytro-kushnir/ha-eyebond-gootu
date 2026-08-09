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
| `config/shell/valuecloud_api.py` | Shared login / session / signed requests |
| `config/shell/valuecloud_set_cpr.sh` | HA entry; runs writer in **background** (HA 60s shell limit) |
| `config/shell/valuecloud_set_cpr.py` | Login → `ctrlDevice` → result file |
| `config/shell/valuecloud_poll_status.*` | Poll `sy_status` (Mains / Battery) |
| Script **ValueCloud — set charging priority** | Manual / automation trigger |
| `sensor.valuecloud_cpr_last` / `sensor.valuecloud_mode_event` | Result + mode-change event files |
| Poll every **3 min** | Cloud HTTP status (safe for Wi‑Fi DTU at this rate) |
| Notify automation | CPR result or Mains↔Battery change |
| CPR schedule (clock only; SoC unreliable in PV-only) | see table below |

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
