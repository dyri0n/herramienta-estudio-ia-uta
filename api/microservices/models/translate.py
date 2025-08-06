from transformers.pipelines import pipeline
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

    def translate(self, texts: list[str]) -> list[str]:
        results = self.model(texts, truncation=True)
        return [r["translation_text"] for r in results]

    @staticmethod
    def detect_language_batch(texts: list[str]) -> list[str]:
        lang_scores = []
        for text in texts:
            text_lower = text.lower()
            words = text_lower.split()
            scores = {}

            for lang in stopwords.fileids():
                if lang == "hinglish":
                    continue
                stops = set(stopwords.words(lang))
                common = [w for w in words if w in stops]
                scores[lang] = len(common)

            if not scores:
                lang_scores.append("unknown")
                continue

            best_lang = max(scores, key=scores.get)
            lang_scores.append(best_lang if scores[best_lang] >= 3 else "unknown")

        return lang_scores

