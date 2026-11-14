"""Save machine-specific KataGo paths in ignored local JSON (never GitHub)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

FIELDS = ("binary", "model", "config", "visits")


def load_settings(path: Path) -> dict:
    """Read locally saved KataGo settings; missing file means no overrides."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"로컬 KataGo 설정 파일을 읽을 수 없습니다: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("로컬 KataGo 설정은 JSON 객체여야 합니다.")
    return {key: data[key] for key in FIELDS if key in data}


def save_settings(path: Path, binary: str, model: str, config: str, visits: int) -> None:
    """Atomically save paths locally; this file is excluded from Git tracking."""
    values = {
        "binary": str(binary).strip(),
        "model": str(model).strip(),
        "config": str(config).strip(),
        "visits": int(visits),
    }
    if not values["binary"] or not values["config"] or values["visits"] not in (5, 10, 25, 50, 100):
        raise ValueError("KataGo 실행 파일, 설정 경로, 방문 수를 확인하세요.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".katago-settings-", suffix=".tmp",
            delete=False,
        ) as tmp:
            temp_name = tmp.name
            json.dump(values, tmp, ensure_ascii=False, indent=2)
        os.replace(temp_name, path)
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()


def suggested_paths(project: Path) -> dict:
    """Suggest existing local files on a first run without hardcoding user paths."""
    home = Path.home()
    binary = home / "KataGo" / "katago.exe"
    candidates = sorted(list((home / "Downloads").glob("*.bin.gz")) + list((home / "Downloads").glob("*.txt.gz")))
    return {
        "binary": str(binary) if binary.is_file() else "katago",
        "model": str(candidates[0]) if len(candidates) == 1 else "",
        "config": str(project / "configs" / "analysis_local.cfg"),
        "visits": 10,
    }
