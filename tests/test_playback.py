"""Tests for SGF autoplay timing and manual navigation."""
import pytest

from src.playback import advance, move_manually


def test_one_move_at_each_configured_speed():
    for speed in (1, 2, 3):
        index, anchor, active = advance(4, 100, 10.0, 10.0 + speed - 0.01, speed)
        assert (index, anchor, active) == (4, 10.0, True)
        index, anchor, active = advance(4, 100, 10.0, 10.0 + speed, speed)
        assert index == 5 and active is True
        assert anchor == 10.0 + speed


def test_background_delay_does_not_skip_multiple_moves():
    index, anchor, active = advance(10, 100, 0.0, 120.0, 1)
    assert index == 11 and anchor == 120.0 and active


def test_stop_at_game_end():
    assert advance(283, 284, 5.0, 6.0, 1) == (284, 6.0, False)
    assert advance(284, 284, 5.0, 10.0, 1) == (284, 5.0, False)


def test_manual_navigation_is_clamped():
    assert move_manually(0, 284, -1) == 0
    assert move_manually(284, 284, 1) == 284
    assert move_manually(50, 284, -1) == 49


def test_invalid_playback_inputs():
    with pytest.raises(ValueError):
        advance(0, 10, 0.0, 1.0, 4)
    with pytest.raises(ValueError):
        advance(-1, 10, 0.0, 1.0, 1)
