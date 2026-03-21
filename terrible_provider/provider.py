import logging
from pathlib import Path

from tf.iface import Provider
from tf.schema import Attribute, Schema
from tf.types import String
from tf.utils import Diagnostics

from .discovery import discover_task_resources
from .host import TerribleHost
from .play import TerriblePlaybook, TerribleRole
from .vault import TerribleVault

log = logging.getLogger(__name__)


class TerribleProvider(Provider):
    def __init__(self):
        self._state: dict[str, dict] = {}
        self._task_resources: list | None = None
        self._task_datasources: list | None = None
        self._vault_secrets: list | None = None

    def _ensure_discovered(self):
        if self._task_resources is None:
            self._task_resources, self._task_datasources = discover_task_resources()

    def get_model_prefix(self) -> str:
        return "terrible_"

    def get_provider_schema(self, diags: Diagnostics) -> Schema:
        return Schema(
            attributes=[
                Attribute(
                    "vault_password",
                    String(),
                    optional=True,
                    sensitive=True,
                    description="Vault password for decrypting Ansible Vault data.",
                ),
                Attribute(
                    "vault_password_file",
                    String(),
                    optional=True,
                    description="Path to a file containing the vault password.",
                ),
            ]
        )

    def full_name(self) -> str:
        return "local/terrible/terrible"

    def validate_config(self, diags: Diagnostics, config: dict):
        if config and config.get("vault_password") and config.get("vault_password_file"):
            diags.add_error(
                "vault_password and vault_password_file are mutually exclusive",
                "Set only one of vault_password or vault_password_file, not both.",
            )

    def configure_provider(self, diags: Diagnostics, config: dict):
        # Vault setup
        self._vault_secrets = None
        if config:
            password = config.get("vault_password")
            vpf = config.get("vault_password_file")
            if not password and vpf:
                try:
                    password = Path(vpf).expanduser().read_text().strip()
                except Exception as exc:
                    diags.add_error("Cannot read vault password file", str(exc))
                    return
            if password:
                from ansible.parsing.vault import VaultSecret

                self._vault_secrets = [("default", VaultSecret(password.encode("utf-8")))]

    def get_data_sources(self) -> list:
        self._ensure_discovered()
        return [TerribleVault, *self._task_datasources]  # type: ignore[misc]

    def get_resources(self) -> list:
        self._ensure_discovered()
        return [TerribleHost, TerriblePlaybook, TerribleRole, *self._task_resources]  # type: ignore[misc]
