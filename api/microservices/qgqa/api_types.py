from pydantic import BaseModel


class PreprocessAndChunkingRequest(BaseModel):
    translated_context: str


class QAGenerationRequest(BaseModel):
    context: str


class GQA(BaseModel):
    context: str
    question: str
    answer: str
    quality: float | None = None


class QAValidationRequest(BaseModel):
    gqas: list[GQA]
