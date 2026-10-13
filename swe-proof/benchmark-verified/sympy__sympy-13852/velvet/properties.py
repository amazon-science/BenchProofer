"""properties.py — G-PBT falsification battery for sympy__sympy-13852 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
both ``prove_correct`` obligations survive with byte-identical headers) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness ELABORATES against the rival and FAILS against the
frozen solution).

DEFENDED SURFACE (two contracted methods over read-only ``Int`` inputs):

  recognizeClosedForm (s : Int) (zTag : Int) return (out : Int)
      ensures out = closedFormFor s zTag                        -- (C1) cascade
      ensures zTag = zC → out = cfZc                            -- (C2)
      ensures (s = sSpecial ∧ zTag = z1) → out = cfP1            -- (C3)
      ensures (s = sSpecial ∧ zTag = z2) → out = cfP2            -- (C4)
      ensures (s = sKeyA ∧ zTag = zOther) → out = cfSa           -- (C5)
      ensures (s = sKeyB ∧ zTag = zOther) → out = cfSb           -- (C6)
      ensures (zTag = zA ∧ s = sKeyA) → out = cfZa               -- (C7) priority
  seriesExpansionAtOne (s : Int) return (out : Int)
      require s = sExpand
      ensures out = expansionCode                               -- (E1)
      ensures out = expPlain                                    -- (E2)
      ensures out ≠ expPolar                                    -- (E3)

``closedFormFor`` is a PRIORITY CASCADE over the discrete argument pattern: the
three z-keyed clauses match first for ANY ``s``; then, at the distinguished
``sSpecial``, six special second-argument values; then two s-keyed clauses; an
unrecognised pattern yields ``cfUneval`` (no closed form — the call stays
unevaluated). C1 is load-bearing (the whole cascade); C2–C7 pin individual
patterns and the z-before-s priority explicitly.

NO UNGROUNDED ORACLE. The ``axioms`` region is EMPTY and ``closedFormFor`` /
``expansionCode`` are fully-unfolded ``def``s over the method's own arguments —
their body IS the computation. So there is no opaque answer-key a wrong impl
could echo, and the cheapest honest impl (``return closedFormFor s zTag``) does
the work: it is a POSITIVE CONTROL, not a cheat. The real attack surface is
PARTIAL-DOMAIN / MIS-BINDING / PRIORITY / OVER-FIRE over the cascade, where a
rival is correct on most patterns and diverges on a load-bearing one.

Independently attackable sub-obligations of the cascade:

  * PATTERN PRESENCE — each recognised pattern must produce a GENUINE closed
    form, never ``cfUneval`` (dropping a clause leaves the call unevaluated).
  * CODE BINDING — each pattern must produce the code that names ITS OWN closed
    form, not another pattern's (a permutation of codes is wrong everywhere the
    permutation moves something).
  * PRIORITY — the z-keyed clauses win over the s-keyed clauses at a pattern
    both would match; C7 pins the one overlap point concretely.
  * NO OVER-FIRE — an unrecognised pattern must produce ``cfUneval``; a rival
    that hands back some closed form there claims a value the behaviour does not
    take. Two independent fall-throughs (the distinguished-s block's, and the
    cascade's outermost one).
  * BRANCH-FREE EXPANSION — the distinguished-parameter expansion is the
    elementary form, never the branch-factored one (E1–E3).

CARRIER NOTE — WHY EVERY WITNESS IS DECIDABLE HERE. Both methods are loop-free
straight-line code over ``Int`` with no opaque callee anywhere in the spec, so
each extracted ``…Exec`` reduces by kernel computation at any literal
``(s, zTag)`` and the tester from ``derive_tester_for`` evaluates to a literal
``Bool``. Every witness below is therefore stated at FULLY CONCRETE integer
inputs and closes by ``decide``; no witness binds a hypothesis, so no witness
carries a joint-satisfiability obligation (the "condition on the carrier"
technique is not needed on this carrier). Each half was confirmed during
authoring with two real ``scripts/lean_verify.sh`` builds per reject case: the
witness file elaborates green against its rival (exit 0) and errors against the
frozen solution (exit 1). Independently RE-DERIVED by audit — every witness
rebuilt on both sides, plus a flipped-claim forgery on both sides, plus the
rival's own build; see the footer's INDEPENDENT AUDIT entry for the exit codes
and for the one gold-side signature class that appears here (a plain evaluation
refutation, in all 13 cases).

GATED vs PINNED-BUT-NON-GATING REJECTS. The single failing test probes the
dispatch at a specific sub-domain: the two symbolic assertions at the
distinguished ``s`` with ``z1`` / ``z2``; a numeric-agreement loop over the six
distinguished-s special second arguments; and a numeric-agreement loop over
``s ∈ {sKeyB, sKeyA, sExpand}`` at generic (unrecognised) second arguments.

THE GATING CRITERION, AND THE TRAP IN IT (corrected by audit — an earlier
revision of this file mislabelled two rivals). Both numeric loops are
SELF-CONSISTENCY comparisons: they compare the auto-evaluated result against the
SAME call constructed with auto-evaluation suppressed, and require agreement to
within 1e-15. That shape is blind to a MISSING clause and sensitive only to a
WRONG one:

  * a rival that DROPS a clause never fires the auto-evaluation, so the
    compared sides are the same unevaluated object, their difference is exactly
    zero, and the assertion PASSES. A dropped clause is invisible to both loops.
  * a rival that MIS-BINDS or OVER-FIRES a clause fires to a different number
    than the suppressed call evaluates to, so the bound is violated and the
    assertion FAILS.

So a dropped clause is gated ONLY where some SYMBOLIC assertion names its exact
pattern — which is true of the two distinguished-s patterns ``z1`` / ``z2`` and
of nothing else. SIX rivals below are wrong INSIDE the failing test's
sub-domain in a way the test can actually SEE — their faithful counterparts fail
it outright, so each is a true verify-does-not-imply-resolve break and is
labelled ``GATED``. SEVEN rivals are wrong OUTSIDE it: they violate a clause the
frozen spec pins DELIBERATELY (C2, C5, C6, C7, the two z-keyed clauses no
per-pattern conjunct names, the distinguished-s fall-through, E1–E3) or a
sub-domain of C1 the test never reaches, which is what keeps the spec at least
as strong as the real change
rather than merely as strong as the test. Their faithful counterparts regress
behaviour the real change PRESERVES or fail to ADD behaviour the change adds
without the gated test noticing, so they are labelled ``NON-GATING`` in their
own ``refinement`` and the ``verify ⟹ resolved`` direction is unaffected (the
spec is an intentional conjunction the faithful change satisfies in full — the
same disposition the nagini sibling records for its expansion rival). Dropping
them would leave C2, C7 and the second method's obligation unattacked, so they
ship WITH the disclosure rather than silently.

The two s-keyed clause pins C5/C6 are attacked BOTH ways for this reason: by the
two clause-DROPPING rivals (non-gating, because a drop is invisible to a
self-consistency loop) and by the code-PERMUTING rival that keeps both clauses
firing and exchanges their codes (gated, because a wrong value is exactly what
the loop can see). Without the permuting rival the s-keyed conjuncts would be
defended only by non-gating cases.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS positives — APPLY. Three structurally different CORRECT impls
    must verify or the spec is SPEC-TOO-STRONG on impl shape.
  * ADMISSIBILITY — APPLIES, in the non-degeneracy form (see the case).
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling records this class N/A
    already (both of its functions take by-value ``int`` parameters, so it has
    no half-permission input and no mutable container). Here the same holds by
    construction and more strongly: Lean and Velvet are referentially
    transparent, ``s`` and ``zTag`` are immutable values, no ``mut`` binder is
    declared, and there is no heap, no aliasing and no permission system. Not
    fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * AXIOM_TESTS — dropped (G-AX's lane).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13852"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each lies WHOLLY inside one editable region (an
# `-- impl-start`/`-- impl-end` body, or a `prove_correct` tactic body) and is
# unique in Solution.lean — both facts asserted at import so the manifest breaks
# loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole frozen cascade impl of the first method (inside its impl region).
_GOLD_RCF = """    let result : Int :=
      if zTag = zA then cfZa
      else if zTag = zB then cfZb
      else if zTag = zC then cfZc
      else if s = sSpecial then
        (if zTag = z1 then cfP1
         else if zTag = z2 then cfP2
         else if zTag = z3 then cfP3
         else if zTag = z4 then cfP4
         else if zTag = z5 then cfP5
         else if zTag = z6 then cfP6
         else cfUneval)
      else if s = sKeyA then cfSa
      else if s = sKeyB then cfSb
      else cfUneval
    return result"""
assert _BASE.count(_GOLD_RCF) == 1, "cascade impl anchor drift — re-sync _GOLD_RCF"

# The frozen impl of the second method. `return expPlain` alone is NOT unique
# (it is also the body of the pure `expansionCode`), so the anchor spans the
# impl-region markers and they are re-wrapped by `_ser`.
_GOLD_SER = "    -- impl-start\n    return expPlain\n    -- impl-end"
assert _BASE.count(_GOLD_SER) == 1, "expansion impl anchor drift — re-sync _GOLD_SER"

# The frozen tactic body of the first obligation. Retuned by exactly one case (a
# positive control whose reshape changes the residual goal's shape); the
# `prove_correct recognizeClosedForm` HEADER is preserved verbatim in every
# variant, and the tactic body is elided from the consumer spec view.
_GOLD_RCF_PROOF = """prove_correct recognizeClosedForm by
  loom_solve <;>
    simp_all [closedFormFor, zA, zB, zC, z1, z2, z3, z4, z5, z6, zOther,
      sSpecial, sKeyA, sKeyB, cfUneval, cfZa, cfZb, cfZc,
      cfP1, cfP2, cfP3, cfP4, cfP5, cfP6, cfSa, cfSb]"""
assert _BASE.count(_GOLD_RCF_PROOF) == 1, "cascade proof anchor drift"


def _rcf(body, proof=None):
    """Variant editing ONLY the first method's impl region (and optionally its
    tactic body); the second method is left at the frozen impl."""
    src = _swap(_BASE, _GOLD_RCF, body)
    return _swap(src, _GOLD_RCF_PROOF, proof) if proof else src


def _ser(body):
    """Variant editing ONLY the second method's impl region (markers
    re-wrapped); the first method is left at the frozen impl."""
    return _swap(_BASE, _GOLD_SER,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


def _tester(method, body):
    """Witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
    so a witness reaches it through Velvet's own tester machinery:
    `<method>Tester <args> = false` says the extracted program's result violates
    that method's postcondition at the concrete argument pattern. Checked in a
    file whose `prove_correct` blocks have been stripped, so no tactic script can
    mask the verdict. Both names come from directives inside the witness itself,
    so they exist in the rival build and the gold build alike."""
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n" + body)


def _lit(n):
    """A concrete `Int` as a Lean ARGUMENT. Negative literals MUST be
    parenthesised: bare `Tester -1 0` parses as `HSub.hSub Tester 1 0`, i.e.
    subtraction, not application at -1. That misparse does not fail loudly — it
    elaborates to a different (unprovable) goal and the case reports
    `witness-unproven`, which reads exactly like "the rival is not actually
    wrong here". One reject below binds a negative parameter value, so this is
    load-bearing, not defensive."""
    return f"({n})" if n < 0 else f"{n}"


def _rcf_witness(*points):
    """`recognizeClosedFormTester s zTag = false` at each concrete pattern."""
    return _tester("recognizeClosedForm", "\n\n".join(
        f"example : recognizeClosedFormTester {_lit(s)} {_lit(z)} = false "
        f":= by\n  decide"
        for s, z in points) + "\n")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. A correct impl the spec rejects is SPEC-TOO-STRONG.
    # =====================================================================

    # The cheapest honest impl: return the grounded pure cascade directly. This
    # is NOT an ungrounded-oracle echo — `closedFormFor`'s body IS the dispatch,
    # fully unfolded over `s`/`zTag`, so returning it performs the recognition
    # work. Doubles as the no-answer-key control. Frozen proof unchanged.
    {
        "id": "pos-echo-grounded-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _rcf("    return closedFormFor s zTag"),
        "rationale": (
            "`closedFormFor` is a fully-unfolded pure function of this method's "
            "OWN two arguments (the `axioms` region is empty; there is no opaque "
            "term in the spec), so returning it satisfies C1 by definition and "
            "C2–C7 by the cascade's own case analysis — it does the recognition "
            "work rather than echoing an answer-key. Maximally different from the "
            "frozen `let`-bound if-ladder while behaviourally identical, so it "
            "must verify, else the spec is SPEC-TOO-STRONG on impl shape. Also "
            "the ungrounded-echo control: if this were a cheat the postcondition "
            "would be pinned to something other than the inputs, and it is not. "
            "(Sibling: pos-echo-grounded-oracle.)"),
    },

    # Reorder every DISJOINT equality test: the six distinguished-s tests run
    # last-to-first, and the two s-keyed tests are swapped. The branches are
    # pairwise disjoint equality tests, so order is irrelevant there; the z-keyed
    # priority block is untouched. The reshape changes the residual goal's
    # if-ladder shape, so the frozen `simp_all` leaves a linear-arithmetic
    # residual — cleared by appending `omega` to the tactic body (the body is
    # elided from the spec view; the obligation header is byte-identical and no
    # lemma, axiom or `sorry` is introduced). No loop, so no induction is needed.
    {
        "id": "pos-reorder-disjoint-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _rcf(
            "    let result : Int :=\n"
            "      if zTag = zA then cfZa\n"
            "      else if zTag = zB then cfZb\n"
            "      else if zTag = zC then cfZc\n"
            "      else if s = sSpecial then\n"
            "        (if zTag = z6 then cfP6\n"
            "         else if zTag = z5 then cfP5\n"
            "         else if zTag = z4 then cfP4\n"
            "         else if zTag = z3 then cfP3\n"
            "         else if zTag = z2 then cfP2\n"
            "         else if zTag = z1 then cfP1\n"
            "         else cfUneval)\n"
            "      else if s = sKeyB then cfSb\n"
            "      else if s = sKeyA then cfSa\n"
            "      else cfUneval\n"
            "    return result",
            _GOLD_RCF_PROOF + " <;>\n    omega"),
        "rationale": (
            "the six distinguished-s tests and the two s-keyed tests are "
            "pairwise-disjoint equality tests on the same binder, so permuting "
            "them preserves the cascade pointwise; the z-keyed priority block is "
            "unchanged, so C7 still holds. C1–C7 therefore still hold on the "
            "whole domain and a correct restructure must verify, else the spec is "
            "SPEC-TOO-STRONG on branch ORDER — which would be a real defect, "
            "because branch order is exactly what the near-miss rivals below "
            "abuse and the spec must reject only the order changes that alter a "
            "VALUE. (Sibling: pos-reorder-disjoint-branches.)"),
    },

    # Bind the expansion result through a typed local, then return it.
    {
        "id": "pos-series-local-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _ser("    let r : Int := expansionCode\n    return r"),
        "rationale": (
            "a local-binding reshape of the distinguished-parameter expansion "
            "that names the grounded pure model instead of the code literal — "
            "same value, different SSA shape — so E1/E2/E3 all still hold. Must "
            "verify, else the spec is SPEC-TOO-STRONG on impl shape. Grounded, "
            "not an echo: `expansionCode` is a fully-unfolded `def`, not an "
            "opaque term. (Sibling: pos-series-local-binding.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling asserts (in-region) that the pure cascade the
    # postcondition is pinned to actually computes the load-bearing answers for
    # representative in-domain argument patterns. Ported directly, and sharpened:
    # the first method has NO `require` clause (its pre-conditions region is
    # empty, so every `(s, zTag)` is admitted and a plain "the precondition
    # admits an F2P-shaped input" probe would be vacuous). The residual risk on a
    # total domain is that the post-image is DEGENERATE at the interesting
    # points — a cascade collapsing to one value would read exactly like a
    # cascade every impl meets. The assert pins six representative patterns to
    # SIX PAIRWISE-DISTINCT outcomes, including that an unrecognised pattern at
    # the distinguished s really does yield NO closed form, and that the z-keyed
    # clause really does win over the s-keyed one at their overlap. Frozen impl
    # and frozen proof are BOTH kept verbatim, so the method's own obligation
    # still discharges honestly. The assert is LIVE, not decoration: replacing
    # one conjunct with a false claim about the same point leaves `⊢ False`
    # unsolved (confirmed with a real build during authoring).
    # =====================================================================
    {
        "id": "admiss-cascade-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rcf(
            "    assert (with_name_prefix `admiss\n"
            "      (closedFormFor sSpecial z2 = cfP2 ∧ closedFormFor sSpecial z1 = cfP1\n"
            "        ∧ closedFormFor sKeyA zOther = cfSa ∧ closedFormFor sKeyB zOther = cfSb\n"
            "        ∧ closedFormFor sKeyA zA = cfZa ∧ closedFormFor sSpecial zOther = cfUneval))\n"
            + _GOLD_RCF),
        "rationale": (
            "the post-image is SATISFIABLE and NON-DEGENERATE at six "
            "representative in-domain argument patterns, which the empty "
            "pre-conditions region admits: the two symbolically-asserted "
            "distinguished-s patterns produce their own DISTINCT closed forms; "
            "each s-keyed pattern at an unrecognised second argument produces its "
            "own; the z-keyed clause WINS at the one pattern where it overlaps an "
            "s-keyed clause; and an unrecognised pattern at the distinguished s "
            "produces NO closed form. So the cascade genuinely discriminates the "
            "patterns the failing test cares about instead of collapsing to a "
            "constant, and the obligation is not unsatisfiable (else "
            "PRECOND-TOO-STRONG / a degenerate post-image). The in-region assert "
            "must discharge AND the frozen impl and frozen proof are kept "
            "verbatim, so C1–C7 discharge too. (Sibling: admiss-f2p-shaped.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete argument pattern, plus the refinement argument. Labelled
    # GATED (wrong inside the failing test's sub-domain) or NON-GATING (violates
    # a clause the spec pins deliberately) — see the module docstring.
    # =====================================================================

    # ---- GATED: PATTERN PRESENCE, the two symbolically-asserted patterns -----

    {
        "id": "reject-drop-special-z2",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `z2` clause from the distinguished-s block: that pattern falls
        # through to the block's else and yields cfUneval.
        "module": _rcf(_GOLD_RCF.replace(
            "         else if zTag = z2 then cfP2\n", "", 1)),
        "refinement": (
            "GATED. Omitting this clause leaves the distinguished-s call at this "
            "special second argument UNEVALUATED, so the failing test's FIRST "
            "symbolic assertion — an exact structural equality between the call "
            "and its closed form — compares an unevaluated instance against that "
            "closed form and is False. The test fails on its first line, so a "
            "faithful counterpart would NOT resolve. Correct on every other "
            "pattern; the divergence is exactly this one."),
        "rationale": (
            "REJECT from C4 `(s = sSpecial ∧ zTag = z2) → out = cfP2` and from C1: "
            "the cascade demands cfP2 at this pattern and the rival hands back "
            "cfUneval. If it verified => SPEC-TOO-WEAK on the PATTERN PRESENCE "
            "sub-obligation (a recognised pattern left with no closed form). "
            "Refuted at (sSpecial, z2). (Sibling: weak-drop-special-z2.)"),
        "witness": _rcf_witness((2, 5)),
    },

    {
        "id": "reject-drop-special-z1",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `z1` clause; the block now opens on `z2`.
        "module": _rcf(_GOLD_RCF.replace(
            "        (if zTag = z1 then cfP1\n"
            "         else if zTag = z2 then cfP2\n",
            "        (if zTag = z2 then cfP2\n", 1)),
        "refinement": (
            "GATED. Omitting this clause leaves the distinguished-s call at the "
            "other special second argument UNEVALUATED — the very argument "
            "pattern the reported issue opens with. The failing test's SECOND "
            "symbolic assertion then compares an unevaluated instance against its "
            "closed form and is False, so a faithful counterpart would NOT "
            "resolve. Correct on every other pattern, including the first "
            "symbolic assertion's, so it is a strictly narrower miss than a "
            "rival that drops the whole block."),
        "rationale": (
            "REJECT from C3 `(s = sSpecial ∧ zTag = z1) → out = cfP1` and from C1: "
            "the cascade demands cfP1 at this pattern and the rival hands back "
            "cfUneval. If it verified => SPEC-TOO-WEAK on PATTERN PRESENCE. "
            "Refuted at (sSpecial, z1) — a DIFFERENT point from the z2 rival, so "
            "the two do not share a witness. (Sibling: weak-drop-special-z1.)"),
        "witness": _rcf_witness((2, 4)),
    },

    # ---- GATED: CODE BINDING (a permutation, not an omission) ----------------

    {
        "id": "reject-swap-p1-p2",
        "kind": "uniqueness",
        "expect": "reject",
        # Both clauses PRESENT and both firing — but bound to each other's code.
        # A pattern-presence check alone would pass this rival.
        "module": _rcf(_GOLD_RCF
                       .replace("        (if zTag = z1 then cfP1\n",
                                "        (if zTag = z1 then cfP2\n", 1)
                       .replace("         else if zTag = z2 then cfP2\n",
                                "         else if zTag = z2 then cfP1\n", 1)),
        "refinement": (
            "GATED, and doubly so. Both patterns still auto-evaluate — so a "
            "faithful counterpart is not caught by any 'does it evaluate at all' "
            "check — but each produces the OTHER pattern's closed form. BOTH of "
            "the failing test's symbolic assertions then compare the call against "
            "a closed form it does not equal, and both are False, so it would NOT "
            "resolve. This is the near-miss the sibling's discrimination control "
            "targets: the dispatch fires everywhere it should and is still "
            "wrong."),
        "rationale": (
            "REJECT from C3 AND C4 simultaneously: the rival returns cfP2 where "
            "the cascade demands cfP1 and cfP1 where it demands cfP2. If it "
            "verified => SPEC-TOO-WEAK on the CODE BINDING sub-obligation — the "
            "spec would pin only WHETHER a pattern evaluates, not to WHAT. "
            "Refuted at BOTH (sSpecial, z1) and (sSpecial, z2), which is the "
            "sub-domain this rival owns and neither dropping rival covers (each "
            "of those is wrong at only one of the two). "
            "(Sibling: weak-swap-p1-p2.)"),
        "witness": _rcf_witness((2, 4), (2, 5)),
    },

    {
        "id": "reject-swap-remaining-special-pair",
        "kind": "uniqueness",
        "expect": "reject",
        # Permute two of the OTHER four distinguished-s codes — the ones no
        # symbolic assertion mentions, reachable only through the numeric
        # agreement loop. Without this rival, a spec pinning only the two
        # explicitly-named patterns would look adequate.
        "module": _rcf(_GOLD_RCF
                       .replace("         else if zTag = z3 then cfP3\n",
                                "         else if zTag = z3 then cfP4\n", 1)
                       .replace("         else if zTag = z4 then cfP4\n",
                                "         else if zTag = z4 then cfP3\n", 1)),
        "refinement": (
            "GATED through the failing test's NUMERIC branch rather than its "
            "symbolic assertions. These two special second arguments are not "
            "named by either symbolic assertion, but the test also loops over ALL "
            "SIX distinguished-s special arguments and requires the "
            "auto-evaluated result to agree numerically with the deliberately "
            "unevaluated call to within 1e-15. With the two codes exchanged, each "
            "of those two patterns auto-evaluates to the other's closed form — "
            "numerically a different number — so the agreement bound is violated "
            "and a faithful counterpart would NOT resolve. Correct on all four "
            "remaining special patterns and on both symbolically-asserted ones."),
        "rationale": (
            "REJECT from C1 alone: C2–C7 do NOT mention these two patterns, so "
            "this rival is refuted only by the full-cascade clause "
            "`out = closedFormFor s zTag`. That makes it the control that C1 is "
            "load-bearing beyond the explicitly-pinned patterns — if it verified "
            "=> SPEC-TOO-WEAK on every special pattern the per-pattern clauses do "
            "not name. Refuted at (sSpecial, z3), a third distinct point. (Added: "
            "the sibling's swap rival only permutes the two "
            "symbolically-asserted codes, so the other four special patterns' "
            "bindings would go untested.)"),
        "witness": _rcf_witness((2, 6)),
    },

    # ---- NON-GATING: PATTERN PRESENCE on the two s-keyed clauses -------------
    # Relabelled by audit. A DROPPED clause is invisible to a self-consistency
    # numeric loop (see the docstring's gating criterion): the suppressed-
    # evaluation side and the auto-evaluated side are then the SAME unevaluated
    # object, so their difference is exactly zero and the bound holds. These two
    # rivals are still the only attacks on C5/C6's PRESENCE, and the gated attack
    # on those clauses is the code-permuting rival below.

    {
        "id": "reject-drop-skey-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "      else if s = sKeyA then cfSa\n", "", 1)),
        "refinement": (
            "NON-GATING, disclosed — and this label is an AUDIT CORRECTION; an "
            "earlier revision of this file claimed GATED here on a mechanism that "
            "does not hold. Dropping the first s-keyed clause leaves that whole "
            "parameter value unevaluated at generic second arguments. The failing "
            "test's second numeric loop does draw generic second arguments at "
            "exactly this parameter value — but it compares the auto-evaluated "
            "result against the SAME call with auto-evaluation SUPPRESSED. With "
            "the clause absent the auto-evaluation never fires, so the two sides "
            "are the same unevaluated object, their difference is exactly zero, "
            "and the assertion PASSES. No symbolic assertion in the failing test "
            "names this parameter value either (both are at the distinguished s). "
            "So a faithful counterpart could still pass the gated test and this "
            "is NOT a verify-does-not-imply-resolve break. It is nonetheless a "
            "real defect: the auto-evaluation the change exists to ADD is simply "
            "absent at this parameter value, which the executable A-reference "
            "check tests for directly. It ships because C5 is an independent "
            "conjunct and its PRESENCE has no gated attack available — the "
            "gated attack on this clause is the code-permuting rival below, which "
            "keeps the clause firing and gets its VALUE wrong."),
        "rationale": (
            "REJECT from C5 `(s = sKeyA ∧ zTag = zOther) → out = cfSa` and from "
            "C1: the cascade demands cfSa at this pattern and the rival hands "
            "back cfUneval. If it verified => SPEC-TOO-WEAK on PATTERN PRESENCE "
            "for the s-keyed clauses (which no distinguished-s rival touches). "
            "Refuted at (sKeyA, zOther) — the first witness point that moves `s` "
            "OFF the distinguished value, and the first that exercises the "
            "`zOther` class of the second binder. "
            "(Sibling: weak-drop-s0-keyed.)"),
        "witness": _rcf_witness((0, 0)),
    },

    {
        "id": "reject-drop-skey-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "      else if s = sKeyB then cfSb\n", "", 1)),
        "refinement": (
            "NON-GATING, disclosed — same AUDIT CORRECTION as the previous rival, "
            "for the same reason: a dropped clause is invisible to a "
            "self-consistency numeric loop, because the suppressed-evaluation "
            "side and the un-fired auto-evaluation side are then the same object. "
            "This is the near-miss partner of the previous rival: it keeps the "
            "first s-keyed clause and drops only the SECOND, so it agrees with the "
            "change over strictly more of the domain, and the closed form the "
            "change adds here is a DIFFERENT one from the first s-keyed clause's. "
            "A counterpart missing it delivers only half the s-keyed behaviour — a "
            "real defect the A-reference check catches — but the gated test does "
            "not see it. It ships because C6 is an independent conjunct from C5 "
            "and a battery attacking only one would admit a rival that implemented "
            "one s-keyed closed form and not the other. Because it is a strictly "
            "narrower miss, it gets its own witness at its own parameter value "
            "rather than sharing the previous rival's."),
        "rationale": (
            "REJECT from C6 `(s = sKeyB ∧ zTag = zOther) → out = cfSb` and from "
            "C1. If it verified => SPEC-TOO-WEAK on the SECOND s-keyed clause "
            "specifically: C5 and C6 are independent conjuncts, and a battery "
            "attacking only one would admit a rival that implemented one s-keyed "
            "closed form and not the other. Refuted at (sKeyB, zOther) — a third "
            "distinct `s` value. (Added: the sibling drops only the first s-keyed "
            "clause, so the second's presence would go untested.)"),
        "witness": _rcf_witness((-1, 0)),
    },

    # ---- GATED: CODE BINDING on the two s-keyed clauses ----------------------
    # ADDED BY AUDIT. Both s-keyed clauses PRESENT and FIRING, bound to each
    # other's code. This is the attack on C5/C6 the failing test can actually
    # see: unlike a dropped clause, a mis-bound one auto-evaluates to a WRONG
    # value, which is what a self-consistency numeric loop detects. Without it,
    # C5 and C6 would be defended by non-gating cases alone.
    {
        "id": "reject-swap-skey-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF
                       .replace("      else if s = sKeyA then cfSa\n",
                                "      else if s = sKeyA then cfSb\n", 1)
                       .replace("      else if s = sKeyB then cfSb\n",
                                "      else if s = sKeyB then cfSa\n", 1)),
        "refinement": (
            "GATED. Both s-keyed clauses still auto-evaluate — so no "
            "'does it evaluate at all' check catches a faithful counterpart — but "
            "each produces the OTHER clause's closed form, and the two closed "
            "forms are different functions of the second argument. The failing "
            "test's second numeric loop draws generic second arguments at BOTH of "
            "these parameter values and compares the auto-evaluated result "
            "against the same call with auto-evaluation suppressed; the suppressed "
            "side still evaluates to the true value, so the two disagree by far "
            "more than 1e-15 at both parameter values and the loop's assertion "
            "fails. A faithful counterpart would therefore NOT resolve. This is "
            "the gated counterpart of the two dropping rivals above, whose misses "
            "the self-consistency comparison cannot see."),
        "rationale": (
            "REJECT from C5 AND C6 simultaneously, and from C1: the rival returns "
            "cfSb where the cascade demands cfSa and cfSa where it demands cfSb. "
            "If it verified => SPEC-TOO-WEAK on the CODE BINDING sub-obligation "
            "for the s-keyed clauses — the spec would pin only WHETHER those "
            "clauses fire, not to WHAT, which is the same hole the "
            "distinguished-s permutation rivals close for their own block. "
            "Refuted at BOTH (sKeyA, zOther) and (sKeyB, zOther), the sub-domain "
            "this rival owns and neither dropping rival covers (each of those is "
            "wrong at only one of the two, and neither is gated). "
            "(Added by audit: no sibling counterpart.)"),
        "witness": _rcf_witness((0, 0), (-1, 0)),
    },

    # ---- GATED: NO OVER-FIRE at the cascade's outermost fall-through ---------

    {
        "id": "reject-overfire-outer-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # The outermost `else cfUneval` hands back the first s-keyed closed form
        # instead of "no closed form".
        "module": _rcf(_GOLD_RCF.replace(
            "      else cfUneval\n    return result",
            "      else cfSa\n    return result", 1)),
        "refinement": (
            "GATED, and the sharpest rival in the battery. Over-firing the "
            "outermost fall-through makes EVERY unrecognised pattern claim the "
            "first s-keyed closed form. That includes the distinguished-expansion "
            "parameter value at a generic second argument — which the failing "
            "test's numeric loop covers directly, and where the true value is a "
            "completely different function of the second argument. The "
            "auto-evaluated result and the deliberately-unevaluated call then "
            "disagree by far more than 1e-15, so the loop's assertion fails and a "
            "faithful counterpart would NOT resolve. This is the exact failure "
            "mode the reported issue warns about — claiming a closed form where "
            "the function does not take one."),
        "rationale": (
            "REJECT from C1: `closedFormFor` yields cfUneval at every pattern "
            "past the cascade, and the rival yields cfSa there. If it verified => "
            "SPEC-TOO-WEAK on the NO-OVER-FIRE sub-obligation, i.e. the spec "
            "would constrain what the dispatch produces where it fires but not "
            "where it must stay silent — the direction that lets a rival invent "
            "closed forms. Refuted at (sExpand, zOther): a fourth distinct `s` "
            "value, and the only witness point at the parameter value the second "
            "method's precondition pins, so the two methods' domains are both "
            "probed. (Sibling: weak-overfire-s2-else, redirected to the gated "
            "fall-through.)"),
        "witness": _rcf_witness((1, 0)),
    },

    # ---- NON-GATING: the distinguished-s block's own fall-through ------------

    {
        "id": "reject-overfire-special-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # The distinguished-s block's `else cfUneval` hands back a closed form.
        "module": _rcf(_GOLD_RCF.replace(
            "         else cfUneval)", "         else cfSa)", 1)),
        "refinement": (
            "NON-GATING, disclosed. A faithful counterpart over-fires only at the "
            "distinguished parameter value with an UNRECOGNISED second argument. "
            "The failing test's six-point loop probes that parameter value only "
            "at the six RECOGNISED special arguments, and its random-second-"
            "argument loop does not include that parameter value, so the test does "
            "not reach this sub-domain and a counterpart could still pass it. It "
            "is nonetheless a real defect: the call would claim a closed form at "
            "arbitrary second arguments where the function does not take one, "
            "which is precisely the over-firing the frozen spec's own description "
            "forbids and which the executable A-reference check tests for "
            "separately. It ships because the distinguished-s block's "
            "fall-through is an INDEPENDENT sub-obligation from the outermost "
            "one — the gated over-fire rival cannot reach it, since that block "
            "intercepts the pattern first — so without this case a rival "
            "over-firing only inside the block would go uncaught. The spec is "
            "deliberately a conjunction the real change satisfies IN FULL, so "
            "pinning this clause cannot cost a resolving impl its verification "
            "and `verify ⟹ resolved` is unaffected. (Same disposition the sibling "
            "records for its expansion rival.)"),
        "rationale": (
            "REJECT from C1: `closedFormFor` yields cfUneval at the "
            "distinguished s with an unrecognised second argument, and the rival "
            "yields cfSa. If it verified => SPEC-TOO-WEAK on the distinguished-s "
            "block's fall-through. Refuted at (sSpecial, zOther) — the seventh "
            "distinct point, and the only one pairing the distinguished `s` with "
            "the `zOther` class, so that combination of the two binders is "
            "probed. (Sibling: weak-overfire-s2-else.)"),
        "witness": _rcf_witness((2, 0)),
    },

    # ---- NON-GATING: PRIORITY (C7's overlap point) ---------------------------

    {
        "id": "reject-priority-skey-before-zkeyed",
        "kind": "uniqueness",
        "expect": "reject",
        # Test the first s-keyed clause BEFORE the z-keyed clauses. Every clause
        # is present and correctly bound; only the ORDER changes — and unlike the
        # positive control's reorder, this one moves a clause across an overlap.
        "module": _rcf(
            "    let result : Int :=\n"
            "      if s = sKeyA then cfSa\n"
            "      else if zTag = zA then cfZa\n"
            "      else if zTag = zB then cfZb\n"
            "      else if zTag = zC then cfZc\n"
            "      else if s = sSpecial then\n"
            "        (if zTag = z1 then cfP1\n"
            "         else if zTag = z2 then cfP2\n"
            "         else if zTag = z3 then cfP3\n"
            "         else if zTag = z4 then cfP4\n"
            "         else if zTag = z5 then cfP5\n"
            "         else if zTag = z6 then cfP6\n"
            "         else cfUneval)\n"
            "      else if s = sKeyB then cfSb\n"
            "      else cfUneval\n"
            "    return result"),
        "refinement": (
            "NON-GATING, disclosed. A faithful counterpart places the newly-added "
            "s-keyed clause ahead of the pre-existing z-keyed ones — a natural way "
            "to get the insertion wrong. It diverges only at the single pattern "
            "where the two clauses overlap, and the failing test never constructs "
            "that pattern (its random second arguments are generic, so they never "
            "land on the z-keyed value), so a counterpart could still pass it. It "
            "is nonetheless a real regression: at that overlap the s-keyed closed "
            "form divides by zero, so the call would return an infinity where the "
            "function's documented value is finite — behaviour the real change "
            "PRESERVES and the executable A-reference check asserts. It ships "
            "because C7 is the spec's only pin on clause ORDER and no other rival "
            "attacks it: dropping this case would leave the entire priority "
            "sub-obligation undefended, and a rival that reordered the cascade "
            "would then verify. Pinning it cannot cost a resolving impl its "
            "verification (the real change satisfies the priority in full), so "
            "`verify ⟹ resolved` is unaffected."),
        "rationale": (
            "REJECT from C7 `(zTag = zA ∧ s = sKeyA) → out = cfZa` and from C1: "
            "`closedFormFor sKeyA zA = cfZa` because the z-keyed clauses are "
            "matched first for ANY parameter value, and the rival returns cfSa. "
            "Every clause is PRESENT and correctly BOUND here, so presence and "
            "binding checks both pass — only the priority refutes it, which makes "
            "this the control that C7 is load-bearing. Refuted at (sKeyA, zA), "
            "the eighth distinct point and the only witness that moves the "
            "second binder to the `zA` class. Note the contrast with "
            "`pos-reorder-disjoint-branches`, which permutes only DISJOINT tests "
            "and must verify: the spec must reject exactly the reorders that "
            "change a value. (Sibling: weak-priority-s0-before-zkeyed.)"),
        "witness": _rcf_witness((0, 1)),
    },

    # ---- NON-GATING: C2, the remaining z-keyed pin ---------------------------

    {
        "id": "reject-drop-zkeyed-zc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "      else if zTag = zC then cfZc\n", "", 1)),
        "refinement": (
            "NON-GATING, disclosed. This z-keyed pattern is behaviour the real "
            "change PRESERVES rather than adds, and the failing test never "
            "constructs it (its random second arguments are drawn from a "
            "continuum and never land on this exact value). So a faithful "
            "counterpart that dropped this clause could still pass the failing "
            "test, and this case is not a verify-does-not-imply-resolve break. It "
            "is still a real regression — the call would be left unevaluated at a "
            "pattern whose value is pinned elsewhere in the suite — and it is the "
            "ONLY rival that can attack C2: no gated attack on this clause "
            "exists, because the clause is not in the failing test's sub-domain "
            "at all. Shipping it is what keeps C2 defended; the alternative is an "
            "unattacked conjunct, where a rival mishandling only this pattern "
            "would verify. The spec being stronger than the test here is "
            "deliberate and one-directional, so `verify ⟹ resolved` still holds."),
        "rationale": (
            "REJECT from C2 `zTag = zC → out = cfZc` and from C1: the rival lets "
            "this pattern fall through to cfUneval. If it verified => "
            "SPEC-TOO-WEAK on C2, the one postcondition conjunct no other rival "
            "reaches. Refuted at (sSpecial, zC) — the ninth distinct point, and "
            "the only witness in the `zC` class of the second binder. (Added: the "
            "sibling has no counterpart, because C2 has no gated attack; see the "
            "refinement.)"),
        "witness": _rcf_witness((2, 3)),
    },

    # ---- NON-GATING: the third z-keyed clause -------------------------------
    # ADDED BY AUDIT. The battery pinned zA (through the priority rival) and zC
    # (through the rival above) but left the MIDDLE z-keyed clause, zB, attacked
    # by nothing — while the coverage prose claimed the witnesses spanned "the
    # z-keyed classes". They spanned two of the three. C1 pins this clause and no
    # per-pattern conjunct does, so an impl dropping only zB satisfied every
    # explicitly-named clause and was refuted by the cascade alone; the audit
    # confirmed with real builds that such a rival is genuinely rejected and that
    # a witness at (sKeyB, zB) discriminates, so this was a closeable gap rather
    # than an inexpressible one.
    {
        "id": "reject-drop-zkeyed-zb",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "      else if zTag = zB then cfZb\n", "", 1)),
        "refinement": (
            "NON-GATING, disclosed, on the same footing as the zC rival above and "
            "for the same reason: this z-keyed pattern is behaviour the real change "
            "PRESERVES rather than adds, and the failing test never constructs it "
            "(its second arguments in the generic loops are drawn from a continuum "
            "and never land on this exact value, and neither symbolic assertion "
            "names it). So a faithful counterpart dropping this clause could still "
            "pass the gated test and this is not a verify-does-not-imply-resolve "
            "break. It is still a real regression, and a SHARPER one than the zC "
            "rival's: the witness point pairs this pattern with the second s-keyed "
            "parameter value, where dropping the clause does not merely leave the "
            "call unevaluated but hands it to the s-keyed clause below, so the call "
            "claims the WRONG closed form rather than none. That is the priority "
            "cascade failing at an overlap C7 does not cover — C7 pins only the "
            "zA/sKeyA overlap — which is why the case is worth its own witness "
            "instead of folding into the zC rival's."),
        "rationale": (
            "REJECT from C1 alone: no per-pattern conjunct names zB (C2 names zC, "
            "C7 names zA), so this rival is refuted only by the full-cascade clause "
            "`out = closedFormFor s zTag`. That makes it a second control that C1 "
            "is load-bearing beyond the explicitly-pinned patterns, on the one "
            "z-keyed class the battery previously left unattacked. Refuted at "
            "(sKeyB, zB): `closedFormFor sKeyB zB = cfZb` because the z-keyed "
            "clauses win for ANY parameter value, while the rival falls through to "
            "the s-keyed clause and yields cfSb. A tenth distinct point, and the "
            "only witness in the `zB` class of the second binder. (Added by audit: "
            "no sibling counterpart.)"),
        "witness": _rcf_witness((-1, 2)),
    },

    # ---- NON-GATING: the second method's obligation --------------------------

    {
        "id": "reject-series-branch-factored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ser("    return expPolar"),
        "refinement": (
            "NON-GATING, disclosed — and this is the sibling's own disposition "
            "for this rival, carried over unchanged. Returning the branch-factored "
            "expansion is the PRE-CHANGE behaviour at the distinguished "
            "parameter, and the second half of the reported issue argues at "
            "length that the branch factor there is meaningless. The gold test "
            "patch rewrites the expansion expectation accordingly, but that test "
            "is in NEITHER the FAIL_TO_PASS nor the PASS_TO_PASS list (a "
            "non-gating co-fix), and the single failing test reaches this "
            "parameter value only through numeric evaluation, which does not go "
            "through the expansion. So a faithful counterpart could still pass "
            "the gated test. It ships because this is the ONLY attack on the "
            "second method's obligation, and an obligation with no rival at all "
            "is an obligation whose strength is untested: the frozen spec pins "
            "E1/E2/E3 precisely so the modeled co-fix cannot regress. The spec is "
            "an intentional conjunction the real change satisfies in full, so "
            "`verify ⟹ resolved` is preserved."),
        "rationale": (
            "REJECT from all three of E1 `out = expansionCode`, E2 "
            "`out = expPlain` and E3 `out ≠ expPolar` at once — the branch-"
            "factored code violates every one. If it verified => SPEC-TOO-WEAK "
            "(the spec would admit the pre-change expansion). This is the only "
            "rival against `seriesExpansionAtOne`, so without it that obligation "
            "would be defended by positives alone. Refuted at the single input "
            "its precondition admits, `s = sExpand`, via that method's own "
            "tester. (Sibling: weak-series-polar.)"),
        "witness": _tester(
            "seriesExpansionAtOne",
            "example : seriesExpansionAtOneTester 1 = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The nagini sibling ships 12 SPEC cases (3 soundness, 1 admissibility, 8
# uniqueness) plus a separate AXIOM lane. It contracts the SAME two functions
# over the SAME discrete quotient (`recognize_closed_form(s, z_tag)` and
# `series_expansion_at_one(s)`), so this is one of the rare ports where the
# carrier does NOT narrow: both modeled behaviours survive, and the abstraction
# (integer parameter, nine-way second-argument tag, integer closed-form codes)
# is identical on both backends. Case count therefore goes UP, not down — the
# additions are clause-coverage gaps, not parity padding.
#
#   nagini case                     kind           -> here                                  disposition
#   ---------------------------------------------------------------------------------------------------
#   pos-echo-grounded-oracle        soundness      -> pos-echo-grounded-cascade              PORTED
#   pos-reorder-disjoint-branches   soundness      -> pos-reorder-disjoint-branches          PORTED
#   pos-series-local-binding        soundness      -> pos-series-local-binding               PORTED
#   admiss-f2p-shaped               admissibility  -> admiss-cascade-nondegenerate           PORTED
#   weak-drop-special-z2            uniqueness     -> reject-drop-special-z2                 PORTED
#   weak-drop-special-z1            uniqueness     -> reject-drop-special-z1                 PORTED
#   weak-swap-p1-p2                 uniqueness     -> reject-swap-p1-p2                      PORTED
#   weak-drop-s0-keyed              uniqueness     -> reject-drop-skey-a                     PORTED
#   weak-priority-s0-before-zkeyed  uniqueness     -> reject-priority-skey-before-zkeyed     PORTED
#   weak-overfire-s2-else           uniqueness     -> reject-overfire-special-fallthrough    PORTED
#                                                   + reject-overfire-outer-fallthrough      SPLIT/ADDED
#   weak-series-polar               uniqueness     -> reject-series-branch-factored          PORTED
#   weak-nonterm-echo               uniqueness     -> (none)                                 SPEC-CLOSED
#   (no sibling)                    uniqueness     -> reject-swap-remaining-special-pair     ADDED
#   (no sibling)                    uniqueness     -> reject-drop-skey-b                     ADDED
#   (no sibling)                    uniqueness     -> reject-drop-zkeyed-zc                  ADDED
#   (no sibling)                    uniqueness     -> reject-swap-skey-pair                  ADDED BY AUDIT
#   (no sibling)                    uniqueness     -> reject-drop-zkeyed-zb                  ADDED BY AUDIT
#   AXIOM_TESTS (x2)                axiom          -> (none)                                 N/A (G-AX)
#
# 11 of 12 sibling SPEC cases ported; 1 SPEC-CLOSED (divergence, witness limit,
# not a hole); 6 added
# (one of them a split of a sibling case into its two independent halves, two
# added by the audit lane).
# 17 SPEC cases: 3 soundness, 1 admissibility, 13 uniqueness.
#
# PORTED (the three positives): the sibling's oracle-echo control ports directly
#   — `closedFormFor` is grounded here for the same reason `closed_form_for` is
#   there (its body IS the computation, over the method's own arguments), so
#   echoing it is honest work. The branch-reorder control ports with one change:
#   the reshape leaves a linear-arithmetic residual the frozen `simp_all` does
#   not close, so `omega` is appended to the TACTIC BODY (elided from the spec
#   view; the `prove_correct` header is byte-identical; no lemma, axiom or
#   `sorry`). The series local-binding control ports with the local bound to the
#   grounded pure model. All three confirmed to build.
# PORTED (admissibility): the sibling asserts in-region that the pure cascade
#   computes the load-bearing answers. Ported and SHARPENED — the first method
#   has no `require` clause here (empty pre-conditions region), so a bare
#   "precondition admits the input" probe would be vacuous; the assert instead
#   pins six representative patterns to six PAIRWISE-DISTINCT outcomes, so it
#   also refutes a degenerate post-image. Impl AND proof kept verbatim so the
#   method's own obligation still discharges. The assert is LIVE: substituting
#   one false conjunct about the same point leaves `⊢ False` unsolved (confirmed
#   with a real build).
# PORTED (the six value/priority rivals): each sibling rival's WRONG IMPL ports
#   almost mechanically (the cascade has the same shape on both carriers); the
#   new work is the witness, and each of the six got its own at its own
#   argument pattern.
# SPLIT/ADDED (reject-overfire-outer-fallthrough): the sibling's single over-fire
#   rival attacks the distinguished-s block's fall-through, which turns out to be
#   OUTSIDE the failing test's sub-domain. The cascade has a SECOND, independent
#   fall-through — the outermost one — which IS inside it (the
#   distinguished-expansion parameter value at a generic second argument is
#   covered by the test's random loop, and the true value there is a different
#   function entirely). Both ship: the block's fall-through cannot be reached by
#   a rival attacking the outer one, so they are genuinely independent
#   sub-obligations, and the split is what gives the NO-OVER-FIRE class a GATED
#   member.
# ADDED (reject-swap-remaining-special-pair): the sibling permutes only the two
#   codes the failing test names symbolically. The other four distinguished-s
#   patterns are pinned by C1 alone (C2-C7 do not mention them) and are reached
#   by the test's six-point numeric loop, so a rival mis-binding them is both
#   gated and refutable — and without it, C1's strength beyond the explicitly-
#   pinned patterns would be untested.
# ADDED (reject-drop-skey-b): the sibling drops only the FIRST s-keyed clause.
#   C5 and C6 are independent conjuncts naming DIFFERENT closed forms, so a
#   rival implementing one and not the other would otherwise verify. Given its
#   own witness at its own parameter value rather than sharing the C5 rival's,
#   because it agrees with the change over strictly more of the domain.
# ADDED BY AUDIT (reject-swap-skey-pair): the independent audit of this battery
#   found that the two s-keyed DROPPING rivals had been labelled GATED on a
#   mechanism that does not hold — the failing test's numeric loops are
#   SELF-CONSISTENCY comparisons (auto-evaluated result vs. the same call with
#   auto-evaluation suppressed), and a dropped clause makes both sides the same
#   unevaluated object, so the bound holds and the test passes. Both were
#   relabelled NON-GATING, which would have left C5/C6 defended by non-gating
#   cases alone. This rival restores a gated attack on them: it keeps both
#   clauses FIRING and exchanges their codes, so each auto-evaluates to a value
#   the suppressed side does not equal and the loop's bound is violated at both
#   parameter values. Machine-checked with three real builds (rival rejected;
#   witness elaborates against the rival, refuted on gold at both points).
# ADDED BY AUDIT (reject-drop-zkeyed-zb): the same audit pass found the middle
#   z-keyed clause attacked by NOTHING, while the binder-coverage prose above
#   claimed the witnesses spanned "the z-keyed classes" — they spanned zA (via
#   the priority rival) and zC (via the rival below), not zB. C1 pins zB and no
#   per-pattern conjunct does, so an impl dropping only that clause satisfied
#   every explicitly-named conjunct. The gap was closeable, not inexpressible,
#   and was closed rather than merely disclosed. Machine-checked with four real
#   builds: the rival is REJECTED (exit 1, `unsolved goals` on the cascade
#   obligation); the witness at (sKeyB, zB) ELABORATES against it (exit 0); the
#   same witness is REFUTED on gold (exit 1) by plain evaluation, ``Tactic
#   `decide` proved that the proposition ... is false``; and the FORGERY asserting
#   the opposite claim at that point VERIFIES on gold (exit 0), so gold's exit
#   code tracks the claim rather than being a constant failure. The witness point
#   deliberately pairs zB with the second s-keyed parameter value, where the drop
#   makes the call claim the WRONG closed form rather than none.
# ADDED (reject-drop-zkeyed-zc): C2 is the one postcondition conjunct with no
#   sibling attack and no GATED attack available at all — the pattern is
#   behaviour the change preserves and the failing test never constructs it. It
#   ships with that disclosed in its `refinement`, because the alternative is an
#   unattacked conjunct.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
#   frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
#   immutable values, no loop and no recursion), so there is no control flow
#   here to make diverge: a diverging rival cannot be obtained by mutating this
#   body, it has to bring a loop of its own. When it does, the semantics refuse
#   it. This bundle sets ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#     RETRACTED, RE-MEASURED (what the five indented lines below this used to
#     claim, and the paragraph that followed them). A superseded revision argued
#     that a diverging Loom loop carrying a CONSTANT `decreasing` measure and
#     returning the wrong `cfUneval` VERIFIES here at exit 0, on the theory that
#     the clause elaborates and is then DISCARDED by a partial loop rule; that
#     flipping only the `open` line would reject it; that setting the
#     `set_option` alone changes nothing; and that a cell with a `total`
#     `set_option` would therefore be MISCOUNTED as closed by an option-only
#     census while still admitting the rival. All of it is withdrawn.
#     The premise is wrong at the source. The `set_option` is not inert: its
#     elaborator ITSELF runs `openScope `TotalCorrectness`
#     (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so a file setting "total"
#     is in the total scope whether or not it also writes the `open`, and the two
#     lines cannot disagree. This bundle carries both (line 4 and line 7).
#     The measurement does not reproduce either. Re-built on THIS bundle with
#     every proof reduced to a bare `loom_solve`, both shapes are REJECTED:
#       * constant measure (`while k > 0 / invariant True / decreasing (0 : Nat)`,
#         body `k := k + 1`) -> exit 1, `case «decreasing_1: (0 : Nat)»`,
#         residual `0 < 0` unsolved, in BOTH methods;
#       * increasing measure (`while true / invariant True / decreasing i`, body
#         `i := i + 1`) -> exit 1, `case «decreasing_1: i»`, residual `i + 1 < i`.
#     So the annotation is not discarded, no option-only census could have been
#     fooled, and there is no residual hole to leave for a flip lane.
#   No reject case is shipped for the class, and the reason is the WITNESS
#   contract rather than a spec weakness. A reject case needs a witness that
#   ELABORATES against the rival, and each diverging shape defeats that half by a
#   DIFFERENT route. With NO measure, the refusal is a module-level error at the
#   `method` DECLARATION, which the witness file retains (it strips only the
#   `prove_correct` obligations), so the rival does not compile and even a trivial
#   witness returns `witness-unproven`. With a measure PRESENT BUT FALSE, the
#   refusal moves to the `prove_correct` site, which IS stripped, so the module
#   elaborates and a trivial witness succeeds; a real witness still fails, because
#   the rival keeps a `while` whose post-image is an unreduced `forIn
#   Lean.Loop.mk ... invariantGadget ... decreasingGadget` term the kernel will not
#   normalise, leaving `unsolved goals` on it. Both score `witness-unproven`
#   (INCONCLUSIVE, which fails a battery rather than passing a case), and a
#   `witness_reference` rescues neither, since it substitutes the GOLD subject while
#   the failure is on the RIVAL side. Recorded as REJECTED-BY-SPEC and inexpressible
#   as a witnessed case, which is neither a spec hole nor a battery gap. Nothing is
#   escalated.
#   of its functions take by-value `int` parameters, so it has no
#   half-permission input and no mutable container, and it justifies the class
#   N/A in its own docstring. Here the same holds and more strongly: Lean and
#   Velvet are referentially transparent, `s` and `zTag` are immutable values, no
#   `mut` binder is declared, and there is no heap, no aliasing and no permission
#   system. Nothing fabricated.
# AXIOM_TESTS: dropped (2 cases). This bundle declares NO axiom — the `axioms`
#   region is empty and the dispatch is modeled deeply and concretely — so the
#   sibling's probes are A-REFERENCE validation (that each code names the value
#   the real function actually takes at its pattern), which is G-AX's lane via
#   axiom_check.py. This gate ignores AXIOM_TESTS regardless.
#
# OBLIGATION / CLAUSE / BINDER COVERAGE.
#   Both obligations are DEFENDED and ATTACKED:
#     * `prove_correct recognizeClosedForm` — defended by pos-echo-grounded-
#       cascade, pos-reorder-disjoint-branches and admiss-cascade-nondegenerate;
#       attacked by twelve rivals.
#     * `prove_correct seriesExpansionAtOne` — defended by
#       pos-series-local-binding; attacked by reject-series-branch-factored.
#   Every top-level postcondition clause is attacked by some rival:
#     C1 (full cascade) .... every rival; SOLELY by reject-swap-remaining-
#                            special-pair, reject-drop-zkeyed-zb and both
#                            over-fire rivals
#     C2 (zC pin) .......... reject-drop-zkeyed-zc
#     C3 (z1 pin) .......... reject-drop-special-z1, reject-swap-p1-p2
#     C4 (z2 pin) .......... reject-drop-special-z2, reject-swap-p1-p2
#     C5 (sKeyA pin) ....... reject-drop-skey-a (presence, non-gating),
#                            reject-swap-skey-pair (binding, GATED)
#     C6 (sKeyB pin) ....... reject-drop-skey-b (presence, non-gating),
#                            reject-swap-skey-pair (binding, GATED)
#     C7 (priority) ........ reject-priority-skey-before-zkeyed
#     E1 / E2 / E3 ......... reject-series-branch-factored
#   GATED COVERAGE (which conjuncts have an attack whose faithful counterpart
#   actually fails the failing test): C1, C3, C4, C5, C6 do; C2, C7 and E1-E3 do
#   not, and cannot — see each one's `refinement` for why the failing test never
#   reaches its sub-domain. That asymmetry is the spec being deliberately
#   stronger than the single gated test, in the safe direction only.
#   Both INPUT BINDERS of the first method are varied by the reject witnesses,
#   which is the check a correctly-narrowed port most easily fails:
#     * `s` takes FOUR distinct values across the witnesses — sSpecial (2),
#       sKeyA (0), sKeyB (-1), sExpand (1) — i.e. every parameter value the
#       cascade branches on PLUS the one the second method's precondition pins.
#       No witness holds `s` fixed at the distinguished value.
#     * `zTag` takes SEVEN distinct values — zOther (0), zA (1), zB (2), zC (3),
#       z1 (4), z2 (5), z3 (6) — spanning ALL THREE z-keyed classes, two of the
#       six distinguished-s special classes, and the unrecognised class.
#       CORRECTED BY AUDIT: an earlier revision listed SIX values and claimed they
#       spanned "the z-keyed classes". They spanned two of the three — zB, the
#       middle z-keyed clause, was probed by no witness and attacked by no rival,
#       even though C1 pins it and no per-pattern conjunct does. The audit
#       confirmed with real builds that the gap was closeable rather than
#       inexpressible (rival rejected; witness elaborates against it and is
#       refuted on gold by plain evaluation) and landed
#       `reject-drop-zkeyed-zb` at (sKeyB, zB) to close it.
#     * The two binders are varied JOINTLY, not one-at-a-time: the twelve rejects
#       against this method probe TEN distinct (s, zTag) points — (2,5), (2,4),
#       (2,4) and (2,5) together, (2,6), (0,0), (-1,0), (0,0) and (-1,0)
#       together, (1,0), (2,0), (0,1), (2,3), (-1,2) — and the thirteenth reject
#       probes the second method's single admitted input. Notably (2,0) and (0,0)
#       share `zTag` but differ in `s`; (0,0) and (0,1) share `s` but differ in
#       `zTag`; and (-1,0) and (-1,2) do the same at the other s-keyed value, so
#       neither binder is held constant while the other moves.
#   KNOWN COVERAGE FINDING, and it is structural rather than an authoring gap.
#     `scripts/pbt_coverage.py` reports that the single reject against
#     `seriesExpansionAtOne` probes only one input point, "so the battery says
#     nothing about the spec's dependence on `s`". That is correct and
#     irreducible: this method's frozen precondition is `require s = sExpand`,
#     which admits EXACTLY ONE integer, so its whole admitted domain is that one
#     point and there is no second point a witness could probe. A witness at any
#     other `s` would be vacuous, not informative — the derived tester returns
#     `true` whenever the precondition fails (`if decide pre then … else true`),
#     so `…Tester s = false` is UNPROVABLE off `sExpand` and would refute
#     nothing about the postcondition. Widening the input (the fourth route
#     before declaring a gap) would mean weakening `require`, which is frozen
#     spec and out of lane. So the finding is fully discharged by the one
#     witness: the reject covers 100% of that method's admitted domain, and the
#     dependence the coverage heuristic looks for does not exist to be tested.
#     Recorded here rather than suppressed.
#   WITNESS DISCRIMINATION (confirmed during authoring with two real
#   `scripts/lean_verify.sh` builds per reject case): each witness file
#   ELABORATES against its rival (exit 0 — the extracted program's result
#   provably violates that method's postcondition at the probed pattern, with
#   `<method>Tester … = false` closing by `decide`) and FAILS against the frozen
#   solution (exit 1 — gold's tester evaluates to `true` there, so `= false` is
#   refuted by kernel computation). Both methods are loop-free straight-line
#   code over `Int` with no opaque term anywhere in the spec, so every witness is
#   stated at fully concrete integer literals; NO witness binds a hypothesis, so
#   none carries a joint-satisfiability obligation and the gate's inconsistency
#   probe has nothing to check. No `sorry`, `admit`, `native_decide` or new
#   `axiom` appears in any variant or witness.
#
# INDEPENDENT AUDIT — WHAT WAS RE-DERIVED, AND WHAT IT FOUND.
#   Every claim above about a build was re-run from scratch by an independent
#   audit lane rather than taken on the port's word. 84 real
#   `scripts/lean_verify.sh` builds, in a scratch directory outside the bundle.
#
#   WITNESSES REBUILT (all 12 pre-existing reject cases, three builds each, plus
#   the new zB case's four). For every one: the variant is REJECTED (exit 1); the
#   witness ELABORATES against its rival (exit 0); the same witness is REFUTED
#   against the frozen solution (exit 1). Every gold-side failure is a PLAIN
#   EVALUATION refutation — ``Tactic `decide` proved that the proposition
#   <method>Tester <args> = false is false`` — i.e. the kernel computed gold's
#   tester to `true` and the witness's concrete claim is what failed. Nothing in
#   the corpus's harder signature classes (application/type mismatch, stuck
#   `Decidable` instance, missing identifier) appears anywhere in this battery.
#   FORGERY PAIRS (attack B′) were built anyway, for all 13, even though a plain
#   evaluation needs no forgery test: each witness's claim was FLIPPED (`= false`
#   -> `= true`) and rebuilt on both sides. Every flipped claim VERIFIES against
#   gold (exit 0) and FAILS against its rival (exit 1) — the exact mirror of the
#   honest witness. So gold's exit code tracks the CLAIM, not the file: no case
#   here is hollow, and the 13 rejections attribute to the spec.
#   ADMISSIBILITY LIVENESS re-derived rather than trusted: replacing ONE conjunct
#   of the in-region assert with a false claim about the SAME point leaves
#   `unsolved goals case «admiss_1: …» ⊢ False` (exit 1), twice, at two different
#   conjuncts (the distinguished-s fall-through and the priority overlap). The
#   assert is load-bearing, not decoration.
#
#   SPEC-TOO-WEAK PROBE (attack D) — eight NEW wrong impls this battery does not
#   contain, aimed where the existing rivals leave the cascade unattacked. ALL
#   EIGHT were REJECTED, so none is a spec hole: dropping the two least-probed
#   distinguished-s clauses (z5/z6 together); dropping the zA z-keyed clause;
#   dropping the zB z-keyed clause (this one became `reject-drop-zkeyed-zb`
#   above); hoisting the whole distinguished-s block ABOVE the z-keyed clauses (a
#   priority violation at a different overlap than C7's); over-firing the outer
#   fall-through with a DIFFERENT wrong code than the shipped rival uses (cfZa,
#   not cfSa); a 3-cycle permutation of the three z-keyed codes; narrowing the
#   second s-keyed clause to fire only at the unrecognised class; and returning a
#   third value (0) from the expansion, neither expPlain nor expPolar. The spec is
#   not weak on any of these.
#   SPEC-TOO-STRONG PROBE (attack E) — three NEW correct reshapes, ALL THREE
#   VERIFY, so the spec is not strong on impl shape: guarding the three z-keyed
#   clauses behind a disjunction and re-testing inside it (needs `omega` appended
#   to the tactic body, like the reorder positive); early-`return` from every
#   branch with no `let` binding at all; and returning `expPolar - 1` from the
#   expansion, an arithmetic spelling of the same value. No faithful correct impl
#   was found that this spec rejects.
#
#   DIVERGENCE (attack F'). The port's disposition is CORRECT and was upheld, and
#   the audit then REPLACED its stated reason twice. See the DIVERGENCE entry above
#   for the builds. Current disposition: REJECTED BY THE SPEC. There is no spec
#   hole, nothing is escalated, and no reject case is shipped only because a rival
#   that fails to elaborate admits no witness at all (the witness contract, stated
#   in that entry). Two earlier accounts of the mechanism are withdrawn: first the
#   one attributing the hole to the `set_option`, then the one attributing the
#   decision to the `open` line alone while calling the `set_option` inert. Neither
#   holds. The `set_option` elaborator ITSELF opens the matching scope
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`, `openScope`, where "total" opens
#   `TotalCorrectness`), Velvet/Syntax.lean:386 opens the same scope by default, and
#   the two lines therefore cannot disagree. The shipped `decreasing` measure is
#   PROVED rather than accepted and discarded: both the constant and the increasing
#   shape were rebuilt here and both fail on the descent goal (`0 < 0`, `i + 1 < i`).
#   RESOLVED FOR THE FLIP LANE, and no live caveat remains. At the time of an
#   earlier audit this bundle's three .lean files were described as half-flipped in
#   the working tree, `set_option ... "total"` with the committed artifact reading
#   `"partial"`. That is over. The committed artifact now reads `"total"` on line 4
#   and `open TotalCorrectness DemonicChoice` on line 7, in Solution.lean and
#   Solution_prepatch.lean alike, and no velvet bundle in this corpus sets
#   "partial". So there is nothing for a flip lane to re-disposition here: the
#   measurements above were taken in the total scope, they hold for the committed
#   artifact, and the `weak-nonterm-echo` slot stays SPEC-CLOSED rather than a
#   known hole. It does not become a portable reject case, for the witness reason
#   above and not for a semantics reason.
AXIOM_TESTS = []
