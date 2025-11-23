# --- Pool de Usuarios (Pacientes) ---
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-user-pool"

  # Configuración de contraseña (Rúbrica de seguridad)
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  # Atributos estándar requeridos
  auto_verified_attributes = ["email"]
  
  # ATRIBUTO PERSONALIZADO PARA MULTI-TENANCY (CRÍTICO)
  schema {
    name                     = "tenant_id"
    attribute_data_type      = "String"
    mutable                  = false
    required                 = false # Cognito no permite 'true' fácil para custom attrs al inicio
    developer_only_attribute = false
    string_attribute_constraints {
      min_length = 1
      max_length = 20
    }
  }

  tags = {
    Name = "LabCloud-Cognito-Pool"
  }
}

# --- Cliente de Aplicación (Para que el Frontend se conecte) ---
resource "aws_cognito_user_pool_client" "client" {
  name = "${var.project_name}-app-client"

  user_pool_id = aws_cognito_user_pool.main.id
  
  # No generamos secreto porque es para una App Web (Javascript)
  generate_secret = false
  
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
}