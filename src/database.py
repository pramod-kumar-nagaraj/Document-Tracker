import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            start_date TEXT,
            expiry_date TEXT,
            reminder_days INTEGER DEFAULT 7,
            alert_time TEXT DEFAULT '08:00',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Add alert_time column if upgrading from old schema
    try:
        cursor.execute(
            "ALTER TABLE documents ADD COLUMN alert_time TEXT DEFAULT '08:00'"
        )
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add links column if upgrading from old schema
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN links TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Profile table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            full_name TEXT DEFAULT '',
            emails TEXT DEFAULT '',
            phones TEXT DEFAULT '',
            passport_number TEXT DEFAULT '',
            driving_license TEXT DEFAULT '',
            address TEXT DEFAULT '',
            date_of_birth TEXT DEFAULT '',
            nationality TEXT DEFAULT ''
        )
        """
    )
    # Ensure one profile row exists
    cursor.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")

    conn.commit()
    conn.close()


def add_document(
    name,
    category,
    start_date,
    expiry_date,
    reminder_days,
    notes,
    alert_time="08:00",
    links="",
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO documents (name, category, start_date, expiry_date, reminder_days, alert_time, notes, links)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            category,
            start_date,
            expiry_date,
            reminder_days,
            alert_time,
            notes,
            links,
        ),
    )

    conn.commit()
    conn.close()


def get_documents(search=""):
    conn = get_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute(
            """
            SELECT * FROM documents
            WHERE name LIKE ? OR category LIKE ? OR notes LIKE ?
            ORDER BY expiry_date ASC
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        )
    else:
        cursor.execute("SELECT * FROM documents ORDER BY expiry_date ASC")

    data = cursor.fetchall()
    conn.close()
    return data


def delete_document(doc_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


def update_document(
    doc_id,
    name,
    category,
    start_date,
    expiry_date,
    reminder_days,
    notes,
    alert_time="08:00",
    links="",
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE documents
        SET name=?, category=?, start_date=?, expiry_date=?, reminder_days=?, alert_time=?, notes=?, links=?
        WHERE id=?
        """,
        (
            name,
            category,
            start_date,
            expiry_date,
            reminder_days,
            alert_time,
            notes,
            links,
            doc_id,
        ),
    )

    conn.commit()
    conn.close()


def get_document_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM documents")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents WHERE expiry_date >= date('now')")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents WHERE expiry_date < date('now')")
    expired = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM documents
        WHERE expiry_date >= date('now')
        AND expiry_date <= date('now', '+7 days')
        """
    )
    expiring_soon = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "active": active,
        "expired": expired,
        "expiring_soon": expiring_soon,
    }


def get_profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "full_name": "",
        "emails": "",
        "phones": "",
        "passport_number": "",
        "driving_license": "",
        "address": "",
        "date_of_birth": "",
        "nationality": "",
    }


def save_profile(
    full_name,
    emails,
    phones,
    passport_number,
    driving_license,
    address,
    date_of_birth,
    nationality,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE profile SET
            full_name=?, emails=?, phones=?, passport_number=?,
            driving_license=?, address=?, date_of_birth=?, nationality=?
        WHERE id = 1
        """,
        (
            full_name,
            emails,
            phones,
            passport_number,
            driving_license,
            address,
            date_of_birth,
            nationality,
        ),
    )
    conn.commit()
    conn.close()
