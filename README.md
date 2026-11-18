# Proyecto_kubernetes_k8s

Análisis del comportamiento de una **API de citas médicas** (FastAPI + PostgreSQL) bajo distintos escenarios de despliegue: Docker Compose y Kubernetes (K3s) con 1, 2 y 3 nodos y 1, 2 y 3 réplicas de la API. La carga se genera con JMeter (10, 50 y 100 usuarios) y se analiza en un notebook.

**Autores:** Angela Lozano ([@alalo10](https://github.com/alalo10)) y Juan José Rangel García ([@Juan24rangel](https://github.com/Juan24rangel))
**Curso:** Principios y prácticas de Desarrollo de Software Orientado a Objetos · **Profesor:** Gabriel Rodrigo Pedraza Ferreira

- 📓 **Notebook de análisis (Colab):** https://colab.research.google.com/github/alalo10/Proyecto_kubernetes_k8s/blob/main/notebooks/analisis_despliegues.ipynb
- 📄 **Reporte PDF:** [`report/reporte_final.pdf`](report/reporte_final.pdf)
- 🗒️ **Bitácora del proceso:** [`docs/BITACORA.md`](docs/BITACORA.md)

## Resultado principal

Con 100 usuarios, Compose y las configuraciones de 1 réplica colapsan por *timeout* del pool de conexiones; con 2 o 3 réplicas no hubo errores (515–636 req/s). Pasar de 2 a 3 réplicas o sumar nodos no mejora más allá de la variabilidad del experimento (≈ 25 %). Detalles y limitaciones en el notebook y en el reporte.

## Estructura

| Carpeta | Contenido |
|---|---|
| `app/` | Código de la API, `Dockerfile` y `scripts/seed.py` (datos de prueba) |
| `docker/` | `docker-compose.yml` (Fase 1) |
| `k8s/` | Manifiestos de Kubernetes: espacio de nombres, PostgreSQL y API (Fases 2–4) |
| `jmeter/` | `plan_citas.jmx`, `correr_pruebas.ps1` y `resultados/` (`.jtl` y monitores de CPU) |
| `notebooks/` | `analisis_despliegues.ipynb` |
| `docs/` | `BITACORA.md` |
| `report/` | Reporte PDF |

## Cómo ejecutarlo

Se necesita: Docker; para Kubernetes, K3s; y para las pruebas, Apache JMeter 5.6.3 (Java) en la máquina que genera la carga. Sustituye `<IP_SERVIDOR>` por la IP de la máquina que sirve la app. **Nunca pegues el token de K3s en chats ni en el repositorio.**

### 1. Clonar

```bash
git clone https://github.com/alalo10/Proyecto_kubernetes_k8s.git
cd Proyecto_kubernetes_k8s
```

### 2. Fase 1: Docker Compose

```bash
cd docker
docker compose up -d --build
docker compose exec api python -m scripts.seed          # carga 25.050 filas
curl http://localhost:8000/health                        # debe responder 200
```

Para volver al estado inicial entre pruebas: `docker compose exec api python -m scripts.seed --reset`.

### 3. Fases 2 a 4: Kubernetes (K3s)

**Servidor (control plane)**, en la máquina principal:

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --disable traefik --disable servicelb" sh -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
docker build -t citas-api:1.0 app
docker save citas-api:1.0 | sudo k3s ctr images import -      # la imagen no se descarga de ningún registro
```

En `k8s/10-postgres.yaml`, cambia el valor de `nodeSelector` (`kubernetes.io/hostname`) por el nombre de **tu** nodo servidor (`kubectl get nodes`). Después:

```bash
kubectl apply -f k8s/00-namespace.yaml -f k8s/10-postgres.yaml -f k8s/20-api.yaml
kubectl -n citas rollout status deployment/citas-api
kubectl -n citas exec deploy/citas-api -- python -m scripts.seed
curl http://<IP_SERVIDOR>:30080/health                        # NodePort 30080, debe responder 200
```

**Nodos adicionales (workers)**, en cada VM, con la **misma versión** de K3s que el servidor (`k3s --version`). El token está en el servidor (`sudo cat /var/lib/rancher/k3s/server/node-token`); léelo sin mostrarlo:

```bash
git clone https://github.com/alalo10/Proyecto_kubernetes_k8s.git && cd Proyecto_kubernetes_k8s
docker build -t citas-api:1.0 app
read -rsp "Token: " TOK; echo
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION='<VERSION_K3S>' K3S_URL=https://<IP_SERVIDOR>:6443 K3S_TOKEN="$TOK" sudo -E sh -s - agent
docker save citas-api:1.0 | sudo k3s ctr images import -
```

**Preparar cada escenario** (nodos × réplicas):

```bash
kubectl cordon <nodo-que-no-participa>              # 2 nodos: aislar el tercero; 3 nodos: kubectl uncordon <nodo>
kubectl -n citas scale deployment/citas-api --replicas=0
kubectl -n citas wait --for=delete pod -l app=citas-api --timeout=90s
kubectl -n citas scale deployment/citas-api --replicas=N      # N = 1, 2 o 3
kubectl -n citas rollout status deployment/citas-api
kubectl -n citas get pods -o wide                             # anota en qué nodo cayó cada pod
kubectl -n citas exec deploy/citas-api -- python -m scripts.seed --reset
```

### 4. Pruebas de carga (JMeter)

Desde **otra máquina** (el generador de carga), en PowerShell. El script comprueba `/health`, hace un calentamiento y lanza 10, 50 y 100 usuarios (60 s cada uno):

```powershell
.\jmeter\correr_pruebas.ps1 -Escenario compose    -HostApi <IP_SERVIDOR> -Puerto 8000
.\jmeter\correr_pruebas.ps1 -Escenario k8s-2n-3r  -HostApi <IP_SERVIDOR> -Puerto 30080
```

Nombres válidos: `compose` y `k8s-{1-3}n-{1-3}r`. Los resultados quedan en `jmeter/resultados/{escenario}_u{usuarios}.jtl`. Si PowerShell bloquea el script: `powershell -ExecutionPolicy Bypass -File .\jmeter\correr_pruebas.ps1 ...`. Si JMeter no está en `C:\apache-jmeter-5.6.3`, usa `-JMeter <ruta>\bin\jmeter.bat`.

**Monitor de CPU** (opcional, en la máquina que sirve la app, mientras corre la prueba):

```bash
# Compose
while true; do echo "$(date +%T) $(docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}' | tr '\n' ' ')"; sleep 2; done | tee monitor_compose.txt
# Kubernetes
while true; do echo "$(date +%T) | $(kubectl top pods -n citas --no-headers | awk '{printf "%s %s %s; ", $1, $2, $3}') | $(kubectl top nodes --no-headers | awk '{printf "%s %s %s; ", $1, $2, $3}')"; sleep 10; done | tee monitor_k8s-2n-3r.txt
```

### 5. Análisis

Sube los resultados (`git add jmeter/resultados && git commit && git push`) y abre el [notebook en Colab](https://colab.research.google.com/github/alalo10/Proyecto_kubernetes_k8s/blob/main/notebooks/analisis_despliegues.ipynb): *Entorno de ejecución → Ejecutar todo*. Clona el repositorio y lee los `.jtl` y los monitores.

## Entorno usado en las mediciones

Portátil de Angela (Zorin OS, ~18 hilos, 16 GB): servidor K3s, base de datos y Compose · Portátil de Rangel (Windows): JMeter · 2 VMs Ubuntu (1 CPU, 3,8 GB) como workers. Todo por Wi-Fi / red institucional.
