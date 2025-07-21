import re
from typing import Callable
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from microservices.qgqa.utils import filter_duplicate_qas, is_valid_answer
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
from transformers import AutoTokenizer



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

class TokenizerWrapper:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.encode = self._encode
        self.decode = self._decode

    def _encode(self, text: str, *args, **kwargs):
        return self.tokenizer.encode(text, *args, **kwargs)

    def _decode(self, tokens: list[int], *args, **kwargs):
        return self.tokenizer.decode(tokens, *args, **kwargs)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP_PERCENTAGE = 1/4
DEFAULT_TIMEOUT = 30.0 

QGQA_MODEL_NAME = 'google/flan-t5-large'

MODEL_CONFIG = {
    "google/flan-t5-large": {
        "max_tokens": 512,
        "recommended_output_tokens": 100
    },
    "google/flan-t5-xl": {
        "max_tokens": 4096,
        "recommended_output_tokens": 200
    },
    "google/flan-t5-xxl": {
        "max_tokens": 4096,
        "recommended_output_tokens": 200
    },
    "google/flan-t5-small": {
        "max_tokens": 256,
        "recommended_output_tokens": 100
    },
}


# Chunkeo por caracteres


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


def split_into_sentences(text: str) -> list[str]:
    # Separación básica por oraciones usando puntuación
    splitted_text = re.split(r'(?<=[.!?])\s+', text.strip())
    print(splitted_text)
    return splitted_text


def count_tokens(text: str, tokenizer: TokenizerWrapper) -> int:
    return len(tokenizer.encode(text)) # type: ignore


def chunk_by_tokens(
    text: str,
    tokenizer: TokenizerWrapper,
    max_input_tokens: int,
    max_output_tokens: int = 100,
    overlap_tokens: int = 50,
    min_chunk_tokens: int = 100
) -> list[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    max_chunk_len = max_input_tokens - max_output_tokens

    while start < len(tokens):
        end = start + max_chunk_len
        chunk_tokens = tokens[start:end]

        # Si es el último chunk y queda muy corto, ajustamos hacia atrás
        if len(chunk_tokens) < min_chunk_tokens and chunks:
            # Pegamos lo que sobra al chunk anterior
            chunks[-1] += " " + tokenizer.decode(chunk_tokens)  
            break

        chunk_text = tokenizer.decode(chunk_tokens)  
        chunks.append(chunk_text.strip())

        start += max_chunk_len - overlap_tokens

    return chunks


def chunk_by_sentences(
    text: str,
    tokenizer: TokenizerWrapper,
    max_input_tokens: int,
    max_output_tokens: int = 100,
    overlap_sentences: int = 1,
    min_chunk_tokens: int = 100
) -> list[str]:
    sentences = split_into_sentences(text)
    chunks = []
    i = 0
    max_chunk_len = max_input_tokens - max_output_tokens

    while i < len(sentences):
        current_chunk = []
        token_count = 0
        j = i

        # Agregar oraciones mientras no se pase del límite de tokens
        while j < len(sentences):
            sentence = sentences[j]
            sentence_tokens = tokenizer.encode(sentence, add_special_tokens=False)
            if token_count + len(sentence_tokens) > max_chunk_len:
                break
            current_chunk.append(sentence)
            token_count += len(sentence_tokens)
            print(sentence, token_count, max_chunk_len)
            print(chunks)
            j += 1

        # Si el chunk está muy corto y no es el primero, lo fusionamos con el anterior
        #if token_count < min_chunk_tokens and chunks:
        #    chunks[-1] += " " + " ".join(current_chunk)
        #else:
        chunks.append(" ".join(current_chunk).strip())

        i = max(i + 1, j - overlap_sentences)

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
    try:
        # 1. Detectar idioma (simulado)
        # idioma = detectar_idioma(request.context)
        # idioma = "es"  # Simulación

        # 2. Traducir a inglés si es necesario (simulado)
        # context_en = traducir(request.context, target_lang="en")
        context_en: str = request.context  # Simulación

        # 3. Chunking del texto

        # Chunkeo precario
        # chunks = _chunk_and_overlap_text(context_en)

        model_spec = MODEL_CONFIG[QGQA_MODEL_NAME]

        tokenizer_hf = TokenizerWrapper(AutoTokenizer.from_pretrained(QGQA_MODEL_NAME))

        # Alternativa basada en tokens:
        # chunks = chunk_by_tokens(
        #     text=context_en,
        #     tokenizer=tokenizer,
        #     max_input_tokens=model_spec["max_tokens"],
        #     max_output_tokens=model_spec["recommended_output_tokens"],
        #     overlap_tokens=50,
        #     min_chunk_tokens=100
        # )

        # Alternativa basada en oraciones:
        chunks = chunk_by_sentences(
            text=context_en,
            tokenizer=tokenizer_hf,
            max_input_tokens=model_spec["max_tokens"],
            max_output_tokens=model_spec["recommended_output_tokens"],
            overlap_sentences=6,
            min_chunk_tokens=model_spec["max_tokens"]-100
        )

        print("===== CHUNKS GENERADOS =====")
        for idx, chunk in enumerate(chunks):
            print(
                f"[Chunk {idx+1} | Tokens: {count_tokens(chunk, tokenizer_hf)}]{chunk}")

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
                    respuesta_generada: str = data.get("response", "")
                except Exception as e:
                    respuesta_generada = f"Error al generar preguntas: {str(e)}"

                # 6. Evaluar las preguntas y respuestas generadas
                # gqa: {chunk, q, a, quality} = evaluar_generacion_qa(q, a)

                all_qas.append(
                    GQA(context=chunk, question=pregunta_generada, answer=respuesta_generada, quality=None))

        # 7. Filtrar QA inválidos o repetidos
        valid_qas = [qa for qa in all_qas if is_valid_answer(qa.answer)]
        filtered_qas = filter_duplicate_qas(valid_qas)

        # 8. Traducir de vuelta al idioma original (simulado)
        # selected_qas = traducir(selected_qas, target_lang=idioma)

        # 9. Responder al API Gateway
        return {"qas": filtered_qas}

    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="T2T Model service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")


@app.post("/summarizer/")
async def summarize(request: SummarizerPromptRequest):
    try:
        print(f"Enviando solicitud a {SUMMARIZER_MODEL_URL}/summarize")  # <-- Agregar
        print(f"Datos enviados: {request.model_dump(mode='json')}")  # <-- Agregar
        
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

                possible_keys = ["translated_text", "traducción", "translation"]
                final_summary = next(
                    (back_translation_json.get(k) for k in possible_keys if k in back_translation_json),
                    summary_en
                )

            return {"resumen": final_summary}

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Alguno de los servicios no está disponible")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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