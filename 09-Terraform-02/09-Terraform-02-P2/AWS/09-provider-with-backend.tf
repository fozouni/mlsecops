terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "eu-central-1"
}

terraform {
  backend "s3" {
    bucket = "THE_NAME_OF_THE_STATE_BUCKET" #ths bucket should be there and created before running terraform init command
    key    = "some_environment/terraform.tfstate"
    region = "us-east-1"
    # encrypt        = true
    # kms_key_id     = "THE_ID_OF_THE_KMS_KEY"
    # dynamodb_table = "THE_ID_OF_THE_DYNAMODB_TABLE"#✅ mechanism to lock the tfstate file when editing it, to avoid race conditions when multiple people are working on the same tfstate file.
    use_lockfile = true
  }
}
