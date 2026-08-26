# Security notes in working with Terraform

[toc]

## Which files must be excluded from git

We must put the following items on `.gitignore` file:

```
*.tfvars
*.tfvars.json
*.tfstate
*.tfstate.*

# Terraform working directory
.terraform/

# Crash logs
crash.log
crash.*.log
```



## Using `.tfvars`?

Create one file named `terraform.tfvars` and write the following there:

```
#terraform.tfvars
api_key = "OUR_SECRET_API_KEY sits here"
```

Now on the `main.tf` file you should have this block:

```
variable "api_key" {
  type      = string
 👉 sensitive = true
}
```



## `.tfstate` and `.tfstate.backup` files

- **`terraform.tfstate`**  = Terraform's **current** knowledge of your infrastructure.
- **`terraform.tfstate.backup`** = the **previous version** of that state file, kept as a backup.

For example, imagine your state originally contained:

```
VM-A
Network-A
SecurityGroup-A
```

Then you run `terraform apply` and Terraform creates another VM:

```
VM-A
VM-B
Network-A
SecurityGroup-A
```

The files may effectively represent:

```
terraform.tfstate
    ↓
VM-A
VM-B
Network-A
SecurityGroup-A

terraform.tfstate.backup
    ↓
VM-A
Network-A
SecurityGroup-A
```

## Config backends with `backend.tf` file

**ArvanCloud**

```
terraform {
  backend "s3" {
    endpoints = {
      s3 = "https://s3.ir-thr-at1.arvanstorage.ir"
    }
    bucket                      = "test-09112223333"
    key                         = "PROD/terraform.tfstate"
    region                      = "ir-thr-at1"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
    encrypt                     = true
  }
}
```

**AWS**

```
terraform {
  backend "s3" {
    bucket = "THE_NAME_OF_THE_STATE_BUCKET" #tihs bucket should be there and created before running terraform init command
    key    = "some_environment/terraform.tfstate"
    region = "us-east-1"
    # encrypt        = true
    # kms_key_id     = "THE_ID_OF_THE_KMS_KEY"
    # dynamodb_table = "THE_ID_OF_THE_DYNAMODB_TABLE"#✅ mechanism to lock the tfstate file when editing it, to avoid race conditions when multiple people are working on the same tfstate file.
   👉 use_lockfile = true
  }
}
```

> If we delete `access_key` and `secret_key` from backend.tf file, and just pass them when we are going to run `terraform apply`, these secrets never will be published on the logs of Terraform. BUT, if we use `TF_LOG=DEBUG` or `TF_LOG=TRACE` all secrets will store as plain texts. So be cautious.
>
> ```bash
> # How we set and use DEBUG
> 
> export TF_LOG=DEBUG
> terraform apply
> ```

When we wanted to run our `.tf` files, and set `use_lockfile = true` while our resources are creating, a file with extension `.tflock` will be created alongside `.tfstate` file. 

Lifecycle of `.tflock` file:

- **Created** when you run `terraform plan` or `apply` (lock acquired).
- **Deleted** automatically when that command finishes, whether it succeeds, fails, or you cancel it cleanly (Ctrl+C, allowing graceful exit).

![](.\diagram\terraform.tfstate.tflock.png)



## Using Vault



### Install Vault

```powershell
winget install HashiCorp.Vault

# or just download this excecutable file and put on your system PATH

https://releases.hashicorp.com/vault/2.0.4/vault_2.0.4_windows_amd64.zip
```

### Some env vars

```powershell
# Tab 1
vault server -dev
# copy the "Root Token: hvs...." from output

# Tab 2
$env:VAULT_ADDR = "http://127.0.0.1:8200"
$env:VAULT_TOKEN = "hvs.XXXXXXXX"   # paste real token

vault secrets enable -path=secret kv-v2
```

### Write the API key into Vault

```powershell
vault kv put secret/arvancloud/api api_key="your-real-arvan-key-here"
```

> **We can insert Multiple fields:**
>
> ```bash
> vault kv put secret/arvancloud/api `
>   	api_key="your-real-arvan-key" `
>   	machine_user="terraform-ci"
> ```

### Verify it was stored

```powershell
vault kv get secret/arvancloud/api
```

### Read just the one field you need

```powershell
vault kv get -field=api_key secret/arvancloud/api
```

### Inject it into Terraform at apply time

```powershell
$env:TF_VAR_api_key = vault kv get -field=api_key secret/arvancloud/api

#Now run

terraform plan

#and then

terraform apply
```

### Handling AWS secrets with Vault

```bash
vault kv put secret/aws/terraform `
  access_key="YOUR_ACCESS_KEY" `
  secret_key="YOUR_SECRET_KEY"
  
vault kv get secret/aws/terraform

$env:AWS_ACCESS_KEY_ID     = vault kv get -field=access_key secret/aws/terraform
$env:AWS_SECRET_ACCESS_KEY = vault kv get -field=secret_key secret/aws/terraform

terraform plan

terraform apply
```

> **Note:**
> 1- Because `backend` blocks are parsed and initialized **before** Terraform loads any variables, so `var.*` / `TF_VAR_*` simply aren't available yet at that stage.
>
> 2- But, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` are read directly by the **AWS SDK** (which the S3 backend uses internally), completely bypassing Terraform's variable-parsing stage. 
>
> 3- When we use `backends.tf` the `terraform.tfstae` does not anymore saved locally. 



## See a graph of your resources (graphviz tools)

```powershell
PS E:\MLSecOps\Contents\09-MLSecOps-Terraform-02> tr graph
digraph G {
  rankdir = "RL";
  node [shape = rect, fontname = "sans-serif"];
  "data.arvan_dedicated_servers.terraform_dedicated_server" [label="data.arvan_dedicated_servers.terraform_dedicated_server"];
  "data.arvan_images.terraform_image" [label="data.arvan_images.terraform_image"];
  "data.arvan_networks.terraform_network" [label="data.arvan_networks.terraform_network"];
  "data.arvan_plans.plan_list" [label="data.arvan_plans.plan_list"];
  "data.arvan_server_groups.server_group_list" [label="data.arvan_server_groups.server_group_list"];
  "arvan_abrak.Lesson_2" [label="arvan_abrak.Lesson_2"];
  "arvan_network.terraform_private_network" [label="arvan_network.terraform_private_network"];
  "arvan_security_group.terraform_security_group" [label="arvan_security_group.terraform_security_group"];
  "arvan_abrak.Lesson_2" -> "data.arvan_images.terraform_image";
  "arvan_abrak.Lesson_2" -> "data.arvan_plans.plan_list";
  "arvan_abrak.Lesson_2" -> "arvan_network.terraform_private_network";
  "arvan_abrak.Lesson_2" -> "arvan_security_group.terraform_security_group";
}
```

Copy and paste the above results in sites like `https://www.devtoolsdaily.com/graphviz` and see the graph. This give us a good sense of our resources, like this:

![](.\diagram\our-resources.png)

## Final Advice (Use prefix binding)

```bash
API_KEY=$(read -s -p "API key: "; echo "$REPLY") terraform plan

# -s stands for silent
# -p comes from a prompt thst will show on sceern
# REPLY is the default name of our variable that defined from read
```

See power of **prefix-binding to the command** (`VAR=value command` syntax):

```bash
amin@ubuntu24:~$ API_KEY=$(read -s -p "API key: "; echo "$REPLY") ls .ssh/
API key: ar-mlsecops-privatekey.pem  id_ed25519.pub   mlsecops-in-action-privateKey.pem
config                      known_hosts
id_ed25519                  known_hosts.old
amin@ubuntu24:~$ echo $API_KEY

amin@ubuntu24:~$
```

**NOW WE HAVE:** minimal exposure window + no leftover state to accidentally leak later.

> We can use leading space in front of each command we run from cli. With this approach, the command will not show up in history or `.bash_history` file.


We can load the secrets in backends like this

```powershell
$env:AWS_ACCESS_KEY_ID = "PUT-YOUR-KEY-HERE"
$env:AWS_SECRET_ACCESS_KEY = "PUT-YOUR-SECRET-KEY-HERE"
```



## Use import in Terraform 

Suppose that we have a running infrastructure that provisioned by Terraform. Now, due any reasons, we manually turn on another server or anything else. We can use `import` command to bring this new resource to Terraform configs, i.e, let Terraform in the future destroy this resource for us. 

```bash
terraform import {1️⃣RESOURCE_NAME}.{2️⃣INTERNAL_NAME} {3️⃣ID_OF_RESOURCE_IN_ARVAN_PANEL}
```

