import os
import sys

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import clean_text, chunk_text, load_documents

COLLECTION_NAME = "fiu_housing"
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

# Loaded once at module import; reused across build and query calls.
_model = SentenceTransformer("all-MiniLM-L6-v2")


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=DB_PATH)


def build_vector_store() -> None:
    """Ingest all PDFs, embed chunks, and load them into ChromaDB."""
    client = _client()

    # Always rebuild from scratch so reruns don't duplicate chunks.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    # cosine distance keeps scores in [0, 2]; lower = more similar.
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    documents = load_documents(DOCS_DIR)
    all_chunks: list[tuple[str, str]] = []
    for raw_text, source in documents:
        cleaned = clean_text(raw_text)
        all_chunks.extend(chunk_text(cleaned, source))

    print(f"Embedding {len(all_chunks)} chunks with all-MiniLM-L6-v2 ...", flush=True)
    texts = [c for c, _ in all_chunks]
    embeddings = _model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=[f"chunk_{i}" for i in range(len(all_chunks))],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {"source": src, "chunk_index": i}
            for i, (_, src) in enumerate(all_chunks)
        ],
    )
    print(f"Stored {len(all_chunks)} chunks in ChromaDB at {DB_PATH}", flush=True)


def query(question: str, k: int = 5) -> list[tuple[str, str]]:
    """Return top-k (chunk_text, source_filename) pairs for *question*."""
    collection = _client().get_collection(COLLECTION_NAME)
    q_emb = _model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=q_emb,
        n_results=k,
        include=["documents", "metadatas"],
    )
    return [
        (doc, meta["source"])
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]


def _safe_print(text: str) -> None:
    encoded = text.encode(sys.stdout.encoding or "utf-8", errors="replace")
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    build_vector_store()

    eval_queries = [
        "What specific problems do students report about The One at University City?",
        "What is the monthly rent range at Advenir at University Park, and what do reviewers say about management?",
        "According to the Fall 2025 off-campus guide, what hidden fees does Terrazul charge on top of listed rent?",
        "What maintenance issues did students report at University Apartments (UA)?",
        "What advice do students give to international students looking for affordable housing near FIU for spring intake?",
    ]

    # Pull distances directly from ChromaDB for the test report.
    collection = _client().get_collection(COLLECTION_NAME)

    _safe_print("\n" + "=" * 70)
    _safe_print("RETRIEVAL TEST — 5 EVALUATION QUERIES")
    _safe_print("=" * 70)

    for i, q in enumerate(eval_queries, 1):
        _safe_print(f"\nQ{i}: {q}")
        _safe_print("-" * 70)
        q_emb = _model.encode([q]).tolist()
        results = collection.query(
            query_embeddings=q_emb,
            n_results=5,
            include=["documents", "metadatas", "distances"],
        )
        for rank, (doc, meta, dist) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ),
            1,
        ):
            _safe_print(
                f"  [{rank}] source: {meta['source']}  distance: {dist:.4f}"
            )
            _safe_print(
                f"       {doc[:300]}{'...' if len(doc) > 300 else ''}"
            )
        _safe_print("")
