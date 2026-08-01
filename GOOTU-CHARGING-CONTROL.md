# Local Gootu charging control

Added local EyeBond Local catalog/profile so HA can expose a **Charging Priority** dropdown (CPR00–CPR03).

## Files
- `custom_components/eybond_local/protocol_catalogs/profiles/eybond_g_ascii/models/gootu_hybrid_24v.json`
- `custom_components/eybond_local/protocol_catalogs/inverter_catalog.json` (surface + device for 230V/15A/24V/50Hz + SVFW `4.007`)

## Apply
```bash
cd <repo_root>
docker compose restart
```

Then in HA:
1. Wait until collector is online (HA only).
2. Open **EyeBond G-ASCII** / inverter device — model should become **Gootu Hybrid 24V 3.7kW** after re-detect.
3. Look for select **Charging Priority** with options: `CPR00`, `CPR01`, `CPR02`, `CPR03`
4. Control mode should be **Full** or **Auto** (capability is marked tested).

If still “EyeBond G-ASCII family” with no select:
- Settings → Devices & Services → EyeBond Local → **Reload**
- or Restart Collector, wait for re-detect

## Labels = raw commands
Dropdown shows exactly what is sent: `CPR00` / `CPR01` / `CPR02` / `CPR03`.

Schedule example:
```yaml
service: select.select_option
target:
  entity_id: select.living_room_gootu_hybrid_24v_3_7kw_charging_priority
data:
  option: CPR03
```
