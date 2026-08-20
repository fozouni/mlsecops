#🔴 This file will launch two Servers with private IP and some other components
# In this file we will show how we can detach a volume and remove it.

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

# Variables
variable "region_ba1" {
  default = "ir-thr-ba1"
}

variable "region_si1" {
  default = "ir-thr-si1"
}

# Data sources for each region
data "arvan_images" "image_ba1" {
  region     = var.region_ba1
  image_type = "distributions"
}

data "arvan_images" "image_si1" {
  region     = var.region_si1
  image_type = "distributions"
}

data "arvan_plans" "plan_ba1" {
  region = var.region_ba1
}

data "arvan_plans" "plan_si1" {
  region = var.region_si1
}

# Locals to get Ubuntu 24.04 images
locals {
  ubuntu_ba1 = [for img in data.arvan_images.image_ba1.distributions : img if img.distro_name == "ubuntu" && img.name == "24.04"][0]
  ubuntu_si1 = [for img in data.arvan_images.image_si1.distributions : img if img.distro_name == "ubuntu" && img.name == "24.04"][0]

  eco_plan_ba1 = [for plan in data.arvan_plans.plan_ba1.plans : plan if plan.id == "eco-1-1-0"][0]
  eco_plan_si1 = [for plan in data.arvan_plans.plan_si1.plans : plan if plan.id == "eco-1-1-0"][0]
}

# Security Groups
resource "arvan_security_group" "sg_ba1" {
  region      = var.region_ba1
  description = "Basic security group"
  name        = "basic-sg"
  rules = [
    { direction = "ingress", protocol = "icmp" },
    { direction = "ingress", protocol = "udp" },
    { direction = "ingress", protocol = "tcp" },
    { direction = "egress", protocol = "" }
  ]
}

resource "arvan_security_group" "sg_si1" {
  region      = var.region_si1
  description = "Basic security group"
  name        = "basic-sg"
  rules = [
    { direction = "ingress", protocol = "icmp" },
    { direction = "ingress", protocol = "udp" },
    { direction = "ingress", protocol = "tcp" },
    { direction = "egress", protocol = "" }
  ]
}

# Volumes
resource "arvan_volume" "vol_ba1" {
  region      = var.region_ba1
  description = "Volume for server"
  name        = "server-volume"
  size        = 10
}

resource "arvan_volume" "vol_si1" {
  region      = var.region_si1
  description = "Volume for server"
  name        = "server-volume"
  size        = 10
}

# Networks
resource "arvan_network" "net_ba1" {
  region         = var.region_ba1
  description    = "Private network"
  name           = "private-net"
  cidr           = "10.255.255.0/24"
  gateway_ip     = "10.255.255.1"
  enable_gateway = true
  enable_dhcp    = true
  dhcp_range     = { start = "10.255.255.19", end = "10.255.255.150" }
  dns_servers    = ["8.8.8.8", "1.1.1.1"]
}

resource "arvan_network" "net_si1" {
  region         = var.region_si1
  description    = "Private network"
  name           = "private-net"
  cidr           = "10.255.255.0/24"
  gateway_ip     = "10.255.255.1"
  enable_gateway = true
  enable_dhcp    = true
  dhcp_range     = { start = "10.255.255.19", end = "10.255.255.150" }
  dns_servers    = ["8.8.8.8", "1.1.1.1"]
}

# Servers
resource "arvan_abrak" "server_ba1" {
  region    = var.region_ba1
  name      = "server-ba1"
  image_id  = local.ubuntu_ba1.id
  flavor_id = local.eco_plan_ba1.id
  disk_size = 25

  networks = [
    { network_id = arvan_network.net_ba1.network_id }
  ]

  security_groups = [arvan_security_group.sg_ba1.id]
  volumes         = [arvan_volume.vol_ba1.id]
}

resource "arvan_abrak" "server_si1" {
  region    = var.region_si1
  name      = "server-si1"
  image_id  = local.ubuntu_si1.id
  flavor_id = local.eco_plan_si1.id
  disk_size = 25

  networks = [
    { network_id = arvan_network.net_si1.network_id }
  ]

  security_groups = [arvan_security_group.sg_si1.id]
  volumes         = [arvan_volume.vol_si1.id]
}

# Outputs
output "server_ba1_info" {
  value = {
    id       = arvan_abrak.server_ba1.id
    name     = arvan_abrak.server_ba1.name
    password = arvan_abrak.server_ba1.password
    network  = arvan_abrak.server_ba1.networks
  }
}

output "server_si1_info" {
  value = {
    id       = arvan_abrak.server_si1.id
    name     = arvan_abrak.server_si1.name
    password = arvan_abrak.server_si1.password
    network  = arvan_abrak.server_si1.networks
  }
}
