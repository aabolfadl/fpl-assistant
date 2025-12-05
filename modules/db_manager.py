# modules/db_manager.py

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth

# Load .env DO NOT REMOVE THIS because settings.py is not imported here
load_dotenv()


class Neo4jGraph:
    """
    Singleton class to manage Neo4j driver and query execution.
    """

    _instance = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jGraph, cls).__new__(cls)

            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USERNAME")
            password = os.getenv("NEO4J_PASSWORD")

            if not uri or not user or not password:
                raise RuntimeError(
                    "Neo4j credentials missing. Please set NEO4J_URI, "
                    "NEO4J_USERNAME, NEO4J_PASSWORD in your .env file."
                )

            try:
                cls._driver = GraphDatabase.driver(
                    uri,
                    auth=basic_auth(user, password),
                    max_connection_pool_size=20,
                    connection_timeout=30,
                )
                print("Neo4j driver initialized successfully.")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Neo4j driver: {e}")

        return cls._instance

    # ------------------------------
    # Cypher Query Execution Wrapper
    # ------------------------------

    def execute_query(self, query: str, params: dict = None):
        """
        Executes a Cypher query safely and returns results as a list of dicts.

        Args:
            query (str): Cypher query string
            params (dict): Query params dict (default: None)

        Returns:
            List[Dict]: Row-based data returned from Neo4j
        """
        if params is None:
            params = {}

        try:
            with self._driver.session() as session:
                results = session.run(query, params)
                return [record.data() for record in results]

        except Exception as e:
            # Log and re-raise so callers can decide how to handle errors.
            err_msg = (
                f"[Neo4j ERROR] Query failed:\n{query}\nParams: {params}\nError: {e}"
            )
            print(err_msg)
            raise

    # ------------------------------
    # Graceful Shutdown
    # ------------------------------

    def close(self):
        """Close the Neo4j driver."""
        if self._driver:
            self._driver.close()
            print("Neo4j driver closed.")


# Instantiate globally so all modules share this instance
neo4j_graph = Neo4jGraph()
