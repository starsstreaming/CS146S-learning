"""Structured tool errors. These dicts go back to the model as data.

retry=False means do not call the same tool again with the same arguments.
retry=True means a later identical call may succeed.
"""

from __future__ import annotations

from typing import Any, Literal


ErrorCode = Literal[
    "auth_required",
    "auth_expired",
    "upstream_unavailable",
    "unknown_semester",
    "parse_failed",
    "invalid_argument",
    "unknown_filter",
]


def tool_error(code: ErrorCode, message: str, *, retry: bool, next_step: str) -> dict[str, Any]:
    """Shape every failure the same way so the agent can branch on `code`."""
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "retry": retry,
            "next_step": next_step,
        },
    }


def auth_required() -> dict[str, Any]:
    return tool_error(
        "auth_required",
        "No cached EAMS session. The school SSO has not been completed on this machine.",
        retry=False,
        next_step=(
            "Ask the user to run `poetry run python -m hunnu_mcp login` in a terminal "
            "under week2/, finish the campus login in the browser window, then call "
            "hunnu_auth_status again. Do not retry this tool until they confirm login."
        ),
    )


def auth_expired() -> dict[str, Any]:
    return tool_error(
        "auth_expired",
        "The cached EAMS session is missing, unreadable, or the gateway bounced us to SSO.",
        retry=False,
        next_step=(
            "Ask the user to run `poetry run python -m hunnu_mcp login` in a terminal. "
            "This tool never opens a browser. After they finish SSO, call hunnu_auth_status."
        ),
    )


def unknown_semester(semester_id: int) -> dict[str, Any]:
    return tool_error(
        "unknown_semester",
        f"semester_id {semester_id} is not in the EAMS semester calendar.",
        retry=False,
        next_step="Call hunnu_list_semesters and pass one of its semester_id values.",
    )


def parse_failed(what: str) -> dict[str, Any]:
    return tool_error(
        "parse_failed",
        f"The EAMS HTML for {what} did not match the expected page script.",
        retry=False,
        next_step="Stop. The campus page markup changed; do not retry the same call.",
    )


def invalid_argument(message: str) -> dict[str, Any]:
    return tool_error(
        "invalid_argument",
        message,
        retry=False,
        next_step="Fix the argument and call the tool again. Do not repeat the same values.",
    )


def unknown_filter(kind: str, value: str, options: list[str]) -> dict[str, Any]:
    shown = "、".join(options[:30])
    return tool_error(
        "unknown_filter",
        f"{kind} {value!r} is not on the campus form. Known values: {shown}",
        retry=False,
        next_step=f"Call again with one {kind} from the message, or omit it.",
    )


def upstream_unavailable(detail: str) -> dict[str, Any]:
    return tool_error(
        "upstream_unavailable",
        f"The EAMS origin could not be reached: {detail}",
        retry=True,
        next_step="Wait a few seconds and call the same tool again. If it still fails, stop.",
    )
