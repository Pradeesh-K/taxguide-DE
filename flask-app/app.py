from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# Service URLs inside Minikube / cluster
OLLAMA_URL = "http://ollama:11434"
VECTOR_STORE_URL = "http://vector-store:5002"
EMBEDDING_URL = "http://embedding-service:5001/embed"

# System prompt for RAG
SYSTEM_PROMPT = "You are a helpful assistant that answers questions based on context provided."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """
    Chat endpoint: sends raw question text to the vector store, gets top chunks,
    builds a prompt, and calls the LLM.
    """
    try:
        data = request.get_json(force=True)
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"answer": "Please provide a question."})

        # 1️⃣ Query vector store for top-k relevant chunks
        try:
            vector_resp = requests.post(
                f"{VECTOR_STORE_URL}/search",
                json={
                    "text": question,   # just text, let vector store handle embedding
                    "k": 5,            # adjust top-k as needed
                    "category": data.get("category")  # optional category filter
                },
                timeout=10
            )
            vector_resp.raise_for_status()
            top_chunks = vector_resp.json().get("results", [])
        except Exception as e:
            return jsonify({"answer": f"Vector store call failed: {str(e)}", "top_chunks": []})

        # 2️⃣ Build context for LLM
        context_text = ""
        for chunk in top_chunks:
            text = chunk.get("text", "")
            doc_id = chunk.get("doc_id", "unknown")
            context_text += f"[{doc_id}] {text}\n"

        prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context_text}\nQuestion: {question}"

        # 3️⃣ Call Ollama LLM
        try:
            llm_resp = requests.post(
                f"{OLLAMA_URL}/v1/completions",
                json={"model": "qwen:0.5b", "prompt": prompt},
                timeout=300
            )
            llm_resp.raise_for_status()
            answer = llm_resp.json()["choices"][0]["text"]
        except Exception as e:
            answer = f"LLM call failed: {str(e)}"

        # 4️⃣ Return answer and top chunks
        return jsonify({
            "answer": answer,
            "top_chunks": top_chunks
        })

    except Exception as e:
        return jsonify({"answer": f"Unexpected error: {str(e)}", "top_chunks": []})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)