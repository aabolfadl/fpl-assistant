# modules/vector_retriever.py


import os
import json
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
import streamlit as st
from modules.graph_visualizer import neo4j_to_visjs_graph

# Load .env DO NOT REMOVE THIS because settings.py is not imported here
load_dotenv()

# =======================
# CONFIGURATION
# =======================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

MODEL_A_NAME = os.getenv("MODEL_A_NAME")
MODEL_B_NAME = os.getenv("MODEL_B_NAME")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./embeddings_out")

FAISS_INDEX_A_PATH = os.getenv("FAISS_INDEX_A_PATH")
FAISS_INDEX_B_PATH = os.getenv("FAISS_INDEX_B_PATH")

MAPPING_A_PATH = os.getenv("MAPPING_A_PATH")
MAPPING_B_PATH = os.getenv("MAPPING_B_PATH")


@st.cache_resource(show_spinner=False)
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


driver = get_driver()


# =======================
# LOAD MODELS + INDEXES
# =======================


@st.cache_resource(show_spinner=False)
def get_models_and_indexes():
    print("Loading SentenceTransformer models and FAISS indexes into memory...")
    model_A = SentenceTransformer(MODEL_A_NAME)
    model_B = SentenceTransformer(MODEL_B_NAME)
    index_A = faiss.read_index(FAISS_INDEX_A_PATH)
    index_B = faiss.read_index(FAISS_INDEX_B_PATH)
    with open(MAPPING_A_PATH, "r") as f:
        mapping_A = json.load(f)
    with open(MAPPING_B_PATH, "r") as f:
        mapping_B = json.load(f)
    print("All embedding models and indexes loaded successfully.")
    return model_A, model_B, index_A, index_B, mapping_A, mapping_B


model_A, model_B, index_A, index_B, mapping_A, mapping_B = get_models_and_indexes()


# =========================
# HELPER FUNCTIONS
# =========================


def _build_query_text(entities: dict) -> str:
    parts = []

    if entities.get("players"):
        parts.append("Players: " + ", ".join(entities["players"]))

    if entities.get("teams"):
        parts.append("Teams: " + ", ".join(entities["teams"]))

    if entities.get("positions"):
        parts.append("Positions: " + ", ".join(entities["positions"]))

    if entities.get("seasons"):
        parts.append("Seasons: " + ", ".join(entities["seasons"]))

    if entities.get("gameweeks"):
        parts.append("Gameweeks: " + ", ".join(str(g) for g in entities["gameweeks"]))

    if entities.get("statistics"):
        parts.append("Statistics: " + ", ".join(entities["statistics"]))

    if not parts:
        return entities.get("raw", "")

    return " | ".join(parts)


def _fetch_sources(tx, embedding_node_ids):
    q = """
    UNWIND $embedding_ids AS eid
    MATCH (e:Embedding) WHERE id(e) = eid
    OPTIONAL MATCH (src)-[:HAS_EMBEDDING]->(e)
    RETURN
        id(e) AS embedding_id,
        e.model AS model,
        e.text AS text,
        id(src) AS source_node_id,
        e.source_label AS source_label,
        src.player_name AS player_name
    """
    res = tx.run(q, embedding_ids=embedding_node_ids)
    return [dict(r) for r in res]


def _fetch_graph(tx, embedding_ids):
    q = """
    UNWIND $embedding_ids AS eid
    MATCH (e:Embedding) WHERE id(e) = eid
    MATCH (e)-[r]-(p:Player)
    RETURN
        collect(DISTINCT e) AS source_nodes,
        collect(DISTINCT p) AS neighbor_nodes,
        collect(DISTINCT r) AS edges
    """
    res = tx.run(q, embedding_ids=embedding_ids).single()

    if not res:
        return [], []

    raw_nodes = [
        n for n in (res["source_nodes"] + res["neighbor_nodes"]) if n is not None
    ]
    raw_edges = [e for e in res["edges"] if e is not None]

    # Convert Neo4j node objects to dictionaries
    nodes = []
    for node in raw_nodes:
        node_dict = dict(node)
        node_dict["id"] = id(node)  # Use Neo4j internal node id
        nodes.append(node_dict)

    # Convert Neo4j relationship objects to dictionaries
    edges = []
    for rel in raw_edges:
        edge_dict = {
            "start_node_id": id(rel.start_node),
            "end_node_id": id(rel.end_node),
            "type": rel.type,
        }
        # Include relationship properties
        edge_dict.update(dict(rel))
        edges.append(edge_dict)

    print(f"Fetched {len(nodes)} nodes and {len(edges)} edges from Neo4j.")

    return nodes, edges


# =========================
# MAIN VECTOR SEARCH API
# =========================


def vector_search(entities: dict, top_k: int = 5, model_choice: str = "A") -> dict:
    """
    model_choice: "A" or "B"
    """

    model_choice = model_choice.upper()

    if model_choice == "A":
        model = model_A
        index = index_A
        mapping = mapping_A
    elif model_choice == "B":
        model = model_B
        index = index_B
        mapping = mapping_B
    else:
        raise ValueError("model_choice must be 'A' or 'B'.")

    # -------- 1. Build query text --------
    query_text = _build_query_text(entities)
    if not query_text:
        query_text = "General football query"
    print(f"Embedding using model {model_choice}: {query_text}")

    # -------- 2. Encode --------
    emb = model.encode([query_text], convert_to_numpy=True)
    emb_norm = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    # -------- 3. Vector similarity search --------
    distances, indices = index.search(emb_norm.astype("float32"), top_k)

    hits = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        emb_node_id = mapping.get(str(int(idx)))
        hits.append(
            {
                "faiss_index": int(idx),
                "distance": float(dist),
                "embedding_node_id": int(emb_node_id),
            }
        )

    embedding_ids = list({h["embedding_node_id"] for h in hits})

    with driver.session() as session:
        sources = session.read_transaction(_fetch_sources, embedding_ids)

        print("Number of embedding_ids:", len(embedding_ids))

        neo4j_nodes, neo4j_edges = session.read_transaction(_fetch_graph, embedding_ids)

    vis_nodes, vis_edges = neo4j_to_visjs_graph(neo4j_nodes, neo4j_edges)

    return {
        "query_text": query_text,
        "model_used": model_choice,
        "hits": hits,
        "sources": sources,
        "graph_nodes": vis_nodes,
        "graph_edges": vis_edges,
    }
