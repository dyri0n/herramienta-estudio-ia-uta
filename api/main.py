from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx

class GeneratorPromptRequest(BaseModel):
    context: str

client: httpx.AsyncClient = None

T2T_MODEL_PORT = "8001"
T2T_MODEL_URL = f"http://localhost:{T2T_MODEL_PORT}"

#CLFY_MODEL_PORT = "8002"
#CLFY_MODEL_URL = f"http://localhost:{CLFY_MODEL_PORT}"

#=========================================================
#                   SERVICIO PRINCIPAL
#
# RECIBE LAS PETICIONES DEL USUARIO Y SE ENCARGA DE
# REDIRIGIRLAS AL MICROSERVICIO DEL MODELO QUE DESEE
# ESTO PARA EVITAR QUE SE CARGUEN A RAM Y HAGAN DEMORAR 
# EL INICIO. 
#
#=========================================================
#
#   CADA MODELO USADO EN LA ESTA API DEBE SER CARGADO POR SU
#   PROPIO MICROSERVICIO
# 
#   EJEMPLO CASO DE USO: 
#       
#   CUS:Generador de Preguntas y respuestas 
#       en base a un texto plano o contexto
#   
#   CONEXIÓN CON MICROSERVICIO "generator"
#
#   TASK: "generator" (Text2TextGenerator)
#   MODELO ACTUAL: FLAN5T_ZERO_SHOT
#   
#   
#

# INICIO DEL SERVICIO PRINCIPAL, CREA CLIENTE ASÍNCRONO 
# PARA CONECTARSE A LOS MICROSERVICIOS
@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient()
    yield
    await client.aclose()

app = FastAPI(lifespan=lifespan)

@app.post("/generator/")
async def generate(request: GeneratorPromptRequest):
    try:
        response = await client.post(f"{T2T_MODEL_URL}/generate", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="T2T Model service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")

#
#==========================================================
#
#
#    EJEMPLO DE CONEXION A MICROSERVICIO DE CLASIFICACIÓN
#
#    (NO IMPLEMENTADO AÚN)
#==========================================================
#
#app.post("classifier o lo que sea")
#async def classify(request: ClassifierPromptRequest)
#   try:
#       response = await client.post(f"{CLFY_MODEL_URL}/classify", json=request.model_dump(mode="json"))
#       response.raise_for_status()
#       return response.json()
#   except httpx.RequestError:
#       raise HTTPException(stauts_code=503, detail="Classifier Model service unavailable")
#   except: httpx.HTTPStautsError as e:
#        raise HTTPException(status_code=500, detail=f"Model error: {e}")
