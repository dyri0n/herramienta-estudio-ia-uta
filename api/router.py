import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx

# TODO: crear otro archivo de tipos independiente
from microservices.qgqa.api_types import QAGenerationRequest, QAValidationRequest, GQA


DEFAULT_TIMEOUT = 30.0


class GeneratorPromptRequest(BaseModel):
    context: str


class SummarizerPromptRequest(BaseModel):
    text: str


# Elimina la definición local de GQA, ya que se importa desde api_types


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

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Agrega tu dominio de frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Se cambia dependiendo del modelo usado en backend


@app.post("/generator/")
async def generate(request: GeneratorPromptRequest):
    MAX_CONCURRENT_TASKS = 5
    try:
        async with httpx.AsyncClient() as client:
            # 1. Detectar idioma (simulado)
            # idioma = detectar_idioma(request.context)
            # idioma = "es"  # Simulación

            # 2. Traducir a inglés si es necesario (simulado)
            # context_en = traducir(request.context, target_lang="en")
            context_en: str = request.context  # Simulación

            # 3. Chunking del texto
            try:
                resp = await client.post(
                    f"{T2T_MODEL_URL}/preprocess-and-chunk",
                    json={"translated_context": context_en}
                )
                resp.raise_for_status()
                data = resp.json()
                chunks = data.get("response", [])
                # Print chunks as a string (max 40 chars), array length, and isinstance
                chunks_str = str(chunks)[:40] + \
                    ("..." if len(str(chunks)) > 40 else "")
                print(
                    f"chunks: {chunks_str} | len: {len(chunks)} | is_list: {isinstance(chunks, list)}")
            except Exception as e:
                print(f"Error al generar preguntas: {str(e)}")
                HTTPException(status_code=500, detail=f"Model error: {e}")
                return

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

            async def generar_qa_para_chunk(client: httpx.AsyncClient, chunk: str):
                async with semaphore:
                    # 4-5-6. Generar preguntas y respuestas y evaluarlas
                    # para cada chunk llamando al microservicio
                    try:
                        req = QAGenerationRequest(context=chunk)
                        resp = await client.post(
                            f"{T2T_MODEL_URL}/generate_qa",
                            json=req.model_dump(mode="json")
                        )
                        resp.raise_for_status()
                        pregunta_generada_data = resp.json().get("response", "")
                        pregunta_generada: GQA | None = GQA(
                            **pregunta_generada_data) if pregunta_generada_data else None

                    except Exception as e:
                        print(f"[ERROR al generar pregunta] {str(e)}")
                        pregunta_generada = None  # No continuar

                    print(
                        (f"{(pregunta_generada.context[:10].strip()+("..." if len(pregunta_generada.context) > 10 else ""))} "
                         f"K: {pregunta_generada.quality}, "
                         f"Q: {pregunta_generada.question[:20].strip()+("..." if len(pregunta_generada.question) > 20 else "")}, "
                         f"A: {pregunta_generada.answer[:20].strip()+("..." if len(pregunta_generada.answer) > 20 else "")}")
                        if pregunta_generada is not None
                        else "No se generó una pregunta válida")

                    if not pregunta_generada:
                        return None

                    return pregunta_generada

            all_qas: list[GQA] = []

            # 4–5-6. Llamada de generación de QAs concurrente
            tareas = [generar_qa_para_chunk(client, chunk) for chunk in chunks]
            all_qas_raw: list[GQA | None] = await asyncio.gather(*tareas)
            all_qas: list[GQA] = [qa for qa in all_qas_raw if qa is not None]

            # 7. Filtrar QA inválidos o repetidos, ordenar y
            try:
                req: QAValidationRequest = QAValidationRequest(
                    gqas=all_qas
                )
                resp = await client.post(
                    f"{T2T_MODEL_URL}/validate_and_deduplicate",
                    json=req.model_dump(mode="json"))
                resp.raise_for_status()
                data = resp.json()
                validated_gqas: list[GQA] = data.get("response", [])
                print(f"respuesta validacion: {str(validated_gqas)[:50]}")
            except Exception as e:
                print(f"Error al generar preguntas: {str(e)}")
                HTTPException(status_code=500, detail=f"Model error: {e}")
                return

            # 8. Traducir de vuelta al idioma original (simulado)
            # selected_qas = traducir(filtered_qas, target_lang=idioma)

            # 9. Responder al API Gateway
            return {"qas": validated_gqas}

    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="T2T Model service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")


@app.post("/summarizer/")
async def summarize(request: SummarizerPromptRequest):
    try:
        # <-- Agregar
        print(f"Enviando solicitud a {SUMMARIZER_MODEL_URL}/summarize")
        # <-- Agregar
        print(f"Datos enviados: {request.model_dump(mode='json')}")

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{SUMMARIZER_MODEL_URL}/summarize",
                json=request.model_dump(mode="json"),
                timeout=DEFAULT_TIMEOUT  # <-- Agregar timeout
            )
            print(f"Respuesta recibida: {response.status_code}")  # <-- Agregar
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"Error de conexión: {str(e)}")  # <-- Agregar
        raise HTTPException(
            status_code=503, detail="Summarizer service unavailable")
    except httpx.HTTPStatusError as e:
        print(f"Error HTTP: {str(e)}")  # <-- Agregar
        raise HTTPException(status_code=500, detail=f"Summarizer error: {e}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")  # <-- Agregar
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.post("/translator/detectar_idioma/")
async def detect_language(request: TranslatePromptRequest):
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{TRANSLATE_MODEL_URL}/detectar_idioma",
                json={"text": request.text},
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            return response.json()  # ejemplo {"language": "es"}
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Translator service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translator error: {e}")


@app.post("/translator/traducir_a_ingles/")
async def translate_to_english(request: TranslatePromptRequest):
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{TRANSLATE_MODEL_URL}/traducir_a_ingles",
                json={"text": request.text},
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            # ejemplo {"translated_text": "This is a translation."}
            return response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Translator service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translator error: {e}")


@app.post("/translator/traducir_a_espanol/")
async def translate_to_spanish(request: TranslatePromptRequest):
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{TRANSLATE_MODEL_URL}/traducir_a_espanol",
                json={"text": request.text},
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            # ejemplo {"translated_text": "Esta es una traducción."}
            return response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Translator service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translator error: {e}")


@app.get("/health")
async def health_check():
    services = {
        "text2text": T2T_MODEL_URL,
        "summarizer": SUMMARIZER_MODEL_URL,
        "translator": TRANSLATE_MODEL_URL
    }

    results = {}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        for name, url in services.items():
            try:
                response = await client.get(f"{url}/health", timeout=DEFAULT_TIMEOUT)
                results[name] = {
                    "status": "active" if response.status_code == 200 else "inactive",
                    "status_code": response.status_code
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)
                }

    return results


@app.post("/summarizer/traducir/")
async def summarize_translation(request: SummarizerPromptRequest):
    try:
        original_text = request.text

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            detection_response = await client.post(
                f"{TRANSLATE_MODEL_URL}/detectar_idioma",
                json={"text": original_text}
            )
            detection_response.raise_for_status()
            language_name = detection_response.json().get("language", "en").lower()

            language_map = {
                "english": "en", "inglés": "en",
                "español": "es", "spanish": "es",
                "francés": "fr", "french": "fr",
                "alemán": "de", "german": "de"
            }
            detected_language = language_map.get(language_name, language_name)

            translated_text = original_text
            was_translated = False
            if detected_language != "en":
                translation_response = await client.post(
                    f"{TRANSLATE_MODEL_URL}/traducir_a_ingles",
                    json={"text": original_text}
                )
                translation_response.raise_for_status()
                translation_json = translation_response.json()

                translated_text = (
                    translation_json.get("translated_text") or
                    translation_json.get("text") or
                    translation_json.get("translation") or
                    ""
                )

                if not translated_text.strip():
                    raise HTTPException(
                        status_code=500,
                        detail="Error al traducira inglés"
                    )

                was_translated = True

            summarize_response = await client.post(
                f"{SUMMARIZER_MODEL_URL}/summarize",
                json={"text": translated_text}
            )
            summarize_response.raise_for_status()
            summary_en = summarize_response.json().get("resumen", translated_text)

            final_summary = summary_en
            if was_translated:
                back_translation_response = await client.post(
                    f"{TRANSLATE_MODEL_URL}/traducir_a_espanol",
                    json={"text": summary_en}
                )
                back_translation_response.raise_for_status()
                back_translation_json = back_translation_response.json()

                possible_keys = ["translated_text",
                                 "traducción", "translation"]
                final_summary = next(
                    (back_translation_json.get(k)
                     for k in possible_keys if k in back_translation_json),
                    summary_en
                )

            return {"resumen": final_summary}

    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Alguno de los servicios no está disponible")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Service error: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}")

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
