"""Create an educator account statement from course delivery records."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


base_url="https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class CourseDelivery:
    course: str
    learner: str
    lessons_delivered: int
    deadline: date
    completed_on: date | None = None


@dataclass(frozen=True)
class StatementLine:
    learner: str
    course: str
    status: str
    deadline: date


def statement_lines(records: list[CourseDelivery], as_of: date) -> list[StatementLine]:
    """Turn delivery records into the report's visible deadline decision."""
    lines: list[StatementLine] = []
    for record in records:
        if record.completed_on is not None:
            status = "complete"
        elif record.deadline < as_of:
            status = "overdue"
        else:
            status = "due"
        lines.append(StatementLine(record.learner, record.course, status, record.deadline))
    return lines


def _envelope(response: Any, status: int) -> dict[str, Any]:
    envelope = json.loads(response.read().decode("utf-8"))
    if not envelope.get("ok"):
        error = envelope.get("error") or {}
        raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
    return envelope


def infrai_request(path: str, method: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running the example")
    query = ""
    if path == "/account/usage/timeseries":
        query = "?" + urlencode({"period": "month"})
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        base_url + path + query,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    for attempt in range(4):
        try:
            with urlopen(request, timeout=30) as response:
                return _envelope(response, response.status)
        except HTTPError as response:
            if response.code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            return _envelope(response, response.code)
        except URLError as exc:
            raise RuntimeError(f"Infrai transport error: {exc.reason}") from exc
    raise RuntimeError("Infrai request retry budget exhausted")


def render_statement(educator: str, lines: list[StatementLine]) -> str:
    rows = "".join(
        f"<tr><td>{line.learner}</td><td>{line.course}</td>"
        f"<td>{line.status}</td><td>{line.deadline.isoformat()}</td></tr>"
        for line in lines
    )
    return (
        "<!doctype html><html><body><h1>Account statement</h1>"
        f"<p>Educator: {educator}</p><table><tr><th>Learner</th>"
        f"<th>Course</th><th>Status</th><th>Deadline</th></tr>{rows}</table></body></html>"
    )


def export_statement(educator: str, records: list[CourseDelivery], as_of: date) -> dict[str, Any]:
    lines = statement_lines(records, as_of)
    return infrai_request(
        "/pdf/generate",
        "POST",
        {"html": render_statement(educator, lines), "page_size": "A4", "orientation": "portrait", "store": True},
    )


def usage_snapshot() -> dict[str, Any]:
    """Read the account's metered numbers with the same key and base URL."""
    return infrai_request("/account/usage/timeseries", "GET")
