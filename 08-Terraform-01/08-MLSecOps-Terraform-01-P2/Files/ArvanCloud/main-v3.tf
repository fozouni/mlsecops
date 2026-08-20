#🔴 This file will launch one Server with public IP and a pinned ssh key name

terraform {
  required_providers {
    arvan = {
      source  = "terraform.arvancloud.ir/arvancloud/iaas"
      version = "~>0.7.16"
    }
  }
}

provider "arvan" {
  api_key = "PUT-YOUR-API-KEY-HERE"
}

variable "region" {
  type    = string
  default = "ir-thr-ba1"
}

# Data sources
data "arvan_images" "ubuntu" {
  region     = var.region
  image_type = "distributions"
}

data "arvan_plans" "plans" {
  region = var.region
}

data "arvan_networks" "networks" {
  region = var.region
}

locals {
  ubuntu_image = try(
    [for img in data.arvan_images.ubuntu.distributions : img
    if img.distro_name == "ubuntu" && img.name == "22.04"][0],
    null
  )

  eco_plan = try(
    [for plan in data.arvan_plans.plans.plans : plan
    if plan.id == "eco-1-1-0"][0],
    null
  )

  public_network = try(
    [for net in data.arvan_networks.networks.networks : net
    if net.name == "public212"][0], # Keep only nets where condition is true.
    null                            # If no network named public212 exists, just set public_network to nothing instead of crashing
  )
}

# Create a security group
resource "arvan_security_group" "sg" {
  region      = var.region
  name        = "allow-ssh"
  description = "Allow SSH access"
  rules = [
    {
      direction      = "ingress"
      protocol       = "tcp"
      port_range_min = 22
      port_range_max = 22
    },
    {
      direction = "egress"
      protocol  = ""
    }
  ]
}

# Server with security group
resource "arvan_abrak" "server" {
  timeouts {
    create = "1h30m"
    update = "2h"
    delete = "20m"
    read   = "10m"
  }
  region          = var.region
  name            = "my-server"
  image_id        = local.ubuntu_image.id
  flavor_id       = local.eco_plan.id
  disk_size       = 25
  ssh_key_name    = "mlsecops"
  security_groups = [arvan_security_group.sg.id]

  networks = [
    { network_id = local.public_network.network_id }
  ]
}

# Outputs
output "server_details" {
  value = {
    id       = arvan_abrak.server.id
    name     = arvan_abrak.server.name
    password = arvan_abrak.server.password
    status   = arvan_abrak.server.status
    networks = arvan_abrak.server.networks
  }
}
