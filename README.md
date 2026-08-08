# Home Assistant + EyeBond (Gootu) — portable setup

Docker Home Assistant on a data disk, with notes for:

- **EyeBond Local** (LAN) + Gootu hybrid patch
- **ValueClouds / SmartValue cloud CPR** helper (schedule charging priority without local polls)

## Clone on another machine

```bash
git clone <your-repo-url> homeassistant
cd homeassistant
mkdir -p config backups
cp config/secrets.yaml.example config/secrets.yaml
# edit secrets — never commit the real file
docker compose pull
docker compose up -d
```

Open `http://<host-ip>:8123` and finish onboarding.

## What is in git

- `docker-compose.yml` — HA stable, `network_mode: host`, `TZ=Europe/Kyiv`
- `patches/eybond_local/` — Gootu catalog/profile patch + local automation examples
- `patches/valuecloud/` — ValueClouds cloud CPR scripts + HA YAML snippets
- Docs: setup, DTU notes, [GOOTU-CHARGING-CONTROL.md](GOOTU-CHARGING-CONTROL.md)
- `.gitignore` — excludes DB, `.storage`, secrets, logs, EyeBond support/proxy packages

## What is NOT in git (on purpose)

- `config/.storage/` (auth, entity registry, tokens)
- `config/home-assistant_v2.db*`
- `config/secrets.yaml` (credentials, collector PN/SN)
- `config/eybond_local/support_packages/` and `proxy_traces/`
- `config/shell/.valuecloud_session.json`, `valuecloud_cpr.log`, result files
- `backups/`

## ValueClouds cloud CPR (optional)

Small helper — **not** a full HACS integration. Same repo is enough; split out only if you later build a reusable custom component.

```bash
mkdir -p config/shell
cp patches/valuecloud/valuecloud_set_cpr.py config/shell/
cp patches/valuecloud/valuecloud_set_cpr.sh config/shell/
chmod +x config/shell/valuecloud_set_cpr.sh
# merge patches/valuecloud/*.yaml snippets; fill secrets.yaml
```

Details: [patches/valuecloud/README.md](patches/valuecloud/README.md) and [GOOTU-CHARGING-CONTROL.md](GOOTU-CHARGING-CONTROL.md).

DTU must remain on the ValueClouds/SmartValue **cloud** for writes to reach the inverter.

## Gootu local patch (EyeBond Local)

Single file vs upstream: `patches/eybond_local/gootu.patch.json`

```bash
bash patches/eybond_local/apply.sh
```

Install HACS + EyeBond Local on each machine (or point HACS at your fork with the Gootu catalog patch). Day/night local CPR examples: `patches/eybond_local/automations.yaml`.

## Upstream references

- EyeBond Local: https://github.com/groove-max/ha-eybond-local  
- HACS custom repositories: https://www.hacs.xyz/docs/faq/custom_repositories/
