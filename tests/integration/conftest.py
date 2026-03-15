"""
Session-scoped QEMU VM fixture for integration tests.

Boots an Alpine Linux cloud image, waits for SSH, installs the provider
into an isolated plugin directory, and yields all connection info.

Prerequisites (installed by CI or locally):
  qemu-system-x86_64, qemu-img, cloud-localds, ssh-keygen
"""

import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import NamedTuple

import pytest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ALPINE_IMAGE_URL = (
    "https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/cloud/"
    "nocloud_alpine-3.21.0-x86_64-bios-cloudinit-r0.qcow2"
)
ALPINE_IMAGE_NAME = "nocloud_alpine-3.21.0-x86_64-bios-cloudinit-r0.qcow2"
IMAGE_CACHE_DIR = Path.home() / ".cache" / "terrible-tests"

BOOT_TIMEOUT = 120  # seconds to wait for SSH after QEMU starts
SSH_HOST = "127.0.0.1"
SSH_USER = "alpine"

REPO_ROOT = Path(__file__).parent.parent.parent
CLOUD_INIT_DIR = Path(__file__).parent / "cloud-init"
TF_CONFIG_SOURCE = Path(__file__).parent / "terraform"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class VMInfo(NamedTuple):
    host: str
    port: int
    user: str
    key_path: str


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_ssh(host: str, port: int, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                return
        except OSError:
            time.sleep(2)
    raise TimeoutError(f"SSH at {host}:{port} did not become available within {timeout}s")


def _download_image() -> Path:
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = IMAGE_CACHE_DIR / ALPINE_IMAGE_NAME
    if dest.exists():
        return dest
    print(f"\n[conftest] Downloading Alpine cloud image → {dest}")
    tmp = dest.with_suffix(".tmp")
    try:
        urllib.request.urlretrieve(ALPINE_IMAGE_URL, tmp)
        tmp.rename(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return dest


def _build_cloud_init_iso(workspace: Path, pub_key: str) -> Path:
    user_data = (CLOUD_INIT_DIR / "user-data").read_text().replace(
        "__SSH_PUBKEY_PLACEHOLDER__", pub_key
    )
    user_data_file = workspace / "user-data"
    user_data_file.write_text(user_data)

    seed_iso = workspace / "seed.iso"
    subprocess.run(
        [
            "cloud-localds",
            str(seed_iso),
            str(user_data_file),
            str(CLOUD_INIT_DIR / "meta-data"),
        ],
        check=True,
        capture_output=True,
    )
    return seed_iso


def _find_tf() -> str:
    for name in ("tofu", "terraform"):
        if shutil.which(name):
            return name
    raise RuntimeError("Neither 'tofu' nor 'terraform' found on PATH")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def integration_workspace(tmp_path_factory):
    """
    Boot an Alpine VM, install the provider, initialise a Terraform working
    directory, and yield a dict of everything tests need.
    """
    ws = tmp_path_factory.mktemp("integration")

    # 1. Ephemeral SSH key pair
    key = ws / "id_ed25519"
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key)],
        check=True, capture_output=True,
    )
    pub_key = (ws / "id_ed25519.pub").read_text().strip()

    # 2. Cloud-init seed ISO
    seed_iso = _build_cloud_init_iso(ws, pub_key)

    # 3. Overlay image (copy-on-write over cached base — never mutates cache)
    base = _download_image()
    overlay = ws / "vm.qcow2"
    subprocess.run(
        ["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", str(base), str(overlay)],
        check=True, capture_output=True,
    )

    # 4. Launch QEMU
    ssh_port = _find_free_port()
    accel = "kvm" if Path("/dev/kvm").exists() else "tcg"
    qemu_cmd = [
        "qemu-system-x86_64",
        f"-accel", accel,
        "-m", "512",
        "-nographic",
        "-drive", f"file={overlay},if=virtio,format=qcow2",
        "-drive", f"file={seed_iso},if=virtio,format=raw,readonly=on",
        "-netdev", f"user,id=net0,hostfwd=tcp:{SSH_HOST}:{ssh_port}-:22",
        "-device", "virtio-net-pci,netdev=net0",
        "-serial", f"file:{ws / 'vm.log'}",
    ]
    print(f"\n[conftest] Starting QEMU on port {ssh_port} (accel={accel})")
    qemu = subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        _wait_for_ssh(SSH_HOST, ssh_port, BOOT_TIMEOUT)
        print("[conftest] SSH is up — VM ready")
        # Give cloud-init a moment to finish writing SSH authorized_keys
        time.sleep(5)

        # 5. Install provider into isolated plugin dir
        plugin_dir = ws / "plugins"
        plugin_dir.mkdir()
        subprocess.run(
            [
                "uv", "run",
                str(REPO_ROOT / "bin" / "install-provider"),
                "--plugin-dir", str(plugin_dir),
                "--provider-script", str(REPO_ROOT / "bin" / "terraform-provider-terrible"),
            ],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
        )

        # 6. Per-session .terraformrc pointing at our isolated plugin dir
        tfrc = ws / ".terraformrc"
        tfrc.write_text(
            f'provider_installation {{\n'
            f'  filesystem_mirror {{\n'
            f'    path    = "{plugin_dir}"\n'
            f'    include = ["local/terrible/terrible"]\n'
            f'  }}\n'
            f'  direct {{\n'
            f'    exclude = ["local/terrible/terrible"]\n'
            f'  }}\n'
            f'}}\n'
        )

        # 7. Terraform working directory (copy of tests/integration/terraform/)
        tf_dir = ws / "terraform"
        shutil.copytree(str(TF_CONFIG_SOURCE), str(tf_dir))

        state_file = str(ws / "terrible.json")
        tf_bin = _find_tf()
        tf_env = {**os.environ, "TF_CLI_CONFIG_FILE": str(tfrc)}

        subprocess.run(
            [tf_bin, "init", "-no-color"],
            cwd=str(tf_dir), env=tf_env, check=True, capture_output=True,
        )

        yield {
            "ws": ws,
            "tf_dir": tf_dir,
            "tf_bin": tf_bin,
            "tf_env": tf_env,
            "state_file": state_file,
            "ssh_host": SSH_HOST,
            "ssh_port": ssh_port,
            "ssh_user": SSH_USER,
            "ssh_key": str(key),
            "vm_log": str(ws / "vm.log"),
        }

    finally:
        qemu.terminate()
        try:
            qemu.wait(timeout=10)
        except subprocess.TimeoutExpired:
            qemu.kill()
        print("[conftest] QEMU stopped")
