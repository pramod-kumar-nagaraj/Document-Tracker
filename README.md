# DocTracker

A mobile-first document expiry tracker built with Flet and SQLite. Runs entirely offline — no cloud, no accounts, your data stays on your device.

## What It Does

- Track documents like passports, licenses, insurance, certificates, contracts, and more
- Get in-app reminders when documents are approaching expiry
- Organize documents by status: Active, Expiring Soon, Expired, No Expiry
- Store personal profile details (passport number, license, contacts) for quick reference
- Copy any profile field to clipboard with one tap
- Set custom reminder windows (1–90 days before expiry) and daily alert times
- Search and filter across all documents
- Dark themed UI optimized for mobile screens

## Tech Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | Flet 0.85.2 |
| Database | SQLite (local, offline) |
| Scheduler | APScheduler (background reminders) |
| Platform | Android APK via `flet build apk` |

## Run Locally

```bash
pip install -r requirements.txt
cd src
python main.py
```

The app opens in a browser window at `http://localhost:port`. All data is stored in a local SQLite database file.

## Build Android APK

```bash
flet build apk
```

Output APK will be in the `build/` directory.

## References

- [Flet Documentation](https://flet.dev/docs)
- [Flet — Build APK for Android](https://flet.dev/docs/publish/android)
