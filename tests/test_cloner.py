```python
# tests/test_cloner.py
import os
import shutil
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from ingestion.cloner import clone_repo, walk_repo, get_repo_summary, CLONE_DIR, IGNORE_DIRS, IGNORE_EXTENSIONS

@pytest.fixture
def mock_git_repo():
    with patch('ingestion.cloner.git.Repo') as mock_repo:
        yield mock_repo

@pytest.fixture
def mock_clone_dir(tmp_path):
    clone_dir = tmp_path / 'cloned_repos'
    clone_dir.mkdir()
    yield clone_dir
    shutil.rmtree(clone_dir)

@pytest.fixture
def mock_repo_path(mock_clone_dir):
    repo_path = mock_clone_dir / 'test_repo'
    repo_path.mkdir()
    yield repo_path
    shutil.rmtree(repo_path)

def test_clone_repo(mock_clone_dir, mock_git_repo):
    """Test cloning a GitHub repository."""
    github_url = 'https://github.com/test/test_repo.git'
    clone_path = clone_repo(github_url)
    assert clone_path == mock_clone_dir / 'test_repo'
    mock_git_repo.clone_from.assert_called_once_with(github_url, clone_path)

def test_clone_repo_existing(mock_clone_dir, mock_git_repo):
    """Test cloning a GitHub repository when it already exists."""
    github_url = 'https://github.com/test/test_repo.git'
    clone_path = mock_clone_dir / 'test_repo'
    clone_path.mkdir()
    clone_repo(github_url)
    mock_git_repo.clone_from.assert_called_once_with(github_url, clone_path)

def test_clone_repo_invalid_url(mock_clone_dir, mock_git_repo):
    """Test cloning a GitHub repository with an invalid URL."""
    github_url = 'invalid_url'
    with pytest.raises(git.exc.GitCommandError):
        clone_repo(github_url)

def test_walk_repo(mock_repo_path):
    """Test walking all files in a cloned repository."""
    file1 = mock_repo_path / 'file1.txt'
    file1.write_text('Hello World!')
    file2 = mock_repo_path / 'file2.py'
    file2.write_text('print("Hello World!")')
    files = walk_repo(mock_repo_path)
    assert len(files) == 2
    assert files[0]['filename'] == 'file1.txt'
    assert files[1]['filename'] == 'file2.py'

def test_walk_repo_ignored_dirs(mock_repo_path):
    """Test walking all files in a cloned repository with ignored directories."""
    file1 = mock_repo_path / 'file1.txt'
    file1.write_text('Hello World!')
    ignored_dir = mock_repo_path / '.git'
    ignored_dir.mkdir()
    files = walk_repo(mock_repo_path)
    assert len(files) == 1
    assert files[0]['filename'] == 'file1.txt'

def test_walk_repo_ignored_extensions(mock_repo_path):
    """Test walking all files in a cloned repository with ignored extensions."""
    file1 = mock_repo_path / 'file1.txt'
    file1.write_text('Hello World!')
    file2 = mock_repo_path / 'file2.png'
    file2.write_text('Hello World!')
    files = walk_repo(mock_repo_path)
    assert len(files) == 1
    assert files[0]['filename'] == 'file1.txt'

def test_get_repo_summary():
    """Test generating a summary of the repository."""
    files = [
        {'filename': 'file1.txt', 'relative_path': 'file1.txt', 'extension': '.txt', 'content': 'Hello World!', 'size': 12},
        {'filename': 'file2.py', 'relative_path': 'file2.py', 'extension': '.py', 'content': 'print("Hello World!")', 'size': 20},
    ]
    summary = get_repo_summary(files)
    assert summary['total_files'] == 2
    assert summary['total_characters'] == 32
    assert summary['file_types'] == {'.txt': 1, '.py': 1}
    assert len(summary['largest_files']) == 2

def test_get_repo_summary_empty():
    """Test generating a summary of an empty repository."""
    files = []
    summary = get_repo_summary(files)
    assert summary['total_files'] == 0
    assert summary['total_characters'] == 0
    assert summary['file_types'] == {}
    assert summary['largest_files'] == []
```