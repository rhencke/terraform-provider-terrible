This example shows how to run the Python provider in development mode and attach it to Terraform.

Quick steps:

1. Make the provider executable:

```bash
chmod +x ../../bin/terraform-provider-terrible
```

2. Run the provider in dev mode from the repository root. This will print an export that you should set:

```bash
./bin/terraform-provider-terrible --dev
# copy the printed export and run it in your shell, e.g.
# export TF_REATTACH_PROVIDERS='{"local/terrible/terrible": {"Protocol": "grpc", ...}}'
```

3. In a second shell, change into this example directory and run Terraform commands:

```bash
cd examples/terraform_provider
terraform init
terraform apply -auto-approve
```

