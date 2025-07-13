from transformers import pipeline
import transformers

class SummarizerModel:
    def __init__(self, model_name: str, uses_cuda: bool = False):
        self.model = pipeline(
            "summarization",
            model=model_name,
            device=0 if uses_cuda else -1
        )

    def summarize(self, text: str, min_len: int, max_len: int) -> str:
        kwargs = {"do_sample": False}
        version = tuple(map(int, transformers.__version__.split(".")[:2]))

        if version >= (4, 30):
            kwargs["min_new_tokens"] = min_len
            kwargs["max_new_tokens"] = max_len
        else:
            kwargs["min_length"] = min_len
            kwargs["max_length"] = max_len

        result = self.model(text, **kwargs)
        return result[0]["summary_text"]
