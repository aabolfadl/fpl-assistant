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

    def execute_query_with_graph(self, query: str, params: dict = None):
        """
        Executes a Cypher query and extracts nodes/relationships for visualization.

        Since most Cypher queries return aggregated/scalar data rather than graph objects,
        this method modifies the query to also return all nodes and relationships involved.

        Args:
            query (str): Cypher query string
            params (dict): Query params dict (default: None)

        Returns:
            Dict with keys:
                - 'results': List[Dict] - Row-based data returned from Neo4j
                - 'nodes': List[Dict] - Extracted nodes for visualization
                - 'edges': List[Dict] - Extracted relationships for visualization
        """
        if params is None:
            params = {}

        try:
            with self._driver.session() as session:
                # Execute original query for data
                results = session.run(query, params)
                records = list(results)
                data = [record.data() for record in records]

                # Build and execute graph extraction query
                nodes_dict = {}
                edges_list = []
                edge_set = set()

                from neo4j.graph import Node, Relationship

                try:
                    # Parse the query to extract variable names and build extraction query
                    graph_query = self._build_graph_extraction_query(query)

                    if graph_query:
                        print(f"[DEBUG] Running graph extraction query")
                        graph_results = session.run(graph_query, params)
                        graph_records = list(graph_results)
                        print(
                            f"[DEBUG] Graph query returned {len(graph_records)} records"
                        )

                        for record in graph_records:
                            # Iterate through all keys in the record
                            for key, value in record.items():
                                # Check for Node objects
                                if isinstance(value, Node):
                                    node_id = value.id
                                    node_obj = {
                                        **dict(value),
                                        "id": node_id,
                                        "labels": list(value.labels),
                                    }
                                    if node_id not in nodes_dict:
                                        nodes_dict[node_id] = node_obj
                                        print(
                                            f"[DEBUG] Added node {node_id} ({', '.join(value.labels)})"
                                        )

                                # Check for Relationship objects
                                elif isinstance(value, Relationship):
                                    rel_type = value.type
                                    start_id = value.start_node.id
                                    end_id = value.end_node.id
                                    edge_id = f"{start_id}-{rel_type}-{end_id}"

                                    if edge_id not in edge_set:
                                        edge_obj = {
                                            "id": value.id,
                                            "type": rel_type,
                                            "start_node_id": start_id,
                                            "end_node_id": end_id,
                                            **dict(value),
                                        }
                                        edges_list.append(edge_obj)
                                        edge_set.add(edge_id)
                                        print(
                                            f"[DEBUG] Added edge {start_id} -[{rel_type}]-> {end_id}"
                                        )

                                # Check for lists of nodes/edges (from COLLECT)
                                elif isinstance(value, list):
                                    print(
                                        f"[DEBUG] Processing list from key '{key}': {len(value)} items"
                                    )
                                    for item in value:
                                        if isinstance(item, Node):
                                            node_id = item.id
                                            node_obj = {
                                                **dict(item),
                                                "id": node_id,
                                                "labels": list(item.labels),
                                            }
                                            if node_id not in nodes_dict:
                                                nodes_dict[node_id] = node_obj
                                                print(
                                                    f"[DEBUG] Added node {node_id} from list ({', '.join(item.labels)})"
                                                )
                                        elif isinstance(item, Relationship):
                                            rel_type = item.type
                                            start_id = item.start_node.id
                                            end_id = item.end_node.id
                                            edge_id = f"{start_id}-{rel_type}-{end_id}"

                                            if edge_id not in edge_set:
                                                edge_obj = {
                                                    "id": item.id,
                                                    "type": rel_type,
                                                    "start_node_id": start_id,
                                                    "end_node_id": end_id,
                                                    **dict(item),
                                                }
                                                edges_list.append(edge_obj)
                                                edge_set.add(edge_id)
                                                print(
                                                    f"[DEBUG] Added edge {start_id} -[{rel_type}]-> {end_id} from list"
                                                )

                except Exception as e:
                    print(f"[DEBUG] Graph extraction error: {str(e)}")
                    import traceback

                    traceback.print_exc()

                print(
                    f"[DEBUG] Extracted {len(nodes_dict)} nodes and {len(edges_list)} edges"
                )
                return {
                    "results": data,
                    "nodes": list(nodes_dict.values()),
                    "edges": edges_list,
                }

        except Exception as e:
            err_msg = (
                f"[Neo4j ERROR] Query failed:\n{query}\nParams: {params}\nError: {e}"
            )
            print(err_msg)
            raise

    def _build_graph_extraction_query(self, query: str) -> str:
        """
        Modifies a MATCH query to also collect all nodes and relationships.
        """
        import re

        # Find MATCH clause
        match_pattern = r"MATCH\s+(.+?)(?=\s+(?:RETURN|WHERE|OPTIONAL|WITH))"
        match = re.search(match_pattern, query, re.IGNORECASE | re.DOTALL)

        if not match:
            print("[DEBUG] Could not parse MATCH clause")
            return None

        match_clause = match.group(1)

        # Extract all variable names from parentheses and brackets
        node_vars = list(set(re.findall(r"\(([a-zA-Z_]\w*)[^)]*\)", match_clause)))
        edge_vars = list(set(re.findall(r"\[([a-zA-Z_]\w*)[^\]]*\]", match_clause)))

        if not node_vars and not edge_vars:
            print("[DEBUG] No variables found in MATCH clause")
            return None

        print(f"[DEBUG] Found node vars: {node_vars}, edge vars: {edge_vars}")

        # Find and replace the RETURN clause
        return_pattern = r"RETURN\s+(.+?)(?=$|\s*LIMIT|\s*ORDER)"
        return_match = re.search(return_pattern, query, re.IGNORECASE | re.DOTALL)

        if not return_match:
            print("[DEBUG] Could not find RETURN clause")
            return None

        original_return = return_match.group(1).strip()

        # Build list of all variables to return
        all_vars = node_vars + edge_vars
        var_returns = ", ".join(all_vars)

        # Create new return clause that includes the original returns + the variables
        new_return = f"{original_return}, {var_returns}"

        # Replace the RETURN clause
        new_query = (
            query[: return_match.start()]
            + f"RETURN {new_return}"
            + query[return_match.end() :]
        )

        print(f"[DEBUG] Built extraction query with RETURN {var_returns}")
        return new_query

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
