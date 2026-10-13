"""properties.py — G-PBT falsification battery for django__django-13794 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (four contracted methods, one per operand-position × carrier
combination of a binary combination of a deferred value with another operand).
None has a ``require`` clause, so the admitted domain is total; both operands of
each method are FREE inputs. A total domain does NOT make the admissibility lane
vacuous — see the ADMISSIBILITY block in ``SPEC_TESTS`` for the total-carrier
analogue (the obligation being unsatisfiable at an F2P-shaped input) and the two
cases that test it. Each method carries exactly ONE load-bearing
top-level ``ensures`` clause fixing the combined result AND that the combination
is NOT rejected (the success constructor):

  deferredConcatLeft  (forced other : List Char)  ensures out = Except.ok (forced ++ other)
  deferredConcatRight (forced other : List Char)  ensures out = Except.ok (other ++ forced)
  deferredSumLeft     (forced other : Int)         ensures out = Except.ok (forced + other)
  deferredSumRight    (forced other : Int)         ensures out = Except.ok (other + forced)

THE DISCRIMINATING CONTENT IS OPERAND ORDER (character carrier) and DEFINEDNESS
(the combination must succeed, not be rejected). ``forced`` is the underlying
value once forced; ``other`` is the other operand. The left-operand methods pin
``forced`` FIRST; the right-operand methods pin ``other`` FIRST. On the character
carrier those two orders differ; on the integer carrier they coincide (``+``
commutes), which is why the order attack lands on the character methods and the
integer methods are attacked instead on the DEFINEDNESS / value facet.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling makes it
    MANDATORY because both inputs there carry a fractional heap permission
    ``Acc(...,1/2)`` an impl can overwrite (write-to-realized forward,
    write-to-other reverse). Lean and Velvet are referentially transparent:
    every parameter is an immutable value, there is no heap, no aliasing, no
    fractional permission, and no method here declares a ``mut`` binder. There
    is no read-only input to overwrite and no substitute probe to build. The
    two nagini frame-mutation rivals therefore have no counterpart; not
    fabricated.
  * OPERAND-ORDER — APPLIES to the character methods and is the sharpest attack
    (nagini's ``weak-swap-order-fwd`` / ``weak-swap-order-rev``). A rival that
    returns the OTHER direction's concatenation matches the elements as a
    multiset but scrambles the order — exactly what the two-method (left vs
    right operand) fix exists to pin. Refuted at two distinct present operands.
  * PARTIAL-DOMAIN / off-by-one — APPLIES to the character methods (nagini's
    ``weak-drop-last-other-fwd``): drop the trailing element of the appended
    operand. Correct only when that operand is empty; wrong on the trailing
    element for every non-empty operand.
  * PREPATCH / rejected-combination — APPLIES to all four, and a rival is now
    written for all four (nagini's ``weak-empty-fwd`` at the value level).
    Pre-patch the deferred value cannot
    be combined and the operation is REJECTED (the ``+`` raises; the caller's
    ``except`` collapses it to the empty result). Modeled here as the rejection
    constructor ``Except.error``, which the load-bearing clause forbids (it
    demands the success constructor). This is the exact bug the fix corrects.
  * VALUE / dropped-operand — APPLIES to the integer methods, where the order
    attack collapses (``+`` commutes). A rival that drops one operand (returns
    the other unchanged) still violates the arithmetic clause off the diagonal.
  * UNGROUNDED-ORACLE ECHO — N/A. Every post-image is a total function of the
    method's own arguments (``++`` / ``+`` on the input carriers); the
    ``axioms`` region is empty (no opaque answer-key to echo). The positives are
    honest cheapest-reshape controls (nagini's ``pos-cached-bound-*``).

WITNESS PLACEMENT. Each reject case carries a Lean ``witness`` proving the rival
violates its method's load-bearing clause at ONE concrete input, checked in a
file whose ``prove_correct`` blocks are stripped (so no tactic script can mask
the verdict). Rivals do not share a refutation point. The two character-order
rivals are refuted at ``['a'] , ['b']`` (left) and ``['a'] , ['b']`` on the
DISTINCT method (right) — distinct methods, distinct testers. The drop-last
rival is refuted at ``['x'] , ['b']`` (a non-empty appended operand), the sub-
domain the order rival does not isolate. The integer value rivals are refuted at
``4 , 5`` (the F2P shape), off the ``forced = other`` diagonal so the dropped
operand is observable. The result carrier ``Except _ _`` needs a decidable
equality the tester's ``prove_postcondition_decidable_for`` does not synthesize
on its own, so each witness derives it first via ``deriving instance
DecidableEq for Except`` — an instance, not an assumption (no ``axiom`` /
``sorry`` / ``native_decide``), so the frozen solution still rejects each
witness.

DIVERGENCE LANE. This bundle runs under ``set_option
loom.semantics.termination "total"`` (open ``TotalCorrectness``), so a
non-terminating impl is REJECTED (``Decreasing annotations are required in total
correctness semantics``) rather than verifying vacuously, so the class is not a
spec hole here. Vacuous verification is the ``partial`` disposition and no velvet
bundle carries it. The nagini sibling carries no ``diverge-*`` /
``nonterm-*`` / ``weak-diverge`` case in any event (its two functions are
straight-line append loops), so there is nothing to port. No reject case is
written for it.

AUDIT NOTE (proof-shape, not a spec defect). An independent audit built a
correct reshape returning ``List.append forced other`` — definitionally the
frozen ``forced ++ other`` — and the FROZEN ``loom_solve`` leaves it open with
``⊢ Except.ok (forced.append other) = Except.ok (forced ++ other)``. That is a
TACTIC-normalization gap, not a spec that rejects a faithful impl: the same
reshape verifies (exit 0) as soon as the obligation is discharged with
``loom_solve <;> rfl``. It is recorded here rather than shipped as a positive
case because a positive whose proof body must be retuned tests the tactic, not
the contract; the four positives below all keep the frozen proof untouched.
Audit a7 reproduced this INDEPENDENTLY on the OTHER character method
(``List.append other forced`` on ``deferredConcatRight``: exit 1 with
``⊢ Except.ok (other.append forced) = Except.ok (other ++ forced)`` under the
frozen body, exit 0 under ``loom_solve <;> rfl``), which confirms the gap is a
property of ``List.append`` normalization and not of one method — and that it is
symmetric, so it hides nothing method-specific. Four further correct reshapes
verify with the frozen proof body UNTOUCHED (``<|`` pipe application, a type
ascription on the concatenation, a ``match`` on the appended operand relying on
``[] ++ other = other``, and ``Int.add`` on the integer carrier), so the spec is
not over-fit to the frozen spelling.

AUDIT NOTE (point-set adequacy, a7). Every shipped character witness sits at
operands of length <= 1, which is the kind of thin point set that lets a rival
wrong only on longer inputs slip through. Probed directly: an impl correct
exactly when both operands have length <= 1 and an impl correct exactly when the
forced value has length <= 1 are BOTH rejected (each with ``unsolved goals`` on
the load-bearing clause under an ``if_neg`` hypothesis), because the clause is
universally quantified — the thin witness points bound what the WITNESSES
discriminate, not what the spec admits. Same result for an impl wrong only at
negative integers, a sub-domain no shipped integer witness visits.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the changed binary
combination is modeled deeply and directly as ``++`` / ``+``). The nagini
sibling likewise has ``AXIOM_TESTS = []``. There is no axiom-soundness
obligation to probe, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13794"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each is the full frozen return line for one method
# ---- plus its closing `-- impl-end` marker, so a swap lies wholly inside that
# ---- method's single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). No case retunes a
# ---- proof body: every reshape below returns a value definitionally equal to
# ---- the frozen one, so the frozen `loom_solve` closes each unchanged.
_L_IMPL = "    return Except.ok (forced ++ other)\n    -- impl-end"
_R_IMPL = "    return Except.ok (other ++ forced)\n    -- impl-end"
_SL_IMPL = "    return Except.ok (forced + other)\n    -- impl-end"
_SR_IMPL = "    return Except.ok (other + forced)\n    -- impl-end"

for _a in (_L_IMPL, _R_IMPL, _SL_IMPL, _SR_IMPL):
    assert _BASE.count(_a) == 1, f"impl region drifted from expected text: {_a!r}"


def _impl(anchor, new_line):
    """Full Solution.lean variant with ONLY one method's impl-region return line
    replaced (the closing `-- impl-end` marker is re-appended)."""
    return _swap(_BASE, anchor, new_line + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `<name>Tester args = false` says the extracted program's result violates
# ---- the method's postcondition at that concrete input. The load-bearing
# ---- clause equates `out` to a value in `Except AddOutcome _`, and
# ---- `prove_postcondition_decidable_for` cannot synthesize `DecidableEq` for
# ---- that carrier on its own, so each witness derives the instance first. It
# ---- is an instance, not an assumption: no `axiom`, `sorry` or `native_decide`
# ---- is involved, and the frozen solution rejects these witnesses all the
# ---- same. Checked in a file whose `prove_correct` blocks have been stripped.
_DEC = "deriving instance DecidableEq for Except\n\n"


def _tester(method):
    return (_DEC +
            f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n")


SPEC_TESTS = [
    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — ADDED BY AUDIT a7.
    #
    # A previous pass recorded this lane `inexpressible` on the ground that no
    # method carries a `require` clause, so the admitted domain is total and
    # nothing could exclude an F2P-shaped input. The first half is true (there
    # is no `require` anywhere in the frozen file) but the conclusion does not
    # follow: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
    # obligation being UNSATISFIABLE at exactly an F2P-shaped input — a clause
    # that pins an unreachable post-image admits no impl at all, and every
    # rival would then be rejected for the wrong reason while the positives
    # (which are quantified over all inputs and closed by `loom_solve`) would
    # never localize it. That is testable directly, and I measured that it is:
    # each case discharges the load-bearing clause's post-image at the concrete
    # F2P point BY EVALUATION, as an in-region `have`, before closing the frozen
    # obligation verbatim. The `have` sits inside the `-- impl-start`/`--
    # impl-end` region (elided from the spec view, so `same_spec` holds) and the
    # frozen `prove_correct` body is NOT retuned — `loom_solve` absorbs the
    # extra `have` because it is already closed by `rfl` at the point of use.
    #
    # Both cases are LIVE, not decoration: asserting the WRONG post-image at the
    # same point fails the build (measured — `['l','a','z','y','s','t',...]`
    # gives `Tactic 'rfl' failed: ... is not definitionally equal to ...`, and
    # `Except.ok 10` for the integer point likewise), so a degenerate or
    # unsatisfiable clause could not pass these.
    # =====================================================================
    {
        "id": "admiss-concat-right-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # The primary F2P shape on the character carrier: an ordinary sequence
        # on the LEFT joined to a deferred value on the RIGHT, which mapping.md
        # §2 records as the operand position that F2P case actually exercises.
        # The `have` evaluates the clause's own post-image there and pins the
        # full joined sequence.
        "module": _impl(
            _R_IMPL,
            "    have hAdm : (Except.ok ((['s','t','r','i','n','g'] : List Char)"
            " ++ ['l','a','z','y'])\n"
            "                  : Except AddOutcome (List Char))\n"
            "                = Except.ok ['s','t','r','i','n','g','l','a','z','y'] := by\n"
            "      rfl\n"
            "    return Except.ok (other ++ forced)"),
        "rationale": (
            "the load-bearing clause `out = Except.ok (other ++ forced)` must be "
            "SATISFIABLE at the F2P-shaped input — an ordinary character "
            "sequence on the left joined to a deferred value on the right — and "
            "must pin a NON-DEGENERATE post-image there: the full joined "
            "sequence in the left-operand-first order, not an empty or "
            "collapsed result. The in-region `have` discharges exactly that by "
            "evaluation, and the method's own `ensures` still discharges under "
            "the untouched frozen proof. If it fails => PRECOND-TOO-STRONG / the "
            "obligation is unsatisfiable at the very input the change exists to "
            "fix, which no uniqueness rival would localize."
        ),
    },
    {
        "id": "admiss-sum-left-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # The integer-carrier F2P shape: two deferred numbers combined on the
        # numeric path, at the concrete point the failing numeric test uses.
        "module": _impl(
            _SL_IMPL,
            "    have hAdm : (Except.ok ((4 : Int) + 5) : Except AddOutcome Int)\n"
            "                = Except.ok 9 := by\n"
            "      rfl\n"
            "    return Except.ok (forced + other)"),
        "rationale": (
            "the integer analogue: `out = Except.ok (forced + other)` must be "
            "satisfiable and non-degenerate at the F2P numeric point (`4 , 5`), "
            "i.e. the clause must actually admit the total `9` there rather than "
            "pinning an unreachable value. Discharged by evaluation in-region "
            "with the frozen proof untouched. Note the tactic matters on this "
            "carrier: `decide` fails here with `failed to synthesize Decidable "
            "(Except.ok (4 + 5) = Except.ok 9)` because the result carrier has no "
            "`DecidableEq` instance in scope in the module (unlike the witness "
            "files, which derive one), while `rfl` closes it definitionally. If "
            "it fails => PRECOND-TOO-STRONG."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each stages the combined value through a typed
    # local before returning it; the value flow is unchanged, so the frozen
    # `loom_solve` still closes. The nagini sibling's positives cache the loop
    # bounds in locals (`nr`/`no`) — the same "restructure the body, keep the
    # value" shape, re-expressed for a carrier that has no loop.
    # =====================================================================
    {
        "id": "pos-concat-left-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_L_IMPL, "    let r := forced ++ other\n    return Except.ok r"),
        "rationale": (
            "binding the combined character sequence to a local before wrapping "
            "it in the success constructor leaves the returned value unchanged, "
            "so `out = Except.ok (forced ++ other)` still discharges; a "
            "structurally-different correct reshape must verify. If it fails => "
            "SPEC-TOO-STRONG (over-fit to the single-expression spelling)."
        ),
    },
    {
        "id": "pos-concat-right-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_R_IMPL, "    let r := other ++ forced\n    return Except.ok r"),
        "rationale": (
            "the right-operand analogue of pos-concat-left-local: staging "
            "`other ++ forced` through a typed local keeps the value, so "
            "`out = Except.ok (other ++ forced)` still discharges. If it fails "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-sum-left-commuted",
        "kind": "soundness",
        "expect": "verify",
        # `+` on Int is commutative, and the clause pins the numeric VALUE, not
        # the term order, so writing the sum the other way round is a correct
        # reshape that must verify.
        "module": _impl(_SL_IMPL, "    return Except.ok (other + forced)"),
        "rationale": (
            "commuting the two summands computes the same integer, so "
            "`out = Except.ok (forced + other)` is unchanged; a correct reshape "
            "must verify (else SPEC-TOO-STRONG on term order). The order swap "
            "that is a genuine attack on the character carrier is a no-op here "
            "precisely because integer `+` commutes — which is why the integer "
            "methods are attacked on the value/definedness facet instead."
        ),
    },
    {
        "id": "pos-sum-right-commuted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_SR_IMPL, "    return Except.ok (forced + other)"),
        "rationale": (
            "the right-operand analogue: commuting the summands keeps the "
            "integer, so `out = Except.ok (other + forced)` still discharges. "
            "If it fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================

    # ---- OPERAND ORDER (the sharpest attack; character carrier) ----
    {
        "id": "weak-swap-order-left",
        "kind": "uniqueness",
        "expect": "reject",
        # left-operand method returns the right-operand concatenation.
        "module": _impl(_L_IMPL, "    return Except.ok (other ++ forced)"),
        "refinement": (
            "the faithful real patch is a left-operand combiner that puts the "
            "other operand FIRST (operands swapped). On the character carrier "
            "that yields the reversed joining of a deferred value on the left "
            "with an ordinary sequence on the right, so the failing test that "
            "asserts the deferred value's characters appear in their original "
            "position observes them in the wrong place and still fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (forced ++ other)`: the impl proves "
            "`out = Except.ok (other ++ forced)`, which differs whenever the two "
            "operands are not equal as ordered prefixes (any two distinct "
            "present operands). Elements match as a multiset but the ORDER does "
            "not — the content the two-method fix defends. If it verified => "
            "SPEC-TOO-WEAK (operand order unpinned)."
        ),
        "witness": _tester("deferredConcatLeft") +
                   "example : deferredConcatLeftTester ['a'] ['b'] = false := by\n  decide\n",
    },
    {
        "id": "weak-swap-order-right",
        "kind": "uniqueness",
        "expect": "reject",
        # right-operand method returns the left-operand concatenation.
        "module": _impl(_R_IMPL, "    return Except.ok (forced ++ other)"),
        "refinement": (
            "the faithful real patch is a right-operand combiner that puts the "
            "forced value first (operands swapped). For the case an ordinary "
            "sequence on the left is joined to a deferred value on the right — "
            "dispatched to the right-operand combiner — it would place the deferred "
            "value's characters ahead of the left operand's, the wrong order, so "
            "the failing test asserting the left operand comes first still "
            "fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (other ++ forced)`: the impl proves "
            "the opposite order, which differs for any two distinct present "
            "operands. Refuted on the right-operand method's own tester, not the "
            "left method's — a distinct refutation point. If it verified => "
            "SPEC-TOO-WEAK (operand order unpinned on the right-operand method)."
        ),
        "witness": _tester("deferredConcatRight") +
                   "example : deferredConcatRightTester ['a'] ['b'] = false := by\n  decide\n",
    },

    # ---- PARTIAL-DOMAIN / off-by-one (character carrier) ----
    {
        "id": "weak-drop-last-left",
        "kind": "uniqueness",
        "expect": "reject",
        # appends the other operand EXCEPT its trailing element.
        "module": _impl(_L_IMPL, "    return Except.ok (forced ++ other.dropLast)"),
        "refinement": (
            "an off-by-one real patch that combined the forced value with all "
            "but the last element of the other operand would drop that operand's "
            "trailing character; the failing test that pins the FULL joined "
            "sequence loses its final character and still fails. Correct only "
            "when the other operand is empty. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (forced ++ other)`: the impl yields "
            "`forced ++ other.dropLast`, one element short for every non-empty "
            "other. Refuted at a non-empty other operand (`['x'] , ['b']`), the "
            "trailing-element sub-domain the order rivals do not isolate — so "
            "the `other` binder is varied across the reject lane rather than "
            "held at a single value. If it verified => SPEC-TOO-WEAK on the "
            "trailing element."
        ),
        "witness": _tester("deferredConcatLeft") +
                   "example : deferredConcatLeftTester ['x'] ['b'] = false := by\n  decide\n",
    },
    {
        "id": "weak-drop-last-right",
        "kind": "uniqueness",
        "expect": "reject",
        # right-operand method drops the trailing element of the forced value.
        "module": _impl(_R_IMPL, "    return Except.ok (other ++ forced.dropLast)"),
        "refinement": (
            "the right-operand analogue of weak-drop-last-left: an off-by-one "
            "real patch combining the other operand with all but the last "
            "element of the forced value would drop the deferred value's "
            "trailing character; the failing test pinning the full joined "
            "sequence still fails. Correct only when the forced value is empty. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (other ++ forced)`: the impl yields "
            "`other ++ forced.dropLast`, one element short for every non-empty "
            "forced. Refuted at `['x'] , ['a']` — a distinct point from the "
            "right-method order rival (`['a'] , ['b']`), so both `forced` and "
            "`other` are varied on the right-operand method rather than pinned. If "
            "it verified => SPEC-TOO-WEAK on the trailing element."
        ),
        "witness": _tester("deferredConcatRight") +
                   "example : deferredConcatRightTester ['x'] ['a'] = false := by\n  decide\n",
    },

    # ---- PREPATCH / rejected-combination (character + integer carriers) ----
    {
        "id": "weak-reject-left",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch outcome at the value level: the combination is REJECTED
        # rather than performed (modeled as the rejection constructor).
        "module": _impl(_L_IMPL, "    return Except.error .unsupported"),
        "refinement": (
            "this is the pre-change behaviour: with no left-operand handler the "
            "combination is rejected (the operator raises and the caller's "
            "except collapses it to the empty result). Its faithful real patch "
            "is the unpatched repo, which yields the empty result for the "
            "failing tests instead of the joined sequence and does NOT resolve — "
            "exactly the bug the fix corrects."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (forced ++ other)`: the clause pins "
            "the SUCCESS constructor carrying the joined sequence, and the impl "
            "returns the rejection constructor, so it fails at every input "
            "(refuted at `[] , []`, where even the degenerate combination must "
            "still succeed with the empty result). This is the definedness "
            "facet — that the combination is performed, not rejected. If it "
            "verified => SPEC-TOO-WEAK (the prepatch regression would go "
            "unnoticed)."
        ),
        "witness": _tester("deferredConcatLeft") +
                   "example : deferredConcatLeftTester [] [] = false := by\n  decide\n",
    },
    {
        # ADDED BY AUDIT. The header claimed the rejected-combination class
        # "APPLIES to all four" methods, but only three carried a definedness
        # rival: `deferredConcatRight` was attacked on the value/order facet
        # only (weak-swap-order-right, weak-drop-last-right), so the one clause
        # whose own docstring says the combination must succeed "even when the
        # left operand cannot by itself combine with a deferred value" had no
        # rival testing that it is pinned. Rebuilt and confirmed rejected.
        "id": "weak-reject-concat-right",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_IMPL, "    return Except.error .unsupported"),
        "refinement": (
            "the right-operand character-carrier prepatch image: with no "
            "right-operand handler the combination is rejected outright, so the "
            "failing test that joins an ordinary sequence on the left to a "
            "deferred value on the right observes the empty result rather than "
            "the joined sequence and does NOT resolve. This is the operand "
            "position that has no left-operand fallback to rescue it, so the "
            "unpatched repo fails it unconditionally."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (other ++ forced)`: the clause pins "
            "the SUCCESS constructor carrying the joined sequence and the impl "
            "returns the rejection constructor, so it fails at every input. "
            "Refuted at `[] , ['b']` — the degenerate-`forced` boundary, "
            "distinct from every other point on this method (the order rival "
            "sits at `['a'] , ['b']`, the off-by-one rival at `['x'] , ['a']`) "
            "and from weak-reject-left's `[] , []`. This is the DEFINEDNESS "
            "facet on the right-operand character method, the only "
            "clause/facet pair the battery previously left unattacked. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _tester("deferredConcatRight") +
                   "example : deferredConcatRightTester [] ['b'] = false := by\n  decide\n",
    },

    # ---- VALUE / dropped-operand (integer carrier; order attack collapses) ----
    {
        "id": "weak-sum-left-drops-other",
        "kind": "uniqueness",
        "expect": "reject",
        # returns the forced value alone, ignoring the other summand.
        "module": _impl(_SL_IMPL, "    return Except.ok forced"),
        "refinement": (
            "a real patch that returned the forced value instead of its sum "
            "with the other operand would leave numeric combination of a "
            "deferred value on the left broken; the failing test that adds two "
            "deferred numbers and checks their total still observes the wrong "
            "value and does NOT resolve. Correct only when the other operand is "
            "the additive identity."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (forced + other)`: the impl drops the "
            "other summand. Refuted at `4 , 5` (the F2P shape), off the "
            "`forced = other` diagonal so the dropped operand is observable. The "
            "order-swap attack is a no-op on this carrier (integer `+` "
            "commutes), so the integer methods are attacked on the value facet. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _tester("deferredSumLeft") +
                   "example : deferredSumLeftTester 4 5 = false := by\n  decide\n",
    },
    {
        "id": "weak-sum-right-drops-forced",
        "kind": "uniqueness",
        "expect": "reject",
        # returns the other operand alone, ignoring the forced value.
        "module": _impl(_SR_IMPL, "    return Except.ok other"),
        "refinement": (
            "the right-operand analogue: a real patch that returned the other "
            "operand instead of its sum with the forced value would leave "
            "numeric combination of a deferred value on the right broken; the "
            "failing test still observes the wrong total and does NOT resolve. "
            "Correct only when the forced value is the additive identity."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (other + forced)`: the impl drops the "
            "forced summand. Refuted at `4 , 5` on the right-operand method's own "
            "tester. This rival abuses the `forced` binder where "
            "weak-sum-left-drops-other abuses `other`, so both integer summands "
            "are exercised. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _tester("deferredSumRight") +
                   "example : deferredSumRightTester 4 5 = false := by\n  decide\n",
    },
    {
        "id": "weak-reject-sum-left",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch outcome on the integer carrier: the numeric combination
        # is REJECTED rather than performed.
        "module": _impl(_SL_IMPL, "    return Except.error .unsupported"),
        "refinement": (
            "the integer-carrier prepatch image: with no left-operand handler "
            "the numeric combination is rejected (the operator raises). Its "
            "faithful real patch is the unpatched repo, which fails to add two "
            "deferred numbers and does NOT resolve — the bug the fix corrects on "
            "the numeric path."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (forced + other)`: the clause pins the "
            "SUCCESS constructor and the impl returns the rejection constructor, "
            "so it fails at every input. Refuted at `1 , 2` — a distinct point "
            "from weak-sum-left-drops-other (`4 , 5`), and the definedness facet "
            "the value rival does not attack. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _tester("deferredSumLeft") +
                   "example : deferredSumLeftTester 1 2 = false := by\n  decide\n",
    },
    {
        "id": "weak-reject-sum-right",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SR_IMPL, "    return Except.error .unsupported"),
        "refinement": (
            "the right-operand integer prepatch image: without a right-"
            "operand handler the numeric combination is rejected, so the failing "
            "test that adds a deferred number on the right does NOT resolve on "
            "the unpatched repo."
        ),
        "rationale": (
            "REJECT from `out = Except.ok (other + forced)`: the impl returns "
            "the rejection constructor where the clause demands success. Refuted "
            "at `1 , 2` — a distinct point from weak-sum-right-drops-forced "
            "(`4 , 5`), attacking the definedness facet on the right-operand method. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _tester("deferredSumRight") +
                   "example : deferredSumRightTester 1 2 = false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 2 order rivals, 1
# partial-domain rival, 1 prepatch-empty rival; AXIOM_TESTS empty) over TWO
# functions `forward_combine(realized, other)` / `reverse_combine(realized,
# other)` on a `List[int]` carrier under a PSeq value abstraction, both inputs
# held at a fractional heap permission `Acc(...,1/2)`.
#
# This velvet bundle models the SAME two operand positions but splits each
# across TWO value carriers the nagini sibling folds into one List[int]: the
# character carrier (`deferredConcat{Left,Right}` on List Char) and the integer
# carrier (`deferredSum{Left,Right}` on Int), because the fix's observable
# order-sensitivity differs between them (strings order-sensitive, ints
# commutative). So the four velvet methods are the (position × carrier) matrix
# of the two nagini functions.
#
#   nagini case                -> here
#   -----------------------------------------------------------------------
#   pos-cached-bound-fwd       -> pos-concat-left-local     RE-SHAPED
#   pos-cached-bound-rev       -> pos-concat-right-local     RE-SHAPED
#                                 (+ pos-sum-left-commuted / pos-sum-right-commuted
#                                    ADDED — the integer-carrier positives)
#   admiss-reads-fwd           -> admiss-concat-right-f2p    RE-AIMED (audit a7)
#                                 (+ admiss-sum-left-f2p      ADDED — integer carrier)
#   frame-mut-realized-fwd     -> (none)                     VACUOUS (no heap/mut)
#   frame-mut-other-rev        -> (none)                     VACUOUS (no heap/mut)
#   weak-swap-order-fwd        -> weak-swap-order-left        PORTED
#   weak-swap-order-rev        -> weak-swap-order-right       PORTED
#   weak-drop-last-other-fwd   -> weak-drop-last-left         PORTED
#                                 (+ weak-drop-last-right ADDED — the right-operand
#                                    off-by-one, for `forced`/`other` coverage)
#   weak-empty-fwd             -> weak-reject-left            PORTED (re-expressed)
#                                 (+ weak-reject-concat-right /
#                                    weak-sum-left-drops-other /
#                                    weak-sum-right-drops-forced /
#                                    weak-reject-sum-left / weak-reject-sum-right
#                                    ADDED — the integer-carrier value and
#                                    definedness rivals, plus the right-operand
#                                    CHARACTER definedness rival added by audit)
#
# 4 ported, 2 re-shaped positives, 1 re-aimed (admissibility), 2 vacuous
# (frame-mutation only), 7 added for integer-carrier, right-operand-method and
# admissibility coverage.
#
# PORTED (4): the two ORDER rivals carry across intact — only the carrier
#   changes from a List[int] under PSeq to List Char, and the discriminator
#   (return the other direction's concatenation) is identical. The PARTIAL-
#   DOMAIN off-by-one carries across as dropLast on the appended operand. The
#   PREPATCH-empty rival is RE-EXPRESSED: nagini modeled the prepatch raise-then-
#   `except: return ''` at the value level as the empty sequence `[]`; this
#   carrier models the two outcomes as the two `Except` constructors
#   (mapping.md §2), so the faithful prepatch image is the REJECTION constructor
#   `Except.error`, refuted by the load-bearing clause's success-constructor
#   demand. (The empty-sequence spelling is not available as a "wrong" value
#   here because the success clause pins the concatenation exactly, so the empty
#   result is refuted the same way at any non-empty operand — but the sharper
#   and more faithful prepatch image is the rejection, which fails even at the
#   empty/empty degenerate input.)
# RE-SHAPED (2 positives): the nagini positives cache the loop bounds in locals
#   (`nr`/`no`) plus trivially-preserved length invariants — "restructure the
#   body, keep the value". This carrier has no loop, so the cheapest structurally-
#   different correct impl is staging the combined value through a typed local.
# ADDED (6): four on the integer carrier, one right-operand off-by-one, and one
#   right-operand character definedness rival (weak-reject-concat-right). The
#   nagini sibling folds strings and ints into one List[int] carrier, so it has
#   no separate integer methods to attack. This bundle models them separately
#   (mapping.md), and a battery that never exercised the integer methods would
#   leave two of the four obligations undefended and unattacked.
#   pos-sum-{left,right}-commuted defend them; weak-sum-left-drops-other /
#   weak-sum-right-drops-forced attack them on the VALUE facet (the order-swap
#   attack collapses because integer `+` commutes — pos-sum-*-commuted is exactly
#   that no-op, verifying), and weak-reject-sum-{left,right} attack them on the
#   DEFINEDNESS facet (the rejection constructor). weak-drop-last-right is the
#   right-operand off-by-one, added so the right-concat method's `forced` and
#   `other` binders are both varied. weak-reject-concat-right closes the last
#   clause x facet cell: before it, `deferredConcatRight` was the only method
#   attacked on the value/order facet ALONE, so the demand that the combination
#   succeed rather than be rejected went untested on exactly the operand
#   position that has no fallback to rescue it. Each rival is a real divergence
#   with a machine-checked witness, not fabricated wrongness.
# RE-AIMED (1 + 1 added): admiss-reads-fwd. The nagini control confirms the
#   fractional half-permission ADMITS the reads a normal operand pair needs —
#   i.e. it probes a non-trivial PRECONDITION. There is no heap permission and no
#   `require` clause on any method here, so the literal "a normal input is
#   in-domain" probe has nothing to falsify. An earlier pass stopped there and
#   recorded the whole lane inexpressible; audit a7 found that wrong. On a total
#   carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#   UNSATISFIABLE at an F2P-shaped input, which is expressible and now tested by
#   admiss-concat-right-f2p (character carrier, the operand position the primary
#   F2P exercises) and admiss-sum-left-f2p (integer carrier). The claim the old
#   note leaned on — that "the four soundness positives already witness
#   satisfiability" — does not substitute: those positives are universally
#   quantified and closed by `loom_solve`, so they never name a concrete point,
#   and a degenerate clause would fail them for reasons no case could localize.
#   Both new cases are demonstrably live (the wrong post-image at the same point
#   fails the build).
# VACUOUS (2):
#   * frame-mut-realized-fwd / frame-mut-other-rev — MANDATORY on nagini because
#     both inputs are `Acc(...,1/2)` read-only and a write must be rejected for
#     insufficient permission. Lean/Velvet are referentially transparent: no
#     heap, no aliasing, no fractional permission, no `mut` binder anywhere in
#     this bundle. There is no read-only input to overwrite and no permission
#     system to violate, so the class is vacuous and no substitute is fabricated.
# DIVERGENCE: the nagini sibling carries no diverge-*/nonterm-*/weak-diverge case
#   (both functions are straight-line append loops), so there is nothing to
#   port. This bundle runs under `total` termination semantics, where a
#   non-terminating impl is REJECTED for missing decreasing annotations rather
#   than verifying vacuously, so the class is not even a spec hole here. Vacuous
#   verification is the `partial` disposition and no velvet bundle carries it;
#   an omitted clause fails with `Decreasing annotations are required in total
#   correctness semantics`, and a clause whose measure does not shrink fails on
#   its own descent goal.
#   No reject case is written for it.
#
# BINDER / CLAUSE / POINT COVERAGE. All four load-bearing clauses are defended
#   (>=1 positive each) and attacked (>=1 reject each), and two of the four are
#   additionally pinned at a concrete F2P point by the admissibility cases (one
#   per carrier). Binders: on the character
#   methods `forced` and `other` are both varied — the order rivals sit at
#   `['a'] , ['b']`, the drop-last rival at `['x'] , ['b']` (a distinct `forced`
#   AND a non-empty `other`), and the reject-left rival at `[] , []` (the empty
#   boundary). On the integer methods `forced` and `other` are exercised on both
#   summand positions (left-drops-other abuses `other`, right-drops-forced
#   abuses `forced`), refuted off the `forced = other` diagonal at `4 , 5` so
#   neither is masked. The reject witnesses probe five distinct input points
#   across the four methods, so no binder is pinned at a single value.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the binary combination is modeled deeply as `++` / `+`), so there is
# nothing there to probe. The nagini sibling likewise ships AXIOM_TESTS = [].
AXIOM_TESTS = []
