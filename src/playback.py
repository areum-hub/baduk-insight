"""Pure helpers for automatic SGF review playback.

No Streamlit dependency: easy to unit test. Each timer event advances at most
one move so background-tab delays never skip ahead several moves at once.
"""


def advance(
    current_move: int,
    last_move: int,
    last_advance_time: float,
    now: float,
    seconds_per_move: int,
) -> tuple[int, float, bool]:
    """Return (move, time_anchor, still_playing) after an optional timer tick."""
    if seconds_per_move not in (1, 2, 3):
        raise ValueError("Playback speed must be 1, 2, or 3 seconds per move.")
    if last_move < 0:
        raise ValueError("Last move must be nonnegative.")
    if not 0 <= current_move <= last_move:
        raise ValueError("Current move out of bounds.")
    if current_move == last_move:
        return current_move, last_advance_time, False
    if now - last_advance_time < seconds_per_move:
        return current_move, last_advance_time, True
    next_move = current_move + 1
    return next_move, now, next_move < last_move


def move_manually(current_move: int, last_move: int, offset: int) -> int:
    """Return a clamped manual navigation position."""
    return min(max(current_move + offset, 0), last_move)


def toggle_playback(
    playing: bool,
    current_move: int,
    last_move: int,
    now: float,
) -> tuple[bool, float]:
    """Toggle pause/play and start a fresh interval without changing the move.

    The elapsed time before a pause must never carry into the next resume.
    Return the new playing state and a fresh monotonic time anchor.
    """
    if last_move < 0 or not 0 <= current_move <= last_move:
        raise ValueError("Current move out of bounds.")
    return (not playing and current_move < last_move), now
