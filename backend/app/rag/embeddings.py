from functools import lru_cache

from langchain_community.embeddings import DashScopeEmbeddings

from backend.app.config import settings

_embeddings: DashScopeEmbeddings | None = None


def _ensure_configured() -> None:
    if settings.EMBEDDING_PROVIDER != "dashscope":
        raise ValueError(
            f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}. "
            "Set EMBEDDING_PROVIDER=dashscope for DashScopeEmbeddings."
        )
    if not settings.EMBEDDING_MODEL:
        raise ValueError("EMBEDDING_MODEL is required")
    if not settings.EMBEDDING_API_KEY:
        raise ValueError("EMBEDDING_API_KEY is required")


def _get_embeddings() -> DashScopeEmbeddings:
    global _embeddings
    _ensure_configured()
    if _embeddings is None:
        _embeddings = DashScopeEmbeddings(
            model=settings.EMBEDDING_MODEL,
            dashscope_api_key=settings.EMBEDDING_API_KEY,
        )
    return _embeddings


def _validate_dimension(vector: list[float]) -> list[float]:
    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Embedding dimension mismatch: got {len(vector)}, "
            f"expected {settings.EMBEDDING_DIMENSIONS}"
        )
    return vector


def embed_text_sync(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Cannot embed empty text")
    vector = _get_embeddings().embed_query(text)
    return _validate_dimension(vector)


def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if any(not text.strip() for text in texts):
        raise ValueError("Cannot embed empty text")
    vectors = _get_embeddings().embed_documents(texts)
    return [_validate_dimension(vector) for vector in vectors]


def embedding_backend() -> str:
    _ensure_configured()
    return f"dashscope:{settings.EMBEDDING_MODEL}"
