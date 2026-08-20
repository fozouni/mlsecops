terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws" # WHERE to download the provider plugin from
      version = "~> 6.0"        # WHICH version(s) are acceptable
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "eu-central-1"
}


# CDKTF ===> python ===> 2025 deprecated 
