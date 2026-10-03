"""ChromaDB testi. Real embedding modeli yüklənməsin deyə sadə oflayn embedding istifadə olunur."""
import hashlib

import pytest
from chromadb import Documents, EmbeddingFunction, Embeddings

from core import vector_store
from core.models import Segment


class HashEmbedding(EmbeddingFunction):
    """Sözləri hash-ləyib 64 ölçülü vektor yaradır (oxşar sözlər -> yaxın vektor)."""

    def __init__(self):
        pass

    def __call__(self, input: Documents) -> Embeddings:
        out = []
        for text in input:
            vec = [0.0] * 64
            for word in text.lower().split():
                vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
            out.append(vec)
        return out

    @staticmethod
    def name() -> str:
        return "hash-embedding"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return HashEmbedding()


@pytest.fixture
def store(data_dirs, monkeypatch):
    monkeypatch.setattr(vector_store, "_client", None)
    monkeypatch.setattr(vector_store, "_collection", None)
    monkeypatch.setattr(vector_store, "_embedding_function", lambda: HashEmbedding())
    return vector_store


def segs(*texts):
    return [Segment(i, i * 10, i * 10 + 9, t) for i, t in enumerate(texts)]


def test_search_returns_best_match_first(store):
    store.reset_collection()
    store.add_segments(segs("cats are cute animals", "how to install python on windows", "the weather is sunny"))
    assert store.search("install python windows", k=3)[0] == 1


def test_search_without_collection_or_empty(store):
    assert store.search("anything") == []
    store.reset_collection()
    assert store.search("anything") == []


def test_reset_collection_clears_old_data(store):
    store.reset_collection()
    store.add_segments(segs("alpha beta", "gamma delta"))
    store.reset_collection()
    assert store.search("alpha") == []


def test_search_clamps_k_to_collection_size(store):
    store.reset_collection()
    store.add_segments(segs("one", "two"))
    assert len(store.search("one", k=50)) == 2
