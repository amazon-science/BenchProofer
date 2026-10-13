# Bring your own agent

Drafting the solution, the proof, the repair and each review auditor are agent sessions: a
model that reads and edits files and runs commands in a workspace of its own, then reports
a structured result. The `session` setting names the one a run uses. The one that ships,
`claude-code`, drives the Claude Code command-line tool through the Claude Agent SDK
(`benchproofer[agent]`). It is one plug-in, not a requirement: another coding agent's
command-line tool, such as Codex CLI or Kiro CLI, can take its place, and no stage, gate or
prompt changes.

A session decides how many bundles get built and how good they are. It cannot change what
"certified" means: the gates re-run every file a session hands back.

## What ships

```bash
benchproofer catalog sessions
```

| session | is |
| --- | --- |
| `claude-code` | the default: the Claude Code command-line tool, through the Claude Agent SDK |
| `scripted` | the smoke suite's session; reports from a packaged fixture and reaches no model |

## Writing a session

A session is an `AgentSession` with one method, `run`, which takes a `SessionSpec` and
returns a `StepOutcome`. A session for a command-line tool writes the request where the
tool can read it, runs the tool in the workspace, and reads its result back:

```python
import json
import shutil
import subprocess
import time
from typing import ClassVar

from benchproofer.core.plugin import Availability
from benchproofer.errors import ProviderError
from benchproofer.llm.agentic import AgentSession, SessionSpec, StepOutcome

COMMAND = "my-agent"  # the tool's command, run without a terminal


class MyAgentSession(AgentSession):
    """Run the stages' sessions with another coding agent's command-line tool."""

    name: ClassVar[str] = "my-agent"
    summary: ClassVar[str] = "my coding agent's command-line tool"

    def availability(self) -> Availability:
        if shutil.which(COMMAND) is None:
            return Availability.missing(f"{COMMAND} is not on PATH", hint="install it first")
        return Availability.ok()

    def run(self, spec: SessionSpec) -> StepOutcome:
        result = spec.cwd / "scratch" / "result.json"
        result.parent.mkdir(parents=True, exist_ok=True)
        prompt = (
            f"{spec.prompt}\n\nWhen you are done, write your result to {result} as one "
            f"JSON object with these fields: {json.dumps(spec.fields)}. "
            f"These are required: {', '.join(spec.required)}."
        )
        started = time.monotonic()
        try:
            done = subprocess.run(
                [COMMAND, ...],  # its non-interactive mode, model, system prompt and tools
                input=prompt, cwd=spec.cwd, capture_output=True, text=True,
                timeout=spec.timeout_s,
            )
        except FileNotFoundError as error:
            raise ProviderError(f"{COMMAND} could not be started: {error}") from error
        except subprocess.TimeoutExpired:
            done = None
        payload = json.loads(result.read_text()) if result.is_file() else None
        return StepOutcome(
            text=done.stdout if done else "",
            payload=payload,
            duration_s=time.monotonic() - started,
        )
```

What the pipeline expects of you:

* **Report the result as `payload`.** It is a dictionary with the fields `spec.fields`
  describes, `spec.required` among them, or None when the agent reported nothing. Raise
  `ProviderError` only when the tool could not be started: a session that ran and reported
  nothing is an outcome, which the stage records as such.
* **Pass the system prompt and the model.** `spec.system` is the stage's system prompt,
  and `self.model` is the model the run declares for this stage; give both to the tool
  through its own options, so the run uses the models it reports.
* **Give it the tools `spec.tools` names and no others, and no web tool.** A search of the
  web can find the golden patch, or another tool's formalization of the same task.
* **Keep what it reads and writes to its workspace.** It may read `spec.cwd`, the
  toolchains in `self.readable` and the system directories, and write what
  `spec.writable` names, its `scratch/` directory and its `tmp/` directory. `claude-code`
  checks each tool call before it runs (`confined` and `fenced` in `llm/claude_code.py`);
  for another tool, use its own permission settings or a sandbox. A session that strays
  cannot make a bundle pass, but it can read another run's work.
* **Keep to the budget.** Stop the session at `spec.timeout_s`, and a single shell command
  after `self.command_timeout_s`. Pass `spec.max_turns` if the tool has a turn limit.
* **Use the session's environment.** Its shell is `/bin/bash`, `TMPDIR` names `tmp/` in
  the workspace, and `PYTHONPATH` and every `BENCHPROOFER_*` variable are empty: the
  `tools` and `check` scripts in the workspace set them from a file the session may not
  read.
* **Ask once more for a missing report.** When the agent stopped without reporting and
  `spec.report` is not empty, send it `spec.report` in the same conversation, if the tool
  can continue one.
* **Record what it was asked.** When `self.record_dir` is set, write the system prompt,
  the prompt, the tools and the budget there.
* **Report what it did, if the tool says.** `turns`, `tool_uses` and `actions` (one short
  line per tool use) go into the run's records.
* **Leave `remote` true** for a tool that reaches a model, so an offline run refuses it.

## Register it

```toml
[project.entry-points."benchproofer.sessions"]
my-agent = "my_package.session:MyAgentSession"
```

```bash
pip install -e .
benchproofer doctor
BENCHPROOFER_SESSION=my-agent benchproofer run swebench-verified --backend nagini
```

`session_model` (`BENCHPROOFER_SESSION_MODEL`) sets the model the drafting, proof and
repair sessions run on; unset, they use the drafting model. The review sessions run on
`audit_model`.

## Checklist

* `availability()` names what is missing and how to install it.
* The result comes back as `payload`, with the fields `spec.fields` describes.
* The tool has the tools `spec.tools` names, and no web tool.
* Reads and writes are kept to the workspace, the toolchains and the system directories.
* The session stops at `spec.timeout_s`, and a shell command at `self.command_timeout_s`.
* A recorded run writes what each session was asked: `--record`, then look in
  `cassette_dir/sessions`.
