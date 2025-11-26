# Rol de ejecución básica (Permite que el servicio Lambda asuma este rol)
resource "aws_iam_role" "lambda_exec" {
  name = "labcloud-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Permiso 1: Logs en CloudWatch (Para ver errores)
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permiso 2: Enviar mensajes a la cola SQS (Específico para tu cola)
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "labcloud-lambda-sqs-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.lab_results.arn
    }]
  })
}

# --- Permiso NUEVO para que la Lambda pueda entrar a la VPC ---
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}