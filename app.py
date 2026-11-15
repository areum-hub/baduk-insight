"""Baduk Insight — SGF review, optional KataGo, and fast local study-note chat."""
import hashlib
import json
import time
from html import escape
from pathlib import Path

import streamlit as st
from sgfmill import sgf

from src.cwi_source import ARCHIVE_URL, fetch_cwi_sgf
from src.go_seigen_source import (
    GO_SEIGEN_ARCHIVE_URL, import_go_seigen, import_go_seigen_archive,
    local_go_seigen_games,
)
from src.board_svg import render_board
from src.katago_client import KataGoError, build_query, gtp_coord, run_analysis, top_candidates
from src.local_settings import resolved_settings, save_settings, suggested_paths
from src.sgf_service import load_sgf, replay
from src.playback import advance, move_manually, seek_widget_key, toggle_playback
from src.ollama_client import OllamaError, chat_stream
from src.study_chat import LOCAL_CHAT_MODEL, build_study_chat_messages
from src.rag_pipeline import build_index, get_collection, load_notes
from src.study_guide import grouped_study_notes, note_title, note_answer

PROJECT = Path(__file__).resolve().parent
DATA_DIR = PROJECT / "data" / "sgf"
DEFAULT_CONFIG = PROJECT / "configs" / "analysis_local.cfg"
PLAYBACK_SECONDS = 2  # Fixed playback interval for personal study
LOCAL_KATAGO_SETTINGS = PROJECT / "data" / "local" / "katago_settings.json"


@st.cache_data(max_entries=128, show_spinner=False)
def cached_katago_analysis(query_json: str, binary_path: str, model_path: str, config_path: str) -> dict:
    """Keep previously analyzed positions in memory for the running Streamlit server."""
    return run_analysis(json.loads(query_json), binary_path, model_path, config_path, timeout_seconds=180)


st.set_page_config(page_title="Baduk Insight", page_icon="⚫", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    /* Noto Sans KR gives both Korean copy and English match names a calm UI style.
       If the web font cannot load, use fonts already available on the OS. */
    @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap");
    :root {
        --bi-font: "Noto Sans KR", "Malgun Gothic", "Apple SD Gothic Neo", "Segoe UI", sans-serif;
    }
    /* Typography should never override Streamlit's Material Symbols icons.
       Streamlit stores icon ligatures (e.g. arrow_right) inside span elements;
       applying Noto Sans KR to every span turns them into visible words. */
    html, body, .stApp {
        font-family: var(--bi-font);
    }
    .stApp :is(h1, h2, h3, h4, h5, h6, p, label, small, button, input, textarea, select) {
        font-family: var(--bi-font) !important;
    }
    /* Preserve the icon font explicitly across Streamlit versions. */
    .stApp :is(.material-symbols-rounded, .material-symbols-outlined, .material-icons, [data-testid="stIconMaterial"]) {
        font-family: "Material Symbols Rounded" !important;
        font-feature-settings: "liga";
        -webkit-font-feature-settings: "liga";
    }
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
        font-size: clamp(2rem, 3.3vw, 2.8rem) !important;
        line-height: 1.12 !important;
        letter-spacing: -0.035em !important;
        font-weight: 700 !important;
        color: inherit !important;
    }
    .bi-brand-subtitle {
        margin: .45rem 0 0 !important;
        font-size: clamp(1rem, 1.4vw, 1.17rem) !important;
        line-height: 1.5 !important;
        color: var(--text-color);
        opacity: .74;
        letter-spacing: -.015em;
    }
    .bi-study-title {
        margin: 0 0 .35rem !important;
        font-size: clamp(1.85rem, 2.4vw, 2.3rem) !important;
        line-height: 1.25 !important;
        font-weight: 720;
        letter-spacing: -.03em;
    }
    .bi-study-subtitle {
        margin: 0 0 1.15rem !important;
        font-size: clamp(1.03rem, 1.35vw, 1.15rem) !important;
        line-height: 1.55;
        color: var(--text-color);
        opacity: .75;
    }
    /* Clear hierarchy for the match and KataGo sections. */
    .bi-game-title {
        font-size: clamp(1.15rem, 1.55vw, 1.45rem) !important;
        font-weight: 600 !important;
        line-height: 1.45 !important;
        letter-spacing: -.015em;
        margin: .2rem 0 .25rem !important;
        overflow-wrap: anywhere;
    }
    .bi-analysis-title {
        font-size: clamp(1.75rem, 2.35vw, 2.25rem) !important;
        font-weight: 740 !important;
        line-height: 1.25 !important;
        letter-spacing: -.025em;
        margin: .15rem 0 .6rem !important;
    }
    /* Playback controls and board share the same responsive 720px lane. */
    .st-key-replay_workspace {
        width: 100%;
        max-width: 720px;
        margin-left: auto;
        margin-right: auto;
    }
    .st-key-replay_workspace [data-testid="stButton"] button {
        width: 100%;
    }
    /* Quiet study sidebar. No duplicated logo or decorative header. */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(135, 116, 91, .18);
    }
    section[data-testid="stSidebar"] > div:first-child {
        background: var(--secondary-background-color, #f8f7f5);
    }
    /* Scroll the settings panel instead of clipping the lower sections. */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        overflow-y: auto;
        max-height: 100dvh;
        overscroll-behavior-y: contain;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: .65rem;
        padding-bottom: .85rem;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
    }
    section[data-testid="stSidebar"] h3 {
        margin: 0 0 .4rem !important;
        padding: 0 !important;
        background: none !important;
        border: 0 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: -.02em;
    }
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        line-height: 1.45;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] details {
        border-radius: 10px;
        border: 1px solid rgba(132, 112, 87, .16);
    }
    section[data-testid="stSidebar"] button:not([data-testid="stSidebarCollapseButton"]),
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        border-radius: 10px;
    }
    /* The study composer stays in its own section instead of creating a
       viewport-wide fixed footer over the Go board. Its sticky positioning
       is bounded by the study workspace, not the whole dashboard. */
    .st-key-study_workspace {
        position: relative;
        isolation: isolate;
    }
    .st-key-study_chat_composer {
        position: sticky;
        bottom: .75rem;
        z-index: 5;
        width: min(100%, 720px);
        margin-inline: auto;
        padding: .35rem .65rem;
        border: 1px solid rgba(127, 127, 127, .18);
        border-radius: 16px;
        background: var(--background-color, #fff);
        box-shadow: 0 3px 16px rgba(0, 0, 0, .08);
    }
    @media (max-width: 640px) {
        .st-key-study_chat_composer {
            width: 100%;
            bottom: .25rem;
            padding: .2rem .3rem;
        }
    }
    </style>
    <div class="bi-brand-header">
        <span class="bi-stones" aria-hidden="true">
            <span class="bi-stone bi-stone-black"></span>
            <span class="bi-stone bi-stone-white"></span>
        </span>
        <div>
            <h1 class="bi-brand-title">Baduk Insight</h1>
            <p class="bi-brand-subtitle">프로 바둑 기보 복기 · AI 착수 분석 · 바둑 개념 학습</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Load only the Go Seigen collection for the default review screen.
# Do not mix previously downloaded SGFs or unrelated sample games into this list.
available = local_go_seigen_games(DATA_DIR)
if not available and not st.session_state.get("go_seigen_initial_attempted", False):
    st.session_state.go_seigen_initial_attempted = True
    try:
        with st.spinner("오청원 기보를 원본 아카이브에서 준비하는 중..."):
            import_go_seigen(DATA_DIR / "go_seigen")
        available = local_go_seigen_games(DATA_DIR)
        st.session_state.pop("go_seigen_initial_error", None)
    except (OSError, ValueError, EOFError) as exc:
        st.session_state.go_seigen_initial_error = str(exc)

with st.sidebar:
    with st.container(border=True):
        st.subheader("01 · 오청원 기보 선택")
        st.caption("기본 목록: 오청원(Go Seigen) 대국")
        raw = None
        name = ""
        source = st.radio(
            "기보 선택 방법",
            ["Go Seigen", "Upload SGF"],
            key="source_mode",
            format_func=lambda item: "오청원" if item == "Go Seigen" else "다른 SGF",
            horizontal=True,
            label_visibility="collapsed",
        )
        if source == "Go Seigen":
            if not available:
                st.warning("오청원 기보를 아직 불러오지 못했습니다.")
                if st.session_state.get("go_seigen_initial_error"):
                    st.caption("자동 다운로드 오류: " + st.session_state["go_seigen_initial_error"])
                if st.button("CWI 원본에서 다시 가져오기", key="retry_go_seigen", use_container_width=True):
                    try:
                        with st.spinner("오청원 기보를 내려받는 중..."):
                            imported = import_go_seigen(DATA_DIR / "go_seigen")
                        st.session_state.pop("go_seigen_initial_error", None)
                        st.success(f"오청원 기보 {imported}개를 저장했습니다.")
                        st.rerun()
                    except (OSError, ValueError, EOFError) as exc:
                        st.error(f"다운로드 실패: {exc}")
                archive = st.file_uploader(
                    "보유한 go_seigen.tgz 파일 가져오기",
                    type=["tgz", "gz"],
                    key="go_seigen_tgz_upload",
                )
                if archive is not None and st.button("TGZ에서 오청원 기보 등록", key="import_go_seigen_tgz"):
                    try:
                        imported = import_go_seigen_archive(
                            archive.getvalue(), DATA_DIR / "go_seigen"
                        )
                        st.session_state.pop("go_seigen_initial_error", None)
                        st.success(f"오청원 기보 {imported}개를 등록했습니다.")
                        st.rerun()
                    except (OSError, ValueError, EOFError) as exc:
                        st.error(f"기보 등록 실패: {exc}")
            else:
                st.caption(f"오청원 대국 {len(available)}개 · 첫 대국 자동 선택")
                selected = st.selectbox(
                    "복기할 오청원 대국",
                    available,
                    format_func=lambda path: path.stem,
                    key="go_seigen_game",
                )
                if selected:
                    raw, name = selected.read_bytes(), selected.name
        else:
            st.link_button("CWI 기보 아카이브", ARCHIVE_URL, use_container_width=True)
            import_mode = st.radio(
                "불러오는 방법",
                ["CWI 원본에서 바로 열기", "내 컴퓨터 파일 업로드"],
                key="sgf_import_mode",
            )
            if import_mode == "CWI 원본에서 바로 열기":
                cwi_url = st.text_input(
                    "SGF 원본 URL",
                    placeholder="https://homepages.cwi.nl/~aeb/go/games/games/.../game.sgf",
                    key="cwi_original_url",
                ).strip()
                if st.button("이 기보로 복기 시작", key="cwi_open_game", disabled=not cwi_url):
                    try:
                        fetched_raw, fetched_name = fetch_cwi_sgf(cwi_url)
                        st.session_state["cwi_loaded"] = {
                            "url": cwi_url, "raw": fetched_raw, "name": fetched_name
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

    analysis_sidebar_card = st.container(border=True)
    with analysis_sidebar_card:
        st.subheader("02 · AI 착수 분석")

        try:
            katago_preferences = resolved_settings(PROJECT, LOCAL_KATAGO_SETTINGS)
        except ValueError as exc:
            st.warning(str(exc))
            katago_preferences = suggested_paths(PROJECT)
        binary = katago_preferences["binary"]
        model = katago_preferences["model"]
        config = katago_preferences["config"]
        visits = katago_preferences["visits"]
        if Path(binary).is_file() and Path(model).is_file():
            st.caption("KataGo 실행 파일 및 모델 경로 확인됨")
        else:
            st.caption("KataGo 설치 파일이나 모델을 확인해 주세요.")
        with st.expander("엔진 설정 및 분석 강도", expanded=False):
            binary = st.text_input("KataGo 실행 파일", value=binary)
            model = st.text_input("신경망 모델 파일", value=model)
            config = st.text_input("분석 설정 파일", value=config)
            visits = st.select_slider(
                "AI 탐색 횟수", options=[5, 10, 25, 50, 100],
                value=visits if visits in (5, 10, 25, 50, 100) else 5,
                help="수치가 작을수록 분석이 빠르지만 결과가 덜 안정적일 수 있습니다.",
            )
            if st.button("이 PC에 분석 설정 저장", key="save_katago"):
                try:
                    save_settings(LOCAL_KATAGO_SETTINGS, binary, model, config, visits)
                    st.success("설정이 PC에 저장되었습니다.")
                except (OSError, ValueError) as exc:
                    st.error(f"설정 저장 실패: {exc}")

with st.sidebar:
    with st.container(border=True):
        st.subheader("03 · 학습 자료")
        try:
            source_notes = load_notes()
            source_count = len(source_notes)
            st.caption(f"바둑 개념 노트 {source_count}개")
            with st.expander("검색 색인 관리 · 선택", expanded=False):
                # Streamlit executes collapsed expanders on every app rerun.
                # Chroma startup can delay the study-card's selection highlight,
                # so access the vector database only on an explicit user action.
                if st.button("현재 색인 확인", key="check_rag_index", use_container_width=True):
                    try:
                        st.session_state["rag_index_count"] = get_collection().count()
                    except (OSError, RuntimeError, ValueError) as exc:
                        st.error(f"검색 색인을 확인하지 못했습니다: {exc}")
                if "rag_index_count" in st.session_state:
                    st.caption(
                        f"기존 RAG 실습 색인 {st.session_state['rag_index_count']}개"
                        f" / 원본 노트 {source_count}개"
                    )
                if st.button("검색 자료 동기화", key="refresh_knowledge", use_container_width=True):
                    try:
                        with st.spinner("검색 색인을 갱신하는 중..."):
                            indexed = build_index(source_notes)
                        st.session_state["rag_index_count"] = indexed
                        st.success(f"{indexed}개 문서 등록 완료")
                        st.rerun()
                    except (OllamaError, ValueError, RuntimeError, OSError) as exc:
                        st.error(f"색인 갱신 실패: {exc}")
        except (OSError, RuntimeError, ValueError) as exc:
            st.error(f"학습 자료를 읽지 못했습니다: {exc}")


def select_study_lesson(path: str) -> None:
    """Update the active card before Streamlit draws the next UI frame."""
    st.session_state["selected_lesson"] = path


def show_study_guide():
    st.markdown(
        '<h2 class="bi-study-title">바둑 개념 학습</h2>'
        '<p class="bi-study-subtitle">분야를 선택하고 학습 카드를 눌러 설명을 읽어보세요.</p>',
        unsafe_allow_html=True,
    )
    try:
        study_groups = grouped_study_notes(load_notes())
        if not study_groups:
            st.info("표시할 바둑 학습 노트가 없습니다.")
            return
        selected_category = st.selectbox(
            "학습 분야", list(study_groups),
            key="study_category", label_visibility="collapsed",
        )
        lessons = study_groups[selected_category]
        st.caption(f"{selected_category} · {len(lessons)}개 주제")
        tiles = st.columns(2)
        for i, lesson in enumerate(lessons):
            with tiles[i % 2]:
                st.button(
                    note_title(lesson),
                    key="lesson_card_" + lesson["path"],
                    use_container_width=True,
                    type="primary" if st.session_state.get("selected_lesson") == lesson["path"] else "secondary",
                    on_click=select_study_lesson,
                    args=(lesson["path"],),
                )
        selected_note = next(
            (n for n in lessons if n["path"] == st.session_state.get("selected_lesson")),
            None,
        )
        if selected_note is not None:
            with st.container(border=True):
                st.markdown(f"#### {note_title(selected_note)}")
                st.markdown(note_answer(selected_note))
    except (ValueError, OSError) as exc:
        st.error(f"바둑 학습 노트를 불러오지 못했습니다: {exc}")
    history = st.session_state.setdefault("study_chat_messages", [])
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # Chat input inside a container renders inline. Sticky CSS keeps it
    # convenient within the study section but never floats over the board.
    with st.container(key="study_chat_composer"):
        question = st.chat_input(
            "학습한 개념에서 궁금한 점을 질문하세요...",
            key="local_study_chat",
        )
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        selected_note = next(
            (note for note in load_notes()
             if note["path"] == st.session_state.get("selected_lesson")),
            None,
        )
        messages = build_study_chat_messages(
            question, load_notes(), selected_note, history,
        )
        history.append({"role": "user", "content": question})
        with st.chat_message("assistant"):
            try:
                with st.spinner("로컬 AI가 답변을 준비하고 있습니다..."):
                    answer = st.write_stream(chat_stream(messages, model=LOCAL_CHAT_MODEL))
                history.append({"role": "assistant", "content": answer})
            except OllamaError as exc:
                st.warning(
                    "로컬 Ollama 연결 또는 모델 로딩에 실패했습니다. "
                    "PowerShell에서 ollama pull qwen3:1.7b 를 실행하고 "
                    "Ollama가 켜져 있는지 확인해 주세요."
                )
                st.caption(str(exc))


if raw is None:
    st.info("기보를 선택하지 않아도 아래 바둑 개념 학습 자료를 읽을 수 있습니다.")
    with st.container(key="study_workspace"):
        show_study_guide()
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

with analysis_sidebar_card:
    # Rules and komi affect KataGo estimates, but need not clutter SGF study UI.
    with st.expander("대국 규칙 · 덤 (필요할 때만)", expanded=False):
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
            st.caption("규칙 정보가 없는 기보이므로 중국식은 임시 분석 기준입니다.")
        else:
            st.caption(f"기보에 기록된 규칙: {recorded_rules}")
        if recorded_komi:
            st.caption(f"기보에 기록된 덤: {recorded_komi}집")
        else:
            st.caption("기보에 덤 기록이 없어 임시 기본값을 사용합니다.")



digest = hashlib.sha256(raw).hexdigest()
if st.session_state.get("game_digest") != digest:
    st.session_state.game_digest = digest
    st.session_state.move_index = 0
    st.session_state.analysis_result = None
    st.session_state.analysis_key = None
    st.session_state.playing = False
    st.session_state.last_advance = time.monotonic()

# Keep both panes aligned: board + controls on the left, KataGo on the right.
# The replay timer is active only while playing, so paused study clicks do
# not trigger unnecessary fragment refreshes.
st.markdown(
    f'<h2 class="bi-game-title">{escape(record.black_player)} (Black) '
    f'vs {escape(record.white_player)} (White)</h2>',
    unsafe_allow_html=True,
)
st.caption(f"{record.event} | {record.date} | {record.result} | {name}")
left, right = st.columns([62, 38], gap="large")

@st.fragment(run_every="0.5s" if st.session_state.playing else None)
def show_replay():
    if st.session_state.pop("replay_full_refresh", False):
        # Refresh the entire page, not only the playback fragment. The KataGo
        # button lives in the right column outside this fragment and would
        # otherwise stay disabled after clicking Pause.
        st.rerun(scope="app")

    def on_toggle_playback():
        # A widget callback runs before the next fragment evaluation.
        # Reset the 2-second clock and request a full rerun so the AI panel
        # immediately sees the new playing state and current move index.
        playing, anchor = toggle_playback(
            st.session_state.playing,
            st.session_state.move_index,
            record.move_count,
            time.monotonic(),
        )
        st.session_state.playing = playing
        st.session_state.last_advance = anchor
        st.session_state.replay_full_refresh = True

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
            st.rerun(scope="app")
    current = st.session_state.move_index
    try:
        board, last = replay(record, current)
    except (ValueError, IndexError) as exc:
        st.session_state.playing = False
        st.error(f"Could not replay move: {exc}")
        return

    current_key = (digest, current, rules, float(komi), visits, binary, model, config)
    ai_point = None
    if (
        current > 0
        and st.session_state.get("analysis_key") == current_key
        and st.session_state.get("analysis_result")
    ):
        candidates = top_candidates(st.session_state["analysis_result"])
        ai_point = candidates[0].get("move") if candidates else None

    # Streamlit HTML renders inline, without an oversized iframe. This keeps
    # the replay controls directly below a responsive 9/13/19-line board.
    st.html(render_board(board, last_move=last, ai_suggestion=ai_point))
    if ai_point:
        st.caption("🟠 주황 테두리: 실제 착수   ·   🔵 파란 테두리: AI 추천 위치")

    controls = st.columns(3)
    with controls[0]:
        if st.button("⏮ 이전", disabled=current == 0, key="replay_previous", use_container_width=True):
            st.session_state.playing = False
            st.session_state.move_index = move_manually(current, record.move_count, -1)
            st.session_state.last_advance = time.monotonic()
            st.rerun(scope="app")
    with controls[1]:
        st.button(
            "▶ 재생" if not st.session_state.playing else "⏸ 일시정지",
            disabled=(not st.session_state.playing and current >= record.move_count),
            key="replay_toggle",
            on_click=on_toggle_playback,
            use_container_width=True,
        )
    with controls[2]:
        if st.button("⏭ 다음", disabled=current >= record.move_count, key="replay_next", use_container_width=True):
            st.session_state.playing = False
            st.session_state.move_index = move_manually(current, record.move_count, 1)
            st.session_state.last_advance = time.monotonic()
            st.rerun(scope="app")

    # A key per position avoids rewriting an already rendered slider widget.
    seek_key = seek_widget_key(digest, current)

    def on_seek():
        st.session_state.playing = False
        st.session_state.move_index = int(st.session_state[seek_key])
        st.session_state.last_advance = time.monotonic()
        st.session_state.replay_full_refresh = True

    st.slider(
        "Move", min_value=0, max_value=record.move_count,
        value=current, key=seek_key, on_change=on_seek,
        help="슬라이더를 움직이면 자동 재생이 멈추고 선택한 수로 이동합니다.",
    )
    st.caption(
        f"복기: {current} / {record.move_count}수 · "
        + (f"자동 재생 중 ({PLAYBACK_SECONDS}초/수)" if st.session_state.playing else "일시정지")
    )

with left:
    with st.container(key="replay_workspace"):
        show_replay()
with right:
    turn = st.session_state.move_index
    st.markdown('<h2 class="bi-analysis-title">AI 착수 분석</h2>', unsafe_allow_html=True)
    if st.session_state.playing:
        st.caption("자동 재생 중 · 일시정지 후 현재 수순 분석 가능")
    else:
        st.caption(f"선택한 장면: {turn} / {record.move_count}수")
    st.caption("현재 수를 두기 **직전**에 AI가 추천한 위치를 분석합니다.")
    if turn > 0:
        lookup = (digest, turn, rules, float(komi), visits, binary, model, config)
        if st.button("이 장면 AI 분석하기", type="primary", disabled=st.session_state.playing):
            try:
                query = build_query(record, turn - 1, rules, float(komi), visits)
                # Query IDs are normally random; replace with a stable key so
                # identical positions reuse the same analysis result.
                position = {key: value for key, value in query.items() if key != "id"}
                key_json = json.dumps(position, ensure_ascii=False, sort_keys=True)
                query["id"] = hashlib.sha256(key_json.encode("utf-8")).hexdigest()[:24]
                query_json = json.dumps(query, ensure_ascii=False, sort_keys=True)
                with st.spinner("AI가 현재 장면을 분석하고 있습니다..."):
                    result = cached_katago_analysis(query_json, binary, model, config)
                st.session_state.analysis_key = lookup
                st.session_state.analysis_result = result
                # Immediately render the blue AI suggestion on the board.
                st.rerun(scope="app")
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
                st.caption(f"분석에 사용한 AI 탐색 횟수: {root_info.get('visits', '확인 불가')}회")
                suggestions = top_candidates(analysis)
                if suggestions:
                    actual = gtp_coord(record.moves[turn - 1][1], record.size)
                    best = str(suggestions[0].get("move", "확인 불가"))
                    col_actual, col_ai = st.columns(2)
                    with col_actual:
                        st.metric("🟠 실제 착수", actual)
                    with col_ai:
                        st.metric("🔵 AI 추천", best)
                    if actual.upper() == best.upper():
                        st.caption("실제 착수와 AI의 1순위 추천이 같습니다.")
                    else:
                        st.caption("두 수가 다르지만, 곧바로 실수라는 뜻은 아닙니다.")
                    with st.expander("다른 후보 수와 예상 진행 확인", expanded=False):
                        st.caption("예상 진행은 실제 기보가 아닌 KataGo가 계산한 가상 수순입니다.")
                        for i, candidate in enumerate(suggestions, start=1):
                            move = candidate.get("move", "확인 불가")
                            st.markdown(f"**{i}순위 후보 · {move}**")
                            pv = (candidate.get("pv") or [])[:6]
                            if pv:
                                st.caption("예상 진행: " + " → ".join(str(x) for x in pv))
                            st.caption(f"AI가 후보를 검토한 횟수: {candidate.get('visits', '확인 불가')}회")
                    st.caption("추천은 착수 전 기준입니다. 승률 손실은 전후 분석이 필요합니다.")
                else:
                    st.warning("후보 수가 반환되지 않았습니다.")

# Study cards and local chat follow the 62/38 review workspace.
st.divider()
with st.container(key="study_workspace"):
    show_study_guide()
