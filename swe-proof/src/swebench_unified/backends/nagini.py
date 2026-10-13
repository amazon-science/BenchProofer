# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Nagini backend: Python + Nagini/Viper contracts, verified on the host in a
pinned conda env via scripts/nagini_verify.sh."""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path

from ..paths import SCRIPTS_ROOT
from ..verify import VerifyResult, _as_text
from .base import Backend, LanguageTables, ShadowSpec

VERIFY_SCRIPT = SCRIPTS_ROOT / "nagini_verify.sh"
# nagini exits 0 on some non-verifying outcomes; the marker is authoritative.
SUCCESS_MARKER = "Verification successful"
# The other half of the protocol, and the one that makes a non-verdict visible.
# Nagini prints exactly one of these two banners when Viper has judged the file
# (`verifier.Success.to_string` / `verifier.Failure.to_string`), and `main.py`
# maps the judgment to `sys.exit(0 if success else 1)`. Everything else that
# leaves nagini with exit 1 said nothing about the file: `Translation failed` for
# a TypeException, InvalidProgramException or UnsupportedException; a
# ConsistencyException on the translated AST; a re-raised JException; and the
# unhandled `TypeError` from `translate()` returning None. See `_no_verdict`.
FAILURE_MARKER = "Verification failed"


def _no_verdict(returncode: int | None, out: str) -> str:
    """Why this run reached no verdict, or "" if it reached one.

    Nagini's front end exits 1 -- the REJECTION code -- when it never reached
    Viper, so `success == False` cannot be read as "the spec turned this file
    down". That reading is unsound in one specific direction and this backend is
    the one place it is unguarded: nagini is in `pbt.WITNESS_REQUIRED`'s
    complement precisely because Viper discharges the postcondition itself, so
    its reject lane concludes a rejection from "did not verify" ALONE. A rival
    impl with a type error, or one using a construct nagini cannot translate, was
    therefore scored as an impl THE SPEC REJECTED -- hollow evidence of spec
    strength, in a lane whose whole job is to certify it.

    It misreads a verifying case as well: a front-end failure is fast where a
    real verdict is not, so a case that normally verifies can come back "rejected
    (verification failed)" in a fraction of the usual time. A repair agent reading
    that record is being sent to weaken a correct spec.

    Stated as "no banner" rather than as a list of failure banners on purpose.
    The banner list would be a guess at nagini's error taxonomy -- `raise e` on a
    JException and `modules, prog = translate(...)` unpacking None both exit 1
    with a bare Python traceback and no banner at all -- whereas "Viper announced
    a judgment" is the protocol this backend already depends on for `success`.
    """
    if returncode not in (0, 1):
        return ""          # not ours to name: `VerifyResult.crashed` has it
    if SUCCESS_MARKER in out or FAILURE_MARKER in out:
        return ""
    first = next((ln.strip() for ln in out.splitlines() if ln.strip()), "")
    return (f"nagini exited {returncode} without a Viper verdict"
            + (f": {first[:160]}" if first else ""))


def _private_cwd() -> Path:
    """A working directory this PROCESS owns, for nagini to put its cache in.

    `nagini_translation/lib/typeinfo.py` sets mypy's `cache_dir` to the RELATIVE
    path `.mypy_cache_strict`, so it lands in whatever cwd the verifier was
    started in. A shared cwd (this backend used to pass `cwd=PROJECT_ROOT`) means
    concurrent nagini verifications share one incremental cache, which mypy does
    not support. Worse, each verification writes its subject as `model.py` in a
    scratch dir that is deleted seconds later, so they all collide on module id
    `__main__`: the cache's `__main__.meta.json` names a temp file belonging to
    whichever process wrote last, and no longer exists.

    That is a cross-run interference hazard whose symptom is a FAST, wandering,
    non-reproducible front-end failure -- exactly the shape `_no_verdict` above
    was written for. The screen makes such a failure honest; this makes it stop
    happening. Per-process rather than per-run because the cache is worth keeping:
    a cold cache costs measurably more wall time than a warm one, and a fresh
    directory per verification would pay that on every nagini run, while a
    directory owned by one process is never shared with a concurrent one.

    Under the temp root, not the project tree: it is a cache, the OS reaps it,
    and a directory named for a pid must never be created inside a bundle. Dead
    siblings are reaped opportunistically so that a long-lived host does not
    accumulate one cache tree per process that ever ran.
    """
    root = Path(os.environ.get("SBU_NAGINI_CWD")
                or Path(tempfile.gettempdir()) / f"sbu_nagini_{os.getuid()}")
    mine = root / str(os.getpid())
    # Recreated on every call: the temp root is reapable by design, and a cwd
    # that has been swept out from under the verifier fails it for no reason.
    mine.mkdir(parents=True, exist_ok=True)
    for sib in _dead_siblings(root):
        _rmtree_quiet(sib)
    return mine


def _dead_siblings(root: Path) -> list[Path]:
    """Sibling cache dirs whose owning process is gone.

    A pid that cannot be signalled is dead; one that raises PermissionError
    belongs to another user and is alive. A recycled pid inherits the directory,
    which is harmless -- it is a cache, and the two runs are not concurrent.
    """
    out = []
    for sib in root.iterdir() if root.is_dir() else ():
        if not sib.is_dir() or not sib.name.isdigit():
            continue
        try:
            os.kill(int(sib.name), 0)
        except ProcessLookupError:
            out.append(sib)
        except OSError:
            pass
    return out


def _rmtree_quiet(p: Path) -> None:
    import shutil
    shutil.rmtree(p, ignore_errors=True)


class NaginiBackend(Backend):
    name = "nagini"
    language = LanguageTables(
        flavor="python",
        solution_filename="model.py",
        comment_line="#",
        region_names=("axioms", "pure", "pre-conditions", "post-conditions",
                      "invariants", "impl"),
        import_allowlist=("typing", "nagini_contracts"),
        banned_tokens=("Assume(", "Refute("),
    )

    def check(self, path: Path, timeout: int = 300,
              float_encoding: str | None = None) -> VerifyResult:
        """The script enforces the timeout (clean JVM+Z3 group kill, exit
        124); the subprocess timeout is only a backstop so the script's kill
        wins (no orphaned JVMs). float_encoding comes from the bundle's
        meta.json.

        `path` is absolute at every call site and nagini is invoked by absolute
        path, so the cwd is nagini's cache location and nothing else; see
        `_private_cwd` for why it must not be shared.
        """
        cmd = ["bash", str(VERIFY_SCRIPT), str(path)]
        if float_encoding:
            cmd.append(f"--float-encoding={float_encoding}")
        env = dict(os.environ, SBN_VERIFY_TIMEOUT=str(timeout))
        start = time.monotonic()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout + 30,
                                  cwd=str(_private_cwd()), env=env)
        except subprocess.TimeoutExpired as e:
            return VerifyResult(False, time.monotonic() - start,
                                _as_text(e.stdout), _as_text(e.stderr) + "\n[timeout]",
                                timed_out=True, returncode=124)
        elapsed = time.monotonic() - start
        out = proc.stdout or ""
        return VerifyResult(proc.returncode == 0 and SUCCESS_MARKER in out,
                            elapsed, out, proc.stderr or "",
                            timed_out=proc.returncode == 124,
                            returncode=proc.returncode,
                            no_verdict_detail=_no_verdict(proc.returncode, out))

    def conf_shadow(self, bundle_dir: Path) -> ShadowSpec | None:
        """The model IS Python: conformance_check.py runs the contract-
        stripped impl region directly — provenance "direct"
        (docs/adding_a_backend.md §1)."""
        script = bundle_dir / "conformance_check.py"
        if not script.exists():
            return None
        return ShadowSpec(provenance="direct", script=script)

    def verifier_tool_name(self) -> str:
        return "nagini_verify"
