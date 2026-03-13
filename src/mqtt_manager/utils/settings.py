"""Settings — QSettings wrapper for persistent app configuration."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMainWindow


def app_settings() -> QSettings:
    """Return the application QSettings instance."""
    return QSettings("MQTT-server", "MQTTManager")


def save_window_geometry(window: QMainWindow, settings: QSettings):
    settings.setValue("window/geometry", window.saveGeometry())
    settings.setValue("window/state", window.saveState())


def restore_window_geometry(window: QMainWindow, settings: QSettings):
    geometry = settings.value("window/geometry")
    if geometry:
        window.restoreGeometry(geometry)
    state = settings.value("window/state")
    if state:
        window.restoreState(state)
