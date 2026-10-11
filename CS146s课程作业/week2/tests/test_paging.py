import httpx

from hunnu_mcp.client import HunnuClient
from hunnu_mcp.portal import read_paged

ONE = """
<table id="grid9" class="gridtable">
<thead><tr><th>名称</th></tr></thead>
<tbody><tr><td>示例教室</td></tr></tbody>
</table>
<script>page_grid9.pageInfo(1,1000,1);</script>
"""

FIRST = """
<table id="grid9" class="gridtable">
<thead><tr><th>名称</th></tr></thead>
<tbody><tr><td>示例甲</td></tr></tbody>
</table>
<script>page_grid9.pageInfo(1,1000,2);</script>
"""

SECOND = """
<table id="grid9" class="gridtable">
<thead><tr><th>名称</th></tr></thead>
<tbody><tr><td>示例乙</td></tr></tbody>
</table>
<script>page_grid9.pageInfo(2,1000,2);</script>
"""


def _client(handler) -> HunnuClient:
    return HunnuClient(
        [{"name": "JSESSIONID", "value": "test", "domain": "example.test", "path": "/"}],
        origin="https://example.test",
        transport=httpx.MockTransport(handler),
    )


def test_page_without_a_grid_is_not_a_finished_empty_search():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>不是查询表格</body></html>")

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is False
    assert document["tables"] == []


def test_header_only_grid_is_a_finished_empty_result():
    page = """
    <table id="grid9" class="gridtable">
    <thead><tr><th>名称</th></tr></thead>
    </table>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=page)

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is True
    assert document["tables"][0]["rows"] == []


def test_fast_click_is_not_finished():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="请不要过快点击")

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is False
    assert "请不要过快点击" in document["notices"]


def test_repeated_page_is_not_finished():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=FIRST)

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is False
    assert [row["名称"] for row in document["tables"][0]["rows"]] == ["示例甲"]


def test_full_page_without_a_total_reads_the_next(monkeypatch):
    monkeypatch.setattr("hunnu_mcp.portal._PAGE_SIZE", 2)
    pages = {
        "1": """
        <table id="grid9" class="gridtable"><thead><tr><th>名称</th></tr></thead>
        <tbody><tr><td>示例甲</td></tr><tr><td>示例乙</td></tr></tbody></table>
        """,
        "2": """
        <table id="grid9" class="gridtable"><thead><tr><th>名称</th></tr></thead>
        <tbody><tr><td>示例丙</td></tr></tbody></table>
        """,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=pages[request.url.params["pageNo"]])

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is True
    assert [row["名称"] for row in document["tables"][0]["rows"]] == ["示例甲", "示例乙", "示例丙"]


def test_one_page_is_complete_when_it_covers_the_total():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.params["pageSize"])
        return httpx.Response(200, text=ONE)

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is True
    assert seen == ["1000"]
    assert document["tables"][0]["rows"] == [{"名称": "示例教室"}]


def test_second_page_is_merged_until_the_total():
    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params["pageNo"]
        return httpx.Response(200, text=FIRST if page == "1" else SECOND)

    client = _client(handler)
    try:
        document, error, complete = read_paged(client, "/eams/example!search.action", {}, pause_s=0)
    finally:
        client.close()
    assert error is None
    assert complete is True
    assert [row["名称"] for row in document["tables"][0]["rows"]] == ["示例甲", "示例乙"]
