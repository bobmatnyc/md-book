"""
Book Structure Detection Module

Detects and parses various book format structures:
- SUMMARY.md (mdBook / GitBook)
- Book.txt (Leanpub)
- _bookdown.yml (Bookdown)
- book.toml (mdBook)
- Auto-detection via filename patterns
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tomllib
    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomli as tomllib
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False

from config import BookReaderConfig


@dataclass
class Chapter:
    """Represents a single chapter in the book."""
    number: int
    title: str
    file_path: Path
    is_intro: bool = False
    is_draft: bool = False
    author: Optional[str] = None
    date: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class BookStructure:
    """Represents the detected book structure."""
    format_type: str  # 'summary', 'leanpub', 'bookdown', 'mdbook', 'auto'
    title: Optional[str] = None
    author: Optional[str] = None
    chapters: List[Chapter] = field(default_factory=list)
    root_path: Optional[Path] = None


class StructureDetector:
    """Detects and parses book structure from various formats."""

    def __init__(self, book_root: Path):
        self.book_root = Path(book_root)
        self.config = BookReaderConfig()

    def detect_structure(self) -> BookStructure:
        """
        Detect book structure in priority order:
        1. SUMMARY.md (mdBook/GitBook)
        2. Book.txt (Leanpub)
        3. _bookdown.yml (Bookdown)
        4. book.toml (mdBook config)
        5. Auto-detect from file patterns
        """
        # Check for SUMMARY.md
        summary_path = self.book_root / 'SUMMARY.md'
        if summary_path.exists():
            return self._parse_summary_md(summary_path)

        # Check for Book.txt (Leanpub)
        leanpub_path = self.book_root / 'Book.txt'
        if leanpub_path.exists():
            return self._parse_leanpub(leanpub_path)

        # Check for _bookdown.yml
        bookdown_path = self.book_root / '_bookdown.yml'
        if bookdown_path.exists():
            return self._parse_bookdown(bookdown_path)

        # Check for book.toml (mdBook)
        mdbook_path = self.book_root / 'book.toml'
        if mdbook_path.exists():
            return self._parse_mdbook_toml(mdbook_path)

        # Fall back to auto-detection
        return self._auto_detect()

    def _parse_summary_md(self, summary_path: Path) -> BookStructure:
        """Parse SUMMARY.md format (mdBook/GitBook)."""
        structure = BookStructure(
            format_type='summary',
            root_path=self.book_root
        )

        try:
            content = summary_path.read_text(encoding='utf-8')
        except Exception:
            return self._auto_detect()

        chapters = []
        chapter_num = 0

        # Parse markdown links: [Title](path/to/file.md)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)')

        for line in content.split('\n'):
            match = link_pattern.search(line)
            if match:
                title = match.group(1).strip()
                rel_path = match.group(2).strip()

                # Resolve the path relative to book root
                file_path = self.book_root / rel_path
                if not file_path.exists():
                    # Try relative to SUMMARY.md location
                    file_path = summary_path.parent / rel_path

                if file_path.exists():
                    is_intro = rel_path.lower() in ['readme.md', 'index.md', 'introduction.md']

                    if is_intro:
                        chapter = Chapter(
                            number=0,
                            title=title,
                            file_path=file_path,
                            is_intro=True
                        )
                    else:
                        chapter_num += 1
                        chapter = Chapter(
                            number=chapter_num,
                            title=title,
                            file_path=file_path
                        )

                    # Parse frontmatter for additional metadata
                    self._enrich_with_frontmatter(chapter)
                    chapters.append(chapter)

        structure.chapters = chapters
        return structure

    def _parse_leanpub(self, book_txt_path: Path) -> BookStructure:
        """Parse Book.txt format (Leanpub)."""
        structure = BookStructure(
            format_type='leanpub',
            root_path=self.book_root
        )

        try:
            content = book_txt_path.read_text(encoding='utf-8')
        except Exception:
            return self._auto_detect()

        chapters = []
        chapter_num = 0

        # Leanpub Book.txt is a simple list of file paths
        manuscript_dir = self.book_root / 'manuscript'
        base_dir = manuscript_dir if manuscript_dir.exists() else self.book_root

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Handle frontmatter.txt, backmatter.txt markers
            if line in ['frontmatter:', 'mainmatter:', 'backmatter:']:
                continue

            file_path = base_dir / line
            if not file_path.exists():
                file_path = self.book_root / line

            if file_path.exists() and file_path.suffix == '.md':
                title = self._extract_title_from_file(file_path) or file_path.stem
                is_intro = line.lower() in ['introduction.md', 'preface.md', 'foreword.md']

                if is_intro:
                    chapter = Chapter(
                        number=0,
                        title=title,
                        file_path=file_path,
                        is_intro=True
                    )
                else:
                    chapter_num += 1
                    chapter = Chapter(
                        number=chapter_num,
                        title=title,
                        file_path=file_path
                    )

                self._enrich_with_frontmatter(chapter)
                chapters.append(chapter)

        structure.chapters = chapters
        return structure

    def _parse_bookdown(self, bookdown_path: Path) -> BookStructure:
        """Parse _bookdown.yml format."""
        structure = BookStructure(
            format_type='bookdown',
            root_path=self.book_root
        )

        if not YAML_AVAILABLE:
            return self._auto_detect()

        try:
            content = bookdown_path.read_text(encoding='utf-8')
            config = yaml.safe_load(content)
        except Exception:
            return self._auto_detect()

        chapters = []
        chapter_num = 0

        # Get book title if available
        structure.title = config.get('book_filename', config.get('title'))

        # Get chapter files from rmd_files or chapter_name pattern
        rmd_files = config.get('rmd_files', [])

        for file_name in rmd_files:
            # Bookdown uses .Rmd files, but we support .md too
            file_path = self.book_root / file_name
            if not file_path.exists():
                # Try .md extension
                md_path = file_path.with_suffix('.md')
                if md_path.exists():
                    file_path = md_path
                else:
                    continue

            title = self._extract_title_from_file(file_path) or file_path.stem
            is_intro = 'index' in file_name.lower() or file_name == rmd_files[0]

            if is_intro and chapter_num == 0:
                chapter = Chapter(
                    number=0,
                    title=title,
                    file_path=file_path,
                    is_intro=True
                )
            else:
                chapter_num += 1
                chapter = Chapter(
                    number=chapter_num,
                    title=title,
                    file_path=file_path
                )

            self._enrich_with_frontmatter(chapter)
            chapters.append(chapter)

        structure.chapters = chapters
        return structure

    def _parse_mdbook_toml(self, toml_path: Path) -> BookStructure:
        """Parse book.toml and look for SUMMARY.md in src directory."""
        structure = BookStructure(
            format_type='mdbook',
            root_path=self.book_root
        )

        if TOML_AVAILABLE:
            try:
                content = toml_path.read_text(encoding='utf-8')
                config = tomllib.loads(content)
                structure.title = config.get('book', {}).get('title')
                structure.author = config.get('book', {}).get('authors', [None])[0] if config.get('book', {}).get('authors') else None
            except Exception:
                pass

        # mdBook uses src/SUMMARY.md by default
        src_summary = self.book_root / 'src' / 'SUMMARY.md'
        if src_summary.exists():
            summary_structure = self._parse_summary_md(src_summary)
            structure.chapters = summary_structure.chapters
            return structure

        # Fall back to auto-detection
        return self._auto_detect()

    def _auto_detect(self) -> BookStructure:
        """
        Auto-detect chapters from file patterns.
        - Sort .md files alphanumerically
        - Skip _ prefixed files
        - Recognize standard chapter patterns
        """
        structure = BookStructure(
            format_type='auto',
            root_path=self.book_root
        )

        chapters = []
        chapter_num = 0

        # First, check for intro files
        for intro_file in self.config.INTRO_FILES:
            intro_path = self.book_root / intro_file
            if intro_path.exists():
                title = self._extract_title_from_file(intro_path) or 'Introduction'
                chapter = Chapter(
                    number=0,
                    title=title,
                    file_path=intro_path,
                    is_intro=True
                )
                self._enrich_with_frontmatter(chapter)
                chapters.append(chapter)
                break

        # Collect all markdown files
        md_files = self._collect_markdown_files()

        # Sort alphanumerically
        md_files.sort(key=lambda p: (self._extract_sort_key(p), p.name.lower()))

        for file_path in md_files:
            # Skip files we've already added as intro
            if any(c.file_path == file_path for c in chapters):
                continue

            # Skip files in skip list
            if file_path.name in self.config.SKIP_FILES:
                continue

            title = self._extract_title_from_file(file_path) or self._title_from_filename(file_path.stem)

            chapter_num += 1
            chapter = Chapter(
                number=chapter_num,
                title=title,
                file_path=file_path
            )
            self._enrich_with_frontmatter(chapter)
            chapters.append(chapter)

        structure.chapters = chapters
        return structure

    def _collect_markdown_files(self) -> List[Path]:
        """Collect markdown files, respecting skip patterns."""
        md_files = []

        # Check for chapter directories (chapter-01, etc.)
        chapter_dirs = sorted(self.book_root.glob('chapter-*'))
        if chapter_dirs:
            for chapter_dir in chapter_dirs:
                # Look in content subdirectory first
                content_dir = chapter_dir / 'content'
                if content_dir.exists():
                    content_files = list(content_dir.glob('*.md'))
                    if content_files:
                        # Pick best file from content directory
                        best_file = self._pick_best_content_file(content_files)
                        if best_file:
                            md_files.append(best_file)
                        continue

                # Otherwise look for .md files directly in chapter dir
                direct_files = [f for f in chapter_dir.glob('*.md')
                              if not f.name.startswith('_')]
                if direct_files:
                    md_files.append(self._pick_best_content_file(direct_files))

            return md_files

        # No chapter directories, look for flat structure
        for md_file in self.book_root.glob('*.md'):
            # Skip underscore-prefixed files
            if md_file.name.startswith('_'):
                continue

            # Skip common non-content files
            if md_file.name.upper() in ['SUMMARY.MD', 'BOOK.TXT']:
                continue

            # Skip intro files (handled separately)
            if md_file.name in self.config.INTRO_FILES:
                continue

            # Skip files in skip list
            if md_file.name in self.config.SKIP_FILES:
                continue

            md_files.append(md_file)

        return md_files

    def _pick_best_content_file(self, files: List[Path]) -> Optional[Path]:
        """Pick the best content file from a list based on priority patterns."""
        if not files:
            return None

        # Priority patterns
        priority_patterns = [
            r'.*complete\.md$',
            r'.*enhanced\.md$',
            r'.*revised\.md$',
            r'.*final\.md$',
        ]

        for pattern in priority_patterns:
            for f in files:
                if re.match(pattern, f.name, re.IGNORECASE):
                    return f

        # Return first file if no priority match
        return files[0]

    def _extract_sort_key(self, file_path: Path) -> Tuple[int, str]:
        """Extract a sort key from filename for proper ordering."""
        name = file_path.stem

        # Try to extract leading numbers
        match = re.match(r'^(\d+)', name)
        if match:
            return (int(match.group(1)), name)

        # Try chapter patterns
        for pattern in self.config.CHAPTER_FILE_PATTERNS:
            match = re.match(pattern, file_path.name, re.IGNORECASE)
            if match:
                return (int(match.group(1)), name)

        # No number found, sort alphabetically at the end
        return (999999, name)

    def _extract_title_from_file(self, file_path: Path) -> Optional[str]:
        """Extract title from file (frontmatter or first heading)."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        # Check for YAML frontmatter
        if content.startswith('---'):
            frontmatter = self._parse_frontmatter(content)
            if frontmatter and 'title' in frontmatter:
                return frontmatter['title']

        # Look for first markdown heading
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()

        return None

    def _title_from_filename(self, stem: str) -> str:
        """Convert filename stem to title."""
        # Remove leading numbers and separators
        title = re.sub(r'^\d+[-_]?', '', stem)
        # Replace separators with spaces
        title = re.sub(r'[-_]+', ' ', title)
        # Title case
        return title.title()

    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """Parse YAML frontmatter from content."""
        if not YAML_AVAILABLE:
            return None

        if not content.startswith('---'):
            return None

        # Find end of frontmatter
        end_match = re.search(r'\n---\s*\n', content[3:])
        if not end_match:
            return None

        frontmatter_text = content[3:3 + end_match.start()]

        try:
            return yaml.safe_load(frontmatter_text)
        except Exception:
            return None

    def _enrich_with_frontmatter(self, chapter: Chapter) -> None:
        """Enrich chapter with frontmatter metadata."""
        try:
            content = chapter.file_path.read_text(encoding='utf-8')
        except Exception:
            return

        frontmatter = self._parse_frontmatter(content)
        if not frontmatter:
            return

        # Update chapter with frontmatter data
        if 'title' in frontmatter:
            chapter.title = frontmatter['title']
        if 'author' in frontmatter:
            chapter.author = frontmatter['author']
        if 'date' in frontmatter:
            chapter.date = str(frontmatter['date'])
        if 'draft' in frontmatter:
            chapter.is_draft = frontmatter['draft']
        if 'chapter' in frontmatter:
            try:
                chapter.number = int(frontmatter['chapter'])
            except (ValueError, TypeError):
                pass

        # Store all frontmatter as metadata
        chapter.metadata = frontmatter
