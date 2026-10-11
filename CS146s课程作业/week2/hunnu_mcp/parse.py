"""Turn EAMS page scripts into small JSON records.

The campus pages are HTML with an embedded semester object and
TaskActivity(...) constructors. Week bit 0 is unused; week n is index n.
Section indexes in the script are 0-based; returned sections are 1-based.
Weekday 0 in the script is Monday; returned weekday is 1-7.

The history grade page is a plain HTML grid. Score cells stay strings
because the campus site also prints values such as 不及格.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

_SEMESTER = re.compile(r'\{id:(\d+),schoolYear:"([^"]+)",name:"([^"]+)"\}')
_CURRENT = re.compile(r'semesterCalendar\(\{empty:"false",onChange:"",value:"(\d+)"\}')
_STD_ID = re.compile(r'addInput\(form,"ids","(\d+)"\)')
_TEACHER = re.compile(r'name:"((?:\\.|[^"\\])*)"')
_TASK = re.compile(r"new TaskActivity\((.*?)\);", re.S)
_INDEX = re.compile(r"index\s*=\s*(\d+)\*unitCount\+(\d+);")
_QUOTED = re.compile(r'"((?:\\.|[^"\\])*)"')

WEEKDAY_NAMES = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")


def parse_semesters(script: str, *, current_semester_id: int | None) -> list[dict[str, Any]]:
    seen: set[int] = set()
    rows: list[dict[str, Any]] = []
    for sid, year, term in _SEMESTER.findall(script):
        semester_id = int(sid)
        if semester_id in seen:
            continue
        seen.add(semester_id)
        rows.append(
            {
                "semester_id": semester_id,
                "school_year": year,
                "term": term,
                "label": f"{year} 第{term}学期",
                "current": semester_id == current_semester_id,
            }
        )
    rows.sort(key=lambda row: row["semester_id"])
    return rows


def current_semester_id(course_table_html: str) -> int | None:
    match = _CURRENT.search(course_table_html)
    return int(match.group(1)) if match else None


def std_ids(course_table_html: str) -> str | None:
    """The first ids= value is the logged-in student's timetable id."""
    match = _STD_ID.search(course_table_html)
    return match.group(1) if match else None


def _unescape(value: str) -> str:
    return value.replace(r"\"", '"').replace(r"\n", " ")


def _split_course(raw: str) -> tuple[str, str]:
    match = re.match(r"(\d+)\(([^)]+)\)", raw)
    if not match:
        return raw, ""
    return match.group(1), match.group(2)


def _course_name(raw: str, class_code: str) -> str:
    suffix = f"({class_code})"
    if class_code and raw.endswith(suffix):
        return raw[: -len(suffix)]
    return raw


def _weeks(mask: str) -> list[int]:
    return [index for index, bit in enumerate(mask) if bit == "1" and index > 0]


def parse_meetings(script: str) -> list[dict[str, Any]]:
    """One record per course block on one weekday, with consecutive sections merged."""
    parts = re.split(r"var teachers\s*=", script)
    raw: list[dict[str, Any]] = []
    for part in parts[1:]:
        task = _TASK.search(part)
        if not task:
            continue
        quoted = [_unescape(item) for item in _QUOTED.findall(task.group(1))]
        if len(quoted) < 5:
            continue
        lesson_id, class_code = _split_course(quoted[0])
        room = quoted[3]
        weeks = _weeks(quoted[4])
        teachers = [_unescape(name) for name in _TEACHER.findall(part[: task.start()])]
        slots = [(int(day), int(section)) for day, section in _INDEX.findall(part[task.end() :])]
        # Indexes after this activity stop at the next teachers block, which split already did.
        by_day: dict[int, list[int]] = {}
        for day, section in slots:
            by_day.setdefault(day, []).append(section)
        for day, sections in by_day.items():
            raw.append(
                {
                    "lesson_id": lesson_id,
                    "class_code": class_code,
                    "course_name": _course_name(quoted[1], class_code),
                    "teachers": teachers,
                    "weekday": day + 1,
                    "sections": sorted(set(sections)),
                    "weeks": weeks,
                    "room": room,
                }
            )
    return [_merge(item) for item in _fill_rooms(raw)]


def _fill_rooms(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Empty-room duplicates keep the room of the same lesson on that weekday."""
    rooms: dict[tuple[str, int], str] = {}
    for row in rows:
        if row["room"]:
            rooms[(row["lesson_id"], row["weekday"])] = row["room"]
    filled: list[dict[str, Any]] = []
    for row in rows:
        if not row["room"]:
            row["room"] = rooms.get((row["lesson_id"], row["weekday"]), "")
        filled.append(row)
    # Drop a row that is only a repeat of the same sections already stored with a room.
    seen: set[tuple] = set()
    unique: list[dict[str, Any]] = []
    for row in filled:
        key = (row["lesson_id"], row["weekday"], tuple(row["sections"]), row["room"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


_SCORE_FIELDS = {
    "平时成绩": "usual_score",
    "实验成绩": "lab_score",
    "期中成绩": "midterm_score",
    "期末成绩": "final_score",
    "正考总评成绩": "regular_score",
    "最终成绩": "score",
    "绩点": "grade_point",
}
_REQUIRED_GRADE_HEADERS = ("学年学期", "课程代码", "课程名称", "学分", "最终成绩")


class _GridTables(HTMLParser):
    """Collect text cells from each top-level table. Nested tables are ignored."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._depth = 0
        self._table: list[list[str]] = []
        self._row: list[str] = []
        self._cell: list[str] = []
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            if self._depth == 0:
                self._table = []
            self._depth += 1
        elif self._depth == 1 and tag == "tr":
            self._row = []
        elif self._depth == 1 and tag in ("td", "th"):
            self._in_cell = True
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append(text)
            self._in_cell = False
        elif tag == "tr" and self._depth == 1 and self._row:
            self._table.append(self._row)
            self._row = []
        elif tag == "table" and self._depth:
            self._depth -= 1
            if self._depth == 0 and self._table:
                self.tables.append(self._table)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell.append(data)


def _blank(value: str) -> str | None:
    text = value.strip()
    return text or None


def _passed(value: str) -> bool | None:
    text = value.strip()
    if text == "是":
        return True
    if text == "否":
        return False
    return None


def _number(value: str) -> int | float | None:
    text = value.strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def _table_by_headers(tables: list[list[list[str]]], required: tuple[str, ...]) -> list[list[str]] | None:
    for table in tables:
        if not table:
            continue
        header = set(table[0])
        if all(name in header for name in required):
            return table
    return None


def parse_grade_page(html: str) -> dict[str, Any] | None:
    """Parse the all-semester grade page.

    Returns None when the course grid header is missing. A header with an
    empty body is valid and yields `grades: []`.
    `term_label` is the campus cell, such as `2025-2026 1`.
    """
    parser = _GridTables()
    parser.feed(html)
    course_table = _table_by_headers(parser.tables, _REQUIRED_GRADE_HEADERS)
    if course_table is None:
        return None
    header = course_table[0]
    grades: list[dict[str, Any]] = []
    for cells in course_table[1:]:
        raw = {name: cells[index] if index < len(cells) else "" for index, name in enumerate(header)}
        course_code = _blank(raw.get("课程代码", ""))
        course_name = _blank(raw.get("课程名称", ""))
        if not course_code or not course_name:
            continue
        row: dict[str, Any] = {
            "term_label": re.sub(r"\s+", " ", raw.get("学年学期", "")).strip(),
            "course_code": course_code,
            "course_seq": _blank(raw.get("课程序号", "")),
            "course_name": course_name,
            "category": _blank(raw.get("课程类别", "")),
            "credits": _number(raw.get("学分", "")),
            "passed": _passed(raw.get("是否通过", "")),
        }
        for source, field in _SCORE_FIELDS.items():
            row[field] = _blank(raw.get(source, ""))
        grades.append(row)

    summaries: list[dict[str, Any]] = []
    summary_table = _table_by_headers(parser.tables, ("学年度", "学期", "门数", "总学分"))
    if summary_table is not None:
        summary_header = summary_table[0]
        for cells in summary_table[1:]:
            raw = {name: cells[index] if index < len(cells) else "" for index, name in enumerate(summary_header)}
            year = raw.get("学年度", "").strip()
            term = raw.get("学期", "").strip()
            if not re.fullmatch(r"\d{4}-\d{4}", year):
                continue
            summaries.append(
                {
                    "school_year": year,
                    "term": term,
                    "term_label": f"{year} {term}",
                    "course_count": _number(raw.get("门数", "")),
                    "credits": _number(raw.get("总学分", "")),
                    "average_score": _blank(raw.get("平均成绩", "")),
                    "gpa": _blank(raw.get("平均绩点", "")),
                }
            )
    return {"grades": grades, "summaries": summaries}


def _merge(row: dict[str, Any]) -> dict[str, Any]:
    sections = row["sections"]
    start = end = sections[0]
    for section in sections[1:]:
        if section == end + 1:
            end = section
            continue
        break
    return {
        "lesson_id": row["lesson_id"],
        "class_code": row["class_code"],
        "course_name": row["course_name"],
        "teachers": row["teachers"],
        "weekday": row["weekday"],
        "weekday_name": WEEKDAY_NAMES[row["weekday"] - 1],
        "start_section": start + 1,
        "end_section": end + 1,
        "weeks": row["weeks"],
        "room": row["room"],
    }
