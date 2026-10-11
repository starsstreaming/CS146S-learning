"""HTTP client that attaches the cached EAMS session.

A 200 on an HTML .action page is not success by itself: the wengine
gateway and school SSO both 302 to login HTML. Probe by final URL and
page markers, never by status code alone.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from hunnu_mcp.config import HOME_PATH, REQUEST_TIMEOUT_S, base_url
from hunnu_mcp.session import Cookie

_LOGIN_URL_MARKERS = (
    "login.hunnu.edu.cn",
    "oauth2.hunnu.edu.cn",
    "wengine-auth",
    "Login?",
)
_HOME_MARKERS = (
    "本科教学管理平台",
    "homeExt.action",
)


@dataclass(frozen=True)
class ProbeResult:
    logged_in: bool
    final_url: str
    status_code: int


def cookies_to_httpx(cookies: list[Cookie]) -> httpx.Cookies:
    jar = httpx.Cookies()
    for item in cookies:
        name = item.get("name")
        value = item.get("value")
        if not name or value is None:
            continue
        domain = (item.get("domain") or "").lstrip(".")
        path = item.get("path") or "/"
        try:
            jar.set(name, str(value), domain=domain or None, path=path)
        except Exception:
            jar.set(name, str(value))
    return jar


def looks_like_login(final_url: str, body: str) -> bool:
    lowered = final_url.lower()
    if any(marker.lower() in lowered for marker in _LOGIN_URL_MARKERS):
        return True
    if "统一身份" in body or "wengine-auth" in body:
        return True
    return False


def looks_like_home(final_url: str, body: str) -> bool:
    if HOME_PATH in final_url and any(marker in body for marker in _HOME_MARKERS):
        return True
    return "您好" in body and "教学周" in body


class HunnuClient:
    def __init__(
        self,
        cookies: list[Cookie],
        *,
        origin: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        kwargs: dict = {
            "base_url": origin or base_url(),
            "cookies": cookies_to_httpx(cookies),
            "timeout": REQUEST_TIMEOUT_S,
            "follow_redirects": True,
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/154.0.0.0 Safari/537.36 Edg/154.0.0.0"
                )
            },
        }
        if transport is not None:
            kwargs["transport"] = transport
        self._client = httpx.Client(**kwargs)

    def close(self) -> None:
        self._client.close()

    def probe_home(self) -> ProbeResult:
        """GET /eams/homeExt.action and decide if the session still works."""
        response = self._client.get(HOME_PATH)
        body = response.text
        final_url = str(response.url)
        if looks_like_login(final_url, body):
            return ProbeResult(False, final_url, response.status_code)
        if looks_like_home(final_url, body):
            return ProbeResult(True, final_url, response.status_code)
        return ProbeResult(False, final_url, response.status_code)
