# DocTracker - Document Expiry Tracker
# Copyright (C) 2026 Pramod Kumar Nagaraj
# Licensed under GNU GPL v3.0 — see LICENSE file for details.
#
# Background scheduler. Runs periodic checks for expiring documents
# and triggers notifications within the configured reminder window.

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from database import get_documents
from notifications import show_notification


scheduler = BackgroundScheduler(timezone="UTC")


def check_reminders():
    """Check all documents and send notifications for those in their reminder window."""
    docs = get_documents()
    now = datetime.now()
    today = now.date()

    for doc in docs:
        name = doc["name"]
        expiry_date = doc["expiry_date"]
        reminder_days = doc["reminder_days"] or 7
        alert_time = doc["alert_time"] or "08:00"

        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            days_left = (expiry - today).days

            # Check if we're within the reminder window (from reminder_days before expiry until expiry)
            if days_left < 0:
                continue  # Already expired, skip

            if days_left > reminder_days:
                continue  # Not yet in reminder window

            # Check if current time matches the alert_time (within 30 min window for scheduler interval)
            alert_hour, alert_min = map(int, alert_time.split(":"))
            current_hour, current_min = now.hour, now.minute

            # Allow a 30-minute window around the alert time
            alert_minutes = alert_hour * 60 + alert_min
            current_minutes = current_hour * 60 + current_min
            if abs(current_minutes - alert_minutes) <= 30:
                if days_left == 0:
                    show_notification("Document Expired!", f"{name} expires TODAY!")
                else:
                    show_notification(
                        "Expiry Reminder", f"{name} expires in {days_left} day(s)"
                    )

        except (ValueError, TypeError):
            continue


def start_scheduler():
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=30,
        id="reminder_check",
        replace_existing=True,
    )
    scheduler.start()
