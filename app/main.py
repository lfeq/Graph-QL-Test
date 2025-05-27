import asyncio
import os
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from ariadne.asgi import GraphQL
from dotenv import load_dotenv

from .schema import schema
from .db import create_tables, get_db_session, AsyncSessionLocal # Importar AsyncSessionLocal
from .background import image_generation_worker

load_dotenv()

STATIC_FILES_DIR = os.getenv("STATIC_FILES_DIR", "static")

# Función de contexto para GraphQL, para inyectar la sesión de BD
async def get_context_value(request):
    # Crear una nueva sesión para cada solicitud GraphQL
    async with AsyncSessionLocal() as session:
        return {"request": request, "db": session}

# Crear la aplicación GraphQL con el contexto
graphql_app = GraphQL(schema, context_value=get_context_value)


async def startup():
    print("Aplicación iniciándose...")
    await create_tables() # Crear tablas de la base de datos si no existen
    # Iniciar el worker de generación de imágenes en segundo plano
    asyncio.create_task(image_generation_worker())
    print("Worker de generación de imágenes iniciado.")

async def shutdown():
    print("Aplicación apagándose...")
    # Aquí podrías añadir lógica para cerrar conexiones o tareas pendientes.

# Configuración de CORS
middleware = [
    Middleware(CORSMiddleware, allow_origins=["https://example.com"], allow_methods=['*'], allow_headers=['*'])
]

# Rutas de la aplicación
routes = [
    Route("/graphql", graphql_app, methods=["GET", "POST", "OPTIONS"]), # Endpoint GraphQL
    Mount(f"/{STATIC_FILES_DIR}", app=StaticFiles(directory=STATIC_FILES_DIR), name="static")
]

# Crear la aplicación Starlette
app = Starlette(
    routes=routes,
    on_startup=[startup],
    on_shutdown=[shutdown],
    middleware=middleware
)