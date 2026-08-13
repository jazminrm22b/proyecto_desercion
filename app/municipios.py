"""
municipios.py
=============
Carga el catálogo INEGI de municipios (static/municipios.json, generado a
partir de MUNICIPIOS_202605.xlsx) y expone una función para resolver el
nombre a partir de (ENT, MUN). Se usa tanto en el formulario (vía fetch en
JS) como en el backend, para mostrar el nombre real del municipio en la
pantalla de resultado y en el PDF, en vez del código numérico crudo.
"""

import json
import os

_RUTA_JSON = os.path.join(os.path.dirname(__file__), "static", "municipios.json")
_catalogo = None


def _cargar():
    global _catalogo
    if _catalogo is None:
        with open(_RUTA_JSON, encoding="utf-8") as f:
            _catalogo = json.load(f)
    return _catalogo


def nombre_municipio(ent, mun) -> str:
    """Regresa 'Nombre del municipio' o, si no se encuentra, el código crudo."""
    try:
        catalogo = _cargar()
        return catalogo[str(int(ent))][str(int(mun))]
    except (KeyError, ValueError, TypeError):
        return str(mun)
