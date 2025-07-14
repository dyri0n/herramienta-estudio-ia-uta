from transformers import pipeline
import transformers

class SummarizerModel:
    def __init__(self, model_name: str, uses_cuda: bool = False):
        self.model = pipeline(
            "summarization",
            model=model_name,
            device=0 if uses_cuda else -1
        )

    def _split_text(self, text: str, max_words: int = 800):
        words = text.split()
        chunks = [words[i:i+max_words] for i in range(0, len(words), max_words)]
        return [" ".join(chunk) for chunk in chunks]

    def summarize(self, text: str, min_len: int = 30, max_len: int = 150) -> str:
        kwargs = {"do_sample": False}
        version = tuple(map(int, transformers.__version__.split(".")[:2]))

        if version >= (4, 30):
            kwargs["min_new_tokens"] = min_len
            kwargs["max_new_tokens"] = max_len
        else:
            kwargs["min_length"] = min_len
            kwargs["max_length"] = max_len

        if len(text.split()) <= 800:
            result = self.model(text, **kwargs)
            return result[0]["summary_text"]
        
        chunks = self._split_text(text)
        partial_summaries = []

        for chunk in chunks:
            chunk_summary = self.model(chunk, **kwargs)[0]["summary_text"]
            partial_summaries.append(chunk_summary)

        combined_summary = " ".join(partial_summaries)

        if len(combined_summary.split()) > 1000:
            final_kwargs = kwargs.copy()
            final_kwargs["min_new_tokens"] = 50
            final_kwargs["max_new_tokens"] = 200
            result = self.model(combined_summary, **final_kwargs)
            return result[0]["summary_text"]

        return combined_summary
