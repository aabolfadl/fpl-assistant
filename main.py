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
from modules.llm_helper import classify_with_deepseek
from modules.llm_engine import (
    deepseek_generate_answer,
    gemma_generate_answer,
    llama_generate_answer,
)

st.set_page_config(page_title="Cole you later", layout="wide")

st.title("FPL Graph-RAG — Assistant")
st.markdown(
    "Ask questions about Fantasy Premier League (player stats, fixture lookups, comparisons, transfer recs)."
)

# Sidebar controls
with st.sidebar:
    st.header("Configuration")

    llm_key_choice = st.selectbox("Choose LLM", list(MODEL_OPTIONS.keys()), index=0)
    llm_model_choice = MODEL_OPTIONS[llm_key_choice]

    embedding_key_choice = st.selectbox(
        "Choose embedding model", list(EMBEDDING_MODEL_OPTIONS.keys()), index=0
    )
    embedding_model_choice = EMBEDDING_MODEL_OPTIONS[embedding_key_choice]

    RETRIEVAL_OPTIONS = ["Baseline (Cypher)", "Embeddings (Vector)", "Hybrid"]

    retrieval_mode = st.radio(
        "Retrieval Mode",
        RETRIEVAL_OPTIONS,
        index=RETRIEVAL_OPTIONS.index(DEFAULT_RETRIEVAL_MODE),
    )

    k = st.number_input(
        "Top-K results (for retrieval)", min_value=1, max_value=20, value=5
    )

    show_debug = st.checkbox("Show debug info", value=False)

# Chat history in session state
if "history" not in st.session_state:
    st.session_state.history = []

# Input box
user_input = st.chat_input("Ask about FPL — e.g. 'Who should I captain for GW10?'")

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
        # TODO more than one query can be detected mesh akeed
        intent = classify_with_deepseek(
            user_input, list(CYPHER_TEMPLATE_LIBRARY.keys())
        )
    except Exception as e:
        intent = local_intent_classify(user_input)

    entities = preprocessing.extract_entities(user_input)
    print("\n\n####### Extracted entities: #######\n\n")
    print(entities)

    # Retrieval
    if modules_missing:
        retrieved_context = placeholder_retrieve(intent, entities, retrieval_mode, k=k)
    else:
        if retrieval_mode == "Baseline (Cypher)":
            try:
                retrieved_context = cypher_retriever.retrieve_data_via_cypher(
                    intent, entities, limit=k
                )
                print("\n\n####### Cypher retrieval result: #######\n\n")
                print(retrieved_context)
            except Exception as e:
                retrieved_context = {"error": str(e)}
                print("\n\n####### Cypher retrieval error: #######\n\n")
                print(retrieved_context)
                if show_debug:
                    st.write("Cypher retrieval error:")
                    st.text(str(e))
        elif retrieval_mode == "Embeddings (Vector)":
            try:
                retrieved_context = vector_retriever.vector_search(
                    entities, top_k=k, model_choice=embedding_model_choice
                )
                print("\n\n####### Vector retrieval result: #######\n\n")
                print(retrieved_context)
            except Exception as e:
                retrieved_context = {"error": str(e)}
                print("\n\n####### Vector retrieval error: #######\n\n")
                print(retrieved_context)
                if show_debug:
                    st.write("Vector retrieval error:")
                    st.text(str(e))
        else:  # Hybrid
            try:
                c_res = cypher_retriever.retrieve_data_via_cypher(
                    intent, entities, limit=k
                )
            except Exception as e:
                c_res = {"error": str(e)}
                if show_debug:
                    st.write("Cypher retrieval error (hybrid):")
                    st.text(str(e))

            try:
                v_res = vector_retriever.vector_search(
                    entities, top_k=k, model_choice=embedding_model_choice
                )
            except Exception as e:
                v_res = {"error": str(e)}
                if show_debug:
                    st.write("Vector retrieval error (hybrid):")
                    st.text(str(e))

            retrieved_context = {"cypher": c_res, "vector": v_res}

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
                if show_debug:
                    st.write("LLM engine error:")
                    st.text(str(e))
        elif llm_model_choice == "B":
            try:
                answer = llama_generate_answer(user_input, retrieved_context)
            except Exception as e:
                answer = placeholder_llm_answer(
                    user_input, retrieved_context, llm_model_choice
                )
                print("\n\n####### LLM engine error: #######\n\n")
                print(str(e))
                if show_debug:
                    st.write("LLM engine error:")
                    st.text(str(e))
        else:  # Gemma (C)
            try:
                answer = gemma_generate_answer(user_input, retrieved_context)
            except Exception as e:
                answer = placeholder_llm_answer(
                    user_input, retrieved_context, llm_model_choice
                )
                print("\n\n####### LLM engine error: #######\n\n")
                print(str(e))
                if show_debug:
                    st.write("LLM engine error:")
                    st.text(str(e))

    # Append assistant reply
    st.session_state.history.append({"role": "assistant", "text": answer})

# Display chat history
if show_debug:
    chat_col, debug_col = st.columns([3, 1])
else:
    # Create a single column for the chat when debug panel is hidden.
    chat_col = st.columns([1])[0]
    debug_col = None
with chat_col:
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["text"])
        else:
            st.chat_message("assistant").write(msg["text"])

# Debug / transparency panel
if show_debug:
    with debug_col:
        st.header("Debug / Transparency")
        st.subheader("Cypher templates (sample)")
        st.code(
            CYPHER_TEMPLATE_LIBRARY.get("PLAYER_RECENT_STATS", "--missing--"),
            language="cypher",
        )

        st.subheader("Last Query / Entities")
        last_entities = (
            st.session_state.history[-2]["text"]
            if len(st.session_state.history) >= 2
            else ""
        )
        st.write(last_entities)

        if modules_missing:
            st.error("Project modules (modules/*) not importable.")
            st.write("Import error summary:")
            st.text(str(_import_error))
            st.write(
                "Implement `modules/preprocessing.py`, `modules/cypher_retriever.py`, and"
                "`modules/vector_retriever.py` to enable full functionality."
            )

# Under-the-hood expander showing raw context returned
with st.expander("Raw retrieval context"):
    # Show the last retrieved context if available
    if "retrieved_context" in locals():
        st.json(retrieved_context)
    else:
        st.write("No retrieval performed yet.")
