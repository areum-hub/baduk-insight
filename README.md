# Baduk Insight

**KataGo와 로컬 AI를 활용한 프로 바둑 기보 복기·개념 학습 프로젝트**

**Baduk Insight**는 SGF 형식의 프로 바둑 기보를 한 수씩 복기하고, 필요한 장면을 **KataGo**로 분석하며, 바둑 개념을 **학습 카드와 로컬 AI 질문**으로 공부하는 Python·Streamlit 기반 개인 프로젝트입니다.

외부 유료 AI API 없이 로컬에서 실행할 수 있도록 구성했습니다. **기보 복기, 국면 분석, 개념 학습**을 하나의 대시보드에서 연결하는 것이 목표입니다.

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| **SGF 기보 불러오기** | 첫 실행 시 CWI의 오청원 기보 아카이브를 자동으로 로컬에 가져와 기본 목록에 표시. 다른 SGF는 별도 업로드 또는 URL로 열기 |
| **기보 자동 복기** | 이전·다음 수, 수순 슬라이더, 재생·일시정지 및 **2초마다 한 수** 진행 (재생 중 슬라이더 상태 충돌 방지) |
| **KataGo 착수 분석** | 선택한 수를 두기 **직전 국면**에서 흑 승률, 예상 집 차이, 추천 착수·후보 수순 확인 |
| **AI 추천 수 표시** | 바둑판에 실제 착수(주황색)와 KataGo 추천 위치(파란색)를 구별하여 표시 |
| **바둑 개념 학습** | 한국어 Markdown 학습 노트 **16개**를 분야별 카드로 탐색하고 원문 설명 읽기 |
| **로컬 AI 추가 질문** | 학습 카드 아래 질문창에서 관련 노트를 참고하는 **Ollama + Qwen3 1.7B** 답변 |
| **RAG 실험 기능** | ChromaDB와 로컬 임베딩 모델을 사용한 **선택형 검색 색인 관리** 보존 |

> **분석 범위:** KataGo의 추천 수가 실제 착수와 다르다고 곧바로 실수라는 뜻은 아닙니다. AI 질문 기능도 프로기사의 의도나 특정 국면의 최선 수를 확인된 사실처럼 제공하지 않습니다.

## 대시보드 구성

- **사이드바:** 기본 접힘 상태. 기보 선택, KataGo 설정, 학습 자료 관리
- **상단 2열:** 바둑판·재생 컨트롤 **65%** / AI 착수 분석 **35%**
- **복기 영역:** 대국명과 대회·날짜·결과를 바둑판 위에 표시. 바둑판·버튼·수순 슬라이더를 같은 최대 **720px** 너비로 정렬
- **하단 전체 너비:** 학습 분야 선택 → 카드 클릭 → 설명 확인 → 그 아래에서 추가 질문
- **스타일:** Noto Sans KR 기반의 간결한 UI, Streamlit 아이콘 글꼴과 본문 글꼴 분리

현재 대시보드는 **Windows에서 실행하는 로컬 웹 앱**이며, 공개 웹 서비스로 배포된 버전은 아닙니다.

## 기술 스택

| 분야 | 기술 |
| --- | --- |
| 언어·화면 | Python, Streamlit, HTML/CSS, SVG |
| 기보 처리 | SGF, `sgfmill` |
| 국면 분석 | KataGo (로컬 엔진 및 신경망 모델 별도 설치) |
| 로컬 생성형 AI | Ollama, `qwen3:1.7b` |
| 학습 자료 검색 | 학습 노트 기반 키워드·유사 표현 검색 |
| 선택형 RAG 실험 | ChromaDB, `embeddinggemma-2:270m` |
| 테스트 | pytest |

**현재 기본 질문 기능**은 학습 노트를 검색하여 Qwen3에 참고 자료로 전달하는 방식입니다. **ChromaDB 벡터 검색은 필수 실행 경로가 아니라 별도 실험 기능**으로 유지하고 있습니다.

## 시작하기 — Windows

### 1. 프로젝트 설치

PowerShell에서 GitHub 최신 ZIP을 다운로드한 뒤 실행합니다. Git clone은 필요하지 않습니다.

```powershell
$work = "$HOME\Downloads\baduk-insight-test"
New-Item -ItemType Directory -Force $work | Out-Null
Invoke-WebRequest -Uri "https://github.com/areum-hub/baduk-insight/archive/refs/heads/main.zip" -OutFile "$work\baduk-insight.zip"
Expand-Archive -Path "$work\baduk-insight.zip" -DestinationPath $work -Force
Set-Location "$work\baduk-insight-main"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 **http://localhost:8501**로 접속합니다.

**기존 설치 사용자:** Streamlit 종료 후 최신 ZIP을 같은 작업 폴더에 덮어 풀고 다시 실행합니다. 로컬 `.venv/`, `data/sgf/go_seigen/`은 유지되지만 제거된 파일은 로컬에 남을 수 있습니다.

### 2. 기보 복기

사이드바의 **01 · 오청원 기보 선택**에서 기본 **오청원** 목록을 사용합니다.

1. **첫 실행 시** 앱이 CWI 원본 오청원 TGZ를 자동으로 내려받아 **`data/sgf/go_seigen/`**에 저장합니다. 네트워크 연결이 필요하며, 이미 저장된 기보가 있으면 다시 다운로드하지 않습니다.
2. 기본 **오청원 기보** 목록에는 이 전용 폴더의 SGF 중 **대국자에 Go Seigen이 포함되고, 착수 기록이 있으며, 메인 수순 재생 검사를 통과한 기보만** 표시됩니다. 첫 번째 대국은 자동 선택됩니다. 기존 다른 SGF나 알파고 기보는 기본 목록에 표시되지 않습니다. 원본 891개 중 기보 정보 기준 6개(다른 대국자 5개, 수순 없는 대국 1개)는 기본 목록에서 제외되며, 추가적인 착수 오류가 발견되면 표시 수는 더 줄어들 수 있습니다.
3. 자동 다운로드가 실패하면 **CWI 원본에서 다시 가져오기**를 누르거나, 보유한 `go_seigen.tgz`를 **TGZ에서 오청원 기보 등록**으로 불러올 수 있습니다.
4. 다른 기보를 연구하려면 **다른 SGF 직접 열기**에서 로컬 SGF를 업로드하거나 CWI 공식 SGF URL을 입력합니다.

기보를 불러오면 바둑판에서 수순을 이동하거나 자동 재생할 수 있습니다. **기보가 없어도 바둑 개념 학습은 사용 가능**합니다.

**오청원 기보의 출처:** [CWI 바둑 기보 아카이브](https://homepages.cwi.nl/~aeb/go/games/games/)의 [Go Seigen 아카이브 원본](https://homepages.cwi.nl/~aeb/go/games/go_seigen.tgz). 이 저장소는 원본 SGF를 포함하거나 재배포하지 않으며, 실행 시 제공처에서 사용자 PC로 다운로드하는 기능만 제공합니다. 아카이브 사용·재배포 조건은 원본 제공처에서 별도로 확인하세요. 다운로드가 실패하면 보유한 원본 `.tgz`를 대시보드에 직접 업로드할 수 있습니다.

### 3. KataGo 분석 (선택 설치)

[KataGo 공식 Releases](https://github.com/lightvector/KataGo/releases)에서 실행 파일과 호환되는 신경망 모델을 별도로 준비합니다.

| 기본 제안 설정 | 경로·값 |
| --- | --- |
| KataGo 실행 파일 | `%USERPROFILE%\KataGo\katago.exe` |
| 경량 신경망 | `%USERPROFILE%\Downloads\kata1-b10c128-s1141046784-d204142634.txt.gz` |
| 분석 설정 파일 | `configs/analysis_local.cfg` |
| 기본 탐색 횟수 | **5** (사이드바에서 변경 가능) |

사이드바의 **02 · AI 착수 분석 → 엔진 설정 및 분석 강도**에서 경로를 확인하고 저장할 수 있습니다. 특정 수로 이동한 뒤 **이 장면 AI 분석하기**를 클릭하면 해당 수의 착수 *전* 위치를 분석합니다. 탐색 횟수가 적으면 빠를 수 있지만 분석의 안정성이 떨어질 수 있습니다.

**규칙·덤 주의:** SGF에 대국 규칙이나 덤이 기록되지 않았다면 앱은 임시 분석 기준을 사용합니다. 이를 공식 대국 규칙으로 확정해서는 안 됩니다.

### 4. 로컬 AI 질문 (선택 설치)

[Ollama](https://ollama.com/download/windows)를 설치하고 실행한 다음 모델을 내려받습니다.

```powershell
ollama pull qwen3:1.7b
```

**바둑 개념 학습**에서 분야·카드를 선택하고, 아래 질문창에 궁금한 내용을 입력합니다. 학습 노트에서 관련 내용을 찾아 로컬 모델의 답변을 생성합니다.

- **사용량에 따른 유료 AI API 요금 없음:** 모델 추론은 사용자 PC에서 실행
- **모델 미설치 시:** 학습 카드·기보 복기는 계속 사용 가능
- **답변 한계:** 참고 노트가 제한적이며 모델 답변의 정확성을 보장하지 않음
- **속도:** 첫 모델 로딩과 CPU 성능에 따라 지연될 수 있음

기존 ChromaDB 색인 동기화는 학습용 선택 기능으로, 기본 카드·질문에 필요하지 않습니다.

## 프로젝트 구조

```text
baduk-insight/
├── app.py                         # Streamlit 대시보드
├── src/
│   ├── sgf_service.py             # SGF 파싱 및 복기
│   ├── board_svg.py               # SVG 바둑판과 착수 표시
│   ├── playback.py                # 자동 재생 로직
│   ├── cwi_source.py              # CWI 원본 단일 기보 불러오기
│   ├── go_seigen_source.py        # 오청원 아카이브 자동 다운로드 및 로컬 추출
│   ├── katago_client.py           # KataGo 분석 연동
│   ├── local_settings.py          # PC별 엔진 설정
│   ├── study_guide.py             # 분야별 학습 카드
│   ├── fast_study.py              # 관련 개념 노트 탐색
│   ├── study_chat.py              # 질문 및 참고 문서 프롬프트
│   ├── ollama_client.py           # 로컬 LLM 통신
│   └── rag_pipeline.py            # 선택형 ChromaDB 실험
├── knowledge/                      # 바둑 개념 학습 노트 16개
├── configs/                        # KataGo 분석 설정
├── tests/                          # pytest 테스트
├── docs/                           # 설치·구조·개발 기록
├── requirements.txt
└── LICENSE                         # 프로젝트 소스 코드 라이선스
```

## 테스트 및 현재 한계

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

단위 테스트에는 **KataGo·Ollama의 모의 응답**을 사용하는 항목이 포함됩니다. **최신 UI의 Windows 브라우저 재생·일시정지·슬라이더 동작, 오청원 TGZ 자동 다운로드, CWI HTTPS 연결, 실제 KataGo 분석과 Qwen3 응답 속도는 환경별 통합 검증이 필요**합니다. 검증하지 않은 사항을 완료된 기능처럼 표시하지 않습니다.

이 프로젝트는 전문 SGF 편집기나 경기 결과 예측 서비스가 아닙니다. 착수별 승률 손실 자동 판정, 개인 학습 기록·북마크의 영구 저장 기능은 현재 구현하지 않았습니다.

## 데이터·저작권·라이선스

- 이 저장소는 **Public**입니다. 소스 코드와 공개 커밋 기록을 누구나 열람할 수 있습니다.
- 사용자 SGF, 로컬 KataGo 모델·설정, ChromaDB 데이터 등은 `.gitignore`에서 관리 대상으로 제외합니다. 다만 **이미 커밋된 파일이나 과거 Git 기록은 `.gitignore`만으로 숨겨지지 않습니다.**
- 외부 SGF 원본, 대국 정보, 타사 모델과 해설의 이용 조건·라이선스는 각각 확인해야 합니다.
- **프로젝트 소스 코드 라이선스:** [MIT License](LICENSE).

## 추가 문서

- [Windows 설치·실행 및 문제 해결](docs/SETUP_WINDOWS.md)
- [시스템 아키텍처와 데이터 흐름](docs/ARCHITECTURE.md)
- [개발 기록과 검증 현황](docs/DEVELOPMENT_LOG.md)
