import json
import os
import psycopg2
import uuid
import boto3

# Configuración de DB
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'labcloud')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

# Configuración Cognito (REEMPLAZA CON TU ID REAL SI NO USAS VAR DE ENTORNO)
# Puedes ver este ID en la consola de Cognito -> User Pools
USER_POOL_ID = os.environ.get('USER_POOL_ID', 'us-east-2_XXXXXXXXX') 

cognito = boto3.client('cognito-idp')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def create_cognito_user(email, password, tenant_id):
    """Crea el usuario en Cognito y le asigna el Tenant ID"""
    try:
        response = cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'custom:tenant_id', 'Value': tenant_id} # <--- LA MAGIA
            ],
            MessageAction='SUPPRESS' # No enviar email de bienvenida (para esta demo)
        )
        
        # Asignar contraseña permanente
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=password,
            Permanent=True
        )
        print(f"Usuario Cognito creado: {email} para Tenant: {tenant_id}")
        return True
    except Exception as e:
        print(f"Error creando usuario Cognito: {str(e)}")
        raise e

def handler(event, context):
    conn = None
    try:
        body = json.loads(event.get('body', '{}'))
        lab_name = body.get('lab_name')
        admin_email = body.get('email')     # Nuevo campo
        admin_pass = body.get('password')   # Nuevo campo
        
        if not all([lab_name, admin_email, admin_pass]):
            return {"statusCode": 400, "body": "Faltan datos (lab_name, email, password)"}

        # 1. Generar Tenant ID
        clean_name = "".join(c for c in lab_name if c.isalnum()).lower()
        suffix = str(uuid.uuid4())[:4]
        tenant_id = f"lab_{clean_name}_{suffix}"

        # 2. Crear BD Schema (Infraestructura)
        conn = get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant_id};")
            cur.execute(f"CREATE TABLE IF NOT EXISTS {tenant_id}.results (id SERIAL PRIMARY KEY, data TEXT);")

        # 3. Crear Usuario Cognito (Acceso)
        create_cognito_user(admin_email, admin_pass, tenant_id)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Laboratorio y Usuario Administrador creados",
                "tenant_id": tenant_id,
                "admin_user": admin_email,
                "login_url": "PUEDES_PONER_TU_IP_DEL_PORTAL_AQUI"
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}
    finally:
        if conn: conn.close()