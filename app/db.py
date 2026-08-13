"""
db.py
=====
Conexión a PostgreSQL en Neon y helpers de acceso a datos.

Variable de entorno requerida:
    DATABASE_URL  -> cadena de conexión de Neon, por ejemplo:
        postgresql://usuario:password@ep-xxxx.us-east-2.aws.neon.tech/dbname?sslmode=require

Neon requiere SSL; si la URL no trae sslmode=require se agrega automáticamente.
"""

import os
import json
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL and "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"


@contextmanager
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL no está configurada. Define esta variable de "
            "entorno con la cadena de conexión de tu proyecto Neon."
        )
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS alumnos (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255),
    acepta_correo   BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluaciones (
    id              SERIAL PRIMARY KEY,
    alumno_id       INTEGER NOT NULL REFERENCES alumnos(id) ON DELETE CASCADE,
    respuestas      JSONB NOT NULL,
    des_entrenamiento SMALLINT NOT NULL,
    des_publico       SMALLINT NOT NULL,
    valor_crudo     DOUBLE PRECISION NOT NULL,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS envios_correo (
    id              SERIAL PRIMARY KEY,
    evaluacion_id   INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    alumno_id       INTEGER NOT NULL REFERENCES alumnos(id) ON DELETE CASCADE,
    correo_destino  VARCHAR(255) NOT NULL,
    estado          VARCHAR(20) NOT NULL,   -- 'enviado' | 'error'
    detalle_error   TEXT,
    enviado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_alumno ON evaluaciones(alumno_id);
CREATE INDEX IF NOT EXISTS idx_envios_alumno ON envios_correo(alumno_id);
"""


def init_db():
    """Crea las tablas si no existen. Llamar una vez al arrancar la app."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)


def upsert_alumno(codigo: str, email: str | None, acepta_correo: bool) -> int:
    """Inserta o actualiza el alumno por código único; regresa su id."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alumnos (codigo, email, acepta_correo)
                VALUES (%s, %s, %s)
                ON CONFLICT (codigo) DO UPDATE
                    SET email = EXCLUDED.email,
                        acepta_correo = EXCLUDED.acepta_correo
                RETURNING id
                """,
                (codigo, email, acepta_correo),
            )
            return cur.fetchone()[0]


def guardar_evaluacion(alumno_id: int, respuestas: dict,
                        des_entrenamiento: int, des_publico: int,
                        valor_crudo: float) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO evaluaciones
                    (alumno_id, respuestas, des_entrenamiento, des_publico, valor_crudo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (alumno_id, json.dumps(respuestas), des_entrenamiento,
                 des_publico, valor_crudo),
            )
            return cur.fetchone()[0]


def registrar_envio_correo(evaluacion_id: int, alumno_id: int, correo_destino: str,
                            estado: str, detalle_error: str | None = None) -> None:
    """Registra en la base de datos, para fines de auditoría, cada intento de
    envío del reporte PDF por correo (exitoso o fallido)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO envios_correo
                    (evaluacion_id, alumno_id, correo_destino, estado, detalle_error)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (evaluacion_id, alumno_id, correo_destino, estado, detalle_error),
            )
