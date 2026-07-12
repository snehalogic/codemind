```python
# tests/test_config.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from config import BASE_DIR, CLONE_DIR, GROQ_API_KEY, IGNORE_EXTENSIONS, MAX_CHUNK_SIZE, CHUNK_OVERLAP
import os

@pytest.fixture
def mock_load_dotenv():
    with patch('dotenv.load_dotenv') as mock_load_dotenv:
        yield mock_load_dotenv

@pytest.fixture
def mock_os_getenv():
    with patch('os.getenv') as mock_os_getenv:
        yield mock_os_getenv

def test_base_dir(mock_load_dotenv):
    """Test that BASE_DIR is set to the parent directory of the config file."""
    assert BASE_DIR == Path(__file__).parent.parent

def test_clone_dir(mock_load_dotenv):
    """Test that CLONE_DIR is set to the 'cloned_repos' directory within BASE_DIR."""
    assert CLONE_DIR == BASE_DIR / "cloned_repos"

def test_clone_dir_exists(mock_load_dotenv):
    """Test that CLONE_DIR is created if it does not exist."""
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        CLONE_DIR.mkdir(exist_ok=True)
        mock_mkdir.assert_called_once()

def test_groq_api_key(mock_load_dotenv, mock_os_getenv):
    """Test that GROQ_API_KEY is set to the value of the 'GROQ_API_KEY' environment variable."""
    mock_os_getenv.return_value = 'test_api_key'
    assert GROQ_API_KEY == 'test_api_key'

def test_ignore_extensions():
    """Test that IGNORE_EXTENSIONS contains the expected file extensions."""
    expected_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
        ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz",
        ".exe", ".dll", ".so", ".lock", ".woff", ".ttf"
    }
    assert IGNORE_EXTENSIONS == expected_extensions

def test_max_chunk_size():
    """Test that MAX_CHUNK_SIZE is set to the expected value."""
    assert MAX_CHUNK_SIZE == 1500

def test_chunk_overlap():
    """Test that CHUNK_OVERLAP is set to the expected value."""
    assert CHUNK_OVERLAP == 100

def test_load_dotenv_called(mock_load_dotenv):
    """Test that load_dotenv is called when the config module is imported."""
    mock_load_dotenv.assert_called_once()

def test_os_getenv_called(mock_load_dotenv, mock_os_getenv):
    """Test that os.getenv is called to retrieve the GROQ_API_KEY environment variable."""
    mock_os_getenv.assert_called_once_with('GROQ_API_KEY')

def test_invalid_groq_api_key(mock_load_dotenv, mock_os_getenv):
    """Test that an error is raised if the GROQ_API_KEY environment variable is not set."""
    mock_os_getenv.return_value = None
    with pytest.raises(TypeError):
        GROQ_API_KEY

def test_invalid_base_dir(mock_load_dotenv):
    """Test that an error is raised if the BASE_DIR is not a valid directory."""
    with patch('pathlib.Path.parent') as mock_parent:
        mock_parent.return_value = None
        with pytest.raises(TypeError):
            BASE_DIR

def test_invalid_clone_dir(mock_load_dotenv):
    """Test that an error is raised if the CLONE_DIR is not a valid directory."""
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        mock_mkdir.side_effect = OSError
        with pytest.raises(OSError):
            CLONE_DIR.mkdir(exist_ok=True)
```