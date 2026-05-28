from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from database import get_documents
from notifications import show_notification


scheduler = BackgroundScheduler()


def check_reminders():
    docs = get_documents()
    today = datetime.today().date()

    for doc in docs:
        name = doc["name"]
        expiry_date = doc["expiry_date"]
        reminder_days = doc["reminder_days"]

        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            days_left = (expiry - today).days

            if days_left == reminder_days:
                show_notification(
                    "Expiry Reminder",
                    f"{name} expires in {days_left} day(s)",
                )

            if days_left == 0:
                show_notification(
                    "Document Expired",
                    f"{name} expires today!",
                )
        except (ValueError, TypeError):
            continue


def start_scheduler():
    scheduler.add_job(check_reminders, "interval", hours=6)
    scheduler.start()