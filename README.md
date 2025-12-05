# FPL Graph-RAG — Project README

This repository contains an experimental Retrieval-Augmented Generation (RAG) assistant for Fantasy Premier League (FPL). The app combines a Neo4j graph knowledge base, template-based Cypher retrieval, semantic vector search (embeddings + FAISS), and a small LLM-driven orchestration layer to answer user questions about players, fixtures, comparisons, and transfer recommendations.

This README documents the repo layout, how to set up the project locally (Windows / PowerShell), runtime expectations, module responsibilities, and common troubleshooting steps for teammates.

**Quick summary**: run the Streamlit UI with `streamlit run main.py` after installing dependencies and providing the required environment variables and data files (Neo4j DB, precomputed FAISS indexes, and optional Deepseek API keys).

**Project status & notes**

- The UI (`main.py`) includes a placeholder mode that activates when the `modules` package fails to import due to missing credentials/assets. This is deliberate for iterative development.
- Some modules perform heavy initialization at import time (Neo4j driver, embedding models, FAISS indexes). See "Runtime & initialization" and "Developer notes" for recommendations to make imports safer (lazy init).

**Repository layout (important files)**

- `main.py` — Streamlit application entrypoint and UI wiring.
- `requirements.txt` — Python dependencies (install with `pip install -r requirements.txt`).
- `config/` — Configuration constants and the Cypher template library.
  - `config/settings.py` — global constants (model options, Neo4j defaults, paths).
  - `config/template_library.py` — Cypher templates used by the baseline retriever.
- `modules/` — Core implementation pieces (each module documented below):
  - `modules/db_manager.py` — Neo4j driver singleton and `execute_query` helper.
  - `modules/preprocessing.py` — intent fallback rules, entity extraction, fuzzy matching.
  - `modules/cypher_retriever.py` — builds Cypher params, picks templates and returns DB results.
  - `modules/vector_retriever.py` — encodes queries, runs FAISS search, and fetches source nodes from Neo4j.
  - `modules/llm_helper.py` — thin HTTP client to Deepseek chat (classification + answer generation).
  - `modules/__init__.py` — package-level imports (note: currently imports submodules eagerly).
- `scripts/` — helper scripts for dataset/embedding generation (e.g., `generate_embeddings.py`).
- `embeddings_out/` — expected location for FAISS indexes and mapping files (modelA/modelB index files and mappings).

## Getting started (Windows PowerShell)

1. Create and activate a Python environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Provide environment variables.
   - Create a `.env` file in the `project/` root (or set the variables system-wide). Example variables used across modules:

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
DEEPSEEK_API_KEY=...
DEEPSEEK_API_URL=https://api.deepseek.example/v1/chat
EMBEDDING_MODEL=A  # or B — controls which precomputed FAISS index to load
```

4. Ensure Neo4j is running and populated with the expected schema and nodes. The modules expect node labels and properties such as `Player.player_name`, `Team.name`, `Embedding` nodes for vector sources, and `Gameweek` nodes.

5. Populate `embeddings_out/` with FAISS index files and mapping JSON files. The `vector_retriever.py` currently expects:

```
embeddings_out/faiss_index_modelA.index
embeddings_out/faiss_index_modelB.index
embeddings_out/idx_to_embedding_id_modelA.json
embeddings_out/idx_to_embedding_id_modelB.json
```

You can generate these using the `scripts/generate_embeddings.py` script (see script for usage). Generating embeddings may require large models and GPU if you want reasonable speed.

6. Run the app (PowerShell):

```powershell
streamlit run main.py
```

## High-level architecture

- UI (`main.py`) receives a user query.
- Intent classification: tries `classify_with_deepseek` (remote LLM). On failure it falls back to `local_intent_classify` in `config/template_library.py`.
- Entities are extracted with `preprocessing.extract_entities` (fuzzy matching uses DB lookups).
- Retrieval options:
  - Baseline (Cypher): `cypher_retriever.retrieve_data_via_cypher(intent, entities, limit)` builds params and runs Cypher.
  - Embeddings (Vector): `vector_retriever.vector_search(entities, top_k)` encodes the query and queries FAISS, then fetches sources from Neo4j.
  - Hybrid: both are run and combined.
- The assembled context is passed to `llm_helper.generate_answer` which calls the Deepseek chat API and returns a response.

## Module responsibilities & important details

- `modules/db_manager.py`:

  - Implements a `Neo4jGraph` singleton that initializes the Neo4j driver in `__new__` and exposes `execute_query(query, params)` that returns a list of dicts.
  - Note: current design instantiates a global `neo4j_graph = Neo4jGraph()` at module import time — this will raise if env vars are missing.

- `modules/preprocessing.py`:

  - Extracts players, teams, positions, seasons, gameweeks and statistics using spaCy + regex + fuzzy matching.
  - Calls `fetch_all_names_from_db` (which uses `Neo4jGraph`) to fetch valid names for fuzzy matching.

- `modules/cypher_retriever.py`:

  - Selects a Cypher template from `config.template_library.CYPHER_TEMPLATE_LIBRARY` using the `intent` key and fills params.
  - Returns a JSON-friendly payload including `intent`, `template_used`, `parameters` and `results`.
  - Important: if an `intent` key is missing from the template library the module will currently raise a KeyError — this can be made defensive.

- `modules/vector_retriever.py`:

  - Loads a `SentenceTransformer` model and a FAISS index and mapping at import time (based on `EMBEDDING_MODEL` env var).
  - Encodes a constructed query text and runs FAISS `index.search` and then queries Neo4j for the embedding sources.
  - Heavy initialization is done at import; see the "Developer notes" section for a recommended lazy-init change to avoid import-time failures.

- `modules/llm_helper.py`:
  - Calls an external chat API (Deepseek) for both intent classification and answer generation. It expects `DEEPSEEK_API_KEY` and `DEEPSEEK_API_URL` to be present in the environment.

## Runtime & initialization considerations

- Eager imports: both `modules/__init__.py` and many modules perform work at import time (driver creation, model loads, reading index files). This means a simple `import modules` in `main.py` can fail if Neo4j credentials, FAISS files, or model files are not present.
- The app (`main.py`) partially anticipates this by catching `ModuleNotFoundError` during `from modules import ...` and falling back to placeholder behavior. However, other exceptions (like `RuntimeError` from missing env) may also be raised during import. To improve developer experience consider:
  - Lazy initialization in `db_manager` and `vector_retriever`.
  - Converting `modules/__init__.py` to a lazy loader (so submodules are imported only when referenced).
  - Catching general import exceptions in `main.py` and surfacing clear instructions to the user.

## Troubleshooting

- If the UI shows placeholder answers and an import error message, check for:

  - Missing `.env` values (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `DEEPSEEK_API_KEY`, `DEEPSEEK_API_URL`).
  - Missing FAISS index files in `embeddings_out/`.
  - Missing Python packages (run `pip install -r requirements.txt`).
  - Neo4j not running or connection refused.

- Common fixes:
  - Ensure `.env` is present and correct.
  - If you don't need embeddings immediately, set `EMBEDDING_MODEL` to a value that won't load FAISS, or edit `modules/vector_retriever.py` to guard index loading.
  - For API-related failures, inspect the raw HTTP error returned by `modules/llm_helper.py`.

## Developer notes & recommended fixes

1. Make `modules/__init__.py` lazy to avoid eager submodule imports. Example implementation:

```python
__all__ = ["db_manager", "preprocessing", "cypher_retriever", "vector_retriever"]

def __getattr__(name):
		if name in __all__:
				import importlib
				mod = importlib.import_module(f"{__name__}.{name}")
				globals()[name] = mod
				return mod
		raise AttributeError(name)
```

2. In `modules/db_manager.py` consider removing the global instantiation `neo4j_graph = Neo4jGraph()` at module import time. Instead let callers instantiate `Neo4jGraph()` when needed or provide a `get_instance()` factory that initializes lazily.

3. In `modules/vector_retriever.py` move heavy loads (SentenceTransformer, faiss.read_index, mapping loads) into an `_ensure_initialized()` function called on first `vector_search` invocation.

4. Make `cypher_retriever.retrieve_data_via_cypher` defensive when the provided `intent` is not present in `CYPHER_TEMPLATE_LIBRARY`. Use `CYPHER_TEMPLATE_LIBRARY.get(intent)` and return a helpful error payload rather than crashing.
