"""Markdown link extraction and filesystem checks."""

import os
import re
from pathlib import Path
from typing import Iterable, List, Tuple

# inline links: [text](url) and [text](url "title")
INLINE_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# reference definitions: [id]: url
REFDEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
# autolinks: <http://...>
AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
# markdown headings
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)


def find_markdown_files(root: str) -> List[Path]:
    p = Path(root)
    if p.is_file():
        return [p] if p.suffix.lower() in (".md", ".markdown") else []
    out: List[Path] = []
    for dirpath, _, filenames in os.walk(p):
        for name in filenames:
            if name.lower().endswith((".md", ".markdown")):
                out.append(Path(dirpath) / name)
    return sorted(out)


def extract_links(text: str) -> List[Tuple[int, str]]:
    """Return list of (line_number, url) for every link found."""
    results: List[Tuple[int, str]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        for m in INLINE_RE.finditer(line):
            results.append((i, m.group(1)))
        for m in AUTOLINK_RE.finditer(line):
            results.append((i, m.group(1)))
    for m in REFDEF_RE.finditer(text):
        # approximate line number
        line_no = text[: m.start()].count("\n") + 1
        results.append((line_no, m.group(1)))
    return results


def slugify(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def file_anchors(path: Path) -> set:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    return {slugify(m.group(1)) for m in HEADING_RE.finditer(text)}


def resolve_relative(base_file: Path, url: str) -> Path:
    # strip fragment and query
    clean = url.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return base_file
    if clean.startswith("/"):
        # treat as relative to cwd root? We'll resolve relative to base file's parent for safety
        return (base_file.parent / clean.lstrip("/")).resolve()
    return (base_file.parent / clean).resolve()


def is_remote(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def is_mailto_or_tel(url: str) -> bool:
    return url.startswith("mailto:") or url.startswith("tel:") or url.startswith("javascript:")