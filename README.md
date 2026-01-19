# Writer-Reader

Segment-based book manuscript editor with git integration.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Overview

Writer-Reader breaks book chapters into individual markdown segments for granular editing, with built-in git integration for tracking changes.

**Features:**
- 📖 Segment chapters into editable markdown files
- ✏️ In-browser editing with live preview
- 🔀 Git integration (status, diff, commit, push)
- 📁 Convention-based file organization
- 🔄 Assemble segments back into chapters

## Installation

```bash
pip install writer-reader
```

Or install from source:

```bash
git clone https://github.com/bobmatnyc/writer-reader.git
cd writer-reader
pip install -e .
```

## Quick Start

### 1. Initialize a new project

```bash
writer-reader init my-book --title "My Book" --author "My Name"
cd my-book
```

### 2. Add your chapters

Place markdown files in `chapters/`:
```
my-book/
├── chapters/
│   ├── chapter-01-introduction.md
│   ├── chapter-02-the-beginning.md
│   └── ...
```

### 3. Segment chapters

```bash
writer-reader segment
```

Creates:
```
my-book/
├── segments/
│   ├── ch01-introduction/
│   │   ├── _meta.yaml
│   │   ├── 01-introduction.md
│   │   ├── 02-the-beginning.md
│   │   └── ...
│   └── _index.yaml
```

### 4. Start the editor

```bash
writer-reader serve
```

Open http://localhost:5555

## File Convention

```
segments/
├── ch01-chapter-title/
│   ├── _meta.yaml           # Chapter metadata
│   ├── 01-opening.md        # First segment
│   ├── 02-section-name.md   # Named section
│   └── ...
├── ch02-next-chapter/
│   └── ...
└── _index.yaml              # Master index
```

### Segment Types

- **chapter-title**: The `# Chapter N: Title` heading
- **section**: `## Section Name` headers
- **prose**: Content between `---` dividers

### Metadata Format

`_meta.yaml`:
```yaml
chapter: 1
title: The Beginning
source_file: chapter-01-the-beginning.md
segments:
  - file: 01-the-beginning.md
    title: "The Beginning"
    type: chapter-title
    index: 1
  - file: 02-first-section.md
    title: "First Section"
    type: section
    index: 2
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `writer-reader init <dir>` | Initialize a new manuscript project |
| `writer-reader segment [dir]` | Segment chapters into individual files |
| `writer-reader serve` | Start the editor server |
| `writer-reader assemble [dir]` | Assemble segments back into chapters |

### Options

```bash
# Serve on different port
writer-reader serve --port 8080

# Segment with force overwrite
writer-reader segment --force

# Assemble specific chapter
writer-reader assemble --chapter 5
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/index` | GET | Get all chapters/segments |
| `/api/chapter/<num>` | GET | Get chapter metadata |
| `/api/segment/<path>` | GET | Read segment content |
| `/api/segment/<path>` | PUT | Write segment content |
| `/api/git/status` | GET | Git status |
| `/api/git/diff` | GET | Show uncommitted changes |
| `/api/git/add` | POST | Stage files |
| `/api/git/commit` | POST | Commit with message |
| `/api/git/push` | POST | Push to remote |
| `/api/assemble/<num>` | GET | Preview assembled chapter |
| `/api/assemble/<num>` | POST | Save assembled chapter |

## Development

```bash
# Clone repository
git clone https://github.com/bobmatnyc/writer-reader.git
cd writer-reader

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/ --fix
```

## Version History

- **0.1.0** - Initial release
  - Chapter segmentation
  - In-browser editing
  - Git integration
  - CLI commands

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Bob Matsuoka ([@bobmatnyc](https://github.com/bobmatnyc))
