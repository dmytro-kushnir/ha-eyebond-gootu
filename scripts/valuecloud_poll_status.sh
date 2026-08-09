#!/bin/sh
# Background status poll — HA shell_command hard-limits at 60s.
set -eu
mkdir -p /config/shell
nohup python3 /config/shell/valuecloud_poll_status.py \
  >/dev/null 2>>/config/shell/valuecloud_status.log &
exit 0
