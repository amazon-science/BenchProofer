# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Agent sessions: what a request grants, which session a run gets, and what is recorded.

The Claude Code command-line tool is never started here: it is a subprocess that reaches a
model, so a case about it would be a case about this machine, and `benchproofer catalog
sessions` is what reports whether it can run. Its helpers are tested directly, and what
this module does with the tool's stream -- how many turns one request becomes, and under
what budget -- is tested against the SDK's own types with the stream scripted (`driven`).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from benchproofer.config import Settings
from benchproofer.errors import ProviderError
from benchproofer.llm.agentic import (
    EDIT,
    READ_ONLY,
    AgentSession,
    SessionSpec,
    StepOutcome,
)
from benchproofer.llm.resolve import require_session, session_for
from benchproofer.registries import SESSIONS

FIELDS = {
    "callee": {"type": "string", "description": "the callee to assume"},
    "property": {"type": "string", "description": "what to assume of it"},
}


def spec(**overrides: object) -> SessionSpec:
    """One request for a session, with the defaults a stage would use."""
    fields: dict[str, object] = {
        "system": "you read a repository",
        "prompt": "find the callee nothing can model",
        "cwd": ".",
        "submit": "axiom",
        "fields": FIELDS,
        "required": ("callee", "property"),
    }
    fields.update(overrides)
    return SessionSpec(**fields)  # type: ignore[arg-type]


class Reporting(AgentSession):
    """A session that runs nowhere, for the cases about which session a run is given."""

    name = "reporting"

    def run(self, request: SessionSpec) -> StepOutcome:
        return StepOutcome(text="")


class Local(Reporting):
    """A session that reaches no model, as the scripted one does."""

    name = "local"
    remote = False


def test_a_session_has_submitted_only_when_it_reported_a_payload() -> None:
    """No payload is an answer -- a session may conclude no assumption is needed."""
    assert not StepOutcome(text="nothing here needs assuming").submitted
    assert StepOutcome(text="found it", payload={"callee": "os.path.getmtime"}).submitted


def test_the_tool_sets_nest_and_none_reaches_the_web() -> None:
    """Reading is the default, and a shell and editing are opted into.

    No set holds a web tool, since a search can find the benchmark's own fix, nor a way of
    waiting to be woken, since one prompt drives a whole session and nothing re-invokes it
    to deliver what it is waiting for.
    """
    assert spec().tools == READ_ONLY
    assert set(READ_ONLY) == {"Read", "Grep", "Glob"}
    assert EDIT[: len(READ_ONLY)] == READ_ONLY
    assert {"Read", "Grep", "Glob", "Bash", "Write", "Edit"} <= set(EDIT)
    waiting = {"WebSearch", "WebFetch", "ScheduleWakeup", "BashOutput", "KillShell", "Agent"}
    assert not waiting & {*READ_ONLY, *EDIT}


def test_a_session_has_the_built_in_tools_its_request_names_and_no_others(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Under `bypassPermissions` the allowed list grants what it names and restricts nothing.

    So the tool is told which built-in tools exist for the session at all: an auditor given
    read-only tools has no shell and no file tool to write with.
    """
    _, asked = driven(monkeypatch, spec(cwd=tmp_path), submits_on=1)

    options = asked[0][1]
    assert options.tools == list(READ_ONLY)
    assert "Bash" not in options.tools and "Write" not in options.tools
    assert options.allowed_tools == [*READ_ONLY, "mcp__benchproofer__axiom"]


def test_the_claude_code_session_is_registered() -> None:
    assert "claude-code" in SESSIONS.names()


# ---- when a session is used, and when it is not --------------------------


def test_an_offline_run_has_no_session_whatever_it_is_configured_with() -> None:
    """Offline means refuse the network, and a session reaches a model over it."""
    configured = Settings(session="claude-code", offline=True)

    assert session_for(configured) is None
    assert session_for(configured.model_copy(update={"session": ""})) is None


def test_a_session_that_reaches_no_model_runs_offline_too(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """What offline refuses is the network, and a session that reaches no model uses none."""
    session = Local()
    monkeypatch.setattr(SESSIONS, "build", lambda name: session)

    assert session_for(Settings(session="local", offline=True)) is session


def test_a_stage_that_needs_a_session_says_what_to_install_when_there_is_none() -> None:
    """Drafting, review and repair cannot run on requests alone, so the run stops on it."""
    with pytest.raises(ProviderError, match=r"^reviewing a bundle needs an agent session"):
        require_session(Settings(session=""), "reviewing a bundle")
    with pytest.raises(ProviderError, match=r"install `benchproofer\[agent\]`"):
        require_session(Settings(session="claude-code", offline=True), "drafting the solution")


def test_a_session_runs_on_the_run_s_drafting_model_unless_told_otherwise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The models a run declares are the models it uses, sessions included.

    Leaving the choice to the machine's own Claude Code configuration would run a
    session on whatever model and account that configuration names, which no record of
    the run shows.
    """
    session = Reporting()
    monkeypatch.setattr(SESSIONS, "build", lambda name: session)

    assert session_for(Settings(session="reporting", model="drafter")) is session
    assert session.model == "drafter"
    session_for(Settings(session="reporting", model="drafter", session_model="other"))
    assert session.model == "other"


def test_the_review_runs_its_sessions_on_the_reviewing_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A review by the model that drafted the bundle is the same judgment twice."""
    monkeypatch.setattr(SESSIONS, "build", lambda name: Reporting())
    configured = Settings(session="reporting", model="drafter", audit_model="reviewer")

    found = require_session(configured, "reviewing a bundle", configured.audit_model)

    assert found.model == "reviewer"
    assert session_for(configured) is not None
    assert session_for(configured).model == "drafter"  # type: ignore[union-attr]


def test_each_stage_gets_a_session_of_its_own(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tasks run side by side, and one instance re-aimed at a model would move another's."""
    configured = Settings(session="reporting", model="drafter", audit_model="reviewer")
    monkeypatch.setattr(SESSIONS, "build", lambda name: Reporting())

    assert session_for(configured, "reviewer") is not session_for(configured)


def test_a_session_nobody_registered_is_absent_rather_than_an_error() -> None:
    """A stage that needs one reports it did not happen; the run carries on."""
    assert session_for(Settings(session="no-such-session")) is None


def test_the_submit_tool_is_declared_with_its_types_and_what_is_optional() -> None:
    """The SDK reads a dict as a schema only when it has `type` and `properties`.

    Anything else it reads as a map from name to Python type, which a JSON-schema property
    is not, so each field would become a required untyped string, and an assumption
    session's `"false"` would read as asking for an assumption it had just said was not
    needed.
    """
    sdk = pytest.importorskip("claude_agent_sdk")
    from benchproofer.llm.claude_code import input_schema

    fields = {
        **FIELDS,
        "needed": {"type": "boolean", "description": "whether an assumption is needed"},
    }
    request = spec(fields=fields, required=("needed",))

    @sdk.tool(request.submit, "report", input_schema(request))
    async def submit(args: dict[str, object]) -> dict[str, object]:
        return {}

    wire = sdk._build_input_schema(submit)

    assert wire == input_schema(request)
    assert wire["properties"]["needed"] == fields["needed"]
    assert wire["required"] == ["needed"]


# ---- one prompt drives the whole session ---------------------------------


def test_a_session_s_environment_stops_a_long_command_and_hides_the_run_s(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One shell command runs at most as long as a program `./tools run` runs, or the session.

    With background tasks off the tool stops a command at its timeout instead of moving it
    to the background with a notification nothing delivers. The shell is bash, whatever the
    user's is. The run's module path and Benchproofer settings are emptied, since they say
    where Benchproofer's source is and what the run is set to.
    """
    from benchproofer.llm.claude_code import environment

    monkeypatch.setenv("PYTHONPATH", "/frozen/src")
    monkeypatch.setenv("BENCHPROOFER_CACHE_DIR", "/run/cache")
    request = spec(cwd=tmp_path, timeout_s=9000.0)

    capped = environment(request, 1800.0)

    assert capped["BASH_DEFAULT_TIMEOUT_MS"] == capped["BASH_MAX_TIMEOUT_MS"] == "1800000"
    assert environment(spec(timeout_s=600.0), 1800.0)["BASH_MAX_TIMEOUT_MS"] == "600000"
    assert environment(request)["BASH_MAX_TIMEOUT_MS"] == "9000000"
    assert capped["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"
    assert capped["SHELL"] == "/bin/bash"
    assert capped["TMPDIR"] == (tmp_path / "tmp").as_posix()
    assert capped["PYTHONPATH"] == capped["BENCHPROOFER_CACHE_DIR"] == ""


def driven(
    monkeypatch: pytest.MonkeyPatch,
    request: SessionSpec,
    *,
    submits_on: int = 0,
    ends_on: tuple[int, str] = (0, ""),
    record_dir: Path | None = None,
    readable: tuple[Path, ...] = (),
    command_timeout_s: float | None = None,
) -> tuple[StepOutcome, list[tuple[str, Any]]]:
    """Run a Claude Code session against the SDK's own types and a scripted stream.

    The command-line tool is never started: `query` is replaced by a generator that
    records what it was asked and yields one turn and one result. ``submits_on`` is the
    turn on which the model calls the submit tool, zero for a session that never does.
    ``ends_on`` is a turn on which the tool ends the session with an error result instead,
    and that result's subtype.

    Returns:
        What the session produced, and one entry per turn it was driven with.
    """
    sdk = pytest.importorskip("claude_agent_sdk")
    from benchproofer.llm.claude_code import ClaudeCodeSession

    declared: list[Any] = []
    building = sdk.create_sdk_mcp_server
    asked: list[tuple[str, Any]] = []

    def built(*, name: str, tools: list[Any]) -> Any:
        declared.extend(tools)
        return building(name=name, tools=tools)

    async def query(*, prompt: str, options: Any) -> Any:
        asked.append((prompt, options))
        if len(asked) == submits_on:
            await declared[0].handler({"callee": "os.getcwd", "property": "it is pure"})
        yield sdk.AssistantMessage(content=[sdk.TextBlock(text="done")], model="a-model")
        if len(asked) == ends_on[0]:
            raise sdk.ResultError("an error result", data={"subtype": ends_on[1]}, exit_code=1)
        yield sdk.ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id=options.session_id or "a-session",
        )

    monkeypatch.setattr(sdk, "create_sdk_mcp_server", built)
    monkeypatch.setattr(sdk, "query", query)
    session = ClaudeCodeSession()
    session.record_dir = record_dir
    session.readable = readable
    session.command_timeout_s = command_timeout_s
    return session.run(request), asked


def test_a_recording_run_keeps_each_session_s_whole_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Claude Code keeps the conversation but not the system prompt, which holds the rules.

    The file is named by the conversation's id, so it finds the tool's own transcript, and
    it says what the session could write and what it could read besides its workspace.
    """
    request = spec(
        system="the lane's rules",
        prompt="the bundle to judge",
        writable=(tmp_path / "scratch",),
    )

    _, asked = driven(
        monkeypatch,
        request,
        submits_on=1,
        record_dir=tmp_path,
        readable=(tmp_path / "toolchain",),
    )

    (kept,) = tmp_path.glob("axiom-*.json")
    written = json.loads(kept.read_text())
    assert (written["system"], written["prompt"]) == ("the lane's rules", "the bundle to judge")
    assert written["session"] == asked[0][1].session_id
    assert kept.name == f"axiom-{written['session']}.json"
    assert written["writable"][0] == (tmp_path / "scratch").as_posix()
    assert written["env"]["TMPDIR"] == "tmp"
    assert written["readable"] == [(tmp_path / "toolchain").as_posix()]


def test_a_session_is_given_somewhere_to_keep_its_requests_only_when_the_run_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(SESSIONS, "build", lambda name: Reporting())
    configured = Settings(session="reporting", cassette_dir=Path("tapes"))

    assert session_for(configured).record_dir is None  # type: ignore[union-attr]
    recording = session_for(configured.model_copy(update={"record": True}))
    assert recording is not None and recording.record_dir == Path("tapes") / "sessions"


def test_a_session_s_commands_are_capped_at_the_run_s_program_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The run sets the cap once, for every session (`session_for`).

    A session given none runs its commands as long as itself.
    """
    outcome, asked = driven(monkeypatch, spec(timeout_s=9000.0), submits_on=1)
    _, capped = driven(
        monkeypatch, spec(timeout_s=9000.0), submits_on=1, command_timeout_s=3600
    )

    assert outcome.submitted and len(asked) == 1
    assert asked[0][1].env["BASH_MAX_TIMEOUT_MS"] == "9000000"
    assert capped[0][1].env["BASH_MAX_TIMEOUT_MS"] == "3600000"
    monkeypatch.setattr(SESSIONS, "build", lambda name: Reporting())
    found = session_for(Settings(session="reporting", oracle_timeout_s=1234))
    assert found is not None and found.command_timeout_s == 1234


def guarded(hook: Any, tool: str, cwd: Path | None = None, **arguments: object) -> str:
    """What a hook decides about one call of ``tool``: `deny`, or empty to let it run."""
    import asyncio

    called: dict[str, object] = {"tool_name": tool, "tool_input": arguments}
    if cwd is not None:
        called["cwd"] = str(cwd)
    answer = asyncio.run(hook(called, "a-use", {"signal": None}))
    return str(answer.get("hookSpecificOutput", {}).get("permissionDecision", ""))


def said(hook: Any, tool: str, **arguments: object) -> str:
    """What a hook tells the session of one call of ``tool``: why it refused, or empty."""
    import asyncio

    answer = asyncio.run(hook({"tool_name": tool, "tool_input": arguments}, "a-use", {}))
    return str(answer.get("hookSpecificOutput", {}).get("permissionDecisionReason", ""))


def test_a_session_s_file_tools_write_only_inside_its_workspace(tmp_path: Path) -> None:
    """What its request names, its scratch directory and its temporary directory, no more.

    Every session has the limit, one that names nothing too: the shared Lake workspace,
    the toolchains and other sessions' files are no session's to write. The target is
    resolved first, so neither a relative path nor a symlink out of the scratch directory
    reaches past the limit.
    """
    from benchproofer.llm.claude_code import confined

    workspace = tmp_path / "workspace"
    (workspace / "scratch").mkdir(parents=True)
    (workspace / "scratch" / "out").symlink_to(tmp_path)
    solution = workspace / "bundles" / "solution.py"
    hook = confined(spec(cwd=workspace, writable=(solution,)))
    bare = confined(spec(cwd=workspace))

    assert guarded(hook, "Write", file_path=str(solution), content="") == ""
    assert guarded(hook, "Edit", file_path=str(workspace / "scratch" / "probe.py")) == ""
    assert guarded(hook, "MultiEdit", file_path="scratch/probe.py") == ""
    assert guarded(bare, "Write", file_path="tmp/notes.txt") == ""
    assert guarded(bare, "Write", file_path=str(solution)) == "deny"
    assert guarded(hook, "Write", file_path=str(workspace / "bundles" / "notes.md")) == "deny"
    assert guarded(hook, "Edit", file_path="scratch/../bundles/notes.md") == "deny"
    assert guarded(hook, "Write", file_path="scratch/out/elsewhere.py") == "deny"
    assert guarded(hook, "NotebookEdit", notebook_path=str(tmp_path / "a.ipynb")) == "deny"
    lake = tmp_path / "lake" / "Velvet" / "velvet_documentation.md"
    assert guarded(bare, "Edit", file_path=str(lake)) == "deny"


def test_no_command_of_a_session_runs_in_the_background(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing re-invokes the session to report it finished, and the report waits on it.

    The tool's background tasks are off in every conversation of the session, the one
    asking for its report too, which takes the shell's `run_in_background` away.
    """
    _, asked = driven(monkeypatch, spec(report="Call the submit tool now."))

    assert len(asked) == 2
    for _, options in asked:
        assert options.env["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"


@pytest.fixture
def walled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Any]:
    """A session's workspace, a toolchain it may read, and its read guard.

    Beside them, the kind of directory no session may read: another session's workspace
    under the same cache, holding a bundle.
    """
    from benchproofer.llm.claude_code import fenced

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    workspace = tmp_path / "cache" / "scratch" / "task-a" / "agent-repair"
    (workspace / "repository").mkdir(parents=True)
    (workspace / "scratch").mkdir()
    other = tmp_path / "cache" / "scratch" / "task-b" / "agent-repair" / "bundles"
    other.mkdir(parents=True)
    toolchain = tmp_path / "home" / ".elan"
    toolchain.mkdir(parents=True)
    hook = fenced(workspace, (toolchain,), {**os.environ, "TMPDIR": str(workspace / "tmp")})
    return workspace, toolchain, hook


def test_a_session_reads_its_workspace_its_toolchains_and_the_system_directories(
    walled: tuple[Path, Path, Any],
) -> None:
    """And a path under a top-level directory this machine lacks, a container's `/app`."""
    workspace, toolchain, hook = walled

    assert guarded(hook, "Read", file_path=str(workspace / "repository" / "setup.py")) == ""
    assert guarded(hook, "Grep", pattern="def reduce", path="repository") == ""
    assert guarded(hook, "Glob", pattern="**/*.py", path=str(workspace)) == ""
    assert guarded(hook, "Read", file_path=str(toolchain / "toolchains" / "Init.lean")) == ""
    assert guarded(hook, "Bash", command="grep -rn spec repository scratch | head") == ""
    assert (
        guarded(hook, "Bash", command="ls /usr/lib/python3* 2>/dev/null; cat /etc/os-release")
        == ""
    )
    assert guarded(hook, "Bash", command="./tools run scratch/probe.py > $TMPDIR/out.txt") == ""
    assert guarded(hook, "Bash", command="ls ~/.elan/toolchains") == ""
    assert guarded(hook, "Bash", command="docker run img python /app/x.py -C /testbed") == ""


def test_a_path_outside_what_a_session_reads_is_refused_however_it_is_spelled(
    walled: tuple[Path, Path, Any], tmp_path: Path
) -> None:
    """An absolute path, `~`, a variable, a `..` escape and a symlink out alike."""
    workspace, _, hook = walled
    other = tmp_path / "cache" / "scratch" / "task-b" / "agent-repair" / "bundles"
    (workspace / "scratch" / "out").symlink_to(other)

    assert guarded(hook, "Read", file_path=str(other / "solution.py")) == "deny"
    assert guarded(hook, "Read", file_path="/tmp/a5wc/test_selinux.py") == "deny"  # noqa: S108
    assert guarded(hook, "Grep", pattern="spec", path=str(tmp_path / "cache")) == "deny"
    assert guarded(hook, "Glob", pattern=f"{tmp_path}/cache/**/solution.py") == "deny"
    assert guarded(hook, "Glob", pattern="*.py", path="scratch/out") == "deny"
    assert guarded(hook, "Bash", command="cat ~/notes.md") == "deny"
    assert guarded(hook, "Bash", command="ls $HOME") == "deny"
    assert guarded(hook, "Bash", command="ls ${HOME}/.cache") == "deny"
    assert guarded(hook, "Bash", command="ls .. && cat ../../task-b/agent-repair/x") == "deny"
    assert guarded(hook, "Bash", command="cat scratch/out/solution.py") == "deny"
    assert guarded(hook, "Bash", command="cp scratch/a.diff /tmp/x.diff") == "deny"
    named = said(hook, "Read", file_path=str(other / "solution.py"))
    assert str(other / "solution.py") in named and str(workspace) in named
    assert "$TMPDIR" in named


def test_a_search_from_outside_what_a_session_reads_is_refused(
    walled: tuple[Path, Path, Any], tmp_path: Path
) -> None:
    """Its root is a path the command names, whichever command walks it.

    A pattern is judged by the directory it matches names in, so `/l*` is the root. A
    listing of every path on the machine is refused whatever it is given, and so is a
    change of directory that names none, which goes home.
    """
    _, _, hook = walled
    cache = tmp_path / "cache"

    for command in (
        'find / -name "*.lean" -path "*Velvet*" 2>/dev/null | head -50',
        f'grep -rl "webengine" {cache} 2>/dev/null | grep -i conform | head',
        f"rg -l conformance {cache}/scratch",
        "ls -R ..",
        "du -sh ~",
        "tree /",
        "ls /l*",
        f"cat {cache}/scratch/*/agent-repair/bundles/task.json",
        "locate Solution.lean",
        "cd && find . -name Solution.lean",
    ):
        assert guarded(hook, "Bash", command=command) == "deny", command
    assert "every path" in said(hook, "Bash", command="locate Solution.lean")
    assert guarded(hook, "Bash", command="find . -name '*.py' | xargs grep -l reduce") == ""


def test_a_relative_path_is_read_from_where_the_command_runs(
    walled: tuple[Path, Path, Any],
) -> None:
    """The shell keeps its directory between calls, and a command may change it first."""
    workspace, _, hook = walled
    deep = workspace / "repository" / "pkg"
    deep.mkdir()

    assert guarded(hook, "Bash", deep, command="sed -n 1,9p ../../scratch/a.py") == ""
    assert guarded(hook, "Bash", command="cd repository/pkg && cat ../../scratch/a.py") == ""
    assert guarded(hook, "Bash", command="cd repository && cat ../../x") == "deny"
    assert guarded(hook, "Bash", deep, command="ls ../../..") == "deny"


def test_what_a_command_hands_a_program_is_not_read_as_paths(
    walled: tuple[Path, Path, Any],
) -> None:
    """A here-document is the program's text, as a written file's content is.

    A bare `/` in quotes is text rather than the root, and a quoted pattern is a name as
    written, since the shell expands neither; Lean's `~` is not the home directory there.
    """
    _, _, hook = walled

    program = (
        "cat > scratch/probe.lean <<'EOF'\ntheorem t (l : List Nat) : l ~ l := by rfl\nEOF"
    )
    assert guarded(hook, "Bash", command=program) == ""
    python = "python3 - <<'PY'\nprint('/'.join(['', 'tmp']))\nPY\necho done"
    assert guarded(hook, "Bash", command=python) == ""
    assert guarded(hook, "Bash", command="python3 -c \"print(p + '/' + k)\"") == ""
    assert guarded(hook, "Bash", command="echo \"=== A / B ===\" && sed 's/^/   /' x") == ""
    assert guarded(hook, "Bash", command="sed -n '/^\\[\\[judgments\\]\\]/,$p' x.toml") == ""
    assert guarded(hook, "Bash", command="cat <<EOF > /tmp/x\nhello\nEOF") == "deny"


def test_what_reveals_the_run_is_refused_inside_what_a_session_reads(
    walled: tuple[Path, Path, Any],
) -> None:
    """Benchproofer's own package wherever it is, and a process's directory under `/proc`.

    The second shows that process's environment, the run's own among them; a device that
    resolves into the guard's own process, such as `/dev/stdin`, is not one.
    """
    import benchproofer

    _, _, hook = walled
    package = Path(benchproofer.__file__).resolve().parent

    assert guarded(hook, "Read", file_path=str(package / "gates" / "audit.py")) == "deny"
    assert guarded(hook, "Bash", command="cat /proc/self/environ") == "deny"
    assert guarded(hook, "Bash", command=f"cat /proc/{os.getpid()}/environ") == "deny"
    assert guarded(hook, "Bash", command="cat /proc/cpuinfo | head") == ""
    assert guarded(hook, "Bash", command="grep -n verify /dev/stdin < tools") == ""


def test_the_read_guard_reads_only_the_tools_that_name_a_path(
    walled: tuple[Path, Path, Any],
) -> None:
    """A note, a to-do list or the report itself reads nothing, whatever it says."""
    _, _, hook = walled

    assert guarded(hook, "TodoWrite", todos=[{"content": "read /tmp/x"}]) == ""
    assert guarded(hook, "mcp__benchproofer__repair", summary="ran find / for nothing") == ""
    assert guarded(hook, "Bash", description="look in /tmp", command="ls scratch") == ""


def test_a_session_s_own_project_directory_is_named_as_claude_code_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every character of the resolved directory but a letter or a digit becomes `-`.

    A name longer than 200 characters is cut there and given a hash of the whole path, and
    the directory is under the tool's configuration directory, which `CLAUDE_CONFIG_DIR`
    moves.
    """
    from benchproofer.llm.claude_code import project_directory

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    workspace = tmp_path / "cache" / "scratch" / "demo-coin_change.v2" / "agent-draft"
    workspace.mkdir(parents=True)
    (tmp_path / "link").symlink_to(workspace)
    spelled = re.sub(r"[^a-zA-Z0-9]", "-", str(workspace.resolve()))

    assert project_directory(workspace) == tmp_path / "config" / "projects" / spelled
    assert project_directory(tmp_path / "link") == project_directory(workspace)
    assert project_directory(Path("/" + "a" * 250)).name == "-" + "a" * 199 + "-feo44x"
    monkeypatch.delenv("CLAUDE_CONFIG_DIR")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert project_directory(workspace).parent == tmp_path / "home" / ".claude" / "projects"


def test_a_session_reads_back_its_own_saved_output_and_no_other_session_s(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Claude Code saves a tool's output too long to show there, and reads it back.

    Under the directory every session started in the workspace shares, the session reads
    its own conversation's and no other's. Both guards go on every session whatever its
    request asks: the write guard on the file tools and the read guard on the tools that
    name a path.
    """
    from benchproofer.llm.claude_code import project_directory

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "config"))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    projects = tmp_path / "config" / "projects"

    _, asked = driven(monkeypatch, spec(cwd=workspace), submits_on=1)

    matchers = asked[0][1].hooks["PreToolUse"]
    assert [matcher.matcher for matcher in matchers] == [
        "Write|Edit|MultiEdit|NotebookEdit",
        "Read|Grep|Glob|Bash",
    ]
    (hook,) = matchers[-1].hooks
    kept = project_directory(workspace)
    saved = kept / str(asked[0][1].session_id) / "tool-results" / "1.txt"
    assert guarded(hook, "Read", file_path=str(saved)) == ""
    assert guarded(hook, "Bash", command=f"sed -n 1,40p {saved}") == ""
    # An earlier session started in the same workspace keeps its transcript beside it.
    earlier = kept / "an-earlier-session" / "tool-results" / "1.txt"
    assert guarded(hook, "Read", file_path=str(earlier)) == "deny"
    assert guarded(hook, "Read", file_path=str(kept / "an-earlier-session.jsonl")) == "deny"
    assert guarded(hook, "Grep", pattern="verdict", path=str(kept)) == "deny"
    assert guarded(hook, "Read", file_path=str(projects / "-elsewhere" / "a.jsonl")) == "deny"
    assert guarded(hook, "Glob", pattern="*", path=str(projects)) == "deny"


def test_a_session_s_temporary_directory_is_inside_its_workspace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`/tmp` is shared by every run on the machine; this one is the session's own."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    _, asked = driven(monkeypatch, spec(cwd=workspace), submits_on=1)

    assert asked[0][1].env["TMPDIR"] == (workspace / "tmp").as_posix()
    assert (workspace / "tmp").is_dir()


def test_every_session_reads_the_toolchains_the_run_s_checkers_use(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The Python environment, the toolchain directory, the Lean toolchains, a Lake workspace.

    Each the machine has, resolved; set once for the run, for every stage's session.
    """
    import sys

    from benchproofer.llm.resolve import toolchains

    monkeypatch.setattr(SESSIONS, "build", lambda name: Reporting())
    lake = tmp_path / "lake"
    lake.mkdir()
    (tmp_path / "elan").mkdir()
    monkeypatch.setenv("BENCHPROOFER_LEAN_WORKSPACE", str(lake))
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "elan"))
    configured = Settings(session="reporting", toolchain_dir=tmp_path / "missing")

    found = toolchains(configured)

    assert Path(sys.prefix).resolve() in found and Path(sys.base_prefix).resolve() in found
    assert lake.resolve() in found and (tmp_path / "elan").resolve() in found
    assert tmp_path / "missing" not in found
    for session in (session_for(configured), session_for(configured, "reviewer")):
        assert session is not None and session.readable == found


def test_a_session_that_stopped_without_submitting_is_asked_for_its_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Its work is on disk and only its report says what may be kept of it.

    The conversation is taken up again, so what it already found is still in front of it.
    """
    request = spec(report="Your time is up. Call the submit tool now.", max_turns=200)

    outcome, asked = driven(monkeypatch, request, submits_on=2)

    assert outcome.submitted
    prompts = [prompt for prompt, _ in asked]
    assert prompts == [request.prompt, request.report]
    assert asked[1][1].resume == asked[0][1].session_id
    assert asked[1][1].session_id is None
    assert asked[1][1].max_turns < request.max_turns
    assert "asked to report" in outcome.detail


def test_a_session_that_used_all_its_turns_is_asked_for_its_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Running out of turns is the budget running out, as running out of time is."""
    request = spec(report="Your turns are up. Call the submit tool now.", max_turns=200)

    outcome, asked = driven(monkeypatch, request, submits_on=2, ends_on=(1, "error_max_turns"))

    assert outcome.submitted
    assert [prompt for prompt, _ in asked] == [request.prompt, request.report]
    assert "200 turn(s)" in outcome.detail


def test_any_other_error_result_is_the_tool_s_own(monkeypatch: pytest.MonkeyPatch) -> None:
    request = spec(report="Call the submit tool now.")

    with pytest.raises(ProviderError, match="an error result"):
        driven(monkeypatch, request, ends_on=(1, "error_during_execution"))


def test_a_session_that_is_asked_for_nothing_more_is_run_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stage that reads the files a session left needs no report from it."""
    outcome, asked = driven(monkeypatch, spec())

    assert not outcome.submitted and len(asked) == 1


def test_a_session_s_actions_name_files_relative_to_its_own_directory() -> None:
    """The record is clipped, and a workspace path would take all of it."""
    from benchproofer.llm.claude_code import _action

    said = _action(
        "Read",
        {"file_path": "/scratch/agent-repair/bundles/solution.py"},
        "/scratch/agent-repair",
    )

    assert said == "Read bundles/solution.py"


def test_a_session_s_actions_name_files_relative_under_a_symlinked_directory(
    tmp_path: Path,
) -> None:
    """A tool reports the resolved path, which ends with the one the session was given."""
    from benchproofer.llm.claude_code import _action

    real = tmp_path / "real" / "home" / "workspace"
    real.mkdir(parents=True)
    (tmp_path / "home").symlink_to(tmp_path / "real" / "home")
    given = tmp_path / "home" / "workspace"

    said = _action("Bash", {"command": f"cd {real}/scratch && cat {given}/a.py"}, str(given))

    assert said == "Bash cd scratch && cat a.py"
