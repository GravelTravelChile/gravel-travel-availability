# Gravel Travel availability

`availability.json` is rebuilt every hour from the Gravel Travel Workshop tool and read by the booking form on the website.
It only contains how many bikes per type and size are free on each date (no customer data).

Build: `python3 scripts/build_availability.py <export-dir> availability.json`
