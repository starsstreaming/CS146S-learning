# CS146S 学习笔记与实践

记录 [CS146S: The Modern Software Developer](https://themodernsoftware.dev) 的学习过程：中文课程笔记、课堂资料，以及编程智能体与 MCP 的作业实践。

目前整理了 **第 1–6 节课程笔记**，作业目录覆盖 **Week 1–2**。可以从下面的课程导航开始阅读，也可以直接进入作业目录运行实践代码。

这是个人学习仓库。中文笔记包含个人理解与延伸资料，课程安排、要求和原始材料以课程方发布的内容为准。

## 课程笔记

按 2026 秋季实际上课顺序编号。课程在周二、周四上课，9 月 22 日开课。文件名统一为 `CS146S_第NN节课_日期_主题.md`，在仓库里会按节次排好。

| 节次 | 日期 | 主题 | 笔记 |
| --- | --- | --- | --- |
| 01 | 2026-09-22 周二 | 现代软件开发者、最小可用编程 Agent | [阅读笔记](<CS146S_第01节课_2026-09-22_现代软件开发者与最小可用编程Agent.md>) |
| 02 | 2026-09-24 周四 | 编码智能体解剖：系统提示、工具、配置、计划与上下文压缩 | [阅读笔记](<CS146S_第02节课_2026-09-24_现代编码智能体解剖.md>) |
| 03 | 2026-09-29 周二 | 高级提示与上下文工程 | [阅读笔记](<CS146S_第03节课_2026-09-29_高级提示与上下文工程.md>) |
| 04 | 2026-10-01 周四 | MCP、工具调用与 Agent Skills | [阅读笔记](<CS146S_第04节课_2026-10-01_MCP工具调用与AgentSkills.md>) |
| 05 | 2026-10-06 周二 | Agent Skills 实战与最佳实践 | [阅读笔记](<CS146S_第05节课_2026-10-06_AgentSkills实战与最佳实践.md>) |
| 06 | 2026-10-08 周四 | 常驻智能体如何工作（Lee Robinson 嘉宾讲座） | [阅读笔记](<CS146S_第06节课_2026-10-08_常驻智能体工作原理.md>) |

建议按顺序阅读：先理解智能体的工具循环，再看真实产品的组成、上下文组织，以及 MCP 和 Skills 如何接入实际工作。

## 课堂资料

[课堂资料目录](<CS146S The Modern Software Developer/>) 按日期保留第 1、2 节的课件、示例与中文补充材料。

- 第 1 节：[课件 PDF](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/官方资源/Lecture 9_22_26.pdf>) · [最小编程 Agent 示例](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/官方资源/coding_agent_from_scratch_lecture.py>) · [逐段拆解](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/个人补充/blog_coding_agent.md>)
- 第 2 节：[课件 PDF](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/Lecture 9_24_26.pdf>) · [配置与提示材料](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/>) · [延伸阅读](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/reading.md>)

## 作业实践

作业原文保存在各周的 `assignment.md`，`writeup.md` 保留作答提纲；代码与运行说明另列如下。

| 周次 | 主题 | 当前内容 | 入口 |
| --- | --- | --- | --- |
| Week 1 | 捕获并分析 Claude Code 会话 | Windows 下的 mitmproxy / CC Switch 中继脚本与抓包说明 | [作业要求](CS146s课程作业/week1/assignment.md) · [抓包配置](CS146s课程作业/week1/CAPTURE-SETUP.md) · [作答提纲](CS146s课程作业/week1/writeup.md) |
| Week 2 | MCP Server 与认证 | 湖南师范大学教务系统的 Hunnu EAMS MCP 实现、配置模板与测试 | [作业要求](CS146s课程作业/week2/assignment.md) · [运行说明](CS146s课程作业/week2/README.md) · [作答提纲](CS146s课程作业/week2/writeup.md) |

### Week 2：Hunnu EAMS MCP

通过 stdio 向智能体提供只读教务工具，支持课表、成绩、培养计划，以及空教室和开课查询。每位使用者需要在自己的电脑上完成学校 SSO 登录，服务随后使用本地缓存的会话。

使用 Python 3.12 和 Poetry，在仓库根目录执行：

```bash
cd CS146s课程作业
poetry install
poetry run playwright install chromium
poetry run pytest -q

cd week2
poetry run python -m hunnu_mcp login
poetry run python -m hunnu_mcp
```

将 [`.mcp.json.example`](CS146s课程作业/week2/.mcp.json.example) 复制为 `.mcp.json`，把 `cwd` 改为本机 `week2` 目录的绝对路径，再交给支持 MCP 的智能体客户端加载。详细说明见 [Week 2 README](CS146s课程作业/week2/README.md)；基础 Python 环境配置见 [作业目录 README](CS146s课程作业/README.md)。

工具调用不会自动打开登录浏览器。遇到 `auth_required` 或 `auth_expired` 时，在 `week2` 目录重新运行登录命令。

### 本地配置与数据

抓包内容可能包含 API 密钥、请求正文和个人信息；教务会话缓存也属于敏感数据。不要提交 `.env`、`.mcp.json`、`.claude/`、`*.flows` 或会话缓存，仓库已有相应忽略规则。公开配置使用 `.example` 模板。

## 仓库结构

```text
.
├── README.md
├── CS146S_第01节课_2026-09-22_….md
├── CS146S_第02节课_2026-09-24_….md
├── CS146S_第03节课_2026-09-29_高级提示与上下文工程.md
├── CS146S_第04节课_2026-10-01_MCP工具调用与AgentSkills.md
├── CS146S_第05节课_2026-10-06_AgentSkills实战与最佳实践.md
├── CS146S_第06节课_2026-10-08_常驻智能体工作原理.md
├── CS146S The Modern Software Developer/
│   ├── CS146S_第01节课_2026-09-22/
│   └── CS146S_第02节课_2026-09-24/
└── CS146s课程作业/
    ├── pyproject.toml
    ├── poetry.lock
    ├── week1/                 作业原文、抓包说明与中继脚本
    └── week2/
        ├── README.md          MCP 运行说明
        ├── hunnu_mcp/         MCP 服务实现
        └── tests/             解析、会话与 MCP 协议测试
```

## 来源与版权

- [课程页面](https://themodernsoftware.dev)
- [作业上游仓库](https://github.com/mihail911/modern-software-dev-assignments)

课件、课堂材料和作业原文的版权归课程方及各自作者。个人笔记仅供学习参考，发现理解偏差或链接问题欢迎通过 Issue 指出。
