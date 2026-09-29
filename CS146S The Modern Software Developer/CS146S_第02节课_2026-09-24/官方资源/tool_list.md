# Built-in tools

## Files

- **Read** — Read a local file, image, or PDF.
- **Edit** — Replace an exact string in a file.
- **Write** — Create a file or fully overwrite an existing one.
- **NotebookEdit** — Replace, insert, or delete a cell in a Jupyter notebook.

## Shell

- **Bash** — Run a shell command and return its output.
- **Monitor** — Stream events from a long-running background script.

## Search and code intelligence

- **WebSearch** — Search the web and return result titles and URLs.
- **WebFetch** — Fetch a URL and answer a prompt against the page.
- **LSP** — Query a language server for definitions, references, hover info, and symbols.

## Agents

- **Agent** — Spawn a subagent for complex, parallel, or delegated work.
- **ListAgents** — List agents this session can message.
- **SendMessage** — Send a message to another agent.
- **TaskStop** — Stop a running background task or agent.
- **Workflow** — Run a multi-agent workflow script in the background.

## Planning and isolation

- **EnterPlanMode** — Switch into plan mode before a non-trivial implementation.
- **ExitPlanMode** — Submit the written plan for user approval.
- **EnterWorktree** — Create an isolated git worktree and switch the session into it.
- **ExitWorktree** — Leave the session worktree and return to the original directory.

## Scheduling

- **CronCreate** — Schedule a one-shot or recurring prompt.
- **CronDelete** — Cancel a cron job scheduled in this session.
- **CronList** — List cron jobs scheduled in this session.
- **ScheduleWakeup** — Schedule the next self-paced wakeup in `/loop` dynamic mode.
- **RemoteTrigger** — Create, update, run, and inspect claude.ai remote triggers.

## Artifacts

- **Artifact** — Publish an HTML page as a private claude.ai artifact.
- **ArtifactComments** — Read and reply to comment threads on a published artifact.
- **ArtifactData** — Read and write a published artifact’s shared database.

## MCP resources

- **ListMcpResourcesTool** — List resources exposed by configured MCP servers.
- **ReadMcpResourceTool** — Read one MCP resource by server name and URI.
- **ReadMcpResourceDirTool** — List the direct children of an MCP directory resource.

## Interaction

- **AskUserQuestion** — Ask the user a blocking decision with selectable options.
- **Skill** — Load a packaged skill’s instructions for the current task.
- **PushNotification** — Send a desktop notification, and a phone push if Remote Control is connected.
- **SendFeedback** — Draft feedback about a Claude Code product or model issue.
- **EndConversation** — Close the conversation after sustained abuse or an explicit demo request.

## Design and review

- **DesignSync** — Sync a local component library with a claude.ai design-system project.
- **ReportFindings** — Submit typed code-review findings for the host UI.
