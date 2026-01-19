# MD Book Tools

A comprehensive toolkit for reading and writing markdown books in the terminal. Supports multiple book formats including mdBook, GitBook, Leanpub, and Bookdown.

## Tools Included

| Tool | Command | Description |
|------|---------|-------------|
| **MD Book Reader** | `md-book-reader` | Terminal-based markdown book reader with rich formatting |
| **MD Book Writer** | `md-book-writer` | CLI for creating and managing markdown book projects |

## Features

### Reader Features
- **Multi-Format Support**: Automatically detects and parses various book structures
- **YAML Frontmatter**: Extracts metadata (title, author, date, draft status) from chapter files
- **Rich Terminal Display**: Beautiful markdown rendering with syntax highlighting
- **Interactive Navigation**: Forward/back navigation, chapter jumping, and table of contents
- **Cross-platform**: Works on macOS, Linux, and Windows
- **Auto-Detection**: Falls back to intelligent chapter discovery when no manifest is present

### Writer Features
- **Project Scaffolding**: Initialize new book projects with proper structure
- **Chapter Management**: Create chapters with automatic numbering and frontmatter
- **TOC Generation**: Automatically generate and update SUMMARY.md from chapters
- **Draft Support**: Mark chapters as drafts during development

## Version Information

MD Book Tools uses semantic versioning with build tracking:

```
Format: MAJOR.MINOR.PATCH+build.BUILD_NUMBER
Example: 2.1.0+build.42
```

- **MAJOR**: Breaking changes to CLI interface or file format
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes and minor improvements
- **BUILD**: Git commit count for tracking incremental changes

Check version with:
```bash
md-book-reader --version
md-book-writer --version
```

## Supported Book Formats

Both tools support reading and writing books in these formats:

### For Reading

The reader detects book structure in the following priority order:

#### 1. SUMMARY.md (mdBook / GitBook)

```markdown
# Summary

- [Introduction](README.md)
- [Chapter 1](chapter-01.md)
- [Chapter 2](chapter-02.md)
```

#### 2. Book.txt (Leanpub)

```
frontmatter:
introduction.md
mainmatter:
chapter-01.md
chapter-02.md
backmatter:
appendix.md
```

#### 3. _bookdown.yml (Bookdown)

```yaml
book_filename: "my-book"
rmd_files:
  - index.Rmd
  - 01-intro.Rmd
  - 02-methods.Rmd
```

#### 4. book.toml (mdBook)

Reads mdBook configuration and looks for `src/SUMMARY.md`.

#### 5. Auto-Detection

When no manifest file is found, the reader:
- Sorts `.md` files alphanumerically
- Skips files prefixed with `_`
- Recognizes standard chapter patterns:
  - `01-chapter-name.md`
  - `chapter-01.md`
  - `ch01-name.md`
- Treats `README.md` or `index.md` as introduction

### For Writing

The writer creates books using the mdBook/GitBook-compatible structure:
- `SUMMARY.md` for table of contents
- `book.yaml` for metadata
- `chapters/` directory for chapter files

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
cd book-reader
pip install -e .
```

This installs both `md-book-reader` and `md-book-writer` commands.

### Install Dependencies Only

```bash
pip install click rich markdown pymdown-extensions pygments pyyaml
```

## Quick Start

### Reading an Existing Book

```bash
# Read book in current directory
md-book-reader

# Read book from specific directory
md-book-reader --root /path/to/book

# Jump directly to chapter 5
md-book-reader --chapter 5

# Show table of contents
md-book-reader --toc

# Show detected book structure info
md-book-reader --info
```

### Creating a New Book

```bash
# Initialize a new book (interactive prompts for title/author)
md-book-writer init

# Initialize with options
md-book-writer init --title "My Book" --author "Jane Doe" --path ./my-book

# Add a new chapter (prompts for title)
md-book-writer new-chapter

# Add chapter with options
md-book-writer new-chapter --title "Getting Started" --draft

# Regenerate SUMMARY.md from existing chapters
md-book-writer toc
```

### Complete Book Writing Workflow

```bash
# 1. Create a new book project
mkdir my-new-book && cd my-new-book
md-book-writer init --title "The Complete Guide" --author "Your Name"

# 2. Add chapters
md-book-writer new-chapter --title "Introduction"
md-book-writer new-chapter --title "Basic Concepts"
md-book-writer new-chapter --title "Advanced Topics" --draft

# 3. Edit your chapters in chapters/ directory
# ... write content in your favorite editor ...

# 4. Regenerate TOC after manual changes
md-book-writer toc

# 5. Read your book
md-book-reader
```

## Command Reference

### md-book-reader

```bash
md-book-reader [OPTIONS]

Options:
  -r, --root PATH      Root directory of the book (defaults to current directory)
  -c, --chapter NUM    Jump to specific chapter
  --toc                Show table of contents
  --info               Show detected book structure info and exit
  --version            Show version and exit
  --help               Show help message and exit
```

#### Interactive Navigation

Once in the reader, use these commands:

| Key | Action |
|-----|--------|
| `n` | Navigate to next chapter |
| `p` | Navigate to previous chapter |
| `toc` | Show table of contents |
| `j` | Jump to specific chapter |
| `q` | Quit the reader |

### md-book-writer

```bash
md-book-writer [COMMAND] [OPTIONS]

Commands:
  init         Create a new book structure
  new-chapter  Add a new chapter with frontmatter
  toc          Regenerate SUMMARY.md from chapters
```

#### init

```bash
md-book-writer init [OPTIONS]

Options:
  -t, --title TEXT   Book title (prompted if not provided)
  -a, --author TEXT  Author name (prompted if not provided)
  -p, --path PATH    Path where to create the book (default: current directory)
```

Creates:
- `book.yaml` - Book metadata
- `SUMMARY.md` - Table of contents
- `chapters/` - Directory for chapter files

#### new-chapter

```bash
md-book-writer new-chapter [OPTIONS]

Options:
  -t, --title TEXT   Chapter title (prompted if not provided)
  -d, --draft        Mark chapter as draft
  -p, --path PATH    Path to book root (default: current directory)
```

Creates a new chapter file with:
- Auto-incremented chapter number
- YAML frontmatter (title, chapter number, date, draft status)
- Slugified filename (e.g., `01-getting-started.md`)
- Updates SUMMARY.md automatically

#### toc

```bash
md-book-writer toc [OPTIONS]

Options:
  -p, --path PATH    Path to book root (default: current directory)
```

Scans `chapters/` directory and regenerates `SUMMARY.md` with all chapters.

## Environment Variables

Set the default book root directory:

```bash
export BOOK_ROOT=/path/to/your/book
md-book-reader
```

## YAML Frontmatter Support

Both tools support YAML frontmatter in chapter files:

```markdown
---
title: "Getting Started"
author: "Jane Doe"
date: 2024-01-15
chapter: 1
draft: false
---

# Getting Started

Chapter content here...
```

Supported frontmatter fields:
- `title`: Chapter title (overrides filename-derived title)
- `author`: Chapter author
- `date`: Publication/revision date
- `chapter`: Chapter number
- `draft`: Boolean indicating draft status (shown in TOC)

## Directory Structures

### Writer Output Structure

```
my-book/
├── book.yaml          # Book metadata
├── SUMMARY.md         # Table of contents
└── chapters/
    ├── 01-introduction.md
    ├── 02-basic-concepts.md
    └── 03-advanced-topics.md
```

### Flat Structure (Auto-detected)

```
my-book/
├── README.md          # Introduction
├── 01-getting-started.md
├── 02-basic-concepts.md
├── 03-advanced-topics.md
└── 04-conclusion.md
```

### Chapter Directory Structure

```
my-book/
├── index.md
├── chapter-01/
│   └── content/
│       └── chapter-01-complete.md
├── chapter-02/
│   └── content/
│       └── chapter-02-complete.md
└── chapter-03/
    └── content/
        └── chapter-03-complete.md
```

### mdBook Structure

```
my-book/
├── book.toml
└── src/
    ├── SUMMARY.md
    ├── chapter-01.md
    └── chapter-02.md
```

### Leanpub Structure

```
my-book/
├── Book.txt
└── manuscript/
    ├── introduction.md
    ├── chapter-01.md
    └── chapter-02.md
```

## Configuration

Modify `config.py` to customize:

- Directories to skip during discovery
- Chapter file patterns
- Introduction file names
- Display settings
- Color scheme
- Markdown rendering options

### Example: Custom Skip Directories

```python
SKIP_DIRECTORIES = {
    'research', 'drafts', 'notes',
    'archive', '.git', '__pycache__'
}
```

### Example: Custom Colors

```python
COLORS = {
    'header': 'bold cyan',
    'chapter_title': 'bold yellow',
    'error': 'red',
    'success': 'green'
}
```

## Troubleshooting

### "No markdown files found"

- Verify the path to your book directory
- Use `--root` option to specify correct path
- Ensure the directory contains `.md` files

### "No chapters found"

- Check that your book has a recognizable structure
- Use `--info` to see what the reader detected
- Add a `SUMMARY.md` or `Book.txt` manifest file

### "Error reading chapter"

- Check file permissions
- Verify markdown files are UTF-8 encoded
- Ensure files are not corrupted

### "chapters/ directory not found" (Writer)

- Run `md-book-writer init` first to create the book structure
- Or manually create the `chapters/` directory

### Debug with --info

```bash
md-book-reader --root /path/to/book --info
```

This shows:
- Detected book title
- Root directory path
- Detected format type
- List of all discovered chapters with file paths

## Development

### File Structure

```
book-reader/
├── book_reader.py        # Reader application
├── book_writer.py        # Writer application
├── version.py            # Version management
├── config.py             # Configuration settings
├── structure_detector.py # Book format detection
├── pyproject.toml        # Package configuration
└── README.md             # This documentation
```

### Extending the Tools

```python
from book_reader import BookReader
from structure_detector import StructureDetector

# Custom structure detection
class CustomDetector(StructureDetector):
    def detect_structure(self):
        # Custom detection logic
        pass

# Extended reader
class ExtendedReader(BookReader):
    def search_content(self, query: str):
        """Search for text across all chapters."""
        pass

    def export_chapter(self, chapter_num: int, format: str):
        """Export chapter to different formats."""
        pass
```

## Requirements

### Python Dependencies

- `click>=8.0.0` - Command line interface
- `rich>=13.0.0` - Terminal formatting
- `markdown>=3.4.0` - Markdown processing
- `pymdown-extensions>=9.0.0` - Enhanced markdown features
- `pygments>=2.14.0` - Syntax highlighting
- `pyyaml>=6.0.0` - YAML frontmatter parsing

### Optional Dependencies

- `tomli>=2.0.0` - TOML parsing (Python < 3.11)

### System Requirements

- Python 3.8+
- Terminal with UTF-8 support
- Minimum 80 character terminal width (120 recommended)

## License

MIT License

## Version History

- **v2.1.0** - Added md-book-writer tool with init, new-chapter, and toc commands
- **v2.0.0** - Generic multi-format support, YAML frontmatter parsing
- **v1.0.0** - Initial release (Augmented Programmer specific)
