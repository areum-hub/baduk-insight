"""Phase 3 tests use fake Ollama responses and a fake Chroma collection.

No model download or live KataGo/Ollama process is required.
"""
from types import SimpleNamespace

import pytest

from src import ollama_client, rag_pipeline


def test_embedding_payload(monkeypatch):
    calls = []
    def mock_post(endpoint, payload, timeout=120):
        calls.append((endpoint, payload))
        return {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}
    monkeypatch.setattr(ollama_client, "_post", mock_post)
    result = ollama_client.embed_texts(["축", "장문"])
    assert len(result) == 2
    assert calls[0][0] == "/api/embed"
    assert calls[0][1]["model"] == "embeddinggemma-2:270m"


def test_empty_or_wrong_embedding(monkeypatch):
    assert ollama_client.embed_texts([]) == []
    with pytest.raises(ValueError):
        ollama_client.embed_texts([""])
    monkeypatch.setattr(ollama_client, "_post", lambda *args, **kwargs: {"embeddings": []})
    with pytest.raises(ollama_client.OllamaError):
        ollama_client.embed_texts(["바둑"])


def test_chat_payload(monkeypatch):
    def mock_post(endpoint, payload, timeout=120):
        assert endpoint == "/api/chat"
        assert payload["stream"] is False
        assert payload["model"] == "qwen3:4b-instruct"
        return {"message": {"role": "assistant", "content": "두 돌이 연결됩니다."}}
    monkeypatch.setattr(ollama_client, "_post", mock_post)
    assert "연결" in ollama_client.chat([{"role": "user", "content": "연결이란?"}])


def test_curated_notes_and_prompts():
    notes = rag_pipeline.load_notes()
    assert len(notes) >= 16
    assert all(note["id"] and note["path"].endswith(".md") for note in notes)
    hits = [{"title": "연결", "path": "02_connection.md", "text": "돌은 활로를 공유한다."}]
    messages = rag_pipeline.build_messages("왜 연결?", hits, {"turn": 45, "game": "test"}, [])
    assert "[1]" in messages[0]["content"]
    assert "승률" in messages[0]["content"]
    assert "아직 해당 장면의 분석 결과가 없습니다" in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "왜 연결?"}


def test_prompt_with_confirmed_analysis_only():
    hits = [{"title": "포석", "path": "05_fuseki.md", "text": "전역적 돌 배치"}]
    analysis = {
        "rootInfo": {"winrate": 0.6, "scoreLead": 2.5},
        "moveInfos": [{"order": 0, "move": "Q16", "pv": ["Q16", "D4"], "visits": 100}],
    }
    messages = rag_pipeline.build_messages("왜 이 수?", hits, {"analysis": analysis})
    assert "Q16" in messages[0]["content"]
    assert "0.6" in messages[0]["content"]


class FakeCollection:
    def __init__(self):
        self.data = {}
    def count(self):
        return len(self.data)
    def get(self, include=None):
        return {"ids": list(self.data)}
    def delete(self, ids):
        for key in ids:
            self.data.pop(key, None)
    def upsert(self, ids, documents, embeddings, metadatas):
        self.data = {key: (doc, emb, meta) for key, doc, emb, meta in zip(ids, documents, embeddings, metadatas)}
    def query(self, query_embeddings, n_results, include):
        items = list(self.data.values())[:n_results]
        return {
            "documents": [[item[0] for item in items]],
            "metadatas": [[item[2] for item in items]],
            "distances": [[0.12 for _ in items]],
        }


def test_index_and_retrieve_without_live_models(monkeypatch):
    monkeypatch.setattr(rag_pipeline, "embed_texts", lambda texts: [[0.1, 0.3] for _ in texts])
    collection = FakeCollection()
    notes = [{"id": "a", "text": "축 설명", "title": "축", "path": "07_tesuji.md"}]
    assert rag_pipeline.build_index(notes, collection=collection) == 1
    result = rag_pipeline.retrieve("축이란?", collection=collection)
    assert result[0]["title"] == "축"
    assert result[0]["path"] == "07_tesuji.md"
    assert rag_pipeline.retrieve("", collection=collection) == []
