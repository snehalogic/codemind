from google import genai
import sys
sys.path.append("..")
from config import GEMINI_API_KEY
from rag.embedder import query_vector_store

client = genai.Client(api_key=GEMINI_API_KEY)


def ask_codebase(question: str, collection_name: str = "codemind") -> str:
    results = query_vector_store(question, collection_name=collection_name, n_results=6)

    context_chunks = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i]["source"]
        context_chunks.append(f"--- From {source} ---\n{doc}")

    context = "\n\n".join(context_chunks)

    prompt = f"""You are CodeMind, an expert AI assistant that understands codebases deeply.
You have been given relevant code snippets from a GitHub repository to answer the user's question.
Always mention which file your answer comes from.
If the code snippets don't contain enough information, say so honestly.

RELEVANT CODE FROM THE REPOSITORY:
{context}

USER QUESTION:
{question}

Answer clearly and cite the file names:"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text


if __name__ == "__main__":
    print("CodeMind is ready! Ask anything about the FastAPI codebase.")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() == "quit":
            break
        if not question:
            continue

        print("\nCodeMind: thinking...\n")
        answer = ask_codebase(question)
        print(f"CodeMind: {answer}\n")
        print("-" * 60 + "\n")