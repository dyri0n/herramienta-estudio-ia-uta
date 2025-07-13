from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()


class SummarizerRequest(BaseModel):
    text: str

# Cargar el modelo
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

@app.post("/summarize")
def summarize(data: SummarizerRequest):
    text = data.text.strip()

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

    summary = summarizer(
        text,
        min_length=min_len,
        max_length=max_len,
        do_sample=False
    )[0]["summary_text"]

    # Devuelve el texto resumido
    return {"resumen": summary}
