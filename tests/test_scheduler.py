from unittest.mock import patch
from datetime import datetime, timedelta

from database import add_document
from scheduler import check_reminders


class TestReminders:
    def test_no_reminder_when_far_from_expiry(self):
        """No notification if expiry is far away."""
        future = (datetime.today() + timedelta(days=365)).strftime("%Y-%m-%d")
        add_document("Far Away", "Other", "2024-01-01", future, 7, "notes", "08:00")

        with patch("scheduler.show_notification") as mock_notify:
            check_reminders()
            mock_notify.assert_not_called()

    def test_reminder_within_window(self):
        """Notification fires when within reminder window and at alert time."""
        expiry = (datetime.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        add_document(
            "Expiring Soon", "Other", "2024-01-01", expiry, 7, "notes", "10:00"
        )

        fake_now = datetime.today().replace(hour=10, minute=5, second=0, microsecond=0)
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.strptime = datetime.strptime
            with patch("scheduler.show_notification") as mock_notify:
                check_reminders()
                mock_notify.assert_called_once()
                assert "Expiring Soon" in mock_notify.call_args[0][1]

    def test_no_reminder_for_expired_doc(self):
        """No notification for already-expired documents."""
        past = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        add_document("Expired", "Other", "2020-01-01", past, 7, "notes", "08:00")

        with patch("scheduler.show_notification") as mock_notify:
            check_reminders()
            mock_notify.assert_not_called()

    def test_no_reminder_for_no_expiry_doc(self):
        """No notification for documents without expiry date."""
        add_document("No Expiry", "Other", "2024-01-01", "", 7, "notes", "08:00")

        with patch("scheduler.show_notification") as mock_notify:
            check_reminders()
            mock_notify.assert_not_called()
