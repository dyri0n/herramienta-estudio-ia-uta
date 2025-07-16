from transformers.pipelines import pipeline
import re


class FlanT5Text2TextGenerator:

    def __init__(self, model: str, tokenizer: str, uses_cuda: bool):
        print("Initializating generator")
        print(
            f"Pipeline\ntask: text2text-generation\nmodel: {model}\ntokenizer: {tokenizer}\nuses_cuda: {uses_cuda}")

        self.generator = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if uses_cuda else -1
        )

    def generate_question(self, context: str, max_length: int = 64) -> str:
        print("Generando pregunta...")
        print(f"Contexto {context}")
        prompt_q = f"Generate a question based on the following context: {context}"

        outputs = self.generator(
            prompt_q,
            max_length=max_length,
            do_sample=True,
        )

        if isinstance(outputs, list) and len(outputs) > 0 and "generated_text" in outputs[0]:
            q_text = outputs[0]["generated_text"].strip()
        else:
            raise RuntimeError(f"Formato inesperado de salida: {outputs!r}")

        return q_text

    # TODO: implementar en la pipeline de generacion de qa
    def proccess_input(self, plain_text: str) -> str:
        # Eliminar caracteres de control no imprimibles excepto saltos de línea
        text = re.sub(
            r'[^\x09\x0A\x0D\x20-\x7EáéíóúÁÉÍÓÚñÑüÜ]', '', plain_text)
        # Reemplazar comillas dobles y simples por comillas estándar
        text = text.replace('“', '"').replace(
            '”', '"').replace("‘", "'").replace("’", "'")
        # Opcional: reemplazar saltos de línea por espacios
        # text = text.replace('\n', ' ')
        return text

    def generate_answer(self, question: str, context: str, max_length: int = 64):
        print("Generando respuesta...")
        print(f"Pregunta {question}")
        prompt_a = (
            "You are teacher making a test. "
            "Given the context below, answer the question with a clearly and concise.\n\n"
            f"Context: {context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        out_a = self.generator(
            prompt_a,
            # beam search
            num_beams=5,
            early_stopping=True,
            length_penalty=1.2,
            # sampling
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
        )

        if isinstance(out_a, list) and len(out_a) > 0 and "generated_text" in out_a[0]:
            a_text = out_a[0]["generated_text"].strip()
        else:
            raise RuntimeError(f"Formato inesperado de salida: {out_a!r}")

        return a_text
