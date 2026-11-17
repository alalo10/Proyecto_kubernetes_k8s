from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.get("", response_model=List[schemas.PacienteSalida])
def listar_pacientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista pacientes con paginación (skip/limit)."""
    return db.query(models.Paciente).order_by(models.Paciente.id).offset(skip).limit(limit).all()


@router.get("/{paciente_id}", response_model=schemas.PacienteSalida)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.get(models.Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@router.post("", response_model=schemas.PacienteSalida, status_code=201)
def crear_paciente(datos: schemas.PacienteCrear, db: Session = Depends(get_db)):
    paciente = models.Paciente(**datos.model_dump())
    db.add(paciente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un paciente con ese documento")
    db.refresh(paciente)
    return paciente


@router.put("/{paciente_id}", response_model=schemas.PacienteSalida)
def actualizar_paciente(paciente_id: int, datos: schemas.PacienteCrear, db: Session = Depends(get_db)):
    paciente = db.get(models.Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(paciente, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un paciente con ese documento")
    db.refresh(paciente)
    return paciente


@router.delete("/{paciente_id}", status_code=204)
def eliminar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.get(models.Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    try:
        db.delete(paciente)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: el paciente tiene citas")
