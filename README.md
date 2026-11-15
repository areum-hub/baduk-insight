# Baduk Insight

**개인 프로젝트 | KataGo와 로컬 AI를 활용한 프로 바둑 기보 복기·개념 학습 대시보드**

Baduk Insight는 **오청원(Go Seigen)의 대국 기보**를 한 수씩 복기하고, **KataGo**로 착수 직전 국면을 분석할 수 있는 **Python·Streamlit 기반 개인 AI 바둑 학습 대시보드**입니다.

16개의 바둑 개념 노트를 통해 기본 개념을 학습하고, 궁금한 내용은 **Ollama 기반 로컬 AI에 질문**할 수 있습니다. PC에서 Streamlit을 실행해 웹 브라우저로 이용합니다.

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| 기보 불러오기 | CWI 오청원 `go_seigen.tgz`를 PC에 저장하고, 오청원 대국 중 재생 가능한 기보를 기본 목록에 표시. 다른 SGF 업로드·CWI HTTPS URL도 지원 |
| 바둑판 복기 | 9·13·19줄 SVG, 이전·재생·일시정지·다음, 수순 슬라이더, **2초당 한 수** |
| KataGo 분석 | 선택한 착수 **직전 국면**의 흑 승률, 예상 집 차이, 추천 수·후보 수순 표시 |
| 바둑 개념 학습 | 분야별 학습 카드와 Markdown 노트 **16개** |
| 로컬 AI 질문 | 관련 개념 노트를 바탕으로 Ollama `qwen3:1.7b` 응답 |
| 선택형 RAG | ChromaDB·`embeddinggemma-2:270m` 색인 실험. 기본 학습·질문에는 불필요 |

**화면 구성:** 왼쪽 62%에 바둑판과 그 아래 재생 버튼·슬라이더, 오른쪽 38%에 AI 착수 분석을 배치합니다. 일시정지한 이전·다음 수 이동은 전체 화면 대신 복기 영역만 갱신하며, 첫 재생 시각과 작은 화면 갱신 지연을 보정하도록 구성했습니다. 대국명 아래에는 SGF에 실제 기록된 대국 연도·장소·결과만 표시하며, 없는 대회명이나 파일명은 대국 정보로 사용하지 않습니다. 바둑판은 `st.image()`로 SVG를 표시하고, 학습 질문창은 하단 학습 영역 안에 둡니다. 사이드바에서 **01 기보 선택 / 02 AI 설정 / 03 학습 자료**를 관리합니다.

> KataGo 수치와 AI 추천으로 프로기사의 실제 의도를 확정할 수 없습니다. 로컬 학습 채팅은 바둑 개념 노트에 기반하며, 현재 KataGo 국면 데이터를 자동으로 전달받지 않습니다.

## Windows 실행

Python이 필요합니다. **Git 설치 없이** GitHub 최신 ZIP을 받아 실행할 수 있습니다. 기존 Streamlit을 실행 중이라면 `Ctrl + C`로 종료하세요.

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

브라우저에서 **http://localhost:8501**에 접속합니다. 기존 폴더에 ZIP을 덮어 풀면 보통 `.venv/` 및 `data/`의 로컬 파일은 유지되지만, 중요한 데이터는 별도로 백업하세요.

## 사용 방법

### 1. 오청원 기보 복기

사이드바 **01 · 오청원 기보 선택**에서 기본 기보를 선택합니다. 처음 실행할 때 CWI 아카이브를 자동으로 가져오며, 실패 시 **CWI 원본에서 다시 가져오기** 또는 `go_seigen.tgz` 업로드를 사용할 수 있습니다.

기보는 `data/sgf/go_seigen/`에 **로컬 저장**됩니다. 기본 목록에는 오청원 대국자 정보와 메인 수순 재생 검사를 통과한 기보만 표시됩니다. **다른 SGF** 메뉴에서는 PC 파일이나 CWI 직접 URL을 열 수 있습니다.

원본 출처: [CWI 오청원 아카이브](https://homepages.cwi.nl/~aeb/go/games/go_seigen.tgz) · [CWI 기보 목록](https://homepages.cwi.nl/~aeb/go/games/games/)

### 2. KataGo 착수 분석 (선택 설치)

[KataGo 공식 릴리스](https://github.com/lightvector/KataGo/releases)에서 실행 파일과 신경망 모델을 준비합니다. 저장소에는 엔진과 모델이 포함되지 않습니다.

사이드바 **02 · AI 착수 분석**에서 실행 파일·모델·`configs/analysis_local.cfg` 경로와 분석 방문 수를 설정합니다. **기본 방문 수는 5회**이며, 선택값은 5·10·25·50·100회입니다. PC별 설정은 `data/local/katago_settings.json`에 저장됩니다.

원하는 수에서 **일시정지 → 이 장면 AI 분석하기**를 누르면 해당 착수 **직전** 국면을 분석합니다. 원본 SGF에 규칙이나 덤 정보가 없으면 임시 기준이 적용될 수 있습니다.

### 3. 바둑 개념 및 로컬 AI

`knowledge/`의 16개 학습 노트는 Ollama 없이 읽을 수 있습니다. 질문 기능은 [Ollama](https://ollama.com/download/windows)를 설치하고 다음 모델을 준비한 뒤 사용합니다.

```powershell
ollama pull qwen3:1.7b
```

기본 질문은 관련 노트를 참고하는 **로컬 AI** 방식입니다. ChromaDB 색인 동기화는 사이드바 **03 · 학습 자료**의 선택 기능이며 기본 질문에 필요하지 않습니다.

## 프로젝트 구조

```text
baduk-insight/
├── app.py                # Streamlit 대시보드
├── src/                  # SGF·바둑판·재생·KataGo·Ollama·학습 로직
├── knowledge/            # 바둑 개념 Markdown 노트 16개
├── configs/              # KataGo 설정
├── tests/                # pytest 테스트
├── docs/                 # Windows 가이드·시스템 구조·개발 기록
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

**오청원 SGF 원본, 가상환경, KataGo 모델, 로컬 설정·캐시·ChromaDB 데이터는 GitHub에 포함하지 않습니다.**

## 테스트 및 검증

프로젝트 폴더의 PowerShell에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

테스트는 SGF·바둑판·재생·CWI URL·KataGo 요청·학습 기능 등을 검사하며, 일부는 모의 데이터를 사용합니다. **레이아웃 테스트는 정적 코드 검사**이므로 실제 Windows 브라우저 동작을 보증하지 않습니다.

바둑판 표시, 2초 재생·일시정지, AI 분석 버튼, 학습 카드·스크롤, 실제 KataGo·Ollama 연결은 로컬 환경에서 별도로 확인해야 합니다. **전체 테스트 통과 및 브라우저 통합 검증은 아직 확인되지 않았습니다.**

## 라이선스 및 문서

- **소스 코드:** [MIT License](LICENSE). 외부 SGF·모델에는 별도의 이용 조건이 적용될 수 있으며, 소스 라이선스가 SGF 재배포 권한을 의미하지 않습니다.
- [Windows 설치·문제 해결](docs/SETUP_WINDOWS.md) · [시스템 구조](docs/ARCHITECTURE.md) · [개발 기록](docs/DEVELOPMENT_LOG.md)
