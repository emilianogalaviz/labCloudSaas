# 1. IP Elástica (Costo fijo bajo)
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "${var.project_name}-nat-eip" }
}

# 2. NAT Gateway ÚNICO (Vive en la zona A, pero sirve a todos)
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_1.id # Se pone en la pública para tener salida

  tags = { Name = "${var.project_name}-nat" }

  depends_on = [aws_internet_gateway.igw]
}

# 3. Tabla de Ruteo Privada COMPARTIDA
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = { Name = "${var.project_name}-private-rt" }
}

# 4. Asociar AMBAS subredes privadas a la misma tabla (Truco de ahorro)
resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private.id
}