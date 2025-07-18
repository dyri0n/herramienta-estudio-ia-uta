from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from models.FlanT5Text2TextGenerator import FlanT5Text2TextGenerator
import torch


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
    model["generator"] = FlanT5Text2TextGenerator(
        model="google/flan-t5-small",
        tokenizer="google/flan-t5-small",
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
    return {"response": generator.generate_question(request.context)}


@app.post("/generate_answer")
def generate_answer(request: AnswerGenerationRequest):
    generator = model.get("generator")
    if generator is None:
        return {"error": "Model not loaded"}
    return {"response": generator.generate_answer(request.question, request.context)}
