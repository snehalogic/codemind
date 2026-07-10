from google import genai
import sys
import jwt
import hashlib
import hmac
import time
sys.path.append("..")
from config import GEMINI_API_KEY, SECRET_KEY

# Implement authentication and authorization checks
def authenticate_user(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

def generate_token(user_id):
    payload = {'user_id': user_id, 'exp': int(time.time()) + 3600}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

client = genai.Client(api_key=GEMINI_API_KEY)

def ask_codebase(question: str, collection_name: str = "codemind", token: str = None) -> str:
    # Check if token is provided and valid
    if token is None or not authenticate_user(token):
        raise Exception("Invalid or missing authentication token")

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

    # Generate a token for the user
    user_id = "default_user"
    token = generate_token(user_id)

    while True:
        question = input("You: ").strip()
        if question.lower() == "quit":
            break
        if not question:
            continue

        print("\nCodeMind: thinking...\n")
        answer = ask_codebase(question, token=token)
        print(f"CodeMind: {answer}\n")
        print("-" * 60 + "\n")