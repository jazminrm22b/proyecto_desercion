"""Catálogo de las variables de entrada, catálogo de estados, y descripciones
del resultado DES. Usado por el formulario web y la validación del backend."""

# Todas las variables que se piden en el formulario (sin cambios en la UI).
ORDEN_VARIABLES = [
    "ENT", "MUN", "SEXO", "EDAD", "SERSALUD", "PERTE_INDIGENA", "NACIONALIDAD",
    "ASISTEN", "ESCOLARI", "NIVACAD", "ESCOACUM", "SITUA_CONYUGAL",
    "SITUACION_TRAB", "COMPUTADORA", "CELULAR", "INTERNET", "INGTRHOG",
    "TAMLOC", "CPV",
]

# ASISTEN, NIVACAD y ESCOACUM se recolectan pero NO entran al modelo (fuga de
# datos: son las variables con las que DES fue calculada originalmente).
# NIVACAD sí se usa después de la predicción para describir el tipo de
# riesgo. Ver entrenamiento_desercion.py y clasificar_nivel_riesgo() en app.py.
VARIABLES_EXCLUIDAS_FUGA = ["ASISTEN", "NIVACAD", "ESCOACUM"]
ORDEN_VARIABLES_MODELO = [v for v in ORDEN_VARIABLES if v not in VARIABLES_EXCLUIDAS_FUGA]

# CPV se fija a un valor constante y no se pide en el formulario.
CPV_VALOR_FIJO = 2020
ORDEN_VARIABLES_FORM = [v for v in ORDEN_VARIABLES if v != "CPV"]

ESTADOS = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur",
    4: "Campeche", 5: "Coahuila", 6: "Colima", 7: "Chiapas", 8: "Chihuahua",
    9: "Ciudad de México", 10: "Durango", 11: "Guanajuato", 12: "Guerrero",
    13: "Hidalgo", 14: "Jalisco", 15: "México", 16: "Michoacán",
    17: "Morelos", 18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca",
    21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas",
    29: "Tlaxcala", 30: "Veracruz", 31: "Yucatán", 32: "Zacatecas",
}

# Definición de cada variable: tipo de control, etiqueta y opciones (si aplica)
VARIABLES = {
    "ENT": {
        "label": "Entidad federativa",
        "help": "Clave de la entidad federativa donde reside.",
        "type": "select",
        "options": ESTADOS,
    },
    "MUN": {
        "label": "Municipio o alcaldía",
        "help": "Primero selecciona tu entidad federativa.",
        # Selección en cascada: el <select> se llena por JS según ENT.
        "type": "cascada",
    },
    "SEXO": {
        "label": "Sexo",
        "type": "select",
        "options": {1: "Hombre", 3: "Mujer"},
    },
    "EDAD": {
        "label": "Edad",
        "help": "Años cumplidos. El modelo solo es válido para 15 años en adelante.",
        "type": "number", "min": 15, "max": 110,
    },
    "SERSALUD": {
        "label": "¿En dónde se atiende cuando tiene problemas de salud?",
        "type": "select",
        "options": {
            1: "IMSS", 2: "ISSSTE", 3: "ISSSTE estatal", 4: "Pemex/Defensa/Marina",
            5: "Seguro Popular / INSABI / IMSS-Bienestar", 6: "Seguro privado",
            7: "Consultorio/médico particular", 8: "Otro lugar", 9: "No se atiende",
        },
    },
    "PERTE_INDIGENA": {
        "label": "¿Habla algún dialecto o lengua indígena?",
        "type": "select",
        "options": {1: "Sí", 2: "No"},
    },
    "NACIONALIDAD": {
        "label": "Nacionalidad",
        "type": "select",
        "options": {1: "Mexicana", 3: "Extranjera"},
    },
    "ASISTEN": {
        "label": "¿Actualmente va a la escuela?",
        "type": "select",
        "options": {1: "Sí", 3: "No"},
    },
    "ESCOLARI": {
        "label": "Años cursados y aprobados del nivel académico actual",
        "help": "Ej. si va en 2° de bachillerato, captura 2.",
        "type": "number", "min": 0, "max": 8,
    },
    "NIVACAD": {
        "label": "Último nivel académico aprobado",
        "type": "select",
        "options": {
            0: "Ninguno", 1: "Preescolar", 2: "Primaria", 3: "Secundaria",
            4: "Preparatoria o bachillerato general",
            5: "Bachillerato tecnológico",
            6: "Estudios técnicos/comerciales con primaria terminada",
            7: "Estudios técnicos/comerciales con secundaria terminada",
            8: "Estudios técnicos/comerciales con preparatoria terminada",
            9: "Normal con primaria o secundaria terminada",
            10: "Normal de licenciatura", 11: "Licenciatura",
            12: "Especialidad", 13: "Maestría", 14: "Doctorado",
        },
    },
    "ESCOACUM": {
        "label": "Escolaridad acumulada (años aprobados en total)",
        "type": "number", "min": 0, "max": 24,
    },
    "SITUA_CONYUGAL": {
        "label": "Situación conyugal actual",
        "type": "select",
        "options": {
            1: "Unión libre", 2: "Separado(a)", 3: "Divorciado(a)",
            4: "Viudo(a)", 5: "Casado(a)", 6: "Soltero(a)",
        },
    },
    "SITUACION_TRAB": {
        "label": "Situación laboral la semana pasada",
        "type": "select",
        "options": {
            1: "Trabajó", 2: "No trabajó pero tiene trabajo",
            3: "Buscó trabajo", 4: "Estudiante sin trabajar",
            5: "Se dedica al hogar", 6: "Otra situación (jubilado, incapacitado, etc.)",
        },
    },
    "COMPUTADORA": {
        "label": "¿En su vivienda tienen computadora?",
        "type": "select",
        "options": {1: "Sí", 2: "No"},
    },
    "CELULAR": {
        "label": "¿En su vivienda tienen teléfono celular?",
        "type": "select",
        "options": {3: "Sí", 4: "No"},
    },
    "INTERNET": {
        "label": "¿En su vivienda tienen internet?",
        "type": "select",
        "options": {1: "Sí", 2: "No"},
    },
    "INGTRHOG": {
        "label": "Ingreso mensual aproximado por trabajo en el hogar (MXN)",
        "type": "number", "min": 0, "max": 500000,
    },
    "TAMLOC": {
        "label": "Tamaño de la localidad donde vive",
        "type": "select",
        "options": {
            1: "2,500 - 14,999 habitantes (rural)", 2: "15,000 - 99,999 habitantes",
            3: "100,000 y más habitantes", 4: "2,500 y más habitantes",
            5: "Menos de 2,500 habitantes",
        },
    },
    "CPV": {
        "label": "Año de referencia del Censo de Población y Vivienda",
        "type": "select",
        "options": {2010: "2010", 2015: "2015", 2020: "2020"},
    },
}

# Mapea los códigos internos (0/5/9, y 7 cuando NIVACAD queda fuera del rango
# histórico de desertores) a los códigos mostrados al usuario.
MAPEO_DES_PUBLICO = {0: 1, 5: 3, 9: 9, 7: 7}

DESCRIPCION_RIESGO = {
    1: {
        "titulo": "Permanencia / Bajo riesgo",
        "detalle": (
            "El modelo no identifica señales de deserción en el perfil "
            "capturado. Se recomienda dar seguimiento preventivo habitual."
        ),
        "color": "#1a7f37",
    },
    3: {
        "titulo": "Riesgo medio — Deserción en nivel medio superior",
        "detalle": (
            "El perfil capturado es similar al de estudiantes que "
            "abandonaron sus estudios en el nivel medio superior "
            "(bachillerato). Se recomienda una intervención tutorial "
            "temprana."
        ),
        "color": "#b98900",
    },
    9: {
        "titulo": "Riesgo alto — Deserción en nivel superior",
        "detalle": (
            "El perfil capturado es similar al de estudiantes que "
            "abandonaron sus estudios en el nivel superior (licenciatura). "
            "Se recomienda canalizar al programa institucional de "
            "retención estudiantil."
        ),
        "color": "#c0392b",
    },
    7: {
        "titulo": "Riesgo detectado — nivel académico fuera de rango",
        "detalle": (
            "El modelo detecta riesgo de deserción, pero el último nivel "
            "académico reportado no corresponde a los rangos históricos "
            "(medio superior o superior) usados para clasificar el tipo de "
            "riesgo. Se recomienda revisión manual del caso."
        ),
        "color": "#b98900",
    },
}
