# Home Assistant + EyeBond (Gootu) — portable setup

Docker Home Assistant on a data disk, with notes for EyeBond Local / Gootu hybrid.

## Clone on another machine

```bash
git clone <your-repo-url> homeassistant
cd homeassistant
mkdir -p config backups
# optional: copy secrets template
cp config/secrets.yaml.example config/secrets.yaml   # if present
docker compose pull
docker compose up -d
```

Open `http://<host-ip>:8123` and finish onboarding.

## What is in git

- `docker-compose.yml` — HA stable, `network_mode: host`, `TZ=Europe/Kyiv`
- Docs: setup, DTU notes, Gootu charging control
- `.gitignore` — excludes DB, `.storage`, secrets, logs, EyeBond support/proxy packages

## What is NOT in git (on purpose)

- `config/.storage/` (auth, entity registry, tokens)
- `config/home-assistant_v2.db*`
- `config/secrets.yaml`
- `config/eybond_local/support_packages/` and `proxy_traces/`
- `backups/`

Install HACS + EyeBond Local on each machine (or point HACS at your fork with the Gootu catalog patch).

## Gootu local patch

See [GOOTU-CHARGING-CONTROL.md](GOOTU-CHARGING-CONTROL.md). Best long-term: keep the catalog/profile changes in a **fork of ha-eybond-local** and install that via HACS, instead of vendoring all of `custom_components/` here.
