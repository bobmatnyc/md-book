"""Tests for update_toc preserve_structure functionality.

Tests the ability to preserve existing SUMMARY.md hierarchy when
adding new chapters vs regenerating flat structure.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from mdbook.domain import Book, BookMetadata, Chapter, ChapterMetadata
from mdbook.services.writer_service import WriterService


@pytest.fixture
def mock_file_repo():
    """Create a mock file repository."""
    repo = Mock()
    repo.exists.return_value = True
    return repo


@pytest.fixture
def mock_config_repo():
    """Create a mock config repository."""
    return Mock()


@pytest.fixture
def mock_structure_service():
    """Create a mock structure service."""
    return Mock()


@pytest.fixture
def writer_service(mock_file_repo, mock_config_repo, mock_structure_service):
    """Create a WriterService with mock dependencies."""
    return WriterService(mock_file_repo, mock_config_repo, mock_structure_service)


@pytest.fixture
def sample_book(tmp_path) -> Book:
    """Create a sample book for testing."""
    metadata = BookMetadata(
        title="Test Book",
        author="Test Author",
        description="",
        language="en",
        created=date.today(),
    )
    return Book(root_path=tmp_path, metadata=metadata, chapters=[])


@pytest.fixture
def sample_chapters(tmp_path) -> list[Chapter]:
    """Create sample chapters."""
    return [
        Chapter(
            file_path=tmp_path / "chapters" / "01-introduction.md",
            metadata=ChapterMetadata(
                title="Introduction",
                number=1,
                date=date.today(),
                draft=False,
            ),
            is_intro=False,
        ),
        Chapter(
            file_path=tmp_path / "chapters" / "02-getting-started.md",
            metadata=ChapterMetadata(
                title="Getting Started",
                number=2,
                date=date.today(),
                draft=False,
            ),
            is_intro=False,
        ),
    ]


class TestPreserveStructure:
    """Tests for preserve_structure=True behavior."""

    def test_preserves_existing_hierarchy_with_parts(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that Part headers and nesting are preserved."""
        # Existing hierarchical SUMMARY.md
        existing_summary = """# Test Book

## Part I: Basics

- [Introduction](chapters/01-introduction.md)
  - [Sub-section](chapters/01a-subsection.md)

## Part II: Advanced

- [Advanced Topics](chapters/10-advanced.md)
"""
        mock_file_repo.read_file.return_value = existing_summary
        mock_file_repo.exists.return_value = True

        # Book has all chapters including a new one
        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-introduction.md",
                metadata=ChapterMetadata(title="Introduction", number=1),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "02-new-chapter.md",
                metadata=ChapterMetadata(title="New Chapter", number=2),
                is_intro=False,
            ),
        ]

        writer_service.update_toc(sample_book, preserve_structure=True)

        # Verify write was called
        mock_file_repo.write_file.assert_called_once()
        written_content = mock_file_repo.write_file.call_args[0][1]

        # Should preserve Part headers
        assert "## Part I: Basics" in written_content
        assert "## Part II: Advanced" in written_content

        # Should preserve existing structure
        assert "[Introduction](chapters/01-introduction.md)" in written_content

        # Should add new chapter
        assert "[New Chapter](chapters/02-new-chapter.md)" in written_content

    def test_no_changes_when_all_chapters_exist(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that no changes are made when all chapters are already in TOC."""
        existing_summary = """# Test Book

- [Introduction](chapters/01-introduction.md)
- [Getting Started](chapters/02-getting-started.md)
"""
        mock_file_repo.read_file.return_value = existing_summary
        mock_file_repo.exists.return_value = True

        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-introduction.md",
                metadata=ChapterMetadata(title="Introduction", number=1),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "02-getting-started.md",
                metadata=ChapterMetadata(title="Getting Started", number=2),
                is_intro=False,
            ),
        ]

        writer_service.update_toc(sample_book, preserve_structure=True)

        written_content = mock_file_repo.write_file.call_args[0][1]

        # Content should be essentially unchanged (may have trailing newline diff)
        assert "- [Introduction](chapters/01-introduction.md)" in written_content
        assert "- [Getting Started](chapters/02-getting-started.md)" in written_content

    def test_preserves_nested_indentation(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that nested chapter indentation is preserved."""
        existing_summary = """# Test Book

- [Part One]()
  - [Chapter 1](chapters/01-ch1.md)
    - [Section 1.1](chapters/01a-section.md)
  - [Chapter 2](chapters/02-ch2.md)
"""
        mock_file_repo.read_file.return_value = existing_summary
        mock_file_repo.exists.return_value = True

        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-ch1.md",
                metadata=ChapterMetadata(title="Chapter 1", number=1),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "03-new.md",
                metadata=ChapterMetadata(title="New Chapter", number=3),
                is_intro=False,
            ),
        ]

        writer_service.update_toc(sample_book, preserve_structure=True)

        written_content = mock_file_repo.write_file.call_args[0][1]

        # Should preserve nested structure
        assert "  - [Chapter 1](chapters/01-ch1.md)" in written_content
        assert "    - [Section 1.1](chapters/01a-section.md)" in written_content


class TestFlatGeneration:
    """Tests for preserve_structure=False behavior."""

    def test_generates_flat_structure(
        self, writer_service, sample_book, sample_chapters, mock_file_repo
    ):
        """Test that flat structure is generated when preserve_structure=False."""
        # Even with existing hierarchical content
        existing_summary = """# Test Book

## Part I

- [Old Chapter](chapters/old.md)
"""
        mock_file_repo.read_file.return_value = existing_summary
        mock_file_repo.exists.return_value = True

        sample_book.chapters = sample_chapters

        writer_service.update_toc(sample_book, preserve_structure=False)

        written_content = mock_file_repo.write_file.call_args[0][1]

        # Should NOT preserve Part headers
        assert "## Part I" not in written_content

        # Should have flat list
        assert "- [Introduction](chapters/01-introduction.md)" in written_content
        assert "- [Getting Started](chapters/02-getting-started.md)" in written_content

    def test_flat_structure_sorts_by_chapter_number(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that flat structure sorts chapters correctly."""
        mock_file_repo.exists.return_value = False  # No existing SUMMARY.md

        # Add chapters out of order
        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "03-third.md",
                metadata=ChapterMetadata(title="Third", number=3),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-first.md",
                metadata=ChapterMetadata(title="First", number=1),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "02-second.md",
                metadata=ChapterMetadata(title="Second", number=2),
                is_intro=False,
            ),
        ]

        writer_service.update_toc(sample_book, preserve_structure=False)

        written_content = mock_file_repo.write_file.call_args[0][1]
        lines = written_content.split("\n")

        # Find chapter lines and verify order
        chapter_lines = [line for line in lines if line.startswith("- [")]
        assert len(chapter_lines) == 3
        assert "First" in chapter_lines[0]
        assert "Second" in chapter_lines[1]
        assert "Third" in chapter_lines[2]


class TestDraftHandling:
    """Tests for draft chapter handling in TOC."""

    def test_draft_chapters_marked_correctly(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that draft chapters are marked with [DRAFT] prefix."""
        mock_file_repo.exists.return_value = False

        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-published.md",
                metadata=ChapterMetadata(title="Published", number=1, draft=False),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "02-draft.md",
                metadata=ChapterMetadata(title="Draft Chapter", number=2, draft=True),
                is_intro=False,
            ),
        ]

        writer_service.update_toc(sample_book, preserve_structure=False)

        written_content = mock_file_repo.write_file.call_args[0][1]

        assert "- [Published]" in written_content
        assert "- [DRAFT] [Draft Chapter]" in written_content


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_chapters_list(self, writer_service, sample_book, mock_file_repo):
        """Test handling of book with no chapters."""
        mock_file_repo.exists.return_value = False

        sample_book.chapters = []

        writer_service.update_toc(sample_book, preserve_structure=False)

        written_content = mock_file_repo.write_file.call_args[0][1]

        # Should have title but no chapter entries
        assert "# Test Book" in written_content
        assert "- [" not in written_content

    def test_intro_chapter_sorted_first(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that intro chapters appear before numbered chapters."""
        mock_file_repo.exists.return_value = False

        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-first.md",
                metadata=ChapterMetadata(title="First", number=1),
                is_intro=False,
            ),
            Chapter(
                file_path=sample_book.root_path / "chapters" / "00-intro.md",
                metadata=ChapterMetadata(title="Introduction", number=0),
                is_intro=True,
            ),
        ]

        writer_service.update_toc(sample_book, preserve_structure=False)

        written_content = mock_file_repo.write_file.call_args[0][1]
        lines = [line for line in written_content.split("\n") if line.startswith("- [")]

        assert "Introduction" in lines[0]
        assert "First" in lines[1]

    def test_default_preserve_structure_is_true(
        self, writer_service, sample_book, mock_file_repo
    ):
        """Test that preserve_structure defaults to True."""
        existing_summary = """# Test Book

## Part I

- [Existing](chapters/01-existing.md)
"""
        mock_file_repo.read_file.return_value = existing_summary
        mock_file_repo.exists.return_value = True

        sample_book.chapters = [
            Chapter(
                file_path=sample_book.root_path / "chapters" / "01-existing.md",
                metadata=ChapterMetadata(title="Existing", number=1),
                is_intro=False,
            ),
        ]

        # Call without preserve_structure parameter
        writer_service.update_toc(sample_book)

        written_content = mock_file_repo.write_file.call_args[0][1]

        # Should preserve Part header (default preserve_structure=True)
        assert "## Part I" in written_content
