"""
ingest.py

Loads schemes_clean.json into a persistent ChromaDB vector database,
ready for retrieval in your RAG chatbot.

USAGE:
    pip install chromadb langchain-text-splitters --break-system-packages
    python ingest.py --input schemes_clean.json --db_path ./chroma_db

This creates a folder called chroma_db/ containing your searchable
vector database. Point your FastAPI backend (built in Antigravity) at
this same folder to query it.
"""

import argparse
import json
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

FIELD_LABELS = {
    "details": "Details",
    "benefits": "Benefits",
    "eligibility": "Eligibility",
    "application_process": "Application Process",
    "documents_required": "Documents Required",
    "faqs": "Frequently Asked Questions",
}


def build_combined_text(scheme: dict) -> str:
    """Combine all scheme fields into one readable document for embedding."""
    parts = [f"Scheme: {scheme.get('scheme_name', 'Unknown')}"]
    for key, label in FIELD_LABELS.items():
        value = scheme.get(key, "").strip()
        if value:
            parts.append(f"{label}: {value}")
    return "\n\n".join(parts)


def ingest(input_path: str, db_path: str, collection_name: str = "schemes"):
    with open(input_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    # Only used as a fallback for any single field that's unusually long
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    client = chromadb.PersistentClient(path=db_path)
    # Uses Chroma's built-in default embedding function (downloads a small
    # local model the first time you run this — needs internet once).
    collection = client.get_or_create_collection(name=collection_name)

    all_docs = []
    all_metadatas = []
    all_ids = []

    for scheme_idx, scheme in enumerate(schemes):
        scheme_name = scheme.get("scheme_name", "Unknown")
        file_name = scheme.get("file", "")
        state_or_ministry = scheme.get("state_or_ministry", "Unknown")

        for field_key, section_label in FIELD_LABELS.items():
            field_text = scheme.get(field_key, "").strip()
            if not field_text:
                continue

            header = f"Scheme: {scheme_name} ({state_or_ministry})\n{section_label}: "

            # Split the RAW field text first (never the header+text combined),
            # so a long field can never produce an orphan chunk that's just
            # the header with no actual content attached.
            if len(field_text) > 500:
                text_pieces = splitter.split_text(field_text)
            else:
                text_pieces = [field_text]

            # Re-attach the header to every piece so each chunk is always
            # a complete, self-contained, labeled unit of meaning.
            sub_chunks = [header + piece for piece in text_pieces]

            for chunk_idx, chunk in enumerate(sub_chunks):
                all_docs.append(chunk)
                all_metadatas.append({
                    "scheme_name": scheme_name,
                    "file": file_name,
                    "section": field_key,
                    "state_or_ministry": state_or_ministry,
                })
                all_ids.append(f"scheme{scheme_idx}_{field_key}_{chunk_idx}")

    if not all_docs:
        print("No documents to ingest. Check your input file.")
        return

    # Chroma recommends batching adds for larger datasets
    batch_size = 100
    for i in range(0, len(all_docs), batch_size):
        collection.add(
            documents=all_docs[i:i + batch_size],
            metadatas=all_metadatas[i:i + batch_size],
            ids=all_ids[i:i + batch_size],
        )
        print(f"Added chunks {i} to {min(i + batch_size, len(all_docs))} of {len(all_docs)}")

    print(f"\nDone. Ingested {len(schemes)} schemes as {len(all_docs)} chunks into '{collection_name}' at {db_path}")


def main():
    parser = argparse.ArgumentParser(description="Ingest cleaned scheme data into ChromaDB")
    parser.add_argument("--input", required=True, help="Path to schemes_clean.json")
    parser.add_argument("--db_path", default="./chroma_db", help="Folder to store the vector database")
    parser.add_argument("--collection", default="schemes", help="Chroma collection name")
    args = parser.parse_args()

    ingest(args.input, args.db_path, args.collection)


if __name__ == "__main__":
    main()
