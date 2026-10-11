"""stdio MCP server.

Tools return JSON. HTML fetching and parsing stay in this process.
Writes are not exposed yet.
"""

from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from pydantic import Field

from hunnu_mcp.client import HunnuClient
from hunnu_mcp.config import session_path
from hunnu_mcp.eams import get_grade_overview, get_grades, get_timetable, list_semesters
from hunnu_mcp.errors import auth_expired, auth_required, upstream_unavailable
from hunnu_mcp.session import load_cookies

mcp = FastMCP(
    "hunnu-eams",
    instructions=(
        "Hunan Normal University undergraduate EAMS. "
        "Call hunnu_auth_status first. "
        "Current courses, credits, and times: hunnu_get_timetable with no arguments. "
        "One day: pass week and weekday (1=Monday .. 7=Sunday); other days are omitted. "
        "The course table has teaching-week numbers, not calendar dates. "
        "It already joins 培养计划 credits. Do not call hunnu_get_plan, "
        "hunnu_get_course_selection, or hunnu_search_open_courses for this student's credits or times. "
        "Omit semester_id on hunnu_get_timetable for the current semester. "
        "Grade standing: hunnu_get_grade_overview, one call, posted-term summaries and failed courses only. "
        "hunnu_get_grades is one semester's full rows and still needs semester_id. "
        "Credit gaps: hunnu_get_plan_progress returns only rollup rows whose 是否通过 contains 缺. "
        "hunnu_search_free_rooms and hunnu_get_room_usage are whole classrooms: "
        "seat_level is false, not library seats and not who sits nearby. "
        "An empty campus plus building result includes buildings, names only. "
        "Other 我的 and 公共服务 items have their own hunnu_* read tools. "
        "If a tool returns auth_required or auth_expired, tell the user to run "
        "`poetry run python -m hunnu_mcp login` in a terminal under week2/. "
        "Never assume a browser will pop during a tool call."
    ),
)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def hunnu_auth_status() -> dict[str, Any]:
    """Check whether the cached EAMS session can load the logged-in homepage.

    Returns JSON only. `ok` is true when GET /eams/homeExt.action stays on
    the teaching portal. On failure, read `error.code`:
    - auth_required: no session file. User must run `python -m hunnu_mcp login`.
    - auth_expired: session file exists but SSO bounced the request. Same login command.
    - upstream_unavailable: network or TLS failure; retry is allowed.

    This tool never opens a browser and never prints cookies.
    """
    cookies = load_cookies()
    if cookies is None:
        if not session_path().is_file():
            return auth_required()
        return auth_expired()

    client = HunnuClient(cookies)
    try:
        probe = client.probe_home()
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    finally:
        client.close()

    if not probe.logged_in:
        return auth_expired()

    return {
        "ok": True,
        "logged_in": True,
        "home_path": "/eams/homeExt.action",
        "http_status": probe.status_code,
    }


def _open() -> tuple[HunnuClient | None, dict[str, Any] | None]:
    cookies = load_cookies()
    if cookies is None:
        if not session_path().is_file():
            return None, auth_required()
        return None, auth_expired()
    return HunnuClient(cookies), None


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def hunnu_list_semesters() -> dict[str, Any]:
    """List EAMS semesters and which one the timetable page treats as current.

    Returns `current_semester_id` and `semesters[]` with `semester_id`,
    `school_year`, `term`, `label`, and `current`. hunnu_get_timetable omits
    semester_id for that current semester. hunnu_get_grade_overview needs no
    semester_id. Pass semester_id to hunnu_get_grades only for one semester's full rows.
    On auth_required or auth_expired, do not retry
    until the user finishes `python -m hunnu_mcp login`.
    """
    client, error = _open()
    if error or client is None:
        return error or auth_required()
    try:
        return list_semesters(client)
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    finally:
        client.close()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def hunnu_get_timetable(
    semester_id: Annotated[
        int | None,
        Field(description="semester_id from hunnu_list_semesters. Omit for the current semester."),
    ] = None,
    week: Annotated[
        int | None,
        Field(ge=1, le=20, description="Teaching week 1-20. Omit to return the whole semester."),
    ] = None,
    weekday: Annotated[
        int | None,
        Field(ge=1, le=7, description="1=Monday .. 7=Sunday. Omit to keep every weekday. Other days are dropped."),
    ] = None,
) -> dict[str, Any]:
    """Return the logged-in student's timetable and credits as JSON.

    Omit semester_id for the current semester. Pass one only for a different
    semester from hunnu_list_semesters. `courses` groups meetings by
    course_name and includes credits from 培养计划. Each meeting has
    lesson_id, class_code, course_name, teachers, credits, weekday
    (1=Monday .. 7=Sunday), weekday_name, start_section, end_section,
    weeks, and room. Do not call hunnu_get_plan, hunnu_get_course_selection,
    or hunnu_search_open_courses for this student's credits or times.
    `week` keeps meetings whose `weeks` include that teaching week.
    `weekday` drops every other day of that week. This page has no calendar dates.
    unknown_semester means the id was not in hunnu_list_semesters.
    This tool never opens a browser.
    """
    client, error = _open()
    if error or client is None:
        return error or auth_required()
    try:
        return get_timetable(client, semester_id, week, weekday)
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    finally:
        client.close()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def hunnu_get_grades(
    semester_id: Annotated[int, Field(description="semester_id from hunnu_list_semesters")],
) -> dict[str, Any]:
    """Return published course grades for one semester as JSON.

    `semester_id` must be a `semester_id` from hunnu_list_semesters.
    A semester with no posted grades returns `ok` true and `count` 0.
    Each grade has term_label, course_code, course_seq, course_name,
    category, credits, usual_score, lab_score, midterm_score, final_score,
    regular_score, score, passed, and grade_point. Score fields are
    strings or null. `summary` is that semester's 门数, 总学分, 平均成绩,
    and 平均绩点, or null when the campus page has no summary row.
    unknown_semester means the id was not in hunnu_list_semesters.
    This tool never opens a browser.
    """
    client, error = _open()
    if error or client is None:
        return error or auth_required()
    try:
        return get_grades(client, semester_id)
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    finally:
        client.close()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def hunnu_get_grade_overview() -> dict[str, Any]:
    """Return every posted term's summary and only the courses that did not pass.

    One call. Do not loop hunnu_get_grades per semester for a grade standing.
    `summaries` has term_label, course_count (门数), credits (总学分),
    average_score (平均成绩), and gpa (平均绩点) for each term on the history page.
    `failed` uses the same grade fields as hunnu_get_grades, and only rows
    whose 是否通过 is 否. Passing course rows are omitted.
    A term with no posted grades is absent. This tool never opens a browser.
    """
    client, error = _open()
    if error or client is None:
        return error or auth_required()
    try:
        return get_grade_overview(client)
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    finally:
        client.close()


from hunnu_mcp.catalog import register_menu_tools

register_menu_tools(mcp, _open)


def main() -> None:
    mcp.run(transport="stdio")
