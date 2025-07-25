@echo off
set BASE_DIR=%~dp0
set PYTHONPATH=%BASE_DIR%api;%PYTHONPATH%

REM Crear y activar entorno virtual para el backend
cd /d "%BASE_DIR%api"
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Iniciar microservicios
start "QGQA" cmd /k "cd /d "%BASE_DIR%api" && call venv\Scripts\activate && uvicorn microservices.qgqa.microservice:app --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak >nul

start "Translate" cmd /k "cd /d "%BASE_DIR%api" && call venv\Scripts\activate && uvicorn microservices.translate.microservice:app --host 0.0.0.0 --port 8002"
timeout /t 2 /nobreak >nul

start "Summarizer" cmd /k "cd /d "%BASE_DIR%api" && call venv\Scripts\activate && uvicorn microservices.summarizer.microservice:app --host 0.0.0.0 --port 8003"
timeout /t 2 /nobreak >nul

REM Iniciar API principal
start "Main API" cmd /k "cd /d "%BASE_DIR%api" && call venv\Scripts\activate && uvicorn main:app --port 8000 --reload"

REM Frontend
cd /d "%BASE_DIR%frontend"
if not exist node_modules (
    echo Instalando dependencias de frontend...
    npm install
)
start "Frontend" cmd /k "cd /d "%BASE_DIR%frontend" && npm run dev"

echo Proyecto iniciado! Accede en http://localhost:3000
pause