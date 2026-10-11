"""Grade reads stay inside the server: calendar check, then the history page."""

import httpx

from hunnu_mcp.client import HunnuClient
from hunnu_mcp.eams import get_grade_overview, get_grades, get_timetable

PAGE = """
jQuery("#semesterBar").semesterCalendar({empty:"false",onChange:"",value:"362"},"searchTable()");
bg.form.addInput(form,"ids","386414");
bg.form.addInput(form,"ids","5561");
"""

CALENDAR = """
semesters:{y0:[{id:100,schoolYear:"2025-2026",name:"1"},{id:362,schoolYear:"2026-2027",name:"1"}]}
"""

GRADES = """
<table>
<tr><th>学年度</th><th>学期</th><th>门数</th><th>总学分</th><th>平均成绩</th><th>平均绩点</th></tr>
<tr><td>2025-2026</td><td>1</td><td>1</td><td>2</td><td>90</td><td>4</td></tr>
</table>
<table>
<tr>
<th>学年学期</th><th>课程代码</th><th>课程序号</th><th>课程名称</th><th>课程类别</th>
<th>学分</th><th>平时成绩</th><th>实验成绩</th><th>期中成绩</th><th>期末成绩</th>
<th>正考总评成绩</th><th>最终成绩</th><th>是否通过</th><th>绩点</th>
</tr>
<tr>
<td>2025-2026 1</td><td>1001</td><td>1001.01</td><td>示例课程甲</td><td>专业必修课</td>
<td>2</td><td></td><td></td><td></td><td></td><td></td><td>90</td><td>是</td><td>4</td>
</tr>
</table>
"""


def _client(handler) -> HunnuClient:
    return HunnuClient(
        [{"name": "JSESSIONID", "value": "test", "domain": "example.test", "path": "/"}],
        origin="https://example.test",
        transport=httpx.MockTransport(handler),
    )


def test_course_table_retries_once_after_the_home_bounce():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("courseTableForStd.action"):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(200, text="new Menu({id:1})")
            return httpx.Response(200, text=PAGE)
        if request.url.path.endswith("dataQuery.action"):
            return httpx.Response(200, text=CALENDAR)
        return httpx.Response(404, text="missing")

    client = _client(handler)
    try:
        from hunnu_mcp.eams import list_semesters

        result = list_semesters(client)
    finally:
        client.close()
    assert calls["n"] == 2
    assert result["ok"] is True
    assert result["current_semester_id"] == 362


def test_get_grades_filters_one_semester_and_allows_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("courseTableForStd.action"):
            return httpx.Response(200, text=PAGE)
        if path.endswith("dataQuery.action"):
            return httpx.Response(200, text=CALENDAR)
        if "historyCourseGrade" in path:
            assert request.url.params["projectType"] == "MAJOR"
            return httpx.Response(200, text=GRADES)
        return httpx.Response(404, text="missing")

    client = _client(handler)
    try:
        posted = get_grades(client, 100)
        assert posted["ok"] is True
        assert posted["count"] == 1
        assert posted["grades"][0]["course_code"] == "1001"
        assert posted["summary"]["course_count"] == 1
        empty = get_grades(client, 362)
        assert empty["ok"] is True
        assert empty["count"] == 0
        assert empty["grades"] == []
        assert empty["summary"] is None
        unknown = get_grades(client, 1)
        assert unknown["ok"] is False
        assert unknown["error"]["code"] == "unknown_semester"
        assert unknown["error"]["retry"] is False
    finally:
        client.close()


TABLE = r"""
var unitCount = 13;
var teachers = [{id:1,name:"王胜春",lab:false}];
activity = new TaskActivity(actTeacherId.join(','),actTeacherName.join(','),"106824(22250110.01)","人工智能应用与开发(22250110.01)","3473","桃花坪四教102","01111111111111111000000000000000000000000000000000000",null,null,"","","");
index =0*unitCount+6;
index =0*unitCount+7;
"""

PLAN = """
<table class="gridtable">
<tr><th>课程代码</th><th>课程名称</th><th>学分</th></tr>
<tr><td>22250110</td><td>人工智能应用与开发</td><td>2.5</td></tr>
<tr><td>应修学分</td><td>应修学分</td><td>20</td></tr>
</table>
"""


def test_timetable_defaults_to_current_semester_and_attaches_plan_credits():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("myPlan.action"):
            return httpx.Response(200, text=PLAN)
        if path.endswith("courseTable.action"):
            return httpx.Response(200, text=TABLE)
        if path.endswith("courseTableForStd.action"):
            return httpx.Response(200, text=PAGE)
        if path.endswith("dataQuery.action"):
            return httpx.Response(200, text=CALENDAR)
        return httpx.Response(404, text=path)

    client = _client(handler)
    try:
        result = get_timetable(client, None, None)
    finally:
        client.close()
    assert result["ok"] is True
    assert result["semester_id"] == 362
    assert result["courses"][0]["course_name"] == "人工智能应用与开发"
    assert result["courses"][0]["credits"] == 2.5
    assert result["courses"][0]["meetings"][0]["weekday_name"] == "星期一"
    assert result["meetings"][0]["credits"] == 2.5
    assert all(course["course_name"] != "应修学分" for course in result["courses"])
    assert "notices" not in result


TWO_DAYS = r"""
var unitCount = 13;
var teachers = [{id:1,name:"王胜春",lab:false}];
activity = new TaskActivity(actTeacherId.join(','),actTeacherName.join(','),"106824(22250110.01)","人工智能应用与开发(22250110.01)","3473","桃花坪四教102","01111111111111111000000000000000000000000000000000000",null,null,"","","");
index =0*unitCount+6;
index =0*unitCount+7;
var teachers = [{id:2,name:"陈武阳",lab:false}];
activity = new TaskActivity(actTeacherId.join(','),actTeacherName.join(','),"106841(22250130.01)","智能终端应用(22250130.01)","3473","树达楼415","00000111111111111000000000000000000000000000000000000",null,null,"","","");
index =4*unitCount+0;
index =4*unitCount+1;
index =4*unitCount+2;
"""


def test_timetable_weekday_drops_other_days():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("myPlan.action"):
            return httpx.Response(200, text=PLAN)
        if path.endswith("courseTable.action"):
            return httpx.Response(200, text=TWO_DAYS)
        if path.endswith("courseTableForStd.action"):
            return httpx.Response(200, text=PAGE)
        if path.endswith("dataQuery.action"):
            return httpx.Response(200, text=CALENDAR)
        return httpx.Response(404, text=path)

    client = _client(handler)
    try:
        result = get_timetable(client, None, 5, 5)
    finally:
        client.close()
    assert result["ok"] is True
    assert result["weekday"] == 5
    assert result["count"] == 1
    meeting = result["meetings"][0]
    assert meeting["course_name"] == "智能终端应用"
    assert meeting["weekday_name"] == "星期五"
    assert meeting["start_section"] == 1
    assert meeting["end_section"] == 3
    assert meeting["room"] == "树达楼415"
    assert all(item["weekday"] == 5 for item in result["meetings"])
    assert all(item["course_name"] != "人工智能应用与开发" for item in result["meetings"])
    assert [course["course_name"] for course in result["courses"]] == ["智能终端应用"]


OVERVIEW = """
<table>
<tr><th>学年度</th><th>学期</th><th>门数</th><th>总学分</th><th>平均成绩</th><th>平均绩点</th></tr>
<tr><td>2025-2026</td><td>1</td><td>11</td><td>22</td><td>86.66</td><td>4</td></tr>
<tr><td>2025-2026</td><td>2</td><td>12</td><td>32</td><td>79.53</td><td>3.43</td></tr>
</table>
<table>
<tr>
<th>学年学期</th><th>课程代码</th><th>课程序号</th><th>课程名称</th><th>课程类别</th>
<th>学分</th><th>平时成绩</th><th>实验成绩</th><th>期中成绩</th><th>期末成绩</th>
<th>正考总评成绩</th><th>最终成绩</th><th>是否通过</th><th>绩点</th>
</tr>
<tr>
<td>2025-2026 1</td><td>1001</td><td>1001.01</td><td>示例课程甲</td><td>专业必修课</td>
<td>2</td><td></td><td></td><td></td><td></td><td></td><td>90</td><td>是</td><td>4</td>
</tr>
<tr>
<td>2025-2026 2</td><td>1002</td><td>1002.01</td><td>示例课程乙</td><td>通识教育选修</td>
<td>1</td><td></td><td></td><td></td><td></td><td></td><td>20</td><td>否</td><td>0</td>
</tr>
</table>
"""


def test_grade_overview_is_one_call_and_drops_passing_rows():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if "historyCourseGrade" in request.url.path:
            return httpx.Response(200, text=OVERVIEW)
        return httpx.Response(404, text=request.url.path)

    client = _client(handler)
    try:
        result = get_grade_overview(client)
    finally:
        client.close()
    assert seen == ["/eams/teach/grade/course/person!historyCourseGrade.action"]
    assert result["ok"] is True
    assert len(result["summaries"]) == 2
    first = result["summaries"][0]
    assert first["course_count"] == 11
    assert first["credits"] == 22
    assert first["average_score"] == "86.66"
    assert first["gpa"] == "4"
    assert result["count"] == 1
    assert result["failed"][0]["course_name"] == "示例课程乙"
    assert result["failed"][0]["passed"] is False
    names = [row["course_name"] for row in result["failed"]]
    assert "示例课程甲" not in names
