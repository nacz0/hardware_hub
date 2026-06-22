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


def get_hardware(hardware_id: int) -> dict | None:
    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
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
            WHERE id = ?
            """,
            (hardware_id,),
        ).fetchone()

    return dict(row) if row else None


def create_hardware(data: dict) -> dict:
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
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
            (
                data.get("external_id"),
                data["name"],
                data.get("brand"),
                data.get("purchase_date"),
                data.get("status"),
                data.get("notes"),
                data.get("assigned_to"),
                data.get("history"),
            ),
        )

    hardware = get_hardware(cursor.lastrowid)
    if hardware is None:
        raise RuntimeError("Created hardware could not be loaded")
    return hardware


def delete_hardware(hardware_id: int) -> bool:
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM hardware WHERE id = ?",
            (hardware_id,),
        )

    return cursor.rowcount > 0


def update_hardware_status(
    hardware_id: int,
    status_value: str,
    assigned_to: str | None,
) -> dict | None:
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE hardware
            SET status = ?, assigned_to = ?
            WHERE id = ?
            """,
            (status_value, assigned_to, hardware_id),
        )

    if cursor.rowcount == 0:
        return None
    return get_hardware(hardware_id)


def transition_hardware_status(
    hardware_id: int,
    expected_status: str,
    status_value: str,
    assigned_to: str | None,
) -> dict | None:
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE hardware
            SET status = ?, assigned_to = ?
            WHERE id = ? AND status = ?
            """,
            (status_value, assigned_to, hardware_id, expected_status),
        )

    if cursor.rowcount == 0:
        return None
    return get_hardware(hardware_id)


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
