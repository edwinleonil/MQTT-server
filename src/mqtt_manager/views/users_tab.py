"""Users Tab — Manage Mosquitto MQTT users via mosquitto_passwd."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mqtt_manager.services.ssh_manager import SSHManager


class AddUserDialog(QDialog):
    """Simple dialog to enter a username and password."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add MQTT User")
        layout = QFormLayout(self)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)
        layout.addRow("Confirm:", self.confirm_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self):
        if not self.username_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Username cannot be empty.")
            return
        if self.password_edit.text() != self.confirm_edit.text():
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            return
        if len(self.password_edit.text()) < 1:
            QMessageBox.warning(self, "Validation", "Password cannot be empty.")
            return
        self.accept()


class UsersTab(QWidget):
    """Tab for managing Mosquitto broker users."""

    def __init__(self, ssh: SSHManager, parent=None):
        super().__init__(parent)
        self._ssh = ssh
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("MQTT Users (mosquitto_passwd):"))

        self._user_list = QListWidget()
        layout.addWidget(self._user_list)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add User")
        self._remove_btn = QPushButton("Remove User")
        self._refresh_btn = QPushButton("Refresh")
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def _connect_signals(self):
        self._add_btn.clicked.connect(self._add_user)
        self._remove_btn.clicked.connect(self._remove_user)
        self._refresh_btn.clicked.connect(self._refresh_users)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _refresh_users(self):
        if not self._ssh.is_connected:
            self._status_label.setText("SSH not connected")
            return
        try:
            users = self._ssh.list_users()
            self._user_list.clear()
            self._user_list.addItems(users)
            self._status_label.setText(f"{len(users)} user(s) found.")
        except Exception as exc:
            self._status_label.setText(f"Error: {exc}")

    def _add_user(self):
        if not self._ssh.is_connected:
            self._status_label.setText("SSH not connected")
            return
        dlg = AddUserDialog(self)
        if dlg.exec() == QDialog.Accepted:
            username = dlg.username_edit.text().strip()
            password = dlg.password_edit.text()
            try:
                _, stderr, code = self._ssh.add_user(username, password)
                if code == 0:
                    self._status_label.setText(f"User '{username}' added.")
                    self._refresh_users()
                else:
                    self._status_label.setText(f"Error: {stderr}")
            except Exception as exc:
                self._status_label.setText(f"Error: {exc}")

    def _remove_user(self):
        if not self._ssh.is_connected:
            self._status_label.setText("SSH not connected")
            return
        item = self._user_list.currentItem()
        if not item:
            return
        username = item.text()
        reply = QMessageBox.question(
            self, "Remove User", f"Remove user '{username}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                _, stderr, code = self._ssh.remove_user(username)
                if code == 0:
                    self._status_label.setText(f"User '{username}' removed.")
                    self._refresh_users()
                else:
                    self._status_label.setText(f"Error: {stderr}")
            except Exception as exc:
                self._status_label.setText(f"Error: {exc}")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def on_ssh_connected(self):
        self._refresh_users()

    def on_ssh_disconnected(self):
        self._user_list.clear()
        self._status_label.setText("")
