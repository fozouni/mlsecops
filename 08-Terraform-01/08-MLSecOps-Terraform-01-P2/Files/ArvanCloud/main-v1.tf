#🔴 This file will launch one Server with private IP and some other components

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
  type        = string
  description = "The chosen region for resources"
  default     = "ir-thr-ba1"
}

variable "chosen_distro_name" {
  type        = string
  description = " The chosen distro name for image"
  default     = "ubuntu"
}

variable "chosen_name" {
  type        = string
  description = "The chosen release for image"
  default     = "24.04"
}

variable "chosen_plan_id" {
  type        = string
  description = "The chosen ID of plan"
  default     = "eco-1-1-0"
}

variable "chosen_server_group_id" {
  type        = string
  description = "The chosen ID of Server Group"
  default     = ""
}

variable "dedicated_server_label" {
  type        = string
  description = "A label for chosen dedicated server"
  default     = ""
}

data "arvan_images" "terraform_image" {
  region     = var.region
  image_type = "distributions"
}

data "arvan_plans" "plan_list" {
  region = var.region
}

data "arvan_server_groups" "server_group_list" {
  region = var.region
}

data "arvan_dedicated_servers" "terraform_dedicated_server" {
  region = var.region
}

locals {
  chosen_image = try(
    [for image in data.arvan_images.terraform_image.distributions : image
    if image.distro_name == var.chosen_distro_name && image.name == var.chosen_name],
    []
  )

  selected_plan = [for plan in data.arvan_plans.plan_list.plans : plan if plan.id == var.chosen_plan_id][0]
}

resource "arvan_security_group" "terraform_security_group" {
  region      = var.region
  description = "Terraform-created security group"
  name        = "lesson_1"
  rules = [
    {
      direction = "ingress"
      protocol  = "icmp"
    },
    {
      direction = "ingress"
      protocol  = "udp"
    },
    {
      direction = "ingress"
      protocol  = "tcp"
    },
    {
      direction = "egress"
      protocol  = "" # ANY protocol (TCP, UDP, ICMP, everything)
      # In a nutshell, the above condition allows all outbound traffic, on any protocol, to anywhere
    }
  ]
}

resource "arvan_volume" "terraform_volume" {
  region      = var.region
  description = "Terraform-created volume"
  name        = "lesson_1"
  size        = 10
}

data "arvan_networks" "terraform_network" {
  region = var.region
}

locals {
  chosen_dedicated_server = try(
    [for ds in data.arvan_dedicated_servers.terraform_dedicated_server.dedicated_servers : ds if contains(ds.labels, var.dedicated_server_label)], []
  )
}

resource "arvan_network" "terraform_private_network" {
  region      = var.region
  description = "Terraform-created private network"
  name        = "lesson_1"
  dhcp_range = {
    start = "10.255.255.19"
    end   = "10.255.255.150"
  }
  dns_servers    = ["8.8.8.8", "1.1.1.1"]
  enable_dhcp    = true
  enable_gateway = true
  cidr           = "10.255.255.0/24"
  gateway_ip     = "10.255.255.1"
}

resource "arvan_abrak" "Lesson_1" {
  depends_on = [arvan_volume.terraform_volume, arvan_network.terraform_private_network, arvan_security_group.terraform_security_group]
  timeouts {
    create = "1h30m"
    update = "2h"
    delete = "20m"
    read   = "10m"
  }
  region          = var.region
  name            = "Lesson-1"
  count           = 1
  image_id        = local.chosen_image[0].id
  flavor_id       = local.selected_plan.id
  disk_size       = 25
  server_group_id = var.chosen_server_group_id
  networks = [
    {
      network_id = arvan_network.terraform_private_network.network_id
    }
  ]
  security_groups = [arvan_security_group.terraform_security_group.id]
  volumes         = [arvan_volume.terraform_volume.id]
}

output "instances" {
  value = arvan_abrak.Lesson_1
}


#✅ In ArvanCloud we have
# network (VPC + subnet combined) ===> NIC (implicit, inside server resource) ===> server

#✅ BUT in AWS

#1 VPC (10.0.0.0/16) =====> Home network (192.168.0.0/16... loosely)
#2    Subnet (10.0.1.0/24) =====> Wi-Fi network (192.168.1.0/24)
#3       NIC (attached to VM) =====> Wi-Fi adapter (in your laptop)
#4          Server (the VM) =====> Your laptop
