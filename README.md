# Baduk Insight

**A personal AI-powered Go (Baduk) game review and learning project.**

바둑이라는 취미를 Python과 AI 공부로 연결하기 위해 시작한 개인 프로젝트입니다. 프로기사 기보를 한 수씩 따라가며 수의 의미를 배우고, 앞으로 KataGo 분석과 RAG 대화형 학습을 결합하려고 합니다.

> **현재: Phase 3 — 로컬 RAG 학습 챗봇 코드 추가.** 코드와 모의 테스트를 등록했으며 실제 Ollama/ChromaDB/KataGo 연동과 전체 앱 실행은 로컬에서 검증이 필요합니다.

## 개발 목표

- [x] SGF 업로드 및 메인 수순 복기용 초기 뷰어 코드
- [ ] CWI 프로 기보 3판 다운로드 및 실제 기보 재생 검증
- [x] KataGo 분석 요청 및 후보 수 표시 코드 작성 (실제 엔진 실행 검증 전)
- [x] EmbeddingGemma 2 + ChromaDB 기반 바둑 개념 검색 코드 작성 (실제 로컬 모델 검증 전)
- [x] 검색 근거를 표시하는 한국어 복기 챗봇 코드 작성 (실제 로컬 모델 검증 전)
- [ ] 개인 학습 기록 및 반복 복습

## Quickstart (Windows PowerShell)

Python 3.10 이상 권장:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_cwi_samples.py
streamlit run app.py
```

### Phase 3 — 로컬 AI 학습 챗봇 실행

1. [Ollama](https://ollama.com/download) 설치 후 Ollama 서버 실행
2. 임베딩·답변 모델 설치 (Ollama 모델 태그는 설치된 버전에 맞게 확인)

```powershell
ollama pull embeddinggemma-2:270m
ollama pull qwen3:4b-instruct
```

3. `streamlit run app.py` 실행 후 **SGF 기보를 선택**합니다.
4. 왼쪽 **Build / refresh knowledge index** 버튼으로 `knowledge/*.md` 학습 노트 10개를 임베딩합니다.
5. 수순을 선택하고 오른쪽의 **AI 바둑 학습 챗봇**에 질문하면 연관 문서 3개를 검색하여 출처와 함께 답변을 생성합니다.
6. 같은 장면을 미리 KataGo로 분석했다면 실제 분석 수치도 답변에 전달합니다. 분석을 실행하지 않았다면 승률·추천 수를 임의로 주장하지 않도록 제한합니다.

이 단계는 **프로 기보 SGF → KataGo(선택사항) → EmbeddingGemma 임베딩 → ChromaDB 검색 → Qwen 한국어 답변** 구조입니다. 색인/대화는 로컬 Ollama에만 요청하고, ChromaDB 저장 파일은 `data/chroma/`에 남으며 Git에 포함하지 않습니다. **기보 전체를 벡터화하지 않습니다.**

**주의:** 이번 구현의 학습 문서는 직접 작성한 기초 바둑 개념 10개입니다. 실제 기사 인터뷰나 특정 기보의 주석 자료가 아닙니다. 모델 답변은 틀릴 수 있고, 프로기사의 실제 의도를 알 수는 없습니다.

```powershell
pytest -q
```

테스트는 Ollama 모의 응답 및 가짜 벡터 컬렉션을 사용합니다. 현재 실제 KataGo·Ollama·Streamlit 통합 실행은 검증하지 않았습니다.

KataGo가 설치되지 않아도 SGF 뷰어를 사용할 수 있습니다. AI 분석을 실행하려면 별도 로컬 KataGo 엔진과 신경망 모델 파일이 필요합니다. Windows에서 KataGo를 다운로드한 뒤 좌측 메뉴에 실행 파일 경로(예: `C:\\Tools\\KataGo\\katago.exe`), 신경망 모델 `.bin.gz` 경로, `configs/analysis_local.cfg` 경로를 지정하고 **Analyze position before this move** 버튼을 누르세요. 테스트를 위해서는 `pytest -q`를 실행할 수 있습니다.

- [KataGo 공식 저장소](https://github.com/lightvector/KataGo)
- [KataGo JSON 분석 프로토콜](https://github.com/lightvector/KataGo/blob/master/docs/Analysis_Engine.md)

설정 파일은 흑 시점 승률(`reportAnalysisWinratesAs = BLACK`)을 사용합니다. SGF의 룰·덤은 분석 전 직접 확인하세요.

다운로드가 불가능하면 [CWI 프로 기보 아카이브](https://homepages.cwi.nl/~aeb/go/games/games/)에서 SGF 파일을 직접 받아 `data/sgf/`에 넣거나, 앱에서 업로드할 수 있습니다.

## Project structure

```text
baduk-insight/
├── app.py
├── requirements.txt
├── src/
│   ├── sgf_service.py
│   ├── board_svg.py
│   ├── katago_client.py
│   ├── ollama_client.py
│   └── rag_pipeline.py
├── scripts/download_cwi_samples.py
├── configs/analysis_local.cfg
├── tests/test_board_svg.py
├── tests/test_katago_client.py
├── tests/test_rag_pipeline.py
├── knowledge/*.md            # 직접 작성한 학습 노트 10개
├── docs/ARCHITECTURE.md
└── data/sgf/                # local SGFs (not committed)
```

## 설계 원칙

- **SGF**는 수순과 보드 상태를 위한 구조화 데이터로 처리합니다.
- **KataGo**가 실제 바둑 형세 및 후보 수를 평가합니다.
- **EmbeddingGemma / RAG**는 정석·행마·사활 등 설명 자료를 검색합니다.
- LLM은 분석과 검색된 근거를 바탕으로 설명하며 프로기사의 실제 의도를 단정하지 않습니다.
- 초기에는 소수의 19×19 기보에서 선택한 장면만 분석하여 로컬 연산량을 줄입니다.

아키텍처 계획은 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참고하세요.

## Data provenance

기보 출처: [CWI Go Games Archive](https://homepages.cwi.nl/~aeb/go/games/). CWI 큐레이터는 기보 컬렉션이 퍼블릭 도메인이라고 안내합니다. 제3자가 작성한 주석과 추가 학습 자료에는 별도 권리가 있을 수 있습니다. 원본 SGF는 Git 저장소에 포함하지 않습니다.

## License

자체 작성 코드: MIT. 외부 기보와 해설은 각 출처의 조건을 따릅니다.
