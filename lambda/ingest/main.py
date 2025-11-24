import json

def handler(event, context):
    print("Evento recibido:", json.dumps(event))
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Datos recibidos correctamente en LabCloud"})
    }