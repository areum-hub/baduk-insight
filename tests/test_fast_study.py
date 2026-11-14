"""Fast study mode must stay local and cite its source notes."""
from src.fast_study import quick_answer


def test_instant_topic_response():
    notes = [
        {"title": "연결과 끊음", "path": "02_connection.md",
         "text": "# 연결과 끊음\n돌이 연결되면 활로를 공유한다.\n끊기면 공격받기 쉽다."},
        {"title": "끝내기", "path": "14_endgame.md",
         "text": "# 끝내기\n끝내기는 경계를 정리하는 단계다."},
    ]
    answer, refs = quick_answer("돌의 연결은 왜 중요해?", notes)
    assert "활로" in answer
    assert refs == [{"title": "연결과 끊음", "path": "02_connection.md"}]


def test_unknown_question_does_not_invent_board_analysis():
    notes = [{"title": "포석", "path": "05_fuseki.md",
              "text": "# 포석\n포석은 바둑 초반의 배치다."}]
    answer, refs = quick_answer("이 장면의 최선의 착수는 어디야?", notes)
    assert refs == []
    assert "KataGo" in answer


def test_no_notes_is_safe():
    answer, refs = quick_answer("장문", [])
    assert refs == []
    assert "찾지 못했습니다" in answer
