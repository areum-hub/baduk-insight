# Baduk Insight

**프로 바둑 기보 복기 · KataGo 착수 분석 · 바둑 개념 학습**

Windows에서 실행하는 개인용 Python/Streamlit 바둑 학습 대시보드입니다. SGF 원본을 한 수씩 복기하고, 필요한 장면만 KataGo로 분석하며, 한국어 학습 노트 16개를 읽고 로컬 AI에게 추가 질문할 수 있습니다.

> **소스 기준:** 2026-11-15 · Private GitHub `main` · **실제 Windows 최신 통합 실행은 아직 미검증**  
> 코드는 GitHub에 반영되어 있으나 사용 중인 PC의 `git pull` 성공·Ollama 모델 실행·KataGo 실분석·CWI HTTPS 접속 여부는 별도로 확인해야 합니다.

## 현재 구현

| 기능 | 실제 동작 |
| --- | --- |
| SGF 기보 | `data/sgf/`의 파일 선택, 컴퓨터에서 업로드, CWI 공식 원본 HTTPS URL 열기 |
| 복기 | 이전·다음, 수순 슬라이더, 재생·일시정지, **2초에 한 수** |
| 바둑판 | SVG 9·13·19줄, 실제 착수 주황 테두리, 엔진 추천 수 파란 테두리 |
| KataGo | 클릭한 수를 두기 **직전** 국면의 흑 승률·예상 점수 차이·최대 3개 후보 수 및 예상 수순 |
| 개념 학습 | `knowledge/`의 한국어 노트 **16개**, 분야 선택 → 제목 카드 → 원문 설명 |
| 추가 질문 | 학습 카드 아래 질문창, **Ollama + `qwen3:1.7b`** 로컬 스트리밍 답변 |
| 선택형 색인 | 사이드바에 접힌 ChromaDB 색인 관리 기능 (학습 카드·기본 질문에 필수 아님) |

**아직 없는 기능:** 착수별 학습 메모·북마크의 지속 저장, 자동 승률 손실 평가, 정확한 프로기사 의도 추론, 보장된 모든 질문의 정답.

## 현재 화면

- **메인 헤더:** Baduk Insight, 큰 부제와 Noto Sans KR 글꼴(접속 불가 시 시스템 글꼴로 대체)
- **사이드바:** 첫 표시 시 접힘. 기보 선택 / KataGo 설정 / 학습 자료의 세 카드로 구성
- **기보 복기 상단:** 왼쪽 바둑판·재생 **65%**, 오른쪽 KataGo **35%**
- **왼쪽 정렬 기준:** 대국명(작은 제목)과 대회·날짜·결과·파일명이 바둑판 위에 배치됨. 바둑판·재생 버튼 3개·수순 슬라이더는 최대 **720px**의 같은 중앙 정렬 영역에 놓임
- **학습 영역:** 두 열 아래 **전체 너비**. 분야를 고르고 카드 하나를 누르면 설명이 열리며, **별도 챗봇 제목·모델 소개 문구 없이** 질문창이 아래에 이어짐
- **아이콘:** Streamlit의 Material Symbols 아이콘 글꼴은 본문 글꼴과 분리하여 아이콘 이름이 글자로 보이지 않도록 스타일 처리

최신 브라우저별 폭·폰트 표시·아이콘 동작은 실제 Windows에서 검증이 필요합니다.

## Windows 실행

이미 내려받은 PC에서 PowerShell로 기존 Streamlit을 `Ctrl + C`로 종료한 다음:

```powershell
cd "C:\Windows\System32\baduk-insight"
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저 주소: **http://localhost:8501**

별도의 실행 스크립트가 있는 경우 `.\start_baduk.ps1`로 GitHub 최신 코드 동기화, 패키지 확인, 실행을 순서대로 시도할 수도 있습니다. GitHub **Private 저장소 인증이 실패하면 코드가 업데이트되지 않습니다.** `reset --hard`로 로컬 파일을 지우지 마세요.

처음 설치·오류 해결은 [Windows 실행 가이드](docs/SETUP_WINDOWS.md)를 참고하세요. 현재 사용자 PC에서 사용한 작업 위치가 `System32` 하위였지만, 장기적으로는 사용자 작업 디렉터리가 더 안전합니다. 기존 폴더를 확인하지 않은 채 이동하지 마세요.

## 로컬 AI 질문 (무료 사용량)

[Ollama](https://ollama.com/download/windows)를 Windows PC에 설치하고 켠 후:

```powershell
ollama pull qwen3:1.7b
```

선택한 학습 카드와 질문에 관련된 학습 노트를 `src/study_chat.py`가 추려 `127.0.0.1:11434`의 Ollama에 전달합니다. **외부 유료 AI API 호출 및 질문 횟수별 요금은 없습니다.** 최초 다운로드와 모델 실행 시간이 필요하며, CPU 성능에 따라 느릴 수 있습니다. 노트에 없는 내용이나 실제 판의 최선 수·승률을 **모델 답변으로 확정해서는 안 됩니다.**

Ollama가 없어도 학습 카드는 읽을 수 있고 기보 복기·KataGo는 별개로 작동합니다. 로컬 ChromaDB 색인을 쓰려면 별도 `embeddinggemma-2:270m` 임베딩 모델이 필요하지만 기본 카드·채팅에는 필요하지 않습니다.

## KataGo 분석

[KataGo Releases](https://github.com/lightvector/KataGo/releases)에서 별도로 설치해야 합니다. GitHub에는 실행 파일·가중치가 포함되지 않습니다.

- 제안 엔진: `%USERPROFILE%\KataGo\katago.exe`
- 제안 모델: `%USERPROFILE%\Downloads\kata1-b10c128-s1141046784-d204142634.txt.gz`
- 분석 설정: `configs/analysis_local.cfg`, 기본 탐색 횟수 **5**
- 사용 PC 전용 값: `data/local/katago_settings.json` (Git 무시)
- **이 장면 AI 분석하기:** 선택한 N번째 수의 *착수 전* 판을 분석함
- 흑 승률·점수 차이는 **흑 기준**, 추천 수가 실제 수와 달라도 바로 실수라고 결론 내리지 않음

원본 SGF에 규칙이나 덤이 없으면 앱은 **임시 기본값**을 사용하며, 실제 대국 규칙으로 확정하지 않습니다.

## CWI 공식 기보

사이드바 **01 · 기보 선택 → SGF 업로드 → CWI 원본에서 바로 열기**에서 제공 샘플 또는 CWI 아카이브의 `.sgf` 직접 주소를 지정합니다. HTTPS 인증서 검증은 끄지 않습니다. 외부 연결에 실패하면 [공식 CWI 아카이브](https://homepages.cwi.nl/~aeb/go/games/games/)에서 SGF를 다운로드하여 **내 컴퓨터 파일 업로드**를 사용하세요.

## 코드 구조

```text
app.py                         화면, 복기·분석·학습 UI
src/sgf_service.py              SGF 파싱과 메인 수순 재생
src/board_svg.py                바둑판, 착수·추천 위치 표시
src/playback.py                 2초 자동 복기 로직
src/cwi_source.py               공식 SGF URL 검증과 HTTPS 불러오기
src/katago_client.py            로컬 KataGo 분석 요청·응답
src/local_settings.py           PC별 KataGo 설정
src/study_guide.py              원문 카드 분류와 표시
src/fast_study.py               질문과 관련된 학습 노트 탐색
src/study_chat.py               로컬 Qwen3 질문 프롬프트
src/ollama_client.py            로컬 Ollama 통신·임베딩 실험
src/rag_pipeline.py             선택형 ChromaDB 색인 실험
knowledge/*.md                  한국어 학습 노트 16개
scripts/download_cwi_samples.py 선택 실행용 CWI 다운로드 헬퍼
start_baduk.ps1                 Windows 실행 스크립트
tests/                          단위 테스트
```

## 테스트 및 제한

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

단위 테스트 일부는 KataGo 및 Ollama를 모의 처리합니다. 테스트를 통과해도 최신 Windows 브라우저의 레이아웃, CWI 원격 HTTPS, 실제 KataGo 처리 속도, 무료 Qwen3 답변 성능이 검증되는 것은 아닙니다.

저장소는 **Private**이며 `data/sgf/`, `data/local/`, `data/chroma/` 등의 개인 데이터, 로컬 설정과 모델 파일은 `.gitignore`에서 제외합니다. 제3자 기보·해설의 저작권 및 이용 조건은 별도 확인해야 합니다.

## 문서

- [Windows 설치와 문제 해결](docs/SETUP_WINDOWS.md)
- [시스템 구조와 데이터 흐름](docs/ARCHITECTURE.md)
- [개발 기록·검증 현황](docs/DEVELOPMENT_LOG.md)
