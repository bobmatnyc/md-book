# CODE_STRUCTURE.md - Writer-Reader Code Analysis

## Module Overview

```
src/writer_reader/
├── __init__.py      # Package initialization
├── cli.py           # CLI entry point
├── project.py       # Project scaffolding
├── segmenter.py     # Core segmentation logic
├── server.py        # Flask API server
└── static/          # Static assets
```

## Module Details

### `__init__.py`

**Purpose**: Package metadata and version.

**Exports**:
- `__version__`: str = "0.1.0"
- `__author__`: str = "Bob Matsuoka"

---

### `cli.py`

**Purpose**: Click-based CLI entry point.

**Entry Point**: `writer_reader.cli:main`

#### Functions

| Function | Type | Description |
|----------|------|-------------|
| `main()` | @click.group | Root CLI group |
| `serve(port, host, book_dir, debug)` | @main.command | Start Flask server |
| `segment(book_dir, force)` | @main.command | Segment chapters |
| `assemble(book_dir, chapter)` | @main.command | Reassemble chapters |
| `init(book_dir, title, author)` | @main.command | Initialize project |

#### Command Details

```python
# serve command
@click.option("--port", "-p", default=5555)
@click.option("--host", "-h", default="localhost")
@click.option("--book-dir", "-d", type=click.Path(exists=True))
@click.option("--debug/--no-debug", default=True)

# segment command
@click.argument("book_dir", default=".")
@click.option("--force", "-f", is_flag=True)

# assemble command
@click.argument("book_dir", default=".")
@click.option("--chapter", "-c", type=int)

# init command
@click.argument("book_dir", default=".")
@click.option("--title", "-t", prompt="Book title")
@click.option("--author", "-a", prompt="Author name")
```

---

### `project.py`

**Purpose**: Project initialization and scaffolding.

#### Functions

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `init_project` | `(book_dir: Path, title: str, author: str)` | `dict` | Create new manuscript structure |

#### Created Structure

```
book_dir/
├── chapters/              # Chapter markdown files
├── segments/              # Segmented content
├── research/              # Research notes
├── outlines/              # Chapter outlines
├── book.yaml              # Project config
├── .gitignore             # Git ignore rules
├── README.md              # Project readme
└── chapters/chapter-01-introduction.md  # Sample chapter
```

---

### `segmenter.py`

**Purpose**: Core logic for parsing chapters into segments and reassembling.

#### Functions

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `slugify` | `(text: str)` | `str` | Convert text to URL-safe slug |
| `parse_chapter_into_segments` | `(content: str)` | `list[dict]` | Parse markdown into segments |
| `create_segment_slug` | `(title: str, index: int)` | `str` | Generate segment filename |
| `segment_chapter` | `(chapter_file: Path, chapter_num: int, chapter_title: str, segments_dir: Path)` | `dict` | Segment single chapter |
| `detect_chapters` | `(chapters_dir: Path)` | `list[dict]` | Auto-detect chapter files |
| `segment_book` | `(book_dir: Path, force: bool = False)` | `dict` | Segment all chapters |
| `assemble_chapters` | `(book_dir: Path, chapter_num: Optional[int] = None)` | `dict` | Reassemble segments |

#### Segment Types

```python
# Segment types identified during parsing
- "chapter-title"  # Lines starting with "# "
- "section"        # Lines starting with "## "
- "prose"          # Content between "---" dividers
```

#### Segment Structure

```python
{
    "title": str,      # Segment title
    "content": str,    # Markdown content
    "type": str,       # chapter-title | section | prose
    "index": int       # 1-based index
}
```

#### Chapter Detection Patterns

```python
patterns = ["chapter-*.md", "ch*.md", "*.md"]
# Extracts chapter number via regex: r"(?:chapter-?|ch)(\d+)"
```

---

### `server.py`

**Purpose**: Flask application factory and REST API.

#### Factory Function

```python
def create_app(book_dir: Path = None) -> Flask:
    """Create and configure the Flask application."""
```

#### Internal Functions

| Function | Description |
|----------|-------------|
| `run_git(args, cwd)` | Execute git commands with timeout |

#### Routes

| Route | Method | Handler | Description |
|-------|--------|---------|-------------|
| `/` | GET | `index()` | Serve editor HTML |
| `/api/info` | GET | `get_info()` | Project info |
| `/api/index` | GET | `get_index()` | Master segment index |
| `/api/chapter/<int:num>` | GET | `get_chapter()` | Chapter metadata |
| `/api/segment/<path>` | GET | `get_segment()` | Read segment |
| `/api/segment/<path>` | PUT | `save_segment()` | Write segment |
| `/api/git/status` | GET | `git_status()` | Git status |
| `/api/git/diff` | GET | `git_diff()` | Git diff |
| `/api/git/diff-staged` | GET | `git_diff_staged()` | Staged diff |
| `/api/git/add` | POST | `git_add()` | Stage files |
| `/api/git/commit` | POST | `git_commit()` | Commit changes |
| `/api/git/push` | POST | `git_push()` | Push to remote |
| `/api/git/log` | GET | `git_log()` | Commit history |
| `/api/assemble/<int:num>` | GET | `assemble_chapter()` | Preview assembled |
| `/api/assemble/<int:num>` | POST | `save_assembled_chapter()` | Save assembled |

#### App Configuration

```python
app.config["BOOK_DIR"] = book_dir      # Path to book directory
app.config["SEGMENTS_DIR"] = segments_dir  # Path to segments
```

#### Git Timeout

```python
timeout = 30  # seconds for git operations
```

---

## Data Structures

### _meta.yaml (Chapter Metadata)

```yaml
chapter: 1
title: "The Beginning"
source_file: "chapter-01-the-beginning.md"
segments:
  - file: "01-the-beginning.md"
    title: "The Beginning"
    type: "chapter-title"
    index: 1
  - file: "02-first-section.md"
    title: "First Section"
    type: "section"
    index: 2
```

### _index.yaml (Master Index)

```yaml
chapters:
  - chapter: 1
    title: "The Beginning"
    source_file: "chapter-01-the-beginning.md"
    dir: "ch01-the-beginning"
    segments:
      - file: "01-the-beginning.md"
        title: "The Beginning"
        type: "chapter-title"
        index: 1
```

### book.yaml (Project Config)

```yaml
title: "My Book"
author: "Author Name"
version: "0.1.0"
chapters: []
```

---

## Dependency Graph

```
cli.py
├── __init__ (__version__)
├── server.create_app()
├── segmenter.segment_book()
├── segmenter.assemble_chapters()
└── project.init_project()

server.py
├── flask
├── flask_cors
├── yaml
└── __init__ (__version__)

segmenter.py
├── yaml
├── shutil
└── re

project.py
└── yaml
```

---

## Extension Points

### Adding New CLI Commands

```python
# In cli.py
@main.command()
@click.option("--your-option")
def your_command(your_option):
    """Command description."""
    pass
```

### Adding New API Endpoints

```python
# In server.py create_app()
@app.route("/api/your-endpoint")
def your_handler():
    return jsonify({"data": "value"})
```

### Adding New Segment Types

```python
# In segmenter.py parse_chapter_into_segments()
# Add detection logic in the while loop
if line.startswith("### "):  # Subsection
    # Handle subsection
```

---

## Code Quality Metrics

| Metric | Value |
|--------|-------|
| Total Python files | 5 |
| Total lines (approx) | ~500 |
| Public functions | 15 |
| CLI commands | 4 |
| API endpoints | 15 |
| External dependencies | 4 |
