"""properties.py — G-PBT falsification battery for django__django-16819 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method combining an index-addition with the
operation that immediately follows it in a plan:

  reduceAddIndex (addedName : List Char) (next : NextOp)
                 (inheritedOutcome : Reduction)
      ensures out =
        (if removesAddedIndex addedName next then Reduction.cancel
         else inheritedOutcome)

The carrier narrows the nagini surface hard, and the narrowing is what fixes
which nagini cases have a counterpart here:

  * ``removesAddedIndex addedName next`` FOLDS nagini's two separate guard
    conjuncts into ONE decidable predicate over the input carrier: the
    "following op is a removal" conjunct becomes the ``NextOp`` constructor
    (``removesIndex name`` vs ``other``), and the "names match" conjunct becomes
    ``name = addedName`` inside that constructor. So the guard is transparent and
    fully attackable — but a distinction it does not carry cannot be attacked
    (see the accounting footer).
  * ``inheritedOutcome`` is a FREE, opaque input: the ordinary reduction decision
    for every non-cancelling pairing is handed in and the spec makes no claim
    about its value (it holds for every ``Reduction``). The single load-bearing
    correction is that the two operations ANNIHILATE (``cancel``) exactly when the
    following operation removes the very index just added, and DEFER to the
    ordinary decision otherwise. There is no answer-key here to echo: the cancel
    branch is the concrete constructor ``cancel`` and the defer branch is the
    input value itself.

ADVERSARIAL READ of the nagini classes (see footer for the full accounting):
  * FRAME-MUTATION — VACUOUS. The class exists on nagini because a read-only
    input may carry a fractional heap permission an impl can overwrite. Lean and
    Velvet are referentially transparent: every parameter is an immutable value
    (no ``mut`` binder here), there is no heap and no aliasing, so there is no
    read-only input to mutate and no substitute probe to build. Reported, not
    fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own inputs (``removesAddedIndex`` is a concrete
    ``def``; the ``axioms`` region declares nothing; the defer value is the free
    input itself). There is no opaque answer key to echo, so the nagini
    ``pos-master-assert`` echo control has nothing to demonstrate as a
    reject/positive PAIR. Its honest half is nonetheless carried here as
    ``pos-echo-both-arms``: an impl that asserts, on each arm, that the value it
    returns equals the post-image at that point, which must verify.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PARTIAL-DOMAIN / VALUE — APPLIES and gets the coverage: rivals right on part
    of the domain but diverging on a sub-domain (annihilate never / annihilate
    too broadly / discard the deferred decision). Each is refuted at a concrete
    point that varies the three input binders across the removal / non-removal,
    matching-name / mismatching-name, and default / non-default deferred-outcome
    boundaries, so no binder is pinned across the battery.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the ordinary
inherited decision is an unchanged free input owed no contract). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16819"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl body (the if/else the variants replace). It is a single
# ---- contiguous block wholly inside the one `-- impl-start` / `-- impl-end`
# ---- region and unique in Solution.lean (the multi-line `return` shape occurs
# ---- nowhere else — the `ensures` states the same decision on ONE line with no
# ---- `return`); both facts are asserted at load by _swap. -----------------
_GOLD_IMPL = (
    "    if removesAddedIndex addedName next then\n"
    "      return Reduction.cancel\n"
    "    else\n"
    "      return inheritedOutcome\n"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# The frozen proof body (the `prove_correct` tactic script). Elided from the
# consumer spec view, so a variant that reshapes the impl (and thus the goal
# `loom_solve` faces) may retune it — the obligation STATEMENT and the
# `prove_correct` header are untouched, so same_spec still holds. Anchored on the
# exact frozen script.
_GOLD_PROOF = "prove_correct reduceAddIndex by\n  loom_solve"


def _impl(body):
    """Full Solution.lean variant: replace the gold impl body only."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl body AND retune the `prove_correct` tactic script."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `reduceAddIndexTester addedName next inheritedOutcome = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. `Reduction`/`NextOp`
# ---- both derive DecidableEq, so every witness closes by `decide`.
def _tester():
    m = "reduceAddIndex"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. This
    # dispatches on the following-operation's SHAPE first (the two `NextOp`
    # constructors) and does a NESTED name check, instead of the frozen single
    # `if removesAddedIndex …`. Observationally identical on every input, but a
    # different source shape whose goal the frozen `loom_solve` does not close on
    # its own — so the tactic script is retuned (the obligation statement and
    # header are byte-identical). Ports nagini `pos-reshape`.
    # =====================================================================
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    match next with\n"
            "    | NextOp.removesIndex name =>\n"
            "      if name = addedName then\n"
            "        return Reduction.cancel\n"
            "      else\n"
            "        return inheritedOutcome\n"
            "    | NextOp.other =>\n"
            "      return inheritedOutcome\n",
            "prove_correct reduceAddIndex by\n"
            "  loom_solve <;> simp_all [removesAddedIndex]"),
        "rationale": "structurally-different but correct: dispatches on the "
                     "following operation's shape (the two NextOp constructors) "
                     "with a nested name-equality check instead of the single "
                     "folded guard, returning the identical outcome on every "
                     "input. No loop/induction is introduced (each branch is a "
                     "direct constructor/equality read pinned by the single "
                     "clause), so the retuned `loom_solve <;> "
                     "simp_all [removesAddedIndex]` discharges the reshaped goal. "
                     "If it fails => the post-image is over-fit to the exact "
                     "frozen guard shape => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous. Re-aimed (as on
    # django__django-16493) at the residual admissibility risk on a total
    # domain: that the post-image is UNSATISFIABLE / degenerate at the F2P
    # corner. This keeps the gold impl verbatim (so the method's own obligation
    # still discharges) and adds an in-region `assert` pinning the post-image at
    # the decisive point — the following operation removes the very index just
    # added (a matching removal), where it must demand ANNIHILATION (`cancel`),
    # not the ordinary deferred decision. The assert is live, not decoration: a
    # false claim about that point leaves an unsolved goal. Ports nagini
    # `admiss-fshape`.
    # =====================================================================
    {
        "id": "admiss-f2p-cancels-matching-removal",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      ((if removesAddedIndex \"idx\".toList "
            "(NextOp.removesIndex \"idx\".toList)\n"
            "        then Reduction.cancel else (Reduction.inherited 0))\n"
            "       = Reduction.cancel))\n" + _GOLD_IMPL,
            "prove_correct reduceAddIndex by\n  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P corner: when the following operation removes the very "
                     "index just added (a matching removal), the guard fires and "
                     "the post-image demands `cancel`, NOT the ordinary deferred "
                     "decision. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable/degenerate at that point => "
                     "PRECOND-TOO-STRONG); the impl is verbatim so the equality "
                     "clause still discharges too.",
    },

    # =====================================================================
    # ECHO CONTROL (honest half) — the nagini `pos-master-assert` counterpart.
    # The post-image names no opaque answer key, so there is no wrong echo to
    # build as a reject case; what CAN be demonstrated is that the cheapest impl
    # satisfying the pins still computes them. On each arm this asserts that the
    # value it is about to return equals the post-image AT THAT POINT (`cancel`
    # under the fired guard; the deferred `inheritedOutcome` otherwise). Both
    # asserts are live goals, so it must verify. Ports the honest half of nagini
    # `pos-master-assert`.
    # =====================================================================
    {
        "id": "pos-echo-both-arms",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    if removesAddedIndex addedName next then\n"
            "      assert (with_name_prefix `assert\n"
            "        ((if removesAddedIndex addedName next then Reduction.cancel\n"
            "          else inheritedOutcome) = Reduction.cancel))\n"
            "      return Reduction.cancel\n"
            "    else\n"
            "      assert (with_name_prefix `assert\n"
            "        ((if removesAddedIndex addedName next then Reduction.cancel\n"
            "          else inheritedOutcome) = inheritedOutcome))\n"
            "      return inheritedOutcome\n",
            "prove_correct reduceAddIndex by\n"
            "  loom_solve <;> simp_all [removesAddedIndex]"),
        "rationale": "no-echo demonstration: the two outcome oracles are GROUNDED "
                     "in the method's own inputs (`removesAddedIndex` is a "
                     "concrete `def`; the defer value is the input itself), so "
                     "the cheapest impl satisfying the pins still computes them. "
                     "Each arm asserts that the value it returns equals the "
                     "post-image at that point, and both asserts are live goals "
                     "(a false one leaves an unsolved goal — measured: flipping "
                     "either arm's claim fails with `decide proved ... is "
                     "false`). It must verify; if it fails => the post-image "
                     "cannot be met by an impl that reasons about it => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. The witnesses vary all
    # three binders: `addedName` over "idx"/"abc", `next` over
    # `removesIndex "idx"` / `removesIndex "xyz"` / `other`, and
    # `inheritedOutcome` over `inherited 0` / `inherited 7`.
    # =====================================================================
    {
        "id": "drop-cancellation",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug. Never annihilates: always defers to the ordinary
        # inherited decision, even when the following operation removes the very
        # index just added. Correct on the whole non-cancelling sub-domain,
        # WRONG on every matching removal.
        "module": _impl("    return inheritedOutcome\n"),
        "refinement": "this is the pre-image: the index-addition had NO "
                      "combination rule against the following operation, so the "
                      "outcome was ALWAYS the ordinary inherited decision. For "
                      "the failing test — an index added and then the same index "
                      "removed — the ordinary decision does NOT annihilate the "
                      "pair, so it is not optimised away and the test still "
                      "fails. It would NOT resolve (this is exactly the "
                      "regression the change fixes).",
        "rationale": "REJECT from the `then` arm of the clause: with a matching "
                     "removal following (`next = removesIndex addedName`) the "
                     "post-image demands `cancel`, but the rival returns the "
                     "deferred `inheritedOutcome`. Refuted at "
                     "`next = removesIndex \"idx\"`, `addedName = \"idx\"`, "
                     "`inheritedOutcome = inherited 0`. If it verified => "
                     "SPEC-TOO-WEAK (admits the bug).",
        "witness": _tester() +
                   "example : reduceAddIndexTester \"idx\".toList "
                   "(NextOp.removesIndex \"idx\".toList) (Reduction.inherited 0) "
                   "= false := by\n  decide\n",
    },
    {
        "id": "cancel-any-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # Annihilates on ANY following index-removal, dropping the name-match
        # requirement (the `name = addedName` half of the folded guard). Correct
        # when the names DO match (or the following op is not a removal), WRONG on
        # a removal of a DIFFERENT-named index. Ports nagini `guard-drop-nameeq`.
        "module": _impl(
            "    match next with\n"
            "    | NextOp.removesIndex _ => return Reduction.cancel\n"
            "    | NextOp.other => return inheritedOutcome\n"),
        "refinement": "annihilating on any following index-removal regardless of "
                      "name drops an index addition against a removal of an "
                      "UNRELATED, differently-named index — losing an index the "
                      "plan genuinely needs. Existing optimizer tests that "
                      "combine independent index operations then observe the "
                      "wrong plan, so it would NOT resolve.",
        "rationale": "REJECT from the `else` arm: when the following op removes a "
                     "DIFFERENT index (`removesAddedIndex` is false because the "
                     "names differ) the post-image demands the deferred "
                     "`inheritedOutcome`, but the rival returns `cancel`. Refuted "
                     "at `next = removesIndex \"xyz\"`, `addedName = \"abc\"`, "
                     "`inheritedOutcome = inherited 0` — a mismatching-name point "
                     "where drop-cancellation agrees with gold. If it verified => "
                     "SPEC-TOO-WEAK (annihilation over-broad on the name).",
        "witness": _tester() +
                   "example : reduceAddIndexTester \"abc\".toList "
                   "(NextOp.removesIndex \"xyz\".toList) (Reduction.inherited 0) "
                   "= false := by\n  decide\n",
    },
    {
        "id": "cancel-on-non-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # Annihilates even when the following op is NOT a removal (the `other`
        # sub-domain), dropping the shape requirement of the folded guard.
        # Correct on both removal sub-cases, WRONG on every non-removal
        # follow-up. Covers the `next = other` value of the binder and attacks
        # the `else` arm on the complementary (non-removal) sub-domain.
        "module": _impl(
            "    match next with\n"
            "    | NextOp.removesIndex name =>\n"
            "      if name = addedName then return Reduction.cancel\n"
            "      else return inheritedOutcome\n"
            "    | NextOp.other => return Reduction.cancel\n"),
        "refinement": "annihilating an index addition against a following "
                      "operation that is NOT an index-removal drops the addition "
                      "against an unrelated operation, corrupting the plan. "
                      "Existing optimizer tests that keep an index addition "
                      "ahead of an unrelated operation then observe it gone, so "
                      "it would NOT resolve.",
        "rationale": "REJECT from the `else` arm on the non-removal sub-domain: "
                     "when the following op is not a removal (`next = other`, so "
                     "`removesAddedIndex` is false) the post-image demands the "
                     "deferred `inheritedOutcome`, but the rival returns "
                     "`cancel`. Refuted at `next = other`, `addedName = \"idx\"`, "
                     "`inheritedOutcome = inherited 0` — a point where both "
                     "removal-based rivals agree with gold. If it verified => "
                     "SPEC-TOO-WEAK (annihilation over-broad on the shape).",
        "witness": _tester() +
                   "example : reduceAddIndexTester \"idx\".toList "
                   "NextOp.other (Reduction.inherited 0) "
                   "= false := by\n  decide\n",
    },
    {
        "id": "else-discards-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        # The annihilation decision is correct, but the NON-cancel branch returns
        # a fixed constant outcome instead of the ordinary inherited decision it
        # was handed. Right whenever the deferred decision happens to equal that
        # constant; WRONG on every other deferred value. The ONLY rival that
        # abuses the `inheritedOutcome` binder — without it that binder is one no
        # rival was built to move.
        "module": _impl(
            "    if removesAddedIndex addedName next then\n"
            "      return Reduction.cancel\n"
            "    else\n"
            "      return (Reduction.inherited 0)\n"),
        "refinement": "returning a fixed outcome in the non-cancel branch "
                      "discards the ordinary reduction decision the operation "
                      "must delegate to for every other pairing. The many "
                      "existing optimizer tests that rely on that ordinary "
                      "decision (field/model reductions, elidable-operation "
                      "handling) then observe the wrong result, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the `else` arm's dependence on the "
                     "`inheritedOutcome` binder: when the guard does not fire the "
                     "post-image demands exactly the deferred `inheritedOutcome`, "
                     "but the rival returns the constant `inherited 0`. Refuted "
                     "at `next = other`, `addedName = \"idx\"`, "
                     "`inheritedOutcome = inherited 7` — the deferred value the "
                     "rival ignores. If it verified => SPEC-TOO-WEAK (the "
                     "deferred outcome is unpinned).",
        "witness": _tester() +
                   "example : reduceAddIndexTester \"idx\".toList "
                   "NextOp.other (Reduction.inherited 7) "
                   "= false := by\n  decide\n",
    },
    {
        "id": "mistag-inherited-outcome",
        "kind": "uniqueness",
        "expect": "reject",
        # The nagini `swap-base-tags` counterpart. The annihilation decision is
        # correct and the non-cancel branch DOES consult the deferred decision —
        # it just hands back a DIFFERENT inherited outcome (the tag bumped by
        # one), so it is not the ordinary decision it was given. Distinct from
        # else-discards-inherited: that one ignores the binder outright, this one
        # reads it and mis-tags the result, which is the sub-domain a rival that
        # merely "uses" the input can still get wrong.
        "module": _impl(
            "    if removesAddedIndex addedName next then\n"
            "      return Reduction.cancel\n"
            "    else\n"
            "      match inheritedOutcome with\n"
            "      | Reduction.cancel => return Reduction.cancel\n"
            "      | Reduction.inherited t => return (Reduction.inherited (t + 1))\n"),
        "refinement": "transposing/renumbering the ordinary decision's outcome "
                      "returns a DIFFERENT reduction than the one the operation "
                      "was handed for every other pairing, so the optimizer keeps "
                      "the wrong thing wherever that ordinary decision is what "
                      "applies. The many existing optimizer tests that rely on "
                      "the unchanged ordinary decision then observe the wrong "
                      "plan, so it would NOT resolve.",
        "rationale": "REJECT from the `else` arm: the post-image demands EXACTLY "
                     "the deferred `inheritedOutcome`, and returning a "
                     "re-tagged inherited outcome is a different value of the "
                     "same carrier — this is why the `tag` keeps the non-cancel "
                     "outcomes an open, DISTINGUISHABLE domain rather than one "
                     "collapsed point. Refuted at `next = removesIndex \"xyz\"`, "
                     "`addedName = \"abc\"`, `inheritedOutcome = inherited 3` — a "
                     "mismatching-name removal, the `else` arm reached through "
                     "the REMOVAL constructor (the other three rivals reach it "
                     "via `other` or agree there). If it verified => "
                     "SPEC-TOO-WEAK (the deferred outcome is pinned only up to "
                     "re-tagging).",
        "witness": _tester() +
                   "example : reduceAddIndexTester \"abc\".toList "
                   "(NextOp.removesIndex \"xyz\".toList) (Reduction.inherited 3) "
                   "= false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 3 positive controls
# (pos-reshape, pos-master-assert, admiss-fshape) and 5 uniqueness rivals
# (frame-mutate-is-remove, frame-mutate-name, drop-cancellation,
# guard-drop-isremove, guard-drop-nameeq, swap-base-tags). The sibling contracts
# one function `reduce_add_index(index_name, self_elidable, operation)` over the
# {0,1,2,3} outcome lattice; this bundle models the SAME decision but narrows the
# carrier hard, and the narrowing is what fixes the disposition of each case.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-reshape                  -> pos-reshape                        PORTED
#   pos-master-assert (echo)     -> pos-echo-both-arms                 PORTED (honest half)
#   admiss-fshape                -> admiss-f2p-cancels-matching-removal RE-AIMED
#   frame-mutate-is-remove       -> (none)                            VACUOUS
#   frame-mutate-name            -> (none)                            VACUOUS
#   drop-cancellation            -> drop-cancellation                  PORTED
#   guard-drop-nameeq            -> cancel-any-removal                 PORTED
#   guard-drop-isremove          -> (see cancel-on-non-removal)        NOT EXPRESSIBLE
#   swap-base-tags               -> mistag-inherited-outcome           PORTED
#
# ADDED (2, no direct sibling counterpart): cancel-on-non-removal and
#   else-discards-inherited. The first attacks the `else` arm on the non-removal
#   (`next = other`) sub-domain — the spirit of the sibling's over-broad
#   cancellation, expressed where the carrier allows it; the second is the rival
#   that DISCARDS the free `inheritedOutcome` binder outright. Both are real
#   divergences from the post-image with machine-checked witnesses.
#
# PORTED (echo control, honest half): pos-master-assert demonstrates the spec is
#   not oracle-echo-vulnerable. Here the post-image names no opaque answer key
#   (the cancel branch is the concrete constructor `cancel`, the defer branch the
#   input value itself), so there is no WRONG echo to pair it with as a reject
#   case — but the positive half ports directly and is carried as
#   pos-echo-both-arms: assert on each arm that the returned value equals the
#   post-image there, which must verify.
# PORTED (swap-base-tags): an earlier accounting recorded this "NOT MODELED — the
#   base rule is an opaque free input, so there is no outcome to transpose". That
#   is wrong, and measurably so: `Reduction.inherited` carries a `tag : Nat`
#   precisely to keep the non-cancel outcomes DISTINGUISHABLE, so "hand back a
#   different inherited outcome than the one given" is statable and is exactly the
#   sibling's mistake. Landed as mistag-inherited-outcome (rival exit 1; witness
#   exit 0 on the rival, 1 on gold with `decide` proving the claim false).
# VACUOUS (frame mutation, ×2): both sibling rivals WRITE a read-only input held
#   at Acc(...,1/2). This backend is referentially transparent, has no heap and
#   no aliasing, and declares NO `mut` binder — there is no read-only input to
#   overwrite and no substitute probe to build. No case fabricated.
# NOT EXPRESSIBLE (guard-drop-isremove): the sibling drops the `isinstance`
#   conjunct — cancel on name-equality ALONE, for a NON-removal op whose name
#   equals the index name. This carrier folds the "is a removal" test into the
#   `NextOp` constructor and carries a name ONLY on `removesIndex`; a non-removal
#   op is `NextOp.other` with NO name field, so "a non-removal whose name equals
#   addedName" is a distinction the abstraction collapses and cannot be probed.
#   The rival's SPIRIT — over-broad cancellation onto ops that should defer — is
#   covered instead by cancel-on-non-removal (annihilate on `other`), which is
#   the strongest form of that mistake this carrier can state.
# BINDER / POINT COVERAGE. The five reject witnesses probe five distinct inputs:
#   (addedName="idx", next=removesIndex "idx", inherited 0)  drop-cancellation
#   (addedName="abc", next=removesIndex "xyz", inherited 0)  cancel-any-removal
#   (addedName="idx", next=other,              inherited 0)  cancel-on-non-removal
#   (addedName="idx", next=other,              inherited 7)  else-discards-inherited
#   (addedName="abc", next=removesIndex "xyz", inherited 3)  mistag-inherited-outcome
#   so `addedName` moves over {"idx","abc"}, `next` over
#   {removesIndex "idx", removesIndex "xyz", other} (both constructors, matching
#   and mismatching names), and `inheritedOutcome` over
#   {inherited 0, inherited 3, inherited 7}. No binder is pinned across the
#   battery, and the single top-level clause is attacked on BOTH arms (the `then`
#   annihilation by drop-cancellation; the `else` deferral by the other four, on
#   the name, shape, discard, and re-tagging axes — the last two reaching that arm
#   through the `other` and the `removesIndex` constructor respectively) and
#   defended by the reshape positive, the echo control, and the admissibility case.
#
# SPEC-TOO-WEAK probes that did NOT verify (so are not shipped as cases, recorded
#   so the next reader need not re-run them): swapped branches; a PREFIX-match
#   guard (`name.take addedName.length = addedName`) in place of full name
#   equality; a LENGTH-only guard (`name.length = addedName.length`); and a guard
#   that additionally requires the added name to be NON-EMPTY. All four were
#   rejected by the frozen spec, each with a witness that holds of the rival and
#   is proven FALSE against gold by `decide`. Correct reshapes that DO verify
#   (spec-too-strong probes, all clean): guard bound to a `let`; `match` on the
#   guard's Bool; the equality written in the other order (`addedName = name`);
#   a negated guard with the arms swapped; and an `else` arm that returns
#   `inheritedOutcome` reconstructed by cases on its constructor.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing there to probe.
AXIOM_TESTS = []
