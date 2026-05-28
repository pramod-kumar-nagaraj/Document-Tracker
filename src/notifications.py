import sys


def show_notification(title, message):
    """Cross-platform desktop notification."""
    try:
        if sys.platform == "win32":
            from plyer import notification
            notification.notify(title=title, message=message, timeout=10)
        else:
            print(f"[NOTIFICATION] {title}: {message}")
    except Exception as e:
        print(f"Notification error: {e}")