from models.FlanT5Text2TextGenerator import FlanT5Text2TextGenerator
from models.summarizerModel import SummarizerModel
import torch

class ModelRegistry:
    def __init__(self):
        self.models = {}

    async def load_models(self):
        self.models["generator"] = await load_generator_model()
        self.models["classifier"] = await load_classifier_model()
        self.models["summarizer"] = await load_summarizer_model()
        
    def clear(self):
        self.models.clear()

    def get(self, name):
        return self.models.get(name)
    

async def load_generator_model():
    return FlanT5Text2TextGenerator(
        model="google/flan-t5-large",
        tokenizer="google/flan-t5-large",
        uses_cuda=torch.cuda.is_available()
    )


async def load_summarizer_model():
    return SummarizerModel(
        model_name="facebook/bart-large-cnn",
        uses_cuda=torch.cuda.is_available()
    )


async def load_classifier_model():
    return """
        ACA SE INSTANCIA EL MODELO SEA CUAL SEA,
        DEBE SER DECLARADO EN EL DIRECTORIO models/

        SU MICROSERVICIO DEBE SER IMPLEMENTADO EN ESTE
        MISMO DIRECTORIO (ver ejemplo de microservicio MICROSERVICE_FlanT5T25G.py)
    """


model_registry = ModelRegistry()
