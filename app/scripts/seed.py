"""Carga datos de prueba: 50 médicos, 5.000 pacientes y 20.000 citas.

Uso (desde la carpeta app/):
    python -m scripts.seed            # carga si la base está vacía
    python -m scripts.seed --reset    # borra todo y vuelve a cargar
"""
import random
import sys
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import text

import models
from database import Base, SessionLocal, engine

N_MEDICOS = 50
N_PACIENTES = 5_000
N_CITAS = 20_000
LOTE = 5_000

ESPECIALIDADES = [
    "Medicina General", "Pediatría", "Cardiología", "Dermatología",
    "Ginecología", "Neurología", "Ortopedia", "Oftalmología",
    "Psiquiatría", "Urología",
]
MOTIVOS = [
    "Control general", "Dolor de cabeza", "Chequeo anual", "Dolor de espalda",
    "Revisión de exámenes", "Fiebre", "Consulta de seguimiento", "Alergia",
    "Dolor abdominal", "Renovación de fórmula",
]


def insertar_por_lotes(db, modelo, filas):
    for i in range(0, len(filas), LOTE):
        db.bulk_insert_mappings(modelo, filas[i:i + LOTE])
        db.commit()


def main():
    random.seed(42)
    Faker.seed(42)
    fake = Faker("es_CO")

    if "--reset" in sys.argv:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        if db.query(models.Cita).count() > 0:
            print("La base ya tiene datos. Use --reset para recargar.")
            return

        print("Insertando médicos...")
        medicos = [
            {"nombre": f"Dr. {fake.name()}", "especialidad": random.choice(ESPECIALIDADES)}
            for _ in range(N_MEDICOS)
        ]
        insertar_por_lotes(db, models.Medico, medicos)

        print("Insertando pacientes...")
        pacientes = [
            {
                "nombre": fake.name(),
                "documento": str(10_000_000 + i),  # único garantizado
                "telefono": fake.phone_number()[:30],
                "correo": f"paciente{i}@correo.com",
            }
            for i in range(N_PACIENTES)
        ]
        insertar_por_lotes(db, models.Paciente, pacientes)

        print("Insertando citas...")
        inicio = datetime(2026, 1, 5, 8, 0)
        usados = set()          # pares (medico_id, fecha_hora) ya ocupados
        citas = []
        estados = list(models.EstadoCita)
        while len(citas) < N_CITAS:
            medico_id = random.randint(1, N_MEDICOS)
            # Franjas de 30 min entre las 8:00 y las 17:30, de lunes a viernes, ~1 año
            dia = inicio + timedelta(days=random.randint(0, 364))
            if dia.weekday() >= 5:
                continue
            fecha_hora = dia + timedelta(minutes=30 * random.randint(0, 19))
            if (medico_id, fecha_hora) in usados:
                continue
            usados.add((medico_id, fecha_hora))
            citas.append({
                "paciente_id": random.randint(1, N_PACIENTES),
                "medico_id": medico_id,
                "fecha_hora": fecha_hora,
                "motivo": random.choice(MOTIVOS),
                "estado": random.choice(estados),
                "creada_en": datetime.utcnow(),
            })
        insertar_por_lotes(db, models.Cita, citas)

        # Reinicia las secuencias por si se usaron ids explícitos (seguridad)
        for tabla in ("medicos", "pacientes", "citas"):
            db.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                f"(SELECT COALESCE(MAX(id), 1) FROM {tabla}))"
            ))
        db.commit()

        print(f"Listo: {N_MEDICOS} médicos, {N_PACIENTES} pacientes, {N_CITAS} citas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
