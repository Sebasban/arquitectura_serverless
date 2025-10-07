import os
import json
import boto3

# Inicializa clientes de AWS
sqs = boto3.client("sqs")
ses = boto3.client("ses", region_name=os.environ.get("SES_REGION", "us-east-1"))
FROM_EMAIL = os.environ.get("FROM_EMAIL", "no-reply@tudominio.com")

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))

    # SQS envía un batch de mensajes en event["Records"]
    for record in event.get("Records", []):
        try:
            print("---- RECORD ----")
            print(json.dumps(record, indent=2))
            print("----------------")

            # Extraer cuerpo del mensaje
            body = record.get("body")
            message = json.loads(body)

            # Si el mensaje viene anidado (doble JSON), decodificarlo de nuevo
            if isinstance(message, dict) and "body" in message and isinstance(message["body"], str):
                print("Mensaje anidado detectado, decodificando capa interna...")
                message = json.loads(message["body"])

            print("Mensaje parseado final:", message)

            # Extraer campos del mensaje
            to_email = message.get("Email")
            event_name = message.get("EventName", "Evento sin nombre")
            entradas = (
                message.get("NumEntries"))

            if not to_email:
                print("⚠️ No se encontró Email, se omite el envío.")
                continue

            # Construir correo
            subject = f"Confirmación de compra: {event_name}"
            body_text = (
                f"¡Gracias por tu compra!\n\n"
                f"Evento: {event_name}\n"
                f"Entradas compradas: {entradas}\n"
                f"Saludos,\nEquipo de Entradas"
            )
            body_html = f"""
                <html>
                <body>
                    <h2>¡Gracias por tu compra!</h2>
                    <p><b>Evento:</b> {event_name}</p>
                    <p><b>Entradas compradas:</b> {entradas}</p>
                    <br/>
                    <p>Saludos,<br/>Equipo de Entradas</p>
                </body>
                </html>
            """

            # Enviar correo por SES
            response = ses.send_email(
                Source=FROM_EMAIL,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": "UTF-8"},
                        "Html": {"Data": body_html, "Charset": "UTF-8"},
                    },
                },
            )

            print(f"Correo enviado a {to_email} | MessageId: {response['MessageId']}")

        except Exception as e:
            print(f"Error procesando mensaje: {str(e)}")

    return {"statusCode": 200, "body": json.dumps({"message": "Mensajes procesados"})}
