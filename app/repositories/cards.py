import sqlite3

from werkzeug.security import generate_password_hash

from app import config
from app.access_code import normalize_code
from app.utils import like_pattern

SORT_ORDERS = {
    "name": "owner_name COLLATE NOCASE ASC",
    "issued": "created_at DESC",
    "recent": "id DESC",
}
COLUMNS = "id, uid, owner_name, student_id, email, active, created_at, (password_hash IS NOT NULL) AS has_login"


class ValidationError(ValueError):
    pass


class ConflictError(ValueError):
    pass


def _clean(data):
    uid = normalize_code(str(data.get("uid", "")))
    name = str(data.get("owner_name", "")).strip()
    student_id = str(data.get("student_id", "")).strip() or None
    email = str(data.get("email", "")).strip() or None
    password = str(data.get("password", ""))
    if not uid or not name:
        raise ValidationError("Name and RFID UID are required")
    if not uid.isascii():
        raise ValidationError("RFID UID must contain only letters and digits")
    if password and len(password) < config.MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must have at least {config.MIN_PASSWORD_LENGTH} characters")
    if password and not (student_id or email):
        raise ValidationError("A student ID or email is needed to sign in")
    return uid, name, student_id, email, password


def _row(row):
    data = dict(row)
    data["active"] = bool(data["active"])
    data["has_login"] = bool(data["has_login"])
    return data


def stats(connection):
    registered, active = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(active), 0) FROM cards"
    ).fetchone()
    return registered, active, registered - active


def search(connection, args):
    conditions, params = "", []
    term = (args.get("q") or "").strip()
    if term:
        conditions = (
            " WHERE owner_name LIKE ? ESCAPE '\\' OR student_id LIKE ? ESCAPE '\\'"
            " OR uid LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\'"
        )
        params = [like_pattern(term)] * 4
    total = connection.execute("SELECT COUNT(*) FROM cards" + conditions, params).fetchone()[0]
    order = SORT_ORDERS.get(args.get("sort"), SORT_ORDERS["recent"])
    per_page = max(1, min(args.get("per_page", default=8, type=int), 100))
    page = max(1, args.get("page", default=1, type=int))
    rows = connection.execute(
        f"SELECT {COLUMNS} FROM cards{conditions} ORDER BY {order} LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page],
    ).fetchall()
    return total, [_row(row) for row in rows]


def create(connection, data):
    uid, name, student_id, email, password = _clean(data)
    try:
        cursor = connection.execute(
            "INSERT INTO cards (uid, owner_name, student_id, email, password_hash, active) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (uid, name, student_id, email, generate_password_hash(password) if password else None),
        )
    except sqlite3.IntegrityError:
        raise ConflictError("RFID UID or student ID already registered") from None
    connection.execute(
        "INSERT INTO door_cards (door_id, card_id) SELECT id, ? FROM doors", (cursor.lastrowid,)
    )
    connection.commit()
    return cursor.lastrowid


def update(connection, card_id, data):
    """Edit a student. Blank password keeps the current one."""
    uid, name, student_id, email, password = _clean(data)
    try:
        cursor = connection.execute(
            "UPDATE cards SET uid = ?, owner_name = ?, student_id = ?, email = ? WHERE id = ?",
            (uid, name, student_id, email, card_id),
        )
        if password:
            connection.execute(
                "UPDATE cards SET password_hash = ? WHERE id = ?",
                (generate_password_hash(password), card_id),
            )
    except sqlite3.IntegrityError:
        connection.rollback()
        raise ConflictError("RFID UID or student ID already registered") from None
    connection.commit()
    return cursor.rowcount > 0


def set_active(connection, card_id, active):
    cursor = connection.execute("UPDATE cards SET active = ? WHERE id = ?", (int(active), card_id))
    connection.commit()
    return cursor.rowcount > 0


def delete(connection, card_id):
    cursor = connection.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    connection.commit()
    return cursor.rowcount > 0
