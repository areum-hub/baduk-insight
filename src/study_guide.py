"""Group existing Markdown Go lessons for a read-first learning guide.

Only reorganizes authored note material; never generates explanations.
"""
from __future__ import annotations

from collections import OrderedDict

CATEGORY_KEYWORDS = (
    ("기본 규칙·돌의 생사", (
        "활로", "단수", "연결", "끊", "두 눈", "두눈", "사활", "생사",
        "빅", "공배", "libert", "connection", "eyes", "life", "death", "seki",
    )),
    ("포석·돌의 형태", (
        "포석", "정석", "귀·변", "행마", "모양", "빈삼각",
        "fuseki", "joseki", "shape", "opening", "haengma",
    )),
    ("전투·수읽기", (
        "축", "장문", "수근", "패싸움", "패감", "공격", "수비",
        "선수", "후수", "tesuji", "ko_fight", "attack", "defense",
        "sente", "gote", "ladder", "tactics",
    )),
    ("끝내기·형세", (
        "끝내기", "계가", "실리", "세력", "형세", "집 계산",
        "endgame", "territory", "influence", "scoring",
    )),
)
OTHER_CATEGORY = "다른 바둑 개념"


def note_title(note: dict) -> str:
    """Use the original Markdown first-level heading as the display title."""
    for line in note.get("text", "").splitlines():
        if line.lstrip().startswith("# "):
            return line.lstrip()[2:].strip()
    return str(note.get("title") or note.get("path") or "학습 노트")


def note_answer(note: dict) -> str:
    """Return only the author's explanation, excluding heading and study prompt."""
    body = []
    for line in note.get("text", "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("학습 질문:", "생각해 볼 질문:", "복습 질문:")):
            continue
        body.append(stripped)
    return "\n\n".join(body)


def classify_note(note: dict) -> str:
    title = note_title(note).casefold()
    filename = str(note.get("path", "")).casefold()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(word.casefold() in title or word.casefold() in filename for word in keywords):
            return category
    return OTHER_CATEGORY


def grouped_study_notes(notes: list[dict]) -> dict[str, list[dict]]:
    """Group each nonempty note once, preserving a predictable category order."""
    result: dict[str, list[dict]] = OrderedDict(
        (label, []) for label, _ in CATEGORY_KEYWORDS
    )
    result[OTHER_CATEGORY] = []
    for note in notes:
        if note_answer(note):
            result[classify_note(note)].append(note)
    return {label: items for label, items in result.items() if items}
