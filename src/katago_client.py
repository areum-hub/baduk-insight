"""KataGo JSON analysis protocol integration.

This is an on-demand local integration. KataGo binaries and neural net weights
must be installed separately and are never downloaded by the application.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path


class KataGoError(RuntimeError):
    """Raised for invalid settings or a failed engine invocation."""


COLUMNS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def gtp_coord(point, size: int) -> str:
    """Convert sgfmill's bottom-left (row, column) to a GTP coordinate."""
    if point is None:
        return "pass"
    row, col = point
    if not (0 <= row < size and 0 <= col < size and size <= len(COLUMNS)):
        raise ValueError(f"Invalid point {point} on a {size}x{size} board")
    return f"{COLUMNS[col]}{row + 1}"


def build_query(record, turn: int, rules: str, komi: float, max_visits: int) -> dict:
    """Analyze position after 'turn' moves, with original history preserved.

    For reviewing move N, pass turn=N-1 (the position *before* the played move).
    """
    if not (0 <= turn <= record.move_count):
        raise ValueError("Turn is outside the SGF game")
    if rules not in ("chinese", "japanese"):
        raise ValueError("Use Chinese or Japanese rules")
    if not 1 <= max_visits <= 10000:
        raise ValueError("max_visits must be between 1 and 10000")
    occupied = record.setup_board.list_occupied_points()
    initial_stones = [
        [colour.upper(), gtp_coord(point, record.size)]
        for colour, point in occupied
    ]
    actual_moves = [
        [colour.upper(), gtp_coord(point, record.size)]
        for colour, point in record.moves[:turn]
    ]
    first = record.moves[0][0].upper() if record.moves else "B"
    return {
        "id": str(uuid.uuid4()),
        "boardXSize": record.size,
        "boardYSize": record.size,
        "initialStones": initial_stones,
        "initialPlayer": first,
        "moves": actual_moves,
        "rules": rules,
        "komi": float(komi),
        "maxVisits": int(max_visits),
        "analysisPVLen": 10,
        "analyzeTurns": [turn],
    }


def _resolve_binary(binary: str) -> str:
    candidate = Path(binary).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())
    found = shutil.which(binary)
    if found:
        return str(Path(found).resolve())
    raise KataGoError("KataGo 실행 파일을 찾을 수 없습니다. KataGo 경로를 확인하세요.")


def _validate_config(config_path: Path) -> None:
    if not config_path.is_file():
        raise KataGoError(f"설정 파일이 없습니다: {config_path}")
    contents = config_path.read_text(encoding="utf-8-sig")
    if not re.search(r"^\s*reportAnalysisWinratesAs\s*=\s*BLACK\s*(?:#.*)?$", contents, re.M | re.I):
        raise KataGoError(
            "승률 표시 오류를 방지하기 위해 분석 설정에 "
            "'reportAnalysisWinratesAs = BLACK'을 지정해 주세요."
        )


def run_analysis(
    query: dict,
    binary: str,
    model: str,
    config: str,
    timeout_seconds: int = 180,
) -> dict:
    """Run one KataGo analysis request and return the final JSON response.

    Closing stdin after one query makes KataGo drain its pending analyses and
    exit. This is robust but may be slower than a persistent engine.
    """
    executable = _resolve_binary(binary)
    model_path = Path(model).expanduser().resolve()
    config_path = Path(config).expanduser().resolve()
    if not model_path.is_file():
        raise KataGoError(f"신경망 모델 파일을 찾을 수 없습니다: {model_path}")
    _validate_config(config_path)
    if not 10 <= timeout_seconds <= 3600:
        raise ValueError("Invalid timeout")
    try:
        finished = subprocess.run(
            [executable, "analysis", "-config", str(config_path), "-model", str(model_path)],
            input=json.dumps(query, ensure_ascii=False) + "\n",
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise KataGoError("KataGo 분석 시간이 초과되었습니다. 방문 수를 줄이거나 PC 설정을 확인하세요.") from exc
    except OSError as exc:
        raise KataGoError(f"KataGo 실행에 실패했습니다: {exc}") from exc

    for raw in finished.stdout.splitlines():
        try:
            response = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(response, dict):
            continue
        if response.get("error") and (not response.get("id") or response.get("id") == query["id"]):
            raise KataGoError(str(response["error"]))
        if response.get("id") == query["id"] and not response.get("isDuringSearch"):
            if response.get("turnNumber") != query["analyzeTurns"][0]:
                continue
            if "rootInfo" not in response:
                continue
            return response

    detail = finished.stderr.strip()[-700:] if finished.stderr else ""
    raise KataGoError(
        f"KataGo가 분석 결과를 반환하지 않았습니다 (종료 코드 {finished.returncode})."
        + (f" 로그: {detail}" if detail else "")
    )


def top_candidates(response: dict, limit: int = 3) -> list[dict]:
    """Return highest-ranked candidate moves with perspective fixed to Black."""
    return sorted(response.get("moveInfos", []), key=lambda move: move.get("order", 9999))[:limit]
