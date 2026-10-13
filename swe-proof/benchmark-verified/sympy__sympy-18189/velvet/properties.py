"""properties.py — G-PBT falsification battery for sympy__sympy-18189 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or the ``prove_correct`` tactic body, is changed — both
of which the consumer spec view elides, so ``markers.same_spec`` holds and the
``prove_correct reorderSolutions`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over an opaque base solver):

  reorderSolutions (order : List Nat) (permute : Bool)
      return (out : List (List Int))
    ensures out = reorderAll order (baseSolve permute)      (clause P1)

The routine produces a solution set when the caller requested the tuple
components in a variable order that differs from the base solver's canonical
one. It consults the base solver — which takes a single Boolean selecting
whether the extra variant solutions are included — and reindexes each returned
tuple into the requested order. The load-bearing content of the fix is that the
base solver is consulted with the SAME Boolean the caller asked for: requesting
a non-canonical order must never suppress the variants the caller selected. The
single ``ensures`` P1 pins ``out`` to ``reorderAll order (baseSolve permute)`` —
BOTH the reindexing (``reorderAll``) and the flag forwarding (``baseSolve
permute``, not a constant) are load-bearing sub-terms.

TWO INPUT BINDERS, both free: ``permute`` (the variant flag — which set the
base solver enumerates) and ``order`` (the requested reindexing). The reject
witnesses must move ``permute`` across BOTH truth values, since the pre-patch
bug lives on the ``permute = true`` sub-domain (the reported failure) while the
mirror error lives on ``permute = false``; a battery that pinned ``permute``
would miss a rival that mishandled only the un-probed value. ``order`` is also
exercised: the drop-reindex rival is refuted wherever the reindexing is
observable.

CARRIER NOTE — WHY THIS PORT CONDITIONS ON THE CARRIER. The base solver is an
``opaque`` function (``baseSolve : Bool → List (List Int)``) with NO
constraining axiom: nothing reduces ``baseSolve true`` or ``baseSolve false`` at
a literal input, and the two are deliberately NOT asserted equal (the flag
genuinely changes which family is enumerated — that non-collapse is what G-AX
validates against the real solver). So a ``decide`` on a concrete literal gets
stuck, and a witness cannot COMPUTE the post-image. Each reject witness instead
CONDITIONS on the carrier: it quantifies over a symbolic ``order`` (and, where
apt, ``permute``), assumes ONE disequality of opaque composites describing
exactly the sub-region the rival is wrong on (e.g. ``reorderAll order (baseSolve
false) ≠ reorderAll order (baseSolve true)`` for the pre-patch rival), and shows
the extracted program's output differs from the post-image there. Reaching the
program uses Velvet's extractor: ``extract_program_for`` gives
``reorderSolutionsExec = NonDetT.run ∘ reorderSolutions``, reducing to
``DivM.res result``. The claim each witness makes is STRONGER than any literal
input could make: *wherever the two composites differ, the rival's answer
differs from the spec's* — the whole sub-domain on which the rival is wrong.

Each witness is checked three ways (the last by the gate): (1) it ELABORATES
against the rival; (2) it FAILS against the frozen solution — the frozen impl
reduces the goal to ``False`` with ``h`` unused, so it is a real discriminator,
not a tautology; (3) its binders are JOINTLY SATISFIABLE — one hypothesis per
witness, an ordinary opaque-composite disequality that is a theorem in NEITHER
direction (no separating axiom on ``baseSolve``), so it is neither
self-contradictory nor a smuggled assumption of the conclusion. No
``sorry``/``admit``/``native_decide``/``axiom``. All three were verified
out-of-band with real ``lake`` builds before shipping.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. The grounded-oracle honest cheapest
    impl (return ``reorderAll order (baseSolve permute)`` directly) and a
    structurally-different flag dispatch (branch on ``permute``, call the base
    solver with the concrete flag in each arm) must both verify, else the spec
    is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — no PRECOND-TOO-STRONG probe, but the residual risk IS
    probed, now at TWO levels. The method carries NO ``require`` clause
    (precondition ≡ True), so there is no precondition to be too strong and the
    sibling's empty-precondition self-call has no counterpart. What remains on a
    total domain is (a) a DEGENERATE post-image and (b) an obligation that is
    UNSATISFIABLE at an F2P-shaped input, and both are expressible rather than
    merely arguable. ``admiss-nondegenerate-reindex`` pins (a) by ``decide`` on
    closed literals: ``reorderAll`` is a genuine positional permutation, not the
    identity. ``admiss-obligation-at-f2p-order`` pins (b) in the shape the total
    -carrier analogue calls for: with the frozen impl intact it discharges P1's
    OWN post-image — the opaque composite ``reorderAll [1,0] (baseSolve <flag>)``,
    for BOTH flag values, at the F2P-shaped requested order ``[1,0]`` — as a
    ``have``-style ``assert`` by evaluation, BEFORE closing the frozen
    obligation verbatim. The first case never touches ``baseSolve`` at all
    (closed literals only), so it cannot see an obligation that is vacuous
    exactly where the reported request lives; the second does. Both were
    controlled: falsifying either conjunct makes the case FAIL (see the audit
    note), so neither assert is decoration.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: ``order`` and
    ``permute`` are immutable values, this bundle declares NO ``mut`` binder,
    there is no heap and no aliasing. No read-only input to overwrite and no
    permission system to trip. Not fabricated (per the porting map, dropped
    rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. P1's post-image ``reorderAll
    order (baseSolve permute)`` is grounded in the inputs (a function of ``order``
    and ``permute``), not an opaque answer-key; the only "echo" available is the
    correct answer, which the grounded-oracle positive control does honestly.
    There is no wrong echo to build.
  * DIVERGENCE / TERMINATION: CLOSED BY THE SEMANTICS, in every shape probed,
    and NOT shippable as a reject case for a reason that has nothing to do with
    the spec being weak. The frozen file sets
    ``set_option loom.semantics.termination "total"``, and in Loom that option is
    itself what opens ``TotalCorrectness`` scope, so option and ``open`` cannot
    disagree. Under total correctness a postcondition is claimed of ALL runs, not
    only terminating ones, and Loom's total loop generator emits a per-iteration
    side condition that the loop's measure STRICTLY DECREASES. The naive
    diverging rival is therefore rejected: splicing ``while True do pure ()``
    ahead of the frozen body fails with ``Decreasing annotations are required in
    total correctness semantics``. An earlier revision of this bullet went on to
    claim that supplying a syntactically valid yet SEMANTICALLY BOGUS measure
    defeats the check, and that a ``while True`` loop carrying
    ``decreasing (1 : Nat)`` and NO ``done_with`` clause makes the loop's
    continuation unreachable so that an impl returning the unambiguously wrong
    ``[[999]]`` VERIFIES at exit 0. That claim is FALSE and is retracted. It was
    re-measured on exactly that shape, with the frozen ``loom_solve`` tail: the
    build is REJECTED (exit 1) on the MEASURE's own goal, carrying the clause's
    own name, ``case «decreasing_1: (1 : Nat)» ... 1 < 1``. So there is no
    escape hatch here and nothing to escalate; the omitted ``done_with`` does
    not buy vacuity, because the descent obligation fires ahead of any
    reachability question. What does block a reject case is the WITNESS
    contract: a case must exhibit a witness that ELABORATES against the rival
    and FAILS against gold, and a diverging rival's module does not compile at
    all (the descent obligation fails at the ``method`` itself, upstream of any
    appended tester), so such a case would score MALFORMED rather than
    rejecting. The class is carried as documentation and defended by the
    semantics.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, via conditioning on the carrier.
    The pre-patch bug (drop the flag → constant ``false``), its mirror (constant
    ``true``), the drop-reindex rival (skip ``reorderAll``), and the
    mangled-order rival (reindex under ``order.reverse``) each re-express onto P1
    as an opaque-composite disequality, refuted on exactly the sub-region where
    the rival diverges. The fourth attacks a sub-term the first three all leave
    untouched: they pass ``order`` through to ``reorderAll`` verbatim, so none of
    them tests that the reindexing uses the order the caller REQUESTED. See the
    footer for the case-by-case sibling accounting.

WITNESS PLACEMENT / coverage. Rivals share a refutation point only when they
fail there for the same reason. The four reject witnesses sit at FOUR DISTINCT
input points: the pre-patch rival at ``permute = true`` (the reported failure
sub-domain), the constant-true mirror at ``permute = false`` (moving the flag
binder across both values), the drop-reindex rival at symbolic ``permute``
conditioned on the reindexing being observable, and the mangled-order rival at
symbolic ``permute`` conditioned on the ORDER ARGUMENT being observable — a
different hypothesis over a different sub-term, not a respelling of the third.
All three load-bearing sub-terms of P1 are attacked: the flag forwarding
(``baseSolve permute`` vs a constant), the presence of the reindexing
(``reorderAll _ _`` vs none), and its order argument (``order`` vs a mangled
order). pts=4.

AUDIT NOTE (SECOND, independent adversarial audit; every number below is an
exit code observed from a real ``lake`` build, not an expectation).

STATEMENT INTEGRITY (attack A). Each of the 7 cases was diffed against the
frozen file. Every diff is confined to the impl-region body, plus — for the two
admissibility cases only — the ``prove_correct`` TACTIC BODY. No case touches the
``method`` signature, the ``ensures`` clause, the ``prove_correct`` header, or
the axioms/pure/pre/post regions. No hypothesis is weakened by reformatting.

WITNESS DISCRIMINATION, RE-DERIVED (attack B) and the FORGERY TEST (attack B′).
All four reject witnesses were rebuilt in both directions plus the gate's
consistency probe: rival exit 0, frozen-solution exit 1, probe exit 1, in every
case. The gold-side failure is a SEMANTIC refutation, and this was established
by the forgery experiment rather than by reading the error: flipping ONLY the
claim (``≠ DivM.res`` → ``= DivM.res``, leaving binders and hypothesis
identical) INVERTS both exit codes — the flipped claim builds against the frozen
solution (exit 0, warning ``unused variable `h```) and FAILS against the rival
(exit 1, ``unsolved goals … ⊢ False``). So gold's exit code tracks the claim and
carries real information; the witnesses are not hollow. The gold-side signature
is ``unsolved goals``/``⊢ False`` with ``h`` in context and reported unused —
the frozen impl reduces the refutation to ``False`` unaided.

HYPOTHESIS INHABITATION. Re-derived, not inherited. Each disequality was closed
by ``decide`` under concrete assumed base-solver values consistent with the flag
dependence G-AX validates (e.g. ``baseSolve true = [[3,2],[2,3]]``,
``baseSolve false = [[2,3]]``); one file, exit 0. Stronger than the gate's probe,
which only fails to derive ``False``.

RIVAL OBSERVABILITY (attack C). No reject case is vacuous. Each rival's goal
names a distinct un-dischargeable equation; ``reorderAll`` is NOT identity in
general (``reorderAll [1,0] [[3,2]] ≠ [[3,2]]``, by ``decide``) yet IS identity at
the canonical order (``reorderAll [0,1] [[3,2]] = [[3,2]]``), so drop-reindex and
order-mangled are genuine PARTIAL-domain rivals rather than blanket-wrong impls.

ATTACK D (new wrong rivals). 13 wrong impls beyond this battery were built:
negated flag, ``baseSolve (order.length == 2)``, ``order.tail``,
``order.map (·+1)``, double reindex, ``base ++ base``, ``base.take 1``,
``.reverse``, ``.eraseDups``, ``return []``, and the sibling's asymmetric
dispatch. All 13 were REJECTED (exit 1) — the spec is not too weak on any of
them. Two "rivals" that are definitionally equal to gold (``!(!permute)``,
``permute && permute``) verified, correctly, and are NOT spec holes.

ATTACK D, THE CLAIMED SPEC HOLE, RETRACTED IN FULL. This slot previously recorded
a real hole on the FROZEN artifact: a ``while True`` loop carrying a bogus
constant measure ``decreasing (1 : Nat)`` and NO ``done_with`` clause, said to
render the loop's continuation unreachable so that P1 is discharged vacuously and
an impl returning the unambiguously wrong ``[[999]]`` VERIFIES (exit 0) with the
frozen ``loom_solve`` unchanged. Re-measured on that exact shape, it does not
reproduce. The build is REJECTED (exit 1), and specifically on the MEASURE's own
goal under the clause's own name: ``case «decreasing_1: (1 : Nat)» ... 1 < 1``.
The two sibling cells the old text offered as evidence that the finding was not
cell-specific were re-measured on the identical splice and are REJECTED the same
way, with the same ``1 < 1`` goal (``django__django-15098``,
``pylint-dev__pylint-4551``), so the generalization falls with the original. The
reason is structural, not a tactic accident: Loom's total-correctness loop
generator (``forWithInvariantLoop`` under ``TotalCorrectness.DemonicChoice.WPGen``)
takes a ``measure : β -> Nat`` and emits the per-iteration side condition
``with_name_prefix `decreasing (measure b' < measure b)``, so a constant or
increasing measure arrives as an unprovable goal regardless of what the
continuation can reach. The twin that takes ``measure : β -> Option ℕ`` and
DISCARDS it lives under ``PartialCorrectness``, and this bundle does not select
that scope. There is accordingly NO spec hole here, nothing escalated from this
slot, and no frozen-artifact change wanted.

ATTACK E (correct reshapes). 5 built. ``!(!permute)``, ``order ++ []``,
``order.reverse.reverse`` verify UNCHANGED (exit 0) — the frozen script absorbs
them. Two genuine reshapes (``(baseSolve permute).map (reorderTuple order)``, and
the fully inlined ``.map (fun t => order.map (fun k => t[k]!))``) fail under the
bare frozen script (unsolved goal ``List.map (reorderTuple order) (baseSolve
permute) = reorderAll order (baseSolve permute)``) and VERIFY (exit 0) once
re-proved with one extra ``simp [reorderAll, reorderTuple]``. The SPEC accepts
both; only the frozen tactic script needed the extra step. Not a spec defect,
and NOT a SPEC-TOO-STRONG finding.

SUBSUMPTION of the dropped sibling rival, demonstrated. The sibling's
``weak-asymmetric-true-uses-false`` was transliterated literally and built: it
fails with the unsolved goal ``reorderAll order (baseSolve false) = reorderAll
order (baseSolve permute)`` under ``if_pos : permute = true``, and
``weak-prepatch-const-false``'s OWN witness elaborates against it unchanged
(exit 0). Same clause, same sub-term, same refutation point — the subsumption is
measured, not asserted.

CASES ADDED BY THIS AUDIT. ``admiss-obligation-at-f2p-order``: the previous
admissibility case used closed literals only and so never touched ``baseSolve``,
leaving the total-carrier analogue of PRECOND-TOO-STRONG (an obligation vacuous
at exactly an F2P-shaped input) untested. The new case discharges P1's own opaque
post-image at ``order = [1,0]`` for BOTH flag values before closing the frozen
obligation. Controlled: un-swapping the components in either conjunct makes it
FAIL (exit 1, ``⊢ ∀ a ∈ baseSolve true, a[1]?.getD 0 = a[0]?.getD 0 ∧ …``), so
the assert is load-bearing. The ORIGINAL admissibility case was controlled the
same way: falsifying either of its conjuncts makes ``decide`` report the
proposition FALSE (exit 1), so it too is load-bearing, not decoration.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18189"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen impl body, verbatim (everything strictly
# ---- inside reorderSolutions's -- impl-start / -- impl-end, comments included).
# ---- Every variant _swap()s only this block, so the edit never touches the
# ---- spec regions (axioms/pure/pre/post + the method signature and the
# ---- `ensures`). Both "present" and "unique" are asserted at load by _swap.
_IMPL = (
    "    -- Consult the base solver with the SAME variant flag the caller requested,\n"
    "    -- then reindex each produced tuple into the requested variable order.\n"
    "    let base := baseSolve permute\n"
    "    let result := reorderAll order base\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "reorderSolutions impl region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean with ONLY reorderSolutions's impl-region body replaced.
    `new_body` is the source strictly between the markers (no markers); the
    surrounding `-- impl-start` / `-- impl-end` lines are preserved by anchoring
    on the frozen block, so the region boundary stays intact and the spec view
    elides all of it."""
    return _swap(_BASE, _IMPL, new_body)


# ---- the frozen proof script, verbatim. A case that keeps the frozen impl but
# ---- adds an in-impl `assert` must extend the tactic body to discharge the new
# ---- goal; `variant_scope` permits that (the `prove_correct reorderSolutions`
# ---- header survives, only the tactic body differs) and same_spec is unaffected
# ---- because the spec view elides the proof body as well as the impl region.
_PROOF = "prove_correct reorderSolutions by\n  loom_solve\n"
assert _BASE.count(_PROOF) == 1, "prove_correct block drifted from expected text"


def _impl_reproved(new_body, new_proof):
    """Impl-region body AND `prove_correct` tactic body replaced (no statement
    change: the `method`/`ensures` header and the `prove_correct <name>` header
    are untouched, so the obligation survives byte-identically)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and its post-image is built from an opaque callee, so a witness reaches
# ---- the impl through Velvet's extractor and CONDITIONS on the carrier: it
# ---- quantifies over the symbolic inputs, assumes one disequality of opaque
# ---- composites (exactly the sub-region the rival mishandles), and shows the
# ---- extracted program's output differs from the post-image there.
# ---- `reorderSolutionsExec order permute` is `NonDetT.run (reorderSolutions
# ---- order permute)`, reducing to `DivM.res result`. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict; the lone hypothesis `h` is an ordinary equality of opaque terms,
# ---- not an assumption of the conclusion, and is jointly satisfiable.
def _wit(binders, hyp, exec_call, post_image):
    return (
        "extract_program_for reorderSolutions\n\n"
        f"example {binders}\n"
        f"    (h : {hyp}) :\n"
        f"    {exec_call} ≠ DivM.res ({post_image}) := by\n"
        "  unfold reorderSolutionsExec reorderSolutions\n"
        "  simp [NonDetT.run, pure, h]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS — positive controls that MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================

    # POS-CONTROL 1 (grounded-oracle honest cheapest impl). Because P1's oracle
    # `reorderAll order (baseSolve permute)` is GROUNDED in the inputs (not an
    # opaque answer-key), the cheapest correct impl returns it directly — it
    # performs the real work (consult the base solver under the caller's flag,
    # then reindex). This STANDS IN PLACE of an ungrounded-oracle echo attack
    # (there is no wrong echo to build). P1 holds definitionally; must verify.
    {
        "id": "pos-grounded-oracle-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Cheapest correct impl: return the grounded reindexed set\n"
            "    -- directly. The flag is forwarded and the reindexing applied,\n"
            "    -- so P1 holds definitionally.\n"
            "    return reorderAll order (baseSolve permute)\n"),
        "rationale": "grounded-oracle honest positive control: P1's oracle "
                     "`reorderAll order (baseSolve permute)` is a function of the "
                     "inputs (no answer-key), so the cheapest correct impl returns "
                     "it directly and MUST verify (P1 is a definitional equality); "
                     "the frozen `loom_solve` closes unchanged. Else "
                     "SPEC-TOO-STRONG. Verified out-of-band.",
    },

    # POS-CONTROL 2 (structurally-different flag dispatch). Instead of the gold's
    # straight-line `baseSolve permute`, branch on the flag and call the base
    # solver with the CONCRETE flag in each arm. On the true branch the verifier
    # knows permute=true so baseSolve true == baseSolve permute; likewise false.
    # Same value on every input, different control shape, no loop / no new lemma.
    # Must verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-flag-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Dispatch on the concrete flag (different control shape, same\n"
            "    -- value): each branch consults the base solver with the flag the\n"
            "    -- verifier knows it is in, then reindexes.\n"
            "    if permute then\n"
            "      let base := baseSolve true\n"
            "      return reorderAll order base\n"
            "    else\n"
            "      let base := baseSolve false\n"
            "      return reorderAll order base\n"),
        "rationale": "a correct impl with DIFFERENT control flow (flag dispatch "
                     "calling the base solver with the concrete flag in each arm "
                     "vs gold's single straight-line call) must verify: on the "
                     "true branch permute=true so baseSolve true==baseSolve "
                     "permute, likewise false; the reindexing is applied whole in "
                     "each arm. `loom_solve` closes both branches. Else "
                     "SPEC-TOO-STRONG. Verified out-of-band.",
    },

    # ADMISSIBILITY / NON-DEGENERACY (added by audit). The method carries no
    # `require`, so there is no PRECOND-TOO-STRONG probe to build — but the
    # residual total-domain risk the empty precondition leaves open IS
    # expressible and was previously only argued in prose: that the post-image
    # is non-degenerate, i.e. `reorderAll` is not the identity, so the
    # reindexing sub-term of P1 has observable content and the drop-reindex
    # rival's hypothesis is INHABITED rather than merely unrefuted. This case
    # pins that at a concrete two-component point with the frozen impl intact:
    # the reindexing really permutes components (`reorderAll [1,0] [[3,2]] ≠
    # [[3,2]]`) and its value is exactly the positional gather. Kept honest by
    # `decide` on closed literals — no opaque term is involved, so nothing here
    # is assumed. If this failed, P1's reindexing sub-term would be vacuous and
    # the drop-reindex witness would be conditioning on an empty region.
    {
        "id": "admiss-nondegenerate-reindex",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (reorderAll [1, 0] [[3, 2], [-3, 2], [2, -3]]\n"
            "         = [[2, 3], [2, -3], [-3, 2]] ∧\n"
            "       reorderAll [1, 0] [[3, 2]] ≠ [[3, 2]]))\n" + _IMPL,
            "prove_correct reorderSolutions by\n"
            "  loom_solve\n"
            "  all_goals decide\n"),
        "rationale": "non-degeneracy of P1's post-image, machine-checked rather "
                     "than argued: with the frozen impl intact, the reindexing "
                     "`reorderAll` is shown to be a genuine positional "
                     "permutation at a concrete two-component point "
                     "(`reorderAll [1,0] [[3,2]] ≠ [[3,2]]`, and the gathered "
                     "value is exactly the requested-order tuple). This is what "
                     "makes the REINDEXING sub-term of P1 observable and the "
                     "drop-reindex rival's hypothesis inhabited — without it "
                     "that witness could be conditioning on an empty region. "
                     "The method has NO `require`, so this replaces the "
                     "sibling's precondition-admissibility self-call: there is "
                     "no precondition to admit, only a post-image to show "
                     "non-degenerate. All literals are closed, so `decide` "
                     "settles it and no opaque behavior is assumed. Verified "
                     "out-of-band (exit 0).",
    },

    # ADMISSIBILITY at an F2P-SHAPED INPUT (added by the second audit). The case
    # above uses CLOSED LITERALS only, so it never touches `baseSolve` and cannot
    # see the other residual risk an empty precondition leaves open: that P1's
    # obligation is UNSATISFIABLE (or degenerate) at exactly the kind of input the
    # F2P test exercises — a non-canonical requested order over the OPAQUE base
    # set. That is the total-carrier analogue of the sibling's precondition
    # admissibility probe, and it IS expressible here: with the frozen impl
    # intact, discharge P1's own post-image — the opaque composite
    # `reorderAll [1,0] (baseSolve <flag>)`, for BOTH flag values — by evaluation
    # as a `have`-style `assert`, BEFORE closing the frozen obligation verbatim.
    # If the obligation were vacuous at that point these asserts could not be
    # proved from the definitions alone; that they can shows the post-image is a
    # real, inhabited positional gather over whatever the opaque solver returns.
    # Controlled: un-swapping the components in either conjunct makes this case
    # FAIL, so the assert is load-bearing rather than decorative.
    {
        "id": "admiss-obligation-at-f2p-order",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- ADMISSIBILITY: discharge the frozen obligation's own post-image\n"
            "    -- at an F2P-shaped requested order, by EVALUATION over the opaque\n"
            "    -- base set, before closing the obligation verbatim.\n"
            "    assert (with_name_prefix `admissObl\n"
            "      (reorderAll [1, 0] (baseSolve true)\n"
            "         = (baseSolve true).map (fun t => [t[1]!, t[0]!]) ∧\n"
            "       reorderAll [1, 0] (baseSolve false)\n"
            "         = (baseSolve false).map (fun t => [t[1]!, t[0]!])))\n" + _IMPL,
            "prove_correct reorderSolutions by\n"
            "  loom_solve\n"
            "  all_goals simp [reorderAll, reorderTuple]\n"),
        "rationale": "the total-carrier analogue of a precondition-admissibility "
                     "probe, at an F2P-SHAPED input. The method has no `require`, "
                     "but the risk that survives an empty precondition is the "
                     "obligation being vacuous or unsatisfiable at exactly the "
                     "inputs the failing test exercises: a NON-CANONICAL requested "
                     "order applied to the OPAQUE base set. Unlike the "
                     "closed-literal non-degeneracy case, this one names "
                     "`baseSolve` and so reaches that region: with the frozen impl "
                     "intact it discharges P1's own post-image `reorderAll [1,0] "
                     "(baseSolve flag)` for BOTH flag values, by evaluation, as an "
                     "`assert` preceding the verbatim obligation. Its proof adds "
                     "only `simp [reorderAll, reorderTuple]` to the frozen "
                     "`loom_solve` (statement and `prove_correct` header "
                     "untouched). Load-bearing, not decoration: swapping the "
                     "components back in either conjunct makes the case FAIL. "
                     "Verified out-of-band (exit 0); falsified control exit 1.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked, satisfiable refutation
    # witness that CONDITIONS on the carrier (see the module docstring) and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================

    # ATTACK 1 (PRE-PATCH — CONSTANT false). Consult the base solver under a fixed
    # false flag, ignoring the caller's `permute`, then reindex. This is the exact
    # base_commit behaviour. Correct only when the caller asked for permute=false;
    # wrong whenever permute=true. Attacks the flag-forwarding sub-term of P1.
    {
        "id": "weak-prepatch-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- PRE-PATCH body: consult the base solver under the DROPPED\n"
            "    -- default flag (constant false), ignoring the caller's flag.\n"
            "    let base := baseSolve false\n"
            "    let result := reorderAll order base\n"
            "    return result\n"),
        "refinement": "this is the base_commit behaviour: the recursive base call "
                      "drops the caller's variant flag, so the re-derivation runs "
                      "in the no-variant configuration. For the reported request "
                      "(the full variant family in a non-canonical variable order) "
                      "the base call then returns only the single base solution "
                      "instead of the full sign/value family, so the reindexed "
                      "answer COLLAPSES to one solution. The failing test demands "
                      "the full family, so it MISMATCHES. The faithful real patch "
                      "(= the pre-patch) does NOT resolve.",
        "rationale": "REJECT from P1 (`out = reorderAll order (baseSolve "
                     "permute)`): the rival produces `reorderAll order (baseSolve "
                     "false)` where the post-image demands `reorderAll order "
                     "(baseSolve permute)`; the opaque `baseSolve` grants no "
                     "false==true equality, so for permute=true the equality is "
                     "unprovable. Refuted at permute=true wherever the two "
                     "reindexed sets differ — the sub-domain the fix is about. "
                     "Correct on the permute=false sub-domain only.",
        "witness": _wit(
            "(order : List Nat)",
            "reorderAll order (baseSolve false) ≠ reorderAll order (baseSolve true)",
            "reorderSolutionsExec order true",
            "reorderAll order (baseSolve true)"),
    },

    # ATTACK 2 (MIRROR — CONSTANT true). The symmetric error: consult the base
    # solver under a fixed true flag, ignoring the caller's `permute`. Correct
    # only when permute=true; wrong whenever permute=false (over-enumerates the
    # full family when the caller asked for the base one). Moves the flag binder
    # to false and guards against a spec that pins only the reported (true)
    # direction and leaves the base direction free.
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- WRONG: always consult the base solver in the full-variant\n"
            "    -- configuration, ignoring the caller's flag.\n"
            "    let base := baseSolve true\n"
            "    let result := reorderAll order base\n"
            "    return result\n"),
        "refinement": "this hard-codes the full-variant configuration on the base "
                      "call regardless of the caller's flag. When a caller asks "
                      "for the base (no-variant) set in a non-canonical variable "
                      "order — the common case across the unchanged tests — the "
                      "routine would now return the full variant family instead of "
                      "the single base family requested. Every such assertion would "
                      "over-enumerate and MISMATCH. The faithful real patch does "
                      "NOT resolve.",
        "rationale": "REJECT from P1: the rival produces `reorderAll order "
                     "(baseSolve true)` where the post-image demands `reorderAll "
                     "order (baseSolve permute)`; no true==false equality is "
                     "granted, so for permute=false the equality is unprovable. "
                     "Refuted at permute=false wherever the two reindexed sets "
                     "differ. Correct on the permute=true sub-domain only — moves "
                     "the flag binder to false and guards against a spec that pins "
                     "only the reported (true) direction.",
        "witness": _wit(
            "(order : List Nat)",
            "reorderAll order (baseSolve true) ≠ reorderAll order (baseSolve false)",
            "reorderSolutionsExec order false",
            "reorderAll order (baseSolve false)"),
    },

    # ATTACK 3 (DROP-THE-REINDEXING — return the base set un-reindexed). Consult
    # the base solver under the caller's `permute` (correct flag) but return the
    # base set DIRECTLY without applying reorderAll — i.e. omit the positional
    # reindexing. Attacks the reindexing sub-term of P1: reorderAll is not
    # asserted to be identity, so the base set need not equal its reindexing.
    {
        "id": "weak-drop-reindex",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- WRONG: skip the positional reindexing; return the base set as-is\n"
            "    -- in the base solver's canonical variable order.\n"
            "    let base := baseSolve permute\n"
            "    return base\n"),
        "refinement": "this drops the positional reindexing and returns the base "
                      "solver's tuples in its CANONICAL variable order, not the "
                      "caller's requested order. The whole point of this branch is "
                      "that the caller asked for a DIFFERENT variable order, so "
                      "every returned tuple would have its components in the wrong "
                      "positions. A test that supplies a non-canonical order and "
                      "asserts the reindexed tuples would MISMATCH. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "REJECT from P1: the rival produces `baseSolve permute` where "
                     "the post-image demands `reorderAll order (baseSolve "
                     "permute)`; reorderAll is not asserted to be the identity, so "
                     "the base set need not equal its reindexing. Refuted at "
                     "symbolic permute wherever `baseSolve permute ≠ reorderAll "
                     "order (baseSolve permute)` — the sub-region where the "
                     "reindexing is observable. Attacks the reindexing sub-term "
                     "the flag-forwarding rivals leave untested.",
        "witness": _wit(
            "(order : List Nat) (permute : Bool)",
            "baseSolve permute ≠ reorderAll order (baseSolve permute)",
            "reorderSolutionsExec order permute",
            "reorderAll order (baseSolve permute)"),
    },

    # ATTACK 4 (WRONG REINDEXING — reindex under a MANGLED order). Added by
    # audit. The three rivals above either replace `baseSolve permute` by a
    # constant or delete `reorderAll` outright; all three pass `order` through
    # to `reorderAll` UNTOUCHED, so none of them tests that the reindexing uses
    # the order the caller actually requested. This rival keeps both the flag
    # forwarding AND the reindexing — it applies `reorderAll` to the base set
    # under the caller's own flag — but reindexes under `order.reverse` instead
    # of `order`. It is the rival that a spec pinning only "SOME reindexing was
    # applied under the right flag" would admit, and it is refuted only because
    # P1 names `order` itself in the post-image. Attacks the `order` ARGUMENT of
    # the reindexing sub-term, a third distinct sub-term of P1.
    {
        "id": "weak-order-mangled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- WRONG: reindex under a MANGLED requested order (reversed),\n"
            "    -- not the order the caller asked for.\n"
            "    let base := baseSolve permute\n"
            "    let result := reorderAll order.reverse base\n"
            "    return result\n"),
        "refinement": "this consults the base solver correctly and does apply "
                      "the positional reindexing, but builds each tuple from the "
                      "requested positions in the opposite order, so every "
                      "returned tuple has its components transposed relative to "
                      "the order the caller asked for. Any caller supplying a "
                      "requested order that is not its own reverse — the "
                      "ordinary case, including the reported request — would "
                      "receive tuples whose components sit in the wrong "
                      "positions and MISMATCH. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "REJECT from P1 (`out = reorderAll order (baseSolve "
                     "permute)`): the rival produces `reorderAll order.reverse "
                     "(baseSolve permute)`, and `reorderAll` is not asserted "
                     "invariant under reversing its order argument, so the "
                     "equality is unprovable. Refuted at symbolic `permute` "
                     "wherever reindexing under the reversed order differs from "
                     "reindexing under the requested one. Distinct from the "
                     "three rivals above: it keeps BOTH the flag forwarding and "
                     "a reindexing, and is refuted only by P1 naming `order` "
                     "itself — the `order` argument is the sub-term the other "
                     "rivals pass through untouched. Observed out-of-band: rival "
                     "build exit 1 with unsolved goal `reorderAll order.reverse "
                     "(baseSolve permute) = reorderAll order (baseSolve "
                     "permute)`; witness exit 0 on the rival, 1 on gold; "
                     "hypothesis inhabited by `decide` at order=[1,0] over a "
                     "concrete two-component base set.",
        "witness": _wit(
            "(order : List Nat) (permute : Bool)",
            "reorderAll order.reverse (baseSolve permute) ≠ "
            "reorderAll order (baseSolve permute)",
            "reorderSolutionsExec order permute",
            "reorderAll order (baseSolve permute)"),
    },
]


# ---------------------------------------------------------------------------
# Sibling (nagini) -> velvet accounting. The sibling battery ships 5 SPEC cases
# (2 soundness positives, 1 admissibility, 4 uniqueness rivals — note it lists
# 2 pos + 1 admiss + 4 uniqueness = 7 entries) plus 2 AXIOM_TESTS. The sibling
# contracts one function, reorder_solution_family(expand: bool), whose recursive
# solver (`solve_family`) and per-tuple reindexer (`relabel`) are A-consumed
# axioms; this bundle contracts one method, reorderSolutions, over an opaque base
# solver with a deeply-modeled reindexing (`reorderAll`/`reorderTuple`). The two
# surfaces model the SAME dispatch; the carrier is opaque on the base solver here,
# which governs the witness mechanics (conditioning on the carrier) but NOT the
# reachability of the reject lane.
#
#   sibling case                          kind          -> here                        status
#   -------------------------------------------------------------------------
#   pos-control-grounded-oracle-cheapest  soundness     -> pos-grounded-oracle-cheapest PORTED
#   pos-control-bool-dispatch             soundness     -> pos-flag-dispatch            PORTED
#   admiss-self-call-both-options         admissibility -> admiss-nondegenerate-reindex REPLACED (audit 1)
#   (same, F2P-input half)                admissibility -> admiss-obligation-at-f2p-order ADDED (audit 2)
#   weak-prepatch-const-false             uniqueness    -> weak-prepatch-const-false    PORTED
#   weak-const-true                       uniqueness    -> weak-const-true              PORTED
#   weak-drop-relabel                     uniqueness    -> weak-drop-reindex            PORTED
#   weak-asymmetric-true-uses-false       uniqueness    -> (none)                       DROPPED (subsumed)
#   (no sibling counterpart)              uniqueness    -> weak-order-mangled           ADDED (audit)
#   ax-solve-family-option-dependence     axiom         -> (none)                       G-AX
#   ax-relabel-bijection                  axiom         -> (none)                       G-AX
#
# 2 soundness PORTED, 3 uniqueness PORTED, 1 uniqueness DROPPED (subsumed),
# 1 admissibility REPLACED by a non-degeneracy probe and 1 admissibility ADDED at
# an F2P-shaped input, 1 uniqueness ADDED, 2 axiom-lane dropped. 8 cases.
#
# REPLACED (admiss-self-call-both-options): the sibling establishes that its EMPTY
#   precondition admits the F2P-shaped input for both flag values via a self-call.
#   This method carries NO `require` clause (precondition ≡ True), so there is no
#   precondition to be too strong and no PRECOND-TOO-STRONG probe to build — that
#   half is genuinely N/A. But the residual total-domain risk the sibling's case
#   also covers, a DEGENERATE post-image, is expressible here and was previously
#   only argued in prose ("refuted by the positive controls"), which does not
#   follow: a positive control verifies just as happily against a post-image whose
#   reindexing sub-term is the identity. `admiss-nondegenerate-reindex` closes it
#   mechanically instead — frozen impl, `decide` on closed literals, showing
#   `reorderAll` genuinely permutes components. That is also what makes the
#   drop-reindex rival's hypothesis inhabited rather than merely unrefuted.
#   AUDIT 2: "no `require`, so the lane is N/A" is NOT a sufficient reason on a
#   total carrier, and the replacement above did not fully close the lane either —
#   it uses closed literals only, so it never touches `baseSolve` and cannot see an
#   obligation that is vacuous at an F2P-SHAPED input. The literal sibling shape
#   does not port (a self-call `let out ← reorderSolutions [1,0] true` fails with
#   `fail to show termination for` — under `total` semantics a self-call raises an
#   unprovable termination obligation, and `unfold` will not unfold the method).
#   The total-carrier analogue DOES port, and is now shipped as
#   `admiss-obligation-at-f2p-order`: discharge the obligation's own post-image
#   over the OPAQUE base set at the non-canonical order `[1,0]`, for both flag
#   values, as an `assert` by evaluation, before closing the frozen obligation
#   verbatim. Both admissibility cases were falsification-controlled (exit 1 when
#   a conjunct is negated), so neither is decoration.
# ADDED (weak-order-mangled): not a sibling port. The three ported rivals all pass
#   `order` to `reorderAll` verbatim, attacking only WHICH flag reaches the base
#   solver and WHETHER a reindexing happens — never whether the reindexing uses
#   the order the caller requested. A spec pinning just "some reindexing under the
#   right flag" would admit a rival that reindexes under a mangled order; this
#   case demonstrates the frozen P1 does not, by naming `order` itself. Third
#   distinct sub-term, fourth distinct refutation hypothesis.
# DROPPED (weak-asymmetric-true-uses-false): the sibling's asymmetric rival
#   dispatches on the flag but consults the wrong (false) option on the true
#   branch, while the false branch is correct — "wrong only on true". On THIS
#   carrier both branches would consult `baseSolve false`, making the rival
#   OBSERVATIONALLY IDENTICAL to weak-prepatch-const-false (a constant-false
#   consult), refuted by the SAME witness at the SAME input for the SAME reason.
#   Shipping it would be a duplicate rival with no new coverage (it neither moves a
#   binder nor attacks a new clause). Per the "two rivals may share a witness only
#   if they really fail at the same input for the same reason" rule, the duplicate
#   is dropped rather than given a spurious distinct witness. weak-prepatch-const-
#   false carries its refinement argument. AUDIT: re-derived rather than accepted.
#   The sibling rival was transliterated literally (both arms `baseSolve false`,
#   dispatching on the flag) and built: it fails with the unsolved goal `reorderAll
#   order (baseSolve false) = reorderAll order (baseSolve permute)` under
#   `if_pos : permute = true` — the same clause, same sub-term, same refutation
#   point as weak-prepatch-const-false, and weak-prepatch-const-false's OWN witness
#   elaborates against it unchanged (exit 0). The subsumption claim is therefore
#   demonstrated, not asserted: the dispatch is dead code that the verifier
#   collapses on each branch, so the two rivals are observationally identical here.
# VACUOUS — frame/permission-mutation: the sibling explicitly records this class
#   as N/A because its only input is a value-type bool carrying no heap permission.
#   The same holds here and more broadly: this backend is referentially
#   transparent, `order`/`permute` are immutable values, no `mut` binder, no heap,
#   no aliasing. No read-only input to overwrite. No substitute fabricated.
# DIVERGENCE / TERMINATION: CLOSED BY THE SEMANTICS, not vacuous, and not
#   shippable as a case for a witness-side reason. This bundle sets
#   `set_option loom.semantics.termination "total"`, and in Loom that option is
#   itself what opens `TotalCorrectness` scope. The naive non-terminating rival is
#   rejected (a bare `while True do pure ()` fails with `Decreasing annotations
#   are required in total correctness semantics`), and so is the sharper form: a
#   `while True` loop carrying `decreasing (1 : Nat)` and NO `done_with` clause is
#   REJECTED (exit 1) on the MEASURE's own goal, `case «decreasing_1: (1 : Nat)»
#   ... 1 < 1`. An earlier revision of this slot claimed that shape VERIFIES and
#   recorded an ESCALATED spec hole on the frozen artifact; that claim was
#   re-measured, does not reproduce, and is RETRACTED IN FULL, here and in the
#   AUDIT NOTE above. There is no defeatable `total` check on this carrier: the
#   descent obligation fires ahead of any reachability question, so omitting
#   `done_with` buys nothing. What blocks a reject case is the WITNESS contract,
#   not the spec. A case needs a witness that ELABORATES against the rival and
#   FAILS against gold, and a diverging rival's module does not compile at all
#   (the descent obligation fails at the `method` itself, upstream of any appended
#   tester), so the case would score MALFORMED instead of rejecting. The class is
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   carried as documentation, defended by the semantics.
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job (meta.json records the
#   G-AX pass over the real recursive solver and the real reindexing), and this
#   gate ignores AXIOM_TESTS. `ax-solve-family-option-dependence` (the flag
#   genuinely changes the family, baseSolve true a superset of baseSolve false,
#   never a collapse) is the very fact that makes the reject witnesses' opaque-
#   composite disequalities jointly satisfiable — but it is validated by G-AX, not
#   asserted here.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` P1 (`out = reorderAll order
#   (baseSolve permute)`) has THREE load-bearing sub-terms and all three are
#   attacked: the FLAG FORWARDING (`baseSolve permute` vs a constant) by weak-
#   prepatch-const-false (permute=true) and weak-const-true (permute=false); the
#   PRESENCE of the reindexing (`reorderAll _ _` vs none) by weak-drop-reindex; and
#   its ORDER ARGUMENT (`order` vs a mangled order) by weak-order-mangled. The
#   `permute` binder is moved across BOTH values (true for prepatch, false for
#   const-true, symbolic for drop-reindex and order-mangled). The `order` binder is
#   quantified symbolically in every witness and is the load-bearing input the
#   drop-reindex and order-mangled rivals are refuted through. All three sub-terms
#   are defended by the two positive controls, the reindexing sub-term's
#   non-degeneracy is pinned concretely by admiss-nondegenerate-reindex, and the
#   obligation's satisfiability over the OPAQUE base set at a non-canonical
#   (F2P-shaped) order is pinned by admiss-obligation-at-f2p-order. Every
#   reject witness was verified with real builds to (1) elaborate against its rival
#   (exit 0), (2) fail against the frozen solution (exit 1, goal reduces to
#   `False`, `h` reported unused — a semantic refutation, not a name/type error),
#   and (3) have a satisfiable hypothesis: the gate's probe cannot derive `False`
#   from it (exit 1), and the audit additionally exhibited each hypothesis as
#   INHABITED by `decide` under concrete assumed base-solver values consistent with
#   the flag dependence G-AX validates. pts=4 (four distinct refutation points over
#   three distinct sub-terms).
AXIOM_TESTS = []
