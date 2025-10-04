import os
import json
import boto3
from decimal import Decimal, InvalidOperation

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# ---------- Helpers ----------
def _json_dumps(o):
    """Convierte Decimal -> int/float para que json.dumps no falle."""
    def _conv(x):
        if isinstance(x, Decimal):
            # int si no tiene parte decimal, float si la tiene
            return int(x) if x % 1 == 0 else float(x)
        if isinstance(x, list):
            return [_conv(i) for i in x]
        if isinstance(x, dict):
            return {k: _conv(v) for k, v in x.items()}
        return x
    return json.dumps(_conv(o))

def _normalize_event(event):
    if isinstance(event, dict):
        return event
    if isinstance(event, str):
        try:
            return json.loads(event)
        except json.JSONDecodeError:
            return {"raw": event}
    # fallback
    return json.loads(json.dumps(event, default=str))

def _to_ddb_number(value):
    """Convierte números a Decimal para DynamoDB sin perder precisión."""
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        # Evitar binarios de float
        return Decimal(str(value))
    # Si viene como string y es número, intentar convertir
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            return value
    return value
# ------------------------------

def lambda_handler(event, context):
    event = _normalize_event(event)

    # Payload esperado:
    # {
    #   "items": { "EventId": "...", "EventStatus": "No Disponible", ... },
    #   "update": { "field": "EventStatus", "value": "Agotado" }  <-- opcional
    # }

    items = (event or {}).get("items") or {}
    eid = items.get("EventId")
    if not eid:
        return {"statusCode": 400, "body": _json_dumps({"message": "Falta items.EventId"})}

    # 1) Campo/valor dinámico (si viene `update`)
    upd = (event or {}).get("update") or {}
    field = upd.get("field")
    value = upd.get("value")

    # 2) Si no se indicó `update`, intentamos usar items.EventStatus (caso común)
    if not field:
        if "EventStatus" in items:
            field = "EventStatus"
            value = items.get("EventStatus")
        else:
            return {
                "statusCode": 400,
                "body": _json_dumps({
                    "message": "Indica 'update.field' y 'update.value' o provee items.EventStatus",
                    "example_update": {"field": "EventStatus", "value": "No Disponible"}
                })
            }

    if field == "EventId":
        return {"statusCode": 400, "body": _json_dumps({"message": "No se puede actualizar la PK EventId"})}

    # Preparar valor para DynamoDB (números -> Decimal)
    ddb_value = _to_ddb_number(value)
    
    try:
        resp = table.update_item(
            Key={"EventId": eid},
            UpdateExpression="SET #f = :v",
            ExpressionAttributeNames={"#f": field},
            ExpressionAttributeValues={":v": 'No disponible'},
            ConditionExpression="attribute_exists(EventId)",
            ReturnValues="ALL_NEW",
        )
        return {"statusCode": 200, "body": _json_dumps(resp.get("Attributes", {}))}
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404, "body": _json_dumps({"message": "not found", "EventId": eid})}
    except Exception as e:
        return {"statusCode": 500, "body": _json_dumps({"message": "error", "error": str(e)})}
