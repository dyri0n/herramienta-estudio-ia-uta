#!/bin/bash
set -e # atomico, cualquier error cancela todo

venv_dir=$(find . -type d -name "*venv" -print -quit)

if [ -d "$venv_dir" ]; then
    echo "Encontrado directorio venv: $venv_dir"
    # Activar el entorno virtual correctamente 
    source "$venv_dir/bin/activate"
else
    echo "Error: Directorio de entorno virtual no encontrado. Por favor, cree uno con terminación *venv." >&2
    exit 1
fi

MICROSERVICES_DIR="microservices"

if [ ! -d "$MICROSERVICES_DIR" ]; then
    echo "Error: Directorio de microservicios no encontrado" >&2
    exit 2
fi

# Buscar microservicios con register.json
for dir in "$MICROSERVICES_DIR"/*/; do
    register="$dir/register.json"
    if [ -f "$register" ]; then
        svc=$(jq -r '.microservice' "$register")
        ip=$(jq -r '.ip' "$register")
        port=$(jq -r '.port' "$register")

        if [ -n "$svc" ] && [ -n "$ip" ] && [ -n "$port" ]; then
            echo "Iniciando $svc en $ip:$port"
            uvicorn "$svc.microservice:app" --host "$ip" --port "$port" &
        else
            echo "Faltan datos en $register"
        fi
    fi
done

wait
