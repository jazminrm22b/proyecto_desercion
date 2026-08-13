"""
email_utils.py
==============
Envío del reporte PDF por correo vía SMTP.
Variables de entorno requeridas:
    SMTP_HOST         smtp-relay.brevo.com
    SMTP_PORT          2525  (usa este puerto en Render; 587/465 no funcionan)
    SMTP_USER          el "Iniciar sesión" que muestra Brevo (login de auth)
    SMTP_PASSWORD      la "SMTP key" que genera Brevo (NO es la API key)
    SMTP_FROM_EMAIL    un correo verificado como Sender en Brevo (remitente
                        visible; NO uses aquí el mismo valor que SMTP_USER)
    SMTP_FROM_NAME      (opcional) nombre visible del remitente
"""

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "2525"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Permanencia Educativa — Modelo Tesis")

# Si el servidor tarda en responder, que falle rápido en vez de colgar el
# worker de Gunicorn hasta que lo mate por timeout.
TIMEOUT_SEGUNDOS = 15


def enviar_reporte_pdf(destinatario: str, codigo_estudiante: str,
                        pdf_bytes: bytes, des_titulo: str = None) -> None:
    """Envía el PDF adjunto con el mismo diseño de correo (tarjeta HTML)
    que usa permanencia_educativa. Lanza una excepción si algo falla (el
    llamador debe capturarla y registrar el error en la base de datos)."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and SMTP_FROM_EMAIL):
        raise RuntimeError(
            "Configuración SMTP incompleta. Define SMTP_HOST, SMTP_USER, "
            "SMTP_PASSWORD y SMTP_FROM_EMAIL como variables de entorno."
        )

    linea_resultado = f"<p>Nivel de riesgo de deserción: <b>{des_titulo}</b></p>" if des_titulo else ""

    html_content = f"""
    <div style="font-family:'Inter',Arial,sans-serif;max-width:560px;margin:auto">
      <h2 style="color:#1f2937">Resultado de tu evaluación de deserción escolar</h2>
      <p>Código de estudiante: <b>{codigo_estudiante}</b></p>
      {linea_resultado}
      <p>Adjuntamos el reporte completo en PDF.</p>
      <p style="margin-top:20px;font-size:13px;color:#6b7280">
        Este resultado fue generado con el modelo que replica la metodología de
        tesis; es orientativo y no sustituye la valoración de un tutor
        académico o psicopedagógico. Si tienes dudas, acércate a tu institución
        educativa.
      </p>
    </div>
    """

    msg = EmailMessage()
    msg["Subject"] = f"Resultado de tu evaluación de deserción escolar — {codigo_estudiante}"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = destinatario
    msg.set_content(
        f"Resultado de tu evaluación (código {codigo_estudiante}).\n\n"
        f"Adjuntamos el reporte en PDF. Este resultado es orientativo y no "
        f"sustituye el acompañamiento de tu institución."
    )
    msg.add_alternative(html_content, subtype="html")
    msg.add_attachment(
        pdf_bytes, maintype="application", subtype="pdf",
        filename=f"reporte_desercion_{codigo_estudiante}.pdf",
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=TIMEOUT_SEGUNDOS) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"Error SMTP al enviar correo: {exc}") from exc
