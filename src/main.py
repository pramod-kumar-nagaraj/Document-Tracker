import flet as ft
import shutil
import os
from datetime import datetime
from database import (
    init_db,
    add_document,
    get_documents,
    delete_document,
    update_document,
    get_document_stats,
    get_profile,
    save_profile,
    DB_PATH,
)
from scheduler import start_scheduler


# =======================
# COLOR SCHEME
# =======================
class C:
    BG = "#0f0f1a"
    SURFACE = "#1a1a2e"
    CARD = "#16213e"
    ACCENT = "#e94560"
    ACCENT_LIGHT = "#ff6b6b"
    SUCCESS = "#00d2d3"
    WARNING = "#baa16d"
    INFO = "#54a0ff"
    TEXT = "#ffffff"
    TEXT2 = "#8a8aa0"
    BORDER = "#2a2a4a"
    INPUT_BG = "#1e2a4a"


def _border(color=None):
    c = color or C.BORDER
    return ft.Border(
        left=ft.BorderSide(1, c),
        top=ft.BorderSide(1, c),
        right=ft.BorderSide(1, c),
        bottom=ft.BorderSide(1, c),
    )


# =======================
# MAIN APP
# =======================
def main(page: ft.Page):
    page.title = "DocTracker"
    page.bgcolor = C.BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    init_db()
    start_scheduler()

    # =======================
    # ABOUT DIALOG
    # =======================
    def show_about_dialog():
        def close_dlg(e):
            about_dlg.open = False
            page.update()

        about_dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=C.INFO),
                    ft.Text(
                        "About DocTracker",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=C.TEXT,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=C.SURFACE,
            content=ft.Column(
                [
                    ft.Text(
                        "DocTracker", size=18, weight=ft.FontWeight.BOLD, color=C.TEXT
                    ),
                    ft.Text("v1.0-beta", size=12, color=C.TEXT2),
                    ft.Container(height=8),
                    ft.Text(
                        "A document expiry tracker. "
                        "Runs entirely offline — no cloud, no accounts, your data stays on your device.",
                        size=13,
                        color=C.TEXT2,
                    ),
                    ft.Container(height=6),
                    ft.Text(
                        "• Track passports, licenses, insurance, certificates & more",
                        size=12,
                        color=C.TEXT2,
                    ),
                    ft.Text(
                        "• In-app reminders before documents expire",
                        size=12,
                        color=C.TEXT2,
                    ),
                    ft.Text(
                        "• Custom reminder windows (1–90 days) & daily alert times",
                        size=12,
                        color=C.TEXT2,
                    ),
                    ft.Text(
                        "• Store profile details for quick reference & copy",
                        size=12,
                        color=C.TEXT2,
                    ),
                    ft.Text(
                        "• Search, filter & organize by status", size=12, color=C.TEXT2
                    ),
                    ft.Text(
                        "• Dark themed UI optimized for mobile", size=12, color=C.TEXT2
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CODE, size=14, color=C.SUCCESS),
                            ft.Text(
                                "Developer: Pramod Kumar Nagaraj", size=13, color=C.TEXT
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "© 2026 Pramod Kumar Nagaraj. All rights reserved.",
                        size=11,
                        color=C.TEXT2,
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
        )
        page.overlay.append(about_dlg)
        about_dlg.open = True
        page.update()

    # =======================
    # THEME TOGGLE
    # =======================
    def toggle_theme():
        show_snack("No support for the light theme yet.", C.WARNING)

    def on_menu_select(e):
        if e.control.data == "theme":
            toggle_theme()
        elif e.control.data == "about":
            show_about_dialog()
        elif e.control.data == "backup":
            show_backup_restore()

    # =======================
    # BACKUP & RESTORE
    # =======================
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def handle_export(e):
        try:
            # Checkpoint WAL to ensure all data is in the main file
            import sqlite3 as _sql

            _conn = _sql.connect(DB_PATH)
            _conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            _conn.close()

            with open(DB_PATH, "rb") as f:
                db_bytes = f.read()
            result = await file_picker.save_file(
                dialog_title="Export Database",
                file_name="doctracker_backup.db",
                allowed_extensions=["db"],
                file_type=ft.FilePickerFileType.CUSTOM,
                src_bytes=db_bytes,
            )
            if result:
                show_snack("Database exported successfully!", C.SUCCESS)
        except Exception as ex:
            show_snack(f"Export failed: {ex}", C.ACCENT)

    async def handle_import(e):
        try:
            files = await file_picker.pick_files(
                dialog_title="Select Database to Import",
                allowed_extensions=["db"],
                file_type=ft.FilePickerFileType.CUSTOM,
                allow_multiple=False,
            )
            if not files or len(files) == 0:
                return

            src = files[0].path
            if not src:
                show_snack("Could not access the selected file.", C.ACCENT)
                return

            # Validate it's a valid SQLite file with the expected table
            import sqlite3 as _sql

            try:
                conn = _sql.connect(src)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                conn.close()
                if "documents" not in tables:
                    show_snack(
                        "Invalid database: 'documents' table not found.", C.ACCENT
                    )
                    return
            except Exception:
                show_snack("Selected file is not a valid database.", C.ACCENT)
                return

            # Confirm before overwriting
            def confirm_import(ev):
                confirm_dlg.open = False
                page.update()
                try:
                    # Remove stale WAL/SHM journal files to avoid conflicts
                    for ext in ("-wal", "-shm", "-journal"):
                        journal = DB_PATH + ext
                        if os.path.exists(journal):
                            os.remove(journal)
                    shutil.copy2(src, DB_PATH)
                    # Reinitialize to run schema migrations on imported DB
                    init_db()
                    show_snack("Database restored! Reloading...", C.SUCCESS)
                    navigate("dashboard")
                except Exception as ex:
                    show_snack(f"Import failed: {ex}", C.ACCENT)

            def cancel_import(ev):
                confirm_dlg.open = False
                page.update()

            confirm_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.WARNING_AMBER_ROUNDED, size=20, color=C.WARNING
                        ),
                        ft.Text(
                            "Replace Database?",
                            size=15,
                            weight=ft.FontWeight.W_600,
                            color=C.TEXT,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=C.SURFACE,
                content=ft.Text(
                    "This will replace ALL your current data with the imported database. This cannot be undone.",
                    size=13,
                    color=C.TEXT2,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_import),
                    ft.TextButton(
                        "Replace",
                        on_click=confirm_import,
                        style=ft.ButtonStyle(color=C.ACCENT),
                    ),
                ],
            )
            page.overlay.append(confirm_dlg)
            confirm_dlg.open = True
            page.update()
        except Exception as ex:
            show_snack(f"Import failed: {ex}", C.ACCENT)

    def show_backup_restore():
        sheet = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.BACKUP_OUTLINED, size=22, color=C.INFO
                                ),
                                ft.Text(
                                    "Backup & Restore",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=C.TEXT,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Text(
                            "Export your database before upgrading the app. "
                            "After reinstalling, import it back to restore your data.",
                            size=12,
                            color=C.TEXT2,
                        ),
                        ft.Container(height=8),
                        # Export button
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.DOWNLOAD_OUTLINED,
                                        color="#ffffff",
                                        size=18,
                                    ),
                                    ft.Text(
                                        "Export Database",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color="#ffffff",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                            ),
                            bgcolor=C.SUCCESS,
                            border_radius=10,
                            padding=ft.Padding(left=0, top=12, right=0, bottom=12),
                            on_click=lambda e: page.run_task(handle_export, e),
                            ink=True,
                        ),
                        # Import button
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.UPLOAD_OUTLINED,
                                        color="#ffffff",
                                        size=18,
                                    ),
                                    ft.Text(
                                        "Import Database",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color="#ffffff",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                            ),
                            bgcolor=C.INFO,
                            border_radius=10,
                            padding=ft.Padding(left=0, top=12, right=0, bottom=12),
                            on_click=lambda e: page.run_task(handle_import, e),
                            ink=True,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            "💡 Tip: Store the backup in Google Drive or another cloud service for safekeeping.",
                            size=11,
                            color=C.TEXT2,
                            italic=True,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                padding=ft.Padding(left=20, top=16, right=20, bottom=24),
                bgcolor=C.SURFACE,
                border_radius=ft.BorderRadius(
                    top_left=16, top_right=16, bottom_left=0, bottom_right=0
                ),
            ),
            bgcolor=C.SURFACE,
            show_drag_handle=True,
        )
        page.show_dialog(sheet)

    # =======================
    # CHECK & SHOW IN-APP REMINDERS
    # =======================
    def check_and_show_reminders():
        docs = get_documents()
        today = datetime.today().date()
        now = datetime.now()

        for doc in docs:
            try:
                expiry = datetime.strptime(doc["expiry_date"], "%Y-%m-%d").date()
                days_left = (expiry - today).days
                reminder_days = doc["reminder_days"] or 7
                alert_time = (
                    doc["alert_time"] if "alert_time" in doc.keys() else "08:00"
                )

                # Only alert if within the reminder window
                if days_left < 0:
                    continue
                if days_left > reminder_days:
                    continue

                # Check if current time is at or past alert time today
                try:
                    alert_hour, alert_min = map(int, (alert_time or "08:00").split(":"))
                except (ValueError, TypeError):
                    alert_hour, alert_min = 8, 0

                if now.hour > alert_hour or (
                    now.hour == alert_hour and now.minute >= alert_min
                ):
                    if days_left == 0:
                        show_snack(f"🚨 {doc['name']} expires TODAY!", C.ACCENT)
                        break
                    else:
                        show_snack(
                            f"⚠️ {doc['name']} expires in {days_left} day(s)!",
                            C.WARNING,
                        )
                        break
            except (ValueError, TypeError):
                continue

    # =======================
    # SNACKBAR
    # =======================
    def show_snack(msg, color=C.SUCCESS):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(msg, color="#fff", size=13),
                bgcolor=color,
                duration=2500,
            )
        )

    # =======================
    # HELPERS
    # =======================
    def days_left_for(expiry_date):
        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            return (expiry - datetime.today().date()).days
        except (ValueError, TypeError):
            return -999

    def status_info(days_left):
        if days_left < 0:
            return "Expired", C.ACCENT, "#3d1520"
        elif days_left <= 7:
            return f"{days_left}d left", C.WARNING, "#3d3515"
        elif days_left <= 30:
            return f"{days_left}d left", C.INFO, "#152a3d"
        else:
            return f"{days_left}d left", C.SUCCESS, "#153d2a"

    # =======================
    # SHOW NOTES BOTTOM SHEET
    # =======================
    def show_notes_dialog(doc):
        name = doc["name"]
        notes = doc["notes"] or "No notes available."
        links = doc["links"] if "links" in doc.keys() else ""
        category = doc["category"] or "Other"
        has_expiry = bool(doc["expiry_date"])
        expiry_date = doc["expiry_date"] if has_expiry else "No Expiry"
        start_date = doc["start_date"] or "—"

        if has_expiry:
            days_left = days_left_for(doc["expiry_date"])
            status_text, status_color, _ = status_info(days_left)
        else:
            status_text, status_color = "∞", C.TEXT2

        content_items = [
            # Header with status
            ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.DESCRIPTION_OUTLINED, color=C.INFO, size=20
                        ),
                        bgcolor=C.INPUT_BG,
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                name, size=16, weight=ft.FontWeight.W_600, color=C.TEXT
                            ),
                            ft.Text(category, size=12, color=C.TEXT2),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(
                            status_text,
                            size=11,
                            weight=ft.FontWeight.W_500,
                            color=status_color,
                        ),
                        bgcolor=C.CARD,
                        border_radius=10,
                        padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                    ),
                ],
                spacing=10,
            ),
            ft.Divider(height=1, color=C.BORDER),
            # Dates
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Start", size=10, color=C.TEXT2),
                            ft.Text(start_date, size=12, color=C.TEXT),
                        ],
                        spacing=2,
                    ),
                    ft.Column(
                        [
                            ft.Text("Expires", size=10, color=C.TEXT2),
                            ft.Text(expiry_date, size=12, color=C.TEXT),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=30,
            ),
            ft.Divider(height=1, color=C.BORDER),
            # Notes
            ft.Text("Notes", size=12, weight=ft.FontWeight.W_600, color=C.INFO),
            ft.Text(notes, size=13, color=C.TEXT2),
        ]

        # Show clickable links
        if links and links.strip():
            content_items.append(ft.Divider(height=1, color=C.BORDER))
            content_items.append(
                ft.Text("Links", size=12, weight=ft.FontWeight.W_600, color=C.INFO)
            )
            for link in links.strip().split("\n"):
                link = link.strip()
                if link:
                    content_items.append(
                        ft.TextButton(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.LINK, size=14, color=C.SUCCESS),
                                    ft.Text(
                                        link if len(link) <= 40 else link[:37] + "...",
                                        size=12,
                                        color=C.SUCCESS,
                                    ),
                                ],
                                spacing=6,
                            ),
                            on_click=lambda e, url=link: page.run_task(
                                ft.UrlLauncher().launch_url, url
                            ),
                            tooltip=link,
                        )
                    )

        sheet = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    content_items, spacing=10, tight=True, scroll=ft.ScrollMode.AUTO
                ),
                padding=ft.Padding(left=20, top=16, right=20, bottom=24),
                bgcolor=C.SURFACE,
                border_radius=ft.BorderRadius(
                    top_left=16, top_right=16, bottom_left=0, bottom_right=0
                ),
            ),
            bgcolor=C.SURFACE,
            show_drag_handle=True,
        )
        page.show_dialog(sheet)

    # =======================
    # ERROR DIALOG
    # =======================
    def show_error_dialog(errors):
        def close_dlg(e):
            err_dlg.open = False
            page.update()

        error_items = []
        for err in errors:
            error_items.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CANCEL_OUTLINED, size=14, color=C.ACCENT),
                        ft.Text(err, size=12, color=C.TEXT2),
                    ],
                    spacing=6,
                )
            )

        err_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=20, color=C.WARNING),
                    ft.Text(
                        "Validation Error",
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=C.WARNING,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=C.SURFACE,
            content=ft.Column(error_items, spacing=6, tight=True),
            actions=[
                ft.TextButton("OK", on_click=close_dlg),
            ],
        )
        page.overlay.append(err_dlg)
        err_dlg.open = True
        page.update()

    # =======================
    # DOCUMENT CARD (mobile)
    # =======================
    def doc_card(doc, on_edit, on_delete):
        doc_id = doc["id"]
        name = doc["name"]
        category = doc["category"] or "Other"
        has_expiry = bool(doc["expiry_date"])
        expiry_date = doc["expiry_date"] if has_expiry else "No Expiry"
        if has_expiry:
            days_left = days_left_for(doc["expiry_date"])
            status_text, status_color, badge_bg = status_info(days_left)
        else:
            status_text, status_color, badge_bg = "∞", C.TEXT2, C.SURFACE

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.DESCRIPTION_OUTLINED, color=C.INFO, size=18
                                ),
                                bgcolor=C.INPUT_BG,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        name,
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color=C.TEXT,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                    ft.Text(category, size=11, color=C.TEXT2),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    status_text,
                                    size=10,
                                    weight=ft.FontWeight.W_500,
                                    color=status_color,
                                ),
                                bgcolor=badge_bg,
                                border_radius=10,
                                padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.Text(f"Expires: {expiry_date}", size=11, color=C.TEXT2),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.INFO_OUTLINE,
                                        icon_color=C.SUCCESS,
                                        icon_size=18,
                                        on_click=lambda e, d=doc: show_notes_dialog(d),
                                        tooltip="View details",
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT_OUTLINED,
                                        icon_color=C.INFO,
                                        icon_size=18,
                                        on_click=lambda e, d=doc: on_edit(d),
                                        tooltip="Edit",
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_color=C.ACCENT_LIGHT,
                                        icon_size=18,
                                        on_click=lambda e, did=doc_id: on_delete(did),
                                        tooltip="Delete",
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=6,
            ),
            padding=14,
            bgcolor=C.CARD,
            border_radius=12,
            border=_border(),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    # =======================
    # SECTION HEADER
    # =======================
    def section_header(title, icon, color, count):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=16),
                            ft.Text(
                                title, size=13, weight=ft.FontWeight.W_600, color=color
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Container(
                        content=ft.Text(
                            str(count), size=11, color=color, weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=C.SURFACE,
                        border_radius=10,
                        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding(left=0, top=12, right=0, bottom=6),
        )

    # =======================
    # DASHBOARD VIEW (grouped)
    # =======================
    def build_dashboard():
        stats = get_document_stats()
        docs = get_documents()

        expired_docs = []
        expiring_docs = []
        active_docs = []
        no_expiry_docs = []

        for doc in docs:
            if not doc["expiry_date"]:
                no_expiry_docs.append(doc)
            else:
                dl = days_left_for(doc["expiry_date"])
                if dl < 0:
                    expired_docs.append(doc)
                elif dl <= 7:
                    expiring_docs.append(doc)
                else:
                    active_docs.append(doc)

        def on_edit(doc):
            navigate("edit", doc)

        def on_delete(did):
            delete_document(did)
            show_snack("Deleted", C.ACCENT)
            navigate("dashboard")

        # Stat chips
        stat_row = ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(stats["total"]),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=C.INFO,
                            ),
                            ft.Text("Total", size=10, color=C.TEXT2),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    bgcolor=C.SURFACE,
                    border_radius=10,
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                    border=_border(),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(stats["active"]),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=C.SUCCESS,
                            ),
                            ft.Text("Active", size=10, color=C.TEXT2),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    bgcolor=C.SURFACE,
                    border_radius=10,
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                    border=_border(),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(stats["expiring_soon"]),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=C.WARNING,
                            ),
                            ft.Text("Soon", size=10, color=C.TEXT2),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    bgcolor=C.SURFACE,
                    border_radius=10,
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                    border=_border(),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(stats["expired"]),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=C.ACCENT,
                            ),
                            ft.Text("Expired", size=10, color=C.TEXT2),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    bgcolor=C.SURFACE,
                    border_radius=10,
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                    border=_border(),
                    expand=True,
                ),
            ],
            spacing=6,
        )

        items = []
        items.append(ft.Container(height=4))
        items.append(stat_row)

        # Expired section
        if expired_docs:
            items.append(
                section_header(
                    "Expired", ft.Icons.ERROR_OUTLINE, C.ACCENT, len(expired_docs)
                )
            )
            for doc in expired_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        # Expiring soon section
        if expiring_docs:
            items.append(
                section_header(
                    "Expiring Soon",
                    ft.Icons.WARNING_AMBER_ROUNDED,
                    C.WARNING,
                    len(expiring_docs),
                )
            )
            for doc in expiring_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        # Active section
        if active_docs:
            items.append(
                section_header(
                    "Active", ft.Icons.CHECK_CIRCLE_OUTLINE, C.SUCCESS, len(active_docs)
                )
            )
            for doc in active_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        # No Expiry section
        if no_expiry_docs:
            items.append(
                section_header(
                    "No Expiry", ft.Icons.ALL_INCLUSIVE, C.TEXT2, len(no_expiry_docs)
                )
            )
            for doc in no_expiry_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        if not docs:
            items.append(ft.Container(height=40))
            items.append(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=C.TEXT2),
                        ft.Text("No documents yet", size=14, color=C.TEXT2),
                        ft.TextButton(
                            "Add your first document",
                            on_click=lambda e: navigate("add"),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                )
            )

        # Fixed header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Dashboard",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=C.TEXT,
                            ),
                            ft.Text("v1.0-beta", size=10, color=C.TEXT2),
                        ],
                        spacing=0,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED,
                                icon_color=C.INFO,
                                icon_size=28,
                                on_click=lambda e: navigate("profile"),
                                tooltip="Profile",
                            ),
                            ft.PopupMenuButton(
                                icon=ft.Icons.MENU,
                                icon_color=C.TEXT,
                                icon_size=24,
                                items=[
                                    ft.PopupMenuItem(
                                        content=ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.DARK_MODE
                                                    if page.theme_mode
                                                    == ft.ThemeMode.DARK
                                                    else ft.Icons.LIGHT_MODE,
                                                    size=18,
                                                    color=C.WARNING,
                                                ),
                                                ft.Text(
                                                    "Light Mode"
                                                    if page.theme_mode
                                                    == ft.ThemeMode.DARK
                                                    else "Dark Mode",
                                                    size=13,
                                                ),
                                            ],
                                            spacing=8,
                                        ),
                                        data="theme",
                                        on_click=on_menu_select,
                                    ),
                                    ft.PopupMenuItem(),  # divider
                                    ft.PopupMenuItem(
                                        content=ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.BACKUP_OUTLINED,
                                                    size=18,
                                                    color=C.SUCCESS,
                                                ),
                                                ft.Text("Backup & Restore", size=13),
                                            ],
                                            spacing=8,
                                        ),
                                        data="backup",
                                        on_click=on_menu_select,
                                    ),
                                    ft.PopupMenuItem(),  # divider
                                    ft.PopupMenuItem(
                                        content=ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.INFO_OUTLINE,
                                                    size=18,
                                                    color=C.INFO,
                                                ),
                                                ft.Text("About", size=13),
                                            ],
                                            spacing=8,
                                        ),
                                        data="about",
                                        on_click=on_menu_select,
                                    ),
                                ],
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding(left=0, top=0, right=0, bottom=4),
        )

        return ft.Column(
            [
                header,
                ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    # =======================
    # DOCUMENTS VIEW (search + filter)
    # =======================
    CATEGORIES = [
        "All",
        "Passport",
        "License",
        "Insurance",
        "Certificate",
        "Warranty",
        "Medical",
        "Subscription",
        "Contract",
        "Other",
    ]

    def build_documents():
        search_field = ft.TextField(
            hint_text="Search...",
            prefix_icon=ft.Icons.SEARCH,
            height=40,
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            hint_style=ft.TextStyle(color=C.TEXT2),
        )

        docs_column = ft.Column(spacing=8)
        active_filter = ["All"]  # mutable

        def on_edit(doc):
            navigate("edit", doc)

        def on_delete(did):
            delete_document(did)
            show_snack("Deleted", C.ACCENT)
            load_docs(search_field.value)

        def load_docs(search=""):
            docs_column.controls.clear()
            docs = get_documents(search)

            # Apply category filter
            if active_filter[0] != "All":
                docs = [
                    d for d in docs if (d["category"] or "Other") == active_filter[0]
                ]

            if not docs:
                docs_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.SEARCH_OFF, size=40, color=C.TEXT2),
                                ft.Text("No documents found", size=13, color=C.TEXT2),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=30,
                        alignment=ft.Alignment(0, 0),
                    )
                )
            else:
                for doc in docs:
                    docs_column.controls.append(doc_card(doc, on_edit, on_delete))

            page.update()

        def on_chip_select(e):
            active_filter[0] = e.control.data
            # Update chip visuals
            for chip in chip_row.controls:
                chip.selected = chip.data == active_filter[0]
            load_docs(search_field.value)

        # Build filter chips
        chip_row = ft.Row(
            controls=[
                ft.Chip(
                    label=ft.Text(cat, size=11),
                    selected=(cat == "All"),
                    on_select=on_chip_select,
                    data=cat,
                    bgcolor=C.SURFACE,
                    selected_color=C.CARD,
                    check_color=C.SUCCESS,
                )
                for cat in CATEGORIES
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
        )

        search_field.on_change = lambda e: load_docs(search_field.value)
        load_docs()

        # Fixed header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "All Documents",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=C.TEXT,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED,
                        icon_color=C.INFO,
                        icon_size=28,
                        on_click=lambda e: navigate("profile"),
                        tooltip="Profile",
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding(left=0, top=0, right=0, bottom=4),
        )

        return ft.Column(
            [
                header,
                search_field,
                chip_row,
                ft.Container(height=4),
                ft.Column([docs_column], scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=8,
            expand=True,
        )

    # =======================
    # ADD / EDIT DOCUMENT VIEW
    # =======================
    def build_form(doc=None):
        is_edit = doc is not None
        title = "Edit Document" if is_edit else "Add Document"

        name_field = ft.TextField(
            label="Document Name *",
            value=doc["name"] if is_edit else "",
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.DESCRIPTION_OUTLINED,
        )

        category_field = ft.Dropdown(
            label="Category *",
            value=doc["category"] if is_edit else None,
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
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

        start_date_field = ft.TextField(
            label="Start Date *",
            value=doc["start_date"] if is_edit else "",
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            hint_text="YYYY-MM-DD",
            read_only=True,
        )

        expiry_date_field = ft.TextField(
            label="Expiry Date",
            value=doc["expiry_date"] if is_edit else "",
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            hint_text="YYYY-MM-DD",
            read_only=True,
        )

        # No Expiry toggle
        no_expiry_check = ft.Checkbox(
            label="No Expiry",
            value=True if (is_edit and not doc["expiry_date"]) else False,
            active_color=C.INFO,
            check_color="#fff",
            label_style=ft.TextStyle(color=C.TEXT2, size=13),
        )

        def on_no_expiry_change(e):
            if no_expiry_check.value:
                expiry_date_field.value = ""
                expiry_date_field.disabled = True
                reminder_field.disabled = True
                alert_time_field.disabled = True
            else:
                expiry_date_field.disabled = False
                reminder_field.disabled = False
                alert_time_field.disabled = False
            page.update()

        no_expiry_check.on_change = on_no_expiry_change

        reminder_field = ft.Dropdown(
            label="Remind Before Expiry *",
            value=str(doc["reminder_days"]) if is_edit else "7",
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            options=[
                ft.dropdown.Option("1", "1 day"),
                ft.dropdown.Option("3", "3 days"),
                ft.dropdown.Option("7", "7 days"),
                ft.dropdown.Option("15", "15 days"),
                ft.dropdown.Option("30", "30 days"),
                ft.dropdown.Option("60", "60 days"),
                ft.dropdown.Option("90", "90 days"),
            ],
        )

        alert_time_field = ft.TextField(
            label="Daily Alert Time *",
            value=doc["alert_time"] if is_edit and doc["alert_time"] else "08:00",
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            hint_text="HH:MM",
            read_only=True,
        )

        time_picker = ft.TimePicker(
            confirm_text="SELECT",
            cancel_text="CANCEL",
        )

        def on_time_picked(e):
            if e.control.value:
                t = e.control.value
                alert_time_field.value = f"{t.hour:02d}:{t.minute:02d}"
                alert_time_field.error_text = None
                page.update()

        time_picker.on_change = on_time_picked
        page.overlay.append(time_picker)

        def open_time_picker(e):
            time_picker.open = True
            page.update()

        alert_time_row = ft.Row(
            [
                ft.Container(content=alert_time_field, expand=True),
                ft.IconButton(
                    icon=ft.Icons.ACCESS_TIME,
                    icon_color=C.SUCCESS,
                    icon_size=22,
                    on_click=open_time_picker,
                    tooltip="Pick time",
                    bgcolor=C.INPUT_BG,
                ),
            ],
            spacing=8,
        )

        # Set initial disabled state for no-expiry docs
        if no_expiry_check.value:
            expiry_date_field.disabled = True
            reminder_field.disabled = True
            alert_time_field.disabled = True

        notes_field = ft.TextField(
            label="Notes *",
            value=doc["notes"] if is_edit else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.NOTES_OUTLINED,
        )

        links_field = ft.TextField(
            label="Links (one per line)",
            value=doc["links"] if is_edit and "links" in doc.keys() else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.LINK,
            hint_text="https://drive.google.com/...",
        )

        # Date pickers
        start_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            confirm_text="SELECT",
            cancel_text="CANCEL",
        )

        expiry_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            confirm_text="SELECT",
            cancel_text="CANCEL",
        )

        def on_start_date_picked(e):
            if e.control.value:
                picked = e.control.value
                start_date_field.value = picked.strftime("%Y-%m-%d")
                start_date_field.error_text = None
                # Restrict expiry picker: only allow dates after start
                expiry_date_picker.first_date = picked
                page.update()

        def on_expiry_date_picked(e):
            if e.control.value:
                expiry_date_field.value = e.control.value.strftime("%Y-%m-%d")
                expiry_date_field.error_text = None
                page.update()

        start_date_picker.on_change = on_start_date_picked
        expiry_date_picker.on_change = on_expiry_date_picked

        page.overlay.append(start_date_picker)
        page.overlay.append(expiry_date_picker)

        def open_start_picker(e):
            start_date_picker.open = True
            page.update()

        def open_expiry_picker(e):
            # If start date is selected, restrict expiry to after it
            if start_date_field.value:
                try:
                    sd = datetime.strptime(start_date_field.value, "%Y-%m-%d")
                    expiry_date_picker.first_date = sd
                except ValueError:
                    pass
            elif not start_date_field.value:
                start_date_field.error_text = "Select start date first"
                page.update()
                return
            expiry_date_picker.open = True
            page.update()

        # Date field rows with calendar button
        start_date_row = ft.Row(
            [
                ft.Container(content=start_date_field, expand=True),
                ft.IconButton(
                    icon=ft.Icons.CALENDAR_MONTH,
                    icon_color=C.INFO,
                    icon_size=22,
                    on_click=open_start_picker,
                    tooltip="Pick date",
                    bgcolor=C.INPUT_BG,
                ),
            ],
            spacing=8,
        )

        expiry_date_row = ft.Row(
            [
                ft.Container(content=expiry_date_field, expand=True),
                ft.IconButton(
                    icon=ft.Icons.CALENDAR_MONTH,
                    icon_color=C.WARNING,
                    icon_size=22,
                    on_click=open_expiry_picker,
                    tooltip="Pick date",
                    bgcolor=C.INPUT_BG,
                ),
            ],
            spacing=8,
        )

        # Validation
        def handle_save(e):
            errors = []

            if not name_field.value or not name_field.value.strip():
                errors.append("Document name is required")

            if not category_field.value:
                errors.append("Please select a category")

            if not start_date_field.value or not start_date_field.value.strip():
                errors.append("Start date is required")

            if not no_expiry_check.value:
                if not expiry_date_field.value or not expiry_date_field.value.strip():
                    errors.append("Expiry date is required (or check 'No Expiry')")

                if not reminder_field.value:
                    errors.append("Please select reminder period")

                if not alert_time_field.value or not alert_time_field.value.strip():
                    errors.append("Please select alert time")

                # Validate start < expiry if both dates present
                if start_date_field.value and expiry_date_field.value:
                    try:
                        start_dt = datetime.strptime(start_date_field.value, "%Y-%m-%d")
                        expiry_dt = datetime.strptime(
                            expiry_date_field.value, "%Y-%m-%d"
                        )
                        if expiry_dt <= start_dt:
                            errors.append("Expiry date must be after start date")
                    except ValueError:
                        errors.append("Invalid date format")

            if not notes_field.value or not notes_field.value.strip():
                errors.append("Notes are required")

            if errors:
                show_error_dialog(errors)
                return

            expiry_val = "" if no_expiry_check.value else expiry_date_field.value
            reminder_val = int(reminder_field.value) if reminder_field.value else 7
            alert_val = (
                alert_time_field.value.strip() if alert_time_field.value else "08:00"
            )
            links_val = links_field.value.strip() if links_field.value else ""

            if is_edit:
                update_document(
                    doc_id=doc["id"],
                    name=name_field.value.strip(),
                    category=category_field.value,
                    start_date=start_date_field.value,
                    expiry_date=expiry_val,
                    reminder_days=reminder_val,
                    notes=notes_field.value.strip(),
                    alert_time=alert_val,
                    links=links_val,
                )
                show_snack("Document updated!")
            else:
                add_document(
                    name=name_field.value.strip(),
                    category=category_field.value,
                    start_date=start_date_field.value,
                    expiry_date=expiry_val,
                    reminder_days=reminder_val,
                    notes=notes_field.value.strip(),
                    alert_time=alert_val,
                    links=links_val,
                )
                show_snack("Document added!")

            # Clean up overlays
            if start_date_picker in page.overlay:
                page.overlay.remove(start_date_picker)
            if expiry_date_picker in page.overlay:
                page.overlay.remove(expiry_date_picker)
            if time_picker in page.overlay:
                page.overlay.remove(time_picker)

            navigate("dashboard")

        def handle_cancel(e):
            if start_date_picker in page.overlay:
                page.overlay.remove(start_date_picker)
            if expiry_date_picker in page.overlay:
                page.overlay.remove(expiry_date_picker)
            if time_picker in page.overlay:
                page.overlay.remove(time_picker)
            navigate("dashboard")

        btn_text = "Update Document" if is_edit else "Save Document"
        btn_icon = ft.Icons.SAVE_OUTLINED if is_edit else ft.Icons.ADD_CIRCLE_OUTLINE

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=C.TEXT,
                            icon_size=20,
                            on_click=handle_cancel,
                        ),
                        ft.Text(
                            title, size=20, weight=ft.FontWeight.BOLD, color=C.TEXT
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(
                    content=ft.Text(
                        "All fields marked with * are required",
                        size=11,
                        color=C.TEXT2,
                        italic=True,
                    ),
                    padding=ft.Padding(left=4, top=0, right=0, bottom=0),
                ),
                ft.Container(height=10),
                name_field,
                ft.Container(height=4),
                category_field,
                ft.Container(height=4),
                start_date_row,
                ft.Container(height=4),
                no_expiry_check,
                expiry_date_row,
                ft.Container(height=4),
                reminder_field,
                ft.Container(height=4),
                alert_time_row,
                ft.Container(height=4),
                notes_field,
                ft.Container(height=4),
                links_field,
                ft.Container(height=16),
                # Save button
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(btn_icon, color="#ffffff", size=18),
                            ft.Text(
                                btn_text,
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color="#ffffff",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=C.SUCCESS,
                    border_radius=12,
                    padding=ft.Padding(left=0, top=14, right=0, bottom=14),
                    on_click=handle_save,
                    ink=True,
                ),
                # Cancel button
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CLOSE, color=C.TEXT2, size=16),
                            ft.Text(
                                "Cancel",
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=C.TEXT2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    bgcolor="transparent",
                    border_radius=12,
                    border=_border(C.BORDER),
                    padding=ft.Padding(left=0, top=12, right=0, bottom=12),
                    on_click=handle_cancel,
                    ink=True,
                ),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =======================
    # PROFILE VIEW
    # =======================
    def build_profile(edit_mode=False):
        profile = get_profile()

        if not edit_mode:
            # Display mode
            def _copy_to_clipboard(val):
                page.run_task(ft.Clipboard().set, val)
                show_snack("Copied!", C.SUCCESS)

            def field_row(icon, label, value):
                display_val = value or "—"
                row_controls = [
                    ft.Icon(icon, size=18, color=C.INFO),
                    ft.Column(
                        [
                            ft.Text(label, size=10, color=C.TEXT2),
                            ft.Text(display_val, size=13, color=C.TEXT),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                ]
                if value:
                    row_controls.append(
                        ft.IconButton(
                            icon=ft.Icons.COPY_OUTLINED,
                            icon_color=C.TEXT2,
                            icon_size=16,
                            on_click=lambda e, v=display_val: _copy_to_clipboard(v),
                            tooltip="Copy",
                        )
                    )
                return ft.Container(
                    content=ft.Row(row_controls, spacing=12),
                    padding=ft.Padding(left=12, top=10, right=4, bottom=10),
                    bgcolor=C.CARD,
                    border_radius=10,
                    border=_border(),
                )

            items = [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=C.TEXT,
                            icon_size=20,
                            on_click=lambda e: navigate("dashboard"),
                        ),
                        ft.Text(
                            "My Profile",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=C.TEXT,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(height=8),
                # Avatar
                ft.Container(
                    content=ft.Column(
                        [
                            ft.CircleAvatar(
                                content=ft.Text(
                                    (profile["full_name"] or "U")[0].upper(),
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color="#fff",
                                ),
                                bgcolor=C.INFO,
                                radius=36,
                            ),
                            ft.Text(
                                profile["full_name"] or "No name set",
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=C.TEXT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(left=0, top=8, right=0, bottom=16),
                ),
                field_row(ft.Icons.EMAIL_OUTLINED, "Email(s)", profile["emails"]),
                field_row(ft.Icons.PHONE_OUTLINED, "Phone(s)", profile["phones"]),
                field_row(
                    ft.Icons.BADGE_OUTLINED,
                    "Passport Number",
                    profile["passport_number"],
                ),
                field_row(
                    ft.Icons.CREDIT_CARD_OUTLINED,
                    "Driving License",
                    profile["driving_license"],
                ),
                field_row(
                    ft.Icons.CAKE_OUTLINED, "Date of Birth", profile["date_of_birth"]
                ),
                field_row(
                    ft.Icons.FLAG_OUTLINED, "Nationality", profile["nationality"]
                ),
                field_row(ft.Icons.HOME_OUTLINED, "Address", profile["address"]),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.EDIT_OUTLINED, color="#ffffff", size=18),
                            ft.Text(
                                "Edit Profile",
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color="#ffffff",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=C.INFO,
                    border_radius=12,
                    padding=ft.Padding(left=0, top=14, right=0, bottom=14),
                    on_click=lambda e: navigate("profile_edit"),
                    ink=True,
                ),
            ]

            return ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        # Edit mode
        name_f = ft.TextField(
            label="Full Name",
            value=profile["full_name"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.PERSON_OUTLINED,
        )
        emails_f = ft.TextField(
            label="Emails (comma separated)",
            value=profile["emails"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            hint_text="email1@x.com, email2@x.com",
        )
        phones_f = ft.TextField(
            label="Phone Numbers (comma separated)",
            value=profile["phones"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.PHONE_OUTLINED,
            hint_text="+1234567890, +0987654321",
        )
        passport_f = ft.TextField(
            label="Passport Number",
            value=profile["passport_number"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.BADGE_OUTLINED,
        )
        license_f = ft.TextField(
            label="Driving License",
            value=profile["driving_license"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.CREDIT_CARD_OUTLINED,
        )
        dob_f = ft.TextField(
            label="Date of Birth",
            value=profile["date_of_birth"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.CAKE_OUTLINED,
            hint_text="YYYY-MM-DD",
        )
        nationality_f = ft.TextField(
            label="Nationality",
            value=profile["nationality"],
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.FLAG_OUTLINED,
        )
        address_f = ft.TextField(
            label="Address",
            value=profile["address"],
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            prefix_icon=ft.Icons.HOME_OUTLINED,
        )

        def handle_profile_save(e):
            save_profile(
                full_name=name_f.value.strip() if name_f.value else "",
                emails=emails_f.value.strip() if emails_f.value else "",
                phones=phones_f.value.strip() if phones_f.value else "",
                passport_number=passport_f.value.strip() if passport_f.value else "",
                driving_license=license_f.value.strip() if license_f.value else "",
                address=address_f.value.strip() if address_f.value else "",
                date_of_birth=dob_f.value.strip() if dob_f.value else "",
                nationality=nationality_f.value.strip() if nationality_f.value else "",
            )
            show_snack("Profile saved!")
            navigate("profile")

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=C.TEXT,
                            icon_size=20,
                            on_click=lambda e: navigate("profile"),
                        ),
                        ft.Text(
                            "Edit Profile",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=C.TEXT,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(height=8),
                name_f,
                emails_f,
                phones_f,
                passport_f,
                license_f,
                dob_f,
                nationality_f,
                address_f,
                ft.Container(height=12),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SAVE_OUTLINED, color="#ffffff", size=18),
                            ft.Text(
                                "Save Profile",
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color="#ffffff",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=C.SUCCESS,
                    border_radius=12,
                    padding=ft.Padding(left=0, top=14, right=0, bottom=14),
                    on_click=handle_profile_save,
                    ink=True,
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CLOSE, color=C.TEXT2, size=16),
                            ft.Text(
                                "Cancel",
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=C.TEXT2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    bgcolor="transparent",
                    border_radius=12,
                    border=_border(C.BORDER),
                    padding=ft.Padding(left=0, top=12, right=0, bottom=12),
                    on_click=lambda e: navigate("profile"),
                    ink=True,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =======================
    # NAVIGATION
    # =======================
    content_area = ft.Container(expand=True, padding=16)
    current_tab = [0]  # mutable to track current tab index

    switcher = ft.AnimatedSwitcher(
        content=content_area,
        duration=300,
        reverse_duration=200,
        transition=ft.AnimatedSwitcherTransition.FADE,
        switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
        expand=True,
    )

    def navigate(view_name, data=None):
        if view_name == "dashboard":
            content_area.content = build_dashboard()
            nav_bar.selected_index = 0
            current_tab[0] = 0
        elif view_name == "documents":
            content_area.content = build_documents()
            nav_bar.selected_index = 1
            current_tab[0] = 1
        elif view_name == "add":
            content_area.content = build_form(doc=None)
            nav_bar.selected_index = 2
            current_tab[0] = 2
        elif view_name == "edit":
            content_area.content = build_form(doc=data)
            nav_bar.selected_index = 1
            current_tab[0] = 1
        elif view_name == "profile":
            content_area.content = build_profile(edit_mode=False)
        elif view_name == "profile_edit":
            content_area.content = build_profile(edit_mode=True)
        # Update badge count
        count = _get_alert_count()
        home_badge.label = str(count) if count > 0 else ""
        home_badge.small_size = 0 if count == 0 else 10
        page.update()

    def on_swipe(e: ft.DragEndEvent):
        views = ["dashboard", "documents", "add"]
        if e.primary_velocity and e.primary_velocity < -300:
            # Swipe left → next tab
            if current_tab[0] < 2:
                navigate(views[current_tab[0] + 1])
        elif e.primary_velocity and e.primary_velocity > 300:
            # Swipe right → previous tab
            if current_tab[0] > 0:
                navigate(views[current_tab[0] - 1])

    swipeable_area = ft.GestureDetector(
        content=switcher,
        on_horizontal_drag_end=on_swipe,
        expand=True,
    )

    def on_nav_change(e):
        idx = e.control.selected_index
        views = ["dashboard", "documents", "add"]
        navigate(views[idx])

    def _get_alert_count():
        stats = get_document_stats()
        return stats["expired"] + stats["expiring_soon"]

    _alert_count = _get_alert_count()
    home_badge = ft.Badge(
        label=str(_alert_count) if _alert_count > 0 else "",
        small_size=0 if _alert_count == 0 else 10,
        bgcolor=C.ACCENT,
        text_color="#ffffff",
    )

    nav_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor=C.SURFACE,
        indicator_color=C.CARD,
        on_change=on_nav_change,
        height=60,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Home",
                badge=home_badge,
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.FOLDER_OUTLINED,
                selected_icon=ft.Icons.FOLDER,
                label="Documents",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                selected_icon=ft.Icons.ADD_CIRCLE,
                label="Add",
            ),
        ],
    )

    # =======================
    # PAGE LAYOUT (mobile)
    # =======================
    page.add(
        ft.SafeArea(
            content=ft.Column(
                [
                    swipeable_area,
                    nav_bar,
                ],
                expand=True,
                spacing=0,
            ),
            expand=True,
        )
    )

    navigate("dashboard")

    # Show reminder on app start
    check_and_show_reminders()


ft.run(main)
