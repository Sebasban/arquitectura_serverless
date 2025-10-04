import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

REQUIRED_KEYS = ["EventId"]  # ajusta según lo que envíes desde la Lambda A

def _normalize_event(event):

    if isinstance(event, dict):
        return event
    if isinstance(event, str):
        try:
            return json.loads(event)
        except json.JSONDecodeError:
            return {"raw": event}
    return json.loads(json.dumps(event, default=str))

def _validate_payload(payload: dict):
    missing = [k for k in REQUIRED_KEYS if k not in payload]
    return missing

def handler(event, context):
    logger.info("Payload recibido (crudo): %s", event)

    payload = _normalize_event(event)
    logger.info("Payload normalizado: %s", payload)

    # Valida campos mínimos
    missing = _validate_payload(payload)
    if missing:
        msg = {"message": "payload inválido", "missing": missing, "payload": payload}
        logger.warning(msg)
        return {"statusCode": 400, "body": json.dumps(msg)}

    # Ejemplo de uso de valores
    event_id = payload["EventId"]

    # 👉 aquí haces tu lógica de negocio
    logger.info(f"Procesando EventId={event_id})")

    item = {
            "EventId": eid,
            "EventName": body["EventName"],
            "EventDate": body["EventDate"],
            "EventStatus": body["EventStatus"],
            "EventCity": body["EventCity"],
            "NumberEntries": body["NumberEntries"]
        }
    table.put_item(Item=item)
    return {"statusCode": 200, "body": json.dumps({"message": "updated", "item": item})}