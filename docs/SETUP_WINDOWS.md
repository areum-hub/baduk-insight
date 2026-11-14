# Windows 실행 가이드 — Baduk Insight

> 대상: Windows PowerShell / VS Code 터미널 사용자  
> 목표: **SGF 바둑판 실행 → Ollama 연결 → RAG 바둑 질문**  
> KataGo는 선택 사항이며 별도 설치합니다. 이 문서는 설치 절차를 설명하는 것이지 실제 사용자 PC에서의 성공을 보증하지는 않습니다.

[← README](../README.md) · [개발 기록](DEVELOPMENT_LOG.md)

## GitHub 최신 코드와 동기화하여 실행

이미 프로젝트를 설치했다면 아래 순서로 실행하세요.

**처음 한 번 (동기화 시작 스크립트 받아오기):**

```powershell
cd "C:\Windows\System32\baduk-insight"
git pull --ff-only origin main
```

**그다음부터는 실행할 때마다:**

```powershell
cd "C:\Windows\System32\baduk-insight"
.\start_baduk.ps1
```

PowerShell 실행 정책이 스크립트 실행을 막으면 현재 실행에 한해서만 다음 명령어를 사용할 수 있습니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_baduk.ps1
```

이 스크립트는 `main` 브랜치와 올바른 GitHub 원격 저장소를 확인하고, **로컬에서 수정한 추적 파일이 있다면 중단**합니다. `git pull --ff-only`로 안전하게 최신 코드를 가져와 의존성을 설치한 뒤 앱을 실행합니다. 인터넷 연결이나 비공개 저장소 인증이 실패하면 동기화를 중단하며, `git reset --hard`는 실행하지 않습니다.

**주의:** 실행 시 한 방향 코드 업데이트입니다. 개인 SGF·RAG 색인 데이터·KataGo 가중치 파일은 GitHub에 올리지 않으며, PC의 로컬 파일로 유지합니다. 실행 중 실시간 반영은 아닙니다. 이미 실행 중인 Streamlit은 `Ctrl + C`로 종료하고 재실행하세요.

## 0. 준비물

- Windows 10/11
- Git, Python 3.10 이상 (`py --version`으로 확인)
- [Ollama for Windows](https://ollama.com/download/windows) — Phase 3의 임베딩/LLM에 필요
- KataGo 실행 파일 및 신경망 가중치 — **Phase 2 분석을 실제 사용할 때만 필요**
- 개인 GitHub 저장소 `areum-hub/baduk-insight`에 접근 권한

> **주의:** 프로젝트는 `C:\Windows\System32`가 아니라 **사용자 폴더**에 저장하세요. 이전에 System32에 복제했다면 삭제할 필요 없이 사용자 폴더에 새로 복제해서 작업하면 됩니다.

## 1. 최신 코드 내려받기

**처음 복제하는 경우:**

```powershell
Set-Location $HOME
New-Item -ItemType Directory -Force -Path "$HOME\Projects" | Out-Null
Set-Location "$HOME\Projects"
git clone https://github.com/areum-hub/baduk-insight.git
Set-Location .\baduk-insight
```

Private 저장소이므로 GitHub 로그인 또는 Git 자격 증명 인증이 필요할 수 있습니다.

**이미 사용자 폴더에 복제했다면:**

```powershell
Set-Location "$HOME\Projects\baduk-insight"
git pull origin main
```

> 위 경로는 권장 예시입니다. 다른 폴더에 이미 저장했다면 **실제 경로로 이동**하세요. `Get-Location`으로 현재 경로를 확인할 수 있습니다.

## 2. Python 패키지 설치

프로젝트 루트(`app.py`가 있는 폴더)에서:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PowerShell 활성화 정책 문제를 피하기 위해 가상환경의 `python.exe`를 **직접 호출**합니다. `Activate.ps1`은 실행하지 않아도 됩니다.

`A new release of pip is available`는 **오류가 아니라 업데이트 안내**입니다. 선택적으로만 업데이트하세요:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

## 3. SGF 기보 준비

기본 다운로드 스크립트는 CWI의 **이세돌–알파고 2016년 제1·4·5국**을 로컬 `data/sgf/`로 내려받도록 작성되어 있습니다.

```powershell
.\.venv\Scripts\python.exe scripts\download_cwi_samples.py
```

성공했으면 `OK:` 및 `Downloaded or existing: 3/3` 형태의 출력이 나올 수 있습니다. 이 출력은 **성공 시 기대 형식**이며, 아직 사용자 PC에서 검증되지 않았습니다.

다운로드가 실패하면 [CWI AlphaGo/Lee Sedol 기보 페이지](https://homepages.cwi.nl/~aeb/go/games/games/AlphaGo/)에서 SGF를 수동 다운로드한 뒤 `data/sgf/`에 놓거나, 앱에서 **Upload SGF**를 선택하세요. 웹페이지의 `sgf` 링크를 누르면 기보 파일을 받을 수 있습니다.

원본 SGF 기보 데이터는 저장소에 커밋하지 않습니다.

**CWI 원본 기보 연결:** 앱의 **기보 불러오기 → SGF 업로드**를 선택하면 **CWI 기보 원본 페이지 열기** 링크가 표시됩니다. 웹사이트에서 필요한 기보를 직접 다운로드한 뒤 파일 선택기로 업로드합니다. 샘플 자동 다운로드 버튼은 없습니다. 기존 `data/sgf/` 기보는 **내 기보에서 선택**에서 이용합니다.

## 4. Ollama 설치 — 이전 오류 해결

이전에 아래와 같은 메시지가 나타났습니다:

```text
'ollama' 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 프로그램의 이름으로 인식되지 않습니다.
```

이 오류는 **Ollama가 설치되지 않았거나, 새 PowerShell에 실행 경로(PATH)가 반영되지 않았다는 뜻**입니다. Python 패키지 설치와는 별개입니다.

1. [Ollama Windows 설치 페이지](https://ollama.com/download/windows)에서 설치합니다.
2. 설치를 마치고 **PowerShell을 완전히 닫았다가 다시 열어** 다음 명령을 실행합니다.

```powershell
ollama --version
```

여전히 인식되지 않으면 기본 설치 위치를 확인합니다.

```powershell
Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
```

- `False`: Ollama 설치 여부와 실제 경로를 확인합니다.
- `True`: 아래 명령으로 실행 파일을 직접 확인합니다.

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
```

설치 경로가 맞지만 `ollama`를 인식하지 못하는 경우, **현재 PowerShell 창에서만 임시로** 경로를 추가할 수 있습니다.

```powershell
$env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
ollama --version
```

## 5. 로컬 AI 모델 설치

Ollama 프로그램이 실행 중인지 확인한 뒤 PowerShell에서:

```powershell
ollama pull embeddinggemma-2:270m
ollama pull qwen3:4b-instruct
ollama list
```

| 모델 | 담당 역할 |
| --- | --- |
| `embeddinggemma-2:270m` | 바둑 개념 문서와 질문을 의미 벡터로 변환 |
| `qwen3:4b-instruct` | 검색된 지식과 실제 KataGo 분석을 바탕으로 한국어 답변 작성 |

모델 파일은 **로컬 PC에 다운로드**되며 Git에 업로드되지 않습니다. 첫 다운로드는 네트워크와 디스크 용량이 필요하고, RAM 사용량은 다운로드 파일 크기보다 클 수 있습니다.

Ollama 앱을 열어 서버가 실행 중인지 확인하세요. 연결 문제 발생 시 아래 명령으로 API 응답을 점검할 수 있습니다.

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

서버가 실행 중인데도 연결되지 않거나 이미 포트를 사용 중이라는 메시지가 나오면 `ollama serve`를 중복 실행하지 말고 기존 Ollama 앱 상태부터 확인하세요.

## 6. 앱 실행

프로젝트 루트에서:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 **http://localhost:8501** 을 여세요.

**화면 확인 순서**

1. 왼쪽 **Load a game**에서 `Local CWI samples` 또는 `Upload SGF` 선택
2. 바둑판이 보이면 **Previous / Next / Move**로 수순 이동
3. 왼쪽 **RAG learning (local)** → **Build / refresh knowledge index** 클릭
4. `현재 검색 색인: 10개 학습 문서` 형태로 표시되는지 확인
5. 오른쪽 **AI 바둑 학습 챗봇**에 질문: **“축과 장문의 차이는 무엇인가요?”**
6. 답변과 **검색 근거 문서** 경로가 표시되는지 확인

`Build / refresh knowledge index`는 처음 한 번 필요하고, `knowledge/*.md` 노트를 수정했다면 다시 실행하세요.

> **자동 복기 이용 팁:** 오른쪽 KataGo 분석과 챗봇은 일시정지 후 현재 국면에 대해 이용하세요. 자동 재생이 끝나면 마지막 수에서 정지합니다. 새 기능을 사용하려면 `git pull origin main`으로 최신 파일을 받으세요.

> **KataGo 설치 전에도** SGF 뷰어와 RAG 챗봇은 사용할 수 있습니다. 단, 실제 추천 착수·승률·점수 차이는 KataGo 없이는 제공되지 않습니다.

## 7. KataGo 분석 사용(선택)

[KataGo 공식 GitHub Releases](https://github.com/lightvector/KataGo/releases)에서 운영체제에 맞는 엔진을 받아 설치하고, 호환되는 신경망 모델 파일을 준비하세요.

앱 왼쪽 **KataGo (local)**에 다음을 지정합니다.

- `KataGo executable`: 실제 `katago.exe` 경로
- `Neural net model path`: 다운로드한 모델 `.bin.gz` 경로
- `Analysis config path`: 프로젝트의 `configs/analysis_local.cfg` 경로

**경로 자동 고정:** 앱이 Windows 사용자 폴더를 기준으로 실행 파일 `~/KataGo/katago.exe`, 소형 모델 `~/Downloads/kata1-b10c128-s1141046784-d204142634.txt.gz`, 프로젝트 분석 설정을 자동 제안합니다. 기존 대형 모델 설정은 소형 모델로 전환합니다. 저장 버튼을 눌러 PC 전용 설정을 확정할 수 있습니다. 파일을 실제 다운로드하지 않았다면 경로가 표시되더라도 분석은 실행되지 않으니 존재 여부를 확인하세요.

**경로 저장:** 설치 경로를 입력한 후 **KataGo 설정 저장**을 누르면 `data/local/katago_settings.json`에 PC 전용 설정이 저장되어 앱을 껐다 켜도 유지됩니다. 파일은 `.gitignore`에 포함되어 Private GitHub에도 업로드되지 않습니다.

**Intel UHD Graphics CPU 분석 최적화:** 첫 분석은 **Maximum visits = 5 또는 10**을 권장합니다. 같은 국면과 동일한 설정의 반복 분석은 실행 중인 Streamlit 서버의 메모리 캐시를 활용합니다. 네트워크 로딩 및 CPU 계산이 계속 오래 걸린다면 공식 KataGo 네트워크 목록에서 더 작은 모델을 받아 기존 `.bin.gz` 경로를 바꾸고 다시 저장하세요. 현재 큰 모델은 CPU에서 상당히 오래 걸릴 수 있습니다.

수순 1 이상을 선택하고 **Analyze position before this move**를 누르면 **그 수를 두기 직전의 국면**을 평가하도록 설계되어 있습니다. 규칙(`Rules for KataGo`)과 덤(`Komi`)은 SGF와 일치하는지 확인하세요.

**착수 비교 표시:** 오른쪽 분석 결과에서 🟠 **실제 프로기사 착수**와 🔵 **AI 추천 위치**가 별도 카드로 나타납니다. 같은 두 위치가 현재 바둑판에 주황색·파란색 테두리로 표시됩니다. 두 수가 다르다고 곧바로 실수라는 뜻은 아니며, 이는 **착수 직전** 분석의 비교입니다.

현재 KataGo를 이용한 실제 엔진 분석은 **아직 Windows PC에서 통합 검증 전**입니다. 후보 수와 변화를 설명하는 기능은 있지만, 착수 전후 승률 손실 비교는 아직 구현되지 않았습니다.

## 빠른 챗봇과 새 사이드바 (2026-11-14)

사이드바는 **기보 선택·AI 착수 분석·AI 학습 자료** 세 카드로 나누어 표시하고, 상세 설정은 접힌 메뉴에서 사용합니다. 기존 기능과 설정 값은 유지합니다. 첫 착수 전(0수)에 표시되던 파란 이동 안내는 제거했습니다.

**바둑 AI에게 물어보기**의 기본값은 **빠른 답변**입니다. `knowledge/`에 저장된 학습 노트를 바로 읽어서 관련 문장을 보여주므로 Ollama가 꺼져 있어도 사용할 수 있습니다. 이는 학습 노트 인용이지 AI 생성형 답변이 아니며, 현재 바둑판의 구체적인 승률이나 최선 수를 계산하지 않습니다. **AI 자세히 설명**을 선택하면 기존 Ollama 기반 RAG 챗봇이 동작합니다. 정확한 속도 개선 여부는 PC에서 확인하세요.

## 7-1. 사이드바와 학습 노트 동기화

사이드바는 **01 · 기보 선택 / 02 · AI 착수 분석 / 03 · AI 학습 자료**로 구성됩니다. 분석 엔진 경로·탐색 횟수 및 규칙·덤 값은 접힌 설정에서만 수정합니다.

바둑 학습 노트는 기존 10개에 새 노트 6개를 더해 **총 16개**를 소스에 포함합니다. 화면에서는 **보유한 학습 노트**와 **AI 검색에 등록된 문서**를 따로 표시합니다. 예를 들어 보유 노트가 16개이고 검색 문서가 10개이면 **학습 자료 관리 → AI 검색 자료 동기화** 버튼을 눌러야 추가 6개가 ChromaDB에 등록됩니다. 동기화 시 Ollama 임베딩 모델이 실행되어 있어야 합니다.

CWI 원본에서 SGF를 불러오는 중 인증서 오류가 발생하면 `pip install -r requirements.txt`로 `truststore`를 설치하고 앱을 재시작하세요. Windows 시스템 인증서를 사용하되 TLS 검증을 끄지는 않습니다. 그래도 오류가 발생하면 공식 아카이브에서 SGF를 받아 **내 컴퓨터 파일 업로드**를 선택하세요.

## 8. 오류별 해결

| 증상 | 점검 |
| --- | --- |
| `ollama` 명령을 찾을 수 없음 | 4단계: Ollama 설치, PowerShell 재시작, 기본 설치 경로 확인 |
| `ModuleNotFoundError: streamlit / sgfmill / chromadb` | 2단계: 프로젝트 폴더에서 가상환경 Python으로 `pip install -r requirements.txt` 실행 |
| Python이 설치되지 않았다고 표시 | `py --version` 확인 후 Python 설치 |
| `No local SGFs` | 3단계 스크립트 실행 또는 앱에서 `Upload SGF` |
| `현재 검색 색인: 0개` | Ollama 모델 설치 후 `Build / refresh knowledge index` |
| Ollama 연결 실패 | Ollama 앱 구동 및 `http://127.0.0.1:11434/api/tags` 확인 |
| KataGo 실행 파일/모델을 찾을 수 없음 | 7단계 경로와 파일 존재 여부 점검; RAG만 사용한다면 생략 가능 |
| `localhost:8501` 접속 불가 | Streamlit 실행 터미널에 오류가 없는지 확인, 현재 포트 확인 |

## 9. 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

일부 테스트는 **Ollama와 KataGo를 가짜 응답으로 대체하는 단위 테스트**입니다. 통과하더라도 실제 모델·기보·화면까지 정상 동작한다는 뜻은 아닙니다.

[개발 단계와 검증 상태 자세히 보기](DEVELOPMENT_LOG.md) · [기술 설계](ARCHITECTURE.md)
