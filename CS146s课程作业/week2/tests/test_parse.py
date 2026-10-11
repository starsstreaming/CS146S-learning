from hunnu_mcp.parse import current_semester_id, parse_grade_page, parse_meetings, parse_semesters, std_ids

PAGE = """
jQuery("#semesterBar").semesterCalendar({empty:"false",onChange:"",value:"362"},"searchTable()");
bg.form.addInput(form,"ids","386414");
bg.form.addInput(form,"ids","5561");
"""

CALENDAR = """
semesters:{y0:[{id:11,schoolYear:"2007-2008",name:"1"},{id:362,schoolYear:"2026-2027",name:"1"}]}
"""

TABLE = r"""
var unitCount = 13;
var teachers = [{id:1,name:"王胜春",lab:false}];
activity = new TaskActivity(actTeacherId.join(','),actTeacherName.join(','),"106824(22250110.01)","人工智能应用与开发(22250110.01)","3473","桃花坪四教102","01111111111111111000000000000000000000000000000000000",null,null,"","","");
index =0*unitCount+6;
index =0*unitCount+7;
var teachers = [{id:2,name:"陈武阳",lab:false}];
activity = new TaskActivity(actTeacherId.join(','),actTeacherName.join(','),"106841(22250130.01)","智能终端应用(22250130.01)","","","00000111111111111000000000000000000000000000000000000",null,null,"","","");
index =4*unitCount+1;
index =4*unitCount+2;
"""


def test_semester_and_student_ids():
    assert current_semester_id(PAGE) == 362
    assert std_ids(PAGE) == "386414"
    rows = parse_semesters(CALENDAR, current_semester_id=362)
    current = [row for row in rows if row["current"]]
    assert current[0]["label"] == "2026-2027 第1学期"
    assert current[0]["semester_id"] == 362


def test_meetings_merge_sections_and_weeks():
    meetings = parse_meetings(TABLE)
    assert len(meetings) == 2
    first = meetings[0]
    assert first["course_name"] == "人工智能应用与开发"
    assert first["lesson_id"] == "106824"
    assert first["weekday"] == 1
    assert first["weekday_name"] == "星期一"
    assert first["start_section"] == 7
    assert first["end_section"] == 8
    assert first["weeks"] == list(range(1, 17))
    assert first["room"] == "桃花坪四教102"
    assert first["teachers"] == ["王胜春"]
    second = meetings[1]
    assert second["weekday_name"] == "星期五"
    assert second["weeks"][0] == 5
    assert second["start_section"] == 2
    assert second["end_section"] == 3


GRADES = """
<table class="gridtable">
<tr><th>学年度</th><th>学期</th><th>门数</th><th>总学分</th><th>平均成绩</th><th>平均绩点</th></tr>
<tr><td>2025-2026</td><td>1</td><td>1</td><td>2</td><td>90</td><td>4</td></tr>
<tr><th colspan="2">在校汇总</th><th>1</th><th>2</th><th>90</th><th>4</th></tr>
</table>
<table class="gridtable">
<tr>
<th>学年学期</th><th>课程代码</th><th>课程序号</th><th>课程名称</th><th>课程类别</th>
<th>学分</th><th>平时成绩</th><th>实验成绩</th><th>期中成绩</th><th>期末成绩</th>
<th>正考总评成绩</th><th>最终成绩</th><th>是否通过</th><th>绩点</th>
</tr>
<tr>
<td>2025-2026 1</td><td>1001</td><td>1001.01</td><td>示例课程甲
</td><td>专业必修课</td><td>2</td><td>80</td><td></td><td></td><td>90</td>
<td>88</td><td>88</td><td>是</td><td>3.7</td>
</tr>
<tr>
<td>2024-2025 2</td><td>1002</td><td>1002.01</td><td>示例课程乙</td><td>选修</td><td>1.5</td>
<td></td><td></td><td></td><td></td><td></td><td>不及格</td><td>否</td><td>0</td>
</tr>
</table>
"""


def test_grade_page_keeps_text_scores_and_skips_rollup():
    parsed = parse_grade_page(GRADES)
    assert parsed is not None
    assert len(parsed["summaries"]) == 1
    assert parsed["summaries"][0]["term_label"] == "2025-2026 1"
    assert parsed["summaries"][0]["course_count"] == 1
    assert len(parsed["grades"]) == 2
    first = parsed["grades"][0]
    assert first["course_name"] == "示例课程甲"
    assert first["credits"] == 2
    assert first["lab_score"] is None
    assert first["score"] == "88"
    assert first["passed"] is True
    second = parsed["grades"][1]
    assert second["credits"] == 1.5
    assert second["score"] == "不及格"
    assert second["passed"] is False


def test_grade_page_without_grid_is_none():
    assert parse_grade_page("<table><tr><td>空</td></tr></table>") is None
