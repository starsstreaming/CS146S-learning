# CS146S 第 10 节课学习笔记：Agent Readiness（智能体就绪度）与可验证性

> **课程**：Stanford CS146S *The Modern Software Developer*（Fall 2026）
> **讲次**：第 10 节课（2026-10-22，周四嘉宾讲座）
> **讲者**：Eno Reyes（Factory 联合创始人兼 CTO）
> **课程安排**：[课程官网](https://themodernsoftware.dev) · *Guest: Eno Reyes (CTO @ Factory)*
> **配套阅读**：[代码库就绪与后台编码 Agent](CS146S_第10节课_2026-10-22_代码库就绪与后台编码Agent.md)。本文聚焦嘉宾讲座中的可验证性与就绪度模型，结合演讲、工程案例和官方文档展开。

> **If you can verify it, an agent can solve it.**
> 能被验证的问题，Agent 就能解决。

| 项目 | 内容 |
| --- | --- |
| 主题 | Agent Readiness（智能体就绪度）：怎样把代码库改造成适合 AI Agent 工作的环境 |
| 核心资料 | ① Eno Reyes（Factory 联合创始人兼 CTO）斯坦福演讲 PPT《If you can verify it, an agent can solve it》<br>② AI Engineer Code 2025 演讲《Making Codebases Agent Ready》<br>③ Basis 工程博客《Making Our Monorepo Ergonomic for Agents》（2026-05-19）<br>④ Factory 官方文档《Agent Readiness》 |
| 扩展资料 | Karpathy《Verifiability》、Jason Wei《Asymmetry of verification and verifier's rule》、AGENTS.md 开放规范 |
| 适合读者 | 在用 Claude Code / Codex / Cursor / Droid 等编码 Agent 的工程师、Tech Lead、研发效能负责人 |
| 预计阅读 | 精读约 60 分钟；动手作业约一个下午 |

---

## 📌 目录

0. [一页纸总结](#0-一页纸总结)
1. [名词速查表](#1-名词速查表)
2. [第一部分：人类简史给我们的启示](#2-第一部分人类简史给我们的启示)
3. [第二部分：Agent 是一台"猜测-检查"机器](#3-第二部分agent-是一台猜测-检查机器)
4. [理论延伸：为什么"可验证性"是 AI 时代最重要的属性](#4-理论延伸为什么可验证性是-ai-时代最重要的属性)
5. [第三部分：Agent Readiness 模型（9 大支柱 × 5 个等级）](#5-第三部分agent-readiness-模型)
6. [演讲精讲：从规范到生产的自主闭环](#6-演讲精讲从规范到生产的自主闭环)
7. [实战案例：Basis 如何把 Monorepo 改造成 Agent 友好型](#7-实战案例basis-如何把-monorepo-改造成-agent-友好型)
8. [第四部分：超越代码——任何领域的"左移"](#8-第四部分超越代码任何领域的左移)
9. [动手作业：一个下午让项目达到 Agent-Ready](#9-动手作业一个下午让项目达到-agent-ready)
10. [常见误区](#10-常见误区)
11. [自测题（附答案）](#11-自测题附答案)
12. [参考资料](#12-参考资料)

---

## 0. 一页纸总结

> 💡 **一句话版本**：Agent 失败时，问题大多不在模型这颗"大脑"，而在它所处的"世界"（环境）。与其等更聪明的模型，不如去搭一个更容易被检查的世界。

**三个必须记住的结论**（来自演讲 Recap 页）：

| # | 结论 | 含义 |
| --- | --- | --- |
| 01 | **瓶颈在环境，不在大脑** | 模型能力已足够；缺的是测试、文档、可复现环境等"检查设施" |
| 02 | **能验证，就能解决** | 只要能自动判断对错，Agent 就能靠反复试错收敛到正确答案 |
| 03 | **让检查便宜、快速、细小** | 检查越快、粒度越细，Agent 能试的次数越多，成功率呈指数级提升 |

**知识地图**：

```
人类历史类比 ──► "我们没有变聪明，只是变得可检查"
       │
       ▼
Agent = 猜测(模型) + 检查(环境) 的循环
       │
       ├─► 两个旋钮：验证精度 × 检查频率
       ├─► 数学：逐步检查 12% → 98%
       └─► 速度：5 秒检查 vs 10 分钟检查 = 120 倍尝试次数
       │
       ▼
Agent Readiness 模型：9 大支柱 × 5 个等级（80% 门槛解锁）
       │
       ▼
落地：AGENTS.md / .env.example / 一键测试 / pre-commit / 先写失败测试 / readiness 报告
       │
       ▼
推广：任何领域都可以通过"把工作左移（变得更易检查）"迎接 Agent
```

---

## 1. 名词速查表

> 先过一遍这些术语，后文读起来会顺畅很多。

| 术语 | 英文 | 通俗解释 |
| --- | --- | --- |
| **智能体 / Agent** | AI Agent | 能自主"读代码 → 计划 → 改代码 → 运行 → 检查 → 修复"多步循环的 AI 程序，而不是只回答一次问题的聊天机器人 |
| **Agent 就绪度** | Agent Readiness | 衡量一个代码库/组织在多大程度上能让 Agent 可靠地自主工作，本质是"可检查程度" |
| **验证器 / 检查器** | Verifier / Checker | 能自动判断一个结果是对是错的机制，比如单元测试、类型检查器、证明检查器 |
| **可验证性** | Verifiability | 任务结果能被多便宜、多快、多客观地判定对错 |
| **粒度** | Granularity | 能多频繁地检查：只在最后检查一次，还是每一步都检查 |
| **基准测试** | Benchmark | 用于比较模型能力的标准化考题集 |
| **SWE-bench / SWE-bench Verified** | — | 用真实 GitHub Issue 测试 AI 修 bug 能力的基准；Verified 版本是经人工筛选、题意更清晰的 500 题子集 |
| **补丁** | Patch | 对代码的一组修改（diff） |
| **PR（拉取请求）** | Pull Request | 向主分支提交代码变更、等待审查合并的请求 |
| **单元测试** | Unit Test | 针对一个函数/模块的小粒度自动化测试 |
| **集成测试 / 端到端测试** | Integration / E2E Test | 测试多个模块或整条用户流程是否协同工作 |
| **Linter（代码检查器）** | Linter | 静态扫描代码风格、潜在 bug 的工具，如 ESLint、Ruff |
| **格式化器** | Formatter | 自动统一代码格式的工具，如 Prettier、Black |
| **类型检查器** | Type Checker | 在运行前检查变量类型是否匹配，如 TypeScript `tsc`、Pyright、mypy |
| **Pre-commit Hook（提交前钩子）** | Pre-commit Hook | `git commit` 时自动运行的脚本，常用于跑 lint/格式化，几秒内给出反馈 |
| **CI（持续集成）** | Continuous Integration | 代码推送后在服务器上自动构建、测试的流水线，如 GitHub Actions，通常需要数分钟 |
| **CD（持续交付/部署）** | Continuous Delivery/Deployment | 测试通过后自动发布到环境/生产 |
| **不稳定测试** | Flaky Test | 代码没变，有时通过有时失败的测试，会严重污染 Agent 的反馈信号 |
| **AGENTS.md** | — | 一种开放约定：放在仓库里的"给 Agent 看的 README"，写明如何构建、测试、遵守哪些规范 |
| **.env.example** | — | 环境变量模板文件，列出项目需要哪些变量（不含真实密钥） |
| **Devcontainer（开发容器）** | Dev Container | 用容器定义的可复现开发环境，所有人/Agent 环境一致 |
| **可观测性** | Observability | 通过日志（logs）、指标（metrics）、链路追踪（traces）了解系统"实际上发生了什么" |
| **结构化日志** | Structured Logging | 以 JSON 等机器可解析格式输出日志，方便检索 |
| **分布式追踪** | Distributed Tracing | 跟踪一次请求跨多个服务的完整调用链 |
| **分支保护** | Branch Protection | 禁止直接推送主分支，要求审查和检查通过才能合并 |
| **密钥扫描** | Secret Scanning | 自动发现被误提交进代码的密码、API Key |
| **CODEOWNERS** | — | 指定某些目录的负责人，改动这些目录需他们审批 |
| **Monorepo（单体仓库）** | Monorepo | 把多个应用/服务放在同一个代码仓库中管理 |
| **Skills（技能）** | Agent Skills | 按需加载的"操作说明包"，匹配到相关任务时才注入 Agent 上下文 |
| **子 Agent** | Sub-agent | 由主 Agent 派生、拥有独立上下文窗口、负责特定职责（如验证）的 Agent |
| **MCP** | Model Context Protocol | 模型上下文协议，一种让 Agent 标准化接入外部工具/数据（如 Linear、Slack、日志平台）的开放协议 |
| **上下文窗口 / Token** | Context Window / Token | 模型一次能"看到"的文本量；Token 是计费与容量的基本单位 |
| **强化学习（RL）** | Reinforcement Learning | 通过"尝试 → 获得奖励 → 调整"来训练模型的方法；可验证的任务天然能提供奖励信号 |
| **后训练** | Post-training | 在预训练之后，用指令数据、RL 等方式进一步打磨模型行为 |
| **Lean** | Lean Theorem Prover | 一种形式化证明语言与检查器，能逐步机械地验证数学证明是否正确 |
| **TDD（测试驱动开发）** | Test-Driven Development | 先写失败的测试，再写代码让它通过 |
| **左移** | Shift Left | 把检查/验证尽量提前、变便宜；本文中指"把一个领域的工作往更易检查的一端推" |
| **部落知识** | Tribal Knowledge | 只存在于老员工脑子里、Slack 聊天里，从没写下来的经验 |

---

## 2. 第一部分：人类简史给我们的启示

### 2.1 大脑长得很慢，世界却爆炸了

| 维度 | 300 万年前 | 今天 | 变化 |
| --- | --- | --- | --- |
| 脑容量 | 约 450 cc | 约 1,350 cc | 约 **3 倍**，且增长极其缓慢 |
| 世界人口 | 约 400 万（公元前 1 万年） | 约 80 亿 | 约 **2000 倍**，几乎全部发生在最近一瞬 |

**关键事实**：智人（Homo sapiens）出现于约 30 万年前，此后大脑"硬件"基本没变。

### 2.2 如果 300 万年压缩成一天

| 时间点 | 事件 |
| --- | --- |
| 晚上 9:36 | 智人出现，大脑基本定型 |
| 晚上 11:50 | 最近 2 万年开始 |
| 晚上 11:54 | 农业 |
| 晚上 11:57 | 文字 |
| 晚上 11:59:43 | 印刷术 |
| 晚上 11:59:58 | 晶体管 |
| **最后 0.1 秒** | **ChatGPT** |

> 🧠 **同样的大脑，全新的世界。** 30 万年来硬件几乎没动，改变一切的是环境。

### 2.3 人类发明的，其实是一系列"让事情可检查"的工具

| 年代 | 发明 | 它回答的问题 |
| --- | --- | --- |
| 约公元前 3200 年 | 文字 | "这是我们约定好的吗？" |
| 约公元前 3000 年 | 度量衡 | "这个分量公平吗？" |
| 1494 年 | 复式记账（帕乔利） | "账平了吗？" |
| 17 世纪 | 科学实验 | "这是真的吗？" |
| 1990 年代 | 单元测试 | "它能跑通吗？" |

**共同点**：每一项都让"分辨对错"这件事变得 **便宜**。

> ✅ **本章结论：我们没有变得更聪明，我们变得更可检查了。进步来自反馈，而不是更大的大脑。**

**🔍 学习提示**：这是整场演讲的"认知锚点"。把"模型"类比成大脑，把"代码库/工具链"类比成文明环境——后面的所有论证都是这个类比在软件工程里的展开。

---

## 3. 第二部分：Agent 是一台"猜测-检查"机器

### 3.1 在基准测试上，Agent 看起来非常聪明

SWE-bench Verified 上的解决率（厂商自报数据）：

| 时间 | 2023.10 | 2024.10 | 2025.02 | 2025.05 | 2025.09 | 2025.11 |
| --- | --- | --- | --- | --- | --- | --- |
| 解决率 | ~2%\* | 49% | 62% | 73% | 77% | **81%** |

\* 2023 年 10 月的数据来自原版、更难的 SWE-bench。

**两年时间，从几乎解决不了真实 GitHub Issue，到能解决大部分。**

### 3.2 为什么基准上表现这么好？因为每道题都自带"阅卷老师"

一个 SWE-bench 任务的流程：

```
01 真实 GitHub Issue ──► 02 Agent 写补丁 ──► 03 运行隐藏测试 ──► 04 通过 / 失败
   （来自热门开源仓库）     （不能偷看答案）     （来自真正修复它的 PR）  （没有部分分，不靠感觉）
```

> 🎯 **洞见：基准测试是地球上 Agent 就绪度最高的代码库。** 它有清晰的任务、可运行的环境、确定的判分标准。你的代码库离这个状态有多远，Agent 在你这儿的表现就会打多大折扣。

### 3.3 Agent 的工作循环

```
Read 读 → Plan 计划 → Edit 编辑 → Run 运行 → ✅ Check 检查 → Fix 修复 → (回到 Read/Plan)
```

> **模型负责猜，环境负责检查。** 每一个能被检查的步骤，都是提前抓住错误的机会。

这就引出了全场最核心的一句话：

> ## **If you can verify it, an agent can solve it.**
> ## **能验证的，Agent 就能解决。**

### 3.4 两个旋钮：验证精度 × 检查频率

把任务放在一个 2×2 矩阵里：

| | **只检查一次**（最后） | **每步都检查** |
| --- | --- | --- |
| **检查精确** | 🎯 **Long shot（碰运气的远射）**<br>学校：一考定终身的期末考<br>软件：大型迁移，最后才测一次 | 🚀 **Autopilot（自动驾驶）**<br>学校：带自动评分的习题集<br>软件：有快速测试套件的 bug 修复 |
| **检查靠感觉** | 🎲 **Coin flip（抛硬币）**<br>学校："写点很棒的东西"<br>软件："把产品做得更好" | 🧑‍🏫 **Coached（有教练指导）**<br>学校：每周有反馈的写作课<br>软件：设计师逐步审阅的 UI 打磨 |

- **纵轴 = 可验证性（Verifiability）**：检查有多精确？是客观的通过/失败，还是主观"感觉还行"？
- **横轴 = 粒度（Granularity）**：多久能检查一次？
- **目标**：把任务尽量推向右上角的 **Autopilot** 象限。

**🛠 实操翻译**：
- 想提高"精度"→ 写测试、加类型、写清楚验收标准。
- 想提高"频率"→ 拆小任务、加 pre-commit、让测试能本地秒级运行。

### 3.5 数学：为什么"小步 + 逐步检查"必胜

**场景**：一个 20 步的任务，Agent 每一步做对的概率是 90%。

**方案 A：只在最后检查一次**

$$
P_{\text{成功}} = 0.9^{20} \approx 0.12
$$

只有 **12%** 的概率整体成功——每一步的小错误会**连乘累积**。

**方案 B：每步都检查，失败最多重试 3 次**

单步连续 3 次都错的概率是 $0.1^3 = 0.001$，所以单步最终成功率为 $1 - 0.001 = 0.999$：

$$
P_{\text{成功}} = (1 - 0.1^3)^{20} = 0.999^{20} \approx 0.98
$$

成功率跃升到 **98%**。

> 📐 **数学直觉**：错误在长链条上是**乘法累积**的；而逐步检查把每一步的错误率从 $p$ 压到 $p^k$（$k$ 为重试次数），是**指数级压缩**。模型能力完全没变，变的只是"检查的位置"。

**延伸思考**：这也解释了为什么"任务分解"是长任务 Agent 的关键能力——只有能拆成可单独验证的子步骤，才能享受这个指数红利。

### 3.6 速度：快速检查 = 更多尝试机会

假设每次尝试都必须等检查结果：

| 检查方式 | 耗时 | 每小时可尝试次数 |
| --- | --- | --- |
| **Pre-commit 钩子** | 5 秒 | **720 次** |
| 本地测试 | 1 分钟 | 60 次 |
| CI 流水线 | 10 分钟 | 6 次 |
| 代码审查 | 1 天 | < 1 次 |

> ⚡ **5 秒的检查比 10 分钟的检查，每小时多出 120 倍的尝试次数**（720 ÷ 6 = 120）。

**结合 3.5 节**：检查越快 → 能重试的次数越多 → 逐步检查的指数红利越大。速度与粒度是相互放大的。

---

## 4. 理论延伸：为什么"可验证性"是 AI 时代最重要的属性

> 本节为联网扩展学习内容，帮助你理解演讲背后的理论来源。

### 4.1 Karpathy：Software 1.0 vs Software 2.0

Andrej Karpathy（OpenAI 创始成员、前特斯拉 AI 总监）提出过一个很有影响力的对比：

| | Software 1.0 | Software 2.0 |
| --- | --- | --- |
| 编程方式 | 人写明确的算法步骤 | 指定目标，让优化过程（梯度下降/RL）搜索出解 |
| 能自动化什么 | **你能"说清楚怎么做"的事**（可规定 specify） | **你能"判断做没做对"的事**（可验证 verify） |

他在 2025 年 11 月的文章《Verifiability》中指出：在新范式下，**最能预测一项工作能否被 AI 自动化的特征就是可验证性**。一个适合 AI"练习"的环境需要具备：

1. **可重置（resettable）**：可以随时重新开始一次尝试；
2. **高效（efficient）**：可以进行大量尝试；
3. **可奖励（rewardable）**：有自动化的方式给每次尝试打分。

> 🔗 对照到代码库：**可重置** = 可复现的开发环境；**高效** = 快速的测试/构建；**可奖励** = 测试、lint、类型检查给出的通过/失败信号。Agent Readiness 本质上就是在把你的代码库改造成一个好的"练习场"。

### 4.2 Jason Wei：验证不对称性与"验证者法则"

Jason Wei（思维链 Chain-of-Thought 论文作者之一）在 2025 年 7 月提出：

- **验证不对称性（Asymmetry of verification）**：有些任务**验证比求解容易得多**。例如数独——解题很难，但检查一个填好的数独是否正确只需几秒。（也有反例：有些数据处理代码，读懂别人的代码并验证它，跟自己写一遍差不多久。）
- **验证者法则（Verifier's rule）**：*训练 AI 解决某项任务的难易程度，与该任务的可验证程度成正比。所有可解且易验证的任务，终将被 AI 解决。*

他列出一个"好验证器"的五个属性，Eno 在演讲中直接引用了：

| 属性 | 英文 | 含义 | 代码库中的例子 |
| --- | --- | --- | --- |
| 客观真理 | Objective truth | 大家对"什么是好答案"有共识 | 测试断言的明确期望值 |
| 验证快速 | Fast to verify | 几秒内能判断 | pre-commit、单元测试 |
| 可规模化 | Scalable | 可并行检查大量候选 | CI 并行运行 |
| 低噪声 | Low noise | 结果可信、不随机 | 消灭 flaky test |
| 连续奖励 | Continuous / graded reward | 能体现"部分正确"，如 30%、70%、100% | 测试通过率、覆盖率 |

> 🧩 **P vs NP 直觉**：计算机科学里，NP 问题的特征就是"答案易验证但未必易求解"。这只是一个帮助理解的类比——工程任务并不严格对应复杂度理论，但"找答案难、查答案易"的不对称正是 Agent 能大放异彩的地方。

### 4.3 把理论串起来

```
可验证 ──► 可以给奖励 ──► 模型可以通过 RL 被训练好（训练时）
可验证 ──► 可以逐步检查重试 ──► Agent 可以自我纠错（使用时）
```

**同一个属性，在训练时决定模型能学会什么，在使用时决定 Agent 能做成什么。** 这就是为什么 Eno 说"在你的代码库上投资验证，比花 45 天比较哪个工具在 SWE-bench 上高 10% 更有价值"。

---

## 5. 第三部分：Agent Readiness 模型

### 5.1 大多数 Agent 失败，其实是环境失败

演讲给出三个典型失败场景：

| # | 环境缺陷 | Agent 遭遇了什么 |
| --- | --- | --- |
| 01 | **没有 pre-commit 钩子** | 等 10 分钟 CI 才知道 linter 5 秒就能告诉它的问题 |
| 02 | **环境配置没有文档** | 只能瞎猜有哪些环境变量 → 失败 → 再猜 |
| 03 | **构建步骤只存在于 Slack 聊天里** | 没有书面的方式检查自己的工作，所以它做不到 |

> 👶 **一个新员工面对这三点也会一样抓狂。** Agent 本质上就是一个"每次任务都要重新入职一遍的新同事"。

### 5.2 九大支柱，九个问题

每个支柱都对应一件 **Agent 需要能自己检查** 的事情：

| 支柱 | Agent 要问的问题 | 为什么重要 | 典型检查项 |
| --- | --- | --- | --- |
| **风格与校验** Style & Validation | 它格式正确吗？ | Linter、类型检查、格式化器能瞬间抓住低级错误，Agent 不用在语法、风格、类型错误上浪费轮次 | Linter 配置、类型检查器、格式化器、pre-commit 钩子 |
| **构建系统** Build System | 它能编译吗？ | 清晰、确定性的构建命令让 Agent 提交前能验证改动能编译运行，不用猜命令和参数 | 构建命令有文档、依赖版本锁定、VCS 命令行工具 |
| **测试** Testing | 它能工作吗？ | 快速的单元/集成测试形成紧密反馈环：跑测试 → 看失败 → 迭代 | 存在单元测试、存在集成测试、测试可本地运行 |
| **文档** Documentation | 我们这儿是怎么做的？ | 把"大家都知道"的部落知识写下来：如何搭环境、跑测试、部署、调试 | AGENTS.md、README、文档新鲜度 |
| **开发环境** Dev Environment | 我能复现吗？ | 环境一致，"在我机器上能跑"这类问题整类消失 | Devcontainer、环境变量模板、本地服务启动方案 |
| **调试与可观测性** Observability | 实际发生了什么？ | 把"它挂了"变成"它挂了，因为收到 Z 之后调用 Y 时 X 为 null" | 结构化日志、分布式追踪、指标采集 |
| **安全** Security | 可以安全上线吗？ | Agent 动作很快，自动化护栏保证它"又快又安全" | 分支保护、密钥扫描、CODEOWNERS |
| **任务发现** Task Discovery | 下一步该做什么？ | 结构良好的 Issue 和模板让 Agent 能自主找活、界定范围 | Issue 模板、Issue 标签体系、PR 模板 |
| **产品与实验** Product & Experiments | 它真的帮到人了吗？ | 让 Agent 看到功能是否被使用、改动有何影响 | 产品埋点分析、A/B 实验基础设施 |

> 📝 **版本说明**：Factory 在 2026 年 1 月发布该功能时的博客写的是"八大支柱"（含 Code Quality），AI Engineer 演讲中也说的是八个；目前官方文档与斯坦福 PPT 已整理为 **九大支柱**。学习时以九支柱为准，理解其背后的"可检查"逻辑即可。

**🧠 记忆技巧**：按"写代码时 → 交付时 → 上线后 → 找下一件事"的时间线记：
- 写代码时：风格校验 → 构建 → 测试 → 文档 → 开发环境
- 交付时：安全
- 上线后：可观测性 → 产品与实验
- 下一件事：任务发现

### 5.3 五个就绪等级

| 等级 | 名称 | 关键词 | 描述 | 示例检查项 |
| --- | --- | --- | --- | --- |
| L1 | **Functional 可运行** | 代码能跑 | 代码能运行，但需要手动配置，缺少自动化校验；检查靠人工 | README、linter、类型检查器、单元测试 |
| L2 | **Documented 有文档** | 写下来 | 基本的文档和流程存在，工作流被写下来，有部分自动化 | AGENTS.md、devcontainer、pre-commit 钩子、分支保护 |
| L3 | **Standardized 标准化** | 强制执行 | 流程清晰、有文档，且**通过自动化强制执行**；全组织统一 | 集成测试、密钥扫描、分布式追踪、指标 |
| L4 | **Optimized 已优化** | 可度量 | 快速反馈环 + 数据驱动改进，持续度量生产力 | 快速 CI 反馈、稳定的部署频率、不稳定测试检测 |
| L5 | **Autonomous 自主** | 放手 | 系统可自我改进，复杂需求能自动分解并并行执行 | 自我改进的系统 |

**规则**：

- 所有仓库从 L1 开始；**通过某一级 80% 的检查项，才能解锁下一级**（门控式晋级）。
- 检查项分两种作用域：
  - **仓库级**：整个仓库评估一次（如是否有 CODEOWNERS、是否开启分支保护）；
  - **应用级**：Monorepo 中每个应用单独评估（如每个应用是否配置了 linter），结果显示为 `3 / 4`（4 个应用中 3 个通过）。

> 🔑 **核心规律：检查越多，自主权越大。** L1 检查靠人；L3 检查自动化并强制；L4+ 反馈足够快，可以放心让 Agent 长时间独立运行。

### 5.4 案例：优秀的项目，不同的就绪度

（Factory 公开报告，2026 年 1 月）

| 项目 | 等级 | 特点 |
| --- | --- | --- |
| **CockroachDB**（分布式 SQL 数据库） | **L4 · Optimized** | 大量 CI、全面的测试；清晰的文档和安全扫描 |
| **Express**（Node.js Web 框架） | **L2 · Documented** | 极其流行、久经考验；但缺少若干基础信号 |

> ⚠️ **流行 ≠ 可检查。** 一个项目被很多人用、代码质量很好，并不代表 Agent 在里面能高效自检。

### 5.5 就绪度会产生复利

```
        ┌──► 更好的检查 ──┐
        │                 ▼
   再投入进去          Agent 做更多事
        ▲                 │
        └── 工程师省出时间 ◄┘
```

- **对所有 Agent 都有帮助**，不只是某一家的产品——换工具也不会白做。
- **对所有人类也有帮助**——这正是新同事入职第一天需要的东西。

### 5.6 官方工具：`/readiness-report` 与 `/readiness-fix`

Factory 提供的配套工具（Factory App 或 Droid CLI 中可用）：

| 工具 | 作用 |
| --- | --- |
| `/readiness-report` | 扫描当前仓库（Monorepo 会先识别所有可独立部署的应用），按五个等级评估所有检查项，输出：当前等级、各检查项得分、**2~3 条最高优先级的改进建议** |
| `/readiness-fix` | 自动修复未通过的检查项 |
| Dashboard / API | 在组织层面查看所有仓库的就绪度，或通过 API 程序化获取报告 |

> 💡 即使不用 Factory，你也可以把 5.2 节的表格当成自查清单，或者让你常用的编码 Agent 按这张表审计你的仓库。

---

## 6. 演讲精讲：从规范到生产的自主闭环

> 本节整理自 Eno Reyes 在 AI Engineer Code 2025 的演讲《Making Codebases Agent Ready》，是 PPT 内容的展开与补充。

### 6.1 工作流的转变：Specify → Generate → Verify → Iterate

传统流程：理解问题 → 设计方案 → 写代码 → 测试。

Agent 时代的显式循环：

| 步骤 | 做什么 |
| --- | --- |
| 1️⃣ **Specify 规定** | 描述期望行为和解必须满足的约束（验收标准） |
| 2️⃣ **Generate 生成** | 让 Agent 产出候选实现 |
| 3️⃣ **Verify 验证** | 用自动化检查 + 人类判断来验证 |
| 4️⃣ **Iterate 迭代** | 根据检查结果修改实现，或澄清规范 |

**关键变化**：验收条件要在生成**之前和之中**就可用，而不是事后补。这也是各类工具纷纷推出"规划模式 / 规范模式（Spec Mode）"的原因。

### 6.2 人类能容忍的缺口，会变成 Agent 的天花板

- 人类团队可能容忍 50%~60% 的测试覆盖率 + 手工测试补位；
- 一个"每三次失败一次"的不稳定构建，老员工知道"再跑一次就好"；
- 但 Agent 没有这些隐性判断。**这些缺口在人类组织里能凑合运转，却会直接限制 Agent 在编码、审查、文档、测试上的能力。**

### 6.3 Linter 要"足够有主见"

> "你的 linter 是否有主见到：编码 Agent 写出的代码一定达到你们资深工程师的水准？"

普通 linter 只能抓语法问题，但可能放过资深工程师会拒绝的代码。**Agent Readiness 要求把越来越多的"质量判断"变成可执行的检查。**（这是方向，不是说 lint 能完全替代资深工程师的判断。）

### 6.4 先做到单任务近 100%，再谈并行

- 并行跑多个 Agent 之前，必须先能可靠地判断**每一个 PR** 是否达成目标、是否会搞坏生产。
- 基本单元是：**清晰的结果 + 预期的做法 + 验证方法**。
- 如果连单个变更都评估不了，产出更多变更只会堆积更多待审查负担。
- **更好的搜索找不回从未写下的验收标准**——Agent 再会找文件，也找不到组织从未明确过的规则。

### 6.5 从"资深 vs 初级"的差异中发现缺失的规则

如果资深工程师用 Agent 效果很好，而初级工程师很挣扎——问题可能不是初级工程师不会用工具，而是**资深工程师在隐性地补充了某些没写下来的约定或校验**。把它们找出来、写成检查，就能把知识从少数人扩展到所有人和所有 Agent。

> 🌰 **Google/Meta 的例子**：一个毫无背景的应届生，可以把 YouTube 某个按钮的圆角改大一点，而不会让十亿用户的服务宕机——不是因为他懂所有上下文，而是因为周围有大量检查在保护部署。

### 6.6 "烂测试也比没测试好"

Factory 工程师 Alvin 的一句话：**"A slop test is better than no test."**

前提条件：这个初始测试在改动正确、基本符合规范时应该能通过。它的价值在于：
- 给人一个可以改进的具体起点；
- 给未来的 Agent 一个可以模仿的模式（仓库里已有的测试会告诉 Agent "我们这里测试长什么样"）。

示例——把"账户名要去空格并小写、空名要报错"这条口头约定变成可执行的检查：

```typescript
import assert from "node:assert/strict";
import test from "node:test";
import { normalizeAccountName } from "./account-name.js";

test("account names follow the project convention", () => {
  assert.equal(normalizeAccountName("  ALICE  "), "alice");
  assert.equal(normalizeAccountName("alice"), "alice");
  assert.throws(() => normalizeAccountName("   "));
});
```

**用 Agent 改善 Agent 的工作环境**：让 Agent 检查 lint 规则哪里不够有主见、帮你生成测试——形成正向飞轮。

### 6.7 终极图景：从 Issue 到生产

```
客户报告问题 → 自动建 bug 工单 → 编码 Agent 领取 → 实现修复并请开发者审查 → 开发者批准 → 合并并部署上线
```

- Eno 设想这个闭环可以在 **1~2 小时** 内完成（设想，非实测数据），且**保留了人类审批**。
- 他的判断：技术上已经可行，限制因素是组织的验证能力而非 Agent 能力。
- 他的预测：投资这些基础，有望带来 **5~7 倍**而不是 1.5~2 倍的提升（预测，非实测）。

> 🧭 **组织层面的真正要求**：AI 不会自动补上缺失的工程标准。团队必须决定接受什么样的结果，把这些决定编码成检查，并投入让反馈变得可靠。

---

## 7. 实战案例：Basis 如何把 Monorepo 改造成 Agent 友好型

> 整理自 Basis（一家 AI 原生会计公司）Atlas 团队技术负责人 Michael Crabtree 的文章《How We Made Our Monorepo Ergonomic for Agents》（2026-05-19）。这是 Agent Readiness 理念的一次完整工业落地。

### 7.1 成果先行

| 指标 | 三个月内的变化 |
| --- | --- |
| 人均 Token 用量 | **提升 5 倍以上** |
| 每周提交速度（commit velocity） | **提升 2.5 倍** |
| 工程师使用多个 worktree 并行管理多个 Agent | **100%** |

> 为什么用"Token 用量"当指标？假设是：如果解决了让 Agent 表现差的问题，工程师就更信任 Agent、同时管理更多 Agent，Token 用量自然上升。再用提交速度确认这是真实的生产力提升而非浪费。

### 7.2 核心认知：代码库同时是两样东西

1. 在生产环境运行的**源代码**；
2. 编码 Agent 用来做决策的**上下文**。

> 🔁 **人类新员工每月入职几个，Agent 每次任务都要"入职"一次。** 入职次数从每月几次变成每月几千次，任何小的不一致、矛盾和缺口都会被迅速放大。

### 7.3 Agent 原生代码库的五大原则

| 原则 | 英文 | 含义 |
| --- | --- | --- |
| ① **权威性** | Canonicality | 每个文件要么是"系统当下状态"的真相来源，要么是"意图与历史"的记录，**绝不两者兼是** |
| ② **就近性** | Localization | 上下文尽量放在使用它的地方；只有变得更通用时才往上提 |
| ③ **可验证性** | Verifiability | Agent 必须能测试自己的工作（子 Agent 角色、pre-commit、测试） |
| ④ **互操作性** | Interoperability | 架构中没有任何一层绑定单一厂商——AI 变化太快，不能押注一个平台 |
| ⑤ **默认拒绝** | Default-no | 任何自动加载的上下文都必须"挣得一席之地"；默认是"不加"，每一行都要被论证过 |

> 💬 为什么第 ⑤ 条刻意用否定式表达？因为当默认是"加进去"，文件会无限膨胀；当默认是"不加"，每一行都得说明存在的理由。**没带来行为改变的 Token，是每个会话、每个 Agent、每个工程师都要交的税。**

### 7.4 权威 vs 非权威：给 Agent 一张"可信度地图"

| ✅ 权威（Canon）：关于"今天"的真相 | 📜 非权威（Not Canon）：意图、历史、假设 |
| --- | --- |
| **AGENTS.md**（根目录与嵌套的）：我们在这里怎么做事 | **.specs/**：仓库内的产品与技术规范 |
| **Skills**：跨领域的操作流程，匹配时加载 | **Linear 工单**：进行中的项目规范、对齐阶段的决策 |
| **docs/**：持久的架构与入职文档 | **.notes/**：贴近改动记录的权衡与取舍 |
| **Docstring**：契约、不变量、副作用 | **PR 描述**：这个 diff 为什么存在、放弃了什么 |
| **代码注释**：就地说明非显而易见的推理 | **Slack 讨论**：未被记录的对话"化石" |

**为什么还要让 Agent 看到非权威信息？** 因为它在复杂情况下很有价值，比如回答"我们当初为什么这样写？"。过去答案是私信写这行代码的人，现在答案是 `.notes/`。

**风险点**：把非权威当权威。一张 Linear 工单可能描述了一个从未实现、或实现方式完全不同的功能——Agent 当真就会对世界状态产生误判。

### 7.5 六层架构

```
┌─────────────────────────────────────────────────────┐
│  上下文金字塔（Layer 1-3）                              │
│   Layer 2  嵌套 AGENTS.md  —— 按目录加载（100+ 个）      │
│   Layer 3  Skills          —— 匹配任务时按需加载          │
│   Layer 1  根 AGENTS.md    —— 每次会话都加载（约 300 行） │
├─────────────────────────────────────────────────────┤
│  Layer 4  子 Agent 角色（.agents/roles/）              │
│  Layer 5  统一 MCP（Linear / Slack / 日志 / 分析 / DB）  │
│  Layer 6  测试与 pre-commit（最后一道防线）              │
└─────────────────────────────────────────────────────┘
```

| 层 | 内容 | 要点 |
| --- | --- | --- |
| **L1 根 AGENTS.md** | 工程原则、工作流、沟通方式、类型安全、命名 | 约 300 行，每个 Agent 每次都读，是仓库中杠杆最高的文件；对 Claude 用户只是做了个软链接（symlink）到 AGENTS.md |
| **L2 嵌套 AGENTS.md** | 100 多个，各自限定在本目录 | 窄而具体，可操作。如 migrations 目录：**永远不要编辑已提交的迁移，总是新建一个** |
| **L3 Skills** | `.agents/skills/`：后端架构、前端模式、测试标准、文档约定、领域知识 | 跨目录知识放这里，按需加载 |
| **L4 子 Agent 角色** | `.agents/roles/`：6 个以上专职 Agent，各有独立上下文窗口 | **verifier**：跑与 diff 相关的测试和 pre-commit，报告通过/失败及可操作的失败细节；**standards-enforcer**：按所有适用的 AGENTS.md 和 Skills 检查代码，查过度防御式编程、死代码、缺失测试 |
| **L5 统一 MCP** | Linear、Slack、Better Stack（日志）、PostHog（分析）、开发数据库 | Agent 调查 bug 时能自己拉工单、看日志、查库，不用工程师手动复制上下文 |
| **L6 测试** | Ruff（Python lint/格式化）、BasedPyright（类型检查）、ESLint + Prettier（TS），外加大文件、私钥、合并冲突检测 | 即使 Agent（或人）忘了遵守规范，也能被强制拦截 |

**嵌套 AGENTS.md 示例**（后端目录，导入规则）：

```markdown
### Imports
All Python imports go at the top of the file.
- Strongly avoid inline/deferred imports to work around circular imports.
  A circular import means the module structure is wrong — fix the structure instead.
- Only acceptable reason for a non-top-level import: the imported module has
  expensive load-time side effects and the calling code path is rarely executed.
```

**verifier 子 Agent 配置示例**（注意：用低推理强度、低啰嗦度的模型做验证，省钱又够用）：

```yaml
id: verifier
name: verifier
description: Runs diff-scoped tests, pre-commit hooks, and relevant lint/type checks,
  then reports pass/fail status with actionable failure details.
codex_model_reasoning_effort: low
codex_model_verbosity: low
```

### 7.6 重写 AGENTS.md：三大常见问题

| 问题 | 反例 | 正确做法 |
| --- | --- | --- |
| ❌ **在"描述"而不是"指令"** | "SRC 是我们放所有源代码的地方。"（Agent 早就知道 src/ 是什么） | 写能改变行为的操作指令："使用严格类型检查"、"永远不要用内联 import 绕开循环依赖，去修模块结构" |
| ❌ **所有规则都是"必须遵守"** | 满屏 MUST / CRITICAL / IMPORTANT | **当一切都重要，就没有什么重要。** 去掉多余强调，把规则放到真正适用的位置 |
| ❌ **跨目录知识放错位置** | 某产品的业务细节只写在后端 AGENTS.md，前端也需要却看不到 | 跨目录知识放进 **Skills** 按需加载（docs/ 改为专门面向人类的材料） |

**AGENTS.md 五条写作规则**：

1. **指令质量**：为 Agent 写，而不是为人写。它要解释 Agent 如何操作，而不是变成永久的人类文档。
2. **层级优先放置**：放在完全拥有该信息的最具体目录；只有真正共享时才往上提。
3. **韧性引用**：用描述性名称而非精确文件路径——路径会变，描述更稳定。
4. **纯文本、便于搜索**：不要 ASCII 艺术、二进制内容或妨碍搜索/解析的格式。
5. **默认拒绝**：Agent 在这个目录的大多数任务中是否合理地需要这条信息？不需要就放到别处。

**留在根 AGENTS.md 中的规则示例**：
- 权威上下文是可信赖的决策依据；非权威上下文代表意图、笔记、临时状态等。
- 优先使用提前返回（early return），而不是深层嵌套。
- 写出不必参考其他文件就能看懂的代码。明确胜过聪明。

### 7.7 大扫除：用 Agent 修复 Agent 传播的坏模式

- 用编码 Agent 按新规范审计每个目录，找出 9 个项目、数千行违规代码；
- 再派 Agent 按清晰的新指令重写——**曾经吸收并传播坏模式的 Agent，现在被用来修复它们**；
- 重写涉及约 **20%~30% 的代码库**；
- Agent 重构有天然极限：有些技术债有结构性原因，Agent 解决不了。优先级：① Agent 能修的高频可见区域 → ② 需要人介入的可见区域 → ③ 其余留给日常流程。

> 📌 **没有捷径。** Agent 原生代码库对局部正确性的要求比纯人类代码库更高，因为**每个文件都是上下文**，而 Agent 在不停地入职。

### 7.8 如何防止上下文"腐烂"

| 机制 | 做法 |
| --- | --- |
| **明确负责人** | 每个权威文件顶部 YAML frontmatter 都有 `owner` 字段；CI 检查新 skill / 非生产 markdown 必须有负责人 |
| **CI 确定性检查** | 合并前校验 frontmatter、该写指令的地方没写成描述、语法正确 |
| **每日扫描器** | 全面扫描 Skills 与 AGENTS.md：过时内容、相互矛盾、重复指令、失效引用、近期改动缺失的上下文 |
| **每日修复 Worker** | 领取扫描器开的工单，做小范围修复 |

> 🔑 **能自动维护的前提是先定义了"什么是权威"。** 权威上下文按定义必须自洽，所以扫描器可以查矛盾；非权威上下文允许自相矛盾（规范会改、计划会废弃）。不划清这条线，两类都没法扫描。

### 7.9 闭合验证环：测试标准化

- **跨团队配对**：一名工程师负责传统测试基础设施（单元/集成测试、fixture、marker、CI 集成），另一名负责把测试标准嵌入 Agent 行为层；
- 写了一个**测试 Skill**：定义需要什么测试、何时必须写、如何组织；
- 反复评估这份指南能否诱导 Agent 写出想要的测试——有时太啰嗦，有时又极其偷懒，调准措辞需要功夫，但值得。

### 7.10 Basis 案例 × Agent Readiness 支柱对照

| Basis 的做法 | 对应支柱 |
| --- | --- |
| Ruff / BasedPyright / ESLint / Prettier + pre-commit | 风格与校验 |
| 测试 Skill + 测试基础设施 + verifier 子 Agent | 测试 |
| 根/嵌套 AGENTS.md、Skills、权威地图 | 文档 |
| MCP 接入 Better Stack 日志、开发数据库 | 可观测性 |
| 私钥检测、standards-enforcer | 安全 |
| MCP 接入 Linear | 任务发现 |
| MCP 接入 PostHog | 产品与实验 |
| 每日扫描器 + 修复 Worker | 迈向 L5 自我改进 |

---

## 8. 第四部分：超越代码——任何领域的"左移"

### 8.1 "Everything's computer."

演讲引用了一句 2025 年的名梗（特朗普坐在特斯拉里说的）："Everything's computer."——**他比自己以为的更正确**：代码只是"形式化"的一种。

### 8.2 可检查性光谱

```
便宜可查 ◄───────────────────────────────────────────► 昂贵难查
  数学      代码       会计       芯片     法律         医学       品味
证明检查器  测试和类型  账目平衡   仿真    审查和判例   临床试验   你的直觉
```

> ⬅️ **任何领域要迎接 Agent，都要把自己的工作往左移**——让检查变得更便宜、更快、更客观。

### 8.3 检查便宜的地方，Agent 先到

| 领域 | 检查方式 | 现状 | 检查成本 |
| --- | --- | --- | --- |
| **数学** | 证明检查器给每一步打分 | DeepMind 的 AlphaProof 借助 Lean 证明检查器，2024 年达到国际数学奥林匹克（IMO）银牌水平；2025 年出现金牌水平的成绩 | 便宜 |
| **代码** | 测试和类型给每次改动打分 | 两年内从约 2% 到约 80% 的真实 GitHub Issue 解决率 | 便宜 |
| **医学** | 最终检查是临床试验 | 每次检查要数年；机会在于发展出人们能信任的更快检查 | 慢 |

### 8.4 给每个人的任务

> ## **你的工作：构建检查器。**
> 稀缺的技能，是把"好"变成机器能验证的东西。

**🛠 跨领域迁移练习**：
- 你是**产品经理**？把"用户体验更好"变成可测量的指标与实验。
- 你是**设计师**？把设计规范变成可自动校验的 design token 与视觉回归测试。
- 你是**内容/运营**？把"写得好"拆成可检查的清单（事实核对、术语一致、格式规范）。
- 你是**数据分析师**？给数据管道加上数据质量断言（行数、空值率、取值范围）。

---

## 9. 动手作业：一个下午让项目达到 Agent-Ready

### 9.1 六项清单

- [ ] **写一个 `AGENTS.md`**：用平实的语言写清如何构建、测试、运行。
- [ ] **添加 `.env.example`**：不让 Agent 猜有哪些环境变量。
- [ ] **一条命令跑全部测试**：只要一条，并写进 AGENTS.md。
- [ ] **先写失败的测试**：再让 Agent 去修 bug（TDD 思路）。
- [ ] **提交时自动 lint 和格式化**：pre-commit 钩子，5 秒反馈。
- [ ] **运行 `/readiness-report`**：看清自己的等级，修复最大的缺口。

### 9.2 模板：AGENTS.md（融合 Basis 写作规则）

```markdown
# AGENTS.md

## Setup
- Install deps: `pnpm install`
- Copy env template: `cp .env.example .env` (ask a human for real secrets; never invent values)
- Start local services: `docker compose up -d`

## Verify your work (run before every commit)
- All checks in one command: `pnpm check`  (= lint + typecheck + unit tests)
- Single test: `pnpm vitest run -t "<test name>"`
- Fix every lint, type, and test error before proposing a PR.

## Code conventions
- Use strict TypeScript. Do not use `any`; narrow types instead.
- Prefer early returns over deep nesting.
- Never edit committed database migrations; always add a new one.
- Add or update tests for any behavior you change.

## PR rules
- Title format: [<package>] <Title>
- Describe *why* the change exists, not just what changed.

## Where to find more
- Domain knowledge for billing: see the "billing" skill.
- Plans and specs in `.specs/` describe intent, not current behavior. Verify against code.
```

> ✍️ **写作检查**：每一行是不是"指令"而不是"描述"？是不是大多数任务都需要？有没有到处喊 MUST？

### 9.3 模板：.env.example

```bash
# Database
DATABASE_URL=postgres://user:password@localhost:5432/app_dev

# Third-party APIs (ask the team for real values)
STRIPE_API_KEY=sk_test_xxx
OPENAI_API_KEY=

# Feature flags
ENABLE_NEW_CHECKOUT=false
```

### 9.4 模板：pre-commit 配置（Python 项目示例）

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff          # lint
        args: [--fix]
      - id: ruff-format   # format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-added-large-files
      - id: detect-private-key
      - id: check-merge-conflict
```

安装：`pip install pre-commit && pre-commit install`。（JS/TS 项目可用 husky + lint-staged 达到同样效果；版本号请以各工具最新版为准。）

### 9.5 推荐的推进路线

| 阶段 | 目标 | 行动 |
| --- | --- | --- |
| 第 1 天 | 冲 L2 | AGENTS.md、.env.example、一键测试、pre-commit、分支保护 |
| 第 1~2 周 | 冲 L3 | 集成测试、密钥扫描、CODEOWNERS、结构化日志、Issue/PR 模板 |
| 第 1~2 月 | 冲 L4 | 加速 CI、检测并消灭 flaky test、度量部署频率；引入 verifier 子 Agent |
| 持续 | 迈向 L5 | 自动化上下文维护（扫描器 + 修复 Worker）、任务自动分解与并行 |

---

## 10. 常见误区

| ❌ 误区 | ✅ 正解 |
| --- | --- |
| "Agent 不好用，等下一代模型就好了。" | 模型已经够强；在不可检查的环境里，再强的模型也会失败。投资环境对所有模型都有效 |
| "花大量时间选 SWE-bench 分数最高的工具。" | 工具差 10% 远不如环境改善带来的提升；环境改善还能惠及所有工具 |
| "项目很流行、代码很好，就适合 Agent。" | 流行 ≠ 可检查（Express 仅 L2） |
| "AGENTS.md 写得越多越好。" | 默认拒绝：每一行都要改变 Agent 行为；描述性内容、不常用知识应移走或放进 Skills |
| "所有规则都标成 MUST 更保险。" | 一切都重要 = 没有重要的。用措辞体现真实优先级 |
| "有 CI 就够了。" | 10 分钟的 CI 每小时只能试 6 次；需要 5 秒级的 pre-commit 和本地测试 |
| "没有好测试就先别写。" | 烂测试也比没测试好——它是可改进的起点，也是 Agent 可模仿的模式 |
| "先上多 Agent 并行提速。" | 单任务成功率接近 100% 之前，并行只会放大审查负担 |
| "Agent 能搜索代码库，就能知道我们的规矩。" | 搜索找不回从未写下的规则 |
| "Linear 工单/规范文档也是真相。" | 区分权威与非权威；规范是意图，代码与 AGENTS.md 才是现状 |

---

## 11. 自测题（附答案）

> 先独立作答，再对照本节末尾的参考答案。

**Q1.** 演讲认为 Agent 失败的主要原因是什么？
**Q2.** 一个 20 步任务，每步正确率 95%，只在最后检查一次，整体成功率约多少？若每步检查、最多重试 2 次呢？
**Q3.** "两个旋钮"分别是什么？最理想的象限叫什么？
**Q4.** 为什么 pre-commit 钩子比 CI 对 Agent 更重要？请用数字说明。
**Q5.** Jason Wei 提出的"验证者法则"是什么？
**Q6.** Agent Readiness 晋级规则是什么？Monorepo 中 `3 / 4` 是什么意思？
**Q7.** Basis 的"权威 / 非权威"划分解决了什么问题？`.notes/` 属于哪一类？
**Q8.** 写 AGENTS.md 时，"SRC 是我们放源代码的地方"这句话有什么问题？
**Q9.** "把工作左移"在本文中是什么意思？举一个你所在领域的例子。

**📋 参考答案**

1. 环境（可检查性不足），而不是模型能力。
2. 只检查一次：$0.95^{20} \approx 0.36$，约 36%。每步检查、最多尝试 2 次：单步成功率 $1 - 0.05^2 = 0.9975$，整体 $0.9975^{20} \approx 0.95$，约 95%。
3. 验证精度（可验证性）与检查频率（粒度）；右上角"Autopilot 自动驾驶"象限——检查精确且每步都能检查。
4. 5 秒 pre-commit 每小时可尝试 720 次，10 分钟 CI 只有 6 次，相差 120 倍；尝试次数越多，逐步检查 + 重试的成功率红利越大。
5. 训练 AI 解决某任务的难易度与该任务的可验证程度成正比；所有可解且易验证的任务终将被 AI 解决。
6. 必须通过当前等级 80% 的检查项才能解锁下一级；`3 / 4` 表示该应用级检查项在 4 个应用中有 3 个通过。
7. 避免 Agent 把意图/历史（如未实现的工单）当成系统现状；同时让上下文自动维护成为可能（权威内容必须自洽，可扫描矛盾）。`.notes/` 属于非权威。
8. 它是"描述"而不是"指令"，Agent 早就知道 src/ 的含义，这行字不会改变行为，违反"默认拒绝"原则，白白消耗每次会话的 Token。
9. 把一个领域的工作往"更便宜、更快、更客观可检查"的方向推进。例如：把"报告写得好"拆成事实核对、数据一致性、格式规范等可自动检查项。

---

## 12. 参考资料

| 资料 | 链接 |
| --- | --- |
| Eno Reyes 演讲视频：Making Codebases Agent Ready（YouTube） | https://www.youtube.com/watch?v=ShuJ_CN6zr4 |
| AI Engineer 演讲整理页 | https://ai.engineer/talks/making-codebases-agent-ready |
| Basis：Making Our Monorepo Ergonomic for Agents（X 文章） | https://x.com/trybasis/status/2056881705269580023 |
| Basis 博客原文 | https://www.getbasis.ai/blogs/how-we-made-our-monorepo-ergonomic-for-agents |
| Factory 文档：Agent Readiness 总览 | https://docs.factory.ai/agent-readiness/overview |
| Factory 文档：/readiness-report 命令 | https://docs.factory.ai/agent-readiness/readiness-report |
| Factory 博客：Introducing Agent Readiness（2026-01-20） | https://factory.ai/news/agent-readiness |
| Andrej Karpathy：Verifiability（2025-11-17） | https://karpathy.bearblog.dev/verifiability |
| Jason Wei：Asymmetry of verification and verifier's rule | https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law |
| AGENTS.md 开放规范 | https://agents.md/ |

---

> 🌱 **结语**
> **Don't wait for a smarter brain. Build a smarter world.**
> 别等一颗更聪明的大脑——去建造一个更聪明的世界。
