"""Baduk Insight — SGF, KataGo, and local RAG study chatbot (Phase 3)."""
import hashlib
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from sgfmill import sgf

from src.board_svg import render_board
from src.katago_client import KataGoError, build_query, gtp_coord, run_analysis, top_candidates
from src.sgf_service import load_sgf, replay
from src.playback import advance, move_manually
from src.ollama_client import OllamaError, chat
from src.rag_pipeline import build_index, build_messages, get_collection, load_notes, retrieve
from scripts.download_cwi_samples import download_samples

PROJECT = Path(__file__).resolve().parent
DATA_DIR = PROJECT / "data" / "sgf"
DEFAULT_CONFIG = PROJECT / "configs" / "analysis_local.cfg"

st.set_page_config(page_title="Baduk Insight", page_icon="⚫", layout="wide")
st.title("Baduk Insight")
st.caption("Personal AI Go learning project | Phase 3: RAG chatbot")
st.info("현재 단계: SGF 복기 + KataGo 선택 수 분석 + 로컬 바둑 개념 RAG 학습 챗봇. 개인 학습 기록은 이후 구현 예정입니다.")

available = sorted(DATA_DIR.glob("*.sgf")) if DATA_DIR.exists() else []
with st.sidebar:
    st.header("Load a game")
    st.caption(f"Local SGF files: {len(available)}")
    source = st.radio("Source", ["Local CWI samples", "Upload SGF"])
    raw = None
    name = ""
    if source == "Upload SGF":
        uploaded = st.file_uploader("Choose SGF", type=["sgf"])
        if uploaded is not None:
            raw, name = uploaded.getvalue(), uploaded.name
    else:
        if not available:
            st.warning("아직 로컬 SGF 기보가 없습니다.")
            if st.button("Download CWI games", type="primary"):
                with st.spinner("CWI 기보 다운로드 중..."):
                    good, errors = download_samples()
                for path in good:
                    st.success(f"기보 준비 완료: {path.name}")
                for error in errors:
                    st.error(f"다운로드 실패: {error}")
                if good:
                    st.rerun()
            st.caption("다운로드가 실패하면 Upload SGF를 선택하고 직접 SGF 파일을 업로드하세요.")
        else:
            selected = st.selectbox("Professional game", available, format_func=lambda p: p.name)
            if selected:
                raw, name = selected.read_bytes(), selected.name
    st.markdown("[CWI archive](https://homepages.cwi.nl/~aeb/go/games/games/AlphaGo/)")

    st.divider()
    st.header("KataGo (local)")
    binary = st.text_input("KataGo executable (path or katago)", value="katago")
    model = st.text_input("Neural net model path (.bin.gz)", value="")
    config = st.text_input("Analysis config path", value=str(DEFAULT_CONFIG))
    visits = st.select_slider("Maximum visits", options=[25, 50, 100, 200, 500], value=100)
    st.caption("분석 실행에는 별도로 설치한 KataGo 실행 파일과 신경망 모델이 필요합니다.")

if raw is None:
    st.info("왼쪽 Download CWI games 버튼을 누르거나 Upload SGF에서 기보 파일을 불러오세요.")
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

with st.sidebar:
    st.divider()
    st.header("RAG learning (local)")
    st.caption("Ollama에서 embeddinggemma-2:270m 및 qwen3:4b-instruct 모델을 미리 설치하세요.")
    if st.button("Build / refresh knowledge index"):
        try:
            notes = load_notes()
            with st.spinner("바둑 개념 임베딩 생성 중..."):
                indexed = build_index(notes)
            st.success(f"{indexed}개 학습 문서 색인 완료")
        except (OllamaError, ValueError, RuntimeError, OSError) as exc:
            st.error(f"색인 실패: {exc}")
    try:
        note_count = get_collection().count()
        st.caption(f"현재 검색 색인: {note_count}개 학습 문서")
    except (OSError, RuntimeError, ValueError) as exc:
        st.warning(f"ChromaDB 초기화 실패: {exc}")

digest = hashlib.sha256(raw).hexdigest()
if st.session_state.get("game_digest") != digest:
    st.session_state.game_digest = digest
    st.session_state.move_index = 0
    st.session_state.analysis_result = None
    st.session_state.analysis_key = None
    st.session_state.rag_messages = []
    st.session_state.rag_scene = None
    st.session_state.playing = False
    st.session_state.playback_speed = 2
    st.session_state.last_advance = time.monotonic()

st.subheader(f"{record.black_player} (Black) vs {record.white_player} (White)")
st.caption(f"{record.event} | {record.date} | {record.result} | {name}")
# A fragment refreshes only the board while playback runs; KataGo and RAG
# panels remain still until playback is paused. One timer tick advances one move.
left, right = st.columns([1.45, 1])

@st.fragment(run_every="0.25s")
def show_replay():
    if st.session_state.pop("replay_full_refresh", False):
        st.rerun()
    with left:
        current = st.session_state.move_index
        if st.session_state.playing:
            new_index, new_anchor, still_playing = advance(
                current, record.move_count,
                st.session_state.last_advance,
                time.monotonic(), st.session_state.playback_speed,
            )
            if new_index != current:
                st.session_state.move_index = new_index
                st.session_state.last_advance = new_anchor
            if not still_playing:
                st.session_state.playing = False
                st.rerun()
        current = st.session_state.move_index
        controls = st.columns([1, 1, 1, 1])
        with controls[0]:
            if st.button("⏮ 이전", disabled=current == 0, key="replay_previous"):
                st.session_state.playing = False
                st.session_state.move_index = move_manually(current, record.move_count, -1)
                st.session_state.last_advance = time.monotonic()
                st.rerun()
        with controls[1]:
            if st.button("▶ 재생" if not st.session_state.playing else "⏸ 일시정지",
                         disabled=(not st.session_state.playing and current >= record.move_count),
                         key="replay_toggle"):
                st.session_state.playing = not st.session_state.playing
                st.session_state.last_advance = time.monotonic()
                st.rerun()
        with controls[2]:
            if st.button("⏭ 다음", disabled=current >= record.move_count, key="replay_next"):
                st.session_state.playing = False
                st.session_state.move_index = move_manually(current, record.move_count, 1)
                st.session_state.last_advance = time.monotonic()
                st.rerun()
        with controls[3]:
            speed = st.selectbox(
                "재생 간격", [1, 2, 3], format_func=lambda v: f"{v}초",
                key="playback_speed", help="한 수를 표시한 다음 다음 수까지 기다리는 시간",
            )
            if speed not in (1, 2, 3):
                st.session_state.playback_speed = 2
        # Use a temporary slider key to keep widget state synchronized with timer changes.
        def on_seek():
            st.session_state.playing = False
            st.session_state.move_index = st.session_state.replay_seek
            st.session_state.last_advance = time.monotonic()
            st.session_state.replay_full_refresh = True
        st.session_state.replay_seek = st.session_state.move_index
        st.slider(
            "Move", 0, record.move_count, key="replay_seek", on_change=on_seek,
            help="슬라이더를 움직이면 자동 재생이 멈추고 선택한 수로 이동합니다.",
        )
        current = st.session_state.move_index
        st.caption(
            f"복기: {current} / {record.move_count}수 · "
            + (f"자동 재생 중 ({st.session_state.playback_speed}초/수)" if st.session_state.playing else "일시정지")
        )
        try:
            board, last = replay(record, current)
        except (ValueError, IndexError) as exc:
            st.session_state.playing = False
            st.error(f"Could not replay move: {exc}")
            return
        height = 625 if record.size == 19 else (510 if record.size == 13 else 410)
        components.html(render_board(board, last_move=last), height=height, scrolling=False)

show_replay()
with right:
    turn = st.session_state.move_index
    st.markdown("### Game review")
    st.metric("Current move (paused view)", f"{turn} / {record.move_count}")
    if st.session_state.playing:
        st.info("자동 재생 중에는 오른쪽 분석·챗봇의 수순이 갱신되지 않습니다. 일시정지하면 현재 수로 갱신됩니다.")
    if turn:
        colour, point = record.moves[turn-1]
        who = "Black" if colour == "b" else "White"
        st.write(f"Last played: **{who} {gtp_coord(point, record.size)}**")

    st.divider()
    st.markdown("### KataGo analysis")
    if st.session_state.playing:
        st.caption("분석하려면 일시정지하세요.")
    st.caption("현재 표시된 수가 아닌, 그 수를 두기 **직전의 국면**에서 AI 추천 수를 분석합니다.")
    if turn == 0:
        st.info("첫 수(착점 이전)를 분석하려면 수순을 1로 이동하세요.")
    else:
        lookup = (digest, turn, rules, float(komi), visits, binary, model, config)
        if st.button("Analyze position before this move", type="primary", disabled=st.session_state.playing):
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
    st.markdown("### AI 바둑 학습 챗봇")
    st.caption("선택한 국면과 검색한 바둑 학습 문서를 근거로 한국어로 질문하세요.")
    scene_id = (digest, turn)
    if st.session_state.get("rag_scene") != scene_id:
        st.session_state.rag_scene = scene_id
        st.session_state.rag_messages = []
    for message in st.session_state.rag_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("검색 근거 문서"):
                    for source in message["sources"]:
                        st.caption(f"{source['title']} · knowledge/{source['path']}")
    question = st.chat_input("예: 왜 중앙의 연결이 중요해?", disabled=st.session_state.playing)
    if question:
        history = list(st.session_state.rag_messages)
        st.session_state.rag_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                hits = retrieve(question, top_k=3)
                if not hits:
                    reply = "검색 색인이 비어 있습니다. 왼쪽에서 'Build / refresh knowledge index'를 먼저 실행해 주세요."
                    st.markdown(reply)
                    st.session_state.rag_messages.append({"role": "assistant", "content": reply})
                else:
                    current_analysis = (
                        st.session_state.get("analysis_result")
                        if turn > 0 and st.session_state.get("analysis_key") ==
                        (digest, turn, rules, float(komi), visits, binary, model, config)
                        else None
                    )
                    last_move = gtp_coord(record.moves[turn-1][1], record.size) if turn else "none"
                    scene = {
                        "game": f"{record.black_player} vs {record.white_player}",
                        "turn": turn,
                        "played_move": last_move,
                        "analysis": current_analysis,
                    }
                    prompt = build_messages(question, hits, scene, history)
                    with st.spinner("근거 문서로 답변 생성 중..."):
                        reply = chat(prompt)
                    st.markdown(reply)
                    with st.expander("검색 근거 문서", expanded=True):
                        for source in hits:
                            st.caption(f"{source['title']} · knowledge/{source['path']}")
                    st.session_state.rag_messages.append({
                        "role": "assistant", "content": reply,
                        "sources": [{"title": x["title"], "path": x["path"]} for x in hits],
                    })
            except (OllamaError, RuntimeError, ValueError, OSError) as exc:
                message = f"RAG 답변을 생성하지 못했습니다: {exc}"
                st.error(message)
                # Failed turns are not part of chat history.
                st.session_state.rag_messages.pop()

    st.caption("현재 장면을 변경하면 이 화면의 대화가 새로 시작됩니다. 별도의 장기 학습 기록은 Phase 4 예정입니다.")
    st.caption("프로기사의 실제 의도는 확인할 수 없으며, AI 설명은 학습 참고용입니다.")
