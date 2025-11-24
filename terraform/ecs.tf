# 1. El Cluster Fargate
resource "aws_ecs_cluster" "main" {
  name = "labcloud-cluster"

  tags = {
    Name = "LabCloud-Cluster"
  }
}

# 2. La Definición de la Tarea (La "receta" del contenedor)
resource "aws_ecs_task_definition" "processor" {
  family                   = "labcloud-processor-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256 # 0.25 vCPU (Lo mínimo para ahorrar $)
  memory                   = 512 # 512 MB RAM

  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([{
    name      = "processor"
    image     = "${aws_ecr_repository.main.repository_url}:latest" # Apunta al repo creado en ecr.tf
    essential = true
    
    # Variables de entorno para que el código sepa dónde conectarse
    # (Estas referencias funcionarán porque Emiliano ya creó la DB)
    environment = [
      { name = "DB_HOST", value = replace(aws_db_instance.main.endpoint, ":5432", "") },
      { name = "DB_NAME", value = "labcloud" },
      { name = "REGION",  value = var.aws_region }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}
# --- El Servicio (El que mantiene al worker vivo) ---
resource "aws_ecs_service" "worker" {
  name            = "labcloud-worker-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.processor.arn
  desired_count   = 1 # Solo 1 para ahorrar dinero (Free Tier friendly-ish)
  launch_type     = "FARGATE"

  # Configuración de Red (¡CRÍTICO!)
  # Lo ponemos en la red privada para que nadie de internet lo toque directo
  # Pero usará el NAT Gateway que creó Emiliano para salir a buscar trabajos a SQS
  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.app.id] # Reusamos el SG de la App
    assign_public_ip = false
  }
}