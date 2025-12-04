# ☁️ LabCloud - SaaS Multi-Tenant para Laboratorios Clínicos

![AWS](https://img.shields.io/badge/AWS-100000?style=for-the-badge&logo=amazon&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

Plataforma "White-Label" que permite a laboratorios médicos gestionar resultados de pacientes de forma segura, escalable y aislada.

---

## 🏗️ Arquitectura

El sistema utiliza una arquitectura **Serverless y basada en Contenedores** sobre AWS, garantizando el aislamiento de datos mediante el patrón **Schema-per-Tenant**.

* **Ingesta:** API Gateway + Lambda (`/ingest`, `/register`).
* **Procesamiento:** Amazon SQS + ECS Fargate (Worker Python).
* **Almacenamiento:** Amazon RDS (PostgreSQL) con esquemas aislados y DynamoDB para facturación.
* **Frontend:** Portal Web en ECS Fargate con autenticación AWS Cognito.
* **DevOps:** CI/CD con GitHub Actions y Terraform Remote State (S3).

---

## 🚀 Despliegue (Cómo levantar el proyecto)

### Prerrequisitos
* AWS CLI configurado.
* Terraform instalado.
* Docker instalado.

### 1. Infraestructura
```bash
cd terraform
terraform init
terraform apply