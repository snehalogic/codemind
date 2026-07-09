import ast
from pathlib import Path


def parse_python_file(file_info: dict) -> dict:
    """Parse a single Python file using AST to extract functions, classes, imports, and calls."""
    content = file_info["content"]
    relative_path = file_info["relative_path"]

    result = {
        "relative_path": relative_path,
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
        "parse_error": None
    }

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        result["parse_error"] = str(e)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            result["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "docstring": ast.get_docstring(node)
            })

        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
                "docstring": ast.get_docstring(node)
            })

        elif isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result["imports"].append(f"{module}.{alias.name}")

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                result["calls"].append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                result["calls"].append(node.func.id)

    return result


def parse_repo(files: list[dict]) -> list[dict]:
    """Parse all Python files in the repo. Returns list of parsed file dicts with structure info."""
    parsed = []
    python_files = [f for f in files if f["extension"] == ".py"]
    
    print(f"Parsing {len(python_files)} Python files...")
    
    for f in python_files:
        parsed_file = parse_python_file(f)
        parsed.append(parsed_file)

    successful = len([p for p in parsed if not p["parse_error"]])
    print(f"Successfully parsed {successful}/{len(python_files)} files")
    return parsed


if __name__ == "__main__":
    from cloner import clone_repo, walk_repo

    repo_path = clone_repo("https://github.com/tiangolo/fastapi")
    files = walk_repo(repo_path)
    parsed = parse_repo(files)

    print("\n--- Sample: first 3 parsed files ---")
    for p in parsed[:3]:
        print(f"\n{p['relative_path']}")
        print(f"  Classes : {[c['name'] for c in p['classes']]}")
        print(f"  Functions: {[f['name'] for f in p['functions']][:5]}")
        print(f"  Imports : {p['imports'][:5]}")