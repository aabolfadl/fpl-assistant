# modules/cypher_retriever.py

"""
Cypher Retriever Module
-----------------------

This module implements the Baseline Retrieval Layer (Experiment A) for the
FPL Graph-RAG system.

It selects Cypher templates based on:
- Intent query (already classified using LLM or local rules)
- Entities extracted by preprocessing (player names, teams, GW, etc.)

It returns JSON-friendly results for use by the LLM, along with graph
visualization data when graph-based retrieval is used.

"""

from typing import Dict, Any
from modules.db_manager import Neo4jGraph
from modules.graph_visualizer import neo4j_to_visjs_graph
from config.template_library import CYPHER_TEMPLATE_LIBRARY, required_params_map

# Neo4j connection singleton
db = Neo4jGraph()


def safe_get(entity_dict, key, index=0):
    """Safely extract entity list values like entities[key][index]."""
    if key not in entity_dict:
        return None
    if entity_dict[key] is None:
        return None
    if not isinstance(entity_dict[key], list):
        return None
    if len(entity_dict[key]) <= index:
        return None
    return entity_dict[key][index]


def render_cypher_template(template: str, params: dict) -> str:
    # Only replace keys that must be injected (not safe as Cypher params)
    # e.g., stat_property, limit, budget
    # These cannot be parameterized in Cypher and must be string-replaced
    for key in ["stat_property", "limit", "budget"]:
        if key in params and f"${key}" in template:
            template = template.replace(f"${key}", str(params[key]))
    return template


# ---------------------------------------------------------
# Main Retrieval Function
# ---------------------------------------------------------


def retrieve_data_via_cypher(intent: str, entities: Dict[str, Any], limit: int = 5):
    """
    Entry point for Baseline Cypher Retrieval.

    Args:
        intent (str): Intent query from preprocessing
        entities (dict): Extracted entities with fuzzy-matched values from preprocessing
        limit (int): Limit count for query results

    Returns:
        dict: Results + metadata + graph visualization data (safe for LLM)
              Includes 'graph_nodes' and 'graph_edges' for visualization
    """

    # Pick the template for this intent
    cypher = CYPHER_TEMPLATE_LIBRARY[intent]

    player1 = safe_get(entities, "players", 0)
    player2 = safe_get(entities, "players", 1)

    team1 = safe_get(entities, "teams", 0)
    team2 = safe_get(entities, "teams", 1)

    position = safe_get(entities, "positions", 0)
    gw = safe_get(entities, "gameweeks", 0)
    stat_property = safe_get(entities, "statistics", 0)
    season = safe_get(entities, "seasons", 0)

    budget = entities.get("budget")[0] if entities.get("budget") else 6.0

    # Convert entities → parameters Neo4j expects
    params = {
        "limit": limit,
        "player1": player1,
        "player2": player2,
        "team1": team1,
        "team2": team2,
        "position": position,
        "gw": gw,
        "season": season,
        "budget": budget,
        "stat_property": stat_property,
    }

    # Clean None values (Neo4j dislikes null param injections)
    params = {k: v for k, v in params.items() if v is not None}

    required = required_params_map.get(intent, [])

    missing = [p for p in required if p not in params]
    # If only 'season' is required and missing, set season to '2022-23'
    if missing == ["season"]:
        params["season"] = "2022-23"
        missing = [p for p in required if p not in params]
    if missing:
        return {
            "intent": intent,
            "template_used": intent,
            "cypher_query": cypher,
            "parameters": params,
            "results": [],
            "error": f"Missing required parameters for template: {missing}",
            "graph_nodes": [],
            "graph_edges": [],
        }

    cypher = render_cypher_template(CYPHER_TEMPLATE_LIBRARY[intent], params)
    # Remove stat_property/limit/budget from params before passing to Neo4j
    # These are injected into the template and should not be passed as parameters
    params.pop("stat_property", None)
    params.pop("limit", None)
    params.pop("budget", None)

    # Execute query with graph extraction
    try:
        query_result = db.execute_query_with_graph(cypher, params)
        raw_results = query_result.get("results", [])
        neo4j_nodes = query_result.get("nodes", [])
        neo4j_edges = query_result.get("edges", [])
    except Exception as e:
        # If execute_query_with_graph fails, fall back to regular execution
        raw_results = db.execute_query(cypher, params)
        neo4j_nodes = []
        neo4j_edges = []

    # Convert Neo4j nodes/edges to vis.js format
    vis_nodes, vis_edges = neo4j_to_visjs_graph(neo4j_nodes, neo4j_edges)

    return {
        "intent": intent,
        "template_used": intent,
        "cypher_query": cypher,
        "parameters": params,
        "results": raw_results,
        "graph_nodes": vis_nodes,
        "graph_edges": vis_edges,
    }
