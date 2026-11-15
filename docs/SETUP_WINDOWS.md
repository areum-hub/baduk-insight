# Baduk Insight — Windows 설치·실행·문제 해결

[README](../README.md) · [아키텍처](ARCHITECTURE.md) · [개발 기록](DEVELOPMENT_LOG.md)

**소스 기준: 2026-11-15 / GitHub Private `main`**. 최신 Windows에서의 전체 통합 동작은 아직 확인하지 않았습니다.

## 1. 설치된 PC에서 최신 코드 실행

기존 Streamlit 서버를 사용 중이면 PowerShell에서 `Ctrl + C`로 종료합니다.

```powershell
cd "C:\Windows\System32\baduk-insight"
git status --short
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 **http://localhost:8501**을 엽니다. **Private 저장소** 인증 실패 시 변경 사항이 적용되지 않습니다. 추적 중인 소스에 수정 사항이 있다면 원인을 확인한 뒤 처리하세요. `git reset --hard`로 복구를 시도하지 마세요.

기존 저장소에 `start_baduk.ps1`이 있으면 `.\start_baduk.ps1`을 실행해 **main 확인 → 원격 동기화 → 종속성 설치 → Streamlit 실행**을 순서대로 시도할 수 있습니다. `-SkipDependencies` 옵션은 이미 설치한 패키지 확인을 건너뛸 때 사용합니다.

> 사용자 PC에서 확인된 기존 폴더가 `C:\Windows\System32\baduk-insight`입니다. 시스템 폴더는 권장 개발 경로가 아니므로 추후 사용자 폴더로 이동할 수 있으나, 현재 파일의 위치를 확인한 뒤 안전하게 옮기세요.

## 2. 새 PC에서 처음 설치

**필요:** Windows PowerShell, Python, Git, Private 저장소 접근 권한.

```powershell
git clone https://github.com/areum-hub/baduk-insight.git
cd baduk-insight
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

웹 브라우저에서 http://localhost:8501을 엽니다.

## 3. 화면과 바둑 기보

앱 최초 진입 시 **사이드바는 접힌 상태**입니다. 왼쪽 상단 버튼으로 여세요.

사이드바 **01 · 기보 선택**:
- **내 기보에서 선택:** `data/sgf/`의 SGF 파일 선택
- **SGF 업로드 → CWI 원본에서 바로 열기:** 제공 샘플 또는 공식 `.sgf` URL 입력 후 **이 기보로 복기 시작**
- **SGF 업로드 → 내 컴퓨터 파일 업로드:** PC의 SGF를 업로드

[CWI 공식 아카이브](https://homepages.cwi.nl/~aeb/go/games/games/)의 SGF만 직접 열 수 있습니다. HTTPS 인증서는 검증하며 우회하지 않습니다. 오류가 나면 웹 브라우저에서 원본 SGF를 내려받아 로컬 업로드를 이용하세요.

기보가 열리면 **상단 왼쪽 65% 바둑판·복기 / 오른쪽 35% KataGo 분석**으로 표시됩니다. 대국명과 대국 메타데이터는 바둑판 위에서 왼쪽 기준선이 맞고, **바둑판·이전/재생·다음 버튼·수순 슬라이더**는 같은 최대 720px 너비로 중앙 정렬됩니다. 자동 재생은 **2초마다 한 수**, 수동 이동 시 일시정지합니다.

**글꼴:** Noto Sans KR 우선, 네트워크에서 웹폰트를 가져올 수 없으면 시스템 글꼴로 대체합니다. 아이콘은 별도 Material Symbols 글꼴을 유지합니다. 메인 제목은 대국명보다 크고, 대국명은 비교적 작은 보조 제목입니다.

## 4. KataGo 로컬 AI 착수 분석

KataGo 엔진·신경망 파일은 앱에 포함되지 않으며 [공식 Releases](https://github.com/lightvector/KataGo/releases)에서 별도로 준비해야 합니다.

| 설정 | 기본 제안 |
| --- | --- |
| 실행 파일 | `%USERPROFILE%\KataGo\katago.exe` |
| 경량 신경망 | `%USERPROFILE%\Downloads\kata1-b10c128-s1141046784-d204142634.txt.gz` |
| 분석 설정 | `configs/analysis_local.cfg` |
| 탐색 횟수 | 기본 **5** (5, 10, 25, 50, 100 중 선택) |
| PC별 저장 | `data/local/katago_settings.json` (Git 제외) |

사이드바 **02 · AI 착수 분석 → 엔진 설정 및 분석 강도**에서 설정합니다. **이 PC에 분석 설정 저장**을 누르면 현재 PC에만 저장됩니다. 원본 SGF에서 규칙 `RU`와 덤 `KM`이 없으면 **대국 규칙 · 덤 (필요할 때만)**에서 분석 기준을 확인해야 합니다. 기본값을 원본 규칙으로 단정하지 않습니다.

장면 N으로 이동해 **이 장면 AI 분석하기**를 누르면 **N수를 두기 직전 국면**을 분석합니다. 흑 승률·예상 점수 차이(흑 기준)와 실제 착수(주황)·추천 수(파랑)를 비교하며, 추가 후보·예상 진행도 확인할 수 있습니다. 추천 수가 다르다는 사실은 실수 판정이 아닙니다. 낮은 탐색 횟수는 빠르지만 결과가 안정적이지 않을 수 있습니다.

## 5. 바둑 개념 학습과 무료 로컬 질문

SGF 없이도 아래의 **바둑 개념 학습**을 사용할 수 있습니다. **기본 규칙·돌의 생사 / 포석·돌의 형태 / 전투·수읽기 / 끝내기·형세** 등 분야를 고르고, 제목 카드를 누르면 해당 설명만 펼쳐집니다. 노트는 `knowledge/*.md` **16개**입니다.

이 학습 화면은 **전체 너비**이며, 카드 아래에 별도의 챗봇 제목이나 모델명 안내 없이 **질문창**이 바로 이어집니다. 카드 읽기에는 AI 설치가 필요 없습니다.

추가 질문에서 자연스러운 로컬 답변을 받으려면 [Ollama Windows](https://ollama.com/download/windows)를 설치·실행하고:

```powershell
ollama pull qwen3:1.7b
```

로컬 모델은 **API 호출 횟수에 따른 요금이 없고**, 질문은 PC의 `127.0.0.1:11434`에 전송됩니다. 대신 모델 다운로드, CPU 처리 및 최초 로딩 시간이 필요합니다. 앱은 선택 카드와 관련 노트를 근거로 간단한 답변을 생성합니다. **실제 국면 분석·승률·프로기사 의도는 생성형 설명만으로 확인할 수 없습니다.**

사이드바 **03 · 학습 자료 → 검색 색인 관리 · 선택**은 이전 ChromaDB/RAG 실험의 선택 기능입니다. **카드 표시와 현재 로컬 질문에는 색인이 필요하지 않습니다.** 색인 갱신에만 별도 `ollama pull embeddinggemma-2:270m`이 필요할 수 있습니다.

## 6. 문제 해결

| 증상 | 확인 사항 |
| --- | --- |
| `git pull` 인증 실패 | Private 저장소 권한, GitHub 자격 증명 확인 |
| `git pull` 로컬 수정 충돌 | 수정 파일을 확인하고 커밋/보관 후 재시도; 강제 초기화 금지 |
| `ModuleNotFoundError` | `.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| `localhost:8501` 접속 불가 | Streamlit 콘솔 메시지 및 포트 확인 |
| SGF 로딩 오류 | SGF 유효성, 확장자 및 파일 크기 확인 |
| CWI SSL 오류 | 인터넷/Windows 인증서 상태 확인 후 공식 사이트에서 직접 다운로드·업로드 |
| KataGo 분석 실패 | 실행 파일·신경망·설정 경로, 모델 호환성 점검 |
| Ollama 응답 실패 | Ollama 실행 여부, `ollama list`에서 `qwen3:1.7b` 설치 확인 |
| 아이콘 대신 `arrow_right` 등 텍스트 노출 | 최신 소스 적용 및 브라우저 강력 새로고침; Material Symbols 글꼴 접근 확인 |
| 노트가 보이지 않음 | `knowledge/` 파일 존재와 분야 선택 확인 |
| ChromaDB 색인 문서 수가 적음 | 기본 카드·질문 동작에 영향 없음; 색인 실험 시에만 갱신 |

## 7. 테스트와 실제 검증

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

모의 응답 단위 테스트가 포함됩니다. 실제 확인 순서는 **GitHub 동기화 → SGF 선택·복기 → 사이드바·폰트·아이콘 → 학습 카드·Ollama 질문 → KataGo 분석 → CWI HTTPS**를 권장합니다. 최신 Windows 종합 실행 결과가 확인되기 전에는 검증 완료로 표시하지 않습니다.

[README](../README.md) · [개발 기록](DEVELOPMENT_LOG.md)
