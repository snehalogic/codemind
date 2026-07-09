from groq import Groq
import sys
sys.path.append("..")
from config import GROQ_API_KEY
from rag.embedder import query_vector_store

client = Groq(api_key=GROQ_API_KEY)


def sanitize_question(question: str) -> tuple[bool, str]:
    """Validate and sanitize user input. Returns (is_valid, cleaned_question) tuple."""
    question = question.strip()
    if not question:
        return False, "Please ask a valid question."
    if len(question) > 2000:
        question = question[:2000]
    try:
        question.encode("ascii")
    except UnicodeEncodeError:
        return False, "Please ask your question in plain ASCII text."
    return True, question


def ask_codebase(question: str, collection_name: str = "codemind") -> str:
    """Retrieve relevant code chunks and use Groq LLM to answer a question about the codebase."""
    valid, result = sanitize_question(question)
    if not valid:
        return result

    question = result

    try:
        results = query_vector_store(question, collection_name=collection_name, n_results=6)
    except Exception as e:
        return f"Could not retrieve relevant code: {str(e)}"

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

    try:
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

    except Exception as e:
        return f"AI response failed: {str(e)}"


if __name__ == "__main__":
    print("CodeMind is ready! Ask anything about the FastAPI codebase.")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            question = input("You: ").strip()
            if question.lower() == "quit":
                break
            if not question:
                continue
            print("\nCodeMind: thinking...\n")
            answer = ask_codebase(question)
            print(f"CodeMind: {answer}\n")
            print("-" * 60 + "\n")
        except KeyboardInterrupt:
            print("\nExiting...")
            break