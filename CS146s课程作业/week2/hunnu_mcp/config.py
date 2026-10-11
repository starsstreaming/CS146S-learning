"""Runtime paths and the school EAMS origin.

The school OAuth client is not ours: redirect_uri is registered on
oauth2.hunnu.edu.cn / wengine. We never store a client secret because
the university does not issue one to this project.
"""

from __future__ import annotations

import os
from pathlib import Path

HOME_PATH = "/eams/homeExt.action"
REQUEST_TIMEOUT_S = 20.0
LOGIN_WAIT_S = 300.0


def base_url() -> str:
    return os.environ.get("HUNNU_BASE_URL", "https://jwglnew.hunnu.edu.cn").rstrip("/")


def home_url() -> str:
    return f"{base_url()}{HOME_PATH}"


def session_path() -> Path:
    default = Path.home() / ".hunnu-mcp" / "session.json"
    return Path(os.environ.get("HUNNU_SESSION_PATH", str(default)))


def profile_dir() -> Path:
    default = Path.home() / ".hunnu-mcp" / "browser-profile"
    return Path(os.environ.get("HUNNU_PROFILE_DIR", str(default)))
