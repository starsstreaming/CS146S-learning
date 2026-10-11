"""Turn an EAMS HTML page into notices, label/value fields, and tables.

Column names stay as the campus headers. Checkbox columns are dropped.
A two-row header such as the training plan keeps the leaf label, and a
numbered child of 建议修读学期 becomes 学期1.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

_PAGE_INFO = re.compile(r"page_(grid\d+)\.pageInfo\((\d+),(\d+),(\d+)\)")
_NOTICE = re.compile(
    r"(当前(?:没有|无|学期|不)[^。\n]{0,40}"
    r"|尚未[^。\n]{0,30}"
    r"|暂无[^。\n]{0,30}"
    r"|没有(?:查询结果|申请|相关)[^。\n]{0,30}"
    r"|未开放[^。\n]{0,20}"
    r"|无法申请[^。\n]{0,24}"
    r"|不在申请[^。\n]{0,30}"
    r"|请求参数非法)"
)
_SPACE = re.compile(r"\s+")


class _Cell:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.classes = ""
        self.colspan = 1
        self.rowspan = 1
        self.checkbox = False
        self.href = ""

    @property
    def text(self) -> str:
        raw = _SPACE.sub(" ", "".join(self.parts).replace("\xa0", " ")).strip()
        if "course" in self.classes:
            raw = re.sub(r"^\d+\s+", "", raw)
        return raw


class _Row:
    def __init__(self) -> None:
        self.cells: list[_Cell] = []
        self.classes = ""
        self.in_head = False


class _Table:
    def __init__(self, attrs: dict[str, str]) -> None:
        self.attrs = attrs
        self.rows: list[_Row] = []


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[_Table] = []
        self.headings: list[str] = []
        self._skip = 0
        self._table_stack: list[_Table] = []
        self._row: _Row | None = None
        self._cell: _Cell | None = None
        self._in_head = False
        self._heading: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag in ("script", "style"):
            self._skip += 1
            return
        if self._skip:
            return
        if tag == "table":
            self._table_stack.append(_Table(attr))
        elif tag == "thead" and self._table_stack:
            self._in_head = True
        elif tag == "tr" and self._table_stack:
            self._row = _Row()
            self._row.classes = attr.get("class", "")
            self._row.in_head = self._in_head
        elif tag in ("td", "th") and self._row is not None:
            cell = _Cell()
            cell.classes = attr.get("class", "")
            cell.colspan = _int(attr.get("colspan"))
            cell.rowspan = _int(attr.get("rowspan"))
            self._cell = cell
        elif tag == "input" and self._cell is not None and attr.get("type") == "checkbox":
            self._cell.checkbox = True
        elif tag == "a" and self._cell is not None and attr.get("href"):
            self._cell.href = attr["href"]
        elif tag in ("h1", "h2"):
            self._heading = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
            return
        if self._skip:
            return
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.cells.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table_stack:
            if self._row.cells:
                self._table_stack[-1].rows.append(self._row)
            self._row = None
        elif tag == "thead":
            self._in_head = False
        elif tag == "table" and self._table_stack:
            table = self._table_stack.pop()
            if table.rows:
                self.tables.append(table)
        elif tag in ("h1", "h2") and self._heading is not None:
            text = _clean("".join(self._heading))
            if text:
                self.headings.append(text)
            self._heading = None

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._cell is not None:
            self._cell.parts.append(data)
        if self._heading is not None:
            self._heading.append(data)


def _int(value: str | None) -> int:
    try:
        return max(int(value or "1"), 1)
    except ValueError:
        return 1


def _clean(value: str) -> str:
    return _SPACE.sub(" ", value.replace("\xa0", " ")).strip()


def _leaf_headers(rows: list[_Row]) -> list[str]:
    occupied: dict[tuple[int, int], str] = {}
    for row_index, row in enumerate(rows):
        column = 0
        for cell in row.cells:
            if cell.checkbox:
                continue
            while (row_index, column) in occupied:
                column += 1
            for down in range(cell.rowspan):
                for across in range(cell.colspan):
                    occupied[(row_index + down, column + across)] = cell.text
            column += cell.colspan
    if not occupied:
        return []
    width = max(column for _, column in occupied) + 1
    depth = max(row for row, _ in occupied) + 1
    headers: list[str] = []
    for column in range(width):
        labels: list[str] = []
        for row in range(depth):
            text = occupied.get((row, column), "")
            if text and (not labels or text != labels[-1]):
                labels.append(text)
        if not labels:
            headers.append("")
        elif len(labels) > 1 and labels[-1].isdigit():
            headers.append(f"学期{labels[-1]}")
        elif len(labels) > 1:
            headers.append(labels[-1])
        else:
            headers.append(labels[0])
    return headers


def _header_rows(table: _Table) -> list[_Row]:
    headed = [row for row in table.rows if row.in_head and any(cell.text for cell in row.cells)]
    if headed:
        return headed
    if not table.rows:
        return []
    first = table.rows[0]
    titled = [
        cell
        for cell in first.cells
        if "title" in cell.classes and cell.text and not cell.text.endswith((":", "："))
    ]
    classes = table.attrs.get("class", "")
    if len(titled) >= 2 or any(name in classes for name in ("formTable", "planTable", "gridtable", "reportTable")):
        if any(cell.text for cell in first.cells):
            return [first]
    return []


def _record(cells: list[_Cell], headers: list[str]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    index = 0
    for cell in cells:
        if cell.checkbox:
            continue
        while index < len(headers) and headers[index] == "":
            index += 1
        if index >= len(headers):
            break
        if index == 0 and cell.colspan > 1:
            record["分组"] = cell.text or None
            index += cell.colspan
            continue
        key = headers[index]
        if key and key not in record:
            record[key] = cell.text or None
        if cell.href and "roomIds=" in cell.href:
            match = re.search(r"roomIds=(\d+)", cell.href)
            if match:
                record["room_id"] = match.group(1)
        index += cell.colspan
    return record


def _fields(table: _Table) -> list[dict[str, str | None]]:
    fields: list[dict[str, str | None]] = []
    pending: str | None = None
    for row in table.rows:
        for cell in row.cells:
            if "title" in cell.classes and cell.text.endswith((":", "：")):
                pending = cell.text.rstrip(":：").strip()
                continue
            if pending:
                fields.append({"label": pending, "value": cell.text or None})
                pending = None
    return fields


def _is_field_table(table: _Table) -> bool:
    classes = table.attrs.get("class", "")
    if "infoTable" in classes:
        return True
    titled = [
        cell
        for row in table.rows
        for cell in row.cells
        if "title" in cell.classes and cell.text.endswith((":", "："))
    ]
    return len(titled) >= 2


def _grid(table: _Table) -> dict[str, Any] | None:
    header_rows = _header_rows(table)
    if not header_rows:
        return None
    headers = _leaf_headers(header_rows)
    if not any(headers):
        return None
    header_ids = {id(row) for row in header_rows}
    rows: list[dict[str, Any]] = []
    for row in table.rows:
        # The filter boxes live in thead and have no label text, so they are not headers.
        if id(row) in header_ids or row.in_head:
            continue
        if "darkColumn" in row.classes and any(cell.colspan > 1 for cell in row.cells):
            record = _record(row.cells, headers)
            if record:
                record["分组"] = next((cell.text for cell in row.cells if cell.colspan > 1 and cell.text), record.get("分组"))
                rows.append(record)
            continue
        text = " ".join(cell.text for cell in row.cells if cell.text)
        if "没有查询结果" in text:
            continue
        record = _record(row.cells, headers)
        echoed = sum(1 for key, value in record.items() if value == key)
        filled = [value for value in record.values() if value]
        # The election week grid is only "第一节" with every day blank. It is not a course.
        if len(filled) == 1 and re.match(r"^第.+节", filled[0]):
            continue
        if record and echoed < 2:
            rows.append(record)
    display: list[str] = []
    for header in headers:
        if header and header not in display:
            display.append(header)
    return {
        "id": table.attrs.get("id", ""),
        "headers": display,
        "rows": rows,
        "page": None,
        "page_size": None,
        "total": None,
    }


def _notices(html: str, headings: list[str]) -> list[str]:
    visible = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    visible = re.sub(r"<style[\s\S]*?</style>", " ", visible, flags=re.I)
    visible = re.sub(r"<[^>]+>", "\n", visible)
    found = list(headings)
    for match in _NOTICE.findall(visible):
        text = _clean(match)
        if text and text not in found:
            found.append(text)
    return found


def parse_selects(html: str) -> dict[str, dict[str, str]]:
    """Map each select name to {visible label: option value}."""
    selects: dict[str, dict[str, str]] = {}
    current: str | None = None
    for match in re.finditer(
        r"<select[^>]*name=\"([^\"]+)\"[^>]*>|</select>|<option([^>]*)>(.*?)</option>",
        html,
        flags=re.I | re.S,
    ):
        if match.group(1):
            current = match.group(1)
            selects.setdefault(current, {})
            continue
        if match.group(0).lower() == "</select>":
            current = None
            continue
        if current is None:
            continue
        attrs = match.group(2) or ""
        label = _clean(re.sub(r"<[^>]+>", "", match.group(3) or ""))
        value_match = re.search(r"value=\"([^\"]*)\"", attrs)
        value = value_match.group(1) if value_match else ""
        if label and label not in ("...", "全部") and value:
            selects[current][label] = value
    return selects


def parse_document(html: str) -> dict[str, Any]:
    parser = _DocumentParser()
    parser.feed(html)
    fields: list[dict[str, str | None]] = []
    tables: list[dict[str, Any]] = []
    for table in parser.tables:
        if _is_field_table(table):
            fields.extend(_fields(table))
            continue
        grid = _grid(table)
        if grid and (grid["rows"] or grid["headers"]):
            tables.append(grid)
    page_info = {grid_id: (int(page), int(size), int(total)) for grid_id, page, size, total in _PAGE_INFO.findall(html)}
    for table in tables:
        info = page_info.get(table["id"])
        if info:
            table["page"], table["page_size"], table["total"] = info
    return {"notices": _notices(html, parser.headings), "fields": fields, "tables": tables}


def merge_documents(parts: list[dict[str, Any]]) -> dict[str, Any]:
    notices: list[str] = []
    fields: list[dict[str, str | None]] = []
    tables: list[dict[str, Any]] = []
    for part in parts:
        for notice in part["notices"]:
            if notice not in notices:
                notices.append(notice)
        fields.extend(part["fields"])
        tables.extend(part["tables"])
    return {"notices": notices, "fields": fields, "tables": tables}


def envelope(menu: str, document: dict[str, Any], **extra: Any) -> dict[str, Any]:
    count = sum(len(table["rows"]) for table in document["tables"])
    body = {
        "ok": True,
        "menu": menu,
        "notices": document["notices"],
        "fields": document["fields"],
        "tables": document["tables"],
        "count": count,
    }
    body.update(extra)
    return body
