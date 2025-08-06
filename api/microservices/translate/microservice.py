from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from ..models.translate import TranslateModel
import torch


class BatchTextRequest(BaseModel):
    texts: list[str]


model_instance: dict[str, dict[str, TranslateModel | None] | None] = {
    "translator": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_instance["translator"] = {
        "to_en": TranslateModel("Helsinki-NLP/opus-mt-mul-en", uses_cuda=torch.cuda.is_available()),
        "to_es": TranslateModel("Helsinki-NLP/opus-mt-en-es", uses_cuda=torch.cuda.is_available())
    }
    yield
    model_instance["translator"] = None

app = FastAPI(lifespan=lifespan)


@app.post("/detectar_idiomas")
def detect_languages(request: BatchTextRequest):
    idiomas = TranslateModel.detect_language_batch(request.texts)
    return {"languages": idiomas}


@app.post("/traducir_batch_a_ingles")
def translate_batch_to_english(request: BatchTextRequest):
    idiomas = TranslateModel.detect_language_batch(request.texts)
    textos = request.texts

    textos_a_traducir = [
        texto for texto, lang in zip(textos, idiomas) if lang != "en"
    ]
    indices = [i for i, lang in enumerate(idiomas) if lang != "en"]

    traducciones = model_instance["translator"]["to_en"].translate(textos_a_traducir)

    resultado = textos.copy()
    for idx, trans in zip(indices, traducciones):
        resultado[idx] = trans

    return {"translations": resultado}


@app.post("/traducir_batch_a_espanol")
def translate_batch_to_spanish(request: BatchTextRequest):
    traducciones = model_instance["translator"]["to_es"].translate(request.texts)
    return {"translations": traducciones}
