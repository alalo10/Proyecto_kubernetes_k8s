import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class EstadoCita(str, enum.Enum):
    """Estados posibles de una cita."""
    programada = "programada"
    cancelada = "cancelada"
    completada = "completada"


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, nullable=False, index=True)
    telefono = Column(String(30))
    correo = Column(String(100))

    citas = relationship("Cita", back_populates="paciente")


class Medico(Base):
    __tablename__ = "medicos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(60), nullable=False, index=True)

    citas = relationship("Cita", back_populates="medico")


class Cita(Base):
    __tablename__ = "citas"
    # Regla de negocio a nivel de base de datos: un médico no puede tener
    # dos citas en la misma fecha y hora.
    __table_args__ = (
        UniqueConstraint("medico_id", "fecha_hora", name="uq_medico_fecha_hora"),
    )

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False, index=True)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False, index=True)
    fecha_hora = Column(DateTime, nullable=False, index=True)
    motivo = Column(String(200))
    estado = Column(
        Enum(EstadoCita, name="estado_cita"),
        nullable=False,
        default=EstadoCita.programada,
        index=True,
    )
    creada_en = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("Paciente", back_populates="citas")
    medico = relationship("Medico", back_populates="citas")
