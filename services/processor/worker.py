import os
import json
import time
import psycopg2
import boto3

# Configuración
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER', 'dbadmin') # Ojo con el usuario que definiste en terraform
DB_PASS = os.environ.get('DB_PASS') # Idealmente usar secrets, por ahora env var
REGION = os.environ.get('REGION', 'us-east-2')
QUEUE_URL = os.environ.get('QUEUE_URL')

# Cliente SQS para leer mensajes
sqs = boto3.client('sqs', region_name=REGION)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

def save_result(data):
    """Guarda el resultado en el esquema aislado del tenant"""
    tenant_id = data.get('tenant_id')
    patient = data.get('patient_name')
    test_type = data.get('test_type')
    result_data = data.get('result_data')

    if not tenant_id:
        print("Error: Mensaje sin Tenant ID")
        return False

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1. AISLAMIENTO: Cambiar al esquema del cliente
            # Esto es lo que evita que Pepe vea los datos de Juan
            cur.execute(f"SET search_path TO {tenant_id};")

            # 2. Insertar datos
            # Nota: La tabla 'results' se creó automáticamente cuando registraste el lab
            sql = """
                INSERT INTO results (patient_id, data, created_at)
                VALUES (%s, %s, NOW());
            """
            # Guardamos el JSON completo del resultado en la columna 'data'
            full_record = json.dumps({"test": test_type, "result": result_data})
            cur.execute(sql, (patient, full_record))
            
            conn.commit()
            print(f"✅ Guardado exitoso para: {tenant_id} - Paciente: {patient}")
            return True

    except Exception as e:
        print(f"❌ Error guardando en DB: {str(e)}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def main():
    print("👷 Worker iniciado. Esperando análisis médicos...")
    
    # Obtener URL de la cola dinámicamente si no está en env
    q_url = QUEUE_URL
    if not q_url:
        response = sqs.get_queue_url(QueueName='labcloud-results-queue')
        q_url = response['QueueUrl']

    while True:
        try:
            # 1. Leer mensajes (Long Polling)
            response = sqs.receive_message(
                QueueUrl=q_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )

            if 'Messages' in response:
                for msg in response['Messages']:
                    body = json.loads(msg['Body'])
                    print(f"📨 Mensaje recibido: {body}")
                    
                    # 2. Procesar y Guardar
                    success = save_result(body)
                    
                    # 3. Borrar de la cola si se guardó bien
                    if success:
                        sqs.delete_message(
                            QueueUrl=q_url,
                            ReceiptHandle=msg['ReceiptHandle']
                        )
            else:
                print("💤 Nada por hacer...")

        except Exception as e:
            print(f"Error en loop principal: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()