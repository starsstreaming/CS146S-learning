"""Fetch one campus page and turn it into the document envelope.

The teaching-plan action answers the first request with a gateway bounce
that ends on the home page, then serves the plan on the next request in
the same cookie jar. Callers retry once and do not write those cookies back.
"""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from hunnu_mcp.client import HunnuClient, looks_like_login
from hunnu_mcp.config import base_url
from hunnu_mcp.document import envelope, merge_documents, parse_document
from hunnu_mcp.errors import auth_expired, parse_failed, upstream_unavailable
from hunnu_mcp.parse import current_semester_id

_HOME = "/eams/homeExt.action"
_SEMESTER_IN_PAGE = re.compile(r"semester(?:\.id|Id)=(\d+)")
# A second hit on the same search within about two seconds returns 请不要过快点击.
# 1000 is the largest page size the grid's own selector offers, so one request
# covers a semester of courses or the room list. A later page waits first.
_PAGE_SIZE = 1000
_FAST_CLICK = "请不要过快点击"


def _referer(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    return base_url().rstrip("/") + _HOME


def _bounced(path: str, response: httpx.Response, text: str) -> bool:
    if "homeExt.action" in path:
        return False
    final = response.url.path
    if final.endswith("homeExt.action"):
        return True
    return "new Menu(" in text


def _error_page(text: str) -> bool:
    return "HTTP Status 500" in text or "HTTP Status 404" in text


def fetch_html(
    client: HunnuClient,
    path: str,
    *,
    data: dict[str, str] | None = None,
    referer: str | None = None,
) -> tuple[str | None, dict[str, Any] | None]:
    """GET or POST `path`. Returns (html, None) or (None, error)."""
    headers = {"Referer": _referer(referer)}

    def once() -> httpx.Response:
        if data is None:
            return client._client.get(path, headers=headers)
        return client._client.post(path, data=data, headers=headers)

    try:
        response = once()
    except httpx.HTTPError as exc:
        return None, upstream_unavailable(str(exc) or exc.__class__.__name__)
    if looks_like_login(str(response.url), response.text):
        return None, auth_expired()
    if _bounced(path, response, response.text):
        try:
            response = once()
        except httpx.HTTPError as exc:
            return None, upstream_unavailable(str(exc) or exc.__class__.__name__)
        if looks_like_login(str(response.url), response.text):
            return None, auth_expired()
        if _bounced(path, response, response.text):
            return None, parse_failed(path)
    if _error_page(response.text):
        return None, parse_failed(path)
    return response.text, None


def _with_semester(path: str, semester_id: int | None, html: str | None) -> str:
    if "{semester}" not in path:
        return path
    value = semester_id
    if value is None and html:
        found = _SEMESTER_IN_PAGE.search(html) or None
        if found:
            value = int(found.group(1))
        else:
            value = current_semester_id(html)
    if value is None:
        return path.replace("{semester}", "")
    return path.replace("{semester}", str(value))


def _shell(path: str) -> str:
    base = path.split("?", 1)[0]
    if "!" in base:
        base = base.split("!", 1)[0] + ".action"
    return base


def load_paths(
    client: HunnuClient,
    menu: str,
    paths: tuple[str, ...],
    *,
    semester_id: int | None = None,
    referer: str | None = None,
) -> dict[str, Any]:
    parts: list[dict[str, Any]] = []
    failures = 0
    for path in paths:
        resolved = path
        if "{semester}" in path:
            page_html = None
            if semester_id is None:
                page_html, error = fetch_html(client, _shell(path), referer=referer)
                if error and page_html is None:
                    failures += 1
                    continue
            resolved = _with_semester(path, semester_id, page_html)
        html, error = fetch_html(client, resolved, referer=referer)
        if error or html is None:
            failures += 1
            continue
        parts.append(parse_document(html))
    if not parts:
        return parse_failed(menu)
    if failures and not any(part["tables"] or part["fields"] or part["notices"] for part in parts):
        return parse_failed(menu)
    document = merge_documents(parts)
    if menu == "计划完成情况":
        # Course rows have no 分组. A satisfied group does not state a gap.
        for table in document["tables"]:
            table["rows"] = [
                row
                for row in table["rows"]
                if row.get("分组") and "缺" in str(row.get("是否通过") or "")
            ]
    return envelope(menu, document)


def load_exams(client: HunnuClient, semester_id: int | None) -> dict[str, Any]:
    """我的考试. Omit semester_id to read the page's current semester."""
    if semester_id is None:
        return load_paths(client, "我的考试", ("/eams/stdExamTable.action",))
    html, error = fetch_html(
        client,
        "/eams/stdExamTable.action",
        data={"semester.id": str(semester_id)},
    )
    if error or html is None:
        return error or parse_failed("我的考试")
    return envelope("我的考试", parse_document(html))


def load_election(client: HunnuClient) -> dict[str, Any]:
    """选课: the round rules, then each 进入选课 page linked from that shell."""
    shell_path = "/eams/stdElectCourse.action"
    html, error = fetch_html(client, shell_path)
    if error or html is None:
        return error or parse_failed("选课")
    parts = [parse_document(html)]
    referer = _referer(base_url().rstrip("/") + shell_path)
    for profile_id in dict.fromkeys(re.findall(r"electionProfile\.id=(\d+)", html)):
        page, page_error = fetch_html(
            client,
            f"/eams/stdElectCourse!defaultPage.action?electionProfile.id={profile_id}",
            referer=referer,
        )
        if page_error or page is None:
            continue
        if page.strip() == "请求参数非法":
            parts[0]["notices"].append("请求参数非法")
            continue
        parts.append(parse_document(page))
    return envelope("选课", merge_documents(parts))


def _fetch_page(
    client: HunnuClient,
    path: str,
    query: dict[str, str],
    *,
    referer: str | None,
    data: dict[str, str] | None,
    pause_s: float,
) -> tuple[str | None, dict[str, Any] | None]:
    if data is None:
        target = path + "?" + urlencode(query)
        body = None
    else:
        target = path
        body = {**data, **query}
    html, error = fetch_html(client, target, data=body, referer=referer)
    for _ in range(3):
        if error or html is None or _FAST_CLICK not in html:
            return html, error
        time.sleep(pause_s)
        html, error = fetch_html(client, target, data=body, referer=referer)
    return html, error


def read_paged(
    client: HunnuClient,
    path: str,
    params: dict[str, str],
    *,
    referer: str | None = None,
    data: dict[str, str] | None = None,
    pause_s: float = 2,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    """Read a search grid. The third value is false when the grid stopped early."""
    collected_rows: list[dict[str, Any]] = []
    first_key: str | None = None
    total: int | None = None
    headers: list[str] = []
    notices: list[str] = []
    fields: list[dict[str, Any]] = []
    # True only when the grid itself ended: empty, short page, or pageInfo total met.
    finished = False
    for page in range(1, 6):
        query = dict(params)
        query["pageNo"] = str(page)
        query["pageSize"] = str(_PAGE_SIZE)
        if page > 1:
            time.sleep(pause_s)
        html, error = _fetch_page(client, path, query, referer=referer, data=data, pause_s=pause_s)
        if error or html is None:
            if page == 1:
                return None, error, False
            break
        if _FAST_CLICK in html:
            notices.append(_FAST_CLICK)
            break
        document = parse_document(html)
        for notice in document["notices"]:
            if notice not in notices:
                notices.append(notice)
        if page == 1:
            fields = document["fields"]
        if not document["tables"]:
            break
        table = document["tables"][0]
        headers = headers or table["headers"]
        # A reported total of 0 while rows exist is a stale grid, not an empty result.
        reported = table["total"]
        if isinstance(reported, int) and reported > 0:
            total = reported
        rows = table["rows"]
        if not rows:
            finished = total is None or len(collected_rows) >= total
            break
        key = repr(rows[0])
        if first_key is None:
            first_key = key
        elif key == first_key:
            finished = total is not None and len(collected_rows) >= total
            break
        collected_rows.extend(rows)
        if total is not None and len(collected_rows) >= total:
            finished = True
            break
        if total is None and len(rows) < _PAGE_SIZE:
            finished = True
            break
    document = {
        "notices": notices,
        "fields": fields,
        "tables": [
            {
                "id": "",
                "headers": headers,
                "rows": collected_rows,
                "page": 1,
                "page_size": _PAGE_SIZE,
                "total": total if total is not None else len(collected_rows),
            }
        ]
        if headers or collected_rows
        else [],
    }
    return document, None, finished
