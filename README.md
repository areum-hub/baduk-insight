# Baduk Insight

**KataGo와 로컬 AI를 활용한 프로 바둑 기보 복기·개념 학습 대시보드**

Baduk Insight는 CWI에 공개된 **오청원(Go Seigen) 프로 대국 SGF**를 로컬로 불러와 수순을 복기하고, **KataGo**로 착수 직전 국면을 분석하며, **16개 바둑 개념 노트와 Ollama**로 공부하는 Python·Streamlit 개인 프로젝트입니다. Windows PC에서 실행하는 로컬 웹 앱이며 현재 공개 웹서비스로 배포하지 않습니다.

## 주요 기능

| 기능 | 현재 구현 |
| --- | --- |
| 오청원 기보 선택 | CWI의 `go_seigen.tgz`를 PC에 다운로드하고, 오청원 대국자 표기 및 메인 수순 재생 검사를 통과한 기보를 기본 목록에 표시 |
| 기타 SGF | PC SGF 파일 업로드 또는 CWI 공식 HTTPS 단일 SGF URL 열기 |
| 바둑판 복기 | 9·13·19줄 SVG, 이전·재생·일시정지·다음, 수순 슬라이더, **2초당 한 수** |
| KataGo 착수 분석 | 선택한 수를 두기 직전 국면의 **흑 승률·흑 기준 예상 집 차이·추천 착수·후보 수순** |
| 실제 수와 AI 추천 | 바둑판에서 실제 착수 **주황색**, AI 추천 위치 **파란색** 테두리 표시 |
| 바둑 개념 학습 | Markdown 학습 노트 **16개**를 분야별로 탐색, 선택 카드 강조 및 원문 설명 |
| 로컬 질문 | Ollama의 `qwen3:1.7b`가 관련 바둑 개념 노트를 참고해 답변 |
| RAG 실험 | ChromaDB 및 `embeddinggemma-2:270m`의 **선택형 색인 관리** (기본 학습 카드·질문에 불필요) |

AI 분석은 프로기사의 실제 의도나 착수의 절대적 우열을 증명하지 않습니다. 로컬 학습 챗봇에는 **현재 KataGo 국면 데이터가 자동 제공되지 않으며**, 바둑 개념 설명에 사용합니다.

## 대시보드 배치

```text
Baduk Insight
대국명 · 대회 · 날짜 · 결과

┌─────────────────────────────┬───────────────────┐
│ 바둑판 복기 62%             │ AI 착수 분석 38%  │
│                             │                   │
│ 반응형 SVG 바둑판           │ 현재 장면         │
│ (Streamlit st.image)        │ KataGo 분석 버튼  │
│                             │ 흑 승률·집 차이    │
│ [이전] [재생/일시정지] [다음]│ AI 추천·후보 수순  │
│ [수순 슬라이더]             │                   │
└─────────────────────────────┴───────────────────┘

바둑 개념 학습
[분야] → [주제 카드] → [설명]
[학습 영역 안의 질문창] → [로컬 AI 답변]
```

- **바둑판 출력**은 `src/board_svg.py`의 SVG를 `st.image()`로 렌더링합니다. 이전의 `st.html()` 사용으로 바둑판이 보이지 않던 경로는 제거했습니다.
- **재생 버튼·슬라이더는 바둑판 바로 아래**에 있습니다. 재생 속도는 `PLAYBACK_SECONDS = 2`로 고정되어 있습니다.
- Streamlit fragment는 **재생 중에만 0.5초마다 경과 시간을 확인**합니다. 매 0.5초에 한 수가 진행되는 것은 아니며, 실제 착수는 2초 간격입니다.
- 일시정지·수순 이동 후에는 오른쪽 AI 분석 영역도 갱신하도록 구성했습니다.
- 질문창은 전체 화면 하단 고정 대신 **학습 영역 내 컨테이너**에 두어 바둑판을 가리지 않도록 수정했습니다.
- 사이드바는 기본적으로 접혀 있으며 **01 오청원 기보 선택 / 02 AI 착수 분석 / 03 학습 자료**로 구성됩니다.

## Windows 설치 및 실행

GitHub 코드 변경은 연결된 GitHub에서 직접 관리하고, 개인 PC에서는 **최신 ZIP으로 갱신**합니다. `git clone`, `git pull`, `start_baduk.ps1`은 필요하지 않습니다.

PowerShell에서 기존 Streamlit을 `Ctrl + C`로 종료하고 실행하세요.

```powershell
$work = "$HOME\Downloads\baduk-insight-test"
New-Item -ItemType Directory -Force $work | Out-Null
Invoke-WebRequest -Uri "https://github.com/areum-hub/baduk-insight/archive/refs/heads/main.zip" -OutFile "$work\baduk-insight.zip"
Expand-Archive -Path "$work\baduk-insight.zip" -DestinationPath $work -Force
Set-Location "$work\baduk-insight-main"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**접속:** http://localhost:8501

ZIP을 기존 작업 폴더에 덮어 풀면 일반적으로 ZIP에 없는 `.venv/`, `data/sgf/go_seigen/`, `data/local/`, `data/chroma/` 파일은 남습니다. 중요한 개인 데이터는 백업해 두세요. GitHub에서 삭제된 이전 소스 파일이 로컬에는 남을 수 있습니다.

## 오청원 기보 사용

1. **01 · 오청원 기보 선택**에서 기본 `오청원` 모드를 유지합니다.
2. 유효한 로컬 기보가 없다면 CWI 원본 아카이브 다운로드를 시도합니다. 실패 시 **CWI 원본에서 다시 가져오기** 또는 보유한 `go_seigen.tgz` 파일을 업로드하세요.
3. 기보는 `data/sgf/go_seigen/`에 로컬 저장되며 GitHub에 포함되지 않습니다.
4. 기본 목록에는 **PB/PW 대국자에 Go Seigen이 기록되고 착수 기록 및 메인 수순 재생 검사를 통과한 SGF**만 나타납니다. 따라서 원본 전체 파일 수와 표시 건수는 다를 수 있습니다.
5. 처음 선택된 대국을 복기하거나, **다른 SGF**를 선택해 컴퓨터의 SGF 또는 CWI 공식 URL을 열 수 있습니다.

**출처:** [CWI 오청원 아카이브](https://homepages.cwi.nl/~aeb/go/games/go_seigen.tgz) · [CWI 기보 목록](https://homepages.cwi.nl/~aeb/go/games/games/)

## KataGo 분석 (선택 설치)

[KataGo 공식 릴리스](https://github.com/lightvector/KataGo/releases)의 실행 파일과 호환되는 신경망 모델을 사용자 PC에 준비하세요. GitHub 저장소에는 엔진·모델이 포함되지 않습니다.

| 기본 설정 | 경로·값 |
| --- | --- |
| KataGo 실행 파일 | `%USERPROFILE%\KataGo\katago.exe` 또는 PATH의 `katago` |
| 경량 신경망 | `%USERPROFILE%\Downloads\kata1-b10c128-s1141046784-d204142634.txt.gz` |
| 분석 설정 | `configs/analysis_local.cfg` |
| 방문 수 | 기본 5회, 선택 5·10·25·50·100회 |

사이드바 **02 · AI 착수 분석**에서 설정을 확인·저장할 수 있습니다. PC별 설정은 `data/local/katago_settings.json`에 저장됩니다.

원하는 수순으로 이동 → **일시정지** → 오른쪽 **이 장면 AI 분석하기**를 선택하세요. N수의 분석은 **그 수를 두기 전인 N−1수까지의 국면**을 요청합니다. SGF의 규칙·덤이 누락됐으면 임시 분석 기준이 적용될 수 있으므로 결과 해석에 주의해야 합니다.

## 바둑 개념 학습 및 로컬 AI

`knowledge/`에는 16개의 Markdown 개념 노트가 있습니다. Ollama 없이도 카드를 선택하고 설명을 읽을 수 있습니다.

로컬 질문 기능을 쓰려면 [Ollama](https://ollama.com/download/windows)를 설치·실행한 후 다음 모델을 준비하세요.

```powershell
ollama pull qwen3:1.7b
```

기본 질문은 `src/fast_study.py`의 관련 노트 검색 → `src/study_chat.py`의 프롬프트 구성 → `src/ollama_client.py`의 Ollama 통신 순서로 처리됩니다. 외부 유료 AI API 요금은 없지만 PC 성능과 모델 로딩에 따른 지연은 있을 수 있습니다.

기본 학습 카드 및 질문 기능에 ChromaDB 임베딩 색인은 필요하지 않습니다. 과거 RAG 실험은 **03 · 학습 자료 → 검색 색인 관리 · 선택**에서 수동으로 색인 확인·동기화할 수 있습니다.

## 저장소 구조

```text
baduk-insight/
├── app.py                       # Streamlit 메인 대시보드
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── configs/
│   └── analysis_local.cfg       # KataGo 설정
├── src/
│   ├── __init__.py
│   ├── board_svg.py             # SVG 바둑판
│   ├── sgf_service.py           # SGF 파싱과 수순 복기
│   ├── playback.py              # 재생·일시정지 상태 및 슬라이더 키
│   ├── go_seigen_source.py      # 오청원 TGZ·로컬 기보 필터링
│   ├── cwi_source.py            # 개별 CWI SGF HTTPS 불러오기
│   ├── katago_client.py         # KataGo 분석
│   ├── local_settings.py        # PC별 KataGo 설정
│   ├── study_guide.py           # 분야별 학습 카드
│   ├── fast_study.py            # 바둑 개념 검색
│   ├── study_chat.py            # 노트 기반 채팅 프롬프트
│   ├── ollama_client.py         # 로컬 Ollama 통신
│   └── rag_pipeline.py          # 선택형 ChromaDB 실험
├── knowledge/                   # 바둑 개념 노트 16개
├── tests/                       # pytest 파일 11개
│   ├── test_board_svg.py
│   ├── test_cwi_source.py
│   ├── test_dashboard_layout.py
│   ├── test_fast_study.py
│   ├── test_go_seigen_source.py
│   ├── test_katago_client.py
│   ├── test_local_settings.py
│   ├── test_playback.py
│   ├── test_rag_pipeline.py
│   ├── test_study_chat.py
│   └── test_study_guide.py
└── docs/
    ├── SETUP_WINDOWS.md         # Windows 설치·실행 가이드
    ├── ARCHITECTURE.md          # 시스템 구조·데이터 흐름
    └── DEVELOPMENT_LOG.md       # 개발 기록·검증 현황
```

**추적 파일 49개**는 실제 GitHub `main` 트리를 기준으로 확인했습니다. `start_baduk.ps1`과 과거 알파고 샘플 다운로드 스크립트는 제거되었습니다. 오청원 SGF 원본, 로컬 KataGo 모델, 가상환경, ChromaDB 데이터, 캐시는 GitHub에 포함하지 않습니다.

## 테스트 및 검증 현황

PowerShell에서 프로젝트 루트로 이동한 다음 실행하세요.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

`tests/`는 SGF·CWI URL·오청원 TGZ·바둑판 SVG·재생 계산·KataGo 요청·학습 자료·질문 처리 등을 검사합니다. 일부 항목은 모의 입력과 가짜 KataGo/Ollama 응답을 사용하며, `test_dashboard_layout.py`는 **정적 소스 구조 검사**이지 실제 브라우저 조작 테스트가 아닙니다.

**별도 Windows 브라우저에서 확인해야 할 항목:** 오청원 바둑판 표시, 2초 재생·일시정지·슬라이더, 우측 AI 분석 버튼과 추천 위치, 학습 카드 반응, 질문창 스크롤 겹침, 실제 KataGo·Ollama 및 CWI 다운로드 연결.

> **검증 상태:** GitHub 코드·파일 구조 확인과 수정 반영을 진행했습니다. 최신 변경 이후 **전체 pytest 통과와 실제 Windows 브라우저 통합 동작은 검증 완료로 확인되지 않았습니다.** 이를 완료된 테스트로 표시하지 않습니다.

## 데이터·저작권·라이선스

- 소스 코드는 [MIT License](LICENSE)입니다. 이 라이선스가 CWI SGF 등 외부 자료의 권리를 포함하지는 않습니다.
- 공개 저장소에는 오청원 SGF 원본을 커밋하지 않습니다. SGF, 로컬 모델·설정, Chroma 데이터 등의 이용 조건과 백업 책임은 별도로 확인하세요.
- `.gitignore`는 새 커밋에 적용되며, 이미 공개된 과거 Git 이력을 지우지는 않습니다.

## 관련 문서

- [Windows 실행 및 문제 해결](docs/SETUP_WINDOWS.md)
- [아키텍처 및 데이터 흐름](docs/ARCHITECTURE.md)
- [개발 기록 및 검증 현황](docs/DEVELOPMENT_LOG.md)
