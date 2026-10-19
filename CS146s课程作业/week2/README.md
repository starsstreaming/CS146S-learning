# Week 2 — Hunnu EAMS MCP

stdio MCP server for Hunan Normal University undergraduate EAMS.
Tools cover the logged-in 我的 and 公共服务 menus.
Timetable and grades: `hunnu_get_timetable`, `hunnu_get_grades`.
Each other menu item has its own read tool. Searches: `hunnu_search_free_rooms`, `hunnu_search_open_courses`, `hunnu_get_room_usage`.
Tools read JSON only. They do not submit applications.

## One-time setup

From `CS146s课程作业/`:

```bash
poetry install
poetry run pytest -q
```

The tests use local fixtures and mocked HTTP responses, including calls through an in-process MCP client. No school account, browser download, or model API key is needed to run them. Installing dependencies needs network access. This is the starting point for readers without Hunnu SSO access.

Only for real school queries, install the browser before the login step below:

```bash
poetry run playwright install chromium
```

## Commands

Login once (opens a browser, you complete school SSO, session is cached):

```bash
cd week2
poetry run python -m hunnu_mcp login
```

Start the MCP server over stdio from the same `week2/` directory:

```bash
poetry run python -m hunnu_mcp
```

Copy `.mcp.json.example` to `.mcp.json`, replace `cwd` with this `week2` absolute path, and point your agent at it. Do not commit `.mcp.json`.

## Auth constraint

Tool calls never open a browser. If the cached session is missing or dead, `hunnu_auth_status` returns `auth_required` / `auth_expired` and tells the agent to ask you to run `python -m hunnu_mcp login` in a terminal.

## Scope relative to the assignment

This implementation is a read-only school integration using cached SSO cookies. It does not implement the OAuth authorization-code exchange, access/refresh-token lifecycle, or write tool required by [the original assignment](assignment.md). An expired school session requires manual login; this is not silent OAuth token refresh.

Use the local tests to study tool schemas, output shaping, error handling, and MCP protocol behavior. To meet the original assignment, add a separate integration with an API for which you can obtain OAuth authorization, implement the required token lifecycle and a write tool with a preview or `dry_run` brake, and record the actual integration results in your own write-up. Do not treat passing mocked tests as evidence of those requirements.
