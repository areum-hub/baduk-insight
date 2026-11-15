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
    # Preserve the nominal cadence after small UI/rendering delays: a tick
    # observed at 2.3 s still belongs to the 2.0 s boundary, so the next
    # position is due around 4.0 s rather than 4.3 s.
    next_anchor = last_advance_time + seconds_per_move
    # After a major stall (e.g. background tab or expensive rendering),
    # restart from 'now' rather than advancing moves in a rapid burst.
    if now - next_anchor >= seconds_per_move / 2:
        next_anchor = now
    return next_move, next_anchor, next_move < last_move


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


def seek_widget_key(game_digest: str, move_index: int) -> str:
    """Use a fresh slider key when the board position changes.

    The autoplay fragment must not repeatedly assign to the Session State
    of an existing slider widget; that can conflict with Streamlit reruns.
    """
    if move_index < 0:
        raise ValueError("Move index must be nonnegative.")
    return f"replay_seek_{game_digest[:16]}_{move_index}"
