"""Tests for SGF autoplay timing and manual navigation."""
import pytest

from src.playback import advance, move_manually, seek_widget_key, toggle_playback


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


def test_pause_does_not_advance_and_resume_starts_fresh_two_second_interval():
    current = 17
    playing, anchor = toggle_playback(True, current, 250, 100.0)
    assert (playing, anchor) == (False, 100.0)
    # Waiting while paused does not count toward the next move.
    playing, anchor = toggle_playback(playing, current, 250, 120.0)
    assert (playing, anchor) == (True, 120.0)
    assert advance(current, 250, anchor, 121.99, 2) == (current, anchor, True)
    assert advance(current, 250, anchor, 122.0, 2) == (current + 1, 122.0, True)


def test_resume_at_last_move_remains_stopped():
    assert toggle_playback(False, 250, 250, 22.0) == (False, 22.0)


def test_autoplay_slider_key_tracks_displayed_position():
    digest = "1234567890abcdef" + "0" * 48
    assert seek_widget_key(digest, 10) != seek_widget_key(digest, 11)
    assert seek_widget_key(digest, 10) == seek_widget_key(digest, 10)
    assert seek_widget_key("abcdef1234567890", 10) != seek_widget_key(digest, 10)
    with pytest.raises(ValueError):
        seek_widget_key(digest, -1)
