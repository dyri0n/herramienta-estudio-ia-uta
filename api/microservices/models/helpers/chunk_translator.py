from deep_translator import GoogleTranslator
from langdetect import detect

class ChunkTranslator:
    def __init__(self):
        # Solo soportamos inglés y español
        self.supported_languages = {"en", "es"}

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text (returns 'en' or 'es')."""
        lang = detect(text)
        return "es" if lang.startswith("es") else "en"

    def translate(self, text: str, from_lang: str, to_lang: str) -> str:
        """Translate text from one language to another using Google Translate."""
        if from_lang == to_lang or not text.strip():
            return text

        if from_lang not in self.supported_languages or to_lang not in self.supported_languages:
            raise ValueError("Only 'en' and 'es' are supported.")

        try:
            return GoogleTranslator(source=from_lang, target=to_lang).translate(text)
        except Exception as e:
            print(f"[Translation Error] {e}")
            return text
