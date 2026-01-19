# DEVELOPER.md - Writer-Reader Developer Guide

## Quick Start

```bash
# Clone and setup
git clone https://github.com/bobmatnyc/writer-reader.git
cd writer-reader
pip install -e ".[dev]"

# Verify installation
writer-reader --version
pytest
```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

This installs:
- Runtime: flask, flask-cors, pyyaml, click
- Dev: pytest, pytest-cov, black, ruff

### Verify Setup

```bash
# Check CLI
writer-reader --help

# Run tests
pytest

# Check linting
ruff check .
black --check .
```

## Development Workflow

### 1. Make Changes

Edit files in `src/writer_reader/`.

### 2. Format Code

```bash
black .
ruff check --fix .
```

### 3. Run Tests

```bash
pytest
```

### 4. Manual Testing

```bash
# Create test book
writer-reader init test-book --title "Test" --author "Dev"
cd test-book

# Segment and serve
writer-reader segment
writer-reader serve
```

### 5. Commit

```bash
git add .
git commit -m "feat: description of change"
```

## Architecture Overview

```
                    ┌─────────────┐
                    │   CLI       │
                    │  (click)    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Server  │    │Segmenter │    │ Project  │
    │ (Flask)  │    │          │    │          │
    └──────────┘    └──────────┘    └──────────┘
           │               │
           ▼               ▼
    ┌──────────────────────────┐
    │    File System           │
    │  (chapters/, segments/)  │
    └──────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| CLI | `cli.py` | User commands, argument parsing |
| Server | `server.py` | REST API, static file serving |
| Segmenter | `segmenter.py` | Parse/assemble chapter content |
| Project | `project.py` | Create project structure |

## Key Design Decisions

### 1. App Factory Pattern

The Flask app uses the factory pattern for testability:

```python
def create_app(book_dir: Path = None):
    app = Flask(__name__)
    # Configure routes
    return app
```

### 2. YAML for Metadata

Metadata stored in YAML for human readability:
- `_meta.yaml` per chapter
- `_index.yaml` for master index
- `book.yaml` for project config

### 3. Segment-Based Editing

Chapters split into segments for:
- Granular version control
- Focused editing
- Parallel work on different sections

### 4. Convention Over Configuration

File naming conventions drive auto-detection:
- `chapter-NN-*.md` or `chNN-*.md` for chapters
- `ch{NN}-{slug}/` for segment directories

## Adding Features

### New CLI Command

```python
# In cli.py

@main.command()
@click.option("--option", "-o", help="Option description")
def mycommand(option):
    """Command description shown in --help."""
    # Implementation
    click.echo(f"Running with {option}")
```

### New API Endpoint

```python
# In server.py create_app()

@app.route("/api/myendpoint", methods=["GET", "POST"])
def my_handler():
    if request.method == "POST":
        data = request.get_json()
        # Process data
        return jsonify({"success": True})
    return jsonify({"data": "value"})
```

### New Segment Type

```python
# In segmenter.py parse_chapter_into_segments()

# Add in the while loop:
if line.startswith("### "):  # Subsection headers
    if current_segment["content"]:
        segments.append(current_segment)
    current_segment = {
        "title": line[4:].strip(),
        "content": [line],
        "type": "subsection"
    }
    i += 1
    continue
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/writer_reader

# Specific test file
pytest tests/test_segmenter.py

# Verbose output
pytest -v
```

### Writing Tests

```python
# tests/test_example.py

import pytest
from pathlib import Path
from writer_reader.segmenter import parse_chapter_into_segments

def test_parse_chapter_title():
    content = "# Chapter 1: Test\n\nSome content."
    segments = parse_chapter_into_segments(content)

    assert len(segments) == 1
    assert segments[0]["type"] == "chapter-title"
    assert segments[0]["title"] == "Chapter 1: Test"

@pytest.fixture
def temp_book_dir(tmp_path):
    """Create temporary book directory."""
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    return tmp_path
```

### Testing Flask Routes

```python
import pytest
from writer_reader.server import create_app

@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path)
    app.config["TESTING"] = True
    return app.test_client()

def test_get_info(client):
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.get_json()
    assert "version" in data
```

## Code Style

### Formatting

```bash
# Auto-format
black .

# Check only
black --check .
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]
```

### Linting

```bash
# Check and auto-fix
ruff check . --fix

# Check only
ruff check .
```

Configuration in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "I", "N", "W", "UP"]
```

### Ruff Rules

| Code | Description |
|------|-------------|
| E | pycodestyle errors |
| F | Pyflakes |
| I | isort (import sorting) |
| N | pep8-naming |
| W | pycodestyle warnings |
| UP | pyupgrade (Python upgrades) |

## Directory Structure

```
writer-reader/
├── src/
│   └── writer_reader/
│       ├── __init__.py
│       ├── cli.py
│       ├── project.py
│       ├── segmenter.py
│       ├── server.py
│       └── static/
├── tests/
│   └── (test files)
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── CODE_STRUCTURE.md
├── DEVELOPER.md
└── .gitignore
```

## Troubleshooting

### Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

### Test Discovery Issues

```bash
# Ensure tests/ has __init__.py if needed
touch tests/__init__.py
```

### Flask Debug Issues

```bash
# Run with explicit debug
FLASK_DEBUG=1 writer-reader serve
```

### Git Operations Fail

Check:
1. Book directory is a git repository
2. Git is installed and in PATH
3. 30-second timeout not exceeded

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feat/my-feature`
3. Make changes
4. Format: `black . && ruff check --fix .`
5. Test: `pytest`
6. Commit: `git commit -m "feat: add my feature"`
7. Push: `git push origin feat/my-feature`
8. Create Pull Request

### Commit Message Format

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance
```

## Release Process

1. Update version in `src/writer_reader/__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG (if exists)
4. Commit: `git commit -m "chore: bump version to X.Y.Z"`
5. Tag: `git tag vX.Y.Z`
6. Push: `git push && git push --tags`
