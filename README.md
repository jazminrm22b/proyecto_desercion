# Predicción de deserción escolar

App web en Flask que estima el riesgo de deserción de un estudiante a
partir de datos sociodemográficos, usando un MLPRegressor entrenado con
microdatos del censo/intercensal del INEGI. Guarda cada evaluación en
Postgres (Neon) y, si el usuario lo pide, le manda el resultado por correo.

## Estructura

```
.
├── app/                    # aplicación Flask (rootDir del servicio)
│   ├── app.py              # rutas /, /evaluar, /salud, /health
│   ├── config.py           # catálogo de variables, etiquetas y opciones del formulario
│   ├── db.py                # conexión y esquema de la base de datos
│   ├── email_utils.py       # envía el resultado por correo (SMTP)
│   ├── municipios.py        # catálogo de municipios para el select Estado → Municipio
│   ├── requirements.txt     # dependencias de runtime (sin pandas)
│   ├── catalogs/            # catálogos JSON (entidades, municipios, opciones de variables)
│   ├── static/               # css, js, imágenes y municipios.json para el frontend
│   └── templates/            # vistas Bootstrap (base, index, resultado, privacidad)
├── models/                 # modelo ya entrenado, listo para servir
│   ├── modelo_desercion_mlp.joblib
│   └── scaler_desercion.joblib
├── training/
│   ├── entrenar_modelo_desercion.py   # entrena el modelo y guarda el .joblib en ../models/
│   ├── Entrenamiento_desercion.ipynb  # mismo entrenamiento en formato notebook (Colab)
│   └── requirements.txt     # dependencias solo de entrenamiento (incluye pandas)
├── Dockerfile
├── render.yaml
├── env.example
└── README.md
```
