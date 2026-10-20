"""Entry point: starts the MQTT bridge and the web interface."""

import os

from app.factory import create_app
from app.mqtt_bridge import build_bridge


def main():
    bridge = None
    try:
        app = create_app()
        bridge = build_bridge()
        bridge.start()
        app.run(host="0.0.0.0", port=int(os.getenv("HTTP_PORT", "5000")))
    finally:
        if bridge is not None:
            bridge.stop()


if __name__ == "__main__":
    main()
