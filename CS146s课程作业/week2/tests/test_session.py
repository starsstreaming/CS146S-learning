from __future__ import annotations

import json

from hunnu_mcp.client import looks_like_home, looks_like_login
from hunnu_mcp.session import load_cookies, save_cookies


def test_save_and_load_cookies(tmp_path, monkeypatch):
    monkeypatch.setenv("HUNNU_SESSION_PATH", str(tmp_path / "session.json"))
    cookies = [{"name": "JSESSIONID", "value": "abc", "domain": "jwglnew.hunnu.edu.cn", "path": "/eams"}]
    path = save_cookies(cookies)
    assert path.is_file()
    loaded = load_cookies()
    assert loaded == cookies
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert "saved_at" in raw
    assert "abc" in path.read_text(encoding="utf-8")


def test_missing_session_is_none(tmp_path, monkeypatch):
    monkeypatch.setenv("HUNNU_SESSION_PATH", str(tmp_path / "missing.json"))
    assert load_cookies() is None


def test_corrupt_session_is_none(tmp_path, monkeypatch):
    path = tmp_path / "session.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv("HUNNU_SESSION_PATH", str(path))
    assert load_cookies() is None


def test_login_wall_detection():
    assert looks_like_login("https://login.hunnu.edu.cn/Login?client_id=x", "")
    assert looks_like_login("https://vweb.hunnu.edu.cn/wengine-auth/login", "<html>")
    assert looks_like_login("https://jwglnew.hunnu.edu.cn/eams/x", "统一身份认证")


def test_home_detection():
    assert looks_like_home(
        "https://jwglnew.hunnu.edu.cn/eams/homeExt.action",
        "<title>湖南师范大学本科教学管理平台</title>",
    )
    assert looks_like_home(
        "https://jwglnew.hunnu.edu.cn/eams/homeExt.action",
        "您好！同学 2026-2027 第 1 学期 第 5 教学周",
    )
