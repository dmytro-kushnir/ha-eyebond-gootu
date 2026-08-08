# ValueClouds / SmartValue — cloud CPR helper for Home Assistant
#
# This is a small shell + Python helper (not a full HACS integration).
# Keep it in this repo next to the EyeBond/Gootu notes. A separate repo only
# makes sense later if you turn it into a reusable custom component.

## Install on an HA host

```bash
mkdir -p config/shell
cp patches/valuecloud/valuecloud_set_cpr.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.sh config/shell/
chmod +x config/shell/valuecloud_set_cpr.sh
```

Merge the YAML snippets (or copy pieces into your existing files):

- `configuration.snippet.yaml` → `configuration.yaml`
- `scripts.yaml` → `scripts.yaml`
- `automations.yaml` → `automations.yaml` (replace `notify.YOUR_NOTIFY_ENTITY`)

Add secrets (see `config/secrets.yaml.example`):

```yaml
valuecloud_username: your_smartvalue_email
valuecloud_password: your_smartvalue_password
valuecloud_pn: YOUR_COLLECTOR_PN
valuecloud_sn: YOUR_DEVICE_SN
valuecloud_devcode: 2506
valuecloud_devaddr: 1
```

Find `pn` / `sn` / `devcode` from ValueClouds web (browser network tab on device page) or SmartValue.

Restart HA (or reload Shell Command + Scripts + Automations + Command Line).

## How it works

See [GOOTU-CHARGING-CONTROL.md](../../GOOTU-CHARGING-CONTROL.md).

DTU must stay on **cloud**. EyeBond Local is optional and independent (kept under `patches/eybond_local/` for local/LAN use).
