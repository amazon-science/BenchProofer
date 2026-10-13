# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A launch that never authenticated must not be recorded as a verdict.

The CLI reports a credential outage the same way it reports everything else that
goes wrong: is_error=true, subtype="success", no diagnostic. The only trace of
the cause is a synthetic assistant turn reading "Not logged in - Please run
/login". Read as an ordinary failure, that becomes a FAILED audit role, which in
this corpus means "this spec admits a wrong implementation" -- a false claim
about a bundle nobody looked at.

So the outage is (a) recognised, (b) waited out ACROSS PROCESSES, since every
driver on the host hits the same outage and each one alone would spend its whole
retry budget re-confirming it, and (c) raised as its own type, so a caller cannot
mistake it for evidence.
"""
from __future__ import annotations

import importlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest


def _reload(monkeypatch, tmp_path: Path, **env: str):
    """Re-import the module so its env-derived module constants take effect.

    The eviction goes through `monkeypatch.delitem`, which puts the ORIGINAL
    module object back in `sys.modules` at teardown. A plain `del` leaves the
    reloaded copy installed for the rest of the session, and then a later test
    that patches `"swebench_unified.agent.<name>"` by string patches this copy
    while calling a function it imported from the first one -- so the patch
    lands on nothing and the test passes vacuously. That is not hypothetical:
    it silently disabled the assertion that a misconfigured launch stamps no
    host-wide outage flag, which is the check standing between one bad process
    and a host where no agent runs at all.

    Restoring `sys.modules` is only half of it, though, because
    `import_module` ALSO rebinds `agent` as an attribute of the
    `swebench_unified` package, and `monkeypatch.delitem` knows nothing about
    that. Leave it behind and the two ways of naming this module disagree for
    the rest of the session -- measured, not reasoned:

        import swebench_unified.agent as m   -> the reloaded copy
        from ..agent import run_agent_step   -> the restored original

    which is worse than either copy winning outright, because a test patches the
    first and the code under test calls the second. It cost a real failure: the
    adversary test that pins "a silent auditor is never recorded as clean"
    patched the copy, `eval/adversary.py` called the original, and the live
    agent ran for six minutes and came back `clean` -- the exact verdict that
    test exists to forbid.
    """
    import swebench_unified

    monkeypatch.setenv("SBU_AUTH_FLAG", str(tmp_path / "auth_down"))
    monkeypatch.setenv("SBU_AGENT_SLOT_DIR", str(tmp_path / "slots"))
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    # Registered BEFORE the re-import, so the value monkeypatch remembers is the
    # original module and not the copy. Setting it to what it already is looks
    # redundant; the point is the undo it records.
    monkeypatch.setattr(swebench_unified, "agent",
                        getattr(swebench_unified, "agent", None), raising=False)
    for mod in [m for m in list(sys.modules) if m.endswith("swebench_unified.agent")]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    return importlib.import_module("swebench_unified.agent")


# --------------------------------------------------------------------------
# recognition


def test_the_strings_a_credential_outage_actually_produces(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path)
    # what the CLI shows, what its transcript calls the field, and what a Bedrock
    # deployment surfaces when its temporary credentials lapse
    for text in [
        "Not logged in · Please run /login",
        '{"error": "authentication_failed", "isApiErrorMessage": true}',
        "ExpiredTokenException: The security token included in the request is expired",
        "UnrecognizedClientException: The security token included is invalid",
        "botocore.exceptions.NoCredentialsError: Unable to locate credentials",
        # the shape the SDK actually raises: the useless prefix, then the fields
        "Exception: Claude Code returned an error result: success; result: "
        "'Not logged in · Please run /login'",
    ]:
        assert ag.is_auth_failure(text), text


def test_an_ordinary_failure_is_not_mistaken_for_an_outage(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path)
    for text in [
        "",
        "agent CLI timed out after 3600s (killed)",
        "subtype=success; stop_reason=stop_sequence; num_turns=41",
        "the spec admits a wrong implementation: atk_3.py verifies but does not resolve",
        "ThrottlingException: Too many requests, please wait before trying again",
    ]:
        assert not ag.is_auth_failure(text), text


# --------------------------------------------------------------------------
# the shared backoff


def test_no_outage_on_record_means_no_wait(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path)
    t0 = time.monotonic()
    assert ag._wait_out_auth_outage(60) == 0.0
    assert time.monotonic() - t0 < 1.0


def test_a_stale_flag_does_not_hold_anyone(tmp_path, monkeypatch):
    """The flag is never cleaned up, so it must expire by AGE, not by existence.

    Otherwise the first outage of a run would stall every launch after it for
    ever, which is strictly worse than the failure it is guarding against.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="300")
    ag._note_auth_failure()
    import os
    old = time.time() - 4000
    os.utime(ag._AUTH_FLAG, (old, old))
    assert ag._wait_out_auth_outage(60) == 0.0


def test_a_fresh_outage_holds_the_launch_until_quiet(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="2")
    ag._note_auth_failure()
    t0 = time.monotonic()
    waited = ag._wait_out_auth_outage(30)
    took = time.monotonic() - t0
    assert waited > 0 and took >= 1.5, (waited, took)
    # and once quiet, the very next caller goes straight through: the callers
    # that arrive when the flag goes stale are how a process learns credentials
    # are back, and that costs one launch per quiet period, not a busy loop.
    assert ag._wait_out_auth_outage(30) == 0.0


def test_the_wait_is_bounded_so_a_long_outage_is_reported_not_hidden(
        tmp_path, monkeypatch):
    """Past the budget the launch proceeds and is allowed to fail.

    An outage longer than the budget is something an operator has to hear about.
    Hanging on it silently would leave a whole lane looking alive and idle.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="3600")
    ag._note_auth_failure()
    t0 = time.monotonic()
    waited = ag._wait_out_auth_outage(2)
    took = time.monotonic() - t0
    assert waited <= 2.5 and took < 4.0, (waited, took)


def _child_waits(flag: str, quiet: str, q) -> None:
    """A second, independent driver: fresh interpreter, same host, same flag."""
    import os
    import sys as _sys
    os.environ["SBU_AUTH_FLAG"] = flag
    os.environ["SBU_AUTH_QUIET"] = quiet
    _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    import importlib
    other = importlib.import_module("swebench_unified.agent")
    q.put(other._wait_out_auth_outage(1) > 0)


def test_the_flag_is_shared_by_every_process_on_the_host(tmp_path, monkeypatch):
    """One driver's discovery has to back off the others; each alone cannot.

    A per-process backoff means N drivers each burn their own retry budget on the
    same outage, cell by cell, so a single outage can mark many cells for
    re-audit.
    """
    import multiprocessing as mp
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="600")

    ag._note_auth_failure()
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_child_waits,
                    args=(str(ag._AUTH_FLAG), "600", q))
    p.start()
    got = q.get(timeout=180)
    p.join(30)
    assert got is True                 # the other process was held, not launched


# --------------------------------------------------------------------------
# run_agent_step


@dataclass
class _Text:
    text: str


class _Assistant:
    def __init__(self, *blocks):
        self.content = list(blocks)


class _Result:
    def __init__(self, is_error: bool, result: str = "", subtype: str = "success"):
        self.is_error = is_error
        self.result = result
        self.subtype = subtype
        self.stop_reason = "stop_sequence"


def _install_sdk(monkeypatch, attempts):
    """Make claude_agent_sdk.query() replay one scripted attempt per call.

    Each element of `attempts` is a list of frames to yield (a BaseException in
    the list is raised instead, which is how the SDK reports a non-zero exit).
    """
    import claude_agent_sdk
    from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock

    calls: list[int] = []

    class Stream:
        def __init__(self, frames):
            self._frames = list(frames)

        async def __anext__(self):
            if not self._frames:
                raise StopAsyncIteration
            f = self._frames.pop(0)
            if isinstance(f, BaseException):
                raise f
            return f

    def fake_query(*, prompt, options):
        i = len(calls)
        calls.append(i)
        frames = attempts[min(i, len(attempts) - 1)]
        out = []
        for f in frames:
            if isinstance(f, BaseException):
                out.append(f)
            elif isinstance(f, _Assistant):
                out.append(AssistantMessage(
                    content=[TextBlock(text=b.text) for b in f.content],
                    model="<synthetic>"))
            else:
                out.append(ResultMessage(
                    subtype=f.subtype, duration_ms=1, duration_api_ms=1,
                    is_error=f.is_error, num_turns=0, session_id="s",
                    total_cost_usd=0.0, usage={}, result=f.result))
        return Stream(out)

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    return calls


_STEP = dict(system_prompt="s", user_prompt="u", timeout_s=30, max_turns=2)

_LOGIN = "Not logged in · Please run /login"


def test_an_outage_raises_its_own_type_not_a_generic_error(
        tmp_path, monkeypatch):
    """The caller must be ABLE to tell "never ran" from "ran and misbehaved".

    build_one turns a RuntimeError into an INCONCLUSIVE gate entry on the cell.
    An outage has to be distinguishable from that, or it lands in meta.json as a
    statement about a spec.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AUTH_RETRIES="2")
    calls = _install_sdk(monkeypatch, [[_Result(True, _LOGIN)]])
    with pytest.raises(ag.AgentAuthError) as ei:
        ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert isinstance(ei.value, RuntimeError)      # still catchable as before
    assert "could not authenticate" in str(ei.value)
    assert _LOGIN.lower()[:14] in str(ei.value).lower()   # keeps the evidence
    assert len(calls) == 3, calls                  # retried, did not give up at 1


def test_the_synthetic_turn_counts_even_when_the_process_exits_zero(
        tmp_path, monkeypatch):
    """The notice arrives as an assistant TURN, sometimes with no error result.

    Then the accumulated text is the only signal there is, and a step that
    "succeeded" with nothing but a login prompt in it would otherwise be handed
    to the caller as the agent's answer.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AUTH_RETRIES="1")
    calls = _install_sdk(
        monkeypatch, [[_Assistant(_Text(_LOGIN)), _Result(False)]])
    with pytest.raises(ag.AgentAuthError):
        ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert len(calls) == 2, calls


def test_a_step_that_ran_may_quote_the_words_without_stalling_the_fleet(
        tmp_path, monkeypatch):
    """A real run is allowed to SAY "not logged in".

    An audit role reading agent.py, or a log, would. Treating a quotation as an
    outage would hold every driver on the host for the quiet period on the
    strength of someone else's prose, so the turn is only read as synthetic when
    it is the whole of a launch that did nothing.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="600")
    long_answer = ("I checked the transcript: the failing role shows "
                   + "'Not logged in' " + "and here is the analysis. " * 40)
    calls = _install_sdk(
        monkeypatch, [[_Assistant(_Text(long_answer)), _Result(False)]])
    out = ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert out.text == long_answer
    assert len(calls) == 1, calls
    assert not ag._AUTH_FLAG.exists()      # nobody else was made to wait


def test_it_recovers_on_its_own_when_credentials_come_back(
        tmp_path, monkeypatch):
    """The point of retrying in here is that the run continues by itself."""
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AUTH_RETRIES="3")
    calls = _install_sdk(monkeypatch, [
        [_Result(True, _LOGIN)],
        [_Result(True, _LOGIN)],
        [_Assistant(_Text("done")), _Result(False)],
    ])
    out = ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert out.text == "done"
    assert len(calls) == 3, calls


def test_a_genuine_cli_error_is_still_raised_immediately(tmp_path, monkeypatch):
    """Only auth is retried here. Everything else is the caller's business.

    Retrying a real failure in this layer would multiply every hard error by
    AUTH_RETRIES and hide it behind a much longer wall time.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AUTH_RETRIES="3")
    calls = _install_sdk(
        monkeypatch, [[_Result(True, "ThrottlingException: slow down")]])
    with pytest.raises(RuntimeError) as ei:
        ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert not isinstance(ei.value, ag.AgentAuthError)
    assert "Throttling" in str(ei.value)
    assert len(calls) == 1, calls


def test_a_retry_can_still_write_its_trace(tmp_path, monkeypatch):
    """The trace handle outlives the attempts.

    Closing it per attempt made the second attempt raise ValueError on a closed
    file, so with SBU_AGENT_TRACE set an outage surfaced as a bogus hard error.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AUTH_RETRIES="2")
    monkeypatch.setenv("SBU_AGENT_TRACE", str(tmp_path / "trace"))
    calls = _install_sdk(monkeypatch, [
        [_Assistant(_Text(_LOGIN)), _Result(True, _LOGIN)],
        [_Assistant(_Text(_LOGIN)), _Result(True, _LOGIN)],
        [_Assistant(_Text("recovered")), _Result(False)],
    ])
    out = ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert out.text == "recovered"
    assert len(calls) == 3, calls
    traced = "".join(p.read_text() for p in (tmp_path / "trace").iterdir())
    assert traced.count("TEXT") == 3, traced      # every attempt got to write


# --------------------------------------------------------------------------
# the launch that dies with no diagnostic at all
#
# Distinct from an outage: is_error=true, subtype="success", errors=[], empty
# stderr. A role that ends this way used to be stamped `fail` -- "this spec
# admits a wrong implementation" about a spec nothing looked at. Re-launching is
# sound exactly when the dead launch produced nothing, so that is the condition,
# and it is what these pin.

def _barren(msg: str = "Claude Code returned an error result: success"):
    return Exception(msg)


def test_a_launch_that_died_having_done_nothing_is_relaunched(
        tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0",
                 SBU_LAUNCH_RETRIES="2", SBU_LAUNCH_BACKOFF="0")
    calls = _install_sdk(monkeypatch, [
        [_barren()],
        [_Assistant(_Text("measured")), _Result(False)],
    ])
    out = ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert out.text == "measured"
    assert len(calls) == 2, calls
    # a diagnostic-free failure says nothing about credentials, so it must not
    # hold every other driver on the host for the quiet period
    assert not ag._AUTH_FLAG.exists()


def test_a_launch_that_had_already_produced_output_is_not_relaunched(
        tmp_path, monkeypatch):
    """Re-running a step that already acted would double its side effects.

    An audit role writes attack files and submits a verdict through a tool. Half
    of that having happened is not "nothing ran", so the failure is the caller's
    to handle even though it looks identical from the outside.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0",
                 SBU_LAUNCH_RETRIES="2", SBU_LAUNCH_BACKOFF="0")
    calls = _install_sdk(monkeypatch, [[_Assistant(_Text("partial")), _barren()]])
    with pytest.raises(ag.LaunchFailure) as ei:
        ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert isinstance(ei.value, RuntimeError)      # still catchable as before
    assert getattr(ei.value, "did_work") is True
    assert len(calls) == 1, calls


def test_work_is_any_tool_use_not_just_text(tmp_path, monkeypatch):
    ag = _reload(monkeypatch, tmp_path)
    assert not ag.LaunchFailure("x").did_work
    assert ag.LaunchFailure("x", tool_uses=1).did_work
    assert ag.LaunchFailure("x", chars=1).did_work


def test_the_relaunch_budget_is_bounded_and_reports_what_it_saw(
        tmp_path, monkeypatch):
    """A cap that keeps failing is a host condition, not something to loop on."""
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0",
                 SBU_LAUNCH_RETRIES="2", SBU_LAUNCH_BACKOFF="0")
    calls = _install_sdk(monkeypatch, [[_barren()]])
    with pytest.raises(ag.LaunchFailure) as ei:
        ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert "3 attempts" in str(ei.value)
    assert "error result: success" in str(ei.value)   # keeps the evidence
    assert len(calls) == 3, calls


def test_the_two_budgets_do_not_cannibalise_each_other(tmp_path, monkeypatch):
    """An outage followed by a barren launch is two conditions, not one.

    Sharing one counter meant whichever failure came first spent the budget the
    other one needed, and the step gave up while the fix for both was one more
    launch.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AUTH_RETRIES="1",
                 SBU_LAUNCH_RETRIES="1", SBU_LAUNCH_BACKOFF="0")
    calls = _install_sdk(monkeypatch, [
        [_Result(True, _LOGIN)],
        [_barren()],
        [_Assistant(_Text("measured")), _Result(False)],
    ])
    out = ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert out.text == "measured"
    assert len(calls) == 3, calls


def test_a_result_frame_error_is_still_reported_at_once(tmp_path, monkeypatch):
    """Only a RAISED stream is a launch failure.

    A step whose result frame carries a real diagnostic ran and was measured; the
    relaunch is for the case where the SDK raises with the subtype standing in
    for a diagnostic that never came.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0",
                 SBU_LAUNCH_RETRIES="2", SBU_LAUNCH_BACKOFF="0")
    calls = _install_sdk(
        monkeypatch, [[_Result(True, "InternalServerException: boom")]])
    with pytest.raises(RuntimeError) as ei:
        ag.run_agent_step(cwd=str(tmp_path), **_STEP)
    assert not isinstance(ei.value, ag.LaunchFailure)
    assert "boom" in str(ei.value)
    assert len(calls) == 1, calls


# --------------------------------------------------------------------------
# the queue is spent from the step's own budget


def _spy_on_run_budget(monkeypatch):
    """Record the timeout the step hands `asyncio.wait_for`, then time out.

    Driving this through a real cap would mean a test that sleeps for the cap,
    and the arithmetic only bites at the caps real roles use (3600-14400s). So
    the budget is observed where it is applied instead.
    """
    import asyncio
    seen: dict[str, float] = {}

    def spy(coro, timeout):
        seen["budget"] = timeout
        coro.close()          # never awaited; closing keeps the warning quiet
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", spy)
    return seen


def test_queue_time_comes_out_of_the_step_budget_not_on_top_of_it(
        tmp_path, monkeypatch):
    """The defect: a queued launch got a FRESH full budget after waiting.

    Queueing for a slot and running the CLI are spent from the same wall clock,
    but the wait was capped at `timeout_s` and the run was then started with
    `timeout_s` again -- so one attempt could occupy twice its stated cap
    (measured: CLIs 7839s old against a 5400s role cap). The caller sized its
    own deadline from that cap, so it killed the CLI mid-run and recorded the
    non-measurement as a verdict on the spec.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AGENT_SLOTS="1",
                 SBU_AGENT_SLOT_WAIT_MIN="1", SBU_AGENT_SLOT_WAIT_MAX="2",
                 SBU_LAUNCH_RETRIES="0")
    seen = _spy_on_run_budget(monkeypatch)
    t0 = time.monotonic()
    with ag._agent_slot(0) as held:          # occupy the only slot
        assert held is True
        with pytest.raises(RuntimeError) as ei:
            ag.run_agent_step(cwd=str(tmp_path), timeout_s=3600,
                              system_prompt="s", user_prompt="u", max_turns=2)
    queued = time.monotonic() - t0
    assert 1.5 <= queued < 8, f"it must have queued its budget, not the cap: {queued:.1f}s"
    # The run got what was LEFT of the 3600s, not a fresh 3600s.
    assert 3595 <= seen["budget"] <= 3599, seen
    # And the report says so, because "timed out after 3600s" and "queued 2s of
    # its 3600s" call for opposite remedies: a larger cap versus a quieter host.
    assert "queued" in str(ei.value), str(ei.value)


def test_an_unqueued_launch_keeps_its_whole_budget(tmp_path, monkeypatch):
    """The deduction must not quietly shorten the common case.

    A launch that gets a slot at once waited for nothing, so it must run with
    the full cap and its timeout must not mention a queue -- otherwise every
    ordinary timeout report starts blaming host load for a slow verifier.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0", SBU_AGENT_SLOTS="4",
                 SBU_LAUNCH_RETRIES="0")
    seen = _spy_on_run_budget(monkeypatch)
    with pytest.raises(RuntimeError) as ei:
        ag.run_agent_step(cwd=str(tmp_path), timeout_s=3600,
                          system_prompt="s", user_prompt="u", max_turns=2)
    assert seen["budget"] > 3599.5, seen
    assert "timed out after 3600s" in str(ei.value), str(ei.value)
    assert "queued" not in str(ei.value), str(ei.value)


def test_the_remainder_floor_never_exceeds_the_cap(tmp_path, monkeypatch):
    """A floor that outgrows the cap inverts the whole fix.

    MIN_RUN_BUDGET_S exists so a queued launch is never handed a zero timeout,
    which `wait_for` treats as already expired. Applied unclamped it hands a
    short step MORE than the caller budgeted -- an 8s step that queued its whole
    8s came out with a 60s run.
    """
    ag = _reload(monkeypatch, tmp_path, SBU_AUTH_QUIET="0")
    now = time.monotonic()
    assert ag._run_budget(8, now - 8) == 8, "the cap bounds the floor"
    assert ag._run_budget(8, now) <= 8
    # above the floor the remainder is what is left, and it is never negative
    assert ag._run_budget(3600, now - 300) == pytest.approx(3300, abs=1)
    assert ag._run_budget(3600, now - 99999) == float(ag.MIN_RUN_BUDGET_S)
