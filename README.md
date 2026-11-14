# Baduk Insight

**A personal AI-powered Go (Baduk) game review and learning project.**

바둑이라는 취미를 Python과 AI 공부로 연결하기 위해 시작한 개인 프로젝트입니다. 프로기사 기보를 한 수씩 따라가며 수의 의미를 배우고, 앞으로 KataGo 분석과 RAG 대화형 학습을 결합하려고 합니다.

> **현재: Phase 1 — SGF 기보 뷰어 초기 구현.** KataGo 분석, EmbeddingGemma 기반 RAG, LLM 챗봇은 개발 예정입니다.

## 개발 목표

- [x] SGF 업로드 및 메인 수순 복기용 초기 뷰어 코드
- [ ] CWI 프로 기보 3판 다운로드 및 실제 기보 재생 검증
- [ ] KataGo 후보 수·형세 분석
- [ ] EmbeddingGemma 2 + ChromaDB 기반 바둑 개념 검색
- [ ] 근거를 표시하는 한국어 복기 챗봇
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

다운로드가 불가능하면 [CWI 프로 기보 아카이브](https://homepages.cwi.nl/~aeb/go/games/games/)에서 SGF 파일을 직접 받아 `data/sgf/`에 넣거나, 앱에서 업로드할 수 있습니다.

## Project structure

```text
baduk-insight/
├── app.py
├── requirements.txt
├── src/
│   ├── sgf_service.py
│   └── board_svg.py
├── scripts/download_cwi_samples.py
├── tests/test_board_svg.py
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
