import os
import json
import time
import psycopg2
import boto3
from datetime import datetime

# Configuraciones desde Variables de Entorno (que definimos en ecs.tf)
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER', 'dbadmin') # O el usuario que pusiste en rds.tf
DB_PASS = os.environ.get('DB_PASS', 'password123') # Ojo aquí, idealmente usar Secrets Manager
REGION = os.environ.get('REGION', 'us-east-2')
QUEUE_URL = os.environ.get('QUEUE_URL')

sqs = boto3.client('sqs', region_name=REGION)

def connect_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def process_message(message):
    try:
        body = json.loads(message['Body'])
        print(f"Procesando resultado para paciente: {body.get('patient_id')}")
        
        # Lógica Multi-Tenant: Insertar en la tabla correcta
        # Aquí iría tu lógica real de inserción en SQL
        # conn = connect_db()
        # ... hacer insert ...
        # conn.close()
        
        return True
    except Exception as e:
        print(f"Error procesando mensaje: {str(e)}")
        return False

def main():
    print("Iniciando Worker de LabCloud...")
    while True:
        try:
            # 1. Leer de SQS
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )
            
            if 'Messages' in response:
                for msg in response['Messages']:
                    success = process_message(msg)
                    if success:
                        # 2. Borrar de SQS si se procesó bien
                        sqs.delete_message(
                            QueueUrl=QUEUE_URL,
                            ReceiptHandle=msg['ReceiptHandle']
                        )
            else:
                print("No hay mensajes, esperando...")
                
        except Exception as e:
            print(f"Error en el ciclo principal: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()