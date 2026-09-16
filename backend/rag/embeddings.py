import logging
import os
from functools import lru_cache

from config import get_settings

# huggingface_hub reads HF_HOME at import time, so this must run before the
# `sentence_transformers` import below pulls it in transitively.
os.environ.setdefault("HF_HOME", get_settings().hf_home)

from sentence_transformers import SentenceTransformer  # noqa: E402

logger = logging.getLogger(__name__)

# multilingual-e5 requires a task prefix on every input, or search quality
# silently degrades — this isn't a style choice, it's how the model was trained.
_PASSAGE_PREFIX = "passage: "
_QUERY_PREFIX = "query: "


@lru_cache
def _model() -> SentenceTransformer:
    model_name = get_settings().embedding_model
    logger.info("embeddings: loading model %s", model_name)
    model = SentenceTransformer(model_name)
    logger.info("embeddings: model %s loaded", model_name)
    return model


def embed_passages(texts: list[str]) -> list[list[float]]:
    prefixed = [_PASSAGE_PREFIX + text for text in texts]
    return _model().encode(prefixed, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    embedding = _model().encode(_QUERY_PREFIX + text, normalize_embeddings=True)
    return embedding.tolist()
