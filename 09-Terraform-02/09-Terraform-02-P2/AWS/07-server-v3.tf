# variable "my_os" {
#   description = "ami-005e54dee72cc1d00" # us-west-2
#   type        = string
# }

variable "my_os_2" {}
# default = "t2.micro" }

resource "aws_instance" "example" {
  ami           = var.my_os_2
  instance_type = "t2.micro"

  tags = {
    Name = "My Instance"
  }
}

# resource "aws_instance" "example" {
#   ami           = var.my_os
#   instance_type = "t2.micro"

#   tags = {
#     Name = "My Instance"
#   }
# }
