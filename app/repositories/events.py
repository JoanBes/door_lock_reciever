from app.utils import like_pattern, to_db_timestamp

RESULT_TYPES = {"granted": "access_granted", "denied": "access_denied"}


def query_access_events(connection, args, paginate=True):
    """Access attempts (granted/denied) joined with card and room data."""
    conditions = ["events.event_type IN ('access_granted', 'access_denied')"]
    params = []

    search = (args.get("q") or "").strip()
    if search:
        conditions.append(
            "(cards.student_id LIKE ? ESCAPE '\\' OR events.uid LIKE ? ESCAPE '\\' "
            "OR cards.owner_name LIKE ? ESCAPE '\\')"
        )
        params += [like_pattern(search)] * 3
    since = to_db_timestamp(args.get("from"))
    if since:
        conditions.append("events.created_at >= ?")
        params.append(since)
    until = to_db_timestamp(args.get("to"))
    if until:
        conditions.append("events.created_at < ?")
        params.append(until)
    result = RESULT_TYPES.get(args.get("result"))
    if result:
        conditions.append("events.event_type = ?")
        params.append(result)

    where = " WHERE " + " AND ".join(conditions)
    source = (
        " FROM events LEFT JOIN cards ON cards.uid = events.uid "
        "LEFT JOIN doors ON doors.id = events.door_id"
    )
    total = connection.execute("SELECT COUNT(*)" + source + where, params).fetchone()[0]

    select = (
        "SELECT events.id, events.created_at, events.uid, events.event_type, "
        "cards.owner_name, cards.student_id, doors.name AS room"
    )
    order = " ORDER BY events.id DESC"
    page_params = []
    if paginate:
        per_page = max(1, min(args.get("per_page", default=10, type=int), 100))
        page = max(1, args.get("page", default=1, type=int))
        order += " LIMIT ? OFFSET ?"
        page_params = [per_page, (page - 1) * per_page]
    rows = connection.execute(select + source + where + order, params + page_params).fetchall()
    return total, [dict(row) for row in rows]
