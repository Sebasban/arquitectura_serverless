import os
import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def to_jsonable(obj):
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, set):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def lambda_handler(event, context):
    query_params = event.get("queryStringParameters", {}) or {}
    event_name = query_params.get("EventName") if query_params else None

    if event_name:
        response = table.scan(FilterExpression=Attr("EventName").eq(event_name))
        message = f"Eventos filtrados por nombre '{event_name}'."
    else:
        response = table.scan()
        message = "Listado completo de eventos."

    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    if not items:
        return {"statusCode": 404, "body": json.dumps({"message": "No se encontraron eventos."})}

    payload = {"message": message, "total": len(items), "data": items}
    return {"statusCode": 200, "body": json.dumps(to_jsonable(payload))}
