from enum import Enum


class FlanT5Model(str, Enum):
    SMALL = "google/flan-t5-small"
    LARGE = "google/flan-t5-large"
    XL = "google/flan-t5-xl"
    BASE = "google/flan-t5-base"


MODEL_CONFIG = {
    "google/flan-t5-large": {
        "max_tokens": 512,
        "recommended_output_tokens": 100
    },
    "google/flan-t5-xl": {
        "max_tokens": 4096,
        "recommended_output_tokens": 200
    },
    "google/flan-t5-xxl": {
        "max_tokens": 4096,
        "recommended_output_tokens": 200
    },
    "google/flan-t5-small": {
        "max_tokens": 256,
        "recommended_output_tokens": 100
    },
    "google/flan-t5-base": {
        "max_tokens": 256,
        "recommended_output_tokens": 100
    },
}


# Cambia a SMALL, BASE o XL si es necesario
MODEL_NAME = FlanT5Model.LARGE.value


DEFAULT_CHUNK_SIZE = MODEL_CONFIG[MODEL_NAME]["max_tokens"]
DEFAULT_OVERLAP_PERCENTAGE = 1/4
