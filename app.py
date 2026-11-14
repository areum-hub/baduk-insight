"""Baduk Insight — Phase 1 SGF viewer prototype."""
import hashlib
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from src.board_svg import render_board
from src.sgf_service import load_sgf, replay

DATA_DIR = Path(__file__).resolve().parent / "data" / "sgf"
st.set_page_config(page_title="Baduk Insight", page_icon="⚫", layout="wide")
st.title("Baduk Insight")
st.caption("Personal AI Go learning project | Phase 1: SGF review")
st.info("KataGo analysis and the RAG chatbot are planned; this version only replays game records.")

available = sorted(DATA_DIR.glob("*.sgf")) if DATA_DIR.exists() else []
with st.sidebar:
    st.header("Load a game")
    source = st.radio("Source", ["Local CWI samples", "Upload SGF"])
    raw = None
    name = ""
    if source == "Upload SGF":
        uploaded = st.file_uploader("Choose SGF", type=["sgf"])
        if uploaded is not None:
            raw, name = uploaded.getvalue(), uploaded.name
    elif available:
        selected = st.selectbox("Professional game", available, format_func=lambda p: p.name)
        if selected:
            raw, name = selected.read_bytes(), selected.name
    else:
        st.warning("No local SGFs. Run: python scripts/download_cwi_samples.py")
    st.markdown("[CWI archive](https://homepages.cwi.nl/~aeb/go/games/games/)")

if raw is None:
    st.code("python scripts/download_cwi_samples.py\nstreamlit run app.py", language="bash")
    st.stop()

try:
    game = load_sgf(raw)
except Exception as exc:
    st.error(f"Cannot read SGF: {exc}")
    st.stop()

if game.size not in (9, 13, 19):
    st.error(f"Unsupported board size: {game.size}")
    st.stop()

digest = hashlib.sha256(raw).hexdigest()
if st.session_state.get("game_digest") != digest:
    st.session_state.game_digest = digest
    st.session_state.move_index = 0

st.subheader(f"{game.black_player} (Black) vs {game.white_player} (White)")
st.caption(f"{game.event} | {game.date} | {game.result} | {name}")
left, right = st.columns([1.5, 1])
with left:
    back, forward = st.columns(2)
    if back.button("Previous", disabled=st.session_state.move_index == 0):
        st.session_state.move_index -= 1
    if forward.button("Next", disabled=st.session_state.move_index == game.move_count):
        st.session_state.move_index += 1
    st.slider("Move", 0, game.move_count, key="move_index")
    try:
        board, last = replay(game, st.session_state.move_index)
    except (ValueError, IndexError) as exc:
        st.error(f"Could not replay move: {exc}")
        st.stop()
    board_height = 625 if game.size == 19 else (510 if game.size == 13 else 410)
    components.html(render_board(board, last_move=last), height=board_height, scrolling=False)
with right:
    st.markdown("### Game review")
    st.metric("Move", f"{st.session_state.move_index} / {game.move_count}")
    if st.session_state.move_index:
        colour, point = game.moves[st.session_state.move_index-1]
        who = "Black" if colour == "b" else "White"
        if point is None:
            st.write(f"Latest move: **{who} pass**")
        else:
            row, col = point
            coordinate = "ABCDEFGHJKLMNOPQRSTUVWXYZ"[col] + str(row+1)
            st.write(f"Latest move: **{who} {coordinate}**")
    st.markdown("### Planned")
    st.markdown("- KataGo position analysis\n- RAG explanations of Go concepts\n- Conversational review\n- Personal study notes")
    st.caption("Only the main SGF line is displayed. Branch variations are not yet supported.")
