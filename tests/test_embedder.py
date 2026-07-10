```python
# tests/test_embedder.py
import pytest
from unittest.mock import patch, MagicMock
from rag.embedder import chunk_file, build_vector_store, query_vector_store
from pathlib import Path
import chromadb
import json

@pytest.fixture
def file_info():
    return {
        "content": "This is a sample file content.",
        "relative_path": "path/to/sample/file.py"
    }

@pytest.fixture
def files():
    return [
        {
            "content": "This is a sample file content.",
            "relative_path": "path/to/sample/file.py"
        },
        {
            "content": "This is another sample file content.",
            "relative_path": "path/to/another/sample/file.py"
        }
    ]

def test_chunk_file(file_info):
    """Test chunking a file into overlapping chunks."""
    chunks = chunk_file(file_info)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "text" in chunk
        assert "source" in chunk
        assert "chunk_index" in chunk

def test_chunk_file_empty_content():
    """Test chunking a file with empty content."""
    file_info = {
        "content": "",
        "relative_path": "path/to/sample/file.py"
    }
    chunks = chunk_file(file_info)
    assert len(chunks) == 0

def test_build_vector_store(files):
    """Test building a vector store from a list of files."""
    with patch("chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.create_collection.return_value = mock_collection
        build_vector_store(files)
        mock_client.return_value.create_collection.assert_called_once()
        mock_collection.add.assert_called()

def test_build_vector_store_empty_files():
    """Test building a vector store from an empty list of files."""
    with patch("chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.create_collection.return_value = mock_collection
        build_vector_store([])
        mock_client.return_value.create_collection.assert_called_once()
        mock_collection.add.assert_not_called()

def test_query_vector_store():
    """Test querying the vector store."""
    with patch("chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.get_collection.return_value = mock_collection
        results = query_vector_store("query")
        mock_client.return_value.get_collection.assert_called_once()
        mock_collection.query.assert_called_once()

def test_query_vector_store_empty_query():
    """Test querying the vector store with an empty query."""
    with patch("chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.get_collection.return_value = mock_collection
        results = query_vector_store("")
        mock_client.return_value.get_collection.assert_called_once()
        mock_collection.query.assert_called_once()

def test_query_vector_store_invalid_collection_name():
    """Test querying the vector store with an invalid collection name."""
    with patch("chromadb.PersistentClient") as mock_client:
        mock_client.return_value.get_collection.side_effect = chromadb.exceptions.CollectionNotFoundError
        with pytest.raises(chromadb.exceptions.CollectionNotFoundError):
            query_vector_store("query", collection_name="invalid_collection")

def test_chunk_file_large_content():
    """Test chunking a file with large content."""
    file_info = {
        "content": "a" * 10000,
        "relative_path": "path/to/sample/file.py"
    }
    chunks = chunk_file(file_info)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "text" in chunk
        assert "source" in chunk
        assert "chunk_index" in chunk

def test_build_vector_store_large_files():
    """Test building a vector store from a list of large files."""
    files = [
        {
            "content": "a" * 10000,
            "relative_path": "path/to/sample/file.py"
        },
        {
            "content": "b" * 10000,
            "relative_path": "path/to/another/sample/file.py"
        }
    ]
    with patch("chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.create_collection.return_value = mock_collection
        build_vector_store(files)
        mock_client.return_value.create_collection.assert_called_once()
        mock_collection.add.assert_called()
```