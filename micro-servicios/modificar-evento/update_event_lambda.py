import os, json, boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    # Normaliza si llega como string
    if isinstance(event, str):
        event = json.loads(event)

    item = event.get("items") or {}
    eid = item.get("EventId")
    if not eid:
        return {"statusCode": 400, "body": json.dumps({"message": "Falta items.EventId"})}

    # Cambia SOLO este campo (ejemplo: EventStatus -> "Agotado")
    try:
        resp = table.update_item(
            Key={"EventId": eid},
            UpdateExpression="SET #f = :v",
            ExpressionAttributeNames={"#f": "EventStatus"},
            ExpressionAttributeValues={":v": "No disponible"},
            ConditionExpression="attribute_exists(EventId)",
            ReturnValues="ALL_NEW",
        )
        return {"statusCode": 200, "body": json.dumps(resp["Attributes"])}
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404, "body": json.dumps({"message": "not found", "EventId": eid})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": "error", "error": str(e)})}
