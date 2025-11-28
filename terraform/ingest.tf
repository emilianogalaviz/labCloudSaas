data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/ingest"
  output_path = "${path.module}/files/ingest.zip"
}


resource "aws_apigatewayv2_api" "main" {
  name          = "labcloud-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
  }
}

resource "aws_lambda_function" "ingest" {
  filename         = data.archive_file.ingest_zip.output_path
  function_name    = "labcloud-ingest"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "main.handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.ingest_zip.output_base64sha256
  timeout          = 10

  # Conectar a la VPC para ver la Base de Datos
  vpc_config {
    subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_group_ids = [aws_security_group.app.id]
  }

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.lab_results.url
      # Nuevas variables para LEER datos
      DB_HOST = replace(aws_db_instance.main.endpoint, ":5432", "")
      DB_NAME = "labcloud"
      DB_USER = aws_db_instance.main.username
      DB_PASS = var.db_password
    }
  }
}

# --- RUTAS DE API GATEWAY ---

# 1. Ruta de Escritura (Ya existía)
resource "aws_apigatewayv2_integration" "lambda_ingest" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.ingest.invoke_arn
}

resource "aws_apigatewayv2_route" "ingest" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /ingest"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_ingest.id}"
}

# 2. NUEVA Ruta de Lectura (Buscar)
resource "aws_apigatewayv2_route" "read_results" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /results" # <--- Nueva ruta
  target    = "integrations/${aws_apigatewayv2_integration.lambda_ingest.id}"
}

# Permisos
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Output
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.main.api_endpoint
}