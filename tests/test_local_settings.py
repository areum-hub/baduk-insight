"""Tests for locally persisted KataGo file paths and fast-study defaults."""
import json

import pytest

from src.local_settings import load_settings, save_settings, suggested_paths


def test_local_round_trip(tmp_path):
    path = tmp_path / "data" / "local" / "katago_settings.json"
    assert load_settings(path) == {}
    save_settings(path, "C:/KataGo/katago.exe", "C:/models/weights.bin.gz", "config.cfg", 10)
    assert load_settings(path) == {
        "binary": "C:/KataGo/katago.exe",
        "model": "C:/models/weights.bin.gz",
        "config": "config.cfg",
        "visits": 10,
    }


def test_invalid_saved_json(tmp_path):
    path = tmp_path / "wrong.json"
    path.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ValueError, match="로컬 KataGo"):
        load_settings(path)


def test_invalid_visit_count(tmp_path):
    with pytest.raises(ValueError):
        save_settings(tmp_path / "settings.json", "katago", "model.bin.gz", "cfg", 200)


def test_auto_suggestion_requires_unambiguous_model(monkeypatch, tmp_path):
    home = tmp_path / "home"
    downloads = home / "Downloads"
    downloads.mkdir(parents=True)
    (downloads / "a.bin.gz").write_bytes(b"test")
    (downloads / "b.bin.gz").write_bytes(b"test")
    monkeypatch.setattr("src.local_settings.Path.home", lambda: home)
    defaults = suggested_paths(tmp_path)
    assert defaults["visits"] == 10
    assert defaults["model"] == ""
    (downloads / "b.bin.gz").unlink()
    assert suggested_paths(tmp_path)["model"].endswith("a.bin.gz")
