# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A session driven by the Claude Code command-line tool.

`claude_agent_sdk.query` starts the tool as a subprocess and streams its turns back. The
model reports its answer by calling a submit tool this module defines in-process from the
caller's own field list, so the shape a stage expects and the shape the model is shown
cannot drift apart. The payload is captured by closure rather than read from a file, so a
model that never submitted is told apart from one whose file went missing.

One prompt drives the whole session, so nothing re-invokes it to deliver a notification:
the tool's background tasks are turned off, and a shell command still running when its
time is up is stopped rather than moved to the background (`environment`). A session
stopped at its budget has done its work and said nothing about it, so the conversation is
taken up once more and asked for the report (`SessionSpec.report`).

A session has the built-in tools its request names and no others (`SessionSpec.tools`),
and two limits are checked before each tool call. Its file tools write only inside its
workspace: its scratch directory, its temporary directory, and what its request names
(`confined`). And a call that names a path is refused unless the path is one the session
may read (`fenced`): its workspace, the toolchains the run's checkers use
(`AgentSession.readable`), the directory where the tool saves its own conversation's long
tool output (`project_directory`), and the system directories programs need (`SYSTEM`).

Its environment is the run's but for four things: bash for its shell, a temporary
directory inside its workspace, a time limit on one shell command, and none of the run's
module path or Benchproofer settings, which the scripts it runs Benchproofer through read
from a file it may not (`core.scripts`).

Routing to Bedrock or to the Anthropic API is left to the tool and its environment, so a
run uses whichever of the two the machine is set up for.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import uuid4

from ..core.plugin import Availability
from ..core.scripts import SCRATCH, private
from ..errors import ProviderError
from ..log import logger
from ..util.fsio import write_json
from .agentic import AgentSession, SessionSpec, StepOutcome

if TYPE_CHECKING:
    from claude_agent_sdk import HookCallback, HookContext, HookInput, HookJSONOutput

__all__ = [
    "SYSTEM",
    "TEMPORARY",
    "ClaudeCodeSession",
    "confined",
    "environment",
    "fenced",
    "input_schema",
    "project_directory",
]

log = logger(__name__)

_INSTALL = "pip install 'benchproofer[agent]' and install the claude command-line tool"
#: What the model is told when it calls the submit tool, so that a session which
#: submits twice is not left wondering which one counted.
_ACCEPTED = "recorded; you may stop now"

#: How many of a session's tool uses are kept: enough to show what it looked at before it
#: concluded anything, without filling the notes with a long search.
ACTION_LIMIT = 24
#: Longest rendering of one tool's arguments: enough for a `Bash` command or a `Grep`
#: pattern.
_ARGUMENT_LIMIT = 120
#: The arguments that say *what* a tool was used on, in the order they are shown, so that
#: `Grep` reports its pattern and the path it searched. A file's content is not one.
_SUBJECTS: tuple[str, ...] = ("file_path", "pattern", "command", "path", "glob", "query")
#: The budget of the further turn a session that submitted nothing is asked for its report
#: in: enough to call one tool and say what it did, and no more. It is spent after the
#: session's own budget, so it cannot take time away from the work.
_REPORT_TURNS = 4
_REPORT_SECONDS = 300.0
#: The directory inside its workspace a session's `TMPDIR` names, which it may write.
TEMPORARY = "tmp"
#: The shell a session's Bash tool runs, whatever the machine's user has.
_SHELL = "/bin/bash"
#: The file tools, whose target the write limit applies to.
_WRITERS = "Write|Edit|MultiEdit|NotebookEdit"
#: The tools whose arguments the read limit checks, with the arguments that name a path.
#: Each file tool writes only where `confined` lets it, which is inside what it may read.
_READERS: dict[str, tuple[str, ...]] = {
    "Read": ("file_path",),
    "Grep": ("path",),
    "Glob": ("path", "pattern"),
    "Bash": ("command",),
}
#: What a session is told when a file tool would write elsewhere.
_CONFINED = (
    "This session writes only {allowed}: put every file of your own in its scratch directory."
)
#: What a session is told when a tool call names a path it may not read.
_FENCED = (
    "That names `{path}`, which this session may not read. It reads its workspace "
    "(`{cwd}`, with its temporary directory `{temporary}/` in `$TMPDIR`), {readable}, its "
    "own saved tool output, and the system directories {system}. Work inside the "
    "workspace: nothing else on this machine belongs in this work."
)
#: What a session is told when it runs a command that lists paths from the whole machine.
_INDEXED = (
    "`{command}` reads a list of every path on this machine, which this session may not "
    "read: search inside the workspace with `find` or `grep` instead."
)
#: The commands that read a list of every path on the machine, whatever they are given.
_LISTERS = frozenset({"locate", "mlocate", "plocate", "slocate"})
#: The system directories every session may read, as programs read them; `/lib*` is each
#: top-level library directory this machine has.
SYSTEM: tuple[str, ...] = ("/usr", "/lib*", "/bin", "/etc", "/proc", "/dev")
#: A word of a shell command, split where a shell splits words or joins a path to a name,
#: so that each path a command names is read out of it.
_WORD = re.compile(r"[^\s'\"`;|&<>()=,:]+")
#: A command word: the first of a command, or one after an operator that starts another.
_COMMAND = re.compile(r"(?:^|[;&|(`{\n]|\$\()\s*(?:sudo\s+|exec\s+|command\s+)?([\w.+-]+)")
#: A change of directory, and the directory it names.
_CHDIR = re.compile(r"(?:^|[;&|(`{\n])\s*(?:cd|pushd)\s+([^\s;&|)]+)")
#: A change of directory that names no directory, which goes home (`cd`) or back (`cd -`).
_HOMEWARD = re.compile(r"(?:^|[;&|(`{\n])\s*(?:cd|pushd)(?:\s+-)?\s*(?=$|[;&|)}\n])")
#: A here-document: its opening line, kept, and the text it hands the command, up to the
#: line that ends it.
_HEREDOC = re.compile(
    r"((?<!<)<<(?!<)-?[ \t]*(['\"]?)([\w.-]+)\2[^\n]*\n).*?(?:\n[ \t]*\3[ \t]*(?=\n|$)|\Z)",
    re.DOTALL,
)
#: A variable as a shell spells it, `$NAME` or `${NAME}`.
_VARIABLE = re.compile(r"\$(?:\{(\w+)\}|(\w+))")
#: The characters with which a shell matches or builds many names out of one word.
_PATTERN = frozenset("*?[{")
#: Benchproofer's own package, which no session reads wherever it is installed.
_OWN = Path(__file__).resolve().parents[1]
#: The longest name Claude Code gives a project directory before it cuts the name and adds a
#: hash of the whole path.
_PROJECT_NAME = 200


def sdk_missing() -> str:
    """Why a Claude Code session cannot run here, or an empty string when it can.

    Two separate requirements, and the messages name which one is absent, because
    installing the Python package does not install the command-line tool it drives.
    """
    try:
        import claude_agent_sdk  # noqa: F401
    except ImportError:
        return (
            "the claude-agent-sdk package is not installed; install this project's "
            "'agent' extra"
        )
    if shutil.which("claude") is None and not os.environ.get("CLAUDE_CODE_PATH"):
        return "the claude command-line tool is not on PATH"
    return ""


def input_schema(spec: SessionSpec) -> dict[str, Any]:
    """The submit tool's input, as the whole JSON schema the SDK sends on the wire.

    Whole, because of how `claude_agent_sdk.tool` reads a dict: one with `type` and
    `properties` is a schema and passes through; any other is a map from name to *Python
    type*, and a JSON-schema property is not a Python type, so every field would fall
    through to a required, untyped string with its description dropped, and a boolean
    would arrive as `"false"`, which reads as true.
    """
    return {"type": "object", "properties": dict(spec.fields), "required": list(spec.required)}


def environment(spec: SessionSpec, command_s: float | None = None) -> dict[str, str]:
    """What a session's environment sets over the run's.

    One shell command may run ``command_s`` seconds, or the session's whole budget where
    that is shorter or no limit is given, and is stopped then: with the tool's background
    tasks off, a command that reaches its timeout is stopped instead of being moved to the
    background with a promise of a notification nothing delivers. The shell is bash,
    whatever the machine's user runs, so a command written for bash runs as written.
    `TMPDIR` names the temporary directory inside the workspace (`TEMPORARY`). And the
    run's module path and Benchproofer settings are emptied (`core.scripts.private`): they
    say where Benchproofer's source is, and the scripts the session runs Benchproofer
    through set them again from a file the session may not read.
    """
    seconds = spec.timeout_s if command_s is None else min(spec.timeout_s, command_s)
    milliseconds = str(max(1, round(seconds * 1000)))
    return {
        **dict.fromkeys(private(os.environ), ""),
        "BASH_DEFAULT_TIMEOUT_MS": milliseconds,
        "BASH_MAX_TIMEOUT_MS": milliseconds,
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
        "SHELL": _SHELL,
        "TMPDIR": (Path(spec.cwd) / TEMPORARY).as_posix(),
    }


def writable(spec: SessionSpec) -> tuple[Path, ...]:
    """Where a session's file tools may write.

    What its request names, its scratch directory and its temporary directory.
    """
    cwd = Path(spec.cwd)
    return (*spec.writable, cwd / SCRATCH, cwd / TEMPORARY)


def confined(spec: SessionSpec) -> HookCallback:
    """A hook refusing a file tool's write outside what `writable` gives ``spec``.

    The target is resolved against the session's directory, so neither a relative path nor
    a symlink reaches past the limit. A call naming no target is left to the tool.
    """
    places = writable(spec)
    allowed = tuple(path.resolve() for path in places)
    said = _CONFINED.format(
        allowed=", ".join(
            f"`{_shown(path.resolve(), Path(spec.cwd).resolve())}`" for path in places
        )
    )

    async def hook(
        called: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        arguments = called.get("tool_input")
        target = (
            arguments.get("file_path") or arguments.get("notebook_path")
            if isinstance(arguments, dict)
            else None
        )
        if not isinstance(target, str):
            return {}
        path = _resolved(target, Path(str(called.get("cwd") or spec.cwd)))
        return {} if path is not None and _under(path, allowed) else _denied(said)

    return hook


def fenced(
    cwd: Path,
    readable: Sequence[Path] = (),
    env: Mapping[str, str] | None = None,
    *,
    conversation: str | None = None,
) -> HookCallback:
    """A hook refusing a tool call that names a path the session in ``cwd`` may not read.

    It may read ``cwd``, ``readable``, the directory its Claude Code project directory
    (`project_directory`) keeps for ``conversation``, where the tool saves a tool's output
    too long to show, and the system directories (`SYSTEM`). Every session started in
    ``cwd`` shares that project directory, so the transcripts of the others there, an
    earlier round's or an earlier ask's, are refused; with no ``conversation`` the whole of
    it is read. The path arguments of the
    file and search tools are read, and each word of a shell command that reads as a path:
    one that starts with `/`, `~` or `$`, holds a `/`, or is `..`. A bare `/` inside quotes
    is text (`'/'.join`, `echo "a / b"`) rather than the root, and the text a here-document
    hands a command is that program's, as a written file's content is; neither is read.

    Each path is resolved from the directory the call runs in, or from one the command
    changes into before it, with `~` and the variables of ``env`` (the session's own)
    spelled out and symlinks followed, so a relative path, a variable or a link that leads
    out is refused as the path it reaches. A word the shell expands to many names is judged
    by the directory it matches them in, so `/l*` is `/`. A path under a top-level
    directory this machine does not have, such as a container's `/app`, names nothing here
    and is let through.

    Refused within what it may read: Benchproofer's own package, wherever it is installed,
    since it judges what the session writes; and a process's own directory under `/proc`,
    which shows that process's environment. Refused outright: a change of directory that
    names none, which goes home, and a command that reads a list of every path on the
    machine (`locate`).

    What a command builds while it runs is not seen: a path the shell or a program puts
    together, or one a program reads of its own accord. The hook keeps a session's reads
    and searches inside what it is given; what it read anyway is in its transcript.
    """
    here = cwd.resolve()
    kept = project_directory(here).resolve()
    roots: tuple[Path, ...] = (here, kept / conversation if conversation else kept)
    roots += tuple(path.resolve() for path in readable)
    roots += tuple(_system())
    spelled = dict(os.environ if env is None else env)
    said = {
        "cwd": here.as_posix(),
        "temporary": TEMPORARY,
        "readable": ", ".join(f"`{path.as_posix()}`" for path in readable) or "nothing else",
        "system": ", ".join(f"`{path}`" for path in SYSTEM),
    }

    def refused(path: Path) -> bool:
        reached = path.resolve()
        if _absent(reached):
            return False
        return _process(path) or _under(reached, (_OWN,)) or not _under(reached, roots)

    async def hook(
        called: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        tool = str(called.get("tool_name") or "")
        arguments = called.get("tool_input")
        if tool not in _READERS or not isinstance(arguments, dict):
            return {}
        within = Path(str(called.get("cwd") or here))
        shell = {**spelled, "PWD": within.as_posix()}
        command = arguments.get("command") if tool == "Bash" else None
        if isinstance(command, str):
            lister = next((word for word in _COMMAND.findall(command) if word in _LISTERS), "")
            if lister:
                return _denied(_INDEXED.format(command=lister))
            named = _commanded(command, within, shell)
        else:
            named = _argued(tool, arguments, within, shell)
        for reached in named:
            if reached and all(refused(path) for path in reached):
                return _denied(_FENCED.format(path=_shown(reached[0].resolve(), here), **said))
        return {}

    return hook


def project_directory(cwd: Path) -> Path:
    """The directory Claude Code keeps the conversation of a session started in ``cwd`` in.

    It is `projects/<name>` under the tool's configuration directory (`CLAUDE_CONFIG_DIR`,
    or `~/.claude`), where the name is the resolved working directory with each character
    but an ASCII letter or digit made `-`, and a name longer than 200 characters is cut there
    and followed by `-` and a base-36 hash of the whole path, as the tool derives it. The
    tool saves there a tool's output too long to show, and the session reads it back.
    """
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
    # The tool works on the path's UTF-16 code units, which its JavaScript strings hold.
    encoded = str(cwd.resolve()).encode("utf-16-le")
    units = [int.from_bytes(encoded[at : at + 2], "little") for at in range(0, len(encoded), 2)]
    name = "".join(
        chr(unit) if chr(unit).isascii() and chr(unit).isalnum() else "-" for unit in units
    )
    if len(name) > _PROJECT_NAME:
        name = f"{name[:_PROJECT_NAME]}-{_base36(abs(_hashed(units)))}"
    return home / "projects" / name


def _hashed(units: Sequence[int]) -> int:
    """The tool's hash of a path: ``hash * 31 + unit`` over its code units, a signed int32."""
    found = 0
    for unit in units:
        found = (found * 31 + unit) & 0xFFFFFFFF
    return found - (1 << 32) if found >= 1 << 31 else found


def _base36(number: int) -> str:
    """``number``, which is not negative, in base 36 with lower-case digits."""
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    spelled = ""
    while True:
        number, digit = divmod(number, 36)
        spelled = digits[digit] + spelled
        if not number:
            return spelled


def _denied(reason: str) -> HookJSONOutput:
    """A hook's answer refusing one tool call, with what the session is told."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _commanded(command: str, cwd: Path, env: Mapping[str, str]) -> Iterator[tuple[Path, ...]]:
    """Every path a shell command names, outside its here-documents (`fenced`).

    Each comes with every path it may reach: a relative one from the directory the command
    starts in and from each it changes into, of which any one may be the one it is read
    from.
    """
    shell = _HEREDOC.sub(lambda found: found.group(1), command)
    if _HOMEWARD.search(shell):
        yield (Path(env.get("HOME") or Path.home()),)
    bases = [cwd]
    for found in _CHDIR.finditer(shell):
        moved = _spelled(found.group(1), bases[-1], env)
        if moved is not None:
            bases.append(moved)
    for word, quoted in _words(shell):
        if quoted and not word.strip("/"):
            continue
        if word.startswith(("/", "~", "$")) or "/" in word or word == "..":
            reached = [_spelled(word, base, env) for base in bases]
            # The shell expands a pattern only outside quotes.
            yield tuple(
                path if quoted else _scope(path) for path in reached if path is not None
            )


def _words(shell: str) -> Iterator[tuple[str, bool]]:
    """Each word of ``shell`` (`_WORD`), and whether it is inside quotes.

    A word straight after a closing `)` or backtick is left out: it is the rest of a path
    whose start a substitution prints, which only running the command shows.
    """
    pieces: list[tuple[str, bool]] = []
    quote, start = "", 0
    for at, char in enumerate(shell):
        if not quote and char in "'\"":
            pieces.append((shell[start:at], False))
            quote, start = char, at + 1
        elif quote and char == quote and not (quote == '"' and shell[at - 1 : at] == "\\"):
            pieces.append((shell[start:at], True))
            quote, start = "", at + 1
    pieces.append((shell[start:], bool(quote)))
    for text, quoted in pieces:
        for found in _WORD.finditer(text):
            if found.start() == 0 or text[found.start() - 1] not in ")`":
                yield found.group(0), quoted


def _argued(
    tool: str, arguments: Mapping[str, object], cwd: Path, env: Mapping[str, str]
) -> Iterator[tuple[Path, ...]]:
    """Every path the arguments of a file or search tool name, resolved (`fenced`).

    A `Glob` pattern counts only where it leaves the directory it is given: one that starts
    with `/` or `~`, or climbs out with `..`.
    """
    for key in _READERS[tool]:
        value = arguments.get(key)
        if not isinstance(value, str) or not value:
            continue
        if key == "pattern" and not (value.startswith(("/", "~")) or ".." in value):
            continue
        path = _spelled(value, cwd, env)
        if path is not None:
            yield (_scope(path),)


def _spelled(word: str, cwd: Path, env: Mapping[str, str]) -> Path | None:
    """``word`` as an absolute path from ``cwd``, symlinks not yet followed, or None.

    Each variable ``env`` defines is replaced by its value, as the shell would, and `~` by
    the home directory; a variable it does not define is left as written.
    """
    expanded = _VARIABLE.sub(
        lambda found: env.get(found.group(1) or found.group(2), found.group(0)), word
    )
    try:
        path = Path(expanded).expanduser()
        return Path(os.path.normpath(path if path.is_absolute() else cwd / path))
    except (OSError, ValueError, RuntimeError):
        return None


def _resolved(spelled: str, cwd: Path) -> Path | None:
    """``spelled`` as the path it reaches from ``cwd``, or None when it cannot be one."""
    try:
        path = Path(spelled).expanduser()
        return (path if path.is_absolute() else cwd / path).resolve()
    except (OSError, ValueError, RuntimeError):
        return None


def _scope(path: Path) -> Path:
    """``path`` cut before its first part that matches many names (`*`, `?`, `[`, `{`)."""
    for at, part in enumerate(path.parts):
        if _PATTERN & set(part):
            return Path(*path.parts[:at])
    return path


def _absent(path: Path) -> bool:
    """Whether ``path`` lies under a top-level directory this machine does not have.

    A pattern the shell expands has been cut before it (`_scope`), so a part that holds one
    here is a name as written.
    """
    parts = path.parts
    return len(parts) > 1 and not Path("/", parts[1]).exists()


def _process(path: Path) -> bool:
    """Whether ``path`` is in a process's own directory under `/proc`."""
    parts = path.parts
    return len(parts) > 2 and parts[1] == "proc" and (parts[2].isdigit() or "self" in parts[2])


def _system() -> Iterator[Path]:
    """The system directories of `SYSTEM` this machine has, `/lib*` spelled out."""
    for spelled in SYSTEM:
        if spelled.endswith("*"):
            yield from sorted(Path("/").glob(spelled.lstrip("/")))
        else:
            yield Path(spelled)


def _under(path: Path, roots: Sequence[Path]) -> bool:
    """Whether ``path`` is one of ``roots`` or lies under one."""
    return any(path == root or root in path.parents for root in roots)


def _shown(path: Path, cwd: Path) -> str:
    """``path`` relative to ``cwd`` where it lies under it, for what a session is told."""
    with suppress(ValueError):
        return path.relative_to(cwd).as_posix()
    return path.as_posix()


def _action(name: str, arguments: object, cwd: str = "") -> str:
    """One line saying what a tool was used on, for the record of a session's work.

    Paths under the session's own directory are shown relative to it, so the line is
    spent on the file rather than on where the workspace happens to be.
    """
    if not isinstance(arguments, dict):
        return name
    said = [
        str(arguments[key]).replace("\n", " ")
        for key in _SUBJECTS
        if arguments.get(key) is not None
    ]
    detail = " ".join(said).strip()
    if cwd:
        # The directory as named and as resolved, longest first, and only where a path
        # starts: under a symlinked home, one is the tail of the other.
        named = {cwd.rstrip("/"), str(Path(cwd).resolve())}
        for prefix in sorted(named, key=len, reverse=True):
            detail = re.sub(r"(?<![\w/.])" + re.escape(prefix + "/"), "", detail)
    if len(detail) > _ARGUMENT_LIMIT:
        detail = detail[: _ARGUMENT_LIMIT - 1].rstrip() + "…"
    return f"{name} {detail}".strip()


def _keep(
    directory: Path,
    conversation: str,
    spec: SessionSpec,
    model: str,
    readable: Sequence[Path],
    env: Mapping[str, str],
) -> None:
    """Write what one session is asked, so a reader can see what it was and was not given.

    Claude Code keeps the conversation under its own projects directory as
    `<conversation>.jsonl`, without the system prompt; this file has the whole request, what
    the session could read and write, what its environment set, and the id that finds the
    rest.
    """
    write_json(
        directory / f"{spec.submit}-{conversation}.json",
        {
            "session": conversation,
            "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": model,
            "cwd": str(spec.cwd),
            "submit": spec.submit,
            "fields": spec.fields,
            "required": list(spec.required),
            "tools": list(spec.tools),
            "writable": [path.as_posix() for path in writable(spec)],
            "readable": [path.as_posix() for path in readable],
            "env": dict(env),
            "max_turns": spec.max_turns,
            "timeout_s": spec.timeout_s,
            "system": spec.system,
            "prompt": spec.prompt,
            "report": spec.report,
        },
    )


class ClaudeCodeSession(AgentSession):
    """Run one Claude Code session and take its submitted payload."""

    name: ClassVar[str] = "claude-code"
    summary: ClassVar[str] = "the Claude Code tool, with file tools and turns of its own"

    def availability(self) -> Availability:
        """Report whether the package and the command-line tool are both present."""
        missing = sdk_missing()
        if missing:
            return Availability.missing(missing, hint=_INSTALL)
        return Availability.ok(detail=self.model or "the tool's default model")

    def run(self, spec: SessionSpec) -> StepOutcome:
        """Run one session to completion, or until its budget runs out."""
        missing = sdk_missing()
        if missing:
            raise ProviderError(missing)
        try:
            return asyncio.run(self._run(spec))
        except ProviderError:
            raise
        except Exception as exc:  # the SDK raises its own hierarchy
            raise ProviderError(f"the claude-code session failed: {exc}") from exc

    async def _run(self, spec: SessionSpec) -> StepOutcome:
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ClaudeSDKError,
            HookMatcher,
            ResultMessage,
            TextBlock,
            ToolUseBlock,
            create_sdk_mcp_server,
            query,
            tool,
        )

        taken: dict[str, Any] = {}

        @tool(spec.submit, f"Report your {spec.submit.replace('_', ' ')}.", input_schema(spec))
        async def submit(args: dict[str, Any]) -> dict[str, Any]:
            taken.update(args)
            return {"content": [{"type": "text", "text": _ACCEPTED}]}

        server = create_sdk_mcp_server(name="benchproofer", tools=[submit])
        # Under `bypassPermissions` nothing is asked before a tool runs, so what a session
        # may not do with a tool it has is refused here, one call at a time.
        cwd = Path(spec.cwd)
        (cwd / TEMPORARY).mkdir(parents=True, exist_ok=True)
        env = environment(spec, self.command_timeout_s)
        # Named here rather than read off the stream, so the conversation can be taken up
        # again even when the budget cut it off before it reported anything at all, and its
        # read guard opens its own saved output and no other session's.
        conversation = str(uuid4())
        guards = [
            HookMatcher(matcher=_WRITERS, hooks=[confined(spec)]),
            HookMatcher(
                matcher="|".join(_READERS),
                hooks=[
                    fenced(
                        cwd,
                        self.readable,
                        {**os.environ, **env},
                        conversation=conversation,
                    )
                ],
            ),
        ]
        name = f"mcp__benchproofer__{spec.submit}"
        if self.record_dir is not None:
            _keep(self.record_dir, conversation, spec, self.model, self.readable, env)
        options = ClaudeAgentOptions(
            system_prompt=spec.system,
            cwd=str(spec.cwd),
            # The built-in tools the session has; under `bypassPermissions` the allowed
            # list below grants every tool it names and restricts none.
            tools=list(spec.tools),
            # Without an explicit list the tool asks permission for everything and a
            # non-interactive session then makes no progress at all.
            allowed_tools=[*spec.tools, name],
            permission_mode="bypassPermissions",
            hooks={"PreToolUse": guards},
            # None of the machine's own Claude Code settings: not its model or AWS profile,
            # not its memory files, rules or MCP servers. A session sees what its request
            # gives it, and runs on the model the run declares.
            setting_sources=[],
            mcp_servers={"benchproofer": server},
            max_turns=spec.max_turns,
            # `session_for` sets the run's model. None, for a session built some other
            # way, leaves the choice to the tool's default.
            model=self.model or None,
            session_id=conversation,
            env=env,
        )

        said: list[str] = []
        counts = {"turns": 0, "uses": 0}
        reported: list[str] = []
        actions: list[str] = []

        async def consume(prompt: str, asked: ClaudeAgentOptions) -> None:
            async for message in query(prompt=prompt, options=asked):
                if isinstance(message, AssistantMessage):
                    counts["turns"] += 1
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            said.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            counts["uses"] += 1
                            if len(actions) < ACTION_LIMIT:
                                actions.append(_action(block.name, block.input, str(spec.cwd)))
                elif isinstance(message, ResultMessage):
                    reported.append(getattr(message, "subtype", "") or "")

        async def spend(prompt: str, asked: ClaudeAgentOptions, budget: float) -> str:
            try:
                # `wait_for` rather than a timeout context, because this package supports
                # the Python the rest of it supports and `asyncio.timeout` arrived after it.
                await asyncio.wait_for(consume(prompt, asked), budget)
            except (TimeoutError, asyncio.TimeoutError):
                # Whatever the session had already said and done is kept: a run stopped at
                # its budget may still have submitted, and discarding that would report a
                # slow machine as a model that had nothing to say.
                log.warning("claude-code session for %s timed out", spec.submit)
                return f"no report within {budget:.0f}s"
            except ClaudeSDKError as exc:
                # The tool ends a session that used every turn it was given with an error
                # result, and that is its budget running out like the time: what it did is
                # on disk, and only a report says what may be kept of it. Any other error
                # result is the tool's own.
                if getattr(exc, "subtype", None) != "error_max_turns":
                    raise
                log.warning("claude-code session for %s used all its turns", spec.submit)
                return f"no report within {asked.max_turns} turn(s)"
            return reported[-1] if reported else ""

        started = time.monotonic()
        detail = await spend(spec.prompt, options, spec.timeout_s)
        if not taken and spec.report:
            # A session stopped before it reported has done the work all the same, and
            # only its report says what may be kept of it.
            log.info("asking the %s session of its own for a report", spec.submit)
            said_so = await spend(
                spec.report,
                # Taking the conversation up again rather than naming it: the tool is being
                # given an id it has already seen.
                replace(
                    options,
                    resume=conversation,
                    session_id=None,
                    max_turns=_REPORT_TURNS,
                ),
                _REPORT_SECONDS,
            )
            detail = "; ".join(part for part in (detail, f"asked to report: {said_so}") if part)

        missing = [key for key in spec.required if key not in taken]
        if taken and missing:
            # A partial submission is not an answer: the caller asked for these fields
            # because it cannot act without them, and half of one recorded as a result
            # would be a stage reporting work it did not do.
            detail = f"submitted without {', '.join(missing)}"
            taken.clear()
        return StepOutcome(
            text="\n\n".join(said).strip(),
            payload=dict(taken) if taken else None,
            duration_s=time.monotonic() - started,
            turns=counts["turns"],
            tool_uses=counts["uses"],
            detail=detail,
            actions=tuple(actions),
        )
