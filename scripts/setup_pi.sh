#!/usr/bin/env bash
# setup_pi.sh — Bootstrap Mosquitto MQTT broker on a Raspberry Pi
# Run this script ON the Pi (e.g. via SSH) with sudo privileges.
set -euo pipefail

MOSQUITTO_CONF="/etc/mosquitto/conf.d/mqtt-server.conf"
PASSWD_FILE="/etc/mosquitto/passwd"
LOG_DIR="/var/log/mosquitto"

echo "=== Installing Mosquitto and client tools ==="
apt-get update -qq
apt-get install -y mosquitto mosquitto-clients

echo "=== Enabling Mosquitto systemd service ==="
systemctl enable mosquitto

echo "=== Creating password file ==="
if [ ! -f "$PASSWD_FILE" ]; then
    touch "$PASSWD_FILE"
fi
# root owns the file (required by newer Mosquitto), group=mosquitto so the
# broker process can read it, no access for others.
chown root:mosquitto "$PASSWD_FILE"
chmod 640 "$PASSWD_FILE"
echo "Password file ready at $PASSWD_FILE (root:mosquitto 640)"

echo "=== Ensuring log directory exists ==="
mkdir -p "$LOG_DIR"
chown mosquitto:mosquitto "$LOG_DIR"

echo "=== Deploying Mosquitto configuration ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../config/mosquitto.conf.template"

if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$MOSQUITTO_CONF"
    echo "Config deployed to $MOSQUITTO_CONF"
else
    echo "WARNING: Template not found at $TEMPLATE — writing default config"
    cat > "$MOSQUITTO_CONF" <<'EOF'
# MQTT-server managed configuration
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
persistence true
persistence_location /var/lib/mosquitto/
max_connections -1
EOF
fi

echo "=== Restarting Mosquitto ==="
systemctl restart mosquitto

echo "=== Verifying ==="
systemctl is-active --quiet mosquitto && echo "Mosquitto is running." || echo "ERROR: Mosquitto failed to start."

echo ""
echo "Setup complete. To add an MQTT user run:"
echo "  sudo mosquitto_passwd -b $PASSWD_FILE <username> <password>"
echo ""
echo "To test the broker:"
echo "  mosquitto_sub -h localhost -t 'test/#' &"
echo "  mosquitto_pub -h localhost -t 'test/hello' -m 'world'"
