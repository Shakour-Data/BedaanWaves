output "instance_public_ips" {
  description = "Public IPs of EC2 instances"
  value       = aws_instance.bedaanwaves[*].public_ip
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.bedaanwaves.endpoint
}

output "db_password" {
  description = "Database password (sensitive)"
  value       = random_string.db_password.result
  sensitive   = true
}

output "ssh_private_key" {
  description = "SSH private key"
  value       = tls_private_key.bedaanwaves.private_key_pem
  sensitive   = true
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}
