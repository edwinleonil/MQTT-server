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

- **Raspberry Pi**: Raspberry Pi OS (Debian-based) with SSH enabled
- **Desktop**: Python 3.10+, [uv](https://docs.astral.sh/uv/) package manager
- **Network**: The desktop machine must be able to reach the Pi on port 22 (SSH) and port 1883 (MQTT)

## Pi Setup

### 1. Install Mosquitto

Copy or clone this repository to the Pi, then run the bootstrap script:

```bash
sudo bash scripts/setup_pi.sh
```

This will:
1. Install `mosquitto` and `mosquitto-clients` via `apt`
2. Enable the Mosquitto systemd service (auto-starts on boot)
3. Create an empty password file at `/etc/mosquitto/passwd`
4. Deploy the configuration to `/etc/mosquitto/conf.d/mqtt-server.conf`
5. Restart the broker

### 2. Create an MQTT user

Anonymous access is disabled by default. Add at least one user:

```bash
sudo mosquitto_passwd -b /etc/mosquitto/passwd myuser mypassword
```

### 3. Verify the broker is running

```bash
systemctl status mosquitto
```

You should see `active (running)`. Mosquitto is enabled as a systemd service, so it will **start automatically** after a reboot.

### 4. Quick test (optional)

Open two terminals on the Pi:

```bash
# Terminal 1 — subscribe
mosquitto_sub -h localhost -t "test/#" -u myuser -P mypassword

# Terminal 2 — publish
mosquitto_pub -h localhost -t "test/hello" -m "world" -u myuser -P mypassword
```

You should see `world` appear in Terminal 1.

### Configuration notes

The setup script deploys a drop-in config to `/etc/mosquitto/conf.d/mqtt-server.conf`. Debian's base config at `/etc/mosquitto/mosquitto.conf` already provides `log_dest`, `persistence`, and `persistence_location` — the drop-in only adds network, auth, and limit settings to avoid duplicate directive errors.

## Desktop Installation

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### Install and run

```bash
# Clone the repo
git clone <repo-url> && cd MQTT-server

# Install dependencies (creates a .venv automatically)
uv sync

# Run the application
uv run mqtt-manager
```

Or run as a Python module:

```bash
uv run python -m mqtt_manager
```

## Usage

### Tab overview

| Tab | Purpose | Requires |
|-----|---------|----------|
| **Connect** | Enter SSH + MQTT credentials, save connection profiles | — |
| **Server** | Start/stop/restart Mosquitto, view live broker logs | SSH connected |
| **Config** | Edit broker settings (port, auth, limits), deploy with "Save & Restart" | SSH connected |
| **Users** | Add/remove MQTT users via `mosquitto_passwd` | SSH connected |
| **Topics** | Browse/edit the topic hierarchy from YAML, export to file | — |
| **Monitor** | Subscribe to topics, view live messages, publish test payloads | MQTT connected |

### Step-by-step

1. **Connect tab** — Enter your Pi's IP address, SSH username/password (or key path), and MQTT credentials. Click **Connect SSH**, then **Connect MQTT**. Save as a profile for quick reconnection.
2. **Server tab** — Verify Mosquitto is running (green "active" status). Use Start/Stop/Restart buttons. The log viewer auto-refreshes at a configurable interval.
3. **Config tab** — Configuration loads automatically when SSH connects. Edit fields and click **Save & Restart** to push changes to the Pi.
4. **Users tab** — View existing MQTT users. Click **Add User** to create a new one (username + password). Select a user and click **Remove User** to delete.
5. **Topics tab** — The default topic hierarchy loads from `config/topics.yaml`. Add, remove, or rename topics. Click **Export YAML** to save changes.
6. **Monitor tab** — Enter a topic filter (e.g. `home/#` or `+/temperature`) and click **Subscribe**. Messages appear in a live table. Use the publish panel at the bottom to send test messages.

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

Names in `{braces}` are dynamic placeholders — replace them with actual values when publishing (e.g. `home/living_room/temperature`). The broker does **not** enforce this structure — clients can publish to any topic. The Topics tab serves as a reference and autocomplete source.

## Running Tests

```bash
uv run pytest
```

Tests cover:
- **Broker config** — Parsing and round-trip serialization of `mosquitto.conf`
- **Topic tree** — YAML loading, tree operations, export
- **SSH manager** — Mock-based command execution and file operations

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `mosquitto.service` fails to start | Check `sudo journalctl -xeu mosquitto.service` for errors. Common cause: duplicate directives between `/etc/mosquitto/mosquitto.conf` and the drop-in config. Ensure `log_dest`, `persistence`, and `persistence_location` are only set in one place. |
| "SSH not connected" in the app | Verify the Pi's IP is reachable and SSH is enabled (`sudo systemctl enable ssh`). Check username/password or key path. |
| MQTT connection refused | Ensure Mosquitto is running (`systemctl status mosquitto`). Verify port 1883 is not blocked by a firewall (`sudo ufw allow 1883` if using ufw). |
| "command not found: uv" | Run `source $HOME/.local/bin/env` or restart your shell after installing uv. |
| No MQTT messages received | Verify you have subscribed to the correct topic filter. Use `#` to match all topics. Check that the publishing client is using valid credentials. |

## Project Structure

```
MQTT-server/
├── pyproject.toml              # Project metadata & dependencies (uv)
├── scripts/
│   └── setup_pi.sh             # Pi bootstrap: install Mosquitto, enable service, deploy config
├── config/
│   ├── mosquitto.conf.template # Drop-in broker config (network, auth, limits)
│   └── topics.yaml             # Topic hierarchy definition
├── src/mqtt_manager/
│   ├── __init__.py
│   ├── __main__.py             # Entry point (uv run mqtt-manager)
│   ├── app.py                  # MainWindow with 6-tab layout
│   ├── models/
│   │   ├── broker_config.py    # Mosquitto config parser / serializer
│   │   ├── topic_tree.py       # Topic hierarchy tree + Qt model
│   │   └── connection.py       # SSH + MQTT connection profile
│   ├── views/
│   │   ├── connect_tab.py      # SSH & MQTT connection form
│   │   ├── server_tab.py       # Service control & log viewer
│   │   ├── config_tab.py       # Broker config editor
│   │   ├── users_tab.py        # MQTT user management
│   │   ├── topics_tab.py       # Topic hierarchy browser
│   │   └── monitor_tab.py      # Live message monitor & publisher
│   ├── services/
│   │   ├── ssh_manager.py      # paramiko SSH client wrapper
│   │   └── mqtt_service.py     # paho-mqtt client with Qt signals
│   └── utils/
│       └── settings.py         # QSettings persistence helper
└── tests/
    ├── test_broker_config.py
    ├── test_topic_tree.py
    └── test_ssh_manager.py
```
```
