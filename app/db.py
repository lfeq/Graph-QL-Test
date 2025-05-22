import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv() # Carga variables desde .env

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for SQLAlchemy")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()

# Dependencia para obtener una sesión de BD en las rutas/resolvers
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Descomentar para borrar tablas al inicio (cuidado!)
        await conn.run_sync(Base.metadata.create_all)