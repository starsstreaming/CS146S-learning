# Week 1 抓包：方案 A（mitmproxy 中继在 CC Switch 前面）

链路：`claude` → `mitmweb 127.0.0.1:58888` → `CC Switch 127.0.0.1:15721` → 上游

## 一次性准备

1. 装 mitmproxy（Windows 安装器，会把 `mitmweb` 放进 PATH）：<https://mitmproxy.org/>
2. 确认 `mitmweb --version` 能跑。
3. CC Switch 保持运行（它占用 15721，是第二跳的落点）。

## 每次抓包

```powershell
# 1) 起中继（保持这个窗口开着）
.\start-proxy.ps1

# 2) 另开一个窗口，确认 58888 在听
Get-NetTCPConnection -LocalPort 58888 -State Listen

# 3) 在“你的 scratch 仓库”里跑 claude（不是 week1，见下面的坑）
```

检查界面在 <http://localhost:8081>；capture 写在 `C:\Users\29468\cs146s-capture\session.flows`（**仓库之外**，不会进 git）。

## 验证项目级 base URL 真的生效了

两种可能都会出现在 mitmweb 里，一眼就能分辨是谁被覆盖了：

- 58888 收到 `POST /v1/messages` → 项目级 `.claude/settings.json` 覆盖成功，抓包正常。
- 只有 CC Switch 自己的日志在动、mitmweb 空的 → 项目级没覆盖成功，改成在启动 claude 前设环境变量：`$env:ANTHROPIC_BASE_URL='http://127.0.0.1:58888'`。

不想开 claude 也能先做链路体检：

```powershell
curl.exe -s -o NUL -w "%{http_code}`n" -X POST http://127.0.0.1:58888/v1/messages `
  -H "content-type: application/json" -H "x-api-key: dummy" `
  -d '{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":1,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}'
```

返回 2xx/4xx 都算链路通（4xx 是假 key 造成的），`Connection refused` 才是中继没起。

## 坑

- **不要让 week1 当 Part I 的抓包仓库。** assignment：`Your own repo: a scratch project, not this one`。week1 只放这份配置当模板，把它复制到 scratch 仓库的 `.claude/` 下再跑会话。
- **顺序不能反**：先起 `start-proxy.ps1` 再进目录跑 `claude`。反代没起时进这个目录，就会复现 `Connection refused (ECONNREFUSED)`。
- **改完 `.claude/settings.json` 要重开会话**，env 是启动时读的。
- 抓到的请求头里有 `x-api-key` / `authorization`，**永远不要贴进 writeup**；request body 里也可能有 agent 读过的 `.env` 内容，引用前先检查 tool result。

## 收尾（assignment 第 54 / 119 行）

```powershell
# 停掉 mitmweb（Ctrl+C 或直接关窗口），然后：
Remove-Item "C:\Users\29468\Desktop\cs146s\CS146s课程作业\week1\.claude\settings.json"
Remove-Item -Recurse "C:\Users\29468\Desktop\cs146s\CS146s课程作业\week1\.claude"
```

`session.flows` 和 `/tmp` 之外的任何 capture 都不要提交；`Desktop\cs146s\.gitignore` 已经忽略 `.claude/`、`session.flows`、`*.flows` 作为兜底。
