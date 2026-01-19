#!/usr/bin/env python3
"""
Writer-Reader Server

Flask API for:
- Reading/writing segment files
- Git operations (status, diff, commit, push)
- Chapter assembly
"""

import subprocess
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


def create_app(book_dir: Path = None):
    """Create and configure the Flask application."""
    book_dir = book_dir or Path.cwd()
    segments_dir = book_dir / "segments"

    app = Flask(__name__, static_folder=str(book_dir), static_url_path="")
    CORS(app)

    # Store config on app
    app.config["BOOK_DIR"] = book_dir
    app.config["SEGMENTS_DIR"] = segments_dir

    def run_git(args: list, cwd: Path = None) -> tuple[bool, str]:
        """Run a git command and return (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or book_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, str(e)

    @app.route("/")
    def index():
        """Serve the editor HTML."""
        # Look for editor in package or book directory
        editor_locations = [
            book_dir / "BOOK_EDITOR.html",
            Path(__file__).parent / "static" / "editor.html",
        ]
        for loc in editor_locations:
            if loc.exists():
                return send_from_directory(loc.parent, loc.name)
        return "Editor HTML not found", 404

    @app.route("/api/info")
    def get_info():
        """Get project info."""
        from . import __version__

        return jsonify(
            {
                "version": __version__,
                "book_dir": str(book_dir),
                "segments_dir": str(segments_dir),
            }
        )

    @app.route("/api/index")
    def get_index():
        """Get the master index of all chapters and segments."""
        index_path = segments_dir / "_index.yaml"
        if not index_path.exists():
            return jsonify({"error": "Index not found. Run 'writer-reader segment' first."}), 404

        with open(index_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return jsonify(data)

    @app.route("/api/chapter/<int:chapter_num>")
    def get_chapter(chapter_num: int):
        """Get metadata for a specific chapter."""
        for item in segments_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"ch{chapter_num:02d}-"):
                meta_path = item / "_meta.yaml"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    data["dir"] = item.name
                    return jsonify(data)

        return jsonify({"error": f"Chapter {chapter_num} not found"}), 404

    @app.route("/api/segment/<path:segment_path>")
    def get_segment(segment_path: str):
        """Get content of a specific segment."""
        filepath = segments_dir / segment_path
        if not filepath.exists():
            return jsonify({"error": "Segment not found"}), 404

        content = filepath.read_text(encoding="utf-8")
        return jsonify(
            {"path": segment_path, "content": content, "modified": filepath.stat().st_mtime}
        )

    @app.route("/api/segment/<path:segment_path>", methods=["PUT"])
    def save_segment(segment_path: str):
        """Save content to a segment file."""
        filepath = segments_dir / segment_path
        if not filepath.parent.exists():
            return jsonify({"error": "Chapter directory not found"}), 404

        data = request.get_json()
        content = data.get("content", "")

        filepath.write_text(content, encoding="utf-8")

        return jsonify(
            {"success": True, "path": segment_path, "modified": filepath.stat().st_mtime}
        )

    @app.route("/api/git/status")
    def git_status():
        """Get git status for the book directory."""
        success, output = run_git(["status", "--porcelain"])
        if not success:
            return jsonify({"error": output}), 500

        files = []
        for line in output.split("\n"):
            if line.strip():
                status = line[:2]
                path = line[3:]
                files.append({"status": status.strip(), "path": path})

        return jsonify({"clean": len(files) == 0, "files": files})

    @app.route("/api/git/diff")
    def git_diff():
        """Get git diff for modified files."""
        path = request.args.get("path", "")

        if path:
            success, output = run_git(["diff", "--", path])
        else:
            success, output = run_git(["diff"])

        if not success:
            return jsonify({"error": output}), 500

        return jsonify({"diff": output})

    @app.route("/api/git/diff-staged")
    def git_diff_staged():
        """Get staged diff."""
        success, output = run_git(["diff", "--staged"])
        return jsonify({"diff": output})

    @app.route("/api/git/add", methods=["POST"])
    def git_add():
        """Stage files for commit."""
        data = request.get_json()
        paths = data.get("paths", [])

        if not paths:
            success, output = run_git(["add", "-A"])
        else:
            success, output = run_git(["add"] + paths)

        if not success:
            return jsonify({"error": output}), 500

        return jsonify({"success": True, "output": output})

    @app.route("/api/git/commit", methods=["POST"])
    def git_commit():
        """Commit staged changes."""
        data = request.get_json()
        message = data.get("message", "Update book content")

        success, output = run_git(["commit", "-m", message])

        if not success:
            return jsonify({"error": output}), 500

        return jsonify({"success": True, "output": output})

    @app.route("/api/git/push", methods=["POST"])
    def git_push():
        """Push to remote."""
        success, output = run_git(["push"])

        if not success:
            return jsonify({"error": output}), 500

        return jsonify({"success": True, "output": output})

    @app.route("/api/git/log")
    def git_log():
        """Get recent commit log."""
        limit = request.args.get("limit", "10")
        success, output = run_git(["log", f"-{limit}", "--oneline"])

        if not success:
            return jsonify({"error": output}), 500

        commits = []
        for line in output.split("\n"):
            if line.strip():
                parts = line.split(" ", 1)
                commits.append({"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""})

        return jsonify({"commits": commits})

    @app.route("/api/assemble/<int:chapter_num>")
    def assemble_chapter(chapter_num: int):
        """Assemble segments back into a single chapter file."""
        chapter_dir = None
        for item in segments_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"ch{chapter_num:02d}-"):
                chapter_dir = item
                break

        if not chapter_dir:
            return jsonify({"error": f"Chapter {chapter_num} not found"}), 404

        meta_path = chapter_dir / "_meta.yaml"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

        parts = []
        for seg in meta.get("segments", []):
            seg_path = chapter_dir / seg["file"]
            if seg_path.exists():
                content = seg_path.read_text(encoding="utf-8")
                parts.append(content)

        assembled = "\n\n---\n\n".join(parts)

        return jsonify(
            {
                "chapter": chapter_num,
                "title": meta.get("title"),
                "content": assembled,
                "segment_count": len(parts),
            }
        )

    @app.route("/api/assemble/<int:chapter_num>", methods=["POST"])
    def save_assembled_chapter(chapter_num: int):
        """Save assembled chapter back to chapters directory."""
        result = assemble_chapter(chapter_num)
        data = result.get_json()

        if "error" in data:
            return result

        chapters_dir = book_dir / "chapters"
        meta_path = None
        for item in segments_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"ch{chapter_num:02d}-"):
                meta_path = item / "_meta.yaml"
                break

        if not meta_path or not meta_path.exists():
            return jsonify({"error": "Metadata not found"}), 404

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

        source_file = meta.get("source_file")
        if source_file:
            dest_path = chapters_dir / source_file
            dest_path.write_text(data["content"], encoding="utf-8")
            return jsonify(
                {"success": True, "path": str(dest_path), "message": f"Saved to {source_file}"}
            )

        return jsonify({"error": "Source file not configured"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=5555, debug=True)
