# terrible — Terraform Provider for Ansible (pure Python)

A minimal Terraform provider that integrates with Ansible, implemented in pure Python.
This repository contains a small reference implementation and helpers to use Ansible
playbooks and tasks as Terraform-managed resources.

## Overview

This project aims to provide a lightweight Terraform provider that delegates
configuration to Ansible. It's written in pure Python to make development and
extension easy for Python-savvy operators.

## Features

- Use Ansible playbooks as Terraform-managed resources
- Small, easy-to-read Python codebase for learning and extension
- Example integration patterns for provisioning and configuration

## Requirements

- Python 3.11+
- Terraform (for real usage)
- Ansible (to execute playbooks)

## Installation

This repository is a minimal implementation — it does not publish a binary
Terraform provider. For development, install the Python dependencies from
`pyproject.toml` and run the example code:

```bash
python -m pip install -e .
```

## Usage (example)

Below is an illustrative Terraform HCL snippet demonstrating how you might
conceptually declare an Ansible-managed resource. This repository does not
include a real Terraform registry provider binary; it's intended as an
implementation and learning reference.

```hcl
provider "ansible" {}

resource "ansible_playbook" "deploy_app" {
	playbook = "site.yml"
	inventory = "inventory.ini"
}
```

In practice, use the Python code in this repo to drive Ansible runs and adapt
its behavior for your environment.

## Development

- Edit `main.py` to explore the provider's entrypoint and behavior.
- Run and iterate locally; the code is intentionally small so you can read and
	modify it quickly.

## Contributing

Contributions and issues are welcome. Keep changes focused and include tests
when adding features.

## License

MIT

