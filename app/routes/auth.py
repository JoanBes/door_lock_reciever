from flask import Blueprint, jsonify, request, session

from app.database import get_db
from app.repositories import users

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    account = users.authenticate(
        get_db(), str(data.get("username", "")), str(data.get("password", ""))
    )
    if account is None:
        return jsonify({"error": "Invalid ID or password"}), 401
    session.clear()
    session.update(account)
    return jsonify({"ok": True, "role": account["role"]})


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})
