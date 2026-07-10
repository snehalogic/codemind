```python
import sys
import os
import hashlib
import hmac
import secrets
from fastapi import FastAPI, HTTPException, Depends
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
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Define a secret key for authentication
secret_key = secrets.token_urlsafe(32)

# Define an OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define a function to verify passwords
def verify_password(plain_password, hashed_password):
    return hmac.compare_digest(plain_password, hashed_password)

# Define a function to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # For simplicity, we'll assume the token is the username
    # In a real application, you'd want to verify the token against a database
    return token

class ReadmeRequest(BaseModel):
    repo_url: str

class TestRequest(BaseModel):
    repo_url: str
    file_path: str

app = FastAPI()

# Add authentication to the API
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # For simplicity, we'll assume the username and password are hardcoded
    # In a real application, you'd want to verify the username and password against a database
    if form_data.username != "admin" or not verify_password(form_data.password, "password"):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    # Generate a token for the user
    token = hashlib.sha256((form_data.username + secret_key).encode()).hexdigest()
    return {"access_token": token, "token_type": "bearer"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a dictionary to store the state of the repository
repo_state = {}

class RepoRequest(BaseModel):
    url: str

class QuestionRequest(BaseModel):
    question: str

# Define a route to analyze a repository
@app.post("/analyze")
async def analyze(req: RepoRequest, token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to analyze a repository")
    try:
        # Check if the repository URL is valid
        if not req.url.startswith("https://github.com/"):
            return {"error": "Please provide a valid GitHub URL"}
        
        # Clone the repository
        repo_name = req.url.rstrip("/").split("/")[-1]
        repo_path = clone_repo(req.url)
        
        # Walk the repository and parse the files
        files = walk_repo(repo_path)
        parsed = parse_repo(files)
        
        # Build the dependency graph and get the graph statistics
        G = build_dependency_graph(parsed)
        stats = get_graph_stats(G)
        
        # Visualize the graph
        visualize_graph(G, output_path="ui/graph.html")
        
        # Build the vector store
        python_files = [f for f in files if f["extension"] == ".py"]
        build_vector_store(python_files)
        
        # Get the file extension counts
        ext_counts = {}
        for f in files:
            ext = f["extension"] or "no extension"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        
        # Update the repository state
        repo_state["ready"] = True
        repo_state["repo_name"] = repo_name
        repo_state["repo_url"] = req.url
        
        # Get the most imported files
        most_imported = [
            {"file": Path(node).name, "count": count}
            for node, count in stats["most_imported"]
        ]
        
        # Return the analysis results
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
        # Return an error message if the analysis fails
        return {"error": f"Analysis failed: {str(e)}"}

# Define a route to chat with the user
@app.post("/chat")
async def chat(req: QuestionRequest, token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to chat")
    try:
        # Check if the repository is ready
        if not repo_state.get("ready"):
            return {"answer": "Please analyze a repo first."}
        
        # Check if the question is valid
        if not req.question.strip():
            return {"answer": "Please ask a valid question."}
        
        # Ask the question and return the answer
        answer = ask_codebase(req.question)
        return {"answer": answer}
    except Exception as e:
        # Return an error message if the chat fails
        return {"answer": f"Something went wrong: {str(e)}"}

# Define a route to get the graph
@app.get("/graph")
async def get_graph(token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to view the graph")
    try:
        # Open the graph file and return its contents
        with open("ui/graph.html", "r", encoding="utf-8") as f:
            return {"html": f.read()}
    except FileNotFoundError:
        # Return a message if the graph file does not exist
        return {"html": "<p>No graph yet — analyze a repo first.</p>"}
    except Exception as e:
        # Return an error message if the graph fails to load
        return {"html": f"<p>Error loading graph: {str(e)}</p>"}

# Define a route to generate tests
@app.post("/generate-tests")
async def generate_tests(req: TestRequest, token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to generate tests")
    try:
        # Check if the repository is ready
        if not repo_state.get("ready"):
            return {"error": "Please analyze a repo first."}
        
        # Generate the tests and return the result
        result = generate_and_pr(req.repo_url, req.file_path)
        return result
    except Exception as e:
        # Return an error message if the test generation fails
        return {"error": f"Test generation failed: {str(e)}"}

# Define a route to generate a README
@app.post("/generate-readme")
async def generate_readme(req: ReadmeRequest, token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to generate a README")
    try:
        # Generate the README and return the result
        result = generate_readme_and_pr(req.repo_url)
        return result
    except Exception as e:
        # Return an error message if the README generation fails
        return {"error": f"README generation failed: {str(e)}"}

# Define a route to check the code quality
@app.post("/code-quality")
async def code_quality(req: RepoRequest, token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to check the code quality")
    try:
        # Clone the repository
        repo_path = clone_repo(req.url)
        
        # Walk the repository and parse the files
        files = walk_repo(repo_path)
        parsed = parse_repo(files)
        
        # Check the code quality and return the report
        report = score_repo(files, parsed)
        return report
    except Exception as e:
        # Return an error message if the code quality check fails
        return {"error": f"Quality check failed: {str(e)}"}

# Define a route to scan the repository for security vulnerabilities
@app.post("/security-scan")
async def security_scan(req: RepoRequest, token: str = Depends(oauth2_scheme)):
    # Check if the user is authenticated
    if not token:
        raise HTTPException(status_code=401, detail="You must be logged in to scan the repository for security vulnerabilities")
    try:
        # Check if the repository URL is valid
        if not req.url.startswith("https://github.com/"):
            return {"error": "Please provide a valid GitHub URL"}
        
        # Clone the repository
        repo_path = clone_repo(req.url)
        
        # Walk the repository and scan for security vulnerabilities
        files = walk_repo(repo_path)
        report = scan_repo(files)
        return report
    except Exception as e:
        # Return an error message if the security scan fails
        return {"error": f"Security scan failed: {str(e)}"}
```