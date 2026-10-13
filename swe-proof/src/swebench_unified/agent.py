# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Claude Agent SDK wrapper for construction (P1) and audit (P2) steps.

Spawns the Claude Code CLI via claude_agent_sdk.query(), with an in-process
submit_result MCP server capturing the step's structured payload (see
submit_result.py). Not sandboxed, so it assumes a trusted single-tenant
machine; the agent writes only into tasks/<id>/. Bedrock/Anthropic routing is
via pass-through env vars.
"""
from __future__ import annotations

import asyncio
import collections
import contextlib
import fcntl
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# THE rule every cap, wait and retry here is sized against: a launch that never
# ran measured nothing, yet the harness stamps the role `fail`, which reads as
# "this spec admits a wrong implementation". A lost launch therefore costs a WRONG
# ARTIFACT, not a slow run, so every limit below fails OPEN rather than closed.
#
# How many agent CLIs may be in flight at once, ACROSS PROCESSES.
#
# A BACKSTOP, not a diagnosis: concurrency is not what a failed launch tracks.
# The cap stays because of the rule above, so the default sits well ABOVE normal
# operation: high enough that a healthy queue never waits, low enough to stop a
# runaway from taking the host with it.
AGENT_SLOTS = int(os.environ.get("SBU_AGENT_SLOTS") or 64)
_SLOT_DIR = Path(os.environ.get("SBU_AGENT_SLOT_DIR")
                 or (Path(tempfile.gettempdir()) / "sbu_agent_slots"))

# How long a launch may QUEUE for a slot before giving up on one and proceeding
# unslotted.
#
# Failing open is right, for the reason above; waiting the role's WHOLE cap
# before doing so is not. Queue time and run time are drawn from the same wall
# clock, so a role that spends its entire cap in the queue reaches the CLI with
# nothing left to spend: it is killed at its cap having done no work, and that
# non-measurement is recorded as a failed audit. Bounding the queue to a small
# share of the cap is what makes a starved role fail open EARLY, with its working
# budget intact.
#
# The floor matters for short steps, where a fraction of the cap would round
# down to a queue too brief to ever win a slot on a busy host, making the limit
# advisory in exactly the conditions it is meant to enforce.
SLOT_WAIT_FRACTION = float(os.environ.get("SBU_AGENT_SLOT_WAIT_FRAC") or 0.1)
SLOT_WAIT_MAX_S = int(os.environ.get("SBU_AGENT_SLOT_WAIT_MAX") or 300)
SLOT_WAIT_MIN_S = int(os.environ.get("SBU_AGENT_SLOT_WAIT_MIN") or 30)
# Never hand asyncio a zero or negative timeout: `wait_for` treats that as
# "already expired" and would report a launch that never happened as a run that
# timed out, which is the same wrong artifact by another route.
#
# It is a floor on the REMAINDER, never a grant: it is always clamped down to
# the step's own cap first. Left unclamped it inverts the fix -- a 10s step that
# queues its whole 10s would come out with a 60s run, so the wait-deduction
# hands back MORE than the caller budgeted.
MIN_RUN_BUDGET_S = 60


def _slot_wait_budget(timeout_s: int) -> int:
    """Seconds a launch may spend queueing for a slot, given the step's cap.

    Never more than the cap itself: a wait that outlives the step it serves is
    the stall that bounding the queue exists to prevent.
    """
    if timeout_s <= SLOT_WAIT_MIN_S:
        return max(0, timeout_s)
    return int(max(SLOT_WAIT_MIN_S,
                   min(SLOT_WAIT_MAX_S, timeout_s * SLOT_WAIT_FRACTION)))


def _run_budget(timeout_s: int, queued_at: float) -> float:
    """What is left of `timeout_s` after queueing since `queued_at`.

    Bounded above by the cap (queueing cannot earn time) and below by
    MIN_RUN_BUDGET_S clamped to the cap (queueing cannot leave nothing).
    """
    floor = min(float(MIN_RUN_BUDGET_S), float(timeout_s))
    return max(floor, timeout_s - (time.monotonic() - queued_at))

# ---------------------------------------------------------------------------
# Credential outages.
#
# The CLI cannot tell a caller "your credentials are gone" in any actionable
# way: it reports is_error=true with subtype="success" and stop_reason=
# "stop_sequence", and the only trace of the cause is a synthetic assistant turn
# reading "Not logged in - Please run /login". Nothing about the bundle, the
# prompt or the machine's load moves that, which is why the text of that turn is
# the only usable detector.
#
# It matters because a role that never authenticated is recorded as a FAILED
# audit, and each process, blind to the others, spends its whole retry budget
# re-confirming the outage cell by cell.
#
# So the backoff is SHARED, through a file whose mtime is the last time any
# process saw an auth failure: a waiter proceeds only once nobody has seen one
# for AUTH_QUIET_S. That needs no probe -- the failures themselves are the clock
# -- and the herd that arrives when the flag goes stale is how the host finds out
# credentials are back, at one launch per role per quiet period instead of a
# continuous burn.
AUTH_QUIET_S = int(os.environ.get("SBU_AUTH_QUIET") or 300)
AUTH_MAX_WAIT_S = int(os.environ.get("SBU_AUTH_MAX_WAIT") or 3600)
AUTH_RETRIES = int(os.environ.get("SBU_AUTH_RETRIES") or 3)
_AUTH_FLAG = Path(os.environ.get("SBU_AUTH_FLAG")
                  or (Path(tempfile.gettempdir()) / "sbu_auth_down"))

# Matched against the whole failure description. "Not logged in" is what the CLI
# actually shows; `authentication_failed` is the field name in its transcript;
# the AWS codes are what a Bedrock deployment surfaces when its temporary
# credentials lapse, and all of them mean the same thing to us -- no request was
# made, so nothing was measured.
_AUTH_MARKERS = (
    "not logged in", "please run /login", "authentication_failed",
    "expiredtoken", "expired token", "invalidsignatureexception",
    "unrecognizedclientexception", "credentials could not be",
    "unable to locate credentials", "invalidclienttokenid",
)


# How many times to re-launch a CLI that died having produced nothing.
#
# Distinct from the auth retries and from the caller's: this is the failure with
# no diagnostic at all -- is_error=true, subtype="success", empty stderr. Each one
# is stamped `fail`, so the cost of not retrying is a wrong artifact rather than a
# slow one. The retry is safe only because it is conditioned on the launch having
# done NOTHING (see LaunchFailure.did_work): re-running a role that already
# submitted, or already wrote attack files, would double its side effects.
LAUNCH_RETRIES = int(os.environ.get("SBU_LAUNCH_RETRIES") or 2)
LAUNCH_BACKOFF_S = float(os.environ.get("SBU_LAUNCH_BACKOFF") or 10)


class LaunchFailure(RuntimeError):
    """The CLI's message stream ended in an error.

    Carries how much the step had produced when it died, because that is what
    decides whether re-launching is sound. A stream that failed before any tool
    ran and before any text arrived measured nothing and touched nothing.
    """

    def __init__(self, msg: str, tool_uses: int = 0, chars: int = 0) -> None:
        super().__init__(msg)
        self.tool_uses = tool_uses
        self.chars = chars

    @property
    def did_work(self) -> bool:
        return self.tool_uses > 0 or self.chars > 0


class AgentAuthError(RuntimeError):
    """The CLI never authenticated, so it never measured anything.

    A distinct type because the remedy is categorically different from an agent
    that ran and misbehaved: waiting is the whole fix, and no verdict about the
    bundle may be derived from it.
    """


def is_auth_failure(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in _AUTH_MARKERS)


def provider_preflight(env: Optional[dict] = None) -> str:
    """Why the agent CLI has no way to authenticate, or "" if it has one.

    A process started from a non-interactive parent inherits none of a shell's
    provider routing, and the CLI it launches then reports "not logged in". That
    failure is INDISTINGUISHABLE at the call site from a real credential outage,
    and treating it as one is expensive: the outage flag is host-wide, so every
    process's launches are held for AUTH_QUIET_S while the one misconfigured
    process waits out the quiet period and re-stamps it.

    So this is checked BEFORE the wait: no configuration is an operator fault
    that must be reported now, at the process that has it, and never published to
    the rest of the host as an outage.
    """
    e = os.environ if env is None else env

    def on(name: str) -> bool:
        return (e.get(name) or "").strip().lower() not in ("", "0", "false")

    if on("CLAUDE_CODE_USE_BEDROCK") or on("CLAUDE_CODE_USE_VERTEX"):
        return ""
    if (e.get("ANTHROPIC_API_KEY") or e.get("ANTHROPIC_AUTH_TOKEN")
            or e.get("CLAUDE_CODE_OAUTH_TOKEN")):
        return ""
    # An interactive login the CLI itself stored is the remaining valid route.
    home = e.get("HOME") or os.path.expanduser("~")
    if (Path(home) / ".claude" / ".credentials.json").is_file():
        return ""
    # Every route the checks above accept, named: an operator holding one this
    # message leaves out is told no route is configured, which is false.
    return ("no provider is configured for the agent CLI: none of "
            "CLAUDE_CODE_USE_BEDROCK, CLAUDE_CODE_USE_VERTEX, "
            "ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN "
            "or a stored CLI login (~/.claude/.credentials.json) is present in "
            "this process's environment, so every launch would fail "
            "'not logged in' having measured nothing")


def _note_auth_failure(why: str = "") -> None:
    """Publish "credentials just failed" for every process on this host.

    The reason is LOGGED as well as published: carried only in the AgentAuthError
    -- which the caller turns into a per-cell verdict -- the one fact an operator
    needs, what the CLI actually said, appears in no log while the flag stalls the
    host.
    """
    logger.error("credentials failed, holding every launch on this host for "
                 "%ss: %s", AUTH_QUIET_S, (why or "no diagnostic")[:400])
    with contextlib.suppress(OSError):
        _AUTH_FLAG.parent.mkdir(parents=True, exist_ok=True)
        _AUTH_FLAG.touch()
        os.utime(_AUTH_FLAG, None)


def _wait_out_auth_outage(max_wait_s: int) -> float:
    """Block while any process on this host is still seeing auth failures.

    Returns the seconds waited. Bounded: past `max_wait_s` the launch goes ahead
    and is allowed to fail, because an outage longer than the budget is
    something the operator has to hear about, not something to hide by hanging.
    """
    waited = 0.0
    while waited < max_wait_s:
        try:
            quiet_for = time.time() - _AUTH_FLAG.stat().st_mtime
        except OSError:
            return waited                       # no outage on record
        if quiet_for >= AUTH_QUIET_S:
            return waited
        nap = min(30.0, AUTH_QUIET_S - quiet_for, max_wait_s - waited)
        if nap <= 0:
            return waited
        if waited == 0.0:
            logger.warning("credentials failed %.0fs ago on this host; holding "
                           "the launch until %ss quiet", quiet_for, AUTH_QUIET_S)
        time.sleep(nap)
        waited += nap
    logger.warning("credential outage still active after %ss; launching anyway",
                   max_wait_s)
    return waited


@contextlib.contextmanager
def _agent_slot(wait_s: int):
    """Hold one of AGENT_SLOTS cross-process slots for the duration of a launch.

    A directory of lock files, each `flock`'d non-blocking: the OS releases a
    slot when its holder dies, so a killed process cannot leak one (a counter in a
    file could). Slots are probed from a per-process offset so N waiters do not
    all queue behind slot 0.

    Fails OPEN on exhaustion: after `wait_s` of queueing the launch proceeds
    unslotted, because a launch that MIGHT fail is better than a launch that
    certainly does not happen -- the caller's retry can absorb the former, while
    the latter is recorded as a spec defect.

    `wait_s` is a QUEUE budget, not the step's cap. Passing the step's cap here
    is the failure described at SLOT_WAIT_FRACTION: the launch fails open with
    none of its working time left, so it is killed at its cap having measured
    nothing. Callers should size it with `_slot_wait_budget`.
    """
    if AGENT_SLOTS <= 0:
        yield True
        return
    _SLOT_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0, wait_s)
    fh = None
    try:
        while fh is None:
            for i in range(AGENT_SLOTS):
                n = (os.getpid() + i) % AGENT_SLOTS
                cand = open(_SLOT_DIR / f"slot{n}", "a+b")
                try:
                    fcntl.flock(cand.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    cand.close()
                    continue
                fh = cand
                break
            if fh is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    logger.warning("no agent slot after %ss; launching unslotted",
                                   wait_s)
                    break
                # Never sleep past the budget. A fixed poll interval OVERSHOOTS a
                # short deadline, which silently converts "fail open after N
                # seconds" into "block for one poll interval" -- the wait outliving
                # its own budget is precisely what fail-open exists to prevent.
                time.sleep(min(3.0, remaining))
        yield fh is not None
    finally:
        if fh is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            fh.close()


def _describe_error(message, cli_err) -> str:
    """Everything the CLI told us about why it failed, on one line.

    The SDK renders a failed launch as "Claude Code returned an error result:
    success" -- the `subtype` standing in for a diagnostic that never arrived.
    That string is worse than useless here, because it is recorded into
    meta.json where a reader takes it for an audit verdict on the spec. So take
    the fields the result actually carries (an api_error_status distinguishes
    throttling from a crash, num_turns=0 distinguishes "never started" from
    "died mid-run") plus the CLI's own stderr, and never report an empty reason.
    """
    bits: list[str] = []
    for key in ("subtype", "stop_reason", "terminal_reason", "api_error_status",
                "num_turns", "session_id"):
        val = getattr(message, key, None)
        if val not in (None, "", []):
            bits.append(f"{key}={val}")
    errors = getattr(message, "errors", None) or []
    if errors:
        bits.append(f"errors={errors}")
    result = (getattr(message, "result", None) or "").strip()
    if result:
        bits.append(f"result={result[:300]!r}")
    tail = [ln for ln in (cli_err or []) if ln.strip()]
    if tail:
        bits.append("stderr=" + " / ".join(tail[-6:])[:600])
    return "; ".join(bits) or "no diagnostic of any kind"


def _kill_descendants(root_pid: int, mark: str | None = None) -> None:
    """SIGKILL descendant processes of root_pid (leaving root alive).

    Used on agent timeout: asyncio cancellation frees the coroutine but the
    spawned `claude` CLI (and its own children — lean-lsp, docker, verifiers)
    keep running. Walk /proc to build the child map, then kill the subtree
    bottom-up. Best-effort; races on a dying pid are ignored.

    `mark`: when given, kill ONLY subtree members whose environment carries
    SBU_AGENT_MARK=<mark> (children inherit it from the spawned CLI). Without
    it, a THREADED caller's timeout would SIGKILL every concurrent sibling
    agent in the same process: one agent hitting its wall clock takes out
    every other in-flight agent (the same hazard sits under
    run_audit_stage's concurrent roles)."""
    import signal

    def _marked(pid: int) -> bool:
        if mark is None:
            return True
        try:
            with open(f"/proc/{pid}/environ", "rb") as fh:
                return f"SBU_AGENT_MARK={mark}".encode() in fh.read()
        except OSError:
            return False
    children: dict[int, list[int]] = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as fh:
                # ppid is field 4, but comm (field 2) may contain spaces/parens;
                # split after the closing paren to stay correct.
                data = fh.read()
                ppid = int(data[data.rfind(")") + 2:].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        children.setdefault(ppid, []).append(int(entry))
    # collect the subtree under root_pid (excluding root)
    subtree: list[int] = []
    stack = list(children.get(root_pid, []))
    while stack:
        pid = stack.pop()
        subtree.append(pid)
        stack.extend(children.get(pid, []))
    for pid in reversed(subtree):  # children before parents
        if not _marked(pid):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

# Bedrock needs the inference-profile prefix (us.anthropic.…); a bare model id
# makes the spawned CLI error immediately ("error result: success", no tool use).
_BEDROCK = os.environ.get("CLAUDE_CODE_USE_BEDROCK", "").strip() not in ("", "0", "false")
DEFAULT_MODEL = os.environ.get(
    "SBU_MODEL",
    "us.anthropic.claude-opus-5" if _BEDROCK else "claude-opus-5",
)


@dataclass
class StepOutcome:
    text: str
    payload: Optional[dict]
    elapsed_s: float
    submission_count: int
    tool_use_count: int


# MUST be passed: without explicit allowed_tools the SDK CLI blocks every tool
# ("error result: success", nothing done). The submit MCP tool is appended when
# a submit_step is attached.
DEFAULT_ALLOWED_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "TodoWrite"]
DEFAULT_MAX_TURNS = 200


def run_agent_step(*, system_prompt: str, user_prompt: str, cwd: str,
                   timeout_s: int = 3600, submit_step: Optional[str] = None,
                   model: str = DEFAULT_MODEL, max_turns: int = DEFAULT_MAX_TURNS,
                   allowed_tools: Optional[list[str]] = None) -> StepOutcome:
    """Run one agent step. Returns text + captured submit_result payload.
    Raises RuntimeError on a hard CLI error (caller decides retry/blocked)."""
    from claude_agent_sdk import query, ClaudeAgentOptions
    from claude_agent_sdk.types import (
        AssistantMessage, TextBlock, ToolUseBlock, ResultMessage,
    )

    from .submit_result import make_submit_server

    mcp_servers: dict = {}
    capture = None
    tools = list(allowed_tools) if allowed_tools is not None else list(DEFAULT_ALLOWED_TOOLS)
    if submit_step is not None:
        server, capture = make_submit_server(submit_step)
        mcp_servers["submit"] = server
        tools.append("mcp__submit__submit_result")

    # Unique per-call marker so a timeout kill can be scoped to THIS agent's
    # subprocess tree (see _kill_descendants; children inherit the env).
    import uuid
    mark = uuid.uuid4().hex
    # A failed launch reports "error result: success" and nothing else, which is
    # unactionable and lands in meta.json as a spec verdict. Keep the CLI's own
    # last words so the failure can name its cause; bounded so a chatty run
    # cannot grow without limit.
    cli_err: collections.deque[str] = collections.deque(maxlen=40)
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        permission_mode="bypassPermissions",
        allowed_tools=tools,
        mcp_servers=mcp_servers,
        cwd=cwd,
        max_turns=max_turns,
        # env= REPLACES the inherited environment, so pass the full inherited
        # env (Bedrock/Anthropic routing vars) plus the kill-scope marker.
        env={**os.environ, "SBU_AGENT_MARK": mark},
        stderr=lambda line: cli_err.append(line.rstrip()),
    )

    # opt-in trajectory trace: SBU_AGENT_TRACE=<dir> logs a timestamped line per
    # tool-use / text block so a slow/stalled agent can be diagnosed after the
    # fact. Zero overhead when unset.
    trace_dir = os.environ.get("SBU_AGENT_TRACE")
    trace_fh = None
    if trace_dir:
        os.makedirs(trace_dir, exist_ok=True)
        trace_fh = open(os.path.join(
            trace_dir, f"{(submit_step or 'agent')}-{os.getpid()}.trace"), "a")

    async def _run() -> tuple[str, int, str]:
        parts: list[str] = []
        tool_uses = 0
        why = ""
        t0 = time.monotonic()
        # The SDK RAISES on a failed launch from inside this iteration rather
        # than yielding the failed ResultMessage, and the string it raises is
        # "returned an error result: success" -- the result's own `subtype`
        # standing in for a diagnostic the CLI never sent. Re-raise it with the
        # CLI's stderr attached, because that string is what ends up in
        # meta.json, where a reader reads it as a verdict about the spec.
        stream = query(prompt=user_prompt, options=options)
        while True:
            try:
                message = await stream.__anext__()
            except StopAsyncIteration:
                break
            except Exception as exc:
                # The CLI sends the failed result frame BEFORE exiting non-zero,
                # so by the time the SDK turns that exit into an exception we have
                # already seen the frame and read its fields into `why`. Report
                # those: they are the only account of the failure that exists.
                tail = " / ".join(ln for ln in cli_err if ln.strip())[-600:]
                raise LaunchFailure(
                    f"{type(exc).__name__}: {exc}"
                    + (f"; result: {why}" if why else "")
                    + (f"; cli stderr: {tail}" if tail else
                       "; the CLI wrote nothing to stderr"),
                    tool_uses=tool_uses,
                    chars=sum(len(p) for p in parts)) from exc
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        parts.append(block.text)
                        if trace_fh:
                            trace_fh.write(f"{time.monotonic()-t0:7.1f}s TEXT "
                                           f"{block.text[:120]!r}\n")
                            trace_fh.flush()
                    elif isinstance(block, ToolUseBlock):
                        tool_uses += 1
                        if trace_fh:
                            inp = str(getattr(block, "input", ""))[:160]
                            trace_fh.write(f"{time.monotonic()-t0:7.1f}s TOOL "
                                           f"{getattr(block,'name','?')} {inp}\n")
                            trace_fh.flush()
            elif isinstance(message, ResultMessage):
                if bool(getattr(message, "is_error", False)):
                    why = _describe_error(message, cli_err)
        return "".join(parts), tool_uses, why

    start = time.monotonic()
    # A launch that never ran is retried HERE, not by the caller. The caller's
    # retry budget exists for an agent that ran and misbehaved; spending it on a
    # launch that never authenticated, or that died with no diagnostic before
    # emitting anything, records an audit verdict about a bundle nobody looked
    # at. Each attempt first waits for the host-wide outage to go quiet, so the
    # attempts cost one launch per quiet period rather than a busy loop.
    #
    # The trace handle is closed by the OUTER finally, not per attempt: a retry
    # runs _run() again, and _run() writes to trace_fh. Closing it per attempt
    # makes the next attempt raise ValueError on a closed file, so an auth outage
    # would surface as a bogus hard error whenever SBU_AGENT_TRACE is set.
    last_auth = ""
    last_barren = ""
    auth_tries = barren_tries = 0
    # Two independent retry budgets, and a loop bound that is the sum of them so
    # a classification bug cannot turn this into a launch loop.
    misconfigured = provider_preflight()
    if misconfigured:
        raise AgentAuthError(misconfigured)
    try:
        for _ in range(AUTH_RETRIES + LAUNCH_RETRIES + 2):
            _wait_out_auth_outage(AUTH_MAX_WAIT_S)
            # The slot is held for the whole step, not just the spawn: the limit
            # that breaks a launch is on CLIs in flight, so releasing at spawn
            # would let N slots admit unboundedly many live agents. Queueing is
            # capped well below the step's own timeout, after which it proceeds
            # unslotted rather than not at all.
            slot_ctx = _agent_slot(_slot_wait_budget(timeout_s))
            queued_at = time.monotonic()
            run_budget = float(timeout_s)
            try:
                slot_ctx.__enter__()
                # Queue time is spent from the same wall clock the caller
                # budgeted, so it comes OUT of this attempt's run budget instead
                # of being granted on top of it. Otherwise one attempt can
                # occupy 2x its stated cap, and the caller -- which sized its own
                # deadline from that cap -- kills the CLI mid-run and records the
                # non-measurement as a verdict on the spec.
                run_budget = _run_budget(timeout_s, queued_at)
                text, tool_use_count, err_why = asyncio.run(
                    asyncio.wait_for(_run(), timeout=run_budget))
            except asyncio.TimeoutError:
                # asyncio cancels the coroutine but does NOT kill the spawned
                # `claude` CLI subprocess tree — it would run on unbounded,
                # hanging the caller (and any slot it holds). Kill our
                # descendants, then surface as an error (run_audit_stage maps
                # this to INCONCLUSIVE -> fail, fail-closed).
                if trace_fh:
                    trace_fh.write(f"{run_budget:7.1f}s TIMEOUT-KILLED\n")
                _kill_descendants(os.getpid(), mark=mark)
                # Report the queue time separately. "Timed out after 5400s" and
                # "queued 300s of its 5400s, then timed out" call for opposite
                # remedies -- a larger cap versus a quieter host.
                queued = max(0.0, timeout_s - run_budget)
                waited = (f" (queued {queued:.0f}s of its {timeout_s}s)"
                          if queued > 1 else "")
                raise RuntimeError(
                    f"agent CLI timed out after {run_budget:.0f}s "
                    f"(killed){waited}")
            except Exception as exc:
                # The SDK turns the CLI's non-zero exit into an exception whose
                # text already carries the result fields (see _run). An auth
                # failure arrives this way, so it has to be classified here too.
                if is_auth_failure(str(exc)):
                    last_auth = str(exc)[:600]
                    _note_auth_failure(last_auth)
                    auth_tries += 1
                    if auth_tries > AUTH_RETRIES:
                        raise AgentAuthError(
                            f"the agent CLI could not authenticate in "
                            f"{auth_tries} attempts over "
                            f"{time.monotonic() - start:.0f}s, so it never "
                            f"ran: {last_auth}") from exc
                    continue
                # A launch that died having produced nothing measured nothing,
                # so re-launching it cannot double any side effect and cannot
                # change any verdict -- it can only replace a non-measurement
                # with a measurement. Backoff is short and doubling, because
                # these cluster in time; the auth flag is deliberately NOT
                # touched, since a diagnostic-free failure is no evidence about
                # credentials and stalling the whole host on it would cost more
                # than the launch.
                if isinstance(exc, LaunchFailure) and not exc.did_work:
                    last_barren = str(exc)[:600]
                    barren_tries += 1
                    if barren_tries > LAUNCH_RETRIES:
                        raise LaunchFailure(
                            f"the agent CLI died before producing anything in "
                            f"{barren_tries} attempts over "
                            f"{time.monotonic() - start:.0f}s: {last_barren}"
                        ) from exc
                    time.sleep(min(60.0,
                                   LAUNCH_BACKOFF_S * 2 ** (barren_tries - 1)))
                    continue
                raise
            finally:
                with contextlib.suppress(Exception):
                    slot_ctx.__exit__(None, None, None)
            # The CLI reports "not logged in" as a synthetic assistant TURN as
            # well as in the result, so check both: the turn is the only signal
            # when the process happens to exit zero.
            #
            # The turn is checked NARROWLY. A step that ran is allowed to write
            # the words "not logged in" -- an audit role reading this very file,
            # or a log, would -- and treating that as an outage would stall every
            # launch on the host for AUTH_QUIET_S on the strength of a quotation.
            # The real thing is the entire output of the launch: no tool ever ran
            # and the synthetic notice is all there is.
            looks_synthetic = (tool_use_count == 0 and len(text) < 400
                               and is_auth_failure(text))
            if is_auth_failure(err_why) or looks_synthetic:
                last_auth = (err_why or text)[:600]
                _note_auth_failure(last_auth)
                auth_tries += 1
                if auth_tries > AUTH_RETRIES:
                    raise AgentAuthError(
                        f"the agent CLI could not authenticate in "
                        f"{auth_tries} attempts over "
                        f"{time.monotonic() - start:.0f}s, so it never ran: "
                        f"{last_auth}")
                continue
            elapsed = time.monotonic() - start
            if err_why:
                raise RuntimeError(
                    f"agent CLI reported is_error after {elapsed:.0f}s: {err_why}")
            return StepOutcome(
                text=text,
                payload=(capture.payload if capture else None),
                elapsed_s=elapsed,
                submission_count=(capture.submission_count if capture else 0),
                tool_use_count=tool_use_count,
            )
        raise RuntimeError(
            f"the agent CLI never produced a result in "
            f"{AUTH_RETRIES + LAUNCH_RETRIES + 2} attempts over "
            f"{time.monotonic() - start:.0f}s: {last_barren or last_auth}")
    finally:
        if trace_fh and not trace_fh.closed:
            trace_fh.close()
