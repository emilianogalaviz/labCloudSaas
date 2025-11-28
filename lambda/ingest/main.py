# FORCE UPDATE: VERSION FINAL CON PROTECCION NULL
import json
import boto3
import os
import psycopg2
from datetime import datetime

# AWS Resources
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Configuración
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
TABLE_NAME = 'labcloud-billing-usage'
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def search_results(tenant_id, search_term):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {tenant_id};")
            
            if search_term:
                query = "SELECT patient_id, data, created_at FROM results WHERE patient_id LIKE %s LIMIT 10;"
                cur.execute(query, (f'%{search_term}%',))
            else:
                query = "SELECT patient_id, data, created_at FROM results ORDER BY created_at DESC LIMIT 10;"
                cur.execute(query)
            
            rows = cur.fetchall()
            results = []
            for row in rows:
                # row[1] es la columna 'data'
                raw_data = row[1]
                
                # --- PROTECCIÓN CONTRA NULOS ---
                if raw_data: 
                    try:
                        parsed_data = json.loads(raw_data)
                    except:
                        parsed_data = {"test": "Error", "result": "Datos corruptos"}
                else:
                    # SI ES NONE, ENTRA AQUÍ Y EVITA EL ERROR
                    parsed_data = {"test": "Pendiente", "result": "Procesando..."}
                # -------------------------------

                results.append({
                    "patient_id": row[0] or "Anónimo",
                    "data": parsed_data,
                    "date": str(row[2])
                })
            return results
    except Exception as e:
        print(f"Error DB: {str(e)}")
        return [] 
    finally:
        if conn: conn.close()

def record_usage(tenant_id):
    try:
        table = dynamodb.Table(TABLE_NAME)
        current_month = datetime.now().strftime('%Y-%m')
        table.update_item(
            Key={'tenant_id': tenant_id, 'month': current_month},
            UpdateExpression="ADD request_count :inc", ExpressionAttributeValues={':inc': 1}
        )
    except: pass

def handler(event, context):
    try:
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        
        # GET (BUSCAR)
        if http_method == 'GET':
            params = event.get('queryStringParameters', {})
            tenant_id = params.get('tenant_id')
            query = params.get('q', '')
            if not tenant_id: return {"statusCode": 400, "body": "Falta tenant_id"}
            data = search_results(tenant_id, query)
            return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(data)}

        # POST (GUARDAR)
        if 'body' in event: body = json.loads(event['body'])
        else: body = event
        
        tenant_id = body.get('tenant_id')
        if not tenant_id: return {"statusCode": 400, "body": "Falta tenant_id"}
        
        record_usage(tenant_id)
        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(body))
        
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"message": "Enviado"})}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}