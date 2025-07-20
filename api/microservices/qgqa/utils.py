from sentence_transformers import SentenceTransformer, util

# Inicializar una sola vez
qa_filter_model = SentenceTransformer("all-MiniLM-L6-v2")

def is_valid_answer(answer: str) -> bool:
    answer = answer.strip()
    if not answer or len(answer) < 15:
        return False
    if answer.lower() in ["none", "n/a", "(ii)", "..."]:
        return False
    return True


def filter_duplicate_qas(qas: list, threshold=0.85) -> list:
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