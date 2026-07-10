```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from groq import Groq
from github import Github, GithubException
from config import GROQ_API_KEY, GITHUB_TOKEN
from ingestion.cloner import clone_repo, walk_repo
from ingestion.parser import parse_repo

# Initialize Groq client with API key
client = Groq(api_key=GROQ_API_KEY)

# Initialize GitHub client with token and authenticate
gh = Github(GITHUB_TOKEN)

def build_repo_context(files: list[dict], parsed: list[dict]) -> str:
    """Build a rich context string from repo files for README generation."""
    ext_counts = {}
    for f in files:
        ext = f["extension"] or "no extension"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    tech_stack = []
    for f in files:
        name = f["filename"].lower()
        if name == "requirements.txt":
            tech_stack.append("Python deps:\n" + f["content"][:800])
        elif name == "package.json" and "node_modules" not in f["relative_path"]:
            tech_stack.append("Node deps:\n" + f["content"][:800])
        elif name == "dockerfile":
            tech_stack.append("Docker: yes")
        elif name in ["docker-compose.yml", "docker-compose.yaml"]:
            tech_stack.append("Docker Compose: yes")
        elif name in [".env.example", ".env.sample"]:
            tech_stack.append("Env vars example:\n" + f["content"][:500])

   
    all_classes = []
    all_functions = []
    for p in parsed[:20]:
        for c in p["classes"]:
            all_classes.append(f"{c['name']} (in {p['relative_path']})")
        for fn in p["functions"][:3]:
            all_functions.append(f"{fn['name']} (in {p['relative_path']})")

    file_tree = [f["relative_path"] for f in files[:60]]

    key_files_content = []
    for f in files:
        name = f["filename"].lower()
        if name in ["readme.md", "readme.txt"]:
            key_files_content.append(f"Existing README:\n{f['content'][:500]}")
        elif f["extension"] in [".js", ".ts", ".jsx", ".tsx"] and f["size"] > 100:
            key_files_content.append(f"JS/TS file {f['relative_path']}:\n{f['content'][:300]}")
        if len(key_files_content) >= 5:
            break

    context = f"""
FILE TYPES: {ext_counts}
TOTAL FILES: {len(files)}

TECH STACK CLUES:
{chr(10).join(tech_stack) if tech_stack else "Not found"}

KEY CLASSES (Python):
{chr(10).join(all_classes[:15]) if all_classes else "None found"}

KEY FUNCTIONS (Python):
{chr(10).join(all_functions[:15]) if all_functions else "None found"}

FULL FILE STRUCTURE:
{chr(10).join(file_tree)}

KEY FILE CONTENTS:
{chr(10).join(key_files_content) if key_files_content else "None"}
"""
    return context

def generate_readme(repo_url: str) -> str:
    """Analyze a repo and use Groq LLM to generate a professional README.md."""
    repo_name = repo_url.rstrip("/").split("/")[-1]

    print("Cloning and analyzing repo...")
    repo_path = clone_repo(repo_url)
    files = walk_repo(repo_path)
    parsed = parse_repo(files)
    context = build_repo_context(files, parsed)

    prompt = f"""You are a senior developer writing a professional README.md for a GitHub repository.

Based on the repository analysis below, write a complete, professional README.md.
This may be a fullstack project with Python backend AND JavaScript/React frontend — cover both.

REPOSITORY NAME: {repo_name}
REPOSITORY URL: {repo_url}

REPOSITORY ANALYSIS:
{context}

Write a README.md that includes:
1. # Project name with a compelling one-line description
2. ## 🏗️ Architecture — explain how the full system works including frontend and backend
3. ## ⚙️ Tech Stack — list ALL technologies including JS frameworks, Python libs, databases
4. ## 📁 Project Structure — explain key files and folders for BOTH frontend and backend
5. ## 🚀 Getting Started — separate setup steps for frontend and backend
6. ## 📖 Usage — how to use the project with examples
7. ## 🔑 Environment Variables — list all required env vars
8. ## 🤝 Contributing — how to contribute

Make it professional, clear, and genuinely useful.
Output ONLY the markdown content, nothing else:"""

    print("Generating README with AI...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert technical writer. Write clear, professional README files."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=3000
    )

    return response.choices[0].message.content


def create_readme_pr(repo_url: str, readme_content: str) -> str:
    """Commit the generated README to a new branch and open a GitHub PR."""

    repo_name = repo_url.rstrip("/").split("/")[-1]
    username = repo_url.rstrip("/").split("/")[-2]

    try:
        # Authenticate and authorize the user
        user = gh.get_user()
        if not user:
            raise Exception("Authentication failed")

        # Check if the user has permission to access the repository
        repo = gh.get_repo(f"{username}/{repo_name}")
        if not repo:
            raise Exception("Repository not found")

        # Check if the user has permission to create a pull request
        if not repo.permissions.push:
            raise Exception("You do not have permission to create a pull request")

        try:
            main_branch = repo.get_branch("main")
        except:
            main_branch = repo.get_branch("master")

        new_branch = "codemind/auto-readme"

        try:
            repo.create_git_ref(
                ref=f"refs/heads/{new_branch}",
                sha=main_branch.commit.sha
            )
        except GithubException:
            repo.get_git_ref(f"heads/{new_branch}").delete()
            repo.create_git_ref(
                ref=f"refs/heads/{new_branch}",
                sha=main_branch.commit.sha
            )

        try:
            existing = repo.get_contents("README.md", ref=new_branch)
            repo.update_file(
                "README.md",
                "CodeMind: update auto-generated README",
                readme_content,
                existing.sha,
                branch=new_branch
            )
        except:
            repo.create_file(
                "README.md",
                "CodeMind: add auto-generated README",
                readme_content,
                branch=new_branch
            )

        pr = repo.create_pull(
            title="📄 CodeMind: Auto-generated README.md",
            body="""## Auto-generated by CodeMind 🧠

This PR adds a professional README.md generated by analyzing the entire codebase.

### What's included:
- Architecture overview
- Tech stack breakdown
- Project structure explanation
- Getting started guide
- Usage examples
- Environment variables
- Contributing guide

> Generated by [CodeMind](https://github.com/snehalogic/codemind)
            """,
            head=new_branch,
            base=main_branch.name
        )
        return pr.html_url

    except Exception as e:
        raise Exception(f"PR creation failed: {str(e)}")


def generate_readme_and_pr(repo_url: str) -> dict:
    """Full pipeline: generate README and open a PR on GitHub."""

    # Authenticate and authorize the user
    try:
        user = gh.get_user()
        if not user:
            raise Exception("Authentication failed")
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")

    readme_content = generate_readme(repo_url)
    print("Creating PR...")
    pr_url = create_readme_pr(repo_url, readme_content)
    print(f"PR created: {pr_url}")
    return {
        "readme": readme_content,
        "pr_url": pr_url
    }


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter GitHub repo URL: ")
    result = generate_readme_and_pr(url)
    print("\n--- Generated README ---")
    print(result["readme"])
    print(f"\n--- PR URL ---")
    print(result["pr_url"])
```