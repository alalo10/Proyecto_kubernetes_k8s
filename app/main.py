import time

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from routers import citas, medicos, pacientes

app = FastAPI(
    title="API de Citas Médicas",
    description="Proyecto final: análisis de despliegue con Docker y Kubernetes",
    version="1.0.0",
)


@app.on_event("startup")
def crear_tablas():
    """Crea las tablas al arrancar. Reintenta por si PostgreSQL aún no está listo."""
    for intento in range(1, 11):
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
            return
        except OperationalError:
            print(f"Base de datos no disponible (intento {intento}/10), reintentando en 3 s...")
            time.sleep(3)
    raise RuntimeError("No se pudo conectar a la base de datos")


app.include_router(pacientes.router)
app.include_router(medicos.router)
app.include_router(citas.router)


@app.get("/", tags=["General"])
def raiz():
    return {"mensaje": "API de Citas Médicas funcionando", "docs": "/docs"}


@app.get("/health", tags=["General"])
def health(db: Session = Depends(get_db)):
    """Verifica que la app y la base de datos respondan."""
    db.execute(text("SELECT 1"))
    return {"estado": "ok"}
