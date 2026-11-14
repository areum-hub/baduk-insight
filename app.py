"""Baduk Insight — SGF review + on-demand KataGo analysis (Phase 2)."""
import hashlib
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from sgfmill import sgf

from src.board_svg import render_board
from src.katago_client import KataGoError, build_query, gtp_coord, run_analysis, top_candidates
from src.sgf_service import load_sgf, replay

PROJECT = Path(__file__).resolve().parent
DATA_DIR = PROJECT / "data" / "sgf"
DEFAULT_CONFIG = PROJECT / "configs" / "analysis_local.cfg"

st.set_page_config(page_title="Baduk Insight", page_icon="⚫", layout="wide")
st.title("Baduk Insight")
st.caption("Personal AI Go learning project | Phase 2: KataGo analysis")
st.info("현재 단계: SGF 복기 + 선택한 착수의 KataGo 분석. RAG 챗봇과 학습 기록은 이후 구현할 예정입니다.")

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

    st.divider()
    st.header("KataGo (local)")
    binary = st.text_input("KataGo executable (path or katago)", value="katago")
    model = st.text_input("Neural net model path (.bin.gz)", value="")
    config = st.text_input("Analysis config path", value=str(DEFAULT_CONFIG))
    visits = st.select_slider("Maximum visits", options=[25, 50, 100, 200, 500], value=100)
    st.caption("분석 실행에는 별도로 설치한 KataGo 실행 파일과 신경망 모델이 필요합니다.")

if raw is None:
    st.code("python scripts/download_cwi_samples.py\nstreamlit run app.py", language="bash")
    st.stop()

try:
    record = load_sgf(raw)
    original_sgf = sgf.Sgf_game.from_bytes(raw)
except Exception as exc:
    st.error(f"Cannot read SGF: {exc}")
    st.stop()

if record.size not in (9, 13, 19):
    st.error(f"Unsupported board size: {record.size}")
    st.stop()

root = original_sgf.get_root()
def sgf_property(prop, fallback=""):
    try:
        return str(root.get(prop)) if root.has_property(prop) else fallback
    except (ValueError, TypeError):
        return fallback

sgf_rules = sgf_property("RU", "").lower()
suggested_rules = "japanese" if any(w in sgf_rules for w in ("japanese", "korean", "territory")) else "chinese"
try:
    suggested_komi = float(sgf_property("KM", "7.5"))
except ValueError:
    suggested_komi = 7.5

with st.sidebar:
    st.subheader("Analysis game settings")
    rules = st.selectbox(
        "Rules for KataGo",
        ["chinese", "japanese"],
        index=0 if suggested_rules == "chinese" else 1,
        help="기보의 실제 규칙과 동일한 설정인지 확인해 주세요. 정확히 일치하지 않으면 분석 수치가 달라질 수 있습니다.",
    )
    komi = st.number_input("Komi", min_value=-20.0, max_value=30.0, value=suggested_komi, step=0.5)
    st.caption(f"SGF RU: {sgf_rules or 'not specified'}; KM: {sgf_property('KM', 'not specified')}")

digest = hashlib.sha256(raw).hexdigest()
if st.session_state.get("game_digest") != digest:
    st.session_state.game_digest = digest
    st.session_state.move_index = 0
    st.session_state.analysis_result = None
    st.session_state.analysis_key = None

st.subheader(f"{record.black_player} (Black) vs {record.white_player} (White)")
st.caption(f"{record.event} | {record.date} | {record.result} | {name}")
left, right = st.columns([1.45, 1])
with left:
    back, forward = st.columns(2)
    if back.button("Previous", disabled=st.session_state.move_index == 0):
        st.session_state.move_index -= 1
    if forward.button("Next", disabled=st.session_state.move_index == record.move_count):
        st.session_state.move_index += 1
    st.slider("Move", 0, record.move_count, key="move_index")
    try:
        board, last = replay(record, st.session_state.move_index)
    except (ValueError, IndexError) as exc:
        st.error(f"Could not replay move: {exc}")
        st.stop()
    height = 625 if record.size == 19 else (510 if record.size == 13 else 410)
    components.html(render_board(board, last_move=last), height=height, scrolling=False)

with right:
    turn = st.session_state.move_index
    st.markdown("### Game review")
    st.metric("Current move", f"{turn} / {record.move_count}")
    if turn:
        colour, point = record.moves[turn-1]
        who = "Black" if colour == "b" else "White"
        st.write(f"Last played: **{who} {gtp_coord(point, record.size)}**")

    st.divider()
    st.markdown("### KataGo analysis")
    st.caption("현재 표시된 수가 아닌, 그 수를 두기 **직전의 국면**에서 AI 추천 수를 분석합니다.")
    if turn == 0:
        st.info("첫 수(착점 이전)를 분석하려면 수순을 1로 이동하세요.")
    else:
        lookup = (digest, turn, rules, float(komi), visits, binary, model, config)
        if st.button("Analyze position before this move", type="primary"):
            try:
                query = build_query(record, turn - 1, rules, float(komi), visits)
                with st.spinner("KataGo 분석 중..."):
                    result = run_analysis(query, binary, model, config, timeout_seconds=180)
                st.session_state.analysis_key = lookup
                st.session_state.analysis_result = result
            except (KataGoError, ValueError, OSError) as exc:
                st.session_state.analysis_key = None
                st.session_state.analysis_result = None
                st.error(str(exc))

        if st.session_state.get("analysis_key") == lookup:
            analysis = st.session_state.get("analysis_result")
            if analysis:
                root_info = analysis.get("rootInfo", {})
                black_winrate = root_info.get("winrate")
                if isinstance(black_winrate, (int, float)):
                    st.metric("흑 승률 (착수 직전)", f"{100 * black_winrate:.1f}%")
                score_lead = root_info.get("scoreLead")
                if isinstance(score_lead, (int, float)):
                    st.metric("예상 점수 차이 (흑 기준)", f"{score_lead:+.1f}집")
                st.caption(f"검색 방문 수: {root_info.get('visits', 'unknown')} · 분석 국면: {analysis.get('turnNumber', 'unknown')}수 이후")
                suggestions = top_candidates(analysis)
                if suggestions:
                    st.markdown("**AI 추천 후보 수**")
                    for candidate in suggestions:
                        st.write(f"{int(candidate.get('order', 0))+1}. **{candidate.get('move', '?')}** · 방문 수 {candidate.get('visits', '?')}")
                        if candidate.get("pv"):
                            st.caption("변화도: " + " → ".join(candidate["pv"][:10]))
                    actual = gtp_coord(record.moves[turn-1][1], record.size)
                    best = suggestions[0].get("move")
                    st.info(f"실제 프로기사 착수: {actual} · AI 첫 추천: {best}")
                else:
                    st.warning("후보 수가 반환되지 않았습니다.")
                st.caption("이 분석은 해당 수를 평가하기 *전*의 후보 비교입니다. 실수 여부나 승률 손실을 판단하려면 착수 이후 국면도 별도로 비교해야 합니다.")

    st.divider()
    st.markdown("### Next: Phase 3")
    st.markdown("- EmbeddingGemma 2 / ChromaDB 기반 바둑 개념 검색\n- AI 대화형 복기 설명\n- 개인 학습 기록")
    st.caption("SGF 메인 수순만 탐색합니다. SGF 변화도(분기)는 아직 표시하지 않습니다.")
