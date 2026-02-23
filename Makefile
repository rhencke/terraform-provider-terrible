PY=python3
PIP=$(PY) -m pip

.PHONY: help editable-install install-provider run-provider example-init example-apply

help:
	@echo "Makefile targets:"
	@echo "  editable-install    - install package in editable mode (pip install -e .)"
	@echo "  install-provider    - install provider into local terraform plugin registry"
	@echo "  run-provider        - run provider in dev mode (prints TF_REATTACH_PROVIDERS)"
	@echo "  example-init        - run 'terraform init' in the example project"
	@echo "  example-apply       - run 'terraform apply' in the example project (interactive)"

editable-install:
	$(PIP) install -e .

install-provider:
	./bin/install-provider

run-provider:
	./bin/terraform-provider-terrible --dev

example-init:
	cd examples/terraform_provider && terraform init

example-apply:
	cd examples/terraform_provider && terraform apply
