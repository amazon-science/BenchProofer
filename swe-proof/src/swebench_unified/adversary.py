# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Machine-checkable substrate for the agentic gates G-EQ / G-PANEL.

Backend-agnostic: everything here goes through Bundle, so an auditor for any
backend calls the same primitives. They exist so an attack produces a FACT, not
an opinion:

  same-spec <backend> <id> <attack-file>
      Confirm an attack module shares the bundle's EXACT spec (only the impl
      region may differ), so a "wrong impl that still verifies" attack can't
      cheat by also weakening a contract. Exit 0 iff identical.

  verify <backend> <id> <attack-file> [--float-encoding=...]
      Run the pinned backend verifier on the attack file. Exit 0 iff it verifies.

  weakness <backend> <id> <attack-file> [--float-encoding=...]
      The spec-too-weak check (G-PANEL attacker 1 / G-EQ): the attack must
      (1) share the bundle spec and (2) verify. If both hold it is a CANDIDATE
      counterexample — the auditor then shows its refined patch does NOT resolve
      (G-EQ), proving the spec admits an incorrect implementation. Exit 0 iff
      CANDIDATE.

Reads the bundle from the active benchmark root (SBU_BENCHMARK_DIR), so it
honors --benchmark-dir like the rest of the pipeline.
"""
from __future__ import annotations

import argparse
import difflib
import os
import sys
from pathlib import Path

from .backends import GATED_BACKENDS, get_backend
from .gates._common import check_bundle_file, env_int
from .markers import same_spec, spec_signature
from .variant_scope import unsound_evasions
from .verify import VerifyResult


def _bundle(backend: str, instance_id: str):
    from .gates.base import Bundle
    return Bundle(instance_id, get_backend(backend))


# One attack build. A cap that the MACHINE rather than the attack runs into makes
# check_attack report verify_completed=False, which the audit derivation must
# treat as inconclusive -- so concurrent load turns a sound cell's audit into a
# fail. So size this against what a verification costs when it is NOT competing,
# and use SBU_ATTACK_VERIFY_TIMEOUT to give a single re-run room without every
# other build paying for it.
ATTACK_VERIFY_TIMEOUT_DEFAULT = 300


def _attack_timeout() -> int:
    return env_int("SBU_ATTACK_VERIFY_TIMEOUT", ATTACK_VERIFY_TIMEOUT_DEFAULT)


# A cap the machine ran into, rather than the attack, is not a measurement.
# Reported as inconclusive it fails the audit closed, and enough of that reads as
# a corpus of broken specs.
#
# So a timeout buys one re-run with room instead of a verdict, which is cheaper
# than narrowing the fan-out: the case it pays for is rare and the case it
# prevents costs an agent-hour of repair work on a hole that is not there.
# Bounded, and 0 disables it: a verification that cannot converge in minutes will
# not converge in an hour, so the retry is for load, not divergence.
ATTACK_VERIFY_RETRY_FACTOR = 3.0
ATTACK_VERIFY_RETRY_CAP = 1800


def _verify_once(backend: str, instance_id: str, attack: Path, fe: str | None,
                 t: int) -> VerifyResult:
    b = _bundle(backend, instance_id)
    # float_encoding: prefer the explicit flag, else the bundle's meta value
    # (check_bundle_file reads meta for nagini). We pass the attack file
    # directly; the backend verifier runs it in place.
    if backend == "nagini" and fe is not None:
        return b.backend.check(attack, t, float_encoding=fe)
    return check_bundle_file(b, attack, t)


def _verify_attack(backend: str, instance_id: str, attack: Path,
                   fe: str | None) -> VerifyResult:
    t = _attack_timeout()
    r = _verify_once(backend, instance_id, attack, fe, t)
    if not getattr(r, "timed_out", False):
        return r
    factor = float(os.environ.get("SBU_ATTACK_VERIFY_RETRY")
                   or ATTACK_VERIFY_RETRY_FACTOR)
    if factor <= 1:
        return r
    roomy = min(ATTACK_VERIFY_RETRY_CAP, int(t * factor))
    if roomy <= t:
        return r
    return _verify_once(backend, instance_id, attack, fe, roomy)


def check_attack(backend: str, instance_id: str, attack: Path,
                 fe: str | None = None) -> dict:
    """Programmatic G-EQ/G-PANEL-1 primitive for the orchestrator: recompute
    the facts about an attack file, so pass/fail derives from a mechanical
    re-check, never the agent's word. Returns
    {same_spec, admissible, verifies, verify_completed, summary}.

    A CANDIDATE counterexample (spec admits a wrong impl) is
    same_spec AND admissible AND verifies. verify_completed is False on a verifier
    timeout/infra error — the caller must treat that as inconclusive, never as
    'does not verify' (which would mask a real weakness).

    admissible is False when the attack keeps the spec but never put a real
    question to the verifier. Two causes, opposite in kind: it would get its exit
    code by assuming rather than establishing (obligation dropped, new axiom,
    `sorry`, an `@ContractOnly` stub), or the checker's front end could not
    translate it at all (`VerifyResult.front_end_refusal`), so no proof obligation
    about it was ever generated. Such an attack is not evidence in either
    direction, so it is reported separately from `verifies`. Reporting it as
    'does not verify' would be worse than useless: the verifier never ran, yet the
    caller would count a rejection the specification never performed."""
    b = _bundle(backend, instance_id)
    out = {"same_spec": False, "admissible": True, "verifies": False,
           "verify_completed": True, "summary": ""}
    if not attack.is_file():
        out["summary"] = f"attack file missing: {attack}"
        out["verify_completed"] = False
        return out
    src = attack.read_text()
    frozen = b.solution.read_text()
    out["same_spec"] = same_spec(frozen, src, b.backend.language)
    if not out["same_spec"]:
        out["summary"] = "attack changed the spec (not a valid counterexample)"
        return out
    ev = unsound_evasions(frozen, src, b.backend.language)
    if ev:
        out["admissible"] = False
        out["summary"] = ("attack assumes rather than establishes: "
                          + "; ".join(ev) + " (not a valid counterexample)")
        return out
    r = _verify_attack(backend, instance_id, attack, fe)
    # A file the front end turned down is inadmissible, not rejected and not
    # inconclusive. Checked BEFORE the crash leg, which it is a subset of: the
    # verifier reached no verdict, but unlike a timeout or a JVM death it never
    # could have. No proof obligation about an untranslatable program exists, so
    # it cannot be the `verifies` candidate a weakness rests on, and the spec
    # never judged it either. Same treatment as an evasion above, for the same
    # reason and with the opposite cause: not evidence in either direction, and
    # so not counted toward the floor of attacks that actually probed the spec.
    if getattr(r, "front_end_refusal", False):
        out["admissible"] = False
        out["summary"] = (f"{r.summary}: the checker could not translate this "
                          "program, so the spec never judged it "
                          "(not a valid counterexample)")
        return out
    # No verdict is not a rejection. Both a timeout and a crash leave
    # `r.success` False, and reading that as "the spec rejected this attack"
    # would retire the attack and take the weakness it was probing with it.
    if getattr(r, "timed_out", False) or getattr(r, "crashed", False):
        out["verify_completed"] = False
        out["summary"] = f"{r.summary} (inconclusive)"
        return out
    out["verifies"] = r.success
    out["summary"] = r.summary
    return out


def cmd_same_spec(backend: str, instance_id: str, attack: str) -> int:
    b = _bundle(backend, instance_id)
    orig = b.solution.read_text()
    atk = Path(attack).read_text()
    tables = b.backend.language
    if same_spec(orig, atk, tables):
        print("SAME — attack shares the bundle's exact specification")
        return 0
    print("DIFFERENT — attack's spec signature differs:")
    for line in difflib.unified_diff(spec_signature(orig, tables).splitlines(),
                                     spec_signature(atk, tables).splitlines(),
                                     "bundle", "attack", lineterm=""):
        print("  " + line)
    return 1


def cmd_verify(backend: str, instance_id: str, attack: str, fe: str | None) -> int:
    r = _verify_attack(backend, instance_id, Path(attack), fe)
    print(f"{'VERIFIED' if r.success else 'FAILED'} in {r.wall_time_s:.1f}s")
    if not r.success:
        for ln in (r.stdout + "\n" + r.stderr).splitlines():
            if any(k in ln for k in ("error", "Error", "Postcondition",
                                     "Invariant", "sorry", "unsolved")):
                print("  " + ln)
    return 0 if r.success else 1


def cmd_weakness(backend: str, instance_id: str, attack: str, fe: str | None) -> int:
    b = _bundle(backend, instance_id)
    orig = b.solution.read_text()
    atk_path = Path(attack)
    if not same_spec(orig, atk_path.read_text(), b.backend.language):
        print("NOT-A-COUNTEREXAMPLE: attack changed the spec (run same-spec to "
              "see). A spec-too-weak attack keeps the spec and changes only the impl.")
        return 2
    r = _verify_attack(backend, instance_id, atk_path, fe)
    if not r.success:
        print(f"NOT-A-COUNTEREXAMPLE: attack does not verify ({r.summary}) — "
              "the spec rejected this impl (good).")
        return 2
    print(f"CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies ({r.wall_time_s:.1f}s).")
    print("  => Now write the REFINED real patch for this impl and show it does NOT")
    print("     resolve (G-EQ / run_resolve). If so, the spec is TOO WEAK.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="G-EQ/G-PANEL machine checks")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("same-spec", "verify", "weakness"):
        p = sub.add_parser(name)
        # Every check here runs a verifier, so the choices are the gated
        # backends from the registry -- never a second hand-written list.
        p.add_argument("backend", choices=sorted(GATED_BACKENDS))
        p.add_argument("instance_id")
        p.add_argument("attack")
        if name != "same-spec":
            p.add_argument("--float-encoding", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "same-spec":
        return cmd_same_spec(args.backend, args.instance_id, args.attack)
    if args.cmd == "verify":
        return cmd_verify(args.backend, args.instance_id, args.attack,
                          args.float_encoding)
    if args.cmd == "weakness":
        return cmd_weakness(args.backend, args.instance_id, args.attack,
                            args.float_encoding)
    return 2


if __name__ == "__main__":
    sys.exit(main())
