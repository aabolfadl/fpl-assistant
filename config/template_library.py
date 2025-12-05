# config/template_library.py

"""
Cypher Template Library
----------------------

Contains all Cypher query templates and intent → template mapping rules
for the FPL Graph-RAG system.
"""

# ---------------------------------------------------------
# 30 Cypher Templates (Extended Retrieval Library)
# ---------------------------------------------------------

CYPHER_TEMPLATE_LIBRARY = {
    # -----------------------------------------------------
    # 1. Player Performance & Statistics (General/Historical)
    # -----------------------------------------------------
    "PLAYER_RECENT_STATS": """
    MATCH (p:Player {player_name: $player})-[r:PLAYED_IN]->(f:Fixture)
    OPTIONAL MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
    RETURN p.player_name AS player,
           gw.season AS season,
           gw.GW_number AS gw,
           r.total_points AS total_points,
           r.goals_scored AS goals_scored,
           r.assists AS assists,
           r.minutes AS minutes,
           r.bonus AS bonus
    ORDER BY season DESC, gw DESC
    LIMIT $limit
    """,
    "PLAYER_STATS_GW": """
    MATCH (p:Player {player_name: $player})
          -[r:PLAYED_IN]->
          (f:Fixture)<-[:HAS_FIXTURE]- (gw:Gameweek {GW_number: $gw})
    RETURN p.player_name AS player,
           gw.season AS season,
           gw.GW_number AS gw,
           r.*
    """,
    "COMPARE_PLAYERS": """
    MATCH (p1:Player {player_name: $player1})
    OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
    WITH p1, coalesce(sum(r1.total_points), 0) AS p1_pts
    MATCH (p2:Player {player_name: $player2})
    OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
    RETURN
        p1.player_name AS player1,
        p1_pts AS player1_points,
        p2.player_name AS player2,
        coalesce(sum(r2.total_points), 0) AS player2_points
    """,
    "PLAYER_CAREER_TOTALS": """
    MATCH (p:Player {player_name: $player})-[r:PLAYED_IN]->(:Fixture)
    RETURN p.player_name AS player,
           sum(r.total_points) AS total_points,
           sum(r.goals_scored) AS career_goals,
           sum(r.assists) AS career_assists,
           sum(r.clean_sheets) AS career_clean_sheets,
           count(r) AS matches_played
    """,
    "PLAYERS_BY_STAT": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r[$stat_property]) AS total_stat
    RETURN p.player_name AS player, total_stat
    ORDER BY total_stat DESC
    LIMIT $limit
    """,
    # -----------------------------------------------------
    # 2. Top Performers & Recommendations
    # -----------------------------------------------------
    "TOP_PLAYERS_POSITION": """
    MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
    MATCH (p)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.total_points) AS total_pts
    RETURN p.player_name AS player, total_pts
    ORDER BY total_pts DESC
    LIMIT $limit
    """,
    "TOP_UNDER_BUDGET": """
    MATCH (p:Player)
    WHERE p.value <= $budget
    MATCH (p)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.total_points) AS total_pts
    RETURN p.player_name AS player,
           p.value AS value,
           total_pts
    ORDER BY total_pts DESC
    LIMIT $limit
    """,
    "CLEAN_SHEET_LEADERS": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.clean_sheets) AS cs
    RETURN p.player_name AS player, cs
    ORDER BY cs DESC
    LIMIT $limit
    """,
    "TOP_FORM": """
    // Average form over all available fixtures
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, avg(r.form) AS avg_form
    RETURN p.player_name AS player, avg_form
    ORDER BY avg_form DESC
    LIMIT $limit
    """,
    "TOP_ICT_ATTACKERS": """
    MATCH (p:Player)-[:PLAYS_AS]->(pos:Position)
    WHERE pos.name IN ['Forward', 'Midfielder']
    MATCH (p)-[r:PLAYED_IN]->(:Fixture)
    WITH p, avg(r.ict_index) AS ict
    RETURN p.player_name AS player, ict
    ORDER BY ict DESC
    LIMIT $limit
    """,
    "TOP_BONUS_POINTS": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.bonus) AS total_bonus
    RETURN p.player_name AS player, total_bonus
    ORDER BY total_bonus DESC
    LIMIT $limit
    """,
    "BEST_PENALTY_SAVERS": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.penalties_saved) AS total_saves
    RETURN p.player_name AS player, total_saves
    ORDER BY total_saves DESC
    LIMIT $limit
    """,
    # -----------------------------------------------------
    # 3. Player Disciplinary & Negative Stats
    # -----------------------------------------------------
    "DISCIPLINARY_LEADERS": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
    RETURN p.player_name AS player, yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
    ORDER BY disciplinary_score DESC
    LIMIT $limit
    """,
    "OWN_GOAL_CONTRIBUTORS": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.own_goals) AS own_goals
    RETURN p.player_name AS player, own_goals
    ORDER BY own_goals DESC
    LIMIT $limit
    """,
    "PENALTY_MISS_LEADERS": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.penalties_missed) AS penalties_missed
    RETURN p.player_name AS player, penalties_missed
    ORDER BY penalties_missed DESC
    LIMIT $limit
    """,
    # -----------------------------------------------------
    # 4. Team Analysis & Defense/Attack Strength
    # -----------------------------------------------------
    "TEAM_DEFENSE_STRENGTH": """
    // Avg Goals Conceded per Game
    MATCH (t:Team {name: $team})
    MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    WITH t, f, avg(r.goals_conceded) AS fixture_gc
    RETURN t.name AS team,
           avg(fixture_gc) AS avg_goals_conceded_per_fixture
    ORDER BY avg_goals_conceded_per_fixture ASC
    LIMIT 1
    """,
    "TEAM_ATTACK_STRENGTH": """
    // Avg Goals Scored per Game
    MATCH (t:Team {name: $team})
    MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    WITH t, f, avg(r.goals_scored) AS fixture_gs
    RETURN t.name AS team,
           avg(fixture_gs) AS avg_goals_scored_per_fixture
    ORDER BY avg_goals_scored_per_fixture DESC
    LIMIT 1
    """,
    "TEAM_TOTAL_POINTS": """
    MATCH (t:Team {name: $team})
    MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    RETURN t.name AS team,
           sum(r.total_points) AS total_fpl_points
    """,
    "TEAMS_BY_CLEAN_SHEETS": """
    MATCH (t:Team)
    MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    WITH t, sum(r.clean_sheets) AS team_clean_sheets
    RETURN t.name AS team, team_clean_sheets
    ORDER BY team_clean_sheets DESC
    LIMIT $limit
    """,
    "TEAM_PLAYERS_TOTAL_PTS": """
    MATCH (t:Team {name: $team})
    MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    WITH p, sum(r.total_points) AS total_pts
    RETURN p.player_name AS player, total_pts
    ORDER BY total_pts DESC
    """,
    # -----------------------------------------------------
    # 5. Fixture Queries
    # -----------------------------------------------------
    "TEAM_FIXTURES": """
    MATCH (t:Team {name: $team})
    MATCH (f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    OPTIONAL MATCH (f)-[:HAS_HOME_TEAM]->(homeTeam)
    OPTIONAL MATCH (f)-[:HAS_AWAY_TEAM]->(awayTeam)
    RETURN
        f.kickoff_time AS kickoff,
        homeTeam.name AS home_team,
        awayTeam.name AS away_team
    ORDER BY f.kickoff_time ASC
    LIMIT $limit
    """,
    "FIXTURES_BETWEEN_TEAMS": """
    MATCH (f:Fixture)
    MATCH (t1:Team {name: $team1})
    MATCH (t2:Team {name: $team2})
    WHERE
        ((f)-[:HAS_HOME_TEAM]->(t1) AND (f)-[:HAS_AWAY_TEAM]->(t2)) OR
        ((f)-[:HAS_HOME_TEAM]->(t2) AND (f)-[:HAS_AWAY_TEAM]->(t1))
    RETURN f.kickoff_time AS kickoff,
           t1.name AS team1,
           t2.name AS team2
    ORDER BY f.kickoff_time ASC
    """,
    "PLAYER_POINTS_VS_TEAM": """
    MATCH (p:Player {player_name: $player})-[r:PLAYED_IN]->(f:Fixture)
    MATCH (t:Team {name: $team})
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    RETURN p.player_name AS player,
           t.name AS opponent,
           sum(r.total_points) AS total_points_vs_opponent,
           count(f) AS matches_played
    """,
    "FIXTURES_FOR_GW": """
    MATCH (gw:Gameweek {GW_number: $gw})-[:HAS_FIXTURE]->(f:Fixture)
    OPTIONAL MATCH (f)-[:HAS_HOME_TEAM]->(homeTeam)
    OPTIONAL MATCH (f)-[:HAS_AWAY_TEAM]->(awayTeam)
    RETURN
        f.kickoff_time AS kickoff,
        homeTeam.name AS home_team,
        awayTeam.name AS away_team
    ORDER BY f.kickoff_time ASC
    """,
    "PLAYER_FIXTURES": """
    MATCH (p:Player {player_name: $player})-[r:PLAYED_IN]->(f:Fixture)
    OPTIONAL MATCH (f)-[:HAS_HOME_TEAM]->(homeTeam)
    OPTIONAL MATCH (f)-[:HAS_AWAY_TEAM]->(awayTeam)
    RETURN
        f.kickoff_time AS kickoff,
        homeTeam.name AS home_team,
        awayTeam.name AS away_team,
        r.total_points AS points_in_match
    ORDER BY f.kickoff_time DESC
    LIMIT $limit
    """,
    # -----------------------------------------------------
    # 6. Player Value & Minutes
    # -----------------------------------------------------
    "MOST_MINUTES_PLAYED": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.minutes) AS total_minutes
    RETURN p.player_name AS player, total_minutes
    ORDER BY total_minutes DESC
    LIMIT $limit
    """,
    "MINUTES_PER_POINT": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
    WHERE total_points > 0 AND total_minutes > 0
    RETURN p.player_name AS player,
           total_minutes / total_points AS minutes_per_point
    ORDER BY minutes_per_point ASC
    LIMIT $limit
    """,
    "TOP_VALUE_FOR_MONEY": """
    MATCH (p:Player)
    MATCH (p)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.total_points) AS total_pts
    WHERE p.value IS NOT NULL AND p.value > 0 AND total_pts > 0
    RETURN p.player_name AS player,
           total_pts / p.value AS points_per_value
    ORDER BY points_per_value DESC
    LIMIT $limit
    """,
    # -----------------------------------------------------
    # 7. Influence, Creativity, Threat (ICT)
    # -----------------------------------------------------
    "TOP_INFLUENCE": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.influence) AS total_influence
    RETURN p.player_name AS player, total_influence
    ORDER BY total_influence DESC
    LIMIT $limit
    """,
    "TOP_CREATIVITY": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.creativity) AS total_creativity
    RETURN p.player_name AS player, total_creativity
    ORDER BY total_creativity DESC
    LIMIT $limit
    """,
    "TOP_THREAT": """
    MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
    WITH p, sum(r.threat) AS total_threat
    RETURN p.player_name AS player, total_threat
    ORDER BY total_threat DESC
    LIMIT $limit
    """,
    "PLAYER_ICT_BREAKDOWN": """
    MATCH (p:Player {player_name: $player})-[r:PLAYED_IN]->(:Fixture)
    RETURN p.player_name AS player,
           avg(r.influence) AS avg_influence,
           avg(r.creativity) AS avg_creativity,
           avg(r.threat) AS avg_threat,
           avg(r.ict_index) AS avg_ict
    """,
}

required_params_map = {
    # -----------------------------------------------------
    # 1. Player Performance & Statistics
    # -----------------------------------------------------
    "PLAYER_RECENT_STATS": ["player", "limit"],
    "PLAYER_STATS_GW": ["player", "gw"],
    "COMPARE_PLAYERS": ["player1", "player2"],
    "PLAYER_CAREER_TOTALS": ["player"],
    "PLAYERS_BY_STAT": ["stat_property", "limit"],
    # -----------------------------------------------------
    # 2. Top Performers & Recommendations
    # -----------------------------------------------------
    "TOP_PLAYERS_POSITION": ["position", "limit"],
    "TOP_UNDER_BUDGET": ["budget", "limit"],
    "CLEAN_SHEET_LEADERS": ["limit"],
    "TOP_FORM": ["limit"],
    "TOP_ICT_ATTACKERS": ["limit"],
    "TOP_BONUS_POINTS": ["limit"],
    "BEST_PENALTY_SAVERS": ["limit"],
    # -----------------------------------------------------
    # 3. Disciplinary & Negative Stats
    # -----------------------------------------------------
    "DISCIPLINARY_LEADERS": ["limit"],
    "OWN_GOAL_CONTRIBUTORS": ["limit"],
    "PENALTY_MISS_LEADERS": ["limit"],
    # -----------------------------------------------------
    # 4. Team Analysis
    # -----------------------------------------------------
    "TEAM_DEFENSE_STRENGTH": ["team"],
    "TEAM_ATTACK_STRENGTH": ["team"],
    "TEAM_TOTAL_POINTS": ["team"],
    "TEAMS_BY_CLEAN_SHEETS": ["limit"],
    "TEAM_PLAYERS_TOTAL_PTS": ["team"],
    # -----------------------------------------------------
    # 5. Fixture Queries
    # -----------------------------------------------------
    "TEAM_FIXTURES": ["team", "limit"],
    "FIXTURES_BETWEEN_TEAMS": ["team1", "team2"],
    "PLAYER_POINTS_VS_TEAM": ["player", "team"],
    "FIXTURES_FOR_GW": ["gw"],
    "PLAYER_FIXTURES": ["player", "limit"],
    # -----------------------------------------------------
    # 6. Player Value & Minutes
    # -----------------------------------------------------
    "MOST_MINUTES_PLAYED": ["limit"],
    "MINUTES_PER_POINT": ["limit"],
    "TOP_VALUE_FOR_MONEY": ["limit"],
    # -----------------------------------------------------
    # 7. ICT Statistics
    # -----------------------------------------------------
    "TOP_INFLUENCE": ["limit"],
    "TOP_CREATIVITY": ["limit"],
    "TOP_THREAT": ["limit"],
    "PLAYER_ICT_BREAKDOWN": ["player"],
}


def local_intent_classify(text: str) -> str:
    """Very small keyword-based fallback intent classifier."""
    t = text.lower()
    if any(w in t for w in ["captain", "recommend", "suggest", "transfer", "under"]):
        print("Transfer rec detected")
        return "TRANSFER_REC"
    if any(w in t for w in ["compare", "better", "vs", "vs."]):
        print("Compare intent detected")
        return "COMPARE"
    if any(w in t for w in ["fixture", "playing", "next", "opponent"]):
        print("Team fixture intent detected")
        return "TEAM_FIXTURE"
    if any(w in t for w in ["points", "how many", "goals", "assists", "stats"]):
        print("Player stats intent detected")
        return "PLAYER_STATS"
    return "GENERAL"
