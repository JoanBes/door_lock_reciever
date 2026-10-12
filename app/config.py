import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "door_lock.db"))
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
SECRET_KEY_PATH = DB_PATH.parent / ".secret_key"

MIN_PASSWORD_LENGTH = 6


def load_secret_key() -> str:
    """SECRET_KEY from the environment, or a random key persisted next to the DB."""
    if os.getenv("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    if not SECRET_KEY_PATH.exists():
        SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SECRET_KEY_PATH.write_text(secrets.token_hex(32))
        SECRET_KEY_PATH.chmod(0o600)
    return SECRET_KEY_PATH.read_text().strip()
