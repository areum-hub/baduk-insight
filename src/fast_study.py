"""Immediate extractive answers for locally curated Baduk concepts.

This mode reads local Markdown notes and does not invoke Ollama or KataGo.
It is a concise note excerpt, not an LLM-generated judgment about the board.
"""
from __future__ import annotations

import re

# Short, carefully chosen terms make Korean concept lookup more reliable.
TOPIC_TERMS = {
    "connection": ("연결", "끊", "이음"),
    "fuseki": ("포석", "귀", "변", "중앙"),
    "tesuji": ("수근", "축", "장문"),
    "sente_gote": ("선수", "후수"),
    "ko_fight": ("패싸움", "패감", "패"),
    "seki": ("빅", "공배"),
    "endgame": ("끝내기", "계가"),
    "territory_influence": ("실리", "세력", "두터움"),
    "attack_defense": ("공격", "수비", "약한 돌"),
}


def _score(question: str, note: dict) -> int:
    question = re.sub(r"\s+", "", question.lower())
    name = note.get("path", "").lower()
    title = re.sub(r"\s+", "", note.get("title", "").lower())
    key = name.rsplit("/", 1)[-1].removesuffix(".md")
    score = 0
    for topic, terms in TOPIC_TERMS.items():
        if topic in key:
            score += sum(7 for term in terms if term in question)
    # Exact title/topic words take priority over loose shared characters.
    words = re.findall(r"[가-힣]{2,}|[a-z]{3,}", title)
    score += sum(3 for word in words if word in question)
    return score


def quick_answer(question: str, notes: list[dict]) -> tuple[str, list[dict]]:
    """Return a grounded excerpt and source, or a clear no-match message."""
    ranking = sorted(
        (( _score(question, note), note) for note in notes),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not ranking or ranking[0][0] < 3:
        return (
            "학습 노트에서 질문과 직접 연결되는 개념을 찾지 못했습니다. "
            "축·장문·연결·포석·패·끝내기처럼 구체적인 개념을 질문하거나 "
            "'AI 자세히 설명'을 이용해 주세요. 현재 바둑판의 정확한 수읽기는 KataGo 분석이 필요합니다.",
            [],
        )
    note = ranking[0][1]
    body = note.get("text", "")
    lines = [line.strip() for line in body.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    # Keep the excerpt grounded in the source, not generated or paraphrased.
    answer = " ".join(lines[:3])
    if len(answer) > 360:
        answer = answer[:357].rsplit(" ", 1)[0] + "…"
    return f"**{note['title']}**\n\n{answer}", [{"title": note["title"], "path": note["path"]}]
