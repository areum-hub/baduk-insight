"""Baduk Insight — SGF, KataGo, and local RAG study chatbot (Phase 3)."""
import hashlib
import json
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from sgfmill import sgf

from src.cwi_source import ARCHIVE_URL, CWI_CHOICES, fetch_cwi_sgf
from src.board_svg import render_board
from src.katago_client import KataGoError, build_query, gtp_coord, run_analysis, top_candidates
from src.local_settings import resolved_settings, save_settings, suggested_paths
from src.sgf_service import load_sgf, replay
from src.playback import advance, move_manually
from src.ollama_client import OllamaError, chat
from src.rag_pipeline import build_index, build_messages, get_collection, load_notes, retrieve

PROJECT = Path(__file__).resolve().parent
DATA_DIR = PROJECT / "data" / "sgf"
DEFAULT_CONFIG = PROJECT / "configs" / "analysis_local.cfg"
PLAYBACK_SECONDS = 2  # Fixed playback interval for personal study
LOCAL_KATAGO_SETTINGS = PROJECT / "data" / "local" / "katago_settings.json"


@st.cache_data(max_entries=128, show_spinner=False)
def cached_katago_analysis(query_json: str, binary_path: str, model_path: str, config_path: str) -> dict:
    """Keep previously analyzed positions in memory for the running Streamlit server."""
    return run_analysis(json.loads(query_json), binary_path, model_path, config_path, timeout_seconds=180)


st.set_page_config(page_title="Baduk Insight", page_icon="⚫", layout="wide")
st.markdown(
    """
    <style>
    .bi-brand-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 4px 0 20px;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(127, 127, 127, 0.22);
    }
    .bi-stones {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        flex-shrink: 0;
    }
    .bi-stone {
        width: 21px;
        height: 21px;
        border-radius: 50%;
        display: inline-block;
        box-sizing: border-box;
    }
    .bi-stone-black {
        background: #202126;
        box-shadow: inset -3px -4px 4px rgba(0, 0, 0, 0.25),
                    0 1px 3px rgba(0, 0, 0, 0.16);
    }
    .bi-stone-white {
        background: #f8f8f6;
        border: 1px solid #9b9b9b;
        box-shadow: inset -3px -3px 4px rgba(0, 0, 0, 0.08),
                    0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .bi-brand-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: clamp(1.75rem, 3vw, 2.25rem) !important;
        line-height: 1.15 !important;
        letter-spacing: -0.035em !important;
        font-weight: 700 !important;
        color: inherit !important;
    }
    </style>
    <div class="bi-brand-header">
        <span class="bi-stones" aria-hidden="true">
            <span class="bi-stone bi-stone-black"></span>
            <span class="bi-stone bi-stone-white"></span>
        </span>
        <h1 class="bi-brand-title">Baduk Insight</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

available = sorted(DATA_DIR.glob("*.sgf")) if DATA_DIR.exists() else []
with st.sidebar:
    st.header("기보 불러오기")
    source = st.radio(
        "기보 선택 방법",
        ["Local CWI samples", "Upload SGF"],
        key="source_mode",
        format_func=lambda item: "내 기보에서 선택" if item == "Local CWI samples" else "SGF 업로드",
    )
    raw = None
    name = ""
    if source == "Upload SGF":
        st.markdown("**CWI 원본 기보 연결**")
        st.caption("CWI 원본을 앱에서 바로 열거나, 내 컴퓨터의 SGF 파일을 업로드하세요.")
        st.link_button(
            "CWI 전체 기보 목록 보기", ARCHIVE_URL,
            use_container_width=True,
        )
        import_mode = st.radio(
            "불러오는 방법",
            ["CWI 원본에서 바로 열기", "내 컴퓨터 파일 업로드"],
            key="sgf_import_mode",
        )
        if import_mode == "CWI 원본에서 바로 열기":
            selection = st.selectbox(
                "CWI 원본 기보",
                ["직접 SGF 주소 입력", *CWI_CHOICES],
                key="cwi_game_selection",
                help="원본 사이트의 다른 대국도 SGF 파일 주소로 열 수 있습니다.",
            )
            if selection == "직접 SGF 주소 입력":
                cwi_url = st.text_input(
                    "SGF 원본 URL",
                    placeholder="https://homepages.cwi.nl/~aeb/go/games/games/.../game.sgf",
                    key="cwi_original_url",
                ).strip()
            else:
                cwi_url = CWI_CHOICES[selection]
                st.caption("선택한 CWI SGF 원본 파일을 직접 불러옵니다.")
            if st.button("이 기보로 복기 시작", key="cwi_open_game", disabled=not cwi_url):
                try:
                    fetched_raw, fetched_name = fetch_cwi_sgf(cwi_url)
                    st.session_state["cwi_loaded"] = {
                        "url": cwi_url,
                        "raw": fetched_raw,
                        "name": fetched_name,
                    }
                    st.session_state.pop("cwi_load_error", None)
                except ValueError as exc:
                    st.session_state["cwi_loaded"] = None
                    st.session_state["cwi_load_error"] = str(exc)
            if st.session_state.get("cwi_load_error"):
                st.error(st.session_state["cwi_load_error"])
            loaded = st.session_state.get("cwi_loaded")
            if loaded and loaded["url"] == cwi_url:
                raw, name = loaded["raw"], loaded["name"]
                st.success(f"복기 중: {name}")
        else:
            uploaded = st.file_uploader("SGF 파일 선택", type=["sgf"])
            if uploaded is not None:
                raw, name = uploaded.getvalue(), uploaded.name
    elif available:
        selected = st.selectbox("복기할 대국", available, format_func=lambda p: p.name)
        if selected:
            raw, name = selected.read_bytes(), selected.name
    else:
        st.info("PC에 저장된 기보가 없습니다. 'SGF 업로드'에서 CWI 원본 기보를 받아 불러오세요.")

    st.divider()
    st.header("KataGo (local)")
    try:
        katago_preferences = resolved_settings(PROJECT, LOCAL_KATAGO_SETTINGS)
    except ValueError as exc:
        st.warning(str(exc))
        katago_preferences = suggested_paths(PROJECT)
    binary = st.text_input("KataGo executable (path or katago)", value=katago_preferences["binary"])
    model = st.text_input("Neural net model path (.bin.gz or .txt.gz)", value=katago_preferences["model"])
    config = st.text_input("Analysis config path", value=katago_preferences["config"])
    visits = st.select_slider(
        "AI 탐색 횟수", options=[5, 10, 25, 50, 100],
        help="KataGo가 다음 수를 판단하기 위해 탐색하는 횟수입니다. 횟수가 적으면 빠르지만 분석의 신뢰도가 낮아질 수 있습니다." ,
        value=katago_preferences["visits"] if katago_preferences["visits"] in (5, 10, 25, 50, 100) else 10,
    )
    if st.button("KataGo 설정 저장", help="경로와 AI 탐색 횟수를 이 컴퓨터에만 저장합니다."):
        try:
            save_settings(LOCAL_KATAGO_SETTINGS, binary, model, config, visits)
            st.success("설정을 이 PC에 저장했습니다. 다음 실행에도 유지됩니다.")
        except (OSError, ValueError) as exc:
            st.error(f"설정 저장 실패: {exc}")
    if not Path(model).is_file():
        st.caption("경량 모델을 Downloads 폴더에 놓으면 기본 경로에서 자동 인식합니다.")
    st.caption("AI 탐색 횟수는 웹사이트 방문자 수와 무관합니다. CPU에서는 5~10회로 먼저 테스트하세요.")

if raw is None:
    st.info("왼쪽에서 CWI 원본 기보를 선택하거나 SGF 파일을 업로드해 주세요.")
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
    st.divider()
    # Rules and komi affect KataGo estimates, but need not clutter SGF study UI.
    with st.expander("AI 계산 기준 · 상세 설정", expanded=False):
        st.caption("승률과 예상 집 차이를 계산할 때 사용하는 설정입니다. 기보 재생에는 영향을 주지 않습니다.")
        rule_labels = {
            "chinese": "중국식 (돌과 집을 함께 계산)",
            "japanese": "일본식 (집을 중심으로 계산)",
        }
        rules = st.selectbox(
            "계산 규칙",
            options=["chinese", "japanese"],
            index=0 if suggested_rules == "chinese" else 1,
            format_func=lambda key: rule_labels[key],
            help="원본 대국 규칙과 일치시켜야 분석 수치가 정확해집니다.",
        )
        komi = st.number_input(
            "백의 덤 (집)",
            min_value=-20.0, max_value=30.0,
            value=suggested_komi, step=0.5,
            help="먼저 두는 흑의 이점을 보정하기 위해 백에게 주는 점수입니다.",
        )
        recorded_rules = sgf_property("RU", "")
        recorded_komi = sgf_property("KM", "")
        if not recorded_rules:
            st.warning(
                "원본 기보에는 규칙이 기록되지 않았습니다. 현재 중국식은 임시 기본값이며 "
                "실제 대국 규칙과 다를 수 있습니다.",
                icon="⚠️",
            )
        else:
            st.caption(f"기보에 기록된 규칙: {recorded_rules}")
        if recorded_komi:
            st.caption(f"기보에 기록된 덤: {recorded_komi}집")
        else:
            st.caption("기보에 덤 기록이 없어 임시 기본값을 사용합니다.")
    rule_name = "중국식" if rules == "chinese" else "일본식"
    note = " · 기보 규칙 미확인" if not sgf_rules else ""
    st.caption(f"AI 계산: {rule_name} · 백 덤 {komi:g}집{note}")

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
    current = st.session_state.move_index
    if st.session_state.playing:
        new_index, new_anchor, still_playing = advance(
            current, record.move_count,
            st.session_state.last_advance,
            time.monotonic(), PLAYBACK_SECONDS,
        )
        if new_index != current:
            st.session_state.move_index = new_index
            st.session_state.last_advance = new_anchor
        if not still_playing:
            st.session_state.playing = False
            st.rerun()
    current = st.session_state.move_index
    controls = st.columns(3)
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
        + (f"자동 재생 중 ({PLAYBACK_SECONDS}초/수)" if st.session_state.playing else "일시정지")
    )
    try:
        board, last = replay(record, current)
    except (ValueError, IndexError) as exc:
        st.session_state.playing = False
        st.error(f"Could not replay move: {exc}")
        return
    height = 625 if record.size == 19 else (510 if record.size == 13 else 410)
    current_key = (
        digest, current, rules, float(komi), visits, binary, model, config
    )
    ai_point = None
    if (
        current > 0
        and st.session_state.get("analysis_key") == current_key
        and st.session_state.get("analysis_result")
    ):
        candidates = top_candidates(st.session_state["analysis_result"])
        ai_point = candidates[0].get("move") if candidates else None
    components.html(
        render_board(board, last_move=last, ai_suggestion=ai_point),
        height=height,
        scrolling=False,
    )
    if ai_point:
        st.caption("🟠 주황 테두리: 실제 착수   ·   🔵 파란 테두리: AI 추천 위치")

with left:
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
    st.markdown("### AI 착수 분석 · KataGo")
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
                # Query IDs are normally random; replace with a stable key so
                # identical positions reuse the same analysis result.
                position = {key: value for key, value in query.items() if key != "id"}
                key_json = json.dumps(position, ensure_ascii=False, sort_keys=True)
                query["id"] = hashlib.sha256(key_json.encode("utf-8")).hexdigest()[:24]
                query_json = json.dumps(query, ensure_ascii=False, sort_keys=True)
                with st.spinner("KataGo 분석 중... (같은 국면은 캐시에서 재사용)"):
                    result = cached_katago_analysis(query_json, binary, model, config)
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
                st.caption(f"AI 탐색 횟수: {root_info.get('visits', '확인 불가')}회 · 분석 기준: {analysis.get('turnNumber', '확인 불가')}수 이후")
                suggestions = top_candidates(analysis)
                if suggestions:
                    st.markdown("**AI 추천 후보 수 (최대 3개)**")
                    for candidate in suggestions:
                        st.write(f"{int(candidate.get('order', 0))+1}. **{candidate.get('move', '?')}** · AI 탐색 {candidate.get('visits', '?')}회")
                        if candidate.get("pv"):
                            st.caption("변화도: " + " → ".join(candidate["pv"][:10]))
                    actual = gtp_coord(record.moves[turn-1][1], record.size)
                    best = str(suggestions[0].get("move", "알 수 없음"))
                    st.markdown("#### 실제 착수와 AI 추천 비교")
                    played_col, ai_col = st.columns(2)
                    with played_col:
                        st.markdown("🟠 **프로기사의 실제 착수**")
                        st.metric("실제 놓은 위치", actual)
                    with ai_col:
                        st.markdown("🔵 **KataGo가 추천하는 착수**")
                        st.metric("AI 추천 위치", best)
                    if actual.upper() == best.upper():
                        st.success("실제 착수와 AI의 첫 번째 추천이 일치합니다.")
                    else:
                        st.caption(
                            "서로 다른 위치를 제안했습니다. 파란 원은 바둑판에 표시되는 "
                            "AI 추천 위치입니다. 위치가 다르다고 곧바로 실수라는 뜻은 아닙니다."
                        )
                    st.caption(
                        "이 추천은 실제 수를 두기 전 국면에서 계산했습니다. "
                        "승률 손실을 알려면 착수 후 분석을 추가로 비교해야 합니다."
                    )
                else:
                    st.warning("후보 수가 반환되지 않았습니다.")
                st.caption("이 분석은 해당 수를 평가하기 *전*의 후보 비교입니다. 실수 여부나 승률 손실을 판단하려면 착수 이후 국면도 별도로 비교해야 합니다.")

    st.divider()
    st.markdown("### 바둑 AI에게 물어보기")
    current_move_label = (
        f"{turn}수 · {gtp_coord(record.moves[turn-1][1], record.size)}"
        if turn else "대국 시작 전"
    )
    st.caption(f"현재 복기 장면: {current_move_label}")
    scene_id = (digest, turn)
    if st.session_state.get("rag_scene") != scene_id:
        st.session_state.rag_scene = scene_id
        st.session_state.rag_messages = []

    # One-click starter questions are visible when the conversation is empty.
    starter_question = None
    if not st.session_state.rag_messages:
        st.markdown("**어떤 점이 궁금하세요?**")
        st.caption("아래 질문을 선택하거나 직접 입력해 보세요.")
        if st.button("이 수에서 중요한 바둑 개념은?", key="study_starter_1", use_container_width=True):
            starter_question = "현재 국면을 공부할 때 알아두면 좋은 바둑 개념을 설명해줘."
        if st.button("돌의 연결은 왜 중요할까?", key="study_starter_2", use_container_width=True):
            starter_question = "돌의 연결이 중요한 이유를 초보자도 이해하기 쉽게 설명해줘."
        if st.button("축과 장문은 어떻게 다를까?", key="study_starter_3", use_container_width=True):
            starter_question = "축과 장문의 차이를 쉽게 설명해줘."
    for message in st.session_state.rag_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("검색 근거 문서"):
                    for source in message["sources"]:
                        st.caption(f"{source['title']} · knowledge/{source['path']}")
    typed_question = st.chat_input(
        "바둑에서 궁금한 점을 입력하세요...",
        disabled=st.session_state.playing,
        key="study_chat_input",
    )
    question = starter_question or typed_question
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

    with st.expander("AI 설명에 대해 알아두기"):
        st.caption(
            "답변은 검색된 바둑 학습 노트를 근거로 작성됩니다. "
            "KataGo 분석을 실행하지 않았다면 실제 착수의 정확한 승률이나 우열을 판단하지 않습니다."
        )
