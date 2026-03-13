"""BrokerConfig — Dataclass and parser for mosquitto.conf files."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BrokerConfig:
    """Maps key Mosquitto configuration directives."""

    listener_port: int = 1883
    listener_address: str = "0.0.0.0"
    allow_anonymous: bool = False
    password_file: str = "/etc/mosquitto/passwd"
    log_dest: str = "file /var/log/mosquitto/mosquitto.log"
    log_type: str = "all"
    persistence: bool = True
    persistence_location: str = "/var/lib/mosquitto/"
    max_connections: int = -1
    extra_lines: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Parser
    # ------------------------------------------------------------------

    @classmethod
    def from_conf(cls, text: str) -> BrokerConfig:
        cfg = cls()
        cfg.extra_lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                cfg.extra_lines.append(raw_line)
                continue
            parts = line.split(None, 1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else ""

            if key == "listener":
                tokens = value.split()
                cfg.listener_port = int(tokens[0])
                if len(tokens) > 1:
                    cfg.listener_address = tokens[1]
            elif key == "allow_anonymous":
                cfg.allow_anonymous = value.lower() == "true"
            elif key == "password_file":
                cfg.password_file = value
            elif key == "log_dest":
                cfg.log_dest = value
            elif key == "log_type":
                cfg.log_type = value
            elif key == "persistence":
                cfg.persistence = value.lower() == "true"
            elif key == "persistence_location":
                cfg.persistence_location = value
            elif key == "max_connections":
                cfg.max_connections = int(value)
            else:
                cfg.extra_lines.append(raw_line)
        return cfg

    # ------------------------------------------------------------------
    # Serializer
    # ------------------------------------------------------------------

    def to_conf(self) -> str:
        lines = [
            "# MQTT-server managed configuration",
            "",
            f"listener {self.listener_port} {self.listener_address}",
            "",
            f"allow_anonymous {'true' if self.allow_anonymous else 'false'}",
            f"password_file {self.password_file}",
            "",
            f"log_dest {self.log_dest}",
            f"log_type {self.log_type}",
            "",
            f"persistence {'true' if self.persistence else 'false'}",
            f"persistence_location {self.persistence_location}",
            "",
            f"max_connections {self.max_connections}",
        ]
        # Append any extra/unknown directives
        extras = [l for l in self.extra_lines if l.strip() and not l.strip().startswith("#")]
        if extras:
            lines.append("")
            lines.extend(extras)
        lines.append("")
        return "\n".join(lines)
