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