import fcntl
import json
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

SYSTEM = Path(__file__).parents[2] / "SYSTEM.md"
TASK = Path(__file__).parents[2] / "TASK.md"


def code_around(path: str, selected: str, row: int, col: int, n: int) -> str:
    """n lines around the selection, with the selection wrapped in <<< >>>.

    Zed's row/column are 1-based and point at the start of the selection (column in bytes)."""
    raw = Path(path).read_bytes()
    sel = selected.encode()
    start = sum(len(line) + 1 for line in raw.split(b"\n")[: row - 1]) + col - 1
    end = start + len(sel)
    raw = raw[:start] + b"<<<" + sel + b">>>" + raw[end:]
    lines = raw.decode(errors="replace").splitlines()
    return "\n".join(lines[max(row - 1 - n, 0): row + selected.count("\n") + n])


def main() -> None:
    lock = open(Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "nalm.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return  # already running, ignore this call

    env = os.environ
    use_system_prompt = env.get("NALM_SYSTEM_PROMPT", "0") == "1"  # replace Claude Code's own prompt
    context_lines = int(env.get("NALM_CONTEXT_LINES", "0"))  # code sent up front, 0 = let Claude read
    thinking = env.get("NALM_THINKING", "1") == "1"  # 0 turns extended thinking off

    context = f"line {env['ROW']}, inside {env.get('SYMBOL') or 'no symbol'}"
    if context_lines:
        context += "\n" + code_around(env["FILE"], env["SELECTED"], int(env["ROW"]), int(env["COLUMN"]), context_lines)

    instructions = SYSTEM.read_text()
    task = (
        TASK.read_text()
        .replace("{{file_path}}", env["FILE"])
        .replace("{{context}}", context)
        .replace("{{selection}}", env["SELECTED"])
    )

    cmd = [
        "claude", "-p", task if use_system_prompt else f"{instructions}\n{task}",
        "--model", "sonnet", "--no-session-persistence",
        "--tools", "Read,Grep,Glob", "--allowedTools", "Read,Grep,Glob",
        "--add-dir", env.get("WORKTREE") or str(Path(env["FILE"]).parent),
        "--max-turns", "4",
        "--output-format", "json",
    ]
    if use_system_prompt:
        cmd += ["--system-prompt", instructions]

    if not thinking:
        env = {**env, "MAX_THINKING_TOKENS": "0"}

    result = json.loads(
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd="/tmp",
            env=env,
        ).stdout
    )

    tooltip = result["result"].strip()
    u = result["usage"]
    stats = (
        f"in {u['input_tokens'] + u['cache_creation_input_tokens'] + u['cache_read_input_tokens']}"
        f" (cached {u['cache_read_input_tokens']}) · out {u['output_tokens']}"
        f" · {result['num_turns']} turns · ${result['total_cost_usd']:.3f}"
    )

    width = min(shutil.get_terminal_size().columns, 80) - 4
    text = textwrap.fill(tooltip, width, initial_indent="  ", subsequent_indent="  ")
    print(f"\033[2J\033[H\n{text}\n\n  \033[2m{stats}\033[0m\n")  # clear panel, then show the latest tooltip
