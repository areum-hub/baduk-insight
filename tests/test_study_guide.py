"""Category grouping and authored-explanation display tests."""
from src.study_guide import classify_note, grouped_study_notes, note_answer, note_title


def test_note_body_is_original_text_without_learning_prompt():
    note = {
        "title": "02_connection",
        "path": "02_connection.md",
        "text": "# 연결과 끊음\n연결된 돌은 활로를 공유한다.\n학습 질문: 왜 이어야 할까?",
    }
    assert note_title(note) == "연결과 끊음"
    assert note_answer(note) == "연결된 돌은 활로를 공유한다."


def test_groups_notes_only_once_and_keeps_contents():
    notes = [
        {"title": "활로", "path": "01_liberties.md", "text": "# 활로와 단수\n활로는 비어 있는 교차점이다."},
        {"title": "포석", "path": "05_fuseki.md", "text": "# 포석과 귀·변·중앙\n포석은 바둑 초반의 돌 배치다."},
        {"title": "패싸움", "path": "12_ko_fight.md", "text": "# 패와 패싸움\n패감의 가치를 비교한다."},
        {"title": "끝내기", "path": "14_endgame.md", "text": "# 끝내기와 계가\n경계를 정리한다."},
    ]
    groups = grouped_study_notes(notes)
    assert list(groups) == ["기본 규칙·돌의 생사", "포석·돌의 형태", "전투·수읽기", "끝내기·형세"]
    assert sum(map(len, groups.values())) == len(notes)
    assert groups["기본 규칙·돌의 생사"][0]["path"] == "01_liberties.md"


def test_missing_or_empty_note_does_not_create_blank_card():
    notes = [{"title": "empty", "path": "empty.md", "text": "# 비어 있음"}]
    assert grouped_study_notes(notes) == {}


def test_fuseki_does_not_match_seki_substring():
    """English Go terms must not accidentally match inside other terms."""
    opening = {
        "title": "Fuseki",
        "path": "05_fuseki.md",
        "text": "# 포석과 귀·변·중앙\n초반에 전역적 배치를 검토한다.",
    }
    seki = {
        "title": "Seki",
        "path": "13_seki.md",
        "text": "# 빅\n서로 상대를 잡을 수 없는 상태다.",
    }
    assert classify_note(opening) == "포석·돌의 형태"
    assert classify_note(seki) == "기본 규칙·돌의 생사"


def test_english_filename_keywords_still_match_when_standalone():
    """Token matching must keep the names used by the actual note archive."""
    for filename, category in (
        ("01_liberties.md", "기본 규칙·돌의 생사"),
        ("05_fuseki.md", "포석·돌의 형태"),
        ("12_ko_fight.md", "전투·수읽기"),
        ("14_endgame.md", "끝내기·형세"),
    ):
        note = {"title": "Example", "path": filename, "text": "# Example\n본문"}
        assert classify_note(note) == category
