# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Backend-neutral verification result + helpers. Checker invocation lives on
`Backend.check` (shells out to scripts/*_verify.sh); verification is static —
no repo code executes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .paths import EXPERIMENTS_ROOT, PROJECT_ROOT

# The JVM's own fatal-error banner. Viper runs on the JVM, driven from Python, so
# a crash down there can surface as a wrapper exit that looks like a verdict.
_JVM_FATAL = "A fatal error has been detected by the Java Runtime Environment"


@dataclass
class VerifyResult:
    success: bool
    wall_time_s: float
    stdout: str
    stderr: str
    timed_out: bool = False
    returncode: int | None = None  # verifier script exit: 0 ok, 124 timeout;
                                   # lean flavor adds 3 = sorry/admit only
    no_verdict_detail: str = ""     # set by a backend that can recognise a
                                    # non-verdict its exit code spells as one;
                                    # see `crashed`

    @property
    def summary(self) -> str:
        if self.timed_out:
            return "timeout"
        if self.no_verdict_detail:
            # Named rather than reported as an exit code, because for this class
            # of non-verdict the exit code is 1 -- the rejection code -- so
            # "(exit 1)" would read as the very verdict this is denying.
            return f"verifier did not reach a verdict ({self.no_verdict_detail})"
        if self.crashed:
            return f"verifier did not reach a verdict (exit {self.returncode})"
        return "verified" if self.success else "verification failed"

    @property
    def sorry_only(self) -> bool:
        """Lean only: file elaborated cleanly, sole issue is sorry/admit
        (exit 3) — valid intermediate state before the proof phase. Always
        False for nagini (its script never exits 3)."""
        return self.returncode == 3

    @property
    def crashed(self) -> bool:
        """The verifier reached no verdict: it died or its environment did.

        `success=False` alone cannot be read as "this file does not verify". The
        scripts define exactly three verdict exits -- 0 accepted, 1 rejected,
        and (lean flavor) 3 accepted-modulo-sorry. Everything else is the
        absence of a judgment: 2 is the wrappers' env-problem code, and a signal
        death (128+n) is the checker itself failing, which happens for real --
        the Python/JVM bridge Viper is driven through segfaults occasionally
        under load, taking the verification with it.

        The distinction is load-bearing in exactly one direction. An attack that
        crashes the verifier, scored as "does not verify", is scored as one the
        spec REJECTED, and a spec weakness the attack would have exposed
        disappears into a green record. So a crash must be inconclusive
        everywhere a rejection would otherwise be concluded.

        `no_verdict_detail` extends that to the non-verdicts the exit code
        CANNOT distinguish, which the backend has to recognise from its own
        checker's output. Nagini is the case that forced it: its front end exits
        1 -- the rejection code -- for a type error, an unsupported construct or
        an uncaught internal error, having never built a Viper program at all.
        See `backends/nagini.py`.
        """
        if self.timed_out:
            return False
        if self.no_verdict_detail:
            return True
        if self.returncode is not None and self.returncode not in (0, 1, 3):
            return True
        # A crash the exit code hides: the runtime under the verifier can die
        # and still let its caller exit 1, which is the rejection code. The
        # banner is only ever emitted by the runtime itself, never by a spec.
        return _JVM_FATAL in self.stderr or _JVM_FATAL in self.stdout

    @property
    def front_end_refusal(self) -> bool:
        """The checker turned the FILE DOWN before building a proof obligation.

        A subset of `crashed`, and the one subset that is not an accident. The
        others -- a timeout, an env-problem exit, a JVM death -- leave open
        whether the file would have verified, so a caller must treat them as
        inconclusive. This one does not: the front end could not translate the
        program at all, which means no proof obligation about it was ever
        generated and none ever could be. Nothing is hidden by it.

        The distinction is what an ATTACK is scored against. An attack is a
        candidate counterexample only if it VERIFIES against the unchanged spec,
        so an untranslatable attack cannot be one -- the language cannot express
        the implementation the reviewer had in mind. But it is not a rejection
        either: the spec never judged it. It belongs with the inadmissible
        attacks `check_attack` already separates out (`sorry`, a dropped
        obligation, an `@ContractOnly` stub) -- evidence in neither direction,
        and so not countable toward the floor of real probes a role requires.
        Scored as a rejection instead, it is a rejection the specification never
        performed.

        Narrower than `no_verdict_detail` alone: exit 1 is the REJECTION code,
        and this is the case where that code is a lie. An exit outside the
        verdict set (2 for an env problem) is a non-verdict of the accidental
        kind whichever way the backend describes it, so it stays inconclusive.
        """
        return bool(self.no_verdict_detail) and self.returncode == 1


def _as_text(v) -> str:
    if v is None:
        return ""
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else v


def run_verify_script(script: Path, module_path: str | Path, timeout: int) -> VerifyResult:
    """Run a scripts/*_verify.sh entry point with the shared exit-code protocol."""
    cmd = ["bash", str(script), str(module_path), str(timeout)]
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout + 60, cwd=str(PROJECT_ROOT))
    except subprocess.TimeoutExpired as e:
        return VerifyResult(False, time.monotonic() - start,
                            _as_text(e.stdout), _as_text(e.stderr) + "\n[timeout]",
                            timed_out=True, returncode=124)
    elapsed = time.monotonic() - start
    return VerifyResult(proc.returncode == 0, elapsed, proc.stdout or "",
                        proc.stderr or "", timed_out=proc.returncode == 124,
                        returncode=proc.returncode)


def verify_source_via(check, src: str, name: str, timeout: int) -> VerifyResult:
    """Check in-memory source through a private scratch dir, removed afterwards.

    The directory does NOT have to sit inside the checkout, which this docstring
    used to claim on the grounds that relative dependencies would otherwise not
    resolve. Each verifier script finds its own workspace from the script's
    location rather than from the file it is handed (`lean_verify.sh` derives
    `lean_shared` from `dirname $BASH_SOURCE/..`), so `SBU_EXPERIMENTS_DIR` or
    `SBU_SCRATCH` may point anywhere writable: measured on all three backends
    with both outside the checkout.
    """
    scratch = os.environ.get("SBU_SCRATCH", str(EXPERIMENTS_ROOT / "scratch"))
    Path(scratch).mkdir(parents=True, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="sbu_verify_", dir=scratch)
    try:
        p = Path(tmpdir) / name
        p.write_text(src)
        return check(p, timeout)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
