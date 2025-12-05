# modules/preprocessing.py

"""
This module handles:
1. Intent classification (keyword-based)
2. Entity extraction (NER + regex)
3. Fuzzy matching entities to Neo4j node values

Author: ACL M3 FPL Graph-RAG
"""

import re
from typing import Dict, List, Optional
import spacy
from thefuzz import (
    process,
    fuzz,
)

# TODO decide on wether to keep thefuzz only or both fuzzywuzzy and thefuzz
from fuzzywuzzy import fuzz

from modules.db_manager import Neo4jGraph
from config.stat_variants import STAT_VARIANTS


# ----------------------------
# Load spaCy model once
# ----------------------------
try:
    nlp = spacy.load("en_core_web_trf")  # transformer model
except:
    nlp = spacy.load("en_core_web_sm")  # fallback


# ----------------------------
# Raw Entity Extraction
# ----------------------------


def extract_entities(user_query: str) -> Dict[str, List[str]]:
    entities = {
        "players": [],
        "teams": [],
        "gameweeks": [],
        "positions": [],
        "seasons": [],
        "statistics": [],
    }

    query_lower = user_query.lower()

    # ------------------
    # Gameweeks
    # ------------------
    gw_matches = re.findall(r"(?:gw|gameweek)\s?(\d+)", query_lower)
    if gw_matches:
        entities["gameweeks"] = [int(g) for g in gw_matches]

    # ------------------
    # Positions
    # ------------------
    position_variants = {
        "DEF": ["defender", "defenders", "defence", "backline"],
        "MID": ["midfielder", "midfielders", "midfield"],
        "FWD": ["forward", "forwards", "attacker", "striker", "strikers"],
        "GK": ["goalkeeper", "keeper", "goalies", "goalie"],
    }
    for code, variants in position_variants.items():
        for var in variants:
            if fuzz.partial_ratio(var, query_lower) >= 80:
                entities["positions"].append(code)
                break

    # ------------------
    # Teams
    # ------------------
    all_teams = fetch_all_names_from_db("Team", "name")
    # TODO team abbreviations
    # fuzz for typos
    for team in all_teams:
        if team.lower() in query_lower:
            entities["teams"].append(team)

    # ------------------
    # Players
    # ------------------
    all_players = fetch_all_names_from_db("Player", "player_name")
    matched_players = []
    for player_name in all_players:
        score = fuzz.partial_ratio(player_name.lower(), query_lower)
        if score >= 80:
            matched_players.append((player_name, score))
    matched_players.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    for name, score in matched_players:
        if name not in seen:
            entities["players"].append(name)
            seen.add(name)

    # ------------------
    # Seasons
    # ------------------
    # TODO what if input was `season 22` ? fallback is 2022-23
    season_patterns = [
        r"(2021[-/ ]?22)",
        r"(21[-/ ]?22)",
        r"(2022[-/ ]?23)",
        r"(22[-/ ]?23)",
    ]
    for pat in season_patterns:
        matches = re.findall(pat, user_query, flags=re.IGNORECASE)
        for m in matches:
            standardized = "2021-22" if "21" in m else "2022-23"
            if standardized not in entities["seasons"]:
                entities["seasons"].append(standardized)

    # ------------------
    # Statistics
    # ------------------
    for stat, variants in STAT_VARIANTS.items():
        for var in variants:
            if fuzz.partial_ratio(var.lower(), query_lower) >= 80:
                if stat not in entities["statistics"]:
                    entities["statistics"].append(stat)
                    break

    return entities


# ----------------------------
# DB Helpers: Fetch valid names
# ----------------------------


def fetch_all_names_from_db(label: str, property_name: str) -> List[str]:
    """
    Loads names from Neo4j, e.g. fetch_all_names_from_db("Player", "player_name")
    """
    query = f"""
    MATCH (n:{label})
    RETURN n.{property_name} AS name
    """

    db = Neo4jGraph()
    result = db.execute_query(query)

    return [row["name"] for row in result]
