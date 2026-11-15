"""Human-readable match labels based solely on recorded SGF properties.

Never treat the source filename as the game date, and omit missing metadata
rather than showing a fabricated 'Unknown' event.
"""
from __future__ import annotations

import re


_MISSING = {"", "unknown", "none", "n/a", "na", "?", "-", "null"}


def _known(value: str | None) -> str:
    text = str(value).strip() if value is not None else ""
    return "" if text.casefold() in _MISSING else text


def format_game_title(black: str, white: str) -> str:
    """Display the recorded players with concise Korean colour labels."""
    return f"{_known(black) or '흑 미상'} (흑) vs {_known(white) or '백 미상'} (백)"


def format_sgf_date(value: str | None) -> str:
    """Show only the precision recorded by SGF DT (never by filename)."""
    raw = _known(value)
    if not raw:
        return ""
    match = re.fullmatch(r"(\d{4})(?:-(\d{1,2}|\?\?)(?:-(\d{1,2}|\?\?))?)?", raw)
    if not match:
        return raw
    year, month, day = match.groups()
    if not month or month in {"00", "0", "??"}:
        return f"{year}년"
    if not 1 <= int(month) <= 12:
        return raw
    if not day or day in {"00", "0", "??"}:
        return f"{year}년 {int(month)}월"
    if not 1 <= int(day) <= 31:
        return raw
    return f"{year}년 {int(month)}월 {int(day)}일"


def format_sgf_result(value: str | None) -> str:
    """Translate common SGF RE codes without inferring missing results."""
    raw = _known(value)
    if not raw:
        return ""
    upper = raw.upper()
    if upper in {"0", "DRAW", "JIGO"}:
        return "무승부"
    if upper in {"VOID", "?"}:
        return "무효"
    match = re.fullmatch(r"([BW])\+(.+)", upper)
    if not match:
        return raw
    side, margin = match.groups()
    winner = "흑" if side == "B" else "백"
    if margin in {"R", "RESIGN"}:
        return f"{winner} 불계승"
    if margin in {"T", "TIME"}:
        return f"{winner} 시간승"
    if margin in {"F", "FORFEIT"}:
        return f"{winner} 반칙승"
    if re.fullmatch(r"\d+(?:\.\d+)?", margin):
        return f"{winner} {margin}집 승"
    return raw


def format_game_details(
    event: str | None,
    date: str | None,
    place: str | None,
    result: str | None,
) -> str:
    """Omit absent fields and use the SGF event/date/place/result only."""
    recorded_place = _known(place)
    if recorded_place.casefold() == "beijing":
        recorded_place = "베이징"
    values = (
        _known(event),
        format_sgf_date(date),
        recorded_place,
        format_sgf_result(result),
    )
    return " · ".join(value for value in values if value)
