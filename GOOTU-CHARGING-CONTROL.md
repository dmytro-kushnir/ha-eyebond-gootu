# Local Gootu patch (vs upstream EyeBond Local)

**One patch file:** `patches/eybond_local/gootu.patch.json`  
(profile CPR+OPR, catalog fingerprint, day/night schedule hint)

```bash
bash patches/eybond_local/apply.sh
```

Then reload EyeBond Local.

## Automations (integrated)

`configuration.yaml` already has:

```yaml
automation: !include automations.yaml
```

Rules are in `config/automations.yaml` (mirrored in `patches/eybond_local/automations.yaml`).

Reload: **Developer Tools → YAML → Check configuration → Automations → Reload**  
(or restart HA). Then check **Settings → Automations** for both Gootu entries.

| Time (HA / Kyiv) | Mode |
|---|---|
| **09:00** | Utility first |
| **21:00** | PV only |

Note: live **Charging Mode Code** `0` corresponds to **PV only** on this Gootu (not the same register as CPR labels, but matches when PV-only is active).


To run once now (without waiting): open the automation → **Run**.

## Controls

| Select | Status |
|---|---|
| Charging Priority (CPR) | Verified |
| Output Priority (OPR) | Test once before automating |

Charge-current writes not included (no effect on this unit).
