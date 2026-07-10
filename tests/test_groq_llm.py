```python
# tests/test_groq_llm.py
import pytest
from unittest.mock import Mock, patch
from llm.groq_llm import sanitize_question, ask_codebase, client
from rag.embedder import query_vector_store

@pytest.fixture
def mock_query_vector_store():
    with patch('rag.embedder.query_vector_store') as mock:
        yield mock

@pytest.fixture
def mock_client():
    with patch('llm.groq_llm.client') as mock:
        yield mock

def test_sanitize_question_valid_input():
    """Test sanitize_question with valid input."""
    question = "What is the meaning of life?"
    is_valid, cleaned_question = sanitize_question(question)
    assert is_valid
    assert cleaned_question == question

def test_sanitize_question_empty_input():
    """Test sanitize_question with empty input."""
    question = ""
    is_valid, cleaned_question = sanitize_question(question)
    assert not is_valid
    assert cleaned_question == "Please ask a valid question."

def test_sanitize_question_too_long_input():
    """Test sanitize_question with input longer than 2000 characters."""
    question = "a" * 2001
    is_valid, cleaned_question = sanitize_question(question)
    assert is_valid
    assert len(cleaned_question) == 2000

def test_sanitize_question_non_ascii_input():
    """Test sanitize_question with non-ASCII input."""
    question = "What is the meaning of life? "
    is_valid, cleaned_question = sanitize_question(question)
    assert not is_valid
    assert cleaned_question == "Please ask your question in plain ASCII text."

def test_ask_codebase_valid_input(mock_query_vector_store, mock_client):
    """Test ask_codebase with valid input."""
    question = "What is the meaning of life?"
    collection_name = "codemind"
    mock_query_vector_store.return_value = {
        "documents": [["doc1", "doc2"]],
        "metadatas": [["source1", "source2"]]
    }
    mock_client.chat.completions.create.return_value = {
        "choices": [{"message": {"content": "The answer is 42."}}]
    }
    answer = ask_codebase(question, collection_name)
    assert answer == "The answer is 42."

def test_ask_codebase_empty_input():
    """Test ask_codebase with empty input."""
    question = ""
    collection_name = "codemind"
    answer = ask_codebase(question, collection_name)
    assert answer == "Please ask a valid question."

def test_ask_codebase_query_vector_store_error(mock_query_vector_store):
    """Test ask_codebase with query_vector_store error."""
    question = "What is the meaning of life?"
    collection_name = "codemind"
    mock_query_vector_store.side_effect = Exception("Mock error")
    answer = ask_codebase(question, collection_name)
    assert answer == "Could not retrieve relevant code: Mock error"

def test_ask_codebase_client_error(mock_client):
    """Test ask_codebase with client error."""
    question = "What is the meaning of life?"
    collection_name = "codemind"
    mock_client.chat.completions.create.side_effect = Exception("Mock error")
    answer = ask_codebase(question, collection_name)
    assert answer == "AI response failed: Mock error"

def test_ask_codebase_non_ascii_input():
    """Test ask_codebase with non-ASCII input."""
    question = "What is the meaning of life? "
    collection_name = "codemind"
    answer = ask_codebase(question, collection_name)
    assert answer == "Please ask your question in plain ASCII text."
```