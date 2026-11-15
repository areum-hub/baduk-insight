# Baduk Insight — 시스템 구조와 데이터 흐름

[README](../README.md) · [Windows 실행](SETUP_WINDOWS.md) · [개발 기록](DEVELOPMENT_LOG.md)

**기준:** 2026-11-15 · Private GitHub `main`. 이 문서는 코드에 실제 연결된 기능과 선택적으로 보존된 실험 코드를 구분합니다.

## 1. 사용자 흐름과 화면 구조

```text
CWI HTTPS SGF / 컴퓨터 SGF 업로드 / data/sgf/
                     │
                sgfmill 파싱
                     │
           Streamlit app.py 대시보드
                     │
     ┌───────────────┴─────────────────────┐
     │                                     │
왼쪽 65% · 기보 복기                  오른쪽 35% · KataGo
SVG 바둑판 + 2초 자동 재생            선택 수 직전 국면 분석
실제 수(주황)·AI 추천(파랑)           승률·집 차이·추천·변화도
     └────────────────┬────────────────────┘
                      │
                 전체 너비 학습
          knowledge/*.md 16개 원문 카드
                      │
               질문 입력 · 대화
                      │
          src/study_chat.py (학습 노트 검색)
                      │
       Ollama 로컬 qwen3:1.7b (선택 설치)
```

**초기 사이드바는 접혀 있음.** 메인 영역의 대국명·대국정보와 바둑판·재생 버튼·수순 슬라이더는 같은 최대 720px 정렬 레인을 공유합니다. 메인 제목은 축소된 Baduk Insight 헤더이며, 대국명은 작은 보조 제목입니다. UI는 Noto Sans KR 우선 적용, 아이콘 글꼴은 별도로 유지합니다.

SGF가 없어도 학습 카드 및 로컬 질문 화면은 표시할 수 있습니다. 카드 아래에는 별도 챗봇 제목과 Ollama 모델명 소개 문구를 표시하지 않습니다.

## 2. 구현 모듈

| 파일 | 연결된 역할 |
| --- | --- |
| `app.py` | Streamlit 사이드바, 65:35 상단 레이아웃, 전체 너비 학습, 로컬 질문 |
| `src/sgf_service.py` | SGF 기본 메타데이터, 설정 돌·메인 수순, 특정 수까지 재생 |
| `src/board_svg.py` | SVG 9·13·19줄 바둑판, 실제 착수·AI 추천 테두리 |
| `src/playback.py` | 자동 진행 및 수동 이동, 백그라운드 탭에서도 1회에 최대 한 수 |
| `src/cwi_source.py` | 공식 CWI HTTPS 링크 범위 검사, 다운로드 크기·SGF 유효성 확인 |
| `src/katago_client.py` | KataGo JSON 분석 요청, 흑 기준 분석 결과, 상위 후보 |
| `src/local_settings.py` | 개인 PC 전용 엔진·모델·분석 설정 |
| `src/study_guide.py` | 16개 원문 노트의 분야 분류·제목·설명 추출 |
| `src/fast_study.py` | 추가 질문에 연관된 노트 키워드·유사 표현 검색 |
| `src/study_chat.py` | 선택 카드 + 연관 노트 + 최근 대화로 근거 제한 프롬프트 |
| `src/ollama_client.py` | 로컬 Ollama `/api/chat` 스트리밍, 선택형 임베딩 API |
| `src/rag_pipeline.py` | 기존 ChromaDB·EmbeddingGemma **선택 실험** |
| `scripts/download_cwi_samples.py` | 앱이 호출하지 않는 독립 실행형 샘플 다운로드 유틸리티 |
| `start_baduk.ps1` | Windows Private GitHub main 확인·안전 동기화·앱 시작 |

## 3. SGF와 CWI 입력 경계

- **PC 파일:** `data/sgf/`의 `.sgf` 선택 또는 직접 업로드
- **CWI 원본:** `https://homepages.cwi.nl/~aeb/go/games/games/` 범위의 직접 `.sgf` 링크만 허용
- URL은 HTTPS·호스트·경로·리다이렉트·쿼리 등을 검사하고 최대 2MB를 읽음
- Windows의 신뢰 인증서를 `truststore`로 사용하며 SSL 검증을 끄지 않음
- 파일은 `sgfmill`에서 파싱하고 9·13·19줄 바둑판만 지원
- 외부 기보의 메인 수순을 복기하는 앱으로, 전문 SGF 분기 편집기는 아님
- 직접 열어 본 CWI 기보는 Streamlit 세션 상태에 유지; 다운로드 도구를 사용하지 않는 한 `data/sgf/`에 자동 저장하지 않음

## 4. 복기와 KataGo 분석

`src/playback.advance`는 매 이동 간격이 지났을 때 **한 번에 한 수**를 진행하며 현재 UI는 **2초 고정**입니다. 수동 버튼 및 슬라이더 이동은 자동 재생을 중단합니다. 바둑판은 Streamlit fragment를 사용해 갱신합니다.

`src/katago_client.build_query(record, turn - 1, ...)`는 현재 표시한 수 N이 **두어지기 전** 국면을 요청합니다. 실제 수와 AI 1순위 제안을 주황/파랑 테두리로 구별합니다. 반환값의 `rootInfo.winrate`와 `rootInfo.scoreLead`는 `configs/analysis_local.cfg`의 **BLACK 기준** 설정을 전제로 표시합니다.

기본 제안: `~/KataGo/katago.exe`, `~/Downloads/kata1-b10c128-s1141046784-d204142634.txt.gz`, 5회 탐색. 엔진과 모델 파일은 GitHub에 포함되지 않습니다. 동일 국면·동일 설정의 분석은 Streamlit 서버 메모리로 캐시합니다. 요청은 사용자 액션 시 실행되므로 대기 시간이 발생할 수 있습니다.

SGF에 `RU`·`KM`이 없으면 분석에 사용하는 임시 기본값을 실제 대국의 규칙으로 확정할 수 없습니다. 추천 수와 실제 수가 다르다고 **승률 손실이나 악수라고 단정하지 않습니다.**

## 5. 바둑 개념 카드와 로컬 채팅

`knowledge/`의 Markdown 학습 노트 **16개**를 `rag_pipeline.load_notes`로 읽습니다. `study_guide.grouped_study_notes`가 파일명·제목을 분야별로 묶고, 사용자가 카드 하나를 누르면 `note_answer`가 원문 설명을 보여줍니다. **카드 읽기에는 ChromaDB·Ollama가 필요하지 않습니다.**

추가 질문은 카드 아래 `st.chat_input`에서 받습니다. `study_chat.build_study_chat_messages`는 선택 카드와 `fast_study.quick_answer`에서 관련성이 확인된 다른 노트(최대 2개)를 프롬프트에 넣고 최근 대화 일부를 포함합니다. 답변은 `ollama_client.chat_stream`으로 **`qwen3:1.7b`**에 전달하여 스트리밍합니다.

Ollama 기본 접속지는 **`http://127.0.0.1:11434`**입니다. 유료 외부 AI API 호출은 없지만 Ollama 설치·모델 다운로드가 필요하고 느릴 수 있습니다. LLM 프롬프트는 제공한 학습 자료 밖의 구체적 사실·실전 승률·프로기사 의도를 추측하지 말도록 제한합니다. **모델이 언제나 이를 준수하거나 정답을 보장하지는 않습니다.** 현재 채팅에 KataGo 현재 국면 데이터가 자동 제공되는 구조는 아닙니다.

## 6. 선택 보존 기능: RAG 색인

기존 학습 실험을 위해 `src/rag_pipeline.py`와 ChromaDB 관리 UI는 유지합니다.

- `embeddinggemma-2:270m` 임베딩을 로컬 Ollama에서 생성
- `data/chroma/`의 선택형 색인, **검색 색인 관리 · 선택 → 검색 자료 동기화**에서만 명시적으로 갱신
- **현재 카드 표시와 추가 질문은 이 색인을 읽지 않음**
- 이전 `build_messages`, `chat` 함수는 연구용 유틸리티로 보존되어 있으나 기본 질문 호출 경로는 `study_chat → chat_stream`

## 7. 로컬 보안과 검증

GitHub는 **Private**이며 `.gitignore`에서 SGF 다운로드, PC별 설정, ChromaDB 파일, 분석 로그와 신경망 가중치 등을 제외합니다. 원본 기보는 해당 사이트의 권리·이용 조건을 확인해야 합니다.

`tests/`는 파일 파싱·원격 URL 검증·바둑판 마커·복기·KataGo 요청·학습 카드·질문 프롬프트 등을 테스트하고, 일부 테스트는 가짜 KataGo·Ollama를 사용합니다. **Windows에서의 전체 사용자 인터페이스·외부 HTTPS·실제 엔진/모델 응답은 최신 코드 기준 미검증**입니다. 현재 상태와 다음 점검은 [개발 기록](DEVELOPMENT_LOG.md)에 정리합니다.
