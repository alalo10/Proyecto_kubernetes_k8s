from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/citas", tags=["Citas"])


def _medico_ocupado(db: Session, medico_id: int, fecha_hora: datetime, excluir_id: Optional[int] = None) -> bool:
    """Devuelve True si el médico ya tiene una cita programada a esa fecha y hora."""
    consulta = db.query(models.Cita.id).filter(
        models.Cita.medico_id == medico_id,
        models.Cita.fecha_hora == fecha_hora,
    )
    if excluir_id is not None:
        consulta = consulta.filter(models.Cita.id != excluir_id)
    return consulta.first() is not None


@router.get("", response_model=List[schemas.CitaSalida])
def listar_citas(
    medico_id: Optional[int] = None,
    paciente_id: Optional[int] = None,
    estado: Optional[models.EstadoCita] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista citas con filtros opcionales y paginación."""
    consulta = db.query(models.Cita)
    if medico_id is not None:
        consulta = consulta.filter(models.Cita.medico_id == medico_id)
    if paciente_id is not None:
        consulta = consulta.filter(models.Cita.paciente_id == paciente_id)
    if estado is not None:
        consulta = consulta.filter(models.Cita.estado == estado)
    if fecha_desde is not None:
        consulta = consulta.filter(models.Cita.fecha_hora >= datetime.combine(fecha_desde, time.min))
    if fecha_hasta is not None:
        consulta = consulta.filter(models.Cita.fecha_hora <= datetime.combine(fecha_hasta, time.max))
    return consulta.order_by(models.Cita.id).offset(skip).limit(limit).all()


@router.get("/{cita_id}", response_model=schemas.CitaSalida)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.get(models.Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita


@router.post("", response_model=schemas.CitaSalida, status_code=201)
def crear_cita(datos: schemas.CitaCrear, db: Session = Depends(get_db)):
    if not db.get(models.Paciente, datos.paciente_id):
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    if not db.get(models.Medico, datos.medico_id):
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    if _medico_ocupado(db, datos.medico_id, datos.fecha_hora):
        raise HTTPException(status_code=409, detail="El médico ya tiene una cita en esa fecha y hora")

    cita = models.Cita(**datos.model_dump())
    db.add(cita)
    try:
        db.commit()
    except IntegrityError:
        # Respaldo: dos peticiones simultáneas pudieron pasar la validación anterior.
        db.rollback()
        raise HTTPException(status_code=409, detail="El médico ya tiene una cita en esa fecha y hora")
    db.refresh(cita)
    return cita


@router.put("/{cita_id}", response_model=schemas.CitaSalida)
def actualizar_cita(cita_id: int, datos: schemas.CitaActualizar, db: Session = Depends(get_db)):
    cita = db.get(models.Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    cambios = datos.model_dump(exclude_unset=True)
    nueva_fecha = cambios.get("fecha_hora")
    if nueva_fecha is not None and _medico_ocupado(db, cita.medico_id, nueva_fecha, excluir_id=cita.id):
        raise HTTPException(status_code=409, detail="El médico ya tiene una cita en esa fecha y hora")

    for campo, valor in cambios.items():
        setattr(cita, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El médico ya tiene una cita en esa fecha y hora")
    db.refresh(cita)
    return cita


@router.delete("/{cita_id}", status_code=204)
def eliminar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.get(models.Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.delete(cita)
    db.commit()
