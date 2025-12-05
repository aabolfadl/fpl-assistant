# scripts/create_kg.py

import pandas as pd
from neo4j import GraphDatabase


def read_config(file_path="config.txt"):
    config = {}
    with open(file_path, "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key] = value
    return config


def create_constraints(tx):
    # Create uniqueness constraints based on schema identifiers
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Season) REQUIRE s.season_name IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Gameweek) REQUIRE (g.season, g.GW_number) IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Fixture) REQUIRE (f.season, f.fixture_number) IS UNIQUE"
    )
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Team) REQUIRE t.name IS UNIQUE")
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Player) REQUIRE (p.player_name, p.player_element) IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pos:Position) REQUIRE pos.name IS UNIQUE"
    )


def create_data(tx, row):
    # 1. Nodes
    # Season
    tx.run("MERGE (:Season {season_name: $season})", season=row["season"])

    # Gameweek
    tx.run(
        """
        MERGE (g:Gameweek {season: $season, GW_number: toInteger($GW)})
    """,
        season=row["season"],
        GW=row["GW"],
    )

    # Fixture (with kickoff_time property)
    tx.run(
        """
        MERGE (f:Fixture {season: $season, fixture_number: toInteger($fixture)})
        ON CREATE SET f.kickoff_time = $kickoff_time
    """,
        season=row["season"],
        fixture=row["fixture"],
        kickoff_time=row["kickoff_time"],
    )

    # Teams
    tx.run("MERGE (:Team {name: $home_team})", home_team=row["home_team"])
    tx.run("MERGE (:Team {name: $away_team})", away_team=row["away_team"])

    # Player
    tx.run(
        """
        MERGE (p:Player {player_name: $name, player_element: toInteger($element)})
    """,
        name=row["name"],
        element=row["element"],
    )

    # Position
    tx.run("MERGE (:Position {name: $position})", position=row["position"])

    # 2. Relationships

    # (Season) -[:HAS_GW]-> (Gameweek)
    tx.run(
        """
        MATCH (s:Season {season_name: $season})
        MATCH (g:Gameweek {season: $season, GW_number: toInteger($GW)})
        MERGE (s)-[:HAS_GW]->(g)
    """,
        season=row["season"],
        GW=row["GW"],
    )

    # (Gameweek) -[:HAS_FIXTURE]-> (Fixture)
    tx.run(
        """
        MATCH (g:Gameweek {season: $season, GW_number: toInteger($GW)})
        MATCH (f:Fixture {season: $season, fixture_number: toInteger($fixture)})
        MERGE (g)-[:HAS_FIXTURE]->(f)
    """,
        season=row["season"],
        GW=row["GW"],
        fixture=row["fixture"],
    )

    # (Fixture) -[:HAS_HOME_TEAM]-> (Team)
    tx.run(
        """
        MATCH (f:Fixture {season: $season, fixture_number: toInteger($fixture)})
        MATCH (t:Team {name: $home_team})
        MERGE (f)-[:HAS_HOME_TEAM]->(t)
    """,
        season=row["season"],
        fixture=row["fixture"],
        home_team=row["home_team"],
    )

    # (Fixture) -[:HAS_AWAY_TEAM]-> (Team)
    tx.run(
        """
        MATCH (f:Fixture {season: $season, fixture_number: toInteger($fixture)})
        MATCH (t:Team {name: $away_team})
        MERGE (f)-[:HAS_AWAY_TEAM]->(t)
    """,
        season=row["season"],
        fixture=row["fixture"],
        away_team=row["away_team"],
    )

    # (Player) -[:PLAYS_AS]-> (Position)
    tx.run(
        """
        MATCH (p:Player {player_name: $name, player_element: toInteger($element)})
        MATCH (pos:Position {name: $position})
        MERGE (p)-[:PLAYS_AS]->(pos)
    """,
        name=row["name"],
        element=row["element"],
        position=row["position"],
    )

    # (Player) -[:PLAYED_IN]-> (Fixture) with properties
    # Converting numerical properties to appropriate types (integers/floats)
    tx.run(
        """
        MATCH (p:Player {player_name: $name, player_element: toInteger($element)})
        MATCH (f:Fixture {season: $season, fixture_number: toInteger($fixture)})
        MERGE (p)-[r:PLAYED_IN]->(f)
        SET r.minutes = toInteger($minutes),
            r.goals_scored = toInteger($goals_scored),
            r.assists = toInteger($assists),
            r.total_points = toInteger($total_points),
            r.bonus = toInteger($bonus),
            r.clean_sheets = toInteger($clean_sheets),
            r.goals_conceded = toInteger($goals_conceded),
            r.own_goals = toInteger($own_goals),
            r.penalties_saved = toInteger($penalties_saved),
            r.penalties_missed = toInteger($penalties_missed),
            r.yellow_cards = toInteger($yellow_cards),
            r.red_cards = toInteger($red_cards),
            r.saves = toInteger($saves),
            r.bps = toInteger($bps),
            r.influence = toFloat($influence),
            r.creativity = toFloat($creativity),
            r.threat = toFloat($threat),
            r.ict_index = toFloat($ict_index),
            r.form = toFloat($form)
    """,
        name=row["name"],
        element=row["element"],
        season=row["season"],
        fixture=row["fixture"],
        minutes=row["minutes"],
        goals_scored=row["goals_scored"],
        assists=row["assists"],
        total_points=row["total_points"],
        bonus=row["bonus"],
        clean_sheets=row["clean_sheets"],
        goals_conceded=row["goals_conceded"],
        own_goals=row["own_goals"],
        penalties_saved=row["penalties_saved"],
        penalties_missed=row["penalties_missed"],
        yellow_cards=row["yellow_cards"],
        red_cards=row["red_cards"],
        saves=row["saves"],
        bps=row["bps"],
        influence=row["influence"],
        creativity=row["creativity"],
        threat=row["threat"],
        ict_index=row["ict_index"],
        form=row["form"],
    )


def main():
    # Load Configuration
    config = read_config()
    uri = config.get("URI", "neo4j://localhost:7687")
    username = config.get("USERNAME", "neo4j")
    password = config.get("PASSWORD", "password")

    # Load Data
    print("Loading CSV data...")
    df = pd.read_csv("fpl_two_seasons.csv")
    # Ensure no NaN values in critical columns or handle them
    df = df.fillna(0)

    # Connect to Neo4j
    driver = GraphDatabase.driver(uri, auth=(username, password))

    with driver.session() as session:
        print("Creating Constraints...")
        session.execute_write(create_constraints)

        print("Building Knowledge Graph (this may take some time)...")
        for index, row in df.iterrows():
            if index % 100 == 0:
                print(f"Processing row {index}...")
            session.execute_write(create_data, row)

    driver.close()
    print("Knowledge Graph created successfully.")


if __name__ == "__main__":
    main()
