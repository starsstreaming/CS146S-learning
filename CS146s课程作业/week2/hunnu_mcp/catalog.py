"""One read tool for each item in the 我的 and 公共服务 menus.

课表 and 我的成绩 stay hunnu_get_timetable and hunnu_get_grades.
These tools only read. They do not submit applications.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
from pydantic import Field

from hunnu_mcp.errors import auth_required, upstream_unavailable
from hunnu_mcp.portal import load_election, load_exams, load_paths
from hunnu_mcp.queries import get_room_usage, search_free_rooms, search_open_courses

READ = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}


@dataclass(frozen=True)
class Page:
    tool: str
    menu: str
    paths: tuple[str, ...] = ()
    semester: bool = False
    kind: str = "paths"


PAGES: tuple[Page, ...] = (
    Page("hunnu_get_plan", "培养计划", ("/eams/myPlan.action",)),
    Page("hunnu_get_plan_progress", "计划完成情况", ("/eams/myPlanCompl.action",)),
    Page("hunnu_get_course_selection", "选课", kind="election"),
    Page("hunnu_list_project_courses", "我的项目制课程", ("/eams/projectLessonStudent!search.action",)),
    Page(
        "hunnu_list_tutor_batches",
        "导师意向申请",
        ("/eams/tutor/stdApplyTutor.action", "/eams/tutor/stdApplyTutor!tutorBatchs.action"),
    ),
    Page("hunnu_get_tutor", "我的导师", ("/eams/tutor/myTutorOfStd.action",)),
    Page("hunnu_get_student_record", "学籍信息", ("/eams/stdDetail.action",)),
    Page("hunnu_get_proof_profile", "CA证明打印", ("/eams/caStdProofPrinter!search.action",)),
    Page("hunnu_get_term_registration", "学生学期注册", ("/eams/student/checkin/checkinForStd.action",)),
    Page(
        "hunnu_list_major_changes",
        "转专业申请(含基地班选拔)",
        ("/eams/stdApply.action", "/eams/stdApply!myApplies.action"),
    ),
    Page(
        "hunnu_list_major_shunts",
        "大类分流志愿填报",
        (
            "/eams/majorShuntStdApply.action",
            "/eams/majorShuntStdApply!myApplies.action",
            "/eams/majorShuntStdApply!myInfos.action",
        ),
    ),
    Page(
        "hunnu_list_status_changes",
        "学籍异动申请",
        ("/eams/stdAlterApply.action", "/eams/stdAlterApply!applyedList.action"),
    ),
    Page("hunnu_list_profile_edits", "个人信息核对与修改", ("/eams/stdInfoApply.action",)),
    Page("hunnu_get_graduation_check", "毕业确认", ("/eams/graduateStdConfirm.action",)),
    Page("hunnu_list_academic_alerts", "我的学业预警", ("/eams/alertInfoForStd!search.action",)),
    Page("hunnu_get_exams", "我的考试", ("/eams/stdExamTable.action",), semester=True, kind="exams"),
    Page(
        "hunnu_list_grade_corrections",
        "成绩更正申请",
        ("/eams/teach/grade/lesson/gradeCorrectApplyStd!search.action",),
    ),
    Page(
        "hunnu_list_course_type_exchanges",
        "成绩课程类别兑换申请",
        ("/eams/exchangeCourseTypeStdApply!myApplies.action",),
    ),
    Page("hunnu_list_defer_exams", "缓考申请", ("/eams/teach/grade/delay/stdDelayApply.action",)),
    Page("hunnu_list_makeup_exams", "补考报名/申请", ("/eams/stdMakeUpApply.action",)),
    Page(
        "hunnu_list_exemption_applies",
        "免修/免考申请",
        ("/eams/teach/grade/avoidTake/stdAvoidTakeApply!search.action?applyState=0",),
    ),
    Page(
        "hunnu_list_self_study",
        "自修申请",
        ("/eams/teach/grade/selfStudy/stdSelfTakeApply!search.action?applyState=0",),
    ),
    Page(
        "hunnu_list_external_exams",
        "校外等级考试报名",
        ("/eams/stdOtherExamSignUp.action", "/eams/stdOtherExamSignUp!configList.action"),
    ),
    Page(
        "hunnu_list_external_grade_confirms",
        "校外等级考试成绩认定申请",
        ("/eams/otherGradeConfirmApply!search.action?semester.id={semester}",),
        semester=True,
    ),
    Page("hunnu_list_talent_credits", "特长生学分抵充", ("/eams/stdGradeConver!search.action",)),
    Page(
        "hunnu_list_textbook_orders",
        "教材订购",
        (
            "/eams/book/process/stdTeachingBookOrder!search.action",
            "/eams/book/process/stdTeachingBookOrderSearch.action",
        ),
    ),
    Page("hunnu_get_postgrad_recommendation", "保研推免确认", ("/eams/recommendExemptionStd.action",)),
    Page(
        "hunnu_get_english_waiver",
        "大学英语免修确认",
        ("/eams/teach/grade/exempt/exemptTakeStdConfirm.action",),
    ),
    Page("hunnu_list_minor_signups", "辅修报名", ("/eams/stdMinorSignUp!search.action",)),
    Page("hunnu_list_micro_signups", "微专业报名", ("/eams/stdMicroSignUp!search.action",)),
    Page("hunnu_list_student_card_reissues", "学生证补办申请", ("/eams/stdCardApply!search.action",)),
    Page("hunnu_list_research_topics", "学生科研课题申报", ("/eams/research/researchTopicApply!search.action",)),
    Page(
        "hunnu_list_award_reports",
        "学生奖励成果申报",
        (
            "/eams/rewardResults/contestApplicationApply!search.action",
            "/eams/rewardResults/scientificResearchApply!search.action",
        ),
    ),
    Page("hunnu_get_guardian_info", "父母(监护人)信息核准补录", ("/eams/stdInfoSupplement!edit.action",)),
    Page("hunnu_list_room_bookings", "教室借用", ("/eams/classroom/apply/std-activity!search.action",)),
    Page("hunnu_list_messages", "站内消息", ("/eams/systemMessageForStd!search.action",)),
)

SEARCH_TOOLS = (
    "hunnu_search_free_rooms",
    "hunnu_search_open_courses",
    "hunnu_get_room_usage",
)


def _describe(page: Page) -> str:
    if page.menu == "计划完成情况":
        return (
            "Read `计划完成情况`. Returns only rollup rows whose 是否通过 contains 缺: "
            "分组, 要求学分, 实修学分, and that gap. "
            "Satisfied groups and individual course rows are omitted. This tool never opens a browser."
        )
    semester = ""
    if page.semester:
        semester = " semester_id comes from hunnu_list_semesters; omit it for the current semester."
    return (
        f"Read `{page.menu}`. Returns notices, fields, and tables. "
        "Table keys are the campus column titles. "
        "A notice with count 0 means that item is closed or has no rows."
        f"{semester} This tool never opens a browser."
    )


def _run(open_client: Callable[[], tuple[Any, dict[str, Any] | None]], call: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
    client, error = open_client()
    if error or client is None:
        return error or auth_required()
    try:
        return call(client)
    except httpx.HTTPError as exc:
        return upstream_unavailable(str(exc) or exc.__class__.__name__)
    finally:
        client.close()


def _register_page(mcp: Any, open_client: Callable[..., Any], page: Page) -> None:
    def invoke(client: Any, semester_id: int | None = None) -> dict[str, Any]:
        if page.kind == "election":
            return load_election(client)
        if page.kind == "exams":
            return load_exams(client, semester_id)
        return load_paths(
            client,
            page.menu,
            page.paths,
            semester_id=semester_id if page.semester else None,
        )

    if page.semester:
        def tool(
            semester_id: Annotated[
                int | None,
                Field(description="semester_id from hunnu_list_semesters. Omit for the current semester."),
            ] = None,
        ) -> dict[str, Any]:
            return _run(open_client, lambda client: invoke(client, semester_id))
    else:
        def tool() -> dict[str, Any]:
            return _run(open_client, lambda client: invoke(client, None))

    tool.__name__ = page.tool
    tool.__doc__ = _describe(page)
    mcp.tool(annotations=READ)(tool)


def register_menu_tools(mcp: Any, open_client: Callable[..., Any]) -> None:
    for page in PAGES:
        _register_page(mcp, open_client, page)

    def hunnu_search_free_rooms(
        date: Annotated[str, Field(description="Day the room must be free, YYYY-MM-DD.")],
        start_time: Annotated[str, Field(description="Start clock time HH:mm.")],
        end_time: Annotated[str, Field(description="End clock time HH:mm.")],
        end_date: Annotated[str | None, Field(description="Last day YYYY-MM-DD. Defaults to date.")] = None,
        campus: Annotated[str | None, Field(description="Campus name such as 桃花坪校区. Omit for every campus.")] = None,
        building: Annotated[str | None, Field(description="Building name. Omit for every building.")] = None,
        room_type: Annotated[str | None, Field(description="Room type such as 多媒体教室. Omit for every type.")] = None,
        min_seats: Annotated[int | None, Field(ge=1, description="Minimum seats.")] = None,
    ) -> dict[str, Any]:
        """Search `空闲教室查询` for whole classrooms free between two clock times.

        seat_level is false. This is not a library seat map and does not say who sits nearby.
        An empty campus plus building result includes buildings: names of buildings that do have a free classroom.
        campus, building, and room_type are names from the campus form.
        unknown_filter lists the names that form actually offers.
        This tool never opens a browser.
        """
        return _run(
            open_client,
            lambda client: search_free_rooms(
                client,
                date=date,
                start_time=start_time,
                end_time=end_time,
                end_date=end_date,
                campus=campus,
                building=building,
                room_type=room_type,
                min_seats=min_seats,
            ),
        )

    def hunnu_search_open_courses(
        semester_id: Annotated[
            int | None,
            Field(description="semester_id from hunnu_list_semesters. Omit for the current semester."),
        ] = None,
        course_name: Annotated[str | None, Field(description="Course name, or part of it.")] = None,
        lesson_no: Annotated[str | None, Field(description="Lesson number such as 22250129.")] = None,
        teacher: Annotated[str | None, Field(description="Teacher name.")] = None,
    ) -> dict[str, Any]:
        """Search `全校开课查询`, the public lesson catalog.

        Do not use this for the logged-in student's own credits or timetable. Call hunnu_get_timetable.
        A name, lesson number, or teacher that matches nothing returns count 0 and drops the unfiltered list.
        This tool never opens a browser.
        """
        return _run(
            open_client,
            lambda client: search_open_courses(
                client,
                semester_id=semester_id,
                course_name=course_name,
                lesson_no=lesson_no,
                teacher=teacher,
            ),
        )

    def hunnu_get_room_usage(
        semester_id: Annotated[
            int | None,
            Field(description="semester_id from hunnu_list_semesters. Omit for the current semester."),
        ] = None,
        campus: Annotated[str | None, Field(description="Campus name. Omit for every campus.")] = None,
        building: Annotated[str | None, Field(description="Building name. Omit for every building.")] = None,
        room: Annotated[str | None, Field(description="Room name. When one row matches, its occupancy board is included.")] = None,
    ) -> dict[str, Any]:
        """Read `教室使用情况` for whole-classroom bookings.

        seat_level is false. Not library seats, and not whether a neighboring seat is empty.
        An empty campus plus building result includes buildings, names only. Do not fetch the campus room list yourself.
        Without room, returns the room list for the semester.
        With a room name that matches one row, also returns that room's board.
        This tool never opens a browser.
        """
        return _run(
            open_client,
            lambda client: get_room_usage(
                client,
                semester_id=semester_id,
                campus=campus,
                building=building,
                room=room,
            ),
        )

    for tool in (hunnu_search_free_rooms, hunnu_search_open_courses, hunnu_get_room_usage):
        mcp.tool(annotations=READ)(tool)
