resource "aws_ecr_repository" "main" {
  name                 = "labcloud-processor"
  image_tag_mutability = "MUTABLE"

  # Escaneo de vulnerabilidades básico (Punto extra en seguridad)
  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "LabCloud-Repo"
  }
}

# Exportamos la URL para usarla luego en el script de despliegue
output "ecr_repository_url" {
  value = aws_ecr_repository.main.repository_url
}