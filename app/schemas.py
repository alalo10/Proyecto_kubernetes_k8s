from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import EstadoCita


# ---------- Pacientes ----------
class PacienteBase(BaseModel):
    nombre: str
    documento: str
    telefono: Optional[str] = None
    correo: Optional[str] = None


class PacienteCrear(PacienteBase):
    pass


class PacienteSalida(PacienteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Médicos ----------
class MedicoBase(BaseModel):
    nombre: str
    especialidad: str


class MedicoCrear(MedicoBase):
    pass


class MedicoSalida(MedicoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Citas ----------
class CitaBase(BaseModel):
    paciente_id: int
    medico_id: int
    fecha_hora: datetime
    motivo: Optional[str] = None
    estado: EstadoCita = EstadoCita.programada


class CitaCrear(CitaBase):
    pass


class CitaActualizar(BaseModel):
    """Todos los campos son opcionales: solo se cambia lo que se envíe."""
    fecha_hora: Optional[datetime] = None
    motivo: Optional[str] = None
    estado: Optional[EstadoCita] = None


class CitaSalida(CitaBase):
    id: int
    creada_en: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
