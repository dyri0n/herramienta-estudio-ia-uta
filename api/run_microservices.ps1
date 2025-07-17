#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configurar directorio de logs
$logDir = Join-Path $PWD "logs"
if (-not (Test-Path $logDir -PathType Container)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
    Write-Host "Directorio de logs creado: $logDir"
}

# Buscar entorno virtual
$venv_dir = if (Test-Path ".venv" -PathType Container) { 
    Resolve-Path ".venv"
} else { 
    Get-ChildItem -Directory -Filter "*venv" | Select-Object -First 1 -ExpandProperty FullName 
}

if (-not $venv_dir) {
    Write-Error "Error: Directorio de entorno virtual no encontrado. Por favor, cree uno con terminación *venv."
    exit 1
}

# Activar entorno virtual
if (Test-Path "$venv_dir\Scripts\Activate.ps1") {
    & "$venv_dir\Scripts\Activate.ps1"
    Write-Host "Entorno virtual activado: $venv_dir"
} else {
    Write-Error "No se encontró el script de activación en $venv_dir"
    exit 1
}

# Verificar directorio de microservicios
$MICROSERVICES_DIR = Join-Path $PWD "microservices"
if (-not (Test-Path $MICROSERVICES_DIR -PathType Container)) {
    Write-Error "Error: Directorio de microservicios no encontrado"
    exit 2
}

# Iniciar microservicios con logging y cambio de directorio
$jobs = @()
Get-ChildItem -Path $MICROSERVICES_DIR -Recurse -Filter "register.json" | ForEach-Object {
    $registerFile = $_.FullName
    $serviceDir = $_.Directory.FullName
    
    $json = Get-Content $registerFile | ConvertFrom-Json
    
    $svc = $json.microservice
    $ip = $json.ip
    $port = $json.port

    if (-not $svc -or -not $ip -or -not $port) {
        Write-Host "Faltan datos en $registerFile" -ForegroundColor Yellow
        return
    }

    # Crear nombre de archivo de log
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logFile = Join-Path $logDir "${svc}_${port}_${timestamp}.log"
    
    Write-Host "Iniciando $svc en ${ip}:$port"
    Write-Host "  Directorio: $serviceDir"
    Write-Host "  Log: $logFile"
    
    # Comando completo con log
    $command = "uvicorn microservice:app --host $ip --port $port"
    Write-Host "  Comando: $command"
    
    # Guardar metadatos del servicio
    @{
        Service = $svc
        IP = $ip
        Port = $port
        Command = $command
        LogFile = $logFile
        StartTime = (Get-Date)
        Directory = $serviceDir
    } | Export-Clixml (Join-Path $logDir "${svc}_meta.xml")
    
    # Ejecutar en nueva ventana con cambio de directorio y logging
    $jobs += Start-Process pwsh -ArgumentList @(
        "-NoExit",
        "-Command", "Set-Location '$serviceDir'; $command *> '$logFile'"
    ) -PassThru
}

# Generar resumen
Write-Host "`nResumen de microservicios:"
$jobs | ForEach-Object {
    $id = $_.Id
    Write-Host "  - PID $id"
}

Write-Host "`nMicroservicios iniciados: $($jobs.Count)"
Write-Host "Logs guardados en: $logDir"
Write-Host "Presiona Ctrl+C para detener este script (los microservicios continuarán)"
Write-Host "Cierra las ventanas individuales para detener cada microservicio`n"

# Mantener script corriendo
try {
    while ($true) {
        Start-Sleep -Seconds 5
        # Opcional: agregar aquí monitoreo de estado
    }
}
finally {
    Write-Host "Script principal detenido"
}