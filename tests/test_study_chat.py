"""Local Qwen prompt construction must stay grounded and concise."""
from src.study_chat import LOCAL_CHAT_MODEL, build_study_chat_messages


def test_lightweight_local_model():
    assert LOCAL_CHAT_MODEL == "qwen3:1.7b"


def test_selected_lesson_is_included():
    note = {"title": "02_connection", "path": "02_connection.md",
            "text": "# 연결과 끊음\n연결된 돌은 활로를 공유한다."}
    messages = build_study_chat_messages("왜 이어야 해?", [note], selected_note=note)
    assert "연결된 돌은 활로를 공유한다." in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "왜 이어야 해?"}
    assert "승률" in messages[0]["content"]


def test_empty_question_rejected():
    try:
        build_study_chat_messages("   ", [])
    except ValueError:
        pass
    else:
        raise AssertionError("empty question must raise")


def test_no_reference_does_not_add_invented_material():
    messages = build_study_chat_messages("오늘 날씨는?", [])
    assert "직접 관련된 학습 노트를 찾지 못했습니다" in messages[0]["content"]
