import flet as ft
from datetime import datetime

from database import get_documents, delete_document


class DashboardView(ft.Column):
    def __init__(self, page):
        super().__init__()

        self.page = page

        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Expiry")),
                ft.DataColumn(ft.Text("Days Left")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
        )

        self.controls = [
            ft.Text("Documents", size=24, weight="bold"),
            self.table,
        ]

        self.load_data()

    def load_data(self):
        self.table.rows.clear()

        docs = get_documents()

        today = datetime.today().date()

        for doc in docs:
            doc_id = doc["id"]
            name = doc["name"]
            category = doc["category"] or "—"
            expiry_date = doc["expiry_date"]

            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                days_left = (expiry - today).days
            except (ValueError, TypeError):
                days_left = -999

            if days_left < 0:
                status = "Expired"
                color = ft.Colors.RED
            elif days_left <= 7:
                status = "Soon"
                color = ft.Colors.ORANGE
            else:
                status = "Active"
                color = ft.Colors.GREEN

            def remove(e, did=doc_id):
                delete_document(did)
                self.load_data()
                self.page.update()

            self.table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(name)),
                        ft.DataCell(ft.Text(category)),
                        ft.DataCell(ft.Text(expiry_date)),
                        ft.DataCell(ft.Text(str(days_left))),
                        ft.DataCell(ft.Text(status, color=color)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                on_click=remove,
                            )
                        ),
                    ]
                )
            )