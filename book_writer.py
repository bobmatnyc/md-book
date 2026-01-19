#!/usr/bin/env python3
"""
Markdown Book Writer CLI
========================

A simple CLI tool for creating and managing markdown books.
Supports mdBook/GitBook-style SUMMARY.md structure.

Commands:
    init        - Create a new book structure
    new-chapter - Add a new chapter with frontmatter
    toc         - Regenerate SUMMARY.md from chapters
"""

import os
import re
import click
import yaml

from version import __version__, get_version
from pathlib import Path
from datetime import date
from typing import Optional, List, Dict


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def get_next_chapter_number(chapters_dir: Path) -> int:
    """Find the next available chapter number."""
    if not chapters_dir.exists():
        return 1

    max_num = 0
    for item in chapters_dir.iterdir():
        if item.is_file() and item.suffix == '.md':
            match = re.match(r'^(\d+)', item.stem)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content

    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = content[match.end():]
    return frontmatter, body


def extract_title_from_content(content: str) -> Optional[str]:
    """Extract title from first H1 heading."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


def scan_chapters(chapters_dir: Path) -> List[Dict]:
    """Scan chapters directory and extract metadata."""
    chapters = []

    if not chapters_dir.exists():
        return chapters

    for item in sorted(chapters_dir.iterdir()):
        if not item.is_file() or item.suffix != '.md':
            continue

        content = item.read_text(encoding='utf-8')
        frontmatter, body = parse_frontmatter(content)

        # Get chapter number from filename
        match = re.match(r'^(\d+)', item.stem)
        chapter_num = int(match.group(1)) if match else 0

        # Get title from frontmatter or content
        title = frontmatter.get('title') or extract_title_from_content(body) or item.stem

        chapters.append({
            'number': chapter_num,
            'title': title,
            'file': item.name,
            'path': item,
            'frontmatter': frontmatter,
            'draft': frontmatter.get('draft', False),
        })

    return sorted(chapters, key=lambda c: c['number'])


def generate_summary(book_root: Path, book_config: Dict, chapters: List[Dict]) -> str:
    """Generate SUMMARY.md content."""
    lines = [f"# {book_config.get('title', 'Summary')}", ""]

    for ch in chapters:
        prefix = "- " if not ch['draft'] else "- [DRAFT] "
        lines.append(f"{prefix}[{ch['title']}](chapters/{ch['file']})")

    return "\n".join(lines) + "\n"


@click.group()
@click.version_option(version=get_version(), prog_name='md-book-writer')
def cli():
    """Markdown Book Writer - Create and manage markdown books."""
    pass


@cli.command()
@click.option('--title', '-t', prompt='Book title', help='Title of the book')
@click.option('--author', '-a', prompt='Author', help='Author name')
@click.option('--path', '-p', default='.', help='Path where to create the book')
def init(title: str, author: str, path: str):
    """Create a new book structure."""
    book_root = Path(path).resolve()

    # Create directories
    chapters_dir = book_root / 'chapters'
    chapters_dir.mkdir(parents=True, exist_ok=True)

    # Create book.yaml
    book_config = {
        'title': title,
        'author': author,
        'description': '',
        'language': 'en',
        'created': date.today().isoformat(),
    }

    book_yaml_path = book_root / 'book.yaml'
    with open(book_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(book_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"Created: {book_yaml_path}")

    # Create SUMMARY.md
    summary_path = book_root / 'SUMMARY.md'
    summary_content = f"# {title}\n\n"
    summary_path.write_text(summary_content, encoding='utf-8')

    click.echo(f"Created: {summary_path}")
    click.echo(f"Created: {chapters_dir}")
    click.echo(f"\nBook initialized at {book_root}")
    click.echo("Use 'md-book-writer new-chapter' to add chapters.")


@cli.command('new-chapter')
@click.option('--title', '-t', prompt='Chapter title', help='Title of the chapter')
@click.option('--draft', '-d', is_flag=True, help='Mark as draft')
@click.option('--path', '-p', default='.', help='Path to book root')
def new_chapter(title: str, draft: bool, path: str):
    """Add a new chapter with frontmatter."""
    book_root = Path(path).resolve()
    chapters_dir = book_root / 'chapters'

    if not chapters_dir.exists():
        click.echo("Error: chapters/ directory not found. Run 'init' first.", err=True)
        raise SystemExit(1)

    # Get next chapter number
    chapter_num = get_next_chapter_number(chapters_dir)

    # Create filename
    slug = slugify(title)
    filename = f"{chapter_num:02d}-{slug}.md"
    chapter_path = chapters_dir / filename

    # Create frontmatter
    frontmatter = {
        'title': title,
        'chapter': chapter_num,
        'date': date.today().isoformat(),
    }
    if draft:
        frontmatter['draft'] = True

    # Create chapter content
    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    content = f"---\n{frontmatter_yaml}---\n\n# {title}\n\n"

    chapter_path.write_text(content, encoding='utf-8')
    click.echo(f"Created: {chapter_path}")

    # Update SUMMARY.md
    book_yaml_path = book_root / 'book.yaml'
    if book_yaml_path.exists():
        with open(book_yaml_path, 'r', encoding='utf-8') as f:
            book_config = yaml.safe_load(f) or {}
    else:
        book_config = {'title': 'Summary'}

    chapters = scan_chapters(chapters_dir)
    summary_content = generate_summary(book_root, book_config, chapters)

    summary_path = book_root / 'SUMMARY.md'
    summary_path.write_text(summary_content, encoding='utf-8')
    click.echo(f"Updated: {summary_path}")


@cli.command()
@click.option('--path', '-p', default='.', help='Path to book root')
def toc(path: str):
    """Regenerate SUMMARY.md from chapters."""
    book_root = Path(path).resolve()
    chapters_dir = book_root / 'chapters'

    if not chapters_dir.exists():
        click.echo("Error: chapters/ directory not found.", err=True)
        raise SystemExit(1)

    # Load book config
    book_yaml_path = book_root / 'book.yaml'
    if book_yaml_path.exists():
        with open(book_yaml_path, 'r', encoding='utf-8') as f:
            book_config = yaml.safe_load(f) or {}
    else:
        book_config = {'title': 'Summary'}

    # Scan chapters
    chapters = scan_chapters(chapters_dir)

    if not chapters:
        click.echo("No chapters found in chapters/ directory.")
        return

    # Generate and write SUMMARY.md
    summary_content = generate_summary(book_root, book_config, chapters)

    summary_path = book_root / 'SUMMARY.md'
    summary_path.write_text(summary_content, encoding='utf-8')

    click.echo(f"Regenerated: {summary_path}")
    click.echo(f"Found {len(chapters)} chapter(s):")
    for ch in chapters:
        draft_marker = " [DRAFT]" if ch['draft'] else ""
        click.echo(f"  {ch['number']:2d}. {ch['title']}{draft_marker}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
