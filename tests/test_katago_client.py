"""Tests for request construction and KataGo output handling (no engine required)."""
import json
from types import SimpleNamespace
import pytest
from src.katago_client import build_query, gtp_coord, run_analysis, top_candidates, KataGoError


class FakeBoard:
    def list_occupied_points(self):
        return [("b", (3, 3)), ("w", (15, 15))]


def sample_record():
    return SimpleNamespace(
        size=19,
        move_count=3,
        setup_board=FakeBoard(),
        moves=[("b", (3, 15)), ("w", (15, 3)), ("b", None)],
    )


def test_gtp_coordinates_and_pass():
    assert gtp_coord((0, 0), 19) == "A1"
    assert gtp_coord((3, 15), 19) == "Q4"
    assert gtp_coord((15, 3), 19) == "D16"
    assert gtp_coord(None, 19) == "pass"


def test_query_analyzes_preceding_position():
    query = build_query(sample_record(), 2, "chinese", 7.5, 100)
    assert query["analyzeTurns"] == [2]
    assert query["initialStones"] == [["B", "D4"], ["W", "Q16"]]
    assert query["moves"] == [["B", "Q4"], ["W", "D16"]]
    assert query["boardXSize"] == 19
    assert query["komi"] == 7.5


def test_query_rejects_invalid_values():
    with pytest.raises(ValueError):
        build_query(sample_record(), 4, "chinese", 7.5, 100)
    with pytest.raises(ValueError):
        build_query(sample_record(), 1, "unknown", 7.5, 100)


def test_top_candidates_order():
    result = {"moveInfos": [
        {"move": "A1", "order": 2},
        {"move": "C3", "order": 0},
        {"move": "B2", "order": 1},
    ]}
    assert [m["move"] for m in top_candidates(result)] == ["C3", "B2", "A1"]


def test_engine_response_parsing(monkeypatch, tmp_path):
    config = tmp_path / "local.cfg"
    config.write_text("reportAnalysisWinratesAs = BLACK\n", encoding="utf-8")
    model = tmp_path / "model.bin.gz"
    model.write_bytes(b"test")
    binary = tmp_path / "katago"
    binary.write_text("test", encoding="utf-8")
    query = build_query(sample_record(), 1, "chinese", 7.5, 100)
    response = {"id": query["id"], "turnNumber": 1, "rootInfo": {"winrate": 0.7}, "moveInfos": []}
    def fake_run(command, **kwargs):
        assert command[1] == "analysis"
        assert json.loads(kwargs["input"])["id"] == query["id"]
        return SimpleNamespace(stdout=json.dumps(response) + "\n", stderr="", returncode=0)
    monkeypatch.setattr("src.katago_client.subprocess.run", fake_run)
    assert run_analysis(query, str(binary), str(model), str(config)) == response


def test_requires_black_perspective(monkeypatch, tmp_path):
    config = tmp_path / "local.cfg"
    config.write_text("reportAnalysisWinratesAs = WHITE\n", encoding="utf-8")
    model = tmp_path / "model.bin.gz"
    model.write_bytes(b"test")
    binary = tmp_path / "katago"
    binary.write_text("test", encoding="utf-8")
    with pytest.raises(KataGoError, match="BLACK"):
        run_analysis({"id": "a", "analyzeTurns": [0]}, str(binary), str(model), str(config))
