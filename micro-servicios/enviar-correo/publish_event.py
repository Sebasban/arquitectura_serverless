import os
import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Inicializar recursos AWS
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
sqs = boto3.client("sqs")
queue_url = 'https://sqs.us-east-1.amazonaws.com/200093566387/QueueMailsBuy'  # puedes moverlo a env var si prefieres

def _body(event):
    b = event.get("body")
    return json.loads(b) if b else {}

def lambda_handler(event, context):
    method = (event.get("httpMethod") or "").upper()

    if method != "PUT":
        return {"statusCode": 405, "body": json.dumps({"message": "Método no permitido"})}

    body = _body(event)

    if "EventName" not in body or "NumberEntries" not in body or "Email" not in body:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Se requieren 'EventName' y 'NumberEntries' y 'Email'"})
        }

    event_name = body["EventName"]
    entries_requested = int(body["NumberEntries"]) 
    email = str(body["Email"])

    # Buscar evento por EventName (índice secundario)
    try:
        response = table.query(
            IndexName="EventNameIndex",
            KeyConditionExpression=Key("EventName").eq(event_name)
        )
        items = response.get("Items", [])
        if not items:
            return {"statusCode": 404, "body": json.dumps({"message": "Evento no encontrado"})}
        event_item = items[0]
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": "Error al buscar evento", "error": str(e)})}

    # Validar fecha del evento
    try:
        event_date = datetime.fromisoformat(event_item["EventDate"])
        now = datetime.utcnow()

        if now >= event_date:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "No se pueden comprar entradas: el evento ya ocurrió."})
            }

        current_entries = int(event_item["NumberEntries"])
        if entries_requested > current_entries:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": f"No hay suficientes entradas disponibles. Quedan {current_entries}."})
            }

        remaining_entries = current_entries - entries_requested

        # Actualizar NumberEntries
        table.update_item(
            Key={"EventId": event_item["EventId"]},
            UpdateExpression="SET NumberEntries = :ne",
            ExpressionAttributeValues={":ne": remaining_entries}
        )

        # Si se agotaron, actualizar estado
        if remaining_entries == 0:
            table.update_item(
                Key={"EventId": event_item["EventId"]},
                UpdateExpression="SET EventStatus = :es",
                ExpressionAttributeValues={":es": "Agotado"}
            )

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": "Error de validación", "error": str(e)})}

    # Enviar a SQS
    try:
        message = {
            "EventId": event_item["EventId"],
            "EventName": event_item["EventName"],
            "EntradasCompradas": entries_requested,
            "Email": email
        }

        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'TipoEvento': {
                    'StringValue': 'CompraEntradas',
                    'DataType': 'String'
                }
            }
        )

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": "Error al enviar a SQS", "error": str(e)})}

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Compra realizada con éxito.",
            "eventId": event_item["EventId"],
            "eventName": event_item["EventName"],
            "compradas": entries_requested,
            "restantes": event_item["Email"]
        })
    }
