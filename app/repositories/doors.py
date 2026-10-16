def room_overview(connection):
    rows = connection.execute(
        """
        SELECT doors.id, doors.name, doors.location, doors.capacity, doors.state,
               (SELECT MAX(created_at) FROM events WHERE events.door_id = doors.id)
                   AS latest_event
        FROM doors ORDER BY doors.name
        """
    ).fetchall()
    return [dict(row) for row in rows]


def entries_since(connection, since):
    return connection.execute(
        "SELECT COUNT(*) FROM events WHERE event_type = 'access_granted' AND created_at >= ?",
        (since,),
    ).fetchone()[0]
