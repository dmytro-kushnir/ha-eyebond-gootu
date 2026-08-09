# ValueClouds / SmartValue — cloud CPR + status helper for Home Assistant
#
# Small shell + Python helper (not a full HACS integration).

## Install

```bash
mkdir -p config/shell
cp patches/valuecloud/valuecloud_api.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.sh config/shell/
cp patches/valuecloud/valuecloud_poll_status.py config/shell/
cp patches/valuecloud/valuecloud_poll_status.sh config/shell/
chmod +x config/shell/valuecloud_set_cpr.sh config/shell/valuecloud_poll_status.sh
```

Merge YAML snippets; replace `notify.YOUR_NOTIFY_ENTITY`; fill secrets.

## Behaviour

- **CPR schedule:** 08/13/17 Utility first, 11/15/21 PV only (clock only; do not use SoC in PV-only)
- **Status poll:** every **3 minutes** via ValueClouds HTTP (`queryDeviceOneDataxxx`) — not local G-ASCII. Safe for the Wi‑Fi stick at this rate; apps refresh more often when open.
- **Notifies:** CPR result + Mains↔Battery mode changes
- **SD-friendly:** unchanged polls do not append logs; file sensors scan every 60s; exclude ValueCloud sensors from recorder

DTU must stay on **cloud**. EyeBond Local remains optional under `patches/eybond_local/`.
