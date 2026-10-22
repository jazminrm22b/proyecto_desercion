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
│   ├── scaler_desercion.joblib
│   └── model_metadata.json  # features, umbral de decisión, regla NIVACAD, métricas
├── training/
│   ├── entrenamiento_desercion.py     # entrena el modelo y guarda el .joblib/.json
│   └── requirements.txt     # dependencias solo de entrenamiento (incluye pandas)
├── Dockerfile
├── render.yaml
├── env.example
└── README.md
```

## Metodología del modelo

El modelo sigue siendo un `MLPRegressor` (`hidden_layer_sizes=(2,2,2,2)`),
pero **no regresa el código crudo de DES** (0/5/9 del censo). En su lugar:

- **Target**: `EN_RIESGO` binario — `1.0` si `DES != 0` (deserción, sin
  importar el nivel), `0.0` si `DES == 0`. El MLPRegressor predice un valor
  continuo entre 0 y 1 que se interpreta como probabilidad de riesgo.
- **Variables excluidas por fuga de datos**: `ASISTEN`, `NIVACAD` y
  `ESCOACUM` se siguen pidiendo en el formulario pero ya no entran al
  modelo, porque son las variables con las que el propio INEGI calculó DES
  originalmente (dejarlas como predictor era "adivinar" la respuesta, no
  predecirla). El modelo entrena con las 16 variables restantes.
- **NIVACAD como regla de post-proceso**: una vez que el modelo dice
  "en riesgo", `NIVACAD` (que el usuario sí reporta en el formulario) se usa
  para clasificar el tipo de riesgo — medio superior, superior, o "fuera de
  rango" si no cae en ninguno de los dos — sin que el modelo lo haya visto
  nunca como entrada. Ver `nivacad_subclassification_rule` en
  `model_metadata.json`.
- **Umbral de decisión**: en vez de clasificar en 0.5, se busca sobre la
  curva precisión-recall el umbral que maximiza el recall dado un piso de
  precisión (`PRECISION_OBJETIVO` en el script de entrenamiento).

Este mismo enfoque (excluir variables con fuga de datos, target binario,
NIVACAD como regla posterior) es el que usan también `permanencia_educativa`
y `desercion_escolar`; aquí solo cambia el algoritmo (MLPRegressor en vez de
MLPClassifier / HistGradientBoostingClassifier).

### Resultados del último entrenamiento

Sobre 1,079,400 registros (863,520 entrenamiento / 215,880 prueba), se
probaron varios valores de `PRECISION_OBJETIVO` — el piso de precisión que
el umbral debe alcanzar antes de maximizar el recall — para decidir el
punto de corte final:

| `PRECISION_OBJETIVO` | Umbral | Accuracy | Balanced acc. | F1 | Recall (en_riesgo) | Falsos negativos | Falsos positivos |
|---|---|---|---|---|---|---|---|
| 0.30 | 0.057 | 59.5% | 0.747 | 0.459 | 98.1% | 729 | 86,702 |
| **0.45 (elegido)** | **0.076** | **78.9%** | **0.838** | **0.603** | **91.5%** | **3,239** | **42,347** |
| 0.50 | 0.081 | 82.5% | 0.851 | 0.641 | 89.3% | 4,062 | 33,825 |
| 0.60 | 0.089 | 87.5% | 0.868 | 0.706 | 85.8% | 5,390 | 21,664 |

En los cuatro casos el ROC-AUC es 0.942 — es el mismo modelo subyacente;
lo único que cambia es dónde se pone el punto de corte sobre la misma curva
precisión-recall.

**Se eligió `PRECISION_OBJETIVO = 0.45`** (modelo actualmente en `models/`)
porque, para este sistema, el costo de que un estudiante en riesgo real no
reciba la alerta pesa más que el costo de una falsa alarma que un tutor
revisa y descarta. Con este umbral el modelo detecta 91.5% de los casos
reales de deserción (solo 3,239 falsos negativos sobre 215,880 casos de
prueba), a cambio de 42,347 falsas alarmas. Es un punto intermedio entre el
extremo de 0.30 (98.1% de casos reales detectados, pero solo 30% de
precisión) y valores más altos como 0.50/0.60, que suben la precisión y la
accuracy pero dejan pasar más casos reales sin detectar.

Si el criterio institucional cambia (por ejemplo, si la capacidad de dar
seguimiento a cada alerta es limitada y priorizar precisión resulta más
práctico), ajusta `PRECISION_OBJETIVO` en `entrenamiento_desercion.py` y
vuelve a entrenar.
