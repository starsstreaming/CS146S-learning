# CS146S 听课笔记

斯坦福 2026 秋季 [CS146S: The Modern Software Developer](https://themodernsoftware.dev) 的个人记录。
这里不是官方仓库。课件、课堂材料和作业原文归课程方。`个人补充` 是对照当周材料整理的中文讲解.

## 目录

听课和作业分开放。

```text
CS146S The Modern Software Developer/     按上课日期
  └─ 官方资源/                            课件、示例、当堂发的配置
  └─ 个人补充/                            中文讲解
CS146s课程作业/                           作业快照，目前到 week 2
```

某一节想重看，先读讲解开头的「一分钟速览」，再按需要翻 PDF。做作业只进 `CS146s课程作业/`，笔记目录不参与安装。

## 第 01 节课 · 9 月 22 日

这节课问的是：代码可以由模型来写之后，开发者还剩下什么。后半段用大约 200 行搭了一个最小的编程智能体，把「智能体就是一个带工具的循环」落到能跑的代码上。

- [中文讲解](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/个人补充/CS146S_第01节课_2026-09-22_现代软件开发者与最小可用编程Agent.md>)
- [把这个小智能体逐段拆开](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/个人补充/blog_coding_agent.md>)
- [课件 PDF](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/官方资源/Lecture 9_22_26.pdf>)
- [课堂示例](<CS146S The Modern Software Developer/CS146S_第01节课_2026-09-22/官方资源/coding_agent_from_scratch_lecture.py>)

## 第 02 节课 · 9 月 24 日

上节课是骨架，这节课拆真实产品的外壳：系统提示、项目配置、工具列表、计划模式、技能、子智能体、钩子，以及把历史压成摘要。讲解是对着下面这些文件写的。

- [中文讲解](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/个人补充/CS146S_第02节课_2026-09-24_现代编码智能体解剖.md>)
- [课件 PDF](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/Lecture 9_24_26.pdf>)
- [system_prompt.md](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/system_prompt.md>)
- [tool_list.md](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/tool_list.md>)
- [config_files.md](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/config_files.md>)
- [plan_mode.md](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/plan_mode.md>)
- [subagent_prompt.md](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/subagent_prompt.md>)
- [compaction_prompt.md](<CS146S The Modern Software Developer/CS146S_第02节课_2026-09-24/官方资源/compaction_prompt.md>)

## 作业

作业原文是英文，说明在各周的 `assignment.md`，作答提纲在 `writeup.md`。Python 环境沿用课程仓库的装法，见 [CS146s课程作业/README.md](CS146s课程作业/README.md)。

| 周 | 要做的事 | 说明 |
| --- | --- | --- |
| Week 1 | 用代理抓住一次真实的 Claude Code 会话，把请求拆开 | [assignment.md](CS146s课程作业/week1/assignment.md) |
| Week 2 | 给一个第三方 API 做 MCP server。重点是工具好不好被智能体调用，以及 OAuth | [assignment.md](CS146s课程作业/week2/assignment.md) |

后面的课和作业仍按这个分法往里加：一节课一个日期目录，一周作业一个 `weekN/`。

## 来源

- 课程页面：<https://themodernsoftware.dev>
- 作业上游：<https://github.com/mihail911/modern-software-dev-assignments>

课表、评分和材料以课程页面为准。课件和作业文本的版权归课程方。
