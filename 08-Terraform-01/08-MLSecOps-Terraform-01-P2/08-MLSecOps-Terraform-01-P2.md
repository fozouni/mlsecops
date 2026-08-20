# 08-MLSecOps-Terraform-01-P2

## Installation

👉 https://developer.hashicorp.com/terraform/install

## ArvanCloud Provider

👉 https://git.arvancloud.ir/arvancloud/iaas/terraform-provider 



## Terraform main Commands

```bash
terraform init

terraform plan

terraform apply

terraform apply --auto-approve

terraform state list

terraform state shows NAME_OF_RESOURCE
```



## Some Notes

In snippet

```json
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

`~>` is called (sometimes) **twiddle-wakka** operator (AKA **pessimistic operator**).

```
~> 6.0    →  allows  >= 6.0.0  and  < 7.0.0
             (locks the MAJOR version, minor/patch can move freely

~> 6.0.0  →  allows  >= 6.0.0  and  < 6.1.0
             (locks MAJOR.MINOR, only patch can move)
```

