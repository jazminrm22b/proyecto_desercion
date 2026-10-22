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

Los microdatos del Censo de Población y Vivienda 2020 (INEGI) tienen
3,195,460 registros; tras filtrar CPV = 2020 y edad ≥ 15, y eliminar
nulos, duplicados y valores fuera de rango de `NIVACAD`, `ESCOACUM` e
`INGTRHOG`, quedan **525,216 registros** (420,172 de entrenamiento y
105,044 de prueba, partición estratificada 80/20). En el conjunto de
prueba hay 16,634 casos en riesgo.

Se probaron varios valores de `PRECISION_OBJETIVO` — el piso de precisión
que el umbral debe alcanzar antes de maximizar el recall — para decidir el
punto de corte final:

| `PRECISION_OBJETIVO` | Umbral | Accuracy | Balanced acc. | F1 | Recall (en_riesgo) | Falsos negativos | Falsos positivos |
|---|---|---|---|---|---|---|---|
| 0.30 | 0.007 | 63.7% | 0.772 | 0.458 | 97.0% | 495 | 37,657 |
| 0.45 | 0.085 | 81.1% | 0.840 | 0.596 | 88.3% | 1,946 | 17,952 |
| 0.50 | 0.104 | 84.2% | 0.848 | 0.631 | 85.7% | 2,383 | 14,251 |
| **0.60 (elegido)** | **0.124** | **88.5%** | **0.856** | **0.691** | **81.4%** | **3,089** | **9,030** |

En los cuatro casos el ROC-AUC es 0.934 (R² = 0.603, MSE = 0.0529) — es el
mismo modelo subyacente; lo único que cambia es dónde se pone el punto de
corte sobre la misma curva precisión-recall.

**Se eligió `PRECISION_OBJETIVO = 0.60`** (modelo actualmente en `models/`,
umbral de decisión 0.1239, el mismo piso de precisión que usan los tres
modelos comparados: `HistGradientBoostingClassifier`, `MLPRegressor` y
`MLPClassifier`). Con este umbral el modelo detecta 81.4% de los casos
reales de deserción (3,089 falsos negativos sobre 105,044 casos de
prueba) con solo 9,030 falsas alarmas. Valores más bajos, como 0.30, detectan
más casos reales (97.0%) pero a cambio de muchas más falsas alarmas
(37,657) y una precisión de solo 30%.

Si el criterio institucional cambia (por ejemplo, si el costo de que un
estudiante en riesgo real no reciba la alerta pesa más que el de una falsa
alarma, o si la capacidad de dar seguimiento a cada alerta es limitada),
ajusta `PRECISION_OBJETIVO` en `entrenamiento_desercion.py` y vuelve a
entrenar.
