from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from models.translate import TranslateModel
import torch

class TextRequest(BaseModel):
    text: str

model_instance = {"translator": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_instance["translator"] = {
        "to_en": TranslateModel("Helsinki-NLP/opus-mt-mul-en", uses_cuda=torch.cuda.is_available()),
        "to_es": TranslateModel("Helsinki-NLP/opus-mt-en-es", uses_cuda=torch.cuda.is_available())
    }
    yield
    model_instance["translator"] = None

app = FastAPI(lifespan=lifespan)

@app.post("/detectar_idioma")
def detect_language(request: TextRequest):
    return {"language": TranslateModel.detect_language(request.text)}

@app.post("/traducir_a_ingles")
def translate_to_english(request: TextRequest):
    idioma = TranslateModel.detect_language(request.text)
    if idioma == "en":
        return {"translation": request.text}
    else:
        translator = model_instance["translator"]["to_en"]
        return {"translation": translator.translate(request.text)}

@app.post("/traducir_a_espanol")
def translate_to_spanish(request: TextRequest):
    translator = model_instance["translator"]["to_es"]
    return {"translation": translator.translate(request.text)}