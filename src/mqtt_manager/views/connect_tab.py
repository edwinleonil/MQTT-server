"""Connect Tab — SSH and MQTT connection management UI."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QComboBox,
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

from mqtt_manager.models.connection import ConnectionProfile
from mqtt_manager.services.mqtt_service import MQTTService
from mqtt_manager.services.ssh_manager import SSHManager


class ConnectTab(QWidget):
    """Tab for configuring and establishing SSH + MQTT connections."""

    ssh_state_changed = Signal(bool)  # True = connected
    mqtt_state_changed = Signal(bool)

    def __init__(self, ssh: SSHManager, mqtt_svc: MQTTService, settings: QSettings, parent=None):
        super().__init__(parent)
        self._ssh = ssh
        self._mqtt = mqtt_svc
        self._settings = settings
        self._build_ui()
        self._connect_signals()
        self._load_profiles()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Profile selector ---
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Profile:"))
        self._profile_combo = QComboBox()
        self._profile_combo.setEditable(True)
        profile_row.addWidget(self._profile_combo, 1)
        self._save_btn = QPushButton("Save")
        self._delete_btn = QPushButton("Delete")
        profile_row.addWidget(self._save_btn)
        profile_row.addWidget(self._delete_btn)
        layout.addLayout(profile_row)

        # --- SSH group ---
        ssh_group = QGroupBox("SSH Connection")
        ssh_form = QFormLayout(ssh_group)
        self._ssh_host = QLineEdit()
        self._ssh_host.setPlaceholderText("e.g. 192.168.1.100")
        self._ssh_port = QSpinBox()
        self._ssh_port.setRange(1, 65535)
        self._ssh_port.setValue(22)
        self._ssh_user = QLineEdit("pi")
        self._ssh_auth = QComboBox()
        self._ssh_auth.addItems(["Password", "SSH Key"])
        self._ssh_password = QLineEdit()
        self._ssh_password.setEchoMode(QLineEdit.Password)
        self._ssh_key_path = QLineEdit()
        self._ssh_key_path.setPlaceholderText("/home/user/.ssh/id_rsa")
        ssh_form.addRow("Host:", self._ssh_host)
        ssh_form.addRow("Port:", self._ssh_port)
        ssh_form.addRow("Username:", self._ssh_user)
        ssh_form.addRow("Auth Method:", self._ssh_auth)
        ssh_form.addRow("Password:", self._ssh_password)
        ssh_form.addRow("Key Path:", self._ssh_key_path)
        layout.addWidget(ssh_group)

        # --- MQTT group ---
        mqtt_group = QGroupBox("MQTT Connection")
        mqtt_form = QFormLayout(mqtt_group)
        self._mqtt_host = QLineEdit()
        self._mqtt_host.setPlaceholderText("Leave empty to use SSH host")
        self._mqtt_port = QSpinBox()
        self._mqtt_port.setRange(1, 65535)
        self._mqtt_port.setValue(1883)
        self._mqtt_user = QLineEdit()
        self._mqtt_password = QLineEdit()
        self._mqtt_password.setEchoMode(QLineEdit.Password)
        mqtt_form.addRow("Host:", self._mqtt_host)
        mqtt_form.addRow("Port:", self._mqtt_port)
        mqtt_form.addRow("Username:", self._mqtt_user)
        mqtt_form.addRow("Password:", self._mqtt_password)
        layout.addWidget(mqtt_group)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self._ssh_connect_btn = QPushButton("Connect SSH")
        self._ssh_disconnect_btn = QPushButton("Disconnect SSH")
        self._ssh_disconnect_btn.setEnabled(False)
        self._mqtt_connect_btn = QPushButton("Connect MQTT")
        self._mqtt_connect_btn.setEnabled(False)
        self._mqtt_disconnect_btn = QPushButton("Disconnect MQTT")
        self._mqtt_disconnect_btn.setEnabled(False)
        btn_row.addWidget(self._ssh_connect_btn)
        btn_row.addWidget(self._ssh_disconnect_btn)
        btn_row.addWidget(self._mqtt_connect_btn)
        btn_row.addWidget(self._mqtt_disconnect_btn)
        layout.addLayout(btn_row)

        # --- Status ---
        self._status_label = QLabel("Disconnected")
        layout.addWidget(self._status_label)

        layout.addStretch()
        self._update_auth_fields()

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self._ssh_auth.currentIndexChanged.connect(self._update_auth_fields)
        self._ssh_connect_btn.clicked.connect(self._on_ssh_connect)
        self._ssh_disconnect_btn.clicked.connect(self._on_ssh_disconnect)
        self._mqtt_connect_btn.clicked.connect(self._on_mqtt_connect)
        self._mqtt_disconnect_btn.clicked.connect(self._on_mqtt_disconnect)
        self._save_btn.clicked.connect(self._on_save_profile)
        self._delete_btn.clicked.connect(self._on_delete_profile)
        self._profile_combo.currentTextChanged.connect(self._on_profile_selected)

        self._ssh.connected.connect(self._on_ssh_connected)
        self._ssh.disconnected.connect(self._on_ssh_disconnected)
        self._ssh.connection_error.connect(self._on_ssh_error)
        self._mqtt.connected.connect(self._on_mqtt_connected)
        self._mqtt.disconnected.connect(self._on_mqtt_disconnected)
        self._mqtt.error.connect(self._on_mqtt_error)

    def _update_auth_fields(self):
        is_password = self._ssh_auth.currentIndex() == 0
        self._ssh_password.setVisible(is_password)
        self._ssh_key_path.setVisible(not is_password)

    # ------------------------------------------------------------------
    # SSH actions
    # ------------------------------------------------------------------

    def _on_ssh_connect(self):
        self._status_label.setText("Connecting SSH...")
        self._ssh.connect(
            host=self._ssh_host.text(),
            port=self._ssh_port.value(),
            username=self._ssh_user.text(),
            password=self._ssh_password.text() if self._ssh_auth.currentIndex() == 0 else None,
            key_path=self._ssh_key_path.text() if self._ssh_auth.currentIndex() == 1 else None,
        )

    def _on_ssh_disconnect(self):
        self._mqtt.disconnect()
        self._ssh.disconnect()

    def _on_ssh_connected(self):
        self._status_label.setText("SSH: Connected")
        self._ssh_connect_btn.setEnabled(False)
        self._ssh_disconnect_btn.setEnabled(True)
        self._mqtt_connect_btn.setEnabled(True)
        self.ssh_state_changed.emit(True)

    def _on_ssh_disconnected(self):
        self._status_label.setText("Disconnected")
        self._ssh_connect_btn.setEnabled(True)
        self._ssh_disconnect_btn.setEnabled(False)
        self._mqtt_connect_btn.setEnabled(False)
        self._mqtt_disconnect_btn.setEnabled(False)
        self.ssh_state_changed.emit(False)
        self.mqtt_state_changed.emit(False)

    def _on_ssh_error(self, msg: str):
        self._status_label.setText(f"SSH Error: {msg}")
        QMessageBox.warning(self, "SSH Connection Error", msg)

    # ------------------------------------------------------------------
    # MQTT actions
    # ------------------------------------------------------------------

    def _on_mqtt_connect(self):
        host = self._mqtt_host.text() or self._ssh_host.text()
        self._status_label.setText("Connecting MQTT...")
        self._mqtt.connect(
            host=host,
            port=self._mqtt_port.value(),
            username=self._mqtt_user.text() or None,
            password=self._mqtt_password.text() or None,
        )

    def _on_mqtt_disconnect(self):
        self._mqtt.disconnect()

    def _on_mqtt_connected(self):
        self._status_label.setText("SSH: Connected | MQTT: Connected")
        self._mqtt_connect_btn.setEnabled(False)
        self._mqtt_disconnect_btn.setEnabled(True)
        self.mqtt_state_changed.emit(True)

    def _on_mqtt_disconnected(self):
        ssh_state = "Connected" if self._ssh.is_connected else "Disconnected"
        self._status_label.setText(f"SSH: {ssh_state} | MQTT: Disconnected")
        self._mqtt_connect_btn.setEnabled(self._ssh.is_connected)
        self._mqtt_disconnect_btn.setEnabled(False)
        self.mqtt_state_changed.emit(False)

    def _on_mqtt_error(self, msg: str):
        self._status_label.setText(f"MQTT Error: {msg}")
        QMessageBox.warning(self, "MQTT Connection Error", msg)

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def _current_profile(self) -> ConnectionProfile:
        return ConnectionProfile(
            name=self._profile_combo.currentText() or "Default",
            ssh_host=self._ssh_host.text(),
            ssh_port=self._ssh_port.value(),
            ssh_username=self._ssh_user.text(),
            ssh_auth_method="password" if self._ssh_auth.currentIndex() == 0 else "key",
            ssh_key_path=self._ssh_key_path.text(),
            mqtt_host=self._mqtt_host.text(),
            mqtt_port=self._mqtt_port.value(),
            mqtt_username=self._mqtt_user.text(),
        )

    def _apply_profile(self, profile: ConnectionProfile):
        self._ssh_host.setText(profile.ssh_host)
        self._ssh_port.setValue(profile.ssh_port)
        self._ssh_user.setText(profile.ssh_username)
        self._ssh_auth.setCurrentIndex(0 if profile.ssh_auth_method == "password" else 1)
        self._ssh_key_path.setText(profile.ssh_key_path)
        self._mqtt_host.setText(profile.mqtt_host)
        self._mqtt_port.setValue(profile.mqtt_port)
        self._mqtt_user.setText(profile.mqtt_username)

    def _load_profiles(self):
        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        for name in ConnectionProfile.list_profiles(self._settings):
            self._profile_combo.addItem(name)
        self._profile_combo.blockSignals(False)
        if self._profile_combo.count() > 0:
            self._on_profile_selected(self._profile_combo.currentText())

    def _on_profile_selected(self, name: str):
        if not name:
            return
        names = ConnectionProfile.list_profiles(self._settings)
        if name in names:
            profile = ConnectionProfile.load(self._settings, name)
            self._apply_profile(profile)

    def _on_save_profile(self):
        profile = self._current_profile()
        profile.save(self._settings)
        self._load_profiles()
        self._profile_combo.setCurrentText(profile.name)

    def _on_delete_profile(self):
        name = self._profile_combo.currentText()
        if name:
            ConnectionProfile.delete_profile(self._settings, name)
            self._load_profiles()
