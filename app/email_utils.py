"""
email_utils.py
==============
Envío de correo con el resultado del diagnóstico vía SMTP a través del
relay de Brevo, puerto 2525.

Variables de entorno requeridas:
    SMTP_HOST         smtp-relay.brevo.com
    SMTP_PORT         2525  (usa este puerto en Render; 587/465 no funcionan)
    SMTP_USER         el "Iniciar sesión" que muestra Brevo (login de auth)
    SMTP_PASSWORD     la "SMTP key" que genera Brevo (NO es la API key)
    SMTP_FROM_EMAIL   un correo verificado como Sender en Brevo (remitente
                       visible; NO uses aquí el mismo valor que SMTP_USER)
    SMTP_FROM_NAME    (opcional) nombre visible del remitente
"""

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "2525"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Deserción Escolar")

TIMEOUT_SEGUNDOS = 15


def enviar_resultado_por_correo(
    destinatario: str,
    codigo_estudiante: str,
    des_titulo: str,
) -> bool:
    """Envía el resultado del diagnóstico al correo del estudiante por SMTP.
    Regresa True si el servidor aceptó el envío, lanza excepción si no."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and SMTP_FROM_EMAIL):
        raise RuntimeError(
            "Configuración SMTP incompleta. Define SMTP_USER, SMTP_PASSWORD "
            "y SMTP_FROM_EMAIL como variables de entorno en Render."
        )

    html_content = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto">
      <h2 style="color:#1f2937">Resultado de tu evaluación de deserción escolar</h2>
      <p>Código de estudiante: <b>{codigo_estudiante}</b></p>
      <p>Nivel de riesgo de deserción: <b>{des_titulo}</b></p>
      <p style="margin-top:20px;font-size:13px;color:#6b7280">
        Este resultado es orientativo, generado por un modelo estadístico
        de predicción y no sustituye la valoración de un tutor académico
        o psicopedagógico. Si tienes dudas, acércate a tu institución
        educativa.
      </p>
    </div>
    """

    msg = EmailMessage()
    msg["Subject"] = f"Resultado de tu evaluación de deserción escolar — {codigo_estudiante}"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = destinatario
    msg.set_content(
        f"Resultado de tu evaluación (código {codigo_estudiante}): {des_titulo}.\n\n"
        "Este resultado es orientativo y no sustituye la valoración de un "
        "tutor académico o psicopedagógico."
    )
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=TIMEOUT_SEGUNDOS) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"Error SMTP al enviar correo: {exc}") from exc

    return True
