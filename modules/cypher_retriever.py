# modules/cypher_retriever.py

"""
Cypher Retriever Module
-----------------------

This module implements the Baseline Retrieval Layer (Experiment A) for the
FPL Graph-RAG system.

It selects Cypher templates based on:
- Intent query (already classified using LLM or local rules)
- Entities extracted by preprocessing (player names, teams, GW, etc.)

It returns JSON-friendly results for use by the LLM.

"""

from typing import Dict, Any
from modules.db_manager import Neo4jGraph
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
        dict: Results + metadata (safe for LLM)
    """

    # Pick the template for this intent
    cypher = CYPHER_TEMPLATE_LIBRARY[intent]

    player = safe_get(entities, "players", 0)
    player1 = safe_get(entities, "players", 0)
    player2 = safe_get(entities, "players", 1)

    team = safe_get(entities, "teams", 0)
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
        "player": player,
        "player1": player1,
        "player2": player2,
        "team": team,
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
    if missing:
        return {
            "intent": intent,
            "template_used": intent,
            "cypher_query": cypher,
            "parameters": params,
            "results": [],
            "error": f"Missing required parameters for template: {missing}",
        }

    raw_results = db.execute_query(cypher, params)

    return {
        "intent": intent,
        "template_used": intent,
        "cypher_query": cypher,
        "parameters": params,
        "results": raw_results,
    }
