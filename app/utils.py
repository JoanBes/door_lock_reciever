from datetime import datetime, timezone


def to_db_timestamp(value):
    """Convert an ISO-8601 string from the browser to the UTC format stored in SQLite."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def start_of_today_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d 00:00:00")


def like_pattern(text):
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def csv_safe(value):
    """Prevent spreadsheet formula injection from user-controlled text."""
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value
