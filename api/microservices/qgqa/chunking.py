import re
from qgqa.constants import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP_PERCENTAGE


class TokenizerWrapper:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.encode = self._encode
        self.decode = self._decode

    def _encode(self, text: str, *args, **kwargs):
        return self.tokenizer.encode(text, *args, **kwargs)

    def _decode(self, tokens: list[int], *args, **kwargs):
        return self.tokenizer.decode(tokens, *args, **kwargs)


# Chunkeo por caracteres


def _chunk_and_overlap_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = int(DEFAULT_CHUNK_SIZE * DEFAULT_OVERLAP_PERCENTAGE)
):
    start = 0
    chunks = []
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def chunk_by_tokens(
    text: str,
    tokenizer: TokenizerWrapper,
    max_input_tokens: int,
    max_output_tokens: int = 100,
    overlap_tokens: int = 50,
    min_chunk_tokens: int = 100
) -> list[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    max_chunk_len = max_input_tokens - max_output_tokens

    while start < len(tokens):
        end = start + max_chunk_len
        chunk_tokens = tokens[start:end]

        # Si es el último chunk y queda muy corto, ajustamos hacia atrás
        if len(chunk_tokens) < min_chunk_tokens and chunks:
            # Pegamos lo que sobra al chunk anterior
            chunks[-1] += " " + tokenizer.decode(chunk_tokens)
            break

        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text.strip())

        start += max_chunk_len - overlap_tokens

    return chunks


def split_into_sentences(text: str) -> list[str]:
    # Separación básica por oraciones usando puntuación
    splitted_text = re.split(r'(?<=[.!?])\s+', text.strip())
    print(splitted_text)
    return splitted_text


def chunk_by_sentences(
    text: str,
    tokenizer: TokenizerWrapper,
    max_input_tokens: int,
    max_output_tokens: int = 100,
    overlap_sentences: int = 1,
    min_chunk_tokens: int = 100
) -> list[str]:
    sentences = split_into_sentences(text)
    chunks = []
    sentence_start = 0
    max_chunk_len = max_input_tokens - max_output_tokens
    chunk_count = 0

    while sentence_start < len(sentences):
        current_chunk = []
        token_count = 0
        sentence_count = 0
        sentence_index = sentence_start

        # Agregar oraciones mientras no se pase del límite de tokens
        while sentence_index < len(sentences):
            sentence = sentences[sentence_index]
            sentence_tokens = tokenizer.encode(
                sentence, add_special_tokens=False)
            if token_count + len(sentence_tokens) > max_chunk_len:
                break
            current_chunk.append(sentence)
            token_count += len(sentence_tokens)
            sentence_count += 1
            sentence_index += 1

        stripped_chunk = " ".join(current_chunk).strip()
        print(
            f"[CHNKNG] ({chunk_count}): {stripped_chunk[:20]}... [SC: {sentence_count}] [TC: {token_count}] [len: {len(stripped_chunk)}]")
        chunks.append(stripped_chunk)

        chunk_count += 1
        sentence_start = max(sentence_start + 1, sentence_index - overlap_sentences)

    return chunks
