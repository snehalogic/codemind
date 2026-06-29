import chromadb
from pathlib import Path
import sys
sys.path.append("..")
from config import MAX_CHUNK_SIZE, CHUNK_OVERLAP


def chunk_file(file_info: dict) -> list[dict]:
    content = file_info["content"]
    path = file_info["relative_path"]
    chunks = []
    start = 0

    while start < len(content):
        end = start + MAX_CHUNK_SIZE
        chunk_text = content[start:end]
        chunks.append({
            "text": chunk_text,
            "source": path,
            "chunk_index": len(chunks)
        })
        start += MAX_CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def build_vector_store(files: list[dict], collection_name: str = "codemind"):
    client = chromadb.PersistentClient(path="./chroma_db")

    try:
        client.delete_collection(collection_name)
    except:
        pass

    collection = client.create_collection(collection_name)

    all_chunks = []
    for f in files:
        all_chunks.extend(chunk_file(f))

    print(f"Total chunks to embed: {len(all_chunks)}")

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        collection.add(
            documents=[c["text"] for c in batch],
            metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in batch],
            ids=[f"{c['source']}_{c['chunk_index']}" for c in batch]
        )
        print(f"Embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks...")

    print("Vector store built successfully!")
    return collection


def query_vector_store(query: str, collection_name: str = "codemind", n_results: int = 5):
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(collection_name)
    results = collection.query(query_texts=[query], n_results=n_results)
    return results


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.cloner import clone_repo, walk_repo

    repo_path = clone_repo("https://github.com/tiangolo/fastapi")
    files = walk_repo(repo_path)

    python_files = [f for f in files if f["extension"] == ".py"]
    print(f"Building vector store from {len(python_files)} Python files...")
    build_vector_store(python_files)

    print("\nTesting a query...")
    results = query_vector_store("how does authentication work")
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i]["source"]
        print(f"\n--- Result {i+1}: {source} ---")
        print(doc[:200])