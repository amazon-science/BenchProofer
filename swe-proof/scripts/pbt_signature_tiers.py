#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Classify the gold-side evidence behind every PASSING G-PBT reject case.

A reject case passes when its witness holds of the rival and FAILS against gold.
"Failed" is an exit code, and the four `_STUCK_*` screens exist because an exit
code can mean "the kernel never evaluated the claim". `gold_signature` records
the first diagnostic so that "which other passing cells rest on this shape?" is
measurable from the artifacts instead of estimated by grepping manifests for
witness shapes. This is the reader.

The tiers are ordered by how directly the recorded bytes attest that GOLD
SATISFIES THE SPEC at the witness's point. `classify` is first-match-wins, so
this is also the order the patterns are tried in:

  decided     the kernel evaluated the claim and reported it false. The
              strongest form and the one the `_STUCK_*` screens protect.

  reduced     the witness's own hypothesis was reduced to `True` against gold,
              or gold's goal to a bare `False`. Stronger than it looks, not
              weaker: `simp` PROVED the equation the witness assumed was
              violated. None of these bytes name the reduct -- the tier surfaces
              only as whatever tactic then choked on it -- so each pattern below
              pairs a tactic with the reason clause that identifies the reduct.
              A bare tactic name would misfile a goal that was never reduced.

  disagreed   two concrete terms are shown to differ (`rfl` printing both sides,
              `omega` reporting the constraints satisfiable), so the claim was
              evaluated far enough to exhibit gold's actual value.

  shape       the script broke on the GOAL'S STRUCTURE before reaching gold's
              values. The unifier looked at gold's term without evaluating it,
              so a real value disagreement and a reduction that stalled are
              indistinguishable from the message. This is the tier that needs an
              agent: a structural mismatch is what a hollow rejection looks
              like, and the deciding test is whether a witness claiming the
              OPPOSITE fails identically -- which needs builds, not a regex.

  inert       a rewriting tactic reported it had nothing to do. Either an
              earlier step of the witness's own script had already reduced the
              target to `True` (so the case is `reduced` in everything but its
              bytes), or the target is an axiomatised callee applied to a
              symbolic argument and nothing was ever evaluated. Both spell ONE
              identical signature, so this cannot be split: two rules would
              carry the same pattern and first-match-wins would collapse them.
              Separating the halves needs a whole-log screen in the
              `_stuck_screen` style, not another signature regex.

  exhausted   a resource wall instead of a verdict, so nothing was decided in
              either direction: the opposite claim exhausts the same budget and
              prints the same bytes. A screen gap as well as a reader gap, since
              no `_STUCK_*` string matches this message.

  stuck       a `_STUCK_*` screen's own text, which should be empty: those cases
              are failed by the gate, not passed. Non-zero here means a screen's
              whole-log scan and the first-diagnostic signature disagreed, which
              is the asymmetry `_stuck_screen` documents.

  truncated   the signature window closed before the goal was printed, so the
              deciding bytes are not in the record at all -- a defect of the
              RECORD rather than of the build. The bucket holds both extremes,
              from a hypothesis reduced to `True` against gold down to a carrier
              gap where nothing was evaluated. The remedy is `unrecorded`'s --
              re-gate to classify -- but only after the window is widened (keep
              the line carrying the goal, or raise `_SIGNATURE_MAX_LINES`), since
              a re-gate at today's window reproduces the same blanks.

  unrecorded  the record predates `gold_signature`. Re-gate to classify.

  other       matched no rule. Printed in full under --verbose so the tiers can
              be extended against real bytes rather than guessed.

HOW A TIER'S MEMBERSHIP IS DECIDED. Every tier below `decided` was widened, or
added, the way the `shape` entry prescribes: by rebuilding the witness against
the frozen solution with its claim FLIPPED, and asking whether the recorded
message reappears. A message that is byte-identical for the opposite claim
attests nothing about gold; one that changes or disappears does. That experiment,
not the bytes, is what puts a message shape in a tier -- on their own the bytes
are frequently a tactic's complaint rather than a statement about the
implementation, which is why every pattern below carries the reason it sits where
it does.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
    python scripts/pbt_signature_tiers.py [--backend velvet|lean]
      [--verbose] [--out <path>]

The last roll-up counts the batteries whose passing rejects rest ENTIRELY on one
tier. Entirely, not partly: a battery with one shape-tier case and six decided
ones is already attested by the six. The tiers that attest nothing are `shape`,
`inert`, `exhausted`, `truncated`, `stuck`, `other` and `unrecorded`, so weak
evidence is the union over those rather than any single one of them -- a battery
whose cases are part `shape` and part `truncated` has no attesting case either.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Ordered: first match wins, strongest first. Written against real build bytes
# from this corpus -- see the docstring for what each tier means. One tuple of
# alternatives per tier, so a shape can be added next to the reason it belongs
# there instead of appended to a single unreadable pattern.
_DECIDED = (
    r"proved that the proposition",
    r"`decide` proved",
    r"\bis false\b",
)

_REDUCED = (
    r"\bhas type True\b",
    r"`True\.symm`",
    r"Projections are not supported",
    r"unsolved goals[^|]*⊢ False\s*$",
    r"has type True but is expected",
    r"\bis a proof of True\b",
    # `simp` rewrote the negated goal's spec instance to `True` and `not_true`
    # collapsed it to the bare constant, so the anonymous constructor carrying
    # the counterexample components met a type with no constructors. `False` is
    # load-bearing: with any other constructorless expected type the inference
    # "simp proved the spec instance" does not hold.
    r"`⟨\.\.\.⟩` notation: The expected type `False` has no constructors",
    # The same reduct met by a trailing `exact` or `simpa using`, whose printed
    # expected type IS the collapsed goal. A hypothesis's type cannot become
    # `False`, so `False` here is the goal after the script's own unfold/simp
    # discharged the antecedent of `¬ spec x (impl x)`; `¬True` is the `simp
    # only` half-step with the reduct still visible. `rfl` is excluded because
    # its metavariable form belongs in `disagreed`, and `noConfusionType` is
    # excluded because there the `False` usually comes from the witness's own
    # intro/rintro/injection rather than from a reduction.
    (r"^Type mismatch\b(?!\s+rfl\b)(?!.*noConfusionType).*"
     r"\bbut is expected to have type (?:False|¬True)$"),
    # The application elaborator printing gold's instantiated hypothesis as a
    # REFLEXIVE equation: the reduction ran and gold's branch produced exactly
    # the term the spec required. The `pure` / `do pure PUnit.unit pure` residue
    # on one side is the do-block pretty-printer, not a semantic wrapper. A
    # reflexive pair of METAVARIABLES is excluded -- that is reflexive only
    # because the unifier had nothing to solve it against.
    (r"Application type mismatch: The argument .*? has type "
     r"(?:(?!\?m\.)(?P<refl_whole>\S.*?) = "
     r"(?:(?:do pure PUnit\.unit )?pure \()?(?P=refl_whole)\)?"
     r"|\((?:do pure PUnit\.unit )?pure \((?!\?m\.)(?P<refl_inner>\S.*?)\)\)"
     r" = (?P=refl_inner))"
     r"(?= but is expected to have type|$)"),
    # The tactic is the victim, not the cause: the build got this far only
    # because an earlier `simp` had already reduced the witness's claim away, so
    # the closing tactic found the goal shape it needed absent. Tactic name and
    # reason clause are paired deliberately -- a bare `equality expected` or
    # `no applicable constructor found` would be free to catch a future goal
    # that was never reduced at all, and this tier outranks the ones that get an
    # agent.
    (r"Tactic `(?:constructor|rfl|split|injection)` failed: "
     r"(?:no applicable constructor found"
     r"|Expected the goal to be a binary relation"
     r"|Could not split an .if. or .match. expression"
     r"|equality expected)"),
    # A lambda over a goal that is already `False` has no domain to bind, so the
    # binder's type never resolves and field notation on it reports the type as
    # unknown. Same reduct, one more tactic away.
    r"Type of \S+ is not known; cannot resolve field",
    # `simp` reduced the spec instance to `True` with the goal left visible.
    r"⊢ ¬True\s*$",
)

_DISAGREED = (
    r"is not definitionally equal to",
    r"omega could not prove the goal",
    r"linarith failed",
    r"The left-hand side",
    # Term-mode `rfl` at an expected type `implementation_f args = value`: the
    # elaborator ran isDefEq on gold's term and it returned false. The weakest
    # member of this tier, because the metavariables are UNASSIGNED and so the
    # claim is printed while gold's reduct is not. The bytes have two opposite
    # causes no regex over them can separate -- both sides reduced to differing
    # values, or one side was stuck on a callee the kernel would not unfold and
    # no values were ever compared -- so cells where reducibility rather than
    # value decides the message are named on the weak worklist instead.
    r"Type mismatch rfl has type \?m\.\d+ = \?m\.\d+ but is expected to have type",
    # A type ascription or `simpa using` rejection whose printed type holds
    # gold's call REDUCED beside the value the witness claimed. Reached only
    # after the `reduced` clause above, so what is left is the case where the
    # expected type is a concrete term rather than the collapsed goal, or where
    # the term was long enough that the signature window cut it -- and a cut can
    # only push a case DOWN into this weaker bucket, never up.
    r"^Type mismatch\b(?!\s+rfl\b)",
    # An `unsolved goals` residue whose goal is `<gold's term> = <the claimed
    # term>`, both exhibited, one `decide` short of a decision. The negative
    # lookahead is load-bearing: without it this clause swallows the monadic
    # carrier goals that belong in `shape`, and reports the hollowest cases in
    # that family as the second-strongest tier.
    (r"^unsolved goals[\s\S]*⊢"
     r"(?!(?:(?!⊢).)*(?:\bpure\b|\bdo\b|Id\.run|\bwp\b))(?:(?!⊢).)*="),
    # `grind` whose single asserted fact is the negation of a CLOSED arithmetic
    # equation, with both sides printed and the claimed equation named false.
    # Anchored on numerals: an opaque-atom grind failure, or the multi-hypothesis
    # form, is not a value disagreement and must not be filed as one.
    r"`grind` failed case grind h : ¬[-0-9 +*()^/=]{1,60}⊢ False",
)

_SHAPE = (
    r"There are no additional binders",
    r"Did not find an occurrence",
    r"no goals to be proved",
    r"unknown identifier",
    r"unknown constant",
    # The application elaborator on two STRUCTURALLY different types: a stuck
    # `match` on an opaque scrutinee, an unexpanded `implementation_*` symbol, an
    # unreduced `if` body, a projection out of a `pure`, a join point, or a
    # metavariables-only pair. The unifier looked at gold's term but the bytes do
    # not show that it evaluated it. Reached only after the reflexive clause in
    # `reduced`, so it claims exactly the non-reflexive remainder.
    r"Application type mismatch: The argument ",
    # The monadic carrier's definitional gap left as the residual goal (`⊢ ¬pure
    # x = x` and its projection and membership forms), because the witness's simp
    # set omits the lemma the bundle's own correctness proof uses. Claim-
    # independent: the same message appears for a claim that is TRUE of gold.
    (r"^unsolved goals[\s\S]*⊢(?:(?!⊢).)*"
     r"(?:\bpure\b|\bdo\b|Id\.run|\bwp\b|∈)"),
    # A weakest-precondition tactic cannot unify its POSITIVE-triple conclusion
    # with a NEGATED goal, and the signature prints the program term unreduced,
    # which is the tell that none of gold's values were evaluated.
    r"could not unify the conclusion of .@?WPGen\.intro.* with the goal ¬",
    # A term applied as a function because the conjunction it really has was
    # never reduced: gold's `if` is printed unreduced, so the exit code cannot
    # tell satisfaction from violation at that point.
    r"Function expected at \w+ but this term has type",
)

# A rewriting tactic reporting that it found nothing to rewrite. One string, two
# opposite meanings, not separable by any regex over it -- see the docstring.
_INERT = (
    r"`?d?simp(?:_all)?`? made no progress",
)

# A resource wall instead of a verdict: the same bytes appear for the opposite
# claim, so nothing was decided in either direction.
_EXHAUSTED = (
    r"maximum recursion depth has been reached",
)

_STUCK = (
    r"did not reduce to",
    r"failed to reduce to a decidable",
    r"Dependent elimination failed",
    r"failed to synthesize",
)

# The signature window closed inside the hypothesis dump, so the goal that would
# decide the tier is not in the record. Last, so it can only take what would
# otherwise be `other`, and after `stuck` so a screen's text keeps priority.
_TRUNCATED = (
    r"^unsolved goals(?![\s\S]*⊢ \S{2,})",
)

TIERS: tuple[tuple[str, re.Pattern], ...] = tuple(
    (name, re.compile("|".join(alts), re.I)) for name, alts in (
        ("decided", _DECIDED),
        ("reduced", _REDUCED),
        ("disagreed", _DISAGREED),
        ("shape", _SHAPE),
        ("inert", _INERT),
        ("exhausted", _EXHAUSTED),
        ("stuck", _STUCK),
        ("truncated", _TRUNCATED),
    )
)


def classify(signature: str) -> str:
    if not signature:
        return "unrecorded"
    for name, rx in TIERS:
        if rx.search(signature):
            return name
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--backend", choices=["velvet", "lean"], action="append",
                    help="repeatable; default both")
    ap.add_argument("--verbose", action="store_true",
                    help="print every 'other' and 'shape' signature in full")
    ap.add_argument("--out", help="write the per-case table as JSON")
    args = ap.parse_args()

    from swebench_unified import paths

    backends = args.backend or ["velvet", "lean"]
    corpus = paths.TASKS_ROOT
    if not corpus.is_dir():
        print(f"no corpus at {corpus} — set SBU_BENCHMARK_DIR", file=sys.stderr)
        return 2

    rows: list[dict] = []
    for d in sorted(p for p in corpus.iterdir() if p.is_dir()):
        for b in backends:
            m = d / b / "meta.json"
            if not m.exists():
                continue
            try:
                blob = json.loads(m.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            gate = (blob.get("gates") or {}).get("G-PBT") or {}
            for case in (gate.get("data") or {}).get("cases", []):
                if case.get("expect") != "reject" or not case.get("ok"):
                    continue
                sig = case.get("gold_signature") or ""
                rows.append({
                    "instance_id": d.name, "backend": b,
                    "case": case.get("id"), "tier": classify(sig),
                    "subject": case.get("witness_subject") or "",
                    "gold_stuck_screen": case.get("gold_stuck_screen") or "",
                    "signature": sig,
                })

    order = [t for t, _ in TIERS] + ["other", "unrecorded"]
    print(f"{len(rows)} passing reject case(s) over {', '.join(backends)}\n")
    for b in backends:
        rs = [r for r in rows if r["backend"] == b]
        if not rs:
            continue
        cnt = collections.Counter(r["tier"] for r in rs)
        print(f"{b}: {len(rs)} case(s)")
        for t in order:
            if cnt[t]:
                print(f"    {cnt[t]:5}  {t}")
        print()

    # Which batteries rest ENTIRELY on one tier: a mixed battery is already
    # attested by its stronger cases, so only the pure ones need a look.
    per_cell: dict[tuple[str, str], collections.Counter] = (
        collections.defaultdict(collections.Counter))
    for r in rows:
        per_cell[(r["backend"], r["instance_id"])][r["tier"]] += 1
    print("batteries whose passing rejects rest ENTIRELY on one tier:")
    pure: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for (b, iid), cnt in sorted(per_cell.items()):
        if len(cnt) == 1:
            pure[next(iter(cnt))].append((b, iid))
    for t in order:
        if pure[t]:
            print(f"    {len(pure[t]):5}  {t}")
    if "stuck" in pure and pure["stuck"]:
        print("\n  !! a PASSING case carrying a stuck screen's own text — the "
              "whole-log scan and the first-diagnostic signature disagree here:")
        for b, iid in pure["stuck"][:20]:
            print(f"     {b} {iid}")

    if args.verbose:
        for t in ("shape", "other"):
            hits = [r for r in rows if r["tier"] == t]
            if not hits:
                continue
            print(f"\n--- {t} ({len(hits)} case(s)) ---")
            for r in hits:
                print(f"  {r['backend']:6} {r['instance_id']:34} "
                      f"{str(r['case'])[:26]:28} {r['signature'][:110]}")

    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=1))
        print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
