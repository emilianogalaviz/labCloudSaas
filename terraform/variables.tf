variable "aws_region" {
  description = "Ohio US east 2"
  default     = "us-east-2"
}

variable "project_name" {
  description = "Prefijo para nombrar recursos"
  default     = "labcloud"
}

variable "vpc_cidr" {
  description = "CIDR block para la VPC"
  default     = "10.0.0.0/16"
}

variable "db_username" {
  description = "Usuario maestro de la base de datos PostgreSQL"
  type        = string
  default     = "dbadmin" # El nombre de usuario puede ser público
}

variable "db_password" {
  description = "Contraseña maestra de la base de datos"
  type        = string
  sensitive   = true
}