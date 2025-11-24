resource "aws_db_instance" "main" {
  identifier           = "${var.project_name}-main-db"
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "16.6"
  instance_class       = "db.t3.micro" # MODO AHORRO (Gratuita elegible)
  db_name              = "labcloud"
  username             = var.db_username
  password             = var.db_password # Ahora usa la variable
  db_subnet_group_name = aws_db_subnet_group.main.name
  skip_final_snapshot  = true
  publicly_accessible  = false # ¡CRÍTICO! Nunca expongas la DB

  # REFERENCIA CRÍTICA: Esto fallará si Emiliano no ha fusionado el security.tf
  vpc_security_group_ids = [aws_security_group.db.id]

  tags = {
    Name = "LabCloud-Postgres"
  }
}