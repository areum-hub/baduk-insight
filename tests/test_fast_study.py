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


def test_paraphrased_connection_question():
    notes = [{"title": "연결과 끊음", "path": "02_connection.md",
              "text": "# 연결과 끊음\n연결된 돌은 활로를 공유한다.\n끊어진 돌은 공격받기 쉽다."}]
    for question in ("돌을 서로 이어서 두는 이유가 뭐야?", "돌이 흩어지면 위험해?"):
        answer, sources = quick_answer(question, notes)
        assert "연결" in answer
        assert sources[0]["path"] == "02_connection.md"


def test_paraphrased_fuseki_and_ko_questions():
    notes = [
        {"title": "포석", "path": "05_fuseki.md",
         "text": "# 포석과 귀·변·중앙\n포석은 초반의 전역적 돌 배치 전략이다."},
        {"title": "패", "path": "12_ko_fight.md",
         "text": "# 패와 패싸움\n패감의 가치는 패를 이길 때 얻는 이익과 비교한다."},
    ]
    assert quick_answer("초반에 어디부터 시작하지?", notes)[1][0]["path"] == "05_fuseki.md"
    assert quick_answer("패감은 언제 사용하는 거야?", notes)[1][0]["path"] == "12_ko_fight.md"


def test_unrelated_words_do_not_get_false_matches():
    notes = [
        {"title": "패와 패싸움", "path": "12_ko_fight.md",
         "text": "# 패와 패싸움\n패감이란 상대의 응수를 요구하는 수다."},
        {"title": "수근과 축·장문", "path": "07_tesuji.md",
         "text": "# 수근과 축·장문\n축은 지그재그로 돌을 몰아 잡는다."},
    ]
    for question in ("오늘 날씨는?", "바둑에서 실패란 뭐야?", "축구는 어떤 운동이야?"):
        assert quick_answer(question, notes)[1] == []


def test_two_topic_answer_grounded_in_both_notes():
    notes = [
        {"title": "축", "path": "07_tesuji.md",
         "text": "# 축과 장문\n축은 상대 돌을 지그재그로 잡는다.\n장문은 도망길을 막는다."},
        {"title": "장문", "path": "08_net.md",
         "text": "# 장문\n장문은 상대 돌이 도망가지 못하게 막는 수단이다."},
    ]
    text, sources = quick_answer("축과 장문은 어떻게 달라?", notes)
    assert sources
    assert "축" in text
    assert "장문" in text
