"""MQTT bridge: authorizes RFID reads against the database and logs events."""

import os

import paho.mqtt.client as mqtt

from app.access_code import derive_access_code, normalize_code
from app.database import get_connection


def log_event(connection, door_id, card_id, uid, event_type):
    connection.execute(
        "INSERT INTO events (door_id, card_id, uid, event_type) VALUES (?, ?, ?, ?)",
        (door_id, card_id, uid, event_type),
    )
    connection.commit()


def set_door_state(connection, door_id, state):
    connection.execute(
        "UPDATE doors SET state = ?, last_seen_at = CURRENT_TIMESTAMP WHERE id = ?",
        (state, door_id),
    )
    connection.commit()


def find_authorized_card(connection, door_id, uid):
    return connection.execute(
        """
        SELECT cards.* FROM cards
        JOIN door_cards ON door_cards.card_id = cards.id
        WHERE door_cards.door_id = ? AND cards.uid = ? AND cards.active = 1
        """,
        (door_id, uid),
    ).fetchone()


class MqttBridge:
    """Receives door-lock messages, checks authorization against the
    database, answers RFID requests, and logs every event."""

    def __init__(self, mqtt_client, broker, port, username, password):
        self.client = mqtt_client
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.connection = get_connection()

        doors = self.connection.execute("SELECT * FROM doors").fetchall()
        if not doors:
            raise RuntimeError(
                "No doors are registered. Run `python db/init_db.py --seed` first."
            )
        self.doors_by_rfid_topic = {door["rfid_topic"]: door for door in doors}
        self.doors_by_released_topic = {door["released_topic"]: door for door in doors}
        self.doors_by_status_topic = {door["status_topic"]: door for door in doors}

        # A released message carries the code, not the UID, so retain the
        # card that opened each door to identify it when the door closes.
        self.open_card_by_door_id = {}

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self):
        if self.username:
            self.client.username_pw_set(self.username, self.password)
        self.client.tls_set()
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        print(f"MQTT connected: {reason_code}")
        for door in self.doors_by_rfid_topic.values():
            client.subscribe(door["rfid_topic"])
            client.subscribe(door["released_topic"])
            client.subscribe(door["status_topic"])
            print(f"Subscribed to topics for door '{door['name']}'")

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode("utf-8", errors="replace")
        print(f"MQTT received | topic={topic} | message={payload}")

        if topic in self.doors_by_rfid_topic:
            self._handle_rfid(self.doors_by_rfid_topic[topic], payload)
        elif topic in self.doors_by_released_topic:
            self._handle_released(self.doors_by_released_topic[topic])
        elif topic in self.doors_by_status_topic:
            self._handle_status(self.doors_by_status_topic[topic], payload)

    def _handle_rfid(self, door, raw_uid):
        uid = normalize_code(raw_uid)
        if not uid:
            print("Empty RFID: no response sent")
            return

        log_event(self.connection, door["id"], None, uid, "rfid_read")

        card = find_authorized_card(self.connection, door["id"], uid)
        if card is None:
            print(f"Access denied for {uid}")
            log_event(self.connection, door["id"], None, uid, "access_denied")
            return

        response_topic = door["command_topic"]
        access_code = derive_access_code(uid)
        self.client.publish(response_topic, access_code)
        self.open_card_by_door_id[door["id"]] = card
        print(
            f"Authorization sent | topic={response_topic} | "
            f"code={access_code} | card={card['owner_name'] or uid}"
        )
        log_event(self.connection, door["id"], card["id"], uid, "access_granted")
        set_door_state(self.connection, door["id"], "unlocked")

    def _handle_released(self, door):
        card = self.open_card_by_door_id.pop(door["id"], None)
        card_id = card["id"] if card else None
        uid = card["uid"] if card else "unknown"
        print(f"Door released | door={door['name']} | card={uid}")
        log_event(self.connection, door["id"], card_id, uid, "door_closed")
        set_door_state(self.connection, door["id"], "locked")

    def _handle_status(self, door, status):
        print(f"Status of {door['name']}: {status}")
        event_type = "status_online" if status == "online" else "status_offline"
        log_event(self.connection, door["id"], None, status, event_type)
        if status == "offline":
            set_door_state(self.connection, door["id"], "offline")


def build_bridge():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=os.getenv("MQTT_CLIENT_ID", "door-lock-server"),
    )
    return MqttBridge(
        mqtt_client=client,
        broker=os.environ["MQTT_BROKER"],
        port=int(os.getenv("MQTT_PORT", "8883")),
        username=os.environ["MQTT_USERNAME"],
        password=os.environ["MQTT_PASSWORD"],
    )
