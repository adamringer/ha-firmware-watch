# Firmware Watch

A Home Assistant integration that checks vendor firmware web pages once a day
and tells you when a new version appears. Many devices have no update
integration; this gives them an `update` entity and an alert anyway.

## Install (HACS)

1. In HACS, open the menu, choose **Custom repositories**, and add
   `https://github.com/OWNER/ha-firmware-watch` with category **Integration**.
2. Install **Firmware Watch** and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration > Firmware Watch**.

## Adding a source

Each watched page is one entry. Pick either:

- **A built-in page:** CarPodGo T4 Plus, Ambient Weather WS-2000, Yamaha TSR-7850.
- **A custom page:** a name, the page URL, and a regular expression with
  exactly one capture group around the version. The expression is run against
  the page's visible text (HTML tags removed). Examples:
  - `ObserverIP Firmware ([0-9.]+)`
  - `Firmware Update:\s*Version\s+([0-9][0-9A-Za-z._-]*)`

When you add a source, the integration downloads the page once to check that
the pattern matches.

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
the entity is unavailable. Fix a custom pattern by removing and re-adding the
source.
