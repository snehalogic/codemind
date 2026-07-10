```python
# tests/test_parser.py
import pytest
from unittest.mock import patch, MagicMock
from ingestion.parser import parse_python_file, parse_repo
from pathlib import Path
import ast

@pytest.fixture
def sample_python_file():
    return {
        "content": """
def add(a, b):
    return a + b

class Calculator:
    def __init__(self):
        pass

    def multiply(self, a, b):
        return a * b

import math
from math import sin
""",
        "relative_path": "sample.py"
    }

@pytest.fixture
def sample_repo_files():
    return [
        {
            "content": """
def add(a, b):
    return a + b

class Calculator:
    def __init__(self):
        pass

    def multiply(self, a, b):
        return a * b

import math
from math import sin
""",
            "relative_path": "sample.py",
            "extension": ".py"
        },
        {
            "content": """
def subtract(a, b):
    return a - b

class Calculator2:
    def __init__(self):
        pass

    def divide(self, a, b):
        return a / b

import random
from random import randint
""",
            "relative_path": "sample2.py",
            "extension": ".py"
        },
        {
            "content": "Invalid Python syntax",
            "relative_path": "invalid.py",
            "extension": ".py"
        }
    ]

def test_parse_python_file(sample_python_file):
    """
    Test parsing a single Python file.
    """
    result = parse_python_file(sample_python_file)
    assert result["relative_path"] == sample_python_file["relative_path"]
    assert len(result["functions"]) == 1
    assert len(result["classes"]) == 1
    assert len(result["imports"]) == 3
    assert len(result["calls"]) == 0
    assert result["parse_error"] is None

def test_parse_python_file_invalid_syntax():
    """
    Test parsing a Python file with invalid syntax.
    """
    file_info = {
        "content": "Invalid Python syntax",
        "relative_path": "invalid.py"
    }
    result = parse_python_file(file_info)
    assert result["relative_path"] == file_info["relative_path"]
    assert result["parse_error"] is not None

def test_parse_repo(sample_repo_files):
    """
    Test parsing a list of Python files in a repo.
    """
    result = parse_repo(sample_repo_files)
    assert len(result) == len(sample_repo_files)
    for parsed_file in result:
        if parsed_file["relative_path"] == "invalid.py":
            assert parsed_file["parse_error"] is not None
        else:
            assert parsed_file["parse_error"] is None

@patch("ingestion.parser.clone_repo")
@patch("ingestion.parser.walk_repo")
def test_parse_repo_integration(mock_walk_repo, mock_clone_repo, sample_repo_files):
    """
    Test parsing a list of Python files in a repo with mocked external dependencies.
    """
    mock_clone_repo.return_value = Path("/tmp/repo")
    mock_walk_repo.return_value = sample_repo_files
    result = parse_repo(sample_repo_files)
    assert len(result) == len(sample_repo_files)
    for parsed_file in result:
        if parsed_file["relative_path"] == "invalid.py":
            assert parsed_file["parse_error"] is not None
        else:
            assert parsed_file["parse_error"] is None

def test_parse_python_file_functions(sample_python_file):
    """
    Test parsing functions in a Python file.
    """
    result = parse_python_file(sample_python_file)
    functions = result["functions"]
    assert len(functions) == 1
    assert functions[0]["name"] == "add"
    assert functions[0]["line"] == 2
    assert functions[0]["args"] == ["a", "b"]
    assert functions[0]["is_async"] is False
    assert functions[0]["docstring"] is None

def test_parse_python_file_classes(sample_python_file):
    """
    Test parsing classes in a Python file.
    """
    result = parse_python_file(sample_python_file)
    classes = result["classes"]
    assert len(classes) == 1
    assert classes[0]["name"] == "Calculator"
    assert classes[0]["line"] == 5
    assert classes[0]["methods"] == ["__init__", "multiply"]
    assert classes[0]["docstring"] is None

def test_parse_python_file_imports(sample_python_file):
    """
    Test parsing imports in a Python file.
    """
    result = parse_python_file(sample_python_file)
    imports = result["imports"]
    assert len(imports) == 3
    assert imports[0] == "math"
    assert imports[1] == "math.sin"
    assert imports[2] == "sin"

def test_parse_python_file_calls(sample_python_file):
    """
    Test parsing calls in a Python file.
    """
    result = parse_python_file(sample_python_file)
    calls = result["calls"]
    assert len(calls) == 0
```