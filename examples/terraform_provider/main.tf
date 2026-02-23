terraform {
  required_providers {
    terrible = {
      source = "local/terrible/terrible"
      version = "0.0.1"
    }
  }
}

provider "terrible" {}

resource "terrible_item" "example" {
  name = "example"
  value = "hello from python provider"
}

output "created_id" {
  value = terrible_item.example.id
}
