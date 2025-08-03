@echo off
setlocal enabledelayedexpansion
set BASE_DIR=%~dp0
set PYTHONPATH=%BASE_DIR%api;%PYTHONPATH%
set ERROR_FLAG=0

title Iniciando Proyecto NLP

:: Backend Setup
cd /d "%BASE_DIR%api"
if not exist .venv (
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Fallo al crear entorno virtual
        set ERROR_FLAG=1
        goto :error_handling
    )
)

call .venv\Scripts\activate

:: Instalar dependencias básicas
python -m pip install --upgrade pip

:: Instalar dependencias principales
if exist "%BASE_DIR%api\requirements.txt" (
    echo Instalando dependencias desde requirements.txt...
    pip install -r "%BASE_DIR%api\requirements.txt" --upgrade
)

:: Instalar dependencias críticas como respaldo
echo Instalando dependencias críticas...
pip install torch==2.7.1 transformers==4.40.0 sentence-transformers==2.7.0 --upgrade

:: Iniciar servicios
start "NLP-QGQA" cmd /k "cd /d "%BASE_DIR%api" && call .venv\Scripts\activate && set PYTHONPATH=%BASE_DIR%api && uvicorn microservices.qgqa.microservice:app --host 0.0.0.0 --port 8001 --app-dir %BASE_DIR%api/microservices/qgqa"
timeout /t 5 /nobreak >nul

start "NLP-Summarizer" cmd /k "cd /d "%BASE_DIR%api" && call .venv\Scripts\activate && set PYTHONPATH=%BASE_DIR%api && uvicorn microservices.summarizer.microservice:app --host 0.0.0.0 --port 8003 --app-dir %BASE_DIR%api/microservices/summarizer"
timeout /t 5 /nobreak >nul

start "NLP-Translate" cmd /k "cd /d "%BASE_DIR%api" && call .venv\Scripts\activate && set PYTHONPATH=%BASE_DIR%api && uvicorn microservices.translate.microservice:app --host 0.0.0.0 --port 8002 --app-dir %BASE_DIR%api/microservices/translate"
timeout /t 5 /nobreak >nul

start "NLP-MainAPI" cmd /k "cd /d "%BASE_DIR%api" && call .venv\Scripts\activate && set PYTHONPATH=%BASE_DIR%api && uvicorn router:app --port 8000 --reload"

:: Frontend Setup
cd /d "%BASE_DIR%frontend"
if not exist node_modules (
    npm install
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Fallo al instalar dependencias de frontend
        set ERROR_FLAG=1
        goto :error_handling
    )
)

start "NLP-Frontend" cmd /k "cd /d "%BASE_DIR%frontend" && npm run dev"

:success
echo.
echo ---------------------------------------------
echo Sistema iniciado correctamente
echo URLs:
echo Frontend:   http://localhost:3000
echo API Main:   http://localhost:8000
echo QGQA:       http://localhost:8001
echo Translate:  http://localhost:8002
echo Summarizer: http://localhost:8003
echo ---------------------------------------------
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
exit /b 0

:error_handling
echo.
echo ---------------------------------------------
echo ERRORES DURANTE LA INSTALACION
echo Último código de error: %ERRORLEVEL%
echo ---------------------------------------------
echo Solución recomendada:
echo 1. Verifica tu conexión a internet
echo 2. Ejecuta manualmente estos comandos:
echo    cd /d "%BASE_DIR%api"
echo    call .venv\Scripts\activate
echo    pip install sentence-transformers==2.7.0
echo    pip install -r requirements.txt
echo 3. Verifica que el archivo requirements.txt existe
echo ---------------------------------------------
pause
exit /b 1