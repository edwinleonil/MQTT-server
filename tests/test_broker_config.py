"""Tests for BrokerConfig parsing and serialization."""

from mqtt_manager.models.broker_config import BrokerConfig

SAMPLE_CONF = """\
# MQTT-server managed configuration

listener 1883 0.0.0.0

allow_anonymous false
password_file /etc/mosquitto/passwd

log_dest file /var/log/mosquitto/mosquitto.log
log_type all

persistence true
persistence_location /var/lib/mosquitto/

max_connections -1
"""


def test_parse_defaults():
    cfg = BrokerConfig.from_conf(SAMPLE_CONF)
    assert cfg.listener_port == 1883
    assert cfg.listener_address == "0.0.0.0"
    assert cfg.allow_anonymous is False
    assert cfg.password_file == "/etc/mosquitto/passwd"
    assert cfg.persistence is True
    assert cfg.max_connections == -1


def test_roundtrip():
    cfg = BrokerConfig.from_conf(SAMPLE_CONF)
    text = cfg.to_conf()
    cfg2 = BrokerConfig.from_conf(text)
    assert cfg2.listener_port == cfg.listener_port
    assert cfg2.listener_address == cfg.listener_address
    assert cfg2.allow_anonymous == cfg.allow_anonymous
    assert cfg2.password_file == cfg.password_file
    assert cfg2.persistence == cfg.persistence
    assert cfg2.max_connections == cfg.max_connections


def test_custom_values():
    cfg = BrokerConfig(
        listener_port=8883,
        listener_address="127.0.0.1",
        allow_anonymous=True,
        max_connections=100,
    )
    text = cfg.to_conf()
    assert "listener 8883 127.0.0.1" in text
    assert "allow_anonymous true" in text
    assert "max_connections 100" in text


def test_parse_minimal():
    cfg = BrokerConfig.from_conf("listener 9001\nallow_anonymous true\n")
    assert cfg.listener_port == 9001
    assert cfg.allow_anonymous is True
