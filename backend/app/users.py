import os
import sqlite3

import bcrypt

from app.database import get_connection


USER_ROLES = {"admin", "user"}


def initialize_users_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def initialize_users() -> None:
    with get_connection() as connection:
        initialize_users_table(connection)
        seed_initial_admin(connection)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(email: str, password: str, role: str = "user") -> dict:
    initialize_users()

    if role not in USER_ROLES:
        raise ValueError("Invalid role")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (normalize_email(email), hash_password(password), role),
        )
        row = connection.execute(
            """
            SELECT id, email, role, created_at
            FROM users
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return dict(row)


def get_user_by_email(email: str) -> dict | None:
    initialize_users()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, password_hash, role, created_at
            FROM users
            WHERE email = ?
            """,
            (normalize_email(email),),
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    initialize_users()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, password_hash, role, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if user is None or not verify_password(password, user["password_hash"]):
        return None
    return user


def seed_initial_admin(connection: sqlite3.Connection) -> None:
    admin_count = connection.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ).fetchone()[0]
    if admin_count > 0:
        return

    email = os.getenv("INITIAL_ADMIN_EMAIL")
    password = os.getenv("INITIAL_ADMIN_PASSWORD")
    if not email or not password:
        return

    normalized_email = normalize_email(email)
    existing_user = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (normalized_email,),
    ).fetchone()
    if existing_user is not None:
        return

    connection.execute(
        """
        INSERT INTO users (email, password_hash, role)
        VALUES (?, ?, 'admin')
        """,
        (normalized_email, hash_password(password)),
    )
