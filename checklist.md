### Phase 1: Input Preprocessing Module

**Goal:** Translate raw user text into structured data (Intents & Entities).

- [ ] **Develop Intent Classification**
  - Create a mechanism to determine what the user wants (e.g., `GetPlayerStats`, `TeamRecommendation`, `ComparePlayers`).
  - _Implementation:_ You can use rule-based keywords (easier) or an LLM-based classifier.
  - _Why:_ This determines which Cypher query to pick later.
- [ ] **Develop Entity Extraction (NER)**
  - Implement Named Entity Recognition to pull specific parameters from the query.
  - _FPL Specific Entities to extract:_ Players, Teams, Positions (e.g., "FWD"), Seasons (e.g., "2023"), Gameweeks, and Statistics (e.g., "Goals", "Assists").

### Phase 2: Graph Retrieval Layer (Experiment A - Baseline)

**Goal:** Retrieve exact facts using deterministic Cypher queries.

- [ ] **Design Cypher Query Templates**
  - Create a library of **at least 10 different Cypher query templates**.
  - Ensure these cover different intents (e.g., Player performance, Player Comparison).
  - _Example to implement:_ "Get top forwards in 2023" $\rightarrow$ Extract `Position="FWD"`, `Season="2022-23"` $\rightarrow$ Query players by position/season.
- [ ] **Implement Query Execution**
  - Write the Python logic to take the entities extracted in Phase 1 and inject them into the chosen Cypher template.
  - Execute against your Neo4j knowledge graph to get the nodes/relationships.

### Phase 3: Graph Retrieval Layer (Experiment B - Embeddings)

**Goal:** Retrieve information based on semantic similarity using vector embeddings.

- [ ] **Choose Your Embedding Strategy**
  - _Option 1 (Node Embeddings):_ Generate vectors based on graph structure/numerical stats for players.
  - _Option 2 (Feature Vector Embeddings):_ Construct text descriptions from your numerical data (e.g., "Player: Haaland, Position: FWD, Points: 200") and embed that text.
- [ ] **Experiment with Models**
  - Select and implement **at least TWO different embedding models** to compare performance.
  - _Resources:_ Use models from Hugging Face.
- [ ] **Vector Indexing**
  - Store these embeddings in a Neo4j Vector Index for fast retrieval.
  - Implement the search logic: Convert user input to a vector and find the closest nodes/features in the database.

### Phase 4: The LLM Integration Layer

**Goal:** Generate the final answer by combining Graph data with an LLM.

- [ ] **Context Merging**
  - Combine the results from **Baseline** (Cypher) and **Embeddings** (Vector Search) into a single text block.
  - Remove duplicates and rank results if necessary.
- [ ] **Prompt Engineering**
  - Construct a structured prompt with three parts:
    1.  **Context:** The data retrieved from Neo4j.
    2.  **Persona:** "You are an FPL expert/assistant".
    3.  **Task:** "Answer the user's question using only the provided information".
- [ ] **Model Comparison (The "Three Models" Rule)**
  - Integrate **at least three different LLMs** to test (DeepSeek, Llama, Gemma).
  - _Tip:_ Use Hugging Face or OpenRouter for free access to open-source models.

### Phase 5: User Interface (Streamlit)

**Goal:** Demonstrate the system to the user.

- [ ] **Basic UI Setup**
  - Build a simple input box for the user question and a display area for the answer.
- [ ] **Transparency Features (Required)**
  - **Show Context:** Display the raw nodes/data retrieved from the Graph _before_ the LLM answers (builds trust).
  - **Show Queries (Optional but Recommended):** Display the Cypher query used.
  - **Graph Viz (Optional):** Use Plotly or NetworkX to show the retrieved subgraph.
- [ ] **Controls**
  - Add a dropdown to select which LLM to use (for the comparison requirement).
  - Add a dropdown to select which embedding model to use.
  - Add a selector for Retrieval Method (Baseline only vs. Embeddings vs. Hybrid).
  - Add an input `Top_k` to limit number of nodes/indexes retrieved.

### Phase 6: Evaluation & Presentation

**Goal:** Analyze performance for the final grade.

- [ ] **Quantitative Evaluation**
  - Measure metrics for your 3 models: Accuracy, Response Time, Token Usage, Cost.
- [ ] **Qualitative Evaluation**
  - Manually review answers for relevance, naturalness, and hallucination reduction.
  - Create specific test cases (e.g., "Who is the best budget defender?") and document how each model handles it.
- [ ] **Error Analysis**
  - Document where the system fails (e.g., can't handle complex multi-gameweek queries).
- [ ] **Slides & Repo**
  - Create architecture diagrams.
  - Clean up GitHub repo, ensure it is private until the deadline.
  - Submit by **December 15th at 23:59**.

---
