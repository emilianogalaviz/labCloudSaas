import json
import os
import psycopg2
import uuid
import boto3

# Configuración
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
USER_POOL_ID = os.environ.get('USER_POOL_ID') # ¡Importante!

cognito = boto3.client('cognito-idp')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def create_cognito_user(email, password, tenant_id):
    """Crea el usuario en Cognito y le asigna el Tenant ID"""
    try:
        # 1. Crear usuario
        cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'custom:tenant_id', 'Value': tenant_id}
            ],
            MessageAction='SUPPRESS'
        )
        # 2. Poner contraseña permanente
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=password,
            Permanent=True
        )
        print(f"Usuario Cognito creado: {email}")
    except Exception as e:
        print(f"Error Cognito: {str(e)}")
        raise e

def handler(event, context):
    conn = None
    try:
        body = json.loads(event.get('body', '{}'))
        lab_name = body.get('lab_name')
        email = body.get('email')
        password = body.get('password')
        
        # Validación básica
        if not all([lab_name, email, password]):
            return {"statusCode": 400, "body": "Faltan datos: lab_name, email, password"}

        # Generar ID del tenant
        clean_name = "".join(c for c in lab_name if c.isalnum()).lower()[:10]
        suffix = str(uuid.uuid4())[:4]
        tenant_id = f"lab_{clean_name}_{suffix}"

        # 1. Crear BD (Schema)
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant_id};")
            # Crear la tabla con la estructura correcta
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {tenant_id}.results (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(100),
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

        # 2. Crear Usuario en Cognito (ESTA ES LA PARTE QUE FALTABA)
        if USER_POOL_ID:
            create_cognito_user(email, password, tenant_id)
        else:
            return {"statusCode": 500, "body": "Error: USER_POOL_ID no configurado en Lambda"}

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Laboratorio y Usuario Administrador creados", # Mensaje NUEVO
                "tenant_id": tenant_id,
                "status": "active"
            })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        if conn: conn.close()