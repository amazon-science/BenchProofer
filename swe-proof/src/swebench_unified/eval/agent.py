# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The evaluation agent scaffold: a conventional ReAct loop (SWE-agent core),
provider-agnostic, iterating until submit or budget.

Tools: bash (in-container, cwd = the benchmark's checkout — /testbed on
SWE-bench_Verified, /app on Pro; see Benchmark.container_workdir);
<backend>_verify (HOST verifier on the agent's OWN artifact only — no repo code,
no hidden tests, provably non-leaking); submit (captures git diff __base + model
file in model modes).

Every tool description and reminder that names the checkout directory is built
per run from the container's resolved workdir, so the agent is never told about a
path the benchmark does not have.

Every message, tool call, and bash i/o goes to a trajectory list the caller
persists (trajectory.jsonl) for cheating review.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from . import prompts
from .adapter import EvalAdapter
from .container import EvalContainer
from .dataset import EvalTask
from .providers import CredentialsExpired, ProviderError, ToolCall, ToolSpec

# bash + submit are backend-independent; the verifier tool comes from the adapter.
# Both are built PER RUN rather than at import, because the checkout directory is
# a per-benchmark fact (container_workdir) and a module constant is bound before
# the registry can be read.


def tool_bash(workdir: str) -> ToolSpec:
    return ToolSpec(
        "bash", f"Run a bash command inside the repository container (cwd {workdir}, "
        "with the project's Python env active). Use it to read/edit files, run the "
        "existing public tests, grep, etc. Returns stdout+stderr (truncated).",
        {"command": {"type": "string", "description": "the bash command to run"}},
        ["command"])


def tool_submit(workdir: str) -> ToolSpec:
    return ToolSpec(
        "submit", "Finalize your solution. The patch is captured automatically as the "
        f"git diff of your edits to {workdir} against the base commit. In modes that "
        "require a verified model, also pass model_path (the file you verified).",
        {"model_path": {"type": "string",
                        "description": "path to your final model file in the container "
                                       "(required in verify modes; omit otherwise)"},
         "note": {"type": "string", "description": "optional short note on your solution"}},
        [])

VERIFY_TIMEOUT = 300
DEFAULT_MAX_STEPS = 250      # budget for model AND patch (full-run peak ~121 steps)
DEFAULT_BASH_TIMEOUT = 120
MAX_TOOL_OUTPUT = 12_000     # chars returned to the model per tool call


@dataclass
class Submission:
    patch: str = ""
    model_src: str | None = None
    model_path: str | None = None
    note: str = ""


@dataclass
class AgentResult:
    instance_id: str
    mode: int
    submitted: bool
    submission: Submission
    trajectory: list = field(default_factory=list)
    steps: int = 0
    stop: str = ""              # submitted | max_steps | error | creds_expired
    usage: dict = field(default_factory=dict)
    error: str = ""


def _truncate(s: str, n: int = MAX_TOOL_OUTPUT) -> str:
    if s is None:
        return ""
    if len(s) <= n:
        return s
    head = s[: n // 2]
    tail = s[-n // 2:]
    return f"{head}\n…[{len(s) - n} chars truncated]…\n{tail}"


class EvalAgent:
    def __init__(self, adapter: EvalAdapter, task: EvalTask, container: EvalContainer,
                 provider, max_steps: int = DEFAULT_MAX_STEPS,
                 bash_timeout: int = DEFAULT_BASH_TIMEOUT):
        self.adapter = adapter
        self.task = task
        self.c = container
        self.provider = provider
        self.max_steps = max_steps
        self.bash_timeout = bash_timeout
        self.traj: list = []
        self.sub = Submission()
        self._submitted = False
        self._verified_ok = False            # any <backend>_verify succeeded?
        self._last_verified_path: str | None = None
        self._submit_gate_used = False       # one-time soft gate (modes 6,2)
        self._budget_reminder_sent = False
        self._usage = {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
        # the container already resolved the benchmark's checkout dir; every
        # agent-visible mention of it is rendered from that one value
        self.workdir = container.workdir
        self._verify_tool = adapter.verify_tool_spec(self.workdir)
        self._bash_tool = tool_bash(self.workdir)
        self._submit_tool = tool_submit(self.workdir)

    def _tools(self) -> list[ToolSpec]:
        tools = [self._bash_tool]
        # verifier per task.offers_verifier: modes 7,6,2,3,8 + formal 100
        # ("verified mode 4"); NOT mode 4, mode 0 (canonical SWE-bench:
        # bash + submit only), or ears 100 (a pure mode-4 twin)
        if self.task.offers_verifier:
            tools.append(self._verify_tool)
        tools.append(self._submit_tool)
        return tools

    def _log(self, kind: str, **data):
        self.traj.append({"t": round(time.monotonic(), 3), "kind": kind, **data})

    def _do_bash(self, args: dict) -> tuple[str, bool]:
        cmd = args.get("command", "")
        if not cmd.strip():
            return "(empty command)", False
        r = self.c.exec(cmd, timeout=self.bash_timeout)
        out = ""
        if r.stdout:
            out += r.stdout
        if r.stderr:
            out += ("\n[stderr]\n" + r.stderr) if out else r.stderr
        if r.timed_out:
            out += f"\n[command timed out after {self.bash_timeout}s]"
        out += f"\n[exit {r.returncode}]"
        self._log("bash", command=cmd, exit=r.returncode, output=out[:40000],
                  timed_out=r.timed_out)
        return _truncate(out), False

    def _do_verify(self, args: dict) -> tuple[str, bool]:
        tool = self.adapter.tool_name
        path = args.get("path", "")
        # nagini: optional float_encoding arg, defaulting to the bundle's value
        fe = None
        if self.adapter.supports_float_encoding:
            fe = args.get("float_encoding") or self.task.float_encoding
        src = self.c.read_file(path)
        if src is None:
            msg = f"({tool}: cannot read {path} in the container)"
            self._log(tool, path=path, ok=False, detail="unreadable")
            return msg, False
        # mechanical, non-leaking pre-checks (don't reveal the answer)
        mech = self.adapter.mechanical_feedback(src)
        # HOST verifier on the agent's file only (no repo/hidden tests)
        res = self.adapter.check_source(src, timeout=VERIFY_TIMEOUT, float_encoding=fe)
        verdict = res.summary
        if res.success:
            self._verified_ok = True
            self._last_verified_path = path
        body = res.stdout or ""
        out = f"{tool}: {verdict}\n"
        if mech:
            out += "Mechanical issues to fix (these block a clean model):\n" + mech + "\n"
        out += _truncate(body, 6000)
        log_extra = {"float_encoding": fe} if self.adapter.supports_float_encoding else {}
        self._log(tool, path=path, ok=res.success, verdict=verdict,
                  wall_s=round(res.wall_time_s, 1), output=body[:20000], **log_extra)
        return out, False

    def _do_submit(self, args: dict) -> tuple[str, bool]:
        mp = args.get("model_path")
        if self.task.require_model_to_submit and not mp:
            # modes 7/3/8 are scored on the model; block submit w/o it
            return ("submit: this mode REQUIRES a verified model — pass model_path "
                    "to the model file you verified."), False
        # Soft gate (modes 6,2): scoring is resolve-only, so never hard-block a
        # real patch — bounce the FIRST unverified submit ONCE with guidance;
        # a subsequent submit always goes through (resolve-only fairness).
        # ears: audited twins must be agent-side IDENTICAL, so the gate moves
        # with the pairs — mode 6 (twin of 1: doc given, nothing to lint into
        # existence) gets NO gate; mode 3 (twin of 3: doc authored) gets the
        # same one-time nudge mode 2 does.
        soft_gate_modes = (3, 4) if self.task.backend == "ears" else (2, 3)
        if (self.task.mode in soft_gate_modes and not self._verified_ok
                and not self._submit_gate_used):
            self._submit_gate_used = True
            self._log("submit_gate", reason="no_verified_model_yet")
            return ("submit: you have not yet gotten a model to VERIFY for "
                    "this task. Verification is the expected method here: write a "
                    f"model that captures the intended fix and run `{self.adapter.tool_name}` "
                    "until it succeeds, then translate it into your patch and submit "
                    "(pass model_path). If you have genuinely tried and cannot get a "
                    "model to verify, call `submit` again to proceed with your patch "
                    "as-is."), False
        self.sub.patch = self.c.extract_patch()
        self.sub.note = args.get("note", "") or ""
        if not mp and self._last_verified_path:
            mp = self._last_verified_path
        if mp:  # capture the model whenever the agent provides one
            src = self.c.read_file(mp)
            if src is not None:
                self.sub.model_path = mp
                self.sub.model_src = src
        self._submitted = True
        self._log("submit", patch_len=len(self.sub.patch),
                  has_model=self.sub.model_src is not None,
                  verified_ok=self._verified_ok, note=self.sub.note)
        return "SUBMITTED", True

    def _dispatch(self, call: ToolCall) -> tuple[str, bool]:
        try:
            if call.name == "bash":
                return self._do_bash(call.input)
            if call.name == self.adapter.tool_name:
                if not self.task.offers_verifier:
                    return f"({self.adapter.tool_name} is not available in this mode)", False
                return self._do_verify(call.input)
            if call.name == "submit":
                return self._do_submit(call.input)
            return f"(unknown tool: {call.name})", False
        except Exception as e:  # noqa: BLE001 — a tool error must not kill the loop
            self._log("tool_error", tool=call.name, error=f"{type(e).__name__}: {e}")
            return f"(tool error in {call.name}: {type(e).__name__}: {e})", False

    def run(self) -> AgentResult:
        system = prompts.system_prompt(self.adapter, self.task)
        user = prompts.initial_user(self.adapter, self.task)
        messages = [{"role": "user", "content": [{"text": user}]}]
        self._log("system", text=system)
        self._log("user", text=user)
        tools = self._tools()
        stop = "max_steps"
        err = ""
        steps = 0
        try:
            while steps < self.max_steps:
                steps += 1
                turn = self.provider.chat(system, messages, tools)
                self._accumulate_usage(turn.usage)
                self._log("assistant", text=turn.text,
                          tool_calls=[{"name": c.name, "input": c.input} for c in turn.tool_calls],
                          stop_reason=turn.stop_reason, usage=turn.usage, step=steps)
                messages.append(turn.raw)

                if not turn.tool_calls:
                    # no tool call: nudge toward submit; end if it persists
                    if turn.stop_reason in ("end_turn", "stop", "completed", ""):
                        messages.append({"role": "user", "content": [{"text":
                            "You have not submitted yet. Continue working with the "
                            "tools, and call `submit` when your solution is ready."}]})
                        self._log("nudge", reason="no_tool_call")
                        if self._consecutive_nudges() >= 3:
                            stop = "no_progress"
                            break
                        continue

                results = []
                ended = False
                for call in turn.tool_calls:
                    out, is_submit = self._dispatch(call)
                    results.append({"tool_result": {"id": call.id, "content": out,
                                                     "is_error": False}})
                    if is_submit:
                        ended = True
                messages.append({"role": "user", "content": results})
                if ended:
                    stop = "submitted"
                    break
                self._maybe_budget_reminder(messages, steps)
            else:
                stop = "max_steps"
        except CredentialsExpired as e:
            stop, err = "creds_expired", str(e)
            self._log("creds_expired", error=str(e))
        except ProviderError as e:
            stop, err = "error", f"provider: {e}"
            self._log("provider_error", error=str(e))
        except Exception as e:  # noqa: BLE001
            stop, err = "error", f"{type(e).__name__}: {e}"
            self._log("agent_error", error=str(e))

        # auto-capture on max_steps/no_progress so existing edits are graded
        # (SWE-agent style); creds_expired is left uncaptured for clean resume
        if not self._submitted and stop in ("max_steps", "no_progress"):
            try:
                self.sub.patch = self.c.extract_patch()
                if self.task.requires_model:
                    self.sub.model_src = self._guess_model_file()
                self._log("auto_capture", stop=stop, patch_len=len(self.sub.patch),
                          has_model=self.sub.model_src is not None)
            except Exception as e:  # noqa: BLE001
                self._log("auto_capture_error", error=str(e))

        return AgentResult(
            instance_id=self.task.instance_id, mode=self.task.mode,
            submitted=self._submitted, submission=self.sub, trajectory=self.traj,
            steps=steps, stop=stop, usage=self._usage, error=err)

    def _guess_model_file(self) -> str | None:
        """On a non-submit exit, find the likeliest model file (last verified
        path, else the adapter's common names) so the work is still graded."""
        for ev in reversed(self.traj):
            if ev["kind"] == self.adapter.tool_name and ev.get("path"):
                src = self.c.read_file(ev["path"])
                if src:
                    return src
        for path in self.adapter.guess_model_paths(self.workdir):
            src = self.c.read_file(path)
            if src and self.adapter.spec_marker_token in src:
                return src
        return None

    def _maybe_budget_reminder(self, messages: list, steps: int) -> None:
        """One-time nudge (verify modes) at ~60% of the step budget if the agent
        has not yet worked on the repo patch — the thing the grader scores —
        so it doesn't burn the budget on the model and submit an EMPTY patch.
        General / non-instance-specific; resolve-only fairness unaffected."""
        if self._budget_reminder_sent or not self.task.offers_verifier:
            return
        if steps < int(0.6 * self.max_steps):
            return
        # has the agent run a repo test or clearly edited the repo yet?
        worked_patch = any(
            ev["kind"] == "bash" and (
                "runtests" in ev.get("command", "") or "pytest" in ev.get("command", "")
                or (f"{self.workdir}/" in ev.get("command", "")
                    and "model" not in ev.get("command", "").lower()
                    and any(x in ev.get("command", "") for x in (">", "sed -i", ".replace(")))
            )
            for ev in self.traj)
        if worked_patch:
            return
        self._budget_reminder_sent = True
        self._log("budget_reminder", steps=steps, max_steps=self.max_steps,
                  verified=self._verified_ok)
        if self._verified_ok:
            msg = (f"[budget: step {steps}/{self.max_steps}] You have a VERIFIED model — "
                   "good. Now spend your remaining budget on the PATCH, which is what is "
                   f"graded: translate the verified model into your {self.workdir} edit (case for "
                   "case), run the repository's existing tests to sanity-check it, then "
                   "`submit`. Don't keep polishing the model at the expense of the patch.")
        else:
            msg = (f"[budget: step {steps}/{self.max_steps}] You have spent most of your "
                   "budget WITHOUT yet editing the repository or getting a model to verify. "
                   "The grader scores your PATCH, so do not run out of budget with an empty "
                   "patch. If you cannot get the model to verify soon, proceed: apply your "
                   f"best fix to {self.workdir} using your current understanding of the spec, run "
                   "the repo's existing tests on it, and `submit`.")
        messages.append({"role": "user", "content": [{"text": msg}]})

    def _consecutive_nudges(self) -> int:
        n = 0
        for ev in reversed(self.traj):
            if ev["kind"] == "nudge":
                n += 1
            elif ev["kind"] in ("bash", self.adapter.tool_name, "submit"):
                break
        return n

    def _accumulate_usage(self, u: dict):
        for k in ("inputTokens", "outputTokens", "totalTokens"):
            if k in u and isinstance(u[k], int):
                self._usage[k] = self._usage.get(k, 0) + u[k]
