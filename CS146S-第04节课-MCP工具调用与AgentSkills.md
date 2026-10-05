# CS146S 第 10 讲学习笔记：MCP、工具调用与 Agent Skills——让模型连上真实世界

> **课程**：Stanford CS146S *The Modern Software Developer*（Fall 2026，Mihail Eric）
> **讲次**：Lecture 10（2026-10-01）—— *MCP, Tool-calling, and Beyond*
> **补充材料**：Cloudflare《Scaling MCP adoption: Our reference architecture for enterprise MCP》、MCP 官方规范、Anthropic Agent Skills 文档
> **阅读时长**：约 45 分钟

---

## 目录

- [0. 一页速览](#0-一页速览)
- [1. 术语表](#1-术语表)
- [2. 为什么需要工具调用：静态知识 vs 动态数据](#2-为什么需要工具调用静态知识-vs-动态数据)
- [3. 工具调用（Tool Calling）的底层原理](#3-工具调用tool-calling的底层原理)
- [4. MCP 是什么：从 M×N 到 M+N](#4-mcp-是什么从-mn-到-mn)
- [5. MCP 深入：角色、原语、流程与传输](#5-mcp-深入角色原语流程与传输)
- [6. 动手：十几行代码写一个 MCP Server](#6-动手十几行代码写一个-mcp-server)
- [7. 如何设计好的 MCP Server（方案一）：为结果而设计](#7-如何设计好的-mcp-server方案一为结果而设计)
- [8. 如何设计好的 MCP Server（方案二）：Search + Execute / Code Mode](#8-如何设计好的-mcp-server方案二search--execute--code-mode)
- [9. 企业级 MCP 架构：Cloudflare 参考架构精读](#9-企业级-mcp-架构cloudflare-参考架构精读)
- [10. Agent Skills：按需加载的能力包](#10-agent-skills按需加载的能力包)
- [11. API vs MCP vs Skills：三者到底什么关系](#11-api-vs-mcp-vs-skills三者到底什么关系)
- [12. 自测题](#12-自测题)
- [13. 参考资料](#13-参考资料)

---

## 0. 一页速览

> **一句话总结**：LLM 的知识是静态的，要让它干实事就得"接工具"。**MCP** 是接工具的**通用插座标准**；**Code Mode** 是在工具爆炸时省 token 的新设计；**Agent Skills** 则是教 agent "怎么把一件事做完"的**可复用操作手册**。

| #   | 核心结论                                                      |
| --- | --------------------------------------------------------- |
| 1   | MCP = 把工具暴露给 LLM 的**标准格式**，基于 **JSON-RPC 2.0**            |
| 2   | 它把"每个 AI 应用 × 每个工具都写一个连接器"（M×N）变成"各自实现一次协议"（M+N）          |
| 3   | 流程五步：问 → `tools/list` 拿工具 → 模型选工具填参数 → server 执行 → 结果回传   |
| 4   | **MCP 不是 REST API 的包装器**：要为"结果"设计工具，而不是为"操作"设计            |
| 5   | 工具太多时只暴露 `search` + `execute` 两个工具，让模型写代码调用，token 可降 90%+ |
| 6   | 企业落地要解决：鉴权、发现、审计、DLP、成本、影子 MCP                            |
| 7   | **API 给开发者调，MCP 给 agent 调，Skills 教 agent 怎么组合着调**         |

---

## 1. 术语表

| 术语              | 英文                                           | 人话解释                                                                |
| --------------- | -------------------------------------------- | ------------------------------------------------------------------- |
| 工具调用 / 函数调用     | Tool Calling / Function Calling              | 模型不直接执行动作，而是**输出一段结构化的"我想调用某某函数、参数是…"**，由宿主程序真正去执行                  |
| MCP             | Model Context Protocol                       | 模型上下文协议。Anthropic 于 2024 年 11 月开源，现已是业界通用的"AI 接工具"标准                |
| JSON-RPC        | JSON Remote Procedure Call                   | 用 JSON 表示"远程调用某个方法"的轻量协议。每条消息有 `jsonrpc`、`id`、`method`、`params` 等字段 |
| JSON Schema     | —                                            | 用 JSON 描述"一段 JSON 应该长什么样"的规范，MCP 用它定义工具参数                           |
| 宿主              | Host                                         | 用户直接使用的 AI 应用，如 Claude Desktop、Cursor、Claude Code                   |
| 客户端             | MCP Client                                   | 嵌在宿主里的协议库，**每连接一个 server 就维持一个有状态会话**                               |
| 服务器             | MCP Server                                   | 挡在某个工具/数据源前面的轻量包装层，把它的能力按 MCP 格式暴露出来                                |
| stdio           | Standard I/O                                 | 标准输入输出。本地 MCP server 作为子进程运行，通过管道收发消息                               |
| Streamable HTTP | —                                            | MCP 的远程传输方式，通过 HTTP POST 收发，必要时用 SSE 流式推送                           |
| SSE             | Server-Sent Events                           | 服务器向浏览器/客户端单向持续推送事件的 HTTP 技术                                        |
| OAuth           | Open Authorization                           | 一种授权标准：用户授权第三方应用以自己的身份访问资源，而不必交出密码                                  |
| SSO / MFA       | Single Sign-On / Multi-Factor Authentication | 单点登录（一次登录访问多个系统）/ 多因素认证（密码 + 手机验证码等）                                |
| ZTNA            | Zero Trust Network Access                    | 零信任网络访问：默认谁都不信，每次访问都校验身份和设备                                         |
| DLP             | Data Loss Prevention                         | 数据防泄漏：检测并阻止敏感数据（如身份证号、密钥）流向不该去的地方                                   |
| PII             | Personally Identifiable Information          | 个人身份信息，如姓名、电话、邮箱                                                    |
| WAF             | Web Application Firewall                     | Web 应用防火墙，检查进入网站的 HTTP 流量并拦截攻击                                      |
| 提示注入            | Prompt Injection                             | 攻击者把恶意指令藏在网页、邮件、工具返回内容里，诱导模型执行非预期操作                                 |
| 影子 MCP          | Shadow MCP                                   | 员工私自使用、未经 IT 审批的 MCP server（类比"影子 IT"）                              |
| 渐进式披露           | Progressive Disclosure                       | 先只给最少信息，需要时再逐步展开细节，用来节省上下文                                          |
| 沙箱              | Sandbox                                      | 隔离的执行环境，代码在里面跑出问题也不会影响外部系统                                          |

---

## 2. 为什么需要工具调用：静态知识 vs 动态数据

> 课件第 4 页：*Why*

- LLM 拥有**海量但静态**的世界知识——只有重新训练才会更新（有"知识截止日期"）；
- 要构建**完全自主**的系统，就必须有**稳健的方式把动态数据喂进去**。

举几个模型"天生做不到"的事：

| 需求 | 为什么模型自己做不到 | 需要什么工具 |
|---|---|---|
| "总结我今天收到 Jack 的邮件" | 训练数据里没有你的邮箱 | 邮箱 API |
| "这个 bug 在 main 分支修了吗" | 代码库每天在变 | Git / GitHub |
| "现在 BTC 多少钱" | 实时数据 | 行情接口 |
| "帮我把这张工单改成已完成" | 需要**执行动作**，不只是读取 | Jira API |

所以工具既是"**眼睛**"（读取动态数据），也是"**手**"（对外部世界执行动作）。

---

## 3. 工具调用（Tool Calling）的底层原理

理解 MCP 之前，先搞清楚"模型调用工具"到底是怎么回事。**关键认知：模型本身从不执行任何代码**，它只负责"决定调用什么、参数填什么"。

```
 ┌────────┐ ① 用户问题 + 工具清单（名称/描述/参数 schema）  ┌────────┐
 │        │ ───────────────────────────────────────────────► │        │
 │  宿主   │                                                 │  LLM   │
 │ 程序    │ ② 模型输出：{"tool":"get_weather","args":{...}} │        │
 │        │ ◄─────────────────────────────────────────────── │        │
 │        │                                                 │        │
 │ ③ 宿主真正执行 get_weather()，拿到结果                     │        │
 │        │                                                 │        │
 │        │ ④ 把工具结果追加进对话，再次请求                   │        │
 │        │ ───────────────────────────────────────────────► │        │
 │        │ ⑤ 模型给出最终回答（或继续调用下一个工具）          │        │
 │        │ ◄─────────────────────────────────────────────── │        │
 └────────┘                                                 └────────┘
```

这就是所有 coding agent 的核心"**agent 循环**"：只要模型还在请求调用工具，就执行并把结果喂回去；模型不再调用工具时，循环结束。

**问题来了**：每家模型厂商、每个 AI 应用，定义工具的格式都不一样；每接一个新服务（GitHub、Slack、数据库……）都要重写一遍鉴权、错误处理、参数转换。这就是 MCP 要解决的问题。

---

## 4. MCP 是什么：从 M×N 到 M+N

### 4.1 定义（课件第 5 页）

> **Model Context Protocol**：一个开放协议，让系统能以**跨集成通用**的方式向 AI 模型提供上下文。
> **用大白话说**：一种**把工具暴露给 LLM 的标准格式**。

常用类比：**MCP 是 AI 世界的 USB-C 接口**。以前每个设备一种充电口，现在一根线通吃。

### 4.2 M×N → M+N（课件第 6～8 页）

假设有 **M 个 AI 应用**（Claude、Cursor、ChatGPT……）和 **N 个工具**（GitHub、Slack、Jira……）：

```
  没有 MCP：每对都要单独写连接器             有 MCP：各自实现一次协议

  Claude ─┬─── GitHub                    Claude ──┐        ┌── GitHub
          ├─── Slack                     Cursor ──┤        ├── Slack
          └─── Jira                      ChatGPT ─┼─ MCP ──┼── Jira
  Cursor ─┬─── GitHub                             │        │
          ├─── Slack                              └────────┘
          └─── Jira
  ChatGPT ┬─── GitHub
          ├─── Slack
          └─── Jira

  连接器数量 = M × N = 3 × 3 = 9          连接器数量 = M + N = 3 + 3 = 6
```

规模越大差距越明显：10 个应用 × 100 个工具，从 **1000** 个连接器降到 **110** 个。

MCP 带来的三个直接好处（课件第 6 页）：

1. **不用重复实现**鉴权、错误处理、限流等基础设施；
2. 用 **JSON-RPC** 强制统一的输出格式；
3. 集成数量从 **M × N 降为 M + N**。

---

## 5. MCP 深入：角色、原语、流程与传输

### 5.1 四个角色（课件第 9 页）

| 角色 | 是什么 | 举例 |
|---|---|---|
| **Host（宿主）** | 用户使用的 AI 应用 | Cursor、Claude Desktop、Claude Code |
| **MCP Client（客户端）** | 嵌在宿主里的库，**每个 server 一个有状态会话** | 宿主连了 3 个 server，就有 3 个 client 实例 |
| **MCP Server（服务器）** | 挡在工具前面的轻量包装层 | GitHub MCP server、Postgres MCP server |
| **Tool（工具）** | 一个可调用的函数，可以是数据源或 API | `search_issues`、`run_query` |

```
┌──────────────────── Host（如 Claude Desktop）────────────────────┐
│                                                                   │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐                  │
│   │ Client 1 │     │ Client 2 │     │ Client 3 │                  │
│   └────┬─────┘     └────┬─────┘     └────┬─────┘                  │
└────────┼────────────────┼────────────────┼────────────────────────┘
         │ stdio          │ HTTP           │ HTTP
   ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
   │ Server A  │    │ Server B  │    │ Server C  │
   │ 本地文件   │    │  GitHub   │    │   Gmail   │
   └───────────┘    └───────────┘    └───────────┘
```

### 5.2 MCP 的原语（扩展知识）

课件聚焦在 **Tool**，但 MCP 规范里 server 其实可以提供三类东西，client 也能反向提供能力：

| 方向              | 原语                  | 谁控制      | 作用                       |
| --------------- | ------------------- | -------- | ------------------------ |
| Server → Client | **Tools（工具）**       | 模型决定何时调用 | 可执行的函数，如"发邮件""查数据库"      |
| Server → Client | **Resources（资源）**   | 应用决定何时加载 | 只读数据，如文件内容、数据库表结构        |
| Server → Client | **Prompts（提示模板）**   | 用户主动选择   | 预置的提示词模板，如"代码审查模板"       |
| Client → Server | **Sampling（采样）**    | —        | server 反过来请求宿主的 LLM 生成内容 |
| Client → Server | **Roots（根目录）**      | —        | 告诉 server 它可以操作哪些目录/范围   |
| Client → Server | **Elicitation（征询）** | —        | server 在执行中向用户追问信息       |

### 5.3 完整流程（课件第 9～10 页）

以课件例子"**帮我总结 Jack 发来的邮件**"为例：

```
  用户                MCP Client（在宿主中）              LLM              MCP Server（Gmail）
   │  ① 提问                 │                            │                       │
   │ ──────────────────────► │                            │                       │
   │                         │  ② tools/list：你能做什么？                          │
   │                         │ ─────────────────────────────────────────────────► │
   │                         │ ◄───────────────────────────────────────────────── │
   │                         │    返回工具 JSON（名称、说明、参数 schema）          │
   │                         │                            │                       │
   │                         │  ③ 问题 + 工具定义注入上下文  │                       │
   │                         │ ─────────────────────────► │                       │
   │                         │ ◄───────────────────────── │                       │
   │                         │   模型输出结构化调用：         │                       │
   │                         │   search_emails(from="Jack")│                       │
   │                         │                            │                       │
   │                         │  ④ tools/call 执行          │                       │
   │                         │ ─────────────────────────────────────────────────► │
   │                         │ ◄───────────────────────────────────────────────── │
   │                         │    返回邮件内容               │                       │
   │                         │  ⑤ 结果回传，对话继续         │                       │
   │                         │ ─────────────────────────► │                       │
   │ ◄────────────────────── │ ◄───────────────────────── │  生成总结              │
```

对应到真实的 JSON-RPC 消息：

**② 发现工具 `tools/list`**

```json
// 请求
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list" }

// 响应
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "tools": [{
      "name": "gmail_search_emails",
      "description": "按发件人、关键词、时间范围搜索邮件，返回标题与正文摘要",
      "inputSchema": {
        "type": "object",
        "properties": {
          "from":  { "type": "string", "description": "发件人姓名或邮箱" },
          "days":  { "type": "integer", "description": "最近多少天，默认 7" }
        },
        "required": ["from"]
      }
    }]
  }
}
```

**④ 调用工具 `tools/call`**

```json
// 请求
{
  "jsonrpc": "2.0", "id": 2,
  "method": "tools/call",
  "params": { "name": "gmail_search_emails", "arguments": { "from": "Jack", "days": 7 } }
}

// 响应
{
  "jsonrpc": "2.0", "id": 2,
  "result": {
    "content": [{ "type": "text", "text": "共 3 封：1) 周五评审会改期… 2) …" }],
    "isError": false
  }
}
```

> **补充：生命周期**。在 `tools/list` 之前，client 和 server 还会先握手：client 发 `initialize`（带协议版本和自身能力），server 回复自己的能力，client 再发 `notifications/initialized`，之后才进入正常通信。

### 5.4 两种传输方式（课件第 9 页）

| 维度 | **stdio** | **Streamable HTTP** |
|---|---|---|
| 运行位置 | 本地，server 是宿主拉起的**子进程** | 远程，server 是一个 **HTTP 服务** |
| 通信方式 | 通过标准输入/输出管道收发 JSON-RPC | HTTP POST 发消息，需要时用 SSE 流式返回 |
| 鉴权 | 依赖本机环境（环境变量里的 token 等） | 通常用 **OAuth** |
| 优点 | 简单、零网络配置、访问本地文件方便 | 可集中部署、集中管理、多人共享 |
| 缺点 | 每人各装一份，版本和来源难以管控 | 需要处理鉴权、网络与运维 |
| 典型场景 | 个人开发、本地文件系统、本地数据库 | 企业内部服务、SaaS 官方 MCP |

> 早期规范里远程传输是"HTTP + SSE"，2025 年起被 **Streamable HTTP** 取代。

---

## 6. 动手：十几行代码写一个 MCP Server

用官方 Python SDK（`pip install "mcp[cli]"`）中的 `MCPServer`：

> 版本提示：较早的 SDK 版本和大量网上教程里写的是 `from mcp.server.fastmcp import FastMCP`，用法几乎一样；新版统一为 `from mcp.server import MCPServer`。

```python
# server.py
from mcp.server import MCPServer
from mcp.server import MCPServer
mcp = MCPServer("expense-tracker")
mcp = MCPServer("expense-tracker")

EXPENSES = [
    {"category": "food", "amount": 32.5, "month": "2026-09"},
    {"category": "rent", "amount": 1800, "month": "2026-09"},
    {"category": "food", "amount": 41.0, "month": "2026-10"},
]

@mcp.tool()
def expense_total_by_category(category:str,month:str) -> str:
total = sum(e["amount"] for e in EXPENSES
		if e["category"] == category and e["month"] == month)
		return f"{month}的{category}总支出为{total:.2f}"
def expense_total_by_category(category: str, month: str) -> str:
    """计算某类别在某月的总支出。month 格式为 YYYY-MM，例如 2026-09。"""
    total = sum(e["amount"] for e in EXPENSES
                if e["category"] == category and e["month"] == month)
    return f"{month} 的 {category} 总支出为 {total:.2f}"

if __name__ == "__main__":
    mcp.run()  # 默认使用 stdio 传输
```

注意观察：

- **函数签名自动变成 `inputSchema`**（`category: str`、`month: str`）；
- **docstring 自动变成工具的 `description`**——这就是为什么课件说"说明文字就是提示词"；
- 在 Claude Code 中注册：`claude mcp add expense -- python server.py`。

---

## 7. 如何设计好的 MCP Server（方案一）：为结果而设计

> 课件第 11 页：**MCP 不是 REST API 的包装器**

### 7.1 把 REST API 一对一包装成 MCP 会怎样？

| 问题 | 具体表现 |
|---|---|
| **工具太多太碎** | 一个服务几十上百个小工具，模型难以挑选 |
| **上下文又大又复杂** | 每个工具的定义都要塞进上下文，还没干活就吃掉上万 token |
| **agent 花大量时间编排逻辑** | 本该由代码完成的"先查 A 再查 B 再调 C"，变成模型的多轮推理，慢、贵、易错 |

### 7.2 四条最佳实践

#### ① 为结果设计，而不是为操作设计（Design for outcomes, not operations）

```text
 不推荐（暴露底层操作，模型要调 3 次、自己串逻辑）：
   get_users(user_id) → list_account(user_email) → send_payment(account_id)

 推荐（暴露用户真正想要的结果，1 次搞定）：
   send_payment(user_email, amount)
```

**原则**：多步编排放在 server 的代码里做（确定、快、便宜），不要交给模型推理。

#### ② 参数要显式（Explicit arguments）

```python
# 不推荐：嵌套字典，模型容易填错结构
def create_ticket(payload: dict): ...

# 推荐：扁平、有类型、有含义的参数
def create_ticket(title: str, priority: Literal["low", "medium", "high"], assignee_email: str): ...
```

#### ③ 说明文字就是上下文（Instructions are context）

docstring、参数描述、**错误信息**都会进入模型上下文，本质上都是**提示词**。

```text
 差的错误信息：  Error 400
 好的错误信息：  未找到邮箱 jack@exmaple.com 对应的用户。请检查拼写，
               或先调用 crm_search_users(name="Jack") 获取正确邮箱。
```

好的错误信息能直接告诉模型**下一步该怎么做**，让 agent 自我纠错。

#### ④ 工具命名要便于发现（Name tools for discovery）

使用**服务前缀**：`github_create_issue`、`jira_create_issue`、`slack_send_message`。当宿主连了十几个 server 时，带前缀的名字能避免冲突，也让模型一眼知道工具属于哪个系统。

---

## 8. 如何设计好的 MCP Server（方案二）：Search + Execute / Code Mode

> 课件第 12～13 页

### 8.1 问题：工具数量爆炸

接的 MCP server 越多，工具定义越多，上下文被工具清单撑满（回忆第 9 讲的"dumb zone"）。Cloudflare 的实测数据：

| 场景 | 工具数 | 工具定义占用 |
|---|---|---|
| 内部 MCP 门户接 4 个 server（传统方式） | 52 个 | 约 **9,400** token |
| 同样场景开启 Code Mode | 2 个 | 约 **600** token（**降 94%**） |
| Cloudflare 全量 API（上千个端点）用 Code Mode | 2 个 | 降 **99.9%** |

而且 Code Mode 的成本是**固定的**：再多接几个 server，token 也不涨。

### 8.2 思路：只暴露两个工具

| 工具 | 作用 |
|---|---|
| **`search`** | 模型写一段 JavaScript，在全部工具定义中**按需搜索**出相关的那几个 |
| **`execute`** | 模型写一段 JavaScript，**直接以函数形式调用**找到的工具，可串联多个操作、过滤结果、处理错误 |

代码在**沙箱**里执行（Cloudflare 用的是 Dynamic Workers）。

### 8.3 例子：找到 Jira 工单并用 Google Drive 里的内容更新它

**第 1 步：search——找工具**

```javascript
// portal_codemode_search
async () => {
  const tools = await codemode.tools();
  return tools
    .filter(t => t.name.includes("jira") || t.name.includes("drive"))
    .map(t => ({ name: t.name, params: Object.keys(t.inputSchema.properties || {}) }));
}
```

模型只拿到"工具名 + 参数名"这份精简清单，**完整 schema 从未进入上下文**。

**第 2 步：execute——一次调用串起三个操作**

```javascript
// portal_codemode_execute
async () => {
  const tickets = await codemode.jira_search_jira_with_jql({
    jql: 'project = BLOG AND status = "In Progress"',
    fields: ["summary", "description"]
  });
  const doc = await codemode.google_workspace_drive_get_content({
    fileId: "1aBcDeFgHiJk"
  });
  await codemode.jira_update_jira_ticket({
    issueKey: tickets[0].key,
    fields: { description: tickets[0].description + "\n\n" + doc.content }
  });
  return { updated: tickets[0].key };
}
```

**对比**：传统方式需要先加载两个 server 的全部工具 schema，再进行 **3 次独立的工具调用**（每次的中间结果都要流经模型上下文）；Code Mode 只需 **2 次调用**，中间数据在沙箱里流转。

### 8.4 为什么这个方法有效？（扩展理解）

1. **LLM 写代码比写工具调用更擅长**：模型在海量真实代码上训练过，而"工具调用格式"只在相对少量的合成数据上训练过；
2. **中间结果不进上下文**：比如从 1 万行表格里筛 5 行，筛选在沙箱里完成，模型只看到 5 行；
3. **控制流交给代码**：循环、条件、重试用代码表达，比让模型一轮轮推理更确定。

Anthropic 在 2025 年 11 月的工程博客《Code execution with MCP》里给出了同方向的结论：一个示例流程从约 15 万 token 降到约 2,000 token（约 98.7%）。

### 8.5 代价与注意事项

| 代价 | 说明 |
|---|---|
| 需要安全的沙箱 | 模型生成的代码必须隔离执行，限制网络、文件系统和执行时间 |
| 调试更难 | 出错时要看生成的代码而不只是一次工具调用 |
| 权限要更严 | 一段代码能串联多个写操作，误操作的影响面更大 |

### 8.6 方案一 vs 方案二：怎么选？

| 场景 | 推荐 |
|---|---|
| 自己写一个专用 server，工具 < 10～20 个 | **方案一**：精心设计少量"结果导向"的工具 |
| 要接入大量 server / 上千个 API 端点 | **方案二**：search + execute |
| 两者兼有 | 每个 server 内部遵循方案一；在网关/门户层用方案二统一收口 |

---

## 9. 企业级 MCP 架构：Cloudflare 参考架构精读

> 课件第 14 页 *Advanced MCP Architecture Design* 的图来自 Cloudflare 博客。Cloudflare 内部从工程到产品、销售、市场、财务团队都在用 MCP，他们总结了一套落地架构。

### 9.1 企业用 MCP 的三大风险

| 风险 | 含义 |
|---|---|
| **授权蔓延**（Authorization sprawl） | 每个员工、每个 server 各管各的 token 和权限，没人说得清谁能访问什么 |
| **提示注入**（Prompt injection） | 工具返回的内容里藏着恶意指令，诱导 agent 越权操作 |
| **供应链风险**（Supply chain risks） | 从公开仓库装来的 MCP server 可能夹带后门、偷偷收集数据 |

### 9.2 架构全景

```
┌─────────────┐      ┌────────────────────── Cloudflare ──────────────────────┐
│ MCP 客户端   │      │                                                         │
│ ChatGPT     │      │  ┌──────────────┐     ┌────────────────┐                 │      ┌──────────────┐
│ Cursor      │─────►│  │ MCP Server   │────►│  远程 MCP       │─────────────────┼─────►│ 内部服务      │
│ Claude …    │      │  │ Portal 门户   │     │  Servers       │                 │      │ ClickHouse   │
└──────┬──────┘      │  │ (发现/审计/   │     └───────▲────────┘                 │      │ Snowflake    │
       │             │  │  DLP/Code    │             │                          │      └──────────────┘
       │             │  │  Mode)       │     ┌───────┴────────┐                 │
       │             │  └──────┬───────┘     │ ZTNA (Access)  │                 │      ┌──────────────┐
       │             │         │             │ 身份认证 OAuth  │                 │      │ SaaS MCP     │
       │             │         └─────────────┴────────────────┴─────────────────┼─────►│ Slack Jira   │
       │             │                                                         │      │ GitHub …     │
       │             └─────────────────────────────────────────────────────────┘      └──────────────┘
       │
       ▼
  ┌────────────┐            ┌────────────────────┐
  │ AI Gateway │──────────► │ 各家 LLM 提供商     │   （切换模型、控制 token 预算）
  └────────────┘            └────────────────────┘
```

### 9.3 五个组件逐一拆解

#### ① 远程 MCP Server：取代本地 server

**为什么不用本地 server？** 本地部署可能来自未经审查的软件来源和版本，增加供应链攻击和工具注入攻击风险；IT 和安全团队也无法统一管理——"这是一场必输的游戏"。

**Cloudflare 的做法**：

- 由**中心团队**在 monorepo 里搭建共享 MCP 平台；
- 员工要把内部资源暴露为 MCP 时：**先获 AI 治理团队批准 → 复制模板 → 写工具定义 → 部署**；
- 自动继承：**默认拒绝写操作 + 审计日志**、自动生成的 CI/CD 流水线、密钥管理；
- 搭一个受治理的新 server 只需几分钟——**治理内建在平台里**，这正是推广快的原因。

#### ② Cloudflare Access：统一身份认证

- 公开资源（如文档 MCP）任何人可用；内部资源必须认证；
- 模板里集成 **Access 作为 OAuth 提供方**：校验 **SSO、MFA**，以及 IP、地理位置、设备证书等上下文属性。

#### ③ MCP Server Portal（门户）：集中发现与治理

server 多了以后出现新问题：**员工不知道有哪些 server 可用**。门户的解法：

- 员工只连一个门户地址，就能看到**自己有权使用的全部**内部和第三方 server；
- **集中日志**：谁登录了哪个门户；
- **DLP 规则**：例如禁止把 PII 发给某些 server；
- **按人群暴露不同工具**：

| 门户 | 谁能访问 | 代码仓库 MCP 暴露哪些工具 |
|---|---|---|
| 财务门户 | 财务组 | 只读工具 |
| 工程门户 | 工程团队 + 公司笔记本 | 读写工具 |

- 门户也是 **Code Mode** 的落脚点：在门户 URL 后加 `?codemode=search_and_execute`，所有上游 server 就会收敛成 `portal_codemode_search` 和 `portal_codemode_execute` 两个工具。

#### ④ AI Gateway：模型网关

放在 **MCP 客户端与 LLM 之间**：

- 在不同 LLM 提供商之间快速切换，**避免厂商锁定**；
- **成本控制**：限制每位员工可消耗的 token 量。

#### ⑤ Cloudflare Gateway：发现并阻断"影子 MCP"

如何找出员工私下在用的未授权远程 MCP？多层扫描：

| 手段 | 检测内容 |
|---|---|
| `httpHost` 选择器 | 已知 MCP 域名（如 `mcp.stripe.com`）、`mcp.*` 通配子域 |
| `httpRequestURI` 选择器 | `/mcp`、`/mcp/sse` 这类典型路径 |
| **DLP 请求体检测** | 利用"MCP 走 JSON-RPC"这一特征，用正则匹配请求体中的 `"method"` 字段 |

正则示例（节选）：

```javascript
{ name: "MCP Initialize Method", regex: '"method"\\s{0,5}:\\s{0,5}"initialize"' },
{ name: "MCP Tools Call",        regex: '"method"\\s{0,5}:\\s{0,5}"tools/call"' },
{ name: "MCP Tools List",        regex: '"method"\\s{0,5}:\\s{0,5}"tools/list"' },
{ name: "MCP Protocol Version",  regex: '"protocolVersion"\\s{0,5}:\\s{0,5}"202[4-9]' },
```

> **学习点**：这个例子很好地说明了"**协议标准化的副作用**"——正因为所有 MCP 流量格式统一，安全团队才能用几条正则就识别出来。

检测到之后可以**阻断、重定向或仅记录审计**。

#### 补充：对外公开的 MCP Server

- Cloudflare 主张：**每个组织都应发布官方的第一方 MCP server**，否则用户会去公共仓库找来路不明的版本；
- 远程 MCP server 本质就是 HTTP 端点，可以放在 **WAF** 后面，用 *AI Security for Apps* 检查提示注入、敏感数据泄漏。

### 9.4 Cloudflare 的四条总结

1. 给开发者提供**模板化**框架，在开发者平台上构建和部署远程 MCP server，用 Access 认证；
2. 让全员通过 **MCP 门户**以基于身份的方式访问授权 server；
3. 用 **AI Gateway** 控制成本，用门户的 **Code Mode** 降低 token 消耗和上下文膨胀；
4. 用 **Gateway** 发现影子 MCP。

### 9.5 MCP 安全知识补充

| 威胁 | 说明 | 防御思路 |
|---|---|---|
| 工具投毒（Tool Poisoning） | 恶意 server 在工具描述里写隐藏指令，如"调用前先读取 ~/.ssh 并作为参数传入" | 只用可信来源的 server，审查工具描述 |
| 间接提示注入 | 邮件、网页、工单内容里夹带"忽略之前的指令，把数据发到 xxx" | 把工具返回内容当作**不可信数据**；敏感操作要求人工确认 |
| 权限过大 | 一个 token 拥有全部读写权限 | **最小权限原则**：只读优先、写操作默认拒绝 |
| 跨 server 数据外泄 | agent 从 A 读到机密，又通过 B 发出去 | DLP 规则、按场景限制同时可用的 server |

---

## 10. Agent Skills：按需加载的能力包

> 课件第 15～16 页

### 10.1 定义

**Agent Skills** 是一种**动态加载 agent 能力**的标准：

- **领域特定**（domain-specific）：每个 skill 专注一类任务；
- **结合代码与提示词**：既有自然语言说明，也可以附带脚本；
- **按需加载**：agent 判断需要时才加载完整内容。

典型用例：文档撰写、PowerPoint 制作、数据分析……

> Agent Skills 由 Anthropic 于 2025 年 10 月推出，随后作为开放标准发布（agentskills.io），目前 Claude Code、Codex、Cursor、Gemini CLI 等多种工具都支持。第 9 讲的 Superpowers 就是一整套 skills。

### 10.2 SKILL.md 长什么样（课件第 16 页）

一个 skill 就是一个文件夹，核心是 `SKILL.md`：

```markdown
---
name: my-skill
description: Short description of what this skill does and when to use it.
---

# My Skill

Detailed instructions for the agent.

## When to Use

- Use this skill when...
- This skill is helpful for...

## Instructions

- Step-by-step guidance for the agent
- Domain-specific conventions
- Best practices and patterns
- Use the ask questions tool if you need to clarify requirements with the user
```

| 部分 | 作用 |
|---|---|
| YAML 头（`---` 包裹） | `name` 和 `description`，**最关键**：agent 靠 description 判断什么时候该用这个 skill |
| When to Use | 进一步说明触发场景 |
| Instructions | 具体步骤、领域约定、最佳实践 |

完整的 skill 目录可以带上辅助文件：

```
pdf-report/
├── SKILL.md          # 必需：元数据 + 主要说明
├── scripts/          # 可选：可直接执行的脚本，如 fill_form.py
├── references/       # 可选：详细参考文档，需要时再读
└── assets/           # 可选：模板、图片等资源
```

### 10.3 核心机制：渐进式披露（扩展知识）

Skills 之所以"省上下文"，靠的是三层加载：

```
 第 1 层：元数据（name + description）  ── 会话开始时全部加载，每个 skill 仅约百来个 token
     │
     │  agent 判断"当前任务用得上"
     ▼
 第 2 层：SKILL.md 正文                ── 触发时才读入上下文
     │
     │  正文里提到"表单填写见 references/forms.md"
     ▼
 第 3 层：references / scripts / assets ── 真正需要时才读取或执行（脚本只需执行，代码本身不必进上下文）
```

对比：如果把 50 份操作手册全写进 AGENTS.md，每次会话都要背着它们；做成 skills，平时只占 50 段简短描述。

### 10.4 写好一个 skill 的建议

1. **description 写清"做什么 + 何时用"**，这是触发的唯一依据；
2. **SKILL.md 保持精简**，长参考资料拆到 `references/`；
3. **确定性工作写成脚本**（如格式转换、校验），而不是让模型每次重新推理；
4. **写明验证方式**：做完怎么检查结果正确。

---

## 11. API vs MCP vs Skills：三者到底什么关系

> 课件第 17 页

### 11.1 官方对比表

| 维度 | **APIs** | **MCP** | **Skills** |
|---|---|---|---|
| **是什么** | 应用暴露给开发者调用的 HTTP / REST / GraphQL 服务接口 | server 暴露的**工具定义**，让 LLM agent 以标准化方式调用 | **可复用的任务包 / 流程**，教 agent 如何完成一项工作，常常编排多个工具/端点 |
| **谁来用** | 你（开发者）或 SDK | **模型 / agent 运行时**（以"工具调用"的形式），而不是每次写定制集成的人类开发者 | agent 或 agent 框架，作为更高层的能力随取随用 |
| **怎么用** | 鉴权、重试、分页、输入校验都由你决定 | 与外部资源、数据、服务交互的**主要机制** | **工作流抽象**——"完成 X 的可重复方法是这样的" |

### 11.2 一个类比：开餐厅

| 概念 | 类比 | 说明 |
|---|---|---|
| **API** | 各家供应商的订货电话 | 每家格式不同，你得自己记怎么打、怎么付款 |
| **MCP** | 统一的订货平台 | 所有供应商接入同一平台，厨师（agent）用同一种方式下单 |
| **Skills** | 菜谱 | 告诉厨师"做宫保鸡丁：先订鸡肉和花生，再按这个顺序炒"——菜谱会用到平台，但它本身是**做法** |

### 11.3 层次关系

```
 ┌─────────────────────────────────────────────┐
 │  Skills：怎么做（流程、经验、约定、脚本）       │  ← "菜谱"
 ├─────────────────────────────────────────────┤
 │  MCP：能做什么（标准化的工具接口）              │  ← "统一订货平台"
 ├─────────────────────────────────────────────┤
 │  APIs：底层服务能力                            │  ← "各家供应商"
 └─────────────────────────────────────────────┘
```

**一个具体例子：每周生成销售周报**

- **API**：Salesforce REST API、Google Slides API；
- **MCP**：`salesforce_query_opportunities`、`slides_create_presentation` 两个工具；
- **Skill**：`weekly-sales-report/SKILL.md`——"先查本周赢单 → 按区域汇总 → 用 `assets/template.pptx` 模板生成 → 用 `scripts/check_numbers.py` 校验合计 → 发给销售总监"。

### 11.4 什么时候用哪个？

| 你的需求                        | 选择                     |
| --------------------------- | ---------------------- |
| 写确定性的业务代码，流程固定              | 直接调 **API**            |
| 想让 agent 能访问某个外部系统          | 写 / 接一个 **MCP server** |
| 想让 agent 稳定地按某种方式完成一类任务     | 写一个 **Skill**          |
| 想让 agent 访问系统**并**按固定流程完成任务 | **MCP + Skill** 组合     |

---

## 12. 自测题

<details>
<summary><b>Q1：模型在工具调用中会"执行"函数吗？</b></summary>

不会。模型只输出结构化的调用意图（工具名 + 参数），由宿主/MCP client 交给 server 真正执行，再把结果放回上下文。
</details>

<details>
<summary><b>Q2：MCP 中 Host、Client、Server 分别是什么？一个宿主连 4 个 server 时有几个 client？</b></summary>

Host 是用户使用的 AI 应用；Client 是嵌在宿主里的协议库，每个 server 对应一个有状态会话；Server 是挡在工具前的轻量包装层。连 4 个 server 就有 4 个 client 会话。
</details>

<details>
<summary><b>Q3：为什么说"MCP 不是 REST API 的包装器"？请把 get_users → list_account → send_payment 改成更好的设计。</b></summary>

一对一包装会导致工具过多、上下文膨胀、编排逻辑压在模型身上。更好的设计是暴露结果导向的工具 `send_payment(user_email, amount)`，把多步查找放进 server 的代码里。
</details>

<details>
<summary><b>Q4：Code Mode 为什么能把 token 降低 90% 以上？</b></summary>

① 只暴露 search/execute 两个工具，完整 schema 不预先加载；② 模型写代码在沙箱里串联多次调用，中间结果不经过上下文；③ 工具总数增长时成本不变。
</details>

<details>
<summary><b>Q5：Cloudflare 为什么不鼓励员工用本地 MCP server？</b></summary>

本地 server 来源和版本不受控，带来供应链与工具注入风险；IT/安全团队无法统一管理和审计。改为由中心平台模板化部署远程 server，内建默认拒绝写、审计日志、密钥管理。
</details>

<details>
<summary><b>Q6：如何检测走了非标准路径的影子 MCP 流量？</b></summary>

用 DLP 检查 HTTP 请求体：MCP 基于 JSON-RPC，请求体里有 `"method": "tools/call"`、`"initialize"` 等固定字段，可用正则识别。
</details>

<details>
<summary><b>Q7：Skills 的"渐进式披露"有哪三层？</b></summary>

① 元数据（name + description）始终加载；② 触发时加载 SKILL.md 正文；③ 需要时才读取 references 或执行 scripts。
</details>

<details>
<summary><b>Q8：用一句话分别概括 API、MCP、Skills。</b></summary>

API：给开发者调用的服务接口；MCP：给 agent 调用的标准化工具接口；Skills：教 agent 如何组合工具完成某类任务的可复用流程。
</details>

---

## 13. 参考资料

| 资料 | 链接 | 说明 |
|---|---|---|
| CS146S 课程主页 | https://themodernsoftware.dev | 本讲课件出处 |
| Cloudflare 企业 MCP 参考架构 | https://blog.cloudflare.com/enterprise-mcp/ | 第 9 节的主要来源 |
| Cloudflare Code Mode | https://blog.cloudflare.com/code-mode/ | Code Mode 思路的首次提出 |
| Anthropic：Code execution with MCP | https://www.anthropic.com/engineering/code-execution-with-mcp | 用代码执行降低 MCP token 消耗 |
| MCP 官方文档与规范 | https://modelcontextprotocol.io | 架构、原语、传输、鉴权的权威说明 |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk | 第 6 节示例所用 SDK |
| Agent Skills 开放标准 | https://agentskills.io | SKILL.md 格式规范 |
| Anthropic：Equipping agents with Agent Skills | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | Skills 设计理念与渐进式披露 |
| Anthropic 官方 skills 示例 | https://github.com/anthropics/skills | 文档、PPT、数据分析等真实 skill |

---

> **学习建议**：
> 1. 用第 6 节的代码写一个自己的 MCP server，接到 Claude Code 里，观察 `tools/list` 返回的 schema（可以结合你之前的抓包方法看真实请求体里工具定义长什么样）；
> 2. 把你常做的一件重复工作（比如"写 CSDN 博客的固定排版"）写成一个 `SKILL.md`，体验 description 写得好坏对触发的影响。
