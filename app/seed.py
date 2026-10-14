"""Initial data for the default door, administrator and student."""

import os
import sqlite3

from werkzeug.security import generate_password_hash

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin1234"
DEFAULT_STUDENT_UID = "113B1207"
DEFAULT_STUDENT_EMAIL = "magicalonso@example.es"
DEFAULT_STUDENT_PASSWORD_HASH = (
    "scrypt:32768:8:1$DASqnbc2L16vyJPO$"
    "e50119db14e4fbaa73881df9a6b150ebae67f5843ab68f1ff7a572d0b788a77f"
    "5954ed1816bc0c5a6b087d8c94a593dee11ae567f09c0779b05b46c927f251fc"
)


def seed_default_data(connection: sqlite3.Connection) -> None:
    # Topics follow the "doorlockJBL/<device>/..." pattern used on the broker.
    connection.execute(
        """
        INSERT OR IGNORE INTO doors
            (device_id, name, rfid_topic, command_topic, released_topic, status_topic, state)
        VALUES (?, ?, ?, ?, ?, ?, 'locked')
        """,
        (
            "ESP32_Door_Lock_01", "Main door",
            "doorlockJBL/01/rfid", "doorlockJBL/01/command",
            "doorlockJBL/01/released", "doorlockJBL/01/status",
        ),
    )
    username = os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    full_name = os.getenv("ADMIN_NAME", DEFAULT_ADMIN_USERNAME)
    admin = connection.execute(
        "INSERT OR IGNORE INTO admin_users (username, full_name, role, password_hash) "
        "VALUES (?, ?, 'Administrator', ?)",
        (username, full_name, generate_password_hash(password)),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO cards
            (uid, owner_name, email, password_hash, active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (
            DEFAULT_STUDENT_UID,
            "Fernando Alonso Diaz",
            DEFAULT_STUDENT_EMAIL,
            DEFAULT_STUDENT_PASSWORD_HASH,
        ),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO door_cards (door_id, card_id)
        SELECT doors.id, cards.id
        FROM doors JOIN cards ON cards.uid = ?
        WHERE doors.device_id = ?
        """,
        (DEFAULT_STUDENT_UID, "ESP32_Door_Lock_01"),
    )
    connection.commit()
    if admin.rowcount and "ADMIN_PASSWORD" not in os.environ:
        print(
            f"Admin created: username '{username}' / password '{password}' "
            "(change it with ADMIN_PASSWORD)."
        )
