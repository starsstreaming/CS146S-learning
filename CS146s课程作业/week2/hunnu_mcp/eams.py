"""Multi-step EAMS reads. One tool call fetches the page, posts the
data query, and returns JSON. The model never sees HTML.
"""

from __future__ import annotations

from typing import Any

import httpx

from hunnu_mcp.client import HunnuClient, looks_like_login
from hunnu_mcp.document import parse_document
from hunnu_mcp.errors import auth_expired, parse_failed, unknown_semester, upstream_unavailable
from hunnu_mcp.parse import _number, current_semester_id, parse_grade_page, parse_meetings, parse_semesters, std_ids
from hunnu_mcp.portal import fetch_html


def _post(client: HunnuClient, path: str, data: dict[str, str]) -> httpx.Response:
    return client._client.post(path, data=data)


def _get(client: HunnuClient, path: str) -> httpx.Response:
    return client._client.get(path)


def _bounced_home(response: httpx.Response) -> bool:
    """The first hit on a fresh session can land on the home menu, not the course table."""
    return response.url.path.endswith("homeExt.action") or "new Menu(" in response.text


def load_course_table_page(client: HunnuClient) -> tuple[str | None, dict[str, Any] | None]:
    try:
        response = _get(client, "/eams/courseTableForStd.action")
        if _bounced_home(response):
            response = _get(client, "/eams/courseTableForStd.action")
    except httpx.HTTPError as exc:
        return None, upstream_unavailable(str(exc) or exc.__class__.__name__)
    if looks_like_login(str(response.url), response.text):
        return None, auth_expired()
    if _bounced_home(response):
        return None, parse_failed("timetable")
    return response.text, None


def _semester_catalog(client: HunnuClient, page: str) -> dict[str, Any]:
    """Query the calendar after the course-table page has already been read.

    A later GET of courseTableForStd.action omits the student id script,
    so callers must capture that id from `page` before this POST.
    """
    current = current_semester_id(page)
    if current is None:
        return parse_failed("semester calendar")
    try:
        response = _post(
            client,
            "/eams/dataQuery.action",
            {"dataType": "semesterCalendar", "empty": "false", "value": str(current)},
        )
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    if looks_like_login(str(response.url), response.text):
        return auth_expired()
    semesters = parse_semesters(response.text, current_semester_id=current)
    if not semesters:
        return parse_failed("semester calendar")
    return {
        "ok": True,
        "current_semester_id": current,
        "semesters": semesters,
    }


def list_semesters(client: HunnuClient) -> dict[str, Any]:
    page, error = load_course_table_page(client)
    if error:
        return error
    assert page is not None
    return _semester_catalog(client, page)


_PLAN_SKIP = {"应修学分", "学分小计", "实修学分"}


def _plan_credits(client: HunnuClient) -> tuple[dict[str, int | float | None], bool]:
    """Course name to 学分 from 培养计划. The bool is false when that page did not load."""
    html, error = fetch_html(client, "/eams/myPlan.action")
    if error or html is None:
        return {}, False
    credits: dict[str, int | float | None] = {}
    for table in parse_document(html)["tables"]:
        for row in table["rows"]:
            name = (row.get("课程名称") or "").strip()
            code = (row.get("课程代码") or "").strip()
            if not name or name in _PLAN_SKIP or code in _PLAN_SKIP:
                continue
            credits[name] = _number(str(row.get("学分") or ""))
    return credits, True


def _courses(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for meeting in meetings:
        name = meeting["course_name"]
        if name not in grouped:
            grouped[name] = {
                "course_name": name,
                "credits": meeting.get("credits"),
                "meetings": [],
            }
            order.append(name)
        grouped[name]["meetings"].append(
            {
                "weekday": meeting["weekday"],
                "weekday_name": meeting["weekday_name"],
                "start_section": meeting["start_section"],
                "end_section": meeting["end_section"],
                "weeks": meeting["weeks"],
                "room": meeting["room"],
            }
        )
    return [grouped[name] for name in order]


def get_timetable(
    client: HunnuClient,
    semester_id: int | None,
    week: int | None,
    weekday: int | None = None,
) -> dict[str, Any]:
    page, error = load_course_table_page(client)
    if error:
        return error
    assert page is not None
    student_ids = std_ids(page)
    if not student_ids:
        return parse_failed("timetable student id")
    catalog = _semester_catalog(client, page)
    if not catalog.get("ok"):
        return catalog
    if semester_id is None:
        semester_id = catalog["current_semester_id"]
    known = {row["semester_id"] for row in catalog["semesters"]}
    if semester_id not in known:
        return unknown_semester(semester_id)
    try:
        response = _post(
            client,
            "/eams/courseTableForStd!courseTable.action",
            {
                "ignoreHead": "1",
                "setting.kind": "std",
                "startWeek": "",
                "semester.id": str(semester_id),
                "ids": student_ids,
            },
        )
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    if looks_like_login(str(response.url), response.text):
        return auth_expired()
    if "TaskActivity" not in response.text and "courseTable" not in response.text:
        return parse_failed("timetable")
    meetings = parse_meetings(response.text)
    if week is not None:
        meetings = [item for item in meetings if week in item["weeks"]]
    if weekday is not None:
        meetings = [item for item in meetings if item["weekday"] == weekday]
    credits, plan_ok = _plan_credits(client)
    for meeting in meetings:
        meeting["credits"] = credits.get(meeting["course_name"])
    result = {
        "ok": True,
        "semester_id": semester_id,
        "week": week,
        "weekday": weekday,
        "count": len(meetings),
        "meetings": meetings,
        "courses": _courses(meetings),
    }
    if not plan_ok:
        result["notices"] = ["培养计划没有读到，credits 为空。不要改用开课查询或选课页补学分。"]
    return result


def get_grades(client: HunnuClient, semester_id: int) -> dict[str, Any]:
    """Published grades for one semester.

    The current-semester search grid is empty until scores are posted.
    person!historyCourseGrade already contains every published row, so
    this filters that page. semester_id still has to be in the calendar.
    """
    page, error = load_course_table_page(client)
    if error:
        return error
    assert page is not None
    catalog = _semester_catalog(client, page)
    if not catalog.get("ok"):
        return catalog
    semester = next((row for row in catalog["semesters"] if row["semester_id"] == semester_id), None)
    if semester is None:
        return unknown_semester(semester_id)
    try:
        response = _get(
            client,
            "/eams/teach/grade/course/person!historyCourseGrade.action?projectType=MAJOR",
        )
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    if looks_like_login(str(response.url), response.text):
        return auth_expired()
    parsed = parse_grade_page(response.text)
    if parsed is None:
        return parse_failed("grades")
    term_label = f"{semester['school_year']} {semester['term']}"
    grades = [row for row in parsed["grades"] if row["term_label"] == term_label]
    summary = next((row for row in parsed["summaries"] if row["term_label"] == term_label), None)
    return {
        "ok": True,
        "semester_id": semester_id,
        "label": semester["label"],
        "count": len(grades),
        "summary": summary,
        "grades": grades,
    }


def get_grade_overview(client: HunnuClient) -> dict[str, Any]:
    """Every posted term's campus summary, plus courses that did not pass.

    One GET of the history page. Passing course rows are left out.
    """
    try:
        response = _get(
            client,
            "/eams/teach/grade/course/person!historyCourseGrade.action?projectType=MAJOR",
        )
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    if looks_like_login(str(response.url), response.text):
        return auth_expired()
    parsed = parse_grade_page(response.text)
    if parsed is None:
        return parse_failed("grades")
    failed = [row for row in parsed["grades"] if row["passed"] is False]
    return {
        "ok": True,
        "summaries": parsed["summaries"],
        "count": len(failed),
        "failed": failed,
    }
