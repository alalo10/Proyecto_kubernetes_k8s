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


## 6. Paso 4: Aplicación y base de datos de prueba

**Qué hicimos:**
- Implementamos la API en `app/` (FastAPI + SQLAlchemy + PostgreSQL 16): `main.py`, `models.py`, `schemas.py`, `database.py` y los routers de pacientes, médicos y citas.
- Probamos la API en local con `uvicorn`: crear paciente, médico y cita respondió `201`, y repetir la misma cita (mismo médico y fecha) respondió `409`.
- Creamos `scripts/seed.py`, que carga 50 médicos, 5.000 pacientes y 20.000 citas (25.050 filas) y admite `--reset` para volver al estado inicial.

**Por qué:** una API con datos suficientes hace que las consultas tarden lo bastante como para que la carga se note, y `--reset` permite que cada escenario parta de la misma base.

**Decisiones de diseño que afectan a las pruebas:**
- Un solo proceso `uvicorn` por contenedor (sin workers): así una réplica equivale, aproximadamente, a un núcleo.
- Pool de conexiones por réplica de 10 + 20 de desborde (30 en total) y `pool_timeout` de 30 s (valor por defecto de SQLAlchemy).
- Listados paginados y restricción única (médico, fecha y hora) con comprobación previa (`409`).
- No se modifica el código de la app durante la serie de pruebas, para que los escenarios sean comparables.

## 7. Paso 5: Docker y Docker Compose (Fase 1)

**Qué hicimos:** instalamos Docker en Zorin, escribimos el `Dockerfile` (python:3.12-slim) y `docker/docker-compose.yml` con dos servicios: `db` (postgres:16 con *healthcheck* y volumen) y `api` (construida desde `app/`, puerto 8000).

**Incidente:** `permission denied` al usar el socket de Docker. **Solución:** `newgrp docker` (o cerrar sesión y volver a entrar) para que el grupo `docker` surta efecto.

## 8. Paso 6: Reparto de máquinas

| Máquina | Rol |
|---|---|
| Portátil de Angela (Zorin OS, 16 GB) | Sirve la app: Docker Compose y control plane de K3s; aloja siempre la base de datos |
| Portátil de Rangel (Windows, 24 GB) | Generador de carga (JMeter), siempre el mismo |
| VM `agente1` (Ubuntu, 1 CPU, 3,8 GB) | Nodo worker de K3s |
| VM `gp19` (Ubuntu, 1 CPU, 3,8 GB) | Nodo worker de K3s |

Las VMs son compartidas con otras prácticas, por lo que su rendimiento puede variar. Todas las máquinas están en la misma red; el tráfico del generador de carga y el de las VMs hacia el Zorin pasa por Wi-Fi o red institucional (ping medio desde las VMs al Zorin: 50 ms en `agente1` y 43 ms en `gp19`, con picos de hasta 117 ms).

## 9. Paso 7: Plan de pruebas JMeter

**Qué hicimos:** generamos `jmeter/plan_citas.jmx`, parametrizado (`host`, `puerto`, `usuarios`, `rampa`, `duracion`), con una mezcla de peticiones ponderada: 30 % `GET /citas` (listado), 30 % `GET /citas/{id}` (consulta de una cita), 20 % `GET /citas` con filtro (médico y estado) y 20 % `POST /citas` (creación). Sin tiempo de espera entre peticiones. Y `jmeter/correr_pruebas.ps1`, que ejecuta la batería de un escenario: comprobación de `/health`, calentamiento, y tres niveles de carga.

**Incidentes con PowerShell:**
- `-Jhost=10.14.70.124` se partía en el primer punto: los argumentos `-J` se pasan como cadenas entre comillas.
- Los avisos de Java por `stderr` provocaban `NativeCommandError` con `$ErrorActionPreference = "Stop"`: se cambió a `Continue` mientras corre JMeter y se comprueba el código de salida.
- Angela copió primero una versión antigua del script; se detectó con `git status` limpio y se corrigió descargando de nuevo y verificando con `grep`.

## 10. Paso 8: Metodología

- Calentamiento de 15 s con 10 usuarios (no se guarda).
- Tres niveles: **10, 50 y 100 usuarios**, 60 s cada uno con 10 s de rampa.
- **Una repetición** por prueba. Antes de cada escenario se reinicia el *seed*.
- En el análisis se descartan los primeros 15 s. El criterio usa el instante en que **termina** cada petición, para que las que se quedan bloqueadas por *timeout* no desaparezcan cuando el sistema colapsa.
- Métricas: throughput (req/s), media, p50, p95 y p99, y porcentaje de errores.
- Convención de nombres: `jmeter/resultados/{escenario}_u{usuarios}.jtl` con los escenarios `compose` y `k8s-{1-3}n-{1-3}r`, y `monitor_{escenario}.txt` para la CPU.

## 11. Paso 9: Fase 1, Docker Compose (resultados)

| Usuarios | Throughput | Media | Errores |
|---|---|---|---|
| 10 | 344 req/s | 29 ms | 0 % |
| 50 | 333 req/s | 150 ms | 0 % |
| 100 | 35 req/s sostenido (100 req/s en toda la prueba) | 3.023 ms | 9,5 % |

**Hallazgo:** a 100 usuarios el sistema se bloquea por episodios: todos los usuarios se quedan esperando a la vez los 30 s del `pool_timeout`, de ahí que los errores salgan en múltiplos de 100. En los registros de la API se confirmó el mensaje de SQLAlchemy sobre el pool agotado (`QueuePool limit … connection timed out`). Es un hallazgo del experimento, no un fallo de configuración, y no se corrigió en el código para no romper la comparación entre escenarios.

**Corrección de una explicación:** el error de JMeter es `SocketTimeoutException` (el servidor tarda más de 30 s en responder); JMeter no "se cuelga".

## 12. Paso 10: Notebook y diapositivas

Se creó `notebooks/analisis_despliegues.ipynb` (Colab) que clona el repositorio, lee los `.jtl` y los archivos del monitor, y genera las tablas, gráficas, hallazgos y conclusiones. También se preparó la presentación (12 láminas en gama azul).

**Corrección importante de método:** la primera versión del notebook calculaba el throughput contando las peticiones que *empezaban* después de los 15 s, lo que inflaba la cifra en las pruebas con colapso (por ejemplo 551 req/s en lugar de 35 para Compose a 100 usuarios). Se cambió a *peticiones terminadas* y se validó que el rendimiento de la prueba completa coincide con el resumen de JMeter. Los hallazgos automáticos y la tabla de "eficiencia" originales se sustituyeron, porque comparaban contra pruebas colapsadas y daban porcentajes sin sentido.

## 13. Paso 11: K3s con un nodo (Fase 2)

**Qué hicimos:**
- Había restos de instalaciones anteriores de K3s en el Zorin y en `gp19`. Se desinstalaron (con acuerdo de sus dueños) y se dejó el *control plane* en el Zorin.
- Instalamos K3s en el Zorin con `traefik` y `servicelb` desactivados (no se usan).
- Importamos la imagen: `docker save citas-api:1.0 | sudo k3s ctr images import -`.
- Aplicamos `k8s/`: espacio de nombres `citas`, PostgreSQL (Deployment con 1 réplica, *Recreate*, PVC de 2 GB, `nodeSelector` al Zorin) y la API (Deployment + Service NodePort 30080).
- Cargamos el *seed* dentro del clúster y comprobamos el acceso por NodePort desde el portátil de Rangel.
- Monitor: `kubectl top pods` y `kubectl top nodes` cada 10 s (K3s trae `metrics-server`).

**Decisión:** la API solo tiene `startupProbe`. Con *readiness* o *liveness*, `/health` fallaría bajo sobrecarga y Kubernetes retiraría el pod del servicio, lo que alteraría el experimento.

## 14. Paso 12: Añadir las VMs como nodos (Fases 3 y 4)

**Qué hicimos:** unimos `agente1` y `gp19` como workers (`K3S_URL=https://<IP del Zorin>:6443` y el token del servidor, con la misma versión de K3s) y cargamos la imagen en cada VM (`docker build` desde el repo y `docker save | k3s ctr images import`).

**Incidentes:**
- Una primera instalación se lanzó con las palabras literales `VERSION` y `TOKEN` en lugar de sus valores y falló al descargar; no se instaló nada.
- `agente1` tenía un **servidor K3s previo** (ocupaba los puertos 6443, 6444 y 10250); el agente no podía arrancar (`bind: address already in use`). Con permiso de su dueña se desinstaló (`k3s-uninstall.sh`) y se reinstaló como agente.
- El agente quedó en bucle con `not authorized`: el token se había pegado mal. Se resolvió leyéndolo oculto (`read -rsp`) y comprobando su longitud (108) contra el original, sin mostrarlo.
- `gp19` usa `sh` en lugar de `bash`, que no admite `read -s`; se abrió `bash`.
- **Seguridad:** el token de unión nunca se pegó completo en el chat ni en el repositorio.

## 15. Paso 13: Escenarios multi-nodo

- **2 nodos:** Zorin + `agente1`; `gp19` queda aislado con `kubectl cordon gp19`. **3 nodos:** `uncordon` y los tres trabajan.
- Antes de cada escenario se escala a 0 y luego a N réplicas, para que el reparto (`topologySpreadConstraints`, `maxSkew: 1`) parta de cero.
- **Ajuste de configuración:** se añadió `nodeTaintsPolicy: Honor` a la regla de reparto. Sin él, el nodo aislado cuenta como un dominio con 0 pods y la tercera réplica de `2n-3r` habría quedado en `Pending`.
- El planificador decide dónde cae cada pod:

| Escenario | Pods de la API |
|---|---|
| 1n-1r, 1n-2r, 1n-3r | todos en el Zorin |
| 2n-1r | 1 en el Zorin (equivalente a 1n-1r) |
| 2n-2r | 1 Zorin + 1 `agente1` |
| 2n-3r | 2 Zorin + 1 `agente1` |
| 3n-1r | 1 en el Zorin (equivalente a 1n-1r) |
| 3n-2r | 1 Zorin + 1 `gp19` |
| 3n-3r | 1 Zorin + 1 `agente1` + 1 `gp19` |

**Cuándo subir resultados:** el generador (Rangel) sube los `.jtl` primero, con `git pull --rebase` antes del push, y después el Zorin sube el monitor. El monitor se detiene solo cuando Rangel indica que salió `Listo`.

## 16. Resultados de las 30 pruebas

Throughput sostenido (req/s) por escenario y número de usuarios:

| Escenario | 10 usuarios | 50 usuarios | 100 usuarios |
|---|---|---|---|
| Compose | 344 | 333 | 35 (9,5 % errores) |
| K8s 1N-1R | 259 | 421 | 42 (7,3 % errores) |
| K8s 1N-2R | 330 | 256 | 596 |
| K8s 1N-3R | 392 | 693 | 619 |
| K8s 2N-1R | 225 | 252 | 185 (0,7 % errores) |
| K8s 2N-2R | 180 | 379 | 515 |
| K8s 2N-3R | 301 | 659 | 626 |
| K8s 3N-1R | 251 | 360 | 6 (57,0 % errores) |
| K8s 3N-2R | 302 | 521 | 636 |
| K8s 3N-3R | 392 | 519 | 595 |

Las tablas completas (media, p95 y errores) y las gráficas están en el notebook y en el reporte PDF.

## 17. Hallazgos

1. **Una réplica no soporta 100 usuarios** (Compose y las tres configuraciones de 1 réplica colapsan por *timeout*). Con 2 o 3 réplicas no hubo errores a 100 usuarios: 515–636 req/s.
2. **Escalabilidad sublineal.** De 2 a 3 réplicas la mejora (+4 %, +22 %, −6 % según el número de nodos) está dentro de la variabilidad medida.
3. **Las VMs no mejoraron el rendimiento** ni lo empeoraron de forma visible, pese a la latencia de red hacia la base de datos.
4. **Variabilidad grande:** tres configuraciones equivalentes (1 pod en el Zorin) dieron 421, 252 y 360 req/s a 50 usuarios (coeficiente de variación ≈ 25 %). Diferencias de ese tamaño entre escenarios no son concluyentes.
5. **Cuello de botella:** cada pod satura aproximadamente un núcleo (1100–1320 m), pero ningún nodo llegó a su límite en el estancamiento de ~600 req/s. Candidatos, sin verificar: el generador de carga, la red o PostgreSQL.
6. **Compose y Kubernetes** se comportan igual con los mismos recursos; no se detecta un sobrecoste de la orquestación.

## 18. Lecciones aprendidas

- Los tokens y credenciales nunca se pegan en chats ni en el repositorio; si se exponen, se revocan.
- Antes de borrar una instalación ajena (K3s previo), se comprueba qué hay dentro y se pide permiso.
- Una sola repetición no basta para distinguir un efecto real de la variabilidad del entorno: hay que repetir cada prueba al menos tres veces.
- Una métrica mal definida puede dar números que parecen razonables y son falsos; se valida contra una cifra independiente (aquí, el resumen de JMeter).
- Reiniciar la base entre niveles de carga (no solo entre escenarios) evitaría medir los 100 usuarios sobre la base más grande.
