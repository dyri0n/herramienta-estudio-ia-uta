from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from models.ModelRegistry import model_registry
import torch

class GenerationRequest(BaseModel):
    context: str

model = {"generator": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    model["generator"] = model_registry["generator"]
    yield
    model["generator"] = None

app = FastAPI(lifespan=lifespan)

@app.post("/generate")
def generate_text(request: GenerationRequest):
    generator = model.get("generator")
    if generator is None:
        return {"error": "Model not loaded"}
    return {"response": generator.generate_questions(request.context)}
