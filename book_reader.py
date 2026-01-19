#!/usr/bin/env python3
"""
Generic Markdown Book Reader
============================

A terminal-based markdown book reader supporting multiple formats:
- mdBook / GitBook (SUMMARY.md)
- Leanpub (Book.txt)
- Bookdown (_bookdown.yml)
- mdBook config (book.toml)
- Auto-detection via filename patterns
"""

import os
import sys
import click

from version import __version__, get_version
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from config import BookReaderConfig
from structure_detector import StructureDetector, BookStructure, Chapter

console = Console()


class BookReader:
    """Main book reader class that handles navigation and display."""

    def __init__(self, book_root: Path):
        """Initialize the book reader with the root directory."""
        self.book_root = Path(book_root).resolve()
        self.config = BookReaderConfig()

        # Detect book structure
        detector = StructureDetector(self.book_root)
        self.structure: BookStructure = detector.detect_structure()

        # Build chapter index
        self.chapters: Dict[int, Chapter] = {
            ch.number: ch for ch in self.structure.chapters
        }
        self.total_chapters = len([c for c in self.chapters.values() if not c.is_intro])

        # Set current chapter to first non-intro chapter, or intro if no chapters
        non_intro = [c.number for c in self.chapters.values() if not c.is_intro]
        self.current_chapter = min(non_intro) if non_intro else 0

        # Book title
        self.book_title = self._detect_book_title()

    def _detect_book_title(self) -> str:
        """Detect book title from structure or directory name."""
        if self.structure.title:
            return self.structure.title

        # Try to get from intro chapter
        if 0 in self.chapters:
            intro = self.chapters[0]
            if intro.title and intro.title.lower() not in ['introduction', 'readme', 'index']:
                return intro.title

        # Fall back to directory name
        return self.book_root.name.replace('-', ' ').replace('_', ' ').title()

    def get_chapter_content(self, chapter_num: int) -> Optional[str]:
        """Get the content of a specific chapter."""
        if chapter_num not in self.chapters:
            return None

        chapter = self.chapters[chapter_num]

        try:
            content = chapter.file_path.read_text(encoding='utf-8')

            # Strip YAML frontmatter from display
            if content.startswith('---'):
                import re
                match = re.search(r'\n---\s*\n', content[3:])
                if match:
                    content = content[3 + match.end():]

            return content
        except Exception as e:
            console.print(f"[red]Error reading chapter {chapter_num}: {e}[/red]")
            return None

    def display_chapter(self, chapter_num: int):
        """Display a specific chapter with proper formatting."""
        if chapter_num not in self.chapters:
            console.print(f"[red]Chapter {chapter_num} not found[/red]")
            return

        content = self.get_chapter_content(chapter_num)
        if not content:
            console.print(f"[red]Could not read Chapter {chapter_num}[/red]")
            return

        # Clear screen
        console.clear()

        # Display header
        chapter = self.chapters[chapter_num]
        if chapter.is_intro:
            header = "Introduction"
        else:
            header = f"Chapter {chapter_num}"

        # Show draft indicator if applicable
        draft_indicator = " [yellow](DRAFT)[/yellow]" if chapter.is_draft else ""

        subtitle_parts = []
        if chapter.author:
            subtitle_parts.append(f"Author: {chapter.author}")
        if chapter.date:
            subtitle_parts.append(f"Date: {chapter.date}")
        subtitle = " | ".join(subtitle_parts) if subtitle_parts else None

        console.print(Panel(
            f"[bold blue]{header}[/bold blue]{draft_indicator}\n[dim]{chapter.title}[/dim]"
            + (f"\n[dim italic]{subtitle}[/dim italic]" if subtitle else ""),
            title=self.book_title,
            subtitle=f"Chapter {chapter_num} of {self.total_chapters}" if not chapter.is_intro else "Introduction",
            border_style="blue"
        ))

        console.print()

        # Display content with rich markdown rendering
        try:
            md = Markdown(content, hyperlinks=True, code_theme=self.config.CODE_THEME)
            console.print(md)
        except Exception:
            # Fallback to plain text if markdown rendering fails
            console.print(content)

        console.print()

        # Display navigation help
        nav_help = "[dim]Navigation: [bold]n[/bold]=next, [bold]p[/bold]=previous, [bold]toc[/bold]=table of contents, [bold]j[/bold]=jump to chapter, [bold]q[/bold]=quit[/dim]"
        console.print(Panel(nav_help, border_style="dim"))

    def display_table_of_contents(self):
        """Display the table of contents."""
        console.clear()

        console.print(Panel(
            "[bold blue]Table of Contents[/bold blue]",
            title=self.book_title,
            border_style="blue"
        ))

        console.print()

        # Show detected format
        format_names = {
            'summary': 'mdBook/GitBook (SUMMARY.md)',
            'leanpub': 'Leanpub (Book.txt)',
            'bookdown': 'Bookdown (_bookdown.yml)',
            'mdbook': 'mdBook (book.toml)',
            'auto': 'Auto-detected'
        }
        console.print(f"[dim]Format: {format_names.get(self.structure.format_type, 'Unknown')}[/dim]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Ch", style="dim", width=4)
        table.add_column("Title", style="bold")
        table.add_column("Status", style="green", width=12)

        for chapter_num in sorted(self.chapters.keys()):
            chapter = self.chapters[chapter_num]

            if chapter.is_draft:
                status = "[yellow]Draft[/yellow]"
            elif chapter.file_path.exists():
                status = "[green]Available[/green]"
            else:
                status = "[red]Missing[/red]"

            display_num = "Intro" if chapter.is_intro else str(chapter_num)
            table.add_row(display_num, chapter.title, status)

        console.print(table)
        console.print()

        nav_help = "[dim]Enter chapter number to jump to, or press Enter to return to current chapter[/dim]"
        console.print(Panel(nav_help, border_style="dim"))

    def interactive_mode(self):
        """Start interactive reading mode."""
        console.print(Panel(
            f"[bold blue]Welcome to {self.book_title}[/bold blue]\n\n"
            f"Detected format: [cyan]{self.structure.format_type}[/cyan]\n"
            f"Total chapters: [cyan]{self.total_chapters}[/cyan]\n\n"
            "[dim]Press Enter to start reading...[/dim]",
            title="Markdown Book Reader",
            border_style="blue"
        ))

        input()  # Wait for user input

        while True:
            self.display_chapter(self.current_chapter)

            try:
                choice = Prompt.ask(
                    f"\n[bold]Chapter {self.current_chapter}[/bold] - What would you like to do?",
                    choices=["n", "p", "toc", "j", "q", "next", "previous", "quit", "jump", "table"],
                    default="n",
                    show_choices=False
                )

                if choice in ["n", "next"]:
                    self.next_chapter()
                elif choice in ["p", "previous"]:
                    self.previous_chapter()
                elif choice in ["toc", "table"]:
                    self.display_table_of_contents()
                    jump_choice = Prompt.ask("Enter chapter number (or press Enter to continue)")
                    if jump_choice.strip():
                        try:
                            target_chapter = int(jump_choice)
                            self.jump_to_chapter(target_chapter)
                        except ValueError:
                            console.print("[red]Invalid chapter number[/red]")
                elif choice in ["j", "jump"]:
                    max_ch = max(self.chapters.keys())
                    target = Prompt.ask(f"Enter chapter number (0-{max_ch})")
                    try:
                        target_chapter = int(target)
                        self.jump_to_chapter(target_chapter)
                    except ValueError:
                        console.print("[red]Invalid chapter number[/red]")
                elif choice in ["q", "quit"]:
                    console.print(f"[blue]Thank you for reading {self.book_title}![/blue]")
                    break

            except KeyboardInterrupt:
                console.print(f"\n[blue]Thank you for reading {self.book_title}![/blue]")
                break
            except EOFError:
                console.print(f"\n[blue]Thank you for reading {self.book_title}![/blue]")
                break

    def next_chapter(self):
        """Navigate to the next chapter."""
        available_chapters = sorted(self.chapters.keys())
        try:
            current_index = available_chapters.index(self.current_chapter)
        except ValueError:
            current_index = 0

        if current_index < len(available_chapters) - 1:
            self.current_chapter = available_chapters[current_index + 1]
        else:
            console.print("[yellow]You're at the last chapter[/yellow]")

    def previous_chapter(self):
        """Navigate to the previous chapter."""
        available_chapters = sorted(self.chapters.keys())
        try:
            current_index = available_chapters.index(self.current_chapter)
        except ValueError:
            current_index = 0

        if current_index > 0:
            self.current_chapter = available_chapters[current_index - 1]
        else:
            console.print("[yellow]You're at the first chapter[/yellow]")

    def jump_to_chapter(self, chapter_num: int):
        """Jump to a specific chapter."""
        if chapter_num in self.chapters:
            self.current_chapter = chapter_num
        else:
            console.print(f"[red]Chapter {chapter_num} not found[/red]")


@click.command()
@click.option('--chapter', '-c', type=int, help='Jump to specific chapter')
@click.option('--toc', is_flag=True, help='Show table of contents')
@click.option('--root', '-r', default=None,
              help='Root directory of the book (defaults to current directory)')
@click.option('--info', is_flag=True, help='Show detected book structure info and exit')
@click.version_option(version=get_version(), prog_name='md-book-reader')
def main(chapter: Optional[int], toc: bool, root: Optional[str], info: bool):
    """
    Generic Markdown Book Reader

    A terminal-based markdown book reader supporting mdBook, GitBook,
    Leanpub, Bookdown, and auto-detected formats.

    Examples:

        # Read book in current directory
        python book_reader.py

        # Read book from specific directory
        python book_reader.py --root /path/to/book

        # Jump to chapter 5
        python book_reader.py --chapter 5

        # Show table of contents
        python book_reader.py --toc

        # Show detected structure info
        python book_reader.py --info
    """

    # Determine book root
    if root is None:
        # Try current directory first
        book_root = Path.cwd()

        # If we're in the book-reader directory, try parent
        if book_root.name == 'book-reader':
            parent = book_root.parent
            if BookReaderConfig.validate_book_root(parent):
                book_root = parent
    else:
        book_root = Path(root)

    if not book_root.exists():
        console.print(f"[red]Book root directory not found: {book_root}[/red]")
        console.print("Please specify the correct path using --root option")
        sys.exit(1)

    if not BookReaderConfig.validate_book_root(book_root):
        console.print(f"[red]No markdown files found in: {book_root}[/red]")
        console.print("Please specify a directory containing markdown files using --root option")
        sys.exit(1)

    reader = BookReader(book_root)

    if not reader.chapters:
        console.print("[red]No chapters found in the specified directory[/red]")
        sys.exit(1)

    if info:
        # Display structure info and exit
        console.print(Panel(
            f"[bold]Book:[/bold] {reader.book_title}\n"
            f"[bold]Root:[/bold] {reader.book_root}\n"
            f"[bold]Format:[/bold] {reader.structure.format_type}\n"
            f"[bold]Chapters:[/bold] {reader.total_chapters}",
            title="Book Structure Info",
            border_style="blue"
        ))

        console.print("\n[bold]Chapters found:[/bold]")
        for ch_num in sorted(reader.chapters.keys()):
            ch = reader.chapters[ch_num]
            prefix = "Intro" if ch.is_intro else f"Ch {ch_num}"
            draft = " (draft)" if ch.is_draft else ""
            console.print(f"  [{prefix}] {ch.title}{draft}")
            console.print(f"       [dim]{ch.file_path}[/dim]")
        return

    if toc:
        reader.display_table_of_contents()
        return

    if chapter is not None:
        reader.jump_to_chapter(chapter)

    reader.interactive_mode()


if __name__ == "__main__":
    main()
