# modules/graph_visualizer.py

"""
Graph Visualizer Module
-----------------------

This module provides utilities to convert Neo4j graph results into
vis.js-compatible format for interactive visualization in Streamlit.

It handles:
- Extraction of nodes and relationships from Neo4j query results
- Conversion to vis.js nodes and edges format
- Color coding for different node types
- Interactive HTML generation for Streamlit
"""

import json
from typing import Dict, Any, List, Tuple, Optional


# Color scheme for different node types
NODE_TYPE_COLORS = {
    "Player": "#3498db",  # Blue
    "Team": "#e74c3c",  # Red
    "Fixture": "#f39c12",  # Orange
    "Gameweek": "#9b59b6",  # Purple
    "Position": "#1abc9c",  # Teal
    "Season": "#34495e",  # Dark gray
    "Stat": "#27ae60",  # Green
    "default": "#95a5a6",  # Light gray
}

EDGE_TYPE_COLORS = {
    "PLAYS_FOR": "#e74c3c",
    "HAS_POSITION": "#1abc9c",
    "PLAYED_IN": "#f39c12",
    "IN_SEASON": "#34495e",
    "HAS_STATS": "#27ae60",
    "default": "#7f8c8d",
}


def extract_node_label(node: Dict[str, Any]) -> str:
    """Extract a readable label from a Neo4j node."""
    # Try common properties in order
    for prop in ["name", "player_name", "team_name", "position_name", "title"]:
        if prop in node:
            return str(node[prop])
    # Fallback to first non-id property
    for key, value in node.items():
        if key != "id" and value is not None:
            return str(value)
    return "Unknown"


def get_node_type(node: Dict[str, Any]) -> str:
    """Determine node type from labels or properties."""
    # Check if node has label information (from RETURN labels(n) in query)
    if "labels" in node:
        labels = node["labels"]
        if isinstance(labels, list) and labels:
            return labels[0]

    # Fallback: infer from properties
    if "player_name" in node or "name" in node:
        return "Player"
    if "team_name" in node:
        return "Team"
    if "gameweek" in node:
        return "Gameweek"

    return "default"


def neo4j_to_visjs_graph(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Convert Neo4j node/edge objects to vis.js nodes and edges.

    Args:
        nodes: List of Neo4j node dicts from db_manager.execute_query_with_graph()
        edges: List of Neo4j edge dicts from db_manager.execute_query_with_graph()

    Returns:
        Tuple[nodes, edges] where:
        - nodes: List of vis.js node objects
        - edges: List of vis.js edge objects
    """

    nodes_dict = {}  # Track unique nodes by id
    edges_list = []
    edge_ids = set()  # Track unique edges

    # Properties to hide from visualization tooltips
    hidden_properties = {
        "embedding_node2vec",
        "embedding_fastrp",
        "embedding",
        "embeddings",
        "id",
        "vector",
    }

    # Process nodes
    for node in nodes:
        if not isinstance(node, dict):
            continue

        node_id = str(node.get("id", id(node)))
        if node_id not in nodes_dict:
            # Filter out hidden properties for tooltip
            filtered_node = {
                k: v for k, v in node.items() if k not in hidden_properties
            }

            nodes_dict[node_id] = {
                "id": node_id,
                "label": extract_node_label(node),
                "title": json.dumps(filtered_node, indent=2, default=str),
                "color": NODE_TYPE_COLORS.get(
                    get_node_type(node), NODE_TYPE_COLORS["default"]
                ),
                "font": {"size": 14},
            }

    # Process edges
    for edge in edges:
        if not isinstance(edge, dict):
            continue

        start_id = str(edge.get("start_node_id"))
        end_id = str(edge.get("end_node_id"))
        edge_type = edge.get("type", "UNKNOWN")
        edge_id = f"{start_id}-{edge_type}-{end_id}"

        if edge_id not in edge_ids:
            # Filter out hidden properties for edge tooltip
            filtered_edge = {
                k: v for k, v in edge.items() if k not in hidden_properties
            }

            edges_list.append(
                {
                    "from": start_id,
                    "to": end_id,
                    "label": edge_type,
                    "title": json.dumps(filtered_edge, indent=2, default=str),
                    "color": EDGE_TYPE_COLORS.get(
                        edge_type, EDGE_TYPE_COLORS["default"]
                    ),
                    "arrows": "to",
                    "smooth": {"type": "continuous"},
                    "font": {"size": 12},
                }
            )
            edge_ids.add(edge_id)

    return list(nodes_dict.values()), edges_list


def generate_html_visualization(
    nodes: List[Dict], edges: List[Dict], height: int = 600
) -> str:
    """
    Generate standalone HTML for vis.js visualization.

    Args:
        nodes: List of vis.js node objects
        edges: List of vis.js edge objects
        height: Height of the visualization container in pixels

    Returns:
        HTML string that can be embedded in Streamlit
    """

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            #network-graph {{
                width: 100%;
                height: {height}px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f9f9f9;
            }}
            .graph-info {{
                padding: 10px;
                background: #f0f0f0;
                border-radius: 4px;
                margin-top: 10px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="network-graph"></div>
        <div class="graph-info">
            <strong>Nodes:</strong> {len(nodes)} | <strong>Relationships:</strong> {len(edges)}<br/>
            <em>Hover over nodes/edges to see details. Drag to move. Scroll to zoom.</em>
        </div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});
            
            var container = document.getElementById('network-graph');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            
            var options = {{
                physics: {{
                    enabled: true,
                    stabilization: {{
                        iterations: 200
                    }},
                    barnesHut: {{
                        gravitationalConstant: -30000,
                        centralGravity: 0.3,
                        springLength: 200,
                        springConstant: 0.04
                    }}
                }},
                nodes: {{
                    shape: 'dot',
                    scaling: {{
                        label: {{
                            enabled: true,
                            min: 14,
                            max: 30
                        }}
                    }},
                    font: {{
                        face: 'Arial',
                        color: 'white',
                        size: 14,
                        weight: 'bold'
                    }}
                }},
                edges: {{
                    font: {{
                        size: 12,
                        face: 'Arial',
                        color: '#222'
                    }},
                    smooth: {{
                        type: 'continuous'
                    }},
                    width: 2
                }},
                interaction: {{
                    navigationButtons: true,
                    keyboard: true,
                    zoomView: true,
                    dragView: true
                }}
            }};
            
            var network = new vis.Network(container, data, options);
            
            // Center and fit the network on load
            setTimeout(function() {{
                network.fit({{
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }}, 500);
        </script>
    </body>
    </html>
    """

    return html
