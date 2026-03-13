"""ConnectionProfile — Dataclass for SSH + MQTT connection settings."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings


@dataclass
class ConnectionProfile:
    """Stores SSH and MQTT connection parameters."""

    name: str = "Default"

    # SSH
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_username: str = "pi"
    ssh_auth_method: str = "password"  # "password" | "key"
    ssh_password: str = ""
    ssh_key_path: str = ""

    # MQTT
    mqtt_host: str = ""  # defaults to ssh_host if empty
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""

    @property
    def effective_mqtt_host(self) -> str:
        return self.mqtt_host or self.ssh_host

    # ------------------------------------------------------------------
    # QSettings persistence
    # ------------------------------------------------------------------

    def save(self, settings: QSettings):
        settings.beginGroup(f"profiles/{self.name}")
        settings.setValue("ssh_host", self.ssh_host)
        settings.setValue("ssh_port", self.ssh_port)
        settings.setValue("ssh_username", self.ssh_username)
        settings.setValue("ssh_auth_method", self.ssh_auth_method)
        settings.setValue("ssh_key_path", self.ssh_key_path)
        settings.setValue("mqtt_host", self.mqtt_host)
        settings.setValue("mqtt_port", self.mqtt_port)
        settings.setValue("mqtt_username", self.mqtt_username)
        # Note: passwords are NOT persisted for security
        settings.endGroup()

    @classmethod
    def load(cls, settings: QSettings, name: str) -> ConnectionProfile:
        profile = cls(name=name)
        settings.beginGroup(f"profiles/{name}")
        profile.ssh_host = settings.value("ssh_host", "")
        profile.ssh_port = int(settings.value("ssh_port", 22))
        profile.ssh_username = settings.value("ssh_username", "pi")
        profile.ssh_auth_method = settings.value("ssh_auth_method", "password")
        profile.ssh_key_path = settings.value("ssh_key_path", "")
        profile.mqtt_host = settings.value("mqtt_host", "")
        profile.mqtt_port = int(settings.value("mqtt_port", 1883))
        profile.mqtt_username = settings.value("mqtt_username", "")
        settings.endGroup()
        return profile

    @classmethod
    def list_profiles(cls, settings: QSettings) -> list[str]:
        settings.beginGroup("profiles")
        names = settings.childGroups()
        settings.endGroup()
        return names

    @classmethod
    def delete_profile(cls, settings: QSettings, name: str):
        settings.beginGroup(f"profiles/{name}")
        settings.remove("")
        settings.endGroup()
