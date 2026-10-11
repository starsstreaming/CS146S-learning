"""Exercise the server through the MCP client, not by calling the Python function."""

from __future__ import annotations

import json

from fastmcp import Client

from hunnu_mcp.catalog import PAGES, SEARCH_TOOLS
from hunnu_mcp.server import mcp


def _text_payload(result) -> dict:
    """FastMCP wraps tool JSON in MCP text content. Parse that envelope."""
    content = result.content[0]
    return json.loads(content.text)


async def test_lists_hunnu_auth_status_over_mcp():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = [tool.name for tool in tools]
        assert names[:4] == [
            "hunnu_auth_status",
            "hunnu_list_semesters",
            "hunnu_get_timetable",
            "hunnu_get_grades",
        ]
        assert names[4] == "hunnu_get_grade_overview"
        assert names[5:] == [page.tool for page in PAGES] + list(SEARCH_TOOLS)
        status = tools[0]
        schema = getattr(status, "input_schema", None) or status.inputSchema
        assert schema.get("properties", {}) == {}
        timetable = tools[2]
        params = (getattr(timetable, "input_schema", None) or timetable.inputSchema)["properties"]
        assert "semester_id" in params
        assert "week" in params
        assert "weekday" in params
        assert "payload" not in params
        assert "hunnu_list_semesters" in (timetable.description or "")
        grades = tools[3]
        grade_params = (getattr(grades, "input_schema", None) or grades.inputSchema)["properties"]
        assert set(grade_params) == {"semester_id"}
        assert "hunnu_list_semesters" in (grades.description or "")
        overview = tools[4]
        overview_schema = getattr(overview, "input_schema", None) or overview.inputSchema
        assert overview_schema.get("properties", {}) == {}
        assert "failed" in (overview.description or "")
        by_name = {tool.name: tool for tool in tools}
        progress = by_name["hunnu_get_plan_progress"]
        assert "缺" in (progress.description or "")
        assert "分组" in (progress.description or "")
        record = by_name["hunnu_get_student_record"]
        record_schema = getattr(record, "input_schema", None) or record.inputSchema
        assert record_schema.get("properties", {}) == {}
        assert "学籍信息" in (record.description or "")
        free = by_name["hunnu_search_free_rooms"]
        free_params = (getattr(free, "input_schema", None) or free.inputSchema)["properties"]
        assert {"date", "start_time", "end_time"} <= set(free_params)
        assert "payload" not in free_params


async def test_auth_status_without_session_is_structured_error(tmp_path, monkeypatch):
    monkeypatch.setenv("HUNNU_SESSION_PATH", str(tmp_path / "no-session.json"))
    async with Client(mcp) as client:
        result = await client.call_tool("hunnu_auth_status", {})
        payload = _text_payload(result)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "auth_required"
        assert payload["error"]["retry"] is False
        assert "python -m hunnu_mcp login" in payload["error"]["next_step"]
