# 1. La Tabla de Facturación (NoSQL)
resource "aws_dynamodb_table" "billing" {
  name           = "labcloud-billing-usage"
  billing_mode   = "PAY_PER_REQUEST" # Importante: Capa gratuita amigable
  hash_key       = "tenant_id"       # Clave principal (Quién paga)
  range_key      = "month"           # Clave de ordenamiento (Cuándo)

  attribute {
    name = "tenant_id"
    type = "S" # String
  }

  attribute {
    name = "month"
    type = "S" # String
  }

  tags = {
    Name = "LabCloud-Billing"
  }
}

# 2. Permiso para que la Lambda pueda escribir en esta tabla
resource "aws_iam_role_policy" "lambda_billing_policy" {
  name = "labcloud-lambda-billing-policy"
  role = aws_iam_role.lambda_exec.id # Usamos el rol que ya creaste en la etapa anterior

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:UpdateItem",
        "dynamodb:GetItem"
      ]
      Resource = aws_dynamodb_table.billing.arn
    }]
  })
}