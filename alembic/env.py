# --- al comienzo del archivo env.py, importa lo necesario ---
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine            # >>> para crear engine síncrono
from alembic import context
from dotenv import load_dotenv                  # >>> para cargar .env

# 1. Carga .env
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 2. Añade el proyecto a sys.path para poder importar tus modelos
#    Asumimos que alembic/ está en la raíz, y el código de tu app está en ./app/
PROJECT_DIR = os.path.join(BASE_DIR, 'app')    # Ajusta si tu carpeta de código está en otra ruta
sys.path.insert(0, PROJECT_DIR)

# 3. Importa el metadata de tus modelos
#    Por ejemplo, si tus modelos están en app/models.py:
from app.db import Base    # Base proviene de db.py
import app.models

print("MODELOS REGISTRADOS:", Base.metadata.tables.keys())

# --- resto del env.py generado por alembic ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 4. Remover/ignorar config.set_main_option('sqlalchemy.url', ...) automático
#    En lugar de basarse en la línea "sqlalchemy.url" de alembic.ini, le pasamos el URL aquí:
target_metadata = Base.metadata

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Obtén la URL síncrona desde la variable de entorno:
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL_DOCKER")
#SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL") # Descomentar cuando se corre en local
if not SYNC_DATABASE_URL:
    raise ValueError("No se encontró SYNC_DATABASE_URL en .env. Alembic necesita un URL síncrono.")

# Definimos una función helper para context.configure
def run_migrations_offline():
    """Run migrations in 'offline' mode (sin conexión)."""
    url = SYNC_DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations en 'online' mode (con conexión)."""
    connectable = create_engine(
        SYNC_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
