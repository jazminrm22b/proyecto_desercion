"""Genera el reporte PDF con las variables capturadas, el resultado DES y una
explicación breve de la metodología. Requiere: reportlab."""

import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

from config import VARIABLES, ORDEN_VARIABLES, DESCRIPCION_RIESGO
from municipios import nombre_municipio

LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "img", "logo.png")

METODOLOGIA_TEXTO = (
    "El resultado se obtuvo con un Perceptrón Multicapa (MLP), un tipo de "
    "Red Neuronal Artificial compuesta por una capa de entrada, cuatro capas "
    "ocultas y una capa de salida. La red fue entrenada con el algoritmo de "
    "optimización Adam sobre registros del Censo y la Encuesta Intercensal "
    "del INEGI (2010, 2015 y 2020), aprendiendo patrones asociados a la "
    "permanencia o el abandono escolar en los niveles medio superior y "
    "superior. El valor mostrado abajo es la clasificación que la red "
    "asigna al perfil capturado y debe interpretarse como un apoyo "
    "referencial para la toma de decisiones, no como un diagnóstico "
    "definitivo."
)


def _formatear_valor(var: str, valor, respuestas: dict) -> str:
    meta = VARIABLES[var]
    if var == "MUN":
        return nombre_municipio(respuestas.get("ENT"), valor)
    if meta["type"] == "select":
        try:
            return str(meta["options"].get(int(valor), valor))
        except (ValueError, TypeError):
            return str(valor)
    return str(valor)


def generar_pdf(codigo_estudiante: str, respuestas: dict, des_publico: int) -> bytes:
    """Regresa los bytes del PDF listo para adjuntar a un correo."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "TituloProyecto", parent=styles["Heading1"], fontSize=16,
        textColor=colors.HexColor("#122b52"), spaceAfter=2,
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#555555"),
    )
    seccion_style = ParagraphStyle(
        "Seccion", parent=styles["Heading2"], fontSize=12,
        textColor=colors.HexColor("#122b52"), spaceBefore=14, spaceAfter=6,
    )
    normal_style = styles["Normal"]

    story = []


    if os.path.exists(LOGO_PATH):
        header_table = Table(
            [[Image(LOGO_PATH, width=2.2 * cm, height=2.2 * cm),
              Paragraph("Sistema de Predicción de Deserción Escolar", titulo_style)]],
            colWidths=[2.6 * cm, None],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph("Sistema de Predicción de Deserción Escolar", titulo_style))

    story.append(Paragraph(
        "Reporte individual generado automáticamente — "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
        subtitulo_style,
    ))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#122b52"), spaceBefore=8, spaceAfter=12))

    story.append(Paragraph(f"<b>Código de estudiante:</b> {codigo_estudiante}", normal_style))
    story.append(Spacer(1, 10))

    info_riesgo = DESCRIPCION_RIESGO[des_publico]
    story.append(Paragraph("Resultado de la evaluación", seccion_style))
    resultado_table = Table(
        [[f"Valor DES: {des_publico}", info_riesgo["titulo"]]],
        colWidths=[4 * cm, None],
    )
    resultado_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(info_riesgo["color"])),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(resultado_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(info_riesgo["detalle"], normal_style))

    story.append(Paragraph("Metodología", seccion_style))
    story.append(Paragraph(METODOLOGIA_TEXTO, normal_style))

    story.append(Paragraph("Respuestas capturadas", seccion_style))
    filas = [["Variable", "Descripción", "Respuesta"]]
    for var in ORDEN_VARIABLES:
        meta = VARIABLES[var]
        filas.append([var, meta["label"], _formatear_valor(var, respuestas.get(var), respuestas)])

    tabla_resp = Table(filas, colWidths=[2.6 * cm, 8.5 * cm, 4.4 * cm], repeatRows=1)
    tabla_resp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#122b52")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_resp)

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Este documento fue generado automáticamente y es de carácter "
        "orientativo. No sustituye el acompañamiento académico institucional.",
        subtitulo_style,
    ))

    doc.build(story)
    return buffer.getvalue()
