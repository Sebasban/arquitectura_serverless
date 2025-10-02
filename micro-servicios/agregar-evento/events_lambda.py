import os
import json
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def _body(event):
    b = event.get("body")
    return json.loads(b) if b else {}

def _event_id(event, body):
    # Prioridad: path -> query -> body -> nuevo uuid (solo POST)
    pid = (event.get("pathParameters") or {}).get("eventId") or (event.get("pathParameters") or {}).get("EventId")
    if not pid:
        pid = (event.get("queryStringParameters") or {}).get("eventId") or (event.get("queryStringParameters") or {}).get("EventId")
    if not pid:
        pid = body.get("EventId")
    return pid

def lambda_handler(event, context):
    method = (event.get("httpMethod") or "").upper()

    if method == "POST":
        body = _body(event)
        # Requiere estos campos (simple y explícito)
        for k in ["EventName", "EventDate", "EventStatus", "EventCity"]:
            if k not in body:
                return {"statusCode": 400, "body": json.dumps({"message": f"Falta {k}"})}
        eid = body.get("EventId") or str(uuid.uuid4())
        item = {
            "EventId": eid,
            "EventName": body["EventName"],
            "EventDate": body["EventDate"],
            "EventStatus": body["EventStatus"],
            "EventCity": body["EventCity"],
        }
        table.put_item(Item=item)
        return {"statusCode": 201, "body": json.dumps({"message": "created", "item": item})}

    if method == "GET":
        body = _body(event)
        eid = _event_id(event, body)
        if not eid:
            return {"statusCode": 400, "body": json.dumps({"message": "EventId requerido"})}
        resp = table.get_item(Key={"EventId": eid})
        item = resp.get("Item")
        if not item:
            return {"statusCode": 404, "body": json.dumps({"message": "not found", "EventId": eid})}
        return {"statusCode": 200, "body": json.dumps(item)}

    if method == "PUT":
        # PUT reemplaza completamente el ítem (más simple).
        body = _body(event)
        eid = _event_id(event, body)
        if not eid:
            return {"statusCode": 400, "body": json.dumps({"message": "EventId requerido"})}
        for k in ["EventName", "EventDate", "EventStatus", "EventCity"]:
            if k not in body:
                return {"statusCode": 400, "body": json.dumps({"message": f"Falta {k}"})}
        item = {
            "EventId": eid,
            "EventName": body["EventName"],
            "EventDate": body["EventDate"],
            "EventStatus": body["EventStatus"],
            "EventCity": body["EventCity"],
        }
        table.put_item(Item=item)
        return {"statusCode": 200, "body": json.dumps({"message": "updated", "item": item})}

    if method == "DELETE":
        body = _body(event)
        eid = _event_id(event, body)
        if not eid:
            return {"statusCode": 400, "body": json.dumps({"message": "EventId requerido"})}
        table.delete_item(Key={"EventId": eid})
        return {"statusCode": 200, "body": json.dumps({"message": "deleted", "EventId": eid})}

    return {"statusCode": 405, "body": json.dumps({"message": "Método no permitido"})}
