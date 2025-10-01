import os
import json
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    # Si no existe body, usar el evento directo como body
    body_str = event.get("body")
    if body_str:
        body = json.loads(body_str)
    else:
        # Esto te permite probar desde el test de la consola de Lambda
        body = event

    event_id = body.get("EventId", str(uuid.uuid4())) 

    item = {
        "EventId": event_id,
        "EventName": body["EventName"],
        "EventDate": body["EventDate"],
        "EventStatus": body["EventStatus"],
        "EventCity": body["EventCity"]
    }

    table.put_item(Item=item)

    return {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Event created", "item": item})
    }
