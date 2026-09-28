"""
test_filtered_query.py

Tests whether filtering by section='documents_required' actually
surfaces the right scheme's chunk, the way main.py's boosting logic
is supposed to.

USAGE:
    python test_filtered_query.py --db_path ./chroma_db --question "documents required for Ayushman Bharat health card"
"""

import argparse
import chromadb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_path", default="./chroma_db")
    parser.add_argument("--collection", default="schemes")
    parser.add_argument("--question", required=True)
    parser.add_argument("--n_results", type=int, default=5)
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=args.db_path)
    collection = client.get_collection(name=args.collection)

    print("=== FILTERED QUERY: section = documents_required ===\n")
    results = collection.query(
        query_texts=[args.question],
        n_results=args.n_results,
        where={"section": "documents_required"},
    )

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances)):
        print(f"--- Result {i+1} (scheme: {meta.get('scheme_name')}, distance: {dist:.3f}) ---")
        print(doc[:300])
        print()


if __name__ == "__main__":
    main()
