"""Create the door lock server's SQLite database.

Usage:
    python db/init_db.py [--db PATH] [--seed]

Without --seed, only creates the tables.
--seed  registers the default door, web administrator and authorized student.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.database import init_db  # noqa: E402
from app.seed import seed_default_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=config.DB_PATH,
                        help=f"Path to the SQLite file (default: {config.DB_PATH})")
    parser.add_argument("--seed", action="store_true",
                        help="Register the default door, administrator and student")
    args = parser.parse_args()

    connection = init_db(args.db)
    if args.seed:
        seed_default_data(connection)
    connection.close()
    print(f"Database ready at: {args.db}")


if __name__ == "__main__":
    main()
