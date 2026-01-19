"""Writer service implementation.

Provides functionality to initialize books, add chapters, and update
the table of contents using constructor injection for dependencies.
"""

import re
from datetime import date
from pathlib import Path

from ..domain import Book, BookMetadata, Chapter, ChapterMetadata
from ..repositories.interfaces import IConfigRepository, IFileRepository
from .interfaces import IStructureService


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: The text to convert.

    Returns:
        A lowercase, hyphen-separated slug.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class WriterService:
    """Service for writing and modifying books.

    Implements IWriterService protocol using constructor injection
    for all dependencies, enabling easy testing and flexibility.
    """

    def __init__(
        self,
        file_repo: IFileRepository,
        config_repo: IConfigRepository,
        structure_service: IStructureService,
    ) -> None:
        """Initialize the writer service with required dependencies.

        Args:
            file_repo: Repository for file system operations.
            config_repo: Repository for configuration file operations.
            structure_service: Service for detecting format and parsing structure.
        """
        self._file_repo = file_repo
        self._config_repo = config_repo
        self._structure_service = structure_service

    def init_book(self, root: Path, title: str, author: str) -> Book:
        """Initialize a new book project.

        Creates the directory structure, configuration files,
        and initial content for a new book.

        Args:
            root: Root directory for the new book project.
            title: The book title.
            author: The book author.

        Returns:
            A Book object representing the newly created book.

        Raises:
            FileExistsError: If a book already exists at root.
            PermissionError: If unable to create directories/files.
        """
        root = Path(root).resolve()

        # Check if book already exists
        book_yaml_path = root / "book.yaml"
        if self._file_repo.exists(book_yaml_path):
            raise FileExistsError(f"Book already exists at {root}")

        # Create directories
        chapters_dir = root / "chapters"
        self._file_repo.mkdir(root, parents=True, exist_ok=True)
        self._file_repo.mkdir(chapters_dir, parents=True, exist_ok=True)

        # Create book.yaml configuration
        today = date.today()
        book_config = {
            "title": title,
            "author": author,
            "description": "",
            "language": "en",
            "created": today.isoformat(),
        }
        self._config_repo.save_yaml(book_yaml_path, book_config)

        # Create empty SUMMARY.md
        summary_path = root / "SUMMARY.md"
        summary_content = f"# {title}\n\n"
        self._file_repo.write_file(summary_path, summary_content)

        # Build and return Book object
        metadata = BookMetadata(
            title=title,
            author=author,
            description="",
            language="en",
            created=today,
        )

        return Book(
            root_path=root,
            metadata=metadata,
            chapters=[],
        )

    def add_chapter(self, book: Book, title: str, draft: bool = False) -> Chapter:
        """Add a new chapter to an existing book.

        Creates the chapter file with appropriate frontmatter
        and updates the book's table of contents.

        Args:
            book: The Book to add the chapter to.
            title: The title for the new chapter.
            draft: If True, mark the chapter as a draft.

        Returns:
            The newly created Chapter object.

        Raises:
            PermissionError: If unable to create the chapter file.
        """
        chapters_dir = book.root_path / "chapters"

        # Ensure chapters directory exists
        if not self._file_repo.exists(chapters_dir):
            self._file_repo.mkdir(chapters_dir, parents=True, exist_ok=True)

        # Calculate next chapter number
        chapter_num = self._get_next_chapter_number(chapters_dir)

        # Create filename from title
        slug = _slugify(title)
        filename = f"{chapter_num:02d}-{slug}.md"
        chapter_path = chapters_dir / filename

        # Create frontmatter
        today = date.today()
        frontmatter = {
            "title": title,
            "chapter": chapter_num,
            "date": today.isoformat(),
        }
        if draft:
            frontmatter["draft"] = True

        # Build chapter content with frontmatter
        frontmatter_lines = ["---"]
        frontmatter_lines.append(f"title: {title}")
        frontmatter_lines.append(f"chapter: {chapter_num}")
        frontmatter_lines.append(f"date: {today.isoformat()}")
        if draft:
            frontmatter_lines.append("draft: true")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        frontmatter_lines.append(f"# {title}")
        frontmatter_lines.append("")

        content = "\n".join(frontmatter_lines)
        self._file_repo.write_file(chapter_path, content)

        # Create Chapter object
        chapter_metadata = ChapterMetadata(
            title=title,
            number=chapter_num,
            date=today,
            draft=draft,
        )
        chapter = Chapter(
            file_path=chapter_path,
            metadata=chapter_metadata,
            is_intro=False,
        )

        # Add to book's chapter list
        book.chapters.append(chapter)

        # Update table of contents
        self.update_toc(book)

        return chapter

    def update_toc(self, book: Book, preserve_structure: bool = True) -> None:
        """Update the book's table of contents.

        When preserve_structure=True (default), preserves existing hierarchy
        in SUMMARY.md (Part headers, nesting levels) and only adds new files.
        When preserve_structure=False, regenerates flat structure.

        Args:
            book: The Book whose TOC should be updated.
            preserve_structure: If True, preserve existing SUMMARY.md hierarchy
                and only add new files. If False, generate flat structure.

        Raises:
            PermissionError: If unable to write the TOC file.
        """
        chapters_dir = book.root_path / "chapters"
        summary_path = book.root_path / "SUMMARY.md"

        # If we have no chapters in the book object, scan the directory
        if not book.chapters and self._file_repo.exists(chapters_dir):
            from ..domain import FormatType

            book.chapters = self._structure_service.parse_structure(
                book.root_path, FormatType.GITBOOK
            )

        # If preserve_structure and SUMMARY.md exists, merge new files into existing
        if preserve_structure and self._file_repo.exists(summary_path):
            summary_content = self._merge_new_chapters_into_toc(book, summary_path)
        else:
            summary_content = self._generate_flat_toc(book)

        self._file_repo.write_file(summary_path, summary_content)

    def _parse_existing_toc(self, summary_path: Path) -> tuple[list[str], set[str]]:
        """Parse existing SUMMARY.md and extract structure and file paths.

        Args:
            summary_path: Path to the SUMMARY.md file.

        Returns:
            Tuple of (lines as list, set of relative file paths already in TOC).
        """
        content = self._file_repo.read_file(summary_path)
        lines = content.split("\n")

        # Extract all file paths from existing TOC
        existing_paths: set[str] = set()
        link_pattern = re.compile(r"\[.*?\]\(([^)]+)\)")

        for line in lines:
            match = link_pattern.search(line)
            if match:
                path = match.group(1)
                existing_paths.add(path)

        return lines, existing_paths

    def _merge_new_chapters_into_toc(self, book: Book, summary_path: Path) -> str:
        """Merge new chapters into existing SUMMARY.md preserving structure.

        Only adds chapters that are not already present in the TOC.

        Args:
            book: The Book with chapters to check.
            summary_path: Path to the existing SUMMARY.md.

        Returns:
            The updated SUMMARY.md content.
        """
        lines, existing_paths = self._parse_existing_toc(summary_path)

        # Find chapters that are not in the existing TOC
        new_chapters = []
        for chapter in book.chapters:
            try:
                rel_path = str(chapter.file_path.relative_to(book.root_path))
            except ValueError:
                rel_path = str(Path("chapters") / chapter.file_path.name)

            if rel_path not in existing_paths:
                new_chapters.append((chapter, rel_path))

        # If no new chapters, return existing content unchanged
        if not new_chapters:
            return "\n".join(lines)

        # Sort new chapters by number
        new_chapters.sort(key=lambda x: (0 if x[0].is_intro else 1, x[0].number or 0))

        # Append new chapters at the end, before any trailing empty lines
        # Find the position to insert (before trailing empty lines)
        insert_pos = len(lines)
        while insert_pos > 0 and lines[insert_pos - 1].strip() == "":
            insert_pos -= 1

        new_lines = []
        for chapter, rel_path in new_chapters:
            prefix = "- " if not chapter.metadata.draft else "- [DRAFT] "
            new_lines.append(f"{prefix}[{chapter.title}]({rel_path})")

        # Insert new chapters
        result_lines = lines[:insert_pos] + new_lines + [""]

        return "\n".join(result_lines)

    def _generate_flat_toc(self, book: Book) -> str:
        """Generate a flat SUMMARY.md structure.

        Args:
            book: The Book with chapters.

        Returns:
            The SUMMARY.md content as a string.
        """
        summary_lines = [f"# {book.metadata.title}", ""]

        # Sort chapters by number
        sorted_chapters = sorted(
            book.chapters,
            key=lambda c: (0 if c.is_intro else 1, c.number or 0),
        )

        for chapter in sorted_chapters:
            try:
                rel_path = chapter.file_path.relative_to(book.root_path)
            except ValueError:
                rel_path = Path("chapters") / chapter.file_path.name

            prefix = "- " if not chapter.metadata.draft else "- [DRAFT] "
            summary_lines.append(f"{prefix}[{chapter.title}]({rel_path})")

        summary_lines.append("")  # Trailing newline
        return "\n".join(summary_lines)

    def _get_next_chapter_number(self, chapters_dir: Path) -> int:
        """Find the next available chapter number.

        Args:
            chapters_dir: Path to the chapters directory.

        Returns:
            The next sequential chapter number.
        """
        if not self._file_repo.exists(chapters_dir):
            return 1

        max_num = 0
        try:
            files = self._file_repo.list_files(chapters_dir, "*.md")
            for file_path in files:
                match = re.match(r"^(\d+)", file_path.stem)
                if match:
                    max_num = max(max_num, int(match.group(1)))
        except Exception:
            # If listing fails, start at 1
            pass

        return max_num + 1
