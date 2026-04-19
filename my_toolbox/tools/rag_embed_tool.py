import pickle
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from pyprojroot import here

_root_path = str(here())
if _root_path not in sys.path:
    sys.path.insert(0, _root_path)

from tools.rag_state import update_state

# ── Constants ─────────────────────────────────────────────────────────────────
PARENT_CHUNK_SIZE    = 3000
PARENT_CHUNK_OVERLAP = 500
CHILD_CHUNK_SIZE     = 500
CHILD_CHUNK_OVERLAP  = 50
EMBEDDING_MODEL      = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVER_K          = 20
ENSEMBLE_WEIGHTS     = [0.5, 0.5]


def _get_rag_paths(topic_slug: str):
    chroma_dir = here(f"data/rag/{topic_slug}/chroma_db")
    parent_pkl = here(f"data/rag/{topic_slug}/parent_chunks.pkl")
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return str(chroma_dir), parent_pkl


class RAGEmbedTool:

    def run(self, folder_path: str, catalog_id: str = None) -> dict:
        """
        Accepts a topic folder e.g. data/transcripts/crewai_tutorial.
        Walks each subfolder, finds the PDF inside, and embeds all of them
        into a single ChromaDB store keyed by catalog_id (if provided) or the folder name.
        """
        topic_dir = Path(folder_path)
        if not topic_dir.exists() or not topic_dir.is_dir():
            return {"status": "error", "message": f"Folder not found: {folder_path}"}

        topic_slug = catalog_id if catalog_id else topic_dir.name

        pdfs = sorted(topic_dir.rglob("*.pdf"))
        if not pdfs:
            return {"status": "error", "message": f"No PDF files found under {folder_path}"}

        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=PARENT_CHUNK_SIZE, chunk_overlap=PARENT_CHUNK_OVERLAP
        )
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHILD_CHUNK_SIZE, chunk_overlap=CHILD_CHUNK_OVERLAP
        )

        chroma_dir, parent_pkl = _get_rag_paths(topic_slug)

        existing_parents = []
        if parent_pkl.exists():
            with open(parent_pkl, "rb") as f:
                existing_parents = pickle.load(f)

        all_parents       = list(existing_parents)
        all_child_chunks  = []
        embedded_files    = []
        errors            = []

        for pdf in pdfs:
            try:
                raw_docs = PyPDFLoader(str(pdf)).load()

                tagged_parents = parent_splitter.split_documents(raw_docs)
                for parent in tagged_parents:
                    parent.metadata["parent_id"]  = hash(parent.page_content[:100])
                    parent.metadata["video_name"] = pdf.parent.name

                child_chunks = []
                for parent in tagged_parents:
                    for child in child_splitter.split_documents([parent]):
                        child.metadata["parent_id"] = parent.metadata["parent_id"]
                        child_chunks.append(child)

                all_parents      += tagged_parents
                all_child_chunks += child_chunks
                embedded_files.append(str(pdf))
                print(f"  Loaded: {pdf.relative_to(topic_dir)}")

            except Exception as exc:
                errors.append({"file": str(pdf), "error": str(exc)})
                print(f"  Skipped {pdf.name}: {exc}")

        if not all_child_chunks:
            return {"status": "error", "message": "All PDFs failed to load.", "errors": errors}

        try:
            embeddings  = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            vectorstore = Chroma.from_documents(
                all_child_chunks,
                embeddings,
                persist_directory=chroma_dir,
                collection_name=topic_slug,
            )
            chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})

            bm25_retriever   = BM25Retriever.from_documents(all_child_chunks)
            bm25_retriever.k = RETRIEVER_K

            ensemble_retriever = EnsembleRetriever(
                retrievers=[chroma_retriever, bm25_retriever],
                weights=ENSEMBLE_WEIGHTS,
            )

            with open(parent_pkl, "wb") as f:
                pickle.dump(all_parents, f)

            update_state(topic_slug, ensemble_retriever, all_parents, folder_path)

        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        return {
            "status":         "success",
            "topic_slug":     topic_slug,
            "embedded_files": embedded_files,
            "parent_chunks":  len(all_parents),
            "child_chunks":   len(all_child_chunks),
            "chroma_dir":     chroma_dir,
            "parent_pkl":     str(parent_pkl),
            "errors":         errors,
        }


# ── Run directly ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    FOLDER_PATH = rf"C:\Users\tvlan\Documents\1.0 Python\3.0 CrewAI\31.0 Selenium+Transcriber+Cleaned\data\transcripts\crew_ai_tutorial"

    tool   = RAGEmbedTool()
    print(f"Embedding PDFs in '{FOLDER_PATH}' ...")

    result = tool.run(FOLDER_PATH)

    if result["status"] == "success":
        print("\nEmbedding complete.")
        print(f"  Topic         : {result['topic_slug']}")
        print(f"  Files embedded: {len(result['embedded_files'])}")
        for f in result["embedded_files"]:
            print(f"    - {f}")
        print(f"  Parent chunks : {result['parent_chunks']}")
        print(f"  Child chunks  : {result['child_chunks']}")
        print(f"  ChromaDB dir  : {result['chroma_dir']}")
        print(f"  Parent pkl    : {result['parent_pkl']}")
        if result["errors"]:
            print(f"  Skipped ({len(result['errors'])}):")
            for e in result["errors"]:
                print(f"    - {e['file']}: {e['error']}")
    else:
        print(f"Error: {result['message']}")
