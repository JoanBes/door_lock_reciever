import csv
import io

from flask import Blueprint, Response, jsonify, request

from app.database import get_db
from app.repositories.events import query_access_events
from app.security import admin_required
from app.utils import csv_safe

bp = Blueprint("events", __name__, url_prefix="/api/events")


@bp.get("")
@admin_required
def list_events():
    total, items = query_access_events(get_db(), request.args)
    return jsonify({"total": total, "items": items})


@bp.get("/export.csv")
@admin_required
def export_events():
    _, items = query_access_events(get_db(), request.args, paginate=False)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp_utc", "student_name", "student_id", "uid", "room", "result"])
    for item in items:
        writer.writerow([
            item["created_at"],
            csv_safe(item["owner_name"] or "Unknown credential"),
            csv_safe(item["student_id"] or ""),
            item["uid"],
            item["room"] or "",
            "granted" if item["event_type"] == "access_granted" else "denied",
        ])
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=access_logs.csv"},
    )
