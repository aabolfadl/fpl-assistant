# main.py

"""
Streamlit main app for FPL Graph-RAG.

This app wires together:
- preprocessing (intent + entity extraction)
- cypher retriever (baseline)
- vector retriever (embeddings)
- hybrid retriever (cypher + vector)
- llm engine (answer generation)

The app is defensive: if the `modules` package isn't implemented yet it will show placeholders
so you can continue development iteratively.
"""

import streamlit as st
import json
from datetime import datetime
from config.settings import (
    MODEL_OPTIONS,
    EMBEDDING_MODEL_OPTIONS,
    DEFAULT_RETRIEVAL_MODE,
)
from config.template_library import CYPHER_TEMPLATE_LIBRARY, local_intent_classify
from modules.llm_helper import classify_with_deepseek, create_query_with_deepseek
from modules.llm_engine import (
    deepseek_generate_answer,
    gemma_generate_answer,
    llama_generate_answer,
)

# Import Neo4jGraph for direct Cypher execution
from modules.db_manager import neo4j_graph
from modules.graph_visualizer import generate_html_visualization
from styles.styles import STYLE


st.set_page_config(
    page_title="FPL Assistant", layout="wide", page_icon="styles/logo2.png"
)

st.markdown(
    STYLE,
    unsafe_allow_html=True,
)

st.title("FPL Graph-RAG Assistant")
st.markdown(
    "Ask questions about Fantasy Premier League (player stats, toughest opponents, comparisons)."
)

# Sidebar controls
with st.sidebar:
    st.image("styles/logo.png", use_column_width=True)
    st.header("Configuration")

    llm_key_choice = st.selectbox("Choose LLM", list(MODEL_OPTIONS.keys()), index=0)
    llm_model_choice = MODEL_OPTIONS[llm_key_choice]

    RETRIEVAL_OPTIONS = [
        "Baseline (Cypher)",
        "Embeddings (Vector)",
        "Hybrid",
        "LLM-generated Cypher",
    ]

    retrieval_mode = st.radio(
        "Retrieval Mode",
        RETRIEVAL_OPTIONS,
        index=RETRIEVAL_OPTIONS.index(DEFAULT_RETRIEVAL_MODE),
    )

    if retrieval_mode in ["Embeddings (Vector)", "Hybrid"]:
        embedding_key_choice = st.selectbox(
            "Choose embedding model", list(EMBEDDING_MODEL_OPTIONS.keys()), index=0
        )
        embedding_model_choice = EMBEDDING_MODEL_OPTIONS[embedding_key_choice]
    else:
        embedding_key_choice = None
        embedding_model_choice = None

    k = st.number_input(
        "Top-K results (for retrieval)", min_value=1, max_value=38, value=5
    )

# Chat history in session state
if "history" not in st.session_state:
    st.session_state.history = []

# Add these:
if "last_intents" not in st.session_state:
    st.session_state.last_intents = []
if "last_entities" not in st.session_state:
    st.session_state.last_entities = {}
if "last_graph_html" not in st.session_state:
    st.session_state.last_graph_html = None
if "last_retrieval_mode" not in st.session_state:
    st.session_state.last_retrieval_mode = None

# Input box
user_input = st.chat_input(
    "Ask about FPL — e.g. 'How many points did Salah score against Wolves?'"
)

# START OF IMPORTS CHECK

# Attempt to import project modules; if not present provide fallback/mocks
modules_missing = False
missing_module_name = None  # Variable to store the name of the missing module

try:
    from modules import preprocessing, cypher_retriever, vector_retriever
except ModuleNotFoundError as e:
    # This specific exception is raised when an import fails
    modules_missing = True
    _import_error = e

    # ModuleNotFoundError includes the name of the module that could not be found
    # The error message is usually "No module named 'module_name'"
    # We can extract the name from the exception's message
    error_message = str(e)
    # The missing module name is usually quoted in the error message,
    # e.g., "No module named 'preprocessing'"
    if "No module named" in error_message:
        # A simple way to extract the quoted name:
        start = error_message.find("'") + 1
        end = error_message.rfind("'")
        missing_module_name = error_message[start:end]

    print(f"ERROR: A required module is missing.")
    if missing_module_name:
        print(f"The module '{missing_module_name}' could not be imported.")
    else:
        # Fallback if extraction fails
        print(f"Details: {_import_error}")

except Exception as e:
    # Catch any other unexpected exception during import
    modules_missing = True
    _import_error = e
    print(f"ERROR: An unexpected error occurred during module import: {e}")

# Example of using the variable outside the try/except block
if modules_missing:
    print(
        "\nPlease install the necessary dependencies or check your 'modules' directory."
    )

# END OF IMPORTS CHECk

# Merging graph nodes and edges from cypher and vector retrievers

import json


def parse_title(node):
    try:
        return json.loads(node.get("title", "{}"))
    except Exception:
        return {}


def c_node_merge_key(node):
    meta = parse_title(node)

    if "Player" in meta.get("labels", []):
        # use Neo4j node id as canonical
        print("cypher node meta:", meta)
        return f"Player::{meta['player_element']}"
    return None


def v_node_merge_key(node):
    meta = parse_title(node)

    if "player_element" in meta:
        print("vector node meta:", meta)
        return f"Player::{meta['player_element']}"
    return None


def merge_graph_nodes(cypher_nodes, vector_nodes):
    merged = {}
    id_map = {}

    # 1️⃣ Add Cypher nodes first (authoritative)
    for node in cypher_nodes:
        key = c_node_merge_key(node)
        print(key)
        node_id = node["id"]

        if key:
            merged[key] = node.copy()
            id_map[node_id] = node_id
        else:
            merged[node_id] = node.copy()
            id_map[node_id] = node_id

    # 2️⃣ Merge Vector nodes
    for node in vector_nodes:
        key = v_node_merge_key(node)
        print(key)
        node_id = node["id"]

        if key and key in merged:
            canonical = merged[key]

            # Merge all missing fields
            for k, v in node.items():
                if k not in canonical:
                    canonical[k] = v

            id_map[node_id] = canonical["id"]
        else:
            merged[node_id] = node.copy()
            id_map[node_id] = node_id

    return list(merged.values()), id_map


def remap_edges(edges, id_map):
    remapped = []

    for edge in edges:
        e = edge.copy()
        e["from"] = id_map.get(edge["from"], edge["from"])
        e["to"] = id_map.get(edge["to"], edge["to"])
        remapped.append(e)

    return remapped


def filter_edges(edges, valid_node_ids):
    filtered = []
    for edge in edges:
        if edge["from"] in valid_node_ids and edge["to"] in valid_node_ids:
            filtered.append(edge)
    return filtered


def placeholder_retrieve(intent, entities, mode, k=5):
    """Return a placeholder context when modules aren't implemented yet."""
    now = datetime.utcnow().isoformat()
    ctx = {
        "intent": intent,
        "entities": entities,
        "mode": mode,
        "k": k,
        "timestamp": now,
        "note": "Placeholder retrieval; implement modules/cypher_retriever.py and modules/vector_retriever.py for real data.",
    }
    return ctx


def placeholder_llm_answer(user_query, context, model_name):
    return f"(LLM Placeholder answer) I received your query: '{user_query}'.\n\nContext summary:\n{json.dumps(context, indent=2)}\n\nChoose 'Show debug' to view more."


# Handle user query
if user_input:
    st.session_state.history.append({"role": "user", "text": user_input})

    # Intent classification

    try:
        # Allow classifier to return up to 3 intents (comma-separated or list)
        intents = classify_with_deepseek(
            user_input, list(CYPHER_TEMPLATE_LIBRARY.keys())
        )
    except Exception as e:
        intents = local_intent_classify(user_input)

    # Normalize to list (support comma-separated string or single string)
    if isinstance(intents, str):
        intents = [i.strip() for i in intents.split(",") if i.strip()]
    if not isinstance(intents, list):
        intents = [intents]
    intents = intents[:3]  # Limit to 3

    st.session_state.last_intents = intents

    entities = preprocessing.extract_entities(user_input)
    print("\n\n####### Extracted entities: #######\n\n")
    print(entities)

    st.session_state.last_entities = entities

    # Retrieval
    if modules_missing:
        # For placeholder, just show the first intent
        retrieved_context = [
            placeholder_retrieve(intent, entities, retrieval_mode, k=k)
            for intent in intents
        ]
        st.session_state.last_graph_html = None
    else:
        graph_html_content = None

        if retrieval_mode == "Baseline (Cypher)":
            # ...existing code...
            cypher_results = []
            for intent in intents:
                try:
                    ctx = cypher_retriever.retrieve_data_via_cypher(
                        intent, entities, limit=k
                    )
                    print(
                        f"\n\n####### Cypher retrieval result for {intent}: #######\n\n"
                    )
                    # print(ctx)

                    # Capture graph visualization data if available
                    if (
                        not graph_html_content
                        and ctx.get("graph_nodes")
                        and ctx.get("graph_edges")
                    ):
                        valid_node_ids = {
                            node["id"] for node in ctx.get("graph_nodes", [])
                        }
                        ctx["graph_edges"] = filter_edges(
                            ctx.get("graph_edges", []), valid_node_ids
                        )
                        graph_html_content = generate_html_visualization(
                            ctx.get("graph_nodes", []),
                            ctx.get("graph_edges", []),
                            height=600,
                        )
                except Exception as e:
                    ctx = {"intent": intent, "error": str(e)}
                    print(
                        f"\n\n####### Cypher retrieval error for {intent}: #######\n\n"
                    )
                    # print(ctx)
                cypher_results.append(ctx)
            # Filter out entries with an 'error' field
            retrieved_context = [res for res in cypher_results if not res.get("error")]
            # Remove graph data from context before passing to LLM
            for ctx in retrieved_context:
                ctx.pop("graph_nodes", None)
                ctx.pop("graph_edges", None)
            st.session_state.last_graph_html = graph_html_content
            st.session_state.last_retrieval_mode = "Baseline (Cypher)"

        elif retrieval_mode == "Embeddings (Vector)":
            # ...existing code...
            try:
                retrieved_context = vector_retriever.vector_search(
                    entities, top_k=k, model_choice=embedding_model_choice
                )
                print("\n\n####### Vector retrieval result: #######\n\n")
                print(retrieved_context)
                # Capture graph visualization if available
                if retrieved_context.get("graph_nodes") and retrieved_context.get(
                    "graph_edges"
                ):
                    valid_node_ids = {
                        node["id"] for node in retrieved_context.get("graph_nodes", [])
                    }
                    retrieved_context["graph_edges"] = filter_edges(
                        retrieved_context.get("graph_edges", []), valid_node_ids
                    )
                    graph_html_content = generate_html_visualization(
                        retrieved_context.get("graph_nodes", []),
                        retrieved_context.get("graph_edges", []),
                        height=600,
                    )
            except Exception as e:
                retrieved_context = {"error": str(e)}
                print("\n\n####### Vector retrieval error: #######\n\n")
                print(retrieved_context)
                graph_html_content = None
            st.session_state.last_graph_html = graph_html_content
            st.session_state.last_retrieval_mode = "Embeddings (Vector)"

        elif retrieval_mode == "Hybrid":
            cypher_contexts = []
            all_cypher_nodes = []
            all_cypher_edges = []

            for intent in intents:
                try:
                    c_res = cypher_retriever.retrieve_data_via_cypher(
                        intent, entities, limit=k
                    )
                    print(
                        f"\n\n####### Cypher retrieval result for {intent}: #######\n\n"
                    )
                    print(c_res)
                    # Collect graph data from all cypher intents
                    if c_res.get("graph_nodes"):
                        all_cypher_nodes.extend(c_res.get("graph_nodes", []))
                    if c_res.get("graph_edges"):
                        # Filter edges within this cypher context
                        valid_node_ids_cypher = {
                            node["id"] for node in c_res.get("graph_nodes", [])
                        }
                        filtered_cypher_edges = filter_edges(
                            c_res.get("graph_edges", []), valid_node_ids_cypher
                        )
                        all_cypher_edges.extend(filtered_cypher_edges)
                except Exception as e:
                    c_res = {"intent": intent, "error": str(e)}
                    print(
                        f"\n\n####### Cypher retrieval error for {intent}: #######\n\n"
                    )
                    print(c_res)
                cypher_contexts.append(c_res)

            # Filter out cypher entries with an 'error' field
            filtered_cypher_contexts = [
                res for res in cypher_contexts if not res.get("error")
            ]
            # Remove graph data from cypher contexts before passing to LLM
            for ctx in filtered_cypher_contexts:
                ctx.pop("graph_nodes", None)
                ctx.pop("graph_edges", None)

            merged_nodes = all_cypher_nodes
            merged_edges = all_cypher_edges

            try:
                v_res = vector_retriever.vector_search(
                    entities, top_k=k, model_choice=embedding_model_choice
                )
                # Merge vector graph data with cypher graph data
                all_vector_nodes = v_res.get("graph_nodes", [])
                all_vector_edges = v_res.get("graph_edges", [])

                # Filter edges within the vector context
                valid_node_ids_vector = {node["id"] for node in all_vector_nodes}
                all_vector_edges = filter_edges(all_vector_edges, valid_node_ids_vector)

                print(all_cypher_nodes[0])
                print(all_vector_nodes[7])

                merged_nodes, id_map = merge_graph_nodes(
                    all_cypher_nodes, all_vector_nodes
                )

                merged_edges = remap_edges(all_cypher_edges + all_vector_edges, id_map)

            except Exception as e:
                v_res = {"error": str(e)}

            if merged_nodes or merged_edges:
                valid_node_ids = {node["id"] for node in merged_nodes}
                merged_edges = filter_edges(merged_edges, valid_node_ids)
                graph_html_content = generate_html_visualization(
                    merged_nodes,
                    merged_edges,
                    height=600,
                )

            retrieved_context = {"cypher": filtered_cypher_contexts, "vector": v_res}
            st.session_state.last_graph_html = graph_html_content
            st.session_state.last_retrieval_mode = "Hybrid"

        elif retrieval_mode == "LLM-generated Cypher":
            # New mode: Use LLM to generate Cypher, then execute it
            try:
                cypher_query = create_query_with_deepseek(user_input)
                print("\n\n####### LLM-generated Cypher query: #######\n\n")
                print(cypher_query)
                # Optionally show the query in debug panel
                query_result = neo4j_graph.execute_query_with_graph(cypher_query)
                cypher_results = query_result.get("results", [])
                neo4j_nodes = query_result.get("nodes", [])
                neo4j_edges = query_result.get("edges", [])

                print("\n\n####### LLM Cypher execution result: #######\n\n")
                print(cypher_results)

                # Generate graph visualization
                if neo4j_nodes or neo4j_edges:
                    from modules.graph_visualizer import neo4j_to_visjs_graph

                    vis_nodes, vis_edges = neo4j_to_visjs_graph(
                        neo4j_nodes, neo4j_edges
                    )
                    graph_html_content = generate_html_visualization(
                        vis_nodes, vis_edges, height=600
                    )

                # Filter out graph data from results before passing to LLM
                clean_results = []
                for result in cypher_results:
                    if isinstance(result, dict):
                        clean_result = {
                            k: v
                            for k, v in result.items()
                            if k not in ["graph_nodes", "graph_edges"]
                        }
                        clean_results.append(clean_result)
                    else:
                        clean_results.append(result)

                retrieved_context = {
                    "cypher_query": cypher_query,
                    "results": clean_results,
                }
            except Exception as e:
                retrieved_context = {"error": str(e)}
                print("\n\n####### LLM Cypher retrieval error: #######\n\n")
                print(retrieved_context)
            st.session_state.last_graph_html = graph_html_content
            st.session_state.last_retrieval_mode = "LLM-generated Cypher"

    # LLM response

    if modules_missing:
        print("modules missing, using placeholder LLM answer.")
        answer = placeholder_llm_answer(user_input, retrieved_context, llm_model_choice)
    else:
        if llm_model_choice == "A":
            try:
                answer = deepseek_generate_answer(user_input, retrieved_context)
            except Exception as e:
                answer = placeholder_llm_answer(
                    user_input, retrieved_context, llm_model_choice
                )
                print("\n\n####### LLM engine error: #######\n\n")
                print(str(e))
        elif llm_model_choice == "B":
            try:
                answer = llama_generate_answer(user_input, retrieved_context)
            except Exception as e:
                answer = placeholder_llm_answer(
                    user_input, retrieved_context, llm_model_choice
                )
                print("\n\n####### LLM engine error: #######\n\n")
                print(str(e))
        else:  # Gemma (C)
            try:
                answer = gemma_generate_answer(user_input, retrieved_context)
            except Exception as e:
                answer = placeholder_llm_answer(
                    user_input, retrieved_context, llm_model_choice
                )
                print("\n\n####### LLM engine error: #######\n\n")
                print(str(e))

    # Append assistant reply
    st.session_state.history.append({"role": "assistant", "text": answer})

# Display chat history
with st.container():
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["text"])
        else:
            st.chat_message("assistant").write(msg["text"])

# Display graph visualization if available
if st.session_state.last_graph_html:
    st.markdown("---")
    with st.expander("Graph Visualization"):
        st.markdown(f"*Retrieved via {st.session_state.last_retrieval_mode}*")
        st.components.v1.html(
            st.session_state.last_graph_html, height=650, scrolling=False
        )
        st.markdown("---")
        st.markdown(
            """
            **Graph Visualization Tips:**
            - Hover over nodes to see full details
            - Drag nodes to rearrange
            - Scroll to zoom in/out
            - Use navigation buttons (top left) to interact with the graph
            """
        )


if user_input:
    # Under-the-hood expander showing raw context returned
    with st.expander("Raw retrieval context"):
        # Show the last retrieved context if available
        if "retrieved_context" in locals():
            st.json(retrieved_context)
        else:
            st.write("No retrieval performed yet.")

    with st.expander("Debug & Transparency"):
        st.subheader("Intents")
        st.code(
            (
                "\n".join(st.session_state.last_intents)
                if st.session_state.last_intents
                else "No intents yet"
            ),
            language="text",
        )

        st.subheader("Cypher Queries")
        st.code(
            (
                "\n".join(
                    CYPHER_TEMPLATE_LIBRARY.get(intent, "--missing--")
                    for intent in st.session_state.last_intents
                )
                if st.session_state.last_intents
                else "No queries yet"
            ),
            language="cypher",
        )

        st.subheader("Last Query")
        query = (
            st.session_state.history[-2]["text"]
            if len(st.session_state.history) >= 2
            else ""
        )
        st.write(query if query else "No queries yet")

        st.subheader("Last Entities")
        st.write(
            st.session_state.last_entities
            if st.session_state.last_entities
            else "No entities yet"
        )
