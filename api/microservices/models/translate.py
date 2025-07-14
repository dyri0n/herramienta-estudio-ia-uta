from transformers import pipeline
import transformers
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords', quiet=True)

class TranslateModel:
    def __init__(self, model_name: str, uses_cuda: bool = False):
        self.model = pipeline(
            "translation",
            model=model_name,
            device=0 if uses_cuda else -1
        )

    def translate(self, text: str) -> str:
        result = self.model(text)
        return result[0]["translation_text"]

    @staticmethod
    def detect_language(text: str) -> str:
        text_lower = text.lower()
        words = text_lower.split()  # tokenización simple por espacio
        scores = {}

        for lang in stopwords.fileids():
            stops = set(stopwords.words(lang))
            common = [w for w in words if w in stops]
            scores[lang] = len(common)

        # Umbral mínimo para confiar en detección
        best_lang = max(scores, key=scores.get) if scores else "unknown"
        if scores[best_lang] < 3:
            return "unknown"
        return best_lang