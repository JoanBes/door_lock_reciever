from flask import Blueprint, jsonify, request

from app.database import get_db
from app.repositories import doors
from app.security import login_required
from app.utils import start_of_today_utc, to_db_timestamp

bp = Blueprint("overview", __name__, url_prefix="/api")


@bp.get("/overview")
@login_required
def overview():
    connection = get_db()
    since = to_db_timestamp(request.args.get("since")) or start_of_today_utc()
    rooms = doors.room_overview(connection)
    return jsonify(
        {
            "entries_today": doors.entries_since(connection, since),
            "occupied": sum(1 for room in rooms if room["state"] == "unlocked"),
            "total_rooms": len(rooms),
            "rooms": rooms,
        }
    )
