from transformers.pipelines import pipeline

class FlanT5Text2TextGenerator:
    
    def __init__(self, model: str, tokenizer: str, uses_cuda: bool):
        print("Initializating generator")
        print(f"Pipeline\ntask: text2text-generation\nmodel: {model}\ntokenizer: {tokenizer}\nuses_cuda: {uses_cuda}")
        
        self.generator = pipeline (
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if uses_cuda else -1
        )
    
    def generate_questions(self, context: str, num_questions: int = 5) -> list[str]:
        prompt_q = f"Generate {num_questions} questions based on the following context:\n\n{context}"
        
        outputs = self.generator(
            prompt_q,
            max_length=64,
            do_sample=True,
            num_return_sequences=4
        )
        
        questions = []
        for out in outputs:
            if "generated_text" in out:
                questions.append(out["generated_text"].strip())
            else:
                raise RuntimeError(f"Formato inesperado de salida: {out!r}")
        
        return questions

    
    def proccess_input(self, plain_text: str):
        ...

    def chunk(self, plain_text: str):
        ...
    
    def generate_answer(self, question: str, context: str):
        ...