"""Tests for locally persisted CPU KataGo setup."""
import pytest

from src.local_settings import (
    LIGHT_MODEL_NAME,
    load_settings,
    resolved_settings,
    save_settings,
    suggested_paths,
)


def test_local_round_trip(tmp_path):
    path = tmp_path / "data" / "local" / "katago_settings.json"
    assert load_settings(path) == {}
    save_settings(path, "C:/KataGo/katago.exe", "C:/models/weights.txt.gz", "config.cfg", 5)
    assert load_settings(path) == {
        "binary": "C:/KataGo/katago.exe",
        "model": "C:/models/weights.txt.gz",
        "config": "config.cfg",
        "visits": 5,
    }


def test_invalid_saved_json(tmp_path):
    path = tmp_path / "wrong.json"
    path.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ValueError, match="로컬 KataGo"):
        load_settings(path)


def test_invalid_visit_count(tmp_path):
    with pytest.raises(ValueError):
        save_settings(tmp_path / "settings.json", "katago", "model.txt.gz", "cfg", 200)


def test_user_home_default_with_fixed_small_model(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / "Downloads").mkdir(parents=True)
    (home / "KataGo").mkdir()
    (home / "KataGo" / "katago.exe").write_bytes(b"exe")
    monkeypatch.setattr("src.local_settings.Path.home", lambda: home)
    defaults = suggested_paths(tmp_path)
    assert defaults["visits"] == 5
    assert defaults["binary"] == str(home / "KataGo" / "katago.exe")
    assert defaults["model"] == str(home / "Downloads" / LIGHT_MODEL_NAME)
    assert defaults["config"] == str(tmp_path / "configs" / "analysis_local.cfg")


def test_previous_large_model_migrated_to_small(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / "Downloads").mkdir(parents=True)
    monkeypatch.setattr("src.local_settings.Path.home", lambda: home)
    saved = tmp_path / "data" / "local" / "katago_settings.json"
    save_settings(
        saved,
        "katago",
        str(home / "Downloads" / "kata1-tf3-b11c768-s12382M-d6533M.bin.gz"),
        str(tmp_path / "configs" / "analysis_local.cfg"),
        100,
    )
    resolved = resolved_settings(tmp_path, saved)
    assert resolved["model"] == str(home / "Downloads" / LIGHT_MODEL_NAME)
    assert resolved["visits"] == 5


def test_custom_model_is_preserved(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setattr("src.local_settings.Path.home", lambda: home)
    saved = tmp_path / "data" / "local" / "katago_settings.json"
    save_settings(saved, "katago", "D:/weights/custom.txt.gz", "config.cfg", 25)
    resolved = resolved_settings(tmp_path, saved)
    assert resolved["model"] == "D:/weights/custom.txt.gz"
    assert resolved["visits"] == 25
