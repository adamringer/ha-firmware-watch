# Firmware Watch

A Home Assistant integration that checks vendor firmware web pages once a day
and tells you when a new version appears. Many devices have no update
integration; this gives them an `update` entity and an alert anyway.

## Install (HACS)

1. In HACS, open the menu, choose **Custom repositories**, and add
   `https://github.com/adamringer/ha-firmware-watch` with category **Integration**.
2. Install **Firmware Watch** and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration > Firmware Watch**.

## Adding a source

Each watched page is one entry. Nothing is built in: you enter three things.

- **Name:** what the update entity is called.
- **Page URL:** the vendor's firmware page (`http://` or `https://`).
- **Pattern:** a regular expression with exactly one capture group around the
  version. It is run against the page's visible text (HTML tags removed) and is
  case sensitive.

When you add a source, the integration downloads the page once and shows the
version it found, so you can check the pattern before saving.

## Examples

Patterns checked against the live pages on 2026-10-04.

| Name | URL | Pattern | Version found |
| --- | --- | --- | --- |
| CarPodGo T4 Plus | `https://www.carpodgo.com/pages/firmware-t4-plus` | `T4 Plus Firmware Update:\s*Version\s+([0-9][0-9A-Za-z._-]*)` | 0.0.22 |
| Ambient Weather WS-2000/WS-4000/WS-5000 | `https://ambientweather.com/firmware-update-alerts` | `WS-2000/WS-4000/WS-5000 Firmware ver\.?\s*([0-9][0-9A-Za-z._-]*)` | 2.0.4 |
| Ambient Weather ObserverIP | `https://ambientweather.com/firmware-update-alerts` | `ObserverIP Firmware ([0-9.]+)` | 4.6.2 |
| Yamaha TSR-7850 | `https://usa.yamaha.com/products/audio_visual/av_receivers_amps/tsr-7850/downloads.html` | `TSR-7850\S* Firmware Update Ver\.?\s*([0-9][0-9A-Za-z._-]*)` | 2.17 |

### Writing a pattern

- Anchor on text unique to your product's line, so other products on the same
  page don't match.
- The first match on the page wins. Pages that list the newest version first
  work well.
- Use `\s*` or `\s+` for spacing between words, and `\S*` to skip a run of
  model names.
- `[0-9][0-9A-Za-z._-]*` captures most version strings.

## How "new" works

- The first version read is the **baseline**.
- If the page later shows a different version (any difference counts; versions
  are compared as text, not ordered), the update entity turns **on**.
- Each change alerts once, even across restarts.
- Pressing **Install** on the update entity means "acknowledged": the latest
  version becomes the new baseline. Nothing is installed.
- Home Assistant's **Skip** also works as usual.

## Notifications

A new version always creates a persistent notification (dismissed when you
acknowledge). In the integration's **Configure** options you can also choose
notify services (for example a phone's `mobile_app_*` service) to receive a
push message. Option changes apply immediately.

## Checking

The page is fetched once a day. The **Check now** button fetches it right away.

## Troubleshooting

If the update entity is **unavailable**, the page could not be downloaded or
the pattern no longer matches (the vendor may have changed the page). The reason
is in the Home Assistant log. It retries every hour until a check succeeds,
and **Check now** stays available. Your baseline is kept, and no alert is sent while
the entity is unavailable. Fix a pattern by removing and re-adding the
source.
