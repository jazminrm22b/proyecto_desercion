"""
features.py
============
Definición ÚNICA de las variables que recibe el modelo, compartida entre
`entrenar_modelo_desercion.py` (entrenamiento) y `app.py` (predicción en
producción). Que ambos importen de aquí evita el error más común en estos
proyectos: que el orden o el cálculo de una variable derivada quede
ligeramente distinto entre el script de entrenamiento y el backend.

FILOSOFÍA DEL MODELO (ver conversación / auditoría de julio 2026):
La predicción se hace ÚNICAMENTE con factores sociodemográficos y
económicos — origen, composición del hogar, acceso a tecnología, ingreso,
situación laboral y conyugal, escolaridad acumulada — nunca con variables
que ya revelan el resultado de forma directa (ASISTEN, ESCOLARI, NIVACAD
fueron retiradas por fuga de datos, ver NOTA 4 en entrenar_modelo_desercion.py).
Esto es intencional: un sistema de alerta temprana solo es útil si predice
el riesgo ANTES de que ya sea evidente por el propio estatus escolar del
estudiante.
"""

# 16 variables que el usuario captura en el formulario (sociodemográficas +
# económicas), en el orden en que llegan del formulario / CSV.
VARIABLES_BASE = [
    "ENT", "MUN", "SEXO", "EDAD", "SERSALUD", "PERTE_INDIGENA", "NACIONALIDAD",
    "ESCOACUM", "SITUA_CONYUGAL", "SITUACION_TRAB", "COMPUTADORA", "CELULAR",
    "INTERNET", "INGTRHOG", "TAMLOC", "CPV",
]

# Variables categóricas nominales (sin orden numérico real) con cardinalidad
# baja, aptas para el soporte nativo de categóricas de HistGradientBoosting
# (requiere < 255 categorías). MUN se deja fuera a propósito: aunque también
# es nominal, tiene ~569 valores posibles y excede ese límite; se trata como
# numérica por restricción técnica, no porque tenga un orden real.
VARIABLES_CATEGORICAS = [
    "ENT", "SEXO", "SERSALUD", "PERTE_INDIGENA", "NACIONALIDAD",
    "SITUA_CONYUGAL", "SITUACION_TRAB", "COMPUTADORA", "CELULAR",
    "INTERNET", "CPV", "TAMLOC",
]

# Variables derivadas (ingeniería de variables) — ambas se calculan SOLO a
# partir de variables sociodemográficas/económicas ya permitidas (EDAD,
# ESCOACUM, SITUACION_TRAB), nunca de ASISTEN/ESCOLARI/NIVACAD.
VARIABLES_DERIVADAS = ["ATRASO_ESCOLAR", "TRABAJA_X_ESCOLARIDAD"]

# Orden final y completo de columnas que recibe el modelo.
FEATURES_MODELO = VARIABLES_BASE + VARIABLES_DERIVADAS

# Índices (posición dentro de FEATURES_MODELO) de las columnas categóricas,
# tal como los pide el parámetro `categorical_features` de
# HistGradientBoostingClassifier.
INDICES_CATEGORICAS = [FEATURES_MODELO.index(c) for c in VARIABLES_CATEGORICAS]


def calcular_derivadas(edad, escoacum, situacion_trab):
    """Calcula las variables derivadas a partir de valores base.

    ATRASO_ESCOLAR: aproximación de "atraso escolar" (años que la persona
    debería haber cursado según su edad, menos los que realmente acumuló).
    Se acota en 0 por abajo (no existe "adelanto negativo" útil para el
    modelo). Es un predictor clásico de deserción en la literatura educativa.

    TRABAJA_X_ESCOLARIDAD: interacción entre situación laboral y
    escolaridad acumulada. Busca capturar el efecto conocido de "trabajar
    y estudiar a la vez", que golpea de forma distinta según cuánta
    escolaridad ya se acumuló.
    """
    import numpy as np
    atraso_escolar = np.maximum(np.asarray(edad) - np.asarray(escoacum) - 6, 0)
    trabaja_x_escolaridad = np.asarray(situacion_trab) * np.asarray(escoacum)
    return atraso_escolar, trabaja_x_escolaridad


def construir_vector(respuestas: dict) -> list:
    """Recibe un dict con las 16 variables base (claves = VARIABLES_BASE) y
    regresa la lista completa de features en el orden que espera el modelo,
    agregando las variables derivadas al final."""
    base = [respuestas[v] for v in VARIABLES_BASE]
    atraso_escolar, trabaja_x_escolaridad = calcular_derivadas(
        edad=respuestas["EDAD"],
        escoacum=respuestas["ESCOACUM"],
        situacion_trab=respuestas["SITUACION_TRAB"],
    )
    return base + [atraso_escolar, trabaja_x_escolaridad]
