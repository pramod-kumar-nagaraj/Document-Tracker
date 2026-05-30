# DocTracker - Document Expiry Tracker
# Copyright (C) 2026 Pramod Kumar Nagaraj
# Licensed under GNU GPL v3.0 — see LICENSE file for details.
#
# Settings view component. Provides app configuration options
# (currently unused — reserved for future settings UI).

import flet as ft


class SettingsView(ft.Column):
    def __init__(self):
        super().__init__()

        self.controls = [
            ft.Text("Settings", size=24, weight="bold"),
            ft.Text("Future settings will appear here."),
        ]
