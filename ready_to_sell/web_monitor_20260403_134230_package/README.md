# Website Monitor — Uptime & Change Detection with Email Alerts

Monitor websites for downtime and content changes. Get an email the moment
something goes wrong — not after you notice it yourself.

## Install

```bash
pip install requests
```

## Quick start

```bash
# Check a single URL once and exit
python web_monitor_20260403_134230.py --url https://yoursite.com --once

# Monitor continuously (check every 5 minutes)
python web_monitor_20260403_134230.py --url https://yoursite.com

# Monitor multiple URLs from a file
python web_monitor_20260403_134230.py --urls sites.txt --interval 60
```

`sites.txt` — one URL per line, lines starting with `#` are ignored:
```
https://mysite.com
https://client-site.com
# https://this-one-is-paused.com
```

## Email alerts

You'll need a Gmail **App Password** (not your regular password):

1. Go to your Google Account → Security
2. Enable 2-Step Verification if not already on
3. Search for "App passwords" in the search bar
4. Select app: Mail → device: Other → name it "web-monitor" → Generate
5. Copy the 16-character password shown (spaces are fine to include)

```bash
python web_monitor_20260403_134230.py \
  --urls sites.txt \
  --interval 60 \
  --alert-email you@gmail.com \
  --from-email sender@gmail.com \
  --smtp-password "abcd efgh ijkl mnop"
```

Non-Gmail SMTP: add `--smtp-host mail.yourdomain.com --smtp-port 465`

## What gets alerted

| Event | Alert sent? |
|-------|-------------|
| Site goes down | Yes — immediately |
| Site stays down on next check | No — one alert per outage |
| Site recovers | Yes |
| Page content changes | Yes — useful for competitor monitoring |

## All options

| Flag | Default | Description |
|------|---------|-------------|
| `--url URL` | — | Single URL to monitor |
| `--urls FILE` | — | Text file with one URL per line |
| `--interval N` | 300 | Check interval in seconds |
| `--expected-text TEXT` | — | Alert if this text is missing from response |
| `--log FILE` | — | Write log to file (in addition to stdout) |
| `--once` | — | Check once and exit (exit 1 if any site is down) |
| `--alert-email EMAIL` | — | Send alerts to this address |
| `--from-email EMAIL` | — | Gmail address to send alerts from |
| `--smtp-password PASS` | — | App password for the from-email account |
| `--smtp-host HOST` | smtp.gmail.com | SMTP server |
| `--smtp-port PORT` | 465 | SMTP port |

## State file

State is saved to `.monitor_state.json` in the current directory. This is how
the tool knows to alert once per outage rather than every check interval.
Delete the file to reset all tracking.

## Run as a background process

```bash
nohup python web_monitor_20260403_134230.py \
  --urls sites.txt --interval 60 \
  --alert-email you@gmail.com \
  --from-email alerts@gmail.com \
  --smtp-password "your app password" \
  --log monitor.log &

echo "PID: $!"
```

## License

Commercial use license included with purchase. You may use this script in
your own projects and for clients. Redistribution for resale is not permitted.
