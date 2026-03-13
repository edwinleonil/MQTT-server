"""Server Tab — Start/Stop/Restart Mosquitto and view logs."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from mqtt_manager.services.ssh_manager import SSHManager


class ServerTab(QWidget):
    """Tab for controlling the Mosquitto service and viewing broker logs."""

    def __init__(self, ssh: SSHManager, parent=None):
        super().__init__(parent)
        self._ssh = ssh
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Setup info banner ---
        self._info_banner = QLabel(
            "ℹ️  If Mosquitto is not yet installed on your Pi, run:  "
            "<b>sudo bash scripts/setup_pi.sh</b>  "
            "(found in this project's scripts/ folder)"
        )
        self._info_banner.setWordWrap(True)
        self._info_banner.setStyleSheet(
            "background-color: #e7f3fe; border: 1px solid #b6d4fe; "
            "border-radius: 4px; padding: 8px; color: #084298;"
        )
        layout.addWidget(self._info_banner)

        # --- Service controls ---
        ctrl_row = QHBoxLayout()
        self._start_btn = QPushButton("Start")
        self._stop_btn = QPushButton("Stop")
        self._restart_btn = QPushButton("Restart")
        self._refresh_status_btn = QPushButton("Refresh Status")
        ctrl_row.addWidget(self._start_btn)
        ctrl_row.addWidget(self._stop_btn)
        ctrl_row.addWidget(self._restart_btn)
        ctrl_row.addWidget(self._refresh_status_btn)
        ctrl_row.addStretch()
        layout.addLayout(ctrl_row)

        # --- Status ---
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Service Status:"))
        self._status_label = QLabel("Unknown")
        self._status_label.setStyleSheet("font-weight: bold;")
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        # --- Log viewer ---
        layout.addWidget(QLabel("Mosquitto Log:"))
        self._log_viewer = QPlainTextEdit()
        self._log_viewer.setReadOnly(True)
        self._log_viewer.setMaximumBlockCount(2000)
        layout.addWidget(self._log_viewer)

        # --- Log controls ---
        log_ctrl = QHBoxLayout()
        log_ctrl.addWidget(QLabel("Lines:"))
        self._log_lines = QSpinBox()
        self._log_lines.setRange(10, 5000)
        self._log_lines.setValue(100)
        log_ctrl.addWidget(self._log_lines)
        log_ctrl.addWidget(QLabel("Auto-refresh (s):"))
        self._refresh_interval = QSpinBox()
        self._refresh_interval.setRange(0, 300)
        self._refresh_interval.setValue(5)
        self._refresh_interval.setSpecialValueText("Off")
        log_ctrl.addWidget(self._refresh_interval)
        self._refresh_log_btn = QPushButton("Refresh Log")
        log_ctrl.addWidget(self._refresh_log_btn)
        self._clear_log_btn = QPushButton("Clear")
        log_ctrl.addWidget(self._clear_log_btn)
        log_ctrl.addStretch()
        layout.addLayout(log_ctrl)

        # --- Auto-refresh timer ---
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_log)
        self._update_timer()

    def _connect_signals(self):
        self._start_btn.clicked.connect(self._start)
        self._stop_btn.clicked.connect(self._stop)
        self._restart_btn.clicked.connect(self._restart)
        self._refresh_status_btn.clicked.connect(self._refresh_status)
        self._refresh_log_btn.clicked.connect(self._refresh_log)
        self._clear_log_btn.clicked.connect(self._log_viewer.clear)
        self._refresh_interval.valueChanged.connect(self._update_timer)

    # ------------------------------------------------------------------
    # Service actions
    # ------------------------------------------------------------------

    def _refresh_status(self):
        if not self._ssh.is_connected:
            self._status_label.setText("SSH not connected")
            return
        try:
            status = self._ssh.get_service_status()
            self._status_label.setText(status)
            color = {"active": "green", "inactive": "gray", "failed": "red"}.get(status, "orange")
            self._status_label.setStyleSheet(f"font-weight: bold; color: {color};")
        except Exception as exc:
            self._status_label.setText(f"Error: {exc}")

    def _start(self):
        if not self._ssh.is_connected:
            return
        self._ssh.start_service()
        self._refresh_status()

    def _stop(self):
        if not self._ssh.is_connected:
            return
        self._ssh.stop_service()
        self._refresh_status()

    def _restart(self):
        if not self._ssh.is_connected:
            return
        self._ssh.restart_service()
        self._refresh_status()

    # ------------------------------------------------------------------
    # Log
    # ------------------------------------------------------------------

    def _refresh_log(self):
        if not self._ssh.is_connected:
            return
        try:
            log = self._ssh.get_log(lines=self._log_lines.value())
            self._log_viewer.setPlainText(log)
            # Scroll to bottom
            scrollbar = self._log_viewer.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as exc:
            self._log_viewer.setPlainText(f"Error reading log: {exc}")

    def _update_timer(self):
        interval = self._refresh_interval.value()
        if interval > 0:
            self._timer.start(interval * 1000)
        else:
            self._timer.stop()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def on_ssh_connected(self):
        self._refresh_status()
        self._refresh_log()

    def on_ssh_disconnected(self):
        self._status_label.setText("SSH not connected")
        self._status_label.setStyleSheet("font-weight: bold; color: gray;")
