import json
import os
import psycopg2
import uuid
import boto3

# Variables de entorno que nos dará Terraform
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def handler(event, context):
    conn = None
    try:
        print("Evento recibido:", event)
        body = json.loads(event.get('body', '{}'))
        lab_name = body.get('lab_name')
        
        if not lab_name:
            return {"statusCode": 400, "body": "Error: Falta el campo 'lab_name'"}

        # 1. Generar ID único para el tenant (ej: lab_chopo_x9z1)
        # Limpiamos el nombre (minúsculas, sin espacios)
        clean_name = "".join(c for c in lab_name if c.isalnum()).lower()
        # Agregamos un sufijo aleatorio corto
        suffix = str(uuid.uuid4())[:4]
        tenant_id = f"lab_{clean_name}_{suffix}"

        # 2. Conectar a RDS y crear el esquema aislado
        conn = get_db_connection()
        conn.autocommit = True # Necesario para CREATE SCHEMA
        
        with conn.cursor() as cur:
            # Crear el esquema (Cajón privado del laboratorio)
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant_id};")
            
            # Crear tabla de resultados dentro de ese esquema
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {tenant_id}.results (
                    result_id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50),
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print(f"Infraestructura creada para: {tenant_id}")

        # 3. Responder con las credenciales (API Key simulada o Tenant ID)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Laboratorio registrado exitosamente",
                "lab_name": lab_name,
                "tenant_id": tenant_id, # ESTE ES EL DATO IMPORTANTE
                "status": "active"
            })
        }

    except Exception as e:
        print(f"Error crítico: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        if conn: conn.close()