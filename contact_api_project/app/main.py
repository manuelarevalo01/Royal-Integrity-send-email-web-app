# app/main.py
import logging
import httpx
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

from .models import ContactFormData
from .email_service import send_internal_notification_email, send_customer_auto_reply_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Servicio de Contacto Royal Integrity")

origins = [
    "http://localhost",
    "http://localhost:8080", 
    "http://localhost:3000", 
    "http://127.0.0.1:8080",
    #URL desplegada
    "https://www.royalintegrity.com.co",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Contact API"}

RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

async def verify_recaptcha(token: str, remote_ip: Optional[str] = None) -> bool:
    if not RECAPTCHA_SECRET_KEY:
        logger.error("RECAPTCHA_SECRET_KEY no está configurada. Saltando verificación de reCAPTCHA.")
        return True

    params = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': token,
    }
    if remote_ip:
        params['remoteip'] = remote_ip

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post('https://www.google.com/recaptcha/api/siteverify', data=params)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Respuesta de verificación de reCAPTCHA: {result}")
            return result.get('success', False)
        except httpx.RequestError as e:
            logger.error(f"Error de solicitud al verificar reCAPTCHA: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al verificar reCAPTCHA: {e}")
            return False
class RecaptchaVerificationPayload(BaseModel):
    token: str

@app.post("/api/auth/re-captcha")
async def verify_recaptcha_endpoint(
    request_data: RecaptchaVerificationPayload,
    request: Request
):
    client_ip = request.client.host if request.client else None
    is_human = await verify_recaptcha(request_data.token, client_ip)

    if is_human:
        logger.info(f"Verificación de reCAPTCHA exitosa para token recibido desde IP {client_ip}")
        return {"message": "reCAPTCHA verification successful"} 
    else:
        logger.warning(f"Verificación de reCAPTCHA fallida para token recibido desde IP {client_ip}")
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")
@app.post("/api/contact/send", status_code=201)
async def handle_contact_submission(
    request: Request,
    payload: ContactFormData = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    logger.info(f"Recibida solicitud en /contact/send de: {payload.corporate_mail}")
    logger.info(f"Contenido del payload para /contact/send: {payload.model_dump()}")

    # Validar política
    if not payload.accept_policy:
        logger.warning(f"Intento de envío sin aceptar política por: {payload.corporate_mail}")
        raise HTTPException(
            status_code=400,
            detail="Es necesario aceptar la política de tratamiento de datos para continuar."
        )

    # Lógica de envío de correos
    background_tasks.add_task(send_internal_notification_email, payload)
    background_tasks.add_task(send_customer_auto_reply_email, payload)

    return {
        "message": "Solicitud recibida exitosamente. Pronto nos comunicaremos contigo y recibirás una confirmación por correo.",
        "data_submitted": payload.model_dump(exclude={'recaptcha_token'})
    }

