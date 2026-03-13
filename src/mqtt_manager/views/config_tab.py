"""Config Tab — Edit Mosquitto configuration remotely."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from mqtt_manager.models.broker_config import BrokerConfig
from mqtt_manager.services.ssh_manager import SSHManager


class ConfigTab(QWidget):
    """Tab for editing and deploying Mosquitto broker configuration."""

    def __init__(self, ssh: SSHManager, parent=None):
        super().__init__(parent)
        self._ssh = ssh
        self._config: BrokerConfig | None = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Network group ---
        net_group = QGroupBox("Network")
        net_form = QFormLayout(net_group)
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(1883)
        self._address = QLineEdit("0.0.0.0")
        self._max_conn = QSpinBox()
        self._max_conn.setRange(-1, 100000)
        self._max_conn.setValue(-1)
        self._max_conn.setSpecialValueText("Unlimited")
        net_form.addRow("Listener Port:", self._port)
        net_form.addRow("Bind Address:", self._address)
        net_form.addRow("Max Connections:", self._max_conn)
        layout.addWidget(net_group)

        # --- Auth group ---
        auth_group = QGroupBox("Authentication")
        auth_form = QFormLayout(auth_group)
        self._allow_anon = QCheckBox("Allow Anonymous")
        self._passwd_file = QLineEdit("/etc/mosquitto/passwd")
        auth_form.addRow(self._allow_anon)
        auth_form.addRow("Password File:", self._passwd_file)
        layout.addWidget(auth_group)

        # --- Logging group ---
        log_group = QGroupBox("Logging")
        log_form = QFormLayout(log_group)
        self._log_dest = QLineEdit("file /var/log/mosquitto/mosquitto.log")
        self._log_type = QLineEdit("all")
        log_form.addRow("Log Destination:", self._log_dest)
        log_form.addRow("Log Type:", self._log_type)
        layout.addWidget(log_group)

        # --- Persistence group ---
        persist_group = QGroupBox("Persistence")
        persist_form = QFormLayout(persist_group)
        self._persistence = QCheckBox("Enable Persistence")
        self._persistence.setChecked(True)
        self._persist_loc = QLineEdit("/var/lib/mosquitto/")
        persist_form.addRow(self._persistence)
        persist_form.addRow("Location:", self._persist_loc)
        layout.addWidget(persist_group)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self._load_btn = QPushButton("Load from Pi")
        self._save_btn = QPushButton("Save && Restart")
        btn_row.addWidget(self._load_btn)
        btn_row.addWidget(self._save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)
        layout.addStretch()

    def _connect_signals(self):
        self._load_btn.clicked.connect(self._load_config)
        self._save_btn.clicked.connect(self._save_config)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _load_config(self):
        if not self._ssh.is_connected:
            self._status_label.setText("SSH not connected")
            return
        try:
            text = self._ssh.read_config()
            self._config = BrokerConfig.from_conf(text)
            self._apply_to_form(self._config)
            self._status_label.setText("Configuration loaded.")
        except Exception as exc:
            self._status_label.setText(f"Error: {exc}")

    def _save_config(self):
        if not self._ssh.is_connected:
            self._status_label.setText("SSH not connected")
            return
        cfg = self._form_to_config()
        try:
            self._ssh.write_config(cfg.to_conf())
            self._ssh.restart_service()
            self._status_label.setText("Configuration saved and Mosquitto restarted.")
        except Exception as exc:
            QMessageBox.warning(self, "Save Error", str(exc))
            self._status_label.setText(f"Error: {exc}")

    # ------------------------------------------------------------------
    # Form ↔ Config
    # ------------------------------------------------------------------

    def _apply_to_form(self, cfg: BrokerConfig):
        self._port.setValue(cfg.listener_port)
        self._address.setText(cfg.listener_address)
        self._max_conn.setValue(cfg.max_connections)
        self._allow_anon.setChecked(cfg.allow_anonymous)
        self._passwd_file.setText(cfg.password_file)
        self._log_dest.setText(cfg.log_dest)
        self._log_type.setText(cfg.log_type)
        self._persistence.setChecked(cfg.persistence)
        self._persist_loc.setText(cfg.persistence_location)

    def _form_to_config(self) -> BrokerConfig:
        cfg = self._config or BrokerConfig()
        cfg.listener_port = self._port.value()
        cfg.listener_address = self._address.text()
        cfg.max_connections = self._max_conn.value()
        cfg.allow_anonymous = self._allow_anon.isChecked()
        cfg.password_file = self._passwd_file.text()
        cfg.log_dest = self._log_dest.text()
        cfg.log_type = self._log_type.text()
        cfg.persistence = self._persistence.isChecked()
        cfg.persistence_location = self._persist_loc.text()
        return cfg

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def on_ssh_connected(self):
        self._load_config()
