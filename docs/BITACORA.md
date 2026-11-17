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
