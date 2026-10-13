"""properties.py — G-PBT falsification battery for sympy__sympy-20438 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside an
``-- impl-start`` / ``-- impl-end`` region is changed, plus — for the one case
that reshapes a loop away — the matching ``prove_correct`` tactic body, which
the consumer spec view also elides; so ``markers.same_spec`` holds and every
``prove_correct`` obligation survives with a byte-identical header).
``expect="verify"`` passes iff (in scope AND verifies); ``expect="reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against
the subject it is refuted on).

DEFENDED SURFACE — THREE contracted methods over a purely-functional core, each
with its own ``prove_correct`` obligation:

  everyElementMember (memberships : List (Option Bool)) return (out : Option Bool)
    ensures out = triAll memberships
  setsCoincide (subAB subBA : Option Bool) return (out : Option Bool)
    ensures out = triAll [subAB, subBA]
  guardedSimplify (bothExpr : Bool) (r normal : Int) return (out : Int)
    ensures bothExpr = true  → out = normal
    ensures bothExpr = false → out = r

``triAll`` is a concrete ``def`` in the pure region (the three-valued
conjunction of a list, dominance order false ≺ none ≺ true): it fully unfolds to
a function of the method's own argument, so the post-images are grounded in the
inputs and there is no opaque answer-key to echo. ``memberships`` /
``subAB`` / ``subBA`` are FREE ``Option Bool`` inputs; ``bothExpr`` / ``r`` /
``normal`` are the free flag and the two relation tokens.

CARRIER NOTE — THE DECIDABLE BOUNDARY, and how a witness reaches the post-image.
The spec is a ``method`` contract, not a bare predicate, so each reject witness
reaches the post-image through Velvet's own tester machinery
(``<name>Tester args = false`` says the extracted program's result violates the
method's postcondition at that concrete input) and closes by ``decide``, checked
in a file whose ``prove_correct`` blocks have been stripped so no tactic script
can mask the verdict. Every argument is a small concrete ``Option Bool`` /
``Bool`` / ``Int`` literal, so ``decide`` reduces the extracted program by
kernel computation. No conditioning on an opaque term is needed anywhere:
``triAll`` is transparent, so every witness is at literal inputs and binds
nothing (the gate's consistency probe is vacuous — there are no hypotheses to be
inconsistent).

THE ``everyElementMember`` REJECT LANE NEEDS A ``witness_reference``, and this is
the one mechanical subtlety of the port. The frozen ``everyElementMember`` keeps
a ``while`` fold, and under ``set_option loom.semantics.choice "demonic"`` that
loop's fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold. So ``decide`` against the FROZEN tester is stuck for EVERY claim, true or
false — the frozen-side exit code carries no information, and a witness refuted
against it would attest to a refutation that was never performed
(``witness-undecided``). Measured here: the stuck error is identical for a real
refutation and for its exact opposite. The four ``everyElementMember`` rivals
therefore name a shared ``witness_reference`` — ``_LOOPFREE``, a variant that
implements the SAME frozen spec as the closed form ``triAll memberships`` (so it
reduces under ``decide``) and VERIFIES. Per the gate's contract that reference is
checked, not trusted: it must share the frozen spec and verify before any witness
is refuted against it. It also ships as an ``expect="verify"`` positive
(``pos-eem-closed-form``), so the battery itself records that loop-freeness is
not what any rival is being rejected for. The ``setsCoincide`` and
``guardedSimplify`` impls are already loop-free, so their witnesses discriminate
against the frozen solution directly.

No ``sorry``/``admit``/``native_decide``/``axiom`` appears in any witness; both
halves of every reject case were checked with real ``scripts/lean_verify.sh``
builds during authoring (rival build green; subject build red BY A REAL
``decide`` REFUTATION — the error text reads "Tactic `decide` proved that the
proposition … is false", never a stuck reduction).

ADVERSARIAL READ of the nagini classes on THIS carrier (full port ledger at the
foot of the file):
  * FRAME / PERMISSION MUTATION — VACUOUS here. This backend is referentially
    transparent; the sequence input is an immutable value handle with no aliasing
    and no fractional permission, so there is nothing to overwrite. The nagini
    frame-mutation rivals (a write to the read-only ``elems`` / ``elems_a``)
    have no counterpart and no substitute is fabricated.
  * PARTIAL-DOMAIN / VALUE — APPLIES as a class, but two specific nagini rivals
    are FALSE RIVALS on this instance and are dropped with the measurement
    recorded: the failing-test membership verdicts are HOMOGENEOUS and the
    reached coincidence queries are symmetric, so "skip the first element" and
    "one containment direction only" faithful patches RESOLVE the harness. See
    the ledger — each was built and run against the real repo, not argued.
  * THREE-VALUED DOMINANCE — the class the nagini sibling could not express and
    the sharpest one here (see ledger): the carrier makes the unknown verdict a
    first-class value, so a rival that gets the false ≺ none ordering BACKWARDS
    is expressible, is refutable, AND leaves a checked test RED. Two such rivals
    are shipped.
  * UNGROUNDED-ORACLE ECHO — N/A. Each post-image is a total, fully unfolded
    function (``triAll`` / an if-then-else) of the method's own arguments; there
    is no opaque answer key to echo.
  * DIVERGENCE / NON-TERMINATION — NOT a spec hole. The spec REJECTS it, and the
    reason it still does not ship as a reject case is a witness-machinery limit,
    not a spec weakness. CORRECTED BY AUDIT on both halves:

    The previous revision called this a "known spec hole" on the stated ground
    that under ``set_option loom.semantics.termination "total"`` a diverging impl
    satisfies every ``ensures`` clause vacuously and VERIFIES. That reasoning is
    the ``"partial"`` disposition and it is exactly INVERTED for this bundle,
    which sets ``"total"``: the verifier discharges a termination obligation, so a
    loop with no decreasing measure is genuinely rejected. Re-measured with real
    builds — a diverging prefix in every impl region (proofs reduced to a bare
    ``loom_solve``) is REJECTED with ``error: Decreasing annotations are required
    in total correctness semantics``, and so is a single-method diverging rival on
    ``setsCoincide``. So is the sharper shape that CARRIES a measure the verifier
    cannot show decreasing, which is the decisive one because it cannot be
    dismissed as merely the missing-annotation linter: ``let mut q : Nat := 1;
    while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q do q := q``
    spliced at the impl anchor is REJECTED on the measure's OWN descent goal,
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. The previous revision cited a
    corpus table splitting 401 ``partial`` bundles against 99 ``total`` ones; that
    cohort does not exist, since all 500 velvet bundles set ``"total"`` and open
    ``TotalCorrectness``. There is NO verify-does-not-imply-resolve gap here and
    the escalation was spurious.

    But the class still cannot ship as a G-PBT reject case, for a reason that is
    structural rather than a proof difficulty. A reject case must carry a witness
    that ELABORATES against the rival, and the diverging rival's module does not
    compile AT ALL: the termination obligation fails at the ``method`` itself, so
    the failure precedes any tester and no appended witness can elaborate there.
    Measured: appending the ``setsCoincideTester (some true) (some true) = false``
    witness to the diverging rival exits 1 with both the decreasing-annotation
    error and a stuck ``Tactic `decide` failed``, which the gate would record as
    ``witness-unproven`` — an INCONCLUSIVE outcome that fails the whole battery.
    That is correct behavior on the gate's part: a diverging impl has no concrete
    input at which it returns a WRONG VALUE, so there is nothing for a
    value-level witness to refute. The rejection is real and attributable to the
    spec's termination clause; it is simply not expressible in the witness
    contract, which is value-level by construction. Recorded as REJECTED-BY-SPEC,
    NOT-EXPRESSIBLE-AS-A-WITNESSED-CASE — neither a spec hole nor a battery gap.
  * AXIOM lane — DROPPED. The three nagini AXIOM_TESTS probe the deep model
    (``triAll`` against the library's three-valued conjunction) and the two
    unchanged reference callees that supply this bundle's inputs; that is G-AX's
    job, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20438"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies wholly inside ONE impl region of _BASE (the one proof-body
# anchor is noted as such) and is unique in the file (both asserted at load by
# _swap). Every variant replaces exactly one of these; the spec, the method
# signatures and the `prove_correct` headers are untouched, so same_spec holds
# and every obligation survives. The frozen tactic scripts no longer close a
# reshaped impl — which is the point: a reject case's rejection is attributed to
# the spec by its witness, not to broken tactics.
# ---------------------------------------------------------------------------

# everyElementMember gold impl body (the whole backward while-fold block).
_GOLD_EEM = """    let mut result : Option Bool := some true
    let mut i := memberships.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ memberships.length
      invariant result = triAll (memberships.drop i)
      done_with i = 0
      decreasing i
    do
      let m := memberships[i - 1]!
      result := tand2 m result
      i := i - 1
    return result"""

# everyElementMember loop body (the three lines under `do`) — the loop-preserving
# positive reshapes only this, leaving the loop/invariants and frozen proof intact.
_EEM_LOOPBODY = """    let m := memberships[i - 1]!
      result := tand2 m result
      i := i - 1"""

# everyElementMember's frozen PROOF BODY. Not an impl anchor: it is the tactic
# body of `prove_correct everyElementMember`, which the consumer spec view elides
# alongside the impl, and which a variant may legitimately re-prove (the
# `prove_correct` HEADER, the obligation itself, is untouched). Only the one
# variant that removes the loop needs this — with no loop there is no drop-step
# goal left for the frozen `rw` to discharge, and leaving it would fail on
# "no goals". Anchored on the two tactic lines that exist solely to serve the
# loop, so the swap cannot silently widen.
_EEM_LOOP_TACTICS = """  rw [triAll_drop_step memberships i (by omega) (by omega)]
  simp_all"""

# setsCoincide gold impl body (the two-valued conjunction).
_GOLD_SC = "    return tand2 subAB subBA"

# guardedSimplify gold impl body (the operand-kind routing guard).
_GOLD_GS = """    if bothExpr then
      return normal
    else
      return r"""

for _a in (_GOLD_EEM, _EEM_LOOPBODY, _EEM_LOOP_TACTICS, _GOLD_SC, _GOLD_GS):
    assert _BASE.count(_a) == 1, f"impl anchor drift — re-sync {_a[:40]!r}"


# ---------------------------------------------------------------------------
# _LOOPFREE — the shared `witness_reference` for the everyElementMember reject
# lane, and simultaneously an expect="verify" positive (pos-eem-closed-form).
#
# WHY IT EXISTS. The frozen everyElementMember keeps a `while` fold; under
# `loom.semantics.choice "demonic"` its fixpoint elaborates through
# `Classical.choice`, which the kernel cannot unfold, so `decide` against the
# frozen tester is STUCK for every claim regardless of truth. Refuting a witness
# there would attest to a refutation that never happened (`witness-undecided`),
# which is precisely what the gate refuses. This variant states the SAME post-
# image as a closed form, so it reduces — and it VERIFIES, which is what makes it
# an admissible subject: an impl the verifier accepts cannot violate its own
# spec, so a genuine witness must still fail against it.
#
# The proof-body swap is required BY the impl reshape, not a weakening: with the
# loop gone `loom_solve` closes the whole obligation (the post-image is now the
# return expression syntactically), and the frozen `rw [triAll_drop_step …]`
# would fail on "no goals". The `prove_correct everyElementMember` header — the
# obligation — is byte-identical, and no lemma, axiom or `sorry` is added: the
# frozen `triAll_drop_step` lemma simply goes unused here. Verified with a real
# build (scope-ok + verifies), and the gate re-checks both before using it.
# ---------------------------------------------------------------------------
_LOOPFREE = _swap(
    _swap(_BASE, _GOLD_EEM, "    return triAll memberships"),
    "\n" + _EEM_LOOP_TACTICS, "")


# ---------------------------------------------------------------------------
# ADMISSIBILITY (added by audit). The frozen `setsCoincide` proof body — elided
# from the spec view alongside the impl, so retuning it keeps `same_spec` and the
# `prove_correct setsCoincide` HEADER (the obligation) byte-identical.
#
# WHY THIS LANE EXISTS ON A TOTAL CARRIER. No method here declares a `require`,
# so the admitted domain is total and no input can be excluded — the crude
# PRECOND-TOO-STRONG shape is genuinely unavailable. But that is NOT the same as
# the lane being vacuous: the analogue on a total carrier is the OBLIGATION being
# unsatisfiable at an F2P-shaped input (a post-image no computation can hit), and
# that is testable directly by discharging the method's own Hoare triple at that
# concrete input, BY EVALUATION, as a `have`, before closing the frozen
# obligation verbatim. The previous revision recorded this lane as VACUOUS on the
# reasoning that "every post-image is a total function so `out = …` is
# satisfiable by construction" — an argument, not a demonstration, and the one
# the audit brief names as insufficient.
#
# The point chosen is `(none, some false)` — the (unknown, definite-false)
# containment pair, which is the input the defended behavior newly decides and
# the sharpest point in the whole battery (`weak-sc-none-dominates` is separated
# from gold at exactly there and nowhere else). If the obligation were
# unsatisfiable there, this `have` could not be discharged and the case would
# FAIL, which is PRECOND-TOO-STRONG. Nothing is weakened: the frozen `loom_solve`
# still closes the real obligation afterwards, and no lemma, axiom or `sorry` is
# added.
# ---------------------------------------------------------------------------
_SC_PROOF = "prove_correct setsCoincide by\n  loom_solve"
assert _BASE.count(_SC_PROOF) == 1, "proof anchor drift — _SC_PROOF"

_ADMISS_SC = _swap(_BASE, _SC_PROOF, """prove_correct setsCoincide by
  have hreach : triple True (setsCoincide none (some false))
      (fun out => out = triAll [none, some false]) := by
    simp only [setsCoincide, triple]
    intro _
    rw [wp_pure]
    decide
  loom_solve""")


# ---------------------------------------------------------------------------
# DIVERGENCE (audit measurement, deliberately NOT shipped as a case).
#
# Kept as source so the measurement is reproducible from the artifact rather than
# only asserted in prose. A non-terminating loop spliced ahead of the
# `setsCoincide` computation — the impl still computes gold's answer, it just
# never delivers it, which is the WEAKEST form of the attack.
#
# Under this bundle's `loom.semantics.termination "total"` the verifier REJECTS
# it: `error: Decreasing annotations are required in total correctness
# semantics`. So the spec is not weak here and there is no hole to escalate.
#
# It is not a shippable reject case because the rejection lands on the `method`'s
# termination obligation, so the module does not compile and NO appended witness
# can elaborate against it (measured: exit 1, decreasing-annotation error plus a
# stuck `decide`, which the gate records as the inconclusive `witness-unproven`).
# A diverging impl returns no wrong VALUE at any concrete input, so there is
# nothing for a value-level witness to refute. See the docstring's divergence
# entry for the full accounting.
# ---------------------------------------------------------------------------
_DIVERGE_SC_MEASURED_REJECTED = _swap(
    _BASE, _GOLD_SC,
    "    while true do\n      pure ()\n    return tand2 subAB subBA")


# ---- witness preambles. `<name>Tester args = false` says the extracted program
# ---- violates the method's postcondition at that concrete input; the block is
# ---- appended to BOTH the rival and the (obligation-stripped) subject file, so
# ---- the tester names exist on both sides by construction.
_EEM_T = (
    "extract_program_for everyElementMember\n"
    "prove_precondition_decidable_for everyElementMember\n"
    "prove_postcondition_decidable_for everyElementMember\n"
    "derive_tester_for everyElementMember\n\n")
_SC_T = (
    "extract_program_for setsCoincide\n"
    "prove_precondition_decidable_for setsCoincide\n"
    "prove_postcondition_decidable_for setsCoincide\n"
    "derive_tester_for setsCoincide\n\n")
_GS_T = (
    "extract_program_for guardedSimplify\n"
    "prove_precondition_decidable_for guardedSimplify\n"
    "prove_postcondition_decidable_for guardedSimplify\n"
    "derive_tester_for guardedSimplify\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify; if a faithful correct reshape cannot verify, the clause
    # is SPEC-TOO-STRONG. All four verified with real builds.
    # =====================================================================
    {
        "id": "pos-eem-inline-head",
        "kind": "soundness",
        "expect": "verify",
        # Inline the exposed element into the `tand2` call instead of naming it
        # in a `let`. Same value flow: the loop, invariants and proof are intact.
        "module": _swap(
            _BASE, _EEM_LOOPBODY,
            "    result := tand2 (memberships[i - 1]!) result\n"
            "      i := i - 1"),
        "rationale": (
            "structurally-different but CORRECT reshape of everyElementMember: "
            "the exposed element is inlined into the `tand2` call rather than "
            "bound to a local. The fold value, and thus `out = triAll "
            "memberships`, is unchanged on every input; only the loop BODY is "
            "touched so the frozen backward-fold proof still discharges. Must "
            "verify, else the clause pins code shape over behavior "
            "(SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-eem-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # The loop replaced by the closed form it computes. Also the shared
        # `witness_reference` for the everyElementMember reject lane — shipped as
        # a positive so the battery RECORDS that loop-freeness verifies, i.e.
        # that it is not what any rival is being rejected for.
        "module": _LOOPFREE,
        "rationale": (
            "structurally-different but CORRECT impl of everyElementMember: the "
            "backward fold is replaced by the closed form it computes, so the "
            "post-image `out = triAll memberships` holds on every input by "
            "definition rather than by loop invariant. This is the MOST "
            "different admissible shape for this obligation, and it must verify "
            "— if a faithful impl that computes the specified conjunction "
            "directly is rejected, the clause pins the ITERATION SCHEME rather "
            "than the value (SPEC-TOO-STRONG). It also carries the battery's "
            "`witness_reference`: shipping it as a positive is what records that "
            "loop-freeness per se verifies, so no everyElementMember rival is "
            "rejected merely for being loop-free. The tactic body drops the two "
            "loop-only lines (with no loop there is no drop-step goal and the "
            "frozen `rw` would fail on 'no goals'); the obligation header is "
            "byte-identical and nothing is assumed."),
    },
    {
        "id": "pos-sc-hoist-local",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the two-valued conjunction into a named local before returning.
        "module": _swap(
            _BASE, _GOLD_SC,
            "    let both := tand2 subAB subBA\n    return both"),
        "rationale": (
            "structurally-different but CORRECT reshape of setsCoincide: the "
            "conjunction is hoisted into a named local before the return. Returns "
            "the identical value, so `out = triAll [subAB, subBA]` still holds "
            "and the frozen `loom_solve` obligation discharges. Must verify, else "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-gs-negate-guard",
        "kind": "soundness",
        "expect": "verify",
        # Negate the discriminator and swap the two branch bodies to match
        # (De-Morgan-equivalent control flow). Same value on every input.
        "module": _swap(
            _BASE, _GOLD_GS,
            "    if bothExpr = false then\n"
            "      return r\n"
            "    else\n"
            "      return normal"),
        "rationale": (
            "structurally-different but CORRECT reshape of guardedSimplify: the "
            "discriminator test is negated and the two branch bodies swapped to "
            "match, still keyed to `bothExpr`, so both implication clauses hold "
            "on every input. Straight-line two-way branch — no lemma — so the "
            "frozen `loom_solve` obligation discharges. Must verify, else "
            "SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY (added by audit) — the obligation must be SATISFIABLE at an
    # F2P-shaped input. On this total carrier there is no `require` to be too
    # strong, so the lane's analogue is an unsatisfiable post-image, discharged
    # here by EVALUATION at the concrete point the defended behavior newly
    # decides. If it cannot be discharged => PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-sc-reachable-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_SC,
        "rationale": (
            "ADMISSIBILITY at an F2P-shaped input. No method in this bundle "
            "declares a `require`, so the admitted domain is total and the crude "
            "PRECOND-TOO-STRONG shape (a precondition that excludes a normal "
            "input) is unavailable. The analogue on a total carrier is the "
            "OBLIGATION being unsatisfiable at a concrete reachable input, and "
            "this case tests that directly: it discharges `setsCoincide`'s own "
            "Hoare triple at `(none, some false)` — the (unknown, definite-false) "
            "containment pair the defended behavior newly decides, and the exact "
            "point at which the battery's sharpest rival "
            "(weak-sc-none-dominates) is separated from the frozen impl — by "
            "EVALUATION, as a `have`, before the frozen `loom_solve` closes the "
            "real obligation verbatim. The post-image must be HIT by an actual "
            "computation at that point, not merely be a total function of the "
            "inputs. If this cannot be discharged the obligation is unsatisfiable "
            "where the fix must act (PRECOND-TOO-STRONG). Added by audit: the "
            "previous revision recorded this lane as vacuous on the argument that "
            "a total post-image is satisfiable by construction — an argument, not "
            "a demonstration. The `prove_correct setsCoincide` header is "
            "byte-identical and nothing is assumed."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # `decide`s) with a machine-checked refutation witness at a concrete input,
    # and the refinement argument grounded in the REAL patched-repo behavior:
    # every rival below was BUILT as a faithful source patch on top of gold and
    # RUN against the F2P tests in the instance image, and left a checked test
    # RED. The ledger records each measurement.
    # =====================================================================

    # ---- everyElementMember: post-image `out = triAll memberships` ----
    # All four refute against `_LOOPFREE` rather than the frozen solution: the
    # frozen loop cannot decide anything (see the module docstring).
    {
        "id": "weak-eem-ignore-none",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: no (product, collection) containment rule, so
        # the query is never decided and the verdict is `none` regardless of the
        # membership values.
        "module": _swap(_BASE, _GOLD_EEM, "    return none"),
        "witness": _EEM_T +
        "example : everyElementMemberTester [some true] = false := by\n  decide\n",
        "witness_reference": _LOOPFREE,
        "refinement": (
            "this is the PRE-PATCH behaviour: with no rule for a finite product "
            "against a finite collection the containment query is never decided "
            "and returns the unknown verdict. MEASURED against the real repo — "
            "the faithful patch (the containment rule returning the unknown "
            "verdict outright) was applied on top of gold and the failing tests "
            "run in the instance image: the reproducer test FAILS "
            "(AssertionError on the positive containment assertion, which "
            "demands a DEFINITE verdict). It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll memberships`: `triAll` of an all-present "
            "list is `some true`, but this impl returns `none`. Refuted at "
            "`memberships = [some true]`, where `triAll = some true ≠ none`. If "
            "it verifies, the clause does not force the verdict to be COMPUTED "
            "from the memberships (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-eem-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the membership values and always report definitely-contained.
        "module": _swap(_BASE, _GOLD_EEM, "    return some true"),
        "witness": _EEM_T +
        "example : everyElementMemberTester [some false] = false := by\n  decide\n",
        "witness_reference": _LOOPFREE,
        "refinement": (
            "reports definitely-contained regardless of the elements' membership. "
            "MEASURED: the faithful patch (the containment rule short-circuiting "
            "to a positive verdict) was applied on top of gold and run — the "
            "reproducer test FAILS (AssertionError), because it asserts a "
            "definitely-NOT-contained verdict for a product whose elements are "
            "absent from the collection. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll memberships`: `triAll` of a list "
            "containing a definite-absent is `some false`, but this impl returns "
            "`some true`. Refuted at `memberships = [some false]`, where "
            "`triAll = some false ≠ some true`. Attacks the false-dominance "
            "direction of the fold: weak-eem-ignore-none is ALSO wrong at this "
            "point (it yields `none`), so the two rivals are not separated here — "
            "what makes them disjoint is the DIRECTION each gets wrong (this one "
            "over-reports containment, that one refuses to decide it), and each "
            "carries its own witness. If it verifies, an absent element need not "
            "force a not-contained verdict (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-eem-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the membership values and always report definitely-not-contained.
        # NEAR-MISS on the EMPTY input: it is the one point where gold says
        # `some true` and every other eem witness agrees with this rival, so it
        # gets its own witness at the empty list rather than sharing one.
        "module": _swap(_BASE, _GOLD_EEM, "    return some false"),
        "witness": _EEM_T +
        "example : everyElementMemberTester ([] : List (Option Bool)) = false := by\n"
        "  decide\n",
        "witness_reference": _LOOPFREE,
        "refinement": (
            "reports definitely-not-contained regardless of the elements' "
            "membership. MEASURED: the faithful patch (the containment rule "
            "returning a negative verdict outright) was applied on top of gold "
            "and run — the reproducer test FAILS (AssertionError) on the "
            "positive containment assertion. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll memberships`: the EMPTY conjunction is "
            "`some true` (the fold's identity), but this impl returns "
            "`some false`. Refuted at `memberships = []` — the boundary point no "
            "other witness in this battery probes, and the only input where this "
            "rival differs from weak-eem-length-only (the two agree on every "
            "non-empty list, both answering `some false`), so it carries its own "
            "witness rather than sharing one. Moves the `memberships` binder to "
            "length 0 and pins the fold's IDENTITY. If it verifies, the empty "
            "case is unconstrained (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-eem-length-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Decide by the SHAPE (emptiness) of the enumeration, never reading a
        # single membership verdict: empty ⇒ definitely-contained, else
        # definitely-not.
        "module": _swap(
            _BASE, _GOLD_EEM,
            "    return (if memberships.isEmpty then some true else some false)"),
        "witness": _EEM_T +
        "example : everyElementMemberTester [some true, some true] = false := by\n"
        "  decide\n",
        "witness_reference": _LOOPFREE,
        "refinement": (
            "decides containment from the enumeration LENGTH alone, never "
            "inspecting a membership verdict: a non-empty product is reported "
            "not-contained outright. MEASURED: the faithful patch (the "
            "containment rule reduced to an emptiness test on the enumeration) "
            "was applied on top of gold and run — the reproducer test FAILS "
            "(AssertionError) on the non-empty, fully-present product. It would "
            "NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll memberships`: a non-empty all-present list "
            "has `triAll = some true`, but this impl returns `some false`. "
            "Refuted at `memberships = [some true, some true]`, where "
            "`triAll = some true ≠ some false`. Moves the binder to a length-2 "
            "point and attacks dependence on the CONTENT rather than the length "
            "(it agrees with gold on the empty list, which is why its witness is "
            "at length 2 and not shared with weak-eem-const-false). If it "
            "verifies, the verdict need not depend on the per-element verdicts at "
            "all (SPEC-TOO-WEAK)."),
    },

    # ---- setsCoincide: post-image `out = triAll [subAB, subBA]` ----
    {
        "id": "weak-sc-ignore-none",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: the generic set-coincidence rule never consults
        # the containment facts and returns the unknown verdict.
        "module": _swap(_BASE, _GOLD_SC, "    return none"),
        "witness": _SC_T +
        "example : setsCoincideTester (some true) (some true) = false := by\n"
        "  decide\n",
        "refinement": (
            "this is the PRE-PATCH behaviour: the generic coincidence rule "
            "returns the unknown verdict without consulting mutual containment. "
            "MEASURED: applied on top of gold and run — BOTH failing tests FAIL "
            "(AssertionError), since each asserts a definite coincidence verdict "
            "where this yields unknown. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll [subAB, subBA]`: two definite-true "
            "containments give `triAll = some true`, but this impl returns "
            "`none`. Refuted at `subAB = some true, subBA = some true`. If it "
            "verifies, coincidence need not be COMPUTED from the two containment "
            "verdicts (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-sc-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Always report definitely-not-coincident, ignoring both containments.
        "module": _swap(_BASE, _GOLD_SC, "    return some false"),
        "witness": _SC_T +
        "example : setsCoincideTester none (some true) = false := by\n  decide\n",
        "refinement": (
            "reports definitely-not-coincident regardless of the containments. "
            "MEASURED: applied on top of gold and run — the reproducer test FAILS "
            "(AssertionError) on the positive coincidence assertion, which "
            "demands definitely-equal for a mutually-contained pair. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = triAll [subAB, subBA]`: when the first "
            "containment is unknown and the second definite-true, `triAll` is "
            "`none`, but this impl returns `some false`. Refuted at "
            "`subAB = none, subBA = some true` — moving `subAB` to the unknown "
            "value, and probing the none-propagation direction of the fold. If it "
            "verifies, the clause does not force the coincidence verdict to track "
            "the containments (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-sc-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Always report definitely-coincident, ignoring both containments.
        "module": _swap(_BASE, _GOLD_SC, "    return some true"),
        "witness": _SC_T +
        "example : setsCoincideTester (some true) (some false) = false := by\n"
        "  decide\n",
        "refinement": (
            "reports definitely-coincident regardless of the containments. "
            "MEASURED: applied on top of gold and run — the changed coincidence "
            "test FAILS (AssertionError), since it asserts definitely-NOT-equal "
            "for a pair that is not mutually contained. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll [subAB, subBA]`: a definite-true and a "
            "definite-false containment give `triAll = some false` (false "
            "dominates), but this impl returns `some true`. Refuted at "
            "`subAB = some true, subBA = some false` — moving `subBA` to the "
            "definite-false value. Attacks the false-dominance direction "
            "(disjoint from weak-sc-const-false). If it verifies, a failed "
            "reverse containment need not defeat coincidence (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-sc-none-dominates",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS, and the sharpest rival in the battery: the three-valued
        # combination is ORDERED WRONG — an unknown containment is allowed to
        # dominate a definite-false one, so the verdict is unknown where it must
        # be definitely-not-coincident. Agrees with gold everywhere else.
        "module": _swap(
            _BASE, _GOLD_SC,
            "    return (if subAB = none then none"
            " else if subBA = none then none else tand2 subAB subBA)"),
        "witness": _SC_T +
        "example : setsCoincideTester none (some false) = false := by\n  decide\n",
        "refinement": (
            "gets the DOMINANCE ORDER of the three-valued combination backwards: "
            "an unknown containment outranks a definite-false one, so a pair with "
            "one unknown and one definitely-failed containment is reported "
            "unknown instead of definitely-not-coincident. This is the rival the "
            "checked domain is sharpest about, and it is NOT a false rival: "
            "MEASURED against the real repo, the faithful patch (the combination "
            "short-circuiting to unknown whenever any operand is unknown) applied "
            "on top of gold makes the changed coincidence test FAIL "
            "(AssertionError) — that test asserts a DEFINITE negative verdict at "
            "exactly a (unknown, definite-false) containment pair, which is the "
            "point the fix newly decides. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll [subAB, subBA]`: `triAll` gives "
            "`some false` when either operand is definite-false, even against an "
            "unknown (false ≺ none in the dominance order), but this impl returns "
            "`none`. Refuted at `subAB = none, subBA = some false` — an input "
            "point NO other witness probes, and the only sub-domain where this "
            "rival differs from gold at all, so it cannot share a witness with "
            "the constant rivals. Pins the false-beats-unknown edge of the fold. "
            "If it verifies, the spec does not fix the dominance ORDER, only the "
            "all-definite cases (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-sc-disjunctive",
        "kind": "uniqueness",
        "expect": "reject",
        # The two containments COMBINED WRONG: either one sufficing (disjunction)
        # instead of both being required (conjunction). Agrees with gold whenever
        # the two containments agree — so its witness must be at a MIXED pair.
        "module": _swap(
            _BASE, _GOLD_SC,
            "    return (if subAB = some true then some true"
            " else if subBA = some true then some true else tand2 subAB subBA)"),
        "witness": _SC_T +
        "example : setsCoincideTester (some false) (some true) = false := by\n"
        "  decide\n",
        "refinement": (
            "COMBINES the two containments disjunctively — either direction "
            "holding is enough — instead of requiring both. MEASURED: applied on "
            "top of gold and run, the changed coincidence test FAILS "
            "(AssertionError), because it asserts definitely-NOT-equal for a pair "
            "where one containment holds and the other definitely fails. It would "
            "NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll [subAB, subBA]`: MUTUAL containment is "
            "required, so a definite-false in either operand forces `some false`, "
            "but this impl returns `some true` on the strength of the other "
            "operand alone. Refuted at `subAB = some false, subBA = some true` — "
            "the MIRROR of weak-sc-const-true's point, which is what "
            "discriminates it: this rival agrees with gold whenever the two "
            "containments agree, so only a mixed pair separates it, and it must "
            "be the mixed pair with the definite-false FIRST (at "
            "`(some true, some false)` this rival is also `some true`, hence a "
            "shared witness would not distinguish which operand is mishandled). "
            "Varies `subAB` to definite-false, a value no other witness gives it. "
            "If it verifies, the clause does not pin the COMBINATION of the two "
            "containments (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-sc-forward-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the verdict from the FIRST containment alone, dropping the second
        # entirely. Recovered by audit: an earlier revision dropped the whole
        # one-direction class as a FALSE rival, but that measurement holds only of
        # the REVERSE direction. See the ledger for the corrected accounting.
        "module": _swap(_BASE, _GOLD_SC, "    return subAB"),
        "witness": _SC_T +
        "example : setsCoincideTester (some true) none = false := by\n  decide\n",
        "refinement": (
            "reads the verdict off the FIRST containment alone and never consults "
            "the second, so a collection contained in another is reported to "
            "coincide with it regardless of the reverse containment. This "
            "direction is F2P-RED, and the distinction from its mirror is the "
            "point: of the reached containment pairs recorded in the ledger, the "
            "one whose two sides DISAGREE is (unknown, definite-false) — first "
            "side unknown, second definite-false. Reading the FIRST side there "
            "yields the unknown verdict where a definite negative is asserted, so "
            "a checked coincidence test FAILS; reading the SECOND side happens to "
            "reproduce gold on every reached pair, which is why only that mirror "
            "is a false rival. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = triAll [subAB, subBA]`: the post-image conjoins "
            "BOTH containments, so the second is load-bearing, but this impl "
            "returns the first operand unchanged. Refuted at `subAB = some true, "
            "subBA = none`, where `triAll` is `none` and the impl yields "
            "`some true`. That point is reached by no other witness in the "
            "battery, and it is the only input where this rival is separated from "
            "gold that the shipped sc lane did not already cover; it also moves "
            "`subBA` to the unknown value, which no other setsCoincide witness "
            "gives it, so that binder now ranges over all three carrier values. "
            "Distinct from weak-sc-disjunctive: that rival over-reports on the "
            "strength of EITHER operand, this one is blind to the second operand "
            "entirely (they differ at `(some false, some true)`, where the "
            "disjunctive rival says `some true` and this one `some false`). If it "
            "verifies, the clause does not force the SECOND containment to be "
            "consulted at all (SPEC-TOO-WEAK)."),
    },

    # ---- guardedSimplify: both implication clauses ----
    {
        "id": "weak-gs-always-normal",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: no operand-kind guard, so the general
        # simplification result is returned UNCONDITIONALLY, even when the
        # operands are not both algebraic expressions.
        "module": _swap(_BASE, _GOLD_GS, "    return normal"),
        "witness": _GS_T +
        "example : guardedSimplifyTester false 3 7 = false := by\n  decide\n",
        "refinement": (
            "this is the PRE-PATCH behaviour: with no operand-kind guard the "
            "general simplification path runs even for non-expression operands. "
            "MEASURED: removing both guards on top of gold reproduces the "
            "reported failure exactly — the reproducer test ERRORS with "
            "AttributeError (the general path forms a difference the "
            "non-expression operand cannot support), so it is RED. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `bothExpr = false → out = r`: when the operands are not "
            "both expressions the relation must be returned UNCHANGED, but this "
            "impl returns the general-path result `normal`. Refuted at "
            "`bothExpr = false, r = 3, normal = 7`, where the clause demands "
            "`out = 3` and the impl yields `7`. The two relation tokens are given "
            "values distinct from each other AND from those in "
            "weak-gs-inverted-guard (which uses 5 / 2, and in the opposite "
            "order), so neither `r` nor `normal` is pinned to a single literal "
            "across the reject lane — a rival returning a CONSTANT in either arm, "
            "rather than the wrong one of the two tokens, is caught too. If it "
            "verifies, the non-expression guard is unpinned (SPEC-TOO-WEAK)."),
    },
    {
        "id": "weak-gs-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The guard keyed BACKWARDS: the general result is returned exactly when
        # the operands are NOT both expressions, and the relation returned
        # unchanged when they ARE. Attacks the OTHER clause
        # (`bothExpr = true → out = normal`), which no other rival here touches.
        "module": _swap(
            _BASE, _GOLD_GS,
            "    if bothExpr then\n      return r\n    else\n      return normal"),
        "witness": _GS_T +
        "example : guardedSimplifyTester true 5 2 = false := by\n  decide\n",
        "refinement": (
            "keys the operand-kind discriminator BACKWARDS: the general "
            "simplification result is returned precisely for the operands that "
            "cannot support it, and the relation is returned unchanged precisely "
            "for the operands that can. MEASURED: applied on top of gold and run, "
            "the reproducer test ERRORS with the reported AttributeError — the "
            "inverted guard still routes non-expression operands into the general "
            "path — so it is RED. It would NOT resolve. (Note the contrast with "
            "the always-return-unchanged rival, which the ledger records as a "
            "FALSE rival: that one resolves the checked set. Inverting the guard "
            "is refutable AND leaves a checked test red, which is why this is the "
            "clause-1 attack that ships.)"),
        "rationale": (
            "REJECT from `bothExpr = true → out = normal`: when the operands ARE "
            "both expressions the general result must be returned, but this impl "
            "returns the original relation `r`. Refuted at "
            "`bothExpr = true, r = 5, normal = 2`, where the clause demands "
            "`out = 2` and the impl yields `5`. This is the ONLY rival attacking "
            "the true-arm clause, and it moves `bothExpr` to true — the value the "
            "other guardedSimplify witness does not probe — so neither clause of "
            "this obligation is left unattacked (its counterpart "
            "weak-gs-always-normal attacks the false-arm at `bothExpr = false`). "
            "The token values (5 / 2) differ from that witness's (3 / 7) and "
            "invert their order, so `r` and `normal` each range over two literals "
            "with `normal` the LARGER in one witness and the SMALLER in the other: "
            "no rival can agree with the spec at both points by returning a "
            "constant, or by comparing the two tokens. If it verifies, the "
            "guard's POLARITY is unpinned (SPEC-TOO-WEAK)."),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals — two of which are
# frame-mutation permission rivals) plus a 3-case AXIOM_TESTS lane this gate
# ignores. The nagini surface contracts three functions
# (`product_subset_of_finite`, `finite_sets_equal`, `simplify_equality_route`)
# over a fractional-permission carrier with a grounded `all_in` fold oracle. This
# velvet bundle models the SAME three behaviors as three methods
# (`everyElementMember`, `setsCoincide`, `guardedSimplify`) over an immutable,
# referentially-transparent carrier, so the two batteries line up behavior-for-
# behavior — but the carrier change forces the frame/permission class out, an
# F2P-domain fact drops the partial-domain and one-direction rivals, and the
# three-valued carrier ADDS a dominance/combination class nagini could not state.
#
# GROUND TRUTH — every claim below was MEASURED in the instance image
# (swebench/sweb.eval.x86_64.sympy_1776_sympy-20438), gold patch + test_patch
# applied, by building each rival as a faithful source patch and running the two
# F2P tests directly. Gold baseline: both F2P tests PASS and all 93 PASS_TO_PASS
# tests pass.
#
#   * The F2P subset queries have HOMOGENEOUS membership verdicts:
#     [T,T,T,T] for the positive containment, [F,F,F,F] for the negative.
#   * The coincidence queries the F2P tests reach, as (subAB, subBA) pairs:
#     (T,T)->true, (F,F)->false, (None,F)->false, (None,None)->false,
#     plus a symbolic pair left unevaluated.
#
# FALSE RIVALS — dropped because their faithful patch RESOLVES (measured, not
# assumed). Shipping one would claim a verify-does-not-imply-resolve break that
# does not exist:
#   - "skip the first enumerated element" (the containment fold started one
#     element in): both F2P tests PASS. The verdict lists are homogeneous, so
#     dropping one element cannot flip either answer. (nagini partial-first-psof)
#   - "one containment direction only", REVERSE direction ONLY (the coincidence
#     verdict taken from the SECOND containment alone): both F2P tests PASS. On
#     every reached pair above, the second side already equals the conjunction,
#     so dropping the first cannot flip an answer. (nagini one-direction-fse,
#     wrong-outcome-route)
#     CORRECTED BY AUDIT: this drop was originally recorded for BOTH directions,
#     on the stated ground that "the reached coincidence pairs are symmetric".
#     They are not. The reached set recorded above contains (None,F) but not its
#     mirror (F,None), so it is not closed under swapping the pair, and the two
#     directions are NOT interchangeable: at (None,F) the conjunction is F, the
#     SECOND side is F (agrees, hence a false rival) but the FIRST side is None
#     (disagrees, hence F2P-RED). The forward direction was therefore dropped on
#     a premise the ledger's own data refutes. It now ships as
#     weak-sc-forward-only; only the reverse direction is a genuine false rival.
#   - "always return the relation unchanged" (both guards fire
#     unconditionally): both F2P tests PASS and all 93 P2P tests pass; it breaks
#     only tests outside the checked set.
#
# NEW RIVALS the nagini carrier could not express. Nagini's `all_in` folds to a
# two-valued `bool`, so the unknown verdict is not a value there and neither the
# dominance ORDER nor the COMBINATION of the containments can be attacked. On this
# carrier `Option Bool` makes both first-class, and both attacks are real:
#   - weak-sc-none-dominates (unknown outranks definite-false): changed
#     coincidence test FAILS. This is the sharpest rival in the battery — it
#     agrees with gold on every all-definite input and is separated ONLY at
#     (none, some false), which is precisely a point the fix newly decides.
#   - weak-sc-disjunctive (either containment suffices): changed coincidence
#     test FAILS.
#   - weak-eem-const-false / weak-gs-inverted-guard: reproducer test FAILS /
#     ERRORS respectively.
#
#   nagini case                       -> here                        status
#   ----------------------------------------------------------------------------
#   pos-control-reshape-psof          -> pos-eem-inline-head           PORTED
#   pos-control-route-reshape         -> pos-gs-negate-guard           PORTED
#   (+ setsCoincide positive)         -> pos-sc-hoist-local            ADDED (per-obligation)
#   (+ loop-free reference positive)  -> pos-eem-closed-form           ADDED (carrier-forced)
#   admiss-fse-selfcall               -> admiss-sc-reachable-point     PORTED (audit: re-aimed
#                                        at post-image SATISFIABILITY at a concrete
#                                        F2P-shaped input; previously dropped as
#                                        VACUOUS on an argument, not a demonstration)
#   frame-mut-psof                    -> (none)                        VACUOUS (no heap/perm)
#   frame-mut-fse                     -> (none)                        VACUOUS (no heap/perm)
#   empty-cheapest-psof               -> weak-eem-length-only          PORTED
#   partial-first-psof                -> (none)                        DROPPED (resolves F2P, measured)
#   one-direction-fse                 -> weak-sc-forward-only          PORTED (audit: forward
#                                        direction is F2P-RED; only the REVERSE
#                                        direction is the false rival)
#   no-guard-route                    -> weak-gs-always-normal         PORTED
#   wrong-outcome-route               -> (none)                        DROPPED (resolves F2P, measured:
#                                        reverse direction only)
#   (+ prepatch/degenerate coverage)  -> weak-eem-ignore-none,
#                                        weak-eem-const-true,
#                                        weak-sc-ignore-none,
#                                        weak-sc-const-false,
#                                        weak-sc-const-true             ADDED
#   (+ three-valued dominance class)  -> weak-sc-none-dominates,
#                                        weak-sc-disjunctive,
#                                        weak-eem-const-false,
#                                        weak-gs-inverted-guard         ADDED (carrier-enabled)
#   AXIOM_TESTS (3)                   -> (none)                        DROPPED (G-AX lane)
#
# 4 positives (2 ported + 2 added), 1 ADMISSIBILITY positive (added by audit) and
# 12 uniqueness rivals shipped; 2 frame-mutation rivals vacuous, 2
# partial/one-direction rivals dropped as MEASURED to resolve (the third, the
# FORWARD one-direction rival, was dropped in error and now ships as
# weak-sc-forward-only — see the corrected false-rival accounting above), 3 axiom
# probes dropped. No case was dropped because its proof or witness was hard; every
# shipped rival's witness was seen to discriminate with real builds, and every
# dropped rival's faithful patch was seen to RESOLVE with a real repo run.
#
# ADMISSIBILITY — LANDED BY AUDIT (was recorded VACUOUS, wrongly):
#  * admiss-fse-selfcall -> admiss-sc-reachable-point. The nagini case witnesses
#    that the read-only half-permission precondition admits an F2P-shaped input
#    and the permissions round-trip. The previous revision dropped the lane as
#    VACUOUS, reasoning that no method here has a `require` (true) and that the
#    residual total-domain risk cannot arise because "every post-image is a total
#    function so `out = …` is satisfiable at every input by construction". That
#    last step is an ARGUMENT, not a demonstration, and dropping the lane on it
#    silently removed one of the three directions this gate exists to test —
#    exactly the systematic omission the audit brief flags (494 of 500 nagini
#    batteries carry this lane; the velvet ports mostly do not).
#    The lane's analogue on a total carrier is the OBLIGATION being unsatisfiable
#    at an F2P-shaped input, and that is now tested directly and mechanically:
#    admiss-sc-reachable-point discharges `setsCoincide`'s own Hoare triple at the
#    concrete `(none, some false)` containment pair — the (unknown,
#    definite-false) point the defended behavior newly decides — by EVALUATION, as
#    a `have`, before the frozen `loom_solve` closes the real obligation verbatim.
#    Measured: it VERIFIES (real build, exit 0), and it is in variant scope
#    (same_spec holds; the `prove_correct setsCoincide` header is byte-identical).
#  * frame-mut-psof / frame-mut-fse. The nagini rivals write to a read-only
#    half-permission input to trip INSUFFICIENT PERMISSION. This backend is
#    referentially transparent, has no heap or aliasing, and this bundle declares
#    no `mut` binder — there is no read-only input to overwrite and no substitute
#    probe. Not fabricated.
#
# DIVERGENCE — NOT A HOLE. CORRECTED BY AUDIT; the previous revision had this
#  class exactly backwards and escalated a gap that does not exist.
#
#  What it said: this bundle carries `set_option loom.semantics.termination
#  "total"`, so a non-terminating impl satisfies every `ensures` clause VACUOUSLY
#  and VERIFIES, a genuine verify-does-not-imply-resolve gap, open and escalated.
#
#  What is true: vacuous satisfaction is the `"partial"` disposition, and this file
#  is not that. Under `"total"` a postcondition is claimed of ALL runs, so the
#  verifier discharges a TERMINATION obligation and a loop with no decreasing
#  measure is REJECTED. The setting and the scope cannot disagree either: the
#  `set_option` elaborator itself runs `openScope `TotalCorrectness`
#  (`Loom/MonadAlgebras/WP/Options.lean:169-186`), and the frozen file opens
#  `TotalCorrectness` on top of that. The previous revision also pointed at a
#  corpus split of 401 `partial` bundles against 99 `total` ones; there is no such
#  split, since all 500 velvet bundles set "total".
#
#  MEASURED HERE with real builds, both shapes:
#    - the generic probe (diverging prefix in EVERY impl region, proofs reduced to
#      a bare `loom_solve`, on a scratch copy with the bundle unmodified):
#      REJECTED, `error: Decreasing annotations are required in total correctness
#      semantics` at all three methods.
#    - a single-method diverging rival on `setsCoincide`
#      (`_DIVERGE_SC_MEASURED_REJECTED`, kept above so this is reproducible):
#      REJECTED, same error.
#    - the sharper shape, a loop that CARRIES a measure the verifier cannot show
#      decreasing (`let mut q : Nat := 1; while q > 0 / invariant 0 <= q /
#      done_with q = 0 / decreasing q`, body `q := q`): REJECTED on the MEASURE's
#      own descent goal, `case «decreasing_1: q»`, residual `q < q`. This is the
#      one that settles it, since it cannot be read as the annotation linter.
#  So the spec is STRONG here and there is nothing to escalate.
#
#  Why it still does not ship as a reject case — a witness-contract limit, not a
#  proof difficulty and not a spec weakness. The rejection lands on the `method`'s
#  termination obligation, so the rival module does not compile at all and no
#  APPENDED witness can elaborate against it. Measured: the diverging rival plus
#  That is the shape with NO measure. A rival that CARRIES a measure which does
#  not decrease is refused at the ``prove_correct`` site instead, which the
#  witness file strips, so that module does elaborate; but its post-image is
#  then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
#  ``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise
#  to a value a concrete-input tester can decide. Both shapes therefore land
#  ``witness-unproven``.
#  the `setsCoincideTester (some true) (some true) = false` witness exits 1 with
#  the decreasing-annotation error AND a stuck `Tactic `decide` failed`, which the
#  gate would record as `witness-unproven` — an inconclusive outcome that fails
#  the whole battery. That is the gate behaving correctly: a diverging impl
#  returns no WRONG VALUE at any concrete input, so a value-level witness has
#  nothing to refute. Disposition: REJECTED-BY-SPEC, not expressible as a
#  witnessed case. (The nagini sibling carries no diverge-* case for this
#  instance, so there is no per-case port owed either way.)
#
# AUDIT PROBES beyond the shipped cases (real builds; none is a shipped case, all
# are recorded so the coverage claims below rest on measurement, not assertion).
#
#  SPEC-TOO-WEAK probes — five NEW wrong impls aimed at what the shipped rivals
#  leave unattacked. ALL FIVE were REJECTED, so no spec hole was found:
#    - eem with the dominance order BACKWARDS (any unknown membership outranks a
#      definite-absent). The shipped battery attacks this class only on
#      setsCoincide, never on the LIST fold, so it was the largest gap.  REJECTED.
#    - eem treating an unknown membership as definitely-present.               REJECTED.
#    - eem dropping the first element of the fold (off-by-one/partial domain).  REJECTED.
#    - gs returning a CONSTANT in the non-expression arm instead of the
#      relation token (ignores `r` while keeping the guard's shape).           REJECTED.
#    - sc with `some false` and `none` SWAPPED on the way out of the fold.     REJECTED.
#
#  SPEC-TOO-STRONG probes — four NEW correct reshapes. All four are provable, so
#  the spec pins VALUE and not code shape:
#    - eem as `List.foldr tand2 (some true)`: verifies once the tactic body is
#      retuned to an induction on the list (a `loom_solve`-only body leaves the
#      `foldr = triAll` goal open — a tactic-tuning fact, NOT the spec rejecting
#      the reshape, which is why the retuned build is the one that counts).
#    - sc as an explicit four-way dominance ladder: verifies with the case split
#      retuned (same accounting as above).
#    - gs as a `match` on the flag instead of if-then-else: verifies on the frozen
#      tactic body unchanged.
#    - sc returning `triAll [subAB, subBA]` (the post-image itself): verifies on
#      the frozen tactic body unchanged.
#
# WITNESS DISCRIMINATION (verified during authoring with real builds, re-checked
# by the gate per reject case): each witness ELABORATES against its loop-free
# rival and FAILS against its subject BY A REAL `decide` REFUTATION — the subject
# build's error reads "Tactic `decide` proved that the proposition … is false",
# which is the evidence that the kernel actually evaluated the claim. The four
# everyElementMember cases are refuted against `_LOOPFREE` via
# `witness_reference`, because the frozen loop elaborates through
# `Classical.choice` and `decide` against it is STUCK for every claim, carrying
# no information (`witness-undecided`); the setsCoincide and guardedSimplify
# cases are refuted against the frozen solution directly, and were observed to
# fail there by refutation. Every witness is at literal inputs and binds nothing,
# so the gate's consistency probe is vacuous. No
# `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# BINDER / CLAUSE COVERAGE (the gate does NOT check this; pbt_coverage.py does).
#  Three obligations, each DEFENDED (>=1 positive) and ATTACKED (>=1 reject):
#   * everyElementMember (`out = triAll memberships`): attacked by
#     weak-eem-ignore-none (at [some true]), weak-eem-const-true (false-dominance,
#     at [some false]), weak-eem-const-false (the fold's IDENTITY, at []),
#     weak-eem-length-only (content-vs-length, at [some true, some true]).
#     `memberships` moved across four distinct lists spanning lengths 0, 1 and 2
#     and both definite element verdicts. The two constant rivals are near-misses
#     of each other on the empty input, so each carries its own witness at the
#     point that separates it.
#   * setsCoincide (`out = triAll [subAB, subBA]`): attacked at SIX distinct
#     points — (some true, some true), (none, some true), (some true, some false),
#     (none, some false), (some false, some true), (some true, none). BOTH binders
#     now range over ALL THREE carrier values: `subAB` over {some true, none,
#     some false} and `subBA` over {some true, some false, none} — the last of
#     those added by weak-sc-forward-only, which is the only witness giving
#     `subBA` the unknown value. So no binder is held fixed and none is confined
#     to the definite values, and THREE structural properties of the fold are each
#     attacked by a dedicated near-miss rival at a point that separates it: the
#     dominance ORDER (false beats unknown), the COMBINATION (both required, not
#     either), and the SECOND OPERAND being consulted at all.
#   * guardedSimplify (two implication clauses): BOTH are now attacked —
#     `bothExpr = false → out = r` by weak-gs-always-normal at
#     (false, r=3, normal=7), and `bothExpr = true → out = normal` by
#     weak-gs-inverted-guard at (true, r=5, normal=2). So all THREE binders are
#     varied: `bothExpr` over both values, `r` over {3,5}, `normal` over {7,2} —
#     and the two token values are ordered oppositely between the witnesses
#     (normal>r in the first, normal<r in the second), so no rival can match the
#     spec at both points by returning a constant or by comparing the tokens.
#     (An earlier revision used (false,0,1) and (true,0,1), which left `r` pinned
#     to 0 and `normal` to 1 — pbt_coverage.py flagged exactly that, and the
#     witnesses were moved rather than the finding waived.) This also closes the
#     clause-coverage gap the previous revision recorded as intentional: the
#     always-return-unchanged rival IS a false rival (measured to resolve), but
#     inverting the guard's polarity attacks the same clause and is both
#     refutable and F2P-red.
#   Twelve distinct reject input points -- one per shipped rival, no two rivals
#   refuted at the same point. No unattacked binder and no unattacked
#   top-level clause.
#
# AXIOM_TESTS: dropped. The nagini axiom lane probes the deep model (`triAll`
#  against the library's three-valued conjunction) and the two unchanged
#  reference callees that supply this bundle's inputs; that is G-AX's job, and
#  this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
