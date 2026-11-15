"""SGF metadata formatting regression tests."""
from src.game_metadata import (
    format_game_details,
    format_game_title,
    format_sgf_date,
    format_sgf_result,
)


def test_go_seigen_1926_record_omits_unknown_and_filename():
    title = format_game_title("Go Seigen", "Wang Yunfeng")
    details = format_game_details("Unknown", "1926", "Beijing", "B+R")
    assert title == "Go Seigen (흑) vs Wang Yunfeng (백)"
    assert details == "1926년 · 베이징 · 흑 불계승"
    assert "Unknown" not in details
    assert "1926-00-00.sgf" not in details


def test_missing_fields_are_not_rendered_as_unknown():
    assert format_game_details("Unknown", "", "", "") == ""
    assert format_game_title("Unknown", None) == "흑 미상 (흑) vs 백 미상 (백)"


def test_partial_dates_preserve_only_known_precision():
    assert format_sgf_date("1926") == "1926년"
    assert format_sgf_date("1926-00-00") == "1926년"
    assert format_sgf_date("1926-05-00") == "1926년 5월"
    assert format_sgf_date("1926-05-13") == "1926년 5월 13일"


def test_result_codes():
    assert format_sgf_result("B+R") == "흑 불계승"
    assert format_sgf_result("W+T") == "백 시간승"
    assert format_sgf_result("B+2.5") == "흑 2.5집 승"
    assert format_sgf_result("?") == ""


def test_realistic_sgf_header_is_used_without_guessing_filename():
    from src.sgf_service import load_sgf
    source = (
        b"(;FF[4]GM[1]SZ[19]PB[Go Seigen]PW[Wang Yunfeng]"
        b"RE[B+R]DT[1926]PC[Beijing]RU[Old Chinese]"
        b"AB[dp][pd]AW[dd][pp];B[qj];W[nc])"
    )
    game = load_sgf(source)
    assert game.date == "1926"
    assert game.event == ""
    assert game.place == "Beijing"
    assert game.result == "B+R"
    assert format_game_details(game.event, game.date, game.place, game.result) == (
        "1926년 · 베이징 · 흑 불계승"
    )
    assert game.move_count == 2


def test_partial_sgf_calendar_date_does_not_invent_day():
    assert format_sgf_date("1926-00-00") == "1926년"
    assert format_sgf_date("1926-02-30") == "1926-02-30"
    assert format_sgf_date("1928-02-29") == "1928년 2월 29일"
