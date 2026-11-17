from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/medicos", tags=["Médicos"])


@router.get("", response_model=List[schemas.MedicoSalida])
def listar_medicos(
    especialidad: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista médicos; se puede filtrar por especialidad."""
    consulta = db.query(models.Medico)
    if especialidad:
        consulta = consulta.filter(models.Medico.especialidad == especialidad)
    return consulta.order_by(models.Medico.id).offset(skip).limit(limit).all()


@router.get("/{medico_id}", response_model=schemas.MedicoSalida)
def obtener_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = db.get(models.Medico, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico


@router.post("", response_model=schemas.MedicoSalida, status_code=201)
def crear_medico(datos: schemas.MedicoCrear, db: Session = Depends(get_db)):
    medico = models.Medico(**datos.model_dump())
    db.add(medico)
    db.commit()
    db.refresh(medico)
    return medico


@router.put("/{medico_id}", response_model=schemas.MedicoSalida)
def actualizar_medico(medico_id: int, datos: schemas.MedicoCrear, db: Session = Depends(get_db)):
    medico = db.get(models.Medico, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(medico, campo, valor)
    db.commit()
    db.refresh(medico)
    return medico


@router.delete("/{medico_id}", status_code=204)
def eliminar_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = db.get(models.Medico, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    try:
        db.delete(medico)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: el médico tiene citas")
