Aquí está **todo el contenido convertido a un archivo `.md`**, sin los fences de código y totalmente listo para copiar/pegar en tu archivo Markdown:

---

# ☁️ LabCloud - SaaS Multi-Tenant para Laboratorios Clínicos

![AWS](https://img.shields.io/badge/AWS-100000?style=for-the-badge\&logo=amazon\&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge\&logo=terraform\&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge\&logo=docker\&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge\&logo=python\&logoColor=ffdd54)

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

## 🚀 Despliegue (Infrastructure as Code)

### Prerrequisitos

* AWS CLI configurado (`aws configure`).
* Terraform instalado.
* Docker instalado.

### 1. Infraestructura

```bash
cd terraform
terraform init
terraform apply
```

### 2. Carga de Código (Docker)

Una vez creada la infraestructura, se deben construir y subir las imágenes a ECR.
*(Nota: Usar `--platform linux/amd64` si se construye desde Mac/Apple Silicon).*

```bash
# Backend Worker (Procesador)
cd services/processor
docker build --platform linux/amd64 -t labcloud-processor .
# Reemplazar con la URL de salida de Terraform
docker push TU_URL_ECR_PROCESSOR:latest

# Frontend Portal (Web)
cd ../portal
docker build --platform linux/amd64 -t labcloud-portal .
docker push TU_URL_ECR_PORTAL:latest
```

---

## 🧪 Uso y Endpoints

### 1. Registrar un Nuevo Laboratorio (Onboarding Automático)

Crea automáticamente el usuario administrador en Cognito y el esquema privado en RDS.

```bash
curl -X POST "https://TU_API_URL/register" \
     -H "Content-Type: application/json" \
     -d '{
           "lab_name": "Laboratorio Demo",
           "email": "admin@demo.com",
           "password": "Password123!"
         }'
```

### 2. Acceder al Portal

* **URL:** Usar la IP Pública de la tarea ECS `labcloud-portal-service`.
* **Credenciales:** Usar el email y password definidos en el registro.
* **Funcionalidad:** El portal detecta automáticamente el Tenant ID del usuario y muestra solo sus datos.

### 3. Ingresar Resultados (Simulación de Máquina)

```bash
curl -X POST "https://TU_API_URL/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "tenant_id": "lab_laboratoriodemo_xxxx",
           "patient_name": "Juan Perez",
           "test_type": "Sangre",
           "result_data": {"glucosa": 98, "colesterol": 180}
         }'
```

---

## 💰 Análisis de Costos

Esta arquitectura está optimizada para bajo costo utilizando servicios compartidos en lugar de dedicados por cliente:

| Recurso               | Costo Estimado (Mensual) | Nota                                           |
| --------------------- | ------------------------ | ---------------------------------------------- |
| **RDS (db.t3.micro)** | ~$15 USD                 | Base de datos compartida (Schema-per-Tenant).  |
| **NAT Gateway**       | ~$32 USD                 | Costo fijo por disponibilidad de red privada.  |
| **ECS Fargate**       | ~$20 USD                 | 2 Tareas corriendo 24/7 (0.25 vCPU).           |
| **Lambda/API**        | < $1 USD                 | Capa gratuita generosa (Pay-per-request).      |
| **Total Estimado**    | **~$68 USD / mes**       | Capacidad para soportar hasta 50 laboratorios. |

---

## ⚠️ Limitaciones Conocidas

1. **IP Dinámica:** El portal usa una IP pública dinámica de ECS Fargate. Para producción se recomienda **ALB + Route 53** para dominio fijo y HTTPS.
2. **Cold Starts:** Lambda puede tardar 1–2 s después de inactividad.
3. **Límite de Conexiones:** Con RDS compartido puede ser necesario un **RDS Proxy** si se superan los 100 clientes concurrentes.

---

## 🛡️ Seguridad y Compliance

* **Aislamiento de Datos:** Uso estricto de `SET search_path` para separar lógicamente los datos.
* **Red:** RDS en subred privada sin acceso a internet.
* **Identidad:** Tokens JWT validados por Cognito con atributo `custom:tenant_id`.
* **Mínimo Privilegio:** IAM roles específicos para cada servicio.

---

**Autores:** Emiliano Galaviz & José Nuñez.

---

