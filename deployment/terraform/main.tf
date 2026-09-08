terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  project_name = "bedaanwaves"
  common_tags = {
    Project     = local.project_name
    ManagedBy   = "Terraform"
    Environment = var.environment
  }
}

resource "random_string" "db_password" {
  length  = 32
  special = false
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-vpc"
  })
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-public-subnet-${count.index + 1}"
    Tier = "public"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-igw"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "bedaanwaves" {
  name_prefix = "${local.project_name}-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-sg"
  })
}

resource "aws_db_subnet_group" "bedaanwaves" {
  name       = "${local.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.public[*].id

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-db-subnet-group"
  })
}

resource "aws_db_instance" "bedaanwaves" {
  identifier             = "${local.project_name}-db"
  engine                 = "postgres"
  engine_version         = "14.10"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_max_allocated_storage
  db_name                = var.db_name
  username               = var.db_username
  password               = random_string.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.bedaanwaves.name
  vpc_security_group_ids = [aws_security_group.bedaanwaves.id]
  publicly_accessible    = false
  storage_encrypted      = true

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.project_name}-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-db"
  })
}

resource "aws_instance" "bedaanwaves" {
  count         = var.instance_count
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public[count.index % 2].id
  vpc_security_group_ids = [aws_security_group.bedaanwaves.id]

  key_name = aws_key_pair.bedaanwaves.key_name

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    db_endpoint     = aws_db_instance.bedaanwaves.endpoint
    db_password     = random_string.db_password.result
    environment     = var.environment
  }))

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-server-${count.index + 1}"
    Role = count.index == 0 ? "primary" : "worker"
  })
}

resource "aws_key_pair" "bedaanwaves" {
  key_name   = "${local.project_name}-key"
  public_key = tls_private_key.bedaanwaves.public_key_openssh

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-key"
  })
}

resource "tls_private_key" "bedaanwaves" {
  algorithm = "RSA"
  rsa_bits  = 4096
}
