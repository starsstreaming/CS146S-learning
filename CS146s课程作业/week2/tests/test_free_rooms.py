import httpx

from hunnu_mcp.client import HunnuClient
from hunnu_mcp.queries import get_room_usage, search_free_rooms, search_open_courses

FORM = """
<select name="classroom.campus.id">
<option value="">...</option><option value="22">桃花坪校区</option>
</select>
<select name="classroom.building.id"><option value="8">达美楼</option></select>
<select name="classroom.type.id"><option value="4">多媒体教室</option></select>
"""

RESULT = """
<table class="gridtable">
<tr><td>序号</td><td>名称</td><td>容量</td></tr>
<tr><td>1</td><td>示例教室</td><td>40</td></tr>
</table>
"""


def test_free_room_search_posts_resolved_ids_and_rejects_unknown_campus():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("free.action"):
            return httpx.Response(200, text=FORM)
        seen.update(dict(request.url.params) if request.method == "GET" else {})
        body = request.content.decode()
        seen["body"] = body
        return httpx.Response(200, text=RESULT)

    client = HunnuClient(
        [{"name": "JSESSIONID", "value": "test", "domain": "example.test", "path": "/"}],
        origin="https://example.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        found = search_free_rooms(
            client,
            date="2026-10-06",
            start_time="08:00",
            end_time="10:00",
            campus="桃花坪",
            room_type="多媒体教室",
        )
        assert found["ok"] is True
        assert found["count"] == 1
        assert found["tables"][0]["rows"][0]["名称"] == "示例教室"
        assert "classroom.campus.id=22" in seen["body"]
        assert "roomApplyTimeType=1" in seen["body"]
        missing = search_free_rooms(
            client,
            date="2026-10-06",
            start_time="08:00",
            end_time="10:00",
            campus="不存在校区",
        )
        assert missing["error"]["code"] == "unknown_filter"
        assert missing["error"]["retry"] is False
        assert found["seat_level"] is False
    finally:
        client.close()


SHELL = """
jQuery("#semesterBar").semesterCalendar({empty:"false",onChange:"",value:"362"},"searchTable()");
"""

STALE = """
<table id="grid1" class="gridtable">
<tr><th>课程序号</th><th>课程名称</th><th>教师</th></tr>
<tr><td>2015</td><td>教育科学研究方法</td><td>某人</td></tr>
</table>
<script>page_grid1.pageInfo(1,1000,0);</script>
"""

OCCUPY = """
jQuery("#semesterBar").semesterCalendar({empty:"false",onChange:"",value:"362"},"searchTable()");
<select name="room.campus.id"><option value="22">桃花坪校区</option></select>
<select name="room.building.id"><option value="9">图书馆</option><option value="8">树达楼</option></select>
"""

EMPTY_ROOMS = """
<table id="grid1" class="gridtable">
<tr><th>教室名称</th><th>教学楼</th><th>校区</th></tr>
</table>
"""

CAMPUS_ROOMS = """
<table id="grid1" class="gridtable">
<tr><th>教室名称</th><th>教学楼</th><th>校区</th></tr>
<tr><td>101</td><td>树达楼</td><td>桃花坪校区</td></tr>
<tr><td>102</td><td>树达楼</td><td>桃花坪校区</td></tr>
<tr><td>201</td><td>达善楼</td><td>桃花坪校区</td></tr>
</table>
"""


def _client(handler) -> HunnuClient:
    return HunnuClient(
        [{"name": "JSESSIONID", "value": "test", "domain": "example.test", "path": "/"}],
        origin="https://example.test",
        transport=httpx.MockTransport(handler),
    )


def test_open_course_name_drops_an_unfiltered_catalog():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path.endswith("courseTableForStd.action"):
            return httpx.Response(200, text=SHELL)
        return httpx.Response(200, text=STALE)

    client = _client(handler)
    try:
        result = search_open_courses(client, semester_id=362, course_name="算法设计与分析")
    finally:
        client.close()
    assert any(path.endswith("courseTableForStd.action") for path in seen)
    assert result["ok"] is True
    assert result["count"] == 0
    assert result["complete"] is True
    assert result["tables"][0]["rows"] == []
    assert "丢弃" in "".join(result["notices"])


def test_empty_building_lists_campus_buildings_without_room_rows(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr("hunnu_mcp.queries.time.sleep", lambda seconds: slept.append(seconds))

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/status.action"):
            return httpx.Response(200, text=OCCUPY)
        if "room.building.id" in request.url.params:
            return httpx.Response(200, text=EMPTY_ROOMS)
        return httpx.Response(200, text=CAMPUS_ROOMS)

    client = _client(handler)
    try:
        result = get_room_usage(client, campus="桃花坪校区", building="图书馆")
    finally:
        client.close()
    assert slept == [2]
    assert result["ok"] is True
    assert result["count"] == 0
    assert result["seat_level"] is False
    assert result["buildings"] == ["树达楼", "达善楼"]
    assert result["tables"][0]["rows"] == []
    assert "座位" in "".join(result["notices"])
