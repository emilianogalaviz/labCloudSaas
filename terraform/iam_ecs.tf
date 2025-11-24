# 1. Rol de Ejecución (Execution Role)
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "labcloud-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# 2. Adjuntar política oficial de AWS
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 3. Grupo de Logs en CloudWatch
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/labcloud-processor"
  retention_in_days = 7
}