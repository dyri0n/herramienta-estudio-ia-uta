from sentence_transformers import SentenceTransformer, util

from transformers import AutoTokenizer

from qgqa.api_types import GQA


def is_valid_answer(answer: str) -> bool:
    answer = answer.strip()
    if not answer:
        return False
    if answer.lower() in ["none", "n/a", "(ii)", "..."]:
        return False
    return True


def filter_duplicate_qas(qas: list[GQA], threshold=0.85) -> list[GQA]:
    qa_filter_model = SentenceTransformer("all-MiniLM-L6-v2")

    filtered = []
    seen_questions = []

    for qa in qas:
        q = qa.question
        q_embed = qa_filter_model.encode(q, convert_to_tensor=True)

        is_duplicate = False
        for seen_q in seen_questions:
            seen_embed = qa_filter_model.encode(seen_q, convert_to_tensor=True)
            sim = util.cos_sim(q_embed, seen_embed).item()
            if sim >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            filtered.append(qa)
            seen_questions.append(q)

    return filtered


def evaluar_calidad_qa(id: str, answer: str, question: str) -> float:
    """
    Devuelve una puntuación de calidad entre 0.0 y 1.0.
    """
    score = 0
    total = 4  # Número total de criterios
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")

    # 1. Validación básica
    if is_valid_answer(answer):
        score += 1

    # 2. Longitud razonable (ni 1 palabra ni 100 tokens)
    answer_tokens = tokenizer.encode(answer, add_special_tokens=False)
    if 3 <= len(answer_tokens) <= 40:
        score += 1

    # 3. Respuesta está relacionada con la pregunta (por similitud)
    question_tokens = tokenizer.encode(question, add_special_tokens=False)
    shared_tokens = set(answer_tokens) & set(question_tokens)
    if len(shared_tokens) / max(1, len(answer_tokens)) < 0.5:  # Evitar que solo repita la pregunta
        score += 1

    # 4. Coherencia del texto (heurística con mayúsculas y punto final)
    if answer[0].isupper() and answer[-1] in ".!?":
        score += 1

    return round(score / total, 2)  # Devuelve un float entre 0.0 y 1.0
