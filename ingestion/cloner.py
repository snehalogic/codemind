import os
import shutil
import git
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CLONE_DIR = Path("cloned_repos")

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "coverage", ".pytest_cache", ".mypy_cache"
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".lock", ".woff", ".ttf",
    ".pkl", ".bin", ".pt", ".pth", ".h5", ".parquet"
}


def clone_repo(github_url: str) -> Path:
    """Clone a GitHub repository to the local cloned_repos directory. Deletes existing copy if present."""
    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    clone_path = CLONE_DIR / repo_name

    if clone_path.exists():
        print(f"Repo already cloned at {clone_path}. Deleting and re-cloning...")
        import stat
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(clone_path, onexc=remove_readonly)

    print(f"Cloning {github_url}...")
    git.Repo.clone_from(github_url, clone_path)
    print(f"Done! Cloned to {clone_path}")
    return clone_path


def walk_repo(repo_path: Path) -> list[dict]:
    """Walk all files in a cloned repo, skipping ignored dirs and binary extensions. Returns list of file dicts."""
    files = []

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in IGNORE_EXTENSIONS:
                continue

            full_path = Path(root) / filename
            relative_path = full_path.relative_to(repo_path)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                files.append({
                    "filename": filename,
                    "relative_path": str(relative_path),
                    "extension": ext,
                    "content": content,
                    "size": len(content)
                })
            except Exception as e:
                print(f"Skipping {filename}: {e}")

    return files


def get_repo_summary(files: list[dict]) -> dict:
    """Generate a summary of the repo including file counts, types, sizes, and largest files."""
    ext_counts = {}
    for f in files:
        ext = f["extension"] or "no extension"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    total_size = sum(f["size"] for f in files)

    return {
        "total_files": len(files),
        "total_characters": total_size,
        "file_types": ext_counts,
        "largest_files": sorted(files, key=lambda x: x["size"], reverse=True)[:5]
    }


if __name__ == "__main__":
    url = input("Enter GitHub repo URL: ")
    repo_path = clone_repo(url)
    files = walk_repo(repo_path)
    summary = get_repo_summary(files)

    print(f"\n--- Repo Summary ---")
    print(f"Total files: {summary['total_files']}")
    print(f"Total characters: {summary['total_characters']:,}")
    print(f"\nFile types:")
    for ext, count in sorted(summary['file_types'].items(), key=lambda x: -x[1]):
        print(f"  {ext}: {count} files")
    print(f"\nLargest files:")
    for f in summary['largest_files']:
        print(f"  {f['relative_path']} ({f['size']:,} chars)")