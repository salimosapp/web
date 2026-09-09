"""
Configuración central de la web pública.

Carga las variables del archivo .env (que NO se sube a GitHub) y las deja
como constantes para que el resto del código las use.

Estas variables apuntan a la MISMA base de datos que usa el panel admin,
así vemos los mismos eventos en ambos lados.
"""

import os
from dotenv import load_dotenv

# Lee el archivo .env y expone sus valores como variables de entorno.
load_dotenv()

# --- Base de datos (PostgreSQL local) ---
# Con el signo "or" ponemos un valor por defecto si el .env no trae alguno.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "berisso_cultura")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")