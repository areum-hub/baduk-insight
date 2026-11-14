# Baduk Insight

**프로 바둑 기보로 공부하는 나만의 AI 바둑 복기 챗봇**  
*A personal Go (Baduk) review & learning chatbot powered by KataGo and RAG.*

좋아하는 **바둑**을 AI 개발 공부와 연결하기 위해 시작한 개인 프로젝트입니다. 프로기사의 실전 기보를 한 수씩 따라가고, 궁금한 착수를 질문하면서 정석·행마·사활 같은 개념을 배워가는 학습 도구를 목표로 합니다.

> **개발 현황 (2026-11-14)**  
> Phase 1~3의 **초기 소스 코드와 테스트가 GitHub에 등록**되었습니다. Windows의 **SGF 기보 뷰어 화면 표시와 Ollama 모델 다운로드**는 확인했습니다. 자동 재생·KataGo·RAG 전체 동작은 **검증 중**입니다.  
> 프로젝트는 **Private** 저장소로 운영합니다.

## 먼저 읽기

| 문서 | 내용 |
| --- | --- |
| **[Windows에서 실행하기](docs/SETUP_WINDOWS.md)** | 처음 설치부터 Streamlit 실행, Ollama 오류 해결까지 |
| **[Phase 1~3 개발 기록](docs/DEVELOPMENT_LOG.md)** | 왜 만들었는지, 단계별로 무엇을 구현했는지, 남은 검증 |
| **[기술 설계와 확장 계획](docs/ARCHITECTURE.md)** | SGF·KataGo·RAG 역할 분리, 한계, Phase 4 |

## 이 프로젝트로 하고 싶은 것

1. **프로 바둑 복기:** CWI의 프로기사 SGF 기보를 앱 내 다운로드 버튼이나 SGF 업로드로 불러와 **자동 재생·일시정지·수순 탐색**으로 공부하기
2. **AI 착수 분석:** KataGo로 선택한 국면의 형세와 추천 후보 수 확인
3. **대화형 바둑 공부:** EmbeddingGemma로 관련 바둑 개념을 검색하고 Qwen에게 한국어 설명 듣기
4. **나만의 학습 기록:** 궁금했던 수, 배운 내용, 반복 실수를 따로 저장하기 *(Phase 4 예정)*

## 서비스 흐름

```text
CWI 프로 기보 (SGF)
   ↓  sgfmill
19×19 기보 뷰어 ── 선택한 착수 ──→ KataGo (형세·후보 수 분석)
   │                                  │
   └──────── 질문/현재 장면 ──────────┤
                                      ▼
바둑 학습 노트 → EmbeddingGemma 2 → ChromaDB에서 관련 개념 검색
                                      │
                                      ▼
                          Qwen3 한국어 RAG 해설
                           + 참고 문서 출처 표시
```

KataGo 분석은 **선택 사항**입니다. 설치하지 않아도 기보 뷰어와 바둑 개념 RAG는 사용할 수 있도록 설계했습니다. 단, 엔진 분석 없이 구체적인 승률이나 '프로기사의 실제 의도'를 단정하지 않습니다.

## 자동 복기 기능 (2026-11-14 추가)

SGF 기보가 열리면 바둑판 위에서 **▶ 재생 / ⏸ 일시정지 / ⏮ 이전 / ⏭ 다음** 버튼을 사용할 수 있습니다. **재생 간격은 2초로 고정**하여 한 수씩 진행합니다. 속도 선택 메뉴는 없습니다. 마지막 수에 도달하면 자동으로 정지하고, 슬라이더로 이동하면 재생을 중단합니다. **분석과 질문은 일시정지 상태에서** 진행하도록 설계했습니다.

자동 재생은 Streamlit fragment 기반으로 갱신합니다. 실행 검증은 사용자 Windows 환경에서 아직 필요합니다. 제어 로직은 `src/playback.py`, 테스트는 `tests/test_playback.py`에 분리했습니다.

## KataGo 경로 저장과 CPU 빠른 분석

왼쪽 **KataGo (local)**에서 `KataGo executable`과 `Neural net model path`, 설정 파일 경로를 입력하고 **KataGo 설정 저장** 버튼을 누르세요. 저장 위치는 `data/local/katago_settings.json`이며 Git에서 제외됩니다. 따라서 개인 PC의 설치 경로가 원격 저장소에 업로드되지 않습니다.

분석 방문 수는 **10회가 기본값**입니다(선택: 5/10/25/50/100). Intel 내장 그래픽 + CPU용 Eigen KataGo에서는 5~10으로 먼저 테스트하세요. 같은 기보·국면·규칙·덤·엔진·모델·방문 수로 재분석하면 Streamlit 서버 메모리 캐시를 재사용합니다. 앱을 재시작하거나 다른 국면을 분석하면 엔진을 다시 시작해야 합니다.

**경량 모델 교체 (Intel UHD Graphics / CPU):** 공식 KataGo `kata1-b10c128-s1141046784-d204142634.txt.gz` 모델을 사용합니다. 기존 대형 `.bin.gz` 대신 PC의 `Downloads`에 새 `.txt.gz`를 내려받은 후, 앱 왼쪽 **Neural net model path**에 전체 경로를 입력하고 **KataGo 설정 저장**을 클릭하세요. `Maximum visits`는 우선 **5 또는 10**으로 설정합니다. 새 모델로 실제 KataGo 분석이 성공한 후 기존 큰 가중치 파일을 삭제할 수 있습니다. 모델 파일은 GitHub에 추가하지 않습니다. [공식 모델 목록](https://katagotraining.org/networks/), [경량 모델 직접 링크](https://media.katagotraining.org/uploaded/networks/models/kata1/kata1-b10c128-s1141046784-d204142634.txt.gz).

**중요:** 대형 KataGo 신경망의 첫 실행과 CPU 추론 자체는 여전히 느릴 수 있습니다. 방문 수를 줄여도 신경망 로딩 시간이 사라지지는 않습니다. 충분히 빨라지지 않으면 [KataGo 공식 모델 목록](https://katagotraining.org/networks/)에서 더 작은 네트워크 모델을 선택해야 합니다. 실제 성능은 사용자 PC에서 검증해야 합니다.

## 단계별 개발 현황

| 단계 | 구현한 코드 | 아직 필요한 작업 |
| --- | --- | --- |
| **Phase 1 — 기보 뷰어** | SGF 파싱, 바둑판, 수순 탐색, 자동 재생·일시정지·2초 고정 간격, CWI 다운로드 스크립트 | 자동 재생 실제 동작 검증 |
| **Phase 2 — KataGo** | 분석 요청, 후보 수 3개, 변화도와 흑 승률 표시 | 엔진·신경망 설치 및 실제 분석 검증 |
| **Phase 3 — RAG 챗봇** | EmbeddingGemma 임베딩, ChromaDB 검색, Qwen 한국어 채팅, 기본 바둑 노트 10개 | 실제 검색·답변 검증 |
| **Phase 4 — 학습 기록** | 미구현 | 기보 북마크, 복습 기록, SQLite 설계 |

## 기술 스택

| 분야 | 도구 | 담당 역할 |
| --- | --- | --- |
| 웹 화면 | Python, Streamlit | 바둑판·분석 패널·챗봇 |
| 기보 처리 | sgfmill, SVG | SGF 파싱과 수순 재생 |
| 바둑 분석 | KataGo | 추천 수, 형세, 대안 변화도 |
| 임베딩 | EmbeddingGemma 2 270M (Ollama) | 바둑 지식 벡터화 |
| 벡터 검색 | ChromaDB | 질문과 관련된 개념 찾기 |
| 답변 생성 | Qwen3 4B Instruct (Ollama) | 한국어 학습 설명 |
| 테스트 | pytest | 주요 모듈 단위 테스트 |

## GitHub 코드 동기화 후 실행 (Windows)

최초 설치를 마친 PC에서는 프로젝트 폴더의 `start_baduk.ps1`를 실행하세요. 시작할 때 **GitHub Private 저장소의 `main` 최신 코드를 fast-forward 방식으로 내려받고**, 의존성을 확인한 뒤 Streamlit을 시작합니다.

```powershell
cd "C:\Windows\System32\baduk-insight"
.\start_baduk.ps1
```

**첫 실행에서는 새 스크립트 자체를 받아야 하므로** 기존 프로젝트에서 한 번만 `git pull --ff-only origin main`을 먼저 실행하세요. 이후에는 위 스크립트 하나로 실행할 수 있습니다. PowerShell 정책 때문에 차단되면 `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_baduk.ps1`로 해당 실행에 한해 스크립트를 실행할 수 있습니다.

이 방식은 **앱을 시작할 때만 코드 동기화**합니다. GitHub 변경 사항이 실행 중인 앱에 실시간 반영되거나 로컬 변경 사항이 GitHub에 자동 업로드되지는 않습니다. 로컬 코드 변경이 있으면 덮어쓰지 않고 중단합니다. 개인 SGF 기보, ChromaDB, KataGo 신경망 가중치, Ollama 모델은 PC에 보관하며 GitHub로 업로드하지 않습니다.

## 빠른 실행 (Windows PowerShell)

**Ollama를 먼저 설치하지 않아도 SGF 뷰어부터 실행할 수 있습니다.**

```powershell
Set-Location $HOME
New-Item -ItemType Directory -Force -Path "$HOME\Projects" | Out-Null
Set-Location "$HOME\Projects"
git clone https://github.com/areum-hub/baduk-insight.git
Set-Location .\baduk-insight
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\download_cwi_samples.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 **http://localhost:8501** 을 열어 왼쪽 **Download CWI games**를 클릭하세요. 다운로드 성공 시 바둑판을 볼 수 있습니다. 다운로드 오류가 뜨면 **Upload SGF**에서 직접 받은 기보 파일을 선택하세요. 코드와 다운로드 스크립트가 실제 PC에서 정상 실행되는지는 아직 검증이 필요합니다.

**RAG 챗봇을 사용하려면** [Ollama](https://ollama.com/download/windows)를 설치하고 새 PowerShell에서:

```powershell
ollama --version
ollama pull embeddinggemma-2:270m
ollama pull qwen3:4b-instruct
ollama list
```

앱 왼쪽의 **Build / refresh knowledge index**를 눌러 학습 노트 10개를 색인하세요. 자세한 단계와 문제 해결은 [Windows 실행 가이드](docs/SETUP_WINDOWS.md)에 정리했습니다.

### 현재 발견한 설치 문제

Windows에서 최초에는 `ollama` 명령 인식 오류가 발생했지만, 이후 **Ollama 설치와 두 모델 다운로드는 `ollama list` 화면으로 확인**했습니다. 아직 실제 RAG 색인·답변 품질은 검증되지 않았습니다. [해결 방법 보기](docs/SETUP_WINDOWS.md#4-ollama-설치--이전-오류-해결).

## 폴더 구조

```text
baduk-insight/
├── app.py                         # Streamlit 앱
├── requirements.txt               # Python 의존성
├── src/
│   ├── sgf_service.py             # 기보 파싱 및 재생
│   ├── board_svg.py               # 바둑판 SVG
│   ├── katago_client.py           # KataGo 분석 요청/응답
│   ├── local_settings.py          # 로컬 KataGo 설정 저장
│   ├── ollama_client.py           # 임베딩과 채팅 요청
│   └── rag_pipeline.py            # 문서 색인·검색·프롬프트
├── knowledge/                     # 직접 작성한 기초 바둑 학습 노트 10개
├── scripts/download_cwi_samples.py
├── configs/analysis_local.cfg
├── tests/                         # 단위 및 모의 연동 테스트
├── docs/
│   ├── SETUP_WINDOWS.md
│   ├── DEVELOPMENT_LOG.md
│   └── ARCHITECTURE.md
└── data/                           # 로컬 기보/색인 (Git에서 제외)
```

## 데이터와 주의사항

- 기보 출처: [CWI Go Games Archive](https://homepages.cwi.nl/~aeb/go/games/games/) — 실제 대국의 SGF를 내려받아 개인 학습에 활용합니다.
- `knowledge/`의 학습 노트는 이 프로젝트를 위해 작성한 기초 설명 자료입니다. 프로기사의 실제 인터뷰나 공식 기보 주석이 아닙니다.
- 바둑판은 KataGo가 평가하고, RAG는 바둑 **개념을 검색**하며, LLM은 확인한 정보에 기반해 설명하는 역할입니다.
- 모델 가중치, 다운로드한 기보, 개인 학습 데이터 및 로컬 벡터 DB는 저장소에 포함하지 않습니다.
- 프로젝트 자체 코드에는 저장소의 MIT LICENSE를 적용합니다. 외부 SGF 및 제3자 해설의 이용 조건은 별도로 확인합니다.

---

**핵심 목표:** 바둑을 취미로 즐기면서 AI 모델 연동, RAG 설계, 데이터 처리, 개인용 서비스를 직접 구현하고 공부하는 것입니다.
