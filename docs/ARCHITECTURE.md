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

## Phase 3 — RAG (planned)

- Curate 20–30 explanatory notes on joseki, tesuji, shape, life-and-death, thickness, sente and yose
- Use EmbeddingGemma 2 on explanatory text, not raw SGF tree
- ChromaDB similarity search with source citations
- Feed both the verified KataGo response and retrieved notes to a Korean-language LLM
- Avoid attributing AI-derived interpretations to the professional player without an actual source

## Phase 4 — Personal learning (planned)

- Bookmarks, own questions, learning notes in SQLite
- Personalized study sessions and repeated-theme review

## Data provenance and privacy

Source: https://homepages.cwi.nl/~aeb/go/games/games/

Do not commit downloaded datasets, personal study records, or large model weights to Git. Third-party annotations may have separate rights from raw game records.

Repository visibility: Private.
