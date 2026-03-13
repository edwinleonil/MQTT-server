"""Tests for SSHManager — mock-based, no real SSH connection needed."""

from unittest.mock import MagicMock, patch

from mqtt_manager.services.ssh_manager import SSHManager


def _make_exec_result(stdout_data: str, stderr_data: str = "", exit_code: int = 0):
    """Create mock return value for paramiko exec_command."""
    stdin = MagicMock()
    stdout = MagicMock()
    stdout.read.return_value = stdout_data.encode()
    stdout.channel.recv_exit_status.return_value = exit_code
    stderr = MagicMock()
    stderr.read.return_value = stderr_data.encode()
    return stdin, stdout, stderr


class TestSSHManagerExecCommand:
    def setup_method(self):
        self.mgr = SSHManager()
        self.mgr._client = MagicMock()
        # Make is_connected return True
        transport = MagicMock()
        transport.is_active.return_value = True
        self.mgr._client.get_transport.return_value = transport

    def test_exec_command(self):
        self.mgr._client.exec_command.return_value = _make_exec_result("hello\n")
        stdout, stderr, code = self.mgr.exec_command("echo hello")
        assert stdout == "hello\n"
        assert code == 0

    def test_get_service_status(self):
        self.mgr._client.exec_command.return_value = _make_exec_result("active\n")
        status = self.mgr.get_service_status()
        assert status == "active"

    def test_list_users(self):
        passwd_content = "alice:$7$hash1\nbob:$7$hash2\n"
        self.mgr._client.exec_command.return_value = _make_exec_result(passwd_content)
        users = self.mgr.list_users()
        assert users == ["alice", "bob"]

    def test_list_users_empty(self):
        self.mgr._client.exec_command.return_value = _make_exec_result("", "", 1)
        users = self.mgr.list_users()
        assert users == []

    def test_start_service(self):
        self.mgr._client.exec_command.return_value = _make_exec_result("")
        _, _, code = self.mgr.start_service()
        assert code == 0
        self.mgr._client.exec_command.assert_called_with(
            "sudo systemctl start mosquitto", timeout=30
        )

    def test_get_log(self):
        log_text = "line1\nline2\nline3\n"
        self.mgr._client.exec_command.return_value = _make_exec_result(log_text)
        log = self.mgr.get_log(lines=50)
        assert log == log_text
        self.mgr._client.exec_command.assert_called_with(
            "sudo tail -n 50 /var/log/mosquitto/mosquitto.log", timeout=30
        )
