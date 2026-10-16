"""Web accounts: administrators (admin_users) and students (cards with a password)."""

from werkzeug.security import check_password_hash

ROLE_ADMIN = "admin"
ROLE_STUDENT = "student"


def initials(name):
    return "".join(part[0] for part in (name or "?").split()[:2]).upper()


def authenticate(connection, identifier, password):
    """Return the session data for valid credentials, otherwise None."""
    identifier = identifier.strip()
    if not identifier or not password:
        return None

    admin = connection.execute(
        "SELECT * FROM admin_users WHERE username = ?", (identifier,)
    ).fetchone()
    if admin is not None:
        if check_password_hash(admin["password_hash"], password):
            return {"user_id": admin["id"], "role": ROLE_ADMIN,
                    "name": admin["full_name"], "title": admin["role"]}
        return None

    student = connection.execute(
        """
        SELECT * FROM cards
        WHERE (LOWER(student_id) = LOWER(?) OR LOWER(email) = LOWER(?))
          AND password_hash IS NOT NULL
        """,
        (identifier, identifier),
    ).fetchone()
    if student and student["active"] and check_password_hash(student["password_hash"], password):
        return {"user_id": student["id"], "role": ROLE_STUDENT,
                "name": student["owner_name"] or identifier, "title": "Student"}
    return None


def student_is_active(connection, card_id):
    row = connection.execute("SELECT active FROM cards WHERE id = ?", (card_id,)).fetchone()
    return bool(row and row["active"])
