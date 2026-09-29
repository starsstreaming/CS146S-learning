
Codebase and user instructions are shown below. Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written.

Contents of /Users/mihaileric/Documents/miscellaneous/claude-code-demystified/CLAUDE.md (project instructions, checked into the codebase):

# CLAUDE.md

## Project Overview

This is a simple todo/task tracker. The core is a Python CLI that lets users add, list, complete, and delete tasks (with priorities, due dates, and subtasks), with data persisted to a local JSON file. There are also web frontends: a FastAPI app (`api/`) and a TypeScript/Express app (`web/`).

## Project Structure

```
todo/
  cli.py      - Command-line interface and argument parsing
  models.py   - Task dataclass and Priority enum
  storage.py  - JSON file persistence layer
api/
  main.py     - FastAPI web app (Jinja2 templates) using the todo package
web/
  src/        - TypeScript Express app (EJS views in web/views)
```

## Running the Application

```bash
python -m todo add "Task title" [--due 2024-12-31] [--priority low|medium|high]
python -m todo list [--status all|pending|completed] [--priority ...] [--sort priority|created]
python -m todo done <task_id>
python -m todo delete <task_id> [--force]
python -m todo add-subtask <parent_id> "Subtask title"
python -m todo done-subtask <subtask_id>
python -m todo delete-subtask <subtask_id> [--force]
```

## Code Style

- Use type hints for function parameters and return values
- Use dataclasses for data models
- Keep functions focused and single-purpose
