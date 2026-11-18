<#
.SYNOPSIS
  Lanza la bateria de pruebas JMeter para UN escenario de despliegue.

.DESCRIPTION
  1. Comprueba que la app responde en /health.
  2. Calentamiento (no se guarda): 10 usuarios durante 15 s.
  3. Tres niveles de carga (10, 50 y 100 usuarios), 60 s cada uno con 10 s de rampa.
  4. Guarda cada prueba en jmeter\resultados\{escenario}_u{usuarios}.jtl

  Nombres de escenario validos:
    compose
    k8s-{nodos}n-{replicas}r    (nodos y replicas entre 1 y 3), por ejemplo k8s-2n-3r

.EXAMPLE
  .\jmeter\correr_pruebas.ps1 -Escenario compose
  .\jmeter\correr_pruebas.ps1 -Escenario k8s-1n-2r -HostApi 10.14.70.124 -Puerto 8000

  Si PowerShell bloquea el script por la politica de ejecucion:
  powershell -ExecutionPolicy Bypass -File .\jmeter\correr_pruebas.ps1 -Escenario compose
#>
param(
    [Parameter(Mandatory = $true)][string]$Escenario,
    [string]$HostApi = "10.14.70.124",
    [int]$Puerto = 8000,
    [string]$JMeter = "C:\apache-jmeter-5.6.3\bin\jmeter.bat",
    [int[]]$Niveles = @(10, 50, 100),
    [int]$Duracion = 60,
    [int]$Rampa = 10,
    [int]$CalentamientoSeg = 15,
    [int]$PausaSeg = 10
)

$ErrorActionPreference = "Stop"

if ($Escenario -notmatch '^(compose|k8s-[123]n-[123]r)$') {
    throw "Escenario invalido: '$Escenario'. Use 'compose' o 'k8s-{1-3}n-{1-3}r' (ej. k8s-2n-3r)."
}
if (-not (Test-Path $JMeter)) {
    throw "No se encuentra JMeter en $JMeter. Use el parametro -JMeter con la ruta correcta."
}

$Plan = Join-Path $PSScriptRoot "plan_citas.jmx"
$Salida = Join-Path $PSScriptRoot "resultados"
New-Item -ItemType Directory -Force -Path $Salida | Out-Null

# --- 1. La app debe responder antes de empezar
$urlSalud = "http://${HostApi}:${Puerto}/health"
try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $urlSalud -TimeoutSec 5
} catch {
    throw "La app no responde en $urlSalud. Revise que este arriba y que la IP sea correcta."
}
if ($resp.StatusCode -ne 200) { throw "/health devolvio $($resp.StatusCode)" }
Write-Host "App OK en $urlSalud" -ForegroundColor Green

# --- Funcion que ejecuta una prueba; los argumentos -J van como cadenas
#     (asi PowerShell no los parte en el primer punto de la IP)
function Invoke-Prueba {
    param([int]$Usuarios, [int]$RampaSeg, [int]$DuracionSeg, [string]$Jtl)

    $argumentos = @("-n", "-t", $Plan)
    if ($Jtl) {
        if (Test-Path $Jtl) { Remove-Item $Jtl -Force }
        $argumentos += @("-l", $Jtl)
    }
    $argumentos += @(
        "-Jhost=$HostApi",
        "-Jpuerto=$Puerto",
        "-Jusuarios=$Usuarios",
        "-Jrampa=$RampaSeg",
        "-Jduracion=$DuracionSeg"
    )

    & $JMeter @argumentos 2>&1 | Where-Object { $_ -match "summary =" } | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { throw "JMeter termino con codigo $LASTEXITCODE" }
}

Write-Host "=== Escenario: $Escenario ===" -ForegroundColor Cyan

# --- 2. Calentamiento (no se registra)
Write-Host "Calentamiento: 10 usuarios, $CalentamientoSeg s (no se guarda)"
Invoke-Prueba -Usuarios 10 -RampaSeg 3 -DuracionSeg $CalentamientoSeg -Jtl ""
Start-Sleep -Seconds $PausaSeg

# --- 3. Niveles de carga
foreach ($u in $Niveles) {
    $jtl = Join-Path $Salida ("{0}_u{1}.jtl" -f $Escenario, $u)
    Write-Host "Prueba: $u usuarios, $Duracion s (rampa $Rampa s) -> $jtl"
    Invoke-Prueba -Usuarios $u -RampaSeg $Rampa -DuracionSeg $Duracion -Jtl $jtl

    $datos = Import-Csv $jtl
    $total = @($datos).Count
    $errores = @($datos | Where-Object { $_.success -eq "false" }).Count
    Write-Host ("  -> {0} peticiones, {1} con error" -f $total, $errores) -ForegroundColor Yellow
    Start-Sleep -Seconds $PausaSeg
}

Write-Host "Listo. Resultados en $Salida" -ForegroundColor Green
Write-Host "Siguiente: git add jmeter/resultados ; git commit ; git push"
