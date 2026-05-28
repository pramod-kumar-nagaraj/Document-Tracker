import flet as ft

from database import add_document


class AddDocumentView(ft.Column):
    def __init__(self, refresh_callback):
        super().__init__()

        self.refresh_callback = refresh_callback

        self.name = ft.TextField(label="Document Name")

        self.category = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Passport"),
                ft.dropdown.Option("License"),
                ft.dropdown.Option("Insurance"),
                ft.dropdown.Option("Certificate"),
                ft.dropdown.Option("Warranty"),
                ft.dropdown.Option("Medical"),
                ft.dropdown.Option("Subscription"),
                ft.dropdown.Option("Contract"),
                ft.dropdown.Option("Other"),
            ],
        )

        self.start_date = ft.TextField(label="Start Date YYYY-MM-DD")

        self.expiry_date = ft.TextField(label="Expiry Date YYYY-MM-DD")

        self.reminder = ft.Dropdown(
            label="Reminder",
            value="7",
            options=[
                ft.dropdown.Option("1"),
                ft.dropdown.Option("3"),
                ft.dropdown.Option("7"),
                ft.dropdown.Option("15"),
                ft.dropdown.Option("30"),
            ],
        )

        self.notes = ft.TextField(label="Notes", multiline=True)

        self.controls = [
            ft.Text("Add Document", size=24, weight="bold"),
            self.name,
            self.category,
            self.start_date,
            self.expiry_date,
            self.reminder,
            self.notes,
            ft.ElevatedButton(
                "Save",
                on_click=self.save_document,
            ),
        ]

    def save_document(self, e):
        if not self.name.value:
            return

        add_document(
            name=self.name.value,
            category=self.category.value or "Other",
            start_date=self.start_date.value or "",
            expiry_date=self.expiry_date.value or "",
            reminder_days=int(self.reminder.value),
            notes=self.notes.value or "",
        )

        self.refresh_callback()