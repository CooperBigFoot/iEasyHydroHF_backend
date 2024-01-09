####
# Terraform state file is handled in the S3 bucket "sapphire-hf-staging" which was manually created.
# Also, EC2 keypair "sapphire_staging_keypair" was created manually and Elastic IP with
# allocation_id "eipalloc-098a9d8258d4b8f79" was manually created.
# Terraform associates the Elastic IP with the newly created EC2 instance.

# If this is your first time running terraform on this project, change to this directory,
# execute 'terraform init' and after making changes 'terraform plan' and 'terraform apply'.
####

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
  required_version = ">= 1.2.0"
  backend "s3" {
    bucket = "sapphire-hf-staging"
    key    = "terraform/terraform.tfstate"
    region = "eu-central-1"
  }
}

provider "aws" {
  region = "eu-central-1"
}

# ECR
resource "aws_ecr_repository" "backend" {
  name                 = "sapphire_backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "sapphire_frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# SECURITY GROUP
resource "aws_security_group" "instance" {
  name        = "sapphire_staging_sec_group"
  description = "Used in sapphire_staging_tf EC2 instance"
}

resource "aws_security_group_rule" "inbound_access_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.instance.id
}

resource "aws_security_group_rule" "inbound_access_http" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.instance.id
}

resource "aws_security_group_rule" "inbound_access_https" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.instance.id
}

resource "aws_security_group_rule" "outbound_internet_access" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.instance.id
}

# EC2 instance
resource "aws_instance" "sapphire_staging_tf" {
  ami                    = "ami-06dd92ecc74fdfb36"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.instance.id]
  key_name               = "sapphire_staging_keypair" # manually created keypair
  root_block_device {
    volume_size           = "30"
    volume_type           = "gp2"
    delete_on_termination = true
  }
  tags = {
    Name = "sapphire_staging"
  }
}

# EBS volume additional
resource "aws_volume_attachment" "sapphire" {
  device_name = "/dev/sdh"
  volume_id   = aws_ebs_volume.sapphire.id
  instance_id = aws_instance.sapphire_staging_tf.id
}

resource "aws_ebs_volume" "sapphire" {
  availability_zone = aws_instance.sapphire_staging_tf.availability_zone
  size              = 30
  tags              = {
    Name = "Sapphire staging EBS"
  }
}

# ELASTIC IP ASSOCIATE, THE IP ALREADY EXISTS IN AWS
resource "aws_eip_association" "eip_assoc" {
  instance_id   = aws_instance.sapphire_staging_tf.id
  allocation_id = "eipalloc-098a9d8258d4b8f79"
}
