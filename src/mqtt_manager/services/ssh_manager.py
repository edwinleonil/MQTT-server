"""SSH Manager — Remote Raspberry Pi management via paramiko."""

from __future__ import annotations

import paramiko
from PySide6.QtCore import QObject, QThread, Signal


class SSHWorker(QObject):
    """Runs SSH operations off the main thread."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args):
        super().__init__()
        self._func = func
        self._args = args

    def run(self):
        try:
            result = self._func(*self._args)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class SSHManager(QObject):
    """Manages an SSH connection to the Raspberry Pi for Mosquitto administration."""

    connected = Signal()
    disconnected = Signal()
    connection_error = Signal(str)

    MOSQUITTO_CONF = "/etc/mosquitto/conf.d/mqtt-server.conf"
    PASSWD_FILE = "/etc/mosquitto/passwd"
    LOG_FILE = "/var/log/mosquitto/mosquitto.log"
    SERVICE_NAME = "mosquitto"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client: paramiko.SSHClient | None = None
        self._threads: list[QThread] = []

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()

    def connect(
        self,
        host: str,
        port: int = 22,
        username: str = "pi",
        password: str | None = None,
        key_path: str | None = None,
    ):
        self.disconnect()
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs: dict = dict(hostname=host, port=port, username=username, timeout=10)
            if key_path:
                kwargs["key_filename"] = key_path
            elif password:
                kwargs["password"] = password
            client.connect(**kwargs)
            self._client = client
            self.connected.emit()
        except Exception as exc:
            self.connection_error.emit(str(exc))

    def disconnect(self):
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self.disconnected.emit()

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def exec_command(self, cmd: str) -> tuple[str, str, int]:
        """Execute a command and return (stdout, stderr, exit_code)."""
        if not self.is_connected:
            raise RuntimeError("SSH not connected")
        _, stdout, stderr = self._client.exec_command(cmd, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), exit_code

    # ------------------------------------------------------------------
    # File operations (SFTP)
    # ------------------------------------------------------------------

    def read_file(self, remote_path: str) -> str:
        if not self.is_connected:
            raise RuntimeError("SSH not connected")
        sftp = self._client.open_sftp()
        try:
            with sftp.open(remote_path, "r") as f:
                return f.read().decode()
        finally:
            sftp.close()

    def write_file(self, remote_path: str, content: str):
        """Write content to a remote file. Uses a temp file + sudo mv for root-owned paths."""
        if not self.is_connected:
            raise RuntimeError("SSH not connected")
        tmp_path = f"/tmp/mqtt_manager_{remote_path.replace('/', '_')}"
        sftp = self._client.open_sftp()
        try:
            with sftp.open(tmp_path, "w") as f:
                f.write(content)
        finally:
            sftp.close()
        self.exec_command(f"sudo mv {tmp_path} {remote_path}")

    # ------------------------------------------------------------------
    # Mosquitto service management
    # ------------------------------------------------------------------

    def get_service_status(self) -> str:
        """Return 'active', 'inactive', 'failed', or the raw status string."""
        stdout, _, _ = self.exec_command(f"systemctl is-active {self.SERVICE_NAME}")
        return stdout.strip()

    def start_service(self) -> tuple[str, str, int]:
        return self.exec_command(f"sudo systemctl start {self.SERVICE_NAME}")

    def stop_service(self) -> tuple[str, str, int]:
        return self.exec_command(f"sudo systemctl stop {self.SERVICE_NAME}")

    def restart_service(self) -> tuple[str, str, int]:
        return self.exec_command(f"sudo systemctl restart {self.SERVICE_NAME}")

    # ------------------------------------------------------------------
    # Mosquitto config
    # ------------------------------------------------------------------

    def read_config(self) -> str:
        return self.read_file(self.MOSQUITTO_CONF)

    def write_config(self, content: str):
        self.write_file(self.MOSQUITTO_CONF, content)

    # ------------------------------------------------------------------
    # User management (mosquitto_passwd)
    # ------------------------------------------------------------------

    def list_users(self) -> list[str]:
        stdout, _, code = self.exec_command(f"sudo cat {self.PASSWD_FILE}")
        if code != 0:
            return []
        users = []
        for line in stdout.strip().splitlines():
            if ":" in line:
                users.append(line.split(":")[0])
        return users

    def add_user(self, username: str, password: str) -> tuple[str, str, int]:
        return self.exec_command(
            f"sudo mosquitto_passwd -b {self.PASSWD_FILE} {username} {password}"
        )

    def remove_user(self, username: str) -> tuple[str, str, int]:
        return self.exec_command(
            f"sudo mosquitto_passwd -D {self.PASSWD_FILE} {username}"
        )

    # ------------------------------------------------------------------
    # Log access
    # ------------------------------------------------------------------

    def get_log(self, lines: int = 100) -> str:
        stdout, _, _ = self.exec_command(f"sudo tail -n {int(lines)} {self.LOG_FILE}")
        return stdout

    # ------------------------------------------------------------------
    # Async helpers
    # ------------------------------------------------------------------

    def run_async(self, func, *args, on_finished=None, on_error=None):
        """Run a function in a background QThread. Returns the thread."""
        thread = QThread()
        worker = SSHWorker(func, *args)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        if on_finished:
            worker.finished.connect(on_finished)
        if on_error:
            worker.error.connect(on_error)

        def cleanup():
            thread.quit()
            thread.wait()
            if thread in self._threads:
                self._threads.remove(thread)

        worker.finished.connect(cleanup)
        worker.error.connect(cleanup)

        self._threads.append(thread)
        thread.start()
        return thread
