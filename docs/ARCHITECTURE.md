# LabCloud - Arquitectura de Plataforma SaaS Multi-Tenant

## 1. Visión General
LabCloud es una plataforma SaaS diseñada para laboratorios médicos que permite la gestión aislada de resultados de pacientes. La arquitectura sigue el modelo **Multi-Tenant** con aislamiento físico a nivel de esquema de base de datos (Schema-per-Tenant), garantizando que los datos de un laboratorio sean inaccesibles para otros.

## 2. Diagrama de Arquitectura (Alto Nivel)

```mermaid
graph TD
    User([Cliente / Laboratorio]) -->|HTTPS| APIGW[API Gateway]
    User -->|HTTPS| Portal[Portal Web (ECS Fargate)]
    
    subgraph "Capa de Ingesta & Auth"
        APIGW -->|/register| LambdaOnboard[Lambda: Onboarding]
        APIGW -->|/ingest| LambdaIngest[Lambda: Ingesta]
        Portal -->|Auth| Cognito[AWS Cognito]
    end
    
    subgraph "Capa de Procesamiento Async"
        LambdaIngest -->|Billing +1| DDB[DynamoDB: Billing]
        LambdaIngest -->|JSON| SQS[Amazon SQS]
        SQS -->|Pull| Worker[ECS Fargate: Worker]
    end
    
    subgraph "Capa de Datos Aislada"
        LambdaOnboard -->|Create Schema| RDS[(RDS PostgreSQL)]
        Worker -->|SET search_path| RDS
        Portal -->|Read Data| RDS
    end
```

## 3. Componentes Principales

### A. Capa de Acceso y Frontend
* **API Gateway (HTTP API):** Punto de entrada único para todas las operaciones (`/register`, `/ingest`, `/results`).
* **ECS Fargate (Portal):** Servidor web Nginx que sirve la aplicación SPA (Single Page Application). Autentica usuarios y muestra dashboards personalizados.
* **AWS Cognito:** Gestiona la identidad de los usuarios. Utiliza **Custom Attributes** para inyectar el `tenant_id` en el token JWT, vinculando al usuario con su laboratorio.

### B. Capa de Lógica y Procesamiento
* **Lambda (Onboarding):** Automatiza el alta de clientes.
    * Crea el usuario administrador en Cognito.
    * Ejecuta DDL (`CREATE SCHEMA`) en RDS para crear el espacio aislado.
* **Lambda (Ingest/Search):**
    * **Escritura:** Valida datos, registra cobro en DynamoDB y envía a SQS.
    * **Lectura:** Consulta resultados en RDS usando el `tenant_id`.
* **ECS Fargate (Worker):** Procesador de fondo (Python) que lee de SQS y guarda en la base de datos de manera asíncrona. Implementa lógica de **Self-Healing** para crear tablas si no existen.

### C. Capa de Datos (Multi-Tenancy)
* **Amazon RDS (PostgreSQL):** Base de datos relacional principal.
    * **Estrategia de Aislamiento:** Schema-per-Tenant.
    * Cada laboratorio tiene su propio esquema (`lab_chopo`, `lab_salud`).
    * El acceso se controla dinámicamente con `SET search_path TO tenant_id`.
* **DynamoDB (Billing):** Base de datos NoSQL para métricas de facturación. Almacena contadores atómicos de uso por tenant.

## 4. Flujos Críticos

### Flujo de Onboarding (Alta de Cliente)
1.  Cliente envía `POST /register` con nombre y correo.
2.  Lambda genera un `tenant_id` único.
3.  Lambda conecta a RDS y crea un **Schema** dedicado.
4.  Lambda conecta a Cognito y crea el usuario Admin con el `tenant_id` incrustado.

### Flujo de Ingesta de Datos (Aislamiento)
1.  Cliente envía datos a `POST /ingest`.
2.  Lambda registra +1 en DynamoDB (Billing).
3.  Lambda pone el mensaje en SQS.
4.  **Worker ECS** toma el mensaje.
5.  Worker extrae el `tenant_id` y ejecuta `SET search_path TO [tenant_id]`.
6.  Worker inserta los datos. **Resultado:** El dato solo existe en el esquema privado del cliente.

## 5. Decisiones de Diseño

| Decisión | Opción Elegida | Justificación |
| :--- | :--- | :--- |
| **Aislamiento** | Schema-per-Tenant (Postgres) | Balance ideal entre seguridad (datos separados físicamente) y costo (una sola instancia RDS para todos). |
| **Cómputo** | Híbrido (Lambda + ECS) | Lambda para tareas cortas/rápidas (API) y ECS Fargate para procesos de larga duración o contenedores web (Worker/Portal). |
| **Billing** | DynamoDB | Escrituras extremadamente rápidas y baratas para contadores de alto volumen. |
| **Infraestructura** | Terraform (IaC) | Permite replicar todo el entorno en minutos y gestionar cambios mediante CI/CD. |

## 6. Seguridad y Red
* **VPC:** Toda la computación ocurre dentro de una VPC privada.
* **Security Groups:** La Base de Datos RDS **no tiene acceso público**. Solo acepta conexiones desde el Security Group de la Aplicación (Lambda/ECS).
* **Encriptación:** Datos en reposo encriptados en RDS y S3.

graph TD
    Client["Laboratory Client"] -->|HTTPS POST| APIGW["API Gateway"]
    
    subgraph Public ["Public Zone"]
        APIGW
        Portal["Patient Portal (ECS Fargate)"]
    end

    subgraph Ingestion ["Ingestion Layer (Serverless)"]
        APIGW -->|Trigger| IngestLambda["Lambda Ingest"]
        APIGW -->|Trigger| OnboardLambda["Lambda Onboarding"]
        IngestLambda -->|Write Usage| DynamoDB[("DynamoDB Billing")]
        IngestLambda -->|Queue Data| SQS["SQS Queue"]
    end

    subgraph Private ["Private Processing Layer (VPC)"]
        SQS -->|Pull| Worker["ECS Worker (Python)"]
        Worker -->|Store Data| RDS[("RDS PostgreSQL")]
        OnboardLambda -->|Create Schema| RDS
    end

    subgraph Security ["Security & Management"]
        Cognito["Amazon Cognito"] -->|Auth| Portal
        ECR["ECR Registry"] -->|Docker Images| Worker
        ECR -->|Docker Images| Portal
    end