"""Local Ollama client for EmbeddingGemma 2 embeddings and Qwen chat.

All calls stay on the user's loopback interface. No remote AI API is used.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OLLAMA_BASE = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "embeddinggemma-2:270m"
CHAT_MODEL = "qwen3:4b-instruct"


class OllamaError(RuntimeError):
    """A local Ollama request could not be completed."""


def _post(endpoint: str, payload: dict, timeout: int = 120) -> dict:
    request = Request(
        OLLAMA_BASE + endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error", str(exc))
        except (UnicodeDecodeError, ValueError):
            detail = str(exc)
        raise OllamaError(
            f"Ollama 요청이 실패했습니다: {detail}. ollama pull 명령으로 모델 설치 여부를 확인하세요."
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OllamaError(
            "로컬 Ollama에 연결할 수 없습니다. Ollama 실행 상태와 설치된 모델을 확인하세요."
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise OllamaError("Ollama가 올바른 JSON 응답을 반환하지 않았습니다.") from exc
    if not isinstance(result, dict) or result.get("error"):
        raise OllamaError(f"Ollama 응답 오류: {result}")
    return result


def chat_stream(messages: list[dict], model: str = CHAT_MODEL):
    """Yield Ollama streaming text chunks to show an answer as it is generated.

    Streaming avoids waiting for the entire response before displaying text.
    Keeping answers short helps CPU-only machines, but first model load may be slow.
    """
    if not messages:
        raise ValueError("Chat messages are empty")
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": False,
        "keep_alive": "15m",
        "options": {"temperature": 0.2, "num_predict": 180, "num_ctx": 3072},
    }
    request = Request(
        OLLAMA_BASE + "/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    received = False
    try:
        with urlopen(request, timeout=90) as response:
            for raw in response:
                if not raw.strip():
                    continue
                try:
                    event = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise OllamaError("Ollama 스트리밍 응답이 올바르지 않습니다.") from exc
                if event.get("error"):
                    raise OllamaError(f"Ollama 오류: {event['error']}")
                message = event.get("message") or {}
                chunk = message.get("content", "") if isinstance(message, dict) else ""
                if chunk:
                    received = True
                    yield chunk
                if event.get("done"):
                    break
    except HTTPError as exc:
        raise OllamaError(f"Ollama HTTP 오류 ({exc.code}). 설치한 모델을 확인하세요.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OllamaError(
            "Ollama 응답이 지연되거나 연결에 실패했습니다. "
            "Ollama 실행 상태와 메모리 사용량을 확인하세요."
        ) from exc
    if not received:
        raise OllamaError("Ollama가 답변 텍스트를 반환하지 않았습니다.")


def embed_texts(texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
    """Return one embedding for each input using the local Ollama /api/embed."""
    if not texts:
        return []
    if not all(isinstance(text, str) and text.strip() for text in texts):
        raise ValueError("Cannot embed empty documents")
    data = _post("/api/embed", {"model": model, "input": texts}, timeout=180)
    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise OllamaError("임베딩 응답 개수가 요청한 문서 수와 다릅니다.")
    if any(not isinstance(vec, list) or not vec or not all(isinstance(x, (int, float)) for x in vec) for vec in embeddings):
        raise OllamaError("Ollama가 비정상적인 임베딩 벡터를 반환했습니다.")
    return embeddings


def chat(messages: list[dict], model: str = CHAT_MODEL) -> str:
    """Generate a Korean answer with the local Ollama chat endpoint."""
    if not messages:
        raise ValueError("Chat messages are empty")
    data = _post(
        "/api/chat",
        {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.2, "num_predict": 550},
        },
        timeout=240,
    )
    message = data.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise OllamaError("LLM이 빈 응답을 반환했습니다.")
    return content.strip()
