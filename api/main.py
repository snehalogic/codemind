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
from llm.test_generator import generate_and_pr
from llm.security_scanner import scan_repo
from llm.readme_generator import generate_readme_and_pr
from llm.code_quality import score_repo

class ReadmeRequest(BaseModel):
    repo_url: str

class TestRequest(BaseModel):
    repo_url: str
    file_path: str

app = FastAPI()

from fastapi.responses import FileResponse

@app.get("/")
def serve_ui():
    """Serve the main CodeMind HTML frontend."""
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
    """Clone, parse, graph, and embed a GitHub repo. Returns full analysis results."""
    try:
        url = req.url.strip()
        if not url.startswith("https://github.com/"):
            return {"error": "Please provide a valid GitHub URL"}

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
        repo_state["repo_url"] = url

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
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


@app.post("/chat")
def chat(req: QuestionRequest):
    """Answer a question about the currently analyzed codebase using RAG + Groq."""
    try:
        if not repo_state.get("ready"):
            return {"answer": "Please analyze a repo first."}
        if not req.question.strip():
            return {"answer": "Please ask a valid question."}
        answer = ask_codebase(req.question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Something went wrong: {str(e)}"}


@app.get("/graph")
def get_graph():
    """Return the HTML content of the generated dependency graph."""
    try:
        with open("ui/graph.html", "r", encoding="utf-8") as f:
            return {"html": f.read()}
    except FileNotFoundError:
        return {"html": "<p>No graph yet — analyze a repo first.</p>"}
    except Exception as e:
        return {"html": f"<p>Error loading graph: {str(e)}</p>"}


@app.post("/generate-tests")
def generate_tests(req: TestRequest):
    """Generate pytest tests for a file and open a GitHub PR automatically."""
    try:
        if not repo_state.get("ready"):
            return {"error": "Please analyze a repo first."}
        result = generate_and_pr(req.repo_url, req.file_path)
        return result
    except Exception as e:
        return {"error": f"Test generation failed: {str(e)}"}

@app.post("/generate-readme")
def generate_readme(req: ReadmeRequest):
    """Generate a professional README.md and open a GitHub PR."""
    try:
        result = generate_readme_and_pr(req.repo_url)
        return result
    except Exception as e:
        return {"error": f"README generation failed: {str(e)}"}

@app.post("/code-quality")
def code_quality(req: RepoRequest):
    """Run a full code quality analysis and return scores and recommendations."""
    try:
        repo_path = clone_repo(req.url)
        files = walk_repo(repo_path)
        parsed = parse_repo(files)
        report = score_repo(files, parsed)
        return report
    except Exception as e:
        return {"error": f"Quality check failed: {str(e)}"}

@app.post("/security-scan")
def security_scan(req: RepoRequest):
    """Scan all Python files in a repo for security vulnerabilities."""
    try:
        if not req.url.startswith("https://github.com/"):
            return {"error": "Please provide a valid GitHub URL"}
        repo_path = clone_repo(req.url)
        files = walk_repo(repo_path)
        report = scan_repo(files)
        return report
    except Exception as e:
        return {"error": f"Security scan failed: {str(e)}"}