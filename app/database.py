import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# La URL se lee de una variable de entorno para poder cambiarla entre
# Docker Compose y Kubernetes sin tocar el código.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://citas_user:citas_pass@localhost:5432/citas_db",
)

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Entrega una sesión de base de datos por petición y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
