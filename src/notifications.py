# DocTracker - Document Expiry Tracker
# Copyright (C) 2026 Pramod Kumar Nagaraj
# Licensed under GNU GPL v3.0 — see LICENSE file for details.
#
# Notification helpers. Sends desktop notifications on supported platforms;
# Android relies on in-app alerts instead.

import sys


def show_notification(title, message):
    """Cross-platform notification (desktop only, Android uses in-app alerts)."""
    try:
        if sys.platform == "win32":
            from plyer import notification

            notification.notify(title=title, message=message, timeout=10)
        else:
            # On Android/other platforms, the in-app snackbar handles reminders
            print(f"[NOTIFICATION] {title}: {message}")
    except Exception as e:
        print(f"Notification error: {e}")
