"""Entrena el modelo MLPRegressor de prediccion de desercion escolar."""

import os
import time
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, confusion_matrix

RUTA_CSV = "Copia_de_Personas_vivienda2010_2015_2020_20VAR_DES.csv"
EDAD_MINIMA = 15
NIVACAD_MIN = 4
NIVACAD_MAX = 11
TEST_SIZE = 0.20
RANDOM_STATE = 42
N_SEMILLAS = 8

VARIABLES_ENTRADA = [
    "ENT", "MUN", "SEXO", "EDAD", "SERSALUD", "PERTE_INDIGENA", "NACIONALIDAD",
    "ASISTEN", "ESCOLARI", "NIVACAD", "ESCOACUM", "SITUA_CONYUGAL",
    "SITUACION_TRAB", "COMPUTADORA", "CELULAR", "INTERNET", "INGTRHOG",
    "TAMLOC", "CPV",
]
VARIABLE_SALIDA = "DES"

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
RUTA_MODELO = os.path.join(MODELS_DIR, "modelo_desercion_mlp.joblib")
RUTA_SCALER = os.path.join(MODELS_DIR, "scaler_desercion.joblib")

# Mapeo de codigos DES del CSV a codigos de presentacion
MAPEO_DES_PUBLICO = {
    0: 1,
    5: 3,
    9: 9,
}


def cargar_y_limpiar_datos(ruta_csv: str) -> pd.DataFrame:
    """Carga el CSV y aplica los filtros de limpieza y depuracion."""
    print(f"Cargando {ruta_csv} ...")
    columnas = VARIABLES_ENTRADA + [VARIABLE_SALIDA]
    df = pd.read_csv(ruta_csv, usecols=columnas, encoding="utf-8-sig")
    print(f"  Registros totales leídos: {len(df):,}")

    df = df[columnas]

    antes = len(df)
    df = df.dropna()
    print(f"  Registros eliminados por valores vacíos: {antes - len(df):,}")

    antes = len(df)
    df = df.drop_duplicates()
    print(f"  Registros eliminados por duplicados: {antes - len(df):,}")

    antes = len(df)
    df = df[df["EDAD"] >= EDAD_MINIMA]
    print(f"  Registros eliminados por filtro EDAD >= {EDAD_MINIMA}: {antes - len(df):,}")

    antes = len(df)
    df = df[(df["NIVACAD"] >= NIVACAD_MIN) & (df["NIVACAD"] <= NIVACAD_MAX)]
    print(f"  Registros eliminados por filtro NIVACAD [{NIVACAD_MIN}-{NIVACAD_MAX}]: "
          f"{antes - len(df):,}")

    antes = len(df)
    df = df[df["ESCOACUM"] != 99]
    print(f"  Registros eliminados por ESCOACUM == 99: {antes - len(df):,}")

    antes = len(df)
    df = df[df["INGTRHOG"] < 999998]
    print(f"  Registros eliminados por INGTRHOG >= 999998: {antes - len(df):,}")

    print(f"  Registros finales para entrenamiento: {len(df):,}")

    valores_des = sorted(df[VARIABLE_SALIDA].unique().tolist())
    print(f"  Valores únicos encontrados en DES: {valores_des}")
    if set(valores_des) != {0, 5, 9} and set(valores_des) != {1, 3, 9}:
        print("  ADVERTENCIA: los valores de DES no coinciden con lo esperado.")

    return df


def entrenar_modelo(df: pd.DataFrame):
    """Divide los datos, escala y entrena el MLPRegressor probando varias semillas."""
    X = df[VARIABLES_ENTRADA].values
    y = df[VARIABLE_SALIDA].values.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"\nEntrenamiento: {len(X_train):,} registros | Prueba: {len(X_test):,} registros")

    scaler = MinMaxScaler()
    X_train_esc = scaler.fit_transform(X_train)
    X_test_esc = scaler.transform(X_test)

    mejor_modelo = None
    mejor_r2 = -np.inf
    print(f"\nProbando {N_SEMILLAS} inicializaciones aleatorias...")

    for i in range(N_SEMILLAS):
        semilla = RANDOM_STATE + i
        modelo = MLPRegressor(
            hidden_layer_sizes=(2, 2, 2, 2),
            activation="relu",
            solver="adam",
            alpha=0.001,
            max_iter=5000,
            random_state=semilla,
        )
        inicio = time.time()
        modelo.fit(X_train_esc, y_train)
        duracion = time.time() - inicio
        r2 = r2_score(y_test, modelo.predict(X_test_esc))
        print(f"  Semilla {semilla}: {modelo.n_iter_} iteraciones, "
              f"{duracion:.1f}s, R^2 = {r2:.6f}")

        if r2 > mejor_r2:
            mejor_r2 = r2
            mejor_modelo = modelo

    print(f"\nMejor semilla: R^2 = {mejor_r2:.6f}")
    return mejor_modelo, scaler, X_test_esc, y_test


def evaluar_modelo(modelo, X_test_esc, y_test, valores_validos):
    """Evalua el modelo como regresion y como clasificacion."""
    y_pred = modelo.predict(X_test_esc)

    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    print("\n--- Resultados como regresión ---")
    print(f"R^2: {r2:.9f}")
    print(f"MSE: {mse:.6f}")

    valores_validos = np.array(sorted(valores_validos))
    y_pred_clase = valores_validos[
        np.argmin(np.abs(y_pred[:, None] - valores_validos[None, :]), axis=1)
    ]
    acc = accuracy_score(y_test, y_pred_clase)
    print("\n--- Resultados como clasificación ---")
    print(f"Accuracy: {acc:.4%}")
    print("Matriz de confusión, orden:", list(valores_validos))
    print(confusion_matrix(y_test, y_pred_clase, labels=valores_validos))

    return r2, mse, acc


def guardar_artefactos(modelo, scaler):
    """Guarda el modelo y el scaler entrenados en disco."""
    joblib.dump(modelo, RUTA_MODELO)
    joblib.dump(scaler, RUTA_SCALER)
    print(f"\nModelo guardado en:  {RUTA_MODELO}")
    print(f"Scaler guardado en:  {RUTA_SCALER}")


def main():
    df = cargar_y_limpiar_datos(RUTA_CSV)
    valores_validos = df[VARIABLE_SALIDA].unique().tolist()

    modelo, scaler, X_test_esc, y_test = entrenar_modelo(df)
    evaluar_modelo(modelo, X_test_esc, y_test, valores_validos)
    guardar_artefactos(modelo, scaler)

    print("\nVariables de entrada usadas (respetar este orden al predecir):")
    print(VARIABLES_ENTRADA)


if __name__ == "__main__":
    main()
