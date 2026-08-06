#!/usr/bin/env bash
# Install persistent Wake-on-LAN for Ubuntu NIC enp4s0 (run on the Ubuntu host).
set -euo pipefail

IFACE="${WOL_IFACE:-enp4s0}"
UNIT_SRC="$(cd "$(dirname "$0")" && pwd)/wol-enp4s0.service"
UNIT_DST="/etc/systemd/system/wol-${IFACE}.service"

if [[ ! -f "$UNIT_SRC" ]]; then
  echo "Missing $UNIT_SRC" >&2
  exit 1
fi

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ethtool

# Rewrite ExecStart for the chosen iface if needed
tmp="$(mktemp)"
sed "s/enp4s0/${IFACE}/g" "$UNIT_SRC" > "$tmp"
sudo cp "$tmp" "$UNIT_DST"
rm -f "$tmp"

sudo systemctl daemon-reload
sudo systemctl enable --now "wol-${IFACE}.service"
echo "=== status ==="
systemctl status "wol-${IFACE}.service" --no-pager || true
echo "=== ethtool ==="
sudo ethtool "$IFACE" | grep -i wake || true
echo "Done. Expect Wake-on: g"
