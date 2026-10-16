# swissknife

Select code in Zed, run a task, and get a one-sentence plain-English explanation
of it in the terminal panel. Uses Claude Code (`claude -p`, Sonnet) with
read-only access to your worktree so it can look up context when needed.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.com/claude-code), logged in (`claude` on your `PATH`)
- [Zed](https://zed.dev)

## Zed setup

1. Clone this repo somewhere, e.g. `~/git/swissknife`.
2. Add a task to `~/.config/zed/tasks.json` (adjust the `--project` path):

```json
[
  {
    "label": "Explain code",
    "command": "uv",
    "args": ["run", "--project", "/path/to/swissknife", "swissknife"],
    "env": {
      "FILE": "$ZED_FILE",
      "ROW": "$ZED_ROW",
      "COLUMN": "$ZED_COLUMN",
      "WORKTREE": "$ZED_WORKTREE_ROOT",
      "SELECTED": "$ZED_SELECTED_TEXT",
      "SYMBOL": "${ZED_SYMBOL:}"
    },
    "use_new_terminal": false,
    "allow_concurrent_runs": false,
    "reveal": "no_focus",
    "hide": "never"
  }
]
```

3. Optionally bind it to a key in `~/.config/zed/keymap.json`:

```json
[
  {
    "context": "Editor",
    "bindings": {
      "alt-e": ["task::Spawn", { "task_name": "Explain code" }]
    }
  }
]
```

Select some code and run the task (`task: spawn` → "Explain code", or your key).

## Options

Set these in the task's `env`:

| Variable                    | Default | Effect                                                         |
| --------------------------- | ------- | -------------------------------------------------------------- |
| `SWISSKNIFE_SYSTEM_PROMPT`  | `0`     | `1` replaces Claude Code's system prompt with `SYSTEM.md`      |
| `SWISSKNIFE_CONTEXT_LINES`  | `0`     | Lines of surrounding code sent up front (`0` = let Claude read) |
| `SWISSKNIFE_THINKING`       | `1`     | `0` turns extended thinking off                                |

The tone and format of the explanation live in `SYSTEM.md` and `TASK.md`.
