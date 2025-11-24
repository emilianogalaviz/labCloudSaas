resource "aws_sqs_queue" "lab_results" {
  name                       = "labcloud-results-queue"
  message_retention_seconds  = 86400 # 1 día de retención
  visibility_timeout_seconds = 30    # Tiempo para procesar

  tags = {
    Name = "LabResultsQueue"
  }
}

output "sqs_url" {
  value = aws_sqs_queue.lab_results.url
}

output "sqs_arn" {
  value = aws_sqs_queue.lab_results.arn
}