#!/usr/bin/env python3
"""
Chapter Segmenter

Segments chapters into individual markdown files and reassembles them.

Convention:
    segments/
    ├── ch01-title/
    │   ├── _meta.yaml
    │   ├── 01-opening.md
    │   ├── 02-section.md
    │   └── ...
"""

import re
import shutil
from pathlib import Path
from typing import Optional

import yaml


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def parse_chapter_into_segments(content: str) -> list[dict]:
    """
    Parse chapter content into segments.

    Segments are split on:
    - Horizontal rules (---) that separate major sections
    - ## Headers that mark new sections
    """
    segments = []
    current_segment = {"title": "", "content": [], "type": "prose"}

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for chapter title (# Chapter...)
        if line.startswith("# "):
            if current_segment["content"]:
                segments.append(current_segment)
            current_segment = {"title": line[2:].strip(), "content": [line], "type": "chapter-title"}
            i += 1
            continue

        # Check for section header (## ...)
        if line.startswith("## "):
            if current_segment["content"]:
                segments.append(current_segment)
            current_segment = {"title": line[3:].strip(), "content": [line], "type": "section"}
            i += 1
            continue

        # Check for horizontal rule (segment break)
        if line.strip() == "---":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1

            if j < len(lines) and lines[j].startswith("## "):
                current_segment["content"].append(line)
                i += 1
                continue

            if current_segment["content"]:
                segments.append(current_segment)

            current_segment = {"title": "", "content": [], "type": "prose"}
            i += 1
            continue

        current_segment["content"].append(line)
        i += 1

    if current_segment["content"]:
        segments.append(current_segment)

    # Post-process
    processed = []
    for idx, seg in enumerate(segments):
        content = "\n".join(seg["content"]).strip()

        if not content:
            continue

        title = seg["title"]
        if not title:
            for line in seg["content"]:
                line = line.strip()
                if line and not line.startswith("#") and line != "---":
                    title = line[:50].strip()
                    if len(line) > 50:
                        title += "..."
                    break
            if not title:
                title = f"Section {idx + 1}"

        processed.append(
            {"title": title, "content": content, "type": seg["type"], "index": len(processed) + 1}
        )

    return processed


def create_segment_slug(title: str, index: int) -> str:
    """Create a filename slug for a segment."""
    clean_title = re.sub(r"^(Chapter \d+:?\s*)", "", title)
    clean_title = re.sub(r"[\"']", "", clean_title)

    if clean_title:
        slug = slugify(clean_title)[:40]
    else:
        slug = "section"

    return f"{index:02d}-{slug}"


def segment_chapter(
    chapter_file: Path, chapter_num: int, chapter_title: str, segments_dir: Path
) -> dict:
    """Segment a single chapter into individual files."""
    if not chapter_file.exists():
        return None

    content = chapter_file.read_text(encoding="utf-8")
    segments = parse_chapter_into_segments(content)

    # Create chapter directory
    chapter_slug = f"ch{chapter_num:02d}-{slugify(chapter_title)}"
    chapter_dir = segments_dir / chapter_slug
    chapter_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "chapter": chapter_num,
        "title": chapter_title,
        "source_file": chapter_file.name,
        "segments": [],
    }

    for seg in segments:
        seg_slug = create_segment_slug(seg["title"], seg["index"])
        seg_file = f"{seg_slug}.md"
        seg_path = chapter_dir / seg_file

        seg_path.write_text(seg["content"], encoding="utf-8")

        meta["segments"].append(
            {"file": seg_file, "title": seg["title"], "type": seg["type"], "index": seg["index"]}
        )

    meta_path = chapter_dir / "_meta.yaml"
    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return meta


def detect_chapters(chapters_dir: Path) -> list[dict]:
    """Auto-detect chapter files and extract metadata."""
    chapters = []

    # Look for chapter-*.md or ch*.md patterns
    patterns = ["chapter-*.md", "ch*.md", "*.md"]

    files = []
    for pattern in patterns:
        files.extend(chapters_dir.glob(pattern))

    for filepath in sorted(set(files)):
        # Try to extract chapter number from filename
        match = re.search(r"(?:chapter-?|ch)(\d+)", filepath.stem, re.IGNORECASE)
        if match:
            ch_num = int(match.group(1))

            # Try to extract title from file content
            content = filepath.read_text(encoding="utf-8")
            title_match = re.search(r"^#\s*(?:Chapter\s+\d+[:\s]*)?(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else filepath.stem

            chapters.append({"num": ch_num, "title": title, "file": filepath})

    return sorted(chapters, key=lambda x: x["num"])


def segment_book(book_dir: Path, force: bool = False) -> dict:
    """Segment all chapters in a book directory."""
    chapters_dir = book_dir / "chapters"
    segments_dir = book_dir / "segments"

    if not chapters_dir.exists():
        raise FileNotFoundError(f"Chapters directory not found: {chapters_dir}")

    # Clean existing segments if force
    if force and segments_dir.exists():
        for item in segments_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)

    segments_dir.mkdir(parents=True, exist_ok=True)

    # Detect chapters
    chapters = detect_chapters(chapters_dir)

    results = []
    total_segments = 0

    for ch in chapters:
        meta = segment_chapter(ch["file"], ch["num"], ch["title"], segments_dir)
        if meta:
            meta["dir"] = f"ch{ch['num']:02d}-{slugify(ch['title'])}"
            results.append(meta)
            total_segments += len(meta["segments"])

    # Write master index
    index_path = segments_dir / "_index.yaml"
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump({"chapters": results}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return {
        "chapters": len(results),
        "total_segments": total_segments,
        "segments_dir": str(segments_dir),
    }


def assemble_chapters(book_dir: Path, chapter_num: Optional[int] = None) -> dict:
    """Assemble segments back into chapter files."""
    segments_dir = book_dir / "segments"
    chapters_dir = book_dir / "chapters"

    if not segments_dir.exists():
        raise FileNotFoundError(f"Segments directory not found: {segments_dir}")

    chapters_assembled = 0

    for item in sorted(segments_dir.iterdir()):
        if not item.is_dir() or item.name.startswith("_"):
            continue

        # Extract chapter number from directory name
        match = re.match(r"ch(\d+)-", item.name)
        if not match:
            continue

        ch_num = int(match.group(1))

        # Skip if specific chapter requested and this isn't it
        if chapter_num is not None and ch_num != chapter_num:
            continue

        meta_path = item / "_meta.yaml"
        if not meta_path.exists():
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

        # Assemble content
        parts = []
        for seg in meta.get("segments", []):
            seg_path = item / seg["file"]
            if seg_path.exists():
                parts.append(seg_path.read_text(encoding="utf-8"))

        assembled = "\n\n---\n\n".join(parts)

        # Write to source file
        source_file = meta.get("source_file")
        if source_file:
            dest_path = chapters_dir / source_file
            dest_path.write_text(assembled, encoding="utf-8")
            chapters_assembled += 1

    return {"chapters_assembled": chapters_assembled}
