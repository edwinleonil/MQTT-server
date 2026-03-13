# MQTT Manager

A PySide6 desktop application for managing a **Mosquitto MQTT broker** running on a Raspberry Pi. The app connects to the Pi over SSH for server administration, and to the MQTT broker directly for real-time message monitoring and publishing.

## Features

- **SSH remote management** — Start/stop/restart Mosquitto, edit config, manage users — all from your desktop
- **MQTT client** — Subscribe to topics, view live messages, publish test payloads
- **Config editor** — GUI form for `mosquitto.conf` settings (port, auth, persistence, logging)
- **User management** — Add/remove MQTT users via `mosquitto_passwd`
- **Topic browser** — Tree view of your topic hierarchy loaded from YAML
- **Connection profiles** — Save and switch between multiple Pi connections

## Architecture

```
┌──────────────────────┐           ┌──────────────────┐
│  Desktop Machine     │   SSH     │  Raspberry Pi    │
│                      │──(22)───▶ │                  │
│  PySide6 App         │           │  Mosquitto       │
│  ├─ paramiko (SSH)   │  MQTT     │  (systemd)       │
│  └─ paho-mqtt ───────│─(1883)──▶│                  │
└──────────────────────┘           └──────────────────┘
```

## Prerequisites

- **Raspberry Pi**: Raspberry Pi OS with SSH enabled
- **Desktop**: Python 3.10+, [uv](https://docs.astral.sh/uv/) package manager

## Pi Setup

Run the bootstrap script **on the Raspberry Pi** (via SSH or directly):

```bash
sudo bash scripts/setup_pi.sh
```

This will:
1. Install `mosquitto` and `mosquitto-clients`
2. Enable the Mosquitto systemd service
3. Create the password file at `/etc/mosquitto/passwd`
4. Deploy the default configuration
5. Start the broker

Add your first MQTT user:

```bash
sudo mosquitto_passwd -b /etc/mosquitto/passwd myuser mypassword
```

## Desktop Installation

```bash
# Clone the repo
git clone <repo-url> && cd MQTT-server

# Install with uv (creates venv automatically)
uv sync

# Run the application
uv run mqtt-manager
```

Or run as a module:

```bash
uv run python -m mqtt_manager
```

## Usage

1. **Connect tab** — Enter your Pi's SSH host/credentials and MQTT user/password. Save as a profile for quick access.
2. **Server tab** — Start/stop/restart Mosquitto. View the broker log in real time.
3. **Config tab** — Edit broker settings (port, auth, persistence). Click "Save & Restart" to deploy.
4. **Users tab** — Add or remove MQTT users.
5. **Topics tab** — Browse the topic hierarchy from `config/topics.yaml`. Add/remove/rename topics. Export to YAML.
6. **Monitor tab** — Subscribe to topic filters (supports `+` and `#` wildcards). Publish test messages. View live message table.

## Topic Structure

The default topic hierarchy in `config/topics.yaml`:

```
home/{room}/temperature      — Temperature in °C
home/{room}/humidity         — Relative humidity %
home/{room}/light/state      — Light on/off
home/{room}/light/brightness — Brightness 0-100
devices/{device_id}/status   — Online/offline
devices/{device_id}/command  — Commands to device
devices/{device_id}/telemetry — Device metrics
system/broker/status         — Broker health
system/broker/clients        — Client count
```

Names in `{braces}` are dynamic placeholders. The broker does **not** enforce this structure — clients can publish to any topic.

## Running Tests

```bash
uv run pytest
```

## Project Structure

```
MQTT-server/
├── pyproject.toml              # Project metadata & dependencies
├── scripts/setup_pi.sh         # Pi bootstrap installer
├── config/
│   ├── mosquitto.conf.template # Default broker config
│   └── topics.yaml             # Topic hierarchy definition
├── src/mqtt_manager/
│   ├── __main__.py             # Entry point
│   ├── app.py                  # MainWindow (6-tab layout)
│   ├── models/                 # Data models (config, topics, connection)
│   ├── views/                  # UI tabs (connect, server, config, users, topics, monitor)
│   ├── services/               # SSH manager (paramiko) + MQTT client (paho-mqtt)
│   └── utils/                  # QSettings persistence
└── tests/                      # Unit tests
```
