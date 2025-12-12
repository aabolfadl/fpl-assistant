"""
Cypher Template Library
----------------------

Contains all Cypher query templates and intent → template mapping rules
for the FPL Graph-RAG system.
"""

# Cypher Template Library
# ----------------------
# Contains all Cypher query templates and intent → template mapping rules for the FPL Graph-RAG system.

CYPHER_TEMPLATE_LIBRARY = {
    # -----------------------------------------------------
    # PLAYER PERFORMANCE & COMPARISON
    # -----------------------------------------------------
    # What are the stats for a player in a specific gameweek in a specific season? tested
    "PLAYER_STATS_GW_SEASON": """
      MATCH (p:Player {player_name: $player1})
         -[r:PLAYED_IN]->
         (f:Fixture)<-[:HAS_FIXTURE]-(gw:Gameweek {GW_number: $gw})
      WHERE gw.season = $season
      RETURN p.player_name AS player,
         gw.season AS season,
         gw.GW_number AS gw,
         r.total_points AS total_points,
         r.goals_scored AS goals_scored,
         r.assists AS assists,
         r.clean_sheets AS clean_sheets,
         r.minutes AS minutes,
         r.bonus AS bonus,
         r.yellow_cards AS yellow_cards,
         r.red_cards AS red_cards,
         r.saves AS saves,
         r.goals_conceded AS goals_conceded
      """,
    # How do two players compare in total points? tested
    "COMPARE_PLAYERS_BY_TOTAL_POINTS": """
       MATCH (p1:Player {player_name: $player1})
       OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
       WITH $player1 AS player1_name, coalesce(sum(r1.total_points), 0) AS p1_pts
       MATCH (p2:Player {player_name: $player2})
       OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
       WITH player1_name, p1_pts, $player2 AS player2_name, coalesce(sum(r2.total_points), 0) AS p2_pts
       RETURN
              player1_name AS player1,
              p1_pts AS player1_points,
              player2_name AS player2,
              p2_pts AS player2_points
       """,
    # How do two players compare in a specific stat sum? tested
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_TOTAL_ALL_TIME": """
       MATCH (p1:Player {player_name: $player1})
       OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
       WITH $player1 AS player1_name, coalesce(sum(r1.$stat_property), 0) AS p1_sum_$stat_property
       MATCH (p2:Player {player_name: $player2})
       OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
       WITH player1_name, p1_sum_$stat_property, $player2 AS player2_name, coalesce(sum(r2.$stat_property), 0) AS p2_sum_$stat_property
       RETURN
              player1_name AS player1,
              p1_sum_$stat_property AS player1_sum_$stat_property,
              player2_name AS player2,
              p2_sum_$stat_property AS player2_sum_$stat_property
       """,
    # How do two players compare in a specific stat average? tested
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_AVG": """
       MATCH (p1:Player {player_name: $player1})
       OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
       WITH $player1 AS player1_name, coalesce(avg(r1.$stat_property), 0) AS p1_avg_$stat_property
       MATCH (p2:Player {player_name: $player2})
       OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
       WITH player1_name, p1_avg_$stat_property, $player2 AS player2_name, coalesce(avg(r2.$stat_property), 0) AS p2_avg_$stat_property
       RETURN
              player1_name AS player1,
              p1_avg_$stat_property AS player1_avg_$stat_property,
              player2_name AS player2,
              p2_avg_$stat_property AS player2_avg_$stat_property
       """,
    # What are the career stats totals for a player? tested
    "PLAYER_CAREER_STATS_TOTALS": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN p.player_name AS player,
              sum(r.total_points) AS total_points,
              sum(r.goals_scored) AS career_goals,
              sum(r.assists) AS career_assists,
              sum(r.clean_sheets) AS career_clean_sheets,
              count(r) AS matches_played
       """,
    # What are the specific stat sum for a player? tested
    "PLAYER_SPECIFIC_STAT_SUM": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN p.player_name AS player,
              sum(r.$stat_property) AS sum_$stat_property,
              count(r) AS matches_played
       """,
    # What are the specific stat avg for a player? tested
    "PLAYER_SPECIFIC_STAT_AVG": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN p.player_name AS player,
              avg(r.$stat_property) AS avg_$stat_property,
              count(r) AS matches_played
       """,
    # What are the specific stat sum for a player in a specific season? tested
    "PLAYER_SPECIFIC_STAT_SUM_SPECIFIC_SEASON": """
      MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
      MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
      WHERE gw.season = $season
      RETURN p.player_name AS player,
         sum(r.$stat_property) AS sum_$stat_property,
         count(r) AS matches_played
      """,
    # What are the specific stat avg for a player in a specific season? tested
    "PLAYER_SPECIFIC_STAT_AVG_SPECIFIC_SEASON": """
      MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
      MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
      WHERE gw.season = $season
      RETURN p.player_name AS player,
         avg(r.$stat_property) AS avg_$stat_property,
         count(r) AS matches_played
      """,
    # Who are the top players by a given stat? tested
    "TOP_PLAYERS_BY_STAT": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.$stat_property) AS total_stat
       RETURN p.player_name AS player, total_stat
       ORDER BY total_stat DESC
       LIMIT $limit
       """,
    # -----------------------------------------------------
    # TOP PERFORMERS & LEADERBOARDS
    # -----------------------------------------------------
    # Who are the top players in a given position in total_points? tested
    "TOP_PLAYERS_BY_POSITION_IN_POINTS": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.total_points) AS total_pts
       RETURN p.player_name AS player, total_pts
       ORDER BY total_pts DESC
       LIMIT $limit
    """,
    # Who are the top players in a given position by form? tested
    "TOP_PLAYERS_BY_POSITION_IN_FORM": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, avg(r.form) AS avg_form
       RETURN p.player_name AS player, avg_form
       ORDER BY avg_form DESC
       LIMIT $limit
    """,
    # Which players have the most stat in total? tested
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS_ANY_POSITION": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.$stat_property) AS stat_total
       RETURN p.player_name AS player, stat_total
       ORDER BY stat_total DESC
       LIMIT $limit
       """,
    # Which players have the most stat in a specific position? tested
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.$stat_property) AS stat_total
       RETURN p.player_name AS player, stat_total
       ORDER BY stat_total DESC
       LIMIT $limit
       """,
    # Which players have the best average of stat? tested
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, avg(r.$stat_property) AS stat_avg
       RETURN p.player_name AS player, stat_avg
       ORDER BY stat_avg DESC
       LIMIT $limit
       """,
    # Which players have the best average of stat in a specific position? tested
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, avg(r.$stat_property) AS stat_avg
       RETURN p.player_name AS player, stat_avg
       ORDER BY stat_avg DESC
       LIMIT $limit
       """,
    # -----------------------------------------------------
    # COMPOUND & DERIVED STATS
    # -----------------------------------------------------
    # Which players have the most yellow/red cards? tested
    "MOST_CARDS_LEADERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
       RETURN p.player_name AS player, yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
       ORDER BY disciplinary_score DESC
       LIMIT $limit
       """,
    # Which players have the most goal contributions (goals + assists)? tested
    "MOST_GOAL_CONTRIBUTIONS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.goals_scored) AS goals, sum(r.assists) AS assists
       RETURN p.player_name AS player, goals, assists, (goals + assists) AS goal_contributions
       ORDER BY goal_contributions DESC
       LIMIT $limit
       """,
    # Which players have the best points per minute ratio? tested
    "POINTS_PER_MINUTE_LEADERS": """
      MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
      WITH p, sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
      WHERE total_points > 0 AND total_minutes > 0
      RETURN p.player_name AS player,
            total_points / total_minutes AS points_per_minute,
            total_points as total_points,
            total_minutes as total_minutes
      ORDER BY points_per_minute DESC
      LIMIT $limit
      """,
    # What is the points per minute ratio for a specific player? tested
    "PLAYER_POINTS_PER_MINUTE": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
         WITH sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
         WHERE total_points > 0 AND total_minutes > 0
         RETURN total_points / total_minutes AS points_per_minute,
                  total_points AS total_points,
                  total_minutes AS total_minutes
         """,
    # What is the points per minute ratio for a specific player in a specific season? tested
    "PLAYER_POINTS_PER_MINUTE_SPECIFIC_SEASON": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
         MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE gw.season = $season
         WITH sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
         WHERE total_points > 0 AND total_minutes > 0
         RETURN total_points / total_minutes AS points_per_minute,
                  total_points AS total_points,
                  total_minutes AS total_minutes
         """,
    # What is the total number of cards for a specific player? tested
    "PLAYER_TOTAL_CARDS": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
         WITH sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
         RETURN yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
         """,
    # What is the total number of goal contributions for a specific player? tested
    "PLAYER_GOAL_CONTRIBUTIONS": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
         WITH sum(r.goals_scored) AS goals, sum(r.assists) AS assists
         RETURN goals, assists, (goals + assists) AS goal_contributions
         """,
    # What is the total number of goal contributions for a specific player in a specific season? tested
    "PLAYER_GOAL_CONTRIBUTIONS_SPECIFIC_SEASON": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
         MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE gw.season = $season
         WITH sum(r.goals_scored) AS goals, sum(r.assists) AS assists
         RETURN goals, assists, (goals + assists) AS goal_contributions
         """,
    # What is the total number of cards for a specific player in a specific season? tested
    "PLAYER_TOTAL_CARDS_SPECIFIC_SEASON": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
         MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE gw.season = $season
         WITH sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
         RETURN yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
         """,
    # -----------------------------------------------------
    # TEAM ANALYSIS & AGGREGATES
    # -----------------------------------------------------
    # How many points has a player scored against a specific team? tested
    "PLAYER_POINTS_VS_SPECIFIC_TEAM": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (t:Team {name: $team1})
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN p.player_name AS player,
              t.name AS opponent,
              sum(r.total_points) AS total_points_vs_opponent,
              count(f) AS matches_played
       """,
    # -----------------------------------------------------
    # PLAYER VALUE & RECENT PERFORMANCE
    # -----------------------------------------------------
    # What are the last N fixtures and points for a player? tested
    "PLAYER_LAST_N_FIXTURES_PERFORMANCE": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       OPTIONAL MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       RETURN f.kickoff_time AS date, gw.GW_number AS gw, r.total_points
       ORDER BY date DESC
       LIMIT $limit
     """,
    # -----------------------------------------------------
    # PLAYER APPEARANCES, SPLITS & CONSISTENCY
    # -----------------------------------------------------
    # What is the maximum stat a player has achieved in a single match? tested
    "PLAYER_MAX_SPECIFIC_STAT_SINGLE_MATCH": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN max(r.$stat_property) AS max_$stat_property
       """,
    # How many fixtures in a specific season has a player appeared in? tested
    "PLAYER_FIXTURE_COUNT_SPECIFIC_SEASON": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       WHERE gw.season = $season AND r.minutes > 0
       RETURN count(r) AS appearances_in_season
       """,
    # How many fixtures in total has a player appeared? tested
    "PLAYER_FIXTURE_COUNT_TOTAL": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE r.minutes > 0
       RETURN count(r) AS appearances_in_season
       """,
    # Against which teams has a player scored the most points? tested
    "PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": """
      MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
      MATCH (t:Team)
      WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
      WITH t, sum(r.total_points) AS points
      ORDER BY points DESC
      SKIP 1        // skip the highest (player's own team)
      LIMIT $limit   // $limit can be 5 to include 2nd-6th, or 1 to get the 6th only
      RETURN t.name AS opponent, points
      """,
    # Against which teams has a player scored the fewest points? tested
    "PLAYER_WORST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (t:Team)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN t.name AS opponent, sum(r.total_points) AS points
       ORDER BY points ASC
       LIMIT $limit
       """,
    # Which position has the best average points? tested
    "POSITION_BEST_AVG_POINTS": """
       MATCH (pos:Position)<-[:PLAYS_AS]-(p:Player)
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WHERE r.minutes>0
       WITH pos, avg(r.total_points) AS avg_points
       RETURN pos.name AS position, avg_points
       ORDER BY avg_points DESC
       """,
    # How many players are there in each position? tested
    "POSITION_PLAYERS_COUNT": """
       MATCH (pos:Position)<-[:PLAYS_AS]-(p:Player)
       RETURN pos.name AS position, count(p) AS players
       """,
    # Who are the least consistent players (highest stdev)? tested
    "LEAST_CONSISTENT_PLAYERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, stdev(r.total_points) AS inconsistency
       RETURN p.player_name AS player, inconsistency
       ORDER BY inconsistency DESC
       LIMIT $limit
       """,
}

required_params_map = {
    # PLAYER PERFORMANCE & COMPARISON
    "PLAYER_STATS_GW_SEASON": ["player1", "gw", "season"],
    "COMPARE_PLAYERS_BY_TOTAL_POINTS": ["player1", "player2"],
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_TOTAL_ALL_TIME": [
        "player1",
        "player2",
        "stat_property",
    ],
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_AVG": ["player1", "player2", "stat_property"],
    "PLAYER_CAREER_STATS_TOTALS": ["player1"],
    "PLAYER_SPECIFIC_STAT_SUM": ["player1", "stat_property"],
    "PLAYER_SPECIFIC_STAT_AVG": ["player1", "stat_property"],
    "PLAYER_SPECIFIC_STAT_SUM_SPECIFIC_SEASON": ["player1", "stat_property", "season"],
    "PLAYER_SPECIFIC_STAT_AVG_SPECIFIC_SEASON": ["player1", "stat_property", "season"],
    # TOP PERFORMERS & LEADERBOARDS
    "TOP_PLAYERS_BY_STAT": ["stat_property", "limit"],
    "TOP_PLAYERS_BY_POSITION_IN_POINTS": ["position", "limit"],
    "TOP_PLAYERS_BY_POSITION_IN_FORM": ["position", "limit"],
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS_ANY_POSITION": ["stat_property", "limit"],
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": [
        "position",
        "stat_property",
        "limit",
    ],
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS": ["stat_property", "limit"],
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": [
        "position",
        "stat_property",
        "limit",
    ],
    # COMPOUND & DERIVED STATS
    "MOST_CARDS_LEADERS": ["limit"],
    "MOST_GOAL_CONTRIBUTIONS": ["limit"],
    "POINTS_PER_MINUTE_LEADERS": ["limit"],
    "PLAYER_POINTS_PER_MINUTE": ["player1"],
    "PLAYER_POINTS_PER_MINUTE_SPECIFIC_SEASON": ["player1", "season"],
    "PLAYER_TOTAL_CARDS": ["player1"],
    "PLAYER_GOAL_CONTRIBUTIONS": ["player1"],
    "PLAYER_TOTAL_CARDS_SPECIFIC_SEASON": ["player1", "season"],
    "PLAYER_GOAL_CONTRIBUTIONS_SPECIFIC_SEASON": ["player1", "season"],
    # TEAM ANALYSIS & AGGREGATES
    "PLAYER_POINTS_VS_SPECIFIC_TEAM": ["player1", "team1"],
    # PLAYER VALUE & RECENT PERFORMANCE
    "PLAYER_LAST_N_FIXTURES_PERFORMANCE": ["player1", "limit"],
    # PLAYER APPEARANCES, SPLITS & CONSISTENCY
    "PLAYER_MAX_SPECIFIC_STAT_SINGLE_MATCH": ["player1", "stat_property"],
    "PLAYER_FIXTURE_COUNT_SPECIFIC_SEASON": ["player1", "season"],
    "PLAYER_FIXTURE_COUNT_TOTAL": ["player1"],
    "PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": ["player1", "limit"],
    "PLAYER_WORST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": ["player1", "limit"],
    "POSITION_BEST_AVG_POINTS": [],
    "POSITION_PLAYERS_COUNT": [],
    "LEAST_CONSISTENT_PLAYERS": ["limit"],
}


def local_intent_classify(text: str) -> str:
    """Very small keyword-based fallback intent classifier."""
    t = text.lower()
    if any(w in t for w in ["captain", "recommend", "suggest", "transfer"]):
        print("Captain rec intent detected")
        return "PLAYER_POINTS_PER_MINUTE_SPECIFIC_SEASON"
    if any(w in t for w in ["compare", "better", "vs", "vs."]):
        print("COMPARE_PLAYERS_BY_TOTAL_POINTS")
        return "Compare players intent detected"
    if any(w in t for w in ["fixture", "playing", "next", "opponent"]):
        print("Player opponent intent detected")
        return "PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS"
    if any(w in t for w in ["points", "how many", "goals", "assists", "stats"]):
        print("Player career stats intent detected")
        return "PLAYER_CAREER_STATS_TOTALS"
    return "PLAYER_CAREER_STATS_TOTALS"
