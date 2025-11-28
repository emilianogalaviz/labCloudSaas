# 1. Empaquetar el código (incluyendo la librería que instalaste)
data "archive_file" "onboarding_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/onboarding"
  output_path = "${path.module}/files/onboarding.zip"
}

# 2. La Función Lambda
resource "aws_lambda_function" "onboarding" {
  filename         = data.archive_file.onboarding_zip.output_path
  function_name    = "labcloud-onboarding"
  role             = aws_iam_role.lambda_exec.arn # Reusamos el rol existente
  handler          = "main.handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.onboarding_zip.output_base64sha256
  timeout          = 15


  # IMPORTANTE: Conectar a la VPC para alcanzar la Base de Datos
  vpc_config {
    subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_group_ids = [aws_security_group.app.id]
  }

  # Pasar las credenciales de la BD
  environment {
    variables = {
      DB_HOST = replace(aws_db_instance.main.endpoint, ":5432", "")
      DB_NAME = "labcloud"
      DB_USER = aws_db_instance.main.username # Ojo: Asegúrate que coincida
      DB_PASS = var.db_password
    }
  }
}

# 3. Integración con API Gateway
resource "aws_apigatewayv2_integration" "lambda_onboarding" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.onboarding.invoke_arn
}

# 4. La Ruta Pública (POST /register)
resource "aws_apigatewayv2_route" "register" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /register"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_onboarding.id}"
}

# 5. Permiso de Invocación
resource "aws_lambda_permission" "api_gw_onboarding" {
  statement_id  = "AllowExecutionFromAPIGatewayOnboarding"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.onboarding.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}