"""
Conexión a la base de datos.

Esta web solo LEE eventos (no los modifica). Toda la escritura la hace el
panel admin (scraping, aprobación, fuentes...).
"""

import psycopg2
from backend.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_SSLMODE,
)


def conectar():
    """Abre una conexión a PostgreSQL. Cada consulta abre y cierra la suya."""
    parametros = {
        "host": DB_HOST,
        "port": DB_PORT,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    if DB_SSLMODE:
        parametros["sslmode"] = DB_SSLMODE

    return psycopg2.connect(**parametros)