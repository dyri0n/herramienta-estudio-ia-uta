from transformers.pipelines import pipeline
import unicodedata
import re

class FlanT5Text2TextGenerator:

    def __init__(self, model: str, tokenizer: str, uses_cuda: bool):
        print("Initializating generator")
        print(f"Pipeline\ntask: text2text-generation\nmodel: {model}\ntokenizer: {tokenizer}\nuses_cuda: {uses_cuda}")

        self.generator = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if uses_cuda else -1
        )

    def generate_question(self, id: str, context: str) -> str:
        print(f"[QG] [{id}] Contexto {context[:20]}..., lenght: {len(context)}")
        if not context:
            raise ValueError("El contexto proporcionado está vacío o no es válido.")

        prompt_q = (
            f"Generate a question based on the following context."
            "Don't make a multiple answer question. Only open-ended questions\n\n"
            f"Context: {context}\n\n"
            "Question:"
        )

        outputs = self.generator(prompt_q, do_sample=True)

        if isinstance(outputs, list) and len(outputs) > 0 and "generated_text" in outputs[0]:
            q_text = outputs[0]["generated_text"].strip()
        else:
            raise RuntimeError(f"Formato inesperado de salida: {outputs!r}")

        print(f"[QG] [{id}] Pregunta generada: {q_text[:20]}..., lenght: {len(q_text)}")
        return q_text

    def generate_answer(self, id: str, question: str, context: str, max_length: int = 64):
        print(f"[AG] [{id}] Pregunta: {question[:20]}..., lenght: {len(context)}")

        prompt_a = (
            "You are teacher making a test. "
            "Given the context below, answer the question.\n\n"
            f"Context: {context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        out_a = self.generator(
            prompt_a,
            num_beams=5,
            early_stopping=True,
            length_penalty=1.2,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
        )

        if isinstance(out_a, list) and len(out_a) > 0 and "generated_text" in out_a[0]:
            a_text = out_a[0].get("generated_text", "").strip()
        else:
            raise RuntimeError(f"Formato inesperado de salida: {out_a!r}")

        print(f"[AG] [{id}] Respuesta generada: {a_text[:20]}..., lenght: {len(a_text)}")
        return a_text

    def generate_questions_batch(self, id: str, contexts: list[str]) -> list[str]:
        prompts = [
            f"Generate a question based on the following context."
            "Don't make a multiple answer question. Only open-ended questions\n\n"
            f"Context: {ctx}\n\n"
            "Question:"
            for ctx in contexts
        ]
        print(f"[BATCH-QG] [{id}] Procesando {len(prompts)} contextos...")
        outputs = self.generator(prompts, do_sample=True)
        return [out["generated_text"].strip() for out in outputs]

    def generate_answers_batch(self, id: str, questions: list[str], contexts: list[str]) -> list[str]:
        assert len(questions) == len(contexts), "questions y contexts deben tener la misma longitud"
        prompts = [
            "You are teacher making a test. "
            "Given the context below, answer the question.\n\n"
            f"Context: {ctx}\n\n"
            f"Question: {q}\n\n"
            "Answer:"
            for q, ctx in zip(questions, contexts)
        ]
        print(f"[BATCH-AG] [{id}] Procesando {len(prompts)} preguntas-contextos...")
        outputs = self.generator(
            prompts,
            num_beams=5,
            early_stopping=True,
            length_penalty=1.2,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
        )
        return [out["generated_text"].strip() for out in outputs]

    def proccess_input(self, id: str, plain_text: str) -> str:
        text = unicodedata.normalize("NFKC", plain_text)
        text = re.sub(r'[^\x20-\x7EáéíóúÁÉÍÓÚñÑüÜ]', ' ', text)
        text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = text.replace('"', '').replace("'", '')
        text = re.sub(r"[{}\[\]<>]", "", text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
