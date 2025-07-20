from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from models.translate import TranslateModel
import torch


class TextRequest(BaseModel):
    text: str


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


@app.post("/detectar_idioma")
def detect_language(request: TextRequest):
    return {"language": TranslateModel.detect_language(request.text)}


@app.post("/traducir_a_ingles")
def translate_to_english(request: TextRequest):
    idioma_texto = TranslateModel.detect_language(request.text)
    if idioma_texto == "en":
        return {"translation": request.text}
    
    translators = model_instance.get("translator")
    if (translators is None):
        raise 
    english_translator = translators.get("to_en")
    
    
    if english_translator is None:
        raise HTTPException(status_code=500, detail="Modelo no cargado")
    
    else:
        return {"translation": english_translator.translate(request.text)}


@app.post("/traducir_a_espanol")
def translate_to_spanish(request: TextRequest):
    translators = model_instance.get("translator")
    if (translators is None):
        raise 
    spanish_translator = translators.get("to_es")
    
    
    if spanish_translator is None:
        raise HTTPException(status_code=500, detail="Modelo no cargado")
    
    return {"translation": spanish_translator.translate(request.text)}
