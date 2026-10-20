# deadlink

A small, zero-dependency CLI that scans Markdown files for broken links — both
remote (`http`/`https`) URLs and relative file paths — and reports them with
file + line numbers.

## Features

- Recursively scans a directory (or single file) for `*.md` files.
- Extracts inline links, reference-style links, and autolinks.
- Checks remote URLs with a HEAD request (falls back to GET).
- Validates relative paths against the filesystem (including `#anchor` fragments).
- Concurrent checking with a configurable worker count.
- Machine-readable JSON output (`--json`) for CI integration.
- No external services or paid APIs required.

## Install

```sh
pip install -e .
```

Or run directly:

```sh
python -m deadlink --help
```

## Usage

```sh
# Scan current directory
deadlink .

# Scan a specific folder, 10s timeout, 8 workers
deadlink docs/ --timeout 10 --workers 8

# JSON output for CI
deadlink . --json > report.json

# Fail (non-zero exit) if any broken link found
deadlink . --fail
```

Example output:

```
docs/guide.md:42  BROKEN  https://example.com/gone  (HTTP 404)
README.md:15       MISSING  ./images/logo.png
```

## License

MIT