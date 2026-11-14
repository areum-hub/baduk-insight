# Baduk Insight — Architecture and roadmap

## Phase 1 — SGF viewer (prototype)

- CWI professional Go games, small sample set (initial target: 3 games)
- SGF mainline parsing and replay with `sgfmill`
- 19×19 board rendering in Streamlit
- Download script: `scripts/download_cwi_samples.py`

Status: code committed; real SGF download and application runtime test remain to be verified on a configured machine.

## Phase 2 — KataGo analysis integration (code added)

- KataGo JSON analysis client: `src/katago_client.py`
- Local config: `configs/analysis_local.cfg` (black winrate perspective)
- GUI: user selects move N, app analyzes position after move N-1
- Display black win rate, black score lead, top 3 candidate moves, and principal variations
- Full engine and neural network binaries are **not** included. Install separately.
- Current implementation launches one subprocess per analysis request; performance can be improved later with a persistent analysis process and memoized results.
- The current output does **not** estimate the actual professional move's win-rate loss. For that, evaluate the position after the played move under comparable search settings.
- The displayed candidate list is a recommendation from the *preceding position*, not a direct explanation of a professional player's intentions.
- KataGo supports Chinese/Japanese settings as configured. Check the original SGF rules and komi: rules mismatch can change results.
- Tests in `tests/test_katago_client.py` use simulated engine output; live engine integration has not been verified here.

Official protocol: https://github.com/lightvector/KataGo/blob/master/docs/Analysis_Engine.md

## Phase 3 — RAG study chatbot (source code added, live integration unverified)

- Local Ollama `/api/embed`: `embeddinggemma-2:270m`.
- ChromaDB persistent index in `data/chroma/`, using only `knowledge/*.md` concept notes.
- Local Ollama `/api/chat`: `qwen3:4b-instruct`, Korean conversational study assistant.
- Retrieval: embed question, select up to three related concept documents, display file-path provenance.
- Context: selected SGF turn and played move; **only** include KataGo data if the user actually ran analysis of the current exact turn with matching settings.
- Answers distinguish general principles from actual move-by-move evaluation; do not guess win rates or professionals' intentions.
- Session chat history is cleared when the SGF or move number changes; Phase 4 persistence is not yet implemented.
- Models run locally; binaries and weights are not uploaded to Git.
- `tests/test_rag_pipeline.py` tests prompts, index, embedding API contract and source labels using fakes. This is not a substitute for integration testing on the user's Windows PC.
- Initial knowledge base contains 10 original elementary Baduk concept notes, which will need expansion and expert review.

## Phase 4 — Personal learning (planned)

- Bookmarks, own questions, learning notes in SQLite
- Personalized study sessions and repeated-theme review

## Data provenance and privacy

Source: https://homepages.cwi.nl/~aeb/go/games/games/

Do not commit downloaded datasets, personal study records, or large model weights to Git. Third-party annotations may have separate rights from raw game records.

Repository visibility: Private.
