import pickle
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from pyprojroot import here

_root_path  = str(here())
_utils_path = str(here("utils"))
for _p in (_root_path, _utils_path):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from utils.LLM_load import llm
from utils.rankingV2 import Ranking
from tools.rag_state import get_state, is_ready, update_state

# ── Constants ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVER_K      = 20
ENSEMBLE_WEIGHTS = [0.5, 0.5]


class RAGQueryTool:

    def run(self, query: str, topic_slug: str, k: int = 10, use_alt_query: bool = True) -> dict:
        if not is_ready(topic_slug):
            if not self._reload_from_disk(topic_slug):
                return {
                    "status":  "error",
                    "message": (
                        f"RAG store for '{topic_slug}' not found. "
                        f"Run RAGEmbedTool first or ensure data/rag/{topic_slug}/ exists."
                    ),
                }

        state = get_state(topic_slug)

        try:
            if use_alt_query:
                alt_query = llm(query).llm_call()
            else:
                alt_query = ""

            context = Ranking(
                query,
                alt_query,
                state["retriever"],
                state["parent"],
                k=k,
            ).quering()

            return {
                "status":            "success",
                "topic_slug":        topic_slug,
                "original_query":    query,
                "alternative_query": alt_query if use_alt_query else None,
                "context":           context,
            }

        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _reload_from_disk(self, topic_slug: str) -> bool:
        try:
            chroma_dir = here(f"data/rag/{topic_slug}/chroma_db")
            parent_pkl = here(f"data/rag/{topic_slug}/parent_chunks.pkl")

            if not chroma_dir.exists() or not parent_pkl.exists():
                return False

            embeddings  = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            vectorstore = Chroma(
                persist_directory=str(chroma_dir),
                embedding_function=embeddings,
                collection_name=topic_slug,
            )
            chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})

            with open(parent_pkl, "rb") as f:
                parent_chunks = pickle.load(f)

            if not parent_chunks:
                return False

            bm25_retriever   = BM25Retriever.from_documents(parent_chunks)
            bm25_retriever.k = RETRIEVER_K

            ensemble_retriever = EnsembleRetriever(
                retrievers=[chroma_retriever, bm25_retriever],
                weights=ENSEMBLE_WEIGHTS,
            )

            update_state(topic_slug, ensemble_retriever, parent_chunks, str(chroma_dir))
            return True

        except Exception:
            return False


# ── Run directly ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TOPIC_SLUG    = "sadhguru_20260418_030200"          # change me
    QUERY         = "is there a god"  # change me
    K             = 20
    USE_ALT_QUERY = False                       # True to use LLM alternative query

    tool   = RAGQueryTool()
    print(f"Querying '{TOPIC_SLUG}' ...\n")

    result = tool.run(QUERY, TOPIC_SLUG, k=K, use_alt_query=USE_ALT_QUERY)

    if result["status"] == "success":
        print(f"Original query   : {result['original_query']}")
        print(f"Alternative query: {result['alternative_query']}")
        print(f"\n--- Context ---\n{result['context']}")
    else:
        print(f"Error: {result['message']}")
