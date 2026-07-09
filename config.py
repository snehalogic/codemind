from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

#Paths
BASE_DIR = Path(__file__).parent
CLONE_DIR = BASE_DIR / "cloned_repos"
CLONE_DIR.mkdir(exist_ok=True)

#Gemini
#GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#GROQ
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

#File filtering
IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".lock", ".woff", ".ttf",
    ".pkl", ".bin", ".pt", ".pth", ".h5", ".parquet" 
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".lock", ".woff", ".ttf"
}

#Chunking
MAX_CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100