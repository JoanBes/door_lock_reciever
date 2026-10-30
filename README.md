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
