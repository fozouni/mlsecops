resource "aws_subnet" "my_subnet" {
  vpc_id            = aws_vpc.my_vpc.id # When the VPC is created, AWS assigns it
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a" # Change based on your default region

  tags = {
    Name = "My Subnet"
  }
}
