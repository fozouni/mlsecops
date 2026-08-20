data "aws_ami" "ubuntu" {
  most_recent = true #if multiple match, take the newest

  filter { #give me AMIs whose name looks like this
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"]
  # Canonical
  # ONLY from this trusted publisher
}

resource "aws_instance" "my_instance" {
  ami           = data.aws_ami.ubuntu.id #we can get the AMI ID from aws panel
  instance_type = "t3.micro"

  tags = {
    Name = "My Instance"
  }
}
