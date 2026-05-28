import flet as ft
from datetime import datetime
from database import (
    init_db,
    add_document,
    get_documents,
    delete_document,
    update_document,
    get_document_stats,
)


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
    WARNING = "#feca57"
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

    # =======================
    # SNACKBAR
    # =======================
    def show_snack(msg, color=C.SUCCESS):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color="#fff", size=13),
            bgcolor=color,
            duration=2500,
        )
        page.snack_bar.open = True
        page.update()

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
    # DOCUMENT CARD (mobile)
    # =======================
    def doc_card(doc, on_edit, on_delete):
        doc_id = doc["id"]
        name = doc["name"]
        category = doc["category"] or "Other"
        expiry_date = doc["expiry_date"] or "—"
        days_left = days_left_for(doc["expiry_date"])
        status_text, status_color, badge_bg = status_info(days_left)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=C.INFO, size=18),
                                bgcolor=C.INPUT_BG,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        name, size=14, weight=ft.FontWeight.W_500,
                                        color=C.TEXT, overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                    ft.Text(category, size=11, color=C.TEXT2),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text(status_text, size=10, weight=ft.FontWeight.W_500, color=status_color),
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
                            ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=color),
                        ],
                        spacing=6,
                    ),
                    ft.Container(
                        content=ft.Text(str(count), size=11, color=color, weight=ft.FontWeight.BOLD),
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

        for doc in docs:
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
                            ft.Text(str(stats["total"]), size=20, weight=ft.FontWeight.BOLD, color=C.INFO),
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
                            ft.Text(str(stats["active"]), size=20, weight=ft.FontWeight.BOLD, color=C.SUCCESS),
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
                            ft.Text(str(stats["expiring_soon"]), size=20, weight=ft.FontWeight.BOLD, color=C.WARNING),
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
                            ft.Text(str(stats["expired"]), size=20, weight=ft.FontWeight.BOLD, color=C.ACCENT),
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
        items.append(ft.Text("Dashboard", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT))
        items.append(ft.Container(height=4))
        items.append(stat_row)

        # Expired section
        if expired_docs:
            items.append(section_header("Expired", ft.Icons.ERROR_OUTLINE, C.ACCENT, len(expired_docs)))
            for doc in expired_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        # Expiring soon section
        if expiring_docs:
            items.append(section_header("Expiring Soon", ft.Icons.WARNING_AMBER_ROUNDED, C.WARNING, len(expiring_docs)))
            for doc in expiring_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        # Active section
        if active_docs:
            items.append(section_header("Active", ft.Icons.CHECK_CIRCLE_OUTLINE, C.SUCCESS, len(active_docs)))
            for doc in active_docs:
                items.append(doc_card(doc, on_edit, on_delete))

        if not docs:
            items.append(ft.Container(height=40))
            items.append(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=C.TEXT2),
                        ft.Text("No documents yet", size=14, color=C.TEXT2),
                        ft.TextButton("Add your first document", on_click=lambda e: navigate("add")),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                )
            )

        return ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    # =======================
    # DOCUMENTS VIEW (search)
    # =======================
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

        def on_edit(doc):
            navigate("edit", doc)

        def on_delete(did):
            delete_document(did)
            show_snack("Deleted", C.ACCENT)
            load_docs(search_field.value)

        def load_docs(search=""):
            docs_column.controls.clear()
            docs = get_documents(search)

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

        search_field.on_change = lambda e: load_docs(search_field.value)
        load_docs()

        return ft.Column(
            [
                ft.Text("All Documents", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT),
                search_field,
                ft.Container(height=4),
                docs_column,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
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
            label="Expiry Date *",
            value=doc["expiry_date"] if is_edit else "",
            border_radius=8,
            bgcolor=C.INPUT_BG,
            border_color=C.BORDER,
            color=C.TEXT,
            label_style=ft.TextStyle(color=C.TEXT2),
            hint_text="YYYY-MM-DD",
            read_only=True,
        )

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

        # Date pickers
        def on_start_date_picked(e):
            if e.control.value:
                start_date_field.value = e.control.value.strftime("%Y-%m-%d")
                start_date_field.error_text = None
                page.update()

        def on_expiry_date_picked(e):
            if e.control.value:
                expiry_date_field.value = e.control.value.strftime("%Y-%m-%d")
                expiry_date_field.error_text = None
                page.update()

        start_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=on_start_date_picked,
            confirm_text="SELECT",
            cancel_text="CANCEL",
        )

        expiry_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=on_expiry_date_picked,
            confirm_text="SELECT",
            cancel_text="CANCEL",
        )

        page.overlay.append(start_date_picker)
        page.overlay.append(expiry_date_picker)

        def open_start_picker(e):
            start_date_picker.open = True
            page.update()

        def open_expiry_picker(e):
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
            has_error = False

            if not name_field.value or not name_field.value.strip():
                name_field.error_text = "Document name is required"
                has_error = True
            else:
                name_field.error_text = None

            if not category_field.value:
                category_field.error_text = "Please select a category"
                has_error = True
            else:
                category_field.error_text = None

            if not start_date_field.value or not start_date_field.value.strip():
                start_date_field.error_text = "Start date is required"
                has_error = True
            else:
                try:
                    datetime.strptime(start_date_field.value, "%Y-%m-%d")
                    start_date_field.error_text = None
                except ValueError:
                    start_date_field.error_text = "Invalid date format"
                    has_error = True

            if not expiry_date_field.value or not expiry_date_field.value.strip():
                expiry_date_field.error_text = "Expiry date is required"
                has_error = True
            else:
                try:
                    datetime.strptime(expiry_date_field.value, "%Y-%m-%d")
                    expiry_date_field.error_text = None
                except ValueError:
                    expiry_date_field.error_text = "Invalid date format"
                    has_error = True

            if not reminder_field.value:
                reminder_field.error_text = "Please select reminder period"
                has_error = True
            else:
                reminder_field.error_text = None

            if not notes_field.value or not notes_field.value.strip():
                notes_field.error_text = "Notes are required"
                has_error = True
            else:
                notes_field.error_text = None

            if has_error:
                page.update()
                return

            # Validate start < expiry
            start_dt = datetime.strptime(start_date_field.value, "%Y-%m-%d")
            expiry_dt = datetime.strptime(expiry_date_field.value, "%Y-%m-%d")
            if expiry_dt <= start_dt:
                expiry_date_field.error_text = "Expiry must be after start date"
                page.update()
                return

            if is_edit:
                update_document(
                    doc_id=doc["id"],
                    name=name_field.value.strip(),
                    category=category_field.value,
                    start_date=start_date_field.value,
                    expiry_date=expiry_date_field.value,
                    reminder_days=int(reminder_field.value),
                    notes=notes_field.value.strip(),
                )
                show_snack("Document updated!")
            else:
                add_document(
                    name=name_field.value.strip(),
                    category=category_field.value,
                    start_date=start_date_field.value,
                    expiry_date=expiry_date_field.value,
                    reminder_days=int(reminder_field.value),
                    notes=notes_field.value.strip(),
                )
                show_snack("Document added!")

            # Clean up overlays
            if start_date_picker in page.overlay:
                page.overlay.remove(start_date_picker)
            if expiry_date_picker in page.overlay:
                page.overlay.remove(expiry_date_picker)

            navigate("dashboard")

        def handle_cancel(e):
            if start_date_picker in page.overlay:
                page.overlay.remove(start_date_picker)
            if expiry_date_picker in page.overlay:
                page.overlay.remove(expiry_date_picker)
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
                        ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=C.TEXT),
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
                expiry_date_row,
                ft.Container(height=4),
                reminder_field,
                ft.Container(height=4),
                notes_field,
                ft.Container(height=16),
                # Save button
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(btn_icon, color="#ffffff", size=18),
                            ft.Text(btn_text, size=15, weight=ft.FontWeight.W_600, color="#ffffff"),
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
                            ft.Text("Cancel", size=14, weight=ft.FontWeight.W_500, color=C.TEXT2),
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
    # NAVIGATION
    # =======================
    content_area = ft.Container(expand=True, padding=16)

    def navigate(view_name, data=None):
        if view_name == "dashboard":
            content_area.content = build_dashboard()
            nav_bar.selected_index = 0
        elif view_name == "documents":
            content_area.content = build_documents()
            nav_bar.selected_index = 1
        elif view_name == "add":
            content_area.content = build_form(doc=None)
            nav_bar.selected_index = 2
        elif view_name == "edit":
            content_area.content = build_form(doc=data)
            nav_bar.selected_index = 1
        page.update()

    def on_nav_change(e):
        idx = e.control.selected_index
        views = ["dashboard", "documents", "add"]
        navigate(views[idx])

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
                    content_area,
                    nav_bar,
                ],
                expand=True,
                spacing=0,
            ),
            expand=True,
        )
    )

    navigate("dashboard")


ft.run(main)
