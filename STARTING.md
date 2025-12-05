# Quick Start — FPL Assistant

This document shows the minimal steps to get the project running locally.

**Prerequisites**

- Neo4j Desktop (download: https://neo4j.com/download/)

**Recommended Neo4j settings**

- When creating a local Neo4j database, you can use the password `ahmedfpl` to match examples in the code.

## 1 — Download required files

- Download the FAISS indexes and helper files from the shared Drive: https://drive.google.com/drive/folders/1nyeVFgM-nb4q6_rRVhxmG5-gnQSjjBjp?usp=sharing this will take some time
- Place the downloaded files in the repository folder `embeddings_out/`.

## 2 — Create and activate a virtual environment

Run the following commands from the project root on VS code terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3 — Configure environment variables

- Copy the template `.env.template` to `.env` and add the required keys (Deepseek API key, Hugging Face token, and any other secrets).

## 4 — Populate the knowledge graph (Neo4j)

- Start Neo4j Desktop and create/launch a local database (use the password from above if you set it).
- From the project root run:

```powershell
python .\scripts\create_kg.py
```

This script will populate nodes and relationships used by the assistant using data from `scripts/fpl_two_seasons.csv`.

## 5 — Generate or load embeddings

- Generate embeddings with the project's script (4 hours):

```powershell
python .\scripts\generate_embeddings.py
```

- Alternatively, if you downloaded FAISS indexes in step 1, ensure the files are in `embeddings_out/` so the app can load them directly. (I am not sure if this will work or not, but it will save around 3.5 hours of time if it does)

## 6 — Run the app (Streamlit)

Start the Streamlit UI from the project root:

```powershell
streamlit run main.py
```

Open the address printed by Streamlit (usually `http://localhost:8501`) in your browser.

## Troubleshooting

- Neo4j connection errors: verify `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` in `.env` and that the DB is running in Neo4j Desktop.
- Missing FAISS/index load errors: confirm required files are present in `embeddings_out/` and have correct filenames.
- Dependency issues: ensure you activated the correct virtual environment and installed `requirements.txt`.

## Notes

- The repository contains helper scripts in `scripts/` and modules in `modules/` for retrieval, embedding, and the LLM engine.
- If you plan to re-generate embeddings, check `scripts/generate_embeddings.py` to review settings (model names, batch size, etc.).

If you want, I can also update `.env.template` or add a short `run-dev.ps1` script to automate the steps above.
