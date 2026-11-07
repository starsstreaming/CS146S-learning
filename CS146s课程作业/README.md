# Assignments for CS146S: The Modern Software Developer

This is the home of the assignments for [CS146S: The Modern Software Developer](https://themodernsoftware.dev), taught at Stanford University fall 2026.

## 作业导航与同步来源

| 周次 | 主题 | 本地入口 |
| --- | --- | --- |
| Week 1 | 捕获并分析编码 Agent 会话 | [作业要求](week1/assignment.md) · [作答提纲](week1/writeup.md) |
| Week 2 | MCP Server 与认证 | [作业要求](week2/assignment.md) · [运行说明](week2/README.md) · [作答提纲](week2/writeup.md) |
| Week 3 | 编写 Agent Skill | [作业要求](week3/assignment.md) · [作答提纲](week3/writeup.md) |
| Week 4 | 探索陌生仓库，编写并验证 AGENTS.md / CLAUDE.md | [作业要求](week4/assignment.md) · [作答提纲](week4/writeup.md) |
| Week 5 | 评估三个仓库的 Agent Readiness（智能体就绪度）并比较结果 | [作业要求](week5/assignment.md) · [作答提纲](week5/writeup.md) |

Week 4–5 的 `assignment.md` 与 `writeup.md` 于 **2026-11-07** 从[官方作业仓库](https://github.com/mihail911/modern-software-dev-assignments)原样同步，固定来源提交为 [`df18839`](https://github.com/mihail911/modern-software-dev-assignments/commit/df18839a8174ca57edad89c03948bd295459c9c0)：[Week 4 原文](https://github.com/mihail911/modern-software-dev-assignments/tree/df18839a8174ca57edad89c03948bd295459c9c0/week4) · [Week 5 原文](https://github.com/mihail911/modern-software-dev-assignments/tree/df18839a8174ca57edad89c03948bd295459c9c0/week5)。后续刷新时应对照来源差异，保留已经填写的个人作答。

当前 Week 4–5 仅包含作业要求和未填写的作答模板，尚未编写目标仓库的 Agent 配置或运行 Droid 就绪度报告。学习时可配合[第 7 节：定制 Agent 配置](../CS146S_第07节课_2026-10-13_定制Agent配置.md)和[第 10 节：Agent Readiness 与可验证性](../CS146S_第10节课_2026-10-22_AgentReadiness与可验证性.md)阅读。

## Repo Setup
These steps work with Python 3.12.

1. Install Anaconda
   - Download and install: [Anaconda Individual Edition](https://www.anaconda.com/download)
   - Open a new terminal so `conda` is on your `PATH`.

2. Create and activate a Conda environment (Python 3.12)
   ```bash
   conda create -n cs146s python=3.12 -y
   conda activate cs146s
   ```

3. Install Poetry
   ```bash
   curl -sSL https://install.python-poetry.org | python -
   ```

4. Install project dependencies with Poetry (inside the activated Conda env)
   From this directory (`CS146s课程作业/`, which contains `pyproject.toml`), not the outer learning repository root:
   ```bash
   poetry install --no-interaction
   ```

## Local tests before account setup

From `CS146s课程作业/` after installing dependencies:

```bash
poetry run pytest -q
```

The tests use local fixtures, mocked HTTP responses, and an in-process MCP client. They do not require a school account, a browser download, or a model API key. Dependency installation still needs network access. Passing these tests does not verify a real school login or an agent client's stdio integration.

For the real Hunnu EAMS integration, continue with the [Week 2 setup](week2/README.md). For a reading-to-practice plan and assignment completion criteria, see the [learning guide](../LEARNING_GUIDE.md).
