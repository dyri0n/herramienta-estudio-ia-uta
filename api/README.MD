
# INSTRUCCIONES DE USO

Ejecutar los siguientes comandos en el directorio
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

En caso de faltar algún paquete, instalar con

```bash
pip install [paquete/dependencia]
```

Acceder al directorio microservices/ y ejectuar por cada microservicio:

```bash
cd microservices/
uvicorn [nombre_microservicio]:app --host 0.0.0.0 --port [puerto_microservicio]
```
Ejemplo
```bash
cd microservices/
uvicorn MICROSERVICE_FlanT5T2TG:app --host 0.0.0.0 --port 8001
```


Una vez ejecutados todos los microservicios, ejecutar servicio principal

```bash
fastapi dev main.py
```