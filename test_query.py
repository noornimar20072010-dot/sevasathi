"""
test_query.py

Quick sanity check: run a real question against your ChromaDB vector
database and see what chunks come back. This tells you if retrieval
is actually working before you build the chatbot on top of it.

USAGE:
    python test_query.py --db_path ./chroma_db --question "What documents do I need for a subsidy scheme?"
"""

import argparse
import chromadb


def main():
    parser = argparse.ArgumentParser(description="Test query against the schemes ChromaDB")
    parser.add_argument("--db_path", default="./chroma_db", help="Path to the chroma_db folder")
    parser.add_argument("--collection", default="schemes", help="Collection name")
    parser.add_argument("--question", required=True, help="Question to search for")
    parser.add_argument("--n_results", type=int, default=3, help="Number of chunks to retrieve")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=args.db_path)
    collection = client.get_collection(name=args.collection)

    results = collection.query(
        query_texts=[args.question],
        n_results=args.n_results,
    )

    print(f"\nQuestion: {args.question}\n")
    print(f"Top {args.n_results} matching chunks:\n")

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances)):
        print(f"--- Result {i+1} (scheme: {meta.get('scheme_name')}, distance: {dist:.3f}) ---")
        print(doc[:400])
        print()


if __name__ == "__main__":
    main()
