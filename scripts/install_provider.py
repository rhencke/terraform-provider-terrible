#!/usr/bin/env python3
"""Install the local Python Terraform provider into a Terraform plugin directory.

This script uses the bundled `tf.runner.install_provider` helper to create the
local registry layout and copies a zipped provider executable for multiple
platform targets. It's intended for local development and testing.

Usage:
  python scripts/install_provider.py [--plugin-dir PATH] [--provider-script PATH]

Defaults:
  host=local, namespace=terrible, project=terrible, version=0.0.1
  plugin-dir=~/.terraform.d/plugins
  provider-script=./bin/terraform-provider-terrible
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    p = argparse.ArgumentParser(description="Install local Python Terraform provider")
    p.add_argument("--host", default="local", help="Provider host (default: local)")
    p.add_argument("--namespace", default="terrible", help="Provider namespace (default: terrible)")
    p.add_argument("--project", default="terrible", help="Provider project (default: terrible)")
    p.add_argument("--version", default="0.0.1", help="Provider version (default: 0.0.1)")
    p.add_argument(
        "--plugin-dir",
        default=str(Path.home() / ".terraform.d" / "plugins"),
        help="Terraform plugin directory to install into",
    )
    p.add_argument(
        "--provider-script",
        default=str(Path.cwd() / "bin" / "terraform-provider-terrible"),
        help="Path to the provider executable script",
    )

    args = p.parse_args(argv)

    plugin_dir = Path(args.plugin_dir).expanduser()
    provider_script = Path(args.provider_script)

    if not provider_script.exists():
        print(f"Provider script not found: {provider_script}", file=sys.stderr)
        return 2

    # Lazy import to avoid importing heavy deps unless needed
    try:
        from tf.runner import install_provider
    except Exception as e:
        print("Failed to import tf.runner.install_provider:", e, file=sys.stderr)
        return 3

    plugin_dir.mkdir(parents=True, exist_ok=True)

    try:
        install_provider(
            args.host,
            args.namespace,
            args.project,
            args.version,
            plugin_dir,
            provider_script,
        )
    except Exception as e:
        print("install_provider failed:", e, file=sys.stderr)
        return 4

    print(f"Installed provider {args.host}/{args.namespace}/{args.project} at {plugin_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
