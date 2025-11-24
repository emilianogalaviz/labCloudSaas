# 1. Empaquetar el código Python automáticamente en un ZIP
data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/ingest"
  output_path = "${path.module}/files/ingest.zip"
}

# 2. La Función Lambda (El portero)
resource "aws_lambda_function" "ingest" {
  filename         = data.archive_file.ingest_zip.output_path
  function_name    = "labcloud-ingest"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "main.handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.ingest_zip.output_base64sha256

  # Le pasamos la URL de la cola como variable de entorno
  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.lab_results.url
    }
  }
}

# 3. API Gateway (Tipo HTTP - Más barato y rápido)
resource "aws_apigatewayv2_api" "main" {
  name          = "labcloud-api"
  protocol_type = "HTTP"
  
  # Configuración CORS (Para que funcione desde el navegador)
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
  }
}

# 4. Integración (Conectar la API con la Lambda)
resource "aws_apigatewayv2_integration" "lambda_ingest" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.ingest.invoke_arn
}

# 5. Ruta (Endpoint: POST /ingest)
resource "aws_apigatewayv2_route" "ingest" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /ingest"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_ingest.id}"
}

# 6. Stage (Despliegue automático)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}

# 7. Permiso final (Dejar que la API invoque a la Lambda)
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Output: Nos dará la URL final para probar
output "api_endpoint" {
  value = aws_apigatewayv2_api.main.api_endpoint
}