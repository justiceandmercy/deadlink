"""Link checking logic."""

import ssl
from pathlib import Path
from typing import Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # noqa: BLE001
    _SSL_CTX = ssl.create_default_context()

from .scanner import file_anchors, is_mailto_or_tel, is_remote, resolve_relative, slugify


def check_link(base_file: Path, url: str, timeout: float) -> Tuple[bool, str]:
    """Return (ok, reason)."""
    url = url.strip().strip("<>")
    if not url or url.startswith("#"):
        if url.startswith("#"):
            anchor = slugify(url[1:])
            anchors = file_anchors(base_file)
            if anchor in anchors:
                return True, "OK"
            return False, "missing anchor"
        return True, "OK"
    if is_mailto_or_tel(url):
        return True, "skipped"
    if is_remote(url):
        return check_remote(url, timeout)
    fragment = ""
    if "#" in url:
        url, fragment = url.split("#", 1)
    target = resolve_relative(base_file, url)
    if not target.exists():
        return False, "missing file"
    if fragment:
        anchors = file_anchors(target)
        if slugify(fragment) not in anchors:
            return False, "missing anchor"
    return True, "OK"


def check_remote(url: str, timeout: float) -> Tuple[bool, str]:
    for method in ("HEAD", "GET"):
        try:
            req = Request(url, method=method, headers={"User-Agent": "deadlink/0.1"})
            with urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                code = getattr(resp, "status", 200)
                if 200 <= code < 400:
                    return True, f"HTTP {code}"
                return False, f"HTTP {code}"
        except HTTPError as e:
            if method == "HEAD" and e.code in (405, 501):
                continue
            if 200 <= e.code < 400:
                return True, f"HTTP {e.code}"
            return False, f"HTTP {e.code}"
        except URLError as e:
            return False, f"network error: {e.reason}"
        except Exception as e:  # noqa: BLE001
            return False, f"error: {e}"
    return False, "no response"