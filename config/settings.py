# config/settings.py

from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
_dotenv_path = Path(__file__).resolve().parents[1] / ".env"
if _dotenv_path.exists():
    load_dotenv(dotenv_path=_dotenv_path)
else:
    load_dotenv()


EMBEDDING_MODEL_OPTIONS = {
    "all-MiniLM-L6-v2": "A",
    "all-mpnet-base-v2": "B",
}

MODEL_OPTIONS = {
    "DeepSeek": "A",
    "Llama": "B",
    "Gemma": "C",
}

VECTOR_TOP_K = 5

DEFAULT_RETRIEVAL_MODE = (
    "Baseline (Cypher)"  # options: "Baseline (Cypher)", "Embeddings", "Hybrid"
)
