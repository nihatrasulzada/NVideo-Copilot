"""ChromaDB vektor bazası ilə iş."""
from typing import Optional, Sequence

import chromadb

import config
from core.models import Segment

_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    return _client


def _embedding_function():
    """İstəyə bağlı çoxdilli embedding. Qurulmayıbsa None (Chroma-nın standartı işləyir)."""
    if not config.USE_MULTILINGUAL_EMBEDDINGS:
        return None
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        return SentenceTransformerEmbeddingFunction(model_name=config.EMBEDDING_MODEL)
    except Exception:
        return None


def reset_collection():
    """Köhnə kolleksiyanı silib təzəsini yaradır (hər yeni video üçün)."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass
    kwargs = {}
    ef = _embedding_function()
    if ef is not None:
        kwargs["embedding_function"] = ef
    _collection = client.create_collection(name=config.COLLECTION_NAME, **kwargs)
    return _collection


def add_segments(segments: Sequence[Segment]) -> None:
    """Seqmentləri bazaya əlavə edir."""
    if _collection is None:
        reset_collection()
    if not segments:
        return
    _collection.add(
        documents=[s.text for s in segments],
        metadatas=[{"index": s.index, "timestamp": s.timestamp} for s in segments],
        ids=[f"seg_{s.index}" for s in segments],
    )


def search(query: str, k: Optional[int] = None) -> list[int]:
    """Suala ən yaxın seqmentlərin indekslərini (uyğunluq sırası ilə) qaytarır."""
    if _collection is None:
        return []
    count = _collection.count()
    n = min(k or config.TOP_K_RESULTS, count)
    if n <= 0:
        return []
    result = _collection.query(query_texts=[query], n_results=n)
    metas = (result.get("metadatas") or [[]])[0]
    return [int(m["index"]) for m in metas]
