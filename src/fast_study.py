"""Fast, source-grounded Korean Baduk note lookup without external models.

Match differently worded questions with concept aliases and phrase overlap.
Return only excerpts present in the local study notes, never invented analysis.
"""
from __future__ import annotations

import re


CONCEPTS: dict[str, tuple[str, ...]] = {
    "활로": ("활로", "단수", "숨통", "숨쉴", "빈 교차점", "따내", "돌이 잡히", "돌을 잡는"),
    "연결": ("연결", "끊", "이어", "이으", "잇", "이음", "떨어진 돌", "돌이 떨어", "돌이 분리", "돌이 흩어"),
    "사활": ("사활", "두 눈", "두눈", "죽는 돌", "죽어", "죽을", "살아남", "돌을 살리", "생사", "안형"),
    "정석": ("정석", "정해진 수순", "귀에서의 수순"),
    "행마": ("행마", "빈삼각", "호구", "돌의 움직임", "돌을 움직이", "돌 모양"),
    "포석": ("포석", "초반", "시작할 때", "처음에", "첫 수", "어디부터", "귀부터", "변부터", "초반 배치"),
    "수근": ("수근", "묘수", "좋은 형태", "효율적인 수"),
    "축": ("축", "축머리", "지그재그", "연속 단수"),
    "장문": ("장문", "도망 경로를 막", "도망길을 막", "넓게 막아 잡"),
    "선수": ("선수", "주도권", "응수", "상대가 받아야", "상대가 응수", "먼저 큰 곳"),
    "후수": ("후수", "상대에게 다음", "다음 큰 곳을 먼저"),
    "패": ("패", "패싸움", "패감", "되따내", "같은 모양 반복"),
    "빅": ("빅", "공배", "서로 살기", "함께 살아", "공통 활로"),
    "끝내기": ("끝내기", "계가", "종반", "막판", "집 계산", "집을 계산", "점수 계산"),
    "실리": ("실리", "집 확보", "집을 늘리", "집을 늘", "집을 지", "집짓", "집을 만들"),
    "세력": ("세력", "영향력", "두터움", "두터운", "외곽의 힘"),
    "공격": ("공격", "압박", "상대 돌을 잡", "돌을 쫓", "쫓아가", "포위"),
    "수비": ("수비", "방어", "도망", "약한 돌", "돌을 지키", "돌을 보호"),
}

STOPWORDS = frozenset({
    "바둑", "바둑판", "돌", "돌이", "돌을", "수", "현재", "장면", "국면", "이수", "이번",
    "어떻게", "어떤", "무엇", "뭐야", "뭔가", "궁금", "질문", "설명", "해줘", "알려줘",
    "알려", "이유", "왜", "차이", "비교", "중요", "좋아", "좋은", "해야", "하면",
    "하는", "있어", "있나", "할까", "것", "대한", "기본", "개념", "관련", "때", "저기",
})


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "", text.casefold())


def _contains_phrase(raw: str, compact: str, phrase: str) -> bool:
    term = _compact(phrase)
    if len(term) != 1:
        return bool(term) and term in compact
    # '패' must not match '실패', nor should '축' match '축구'.
    suffixes = (
        "", "이", "가", "은", "는", "을", "를", "와", "과", "도", "만", "에",
        "로", "의", "란", "이란", "때", "이면", "에서",
    )
    return any(
        word == term + suffix
        for word in re.findall(r"[가-힣]+", raw.casefold())
        for suffix in suffixes
    )


def _topic_hits(question: str) -> dict[str, int]:
    normalized = _compact(question)
    matches = {}
    for topic, aliases in CONCEPTS.items():
        lengths = [
            len(_compact(alias))
            for alias in aliases if _contains_phrase(question, normalized, alias)
        ]
        if lengths:
            matches[topic] = max(lengths)
    return matches


def _heading(note: dict) -> str:
    for line in note.get("text", "").splitlines():
        if line.lstrip().startswith("# "):
            return line.lstrip()[2:].strip()
    return note.get("title", "")


def _body_lines(note: dict) -> list[str]:
    return [
        line.strip() for line in note.get("text", "").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
        and not line.strip().startswith("학습 질문:")
    ]


def _query_terms(question: str) -> list[str]:
    words = re.findall(r"[가-힣a-z0-9]+", question.casefold())
    return [word for word in words if len(word) >= 2 and word not in STOPWORDS]


def _score(note: dict, query: str, hits: dict[str, int]) -> float:
    title = _compact(_heading(note))
    body = _compact(" ".join(_body_lines(note)))
    score = 0.0
    for topic, length in hits.items():
        term = _compact(topic)
        if term in title:
            score += 17 + min(5, length)
        elif term in body:
            score += 2.5 + min(2, length * 0.3)
    for word in _query_terms(query):
        if word in title:
            score += 5
        elif word in body:
            score += 0.85
    return score


def _excerpt(note: dict, question: str, max_lines: int = 3) -> str:
    lines = _body_lines(note)
    if not lines:
        return ""
    if len(lines) <= max_lines:
        selected = lines
    else:
        # Keep the definition, then choose the most relevant source lines.
        terms = _query_terms(question) + list(_topic_hits(question))
        rankings = sorted(
            range(1, len(lines)),
            key=lambda idx: (
                -sum(1 for word in terms if _compact(word) in _compact(lines[idx])),
                idx,
            ),
        )
        selected = [lines[i] for i in sorted([0, *rankings[:max_lines - 1]])]
    answer = " ".join(selected)
    if len(answer) > 500:
        answer = answer[:497].rsplit(" ", 1)[0] + "…"
    return answer


def quick_answer(question: str, notes: list[dict]) -> tuple[str, list[dict]]:
    """Return a relevant original note excerpt and internal source metadata.

    No Ollama, ChromaDB, embedding model, or live KataGo call.
    """
    if not question.strip() or not notes:
        return (
            "학습 노트에서 질문과 연결되는 내용을 찾지 못했습니다. "
            "바둑 개념을 조금 더 구체적으로 질문해 주세요.",
            [],
        )
    hits = _topic_hits(question)
    scored = sorted(
        ((_score(note, question, hits), note) for note in notes),
        key=lambda pair: pair[0], reverse=True,
    )
    best = scored[0][0]
    # Don't guess the answer when only incidental words happen to overlap.
    if best < 7:
        return (
            "학습 노트에서 질문과 관련된 설명을 찾지 못했습니다. "
            "연결·활로·축·장문·포석·패·끝내기 등 다른 말로도 질문해 볼 수 있습니다. "
            "현재 장면의 최선 수나 승률은 KataGo에서 분석해야 합니다.",
            [],
        )
    selected = [scored[0][1]]
    if len(scored) > 1 and scored[1][0] >= max(15, best * 0.88):
        # Distinct topics can require excerpts from two relevant notes.
        selected.append(scored[1][1])
    excerpts = []
    sources = []
    for note in selected:
        body = _excerpt(note, question, max_lines=3 if len(selected) == 1 else 2)
        if not body:
            continue
        heading = _heading(note)
        excerpts.append(f"**{heading}**\n\n{body}")
        sources.append({"title": note.get("title", heading), "path": note.get("path", "")})
    if not excerpts:
        return "관련 주제의 학습 노트가 있지만 설명 내용이 비어 있습니다.", []
    specific = ("현재장면", "이장면", "이번수", "지금이수", "최선수", "승률", "어디에둬", "이길까")
    preface = (
        "*아래는 일반 바둑 개념 설명이며, 현재 국면을 판정한 결과는 아닙니다.*\n\n"
        if any(word in _compact(question) for word in specific) else ""
    )
    return preface + "\n\n".join(excerpts), sources
