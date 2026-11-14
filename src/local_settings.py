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


LIGHT_MODEL_NAME = "kata1-b10c128-s1141046784-d204142634.txt.gz"
PREVIOUS_LARGE_MODEL_NAME = "kata1-tf3-b11c768-s12382M-d6533M.bin.gz"


def suggested_paths(project: Path) -> dict:
    """Default to the agreed lightweight network without a hardcoded username."""
    home = Path.home()
    binary = home / "KataGo" / "katago.exe"
    light_model = home / "Downloads" / LIGHT_MODEL_NAME
    return {
        "binary": str(binary) if binary.is_file() else "katago",
        # Show the intended file location even before download.
        "model": str(light_model),
        "config": str(project / "configs" / "analysis_local.cfg"),
        "visits": 5,
    }


def resolved_settings(project: Path, settings_path: Path) -> dict:
    """Restore per-PC values, upgrading the old large model to the small model.

    A manually saved *other* network is respected; the previously used large
    model is intentionally replaced even if the new model is not yet downloaded.
    """
    defaults = suggested_paths(project)
    stored = load_settings(settings_path)
    merged = defaults | stored
    selected_name = Path(str(stored.get("model", ""))).name
    if not selected_name or selected_name == PREVIOUS_LARGE_MODEL_NAME:
        merged["model"] = defaults["model"]
        merged["visits"] = 5
    if merged["visits"] not in (5, 10, 25, 50, 100):
        merged["visits"] = 5
    # Do not trust stale absolute config paths if project was moved.
    if not Path(str(merged["config"])).is_file():
        merged["config"] = defaults["config"]
    # Restore known home-folder engine if saved path was removed.
    stored_binary = str(merged["binary"]).strip()
    if not Path(stored_binary).is_file() and defaults["binary"] != "katago":
        merged["binary"] = defaults["binary"]
    return merged
