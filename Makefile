UV=uv run

.PHONY: help editable-install install-provider run-provider example-init example-apply example-fresh integration-test integration-test-local build-binary

help:
	@echo "Makefile targets:"
	@echo "  editable-install    - install package in editable mode"
	@echo "  install-provider    - install provider into local terraform plugin registry"
	@echo "  run-provider        - run provider in dev mode (prints TF_REATTACH_PROVIDERS)"
	@echo "  example-init        - run 'terraform init' in the example project"
	@echo "  example-apply       - run 'terraform apply' in the example project (interactive)"
	@echo "  example-fresh       - reinstall provider, wipe state, and auto-apply the example"
	@echo "  integration-test    - run integration tests against a QEMU VM (requires QEMU + cloud-image-utils)"
	@echo "  integration-test-local - same, with verbose output and longer timeout"
	@echo "  build-binary        - build a standalone pex binary (terraform-provider-terrible)"

editable-install:
	$(UV) pip install -e .

install-provider:
	$(UV) ./bin/install-provider

run-provider:
	$(UV) ./bin/terraform-provider-terrible --dev

example-init:
	cd examples/terraform_provider && terraform init

example-apply:
	cd examples/terraform_provider && terraform apply

example-fresh: install-provider
	rm -f examples/terraform_provider/terraform.tfstate examples/terraform_provider/terraform.tfstate.backup terrible_state.json
	cd examples/terraform_provider && terraform apply -auto-approve

integration-test: install-provider
	TERRIBLE_INTEGRATION=1 $(UV) pytest tests/integration/ -v --timeout=240

integration-test-local: install-provider
	TERRIBLE_INTEGRATION=1 $(UV) pytest tests/integration/ -v -s --timeout=300

build-binary:
	$(UV) uv export -f requirements.txt --no-dev -o /tmp/terrible-requirements.txt
	$(UV) pex -r /tmp/terrible-requirements.txt ./ \
	  -o terraform-provider-terrible \
	  --scie eager \
	  -m terrible_provider.cli:main
	@echo "Binary built: ./terraform-provider-terrible"
