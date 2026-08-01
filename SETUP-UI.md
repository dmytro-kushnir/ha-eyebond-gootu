# Home Assistant UI setup (after container install)

Container and custom components are already installed. Complete these steps in the browser.

## Access

- URL: http://<ha_host_ip>:8123
- Timezone in compose: `Europe/Kyiv`
- Config: `<repo_root>/config`
- Backups: `<repo_root>/backups`

## 1. Onboarding

1. Open http://<ha_host_ip>:8123
2. Create your admin user
3. Set location / units as preferred (timezone already `Europe/Kyiv` via Docker)

## 2. Enable HACS

Files are already in `config/custom_components/hacs` (v2.0.5).

1. **Settings → Devices & Services → Add Integration → HACS**
2. Accept terms
3. Complete GitHub device-code authentication

## 3. EyeBond Local (already installed)

`eybond_local` **0.3.0-beta.1** is already in `config/custom_components/eybond_local`
(same result as downloading via HACS custom repository).

Optional — register the repo in HACS for future updates:

1. **HACS → Integrations → ⋮ → Custom repositories**
2. URL: `https://github.com/groove-max/ha-eybond-local`
3. Category: **Integration**

## 4. Configure EyeBond Local

1. **Settings → Devices & Services → Add Integration → EyeBond Local**
2. Prefer collector IP **<collector_ip_1>** (see `DTU-IDENTIFICATION.md`)
3. If scan fails, try **<collector_ip_2>** or manual IP
4. Collector mode: **Cloud + HA** (keeps SmartValue working)
5. Control mode: **Read-only** or **Auto** for first test

## Useful commands

```bash
cd <repo_root>
docker compose ps
docker compose logs -f --tail=100
docker compose restart
```

## Note on Bluetooth warning

HA logs may show missing `NET_ADMIN`/`NET_RAW` for Bluetooth. That only matters for Bluetooth Wi‑Fi setup of the collector. LAN EyeBond discovery does not require it.
