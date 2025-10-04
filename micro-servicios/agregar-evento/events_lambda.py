import os
import json
import uuid
import boto3
import time


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
scheduler = boto3.client("scheduler")

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
        try:
            schedule_name = f"test-schedule-{int(time.time())}"
            scheduler.create_schedule(
                Name=schedule_name,
                ScheduleExpression="at(2025-10-03T20:20:00Z)",  # 🕒 FECHA QUEMADA
                FlexibleTimeWindow={"Mode": "OFF"},
                Target={
                    "Arn": "arn:aws:lambda:us-east-1:200093566387:function:UpdateEventLambda",
                    "RoleArn": "arn:aws:iam::200093566387:role/nequi-root-dev-EventBridg-EventBridgeInvokeLambdaRo-GQSJVZLTaasf",
                    "Input": json.dumps({"triggered_by": "Lambda A", "EventId": eid})
                },
                State="ENABLED",
                GroupName="default"
            )
            item["schedule_created"] = True
            item["scheduled_for"] = "2025-10-03T22:00:00Z"
        except Exception as e:
            item["schedule_created"] = False
            item["error"] = str(e)
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
