# Baduk Insight — 시스템 구조와 데이터 흐름

[README](../README.md) · [Windows 실행](SETUP_WINDOWS.md) · [개발 기록](DEVELOPMENT_LOG.md)

**기준:** 2026-11-15 · Public GitHub `main`. 이 문서는 코드에 실제 연결된 기능과 선택적으로 보존된 실험 코드를 구분합니다.

## 1. 사용자 흐름과 화면 구조

```text
CWI 오청원 TGZ → data/sgf/go_seigen/ / SGF 업로드 / CWI 직접 URL
                     │
                sgfmill 파싱
                     │
           Streamlit app.py 대시보드
                     │
     ┌───────────────┴─────────────────────┐
     │                                     │
왼쪽 62% · 기보 복기                  오른쪽 38% · KataGo
SVG 바둑판 아래 재생 버튼·슬라이더       선택 수 직전 국면 분석
실제 수(주황)·AI 추천(파랑)           승률·집 차이·추천·변화도
     └────────────────┬────────────────────┘
                      │
                 전체 너비 학습
          knowledge/*.md 16개 원문 카드
                      │
               질문 입력 · 대화
                      │
          src/study_chat.py (학습 노트 검색)
                      │
       Ollama 로컬 qwen3:1.7b (선택 설치)
```

**초기 사이드바는 접혀 있음.** 대국명·대국정보 아래에서 왼쪽 바둑판은 최대 720px 레인에 반응형으로 렌더링되고, 이전·재생·다음 버튼과 슬라이더가 바둑판 바로 아래 배치됩니다. 오른쪽 38% 영역은 KataGo 착수 분석입니다. 메인 제목은 축소된 Baduk Insight 헤더이며, 대국명은 작은 보조 제목입니다. UI는 Noto Sans KR 우선 적용, 아이콘 글꼴은 별도로 유지합니다.

SGF가 없어도 학습 카드 및 로컬 질문 화면은 표시할 수 있습니다. 카드 아래에는 별도 챗봇 제목과 Ollama 모델명 소개 문구를 표시하지 않습니다.

## 2. 구현 모듈

| 파일 | 연결된 역할 |
| --- | --- |
| `app.py` | Streamlit 사이드바, 62:38 바둑판·분석 레이아웃, 보드 아래 재생 조작부, 학습 영역 내 질문창 |
| `src/sgf_service.py` | SGF 기본 메타데이터, 설정 돌·메인 수순, 특정 수까지 재생 |
| `src/game_metadata.py` | SGF PB/PW/DT/EV/PC/RE 기반 대국명·날짜·장소·결과 표시; 없는 데이터와 파일명은 표시하지 않음 |
| `src/board_svg.py` | SVG 9·13·19줄 바둑판, 실제 착수·AI 추천 테두리 |
| `src/playback.py` | 자동 진행 및 수동 이동, 백그라운드 탭에서도 1회에 최대 한 수 |
| `src/go_seigen_source.py` | 오청원 원본 TGZ를 로컬 전용 폴더에 저장, 오청원 포함·재생 가능한 SGF 필터링 |
| `src/cwi_source.py` | 공식 CWI HTTPS 링크 범위 검사, 다운로드 크기·SGF 유효성 확인 |
| `src/katago_client.py` | KataGo JSON 분석 요청, 흑 기준 분석 결과, 상위 후보 |
| `src/local_settings.py` | 개인 PC 전용 엔진·모델·분석 설정 |
| `src/study_guide.py` | 16개 원문 노트의 분야 분류·제목·설명 추출 |
| `src/fast_study.py` | 추가 질문에 연관된 노트 키워드·유사 표현 검색 |
| `src/study_chat.py` | 선택 카드 + 연관 노트 + 최근 대화로 근거 제한 프롬프트 |
| `src/ollama_client.py` | 로컬 Ollama `/api/chat` 스트리밍, 선택형 임베딩 API |
| `src/rag_pipeline.py` | 기존 ChromaDB·EmbeddingGemma **선택 실험** |

## 3. SGF와 CWI 입력 경계

- **오청원 기본 목록:** 원본 TGZ를 PC의 `data/sgf/go_seigen/`에 보관하며, 오청원 기보 중 수순을 재생할 수 있는 SGF만 선택
- **다른 기보:** 직접 SGF 업로드 또는 CWI 개별 URL 열기
- **CWI 원본:** `https://homepages.cwi.nl/~aeb/go/games/games/` 범위의 직접 `.sgf` 링크만 허용
- URL은 HTTPS·호스트·경로·리다이렉트·쿼리 등을 검사하고 최대 2MB를 읽음
- Windows의 신뢰 인증서를 `truststore`로 사용하며 SSL 검증을 끄지 않음
- 파일은 `sgfmill`에서 파싱하고 9·13·19줄 바둑판만 지원
- 대국 상세 정보는 원본 SGF 속성 `PB`·`PW`·`DT`·`EV`·`PC`·`RE`만 사용하고 날짜가 연도까지만 기록된 경우 연도만 표시합니다. `Unknown`·파일명을 대회명이나 대국 날짜로 사용하지 않습니다.
- 외부 기보의 메인 수순을 복기하는 앱으로, 전문 SGF 분기 편집기는 아님
- 개별 CWI SGF URL로 열어 본 기보는 Streamlit 세션 상태에 유지하며, 오청원 TGZ 자동 다운로드는 로컬 `data/sgf/go_seigen/`에만 저장

## 4. 복기와 KataGo 분석

`src/playback.advance`는 **2초당 한 수**를 진행하며, 0.5초 Streamlit 주기 갱신의 작은 지연은 시간 기준을 유지해 누적되지 않도록 합니다. 큰 지연(백그라운드 탭·렌더링 지연)에는 시계를 다시 시작하여 한꺼번에 수순을 건너뛰지 않습니다. 첫 재생은 전체 화면 초기화 뒤 시작 시각을 잡습니다. 바둑판(`st.image` SVG), 이전·재생·다음 버튼·수순 슬라이더와 **오른쪽 KataGo 분석 패널**을 **하나의 Streamlit fragment** 안에 배치했습니다. 일시정지된 이전·다음·슬라이더 이동은 fragment만 갱신하며, 재생·일시정지처럼 주기적 갱신 설정이 달라지는 경우에만 앱 전체를 새로 고칩니다. **슬라이더는 수순별 개별 키로 관리**하여 자동 진행 중 위젯 상태 충돌을 피합니다. 실제 브라우저에서의 재생 간격 정밀도는 별도 확인이 필요합니다.

`src/katago_client.build_query(record, turn - 1, ...)`는 현재 표시한 수 N이 **두어지기 전** 국면을 요청합니다. 실제 수와 AI 1순위 제안을 주황/파랑 테두리로 구별합니다. 반환값의 `rootInfo.winrate`와 `rootInfo.scoreLead`는 `configs/analysis_local.cfg`의 **BLACK 기준** 설정을 전제로 표시합니다.

기본 제안: `~/KataGo/katago.exe`, `~/Downloads/kata1-b10c128-s1141046784-d204142634.txt.gz`, 5회 탐색. 엔진과 모델 파일은 GitHub에 포함되지 않습니다. 동일 국면·동일 설정의 분석은 Streamlit 서버 메모리로 캐시합니다. 요청은 사용자 액션 시 실행되므로 대기 시간이 발생할 수 있습니다.

SGF에 `RU`·`KM`이 없으면 분석에 사용하는 임시 기본값을 실제 대국의 규칙으로 확정할 수 없습니다. 추천 수와 실제 수가 다르다고 **승률 손실이나 악수라고 단정하지 않습니다.**

## 5. 바둑 개념 카드와 로컬 채팅

`knowledge/`의 Markdown 학습 노트 **16개**를 `rag_pipeline.load_notes`로 읽습니다. `study_guide.grouped_study_notes`가 파일명·제목을 분야별로 묶고, 사용자가 카드 하나를 누르면 `note_answer`가 원문 설명을 보여줍니다. **카드 읽기에는 ChromaDB·Ollama가 필요하지 않습니다.**

추가 질문은 학습 영역 컨테이너 안에 렌더링된 `st.chat_input`에서 받으며, 해당 영역 밖의 바둑판을 덮는 전체 화면 고정 입력창은 사용하지 않습니다. `study_chat.build_study_chat_messages`는 선택 카드와 `fast_study.quick_answer`에서 관련성이 확인된 다른 노트(최대 2개)를 프롬프트에 넣고 최근 대화 일부를 포함합니다. 답변은 `ollama_client.chat_stream`으로 **`qwen3:1.7b`**에 전달하여 스트리밍합니다.

Ollama 기본 접속지는 **`http://127.0.0.1:11434`**입니다. 유료 외부 AI API 호출은 없지만 Ollama 설치·모델 다운로드가 필요하고 느릴 수 있습니다. LLM 프롬프트는 제공한 학습 자료 밖의 구체적 사실·실전 승률·프로기사 의도를 추측하지 말도록 제한합니다. **모델이 언제나 이를 준수하거나 정답을 보장하지는 않습니다.** 현재 채팅에 KataGo 현재 국면 데이터가 자동 제공되는 구조는 아닙니다.

## 6. 선택 보존 기능: RAG 색인

기존 학습 실험을 위해 `src/rag_pipeline.py`와 ChromaDB 관리 UI는 유지합니다.

- `embeddinggemma-2:270m` 임베딩을 로컬 Ollama에서 생성
- `data/chroma/`의 선택형 색인, **검색 색인 관리 · 선택 → 검색 자료 동기화**에서만 명시적으로 갱신
- **현재 카드 표시와 추가 질문은 이 색인을 읽지 않음**
- 이전 `build_messages`, `chat` 함수는 연구용 유틸리티로 보존되어 있으나 기본 질문 호출 경로는 `study_chat → chat_stream`

## 7. 로컬 보안과 검증

GitHub는 **Public**이며 `.gitignore`에서 SGF 다운로드, PC별 설정, ChromaDB 파일, 분석 로그와 신경망 가중치 등을 제외합니다. 이미 Git에 커밋된 파일과 과거 기록은 `.gitignore`로 숨겨지지 않으므로 공개 저장소의 커밋 내역도 별도로 점검해야 합니다. 원본 기보는 해당 사이트의 권리·이용 조건을 확인해야 합니다.

`tests/`는 파일 파싱·원격 URL 검증·바둑판 마커·복기·KataGo 요청·학습 카드·질문 프롬프트 등을 테스트하고, 일부 테스트는 가짜 KataGo·Ollama를 사용합니다. **Windows에서의 전체 사용자 인터페이스·외부 HTTPS·실제 엔진/모델 응답은 최신 코드 기준 미검증**입니다. Windows에서는 Git 동기화 스크립트 대신 GitHub 최신 ZIP을 내려받아 실행합니다. 현재 상태와 다음 점검은 [개발 기록](DEVELOPMENT_LOG.md)에 정리합니다.
