terraform {
  required_providers {
    terrible = {
      source  = "local/terrible/terrible"
      version = "0.0.1"
    }
  }
}

variable "state_file" {
  description = "Path for the terrible provider state file"
  default     = "/tmp/async_task_state.json"
}

provider "terrible" {
  state_file = var.state_file
}

resource "terrible_host" "local" {
  host       = "127.0.0.1"
  connection = "local"
}

resource "terrible_command" "async_touch" {
  host_id       = terrible_host.local.id
  cmd           = "touch /tmp/terrible_async_marker.txt"
  async_seconds = 10
  poll_interval = 2
}

output "async_rc" {
  value = terrible_command.async_touch.rc
}

output "async_changed" {
  value = terrible_command.async_touch.changed
}
