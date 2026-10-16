from functools import wraps

from flask import jsonify, redirect, request, session, url_for

from app.database import get_db
from app.repositories.users import ROLE_ADMIN, initials, student_is_active


def current_user():
    name = session.get("name", "")
    return {
        "name": name,
        "title": session.get("title", ""),
        "role": session.get("role"),
        "initials": initials(name),
    }


def _still_valid():
    """Students lose access immediately when deactivated or deleted."""
    if session.get("role") == ROLE_ADMIN:
        return True
    return student_is_active(get_db(), session["user_id"])


def _deny(status, message, page_redirect):
    if request.path.startswith("/api/"):
        return jsonify({"error": message}), status
    return redirect(url_for(page_redirect))


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return _deny(401, "authentication required", "pages.login")
        if not _still_valid():
            session.clear()
            return _deny(401, "authentication required", "pages.login")
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != ROLE_ADMIN:
            return _deny(403, "administrator access required", "pages.overview")
        return view(*args, **kwargs)

    return wrapper
