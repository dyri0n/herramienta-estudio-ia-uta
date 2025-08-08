import uuid
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from qgqa.api_types import GQA, PreprocessAndChunkingRequest, QAGenerationRequest, QAValidationRequest
from qgqa.validation import filter_duplicate_qas, is_valid_answer
from models.FlanT5Text2TextGenerator import FlanT5Text2TextGenerator
from qgqa.chunking import TokenizerWrapper, chunk_by_sentences

from qgqa.constants import MODEL_CONFIG, MODEL_NAME
import torch
from transformers import AutoTokenizer
from models.helpers.quality_evaluator import QualityEvaluator

model: dict[str, FlanT5Text2TextGenerator | None] = {
    "generator": None
}
#EVALUADOR DE CALIDAD
qe = QualityEvaluator()

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

    contexts = [generator.proccess_input(
        process_code, c) for c in request.context]
    contexts = [c for c in contexts if c]

    if not contexts:
        raise HTTPException(
            status_code=410, detail="Todos los contextos están vacíos")

    try:
        questions = generator.generate_questions_batch(process_code, contexts)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generando preguntas: {str(e)}")

    try:
        answers = generator.generate_answers_batch(
            process_code, questions, contexts)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generando respuestas: {str(e)}")

    gqas = []
    for ctx, q, a in zip(contexts, questions, answers):
        if not a:
            gqas.append(GQA(context=ctx, question=q, answer=a, quality=0))
            continue
        quality = qe.get_quality_of(ctx, q, a)
        if quality>0.3:
            gqa = GQA(
                context=ctx,
                question=q,
                answer=a,
                quality=quality if quality else 0
            )
            gqas.append(gqa)
            print(f"[✅] Generated QA: {gqa.quality} ({gqa.context[:10]}) ({gqa.question[:10]}) ({gqa.answer[:10]})")

    return {"response": gqas}


@app.post("/validate_and_deduplicate")
def validate_and_deduplicate_gqa(request: QAValidationRequest):
    all_qas: list[GQA] = request.gqas
    process_code = uuid.uuid4().hex[:5]

    print(f"[ START-VDF] [{process_code}] Recibidas: {len(all_qas)} QAs")

    if not all_qas:
        raise HTTPException(status_code=410, detail="No se generó nada válido")

    valid_qas = [qa for qa in all_qas if is_valid_answer(qa.answer)]
    if not valid_qas:
        raise HTTPException(
            status_code=410, detail="No se generaron QAs válidos")

    print(f"[VALIDATING] [{process_code}] QAs válidas: {len(valid_qas)}")

    filtered_qas = filter_duplicate_qas(valid_qas)
    if not filtered_qas:
        raise HTTPException(
            status_code=410, detail="Se eliminaron todas las QAs al deduplicar")

    print(f"[ FILTERING] [{process_code}] QAs únicas: {len(filtered_qas)}")

    filtered_qas.sort(
        key=lambda x: x.quality if x.quality is not None else 0, reverse=True)
    print(f"[   SORTING] [{process_code}] QAs ordenadas")

    return {"response": filtered_qas}
