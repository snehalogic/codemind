```python
import sys
import os
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from groq import Groq
from config import GROQ_API_KEY

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create a file handler and a stream handler
file_handler = logging.FileHandler('code_quality.log')
stream_handler = logging.StreamHandler()
# Create a formatter and attach it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

client = Groq(api_key=GROQ_API_KEY)


def score_documentation(parsed_files: list[dict]) -> dict:
    """Score the repo's documentation based on docstring coverage across functions and classes."""

    total_functions = 0
    documented_functions = 0
    total_classes = 0
    documented_classes = 0

    for f in parsed_files:
        for fn in f["functions"]:
            total_functions += 1
            if fn.get("docstring"):
                documented_functions += 1
        for cls in f["classes"]:
            total_classes += 1
            if cls.get("docstring"):
                documented_classes += 1

    total = total_functions + total_classes
    documented = documented_functions + documented_classes
    score = int((documented / total) * 100) if total > 0 else 0

    return {
        "score": score,
        "total_functions": total_functions,
        "documented_functions": documented_functions,
        "total_classes": total_classes,
        "documented_classes": documented_classes,
        "detail": f"{documented}/{total} functions and classes have docstrings"
    }


def score_complexity(parsed_files: list[dict], files: list[dict]) -> dict:
    """Score code complexity based on function argument counts and file sizes."""

    issues = []
    total_functions = 0
    complex_functions = 0

    for f in parsed_files:
        for fn in f["functions"]:
            total_functions += 1
            if len(fn.get("args", [])) > 7:
                complex_functions += 1
                issues.append(f"{fn['name']} in {f['relative_path']} has {len(fn['args'])} arguments")

    large_files = []
    for f in files:
        if f["extension"] == ".py" and f["size"] > 10000:
            large_files.append(f"{f['relative_path']} ({f['size']:,} chars)")

    complexity_penalty = (complex_functions / total_functions * 40) if total_functions > 0 else 0
    large_file_penalty = min(len(large_files) * 10, 30)
    score = max(0, 100 - int(complexity_penalty) - large_file_penalty)

    return {
        "score": score,
        "complex_functions": complex_functions,
        "large_files": large_files[:5],
        "issues": issues[:5],
        "detail": f"{complex_functions} overly complex functions, {len(large_files)} large files"
    }


def score_test_coverage(files: list[dict]) -> dict:
    """Score test coverage by comparing test files to source files."""

    test_files = [f for f in files if "test" in f["filename"].lower() or "test" in f["relative_path"].lower()]
    python_files = [f for f in files if f["extension"] == ".py" and "test" not in f["filename"].lower()]

    has_pytest = any("pytest" in f["content"].lower() for f in files if f["extension"] in [".txt", ".toml", ".cfg"])
    has_unittest = any("import unittest" in f["content"] for f in test_files)

    ratio = len(test_files) / len(python_files) if python_files else 0
    score = min(100, int(ratio * 100) + (10 if has_pytest else 0) + (10 if has_unittest else 0))

    return {
        "score": score,
        "test_files": len(test_files),
        "python_files": len(python_files),
        "has_pytest": has_pytest,
        "detail": f"{len(test_files)} test files for {len(python_files)} source files"
    }


def score_style(files: list[dict], parsed_files: list[dict]) -> dict:
    """Score code style based on presence of .gitignore, requirements.txt, README, and .env.example."""

    issues = []

    has_gitignore = any(f["filename"] == ".gitignore" for f in files)
    has_requirements = any(f["filename"] == "requirements.txt" for f in files)
    has_readme = any("readme" in f["filename"].lower() for f in files)
    has_env_example = any(".env.example" in f["filename"].lower() for f in files)

    score = 40
    if has_gitignore:
        score += 15
    else:
        issues.append("Missing .gitignore")
    if has_requirements:
        score += 15
    else:
        issues.append("Missing requirements.txt")
    if has_readme:
        score += 20
    else:
        issues.append("Missing README.md")
    if has_env_example:
        score += 10
    else:
        issues.append("Missing .env.example")

    return {
        "score": min(score, 100),
        "has_gitignore": has_gitignore,
        "has_requirements": has_requirements,
        "has_readme": has_readme,
        "has_env_example": has_env_example,
        "issues": issues,
        "detail": f"{4 - len(issues)}/4 best practices followed"
    }


def generate_recommendations(scores: dict) -> list[str]:
    """Generate a list of actionable recommendations based on quality scores."""

    recommendations = []

    if scores["documentation"]["score"] < 60:
        recommendations.append("Add docstrings to functions and classes — documentation score is low")
    if scores["complexity"]["score"] < 60:
        recommendations.append("Break down complex functions with too many arguments into smaller ones")
    if scores["test_coverage"]["score"] < 40:
        recommendations.append("Add pytest tests — test coverage is critically low")
    if scores["style"]["score"] < 60:
        for issue in scores["style"]["issues"]:
            recommendations.append(f"Fix: {issue}")

    if not recommendations:
        recommendations.append("Great codebase! Keep maintaining documentation and test coverage.")

    return recommendations


def score_repo(files: list[dict], parsed_files: list[dict]) -> dict:
    """Run all quality checks and return an overall score, grade, and recommendations."""

    # Instead of printing to the console, log the messages
    logger.info("Scoring documentation...")
    doc_score = score_documentation(parsed_files)

    logger.info("Scoring complexity...")
    complexity_score = score_complexity(parsed_files, files)

    logger.info("Scoring test coverage...")
    test_score = score_test_coverage(files)

    logger.info("Scoring code style...")
    style_score = score_style(files, parsed_files)

    scores = {
        "documentation": doc_score,
        "complexity": complexity_score,
        "test_coverage": test_score,
        "style": style_score,
    }

    overall = int(
        doc_score["score"] * 0.30 +
        complexity_score["score"] * 0.25 +
        test_score["score"] * 0.25 +
        style_score["score"] * 0.20
    )

    recommendations = generate_recommendations(scores)

    return {
        "overall_score": overall,
        "scores": scores,
        "recommendations": recommendations,
        "grade": "A" if overall >= 90 else "B" if overall >= 75 else "C" if overall >= 60 else "D" if overall >= 40 else "F"
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from ingestion.cloner import clone_repo, walk_repo
    from ingestion.parser import parse_repo

    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter GitHub repo URL: ")
    repo_path = clone_repo(url)
    files = walk_repo(repo_path)
    parsed = parse_repo(files)
    report = score_repo(files, parsed)

    # Instead of printing to the console, log the messages
    logger.info("\n--- Code Quality Report ---")
    logger.info(f"Overall Score : {report['overall_score']}/100 (Grade: {report['grade']})")
    logger.info(f"Documentation : {report['scores']['documentation']['score']}/100 — {report['scores']['documentation']['detail']}")
    logger.info(f"Complexity    : {report['scores']['complexity']['score']}/100 — {report['scores']['complexity']['detail']}")
    logger.info(f"Test Coverage : {report['scores']['test_coverage']['score']}/100 — {report['scores']['test_coverage']['detail']}")
    logger.info(f"Code Style    : {report['scores']['style']['score']}/100 — {report['scores']['style']['detail']}")
    logger.info(f"\nRecommendations:")
    for r in report["recommendations"]:
        logger.info(f"  • {r}")
```