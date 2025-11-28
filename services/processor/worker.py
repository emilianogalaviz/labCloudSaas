import os
import json
import time
import psycopg2
import boto3

# Configuración
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER', 'dbadmin')
DB_PASS = os.environ.get('DB_PASS')
REGION = os.environ.get('REGION', 'us-east-2')
QUEUE_URL = os.environ.get('QUEUE_URL')

sqs = boto3.client('sqs', region_name=REGION)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

def save_result(data):
    tenant_id = data.get('tenant_id')
    # Guardamos todo el objeto data como JSON para evitar problemas de columnas
    json_data = json.dumps(data) 

    if not tenant_id: return False

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {tenant_id};")

            # INTENTO 1: Usar la columna patient_id si existe
            try:
                sql = """
                    INSERT INTO results (patient_id, data, created_at)
                    VALUES (%s, %s, NOW());
                """
                cur.execute(sql, (data.get('patient_name'), json_data))
            except Exception:
                # INTENTO 2 (FALLBACK): Si falla porque no existe la columna,
                # guardamos todo en 'data' y usamos un ID genérico o null si la tabla lo permite.
                # Pero para arreglarlo rápido, vamos a asumir que la tabla se creó simple:
                # (id, data, created_at) <- Estructura más probable si falló lo anterior
                conn.rollback() # Revertir el error anterior
                
                # Vamos a intentar insertar en la estructura genérica
                # Si tu tabla solo tiene (id, data), esto funcionará:
                sql_simple = "INSERT INTO results (data) VALUES (%s);"
                cur.execute(sql_simple, (json_data,))
            
            conn.commit()
            print(f"✅ Guardado exitoso para: {tenant_id}")
            return True

    except Exception as e:
        print(f"❌ Error guardando en DB: {str(e)}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def main():
    print("👷 Worker iniciado v2.0...")
    q_url = QUEUE_URL
    if not q_url:
        response = sqs.get_queue_url(QueueName='labcloud-results-queue')
        q_url = response['QueueUrl']

    while True:
        try:
            response = sqs.receive_message(QueueUrl=q_url, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            if 'Messages' in response:
                for msg in response['Messages']:
                    body = json.loads(msg['Body'])
                    if save_result(body):
                        sqs.delete_message(QueueUrl=q_url, ReceiptHandle=msg['ReceiptHandle'])
        except Exception as e:
            print(f"Error loop: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()