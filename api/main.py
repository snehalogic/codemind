import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ingestion.cloner import clone_repo, walk_repo
from ingestion.parser import parse_repo
from graph.dependency import build_dependency_graph, get_graph_stats, visualize_graph
from rag.embedder import build_vector_store
from llm.groq_llm import ask_codebase
from pathlib import Path

app = FastAPI()

from fastapi.responses import FileResponse

@app.get("/")
def serve_ui():
    return FileResponse("ui/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

repo_state = {}

class RepoRequest(BaseModel):
    url: str

class QuestionRequest(BaseModel):
    question: str

@app.post("/analyze")
def analyze(req: RepoRequest):
    url = req.url
    repo_name = url.rstrip("/").split("/")[-1]

    repo_path = clone_repo(url)
    files = walk_repo(repo_path)
    parsed = parse_repo(files)

    G = build_dependency_graph(parsed)
    stats = get_graph_stats(G)
    visualize_graph(G, output_path="ui/graph.html")

    python_files = [f for f in files if f["extension"] == ".py"]
    build_vector_store(python_files)

    ext_counts = {}
    for f in files:
        ext = f["extension"] or "no extension"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    repo_state["ready"] = True
    repo_state["repo_name"] = repo_name

    most_imported = [
        {"file": Path(node).name, "count": count}
        for node, count in stats["most_imported"]
    ]

    return {
        "repo_name": repo_name,
        "total_files": len(files),
        "python_files": len(python_files),
        "total_chars": sum(f["size"] for f in files),
        "graph_nodes": stats["total_nodes"],
        "graph_edges": stats["total_edges"],
        "most_imported": most_imported,
        "file_types": ext_counts,
        "parsed_files": [
            {
                "path": p["relative_path"],
                "functions": len(p["functions"]),
                "classes": len(p["classes"]),
            }
            for p in parsed[:50]
        ]
    }

@app.post("/chat")
def chat(req: QuestionRequest):
    if not repo_state.get("ready"):
        return {"answer": "Please analyze a repo first."}
    answer = ask_codebase(req.question)
    return {"answer": answer}

@app.get("/graph")
def get_graph():
    try:
        with open("ui/graph.html", "r", encoding="utf-8") as f:
            return {"html": f.read()}
    except:
        return {"html": "<p>No graph yet.</p>"}