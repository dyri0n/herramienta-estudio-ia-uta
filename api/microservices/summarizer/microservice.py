from contextlib import asynccontextmanager
import re
import unicodedata
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from models.summarizerModel import SummarizerModel


class SummarizerRequest(BaseModel):
    text: str


model: dict[str, SummarizerModel | None] = {
    "summarizer": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cargar el modelo de resumen al iniciar la aplicación
    model["summarizer"] = SummarizerModel(
        model_name="facebook/bart-large-cnn",
        uses_cuda=torch.cuda.is_available()
    )
    yield
    # Limpiar el modelo al cerrar la aplicación
    model["summarizer"] = None

app = FastAPI(lifespan=lifespan)


@app.post("/summarize")
def summarizer_endpint(data: SummarizerRequest):
    text = data.text
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Texto vacío")

    word_count = len(text.split())

    if word_count < 30:
        raise HTTPException(status_code=400, detail="Texto demasiado corto")

    # Establecer proporciones de mínimo y máximo de palabras del resumen de acuerdo
    # al número de palabras del texto original
    if word_count < 200:
        min_pct, max_pct = 0.4, 0.6
    elif word_count > 1000:
        min_pct, max_pct = 0.2, 0.35
    else:
        min_pct, max_pct = 0.3, 0.5

    estimated_tokens = int(word_count * 1.3) 
    min_len = max(int(estimated_tokens * min_pct), 30)
    max_len = min(int(estimated_tokens * max_pct), 512)

    summarizer = model.get("summarizer")
    if summarizer is None:
        raise HTTPException(status_code=500, detail="Modelo no cargado")

    try:
        summary = summarizer.summarize(text, min_len=min_len, max_len=max_len)
        return {"resumen": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
