# 100 行代码手搓一个 AI 编程助手：看懂 Agent，只需要看懂一个循环

> 不用框架、不用 LangChain，只用 OpenAI SDK 加三个文件工具，就能让大模型自己读你的代码、自己改文件。这篇文章带你把核心代码逐行拆开，看完你会发现：所谓 Agent，本质就是一个"套娃循环"。

---

## 一、先说一下这个程序能干嘛

运行之后，它会变成一个命令行里的对话窗口。你可以直接用人话指挥它：

```
You: 帮我看看 main.py 里有没有 bug
```

接下来神奇的事情发生了——它不是凭空猜，而是：

1. 先调用 `list_files` 看看你目录里有什么文件；
2. 再调用 `read_file` 把 `main.py` 读出来；
3. 分析完之后告诉你 bug 在哪；
4. 你说"帮我改了"，它就调用 `edit_file` 直接改你磁盘上的文件。

也就是说，**大模型不仅能"说"，还能"动手"了。** 这就是现在大家常挂在嘴边的 Agent（智能体）。

而实现它，核心代码只有 100 行左右。下面我们就拆开看。

---

## 二、整体结构：三块拼图

整个程序可以分成三部分，先看个全景图：

```
┌─────────────────────────────────────────────┐
│              run_coding_agent_loop          │
│         （对话主循环，本文的主角）            │
└──────────────┬──────────────┬───────────────┘
               │              │
      ┌────────▼─────┐   ┌────▼──────────┐
      │  工具三件套   │   │   工具说明书   │
      │ read_file    │   │ (System       │
      │ list_files   │   │  Prompt 拼装)  │
      │ edit_file    │   └───────────────┘
      └──────────────┘
```

- **工具三件套**：三个普通的 Python 函数，负责真正读文件、列目录、改文件。
- **工具说明书**：把每个工具的"名字 + 功能 + 参数格式"拼成一段文字，塞进 System Prompt 里告诉模型。
- **主循环**：负责"你 ↔ 模型 ↔ 工具"之间的传话，是全程序的大脑。

一句话概括原理：**模型本身不会读写文件，它只是"申请"调用工具；Python 代码替它执行，再把结果喂回去。**

---

## 三、准备工作（快速过一遍）

### 3.1 三个工具函数

```python
def read_file_tool(filename: str) -> Dict[str, Any]:
    """读取一个文件的完整内容"""

def list_files_tool(path: str) -> Dict[str, Any]:
    """列出一个目录下的所有文件"""

def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """把文件里的 old_str 替换成 new_str，old_str 为空则创建文件"""
```

注意一个小细节：`resolve_abs_path` 会把 `file.py`、`~/code/file.py` 这种写法统一转成绝对路径，免得模型给个相对路径就找不到北。

然后注册进一张"工具表"：

```python
TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool
}
```

以后模型只要报工具名，我们就能通过这张表找到对应的函数来执行。

### 3.2 给模型写"说明书"

模型怎么知道有哪些工具可用？答案很朴素：**直接在 Prompt 里告诉它。**

```python
def get_tool_str_representation(tool_name: str) -> str:
    tool = TOOL_REGISTRY[tool_name]
    return f"""
    Name: {tool_name}
    Description: {tool.__doc__}            # 函数文档字符串
    Signature: {inspect.signature(tool)}   # 参数和返回值
    """
```

这里用到了 `inspect` 模块——相当于 Python 自带的"读代码眼镜"，能自动把函数的参数表和 docstring 抠出来。所以**写好 docstring 不只是好习惯，在这里它直接决定了模型会不会用工具。**

拼出来的说明书长这样，会一起塞进 System Prompt：

```
TOOL
===
    Name: read_file
    Description:
    Gets the full content of a file provided by the user.
    ...
    Signature: (filename: str) -> Dict[str, Any]
===============
```

同时在 Prompt 里跟模型约定一个"暗号"：

```
想调用工具时，只回复一行：'tool: 工具名({"参数": "值"})'，别的什么都别说。
```

### 3.3 识别"暗号"：extract_tool_invocations

模型回复之后，我们要检查它是不是想调工具。这个函数做的事就是逐行扫描，找 `tool:` 开头的行：

```python
for raw_line in text.splitlines():
    line = raw_line.strip()
    if not line.startswith("tool:"):
        continue          # 不是暗号，跳过
    # 是暗号：拆出工具名和括号里的 JSON 参数
    name, rest = after.split("(", 1)
    args = json.loads(rest[:-1])
    invocations.append((name, args))
```

注意它返回的是**一个列表**——也就是说模型一次可以连发好几个工具调用，我们逐个执行。

---

## 四、主角登场：run_coding_agent_loop 深度拆解

前面的都是铺垫，真正让这一切转起来的是这个函数。**它的结构是"双层循环"，理解了这两层套娃，你就理解了所有 Agent 框架的核心。**

先上完整代码：

```python
def run_coding_agent_loop():
    conversation = [
        {"role": "system", "content": get_full_system_prompt()}
    ]
    while True:                                    # ← 外层循环
        try:
            user_input = input(f"{YOU_COLOR}You:{RESET_COLOR}:")
        except (keyboardInterrupt, EOFError):       
            break
        conversation.append({
            "role": "user",
            "content": user_input.strip(),
        })
        while True:                                # ← 内层循环
            assistant_response = execute_llm_call(conversation)
            tool_invocations = extract_tool_invocations(assistant_response)
            if not tool_invocations:
                print(f"{ASSISTANT_COLOR}Assistant:{RESET_COLOR}:{assistant_response}")
                conversation.append({
                    "role": "assistant",
                    "content": assistant_response,
                })
                break                              # 内层循环唯一的出口
            for name, args in tool_invocations:
                tool = TOOL_REGISTRY[name]
                if name == "read_file":
                    resp = tool(args.get("filename", "."))
                elif name == "list_files":
                    resp = tool(args.get("path", ""))
                elif name == "edit_file":
                    resp = tool(args.get("path", ""),
                                args.get("old_str", ""),
                                args.get("new_str", ""))
                conversation.append({
                    "role": "assistant",
                    "content": f"tool_result({json.dumps(resp)})",
                })
```

### 4.1 外层循环：一轮一轮的人机对话

外层 `while True` 很好理解，就是聊天软件的经典模式：

```python
while True:
    用户输入一句话
    塞进 conversation
    ...让模型处理...
```

`conversation` 这个列表非常关键，它就是**整个对话的"记忆"**。从第一条 system 消息开始，你说的话、模型说的话、工具的执行结果，全都按顺序堆在里面。每次调模型，都把这个完整列表发过去——模型之所以能"记得"上文，靠的就是它。

### 4.2 内层循环：本文最核心的设计

重点来了。为什么外层里面还要再套一个 `while True`？

因为**模型回答一个问题，往往不是一次回复能搞定的**。比如你说"帮我看看 main.py 有没有 bug"，模型的内心戏是这样的：

```
第 1 次回复：tool: list_files({"path": "."})        ← 先看看有啥文件
第 2 次回复：tool: read_file({"filename": "main.py"}) ← 再读文件
第 3 次回复：这个文件第 8 行有个 bug：xxx……        ← 最后才说人话
```

中间前两次回复都不是给你看的，而是"我要调用工具"的申请。所以内层循环的逻辑是：

```
┌──────────────────────────────────────────────┐
│              内层 while True                  │
│                                              │
│   1. 把完整 conversation 发给模型             │
│   2. 模型回复                                │
│   3. 检查回复里有没有 "tool:" 暗号            │
│      ├─ 没有 → 这是最终答案                   │
│      │        打印出来，存进 conversation     │
│      │        break ← 唯一出口               │
│      │                                       │
│      └─ 有   → 逐个执行工具                   │
│               把结果包装成 tool_result(...)   │
│               塞回 conversation               │
│               （不 break，回到第 1 步）        │
└──────────────────────────────────────────────┘
```

一句话总结：

> **模型只要还在"要工具"，内层循环就不停；直到模型给出一句不需要工具的普通回复，才把这句话打印给你，退出内层，等你下一轮输入。**

这就是 Agent 的所谓 "ReAct"（推理→行动→观察→再推理）模式的最简实现：模型每走一步都能"看到"上一步工具返回的结果，再决定下一步干什么。循环本身就是智能的载体。

### 4.3 一个容易看漏的细节：tool_result 的身份

注意这段：

```python
conversation.append({
    "role": "assistant",
    "content": f"tool_result({json.dumps(resp)})",
})
```

工具的执行结果，是以 `assistant` 的身份、`tool_result(...)` 的格式塞回对话历史的。这样做的好处是：**模型下一次被调用时，能天然地看懂"这是我上一步申请的工具返回给我的结果"**，对话链条不会断。

### 4.4 用一张图看完整流程

把两层循环合起来，一次完整交互长这样：

```
你说:"看看 main.py 有没有 bug"
        │
        ▼
┌─ 外层循环 ──────────────────────────────────┐
│  user 消息入队                              │
│      │                                      │
│      ▼                                      │
│  ┌─ 内层循环 ────────────────────────────┐  │
│  │ 轮次1: 模型说 → tool: list_files(...) │  │
│  │        执行 → tool_result([文件列表]) │  │
│  │ 轮次2: 模型说 → tool: read_file(...)  │  │
│  │        执行 → tool_result(文件内容)   │  │
│  │ 轮次3: 模型说 → "第8行有bug..."       │  │
│  │        无工具调用 → 打印 → break ✔    │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  回到外层，等你下一句话                      │
└─────────────────────────────────────────────┘
```

---

## 五、写在最后：Agent 没那么神秘

把这 100 行代码拆完，你会发现 Agent 的内核朴素得惊人：

| 听起来很高大上的概念 | 在这份代码里的样子 |
|---|---|
| 工具调用 / Function Calling | `tool: xxx({json})` 一行暗号 |
| 工具注册表 | 一个字典 `TOOL_REGISTRY` |
| 推理-行动循环（ReAct） | 内层 `while True` |
| 上下文记忆 | 一个不断变长的 `conversation` 列表 |

那些大型框架（LangChain、AutoGen 等）做的事情，本质上是把这套循环加上重试、并行、权限控制、记忆压缩等"精装修"。但地基，就是你今天看到的这个双层循环。

下次再看到"AI Agent"三个字，你可以很自信地说：**它的核心，我 100 行代码就能写出来。**

---

*如果这篇文章对你有帮助，欢迎点赞收藏，评论区聊聊你想给这个小 Agent 加什么工具？* 🚀
