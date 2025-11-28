import os
import json
import time
import psycopg2
from psycopg2 import sql
import boto3

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER', 'dbadmin')
DB_PASS = os.environ.get('DB_PASS')
REGION = os.environ.get('REGION', 'us-east-2')
QUEUE_URL = os.environ.get('QUEUE_URL')

sqs = boto3.client('sqs', region_name=REGION)

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)


def ensure_tenant_schema(cur, tenant_id):
    """Crea el esquema del tenant (si no existe) y lo selecciona de forma segura."""

    # Crear el esquema sin riesgo de inyección
    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema};").format(schema=sql.Identifier(tenant_id)))

    # Fijar el search_path del tenant y conservar public como fallback
    cur.execute(
        sql.SQL("SET search_path TO {schema}, public;").format(schema=sql.Identifier(tenant_id))
    )

def ensure_results_table(cur):
    """Garantiza que la tabla results tenga la columna patient_id.

    Algunos clientes antiguos fueron creados antes de agregar el campo
    patient_id, lo que provoca errores al insertar. Este bloque crea la
    tabla si falta y agrega la columna cuando no existe.
    """
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id SERIAL PRIMARY KEY,
            patient_id VARCHAR(100),
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'results'
                  AND column_name = 'patient_id'
            ) THEN
                ALTER TABLE results ADD COLUMN patient_id VARCHAR(100);
            END IF;
        END $$;
        """
    )

def save_result(data):
    tenant_id = data.get('tenant_id')
    patient = data.get('patient_name') or 'Desconocido'
    json_data = json.dumps(data)

    if not tenant_id: return False

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            ensure_tenant_schema(cur, tenant_id)

            # Aseguramos que la tabla tenga la columna patient_id
            ensure_results_table(cur)

            # Insertamos explícitamente en patient_id
            sql = """
                INSERT INTO results (patient_id, data, created_at)
                VALUES (%s, %s, NOW());
            """
            cur.execute(sql, (patient, json_data))
            
            conn.commit()
            print(f"✅ Guardado: {tenant_id}")
            return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def main():
    print("👷 Worker v4.0 Corrección de Tablas...")
    q_url = QUEUE_URL
    if not q_url:
        try:
            response = sqs.get_queue_url(QueueName='labcloud-results-queue')
            q_url = response['QueueUrl']
        except: pass

    while True:
        try:
            if q_url:
                response = sqs.receive_message(QueueUrl=q_url, MaxNumberOfMessages=1, WaitTimeSeconds=20)
                if 'Messages' in response:
                    for msg in response['Messages']:
                        body = json.loads(msg['Body'])
                        if save_result(body):
                            sqs.delete_message(QueueUrl=q_url, ReceiptHandle=msg['ReceiptHandle'])
            else:
                time.sleep(5)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    main()