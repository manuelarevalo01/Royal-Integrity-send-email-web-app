# app/email_service.py
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from emails import Message

from .models import ContactFormData

logger = logging.getLogger(__name__)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configuración SMTP desde variables de entorno
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT_STR = os.getenv("SMTP_PORT")
SMTP_PORT = int(SMTP_PORT_STR) if SMTP_PORT_STR and SMTP_PORT_STR.isdigit() else 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_SENDER_ADDRESS = os.getenv("EMAIL_SENDER_ADDRESS")
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "Royal Integrity")
INTERNAL_RECIPIENT_EMAIL = os.getenv("INTERNAL_RECIPIENT_EMAIL")

if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_SENDER_ADDRESS, INTERNAL_RECIPIENT_EMAIL]):
    logger.error("¡CONFIGURACIÓN SMTP INCOMPLETA! Revisa tu archivo .env. El envío de correos no funcionará.")

templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
jinja_env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Función auxiliar para enviar un correo."""
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_SENDER_ADDRESS]):
        logger.error("Faltan credenciales SMTP para enviar correo.")
        return False

    message = Message(
        subject=subject,
        html=html_body,
        mail_from=(EMAIL_SENDER_NAME, EMAIL_SENDER_ADDRESS)
    )

    smtp_params = {
        "host": SMTP_SERVER,
        "port": SMTP_PORT,
        "user": SMTP_USERNAME,
        "password": SMTP_PASSWORD,
        "timeout": 10,
    }
    if SMTP_PORT == 587:
        smtp_params["tls"] = True
    elif SMTP_PORT == 465:
        smtp_params["ssl"] = True

    try:
        response = message.send(to=to_email, smtp=smtp_params)
        if response and response.status_code in [250, 200]:
            logger.info(f"Correo enviado exitosamente a {to_email} con asunto: '{subject}'")
            return True
        else:
            error_msg = response.error if response else "Respuesta SMTP desconocida o nula."
            status_code_msg = response.status_code if response else "N/A"
            logger.error(f"Fallo al enviar correo a {to_email}. Código: {status_code_msg}. Error: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Excepción durante el envío de correo a {to_email}: {str(e)}", exc_info=True)
        return False

async def send_internal_notification_email(form_data: ContactFormData):
    """Envía una notificación al correo interno de la empresa."""
    logger.info(f"Preparando notificación interna para: {INTERNAL_RECIPIENT_EMAIL}")
    subject = f"Nuevo Contacto desde Formulario Web: {form_data.customer_name}"
    
    html_body_internal = f"""
    <h2>Nueva Solicitud de Contacto Recibida</h2>
    <p><strong>Nombre:</strong> {form_data.customer_name}</p>
    <p><strong>Email:</strong> {form_data.corporate_mail}</p>
    <p><strong>Aceptó Política:</strong> {'Sí' if form_data.accept_policy else 'No'}</p>
    <p><strong>Solicitud/Mensaje:</strong></p>
    <pre>{form_data.requests if form_data.requests else "No proporcionado"}</pre>
    <hr>
    <p><em>Mensaje enviado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    """
    
    if INTERNAL_RECIPIENT_EMAIL:
        _send_email(
            to_email=INTERNAL_RECIPIENT_EMAIL,
            subject=subject,
            html_body=html_body_internal
        )
    else:
        logger.warning("INTERNAL_RECIPIENT_EMAIL no está configurado. No se enviará notificación interna.")

async def send_customer_auto_reply_email(form_data: ContactFormData, template_name: str = "auto_reply_template_es.html"):
    """Envía un correo de auto-respuesta al cliente."""
    logger.info(f"Preparando auto-respuesta para: {form_data.corporate_mail}")
    subject = "Hemos recibido tu mensaje - Royal Integrity"

    try:
        template = jinja_env.get_template(template_name)
        html_body_customer = template.render(
            customer_name=form_data.customer_name,
            customer_email=form_data.corporate_mail,
            requests_message=form_data.requests if form_data.requests else "No has proporcionado un mensaje específico.",
            company_name="Royal Integrity",
            current_year=datetime.now().year
        )
    except Exception as e:
        logger.error(f"Error al renderizar la plantilla '{template_name}': {str(e)}")
        html_body_customer = f"<p>Estimado/a {form_data.customer_name},</p><p>Hemos recibido tu mensaje y pronto nos comunicaremos contigo. Gracias.</p>"
        
    _send_email(
        to_email=form_data.corporate_mail,
        subject=subject,
        html_body=html_body_customer
    )