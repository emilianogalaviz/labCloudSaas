resource "aws_db_subnet_group" "main" {
  name = "${var.project_name}-db-sng"
  # Referencia las subredes que Emiliano definió en vpc.tf
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "${var.project_name}-db-sng"
  }
}