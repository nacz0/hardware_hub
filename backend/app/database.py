from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parent.parent / "hardware_hub.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection():
        pass
