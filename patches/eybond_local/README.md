# Gootu local patch (EyeBond Local)

Everything lives in **`gootu.patch.json`**. Apply with:

```bash
bash patches/eybond_local/apply.sh
```

Helper files (not the patch itself):
- `apply.sh` — installer
- `automations.yaml` — day/night CPR examples derived from the schedule block in the patch

Also optional: `automations_extra.yaml` (periodic Request Callback + CPR notify).
