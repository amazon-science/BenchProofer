"""properties.py — G-PBT falsification battery for django__django-11179 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct fastDelete`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable identity handle plus a
read-only removal count:

  fastDelete (mut pk : Option Int) (removed : Nat) return (count : Nat)
    ensures pk = none
    ensures count = removed

The record's identity handle ``pk`` is an ``Option Int`` (present ``some k``
while the record denotes a stored row, ``none`` once cleared); ``removed`` is the
count the batch removal reported, carried in as a read-only input. There is no
``require`` clause, so the admitted domain is total.

TWO independent top-level clauses, each load-bearing:
  (1) ``pk = none`` — THE fix. After the short-circuit the record no longer
      denotes any stored row, so its identity handle MUST be cleared, regardless
      of what it held before. A body that leaves ``pk`` at its incoming
      ``some k`` fails here — this is exactly the pre-change behaviour the F2P
      test observes.
  (2) ``count = removed`` — the reported count is the batch's count UNCHANGED;
      clearing the handle must not perturb the returned number. The post-image is
      GROUNDED in the method input ``removed`` (directive 8), a transparent
      ``Nat`` equality — NOT an opaque answer key. A body that fabricates the
      count (a literal, or anything other than the input ``removed``) fails here.

BINDER STRUCTURE (read before judging binder coverage). Clause (1) depends on
the ``pk`` binder alone; clause (2) depends on the ``removed`` binder alone. The
reject witnesses vary BOTH: ``pk`` over ``some 5 / some 7 / some 2`` and
``removed`` over ``3 / 5 / 3`` — the drop-clear rival abuses a PRESENT ``pk`` (so
clearing is a real transition), and the two count rivals abuse a NON-ZERO
``removed`` (so a fabricated literal is observably wrong). Neither binder is
pinned across the battery.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling holds
    ``instance.pk`` at a FULL heap permission the fix must WRITE, and reasons
    about permission preservation (``Ensures(Acc(instance.pk))``). Lean and
    Velvet are referentially transparent: ``pk`` is a ``mut`` VALUE binder with
    no heap footprint, no aliasing, and no fractional-permission system — the
    unchanged-frame obligation is instead discharged by pinning ``pk``'s exact
    post-state (``pk = none``) and the count's (``count = removed``). Nagini
    itself notes there is NO read-only ``Acc(.,1/2)`` input here (``using`` is a
    pass-by-value scalar), so the canonical frame-mutation probe does not apply
    on either backend. Not fabricated (porting map: vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A here. On nagini the count is produced by a
    ``@Pure @ContractOnly`` oracle ``removed_row_count(identifier)`` whose only
    guarantee is ``>= 0`` (an OPAQUE value): the two count attacks there are
    "fabricate a literal" and "call the oracle on the WRONG identifier". On this
    carrier the batch's count is NOT re-derived — it is taken as the method input
    ``removed`` (mapping.md §3), so the post-image ``count = removed`` is grounded
    directly in a transparent input. The fabricate-a-literal attack ports
    directly (below); the wrong-identifier attack has NO counterpart, because
    there is no second numeric input to mis-apply and no opaque oracle to call —
    the count clause names ``removed`` and nothing else. See the footer.
  * DIVERGENCE / NON-TERMINATION — no ``diverge-*`` / ``nonterm-*`` /
    ``weak-diverge`` case exists in the nagini sibling, so there is nothing to
    port and no known-hole to record for this instance.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``fastDeleteTester pk removed = false`` says the extracted program's observable
(the mutated handle ``pk`` and the returned count) violates the method's
postcondition at that concrete input. Checked in a file whose ``prove_correct``
block has been stripped, so no tactic script can mask the verdict. The carriers
are ``Option Int`` and ``Nat`` with decidable equality, so every witness closes
by ``decide``. Each reject witness below was run against BOTH the rival (exit 0)
and the frozen solution (exit 1) with two real builds and was SEEN to
discriminate.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the batch's count
is a directive-7 free input ``removed``, and the identity-clear is modeled deeply
as ``pk := none`` — no consumed oracle). The gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11179"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_GOLD_IMPL = (
    "    pk := none\n"
    "    return removed"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case may retune the tactic script without
# ---- touching the spec statement or dropping the obligation. Unique in file.
_GOLD_PROOF = "prove_correct fastDelete by\n  loom_solve"

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. `fastDeleteTester pk removed = false` says the extracted
# ---- program's observable violates the postcondition at that input. No
# ---- `axiom`/`sorry`/`native_decide`; the frozen solution rejects each witness.
def _tester(body):
    return (
        "extract_program_for fastDelete\n"
        "prove_precondition_decidable_for fastDelete\n"
        "prove_postcondition_decidable_for fastDelete\n"
        "derive_tester_for fastDelete\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG. Each keeps the
    # byte-identical two-clause obligation and only reshapes the executable
    # surface; the frozen `loom_solve` script still discharges both. Both
    # verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # CAPTURE the count into a temporary, CLEAR the handle FIRST, then return
        # the captured count — the clear-then-report order (vs the gold
        # report-value/clear order). Observationally identical final state: the
        # handle is `none` and the returned count is `removed`, so both clauses
        # discharge and no new obligation is introduced.
        "module": _impl(
            "    let c := removed\n"
            "    pk := none\n"
            "    return c"),
        "rationale": "a correct reshape: bind the count to a local temporary, "
                     "clear the handle FIRST, then return the temporary (clear-"
                     "then-report vs the gold order). The final handle is `none` "
                     "and the returned count equals `removed` on every input, so "
                     "both clauses (`pk = none`, `count = removed`) still discharge "
                     "under the frozen script; if it failed to verify the spec "
                     "would be SPEC-TOO-STRONG on impl shape. (Sibling: "
                     "pos-control-reorder.)",
    },
    {
        "id": "pos-control-arith",
        "kind": "soundness",
        "expect": "verify",
        # An equivalent ARITHMETIC form of the returned count: `removed + 0`.
        # Same clear, same value (`removed + 0 = removed` on `Nat`), so both
        # clauses discharge. A local-shape reshape of the reported number that a
        # `count` temporary would otherwise hide.
        "module": _impl(
            "    pk := none\n"
            "    return removed + 0"),
        "rationale": "a correct reshape of the reported count into the equivalent "
                     "arithmetic form `removed + 0` (definitionally `removed` on "
                     "`Nat`), with the same handle clear. Both clauses still "
                     "discharge under the frozen script; if it failed to verify "
                     "the spec would be SPEC-TOO-STRONG. (Sibling: "
                     "pos-control-inline.)",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude the
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is DEGENERATE at the interesting F2P point.
    # This case discharges an in-region `assert` pinning the F2P-shaped corner —
    # a record whose handle is genuinely PRESENT (`some 7 ≠ none`, so clearing is
    # a real transition) with a concrete non-zero count — as satisfiable and
    # non-degenerate. The surrounding impl and the frozen proof are kept verbatim
    # so the method's own obligation still discharges; the assert is LIVE (a
    # false claim about the same point leaves an unsolved goal — confirmed
    # out-of-band).
    # =====================================================================
    {
        "id": "admiss-present-handle-nonzero-count",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      ((some 7 : Option Int) ≠ none ∧ (3 : Nat) = 3))\n"
            "    pk := none\n"
            "    return removed"),
        "rationale": "the modeled behaviour is non-degenerate at the F2P corner: "
                     "the record's identity handle is genuinely PRESENT before the "
                     "short-circuit (`some 7 ≠ none`, so clearing it to `none` is a "
                     "real state transition, not a no-op) and the reported count is "
                     "a concrete non-zero number. The in-region assert must "
                     "discharge (else the interesting input is excluded / "
                     "PRECOND-TOO-STRONG at the point that matters); the impl and "
                     "frozen proof are kept verbatim so `pk = none` and "
                     "`count = removed` still discharge too. (Sibling: "
                     "admiss-f2p-shaped-input.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH
    # binders (see BINDER STRUCTURE above).
    # =====================================================================
    {
        "id": "weak-drop-clear",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Omit the handle clear entirely: report the count but leave the
        # handle at its incoming `some k`. Isolates clause (1): clause (2) holds
        # (the count is `removed`), only the cleared-handle guarantee fails.
        "module": _impl("    return removed"),
        "refinement": "this IS the pre-change behaviour the failing test observes: "
                      "the single-standalone-record short-circuit removes the row "
                      "and reports the count but never clears the record's identity "
                      "handle, so a record that no longer denotes any stored row is "
                      "left carrying its stale identifier. The F2P test creates "
                      "such a record, runs the removal, and asserts the handle is "
                      "cleared afterward; with the clear absent the handle keeps "
                      "its value and the assertion fails. Its faithful real patch "
                      "(the un-patched short-circuit) is exactly what does NOT "
                      "resolve.",
        "rationale": "REJECT from clause (1) `pk = none`: with the clear dropped, "
                     "`pk` is still the non-None incoming handle at return, "
                     "violating the cleared-handle guarantee. The count clause is "
                     "kept correct so the ONLY failing clause is the handle. If "
                     "this verified the spec would admit the pre-change bug => "
                     "SPEC-TOO-WEAK. Refuted at `pk = some 5`, `removed = 3` (a "
                     "present handle: `some 5 ≠ none`). (Sibling: uniq-drop-clear.)",
        "witness": _tester(
            "example : fastDeleteTester (some 5) 3 = false := by\n  decide\n"),
    },
    {
        "id": "weak-fabricate-count",
        "kind": "uniqueness",
        "expect": "reject",
        # Clears the handle correctly but FABRICATES the reported count as the
        # literal 1 instead of the batch's count `removed`. Isolates clause (2):
        # clause (1) holds, only the reported count is wrong.
        "module": _impl(
            "    pk := none\n"
            "    return 1"),
        "refinement": "returning a hard-coded 1 fabricates the surfaced deleted-row "
                      "count. The real batch removal reports the DB-reported "
                      "rowcount (1 for a live single row, but 0 when no row "
                      "matches); the count-observing tests read the actual number. "
                      "A faithful patch that returned a constant 1 would report a "
                      "deletion when nothing was deleted and would NOT resolve "
                      "those count-observing tests.",
        "rationale": "REJECT from clause (2) `count = removed`: the body returns "
                     "the literal 1, which differs from `removed` whenever "
                     "`removed ≠ 1`. The post-image pins the count to the input "
                     "`removed` REGARDLESS of the literal, so a `removed ≠ 1` "
                     "refutes it. The handle clear is kept correct so the ONLY "
                     "failing clause is the count. Refuted at `pk = some 7`, "
                     "`removed = 5` (5 ≠ 1). (Sibling: uniq-fabricate-count.)",
        "witness": _tester(
            "example : fastDeleteTester (some 7) 5 = false := by\n  decide\n"),
    },
    {
        "id": "weak-fabricate-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # The supporting near-miss: report the literal 0 ("no rows deleted").
        # Same defect as fabricate-count (a literal cannot equal the input count
        # in general), refuted at its own distinguishing point where `removed`
        # differs from 0.
        "module": _impl(
            "    pk := none\n"
            "    return 0"),
        "refinement": "returning a hard-coded 0 always reports 'no rows deleted'. A "
                      "faithful patch returning a constant 0 would tell caller code "
                      "nothing was deleted even when a live row was removed, failing "
                      "the tests that assert the count of the deleted object. "
                      "Supporting near-miss for the fabricated-count attack.",
        "rationale": "REJECT from clause (2) `count = removed`: the literal 0 "
                     "differs from `removed` whenever `removed ≠ 0`. The handle "
                     "clear is kept correct so the ONLY failing clause is the "
                     "count. Refuted at `pk = some 2`, `removed = 3` (3 ≠ 0) — a "
                     "DIFFERENT input point from the fabricate-1 rival (which is "
                     "refuted only where `removed ≠ 1`), so it demonstrates the "
                     "count must equal the input, not merely differ from one "
                     "particular literal. (Sibling: uniq-fabricate-zero.)",
        "witness": _tester(
            "example : fastDeleteTester (some 2) 3 = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a two-case AXIOM lane,
# contracting `remove_single_independent(instance, using)` over a
# permission-bearing heap object whose count is produced by an opaque `@Pure`
# oracle `removed_row_count(identifier)`. This bundle models a NARROWER, more
# TRANSPARENT surface: `fastDelete (mut pk : Option Int) (removed : Nat)` folds
# the batch's count into the read-only input `removed` (grounded, not oracle-
# derived) and models the identity-clear deeply as `pk := none`. Every sibling
# case is accounted for below.
#
#   sibling case (nagini)        -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder          -> pos-control-reorder                PORTED
#   pos-control-inline           -> pos-control-arith                  RE-EXPRESSED
#   admiss-f2p-shaped-input      -> admiss-present-handle-nonzero-count RE-AIMED
#   uniq-drop-clear              -> weak-drop-clear                    PORTED (central)
#   uniq-fabricate-count         -> weak-fabricate-count               PORTED
#   uniq-fabricate-zero          -> weak-fabricate-zero                PORTED
#   uniq-wrong-identifier        -> (none)                             N/A (no counterpart)
#   uniq-count-after-clear       -> (none)                             N/A (no counterpart)
#   AXIOM_TESTS (2)              -> (none)                             DROPPED (G-AX)
#
# PORTED (pos-control-reorder): the sibling captures the stored pk, clears it
#   first, then computes the count; here the analogue binds the count to a
#   temporary, clears the handle first, then returns it. RE-EXPRESSED
#   (pos-control-arith): the sibling drops the `count` temporary and returns the
#   oracle call directly; on this carrier the count IS the input `removed`, so the
#   "different local-variable shape" is re-expressed as the equivalent arithmetic
#   form `removed + 0`. Both verified with real builds under the frozen proof.
# RE-AIMED (admiss): the sibling injects an in-impl witness building a concrete
#   F2P-shaped persisted object and asserts it satisfies the Requires (Acc + pk
#   is not None). There is no `require` clause here, so the "a normal input
#   satisfies the precondition" reading is vacuous. The case is re-aimed at
#   proving the modeled behaviour is non-degenerate at the F2P corner (a genuinely
#   PRESENT handle `some 7 ≠ none`, so clearing is a real transition, with a
#   concrete non-zero count). loom_solve discharges the assert VC; the impl and
#   frozen proof are kept verbatim.
# PORTED (weak-drop-clear): the central prepatch bug (omit the handle clear)
#   ports directly and is the headline reject. PORTED (weak-fabricate-count /
#   weak-fabricate-zero): the two literal-fabrication attacks on the count clause
#   port directly; on this carrier they are refuted WITHOUT any opaque oracle
#   because `count = removed` is grounded in a transparent `Nat` input — the
#   witnesses `decide` outright.
# N/A (uniq-wrong-identifier): the sibling calls the oracle on the WRONG
#   identifier (`using`, a second scalar) so the two opaque oracle applications
#   cannot be proven equal. On this carrier the count is NOT re-derived from an
#   identifier — it is the single input `removed`, and there is no second numeric
#   input to mis-apply and no oracle to call. The attack has no expressible
#   counterpart (the abstraction folds the derivation away); NOT dropped for
#   difficulty. N/A (uniq-count-after-clear): the sibling's order-of-operations
#   attack reads the pk for the count AFTER clearing it, so the count is taken of
#   the post-clear (None) value. Here the count does NOT depend on `pk` at all
#   (it is the input `removed`), so clearing the handle before/after returning the
#   count cannot perturb it — there is no order-of-operations attack on clause (2)
#   to express. Both count-clause order/identifier attacks collapse because the
#   count is grounded in a free input rather than derived from the handle.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this bundle declares no
#   axiom (the batch's count is a directive-7 free input `removed`, modeled as an
#   A-reference; the identity-clear is modeled deeply as `pk := none`), so there
#   is nothing there to probe. The gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Both independent top-level clauses are attacked:
#   (1) `pk = none` by weak-drop-clear, (2) `count = removed` by
#   weak-fabricate-count and weak-fabricate-zero; and both are defended by the two
#   positive controls and the admissibility case. The three reject witnesses probe
#   three DISTINCT inputs (pts=3):
#     pk=some 5, removed=3     weak-drop-clear
#     pk=some 7, removed=5     weak-fabricate-count
#     pk=some 2, removed=3     weak-fabricate-zero
#   so `pk` is varied over {some 5, some 7, some 2} (always PRESENT, so the clear
#   is a real transition the drop-clear rival abuses) and `removed` over {3, 5}
#   (non-zero, and 3 ≠ 0 / 5 ≠ 1 are exactly what make the two literal fabrications
#   observably wrong at their own distinguishing points). Neither binder is pinned
#   across the battery. Each witness was SEEN to discriminate: it ELABORATES
#   against the rival (exit 0) and FAILS against the frozen solution (exit 1),
#   confirmed with two real builds each.
AXIOM_TESTS = []
