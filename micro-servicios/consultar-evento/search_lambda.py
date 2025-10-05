import os
import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        # Obtener parámetros del request a través de Query Params
        query_params = event.get('queryStringParameters', {}) or {}
        event_name = query_params.get('EventName')

        if not event_name:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Falta el parámetro 'EventName' en la consulta"
                })
            }

        # Buscar por nombre del evento (Scan con filtro)
        response = table.scan(
            FilterExpression=Attr('EventName').eq(event_name)
        )
        items = response.get('Items', [])

        # Validar si se encontraron resultados
        if not items:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "message": f"No se encontró ningún evento con nombre '{event_name}'"
                })
            }

        # Responder con los eventos encontrados
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Evento encontrado correctamente",
                "data": items
            })
        }

    except Exception as e:
        print("Error en búsqueda:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error interno al buscar el evento",
                "error": str(e)
            })
        }