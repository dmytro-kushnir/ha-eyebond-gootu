# Wake-on-LAN (Pi HA → Ubuntu PC)

## Docker (required)
Home Assistant must use **host networking** so the magic packet is a real LAN broadcast.
`privileged: true` is **not** required with `network_mode: host`.

```yaml
network_mode: host
# do not publish ports: when using host networking
```

Same as: `wakeonlan <WOL_TARGET_MAC>` on the Pi host.

## HA config
1. Add `wake_on_lan:` + `input_button.wake_ubuntu_pc` from `configuration.snippet.yaml`
2. Merge `scripts.yaml` and `automation.yaml`
3. Restart HA / reload scripts+automations
4. Call `script.wake_ubuntu_pc` or press the button

Ubuntu receive side: `scripts/install-wol-enp4s0.sh` (`ethtool … wol g`) + BIOS WoL.
