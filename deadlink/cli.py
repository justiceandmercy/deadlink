"""Command-line entry point."""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import __version__
from .checker import check_link
from .scanner import extract_links, find_markdown_files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="deadlink", description="Find broken links in Markdown.")
    parser.add_argument("path", nargs="?", default=".", help="file or directory to scan")
    parser.add_argument("--timeout", type=float, default=8.0, help="HTTP timeout seconds (default 8)")
    parser.add_argument("--workers", type=int, default=8, help="concurrent workers (default 8)")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--fail", action="store_true", help="exit non-zero if broken links found")
    parser.add_argument("--include", default=None, help="glob of files to include (default *.md)")
    args = parser.parse_args(argv)

    files = find_markdown_files(args.path)
    if args.include:
        import fnmatch
        files = [f for f in files if fnmatch.fnmatch(f.name, args.include)]

    tasks = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, url in extract_links(text):
            tasks.append((f, line_no, url))

    results = []
    broken_count = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        future_map = {
            ex.submit(check_link, f, url, args.timeout): (f, line_no, url)
            for (f, line_no, url) in tasks
        }
        for fut in as_completed(future_map):
            f, line_no, url = future_map[fut]
            ok, reason = fut.result()
            entry = {
                "file": str(f),
                "line": line_no,
                "url": url,
                "ok": ok,
                "reason": reason,
            }
            results.append(entry)
            if not ok:
                broken_count += 1

    # stable ordering
    results.sort(key=lambda r: (r["file"], r["line"], r["url"]))

    if args.json:
        print(json.dumps({"broken": broken_count, "total": len(results), "results": results}, indent=2))
    else:
        for r in results:
            if r["ok"]:
                continue
            print(f"{r['file']}:{r['line']}  BROKEN  {r['url']}  ({r['reason']})")
        print(f"\n{broken_count} broken / {len(results)} checked", file=sys.stderr)

    if args.fail and broken_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())