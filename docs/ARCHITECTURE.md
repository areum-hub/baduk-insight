# Architecture and roadmap

## Phase 1 — SGF viewer (prototype)

- SGF files from the CWI professional Go archive (initial target: 3 games)
- Parse the main variation using sgfmill
- Replay captures and passes; display 19x19 Go board
- Local Streamlit UI

## Phase 2 — KataGo (planned)

- Call KataGo analysis engine for selected moves
- Cache evaluations by position, rules, komi, engine/network version, and visits
- Show AI candidate moves, variations, win rate and estimated score
- Do not infer professional players' internal thoughts as facts

## Phase 3 — RAG (planned)

- Curate 20–30 learning notes about joseki, shape, life-and-death, thickness, sente and yose
- Use EmbeddingGemma 2 to embed **explanatory text**, not the raw SGF tree
- Retrieve from ChromaDB and provide citations
- Combine retrieved concepts with real KataGo output for a Korean language tutor

## Phase 4 — Personal learning (planned)

- SQLite bookmarks and study notes
- Review history of recurring tactical and conceptual gaps

## Data

SGF source: https://homepages.cwi.nl/~aeb/go/games/games/

Third-party annotations can carry separate rights from raw game records.
