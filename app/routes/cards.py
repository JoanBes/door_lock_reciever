from flask import Blueprint, jsonify, request

from app.database import get_db
from app.repositories import cards
from app.security import admin_required

bp = Blueprint("cards", __name__, url_prefix="/api/cards")


def _json_error(error):
    status = 409 if isinstance(error, cards.ConflictError) else 400
    return jsonify({"error": str(error)}), status


@bp.get("")
@admin_required
def list_cards():
    connection = get_db()
    registered, active, inactive = cards.stats(connection)
    total, items = cards.search(connection, request.args)
    return jsonify({"registered": registered, "active": active, "inactive": inactive,
                    "total": total, "items": items})


@bp.post("")
@admin_required
def create_card():
    connection = get_db()
    try:
        return jsonify({
            "id": cards.create(connection, request.get_json(silent=True) or {})
        }), 201
    except (cards.ValidationError, cards.ConflictError) as error:
        return _json_error(error)


@bp.put("/<int:card_id>")
@admin_required
def update_card(card_id):
    connection = get_db()
    try:
        if not cards.update(connection, card_id, request.get_json(silent=True) or {}):
            return jsonify({"error": "card not found"}), 404
        return jsonify({"id": card_id})
    except (cards.ValidationError, cards.ConflictError) as error:
        return _json_error(error)


@bp.patch("/<int:card_id>")
@admin_required
def toggle_card(card_id):
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("active"), bool):
        return jsonify({"error": "'active' must be true or false"}), 400
    if not cards.set_active(get_db(), card_id, data["active"]):
        return jsonify({"error": "card not found"}), 404
    return jsonify({"id": card_id, "active": data["active"]})


@bp.delete("/<int:card_id>")
@admin_required
def delete_card(card_id):
    if not cards.delete(get_db(), card_id):
        return jsonify({"error": "card not found"}), 404
    return jsonify({"id": card_id, "deleted": True})
