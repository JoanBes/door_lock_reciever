import sqlite3
from pathlib import Path

from flask import g

from app import config


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path or config.DB_PATH, check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.row_factory = sqlite3.Row
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = get_connection()
    return g.db


def close_db(_error=None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection(db_path)
    connection.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.commit()
    return connection
