```python
import sys
import os
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from groq import Groq
from config import GROQ_API_KEY

# Create a logger to handle security reports instead of printing to console
logging.basicConfig(filename='security_report.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = Groq(api_key=GROQ_API_KEY)


def scan_file_for_vulnerabilities(file_content: str, filename: str) -> dict:
    """Use Groq LLM to scan a single Python file for security vulnerabilities."""
    prompt = f"""You are a senior security engineer. Analyze this Python code for security vulnerabilities.

Check for:
1. Hardcoded secrets, API keys, passwords
2. SQL injection risks
3. Missing authentication/authorization checks
4. Exposed sensitive endpoints
5. Insecure deserialization
6. Path traversal vulnerabilities
7. Command injection risks
8. Missing input validation
9. Insecure dependencies usage
10. Sensitive data exposure

For each issue found, respond in this exact format:
ISSUE: <issue title>
SEVERITY: <HIGH/MEDIUM/LOW>
LINE: <line number or "unknown">
DESCRIPTION: <what the problem is>
FIX: <how to fix it>
---

If no issues found, respond with: NO_ISSUES_FOUND

FILENAME: {filename}

CODE:
{file_content}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert security engineer. Be thorough and precise."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2048
    )
    
    raw = response.choices[0].message.content
    return parse_security_report(raw, filename)


def parse_security_report(raw: str, filename: str) -> dict:
    """Parse the raw LLM security output into structured issue dicts."""
    if "NO_ISSUES_FOUND" in raw:
        return {"filename": filename, "issues": [], "safe": True}

    issues = []
    blocks = raw.strip().split("---")
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        issue = {}
        for line in block.split("\n"):
            if line.startswith("ISSUE:"):
                issue["title"] = line.replace("ISSUE:", "").strip()
            elif line.startswith("SEVERITY:"):
                issue["severity"] = line.replace("SEVERITY:", "").strip()
            elif line.startswith("LINE:"):
                issue["line"] = line.replace("LINE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                issue["description"] = line.replace("DESCRIPTION:", "").strip()
            elif line.startswith("FIX:"):
                issue["fix"] = line.replace("FIX:", "").strip()
        
        if issue.get("title"):
            issues.append(issue)

    return {
        "filename": filename,
        "issues": issues,
        "safe": len(issues) == 0,
        "high": len([i for i in issues if i.get("severity") == "HIGH"]),
        "medium": len([i for i in issues if i.get("severity") == "MEDIUM"]),
        "low": len([i for i in issues if i.get("severity") == "LOW"])
    }


def scan_repo(files: list[dict]) -> dict:
    """Scan all Python files in the repo and return a full security report with score."""
    results = []
    total_high = 0
    total_medium = 0
    total_low = 0

    python_files = [f for f in files if f["extension"] == ".py"]
    logging.info(f"Scanning {len(python_files)} Python files...")

    for f in python_files:
        logging.info(f"  Scanning {f['relative_path']}...")
        result = scan_file_for_vulnerabilities(f["content"], f["relative_path"])
        results.append(result)
        total_high += result.get("high", 0)
        total_medium += result.get("medium", 0)
        total_low += result.get("low", 0)

    score = max(0, 100 - (total_high * 20) - (total_medium * 10) - (total_low * 5))

    return {
        "files_scanned": len(python_files),
        "total_high": total_high,
        "total_medium": total_medium,
        "total_low": total_low,
        "security_score": score,
        "results": results
    }


if __name__ == "__main__":
    from ingestion.cloner import clone_repo, walk_repo

    repo_path = clone_repo("https://github.com/snehalogic/VoiceVault")
    files = walk_repo(repo_path)
    report = scan_repo(files)

    logging.info(f"\n--- Security Report ---")
    logging.info(f"Files scanned: {report['files_scanned']}")
    logging.info(f"Security score: {report['security_score']}/100")
    logging.info(f"HIGH: {report['total_high']} | MEDIUM: {report['total_medium']} | LOW: {report['total_low']}")
    
    for result in report["results"]:
        if result["issues"]:
            logging.info(f"\n{result['filename']}:")
            for issue in result["issues"]:
                logging.info(f"  [{issue.get('severity')}] {issue.get('title')}")
                logging.info(f"    → {issue.get('fix')}")
```