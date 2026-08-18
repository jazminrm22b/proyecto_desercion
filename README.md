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

- El servicio corre `app/app.py` con `gunicorn app:app` desde dentro de `app/`
  (así lo arma el `Dockerfile`); por eso `app.py` calcula la ruta al modelo
  como `app/../models/...`.
- `app/requirements.txt` trae solo lo necesario para servir la app;
  `training/requirements.txt` trae lo necesario para reentrenar (incluye
  `pandas`, que la app en producción no usa).

## Variables de entorno

Ver `.env.example`. En resumen:

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | conexión a Neon |
| `FLASK_SECRET_KEY` | sesión/flash de Flask |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_NAME` | envío de correo |

## Correr en local

```bash
python -m venv venv && source venv/bin/activate
pip install -r app/requirements.txt
cp env.example .env   # edita con tus valores
export $(cat .env | xargs)
cd app && python app.py
```

Abre http://localhost:5000

## Desplegar en Render

1. Sube el proyecto a GitHub.
2. En Render: **New > Blueprint** (usa `render.yaml`) o **New > Web Service > Docker**.
3. Configura las variables de entorno de arriba.
4. Las tablas se crean solas en el primer request (`db.init_db()`).
5. El healthcheck está en `/salud`.

## Cosas a tener en cuenta

- El modelo se entrenó con los códigos originales de la variable DES (0, 5, 9);
  la app los traduce a 1/3/9 solo para mostrarlos al usuario (`MAPEO_DES_PUBLICO`
  en `config.py`).
- Los catálogos de opciones (SERSALUD, SITUA_CONYUGAL, etc.) siguen el
  cuestionario del INEGI y los valores que aparecen en el CSV de
  entrenamiento — revísalos si tu institución usa otra codificación.
- El logo por defecto está en `static/img/logo.png`; cámbialo por el tuyo
  cuando quieras.
- El campo del año de censo (CPV) no se le pregunta al estudiante: queda
  fijo al valor más reciente con el que se entrenó el modelo.
- El resultado es orientativo, no un diagnóstico — se aclara en pantalla.
