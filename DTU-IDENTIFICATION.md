# EyeBond / WFBLE DTU Identification

Scanned: 2026-07-31T22:39:38+03:00  
HA host: **<ha_host_ip>** (`http://<ha_host_ip>:8123`)

## Conclusion

**Most likely EyeBond / WFBLE DTU: `<collector_ip_1>` (Bouffalolab_BL602)**

| IP | Hostname / chip | MAC | Ping | HTTP | TCP 8899 | Assessment |
|---|---|---|---|---|---|---|
| **<collector_ip_1>** | Bouffalolab_BL602 | `<collector_mac_1>` | OK (ttl=64) | refused | closed | **Primary candidate** — EyeBond WFBLE modules commonly use BL602 |
| **<collector_ip_2>** | BP_WFC_OEM | `<collector_mac_2>` | OK (ttl=255) | refused | closed | Secondary — name suggests WiFi collector OEM; confirm with EyeBond Local scan |

Neither host exposes a web UI or listens on TCP 8899. That is **expected**: EyeBond collectors receive UDP discovery (port **58899**) and then open an **outbound** TCP connection to Home Assistant on **8899**.

UDP unicast probes to both IPs on 58899 produced no reply within 2s (common when the collector is already bound to the vendor cloud). Use EyeBond Local quick/deep scan or manual IP `<collector_ip_1>` for definitive confirmation.

## ICMP ping

### <collector_ip_1> (Bouffalolab_BL602)

```
PING <collector_ip_1> (<collector_ip_1>) 56(84) bytes of data.
64 bytes from <collector_ip_1>: icmp_seq=1 ttl=64 time=3.17 ms
64 bytes from <collector_ip_1>: icmp_seq=2 ttl=64 time=4.20 ms
64 bytes from <collector_ip_1>: icmp_seq=3 ttl=64 time=4.90 ms
3 packets transmitted, 3 received, 0% packet loss
```

### <collector_ip_2> (BP_WFC_OEM)

```
PING <collector_ip_2> (<collector_ip_2>) 56(84) bytes of data.
64 bytes from <collector_ip_2>: icmp_seq=1 ttl=255 time=28.5 ms
64 bytes from <collector_ip_2>: icmp_seq=2 ttl=255 time=1.95 ms
64 bytes from <collector_ip_2>: icmp_seq=3 ttl=255 time=2.37 ms
3 packets transmitted, 3 received, 0% packet loss
```

## Neighbor / MAC

```
<collector_ip_2> dev <lan_iface> lladdr <collector_mac_2>
<collector_ip_1> dev <lan_iface> lladdr <collector_mac_1>
```

## TCP port scan

Both hosts: ports 22, 23, 80, 443, 502, 8080, 8899, 1883 — **closed**.

## HTTP checks

- `http://<collector_ip_1>/` — connection refused  
- `http://<collector_ip_2>/` — connection refused  

## UDP 58899

- Privileged `nmap -sU` skipped (sudo password required).  
- Application-level UDP probe (`set>server=<ha_host_ip>:8899;`) — no reply from either IP within 2s.

## Next step in HA

1. Prefer collector IP **<collector_ip_1>** in EyeBond Local.  
2. If that fails, try **<collector_ip_2>**.  
3. Collector mode: **Cloud + HA** (keeps SmartValue working).  
4. Control mode: **Read-only** or **Auto** for first test.
