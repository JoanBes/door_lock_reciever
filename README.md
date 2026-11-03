# MQTT receiver for the ESP32 door lock

This Python server connects to an MQTT broker, listens for RFID reads from the
ESP32, checks card permissions against a SQLite database, and returns an
authorization code when appropriate. It records reads, access decisions, door
closures, and connection status as events.

## MQTT and RFID flow

The receiver subscribes to the RFID, released, and status topics for each
registered door:

1. On an RFID message, it normalizes the UID and checks that the card is active
   and authorized for that door (`cards` and `door_cards`).
2. If authorized, it calculates the FNV-1a code and publishes it to the door's
   command topic. Otherwise, it sends no response.
3. Every authorized or denied attempt is recorded in `events`.
4. A `released` message indicates that the ESP32 has closed the door after the
   same card was scanned again. The closure is recorded without revalidation,
   since the ESP32 has already checked the card locally.
5. Status messages (`online` or `offline`) are recorded and update the door
   state in the database.

The ESP32 firmware must use the same topic pattern and access-code algorithm.
If either changes, update both sides. Door topics are stored in the `doors`
table, allowing multiple doors to use different topics.

## Requirements

- Python 3.10 or later
- pip
- Access to an MQTT broker with TLS

## Installation

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuration

The server loads variables from a `.env` file in the project directory.
Already exported environment variables take precedence. Copy `.env.example` to
`.env` and set the required broker values, or export them directly:

```bash
export MQTT_BROKER="your-broker.example.com"
export MQTT_PORT="8883"
export MQTT_USERNAME="server"
export MQTT_PASSWORD="your-password"
export MQTT_CLIENT_ID="door-lock-server"
export HTTP_PORT="5000"
```

`MQTT_BROKER`, `MQTT_USERNAME`, and `MQTT_PASSWORD` are required. See
`.env.example` for the complete list. Never commit real credentials.

## Database

Create the database on first use, or after deleting `data/door_lock.db`:

```bash
python db/init_db.py --seed
```

`--seed` creates the web administrator using `ADMIN_USERNAME`,
`ADMIN_PASSWORD`, and `ADMIN_NAME`. By default the username and name are
`admin` and the password is `admin1234`; change the password. It also creates
an active student card for the main door (UID `11:3B:12:07`, account
`magicalonso@example.es`).

The command registers the `ESP32_Door_Lock_01` door with
`doorlockJBL/01/...` topics. To add authorized cards directly with SQL:

```sql
INSERT INTO cards (uid, owner_name, active) VALUES ('A1B2C3D4', 'Name', 1);
INSERT INTO door_cards (door_id, card_id)
  SELECT 1, id FROM cards WHERE uid = 'A1B2C3D4';
```

The UID must be normalized as in the firmware: uppercase alphanumeric
characters only. Older databases are not migrated; if the schema changes,
create a new database and run the seed command again. Set the optional
`DB_PATH` variable to change the database location. See
[`db/SCHEMA.md`](db/SCHEMA.md) for the table descriptions.

## Running the server

With the virtual environment active and the database initialized:

```bash
python server.py
```

This starts the MQTT connection, subscribes to registered door topics, and
serves the LibraGate web interface at `http://0.0.0.0:5000`. Set the optional
`SECRET_KEY` for session security; otherwise a key is generated in
`data/.secret_key`.

## Project structure

```text
server.py              Entry point for MQTT and the web server
app/
  config.py            Paths and environment variables
  database.py          Database connection and initialization
  seed.py              Initial door, administrator, and student data
  security.py          Sessions and role decorators
  access_code.py       UID normalization and ESP32-compatible FNV-1a code
  mqtt_bridge.py       MQTT client and authorization logic
  factory.py           Flask application factory
  utils.py             Dates, LIKE searches, and CSV safety
  repositories/        SQL queries for users, doors, events, and cards
  routes/              Pages and API blueprints
templates/ static/     Web interface (HTML, CSS, and JavaScript)
db/                    Schema, initialization CLI, and schema documentation
```
