"""
Configuration settings for the Generic Markdown Book Reader
"""

import os
from pathlib import Path
from typing import List, Set


class BookReaderConfig:
    """Configuration class for book reader settings."""

    # Directories to skip during chapter discovery
    SKIP_DIRECTORIES: Set[str] = {
        'research', 'drafts', 'notes', 'project-management',
        'background', 'tasks', 'archive', '.git', '__pycache__',
        'node_modules', '.venv', 'venv', 'env'
    }

    # File patterns for standard chapter naming (regex patterns)
    CHAPTER_FILE_PATTERNS: List[str] = [
        r'^(\d+)[-_](.+)\.md$',           # 01-chapter-name.md, 01_chapter_name.md
        r'^chapter[-_]?(\d+)[-_]?(.*)\.md$',  # chapter-01.md, chapter01.md, chapter-01-name.md
        r'^ch(\d+)[-_]?(.*)\.md$',         # ch01.md, ch01-name.md
        r'^part[-_]?(\d+)[-_]?(.*)\.md$',  # part-01.md, part1-intro.md
    ]

    # Files to treat as introduction/index (in priority order)
    INTRO_FILES: List[str] = [
        'README.md',
        'readme.md',
        'index.md',
        'INDEX.md',
        'introduction.md',
        'INTRODUCTION.md',
        '00-introduction.md',
        '00-intro.md',
    ]

    # Files to skip (not part of book content)
    SKIP_FILES: Set[str] = {
        'CONTRIBUTING.md',
        'CHANGELOG.md',
        'LICENSE.md',
        'CODE_OF_CONDUCT.md',
    }

    # Book structure detection files (in priority order)
    STRUCTURE_FILES = {
        'summary': 'SUMMARY.md',      # mdBook / GitBook
        'leanpub': 'Book.txt',        # Leanpub
        'bookdown': '_bookdown.yml',  # Bookdown
        'mdbook': 'book.toml',        # mdBook config
    }

    # Display settings
    CONSOLE_WIDTH: int = 120
    WRAP_TEXT: bool = True

    # Navigation settings
    NAVIGATION_HELP = {
        'n': 'Next chapter',
        'p': 'Previous chapter',
        'toc': 'Table of contents',
        'j': 'Jump to chapter',
        's': 'Search',
        'q': 'Quit'
    }

    # Color scheme
    COLORS = {
        'header': 'bold blue',
        'chapter_title': 'bold green',
        'navigation': 'dim',
        'error': 'red',
        'success': 'green',
        'warning': 'yellow',
        'info': 'blue'
    }

    # Markdown rendering settings
    MARKDOWN_EXTENSIONS: List[str] = [
        'codehilite',
        'fenced_code',
        'tables',
        'toc',
        'footnotes',
        'attr_list',
        'def_list'
    ]

    # Code highlighting theme
    CODE_THEME: str = 'github-dark'

    @classmethod
    def get_book_root(cls) -> Path:
        """Get the book root directory from environment variable or current directory."""
        env_root = os.environ.get('BOOK_ROOT')
        if env_root:
            return Path(env_root)
        return Path.cwd()

    @classmethod
    def validate_book_root(cls, book_root: Path) -> bool:
        """Validate that the book root directory exists and contains markdown files."""
        if not book_root.exists():
            return False

        if not book_root.is_dir():
            return False

        # Check for any markdown files
        md_files = list(book_root.glob('*.md')) + list(book_root.glob('**/*.md'))
        return len(md_files) > 0
