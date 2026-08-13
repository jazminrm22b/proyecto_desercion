"""Backend Flask del sistema de predicción de deserción escolar.

Rutas:
  GET  /        -> formulario
  POST /evaluar -> valida, predice, guarda en la base de datos y opcionalmente
                   genera PDF + envía correo
  GET  /salud   -> healthcheck
"""

import json
import os
import logging

import joblib
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash

from config import (
    ORDEN_VARIABLES, ORDEN_VARIABLES_FORM, CPV_VALOR_FIJO, VARIABLES,
    VALORES_DES_ENTRENAMIENTO, MAPEO_DES_PUBLICO, DESCRIPCION_RIESGO,
)
import db
from pdf_report import generar_pdf
from email_utils import enviar_reporte_pdf
from municipios import nombre_municipio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("desercion_app")

BASE_DIR = os.path.dirname(__file__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambia-esta-clave-en-produccion")

MODELOS_DIR = os.path.join(BASE_DIR, "..", "models")
MODELO_PATH = os.path.join(MODELOS_DIR, "modelo_desercion_mlp.joblib")
SCALER_PATH = os.path.join(MODELOS_DIR, "scaler_desercion.joblib")

_modelo = None
_scaler = None

CATALOGS_DIR = os.path.join(BASE_DIR, "catalogs")
with open(os.path.join(CATALOGS_DIR, "entidades.json"), encoding="utf-8") as f:
    _ENTIDADES = json.load(f)
with open(os.path.join(CATALOGS_DIR, "municipios.json"), encoding="utf-8") as f:
    _MUNICIPIOS = json.load(f)
with open(os.path.join(CATALOGS_DIR, "variable_choices.json"), encoding="utf-8") as f:
    _VARIABLE_CHOICES = json.load(f)


def get_modelo():
    global _modelo
    if _modelo is None:
        _modelo = joblib.load(MODELO_PATH)
    return _modelo


def get_scaler():
    global _scaler
    if _scaler is None:
        _scaler = joblib.load(SCALER_PATH)
    return _scaler


@app.before_request
def _ensure_db():
    # El healthcheck de Render (/salud, /health) nunca debe depender de que
    # Neon esté disponible: si se cuelga aquí, Render reinicia el contenedor
    # en bucle aunque la app sí esté sirviendo tráfico.
    if request.path in ("/salud", "/health"):
        return
    # Crea las tablas la primera vez que se recibe una petición.
    if not getattr(app, "_db_ready", False):
        try:
            db.init_db()
            app._db_ready = True
        except Exception as exc:  # no tumbar la app si Neon no está lista aún
            logger.warning("No se pudo inicializar la base de datos: %s", exc)


@app.route("/salud")
@app.route("/health")
def salud():
    return {"status": "ok"}, 200


@app.route("/")
def index():
    return render_template(
        "index.html",
        variables=VARIABLES,
        orden=ORDEN_VARIABLES_FORM,
        entidades=_ENTIDADES,
        municipios=_MUNICIPIOS,
        choices=_VARIABLE_CHOICES,
    )


@app.route("/privacidad")
def privacidad():
    return render_template("privacidad.html")


def _validar_y_extraer_respuestas(form) -> dict:
    """Valida los campos del formulario y los convierte a número. CPV se
    fija a CPV_VALOR_FIJO porque no se pide en el formulario."""
    respuestas = {}
    for var in ORDEN_VARIABLES_FORM:
        crudo = form.get(var, "").strip()
        if crudo == "":
            raise ValueError(f"Falta el campo obligatorio: {VARIABLES[var]['label']}")
        try:
            valor = float(crudo)
        except ValueError:
            raise ValueError(f"Valor inválido en «{VARIABLES[var]['label']}»")
        meta = VARIABLES[var]
        if "min" in meta and valor < meta["min"]:
            raise ValueError(f"«{meta['label']}» debe ser mayor o igual a {meta['min']}")
        if "max" in meta and valor > meta["max"]:
            raise ValueError(f"«{meta['label']}» debe ser menor o igual a {meta['max']}")
        respuestas[var] = valor
    respuestas["CPV"] = float(CPV_VALOR_FIJO)
    return respuestas


@app.route("/evaluar", methods=["POST"])
def evaluar():
    codigo_estudiante = request.form.get("codigo_estudiante", "").strip()
    acepta_privacidad = request.form.get("acepta_privacidad") == "on"
    acepta_correo = request.form.get("quiere_correo") == "on"
    email = request.form.get("email", "").strip() or None

    if not acepta_privacidad:
        flash("Debes aceptar el aviso de privacidad para continuar.", "danger")
        return redirect(url_for("index"))

    if not codigo_estudiante:
        flash("El código de estudiante es obligatorio.", "danger")
        return redirect(url_for("index"))

    if acepta_correo and not email:
        flash("Indica un correo electrónico o desmarca la opción de recibir resultados.", "danger")
        return redirect(url_for("index"))

    try:
        respuestas = _validar_y_extraer_respuestas(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("index"))

    X = np.array([[respuestas[var] for var in ORDEN_VARIABLES]])
    X_esc = get_scaler().transform(X)
    valor_crudo = float(get_modelo().predict(X_esc)[0])

    valores_validos = np.array(VALORES_DES_ENTRENAMIENTO)
    des_entrenamiento = int(valores_validos[np.argmin(np.abs(valor_crudo - valores_validos))])
    des_publico = MAPEO_DES_PUBLICO[des_entrenamiento]

    evaluacion_id = None
    try:
        alumno_id = db.upsert_alumno(codigo_estudiante, email, acepta_correo)
        evaluacion_id = db.guardar_evaluacion(
            alumno_id, respuestas, des_entrenamiento, des_publico, valor_crudo
        )
    except Exception as exc:
        logger.error("Error guardando en la base de datos: %s", exc)
        flash("Tu resultado se calculó, pero no se pudo guardar en la base de datos.", "warning")
        alumno_id = None

    correo_enviado = False
    correo_error = None
    if acepta_correo and email:
        try:
            pdf_bytes = generar_pdf(codigo_estudiante, respuestas, des_publico)
            enviar_reporte_pdf(email, codigo_estudiante, pdf_bytes, des_titulo=DESCRIPCION_RIESGO[des_publico]["titulo"])
            correo_enviado = True
            if alumno_id and evaluacion_id:
                db.registrar_envio_correo(evaluacion_id, alumno_id, email, "enviado")
        except Exception as exc:
            correo_error = str(exc)
            logger.error("Error enviando correo: %s", exc)
            if alumno_id and evaluacion_id:
                try:
                    db.registrar_envio_correo(evaluacion_id, alumno_id, email, "error", correo_error)
                except Exception:
                    pass

    info_riesgo = DESCRIPCION_RIESGO[des_publico]
    nombre_mun = nombre_municipio(respuestas.get("ENT"), respuestas.get("MUN"))
    return render_template(
        "resultado.html",
        codigo_estudiante=codigo_estudiante,
        des_publico=des_publico,
        info_riesgo=info_riesgo,
        respuestas=respuestas,
        variables=VARIABLES,
        orden=ORDEN_VARIABLES,
        nombre_mun=nombre_mun,
        correo_enviado=correo_enviado,
        correo_error=correo_error,
        acepta_correo=acepta_correo,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
