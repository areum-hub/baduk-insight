# Baduk Insight — Windows 실행 가이드

[← README](../README.md) · [개발 기록](DEVELOPMENT_LOG.md) · [구조 설명](ARCHITECTURE.md)

이 문서는 **현재 GitHub `main` 브랜치의 Baduk Insight**를 Windows에서 실행하고 확인하는 방법입니다. 챗봇은 **16개 바둑 학습 노트 기반 빠른 답변 전용**입니다. KataGo 착수 분석은 별도 설치가 필요합니다.

## 1. 기존 PC에서 최신 코드 실행

기존 Streamlit 서버를 실행한 PowerShell 창에서 `Ctrl + C`로 중지합니다.

```powershell
cd "C:\Windows\System32\baduk-insight"
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 **http://localhost:8501** 을 엽니다. `git pull`이 GitHub 인증 오류를 내면 업데이트가 반영되지 않은 상태입니다. 오류를 해결한 뒤 다시 실행하세요. `reset --hard`로 기존 PC 데이터를 지우지 마세요.

**간편 실행:** 설치된 프로젝트에 `start_baduk.ps1`이 있으면 다음 명령도 사용할 수 있습니다.

```powershell
cd "C:\Windows\System32\baduk-insight"
.\start_baduk.ps1
```

스크립트는 원격 저장소와 `main` 브랜치를 확인하고, GitHub 동기화·Python 패키지 설치·Streamlit 실행을 순서대로 시도합니다. 로컬에서 수정한 추적 파일이 있으면 중단합니다.

> 현재 확인된 PC 프로젝트 위치가 Windows의 `System32` 아래입니다. 권장 개발 위치는 사용자 폴더지만 **기존 작업 위치를 확인하지 않고 임의로 이동하거나 삭제하지 마세요.**

## 2. 처음 설치한다면

**준비:** Python, Git, Windows PowerShell, GitHub Private 저장소 접근 권한.

```powershell
git clone https://github.com/areum-hub/baduk-insight.git
cd baduk-insight
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

이미 설치한 PC에서는 `git clone`을 다시 할 필요가 없습니다. 실행 중 오류가 발생하면 `.venv\Scripts\python.exe`의 경로부터 확인하세요.

## 3. 사이드바 — 기보 선택

**01 · 기보 선택**에서 세 방식 중 하나로 기보를 불러옵니다.

- **내 기보에서 선택:** PC의 `data/sgf/` 폴더에 있는 SGF 선택
- **SGF 업로드 → CWI 원본에서 바로 열기:** 기본 샘플(이세돌–알파고 1·4·5국) 또는 CWI 공식 SGF 파일 주소로 직접 연결, **이 기보로 복기 시작**
- **SGF 업로드 → 내 컴퓨터 파일 업로드:** 내 PC에서 SGF 업로드

[CWI 공식 아카이브](https://homepages.cwi.nl/~aeb/go/games/games/)에서 원본 기보를 확인할 수 있습니다. 원본 SGF의 HTTPS 연결은 Windows의 신뢰 인증서 저장소를 사용합니다. SSL 오류가 발생하면 원본 사이트에서 직접 SGF를 저장하여 **내 컴퓨터 파일 업로드**를 사용하세요. 앱은 인증서 검증을 꺼서 우회하지 않습니다.

## 4. 기보 복기

기보를 불러온 후 화면에서 **⏮ 이전 / ▶ 재생·⏸ 일시정지 / ⏭ 다음 / 수순 슬라이더**를 이용합니다.

자동 재생은 **2초마다 한 수**로 고정됩니다. 슬라이더로 이동하면 재생을 중단합니다. 마지막 수에서 자동으로 정지합니다. KataGo 분석과 채팅 입력은 재생을 일시정지하고 이용하세요.

## 5. KataGo 착수 분석 (선택 설치)

KataGo 엔진 및 신경망 모델은 앱/저장소에 포함되지 않으며 PC에 설치해야 합니다.

- 실행 파일 기본 제안: `%USERPROFILE%\KataGo\katago.exe`
- 경량 모델 기본 제안: `%USERPROFILE%\Downloads\kata1-b10c128-s1141046784-d204142634.txt.gz`
- 프로젝트 분석 설정: `configs/analysis_local.cfg`

KataGo가 설치되어 있다면 **02 · AI 착수 분석 → 엔진 설정 및 분석 강도**에서 실제 경로를 확인하고 필요한 경우 **이 PC에 분석 설정 저장**을 누릅니다. 해당 값은 `data/local/katago_settings.json`에만 저장되고 GitHub에 업로드되지 않습니다.

**AI 탐색 횟수** 기본값은 5입니다. 수치가 작으면 분석이 빨라질 수 있지만 신뢰도가 떨어질 수 있습니다. 실제 CPU 환경에 따라 시간이 많이 걸릴 수 있습니다.

수순 N을 선택하고 **이 장면 AI 분석하기**를 누르면 **N수를 두기 직전 국면**의 승률(흑 기준), 예상 집 차이, 추천 수를 표시합니다. **🟠 실제 착수**와 **🔵 AI 추천**을 비교하고, **다른 후보 수와 예상 진행 확인**에서 상세 내용을 펼칩니다. 다른 수라는 이유만으로 잘못된 수라고 판단하면 안 됩니다.

**대국 규칙 · 덤 (필요할 때만)**에서 KataGo 계산 규칙과 백의 덤을 확인합니다. SGF에 규칙 정보(`RU`)가 없으면 중국식 기본값은 **확인되지 않은 임시 기준**입니다.

공식 설치 자료: [KataGo Releases](https://github.com/lightvector/KataGo/releases). 다운로드 파일이 실제 PC와 호환되는지 확인하세요.

## 6. 바둑 AI에게 물어보기 — 빠른 학습 노트 답변

챗봇은 `knowledge/`에 들어 있는 **16개 바둑 노트**를 직접 검색하여 관련된 문장을 보여줍니다. **Ollama·ChromaDB·Qwen 생성 모델 호출은 하지 않습니다.**

질문 예시: `돌의 연결은 왜 중요할까?`, `축과 장문은 어떻게 다를까?`. 이전의 '이 수에서 중요한 바둑 개념은?' 질문은 제거했으며, 참고 노트 및 개별 학습 주제 목록은 화면에 표시하지 않습니다.

현재 수에 대한 정확한 승률·최선 수·프로기사의 의도는 채팅으로 판단하지 않으며, 그 판단은 별도 KataGo 분석이 필요합니다. 현재 기보/착수 장면을 바꾸면 화면의 대화 이력이 새로 시작됩니다.

## 7. 학습 자료 확인과 관리

**03 · AI 학습 자료** 사이드바 카드에는 다음 정보가 있습니다.

- 보유 학습 노트 수(기본 16개)
- 개별 학습 주제 제목은 사이드바에 표시하지 않음
- AI 검색에 등록된 문서 수(선택형 ChromaDB 색인)

**현재 챗봇 빠른 답변에서는 검색 색인 동기화가 필수는 아닙니다.** 다만 이전 RAG 실습의 임베딩 색인을 갱신하려면 **학습 자료 관리 → AI 검색 자료 동기화**를 사용하며, 이 버튼에는 Ollama의 `embeddinggemma-2:270m` 모델 실행이 필요합니다. 노트 16개와 색인 문서 수가 다르다고 빠른 채팅에 문제가 있는 것은 아닙니다.

## 8. 오류별 점검

| 증상 | 점검 |
| --- | --- |
| `git pull` 인증 실패 | GitHub Private 저장소 인증·권한 확인 |
| `start_baduk.ps1` 파일 없음 | 먼저 최신 코드를 동기화하거나 Streamlit 직접 실행 |
| `ModuleNotFoundError` | `.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| `localhost:8501` 화면이 안 열림 | Streamlit 프로세스 오류 확인, 서버 종료 후 재실행 |
| 기보가 표시되지 않음 | SGF 파일 업로드 또는 CWI 연결, 파일 유효성 확인 |
| CWI `CERTIFICATE_VERIFY_FAILED` | 의존성 설치 확인, 원본 다운로드 후 직접 업로드 |
| KataGo 실행/모델 경로 오류 | 엔진 파일과 경량 `.txt.gz` 모델의 실제 존재 여부 확인 |
| 학습 노트 빠른 답변에 맞는 문서가 없음 | **03 · AI 학습 자료**에서 제목 확인, 더 구체적인 바둑 개념 질문 |
| ChromaDB 문서 수가 16개 미만 | 빠른 챗봇에는 영향 없음; 필요할 때만 색인 동기화 |

## 9. 테스트와 검증

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

단위 테스트에는 가짜 KataGo/Ollama 응답이 사용됩니다. 실제 Windows의 전체 분석, HTTPS 접속, Streamlit 화면 배치와 응답 속도는 별도로 검증해야 합니다.

[개발 기록](DEVELOPMENT_LOG.md) · [구조와 데이터 흐름](ARCHITECTURE.md)
