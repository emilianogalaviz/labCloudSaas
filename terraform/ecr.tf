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

# --- Repositorio para el Portal Web (Frontend) ---
resource "aws_ecr_repository" "portal" {
  name                 = "labcloud-portal"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "LabCloud-Portal-Repo"
  }
}

# Output para saber dónde subir el Docker del portal después
output "ecr_portal_url" {
  value = aws_ecr_repository.portal.repository_url
}