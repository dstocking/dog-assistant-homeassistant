# Dog Assistant

[![Validate](https://github.com/dstocking/dog-assistant-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/dstocking/dog-assistant-homeassistant/actions/workflows/validate.yml)
[![Test](https://github.com/dstocking/dog-assistant-homeassistant/actions/workflows/test.yml/badge.svg)](https://github.com/dstocking/dog-assistant-homeassistant/actions/workflows/test.yml)
[![hacs](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

A local, no-cloud [Home Assistant](https://www.home-assistant.io/) integration to track everyday dog
care: **feeding**, **walks**, **poo**, and **pee**. Tap a button (or call a service) to log an event, and
the integration keeps running counts, timestamps, and a full history you can graph and review over time.

It is purely **local** — no account, no external service, no network calls. Everything is stored
on your Home Assistant instance.

## Features

- One **button per activity** — press to record it at the current time.
- Configurable **daily targets** for feeding and walks, with **remaining** and **due** sensors.
- A **timestamp** of when each activity last happened (shown as "5 minutes ago" in the UI).
- A per-activity **event entity**, so every record is a discrete entry in the **Logbook** and history.
- **Service actions** (`dog_assistant.record_*`) that accept optional details (portion, food, who fed,
  walk duration/distance, poo quality, notes) — perfect for automations, dashboards, or voice.
- Counts and timestamps **persist across restarts** and feed **long-term statistics**.

## Entities

All entities are grouped under a single device named after your dog (`<dog>` below is your dog's name).

| Entity | feeding | walk | poo | pee | Notes |
|--------|:------:|:----:|:---:|:---:|-------|
| `button.<dog>_feed` / `_walk` / `_poo` / `_pee` | ✓ | ✓ | ✓ | ✓ | Press to record now |
| `sensor.<dog>_feedings_today` (and walk/poo/pee) | ✓ | ✓ | ✓ | ✓ | Count in the current day |
| `sensor.<dog>_last_fed` / `_last_walk` / `_last_poo` / `_last_pee` | ✓ | ✓ | ✓ | ✓ | Timestamp of last record |
| `sensor.<dog>_feedings_remaining` / `_walks_remaining` | ✓ | ✓ | — | — | Target minus today's count |
| `binary_sensor.<dog>_feeding_due` / `_walk_due` | ✓ | ✓ | — | — | On while still due today |
| `event.<dog>_feeding` / `_walk` / `_poo` / `_pee` | ✓ | ✓ | ✓ | ✓ | Fires on each record |

## Installation

### HACS (custom repository)

1. In Home Assistant, open **HACS**.
2. Click the **⋮** menu (top-right) → **Custom repositories**.
3. Add the repository URL `https://github.com/dstocking/dog-assistant-homeassistant` and choose the
   category **Integration**, then click **Add**.
4. Find **Dog Assistant** in HACS, click **Download**, and **restart Home Assistant**.
5. Go to **Settings → Devices & Services → Add Integration**, search for **Dog Assistant**, and follow
   the setup.

### Manual

Copy `custom_components/dog_assistant` into your Home Assistant `config/custom_components/` directory and
restart Home Assistant, then add the integration from **Settings → Devices & Services**.

## Configuration

Setup and all settings are done in the UI — no YAML.

**Setup parameters** (asked when you add the integration):

| Field | Description | Default |
|-------|-------------|---------|
| Dog's name | Names the device and its entities. | — |
| Feedings per day | Daily target used for *remaining* and *due*. | 2 |
| Walks per day | Daily target used for *remaining* and *due*. | 2 |

**Options** (Settings → Devices & Services → Dog Assistant → **Configure**):

| Option | Description | Default |
|--------|-------------|---------|
| Feedings per day | Daily feeding target. | 2 |
| Walks per day | Daily walk target. | 2 |
| Daily reset time | Time of day the daily counters reset to zero. | 00:00:00 |

To rename the dog later, use **Configure → Reconfigure** on the integration entry.

## Actions (services)

Each activity has a `record_*` service. All detail fields are optional; the button is equivalent to
calling the service with no details.

- `dog_assistant.record_feeding` — `portion`, `food`, `fed_by`
- `dog_assistant.record_walk` — `duration` (min), `distance` (km), `walked_by`
- `dog_assistant.record_poo` — `quality` (`normal`/`soft`/`hard`/`diarrhea`), `location`, `notes`
- `dog_assistant.record_pee` — `location`, `notes`

```yaml
action: dog_assistant.record_feeding
data:
  portion: "1 cup"
  food: kibble
  fed_by: Dana
```

## Use cases & examples

**Remind us if the dog hasn't been fed by evening:**

```yaml
alias: Feeding reminder
triggers:
  - trigger: time
    at: "19:00:00"
conditions:
  - condition: state
    entity_id: binary_sensor.joie_feeding_due
    state: "on"
actions:
  - action: notify.family
    data:
      message: "Joie still needs feeding today."
```

**Log a feeding by voice** ("Hey Google, record feeding") by exposing `dog_assistant.record_feeding` to
your assistant, or by putting the buttons on a dashboard for one-tap logging.

## How the data updates

There is nothing to poll — state changes the instant you press a button or call a service. Counts are
derived from a stored event log filtered to the current day (defined by the reset time), so they are
always consistent, survive restarts, and reset automatically at the configured time. The `*_today`
sensors also feed Home Assistant's long-term statistics for trend graphs.

## Known limitations

- Tracks a **single dog** (one config entry). Multi-pet support is not yet available.
- Poo and pee are **occurrence logs** only — they have no daily target, "remaining", or "due" sensors.
- The reset time defines a fixed daily window; there is no per-activity schedule.

## Troubleshooting

- **Entities missing after install?** Ensure you restarted Home Assistant and added the integration from
  Settings → Devices & Services.
- **A service call errors with "not set up yet"?** The integration entry is not loaded — add or reload it.
- Download **diagnostics** from the integration entry (⋮ → Download diagnostics) when reporting an issue.

## Removal

Go to **Settings → Devices & Services → Dog Assistant**, open the ⋮ menu on the entry, and choose
**Delete**. If installed through HACS, you can then remove it from HACS as well. The stored event log in
`.storage/dog_assistant.*` is removed with the entry.

## Contributing

Issues and PRs welcome at
[github.com/dstocking/dog-assistant-homeassistant](https://github.com/dstocking/dog-assistant-homeassistant).

## License

[MIT](LICENSE)
