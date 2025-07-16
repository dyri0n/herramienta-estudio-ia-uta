from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx


class GeneratorPromptRequest(BaseModel):
    context: str


class SummarizerPromptRequest(BaseModel):
    text: str


class GQA(BaseModel):
    context: str
    question: str
    answer: str
    quality: float | None = None

class TranslatePromptRequest(BaseModel):
    text: str

# RUTAS HARDCODEADAS
# TODO: MOVER A APIGATEWAY PARA GESTIONAR LOADBALANCING
T2T_MODEL_PORT = "8001"
T2T_MODEL_URL = f"http://localhost:{T2T_MODEL_PORT}"

TRANSLATE_MODEL_PORT = "8002"
TRANSLATE_MODEL_URL = f"http://localhost:{TRANSLATE_MODEL_PORT}"

SUMMARIZER_MODEL_PORT = "8003"
SUMMARIZER_MODEL_URL = f"http://localhost:{SUMMARIZER_MODEL_PORT}"

# CLFY_MODEL_PORT = "8002"
# CLFY_MODEL_URL = f"http://localhost:{CLFY_MODEL_PORT}"

# =========================================================
#                   SERVICIO PRINCIPAL
#
# RECIBE LAS PETICIONES DEL USUARIO Y SE ENCARGA DE
# REDIRIGIRLAS AL MICROSERVICIO DEL MODELO QUE DESEE
# ESTO PARA EVITAR QUE SE CARGUEN A RAM Y HAGAN DEMORAR
# EL INICIO.
#
# =========================================================
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

# ----------------
# HELPER FUNCTIONS
# ----------------

DEFAULT_CHUNK_SIZE = 256
DEFAULT_OVERLAP_PERCENTAGE = 1/4


def _chunk_and_overlap_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = int(DEFAULT_CHUNK_SIZE * DEFAULT_OVERLAP_PERCENTAGE)
):
    start = 0
    chunks = []
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# ---------
# ENDPOINTS
# ---------


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
        # 1. Detectar idioma (simulado)
        # idioma = detectar_idioma(request.context)
        # idioma = "es"  # Simulación

        # 2. Traducir a inglés si es necesario (simulado)
        # context_en = traducir(request.context, target_lang="en")
        context_en: str = request.context  # Simulación

        # 3. Chunking del texto
        chunks = _chunk_and_overlap_text(context_en)

        all_qas: list[GQA] = []
        async with httpx.AsyncClient() as client:
            # 4. Generar preguntas para cada chunk llamando al microservicio
            for chunk in chunks:
                try:
                    resp = await client.post(
                        f"{T2T_MODEL_URL}/generate_question",
                        json={"context": chunk})
                    resp.raise_for_status()
                    data = resp.json()  # TODO: tipar respuesta
                    pregunta_generada: str = data.get("response", "")
                except Exception as e:
                    pregunta_generada = f"Error al generar preguntas: {str(e)}"

                # 5. Generar respuestas para cada pregunta llamando al microservicio (simulado)
                try:
                    resp = await client.post(
                        f"{T2T_MODEL_URL}/generate_answer",
                        json={"context": chunk, "question": pregunta_generada})
                    resp.raise_for_status()
                    data = resp.json()
                    respuesta_generada: str = data.get("respuesta", "")
                except Exception as e:
                    respuesta_generada = f"Error al generar preguntas: {str(e)}"

                # 6. Evaluar las preguntas y respuestas generadas
                # gqa: {chunk, q, a, quality} = evaluar_generacion_qa(q, a)

                all_qas.append(
                    GQA(context=chunk, question=pregunta_generada, answer=respuesta_generada, quality=None))

        # 7. Selección de QA (simulado, aquí devolvemos todos)
        # selected_qas = evaluate(all_qas)  # Aquí podrías filtrar/deduplicar

        # 8. Traducir de vuelta al idioma original (simulado)
        # selected_qas = traducir(selected_qas, target_lang=idioma)

        # 9. Responder al API Gateway
        return {"qas": all_qas}

    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="T2T Model service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")


@app.post("/summarizer/")
async def summarize(request: SummarizerPromptRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SUMMARIZER_MODEL_URL}/summarize",
                json=request.model_dump(mode="json")
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Summarizer service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Summarizer error: {e}")


@app.post("/translator/detectar_idioma/")
async def detect_language(request: TranslatePromptRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TRANSLATE_MODEL_URL}/detectar_idioma",
                json={"text": request.text}
            )
            response.raise_for_status()
            return response.json()  # ejemplo {"language": "es"}
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Translator service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translator error: {e}")


@app.post("/translator/traducir_a_ingles/")
async def translate_to_english(request: TranslatePromptRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TRANSLATE_MODEL_URL}/traducir_a_ingles",
                json={"text": request.text}
            )
            response.raise_for_status()
            return response.json()  # ejemplo {"translated_text": "This is a translation."}
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Translator service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translator error: {e}")


@app.post("/translator/traducir_a_espanol/")
async def translate_to_spanish(request: TranslatePromptRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TRANSLATE_MODEL_URL}/traducir_a_espanol",
                json={"text": request.text}
            )
            response.raise_for_status()
            return response.json()  # ejemplo {"translated_text": "Esta es una traducción."}
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Translator service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translator error: {e}")

#
# ==========================================================
#
#
#    EJEMPLO DE CONEXION A MICROSERVICIO DE CLASIFICACIÓN
#
#    (NO IMPLEMENTADO AÚN)
# ==========================================================
#
# app.post("classifier o lo que sea")
# async def classify(request: ClassifierPromptRequest)
#   try:
#       response = await client.post(f"{CLFY_MODEL_URL}/classify", json=request.model_dump(mode="json"))
#       response.raise_for_status()
#       return response.json()
#   except httpx.RequestError:
#       raise HTTPException(stauts_code=503, detail="Classifier Model service unavailable")
#   except: httpx.HTTPStautsError as e:
#        raise HTTPException(status_code=500, detail=f"Model error: {e}")
