# --- Security Group para la Aplicación (Frontend/Lambda) ---
resource "aws_security_group" "app" {
  name        = "labcloud-app-sg"
  description = "Security Group para la aplicacion web y lambdas"
  vpc_id      = aws_vpc.main.id

  # Regla de Entrada: Permitir HTTP (Puerto 80) desde cualquier lugar
  ingress {
    description = "Acceso HTTP desde Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Regla de Entrada: Permitir HTTPS (Puerto 443) desde cualquier lugar
  ingress {
    description = "Acceso HTTPS desde Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Regla de Salida: Permitir TODO el tráfico de salida (necesario para descargar cosas)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "LabCloud-App-SG"
  }
}

# --- Security Group para la Base de Datos (Backend) ---
resource "aws_security_group" "db" {
  name        = "labcloud-db-sg"
  description = "Security Group para la base de datos RDS"
  vpc_id      = aws_vpc.main.id

  # Regla de Entrada: Permitir PostgreSQL (5432) SOLO desde el grupo "app"
  ingress {
    description     = "Acceso PostgreSQL solo desde la App"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id] # <--- AQUI ESTA LA SEGURIDAD
  }

  tags = {
    Name = "LabCloud-DB-SG"
  }
}