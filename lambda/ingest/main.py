import json
import boto3
import os
from datetime import datetime

# Recursos AWS
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Variables de Entorno
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
TABLE_NAME = 'labcloud-billing-usage'

def record_usage(tenant_id):
    """Cobra 1 crédito al laboratorio"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        current_month = datetime.now().strftime('%Y-%m')
        table.update_item(
            Key={'tenant_id': tenant_id, 'month': current_month},
            UpdateExpression="ADD request_count :inc",
            ExpressionAttributeValues={':inc': 1}
        )
    except Exception as e:
        print(f"Error billing: {str(e)}")

def handler(event, context):
    try:
        print("Evento recibido:", event)
        body = json.loads(event.get('body', '{}'))
        tenant_id = body.get('tenant_id')

        if not tenant_id:
            return {"statusCode": 400, "body": "Falta tenant_id"}

        # 1. Billing (Cobrar)
        record_usage(tenant_id)

        # 2. Enviar a la Cola SQS (Para que el Worker lo guarde en DB)
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(body) # Enviamos todo el paquete (paciente, resultados, etc)
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" # Importante para que el navegador no se queje
            },
            "body": json.dumps({"message": "Procesando y guardando datos..."})
        }

    except Exception as e:
        print(f"Error critico: {str(e)}")
        return {"statusCode": 500, "body": str(e)}