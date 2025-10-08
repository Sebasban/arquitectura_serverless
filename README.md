# 🎟️ Proyecto: API de Gestión de Eventos

## 📖 Descripción del proyecto

Este proyecto implementa una infraestructura serverless en AWS para la **gestión de eventos**, permitiendo registrar nuevos eventos, comprar entradas (boletas) y consultar la disponibilidad de los mismos.  
Está diseñado para automatizar el flujo completo de publicación, compra y notificación mediante AWS Lambda, API Gateway, SQS y SES.

El flujo principal es el siguiente:
1. Un **administrador** registra un evento a través del endpoint `/event`.
2. Un **usuario** puede comprar boletas del evento mediante el endpoint `/user`.
3. La aplicación valida la disponibilidad, actualiza los datos y **envía automáticamente un correo electrónico** confirmando la compra.
4. Los eventos pueden consultarse con métodos GET o modificarse/eliminarse (solo por administradores).

---

## 🧩 A. Registrar un evento

### Paso 1 – Obtener el endpoint
1. Dirígete a la etapa **`event`** de la API en API Gateway.  
2. Copia el **endpoint** que se muestra en esa sección.

### Paso 2 – Configurar la API Key
1. En la consola de AWS, entra a la sección **API Keys**.  
2. Copia el valor del **API Key**.  
3. En **Postman**, agrega el encabezado:
   ```
   x-api-key: <tu-api-key>
   ```
   Esto asegura que solo los administradores puedan crear eventos.

### Paso 3 – Probar con el siguiente JSON
```json
{
  "EventCity": "Manizales",
  "EventDate": "2025-10-09T19:15:00",
  "EventName": "Carlos",
  "EventStatus": "Disponible",
  "NumberEntries": 20000
}
```

### Importante:
- El formato de fecha **debe respetar ISO 8601** (`YYYY-MM-DDTHH:mm:ss`).
- La fecha del evento **debe ser posterior a la fecha de creación**.
- Si el evento tiene una fecha anterior o inválida, **se bloqueará automáticamente la venta**.

---

## 🎫 B. Comprar una boleta

Para comprar una boleta, haz un **PUT** al endpoint de la etapa **`user`**.  
> ⚠️ Este paso **no requiere API Key**.

Ejemplo de body:
```json
{
  "EventName": "Carlos",
  "NumberEntries": 50,
  "Email": "sebastian.buritica.m@gmail.com"
}
```

Al realizar la compra, el sistema enviará automáticamente un **correo electrónico** confirmando la venta.

---

## 🔍 C. Consultar eventos disponibles

### Obtener todos los eventos:
Haz un **GET** al endpoint base, sin enviar body.

### Filtrar un evento específico:
Usa el parámetro `EventName` en la URL:
```
https://czzc0ie9z6.execute-api.us-east-1.amazonaws.com/prod/user?EventName='nombre evento'
```

---

## 🛠️ D. Operaciones de administrador

Si eres administrador y deseas realizar operaciones sobre eventos, utiliza la misma URL, pero reemplazando **`user`** por **`event`**:

| Método | Descripción |
|---------|--------------|
| **PUT** | Actualizar información de un evento |
| **GET** | Consultar información detallada de un evento |
| **DELETE** | Eliminar un evento específico |

Cada operación se filtra utilizando el **EventId** correspondiente.

---

## 🌐 Endpoint base
```
https://czzc0ie9z6.execute-api.us-east-1.amazonaws.com/prod/
```

---

## 🧠 Tecnologías utilizadas
- **AWS Lambda**: ejecución de funciones serverless.
- **Amazon API Gateway**: exposición de los endpoints REST.
- **Amazon DynamoDB**: almacenamiento de los eventos y transacciones.
- **Amazon SQS**: gestión de colas de mensajes para desacoplar procesos.
- **Amazon SES**: envío automático de correos electrónicos.
- **Python 3.x**: lenguaje principal de las Lambdas.

---

## 👨‍💻 Autor
Desarrollado por : **Paula Andrea Urrego Cornejo** **Sebastian Buritica Montoya**