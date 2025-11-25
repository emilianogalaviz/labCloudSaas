terraform {
  backend "s3" {
    # REEMPLAZA ESTO CON EL NOMBRE DE TU BUCKET DEL PASO 1
    bucket         = "computing-labcloud-state-2201" 
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-2"
    
    # REEMPLAZA CON EL NOMBRE DE TU TABLA DEL PASO 1
    dynamodb_table = "labcloud-terraform-locks"
    encrypt        = true
  }
}