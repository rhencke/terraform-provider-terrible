"""
Integration tests for the terrible provider against a real Alpine Linux VM.

Skip unless TERRIBLE_INTEGRATION=1 is set so normal `pytest -q` never tries
to boot a VM.

Usage:
  TERRIBLE_INTEGRATION=1 uv run pytest tests/integration/ -v
"""

import json
import os
import subprocess

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("TERRIBLE_INTEGRATION"),
    reason="Set TERRIBLE_INTEGRATION=1 to run integration tests",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_vars(ws: dict) -> list[str]:
    pairs = {
        "ssh_host": ws["ssh_host"],
        "ssh_port": str(ws["ssh_port"]),
        "ssh_user": ws["ssh_user"],
        "ssh_key_path": ws["ssh_key"],
        "state_file": ws["state_file"],
    }
    args = []
    for k, v in pairs.items():
        args += ["-var", f"{k}={v}"]
    return args


def tf_apply(ws: dict) -> dict:
    subprocess.run(
        [ws["tf_bin"], "apply", "-auto-approve", "-no-color"] + _base_vars(ws),
        cwd=ws["tf_dir"], env=ws["tf_env"], check=True,
    )
    raw = subprocess.check_output(
        [ws["tf_bin"], "output", "-json"],
        cwd=ws["tf_dir"], env=ws["tf_env"],
    )
    return {k: v["value"] for k, v in json.loads(raw).items()}


def tf_plan_exit_code(ws: dict) -> int:
    """Return terraform plan exit code: 0=no changes, 2=changes, 1=error."""
    r = subprocess.run(
        [ws["tf_bin"], "plan", "-detailed-exitcode", "-no-color"] + _base_vars(ws),
        cwd=ws["tf_dir"], env=ws["tf_env"],
    )
    return r.returncode


def tf_destroy(ws: dict) -> None:
    subprocess.run(
        [ws["tf_bin"], "destroy", "-auto-approve", "-no-color"] + _base_vars(ws),
        cwd=ws["tf_dir"], env=ws["tf_env"],
    )


def ssh_run(ws: dict, cmd: str) -> str:
    return subprocess.check_output(
        [
            "ssh",
            "-i", ws["ssh_key"],
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "BatchMode=yes",
            "-p", str(ws["ssh_port"]),
            f"{ws['ssh_user']}@{ws['ssh_host']}",
            cmd,
        ],
        text=True,
    ).strip()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def applied(integration_workspace):
    """Apply once for the module; destroy on teardown."""
    outputs = tf_apply(integration_workspace)
    yield integration_workspace, outputs
    tf_destroy(integration_workspace)


class TestApply:
    def test_host_id_assigned(self, applied):
        _, out = applied
        assert out["host_id"], "host_id should be a non-empty UUID hex"

    def test_ping_returns_pong(self, applied):
        _, out = applied
        assert out["ping_result"] == "pong"

    def test_command_rc_zero(self, applied):
        _, out = applied
        assert out["marker_rc"] == 0

    def test_command_stdout_contains_marker(self, applied):
        _, out = applied
        assert "terrible-ok" in out["marker_stdout"]

    def test_command_changed_on_first_apply(self, applied):
        _, out = applied
        assert out["marker_changed"] is True

    def test_file_directory_exists_on_vm(self, applied):
        ws, _ = applied
        result = ssh_run(ws, "test -d /tmp/terrible_test_dir && echo exists")
        assert result == "exists"

    def test_marker_file_exists_on_vm(self, applied):
        ws, _ = applied
        content = ssh_run(ws, "cat /tmp/terrible_marker.txt")
        assert "terrible-ok" in content


class TestIdempotency:
    def test_second_plan_has_no_changes(self, applied):
        ws, _ = applied
        exit_code = tf_plan_exit_code(ws)
        assert exit_code == 0, (
            f"Expected exit code 0 (no changes) but got {exit_code}. "
            "Provider state may be drifting."
        )
