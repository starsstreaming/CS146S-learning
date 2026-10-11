"""One-shot campus SSO. Run from a terminal, never from a tool call.

Flow the browser already follows:
1. jwglnew.hunnu.edu.cn/eams/homeExt.action
2. wengine gateway 302
3. oauth2.hunnu.edu.cn/authorize (authorization code)
4. login.hunnu.edu.cn
5. back to EAMS with a JSESSIONID

We cannot register a localhost redirect_uri on the school client, so
this command drives a real browser, waits until homeExt.action stays
put, and writes cookies to the session file.
"""

from __future__ import annotations

from hunnu_mcp.config import LOGIN_WAIT_S, home_url, profile_dir
from hunnu_mcp.session import save_cookies


def run_login() -> str:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    target = home_url()
    profile = profile_dir()
    profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(target, wait_until="domcontentloaded")
        try:
            page.wait_for_url("**/eams/homeExt.action", timeout=LOGIN_WAIT_S * 1000)
            page.wait_for_timeout(1500)
        except PlaywrightTimeout as exc:
            context.close()
            raise SystemExit(
                f"Timed out waiting for {target}. "
                "Finish school SSO in the opened window and run this command again."
            ) from exc
        if "login.hunnu.edu.cn" in page.url or "wengine-auth" in page.url:
            context.close()
            raise SystemExit("Still on the SSO page. Log in fully, then rerun login.")
        cookies = context.cookies()
        context.close()
    path = save_cookies(cookies)
    return str(path)


def main() -> None:
    print("Opening a browser for school SSO. Log in as yourself.")
    print(f"Waiting until the tab stays on {home_url()}")
    saved = run_login()
    print(f"Session saved to {saved}")
    print("Start the MCP server with: poetry run python -m hunnu_mcp")


if __name__ == "__main__":
    main()
