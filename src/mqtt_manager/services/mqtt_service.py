"""MQTT Service — paho-mqtt client with PySide6 signal integration."""

from __future__ import annotations

import threading

import paho.mqtt.client as mqtt
from PySide6.QtCore import QObject, Signal


class MQTTService(QObject):
    """Wraps paho-mqtt with Qt signals for UI integration."""

    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str, bytes, int, bool)  # topic, payload, qos, retain
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client: mqtt.Client | None = None
        self._loop_thread: threading.Thread | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(
        self,
        host: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
    ):
        self.disconnect()

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTv311,
        )

        if username:
            self._client.username_pw_set(username, password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect(host, port, keepalive=60)
            self._client.loop_start()
        except Exception as exc:
            self.error.emit(str(exc))

    def disconnect(self):
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            self._client = None

    # ------------------------------------------------------------------
    # Pub / Sub
    # ------------------------------------------------------------------

    def subscribe(self, topic: str, qos: int = 0):
        if self._client and self._client.is_connected():
            self._client.subscribe(topic, qos)

    def unsubscribe(self, topic: str):
        if self._client and self._client.is_connected():
            self._client.unsubscribe(topic)

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        if self._client and self._client.is_connected():
            self._client.publish(topic, payload.encode(), qos=qos, retain=retain)

    # ------------------------------------------------------------------
    # paho callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self.connected.emit()
        else:
            self.error.emit(f"MQTT connect failed: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.disconnected.emit()

    def _on_message(self, client, userdata, msg):
        self.message_received.emit(msg.topic, msg.payload, msg.qos, msg.retain)
