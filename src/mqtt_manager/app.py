"""Main application window — ties together all tabs and services."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QToolBar

from mqtt_manager.services.mqtt_service import MQTTService
from mqtt_manager.services.ssh_manager import SSHManager
from mqtt_manager.utils.settings import app_settings, restore_window_geometry, save_window_geometry
from mqtt_manager.views.config_tab import ConfigTab
from mqtt_manager.views.connect_tab import ConnectTab
from mqtt_manager.views.monitor_tab import MonitorTab
from mqtt_manager.views.server_tab import ServerTab
from mqtt_manager.views.topics_tab import TopicsTab
from mqtt_manager.views.users_tab import UsersTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MQTT Manager")
        self.setMinimumSize(900, 600)

        # --- Services ---
        self._settings = app_settings()
        self._ssh = SSHManager(self)
        self._mqtt = MQTTService(self)

        # --- Tab widget ---
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        # --- Create tabs ---
        self._connect_tab = ConnectTab(self._ssh, self._mqtt, self._settings)
        self._server_tab = ServerTab(self._ssh)
        self._config_tab = ConfigTab(self._ssh)
        self._users_tab = UsersTab(self._ssh)
        self._topics_tab = TopicsTab()
        self._monitor_tab = MonitorTab(self._mqtt)

        self._tabs.addTab(self._connect_tab, "Connect")
        self._tabs.addTab(self._server_tab, "Server")
        self._tabs.addTab(self._config_tab, "Config")
        self._tabs.addTab(self._users_tab, "Users")
        self._tabs.addTab(self._topics_tab, "Topics")
        self._tabs.addTab(self._monitor_tab, "Monitor")

        # --- Toolbar with status indicator ---
        toolbar = QToolBar("Status")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        self._ssh_indicator = QLabel(" SSH: ")
        self._mqtt_indicator = QLabel(" MQTT: ")
        self._ssh_status = QLabel("Disconnected")
        self._mqtt_status = QLabel("Disconnected")
        toolbar.addWidget(self._ssh_indicator)
        toolbar.addWidget(self._ssh_status)
        toolbar.addSeparator()
        toolbar.addWidget(self._mqtt_indicator)
        toolbar.addWidget(self._mqtt_status)

        # --- Initial state: disable tabs that need connections ---
        self._set_ssh_tabs_enabled(False)

        # --- Wire signals ---
        self._connect_tab.ssh_state_changed.connect(self._on_ssh_state)
        self._connect_tab.mqtt_state_changed.connect(self._on_mqtt_state)

        # --- Load default topics ---
        default_topics = Path(__file__).resolve().parent.parent.parent / "config" / "topics.yaml"
        self._topics_tab.load_default_topics(default_topics)

        # --- Restore window geometry ---
        restore_window_geometry(self, self._settings)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _set_ssh_tabs_enabled(self, enabled: bool):
        for i, tab in enumerate(
            [self._connect_tab, self._server_tab, self._config_tab, self._users_tab, self._topics_tab, self._monitor_tab]
        ):
            if tab in (self._connect_tab, self._topics_tab):
                continue  # Always enabled
            if tab is self._monitor_tab:
                continue  # Controlled by MQTT state
            self._tabs.setTabEnabled(i, enabled)

    def _set_mqtt_tabs_enabled(self, enabled: bool):
        pass  # Monitor tab is always accessible

    def _on_ssh_state(self, connected: bool):
        self._set_ssh_tabs_enabled(connected)
        if connected:
            self._ssh_status.setText("Connected")
            self._ssh_status.setStyleSheet("color: green; font-weight: bold;")
            self._server_tab.on_ssh_connected()
            self._config_tab.on_ssh_connected()
            self._users_tab.on_ssh_connected()
        else:
            self._ssh_status.setText("Disconnected")
            self._ssh_status.setStyleSheet("color: red;")
            self._server_tab.on_ssh_disconnected()
            self._users_tab.on_ssh_disconnected()
            self._set_mqtt_tabs_enabled(False)
            self._mqtt_status.setText("Disconnected")
            self._mqtt_status.setStyleSheet("color: red;")

    def _on_mqtt_state(self, connected: bool):
        self._set_mqtt_tabs_enabled(connected)
        if connected:
            self._mqtt_status.setText("Connected")
            self._mqtt_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self._mqtt_status.setText("Disconnected")
            self._mqtt_status.setStyleSheet("color: red;")
            self._monitor_tab.on_mqtt_disconnected()

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        save_window_geometry(self, self._settings)
        self._mqtt.disconnect()
        self._ssh.disconnect()
        super().closeEvent(event)
