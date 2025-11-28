import os
import json
import time
import psycopg2
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

def save_result(data):
    tenant_id = data.get('tenant_id')
    patient = data.get('patient_name') or 'Desconocido'
    json_data = json.dumps(data)

    if not tenant_id: return False

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {tenant_id};")
            
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