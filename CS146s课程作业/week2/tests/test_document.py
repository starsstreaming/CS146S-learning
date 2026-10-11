import httpx

from hunnu_mcp.client import HunnuClient
from hunnu_mcp.document import parse_document
from hunnu_mcp.portal import load_paths

PLAN = """
<table class="planTable">
<thead>
<tr>
<td rowspan="2" colspan="3">分类</td>
<td rowspan="2">课程代码</td>
<td rowspan="2">课程名称</td>
<td colspan="2">总学时分配</td>
<td rowspan="2">学分</td>
<td colspan="2">建议修读学期</td>
</tr>
<tr>
<td>讲授学时</td><td>实验学时</td><td>1</td><td>3</td>
</tr>
</thead>
<tr>
<td class="group" colspan="3">专业选修课</td>
<td>1001</td>
<td class="course">1 示例课程</td>
<td>16</td><td>32</td><td>2</td><td></td><td>√</td>
</tr>
</table>
"""

PROGRESS = """
<table class="formTable">
<tr><td>序号</td><td>课程序号</td><td>课程名称</td><td>要求学分</td><td>是否通过</td></tr>
<tr class="darkColumn"><td colspan="3">专业选修课</td><td>17</td><td>缺 17 学分</td></tr>
<tr><td>1</td><td>1001</td><td>示例课程</td><td>2</td><td>否</td></tr>
<tr class="darkColumn"><td colspan="3">任意选修课</td><td>0</td><td>是</td></tr>
</table>
"""

RECORD = """
<table class="infoTable">
<tr><td class="title">院系：</td><td>示例学院</td><td class="title">专业：</td><td>示例专业</td></tr>
</table>
<h2>当前没有开放申请！</h2>
<table class="gridtable">
<tr><th></th><th>课程名称</th><th>学分</th></tr>
<tr><td><input type="checkbox"></td><td>示例课</td><td>2</td></tr>
</table>
"""


FILTER = """
<table id="grid1" class="gridtable">
<thead>
<tr><th><input type="text" value=""></th><th><input type="text" value=""></th></tr>
<tr><th>课程序号</th><th>课程名称</th></tr>
</thead>
<tbody><tr><td>1001</td><td>示例课程</td></tr></tbody>
</table>
<script>page_grid1.pageInfo(1,1000,1);</script>
"""


SECTION = """
<table class="gridtable">
<tr><th>星期一</th><th>星期二</th></tr>
<tr><td>第一节</td><td></td></tr>
<tr><td>1001</td><td>示例课程</td></tr>
</table>
"""


def test_blank_section_row_is_not_a_course():
    rows = parse_document(SECTION)["tables"][0]["rows"]
    assert rows == [{"星期一": "1001", "星期二": "示例课程"}]


def test_filter_row_in_thead_is_not_a_result():
    table = parse_document(FILTER)["tables"][0]
    assert table["rows"] == [{"课程序号": "1001", "课程名称": "示例课程"}]
    assert table["total"] == 1


def test_plan_table_uses_leaf_headers_and_group():
    document = parse_document(PLAN)
    table = document["tables"][0]
    assert table["headers"][:4] == ["分类", "课程代码", "课程名称", "讲授学时"]
    assert "学期3" in table["headers"]
    row = table["rows"][0]
    assert row["分组"] == "专业选修课"
    assert row["课程代码"] == "1001"
    assert row["课程名称"] == "示例课程"
    assert row["学期3"] == "√"


def test_progress_section_and_record_fields():
    progress = parse_document(PROGRESS)
    rows = progress["tables"][0]["rows"]
    assert rows[0]["分组"] == "专业选修课"
    assert rows[0]["要求学分"] == "17"
    assert rows[1]["课程名称"] == "示例课程"
    record = parse_document(RECORD)
    assert record["fields"] == [
        {"label": "院系", "value": "示例学院"},
        {"label": "专业", "value": "示例专业"},
    ]
    assert record["notices"] == ["当前没有开放申请！"]
    assert record["tables"][0]["headers"] == ["课程名称", "学分"]
    assert record["tables"][0]["rows"] == [{"课程名称": "示例课", "学分": "2"}]


def test_plan_progress_keeps_gap_rollups_only():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("myPlanCompl.action"):
            return httpx.Response(200, text=PROGRESS)
        return httpx.Response(404, text=request.url.path)

    client = HunnuClient(
        [{"name": "JSESSIONID", "value": "test", "domain": "example.test", "path": "/"}],
        origin="https://example.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        result = load_paths(client, "计划完成情况", ("/eams/myPlanCompl.action",))
    finally:
        client.close()
    rows = result["tables"][0]["rows"]
    assert result["ok"] is True
    assert result["count"] == 1
    assert rows[0]["分组"] == "专业选修课"
    assert "缺" in rows[0]["是否通过"]
    assert all(row.get("分组") for row in rows)
    assert all("缺" in str(row.get("是否通过") or "") for row in rows)
    assert all(row.get("课程名称") != "示例课程" for row in rows)
    assert all(row.get("分组") != "任意选修课" for row in rows)
