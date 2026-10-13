# CS146S 第 05 节课学习笔记：Agent Skills 实战——把"怎么做事"写成 agent 能复用的技能

> **课程**：Stanford CS146S *The Modern Software Developer*（Fall 2026，Mihail Eric）
> **讲次**：第 05 节课（2026-10-06，周二）—— *Agent Skills*
> **补充材料**：Cursor 官方插件 [pstack](https://github.com/cursor/plugins/tree/main/pstack)（poteto）、[mattpocock/skills](https://github.com/mattpocock/skills)、[browse.sh](https://browse.sh/)（Browserbase）、[obra/superpowers](https://github.com/obra/superpowers)、[Agent Skills 规范](https://agentskills.io/specification)
> **前置知识**：第 03 节课（RePPIT、上下文工程）、第 04 节课（MCP、工具调用）
> **阅读时长**：约 50 分钟

---

## 目录

- [0. 一页速览](#0-一页速览)
- [1. 术语表](#1-术语表)
- [2. 为什么需要 Skills：MCP 管"连接"，Skills 管"流程"](#2-为什么需要-skillsmcp-管连接skills-管流程)
- [3. Agent Skills 快速回顾：一个文件夹 + 一份说明书](#3-agent-skills-快速回顾一个文件夹--一份说明书)
- [4. 技能的四大类别（课件主线）](#4-技能的四大类别课件主线)
- [5. 类别一：代码理解与规划](#5-类别一代码理解与规划)
- [6. 类别二：验证（Verification）](#6-类别二验证verification)
- [7. 类别三：代码风格（Code Style）](#7-类别三代码风格code-style)
- [8. 类别四：杂项——浏览器解析与 browse.sh](#8-类别四杂项浏览器解析与-browsesh)
- [9. 三大开源技能库横向对比](#9-三大开源技能库横向对比)
- [10. 写好 Skill 的八条最佳实践](#10-写好-skill-的八条最佳实践)
- [11. 动手：从零写一个自己的 Skill](#11-动手从零写一个自己的-skill)
- [12. 再看 API vs MCP vs Skills](#12-再看-api-vs-mcp-vs-skills)
- [13. 自测题](#13-自测题)
- [14. 参考资料与学习建议](#14-参考资料与学习建议)

---

## 0. 一页速览

> **一句话总结**：MCP 让 agent **"够得着"** 外部世界，Skills 让 agent **"知道怎么做"** 一件事。一个好的 Skill 就是一份**范围聚焦、写明触发条件、按需加载、自带验证**的 Markdown 操作手册，而且它应该从**你自己的工作记录**里长出来。

| # | 核心结论 |
|---|---|
| 1 | MCP 擅长第三方集成；而 LLM **极其擅长遵循长篇流程**，把这种能力暴露出来是任何 agent 框架（harness）的重要组成部分 |
| 2 | Skill = 动态加载的能力包：**领域特定**、**代码 + 提示词结合**、**按需加载** |
| 3 | 课程把常用 Skill 分四类：**代码理解与规划**、**验证**、**代码风格**、**杂项**（如浏览器解析） |
| 4 | `grill-me`：开工前让 agent **反过来拷问你**，对齐需求；`grill-with-docs` 顺便沉淀术语表和决策记录 |
| 5 | `create-verification-skill`：为项目生成一个"像用户一样驱动真实应用并留证据"的验证技能 |
| 6 | 代码风格 Skill 把团队规范写成 agent 可执行的条文，特别适合**代码审查 agent** |
| 7 | browse.sh：浏览器自动化技能的开放目录 + CLI，用"建议的选择器和 XHR 请求"替代盲目点网页 |
| 8 | 最佳实践：一技一事、自建可移植技能库、**挖掘自己的聊天记录**、CLI + Skill、写明触发词、渐进式披露、模块化组合、维护验证技能形成改进闭环 |

```text
            你的需求
               │
     ┌─────────▼─────────┐
     │  理解与规划 Skill  │  grill-me / RePPIT / how / why
     └─────────┬─────────┘
               │ 对齐后的 spec / plan
     ┌─────────▼─────────┐
     │   实现（TDD 等）   │  ← 代码风格 Skill 全程约束
     └─────────┬─────────┘
               │
     ┌─────────▼─────────┐
     │    验证 Skill      │  verify-<app>：启动→驱动→取证→清理
     └─────────┬─────────┘
               │ 发现问题 / 被你纠正
     ┌─────────▼─────────┐
     │  复盘并改进 Skill  │  挖聊天记录 → 更新技能（闭环）
     └───────────────────┘
```

---

## 1. 术语表

| 术语 | 英文 | 人话解释 |
|---|---|---|
| Agent Skill / 技能 | Agent Skill | 一个文件夹，核心是 `SKILL.md`，告诉 agent"遇到某类任务时，按这个流程做"。可附带脚本和参考资料 |
| Harness / 框架外壳 | Agent Harness | 包在模型外面的那层程序：管上下文、调工具、加载技能。Claude Code、Cursor、Codex 都是 harness |
| 渐进式披露 | Progressive Disclosure | 不一次性把所有内容塞进上下文，先只给"目录"（名字 + 描述），需要时再读正文、再读附件 |
| Frontmatter | YAML Frontmatter | `SKILL.md` 顶部 `---` 包起来的元数据区，至少有 `name` 和 `description` |
| 触发条件 | Trigger | 让 agent 判断"该用这个技能了"的线索，主要写在 `description` 里 |
| 用户调用 / 模型调用 | User-invoked / Model-invoked | 前者只能由你输入 `/技能名` 触发；后者 agent 可以在合适时机自己决定调用 |
| Grilling / 拷问 | Grilling session | 让 agent 连珠炮式地问你问题，直到需求的每个分支都想清楚 |
| 设计树 | Design Tree | 把一个设计拆成决策节点：每个决策下面挂着依赖它的子决策 |
| 前沿 | Frontier | 设计树中"前置条件都已确定、现在就能问"的那批问题 |
| 通用语言 | Ubiquitous Language | 来自领域驱动设计（DDD）：开发者、业务方、代码都用同一套词汇，减少翻译成本 |
| ADR | Architecture Decision Record | 架构决策记录：一份短文档记下"我们为什么这样决定" |
| 验证技能 | Verification Skill | 教 agent 如何**真实地**启动、操作应用并收集证据，证明功能可用 |
| 功能地图 | Feature Map | 验证技能里的一组文档：每个用户可见功能怎么进入、怎么驱动、什么结果算通过 |
| 冒烟 / 证据 | Smoke test / Evidence | 粗粒度"能不能跑起来"的检查；证据指截图、终端记录、响应体、日志、数据库状态等 |
| TDD | Test-Driven Development | 测试驱动开发：红（先写失败的测试）→ 绿（写代码让它通过）→ 重构 |
| 代码审查 agent | Code Review Agent | 专门审 diff 的 agent，按规范逐条检查并给出意见 |
| Slop | AI slop | 网络俚语，指 AI 产出的大量"能跑但啰嗦、低质量"的代码或文字 |
| XHR | XMLHttpRequest | 网页在后台向服务器发的数据请求。直接调这些请求往往比"模拟点按钮"更快、更省 token |
| CDP | Chrome DevTools Protocol | 程序化控制 Chrome 的协议，Playwright 等工具底层都用它 |
| CLI | Command-Line Interface | 命令行工具。课件建议：给 agent 一个 CLI，再用 Skill 封装样板流程 |
| Playbook | Playbook | 剧本：针对某类任务（修 bug、性能优化……）的固定步骤清单，pstack 里有 23 个 |

---

## 2. 为什么需要 Skills：MCP 管"连接"，Skills 管"流程"

课件第 4 页给出的动机只有两句话，但很关键：

> - MCP is good for 3rd party integrations for coding agents
> - LLMs are amazingly good at following longer form procedures and exposing such capabilities is an important part of any harness

翻译成人话：

1. **MCP 解决"够得着"的问题**：让 agent 能连 GitHub、Jira、数据库、浏览器……
2. **但"够得着"≠"会做事"**：有了 Jira 工具，agent 并不知道你们团队"提 bug 要先复现、再写失败测试、再修、最后关联 PR"这套流程。
3. **LLM 恰好很擅长照着长流程执行**：只要你把流程写清楚，它就能一步步做下来。
4. **所以 harness 需要一种机制**，把这些流程打包、按需加载——这就是 Skills。

### 类比：新员工入职

```text
MCP     ≈ 给新员工开通各种系统账号（Git、Jira、数据库、内部 API）
Skills  ≈ 给新员工的《岗位操作手册》（发版流程、代码规范、排障清单）
上下文  ≈ 新员工的工作记忆（有限，所以手册要"用到哪页翻哪页"）
```

只开账号不给手册，新员工会"自由发挥"；只给手册不开账号，新员工什么都干不了。两者是**互补**关系，不是替代关系。

---

## 3. Agent Skills 快速回顾：一个文件夹 + 一份说明书

> 第 04 节课已经讲过 Skills 的基本概念，这里只做快速回顾并补充规范细节。

### 3.1 课件定义

- **一种动态加载 agent 能力的标准**（A standard for dynamically loaded agent capabilities）
  - **领域特定**（Domain-specific）：一个技能只管一个领域
  - **代码与提示词结合**（Combine code and prompts）：Markdown 写流程，脚本干确定性的活
  - **按需加载**（Loaded by agent as needed）：平时只占一行描述的上下文
- **典型用途**：文档撰写、PPT 制作、数据分析……以及更多

### 3.2 目录结构（来自 agentskills.io 规范）

```text
skill-name/
├── SKILL.md          # 必需：元数据 + 指令
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：参考文档（按需读取）
├── assets/           # 可选：模板、资源文件
└── ...
```

### 3.3 Frontmatter 字段

| 字段 | 必需 | 约束 / 作用 |
|---|---|---|
| `name` | 是 | ≤ 64 字符，只能小写字母、数字、连字符；不能以 `-` 开头/结尾，不能有 `--`；**必须和文件夹名一致** |
| `description` | 是 | ≤ 1024 字符。要同时写清"**做什么**"和"**什么时候用**"，并包含触发关键词 |
| `license` | 否 | 许可证 |
| `compatibility` | 否 | 环境要求（需要什么系统包、是否联网等） |
| `metadata` | 否 | 任意键值对（作者、版本等） |
| `allowed-tools` | 否 | 预先批准该技能可用的工具（实验性） |

> **扩展字段**：Claude Code 和 Cursor 还支持 `disable-model-invocation: true`，含义是"**只允许用户手动输入 `/技能名` 触发，模型不能自己调用**"。mattpocock/skills 和 pstack 大量使用这个字段来区分"编排型"和"纪律型"技能（见第 10.7 节）。它不在 agentskills.io 的通用规范表里，属于具体产品的扩展。

### 3.4 渐进式披露的三层加载

```text
第 1 层  启动时：只加载所有技能的 name + description（每个几十 token）
   │
   │  用户的请求命中某个 description
   ▼
第 2 层  触发时：读取该技能的 SKILL.md 正文
   │
   │  正文里写着"如果是 X 情况，读 references/x.md"
   ▼
第 3 层  需要时：读取 references/ 里的细节，或执行 scripts/ 里的脚本
```

**好处**：装 100 个技能，平时也只多占几千 token；真正用到时才"翻手册"。这正好呼应第 03 节课"守住上下文窗口的聪明区"。

---

## 4. 技能的四大类别（课件主线）

课件把常用技能归成四类，后面四节逐一展开：

| 类别 | 解决的问题 | 课件举例 | 补充举例 |
|---|---|---|---|
| **代码理解与规划** | agent 不懂代码库、没对齐需求就开干 | RePPIT 系列技能、`grill-me` / `grill-with-docs` | pstack 的 `/how`、`/why`、`/architect`；Superpowers 的 `brainstorming`、`writing-plans` |
| **验证** | agent 说"做完了"，其实没跑过 | `create-verification-skill` | Superpowers 的 `verification-before-completion`；Matt 的 `tdd` |
| **代码风格** | agent 写的代码不符合团队习惯 | 定义代码层面的最佳实践，用于审查 agent | pstack 的 `typescript-best-practices`、`no-comments`；Matt 的 `code-review` |
| **杂项** | 其他高频、可复用的专门任务 | 浏览器解析：browse.sh | 文档、PPT、数据分析类技能 |

记忆口诀：**想清楚 → 写规范 → 证明它 → 其他杂活**。

---

## 5. 类别一：代码理解与规划

### 5.1 RePPIT 技能（回顾第 03 节课）

第 03 节课的 RePPIT（Research → Propose → Plan → Implement → Test）本身就可以拆成一组技能：

| 阶段 | 可以做成的技能 | 产出物 |
|---|---|---|
| Research | `research-codebase`：只调研现状，不改代码 | `research.md` |
| Propose | `propose-solutions`：给出 2～3 个方案和取舍 | `proposal.md` |
| Plan | `write-plan`：拆成可验证的小步骤 | `plan.md` |
| Implement | `implement-plan`：按计划逐步实现，每步更新进度 | 代码 + 进度记录 |
| Test | `verify-change`：跑测试、真实驱动应用 | 测试结果 + 证据 |

把每个阶段写成技能的好处：**每次都按同一套流程走**，不依赖你当天记不记得提醒 agent。

### 5.2 `grill-me`：让 agent 反过来拷问你

> 来源：Matt Pocock（TypeScript 圈知名讲师，Total TypeScript 作者）的 [mattpocock/skills](https://github.com/mattpocock/skills)。课件的说法是：**帮助建立对任务的心智模型（mental model）**。

**它解决的问题**：Matt 在 README 里说，软件开发最常见的失败是**没对齐（misalignment）**——你以为 agent 懂了，等它做完才发现完全不是你要的。他引用《程序员修炼之道》："No-one knows exactly what they want"（没人确切知道自己想要什么）。

**解法**：开工前进行一次 **grilling session**，让 agent 详细地问你问题。

#### 它的实现很有意思：一层"转发"

`grill-me` 的 `SKILL.md` 正文只有一句话：

````markdown
---
name: grill-me
description: A relentless interview to sharpen a plan or design.
disable-model-invocation: true
---

Call the Skill tool with "grilling".
````

真正的逻辑在另一个**模型可调用**的技能 `grilling` 里。这就是"**用户调用的技能负责编排，模型调用的技能负责纪律**"的设计（第 10.7 节详述）。

#### `grilling` 的核心机制：设计树 + 前沿 + 轮次

```text
                 [要做一个记账导出功能]
                 /          |          \
          导出格式?      导出范围?      谁能导出?        ← 第 1 轮（前沿）
          /    \            |
       CSV    PDF       按月/自定义?                   ← 第 2 轮（依赖第 1 轮答案）
        |       \
   编码/分隔符?  要不要图表?                            ← 第 3 轮
```

规则要点（意译自 `grilling/SKILL.md`）：

1. **把问题建成设计树**：每个决策都分叉出依赖它的子决策。
2. **按轮次推进**：每轮把"前沿"上的所有问题一次性问完，**编号**，并**给出你推荐的答案**。
3. **措辞让"是"等于接受推荐**：用户回一个"yes"就能快速推进。
4. **依赖未决问题的问题放到下一轮**，不要猜。
5. **事实自己查，决策问用户**：需要从代码库、文件系统里找的事实，agent 应该自己（或派子 agent）去查，**不要拿可以自己查到的东西去问用户**。
6. **前沿为空才结束**：所有分支都走过、没有任何隐含假设；并且要等用户确认"我们已达成共识"才开始动手。

一轮拷问的格式长这样：

```text
❓ Q1 - 导出格式：只支持 CSV，还是 CSV + PDF？
➡️ 推荐：先只做 CSV，PDF 放到下个迭代。

---

❓ Q2 - 权限：所有登录用户都能导出自己的数据吗？
➡️ 推荐：是，只能导出自己的数据，管理员不额外开放。
```

> 💡 **学习提示**：这个技能的价值不在"问问题"本身，而在**强迫你在动手前把隐含决策显式化**。很多返工都来自"我以为你知道"。

### 5.3 `grill-with-docs`：拷问 + 沉淀文档

`grill-with-docs` 的正文同样极短：**依次调用 `grilling` 和 `domain-modeling` 两个技能**。后者负责在拷问过程中：

- 维护项目根目录的 **`GLOSSARY.md`**（术语表）
- 在 `docs/adr/` 下写 **ADR**（架构决策记录）
- 当你用的词和术语表冲突时**当场指出**："术语表把 cancellation 定义为 X，但你好像指的是 Y，到底是哪个？"
- 当你用了模糊词时**提出精确用词**："你说的 account 是 Customer 还是 User？这是两个东西。"

```text
/
├── GLOSSARY.md            ← 项目通用语言
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

**为什么术语表这么重要？** Matt 举的例子：

- **之前**："当课程某个章节里的一节课被'实体化'（也就是在文件系统里给它分配了位置）的时候会出问题"
- **之后**："materialization cascade 有问题"

一个约定好的词顶二十个词。好处是连锁的：变量/函数/文件命名一致 → 代码库更好导航 → agent 思考时**花的 token 更少**。Matt 自己说这"可能是这个仓库里最酷的技巧"。

### 5.4 补充：pstack 的理解类技能

pstack（见第 9 节）也有一组"先理解再动手"的技能：

| 技能 | 用途 |
|---|---|
| `/how` | 讲解某个子系统**怎么工作**，例："我们怎么取消 run？有没有 N+1 查询？" |
| `/why` | 追溯某个东西**为什么这样设计**：运行时发现可用的 MCP，并行查源码历史、issue、文档、聊天记录、监控、错误追踪等证据 |
| `/architect` | 写跨函数边界的代码前，先把调用方用法、类型、模块形状定下来 |
| `/blast-radius` | 一个看起来很小的改动可能炸到哪些地方，并**用运行代码证明**它是安全的 |
| `/teach` | 结合 how + why，一张图一张图地讲懂一个改动或子系统 |

---

## 6. 类别二：验证（Verification）

### 6.1 为什么验证技能最值得投资

AI 写代码最大的问题不是"写不出来"，而是"**说写好了，其实没验证**"。Superpowers 的哲学里有一条叫 **Evidence over claims**（证据胜于声明）；pstack 有一条原则叫 **prove-it-works**（证明它能用）。

课件在最佳实践里也明确说：**维护一个验证技能，让 agent 检查自己的工作，从而形成改进闭环**。

### 6.2 `create-verification-skill`：生成"验证技能"的技能

> 来源：pstack。它不是验证技能本身，而是一个**元技能**：读你的仓库，为它**生成**一个项目专属的验证技能 `.cursor/skills/verify-<app>/`。

**它的五个步骤：**

```text
① 访谈仓库（不是访谈用户）
   └─ 用户接触的界面是什么？怎么启动？怎么程序化驱动？能收集什么证据？能不能并行跑两份？
② 生成技能 SKILL.md
   └─ Launch / Doctor / Drive / Evidence / Cleanup / Helpers 六个部分
③ 播种功能地图（Feature Map）
   └─ features/README.md + 每个功能一个文件（先挑最重要的 3～5 个）
④ 交付前先自证
   └─ 按生成的技能完整跑一遍：启动→体检→驱动一个功能→取证→清理，确认证据还在
⑤ 提供维护闭环
   └─ 应用变了，用 /maintain-verification-skill 修正功能地图
```

**第 ① 步的五个问题：**

| 维度 | 要回答的问题 | 举例 |
|---|---|---|
| 界面 Surface | 用户实际接触什么？ | Web UI、CLI/TUI、桌面应用、API、移动端、库 |
| 运行 Run | 本地怎么启动？ | 优先用仓库自己文档里的命令；端口、环境变量、种子数据、登录 |
| 驱动 Drive | agent 怎么程序化地操作它？ | 先找现成的 Playwright/Cypress；没有再选通用方案：Web 用浏览器/CDP，CLI 用 tmux/PTY，服务用 HTTP |
| 观察 Observe | 能收集什么证据？ | 截图、终端记录、响应体、日志、退出码、数据库状态 |
| 隔离 Isolate | 能否两个实例并行？ | 不能就写明：拒绝同时驱动共享实例，避免搞坏用户的会话 |

**第 ② 步生成的六个部分：**

| 部分 | 内容 | 关键要求 |
|---|---|---|
| **Launch** 启动 | 精确的启动命令 + 怎么判断就绪（日志行、端口响应） + 如何关闭 | 不留占位符 |
| **Doctor** 体检 | 一个只读检查："这个实例值得驱动吗？" | 进程在、版本对、端口是我们的、登录有效 |
| **Drive** 驱动 | 用本仓库**真实**的选择器/命令 | 优先稳定标识（ARIA 标签、data 属性、路由），不用坐标 |
| **Evidence** 证据 | 截什么、存哪 | 走真实用户路径，不用测试专用接口；记录动作和结果状态；检查副作用（写文件、插数据库） |
| **Cleanup** 清理 | 关掉本次启动的实例 | **只杀自己启动的进程**，不按进程名杀；**清理不能删掉证据** |
| **Helpers** 辅助脚本 | 技能附带的脚本 | 可执行，且在正文里写明怎么调用 |

> 💡 **一句很到位的话**："A generated skill that was never executed is a draft, not a deliverable."（**一个从没执行过的技能只是草稿，不是交付物。**）

**功能地图的单个文件结构**（四个固定二级标题）：

```markdown
# 导出 CSV

## Sub-features
- 按月导出、自定义日期范围导出

## How to get to it (user POV)
- 登录 → 侧边栏「报表」→ 右上角「导出」

## Driving it with Playwright
- 点击 `[data-testid="export-button"]`，选择月份，等待下载事件

## Gotchas
- 本地环境下载目录在 ./tmp/downloads，跑之前先清空
```

### 6.3 其他验证类技能

| 技能 | 来源 | 一句话 |
|---|---|---|
| `verification-before-completion` | Superpowers | 宣布"修好了"之前，必须真的确认修好了 |
| `tdd` | Matt / Superpowers / pstack | 红-绿-重构；Matt 版强调**只在事先约定的"接缝"（seam）测试**，测行为而不是实现细节 |
| `diagnosing-bugs` | Matt | 先建一个对该 bug 会变红的反馈回路 → 最小化 → 假设 → 插桩 → 修复 → 回归测试 |
| `/maintain-verification-skill` | pstack | 功能地图和应用不同步时，修正它 |
| `/benchmark-checklist` | pstack | 报告性能数字前先审一遍：瓶颈在哪、重复跑了没、端到端是否相关 |

---

## 7. 类别三：代码风格（Code Style）

### 7.1 课件要点

- **定义代码层面的最佳实践**（Define code-level best practices）
- **对代码审查 agent 特别有用**（Useful for code review agents）

### 7.2 为什么不直接写进 `AGENTS.md`？

| 放在 `AGENTS.md` / `CLAUDE.md` | 放在代码风格 Skill |
|---|---|
| **每轮都在上下文里**，占 token | 只在写代码 / 审代码时加载 |
| 适合"全局必须知道"的少量规则 | 适合**大量、细致**的规范，如 TypeScript 类型纪律 |
| 很难分语言、分场景 | 可以按语言拆：`ts-style`、`python-style`、`sql-style` |

### 7.3 业界例子

- **pstack 的"原则"技能**：二十多个 `principle-*` 技能，每个讲一条工程原则，例如：
  - `principle-guard-the-context-window`：大输出交给子 agent，主线程只留摘要
  - `principle-test-behavior-not-implementation`：测行为，不测实现
  - `principle-subtract-before-you-add`：先做减法再做加法
  - `principle-type-system-discipline`：用类型系统表达约束
- **`/typescript-best-practices`**：把"类型纪律"原则落到具体 TS 语法上
- **`/no-comments`**：审查前去掉多余注释（会派一个叫 "Comment Sicko" 的子 agent 专门挑注释）
- **`/unslop`**：去掉文字中的"AI 味"
- **Matt 的 `code-review`**：**两个维度并行审查**——
  - **Standards**：是否符合仓库编码规范（外加 Martin Fowler 的"代码坏味道"基线）
  - **Spec**：是否忠实实现了原始 issue / spec
  - 两个维度用**两个子 agent 分开跑**，互不干扰上下文

### 7.4 一个代码风格 Skill 的骨架

````markdown
---
name: ts-code-style
description: TypeScript code style rules for this repo. Use when writing, editing, or reviewing .ts/.tsx files, or when asked to "review this diff" or "check style".
---

# TypeScript Code Style

## Rules（每条都要可检查）
1. 禁止 `any`；外部输入用 `unknown` + 类型守卫收窄。
2. 函数参数超过 3 个时改用对象参数。
3. 不写解释"做了什么"的注释，只写解释"为什么"的注释。
4. 错误信息必须带上下文：说明是哪个操作、哪个对象失败，并附上原始错误。

## When reviewing
- 逐条对照 Rules，输出：文件:行号 / 违反的规则编号 / 建议修改。
- 规则没覆盖的问题单独列为"建议"，不要混进"违规"。

## Examples
- 好/坏对比示例见 references/examples.md（只在不确定时读取）。
````

> 💡 **写规则的诀窍**：每条规则都应该是**可判定**的（看一眼代码就能判断是否违反）。"代码要优雅"这种规则对 agent 没有用。

---

## 8. 类别四：杂项——浏览器解析与 browse.sh

### 8.1 browse.sh 是什么

[browse.sh](https://browse.sh/) 由云浏览器公司 **Browserbase** 推出，官网自我介绍是两件事：

1. **"The open web catalog"**：一个开放的**浏览器自动化技能目录**，按 `网站 · 技能 · 方法 · 地区` 组织，目前有大量网站的技能（Amazon、Airbnb、GitHub、FedEx、Google Flights、NASA APOD……）。
2. **"A browser CLI for your AI Agents"**：一个给 agent 用的浏览器命令行工具（安装：`npm i -g browse`）。

### 8.2 CLI 的四类能力

```bash
# ① 安装某个网站的技能
browse skills add alltrails.com
browse skills add recreation.gov

# ② 底层浏览器原语：点击、输入、选择、按键、滚动、截图
browse click "input#search"
browse type "Apartments in SF"
browse select @8 "Single family unit"   # @8 = agent 的无障碍树引用
browse press "Enter"
browse screenshot

# ③ 实时查看网络和控制台（调试神器）
browse network --tail
browse console --tail

# ④ 切到云端会话（前缀加 cloud）
browse cloud sessions create
browse cloud search "Latest White House press release"
browse cloud fetch "https://www.nytimes.com/section/us"
```

所有命令默认用本地 Chromium，加 `cloud` 前缀即可切到 Browserbase 的远程浏览器。

### 8.3 核心价值："先找捷径，再点页面"

官网宣称："**Suggested DOM selectors and XHR requests cut token costs by 50x.**"（建议的 DOM 选择器和 XHR 请求能让 token 成本降低 50 倍。）

目录里每个技能都标注了**方法**，大致可以这样理解（我根据目录描述的归纳）：

| 方法标签 | 含义 | 成本 |
|---|---|---|
| **API** | 直接调网站的公开或内部 JSON 接口 | 最低 |
| **Fetch** | 一次 HTTP GET 拿页面再解析，不开浏览器 | 低 |
| **Browser** | 真的打开浏览器去点、去输入 | 高 |
| **Hybrid** | 混合：能走接口的走接口，必须交互的用浏览器 | 中 |
| **MCP** | 通过该网站提供的 MCP server 完成 | 视情况 |

**看一个真实技能**：NASA 每日一图（APOD）技能的正文明确写着：

> APOD 提供了文档完备、免费、无反爬的 JSON API……**直接用它，不要为这个任务驱动浏览器。** 浏览器路径做的事是它的超集，产出的结构化数据却更少。

然后给出 `curl` 命令、参数表、响应字段说明、`media_type` 是 image 还是 video 要分支处理……这就是一个标准的"**把踩坑经验写成手册**"的技能。

```text
没有技能时：  打开网页 → 截图 → 让模型看图 → 找按钮 → 点击 → 再截图 → ……（几十轮，大量 token）
有技能时：    读 SKILL.md → 一条 curl → 解析 JSON → 完成
```

> ⚠️ **注意合规**：目录里有些技能使用了网站的"未公开内部接口"或住宅代理，实际使用时要自己确认是否符合目标网站的服务条款，以及公司/学校的安全规定。

### 8.4 和第 04 节课 Code Mode 的联系

第 04 节课的 Code Mode 思路是"**与其让模型一个个点工具，不如让它写代码一次性调**"；browse.sh 的思路是"**与其让模型一个个点页面，不如告诉它直接调哪个接口**"。两者本质相同：**把高频、确定的路径提前固化，省掉模型的摸索成本。**

---

## 9. 三大开源技能库横向对比

### 9.1 三位作者，三种风格

| 维度 | **Superpowers** | **mattpocock/skills** | **pstack** |
|---|---|---|---|
| 作者 | Jesse Vincent（obra） | Matt Pocock | Lauren Tan（poteto），React 核心团队成员，经历 Meta、Netflix、Cursor |
| 定位 | 端到端、强约束的开发方法论 | 小而可组合、"给真正的工程师" | 少写代码但写高质量代码，"放心并行" |
| 主入口 | 自动触发：brainstorming → plan → 执行 | 手动：`/grill-me`、`/grill-with-docs`、`/to-spec`、`/implement` | `/poteto-mode`：自动匹配 23 个 playbook 之一 |
| 理念关键词 | TDD、系统化、降复杂度、证据胜于声明 | 对齐、通用语言、反馈回路、深模块 | 先深后快、证明能用、多模型分工 |
| 对"控制权"的态度 | 流程比较"重"，强制按步骤走 | 明确批评 GSD、BMAD、Spec-Kit 这类框架"接管流程、夺走控制权" | 介于两者之间：一个 mode 统一入口，其余技能情境触发 |
| 安装 | 各 agent 的插件市场 | `npx skills@latest add mattpocock/skills` 或 Claude Code 插件 `mattpocock-skills` | Cursor 中 `/add-plugin pstack` |
| 适合谁 | 想要一套"开箱即用的纪律"的人 | 想自己掌控、按需挑选改造的人 | Cursor 用户、需要长时间/多 agent 并行的人 |

### 9.2 Superpowers 技能清单（按 README 分类）

| 类别 | 技能 |
|---|---|
| 测试 | `test-driven-development` |
| 调试 | `systematic-debugging`（四阶段根因分析）、`verification-before-completion` |
| 协作 | `brainstorming`、`writing-plans`、`executing-plans`、`dispatching-parallel-agents`、`requesting-code-review`、`receiving-code-review`、`using-git-worktrees`、`finishing-a-development-branch`、`subagent-driven-development` |
| 元技能 | `writing-skills`（按最佳实践写新技能，含测试方法）、`using-superpowers` |

### 9.3 Matt Pocock 的四个"失败模式"

Matt 把他的技能库组织成对四个常见失败的解法，这是一个很好的学习框架：

| 失败模式 | 根因 | 解法技能 |
|---|---|---|
| ① agent 没做我想要的 | 没对齐 | `/grill-me`、`/grill-with-docs` |
| ② agent 太啰嗦 | 没有共享语言 | `GLOSSARY.md` + `domain-modeling` |
| ③ 代码跑不起来 | 缺反馈回路 | `/tdd`、`/diagnosing-bugs`（加上类型检查、浏览器访问） |
| ④ 代码变成一团泥 | 不关心设计，AI 加速了软件熵增 | `/to-spec`、`/improve-codebase-architecture`、`codebase-design` |

### 9.4 pstack 的 `/poteto-mode` 是怎么工作的

```text
/poteto-mode 这个 PR 有个滚动每 750ms 漂移的 bug，先复现，再修复并验证
        │
        ▼
① 把任务匹配到一个 playbook（这里是 bug-fix），把它的步骤原样抄进 todo 列表
        │
        ▼
② 步骤执行到哪，就路由到对应技能（how / tdd / interrogate / unslop …）
        │
        ▼
③ 最后用 opening-a-pr playbook 开 PR，回复也经过 unslop 去 AI 味
```

23 个 playbook 覆盖：调查、修 bug、性能、指标爬坡（hillclimb）、运行时取证、功能开发、重构、原型、视觉对齐、**写技能**、评测、看护 PR、发版、长时间自主运行、多阶段计划、会话接手、安全暂停等。

---

## 10. 写好 Skill 的八条最佳实践

> 课件第 12～13 页列出的最佳实践，下面逐条讲解并配例子。

### 10.1 范围聚焦：一个技能，一个明确定义的任务

> Keep scope focused — One skill, one clearly defined task

- ❌ `dev-helper`：既管写代码又管测试又管部署
- ✅ `write-migration`、`verify-web-app`、`release-notes` 各管一件

**为什么**：范围越大，`description` 越难写准，agent 越难判断何时触发；正文越长，加载后占的上下文越多。

### 10.2 维护自己的、可跨项目移植的技能库

> Maintain your own collection of skills that you can easily port across projects
> **Chefs bring their own knives between kitchens** — poteto

**厨师换厨房会带自己的刀。** 你的技能库就是你的刀具：换公司、换项目、换 agent 都能带走。

实践建议：

```text
~/my-skills/                 ← 放进一个 Git 仓库
├── grill-me/
├── write-plan/
├── verify-web-app/
└── python-style/

# 用符号链接装到各个 agent 的技能目录
ln -s ~/my-skills/grill-me ~/.claude/skills/grill-me
ln -s ~/my-skills/grill-me ~/.cursor/skills/grill-me
```

（Matt 的仓库就提供了一个 `scripts/link-skills.sh` 做这件事，`git pull` 一下所有已安装的技能就同步更新。）

### 10.3 挖掘你自己的聊天记录

> Mine your own transcripts — Skills are processes written as markdown – dig your own chats to see where you intervened or corrected

**这是整讲最有价值的一条。** 技能本质上就是"用 Markdown 写下来的流程"。最好的技能素材不在网上，在**你和 agent 的历史对话里**：

```text
翻聊天记录，找这三种时刻：
  1. 你打断了 agent       → "等等，先别改，先跑一下测试"
  2. 你纠正了 agent       → "不对，我们项目里日期都用 UTC"
  3. 你重复说了同样的话   → 第 3 次说"记得先写失败的测试"
        │
        ▼
  把这些纠正写进技能，下次 agent 一开始就知道
```

**现成工具**：

| 技能 | 来源 | 做什么 |
|---|---|---|
| `/automate-me` | pstack | 从你最近的对话记录中提炼你的工作习惯，生成一个个人 `<你的名字>-mode` 技能 |
| `/correct` | pstack | 挖掘 agent 反复犯的错误类型（**同一类错误出现两次才算一类**），按"架构 → 类型 → lint → 测试 → 文档"的优先级让它**不可能再犯** |
| `/reflect` | pstack | 一个长任务完成后，把学到的"配方"写回技能 |
| `/retro` | Matt | 一次会话结束后，建议改进 agent 环境（导航、自动检查、规范、引导文件），按严重程度排序 |

> 💡 `/correct` 的思路值得细品：**文档是最后的手段**。能用架构让错误不可能发生，就不要靠写一条"请不要这样做"的规则。

### 10.4 别重复造轮子：给 agent 一个 CLI，再用 Skill 包住样板流程

> Don't burn tokens/time reinventing the wheel — Equip agents with a CLI tool and wrap the boilerplate in a skill

```text
❌ 每次都让 agent 现写 50 行 Python 去调内部 API、处理分页和重试
✅ 写一个 CLI：mytool export --month 2026-09 --format csv
   再写一个技能：什么时候用、参数怎么选、输出怎么检查、常见报错怎么处理
```

browse.sh 就是这个模式的典范：**`browse` 是 CLI，`browse skills add xxx` 装的是技能**。

### 10.5 写明触发场景和请求短语

> Include situations and request phrases that should trigger the skill

`description` 是 agent 决定"要不要用这个技能"的**唯一依据**（第 1 层只加载它），所以要写得像搜索关键词：

```yaml
# ❌ 太空泛
description: Helps with PDFs.

# ✅ 做什么 + 什么时候用 + 用户可能怎么说
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

pstack 的 `create-verification-skill` 甚至把用户可能的原话写进去了：`Use for /create-verification-skill, "make a control skill for this repo", or when a project has no scripted way to prove UI/CLI/service behavior.`

> Matt 的 `writing-for-agents` 技能有两条相关建议：**把最关键的词放在最前面**；**每个分支场景只写一个触发词**，同义词堆砌只是重复占 token。

### 10.6 渐进式披露：按需引用具体文件

> Progressive disclosure — Reference specific files as needed with additional context

```markdown
## 迁移数据库
1. 运行 `make db-diff` 查看差异。
2. 如果涉及删除列，**先读 references/destructive-migrations.md** 再继续。
3. 如果是 PostgreSQL 分区表，读 references/partitioned-tables.md。
```

注意第 2、3 步：**写清楚"什么情况下读哪个文件"**，而不是一句"更多信息见 references/"。

但也别过度拆分。pstack 的 `guard-the-context-window` 原则提醒：**每次都要用的模板和参考，应该直接放在技能文件里**，而不是放到单独文件让 agent 每次多读一次。

| 内容 | 放哪里 |
|---|---|
| 每次都要用的步骤和规则 | `SKILL.md` 正文 |
| 只在特定分支才需要的细节 | `references/xxx.md`，正文写明触发条件 |
| 确定性的、可重复的操作 | `scripts/xxx.sh`，正文写明调用方式 |

### 10.7 模块化与组合

> Modularize and compose skills

Matt 的库给出了一个清晰的组合规则：

```text
用户调用的技能（编排者，disable-model-invocation: true）
    │  只能由你输入 /xxx 触发
    │  可以调用模型调用的技能
    │  但不能调用另一个用户调用的技能
    ▼
模型调用的技能（纪律 / 原语）
    │  你可以调，agent 也可以在合适时自己调
    ▼
例：/grill-with-docs  =  grilling  +  domain-modeling
    /grill-me         =  grilling
    /triage、/wayfinder、/improve-codebase-architecture 也都复用 grilling
```

**好处**：`grilling` 只写一遍，五个技能复用；改进它一次，五个技能同时变好。

### 10.8 维护验证技能，形成改进闭环

> Maintain a verification skill to have an agent check its work — Allows for improvement loop

```text
       ┌──────────────────────────────────┐
       ▼                                  │
  agent 实现功能                          │
       │                                  │
       ▼                                  │
  调用 verify-<app> 技能自检              │
       │                                  │
   ┌───┴────┐                             │
   │ 通过？  │── 否 ──► 修复 ─────────────┤
   └───┬────┘                             │
       │ 是                               │
       ▼                                  │
  人工检查时又发现问题？── 是 ──► 把这个检查点补进验证技能 ┘
       │ 否
       ▼
     交付
```

**关键点**：每次你人工发现了 agent 没发现的问题，都应该问自己"能不能把这一步写进验证技能？"——这样 agent 会越用越靠谱。

### 10.9 最佳实践速查卡

| # | 原则 | 一句话 | 检查问题 |
|---|---|---|---|
| 1 | 范围聚焦 | 一技一事 | 能用一句话说清它干什么吗？ |
| 2 | 自建技能库 | 带着自己的刀 | 换项目时能直接带走吗？ |
| 3 | 挖聊天记录 | 从纠正中提炼 | 这条规则是我真的纠正过的吗？ |
| 4 | CLI + Skill | 别每次重写样板 | 有没有重复写的胶水代码？ |
| 5 | 写触发词 | description 是搜索词 | 用户的原话能匹配上吗？ |
| 6 | 渐进式披露 | 用到哪页翻哪页 | 正文里每个引用都写了触发条件吗？ |
| 7 | 模块化组合 | 原语复用 | 有没有两个技能在重复同一段流程？ |
| 8 | 验证闭环 | 让 agent 自检 | 有验证技能吗？上次人工发现的问题补进去了吗？ |

---

## 11. 动手：从零写一个自己的 Skill

### 11.1 场景

假设你在维护一个 Flask + React 的记账应用（课程作业里的那种），你发现自己每次都要提醒 agent："改完后端要跑 pytest，改完前端要起服务点一下页面，截图给我看。"——这就是一个**该写成技能的信号**。

### 11.2 第一步：从聊天记录里找素材

```text
你说过的话（模拟）：
  - "先跑 pytest，别直接说改好了"
  - "前端起在 5173，后端在 5000，别搞反"
  - "截图要包含整个页面，不要只截局部"
  - "测完把你启动的服务关掉，别把我的开发服务器也杀了"
```

### 11.3 第二步：写 SKILL.md

````markdown
---
name: verify-expense-app
description: Verify changes to the expense tracker by running backend tests and driving the real web UI with screenshots. Use after editing backend/ or frontend/, before saying a change is done, or when asked to "verify", "test it", or "check it works".
---

# Verify the expense tracker

## Launch
1. 后端：`cd backend && flask run --port 5001`，看到 `Running on http://127.0.0.1:5001` 即就绪。
2. 前端：`cd frontend && VITE_API=http://127.0.0.1:5001 npm run dev -- --port 5174`，端口 5174 响应即就绪。
   - 用 5001/5174 而不是 5000/5173，避免和用户自己的开发服务器冲突。

## Doctor
- `curl -fsS http://127.0.0.1:5001/api/health` 返回 `{"ok": true}`，否则先修启动问题再继续。

## Drive
- 改了 backend/：先跑 `cd backend && pytest -q`，必须全绿。
- 改了 frontend/：用 Playwright 打开 http://127.0.0.1:5174，按 features/ 里对应功能文件操作。
- 优先使用 `data-testid` 选择器，不要用坐标。

## Evidence
- 截全页图存到 `./verify-artifacts/<日期>-<功能>.png`。
- 记录：执行的操作、看到的结果、pytest 输出最后 20 行。
- 如果功能会写数据库，额外查询一次确认数据确实写入。

## Cleanup
- 只关闭本次在 5001、5174 启动的进程，不要按进程名 kill。
- 不删除 ./verify-artifacts/。

## Features
- 功能地图见 features/README.md；修改哪个功能，就读对应文件。
````

### 11.4 第三步：先自己跑一遍

按 `create-verification-skill` 的标准：**按技能写的步骤完整执行一次**，有任何一步跑不通就改技能，直到它能一次跑通。

### 11.5 第四步：发现新问题就补

下次你发现"agent 没测移动端宽度"，就在 Drive 里加一行"额外用 375px 宽度截一张图"。技能就这样**越用越准**。

### 11.6 自查清单

- [ ] `name` 和文件夹名一致，全小写 + 连字符
- [ ] `description` 同时写了"做什么"和"什么时候用"，包含用户可能说的原话
- [ ] 正文是**可执行的步骤**，不是空泛的原则
- [ ] 所有命令、端口、路径都是**真实的**，没有占位符
- [ ] 引用的每个附件都写了"什么情况下读"
- [ ] 有明确的"完成标准"（什么证据算通过）
- [ ] 自己完整跑过一遍

---

## 12. 再看 API vs MCP vs Skills

课件最后再次对比三者（第 04 节课也讲过，这里作为收尾巩固）：

| | **APIs** | **MCP** | **Skills** |
|---|---|---|---|
| **是什么** | 应用暴露给**开发者**调用的 HTTP/REST/GraphQL 接口 | server 暴露的**工具定义**，让 LLM agent 以标准化方式调用 | **可复用的任务包 / 流程**，教 agent 怎么完成一项工作，常常编排多个工具/接口 |
| **谁来用** | 你，或 SDK | 模型 / agent 运行时（以"工具调用"形式），而不是每次手写集成的开发者 | agent 或 agent 框架，作为更高层的能力 |
| **怎么用** | 鉴权、重试、分页、输入校验都由你决定 | 与外部资源、数据、服务交互的**主要机制** | **工作流抽象**："完成 X 的可重复做法就是这样" |
| **类比** | 厨房里的燃气、水电 | 标准化的厨具接口（任何厨师都能用） | 菜谱 |

```text
            ┌──────────────────────────────┐
  Skills    │ "做一份周报：先查 Jira，再读   │  ← 流程（怎么做）
            │  Drive 文档，最后发 Slack"     │
            └──────────────┬───────────────┘
                           │ 编排
            ┌──────────────▼───────────────┐
  MCP       │ jira_search / drive_get /     │  ← 工具（能做什么）
            │ slack_post                    │
            └──────────────┬───────────────┘
                           │ 包装
            ┌──────────────▼───────────────┐
  APIs      │ Jira REST / Drive API /       │  ← 底层接口
            │ Slack Web API                 │
            └──────────────────────────────┘
```

> 💡 **一个常见误区**：Skill 不一定要依赖 MCP。它也可以只编排 CLI（如 `browse`、`git`、`pytest`），或者纯粹是思考流程（如 `grill-me`）。

---

## 13. 自测题

<details>
<summary><b>Q1：既然有了 MCP，为什么还需要 Skills？</b></summary>

MCP 解决"agent 能调用哪些外部能力"，Skills 解决"agent 应该按什么流程完成一项任务"。LLM 很擅长遵循长流程，把流程打包成可按需加载的技能，是 harness 的重要能力。两者互补：MCP 是账号权限，Skills 是操作手册。

</details>

<details>
<summary><b>Q2：渐进式披露的三层分别加载什么？为什么能节省上下文？</b></summary>

① 启动时只加载 `name` + `description`；② 命中时读取 `SKILL.md` 正文；③ 需要时读取 `references/` 或执行 `scripts/`。平时每个技能只占几十 token，只有用到的技能才展开。

</details>

<details>
<summary><b>Q3：grilling 技能里的"前沿（frontier）"是什么？为什么不一次把所有问题问完？</b></summary>

前沿是设计树中前置决策都已确定、现在就能问的问题。依赖未决问题的问题如果提前问，就得猜前面的答案，问了也可能白问。所以按轮次推进：每轮问完当前前沿，根据回答重新计算前沿。

</details>

<details>
<summary><b>Q4：grilling 中哪些问题应该问用户，哪些不应该？</b></summary>

**决策**问用户（要不要支持 PDF、谁有权限）；**事实**自己查（代码里用的什么框架、现有接口长什么样），可派子 agent 去查。不要拿能自己查到的东西去打扰用户。

</details>

<details>
<summary><b>Q5：`grill-with-docs` 比 `grill-me` 多了什么？它对后续开发有什么好处？</b></summary>

多调用了 `domain-modeling`：拷问过程中维护 `GLOSSARY.md` 和 ADR，指出用词冲突、提出精确术语。好处是形成项目通用语言：命名一致、代码更好导航、agent 表达更简洁、思考更省 token。

</details>

<details>
<summary><b>Q6：`create-verification-skill` 生成的验证技能包含哪几部分？哪条规则最容易被忽视？</b></summary>

Launch、Doctor、Drive、Evidence、Cleanup、Helpers，外加 features/ 功能地图。最容易被忽视的是：**清理只杀自己启动的进程，且不能删除证据**；以及**技能必须自己完整跑通一次才算交付**。

</details>

<details>
<summary><b>Q7：为什么代码风格规范适合做成 Skill 而不是全塞进 AGENTS.md？</b></summary>

AGENTS.md 每轮都在上下文里，规范一多就持续占用 token；做成技能只在写/审代码时加载，还能按语言、场景拆分。代码审查 agent 可以逐条对照规则输出结果。

</details>

<details>
<summary><b>Q8：browse.sh 为什么能省 token？它的思路和第 04 节课的 Code Mode 有什么共同点？</b></summary>

技能里提前写好了建议的 DOM 选择器和可直接调用的 XHR/API 请求，agent 不必反复截图、看图、找按钮。共同点：都把高频、确定的路径提前固化，省掉模型逐步摸索的成本。

</details>

<details>
<summary><b>Q9："挖掘自己的聊天记录"具体要找什么？</b></summary>

找你打断 agent、纠正 agent、反复说同一句话的时刻。这些就是 agent 缺失的流程知识，应该写进技能。pstack 的 `/automate-me`、`/correct`，Matt 的 `/retro` 都是辅助这件事的工具。

</details>

<details>
<summary><b>Q10：下面这个 description 有什么问题？怎么改？<br><code>description: A helpful skill for testing.</code></b></summary>

太空泛：没说测什么、什么时候用、用户会怎么说。可改为：`Run backend pytest and drive the web UI with Playwright to verify changes in the expense app. Use after editing backend/ or frontend/, or when asked to "verify" or "check it works".`

</details>

<details>
<summary><b>Q11：Matt 的库里"用户调用技能"和"模型调用技能"的组合规则是什么？</b></summary>

用户调用技能（`disable-model-invocation: true`）负责编排，只能由人手动触发；它可以调用模型调用技能，但不能调用另一个用户调用技能。模型调用技能承载可复用的纪律，人和 agent 都能调用。

</details>

<details>
<summary><b>Q12：Superpowers、mattpocock/skills、pstack 各自最适合什么样的人？</b></summary>

Superpowers：想要一套开箱即用、强约束开发纪律的人。mattpocock/skills：想保留控制权、挑选小技能自己改造的人。pstack：Cursor 用户、需要长时间运行和多 agent 并行、重视"证明能用"的人。

</details>

---

## 14. 参考资料与学习建议

### 14.1 课程与指定资料

| 资料 | 链接 | 看什么 |
|---|---|---|
| CS146S 课程网站 | https://themodernsoftware.dev | 课件与作业 |
| pstack（Cursor 官方插件） | https://github.com/cursor/plugins/tree/main/pstack | README 的 playbook 表和技能表；`skills/create-verification-skill/SKILL.md` |
| mattpocock/skills | https://github.com/mattpocock/skills | README 的"四个失败模式"；`grilling`、`domain-modeling`、`writing-for-agents` |
| browse.sh | https://browse.sh/ | CLI 用法；随便点开几个技能看它们怎么写 |
| obra/superpowers | https://github.com/obra/superpowers | 技能清单与工作流；`writing-skills` 技能 |

### 14.2 扩展阅读

| 资料 | 链接 |
|---|---|
| Agent Skills 规范 | https://agentskills.io/specification |
| Anthropic：Agent Skills 文档 | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview |
| Claude Code：Skills | https://code.claude.com/docs/en/skills |
| Cursor：Skills | https://cursor.com/docs/skills |
| Superpowers 发布文章 | https://blog.fsck.com/2025/10/09/superpowers/ |
| Eric Evans《领域驱动设计》 | 理解"通用语言"的出处 |
| John Ousterhout《软件设计的哲学》 | 理解"深模块"（Matt 的 `codebase-design` 技能基于此） |

### 14.3 学习建议

1. **先用再写**：装一个现成的技能库（推荐从 Matt 的 `grill-me` 开始，门槛最低），用一周，感受技能何时触发、何时没触发。
2. **读三个好技能的源码**：`grilling`（看怎么把"拷问"写成可执行流程）、`create-verification-skill`（看怎么写"元技能"）、browse.sh 的任意一个网站技能（看怎么把踩坑经验写清楚）。
3. **从自己的聊天记录写第一个技能**：回看最近 5 次和 agent 的对话，找出你纠正最多的那件事，写成技能。
4. **一定要有验证技能**：如果只写一个技能，就写你项目的 `verify-<app>`。
5. **建一个自己的技能仓库**：放进 Git，用符号链接装到 Claude Code / Cursor / Codex，换项目时直接带走。

---

> 本文基于 CS146S 第 05 节课（2026-10-06）课件整理，并结合 pstack、mattpocock/skills、browse.sh、Superpowers 的公开文档进行扩展。各技能库更新很快，具体命令和技能名以各仓库最新 README 为准。
