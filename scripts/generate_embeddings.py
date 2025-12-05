# scripts/generate_embeddings.py

import json
import os
from neo4j import GraphDatabase
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from rapidfuzz import process, fuzz
from datetime import datetime
import math

# ---------- CONFIG ----------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "ahmedfpl"

# Choose two sentence-transformer models (change to models you prefer)
MODEL_A_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # small & fast
MODEL_B_NAME = "sentence-transformers/all-mpnet-base-v2"  # larger & higher quality

OUTPUT_DIR = "./embeddings_out"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FAISS_INDEX_A_PATH = os.path.join(OUTPUT_DIR, "faiss_index_modelA.index")
FAISS_INDEX_B_PATH = os.path.join(OUTPUT_DIR, "faiss_index_modelB.index")
MAPPING_A_PATH = os.path.join(OUTPUT_DIR, "idx_to_embedding_id_modelA.json")
MAPPING_B_PATH = os.path.join(OUTPUT_DIR, "idx_to_embedding_id_modelB.json")
# ----------------------------

# Load models
model_a = SentenceTransformer(MODEL_A_NAME)
model_b = SentenceTransformer(MODEL_B_NAME)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def fetch_rows(tx):
    # Use Cypher from above: returns each player's played-in fixture instance
    q = """
    MATCH (p:Player)-[played:PLAYED_IN]->(f:Fixture)
    MATCH (f)-[:HAS_HOME_TEAM]->(home:Team)
    MATCH (f)-[:HAS_AWAY_TEAM]->(away:Team)
    OPTIONAL MATCH (p)-[:PLAYS_AS]->(pos:Position)
    OPTIONAL MATCH (f)<-[:HAS_FIXTURE]-(gw:Gameweek)-[:HAS_GW]-(s:Season)
    RETURN
      id(p) AS player_id,
      p.player_name AS player_name,
      p.player_element AS player_element,
      coalesce(pos.name, '') AS position,
      gw.GW_number AS GW,
      s.season_name AS season,
      f.kickoff_time AS kickoff_time,
      played.minutes AS minutes,
      played.goals_scored AS goals_scored,
      played.assists AS assists,
      played.total_points AS total_points,
      played.bonus AS bonus,
      played.clean_sheets AS clean_sheets,
      played.goals_conceded AS goals_conceded,
      played.own_goals AS own_goals,
      played.penalties_saved AS penalties_saved,
      played.penalties_missed AS penalties_missed,
      played.yellow_cards AS yellow_cards,
      played.red_cards AS red_cards,
      played.saves AS saves,
      played.bps AS bps,
      played.influence AS influence,
      played.creativity AS creativity,
      played.threat AS threat,
      played.ict_index AS ict_index,
      played.form AS form,
      home.name AS home_team,
      away.name AS away_team
    """
    result = tx.run(q)
    return [dict(r) for r in result]


def build_text_description(row):
    # Build a compact textual representation of the numeric features + context.
    # Only include values that are not None or NaN
    parts = []
    parts.append(f"Player: {row.get('player_name')}")
    if row.get("position"):
        parts.append(f"Position: {row.get('position')}")
    if row.get("season"):
        parts.append(f"Season: {row.get('season')}")
    if row.get("GW") is not None:
        parts.append(f"Gameweek: {row.get('GW')}")
    # numeric fields
    numeric_fields = [
        "total_points",
        "goals_scored",
        "assists",
        "minutes",
        "bonus",
        "clean_sheets",
        "goals_conceded",
        "own_goals",
        "penalties_saved",
        "penalties_missed",
        "yellow_cards",
        "red_cards",
        "saves",
        "bps",
        "influence",
        "creativity",
        "threat",
        "ict_index",
        "form",
    ]
    for f in numeric_fields:
        val = row.get(f)
        if val is None:
            continue
        # format float/truncation
        if isinstance(val, float):
            if math.isnan(val):
                continue
            val_str = f"{val:.2f}"
        else:
            val_str = str(val)
        parts.append(f"{f}: {val_str}")
    # teams
    if row.get("home_team") and row.get("away_team"):
        parts.append(f"Fixture: {row.get('home_team')} vs {row.get('away_team')}")
    return " | ".join(parts)


def upsert_embedding_node(tx, source_node_id, source_label, model_tag, vector, text):
    # Create Embedding node linked to source node (via relationship)
    q = """
    MATCH (src) WHERE id(src) = $source_node_id
    CREATE (e:Embedding {
      model: $model,
      vector: $vector,
      text: $text,
      created_at: datetime(),
      source_label: $source_label,
      source_node_id: $source_node_id
    })
    CREATE (src)-[:HAS_EMBEDDING]->(e)
    RETURN id(e) AS embedding_node_id
    """
    res = tx.run(
        q,
        model=model_tag,
        vector=list(map(float, vector)),
        text=text,
        source_label=source_label,
        source_node_id=source_node_id,
    )
    rec = res.single()
    return rec["embedding_node_id"]


def main():
    with driver.session() as session:
        rows = session.read_transaction(fetch_rows)
        print(f"Fetched {len(rows)} rows from Neo4j.")

        texts = []
        source_infos = []  # keep (source_node_id, source_label)
        for r in rows:
            text = build_text_description(r)
            texts.append(text)
            # we set source_label to "Player" here (you can generalize)
            source_infos.append((int(r["player_id"]), "Player"))

        # encode with both models
        print("Encoding with model A:", MODEL_A_NAME)
        emb_a = model_a.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        print("Encoding with model B:", MODEL_B_NAME)
        emb_b = model_b.encode(texts, convert_to_numpy=True, show_progress_bar=True)

        # Build FAISS indexes
        dim_a = emb_a.shape[1]
        dim_b = emb_b.shape[1]
        print("Model A dim:", dim_a, "Model B dim:", dim_b)

        index_a = faiss.IndexFlatIP(
            dim_a
        )  # use inner-product on normalized vectors (will normalize below)
        index_b = faiss.IndexFlatIP(dim_b)

        # normalize vectors for cosine similarity via inner product
        def normalize_rows(mat):
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return mat / norms

        emb_a_norm = normalize_rows(emb_a)
        emb_b_norm = normalize_rows(emb_b)

        # add to indexes and keep mapping
        index_a.add(emb_a_norm.astype("float32"))
        index_b.add(emb_b_norm.astype("float32"))

        # save indexes
        faiss.write_index(index_a, FAISS_INDEX_A_PATH)
        faiss.write_index(index_b, FAISS_INDEX_B_PATH)
        print("Saved FAISS indexes to disk.")

        # Persist Embedding nodes in Neo4j (we will create one embedding node per model per source)
        idx_to_embedding_id_a = {}
        idx_to_embedding_id_b = {}

        # iterate and create embedding nodes
        for i, (src_id, src_label) in enumerate(source_infos):
            text = texts[i]
            vector_a = emb_a_norm[i].tolist()
            vector_b = emb_b_norm[i].tolist()
            emb_node_id_a = session.write_transaction(
                upsert_embedding_node, src_id, src_label, "modelA", vector_a, text
            )
            emb_node_id_b = session.write_transaction(
                upsert_embedding_node, src_id, src_label, "modelB", vector_b, text
            )
            idx_to_embedding_id_a[i] = int(emb_node_id_a)
            idx_to_embedding_id_b[i] = int(emb_node_id_b)

        # Save mappings
        with open(MAPPING_A_PATH, "w") as f:
            json.dump(idx_to_embedding_id_a, f)
        with open(MAPPING_B_PATH, "w") as f:
            json.dump(idx_to_embedding_id_b, f)

        print("Saved mapping files to disk.")


if __name__ == "__main__":
    main()
