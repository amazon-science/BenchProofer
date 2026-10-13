"""properties.py — G-PBT falsification battery for sympy__sympy-16450 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct makeSurrogates``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against the second subject — here the
``witness_reference``, a loop-free VERIFYING impl of the same frozen spec, because
the frozen impl's loop makes its own exit code independent of what is claimed; see
the CARRIER NOTE).

DEFENDED SURFACE (one contracted method):

  makeSurrogates (symbols : List Sym) return (out : List (List (String × Bool)))
    ensures out = surrogatesAll symbols

  ``surrogatesAll`` is a front-recursive spec fold: one per-element property set
  per symbol, in input order, each produced by the per-symbol ``surrogate``.
  ``surrogate`` branches on the symbol's sign-determinacy:

    * sign undetermined (``none``)  — the surrogate's property set is the closure
      of "the positivity fact TOGETHER WITH the symbol's already-declared
      properties" (``closeProps (("positive", true) :: s.props)``): positivity is
      asserted WITHOUT discarding what was already known.
    * sign determined (``some _``)  — the symbol is left as-is, keeping its own
      properties (``s.props``).

  The single ``ensures`` pins ``out`` to ``surrogatesAll symbols`` on the WHOLE
  domain, so it binds three things jointly: the OUTER structure (one property set
  per symbol, in order), WHICH branch fires on which sign, and the exact argument
  handed to the closure on the undetermined branch (the positivity fact prepended
  to the declared properties, none dropped, none fabricated). The failing test
  (issue 16438) asserts the closed property set of a sign-undetermined,
  finiteness-declared symbol's surrogate by EXACT whole-set equality — every
  declared fact preserved AND positivity added — which this clause binds.

CARRIER NOTE — why this port looks like sympy-23534, not the django exemplar.

  The closure engine is an OPAQUE axiom (``closeProps : List (String × Bool) →
  List (String × Bool)``), so ``surrogatesAll`` is ``noncomputable``. Two
  consequences drive every design choice below:

   1. The ``extract_program_for`` / ``derive_tester_for`` + ``decide`` witness
      route is UNAVAILABLE: extraction cannot compile a program whose
      postcondition depends on a noncomputable term. So each reject ``witness``
      refutes the method's Hoare triple DIRECTLY at a concrete input — ``¬ triple
      True (makeSurrogates …) (fun out => out = surrogatesAll …)`` — reduced
      through ``triple_pure`` for the straight-line rivals, checked in a file
      whose ``prove_correct`` block has been stripped so no tactic script
      interferes.

      CONSEQUENCE, and it decides the second subject of every reject case: the
      FROZEN impl is a ``while`` loop, so its triple is a ``forIn Lean.Loop.mk``
      program term that ``triple_pure`` does not apply to. Against the frozen
      solution every witness of this shape therefore fails the same way — the
      ``simp only [triple_pure, …]`` is reported UNUSED, ``hEq`` survives as the
      raw loop term, and the script dead-ends at ``⊢ False`` — REGARDLESS of what
      the witness claims. Measured (see ``witness_reference`` below): the same
      witness built against a deliberately WRONG loop-keeping impl produces a
      byte-identical error block apart from the impl term it embeds, and a
      type-revealing probe (``exact (hEq : Nat)``) shows ``hEq``'s real type is
      the unreduced program on the frozen impl versus ``True`` on a loop-free
      one. So the frozen solution cannot serve as the discriminating subject
      here: its exit code carries no information about the claim. Each reject
      case names a ``witness_reference`` instead — a loop-free impl of the SAME
      frozen spec that the gate independently checks VERIFIES — against which the
      refutation reduces completely and then genuinely fails.
   2. What is DISCRIMINABLE is narrowed by the opacity. We do not need to know
      what ``closeProps`` COMPUTES to refute a rival that hands it the WRONG
      ARGUMENT: it is enough to ASSUME the two closure results differ (the value
      rivals below each carry one such hypothesis, whose satisfiability the gate
      independently checks). What is refutable WITHOUT any assumption is the OUTER
      structure (the list length / one-set-per-symbol shape) and WHICH branch of
      ``surrogate`` fired.

ADVERSARIAL READ of the weakness classes (others justified-N/A in `assessment`):
  * FRAME-MUTATION — VACUOUS. The nagini sibling's mandatory frame-mutation rival
    writes to a read-only input held at a fractional heap permission (it plants a
    fact into the source symbol's declared properties before handing it to the
    engine). This backend is referentially transparent: every parameter is an
    immutable value, this bundle declares no `mut` binder on an input, there is no
    heap and no aliasing. No read-only input to overwrite, no permission system to
    trip. Not fabricated (per the porting map, dropped rather than replaced).
  * WRONG-ARGUMENT / value — APPLIES, conditioned on the carrier. The nagini
    headline rivals feed the closure the wrong argument (empty base = positivity
    ALONE; the declared properties WITHOUT positivity; the engine output EXTENDED
    with a fabricated fact). Each ports as a rival handing `closeProps` a
    different argument, refuted at a concrete input under one hypothesis that the
    two closure results differ. The argument is attacked in BOTH directions:
    shrunk (the two ported rivals) and ENLARGED with an undeclared input fact.
    The enlarged case is the one no output-side check can reach — its result is a
    genuine closure of a genuine fact set — so it is what makes "the exact
    argument is pinned" a tested claim rather than an asserted one.
  * PARTIAL-DOMAIN / structure — APPLIES against the OUTER shape and the branch
    selector. A rival that produces the wrong NUMBER of property sets (or bypasses
    the closure entirely) refutes the clause via list length with NO hypothesis;
    a rival that fires the wrong `surrogate` branch (positivizing a symbol whose
    sign is already determined) refutes it on the sign=`some` sub-domain nagini
    never modeled (its carrier only ever held sign-undetermined inputs). Because
    `sign : Option Bool` has THREE inhabitants, the pass-through branch is
    attacked at BOTH of its values: a rival that drops the guard is caught at
    `some true`, but a rival whose guard tests POSITIVITY (`sign = some true`)
    instead of DETERMINACY agrees with the spec everywhere except `some false`,
    so that third point is required to discriminate it at all.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. The clause is grounded in
    `surrogatesAll` (a fold over the actual input `symbols`), not an opaque
    answer-key; the only way to satisfy it is to build each surrogate through the
    correct branch with the correct argument, which the positive control does.
  * ADMISSIBILITY — APPLIES, re-expressed for a total carrier (case
    `S-admiss-declared-fact-preserved`). There is no `require` clause, so there is
    no precondition LITERAL to be too strong — but that is not the same as the
    lane being vacuous, and treating it as vacuous is what silently drops one of
    the three directions this gate tests. On a total carrier the analogue is the
    obligation being unsatisfiable, or satisfiable only degenerately, at exactly
    an F2P-shaped input. The case tests that directly: it discharges the spec
    fold at the one-symbol, sign-undetermined, finiteness-declared input BY
    EVALUATION as a `have`, showing it equals the closure of the positivity fact
    together with the declared fact, and only then closes the frozen obligation
    verbatim. A fold that was degenerate at that point would fail this case while
    every uniqueness rival still passed.
  * DIVERGENCE / non-termination — SHIPPABLE-BUT-UNWITNESSABLE, recorded as a
    known hole rather than as a vacuous class. This bundle sets
    `loom.semantics.termination "total"`, so a diverging rival IS genuinely
    rejected and the class is not vacuous: measured, an impl whose loop body never
    decreases `i` fails (exit 1, `unsolved goals` on the decreasing obligation),
    and one that drops the `decreasing` clause fails with `Decreasing annotations
    are required in total correctness semantics`. What could not be landed is the
    WITNESS such a case needs on this backend. A diverging rival keeps the loop, so
    its triple keeps the `forIn Lean.Loop.mk` term that blocks every reduction
    route the value witnesses use, and it cannot be refuted against the loop-free
    `witness_reference` either — the rejection there is a termination obligation,
    not a violation of `out = surrogatesAll symbols` at any input, so there is no
    concrete-input claim to state. Five witness routes were tried against a
    diverging rival (the `triple_pure` route, `simp [triple, wp]`, unfolding
    `liftM`/`monadLift`, `simp_all` on the fold lemmas, and `absurd … (by
    loom_solve)`); all failed, and the positive triple is not provable about the
    diverging impl either. So the case would be a rejection the witness mechanism
    cannot attribute, which is exactly what this gate refuses to count. Stated as
    a hole in what the battery can attest, not as a property of the spec.

WITNESS PLACEMENT / coverage. The lone binder `symbols` is varied across SEVEN
distinct input points (pts=7): a two-element list (structural), and six
one-element lists whose sole symbol ranges over declared property `finite`,
`integer`, `prime`, `rational` and the EMPTY property set, and over ALL THREE
values of `sign` (`none` for the undetermined-branch rivals, `some true` and
`some false` for the two determined-branch rivals). Rivals share no witness:
each fails for a distinct reason at a distinct point (empty list-length; the
closure argument shrunk, or enlarged, on the undetermined branch; the wrong
branch taken on each of the two determined sub-domains). The value rivals each
condition on ONE hypothesis (two closure results differ), whose satisfiability
the gate confirms by failing to derive `False` from it. The admissibility case
re-uses the sign-undetermined/finiteness-declared point, deliberately: that is
the F2P-shaped input, and the question it asks there (is the obligation
satisfiable?) is the opposite of the rivals' (is a wrong impl refutable?).

EVIDENCE THAT THE RIVAL HALF IS INFORMATIVE, not just the reference half. For
each value/branch rival an AGREEMENT-POINT forgery was built: the same statement
shape and the same tactic script, with the input moved to a point where that
rival AGREES with the frozen spec (e.g. the empty-property input for the rival
that closes from positivity alone, a sign-determined input for the rival that
omits positivity, a sign-undetermined input for the guard-dropping rival, and
`some true` for the rival that guards on positivity). All six FAIL against their
own rival, so the rival-side exit 0 tracks the input the witness names and is not
an artifact of the script. Combined with the reference-side failures, each reject
case's two exit codes both carry information about the claim.

Covering all three `sign` values is load-bearing, not decorative: a rival whose
guard is `s.sign = some true` rather than `s.sign = none` agrees with the spec at
`none` AND at `some true`, so it is discriminated ONLY at `some false`
(`S-branch-on-positive-not-determined`). Likewise the argument to the closure is
attacked in BOTH directions — shrunk (`S-drop-declared-props`,
`S-forget-positive`) and enlarged (`S-fabricate-declared-fact`) — because an
enlarged argument still yields a REAL closure of a REAL fact set, so no property
of the OUTPUT can distinguish it; only pinning the argument itself can.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16450"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The whole loop-based impl body (text strictly between -- impl-start and
# -- impl-end). Replaced wholesale by the structure/value-attacking rivals,
# which abandon the loop for a single `symbols.map`.
_IMPL = (
    "    let mut result : List (List (String × Bool)) := []\n"
    "    let mut i := symbols.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ symbols.length\n"
    "      invariant result = surrogatesAll (symbols.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let s := symbols[i - 1]!\n"
    "      result := surrogate s :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The two loop-body lines that bind `s` then prepend its surrogate. The positive
# control inlines `s` into the prepend — a data-flow reshape that keeps the
# accumulated result definitionally identical, so the frozen tactic script still
# closes.
_INNER = (
    "      let s := symbols[i - 1]!\n"
    "      result := surrogate s :: result\n"
)

# The frozen proof body (tactic script only; elided from the spec view). The
# structure/value rivals reshape the impl into a single `map` expression, so
# there is no loop invariant to peel: they retune the proof to a bare
# `loom_solve` (which then FAILS for them — the point, attributed by the
# witness, not by a stale tactic script tuned to a loop that no longer exists).
_PROOF = (
    "prove_correct makeSurrogates by\n"
    "  loom_solve\n"
    "  rw [surrogatesAll_drop_step symbols i (by omega) (by omega)]\n"
    "  simp_all\n"
)
_PROOF_FLAT = "prove_correct makeSurrogates by\n  loom_solve\n"

assert _BASE.count(_IMPL) == 1, "impl anchor drift — re-sync _IMPL"
assert _BASE.count(_INNER) == 1, "inner anchor drift — re-sync _INNER"
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"


def _map_rival(map_body):
    """A full Solution.lean whose impl is a single `symbols.map (…)` and whose
    proof is the flat `loom_solve` (which fails for the rival — the rejection is
    then attributed by the witness). Edits ONLY the impl and proof regions."""
    return _swap(_swap(_BASE, _IMPL, map_body), _PROOF, _PROOF_FLAT)


# ---- witness_reference: the second subject every reject case is refuted
# ---- against, in place of the frozen solution.
#
# WHY IT IS NEEDED (measured, not argued). The frozen impl is a `while` loop, so
# `makeSurrogates`'s triple elaborates to a `forIn Lean.Loop.mk` program term and
# `triple_pure` — which rewrites only `pure` — does not apply. Every witness of
# this shape therefore fails against the frozen solution for a SHAPE reason: the
# `simp only [triple_pure, …]` is reported unused, `hEq` stays the raw loop term,
# and the refutation dead-ends at `⊢ False` no matter what it claims. Three builds
# establish that the frozen exit code is uninformative rather than a refutation:
#
#   * the same witness against a deliberately WRONG loop-keeping impl (the frozen
#     loop, closing from the positivity fact alone) fails with an error block
#     BYTE-IDENTICAL to the frozen one except for the impl term it embeds;
#   * a type-revealing variant (`exact (hEq : Nat)` as the final step) prints
#     `hEq`'s real type: the unreduced `{True}do let r ← forIn Lean.Loop.mk …`
#     against the frozen impl, versus `True` against this reference (i.e. `simp`
#     PROVED the equation there) and a concrete list equation against a rival;
#   * asserting the TRUE claim at the same input by the same route also fails
#     against the frozen impl, so both directions of the claim collapse to one
#     exit code.
#
# WHY THIS REFERENCE IS ADMISSIBLE. It is a loop-free impl of the SAME frozen
# spec, so the triple reduces through `triple_pure` and the refutation is actually
# evaluated. The gate does not take that on trust: it re-checks that the reference
# shares the frozen spec and that it VERIFIES before refuting anything against it,
# and an impl the verifier accepts cannot violate its own spec — so a genuine
# refutation must still fail there, while a forged one is caught. Its proof is a
# real induction over `symbols` (no new lemma, no changed statement), which is
# also the SPEC-TOO-STRONG evidence the positive control's defeq-trivial reshape
# cannot supply on its own.
_REFERENCE = _swap(
    _swap(_BASE, _IMPL, "    return symbols.map surrogate\n"),
    _PROOF,
    "prove_correct makeSurrogates by\n"
    "  loom_solve\n"
    "  induction symbols with\n"
    "  | nil => rfl\n"
    "  | cons s ss ih => simp [surrogatesAll_cons, ih]\n")


# ---- witness helper. The postcondition is noncomputable, so a witness refutes
# ---- the method's Hoare triple directly at a concrete input, checked in a file
# ---- whose `prove_correct` block has been stripped. `preamble` optionally
# ---- declares the example's head binder (a hypothesis that two closure results
# ---- differ, for the value rivals); `refute` is the tactic body.
def _witness(preamble, symbols_lit, refute):
    return (
        f"example {preamble}:\n"
        f"    ¬ (triple (l := Prop) True\n"
        f"    (makeSurrogates {symbols_lit})\n"
        f"    (fun out => out = surrogatesAll {symbols_lit})) := by\n"
        f"  unfold makeSurrogates\n"
        f"  simp only [triple_pure, le_Prop_eq, true_implies]\n"
        f"{refute}"
    )


# The value-rival refutation body: peel the single-element fold, unfold
# `surrogate` to expose the closure argument, and reduce the goal to the
# hypothesis `h` that the two closure results differ.
_VALUE_REFUTE = (
    "  intro hEq\n"
    "  rw [surrogatesAll_cons, surrogatesAll_nil] at hEq\n"
    "  simp only [surrogate, List.map] at hEq\n"
    "  apply h\n"
    "  simp_all\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG. The intermediate
    # `let s := symbols[i-1]!` binding is inlined into the prepend: the
    # accumulated `result` is DEFINITIONALLY identical, so `loom_solve` leaves
    # the same single loop-body goal and the frozen tactic script
    # (`rw [surrogatesAll_drop_step …]; simp_all`) discharges it unchanged. No new
    # lemma is introduced and the obligation statement is byte-identical.
    # (Verified during authoring: verifies, exit 0.)
    # =====================================================================
    {
        "id": "S-pos-inline-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INNER,
            "      result := surrogate symbols[i - 1]! :: result\n"),
        "rationale": "Inlining the per-symbol binding into the surrogate prepend "
                     "leaves the accumulated `result` definitionally identical, "
                     "so `out = surrogatesAll symbols` still holds on the whole "
                     "domain and the frozen proof closes without change. A correct "
                     "reshape that failed to verify would mean the spec is "
                     "SPEC-TOO-STRONG on the impl's data-flow shape.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) #2 — a NON-defeq correct reshape. The
    # inline-binding positive above is definitionally identical to the frozen
    # impl, so it re-runs the frozen tactic script and tests SPEC-TOO-STRONG
    # only against a data-flow relabelling. This one abandons the backward loop
    # for `symbols.map surrogate` and discharges the obligation by a real
    # induction over `symbols`: a genuinely different program shape and a
    # genuinely different proof, with the obligation statement byte-identical
    # and no new lemma. It is also the `witness_reference` every reject case
    # below is refuted against, so the battery's positive lane and its
    # discrimination lane rest on the same machine-checked impl.
    # =====================================================================
    {
        "id": "S-pos-map-induction",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": "`symbols.map surrogate` computes the same per-symbol "
                     "property sets in the same order as the frozen backward "
                     "loop, but is NOT definitionally equal to it: the frozen "
                     "loop's `drop`-indexed invariant is replaced by an "
                     "induction on `symbols`, so `loom_solve` leaves a different "
                     "goal and the frozen tactic script does not apply. It "
                     "verifies, which is the SPEC-TOO-STRONG evidence a "
                     "defeq-trivial reshape cannot give: the spec pins the "
                     "per-symbol RESULT, not the loop shape that produced it. A "
                     "correct reshape this far from the frozen form being "
                     "rejected would mean the clause was over-fitted to the "
                     "frozen impl's control flow.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at an F2P-shaped input.
    # The method carries no `require`, so there is no precondition literal to be
    # too strong; on a total carrier the analogue of PRECOND-TOO-STRONG is the
    # obligation being unsatisfiable at exactly the input the failing scenario
    # exercises. This case discharges that obligation at that concrete input BY
    # EVALUATION, as a `have` proven before the frozen obligation is closed
    # verbatim: the sign-undetermined, finiteness-declared one-symbol input must
    # have `surrogatesAll` equal to the closure of the positivity fact TOGETHER
    # WITH the declared finiteness fact. If the spec fold were degenerate at
    # that point (branching the other way, or dropping the declared fact) the
    # `have` would not close and this case would fail while every rival above
    # still passed — which is precisely the direction the other lanes cannot see.
    # =====================================================================
    {
        "id": "S-admiss-declared-fact-preserved",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct makeSurrogates by\n"
            "  have hadm : surrogatesAll "
            "[{ props := [(\"finite\", true)], sign := none }]\n"
            "      = [closeProps [(\"positive\", true), (\"finite\", true)]] := by\n"
            "    simp [surrogatesAll_cons, surrogatesAll_nil, surrogate]\n"
            "  loom_solve\n"
            "  rw [surrogatesAll_drop_step symbols i (by omega) (by omega)]\n"
            "  simp_all\n"),
        "rationale": "PRECOND-TOO-STRONG has no literal analogue (no `require` "
                     "clause), so the admissible-input question on this total "
                     "carrier is whether the obligation is SATISFIABLE at an "
                     "F2P-shaped input. The `have` evaluates the spec fold at the "
                     "one-symbol, sign-undetermined, finiteness-declared input the "
                     "failing scenario uses and shows it equals the closure of the "
                     "positivity fact together with the declared fact — i.e. the "
                     "spec demands exactly the behaviour the scenario asserts, at "
                     "that point, and demands something achievable. The frozen "
                     "obligation is then closed verbatim by the frozen script, so "
                     "the case adds an evaluated sub-domain claim without weakening "
                     "anything. A degenerate fold at that input (wrong branch, or "
                     "the declared fact dropped) would fail here while leaving "
                     "every uniqueness rival passing.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete
    # input and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================

    # ---- STRUCTURAL: produce ZERO property sets, bypassing the fold and the
    # ---- closure entirely (the on-carrier analogue of the nagini "hand-built
    # ---- object that ducks the engine"). Refuted via the list LENGTH with NO
    # ---- hypothesis. Uses a two-element input, isolating the group-count
    # ---- clause at a distinct point from the value rivals.
    {
        "id": "S-empty-structure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival("    return []\n"),
        "refinement": "Returning no property sets at all bypasses the closure "
                      "engine entirely and has no gold counterpart (the fix "
                      "produces exactly one surrogate property set per free "
                      "symbol). A faithful real patch that emitted nothing could "
                      "not reproduce the documented surrogate for the "
                      "sign-undetermined symbol the failing scenario "
                      "deconstructs, so its assertion would error. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: for a "
                     "two-element input `surrogatesAll` has length 2 while the "
                     "rival returns length 0. Verifying would be SPEC-TOO-WEAK on "
                     "the outer structure. Refuted with NO hypothesis at a "
                     "two-element input (one sign-undetermined + one "
                     "sign-determined symbol) via the list length.",
        "witness": _witness(
            "",
            "[{ props := [(\"finite\", true)], sign := none }, "
            "{ props := [], sign := some true }]",
            "  intro hEq\n"
            "  rw [surrogatesAll_cons, surrogatesAll_cons, surrogatesAll_nil] "
            "at hEq\n"
            "  simp at hEq\n"),
        "witness_reference": _REFERENCE,
    },

    # ---- WRONG ARGUMENT (the prepatch bug): on the sign-undetermined branch,
    # ---- close from the positivity fact ALONE, discarding the symbol's declared
    # ---- properties. This is the pre-patch construction — the surrogate built
    # ---- from positivity only. Refuted under the hypothesis that the two
    # ---- closures differ, at a finiteness-declared symbol.
    {
        "id": "S-drop-declared-props",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival(
            "    return symbols.map (fun s => if s.sign = none then "
            "closeProps [(\"positive\", true)] else s.props)\n"),
        "refinement": "Closing from positivity alone drops the symbol's declared "
                      "properties — exactly the pre-patch construction. For a "
                      "sign-undetermined, finiteness-declared symbol the surrogate "
                      "then lacks the finiteness fact, so the failing scenario "
                      "(issue 16438), which pins the surrogate's property set by "
                      "exact whole-set equality including that declared fact, "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: on the "
                     "sign-undetermined branch the spec closes from `(\"positive\", "
                     "true) :: s.props` while the rival closes from `[(\"positive\", "
                     "true)]`, dropping the declared properties. Verifying would "
                     "leave the argument to the closure unpinned (SPEC-TOO-WEAK). "
                     "Refuted at a one-element `[finite]/none` input under the "
                     "hypothesis that the two closures differ.",
        "witness": _witness(
            "(h : closeProps [(\"positive\", true)]\n"
            "          ≠ closeProps [(\"positive\", true), (\"finite\", true)]) ",
            "[{ props := [(\"finite\", true)], sign := none }]",
            _VALUE_REFUTE),
        "witness_reference": _REFERENCE,
    },

    # ---- WRONG ARGUMENT (positivity forgotten): on the sign-undetermined
    # ---- branch, carry the declared properties but FORGET the positivity fact.
    # ---- The nagini "wrong flag" rival. Refuted under the hypothesis that the
    # ---- two closures differ, at an integer-declared symbol (a distinct point).
    {
        "id": "S-forget-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival(
            "    return symbols.map (fun s => if s.sign = none then "
            "closeProps s.props else s.props)\n"),
        "refinement": "Carrying the declared properties but omitting the "
                      "positivity fact leaves the surrogate's sign undecided — the "
                      "whole point of the transformation is the POSITIVE "
                      "surrogate. A real patch that closed from the symbol's "
                      "declared property set alone, "
                      "without adding positivity, would make the surrogate's "
                      "positivity None, so the failing scenario (which pins "
                      "`positive: True` in the surrogate's property set) fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: on the "
                     "sign-undetermined branch the spec closes from `(\"positive\", "
                     "true) :: s.props` while the rival closes from `s.props`, "
                     "omitting positivity. Verifying would leave the positivity "
                     "contribution unpinned (SPEC-TOO-WEAK). Refuted at a distinct "
                     "one-element `[integer]/none` input under the hypothesis that "
                     "the two closures differ.",
        "witness": _witness(
            "(h : closeProps [(\"integer\", true)]\n"
            "          ≠ closeProps [(\"positive\", true), (\"integer\", true)]) ",
            "[{ props := [(\"integer\", true)], sign := none }]",
            _VALUE_REFUTE),
        "witness_reference": _REFERENCE,
    },

    # ---- WRONG ARGUMENT (spurious key): take the correct closure, then EXTEND
    # ---- it with a fact the engine never produced (the nagini atk-12 regression
    # ---- that motivated the whole-set strengthening). Refuted under the
    # ---- hypothesis that the extended list differs from the closure, at a
    # ---- prime-declared symbol (a distinct point).
    {
        "id": "S-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival(
            "    return symbols.map (fun s => if s.sign = none then "
            "closeProps ((\"positive\", true) :: s.props) ++ [(\"z\", true)] "
            "else s.props)\n"),
        "refinement": "Appending a fact the closure never derived makes the "
                      "surrogate's property set differ from the real closed set, "
                      "so the failing scenario — which pins the surrogate's "
                      "property set by EXACT whole-set equality — sees an extra "
                      "key and fails; a fabricated fact may also be inconsistent "
                      "with the real closure. A real patch that added a key to the "
                      "closure output would NOT resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: the spec's "
                     "surrogate is exactly `closeProps ((\"positive\", true) :: "
                     "s.props)` while the rival appends `(\"z\", true)`. Verifying "
                     "would admit a fabricated derived fact (the too-weak-spec "
                     "regression). Refuted at a distinct one-element `[prime]/none` "
                     "input under the hypothesis that the extended list differs "
                     "from the closure.",
        "witness": _witness(
            "(h : closeProps [(\"positive\", true), (\"prime\", true)] ++ "
            "[(\"z\", true)]\n"
            "          ≠ closeProps [(\"positive\", true), (\"prime\", true)]) ",
            "[{ props := [(\"prime\", true)], sign := none }]",
            _VALUE_REFUTE),
        "witness_reference": _REFERENCE,
    },

    # ---- WRONG BRANCH (sign guard dropped): positivize EVERY symbol, ignoring
    # ---- the sign-determinacy guard, so a symbol whose sign is already
    # ---- determined is wrongly replaced. This attacks the sign=`some`
    # ---- sub-domain the nagini carrier never modeled (its inputs were always
    # ---- sign-undetermined). Refuted under the hypothesis that the closure
    # ---- differs from the untouched properties, at a sign-DETERMINED symbol.
    {
        "id": "S-ignore-sign-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival(
            "    return symbols.map (fun s => "
            "closeProps ((\"positive\", true) :: s.props))\n"),
        "refinement": "Dropping the sign-determinacy guard replaces symbols whose "
                      "sign is ALREADY determined, overwriting their properties "
                      "with a positive-closed set. A real patch that removed the "
                      "sign-undetermined filter would positivize symbols the "
                      "surrounding transformation must leave untouched, changing "
                      "already-determined symbols' assumptions and breaking the "
                      "existing (PASS_TO_PASS) behaviour. It would NOT resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: on the "
                     "sign-DETERMINED branch the spec keeps `s.props` while the "
                     "rival returns `closeProps ((\"positive\", true) :: s.props)`. "
                     "Verifying would leave the branch selector unpinned "
                     "(SPEC-TOO-WEAK on which sign fires which branch). Refuted at "
                     "a one-element `[integer]/some true` input — the "
                     "sign-determined sub-domain no other rival probes — under the "
                     "hypothesis that the closure differs from the untouched "
                     "properties.",
        "witness": _witness(
            "(h : closeProps [(\"positive\", true), (\"integer\", true)]\n"
            "          ≠ [(\"integer\", true)]) ",
            "[{ props := [(\"integer\", true)], sign := some true }]",
            _VALUE_REFUTE),
        "witness_reference": _REFERENCE,
    },

    # ---- WRONG ARGUMENT (fabricated INPUT fact): hand the closure a fact the
    # ---- symbol never declared. The existing spurious-key rival fabricates on
    # ---- the OUTPUT side (appending to the engine's result); this one
    # ---- fabricates on the INPUT side, so the returned list IS a genuine
    # ---- closure — just of the wrong argument. Nothing downstream of the
    # ---- opaque engine can spot it, which is exactly why the clause has to pin
    # ---- the argument. Refuted at a symbol with NO declared properties (a
    # ---- distinct input point, and the one where "the argument was enlarged"
    # ---- is the only possible discrepancy).
    {
        "id": "S-fabricate-declared-fact",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival(
            "    return symbols.map (fun s => if s.sign = none then "
            "closeProps ((\"positive\", true) :: (\"finite\", true) :: s.props) "
            "else s.props)\n"),
        "refinement": "Injecting a property the symbol never declared makes the "
                      "surrogate claim a fact about a quantity that was never "
                      "asserted to have it. For a sign-undetermined symbol with no "
                      "declared properties the surrogate then carries an extra "
                      "fact, so the failing scenario — which pins the surrogate's "
                      "property set by EXACT whole-set equality — sees a set it "
                      "did not expect and fails; asserting an unfounded property "
                      "may also contradict the symbol's real constraints. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: the spec hands "
                     "the closure exactly `(\"positive\", true) :: s.props` while "
                     "the rival enlarges the argument with a fact the symbol never "
                     "declared. Verifying would leave the argument pinned only up "
                     "to 'contains positivity and the declared properties', "
                     "admitting arbitrary extra input facts (SPEC-TOO-WEAK). Note "
                     "this rival's output is a REAL closure, so no output-side "
                     "check can catch it — only pinning the argument does. Refuted "
                     "at a one-element `[]/none` input (no declared properties — a "
                     "point no other rival uses) under the hypothesis that the "
                     "enlarged-argument closure differs from the correct one.",
        "witness": _witness(
            "(h : closeProps [(\"positive\", true), (\"finite\", true)]\n"
            "          ≠ closeProps [(\"positive\", true)]) ",
            "[{ props := [], sign := none }]",
            _VALUE_REFUTE),
        "witness_reference": _REFERENCE,
    },

    # ---- WRONG BRANCH (determinacy confused with positivity): branch on
    # ---- `sign = some true` instead of on sign-DETERMINACY, so a symbol whose
    # ---- sign is determined NEGATIVE is wrongly positivized. S-ignore-sign-
    # ---- branch drops the guard entirely; this rival keeps a guard but tests
    # ---- the wrong predicate, which is the likelier real mistake and survives
    # ---- every input the other rivals use (it agrees with the spec on
    # ---- `none` and on `some true`). Refuted at `sign := some false`.
    {
        "id": "S-branch-on-positive-not-determined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _map_rival(
            "    return symbols.map (fun s => if s.sign = some true then s.props "
            "else closeProps ((\"positive\", true) :: s.props))\n"),
        "refinement": "Testing 'is the sign positive' instead of 'is the sign "
                      "determined' positivizes a symbol whose sign is already "
                      "determined to be non-positive — a quantity the surrounding "
                      "transformation must leave alone. A real patch that filtered "
                      "on positivity rather than on sign-determinacy would rewrite "
                      "already-determined symbols and assert positivity of a "
                      "quantity known not to be positive, changing established "
                      "behaviour (PASS_TO_PASS). It would NOT resolve.",
        "rationale": "REJECT from `out = surrogatesAll symbols`: the spec's guard "
                     "is sign-DETERMINACY (`s.sign = none`), so both `some true` "
                     "and `some false` take the pass-through branch; this rival "
                     "positivizes `some false`. Verifying would pin the branch "
                     "selector only on the two sign values the other rivals probe "
                     "(`none`, `some true`) and leave the third free "
                     "(SPEC-TOO-WEAK). Refuted at a one-element "
                     "`[rational]/some false` input — the third sign value, which "
                     "no other case exercises — under the hypothesis that the "
                     "closure differs from the untouched properties.",
        "witness": _witness(
            "(h : closeProps [(\"positive\", true), (\"rational\", true)]\n"
            "          ≠ [(\"rational\", true)]) ",
            "[{ props := [(\"rational\", true)], sign := some false }]",
            _VALUE_REFUTE),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 3 uniqueness rivals) plus 2
# AXIOM_TESTS. This bundle models only the purely-functional core — a single
# method `makeSurrogates` whose closure engine is an OPAQUE axiom `closeProps` —
# with a single `ensures` clause and a single input binder `symbols`. Every
# sibling case is accounted for below.
#
#   sibling case                 -> here
#   -------------------------------------------------------------------------
#   pos-control-local-base       -> S-pos-inline-binding        PORTED
#                                +  S-pos-map-induction        ADDED (audit a2:
#                                                                non-defeq reshape)
#   admiss-finite-base           -> S-admiss-declared-fact-     RE-EXPRESSED
#                                     preserved                  (audit a2)
#   frame-mutate-stated          -> (none)                      VACUOUS
#   prepatch-empty-base          -> S-drop-declared-props       PORTED
#   wrong-flag-no-positive       -> S-forget-positive           PORTED
#   atk12-spurious-key           -> S-spurious-key              PORTED
#   fresh-dict-not-engine-map    -> S-empty-structure           RE-EXPRESSED
#   (no sibling: this carrier's  -> S-ignore-sign-branch        ADDED (branch
#    explicit sign branch)                                       coverage)
#   (no sibling: input-side      -> S-fabricate-declared-fact   ADDED (audit a1:
#    argument fabrication)                                        closure-argument
#                                                                 coverage)
#   (no sibling: third sign      -> S-branch-on-positive-       ADDED (audit a1:
#    value `some false`)             not-determined               branch-predicate
#                                                                 coverage)
#   ax-sound-resolve/ax-contain  -> (none)                      DROPPED (G-AX lane)
#
# 4 ported, 2 re-expressed, 4 added, 3 dropped (1 vacuous, 2 axiom-lane).
# No case was dropped because its proof was hard.
#
# ADDED BY AUDIT (independent adversarial re-derivation of this port). Two gaps
#   the original five rivals left, each closed by a rival built and checked with
#   the real verifier (rival build exit 0 for the witness, gold build exit 1,
#   consistency probe exit 1 = hypotheses satisfiable):
#   * S-fabricate-declared-fact — every original value rival either shrank the
#     closure argument (S-drop-declared-props, S-forget-positive) or corrupted the
#     engine's OUTPUT (S-spurious-key). None ENLARGED the argument, so nothing
#     pinned the argument against extra INPUT facts. That gap mattered because
#     such a rival's output is a genuine closure of a genuine fact set: no
#     output-side property distinguishes it, only the argument identity does.
#   * S-branch-on-positive-not-determined — `s.sign : Option Bool` has THREE
#     values and the original battery probed two (`none`, `some true`). A rival
#     branching on `s.sign = some true` agrees with the spec at both of those and
#     differs only at `some false`, so the whole battery was blind to it while the
#     manifest claimed the branch selector was pinned.
#
# VACUOUS (frame-mutate-stated): the sibling writes to a read-only input held at
#   a fractional heap permission (planting a fact into the source symbol's
#   declared properties). This backend is referentially transparent: every
#   parameter is an immutable value, no `mut` input binder, no heap, no aliasing.
#   No read-only input to overwrite, no permission system to trip. No substitute
#   fabricated (per the porting map, dropped rather than replaced).
# RE-EXPRESSED (admiss-finite-base -> S-admiss-declared-fact-preserved): the
#   method carries NO `require` clause, so the sibling's literal "a normal input
#   satisfies the precondition" probe has no counterpart. That is NOT a reason to
#   drop the lane — doing so removes the only detector of PRECOND-TOO-STRONG. The
#   analogue on a total carrier is the obligation being unsatisfiable, or
#   satisfiable only degenerately, at an F2P-shaped input, which the re-expressed
#   case tests by discharging the spec fold at that concrete input by EVALUATION
#   (as a `have`) before closing the frozen obligation verbatim. The sibling's
#   input is preserved exactly: one symbol, sign undetermined, finiteness
#   declared.
# RE-EXPRESSED (S-empty-structure): the sibling's fresh-dict rival hand-builds an
#   assumptions dict that ducks the inference engine. On this carrier the
#   discriminable analogue that requires NO hypothesis is bypassing the closure
#   AND the fold entirely — returning zero property sets — refuted via the outer
#   list length. (A hand-built non-empty set would require a closure hypothesis
#   just like the value rivals; the empty-structure form isolates the outer
#   clause at a two-element point instead.)
# ADDED (S-ignore-sign-branch): nagini's carrier only ever held sign-undetermined
#   symbols (`stated` was always a symbol the transformation replaces, i.e. one
#   whose sign is undetermined), so
#   it had no case for the sign-DETERMINED branch. This bundle models the sign
#   guard explicitly (`surrogate` branches on `s.sign`), so the pass-through
#   branch is part of the defended surface and is attacked by a rival that
#   positivizes a sign-determined symbol.
# DROPPED (ax-sound-resolve, ax-contain-resolve): the sibling's two AXIOM_TESTS
#   probe the `resolve`/`derived` oracle's soundness and containment against the
#   real engine. Here the closure is the opaque axiom `closeProps`, validated by
#   axiom_check.py (G-AX); the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single clause `out = surrogatesAll symbols` is
#   attacked by all seven rivals along three axes:
#     - OUTER STRUCTURE: S-empty-structure (via list length, NO hypothesis).
#     - CLOSURE ARGUMENT on the sign-undetermined branch, in BOTH directions —
#       shrunk: S-drop-declared-props (positivity alone), S-forget-positive
#       (declared properties alone); enlarged: S-fabricate-declared-fact (an
#       undeclared input fact); and corrupted on the OUTPUT side: S-spurious-key
#       (engine output + fabricated fact).
#     - BRANCH SELECTOR on the sign-determined sub-domain: S-ignore-sign-branch
#       (guard dropped, caught at `some true`) and
#       S-branch-on-positive-not-determined (guard tests positivity instead of
#       determinacy, caught ONLY at `some false`).
#   The lone binder `symbols` is varied across SEVEN distinct input points
#   (pts=7): a two-element list and six one-element lists whose symbol ranges over
#   declared `finite`/`integer`/`prime`/`rational` and the EMPTY property set, and
#   over ALL THREE values of `sign` (`none`, `some true`, `some false`). Both
#   branches of `surrogate` are exercised, and the pass-through branch is probed at
#   both of its sign values. Each value rival conditions on ONE satisfiable
#   hypothesis (the two closure results differ), never two about the same term. No
#   two rivals share a witness. The clause is defended by S-pos-inline-binding.
#
# WHY THE WITNESSES DISCRIMINATE ON CORRECTNESS, NOT ON SHAPE — and why the
#   second subject is the `witness_reference` and NOT the frozen solution.
#
#   Every rival here abandons the frozen loop for a `symbols.map`, so the fair
#   question is whether each witness fails against its second subject because that
#   subject is CORRECT, or merely because it is loop-shaped (the triple not
#   reducing through `triple_pure`). Against the FROZEN solution it is the latter,
#   and that is measured rather than suspected:
#
#     * the witness against the frozen solution leaves `hEq` as the raw
#       `forIn Lean.Loop.mk` term with the `triple_pure` simp argument reported
#       UNUSED, dead-ending at `⊢ False`;
#     * the SAME witness against a deliberately WRONG loop-keeping impl (the frozen
#       loop, closing from the positivity fact alone) fails with an error block
#       byte-identical except for the impl term it embeds — so that exit code is
#       what a wrong impl of the frozen shape also produces;
#     * a type-revealing final step (`exact (hEq : Nat)`) prints `hEq`'s real type:
#       the unreduced `{True}do let r ← forIn Lean.Loop.mk …` against the frozen
#       impl, `True` against the loop-free reference (`simp` PROVED the equation
#       there), and a concrete list equation against a rival;
#     * asserting the TRUE claim at the same input by the same route ALSO fails
#       against the frozen impl, so both directions of the claim collapse onto one
#       exit code.
#
#   None of the gate's stuck-reduction screens matches this arrival (there is no
#   "did not reduce", no missing `Decidable`, and only half of the
#   loop-unification pair), so nothing mechanical would have caught it.
#
#   What the witnesses DO discriminate is checked against the `witness_reference`,
#   a loop-free impl of the same frozen spec that the gate independently verifies.
#   All seven witnesses fail against it (exit 1) with the refutation FULLY REDUCED
#   to a semantic dead end — `hEq : True ⊢ False` for the structural rival, and
#   `h : ¬closeProps … = closeProps … ⊢ False` for the value and branch rivals:
#   the claim is evaluated, found not to hold of a correct impl, and the remaining
#   goal is unprovable precisely because the reference does not violate the clause.
#   So the witnesses key on the closure argument and the branch taken, on a subject
#   whose exit code responds to what is claimed.
#
# MODELING-FIDELITY OBSERVATION for the spec owners (NOT a spec hole, and not
#   actionable in this lane). The clause pins the closure ARGUMENT up to LIST
#   identity: `closeProps (("positive", true) :: s.props)`. mapping.md §2 records
#   that the repo side is a dict and that key order is irrelevant — both sides
#   treat it as the SET of facts. So an impl that builds the same fact set in the
#   other order (`s.props ++ [("positive", true)]`) is faithful under that
#   bijection, yet the spec rejects it: built and measured, exit 1, with the
#   residual goal `closeProps (s.props ++ [("positive", true)]) = closeProps
#   (("positive", true) :: s.props)`. That equation is not provable here and should
#   not be — `closeProps` is uninterpreted, so nothing licenses permuting its
#   argument (checked: the equation fails under simp/simp_all/rfl/decide/grind).
#   With an opaque callee, list identity is the only pinning that can be STATED, so
#   this is a limit of the abstraction rather than a weakness in the clause; every
#   wrong impl probed is still rejected and every correct impl in the frozen
#   argument order is still accepted. Relaxing it would need a
#   permutation-respecting property of the closure, i.e. a SPEC change that must
#   re-clear the equivalence and leakage gates outside this lane. Recorded here so
#   it is not re-derived.
#
# AXIOM_TESTS: empty. The opaque `closeProps` is validated by G-AX
#   (axiom_check.py); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
