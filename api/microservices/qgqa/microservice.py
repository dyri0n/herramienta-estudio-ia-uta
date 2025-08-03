import uuid
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from ..models.FlanT5Text2TextGenerator import FlanT5Text2TextGenerator
from validation import filter_duplicate_qas, is_valid_answer, evaluar_calidad_qa
from chunking import TokenizerWrapper, chunk_by_sentences
from api_types import GQA, PreprocessAndChunkingRequest, QAGenerationRequest, QAValidationRequest
from constants import MODEL_CONFIG, MODEL_NAME
import torch
from transformers import AutoTokenizer


model: dict[str, FlanT5Text2TextGenerator | None] = {
    "generator": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model["generator"] = FlanT5Text2TextGenerator(
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        uses_cuda=torch.cuda.is_available()
    )
    yield
    model["generator"] = None

app = FastAPI(lifespan=lifespan)


@app.post("/preprocess-and-chunk")
def preprocess_and_chunk_text(request: PreprocessAndChunkingRequest):
    model_spec = MODEL_CONFIG[MODEL_NAME]
    tokenizer_hf = TokenizerWrapper(AutoTokenizer.from_pretrained(MODEL_NAME))
    chunks = chunk_by_sentences(
        text=request.translated_context,
        tokenizer=tokenizer_hf,
        max_input_tokens=model_spec["max_tokens"],
        max_output_tokens=model_spec["recommended_output_tokens"],
        overlap_sentences=6,
        min_chunk_tokens=model_spec["max_tokens"]-100
    )
    return {"response": chunks}


@app.post("/generate_qa")
def generate_text(request: QAGenerationRequest):
    process_code = uuid.uuid4().hex[:5]
    generator = model.get("generator")
    if generator is None:
        return {"error": "Model not loaded"}

    # secuencial pq asi debe ser
    context = generator.proccess_input(process_code, request.context)
    if not context:
        raise HTTPException(status_code=410, detail=f"Contexto vacío")
    question = generator.generate_question(process_code, context)
    if not question:
        raise HTTPException(
            status_code=500, detail=f"No se generó una pregunta válida")
    answer = generator.generate_answer(process_code, question, context)

    if not answer:
        gqa = GQA(context=context, question=question, answer=answer, quality=0)
        return {"response": gqa}
    # TODO: implementar process_code
    quality = evaluar_calidad_qa(process_code, question, answer)
    gqa = GQA(
        context=context,
        question=question,
        answer=answer,
        quality=quality if quality else 0)

    print(
        f"[✅] Generated QA: {gqa.quality} ({gqa.context[:10]}) ({gqa.question[:10]}) ({gqa.answer[:10]}) ")
    return {"response": gqa}


@app.post("/validate_and_deduplicate")
def validate_and_deduplicate_gqa(request: QAValidationRequest):
    all_qas: list[GQA] = request.gqas
    process_code = uuid.uuid4().hex[:5]
    print(f"[ START-VDF] [{process_code}] {str(all_qas)[:50]}")
    if all_qas is None:
        raise HTTPException(
            status_code=410, detail=f"No se generó nada válido")

    # Removing invalid gqas
    valid_qas: list[GQA] = [qa for qa in all_qas if is_valid_answer(qa.answer)]
    if not valid_qas:
        raise HTTPException(
            status_code=410, detail=f"No se generaron preguntas y respuestas válidas"
        )
    print(f"[VALIDATING] [{process_code}] {str(valid_qas)[:50]}")

    # Removing duplicated gqas
    filtered_qas: list[GQA] = filter_duplicate_qas(valid_qas)
    if not filtered_qas:
        raise HTTPException(
            status_code=410, detail=f"Se quedo sin preguntas y respuestas al deduplicar"
        )
    print(f"[ FILTERING] [{process_code}] {str(filtered_qas)[:50]}")

    # Sorting by quality
    filtered_qas.sort(
        key=lambda x:
            x.quality if x.quality is not None else 0,
            reverse=True)

    print(f"[   SORTING] [{process_code}] {str(filtered_qas)[:50]}")
    return {"response": filtered_qas}
