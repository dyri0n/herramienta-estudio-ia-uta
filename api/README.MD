# INSTRUCCIONES DE USO

Crea un entorno virtual de python (de preferencia python>=3.10)

> El creador de este readme usó Python 3.12.9

## Preparar entorno virtual

### Windows

```powershell
# api/
python.exe -m venv .venv # .venv es el nombre del entorno virtual
./.venv/Scripts/Activate.ps1 # para Powershell
```

```powershell
./.venv/Scripts/activate.bat # para cmd
```

### Linux

```bash
python3 -m venv venv (en algunas distros se tiene que instalar el paquete python3.XX-venv)
source venv/bin/activate
```

En la terminal deberá aparecer el nombre del entorno virtual creado

```bash
(.venv) .../api/:
```

### Actualizar pip

Luego de crear el entorno virtual, actualiza pip (Sólo para versiones antiguas de python<3.13)

```bash
python.exe -m pip install --upgrade pip # Windows
```

```bash
pip install --upgrade pip # Linux
```

## Instalar dependencias

### Sistemas compatibles con CUDA (GPU)

Para utilizar los microservicios con una gráfica, es necesario instalar el toolkit de CUDA para exponer la gráfica al código.

<https://developer.nvidia.com/cuda-toolkit>

La versión usada en este proyecto es la `12.8`

### Requirements de python

> Si estás instalando CUDA para probar las capacidades gráficas, es necesario que verifiques la version de torch para que corresponda con la del toolkit instalado.
>
> <https://pytorch.org/get-started/locally/>
>
> La sección `--extra-index-url https://download.pytorch.org/whl/cu128` del requirements.txt debe ser modificada según la versión compatible para su sistema.

> REVISA BIEN QUE TENGAS ACTIVADO EL ENTORNO VIRTUAL. Instalar las dependencias globalmente (system-wide) puede generar problemas inesperados o incompatibilidades con otras dependencias instaladas en su sistema. Se recomienda encarecidamente utilizar un entorno virtual separado.

Para instalar todas las dependencias en un solo entorno virtual:

```bash
pip install -r requirements.txt # el archivo requirements de ./api/ tiene todas las dependencias
```

En un entorno de producción se tienen que crear entornos virtuales para cada microservicio por separado.

#### Instalación en limpio

Si tienes problemas con las dependencias y quieres borrar todo y comenzar de nuevo puedes hacer una instalación en limpio:

1. Borra el entorno virtual (Asegúrate de cerrar VSCode o Terminales que la estén usando)

En la terminal:

```powershell
rm -Force -Recurse ./.venv/ # Powershell
```

```bash
rm -rf ./.venv # Linux
```

O en el gestor de archivos (click derecho > eliminar)

2. Crea el entorno virtual de nuevo
3. Actualiza pip
4. Instala las dependencias sin usar la caché de pip

```bash
pip install -r .\requirements.txt --no-cache-dir
```

#### Errores

Si encontró errores al instalar las dependencias con el comando anterior, puede instalarlas ejecutando el comando pip separando las librerías con espacios.

```bash
pip install <librería1> <librería2> ...
# pip install transformers nltk sentencepiece etc...
```

Si tiene instalada la extensión de Python para VSCode, abrir el archivo requirements.txt señalará qué dependencias están instaladas en su entorno virtual.

## Ejecutar el proyecto

### Encender los microservicios

Acceder al directorio microservices/ y ejectuar por cada microservicio:

```bash
cd ./microservices/
# uvicorn [nombre_microservicio].microservice:app --host 0.0.0.0 --port [puerto_microservicio]
uvicorn qgqa.microservice:app --host 0.0.0.0 --port 8001
uvicorn translate.microservice:app --host 0.0.0.0 --port 8002
uvicorn summarizer.microservice:app --host 0.0.0.0 --port 8003
```

Deberían cargar los modelos y luego ejecutar el servicio de api.

### Encender el Api Gateway

todavia no esta implementado

### Encender el Router principal

Una vez ejecutados todos los microservicios, ejecutar servicio principal

```bash
# api/
fastapi dev router.py
```
