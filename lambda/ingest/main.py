import json
import boto3
import os
from datetime import datetime

# Conectamos con DynamoDB
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'labcloud-billing-usage'

def record_usage(tenant_id):
    """Incrementa el contador de uso para el laboratorio"""
    table = dynamodb.Table(TABLE_NAME)
    # Obtenemos el mes actual (ej: "2023-11")
    current_month = datetime.now().strftime('%Y-%m')
    
    # Operación Atómica: Sumar +1 sin leer primero (rápido y seguro)
    table.update_item(
        Key={
            'tenant_id': tenant_id,
            'month': current_month
        },
        UpdateExpression="ADD request_count :inc",
        ExpressionAttributeValues={
            ':inc': 1
        }
    )
    print(f"Cobro registrado para: {tenant_id}")

def handler(event, context):
    try:
        print("Evento recibido:", event)
        
        # 1. Extraer datos
        # Si viene desde API Gateway, el cuerpo puede venir como string
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        tenant_id = body.get('tenant_id', 'UNKNOWN_LAB')
        
        # 2. Registrar Facturación (Billing)
        record_usage(tenant_id)
        
        # 3. Responder
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Datos recibidos y cobro registrado",
                "tenant_id": tenant_id,
                "status": "processing"
            })
        }
        
    except Exception as e:
        print(f"Error procesando: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }