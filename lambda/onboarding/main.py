import json
import os
import psycopg2
import uuid
import boto3

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def handler(event, context):
    conn = None
    try:
        body = json.loads(event.get('body', '{}'))
        lab_name = body.get('lab_name')
        
        # Generar ID
        clean_name = "".join(c for c in lab_name if c.isalnum()).lower()[:10]
        suffix = str(uuid.uuid4())[:4]
        tenant_id = f"lab_{clean_name}_{suffix}"

        conn = get_db_connection()
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # 1. Crear Esquema
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant_id};")
            
            # 2. CREAR TABLA CORRECTA (Con columna patient_id)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {tenant_id}.results (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(100),  -- <--- ESTA ES LA COLUMNA QUE FALTABA
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print(f"Infraestructura creada para: {tenant_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Laboratorio registrado exitosamente",
                "tenant_id": tenant_id,
                "status": "active"
            })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        if conn: conn.close()