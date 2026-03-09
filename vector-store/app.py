from flask import Flask, request, jsonify
import faiss
import numpy as np
import os
import pickle
import requests

app = Flask(__name__)

# ------------------------
# Paths
# ------------------------
INDEX_PATH = "/data/faiss.index"
META_PATH = "/data/metadata.pkl"

# ------------------------
# FAISS setup
# ------------------------
dim = 384  # embedding dimension

if os.path.exists(INDEX_PATH):
    with open(INDEX_PATH, "rb") as f:
        index = pickle.load(f)
    print("[DEBUG] Loaded existing FAISS index")
else:
    index = faiss.IndexFlatL2(dim)
    print("[DEBUG] Created new FAISS index")

# Metadata store
if os.path.exists(META_PATH):
    with open(META_PATH, "rb") as f:
        id_to_metadata = pickle.load(f)
    print("[DEBUG] Loaded existing metadata")
else:
    id_to_metadata = {}
    print("[DEBUG] Created new metadata store")

# ------------------------
# Embedding service URL
# ------------------------
EMBEDDING_URL = "http://embedding-service:5001/embed"

# ------------------------
# TEXT CHUNKING
# ------------------------
def chunk_text(text, chunk_size=100, overlap=10):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    print(f"[DEBUG] Chunked text into {len(chunks)} chunks")
    return chunks

# ------------------------
# ADD DOCUMENT
# ------------------------
@app.route("/add", methods=["POST"])
def add_vector():
    print("[DEBUG] /add called")

    # Handle file upload
    if "file" in request.files:
        f = request.files["file"]
        text = f.read().decode("utf-8")
        doc_id = f.filename
        category = request.form.get("category", "general")
        print(f"[DEBUG] Received file '{doc_id}' with category '{category}'")
    else:
        # fallback to JSON
        data = request.get_json()
        text = data.get("text", "").strip()
        doc_id = data.get("doc_id", "unknown")
        category = data.get("category", "general")
        print(f"[DEBUG] Received JSON doc_id '{doc_id}' category '{category}'")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    chunks = chunk_text(text)
    added_ids = []

    for i, chunk in enumerate(chunks):
        print(f"[DEBUG] Embedding chunk {i} length={len(chunk)}")
        try:
            embed_resp = requests.post(EMBEDDING_URL, json={"text": chunk})
            embedding = embed_resp.json().get("embedding", [])
            print(f"[DEBUG] Chunk {i} embedding length: {len(embedding)}")
            if not embedding:
                print(f"[WARNING] Chunk {i} embedding failed, skipping")
                continue
        except Exception as e:
            print(f"[ERROR] Embedding service failed for chunk {i}: {str(e)}")
            return jsonify({"error": str(e)}), 500

        embedding_np = np.array(embedding, dtype="float32")
        index.add(np.expand_dims(embedding_np, axis=0))
        vector_id = index.ntotal - 1

        id_to_metadata[vector_id] = {
            "text": chunk,
            "category": category,
            "doc_id": doc_id,
            "chunk_index": i
        }
        added_ids.append(vector_id)
        print(f"[DEBUG] Added chunk {i} to FAISS with vector_id={vector_id}")

    # persist
    os.makedirs("/data", exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(index, f)
    with open(META_PATH, "wb") as f:
        pickle.dump(id_to_metadata, f)

    print(f"[DEBUG] Persisted {len(added_ids)} chunks to disk")

    return jsonify({
        "chunks_added": len(added_ids),
        "chunks": chunks  # full chunks for debugging
    })

# ------------------------
# SEARCH
# ------------------------
@app.route("/search", methods=["POST"])
def search_vector():
    print("[DEBUG] /search called")
    data = request.get_json()
    query_text = data.get("text", "").strip()
    k = int(data.get("k", 5))
    category = data.get("category", None)

    print(f"[DEBUG] Searching for '{query_text}', k={k}, category={category}")

    if not query_text:
        return jsonify({"error": "No query text provided"}), 400

    try:
        embed_resp = requests.post(EMBEDDING_URL, json={"text": query_text})
        query_embedding = embed_resp.json().get("embedding", [])
        print(f"[DEBUG] Query embedding length: {len(query_embedding)}")
    except Exception as e:
        print(f"[ERROR] Embedding service failed for query: {str(e)}")
        return jsonify({"error": f"Embedding service failed: {str(e)}"}), 500

    if not query_embedding:
        return jsonify({"error": "Embedding failed"}), 500

    query_np = np.array(query_embedding, dtype="float32").reshape(1, -1)

    try:
        distances, indices = index.search(query_np, k)
        print(f"[DEBUG] FAISS returned indices: {indices}, distances: {distances}")
    except Exception as e:
        print(f"[ERROR] FAISS search failed: {str(e)}")
        return jsonify({"error": f"FAISS search failed: {str(e)}"}), 500

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        meta = id_to_metadata.get(idx)
        if not meta:
            print(f"[WARNING] No metadata for index {idx}")
            continue
        if category and meta["category"] != category:
            continue
        results.append({
            "text": meta["text"],
            "doc_id": meta["doc_id"],
            "chunk_index": meta["chunk_index"],
            "category": meta["category"],
            "distance": float(dist)
        })
        print(f"[DEBUG] Returning result: {meta['doc_id']} chunk {meta['chunk_index']} distance {dist}")

    return jsonify({"results": results})


if __name__ == "__main__":
    os.makedirs("/data", exist_ok=True)
    print("[DEBUG] Starting Flask app on 0.0.0.0:5002")
    app.run(host="0.0.0.0", port=5002, debug=True)