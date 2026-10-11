"""On-disk EAMS cookie jar.

This file is the stand-in for an OAuth refresh token. The school login
hands us a browser session (JSESSIONID plus wengine tickets), not a
Bearer token we can refresh at a token endpoint. Tools must load this
file; they must not start a browser to replace it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hunnu_mcp.config import session_path

# Playwright-style cookie dicts: name, value, domain, path, ...
Cookie = dict[str, Any]


def load_cookies() -> list[Cookie] | None:
    """Return cookies or None if the cache is absent or corrupt."""
    path = session_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    cookies = raw.get("cookies")
    if not isinstance(cookies, list) or not cookies:
        return None
    return cookies


def save_cookies(cookies: list[Cookie]) -> Path:
    """Write cookies with 0o600 on POSIX. Windows ACL is left as the user profile default."""
    path = session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "cookies": cookies,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def clear_session() -> None:
    path = session_path()
    if path.is_file():
        path.unlink()
