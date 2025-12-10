# FPL Graph-RAG — Project README

This repository contains an experimental Retrieval-Augmented Generation (RAG) assistant for Fantasy Premier League (FPL). The app combines a Neo4j graph knowledge base, template-based Cypher retrieval, semantic vector search (embeddings + FAISS), and a small LLM-driven orchestration layer to answer user questions about players, fixtures, comparisons, and transfer recommendations.

This README documents the repo layout, how to set up the project locally (Windows / PowerShell), runtime expectations, module responsibilities, and common troubleshooting steps for teammates.

1. Create and activate a Python environment (recommended):

```powershell
python -m venv .venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Provide environment variables.

   - Create a `.env` file in the root (Find a template in `.env.template`)

4. Ensure Neo4j is running and populated with the expected schema and nodes.

5. Populate `embeddings_out/` with FAISS index files and mapping JSON files from `https://drive.google.com/drive/folders/1nyeVFgM-nb4q6_rRVhxmG5-gnQSjjBjp?usp=sharing`. The `vector_retriever.py` currently expects:

```
embeddings_out/faiss_index_modelA.index
embeddings_out/faiss_index_modelB.index
embeddings_out/idx_to_embedding_id_modelA.json
embeddings_out/idx_to_embedding_id_modelB.json
```

You can generate these using the `scripts/generate_embeddings.py` script. Generating embeddings requires 4 hours (CPU).

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
- The assembled context is passed to `llm_helper.generate_answer` which calls the Deepseek/Gemma/Llama API and returns a response.

## Premier league color pallette:

- Cyan: rgb(4, 245, 255)
- Pink: rgb(233, 0, 82)
- White: rgb(255, 255, 255)
- Green: rgb(0, 255, 133)
- Purple: rgb(56, 0, 60)
