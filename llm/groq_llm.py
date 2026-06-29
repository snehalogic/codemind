from groq import Groq
import sys
sys.path.append("..")
from config import GROQ_API_KEY
from rag.embedder import query_vector_store

client = Groq(api_key=GROQ_API_KEY)


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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are CodeMind, an expert AI codebase assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1024
    )

    return response.choices[0].message.content


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