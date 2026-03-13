"""Monitor Tab — Subscribe to topics, view live messages, publish test messages."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from mqtt_manager.services.mqtt_service import MQTTService


class MonitorTab(QWidget):
    """Tab for real-time MQTT message monitoring and publishing."""

    def __init__(self, mqtt_svc: MQTTService, parent=None):
        super().__init__(parent)
        self._mqtt = mqtt_svc
        self._subscriptions: list[str] = []
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        # ---- Top: Subscribe + Message Table ----
        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Subscribe row
        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Topic Filter:"))
        self._sub_topic = QLineEdit("#")
        self._sub_topic.setPlaceholderText("e.g. home/+/temperature or #")
        sub_row.addWidget(self._sub_topic, 1)
        self._sub_btn = QPushButton("Subscribe")
        self._unsub_btn = QPushButton("Unsubscribe")
        sub_row.addWidget(self._sub_btn)
        sub_row.addWidget(self._unsub_btn)
        top_layout.addLayout(sub_row)

        # Active subscriptions
        self._sub_label = QLabel("Subscriptions: (none)")
        top_layout.addWidget(self._sub_label)

        # Message table
        self._msg_model = QStandardItemModel()
        self._msg_model.setHorizontalHeaderLabels(
            ["Timestamp", "Topic", "Payload", "QoS", "Retain"]
        )
        self._msg_table = QTableView()
        self._msg_table.setModel(self._msg_model)
        self._msg_table.setAlternatingRowColors(True)
        self._msg_table.setSelectionBehavior(QTableView.SelectRows)
        self._msg_table.horizontalHeader().setStretchLastSection(True)
        self._msg_table.setColumnWidth(0, 160)
        self._msg_table.setColumnWidth(1, 200)
        top_layout.addWidget(self._msg_table)

        # Clear button
        clear_row = QHBoxLayout()
        self._clear_btn = QPushButton("Clear Messages")
        self._auto_scroll = QCheckBox("Auto-scroll")
        self._auto_scroll.setChecked(True)
        clear_row.addWidget(self._clear_btn)
        clear_row.addWidget(self._auto_scroll)
        clear_row.addStretch()
        top_layout.addLayout(clear_row)

        splitter.addWidget(top)

        # ---- Bottom: Publish Panel ----
        publish_group = QGroupBox("Publish")
        pub_layout = QVBoxLayout(publish_group)

        pub_row1 = QHBoxLayout()
        pub_row1.addWidget(QLabel("Topic:"))
        self._pub_topic = QLineEdit()
        self._pub_topic.setPlaceholderText("e.g. home/living_room/temperature")
        pub_row1.addWidget(self._pub_topic, 1)
        pub_layout.addLayout(pub_row1)

        pub_row2 = QHBoxLayout()
        pub_row2.addWidget(QLabel("QoS:"))
        self._pub_qos = QComboBox()
        self._pub_qos.addItems(["0", "1", "2"])
        pub_row2.addWidget(self._pub_qos)
        self._pub_retain = QCheckBox("Retain")
        pub_row2.addWidget(self._pub_retain)
        self._pub_btn = QPushButton("Publish")
        pub_row2.addWidget(self._pub_btn)
        pub_row2.addStretch()
        pub_layout.addLayout(pub_row2)

        pub_layout.addWidget(QLabel("Payload:"))
        self._pub_payload = QPlainTextEdit()
        self._pub_payload.setMaximumHeight(100)
        self._pub_payload.setPlaceholderText('{"value": 22.5, "unit": "C"}')
        pub_layout.addWidget(self._pub_payload)

        splitter.addWidget(publish_group)

        layout.addWidget(splitter)

    def _connect_signals(self):
        self._sub_btn.clicked.connect(self._subscribe)
        self._unsub_btn.clicked.connect(self._unsubscribe)
        self._clear_btn.clicked.connect(self._msg_model.removeRows, 0, self._msg_model.rowCount())
        self._clear_btn.clicked.connect(lambda: self._msg_model.setRowCount(0))
        self._pub_btn.clicked.connect(self._publish)
        self._mqtt.message_received.connect(self._on_message)

    # ------------------------------------------------------------------
    # Subscribe / Unsubscribe
    # ------------------------------------------------------------------

    def _subscribe(self):
        topic = self._sub_topic.text().strip()
        if not topic:
            return
        self._mqtt.subscribe(topic)
        if topic not in self._subscriptions:
            self._subscriptions.append(topic)
        self._update_sub_label()

    def _unsubscribe(self):
        topic = self._sub_topic.text().strip()
        if not topic:
            return
        self._mqtt.unsubscribe(topic)
        if topic in self._subscriptions:
            self._subscriptions.remove(topic)
        self._update_sub_label()

    def _update_sub_label(self):
        if self._subscriptions:
            self._sub_label.setText(f"Subscriptions: {', '.join(self._subscriptions)}")
        else:
            self._sub_label.setText("Subscriptions: (none)")

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    def _on_message(self, topic: str, payload: bytes, qos: int, retain: bool):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        try:
            payload_str = payload.decode("utf-8")
        except UnicodeDecodeError:
            payload_str = payload.hex()

        row = [
            QStandardItem(timestamp),
            QStandardItem(topic),
            QStandardItem(payload_str),
            QStandardItem(str(qos)),
            QStandardItem("Yes" if retain else "No"),
        ]
        for item in row:
            item.setEditable(False)
        self._msg_model.appendRow(row)

        if self._auto_scroll.isChecked():
            self._msg_table.scrollToBottom()

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------

    def _publish(self):
        topic = self._pub_topic.text().strip()
        payload = self._pub_payload.toPlainText()
        qos = int(self._pub_qos.currentText())
        retain = self._pub_retain.isChecked()
        if topic:
            self._mqtt.publish(topic, payload, qos, retain)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def on_mqtt_disconnected(self):
        self._subscriptions.clear()
        self._update_sub_label()
