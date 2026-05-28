import flet as ft


class SettingsView(ft.Column):
    def __init__(self):
        super().__init__()

        self.controls = [
            ft.Text("Settings", size=24, weight="bold"),
            ft.Text("Future settings will appear here."),
        ]