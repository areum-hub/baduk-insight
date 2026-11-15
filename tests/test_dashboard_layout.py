"""Static regression checks for the Streamlit dashboard composition.

AST inspection avoids importing app.py, which starts Streamlit, downloads
remote SGFs, and would require a running server during pytest collection.
"""
import ast
from pathlib import Path


APP_SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_dashboard_has_valid_python_syntax():
    ast.parse(APP_SOURCE, filename="app.py")


def test_board_is_drawn_before_controls_and_seek_slider():
    start = APP_SOURCE.index("def show_replay():")
    end = APP_SOURCE.index("\nshow_replay()", start)
    replay_code = APP_SOURCE[start:end]
    assert replay_code.index("st.image(") < replay_code.index("controls = st.columns(3)")
    assert replay_code.index("controls = st.columns(3)") < replay_code.index("st.slider(")
    assert "render_board(board, last_move=last, ai_suggestion=ai_point)" in replay_code
    assert "use_container_width=True" in replay_code
    assert "st.html(render_board(" not in replay_code
    assert "components.html(" not in replay_code


def test_ai_panel_is_right_of_board_and_refreshes_when_paused():
    assert "left, right = st.columns([62, 38]" in APP_SOURCE
    fragment_code = APP_SOURCE.split("def show_replay():", 1)[1].split("\nshow_replay()", 1)[0]
    assert "with left:" in fragment_code
    assert "with right:" in fragment_code
    assert "st.session_state.replay_full_refresh = True" in fragment_code
    assert 'st.rerun(scope="fragment")' in fragment_code
    assert "disabled=st.session_state.playing" in fragment_code


def test_study_chat_is_scoped_to_study_workspace():
    assert 'with st.container(key="study_workspace"):' in APP_SOURCE
    assert 'with st.container(key="study_chat_composer"):' in APP_SOURCE
    assert 'key="local_study_chat"' in APP_SOURCE
    assert '[data-testid="stBottomBlockContainer"]' not in APP_SOURCE


def test_autoplay_refreshes_only_while_playing():
    assert '@st.fragment(run_every="0.5s" if st.session_state.playing else None)' in APP_SOURCE
    assert "PLAYBACK_SECONDS = 2" in APP_SOURCE


def test_match_header_uses_parsed_sgf_metadata_not_filename():
    assert "format_game_title(record.black_player, record.white_player)" in APP_SOURCE
    assert "record.event, record.date, record.place, record.result" in APP_SOURCE
    assert 'st.caption(f"{record.event} | {record.date} | {record.result} | {name}")' not in APP_SOURCE


def test_paused_manual_controls_avoid_full_app_reruns():
    replay = APP_SOURCE.split("def show_replay():", 1)[1].split("\nshow_replay()", 1)[0]
    assert replay.count('st.rerun(scope="app" if was_playing else "fragment")') == 2
    assert "st.session_state.replay_full_refresh = was_playing" in replay
    assert "st.session_state.replay_start_pending = playing" in replay
    assert 'st.session_state.pop("replay_start_pending", False)' in replay
    assert replay.index("left, right = st.columns([62, 38]") < replay.index("with right:")
