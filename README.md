# ⚽ FPL Graph-RAG Assistant

> **A Retrieval-Augmented Generation (RAG) system for intelligent Fantasy Premier League analysis using Neo4j knowledge graphs, semantic embeddings, and large language models.**

📊 **[View Full Presentation](https://docs.google.com/presentation/d/1iLP3R66Uuv8ef7xdOnurZQ_TR517fWh4z0qglueGrXw/edit?slide=id.g3b0f5e9e03f_0_29#slide=id.g3b0f5e9e03f_0_29)**

---

## 🎯 Overview

**FPL Assistant** is an intelligent conversational system that answers Fantasy Premier League questions using a **retrieval-augmented generation (RAG)** approach. Instead of hallucinating answers, the system:

1. **Classifies intent** — understands what the user is asking (e.g., player stats, comparisons)
2. **Extracts entities** — identifies relevant players, teams, gameweeks, and statistics from the query
3. **Retrieves context** — uses multiple retrieval strategies (deterministic Cypher queries, semantic vector search, or hybrid) to fetch facts from a Neo4j knowledge graph
4. **Generates answers** — passes retrieved context to a language model (DeepSeek, Llama, or Gemma) to synthesize natural, conversational responses

The system supports queries like:

- _"Compare Salah and Haaland's total points"_
- _"How many goals did Salah score against Wolves?"_
- _"Which team did Salah score the least against in the 2022-23 season?"_

### Why This Approach?

Traditional LLMs on FPL data are prone to hallucination (making up stats). RAG solves this by grounding responses in **actual data** from the knowledge graph, ensuring accuracy and factuality.

---

## ✨ Key Features

| Feature                       | Description                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| **Multi-Model LLM Support**   | DeepSeek (default), Llama, or Gemma for answer generation                                    |
| **Dual Embedding Models**     | All-MiniLM-L6-v2 (fast, small) and All-MPNet-Base-V2 (high-quality)                          |
| **Four Retrieval Strategies** | Baseline Cypher, Embeddings (Vector), Hybrid, and LLM-generated Cypher                       |
| **Fuzzy Entity Matching**     | Robust player/team name recognition despite typos and abbreviations                          |
| **Comprehensive FPL Schema**  | Covers players, teams, positions, gameweeks, seasons, and detailed performance stats         |
| **Interactive Web UI**        | Streamlit-based interface with debug mode and real-time configuration                        |
| **Evaluation Framework**      | 30 test prompts × 18 permutations = 540 experiments to benchmark retrieval + LLM performance |
| **Two Seasons of Data**       | 2021-22 and 2022-23 FPL data with player performance across all gameweeks                    |

---

## 🏗️ System Architecture

```
User Query
    ↓
┌─────────────────────────────────────────────────┐
│  PREPROCESSING & UNDERSTANDING                  │
│  • Intent Classification (LLM or Rule-based)    │
│  • Entity Extraction (NER + Fuzzy Matching)     │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  RETRIEVAL LAYER (Multi-Strategy)               │
│  ┌─────────────────┐  ┌──────────────────┐      │
│  │ Cypher Baseline │  │ Vector Embeddings│      │
│  │  (Deterministic)│  │  (Semantic)      │      │
│  └────────┬────────┘  └────────┬─────────┘      │
│           └──────┬──────────────┘               │
│                  ↓                              │
│          Neo4j Knowledge Graph                  │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  CONTEXT ASSEMBLY                               │
│  • Combine & deduplicate results                │
│  • Format for LLM consumption                   │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  LLM ANSWER GENERATION                          │
│  • DeepSeek / Llama / Gemma                     │
│  • Grounded in retrieved facts                  │
│  • Suggest follow-up questions                  │
└─────────────────────────────────────────────────┘
    ↓
Natural, Factual Answer
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12**
- **Neo4j** (Desktop or Docker)
- **4 GB+ RAM** (for embedding models + FAISS indexes)
- **Internet connection** (for LLM API calls)

### Step 1: Clone & Setup Environment

```powershell
# Create and activate virtual environment
python -m venv .venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Credentials

Create a `.env` file in the project root:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your_password>

# LLM API Keys
DEEPSEEK_API_KEY=<your_deepseek_key>
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat

HF_TOKEN=<your_huggingface_token>

# Embedding Models
MODEL_A_NAME=sentence-transformers/all-MiniLM-L6-v2
MODEL_B_NAME=sentence-transformers/all-mpnet-base-v2

# FAISS Index Paths
FAISS_INDEX_A_PATH=./embeddings_out/faiss_index_modelA.index
FAISS_INDEX_B_PATH=./embeddings_out/faiss_index_modelB.index
MAPPING_A_PATH=./embeddings_out/idx_to_embedding_id_modelA.json
MAPPING_B_PATH=./embeddings_out/idx_to_embedding_id_modelB.json

# Output Directory
OUTPUT_DIR=./embeddings_out
```

### Step 3: Populate Neo4j Knowledge Graph using `fpl_two_seasons.csv`

```powershell
# Start Neo4j Desktop and create/launch a local database

# Run the knowledge graph creation script
python .\scripts\create_kg.py
```

This populates Neo4j with:

- **Seasons**: 2021-22, 2022-23
- **Players**: ~600 per season
- **Teams**: 20 Premier League teams
- **Fixtures**: 380 per season (38 gameweeks × 20 teams)
- **Performance Data**: Goals, assists, clean sheets, total points, etc.

### Step 4: Load/Generate Embeddings

#### Option A: Download Pre-computed Indexes (⚡ Fastest)

Download FAISS indexes and mappings from: [Google Drive Link](https://drive.google.com/drive/folders/1nyeVFgM-nb4q6_rRVhxmG5-gnQSjjBjp?usp=sharing)

Place files in `embeddings_out/`:

```
embeddings_out/
├── faiss_index_modelA.index
├── faiss_index_modelB.index
├── idx_to_embedding_id_modelA.json
└── idx_to_embedding_id_modelB.json
```

#### Option B: Generate From Scratch (⏱️ ~4 hours on CPU)

```powershell
python .\scripts\generate_embeddings.py
```

This script:

1. Fetches all player performance records from Neo4j
2. Generates text descriptions (e.g., "Haaland: 13 goals | assists: 1 | total_points: 10 | Position: FWD")
3. Encodes them using both embedding models
4. Creates FAISS indexes for fast similarity search

### Step 5: Run the Web UI

```powershell
streamlit run main.py
```

Open **http://localhost:8501** in your browser.

---

## 📂 Project Structure

```
fpl-assistant/
├── main.py                           # Streamlit web UI entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── STARTING.md                       # Minimal setup guide
├── schema.md                         # Data schema documentation
├── checklist.md                      # Project development phases
├── .env.template                     # Environment variables template
│
├── config/                           # Configuration & lookup tables
│   ├── settings.py                   # Model options, defaults
│   ├── template_library.py           # 35 Cypher query templates
│   ├── team_name_variants.py         # Team abbreviation → full name
│   ├── stat_variants.py              # Statistic name aliases
│   ├── styles.py                     # Streamlit CSS styling
│   └── FPLTrivia.md                  # Possible user queries
│
├── modules/                          # Core application logic
│   ├── preprocessing.py              # Intent classification + entity extraction
│   ├── cypher_retriever.py           # Baseline retrieval via Cypher
│   ├── vector_retriever.py           # Semantic retrieval via embeddings
│   ├── db_manager.py                 # Neo4j connection pool
│   ├── llm_engine.py                 # LLM API calls (DeepSeek, Llama, Gemma)
│   ├── llm_helper.py                 # Intent classification & Cypher Generator with LLM
│   └── tests_llm_engine.py           # `llm_engine.py` customized for performance testing
│
├── scripts/                          # Data processing & setup
│   ├── create_kg.py                  # Populate Neo4j from CSV
│   ├── generate_embeddings.py        # Create FAISS indexes
│   ├── fpl_two_seasons.csv           # Raw FPL data (2 seasons)
│   └── config.txt                    # Neo4j connection configuration
│
├── embeddings_out/                   # Pre-computed embeddings
│   ├── faiss_index_modelA.index      # Fast index for model A
│   ├── faiss_index_modelB.index      # Fast index for model B
│   ├── idx_to_embedding_id_modelA.json
│   └── idx_to_embedding_id_modelB.json
│
├── experiments/                      # Evaluation framework
│   ├── run_experiments.py            # Execute all experiments
│   ├── tests.json                    # 30 test prompts
│   ├── results.json                  # Experimental results (540 trials)
│   ├── validate_tests.json           # Ground truth answers
│   ├── cost_modify.py                # Calculate LLM costs
│   ├── viz.py                        # Visualize results using plots
│   └── plots/                        # Generated charts
│
└── logo.png                          # App logo
```

---

## 📚 Module Documentation

### 1. **preprocessing.py** — Intent & Entity Extraction

Converts raw user text into structured data.

**Key Functions:**

- `extract_entities(query: str) → dict` — Extracts players, teams, positions, gameweeks, seasons, stats

**Features:**

- **Spacy NER** for organization recognition (team names)
- **Fuzzy matching** to handle typos and partial names
- **Regex patterns** for gameweeks (e.g., "GW10"), positions, seasons
- **Database lookups** for robustness

**Example:**

```python
query = "How many goals did Haaland score in GW5 2022-23?"
entities = extract_entities(query)
# Output:
# {
#   "players": ["Erling Haaland"],
#   "gameweeks": [5],
#   "seasons": ["2022-23"],
#   "statistics": []
# }
```

### 2. **cypher_retriever.py** — Baseline Deterministic Retrieval

Executes templated Cypher queries against Neo4j.

**Key Functions:**

- `retrieve_data_via_cypher(intent, entities, limit) → dict` — Executes a Cypher template selected by intent

**Template Examples:**

- `PLAYER_STATS_GW_SEASON` — Get a player's stats in a specific gameweek
- `COMPARE_PLAYERS_BY_TOTAL_POINTS` — Compare two players' total points
- `PLAYER_CAREER_STATS_TOTALS` — Career aggregates
- `TOP_PLAYERS_BY_POSITION` — Rank players by position
- `TEAM_FIXTURE_SCHEDULE` — Get team's upcoming/past fixtures

**Features:**

- Parameter injection safety (parameterized + template rendering)
- Missing parameter detection with fallbacks
- JSON-friendly output

### 3. **vector_retriever.py** — Semantic Embedding-Based Retrieval

Finds players/fixtures using semantic similarity via embeddings.

**Key Functions:**

- `vector_search(entities, top_k, model_choice) → dict` — Performs FAISS similarity search
- `get_models_and_indexes()` → Cached loading of models + FAISS indexes

**Process:**

1. Build query text from entities (e.g., "Players: Haaland | Positions: FWD")
2. Encode query using SentenceTransformer
3. Query FAISS index for top-k similar embeddings
4. Fetch source nodes from Neo4j

**Embedding Models:**

- **Model A**: `all-MiniLM-L6-v2` (22M params, fast)
- **Model B**: `all-mpnet-base-v2` (109M params, high-quality)

### 4. **db_manager.py** — Neo4j Connection Management

Singleton pattern for safe, pooled Neo4j access.

```python
db = Neo4jGraph()  # Singleton
results = db.execute_query("MATCH (p:Player) RETURN p LIMIT 5")
```

### 5. **llm_engine.py** — Multi-Model LLM Answer Generation

Interfaces with multiple LLM providers.

**Supported Models:**

- **DeepSeek** (default, most cost-effective)
- **Llama** via Hugging Face Inference API
- **Gemma** via Hugging Face Inference API

**Functions:**

- `deepseek_generate_answer(query, context) → str`
- `llama_generate_answer(query, context) → str`
- `gemma_generate_answer(query, context) → str`

**System Prompt:**

```
You are an elite Fantasy Premier League analyst.
Answer the user's question using ONLY the data provided.
Do NOT guess or hallucinate.
Keep output concise and actionable.
Suggest a follow-up question at the end.
```

### 6. **llm_helper.py** — Intent Classification & Prompt Engineering

- High-level LLM utilities for understanding user intent.
- Generating cypher queries.

**Functions:**

- `classify_with_deepseek(query, options) → list` — Map query to up to 3 Cypher templates
- Fallback: `local_intent_classify(query)` (rule-based, in `config/template_library.py`)
- `create_query_with_deepseek(query: str, schema) -> cypher query` - Generate a consistent query for user's query with respect to KG schema.

---

## 🗄️ Knowledge Graph Schema

### Node Types

| Node          | Properties                                 | Purpose                                  |
| ------------- | ------------------------------------------ | ---------------------------------------- |
| **Season**    | `season_name`                              | Either 2021-22 or 2022-23                |
| **Gameweek**  | `season`, `GW_number`                      | 38 gameweeks per season                  |
| **Fixture**   | `season`, `fixture_number`, `kickoff_time` | Individual matches                       |
| **Team**      | `name`                                     | 20 Premier League clubs per season       |
| **Player**    | `player_name`, `player_element`            | Individual players                       |
| **Position**  | `name`                                     | FWD, MID, DEF, GK                        |
| **Embedding** | `model`, `text`, `source_label`            | Vector embeddings of player descriptions |

### Relationships

```
- (Season) - [:HAS_GW]-> (Gameweek)
- (Gameweek) - [:HAS_FIXTURE]-> (Fixture)
- (Fixture) - [:HAS_HOME_TEAM]-> (Team)
- (Fixture) - [:HAS_AWAY_TEAM]-> (Team)
- (Player) - [:PLAYS_AS]-> (Position)
- (Player) - [:PLAYED_IN]-> (Fixture)
```

### Performance Stats on `PLAYED_IN` Relationships

```
minutes, goals_scored, assists, total_points, bonus,
clean_sheets, goals_conceded, own_goals, yellow_cards,
red_cards, saves, penalties_saved, penalties_missed,
bps, influence, creativity, threat, ict_index, form
```

---

## 🔍 Retrieval Methods

The system supports **four retrieval strategies**, configurable from the UI sidebar:

### 1. **Baseline (Cypher)** — Deterministic Graph Queries

**When to use:** High-precision factual queries (stats, comparisons)

**Process:**

1. Classify intent (e.g., "PLAYER_STATS_GW_SEASON")
2. Map entities to template parameters
3. Execute Cypher query
4. Return structured results

**Pros:** Deterministic, precise, low latency  
**Cons:** Requires exact entity matching; limited flexibility

### 2. **Embeddings (Vector)** — Semantic Similarity Search

**When to use:** Exploratory queries, fuzzy matching (e.g., "players similar to Salah")

**Process:**

1. Encode query + entities as a text vector
2. Query FAISS index for top-k similar embeddings
3. Fetch corresponding nodes from Neo4j
4. Return ranked results

**Pros:** Robust to phrasing differences, discovers similar items  
**Cons:** Less precise; slower than Cypher; not practically useful for the FPL Knowledge Graph

### 3. **Hybrid** — Best of Both Worlds

**When to use:** Balance precision + recall

**Process:**

1. Run Cypher retrieval
2. Run embedding search in parallel
3. Combine results, deduplicate, rank by relevance

**Pros:** High recall + precision  
**Cons:** Slower (executes both retrievers)

### 4. **LLM-Generated Cypher** — Let the Model Write Queries

**When to use:** Complex, unconventional questions

**Process:**

1. Prompt DeepSeek to generate Cypher queries
2. Execute against Neo4j
3. Return results

**Pros:** Flexibility for novel queries  
**Cons:** Can generate invalid Cypher; slower; major cybersecurity threat

---

## 🤖 LLM Comparison

| Model           | Provider     | Speed   | Quality    | Cost     |
| --------------- | ------------ | ------- | ---------- | -------- |
| **DeepSeek**    | Deepseek API | ⚡ Fast | ⭐⭐⭐⭐   | 💰 Cheap |
| **Llama 2 70B** | Hugging Face | 🐢 Slow | ⭐⭐⭐⭐⭐ | 💰💰     |
| **Gemma 7B**    | Hugging Face | ⚡ Fast | ⭐⭐⭐     | 💰 Cheap |

---

## 📊 Experiments & Evaluation

### Evaluation Framework

The project includes a comprehensive **evaluation suite** with:

- **30 test prompts** across different query types
- **18 permutations** per prompt (different retrieval modes × LLM models × embedding models)
- **540 total experiments** to benchmark performance

### Running Experiments

```powershell
python -m experiments.run_experiments
```

**Outputs:**

- `experiments/results.json` — Detailed results for each trial
- `experiments/plots/` — Generated visualizations
- Summary metrics: latency, token usage, cost analysis

### Test Prompt Categories

1. **Player Performance** — Stats, comparisons, rankings
2. **Team Analysis** — Fixture difficulty, form
3. **Transfer Advice** — Form
4. **Comparisons** — Head-to-head player metrics
5. **Recommendations** — Top performers by position

---

## 🎨 UI Features

### Streamlit Interface

```
┌────────────────────────────────────────────────────┐
│  FPL Graph-RAG Assistant                           │
│  Ask questions about Fantasy Premier League        │
├─────────────────────┬──────────────────────────────┤
│  SIDEBAR            │  MAIN CONTENT                │
│  ├─ LLM Choice      │  • Chat input                │
│  ├─ Retrieval       │  • Answer                    │
│  ├─ Embedding model │  • Graph visualization       │
│  ├─ Top-K           │  • Raw retrieval context     │
│  └─ PL Logo         │  • Debug & Transparency      │
│                     │  • Chat history              │
└─────────────────────┴──────────────────────────────┘
```

### Color Palette (Official PL Colors)

| Color                                                                    | RGB                  | Use                 |
| ------------------------------------------------------------------------ | -------------------- | ------------------- |
| <span style="color:rgb(4, 245, 255); font-weight:bold;">● Cyan</span>    | `rgb(4, 245, 255)`   | Highlights, accents |
| <span style="color:rgb(233, 0, 82); font-weight:bold;">● Pink</span>     | `rgb(233, 0, 82)`    | Warnings, important |
| <span style="color:rgb(0, 255, 133); font-weight:bold;">● Green</span>   | `rgb(0, 255, 133)`   | Success, positive   |
| <span style="color:rgb(56, 0, 60); font-weight:bold;">● Purple</span>    | `rgb(56, 0, 60)`     | Background, muted   |
| <span style="color:rgb(255, 255, 255); font-weight:bold;">● White</span> | `rgb(255, 255, 255)` | Text, primary       |

---

## 🤝 Team & Contributing

This project was developed as part of **Advanced Computer Lab Milestone 3 course work** on AI tools at The German University in Cairo, CSEN 903.

### Key Components Built By

- **Graph Architecture** — Neo4j schema design, Cypher templates
- **Preprocessing** — Intent classification, fuzzy entity extraction
- **Retrieval Layer** — Cypher baseline, FAISS embeddings, hybrid approach
- **LLM Integration** — Multi-model support, prompt engineering
- **Evaluation** — Comprehensive benchmark suite with 540 trials

### Future Work

- [ ] Add `value`, `selected_by`, `transfer_balance` for actual FPL transfers recommendations
- [ ] Add KG relations between Players & Teams
- [ ] Optimize FAISS indexes for faster search
- [ ] Add more LLM providers (Claude, GPT-4)
- [ ] Cache common queries for faster responses
- [ ] Implement streaming responses for long answers
- [ ] Add user feedback loop for fine-tuning (PPO)

---

## 📄 License

This project is for educational purposes as part of ACL coursework.

---
