"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13439 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct compositeSize`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  compositeSize (steps : List Int) return (n : Nat)
    ensures n = steps.length

A composite is an ordered collection of constituent stages; the query reports
how many stages it holds. The single load-bearing ``ensures`` clause pins the
result to the exact cardinality of the input collection ``steps`` — every stage
counted once, none omitted, none double-counted — so an index handle spanning
"from the start up to the size" covers the whole collection. ``steps`` is the
only input binder; the reject witnesses must vary its LENGTH, since a rival that
mishandled only one cardinality would slip past a battery that probed a single
length.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer.)
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the whole reject lane here:
    the single clause pins the count on EVERY cardinality, so a rival that is
    correct on part of the length domain but diverges on a sub-domain (one short
    on every collection; a constant that is right only at the F2P size; wrong
    only on the empty collection) is refutable at exactly that sub-domain.
  * UNGROUNDED-ORACLE ECHO — N/A. The result is pinned to ``steps.length``, the
    fully-unfolded cardinality of the actual input (the ``axioms`` region is
    empty — no opaque answer key to echo); the cheapest correct impl simply
    evaluates it, which the positive control covers honestly.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
three witnesses sit at three DISTINCT collection lengths (3, 1, 0), so the
manifest demonstrates the post-image's dependence on the cardinality of
``steps`` rather than merely its value at one pinned length.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13439"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole impl body is the single statement
# ---- `return steps.length`; the `ensures` clause reads `n = steps.length`
# ---- (no `return`), so this substring lies wholly inside the impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap).
_A_IMPL = "    return steps.length\n"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. Unique in the file.
_T_PROOF = "prove_correct compositeSize by\n  loom_solve\n"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `compositeSizeTester steps = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("\n"
            "extract_program_for compositeSize\n"
            "prove_precondition_decidable_for compositeSize\n"
            "prove_postcondition_decidable_for compositeSize\n"
            "derive_tester_for compositeSize\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Keeps the obligation and only reshapes the executable
    # surface; the contract is point-wise, so the reproof stays a `loom_solve`
    # away from the frozen script (verified during authoring).
    # =====================================================================
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the cardinality into a named local `n` and return it — a
        # different impl shape from gold's inline `return steps.length`.
        # Observationally identical for every input.
        "module": _swap(
            _BASE, _A_IMPL,
            "    let n : Nat := steps.length\n"
            "    return n\n"),
        "rationale": "binding the cardinality into a named local `n := "
                     "steps.length` and returning it computes the same value, so "
                     "`n = steps.length` still holds on the whole domain; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "query's shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require`, so the "a normal input
    # satisfies the precondition" probe is trivial and not where the risk sits.
    # The residual admissibility risk on this surface is that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like one every impl meets. This case discharges an
    # in-region `assert` pinning the post-image's value at the F2P-shaped input
    # (a 2-stage composite): its reported size is exactly 2. The surrounding
    # impl is kept verbatim so the method's own obligation still discharges; the
    # assert is live (a false claim about that point leaves an unsolved goal —
    # verified during authoring).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _A_IMPL,
            "    assert (with_name_prefix `assert\n"
            "      (([1, 2] : List Int).length = 2))\n"
            "    return steps.length\n",
            _T_PROOF,
            "prove_correct compositeSize by\n  loom_solve <;> decide\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped input: for a 2-stage composite it demands the "
                     "reported size be exactly 2, the cardinality of the "
                     "collection. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable / PRECOND-TOO-STRONG); the impl "
                     "is kept verbatim so the method's own `ensures` still "
                     "discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-undercount-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Report one fewer than the cardinality. Wrong on every non-empty
        # collection (on the empty one, truncated Nat subtraction coincidentally
        # agrees, so the witness sits at a non-empty length).
        "module": _swap(_BASE, _A_IMPL,
                        "    return steps.length - 1\n"),
        "refinement": "a counterpart that reports one fewer than the number of "
                      "stages under-counts every non-empty composite; for the "
                      "F2P 2-stage composite it would report 1, so the assertion "
                      "that the reported size equals 2 FAILS, and an index handle "
                      "spanning up to the size would drop the terminal stage. It "
                      "would NOT resolve — this is the pre-fix truncated-traversal "
                      "shape.",
        "rationale": "REJECT from `n = steps.length`: `steps.length - 1` is one "
                     "short of the cardinality on every non-empty collection, "
                     "where the post-image demands the exact count. Verifying "
                     "would be SPEC-TOO-WEAK on the cardinality. Refuted at a "
                     "3-stage collection (a non-empty length distinct from the "
                     "other rivals' inputs).",
        "witness": _tester(
            "example : compositeSizeTester [3, 4, 5] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-constant-f2p-size",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the constant 2 — correct ONLY at the F2P cardinality, wrong for
        # every other collection size.
        "module": _swap(_BASE, _A_IMPL,
                        "    return 2\n"),
        "refinement": "a counterpart that always reports 2 passes the F2P "
                      "assertion (the 2-stage composite) but is correct ONLY at "
                      "cardinality 2: composites of any other size report the "
                      "wrong count, so index handles spanning up to the size "
                      "would over- or under-span. It would NOT resolve on the "
                      "many other-sized composites the surrounding tests build.",
        "rationale": "REJECT from `n = steps.length`: a constant 2 disagrees with "
                     "the cardinality on every collection whose length is not 2. "
                     "Verifying would be SPEC-TOO-WEAK (the clause pins ALL "
                     "cardinalities, not just the F2P witness). Refuted at a "
                     "1-stage collection (length 1, distinct from the other "
                     "rivals' inputs).",
        "witness": _tester(
            "example : compositeSizeTester [9] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-empty-overcount",
        "kind": "uniqueness",
        "expect": "reject",
        # Report 1 for the empty collection (correct otherwise). Isolates the
        # empty sub-domain.
        "module": _swap(_BASE, _A_IMPL,
                        "    if steps.length = 0 then\n"
                        "      return 1\n"
                        "    else\n"
                        "      return steps.length\n"),
        "refinement": "a counterpart that special-cases the empty composite to "
                      "report size 1 is correct for every non-empty composite but "
                      "mis-reports the empty one (an empty composite would claim "
                      "one stage), so an index handle spanning up to the size "
                      "would over-span and address a non-existent stage. It "
                      "diverges from the exact cardinality precisely on the empty "
                      "sub-domain, so it would NOT resolve there.",
        "rationale": "REJECT from `n = steps.length`: returns 1 when the "
                     "collection is empty (0), where the post-image demands 0. "
                     "Verifying would be SPEC-TOO-WEAK on the empty sub-domain. "
                     "Refuted at the empty collection (length 0, the sub-domain "
                     "no other rival probes).",
        "witness": _tester(
            "example : compositeSizeTester [] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 3 partial-domain uniqueness
# rivals). This bundle models only the purely-functional core — a single method
# `compositeSize` — where the sibling contracts one query over a
# permission-bearing list object. The value surface (the cardinality clause)
# carries across intact; the permission surface does not exist here. Every
# sibling case is accounted for below.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-local-reshape            -> pos-control-local-reshape     PORTED
#   admissibility-readonly-input         -> admiss-postimage-nondegenerate RE-AIMED
#   frame-mutation-write-steps           -> (none)                        VACUOUS
#   partial-domain-prepatch-undercount   -> weak-undercount-by-one        PORTED
#   partial-domain-constant-f2p-size     -> weak-constant-f2p-size        PORTED
#   partial-domain-empty-undercount      -> weak-empty-overcount          PORTED
#
# 4 ported, 1 re-aimed, 1 vacuous.
#
# VACUOUS (frame-mutation-write-steps): the sibling's mandatory frame-mutation
#   rival writes to a read-only input that carries only a fractional heap
#   permission, and is rejected for INSUFFICIENT PERMISSION before any value
#   reasoning. This backend is referentially transparent: every parameter is an
#   immutable value, this bundle declares no `mut` binder, there is no heap and
#   no aliasing. There is no read-only input to overwrite and no permission
#   system to trip, so the class is vacuous. No substitute is fabricated (per
#   the porting map, this class is legitimately dropped here rather than
#   replaced).
# RE-AIMED (admissibility): the sibling establishes that the half-permission
#   input is readable and reaches a normal return. There is no precondition and
#   no permission here, so that probe is not where the risk sits. It is re-aimed
#   at the residual admissibility risk on this surface: that the post-image is
#   unsatisfiable or degenerate at the interesting point. The case discharges an
#   in-region assert pinning the reported size of the F2P-shaped 2-stage
#   composite to exactly 2.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `n = steps.length` is
#   attacked by all three rivals across three distinct length sub-domains — the
#   uniform one-short under-count, the F2P-only constant, and the empty-only
#   over-count — refuted at three DISTINCT collection lengths (3, 1, 0; pts=3).
#   The single input binder `steps` is varied by length across the three
#   witnesses, so the manifest demonstrates the post-image's dependence on the
#   cardinality of `steps`, not merely its value at one pinned length.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; there is no axiomatized
#   callee (the cardinality is modeled deeply as `List.length`), and this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
