# Bitácora del Proyecto

Proyecto final: Análisis del comportamiento de aplicaciones bajo diferentes
escenarios de despliegue (Docker Compose y Kubernetes).

**Autores:** Angela Lozano (alalo10) y Juan José Rangel García
**Curso:** Principios y prácticas de Desarrollo de Software Orientado a Objetos

---

## 1. Objetivo del proyecto

Desplegar una misma aplicación (gestión de citas médicas) en distintos
escenarios (Docker Compose, Kubernetes con 1, 2 y 3 nodos, variando
réplicas) y medir con JMeter el tiempo medio de respuesta y el throughput
para analizar su escalabilidad.

## 2. Paso 1: Repositorio y Git

**Qué hicimos:**
- Instalamos Git en Zorin OS.
- Configuramos la identidad de Git (nombre y correo).
- Creamos el repositorio público `Proyecto_kubernetes_k8s` en GitHub con
  README, .gitignore de Python y licencia MIT.
- Agregamos a Rangel como colaborador.
- Clonamos el repositorio en la máquina de Angela.

**Por qué:**
- Git permite versionar el trabajo y colaborar sin perder cambios.
- Un repositorio público facilita la revisión por parte del profesor.
- Para subir cambios (`git push`) se usa un token de acceso personal; nunca
  se comparte ni se sube al repositorio.

## 3. Paso 2: Estructura de carpetas

| Carpeta | Contenido |
|---------|-----------|
| docs/ | Bitácora y documentación |
| app/ | Código de la app de citas médicas y su Dockerfile |
| docker/ | docker-compose.yml (Fase 1) |
| k8s/ | Archivos YAML de Kubernetes (Fases 2, 3 y 4) |
| jmeter/ | Planes de prueba y resultados |
| notebooks/ | Notebook de Jupyter/Colab con el análisis |
| report/ | Reporte PDF final |

**Por qué:** separar por responsabilidad hace el repo ordenado y fácil de
evaluar, y coincide con el formato de entrega pedido.


## 4. Incidente: error 403 al hacer el primer push

**Qué pasó:** `git push` devolvió `403 Permission denied` aunque el usuario era
correcto.

**Causa:** el token de acceso personal no tenía el permiso (scope) `repo`.

**Solución:** se creó un token nuevo de tipo *classic* con el scope `repo`.
Clonar un repo público no pide credenciales; solo el `push` las exige.

**Lección:** los tokens nunca se pegan en chats ni en el repositorio. Si se
expone uno, se revoca de inmediato.

## 5. Paso 3: Diseño de la aplicación de citas médicas

### Requisitos del proyecto que la app debe cumplir
- Backend con lógica significativa.
- API REST (para poder probarla con JMeter).
- Persistencia en base de datos.
- Mínimo 10.000 registros.

### Tecnologías elegidas
| Tecnología | Para qué |
|------------|----------|
| Python + FastAPI | Backend y API REST, con documentación automática |
| PostgreSQL | Base de datos relacional |
| Docker / Docker Compose | Empaquetado y despliegue en Fase 1 |
| Kubernetes | Despliegue escalable en Fases 2, 3 y 4 |

**Por qué:** FastAPI es sencillo y rápido; PostgreSQL es robusta y muy usada
con contenedores; ambos se despliegan fácilmente en Docker y Kubernetes.

### Entidades (tablas)
- **Pacientes:** nombre, documento, teléfono, correo.
- **Médicos:** nombre, especialidad.
- **Citas:** paciente, médico, fecha y hora, motivo, estado
  (programada, cancelada, completada).

### Endpoints REST
| Método | Ruta | Función |
|--------|------|---------|
| GET | /citas | Listar citas (con filtros) |
| GET | /citas/{id} | Ver una cita |
| POST | /citas | Crear cita |
| PUT | /citas/{id} | Actualizar cita |
| DELETE | /citas/{id} | Eliminar cita |
| GET/POST/PUT/DELETE | /pacientes, /medicos | CRUD equivalente |
| GET | /health | Verificación de salud (Kubernetes) |

### Lógica de negocio
- Un médico no puede tener dos citas en la misma fecha y hora.
- Las citas se pueden filtrar por médico, paciente, fecha y estado.

### Datos de prueba
Un script cargará más de 10.000 registros (citas, pacientes y médicos) para
cumplir el requisito y hacer significativas las pruebas de carga.
