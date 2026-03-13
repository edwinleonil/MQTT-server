"""Entry point for the MQTT Manager application."""

import sys

from PySide6.QtWidgets import QApplication

from mqtt_manager.app import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MQTT Manager")
    app.setOrganizationName("MQTT-server")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
