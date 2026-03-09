# TaxGuide DE

A specialized AI assistant for **German income tax**. TaxGuide DE provides **clear, contextual answers** to tax questions, with **direct citations from official regulations and law documents**. Built with a lightweight RAG (Retrieval-Augmented Generation) architecture, it runs fully on CPU-friendly infrastructure and local Kubernetes.

---

## Project Overview

**TaxGuide DE** is a ultra light CPU-friendly RAG chatbot that combines:

* **LLM**: Ollama’s `qwen:0.5b`
* **Embeddings**: SentenceTransformer (`all-MiniLM-L6-v2`)
* **Vector Store**: FAISS
* **Web App/API**: Flask
* **Container Orchestration**: Kubernetes (Minikube)

It demonstrates **ML system design, microservice orchestration, and persistent storage handling** without needing high-end GPU hardware.

Screenshots

[rag bot answer with references](images/rag bot answer with references.PNG) – shows how answers include direct citations from official tax documents, making them verifiable.

[rag bot asking question](images/rag bot asking question.PNG) – example of a user submitting a question to the chatbot.

[rag chatbot user interface](images/rag chatbot user interface.PNG) – the UI has two sections: on the left, a chat interface where users ask questions; on the right, the relevant sections of the tax document used to answer the question. This design ensures answers are traceable and verifiable.

## 🏗️ Architecture

[User Browser]
↓
[Flask API / UI Pod]
↓
[Vector Store Pod] ←→ [Embedding Service Pod]
↓
[LLM Pod (Ollama)]

* **Flask API / UI**: Accepts user queries and returns answers with relevant context.
* **Embedding Service**: Converts text into vector representations using MiniLM.
* **Vector Store (FAISS)**: Stores and retrieves text chunks based on embeddings.
* **LLM (Ollama)**: Generates answers using retrieved context.

All components are deployed on **Minikube** with PVC-backed persistent storage.

---

## Tech Stack

* **LLM**: Ollama qwen:0.5b
* **Embeddings**: SentenceTransformer (`all-MiniLM-L6-v2`)
* **Vector Store**: FAISS
* **Web/API**: Flask
* **Orchestration**: Kubernetes (Minikube)
* **Persistent Storage**: PVCs for FAISS index & Ollama model

---

## 📁 Repository Structure

EdgeRAG/
├── embedding-service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── flask-app/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── llm-service/
├── vector-store/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── images/
│   ├── rag bot answer with references.PNG
│   ├── rag bot asking question.PNG
│   └── rag chatbot user interface.PNG
├── k8s/
│   ├── embedding-service.yaml
│   ├── flask-app.yaml
│   ├── ollama-deployment.yaml
│   ├── ollama-pvc.yaml
│   ├── ollama-service.yaml
│   └── vector-store-service.yaml
├── LICENSE
├── vector_store_helper.py
└── vs_help.txt

---

## 💾 Data Flow

1. **User Query** → Flask API
2. Flask calls **Embedding Service** → gets vector
3. Vector passed to **FAISS Vector Store** → top-k relevant chunks
4. Flask builds **RAG Prompt** → sends to Ollama LLM
5. **LLM generates answer** using retrieved context
6. Flask returns **answer + source chunks** to user

---

## 🔧 Development & Deployment

* **Minikube**: single-node Kubernetes cluster (CPU-friendly)
* **Persistent Volumes**: Ollama models & FAISS index persist across pod restarts
* **Docker**: each service containerized for reproducibility
* **Flask**: exposes `/chat` API & minimal HTML frontend
* **Embedding Model**: MiniLM small, fast on CPU

---

## ⚡ Highlights / CV Value

* Demonstrates **ML + Infra + Kubernetes orchestration**
* Shows handling of **stateful workloads** via PVC
* CPU-only RAG architecture suitable for **resource-constrained environments**
* Modular microservices: LLM, embeddings, vector store, Flask API

---

## 📝 Usage

1. Deploy services to Minikube (Flask, Embedding, Vector Store, Ollama)
2. Ensure **PVCs** are bound and Ollama has downloaded `qwen:0.5b`
3. Start Flask web UI → `/chat` endpoint accepts German tax questions
4. Returns **answers with top chunks** as citations

---

## 📸 Screenshots

* rag bot answer with references
* rag bot asking question
* rag chatbot user interface

---

## 📚 References

* [FAISS](https://github.com/facebookresearch/faiss)
* [SentenceTransformers](https://www.sbert.net/)
* [Ollama](https://ollama.com/)
* [Kubernetes Docs](https://kubernetes.io/docs/)

---

#
