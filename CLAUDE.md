# CLAUDE.md - Writer-Reader Project Guidelines

## Project Overview

**Writer-Reader** is a segment-based book manuscript editor with git integration. It breaks book chapters into individual markdown segments for granular editing.

- **Framework**: Flask (Python web)
- **CLI**: Click-based at `writer_reader.cli:main`
- **Python**: 3.10+
- **Build System**: hatchling

## Priority Rules

### RED - CRITICAL (Must Follow Always)

1. **Never commit secrets** - No API keys, tokens, or credentials in code
2. **Run tests before commits** - `pytest` must pass
3. **Preserve user manuscript data** - Never delete/overwrite without explicit request
4. **Type-safe YAML handling** - Always use `yaml.safe_load()` for reading
5. **Git operations require user confirmation** - Never auto-push

### YELLOW - IMPORTANT

1. **Format before commit** - Run `black .` and `ruff check --fix .`
2. **Lint clean** - Zero ruff errors before PR
3. **Test coverage** - New features require tests
4. **Error messages** - User-facing errors must be clear and actionable
5. **Encoding** - Always use `encoding="utf-8"` for file operations

### GREEN - RECOMMENDED

1. **Docstrings** - All public functions/classes need docstrings
2. **Type hints** - Add type hints to function signatures
3. **Small commits** - One logical change per commit
4. **Conventional commits** - Use `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
5. **Path handling** - Use `pathlib.Path` over `os.path`

### WHITE - OPTIONAL

1. **Line length** - 100 chars (configured in pyproject.toml)
2. **Import ordering** - ruff handles this automatically
3. **Quote style** - Double quotes preferred

## Single-Path Workflows

### Setup (ONE way)
```bash
pip install -e ".[dev]"
```

### Testing (ONE way)
```bash
pytest
```

### Linting (ONE way)
```bash
ruff check . && black --check .
```

### Formatting (ONE way)
```bash
black . && ruff check --fix .
```

### Running Server (ONE way)
```bash
writer-reader serve --book-dir /path/to/book
```

## Architecture

```
src/writer_reader/
├── __init__.py      # Package metadata, version
├── cli.py           # Click CLI commands (serve, segment, assemble, init)
├── project.py       # Project initialization logic
├── segmenter.py     # Chapter segmentation/assembly logic
├── server.py        # Flask app factory and API routes
└── static/          # Static assets (editor HTML)
```

### Key Components

1. **CLI** (`cli.py`): Entry point, delegates to other modules
2. **Server** (`server.py`): Flask app with REST API for segments and git
3. **Segmenter** (`segmenter.py`): Parses chapters into segments, reassembles
4. **Project** (`project.py`): Creates new manuscript directory structure

### Data Flow

```
chapters/*.md  -->  segment_book()  -->  segments/ch01-*/
                                              ├── _meta.yaml
                                              └── *.md

segments/ch01-*/*.md  -->  assemble_chapters()  -->  chapters/*.md
```

## Code Patterns

### Flask Routes
```python
@app.route("/api/segment/<path:segment_path>")
def get_segment(segment_path: str):
    filepath = segments_dir / segment_path
    if not filepath.exists():
        return jsonify({"error": "Segment not found"}), 404
    content = filepath.read_text(encoding="utf-8")
    return jsonify({"path": segment_path, "content": content})
```

### CLI Commands
```python
@main.command()
@click.option("--port", "-p", default=5555)
def serve(port: int):
    """Start the editor server."""
    from .server import create_app
    app = create_app(Path.cwd())
    app.run(port=port)
```

### YAML Handling
```python
# Reading (safe)
with open(meta_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

# Writing
with open(meta_path, "w", encoding="utf-8") as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

## Testing Approach

- **Framework**: pytest
- **Location**: `tests/`
- **Naming**: `test_*.py` files, `test_*` functions
- **Fixtures**: Use pytest fixtures for setup
- **Coverage**: `pytest-cov` available

### Test Categories
1. Unit tests for segmenter parsing logic
2. Unit tests for project initialization
3. Integration tests for Flask API endpoints
4. CLI tests using Click's test runner

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/index` | GET | Master chapter/segment index |
| `/api/chapter/<num>` | GET | Chapter metadata |
| `/api/segment/<path>` | GET/PUT | Read/write segment content |
| `/api/git/status` | GET | Git status |
| `/api/git/diff` | GET | Show changes |
| `/api/git/add` | POST | Stage files |
| `/api/git/commit` | POST | Commit changes |
| `/api/git/push` | POST | Push to remote |

## Dependencies

### Runtime
- flask>=2.0
- flask-cors>=3.0
- pyyaml>=6.0
- click>=8.0

### Development
- pytest>=7.0
- pytest-cov>=4.0
- black>=23.0
- ruff>=0.1.0

## File Conventions

### Chapters
- Location: `chapters/`
- Naming: `chapter-NN-title.md` or `chNN-title.md`

### Segments
- Location: `segments/chNN-title/`
- Metadata: `_meta.yaml`
- Content: `NN-section-name.md`

## Common Issues

### "Index not found"
Run `writer-reader segment` to create segment index.

### Encoding errors
Ensure all files use UTF-8 encoding.

### Git command timeout
Git operations have 30-second timeout. Check repository state.
