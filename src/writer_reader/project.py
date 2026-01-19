#!/usr/bin/env python3
"""
Project Initialization

Create new manuscript project structure.
"""

from pathlib import Path

import yaml


def init_project(book_dir: Path, title: str, author: str) -> dict:
    """Initialize a new manuscript project."""
    book_dir = Path(book_dir)
    book_dir.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    dirs = ["chapters", "segments", "research", "outlines"]
    for d in dirs:
        (book_dir / d).mkdir(exist_ok=True)

    # Create project config
    config = {
        "title": title,
        "author": author,
        "version": "0.1.0",
        "chapters": [],
    }

    config_path = book_dir / "book.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Create .gitignore
    gitignore = """# Writer-Reader
*.pyc
__pycache__/
.DS_Store
*.swp
*.swo
.env
venv/
"""
    gitignore_path = book_dir / ".gitignore"
    gitignore_path.write_text(gitignore)

    # Create README
    readme = f"""# {title}

By {author}

## Structure

```
{book_dir.name}/
├── chapters/       # Full chapter markdown files
├── segments/       # Segmented chapters for editing
├── outlines/       # Chapter outlines
├── research/       # Research notes
└── book.yaml       # Project configuration
```

## Usage

```bash
# Segment chapters into editable segments
writer-reader segment

# Start the editor server
writer-reader serve

# Assemble segments back into chapters
writer-reader assemble
```

## Editor

Open http://localhost:5555 after running `writer-reader serve`
"""
    readme_path = book_dir / "README.md"
    readme_path.write_text(readme)

    # Create sample chapter
    sample_chapter = f"""# Chapter 1: Introduction

Your opening paragraph goes here.

---

## The Beginning

Start your story here.

---

## What Follows

Continue the narrative.
"""
    sample_path = book_dir / "chapters" / "chapter-01-introduction.md"
    sample_path.write_text(sample_chapter)

    return {
        "created": [
            str(config_path),
            str(gitignore_path),
            str(readme_path),
            str(sample_path),
        ]
    }
