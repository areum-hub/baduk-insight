# Baduk Insight — Windows 설치·실행 및 문제 해결

[README](../README.md) · [시스템 구조](ARCHITECTURE.md) · [개발 기록](DEVELOPMENT_LOG.md)

**기준:** 2026-11-15 · GitHub `areum-hub/baduk-insight` `main`

ChatGPT가 연결된 GitHub 저장소 코드를 직접 수정합니다. Windows에서는 공개 GitHub ZIP을 받아 Streamlit을 실행하면 됩니다. **`git clone`, `git pull`, `start_baduk.ps1`은 필요하지 않습니다.**

## 1. 최신 코드 받기 — Git 없이 ZIP 사용

실행 중인 Streamlit 서버가 있다면 PowerShell에서 `Ctrl + C`로 종료하세요.

```powershell
$work = "$HOME\Downloads\baduk-insight-test"
New-Item -ItemType Directory -Force $work | Out-Null

Invoke-WebRequest -Uri "https://github.com/areum-hub/baduk-insight/archive/refs/heads/main.zip" -OutFile "$work\baduk-insight.zip"
Expand-Archive -Path "$work\baduk-insight.zip" -DestinationPath $work -Force
Set-Location "$work\baduk-insight-main"
```

압축을 덮어 풀어도 **`.venv/`와 `data/sgf/go_seigen/`에 있는 기존 로컬 데이터는 유지**됩니다. 코드 갱신은 GitHub ZIP의 파일을 덮어쓰는 것이므로, 예전 버전에서 제거된 파일이 로컬에 남을 수 있습니다. 로컬의 `start_baduk.ps1`이나 `scripts/download_cwi_samples.py`는 실행하지 마세요.

## 2. Python 준비 및 Streamlit 실행

```powershell
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 **http://localhost:8501**로 접속하세요.

## 3. 오청원 기보 불러오기

사이드바 **01 · 오청원 기보 선택**에서 기본값은 **오청원**입니다.

- 최초 실행 시 CWI의 `go_seigen.tgz`를 자동으로 다운로드해 `data/sgf/go_seigen/`에 SGF를 로컬 저장합니다.
- 기본 목록에서는 **PB/PW에 Go Seigen이 기록되고, 착수 수순을 재생할 수 있는 기보만** 표시합니다. 아카이브의 891개가 모두 표시되는 것은 아닙니다.
- 자동 다운로드에 실패하면 **CWI 원본에서 다시 가져오기** 또는 보유한 `.tgz` 파일 업로드 기능을 사용하세요.
- 일반 SGF 파일이나 CWI 직접 SGF URL은 **다른 SGF**에서 별도로 선택합니다.
- SGF 원본 데이터는 공개 GitHub 저장소에 재배포하지 않습니다.

## 4. 기보 재생 (2초/수)

왼쪽 **바둑판 바로 아래**에 이전·재생·다음 버튼과 수순 슬라이더가 있고, 오른쪽에는 **AI 착수 분석**이 표시됩니다. 바둑판:AI 패널의 열 비율은 62:38입니다. **▶ 재생**을 누르면 2초당 한 수씩 이동합니다. **⏸ 일시정지**를 누르면 현재 수에 멈추고, 다시 재생하면 새로운 2초 간격으로 진행합니다. **이전/다음** 및 수순 슬라이더를 조작하면 재생이 중지됩니다.

**확인 순서:** 첫 수 표시 → 재생 → 일시정지 → 재개를 3회 반복 → 슬라이더로 수순 이동 → 재생 재개 → 마지막 수에서 자동 종료. 오류가 생기면 PowerShell 콘솔의 예외 메시지와 실행 중인 대국 파일명을 확인하세요.

## 5. KataGo AI 착수 분석 (선택)

KataGo 엔진과 신경망 파일은 저장소에 포함되지 않습니다. 공식 [KataGo Releases](https://github.com/lightvector/KataGo/releases)에서 설치합니다.

사이드바 **02 · AI 착수 분석 → 엔진 설정 및 분석 강도**에서 실행 파일, 모델, `configs/analysis_local.cfg`, 탐색 횟수(5/10/25/50/100)를 설정합니다. 기본 탐색 횟수는 5회입니다. 설정은 로컬의 `data/local/katago_settings.json`에 보관되며 GitHub로 업로드되지 않습니다.

원하는 수순에서 재생을 멈춘 다음 **이 장면 AI 분석하기**를 실행합니다. 결과는 해당 수를 두기 **직전 국면** 기준이며, 실제 프로기사의 의도를 확인하는 근거가 될 수는 없습니다.

## 6. 바둑 개념 학습 및 로컬 AI (선택)

`knowledge/`의 학습 노트 16개는 AI 설치 없이 볼 수 있습니다. 추가 질문에 로컬 AI 답변을 받으려면 Ollama를 실행하고 다음 모델을 준비하세요.

```powershell
ollama pull qwen3:1.7b
```

바둑 개념 학습 영역 안에 있는 질문창으로 질문할 수 있습니다. 입력창은 학습 영역을 벗어나 바둑판 위에 고정되지 않도록 구성되어 있습니다. 선택적 ChromaDB 검색 색인 실험은 사이드바 **03 · 학습 자료 → 검색 색인 관리 · 선택**에서 관리하며, 기본 학습 카드와 질문 기능에는 필요하지 않습니다.

## 7. 테스트 및 문제 해결

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

| 증상 | 확인 사항 |
| --- | --- |
| `ModuleNotFoundError` | `pip install -r requirements.txt` 재실행 |
| `localhost:8501` 접속 실패 | Streamlit 실행 창의 주소 및 포트 확인 |
| 오청원 목록이 비어 있음 | CWI 다운로드 오류 확인 또는 보유한 TGZ 파일 업로드 |
| 재생 중 Streamlit 예외 | 최신 ZIP 갱신 후 재시작, 오류 메시지와 SGF 파일명 확인 |
| 수순 슬라이더 오류 | 최신 `app.py`에서 위치별 슬라이더 키를 쓰는지 확인 |
| KataGo 분석 실패 | 엔진·모델·설정 파일 경로 및 모델 호환성 확인 |
| Ollama 질문 실패 | Ollama 실행 여부 및 `ollama list`에서 모델 확인 |

**검증 구분:** 정적 코드 확인 및 단위 테스트 통과와 실제 Windows 브라우저에서의 자동 재생·바둑판 SVG 표시·오른쪽 분석 패널·질문창 스크롤 동작 성공은 다릅니다. 재생·일시정지·슬라이더 동작은 PC의 Streamlit 화면에서 직접 확인해야 합니다.
