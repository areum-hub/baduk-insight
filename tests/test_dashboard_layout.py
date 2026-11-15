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
    end = APP_SOURCE.index("\nwith left:", start)
    replay_code = APP_SOURCE[start:end]
    assert replay_code.index("st.html(render_board(") < replay_code.index("controls = st.columns(3)")
    assert replay_code.index("controls = st.columns(3)") < replay_code.index("st.slider(")
    assert "components.html(" not in replay_code


def test_ai_panel_is_right_of_board_and_refreshes_when_paused():
    assert "left, right = st.columns([62, 38]" in APP_SOURCE
    assert "with left:" in APP_SOURCE
    assert "with right:" in APP_SOURCE
    assert "st.session_state.replay_full_refresh = True" in APP_SOURCE
    assert 'st.rerun(scope="app")' in APP_SOURCE
    assert "disabled=st.session_state.playing" in APP_SOURCE


def test_study_chat_is_scoped_to_study_workspace():
    assert 'with st.container(key="study_workspace"):' in APP_SOURCE
    assert 'with st.container(key="study_chat_composer"):' in APP_SOURCE
    assert 'key="local_study_chat"' in APP_SOURCE
    assert '[data-testid="stBottomBlockContainer"]' not in APP_SOURCE


def test_autoplay_refreshes_only_while_playing():
    assert '@st.fragment(run_every="0.5s" if st.session_state.playing else None)' in APP_SOURCE
    assert "PLAYBACK_SECONDS = 2" in APP_SOURCE
