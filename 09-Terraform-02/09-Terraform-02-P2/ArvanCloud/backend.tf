terraform {
  backend "s3" {
    endpoints = {
      s3 = "https://s3.ir-thr-at1.arvanstorage.ir"
    }
    bucket                      = "test-09112223333"
    key                         = "PROD/terraform.tfstate"
    access_key                  = "YOUR_ACCESS_KEY"
    secret_key                  = "YOUR_SECRET_KEY"
    region                      = "ir-thr-at1"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
    use_lockfile                = true
    # encrypt                     = true

  }
}

