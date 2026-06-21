from pathlib import Path
import sqlite3

from app.seed_data import HARDWARE_SEED


DATABASE_PATH = Path(__file__).resolve().parent.parent / "hardware_hub.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    from app.users import initialize_users_table, seed_initial_admin

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hardware (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id INTEGER,
                name TEXT NOT NULL,
                brand TEXT,
                purchase_date TEXT,
                status TEXT,
                notes TEXT,
                assigned_to TEXT,
                history TEXT
            )
            """
        )

        initialize_users_table(connection)
        seed_hardware(connection)
        seed_initial_admin(connection)


def list_hardware() -> list[dict]:
    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                external_id,
                name,
                brand,
                purchase_date,
                status,
                notes,
                assigned_to,
                history
            FROM hardware
            ORDER BY id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def seed_hardware(connection: sqlite3.Connection) -> None:
    row_count = connection.execute("SELECT COUNT(*) FROM hardware").fetchone()[0]
    if row_count > 0:
        return

    # Preserve dirty seed data verbatim so the AI auditor can detect it later.
    connection.executemany(
        """
        INSERT INTO hardware (
            external_id,
            name,
            brand,
            purchase_date,
            status,
            notes,
            assigned_to,
            history
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.get("id"),
                item.get("name"),
                item.get("brand"),
                item.get("purchaseDate"),
                item.get("status"),
                item.get("notes"),
                item.get("assignedTo"),
                item.get("history"),
            )
            for item in HARDWARE_SEED
        ],
    )
