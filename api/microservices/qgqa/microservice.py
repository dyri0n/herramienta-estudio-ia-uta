from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from models.FlanT5Text2TextGenerator import FlanT5Text2TextGenerator
import torch
from enum import Enum


class QuestionGenerationRequest(BaseModel):
    context: str


class AnswerGenerationRequest(BaseModel):
    context: str
    question: str


model: dict[str, FlanT5Text2TextGenerator | None] = {
    "generator": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Instanciar el modelo directamente aquí
    class FlanT5Model(str, Enum):
        SMALL = "google/flan-t5-small"
        LARGE = "google/flan-t5-large"
        XL = "google/flan-t5-xl"
        BASE= "google/flan-t5-base"

    model_name = FlanT5Model.BASE.value  # Cambia a SMALL, BASE o XL si es necesario

    model["generator"] = FlanT5Text2TextGenerator(
        model=model_name,
        tokenizer=model_name,
        uses_cuda=torch.cuda.is_available()
    )
    yield
    model["generator"] = None

app = FastAPI(lifespan=lifespan)


@app.post("/generate_question")
def generate_text(request: QuestionGenerationRequest):
    generator = model.get("generator")
    if generator is None:
        return {"error": "Model not loaded"}
    return {"response": generator.generate_question(generator.proccess_input(request.context))}


@app.post("/generate_answer")
def generate_answer(request: AnswerGenerationRequest):
    generator = model.get("generator")
    if generator is None:
        return {"error": "Model not loaded"}
    return {"response": generator.generate_answer(request.question, request.context)}
