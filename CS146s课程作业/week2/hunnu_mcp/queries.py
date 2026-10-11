"""Parameterized campus searches. The menu shells only hold the form."""

from __future__ import annotations

import re
import time
from typing import Any

from hunnu_mcp.client import HunnuClient
from hunnu_mcp.config import base_url
from hunnu_mcp.document import envelope, merge_documents, parse_document, parse_selects
from hunnu_mcp.errors import invalid_argument, parse_failed, unknown_filter
from hunnu_mcp.parse import current_semester_id
from hunnu_mcp.portal import fetch_html, read_paged

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME = re.compile(r"^\d{2}:\d{2}$")
_SEMESTER = re.compile(r"semester(?:\.id|Id)=(\d+)")


def _resolve(options: dict[str, str], kind: str, value: str | None) -> tuple[str, dict[str, Any] | None]:
    if not value:
        return "", None
    if value in options:
        return options[value], None
    matches = [label for label in options if value in label]
    if len(matches) == 1:
        return options[matches[0]], None
    return "", unknown_filter(kind, value, list(options))


def _semester_from(html: str, semester_id: int | None) -> int | None:
    if semester_id is not None:
        return semester_id
    found = _SEMESTER.search(html)
    if found:
        return int(found.group(1))
    return current_semester_id(html)


_NO_SEAT = "这是整间教室的排课，不是图书馆座位，也看不出空位旁边有没有人。"
_DROPPED = "查询条件没有命中任何开课，已丢弃未过滤的默认列表。"


def _rows(document: dict[str, Any]) -> list[dict[str, Any]]:
    if not document["tables"]:
        return []
    return document["tables"][0]["rows"]


def _note(document: dict[str, Any], text: str) -> None:
    if text not in document["notices"]:
        document["notices"].append(text)


def _building_names(rows: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for row in rows:
        name = (row.get("教学楼") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _campus_buildings(
    document: dict[str, Any],
    *,
    campus: str | None,
    building: str | None,
    again,
) -> list[str] | None:
    """Names only. An empty building used to make the model download every room."""
    rows = _rows(document)
    if rows:
        return _building_names(rows) or None
    if not campus or not building:
        return None
    # ponytail: one extra campus search, stopped by read_paged at 5 pages. The model must not do this itself.
    time.sleep(2)
    wider, error, _complete = again()
    if error or wider is None:
        return []
    return _building_names(_rows(wider))


def _drop_unfiltered(
    document: dict[str, Any],
    *,
    course_name: str | None,
    lesson_no: str | None,
    teacher: str | None,
) -> bool:
    """True when the campus grid ignored the filter and this replaced its rows."""
    rows = _rows(document)

    def hit(row: dict[str, Any]) -> bool:
        if course_name and course_name not in (row.get("课程名称") or ""):
            return False
        if lesson_no and lesson_no not in (row.get("课程序号") or ""):
            return False
        taught = row.get("教师") or row.get("教师姓名") or ""
        if teacher and teacher not in taught:
            return False
        return True

    matched = [row for row in rows if hit(row)]
    if len(matched) == len(rows):
        return False
    if document["tables"]:
        document["tables"][0]["rows"] = matched
        document["tables"][0]["total"] = len(matched)
    if not matched:
        _note(document, _DROPPED)
    return True


def search_free_rooms(
    client: HunnuClient,
    *,
    date: str,
    start_time: str,
    end_time: str,
    end_date: str | None = None,
    campus: str | None = None,
    building: str | None = None,
    room_type: str | None = None,
    min_seats: int | None = None,
) -> dict[str, Any]:
    """POST 空闲教室查询. Clock times use roomApplyTimeType=1, not section numbers."""
    if not _DATE.match(date) or (end_date is not None and not _DATE.match(end_date)):
        return invalid_argument("date and end_date must be YYYY-MM-DD.")
    if not _TIME.match(start_time) or not _TIME.match(end_time):
        return invalid_argument("start_time and end_time must be HH:mm.")
    form_path = "/eams/classroom/apply/free.action"
    referer = base_url().rstrip("/") + form_path
    form, error = fetch_html(client, form_path)
    if error or form is None:
        return error or parse_failed("空闲教室查询")
    selects = parse_selects(form)
    campus_id, filter_error = _resolve(selects.get("classroom.campus.id", {}), "campus", campus)
    if filter_error:
        return filter_error
    building_id, filter_error = _resolve(selects.get("classroom.building.id", {}), "building", building)
    if filter_error:
        return filter_error
    type_id, filter_error = _resolve(selects.get("classroom.type.id", {}), "room_type", room_type)
    if filter_error:
        return filter_error
    payload = {
        "classroom.type.id": type_id,
        "classroom.campus.id": campus_id,
        "classroom.building.id": building_id,
        "classroom.name": "",
        "seats": "" if min_seats is None else str(min_seats),
        "cycleTime.cycleCount": "1",
        "cycleTime.cycleType": "1",
        "cycleTime.dateBegin": date,
        "cycleTime.dateEnd": end_date or date,
        "roomApplyTimeType": "1",
        "timeBegin": start_time,
        "timeEnd": end_time,
    }

    document, error, complete = read_paged(
        client,
        "/eams/classroom/apply/free!search.action",
        {},
        referer=referer,
        data=payload,
    )
    if error or document is None:
        return error or parse_failed("空闲教室查询")
    buildings = _campus_buildings(
        document,
        campus=campus,
        building=building,
        again=lambda: read_paged(
            client,
            "/eams/classroom/apply/free!search.action",
            {},
            referer=referer,
            data={**payload, "classroom.building.id": ""},
        ),
    )
    _note(document, _NO_SEAT)
    extra: dict[str, Any] = {"complete": complete, "seat_level": False}
    if buildings is not None:
        extra["buildings"] = buildings
    return envelope("空闲教室查询", document, **extra)


def search_open_courses(
    client: HunnuClient,
    *,
    semester_id: int | None = None,
    course_name: str | None = None,
    lesson_no: str | None = None,
    teacher: str | None = None,
) -> dict[str, Any]:
    shell_path = "/eams/stdSyllabus.action"
    # Name filters are ignored until the course table has been opened on this client.
    shell, error = fetch_html(client, "/eams/courseTableForStd.action")
    if error or shell is None:
        return error or parse_failed("全校开课查询")
    semester = semester_id if semester_id is not None else current_semester_id(shell)
    if semester is None:
        return parse_failed("全校开课查询")
    params = {"lesson.project.id": "1", "lesson.semester.id": str(semester)}
    if course_name:
        params["lesson.course.name"] = course_name
    if lesson_no:
        params["lesson.no"] = lesson_no
    if teacher:
        params["teacher.name"] = teacher
    document, error, complete = read_paged(
        client,
        "/eams/stdSyllabus!search.action",
        params,
        referer=base_url().rstrip("/") + shell_path,
    )
    if error or document is None:
        return error or parse_failed("全校开课查询")
    if (course_name or lesson_no or teacher) and _drop_unfiltered(
        document,
        course_name=course_name,
        lesson_no=lesson_no,
        teacher=teacher,
    ):
        complete = True
    return envelope("全校开课查询", document, semester_id=semester, complete=complete)


def get_room_usage(
    client: HunnuClient,
    *,
    semester_id: int | None = None,
    campus: str | None = None,
    building: str | None = None,
    room: str | None = None,
) -> dict[str, Any]:
    """教室使用情况. `room` adds that room's occupancy board when one row matches."""
    shell_path = "/eams/classroom/occupy/status.action"
    shell, error = fetch_html(client, shell_path)
    if error or shell is None:
        return error or parse_failed("教室使用情况")
    semester = _semester_from(shell, semester_id)
    if semester is None:
        return parse_failed("教室使用情况")
    selects = parse_selects(shell)
    campus_id, filter_error = _resolve(selects.get("room.campus.id", {}), "campus", campus)
    if filter_error:
        return filter_error
    building_id, filter_error = _resolve(selects.get("room.building.id", {}), "building", building)
    if filter_error:
        return filter_error
    params = {"semesterId": str(semester)}
    if campus_id:
        params["room.campus.id"] = campus_id
    if building_id:
        params["room.building.id"] = building_id
    if room:
        params["room.name"] = room
    document, error, complete = read_paged(
        client,
        "/eams/classroom/occupy/status!search.action",
        params,
        referer=base_url().rstrip("/") + shell_path,
    )
    if error or document is None:
        return error or parse_failed("教室使用情况")
    rows = document["tables"][0]["rows"] if document["tables"] else []
    matched = [row for row in rows if room and room in (row.get("教室名称") or "")]
    target = matched[0] if len(matched) == 1 else None
    room_id = target.get("room_id") if target else None
    if room_id:
        detail, detail_error = fetch_html(
            client,
            "/eams/classroom/occupy/status!info.action"
            f"?mode=detail&roomIds={room_id}&semesterId={semester}",
            referer=base_url().rstrip("/") + shell_path,
        )
        if detail and not detail_error:
            document = merge_documents([document, parse_document(detail)])
    buildings = _campus_buildings(
        document,
        campus=campus,
        building=building,
        again=lambda: read_paged(
            client,
            "/eams/classroom/occupy/status!search.action",
            {"semesterId": str(semester), **({"room.campus.id": campus_id} if campus_id else {})},
            referer=base_url().rstrip("/") + shell_path,
        ),
    )
    _note(document, _NO_SEAT)
    extra: dict[str, Any] = {"semester_id": semester, "complete": complete, "seat_level": False}
    if buildings is not None:
        extra["buildings"] = buildings
    return envelope("教室使用情况", document, **extra)
