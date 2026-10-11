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
poetry run playwright install chromium
```

## Commands

Login once (opens a browser, you complete school SSO, session is cached):

```bash
cd week2
poetry run python -m hunnu_mcp login
```

Start the MCP server over stdio:

```bash
cd week2
poetry run python -m hunnu_mcp
```

Copy `.mcp.json.example` to `.mcp.json`, replace `cwd` with this `week2` absolute path, and point your agent at it. Do not commit `.mcp.json`.

## Auth constraint

Tool calls never open a browser. If the cached session is missing or dead, `hunnu_auth_status` returns `auth_required` / `auth_expired` and tells the agent to ask you to run `python -m hunnu_mcp login` in a terminal.
