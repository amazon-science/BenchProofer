"""properties.py — G-PBT falsification battery for django__django-14122 (velvet).

NOT a Velvet module; a record of the adversarial cases the G-PBT gate executes
and stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant
that shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct groupingColumns`` obligation
survives with a byte-identical header) and swaps in a candidate implementation.
Each is checked by the real Lean verifier. ``expect:"verify"`` passes iff (in
scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify
AND its refutation ``witness`` discriminates — the witness elaborates against the
rival and FAILS against the witness SUBJECT. That subject is normally the frozen
solution; here it is an explicit ``witness_reference``, because the frozen impl's
extracted loop cannot be reduced by the kernel and so decides nothing. See the
CARRIER NOTE.

DEFENDED SURFACE — one contracted method over five READ-ONLY inputs:

  groupingColumns (baseCols selectCols orderTerms havingCols metaOrdering)
    ensures out = groupingSet baseCols selectCols orderTerms havingCols metaOrdering
    ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols

The method assembles the column list a row-grouping clause must contain by
concatenating four contributions in order: the grouping base, the selected
columns, the ordering-term columns, and the filter columns. ``groupingSet`` is a
fully-unfolded ``def`` over the method's own arguments (``orderFold`` is a
concrete front-recursive fold, not an opaque answer-key), so there is no
ungrounded oracle to echo.

Two independent top-level clauses:
  (C1) the total post-image ``out = groupingSet …`` — pins ALL five inputs and
       their concatenation order;
  (C2) the DISCRIMINATING clause: when the ordering was NOT requested explicitly
       (``metaOrdering = true`` — a default ordering), the ordering terms
       contribute NOTHING (``out = baseCols ++ selectCols ++ havingCols``). This
       is where the whole behavioural fix lives: a default ordering must not
       widen the grouping set, else the aggregation splits into spurious groups —
       the failing scenario the F2P test exercises.

The five inputs — ``baseCols``, ``selectCols``, ``orderTerms``, ``havingCols``,
``metaOrdering`` — are FREE: the post-image must hold for every value each takes.
That is what makes each partial-domain / dropped-contribution rival refutable at
a concrete point, and what the reject witnesses vary each binder across.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY GOLD CANNOT BE THE SUBJECT.
All five carriers are fully transparent (``List Int``, ``OrderTerm`` = two
transparent fields, ``Bool``): there is NO opaque leaf in the spec. A witness
reaches the post-image through Velvet's tester machinery
(``groupingColumnsTester … = false`` says the extracted program's result violates
the method's postcondition at that concrete input) and closes by ``decide`` at
concrete literals. Each reject rival is written as a LOOP-FREE closed form (a
single concatenation over the pure helpers ``orderFold`` / ``List.flatMap``), so
its extracted tester ``decide``s.

The constraint the carrier imposes is on the OTHER half. The frozen impl computes
the ordering contribution with a ``while`` loop, which extracts to a
``forIn Lean.Loop.mk`` fixpoint in ``DivM``; the kernel cannot reduce that, so
``decide`` on the gold tester is STUCK — for EVERY claim, at EVERY input,
regardless of truth. Measured: the gold-side build fails identically
(``did not reduce to `isTrue` or `isFalse` ``) for the real witness, for the exact
OPPOSITE claim (``… = true``), and for an all-empty input at which the loop runs
ZERO iterations. A gold-side exit code here therefore carries NO information, and
a stuck reduction is NOT the "fail against gold" half — it is the
``witness-undecided`` defect: it would attest to a refutation the kernel never
performed.

So every reject case below carries an explicit ``witness_reference``: the
loop-free ``pos-direct-model`` source, which shares the frozen spec byte-for-byte
and VERIFIES (it is also shipped as its own ``expect="verify"`` positive, so the
battery itself records that loop-freeness is not what any rival is rejected for).
The gate refutes each witness against THAT impl instead of gold. This is sound
for the reason gold was: an impl the verifier accepts cannot violate its own
spec, so a genuine witness must still fail there — and against the reference the
refutation is genuinely DECIDED (``decide`` reports "proved that the proposition
… is false"), not stuck. Verified by hand for all seven: rival exit 0, reference
exit 1 with a real verdict and no stuck-reduction message.

ADVERSARIAL READ of the sibling's classes (nagini, over five contracted list
inputs held at fractional permission):
  * FRAME-MUTATION — VACUOUS on this backend. The sibling writes into a
    half-permission read-only input to trip INSUFFICIENT PERMISSION. This backend
    is referentially transparent, has no heap and no aliasing, and this bundle
    declares NO ``mut`` binder — there is no read-only input to overwrite and no
    substitute probe to fabricate. (mapping.md directive 5 is discharged here by
    the absence of ``mut``, not by a permission check.)
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the domain but
    diverging on a sub-domain (the default-ordering branch; a back-reference
    ordering term; a dropped contribution). This is the sibling's core class and
    the bulk of the battery below.
  * FREE-INPUT PRESERVATION — APPLIES: the post-image carries FIVE free inputs;
    a rival can get the guard right and still drop one contribution, so each
    contribution is attacked on its own so its witness sits at a value the others
    do not probe.

WITNESS PLACEMENT. Rivals share a refutation point only when they fail there for
the same reason (they do not). Between them the seven reject witnesses move every
binder off any fixed value: ``metaOrdering`` takes both ``true`` (uncond-fold)
and ``false`` (all others); ``orderTerms`` carries both a back-reference term
(``isRef = true``) and a genuine term (``isRef = false``); ``baseCols`` /
``selectCols`` / ``havingCols`` are each moved to a non-empty value by the rival
that drops that contribution.

AXIOM lane: empty. The spec consumes NO ``axiom`` (the ordering decision is
modeled DEEPLY via ``orderFold`` and the ``groupingSet`` guard; the per-term
column lists and the reference flag are the method's explicit inputs, an
A-reference validated by G-AX, not a consumed contract). There is no axiom
soundness obligation for this gate, and the gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-14122"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). Rivals
# ---- that swap the whole body use this; sub-edits use the finer anchors below.
_IMPL_GOLD = (
    "    -- impl-start\n"
    "    -- Collect the ordering-term contributions (reference terms contribute\n"
    "    -- nothing) into `order`, built back-to-front so one fold unfold is exposed\n"
    "    -- per loop step.\n"
    "    let mut order : List Int := []\n"
    "    let mut i := orderTerms.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ orderTerms.length\n"
    "      invariant order = orderFold (orderTerms.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let t := orderTerms[i - 1]!\n"
    "      order := (if t.isRef then [] else t.cols) ++ order\n"
    "      i := i - 1\n"
    "    -- The ordering terms widen the grouping set only when the ordering is\n"
    "    -- explicit; a default-ordering-derived ordering contributes nothing.\n"
    "    let orderContrib : List Int := if metaOrdering then [] else order\n"
    "    return baseCols ++ selectCols ++ orderContrib ++ havingCols\n"
    "    -- impl-end"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: groupingColumns body not verbatim"

# ---- the impl-start marker (for admissibility: prepend an in-region assert
# ---- while keeping the whole gold body, so the method's own obligation still
# ---- discharges). Unique in the file.
_IMPL_START = "    -- impl-start\n"

# ---- the loop-body contribution line (for the branch/localvar reshape
# ---- positives). Unique in the file.
_LOOP_STEP = (
    "      let t := orderTerms[i - 1]!\n"
    "      order := (if t.isRef then [] else t.cols) ++ order\n"
    "      i := i - 1\n"
)
assert _BASE.count(_LOOP_STEP) == 1, "loop-step anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a positive that reshapes the impl or an admissibility case that adds an
# ---- in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). Unique in the file.
_PROOF_GOLD = (
    "prove_correct groupingColumns by\n"
    "  loom_solve\n"
    "  · rw [orderFold_drop_step orderTerms i (by omega) (by omega)]\n"
    "    simp_all\n"
    "  all_goals simp_all [groupingSet]"
)
assert _PROOF_GOLD in _BASE, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `groupingColumnsTester b s o h m = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. Every argument is a concrete literal
# ---- so `decide` reduces the (loop-free) extracted rival program; against gold
# ---- the extracted loop program does not reduce, so `decide` stays stuck and
# ---- the witness FAILS — the discrimination half.
_TESTER = (
    "extract_program_for groupingColumns\n"
    "prove_precondition_decidable_for groupingColumns\n"
    "prove_postcondition_decidable_for groupingColumns\n"
    "derive_tester_for groupingColumns\n\n"
)


def _witness(b, s, o, h, m):
    return _TESTER + (
        f"example : groupingColumnsTester {b} {s} {o} {h} {m} = false := by\n"
        "  decide\n"
    )


# A concrete OrderTerm literal.
def _T(cols, is_ref):
    return "{cols := %s, isRef := %s}" % (cols, "true" if is_ref else "false")


# ---- THE WITNESS SUBJECT. Gold cannot serve (its extracted `while` loop is a
# ---- kernel-irreducible `forIn Lean.Loop.mk` fixpoint, so `decide` is stuck for
# ---- every claim — see the CARRIER NOTE). This is the loop-free correct impl the
# ---- reject lane is refuted against instead: it shares the frozen spec
# ---- byte-for-byte, it VERIFIES (the gate re-checks both before using it), and
# ---- it REDUCES, so the refutation is genuinely decided. It is the same source
# ---- shipped as the `pos-direct-model` positive below, which is what records
# ---- that loop-freeness is not the property any rival is rejected for.
_LOOPFREE = _swap(
    _swap(
        _BASE, _IMPL_GOLD,
        "    -- impl-start\n"
        "    return groupingSet baseCols selectCols orderTerms havingCols metaOrdering\n"
        "    -- impl-end"),
    _PROOF_GOLD,
    "prove_correct groupingColumns by\n"
    "  loom_solve\n"
    "  all_goals simp_all [groupingSet]")


# Closed-form rival body: gold's `orderContrib` guard kept verbatim (so C2's
# metaOrdering gate is respected unless the rival specifically attacks it), with
# the loop removed — the ordering contribution written as a single expression.
def _closed(order_expr, ret_expr):
    return _swap(
        _BASE, _IMPL_GOLD,
        "    -- impl-start\n"
        f"    let orderContrib : List Int := {order_expr}\n"
        f"    return {ret_expr}\n"
        "    -- impl-end",
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation with a byte-identical header;
    # the tactic body is retuned only as the reshaped impl requires.
    # =====================================================================
    {
        "id": "pos-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Negate-and-swap the per-entry skip inside the loop:
        # `if t.isRef then [] else t.cols`  ->  `if !t.isRef then t.cols else []`.
        # Semantically identical contribution; the loop invariant is unchanged.
        # The proof gains a `cases … .isRef` split to line the two branch shapes
        # up. (Faithful port of the sibling's pos-branch-reshape.)
        "module": _swap(
            _swap(
                _BASE, _LOOP_STEP,
                "      let t := orderTerms[i - 1]!\n"
                "      order := (if !t.isRef then t.cols else []) ++ order\n"
                "      i := i - 1\n"),
            _PROOF_GOLD,
            "prove_correct groupingColumns by\n"
            "  loom_solve\n"
            "  · rw [orderFold_drop_step orderTerms i (by omega) (by omega)]\n"
            "    cases (orderTerms[i-1]!).isRef <;> simp_all\n"
            "  all_goals simp_all [groupingSet]"),
        "rationale": "structurally-different but CORRECT impl (negate-and-swap "
                     "the per-entry reference skip inside the loop) keeping the "
                     "loop invariant; `orderContrib` and the concatenation are "
                     "unchanged, so both ensures clauses still hold. Must verify, "
                     "else SPEC-TOO-STRONG on branch shape.",
    },
    {
        "id": "pos-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Route the per-entry contribution through a fresh local `contribution`
        # instead of inlining it into the prepend. Pure structural reshape; the
        # value flow and invariant are identical, so the frozen proof still
        # closes unchanged. (Faithful port of the sibling's pos-localvar-reshape.)
        "module": _swap(
            _BASE, _LOOP_STEP,
            "      let t := orderTerms[i - 1]!\n"
            "      let contribution := if t.isRef then [] else t.cols\n"
            "      order := contribution ++ order\n"
            "      i := i - 1\n"),
        "rationale": "reshape: bind the per-entry contribution to a fresh local "
                     "and prepend it, rather than inlining the conditional. Pure "
                     "structural reshape; value flow and loop invariant intact, "
                     "so the post-image is unchanged and the frozen proof closes. "
                     "Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold scan.
        # `out` IS `groupingSet …`, so C1 holds definitionally and C2 follows.
        # The honest no-ungrounded-echo control too: the model IS the real work
        # (a spelled-out fold + guard), so a direct return is correct, not a
        # cheat.
        # Same source as `_LOOPFREE`, the subject every reject witness is
        # refuted against: shipping it as a positive is what machine-checks
        # that the subject VERIFIES, i.e. that no rival is being rejected
        # merely for being loop-free.
        "module": _LOOPFREE,
        "rationale": "the grounded model `groupingSet …` returned directly (no "
                     "loop) is the cheapest correct impl; `out` IS that model, so "
                     "C1 holds on the whole domain and C2 follows. If this fails "
                     "the spec is over-fit to the scan code shape "
                     "(SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the sibling's "a
    # normal input satisfies the precondition" probe cannot be ported as-is
    # (nothing could exclude an input). But "no precondition" is NOT a reason to
    # drop the lane: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
    # obligation being UNSATISFIABLE at exactly an F2P-shaped input — two ensures
    # clauses that cannot both hold there, which no impl could then discharge and
    # which reads from the outside exactly like a spec every impl meets. This case
    # discharges TWO in-region `assert`s, at fully concrete literals, by
    # evaluation, before the frozen obligation closes verbatim:
    #
    #   `admiss`     — NON-DEGENERACY on the discriminating axis: for a genuine
    #                  ordering term the grouping set under a default ordering
    #                  (metaOrdering = true) DIFFERS from the one under an
    #                  explicit ordering (metaOrdering = false). A post-image that
    #                  did not separate those two points would let the whole
    #                  guard collapse without any rival noticing.
    #   `admissF2P`  — JOINT SATISFIABILITY at the F2P-shaped point itself: at a
    #                  default ordering carrying a genuine ordering term, with all
    #                  three other contributions non-empty, clause C1's value
    #                  (`groupingSet …`) is EQUAL to the value clause C2 demands
    #                  (`baseCols ++ selectCols ++ havingCols`). The two clauses
    #                  are independent, so this is the thing that could actually
    #                  be unsatisfiable; asserting it at literals is what shows
    #                  the obligation is dischargeable exactly where the behaviour
    #                  under repair lives, rather than only away from it.
    #
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the two assert goals.
    # Both asserts are LIVE, not decoration — each was rebuilt with its own claim
    # flipped and each flip left an unsolved goal (`orderFold [{cols := [7],
    # isRef := false}] = []` and `False` respectively), so neither is discharged
    # by the surrounding context.
    # =====================================================================
    {
        "id": "admiss-guard-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_START,
                _IMPL_START +
                "    assert (with_name_prefix `admiss (\n"
                "      groupingSet [] [] [" + _T("[(7:Int)]", False) + "] [] true\n"
                "        ≠ groupingSet [] [] [" + _T("[(7:Int)]", False) + "] [] false))\n"
                "    assert (with_name_prefix `admissF2P (\n"
                "      groupingSet [(1:Int)] [(2:Int)] ["
                + _T("[(7:Int)]", False) + "] [(9:Int)] true\n"
                "        = [(1:Int)] ++ [(2:Int)] ++ [(9:Int)]))\n"),
            _PROOF_GOLD,
            "prove_correct groupingColumns by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (rw [orderFold_drop_step orderTerms i (by omega) (by omega)]; simp_all)\n"
            "    | decide\n"
            "    | simp_all [groupingSet]"),
        "rationale": "the obligation is SATISFIABLE at an F2P-shaped input and "
                     "NON-DEGENERATE on the discriminating axis. `admissF2P` "
                     "discharges, by evaluation at literals, that at a default "
                     "ordering carrying a genuine ordering term (all three other "
                     "contributions non-empty) clause C1's value coincides with "
                     "the value C2 demands — the two independent clauses can "
                     "jointly hold exactly where the behaviour under repair "
                     "lives, so no impl is excluded there (the total-carrier "
                     "analogue of PRECOND-TOO-STRONG). `admiss` discharges that "
                     "the grouping set under a default ordering differs from the "
                     "one under an explicit ordering for a genuine term, so the "
                     "post-image genuinely separates the two branches rather "
                     "than being met vacuously. Both asserts are live: flipping "
                     "either claim leaves an unsolved goal. The impl is kept "
                     "verbatim so `out = groupingSet …` still verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each rival is a LOOP-FREE closed
    # form so its extracted tester `decide`s (see the CARRIER NOTE); the frozen
    # proof — tuned to the loop — fails to close, which is the rejection.
    # =====================================================================
    {
        "id": "uncond-fold-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE canonical discriminator: fold the ordering contribution
        # UNCONDITIONALLY, ignoring metaOrdering (the pre-patch behaviour). Right
        # on the explicit-ordering sub-domain (metaOrdering = false), wrong on the
        # default-ordering sub-domain, where a genuine ordering term leaks its
        # columns into the grouping set.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    -- impl-start\n"
            "    return baseCols ++ selectCols ++ orderFold orderTerms ++ havingCols\n"
            "    -- impl-end"),
        "refinement": "this is the pre-patch behaviour: the ordering contribution "
                      "is folded in regardless of whether the ordering was "
                      "explicit. For a default ordering (the failing scenario) a "
                      "genuine ordering column leaks into the grouping set and "
                      "splits the aggregation into spurious groups — the exact "
                      "wrong aggregation the fix removes. The faithful counterpart "
                      "does NOT resolve.",
        "rationale": "REJECT from C2 (metaOrdering = true → out = baseCols ++ "
                     "selectCols ++ havingCols): the rival ignores metaOrdering "
                     "and folds the ordering columns in even for a default "
                     "ordering. Refuted at metaOrdering = true with one genuine "
                     "ordering term — the only witness that moves metaOrdering to "
                     "true.",
        "witness": _witness("[]", "[]", "[" + _T("[(7:Int)]", False) + "]", "[]", "true"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "guard-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the metaOrdering guard: fold the ordering columns EXACTLY when
        # the ordering is default (metaOrdering = true) and drop them exactly when
        # it is explicit (metaOrdering = false). Violates C2 (default -> tokens
        # added) AND C1 on the explicit sub-domain (explicit -> tokens dropped),
        # whenever a genuine ordering term is present.
        "module": _closed(
            "if metaOrdering then orderFold orderTerms else []",
            "baseCols ++ selectCols ++ orderContrib ++ havingCols"),
        "refinement": "inverts the added guard, so a default ordering STILL leaks "
                      "its columns (fails the failing scenario) and an explicit "
                      "ordering DROPS its columns (breaks the explicit-ordering "
                      "aggregation the PASS_TO_PASS cases exercise). Resolves "
                      "nothing.",
        "rationale": "REJECT from C1: the ordering contribution is gated on the "
                     "wrong polarity of metaOrdering. Refuted at "
                     "metaOrdering = false with one genuine ordering term, where "
                     "the post-image folds the term's columns in and the rival "
                     "drops them.",
        "witness": _witness("[(1:Int)]", "[(2:Int)]",
                            "[" + _T("[(7:Int)]", False) + "]", "[(9:Int)]", "false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-backref-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Append EVERY ordering term's columns regardless of its reference flag
        # (drop the back-reference skip). Correct only when no term is a
        # back-reference; wrong as soon as one term has isRef = true — a
        # back-reference term points at a column already selected, so re-adding it
        # widens the grouping set with a duplicate contribution the fold drops.
        "module": _closed(
            "if metaOrdering then [] else orderTerms.flatMap (fun t => t.cols)",
            "baseCols ++ selectCols ++ orderContrib ++ havingCols"),
        "refinement": "drops the reference skip; a back-reference ordering term "
                      "points at a column already in the SELECT/GROUP BY, so "
                      "re-adding its columns yields a wrong (extra) grouping "
                      "contribution. The explicit-ordering aggregation cases and "
                      "the failing scenario do not resolve.",
        "rationale": "REJECT from C1 (out = groupingSet …, whose orderFold pins a "
                     "reference term's contribution to []): the rival appends "
                     "every term's columns. Refuted at an explicit ordering "
                     "(metaOrdering = false) with one back-reference term "
                     "(isRef = true) — the only witness that carries a "
                     "back-reference term.",
        "witness": _witness("[(1:Int)]", "[(2:Int)]",
                            "[" + _T("[(7:Int)]", True) + "]", "[(9:Int)]", "false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "invert-backref-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep ONLY back-reference terms and drop the genuine ones — the exact
        # opposite of the reference skip. Appends the columns the fold drops and
        # drops the columns it keeps; wrong whenever the two classes differ.
        "module": _closed(
            "if metaOrdering then [] else orderTerms.flatMap (fun t => if t.isRef then t.cols else [])",
            "baseCols ++ selectCols ++ orderContrib ++ havingCols"),
        "refinement": "keeps exactly the back-reference ordering columns (already "
                      "grouped) and drops the genuine ones — the opposite of the "
                      "reference skip. Wrong grouping set for every ordering case; "
                      "resolves nothing.",
        "rationale": "REJECT from C1: the rival appends the terms orderFold drops "
                     "and drops the ones it keeps. Refuted at an explicit ordering "
                     "(metaOrdering = false) with one genuine term "
                     "(isRef = false), where the post-image folds its columns in "
                     "and the rival emits nothing.",
        "witness": _witness("[]", "[]", "[" + _T("[(7:Int)]", False) + "]", "[]", "false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-base-contribution",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the grouping-base contribution from the assembled list. Abuses the
        # `baseCols` free input — the only rival that does, so it is what moves
        # `baseCols` off the empty value the other witnesses hold it at.
        "module": _closed(
            "if metaOrdering then [] else orderFold orderTerms",
            "selectCols ++ orderContrib ++ havingCols"),
        "refinement": "a counterpart that omits the grouping base emits a grouping "
                      "set missing the base columns the query must group by, so "
                      "the produced SQL groups on the wrong set of columns and the "
                      "aggregation is wrong. It would NOT resolve.",
        "rationale": "REJECT from C1 (out = groupingSet …, which prepends "
                     "`baseCols`): the impl omits it. Refuted at baseCols = [4] "
                     "(all other inputs empty) — the only witness that moves the "
                     "baseCols binder off the empty value.",
        "witness": _witness("[(4:Int)]", "[]", "[]", "[]", "false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-select-contribution",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the selected-columns contribution. Abuses the `selectCols` free
        # input — the only rival that moves it off empty.
        "module": _closed(
            "if metaOrdering then [] else orderFold orderTerms",
            "baseCols ++ orderContrib ++ havingCols"),
        "refinement": "a counterpart that omits the selected columns drops columns "
                      "the SELECT clause requires in the grouping set, so the "
                      "aggregation groups on too few columns and is wrong. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C1 (which includes `selectCols`): the impl omits "
                     "it. Refuted at selectCols = [5] (all other inputs empty) — "
                     "the only witness that moves the selectCols binder off the "
                     "empty value.",
        "witness": _witness("[]", "[(5:Int)]", "[]", "[]", "false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-having-contribution",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the filter (having) contribution. Abuses the `havingCols` free
        # input — the only rival that moves it off empty. Its witness also holds
        # metaOrdering = true, so the C2 clause (which retains havingCols) is what
        # exposes the drop even on the default-ordering branch.
        "module": _closed(
            "if metaOrdering then [] else orderFold orderTerms",
            "baseCols ++ selectCols ++ orderContrib"),
        "refinement": "a counterpart that omits the filter columns drops columns "
                      "the row-filtering predicate requires in the grouping set, "
                      "so the aggregation is wrong. It would NOT resolve.",
        "rationale": "REJECT from C1 and C2 (both retain `havingCols`): the impl "
                     "omits it. Refuted at havingCols = [8] under a default "
                     "ordering (metaOrdering = true), where C2 pins out = baseCols "
                     "++ selectCols ++ havingCols and the rival drops the having "
                     "term — the only witness that moves the havingCols binder off "
                     "empty.",
        "witness": _witness("[]", "[]", "[]", "[(8:Int)]", "true"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 4 partial-domain rivals) over a
# single contracted function `assemble_grouping_key` with four read-only list
# inputs held at fractional permission. This bundle contracts a single method
# `groupingColumns` over FIVE read-only inputs (the sibling's select/order/
# order_is_backref/trailing plus an explicit grouping base), so the sibling's
# cases re-aim onto the corresponding clause of the one post-image here.
#
#   sibling case                       -> here                          disposition
#   ----------------------------------------------------------------------------
#   pos-branch-reshape                 -> pos-branch-reshape             PORTED
#   pos-localvar-reshape               -> pos-localvar-reshape           PORTED
#   admiss-f2p-shaped                  -> admiss-guard-nondegenerate     RE-AIMED
#   frame-mutation-trailing-write      -> (none)                        VACUOUS
#   uncond-fold-prepatch               -> uncond-fold-prepatch           PORTED
#   guard-inverted                     -> guard-inverted                 PORTED
#   drop-backref-skip                  -> drop-backref-skip              PORTED
#   invert-backref-skip                -> invert-backref-skip            PORTED
#
# 6 ported, 1 re-aimed, 1 vacuous. Plus 3 ADDED for binder coverage (below).
#
# RE-AIMED (admissibility): the sibling establishes that the four read-only
#   half-permission inputs are usable at 1/2 and a normal return is reachable.
#   This backend has no permissions and no `require` clause, so that exact probe
#   cannot be ported. The lane is NOT dropped: the analogue on a total carrier is
#   the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which the
#   case tests directly by discharging, at concrete literals and by evaluation,
#   that clause C1's value there EQUALS the value clause C2 demands (the
#   `admissF2P` assert) — the two clauses are independent, so that is the thing
#   that could actually fail. Paired with a NON-DEGENERACY assert (`admiss`) that
#   the grouping set under a default ordering differs from the one under an
#   explicit ordering for a genuine term, so the post-image separates the two
#   branches rather than being met vacuously. Both asserts were rebuilt with
#   their claims flipped and both flips FAILED (unsolved goals), so neither is
#   decoration. Also subsumes the sibling's third positive role: pos-direct-model
#   is the honest no-ungrounded-echo control (the model is the real work, so
#   returning it is correct, not a cheat).
# VACUOUS (frame-mutation-trailing-write): the sibling writes into a read-only
#   half-permission input to trip INSUFFICIENT PERMISSION. This backend is
#   referentially transparent, has no heap or aliasing, and this bundle declares
#   NO `mut` binder. DEMONSTRATED rather than asserted: splicing `baseCols :=
#   baseCols` into the impl region does not produce a spec rejection at all, it
#   fails to ELABORATE — "`baseCols` cannot be mutated, only variables declared
#   using `let mut` can be mutated". A module that does not elaborate cannot carry
#   a discriminating witness (no witness can hold of it), so the class is
#   inexpressible here, not merely hard. Not fabricated. (mapping.md's read-only
#   discipline is discharged here by the absence of `mut`.)
# DIVERGENCE lane - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# ADDED (3, binder coverage — no sibling counterpart because the sibling attacks
#   its select_cols / trailing_cols contributions ONLY via the frame-mutation
#   case, which is vacuous here): drop-base-contribution, drop-select-contribution,
#   drop-having-contribution. Without these, the baseCols / selectCols /
#   havingCols binders would never be moved off the empty value, and a rival that
#   dropped one of those contributions would verify uncaught. Each carries a
#   machine-checked witness at the input that moves its binder, and each faithful
#   counterpart (a grouping set missing a required contribution) leaves the
#   aggregation grouping on the wrong column set, so it does not resolve.
#
# COVERAGE. Binders moved by the reject witnesses: metaOrdering {true, false};
#   orderTerms carries both a back-reference term (isRef=true, drop-backref-skip)
#   and a genuine term (isRef=false, several); baseCols {[], [4]}; selectCols
#   {[], [5]}; havingCols {[], [8]}. All five binders varied; pts = 7 distinct
#   input points. Independent clauses attacked: C1 (the total post-image —
#   guard-inverted, both backref rivals, all three drop rivals) and C2 (the
#   discriminating default-ordering clause — uncond-fold-prepatch, and
#   drop-having-contribution which is refuted on the C2 branch).
#
# INDEPENDENT PROBES (audit, machine-checked with the real verifier; none is
#   shipped as a case because each behaved as the spec requires). Exit codes below
#   are the ones actually observed.
#
#   ELEVEN NEW WRONG impls beyond the rivals above, aimed at the axes no shipped
#   rival attacks — concatenation ORDER, MULTIPLICITY, term SUBSETTING, and
#   near-miss GUARD conditions. All eleven were REJECTED (exit 1):
#     multiplicity  — duplicate the filter contribution (`… ++ havingCols ++
#                     havingCols`); de-duplicate the whole result (`.eraseDups`)
#     order         — swap the base and selected contributions; place the ordering
#                     contribution before the selected one; reverse the ordering
#                     contribution; permute the filter contribution ahead of it
#     subsetting    — keep only the first ordering column (`.take 1`); drop the
#                     last ordering term (`.dropLast`); reverse the term list;
#                     keep only the first term (`.take 1`)
#     near-miss     — narrow the guard to fire only for 2+ ordering terms; gate on
#       guards       the terms' own reference flags instead of `metaOrdering`; gate
#                     additionally on the filter contribution being empty
#   The two near-miss guard rivals are the sharpest of these: each is correct on
#   most of the domain and wrong only at the F2P-shaped point, and each was still
#   rejected with an unsolved goal naming the guard (`metaOrdering = true →
#   orderTerms.length < 2 → orderFold orderTerms = []`). So the post-image pins
#   contribution order, multiplicity, the whole term list, and the guard's exact
#   condition — not merely the column set. NO spec hole was found on any of them.
#
#   FOUR NEW CORRECT reshapes were probed and all four VERIFY (exit 0):
#   re-associate the concatenation; write the guard with the negated test
#   (`if !metaOrdering then orderFold … else []`); guard additionally on the term
#   list being non-empty (a redundant conjunct, since an empty list folds to `[]`);
#   and compute the contribution as `(orderTerms.filter (fun t => !t.isRef)).flatMap
#   (·.cols)`. The last three need the tactic body retuned (a `cases metaOrdering`,
#   a `cases orderTerms`, and for the filter reshape an inline `have` proving
#   filter-then-flatMap equals `orderFold` by induction — a `have`, not a new
#   top-level lemma, so variant scope is preserved). That is proof-shape work, NOT
#   the spec rejecting a faithful impl, so there is no SPEC-TOO-STRONG finding.
#
#   NOTE the one genuine limit, re-measured: `baseCols ++ selectCols ++ havingCols
#   ++ orderContrib` (a permutation) and `(…).eraseDups` (de-duplication) are both
#   FAITHFUL under mapping.md §2, which says the result's order and duplicates are
#   not observable (GROUP BY is a set), yet both are REJECTED by C1, which pins the
#   concatenation as a list. Their failures are on the value clause itself
#   (`(havingCols ++ if … ) = (if … ) ++ havingCols`), not on a tactic gap. The
#   spec is thus stricter than the documented observable. This is a deliberate,
#   sound over-specification — it rejects strictly more wrong impls and the gold
#   impl satisfies it — not a soundness hole: it can never admit a wrong impl.
#   Recorded here so the next reader does not mistake it for one.
#
# WHY THE REJECT LANE USES A `witness_reference`, RE-MEASURED. The CARRIER NOTE's
#   claim was re-derived from scratch rather than taken on trust, with the
#   forgery experiment the audit protocol requires. For every one of the seven
#   reject cases, three builds: the witness against the rival (exit 0), against
#   the reference subject (exit 1, `Tactic 'decide' proved that the proposition
#   groupingColumnsTester … = false is false` — a real verdict naming the case's
#   own input), and the FLIPPED claim (`… = true`) against that same subject
#   (exit 0). The reference-side error therefore TRACKS the claim: flipping what
#   is asserted flips the exit code, which is exactly what makes it admissible
#   evidence. Against the FROZEN impl, by contrast, the witness and its flipped
#   twin both fail with the byte-identical `did not reduce to isTrue or isFalse`,
#   and so does an all-empty input at which the loop runs ZERO iterations — so
#   gold's exit code carries no information about any claim, and gold could not
#   have served as the subject. Each witness was additionally checked to FAIL at
#   an agreement point (all-empty inputs, exit 1 against three of the rivals),
#   confirming it is the case's specific input doing the discriminating and not
#   a claim true of the rival everywhere.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the ordering decision is modeled deeply — orderFold + the groupingSet
#   guard — so the per-term column-list callee is a G-AX A-reference, not a
#   consumed contract), so there is nothing here for this gate to probe.
AXIOM_TESTS = []
