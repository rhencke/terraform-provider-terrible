# terrible — Terraform Provider for Ansible (pure Python)

A Terraform/OpenTofu provider that exposes Ansible tasks as Terraform-managed resources. Operators define target hosts and Ansible module executions as Terraform resources, keeping everything in state — no Ansible inventory required.

## Overview

**terrible** executes Ansible modules in-process (no SSH round-trips for the Ansible control path) and maps module inputs/outputs to Terraform resource attributes. Task resources are discovered dynamically from all installed Ansible modules at startup; schemas are generated from each module's `DOCUMENTATION` and `RETURN` blocks.

## Features

- Every installed Ansible module becomes a Terraform resource (`terrible_ping`, `terrible_command`, `terrible_file`, etc.)
- Community collection modules are also discovered (`terrible_community_general_git_config`, etc.)
- Data sources generated for modules with full check-mode support (`terrible_datasource_stat`, etc.)
- Ephemeral resources for one-shot operations that don't persist to state
- WinRM support for Windows targets
- Ansible Vault integration (`terrible_vault` data source)
- State-file–based drift detection via Ansible check mode

## Requirements

- Python 3.12+
- Terraform or OpenTofu
- Ansible (≥ 13.3.0)
- uv (package management)

## Platform support

**Linux and macOS only.** Ansible does not support Windows as a control node — the machine running Terraform and this provider must be Linux or macOS. Windows machines can be *targeted* via WinRM, but the provider itself cannot run on Windows. Use WSL if you need to run Terraform on a Windows host.

Binaries are provided for Linux (amd64, arm64) and macOS (arm64). Intel Mac users can run the arm64 binary transparently via Rosetta 2.

## Installation

The provider is published to the [Terraform Registry](https://registry.terraform.io/providers/rhencke/terrible/latest). Add it to your Terraform configuration:

```hcl
terraform {
  required_providers {
    terrible = {
      source  = "rhencke/terrible"
    }
  }
}
```

## Quick start

```hcl
provider "terrible" {}

resource "terrible_host" "localhost" {
  connection = "local"
}

resource "terrible_ping" "check" {
  host_id = terrible_host.localhost.id
}
```

See [`examples/`](examples/) for working configurations demonstrating task chains, parallel execution, triggers, and cloud VM provisioning.

## Development

### Setup

```bash
uv sync
make install-hooks     # install pre-commit hook (runs tests before every commit)
```

### Common commands

```bash
make test              # unit tests (100% coverage required)
make integration-test  # integration tests against localhost
make test-all          # unit + integration (same as pre-commit hook)
make run-provider      # run provider in dev mode (prints TF_REATTACH_PROVIDERS)
make install-provider  # install provider into Terraform plugin directory
make example-init      # terraform init for examples
make example-apply     # terraform apply for examples
```

### Project structure

```
terrible_provider/
  cli.py             # CLI entrypoint
  provider.py        # TerribleProvider — schema, state, resource/datasource registry
  host.py            # terrible_host resource
  task_base.py       # TerribleTaskBase — dynamically-discovered Ansible module resources
  task_datasource.py # Task data sources (modules with check_mode: full)
  discovery.py       # Ansible modules → Terraform resources/datasources
  play.py            # terrible_playbook and terrible_role resources (deprecated)
  vault.py           # terrible_vault data source
  install.py         # Provider installation utilities
tests/
  test_*.py          # Unit tests
  integration/       # Integration test cases
examples/            # Working Terraform configurations
```

### Architecture

- **State:** `terrible_state.json` in the Terraform working directory
- **Ansible execution:** In-process via `TaskQueueManager` with a single thread-safe lock
- **Discovery:** Modules introspected at startup; schemas cached in SQLite at `~/.cache/tf-python-provider/discovery.db`
- **Task resources:** Common attributes: `host_id`, `result`, `changed`, `triggers`, `timeout`, `ignore_errors`, `changed_when`, `failed_when`, `environment`, `tags`, `skip_tags`, `async_seconds`, `poll_interval`, `delegate_to_id`

## License

GPLv3
