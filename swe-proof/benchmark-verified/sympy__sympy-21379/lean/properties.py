"""PBT manifest for sympy__sympy-21379 (lean) — adversarial falsification battery.

NOT a Lean file; a record of adversarial cases the G-PBT runner executes and
stamps with RESULT. Every case is a full `Solution.lean` variant that shares the
FROZEN spec byte-for-byte (region surgery: only the text strictly inside the
`-- impl-start` / `-- impl-end` region and, where the reshaped implementation
needs reproving, the `-- proof-start` / `-- proof-end` body is edited), so
`markers.same_spec` holds by construction and every verdict is attributable to
`problem_spec_factorReduce` rather than to a tampered spec. The
`theorem correct_factorReduce` STATEMENT is byte-identical in every case; no
variant introduces an axiom, a helper lemma, `sorry`, `admit`, or
`native_decide`.

Ported from the nagini sibling's battery (`../nagini/properties.py`), which is
the design document for the adversarial reasoning below. The nagini carrier
contracts the step over an integer operand-shape `code` with an explicit
precondition and an exception facet; this bundle models the same step over an
abstract expression carrier with a total signature, so each nagini rival is
re-expressed against THIS carrier and given a refutation witness (new work —
nagini's rejections rest on Viper discharging the contract itself, an inference
that is invalid on a tactic-proof backend).

DEFENDED SURFACE
================

ONE modeled obligation:

  implementation_factorReduce (p q : Expr) : Except Unit (Expr × Expr × Expr)
    Precondition: NONE. `correct_factorReduce : ∀ (p q : Expr), …` binds the
    total carrier, so no precondition can be too strong in the literal sense —
    the admissibility lane is still exercised, as satisfiability of the
    obligation at an F2P-shaped input (see `admiss-tolerated-failure-point`).
    Postcondition `problem_spec_factorReduce p q result`, a case split on the
    helper routine's outcome, with three independent top-level obligations:

      (clause OK-unit)  extractFactor p q = ok g  and  g = one  ->
          result = ok (g, p, q)                    — both expressions kept as-is
      (clause OK-rewr)  extractFactor p q = ok g  and  g ≠ one  ->
          result = ok (g, reduceByFactor p g, reduceByFactor q g)
                                                   — EACH expression rewritten,
                                                     each with ITS OWN argument
      (clause ERR)      extractFactor p q = error () ->
          result = ok (one, p, q)                  — the failure is TOLERATED:
                                                     the unit is recorded, both
                                                     expressions kept, and the
                                                     step still yields `ok`

    LOAD-BEARING content, matching the nagini sibling's two load-bearing
    clauses: (a) clause ERR, and specifically that its right-hand side is an
    `ok` and never an `error ()` — this is the discriminating content of the
    desired behavior (a failure of the helper routine must be tolerated rather
    than propagated), and it is the clause the prepatch violates; (b) clause
    OK-rewr, which pins each of the two result expressions to the OPAQUE
    per-expression rewrite of the CORRESPONDING input, so an implementation that
    skips the rewrite, applies it to only one expression, or crosses the two
    arguments cannot discharge it. Clause OK-unit additionally pins the
    complementary sub-domain, so an implementation cannot buy clause OK-rewr by
    rewriting unconditionally.

    Note the carrier's ONLY transparent structure is the `Except`/tuple shape
    and the `g = one` test; `extractFactor`, `reduceByFactor` and `one` are all
    `opaque`, so `decide` computes nothing here. Every reject witness therefore
    CONDITIONS on the carrier (see below) rather than computing over it.

INPUT FRAME
===========

`p` and `q` are values of an immutable Lean `structure`; Lean is referentially
transparent, so there is no aliasing, no fractional read-only permission, and no
frame or permission obligation to violate. The nagini sibling's
frame/permission-mutation probe class is therefore VACUOUS on this carrier, not
merely untested (see "omitted classes"). What that probe defends structurally —
that the operand values reach the result untouched on the paths that require it
— IS attacked here, as a postcondition matter: `rewrite-unconditionally`,
`rewrite-on-tolerated-path` and `record-input-as-factor` each put something
other than the pinned input value into a result component.

ORACLE GROUNDING
================

There is no answer-key literal an implementation could echo: `extractFactor`,
`reduceByFactor` and `one` are opaque with NO constraining axiom, so the spec
pins the result only by how the opaque results are COMBINED — which routing
fires on which outcome, which expression each rewrite is applied to, and which
component of the triple each value lands in. That combination is exactly what
the rivals below attack, and it is refutable without knowing any opaque value:
each witness assumes only enough about the carrier to SEPARATE the rival from
the frozen solution (one hypothesis naming the helper's outcome at a concrete
input, plus, where the rival's error is a dropped or misdirected rewrite, one
hypothesis saying that rewrite actually changes something). Those hypotheses are
about distinct terms and are jointly satisfiable — the gate's inconsistency
probe fails on every one of them, as it must.

WITNESS POINTS
==============

Eight distinct reject-witness points, chosen so no binder is held fixed across
the battery and so every clause is attacked, plus a ninth point carrying the
admissibility positive:

  clause ERR      : ("u","v")  ("j","k")  ("z","y")   [+ ("pw","zz"), admiss]
  clause OK-rewr  : ("d","e")  ("m","n")  ("s","t")  ("w","x")
  clause OK-unit  : ("a","b")

`p` and `q` take a different value at every point, and the pair is asymmetric
everywhere (`("z","y")` deliberately reverses the alphabetical order the other
points follow), so a rival that mishandled only one of the two coordinates — or
only their order — cannot hide.

WITNESS SHAPE — and why it is stated directly rather than via a `have`
=====================================================================

Every reject witness here states its refutation DIRECTLY over the unfolded
implementation: `unfold`, `rw [he]` to select the clause, then
`dsimp only [Id.run, pure, Id.instMonad]` to reduce the `do` block to a bare
equation between two triples, then one `simp` that decides THAT equation.

An earlier revision of this manifest instead routed every witness through an
intermediate `have himpl : implementation_factorReduce … = <the rival's triple>`
and closed the goal with `rw [he, himpl]`. That shape passed the gate and was
HOLLOW, and the reason is worth recording because it is invisible to the gate:
the `have` asserts the RIVAL's return value, so against the frozen solution the
build dies inside the `have` — on `rfl`, proving a triple the frozen impl never
produces — strictly BEFORE the refutation claim is ever reached. Measured on all
eight cases: the gold-side error was byte-identical between the real witness and
a FORGERY differing only in dropping the `¬` (i.e. asserting the frozen solution
is CORRECT there, the opposite of a refutation). Seven of the eight printed the
identical `Tactic 'rfl' failed: The left-hand side (have G := one; …` for both
claims. So gold's exit code carried NO information about the claim, and a
witness asserting gold is correct would have been recorded as a refutation just
the same.

The direct shape fixes exactly that: the failure now lands on the claim itself.
Against the frozen solution `simp` PROVES the pinned equation, so the negation is
left unprovable and the goal reported is `⊢ False`; flipping the claim makes the
same file BUILD (exit 0 on gold). That flip is the evidence that the gold-side
exit code tracks the claim rather than the shape of a scaffolding step, and it is
why no witness here introduces an intermediate `have`.

OMITTED NAGINI CASES (all four are carrier narrowing or vacuity, none is a
dropped-because-hard case)
=========================================================================

  * `admiss-incode-range` (admissibility) is PORTED, not omitted, as
    `admiss-tolerated-failure-point`. Nagini's precondition is `0 <= code <= 2`
    and that case confirms a normal caller can establish it.
    `correct_factorReduce` binds `∀ (p q : Expr)` with NO hypothesis, so there
    is indeed no precondition to be too strong — but that does NOT make the
    class vacuous, and an earlier revision of this manifest wrongly recorded it
    so and shipped 0 admissibility cases. The analogue on a total carrier is
    the obligation being unsatisfiable at exactly an F2P-shaped input, which a
    positive that discharges the obligation at that concrete input — by
    evaluation, as a `have`, before closing the frozen obligation verbatim —
    tests directly. See the first case in SPEC_TESTS; it is machine-checked and
    demonstrated non-vacuous.
  * The frame / permission-mutation probe. Vacuous — see "INPUT FRAME".
  * `diverge-before-return` (non-termination). This bundle sets NO
    `set_option loom.semantics.termination`: it is the plain Lean/Mathlib
    carrier, where a `def` must be shown terminating, so the "partial"
    vacuous-verification hole does not arise here. The disposition is a KNOWN
    HOLE in the reject lane rather than a vacuous class, and the earlier claim
    that "a diverging implementation cannot be written at all" is too strong —
    measured, a plainly recursive `def implementation_factorReduce p q :=
    implementation_factorReduce p q` is refused (`fail to show termination`),
    but an unbounded `while true do` inside the frozen `Id.run do` shape DOES
    elaborate, and the frozen obligation then fails on it, so it is rejected.
    It is not shipped as a reject case because it cannot be given a
    DISCRIMINATING witness on this carrier: the loop elaborates to an
    unreduced `forIn Lean.Loop.mk` term, and a witness against it fails with
    `⊢ ¬(forIn Lean.Loop.mk one fun x r => ForInStep.yield one) = one` — a
    stuck reduction, which the gate's own `_STUCK_REDUCTION` screen exists to
    refuse as evidence. Shipping it would attest to a tactic gap, not to the
    spec. Recorded as a hole, not as vacuity.
  * `AXIOM_TESTS`. Out of scope for this gate; the axiom lane is G-AX's job, and
    this bundle's G-AX is a recorded skip (the callees enter fully abstract with
    no consumed property).

Nagini's `unguarded-raise-escapes` (the prepatch shape) ports as
`propagate-failure`; `drop-operand-regroup` as `keep-both-expressions`;
`drop-one-operand-transform` as `rewrite-first-only`; `operand-overwrite-on-
refusal` as `rewrite-on-tolerated-path`; `wrong-factor-on-refusal` as
`record-input-as-factor`; `hardcode-trivial-always` / `fabricate-literal-factor`
(nagini's two opacity cheats, which fabricate a literal in place of the opaque
factor) as `record-unit-as-factor` — a literal cannot be written for this
carrier's opaque `Expr`, so the same cheat is expressed as substituting the one
named carrier value, `one`, for the helper's actual output. Two rivals have no
nagini counterpart and are added because this carrier exposes structure nagini's
integer `code` did not: `rewrite-unconditionally` attacks the complementary
sub-domain of the `g = one` guard, and `cross-rewrite-arguments` attacks the
per-expression PAIRING of rewrite argument to rewrite subject.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21379"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. `_GOLD_IMPL` is the executable body of the SINGLE impl region
# (strictly inside `-- impl-start` / `-- impl-end`); `_GOLD_PROOF` is the tactic
# body of the SINGLE proof region (strictly inside `-- proof-start` /
# `-- proof-end`, below the `theorem correct_factorReduce` statement, which no
# case touches). Editing only these two blocks keeps the spec view byte-identical
# and the obligation intact. Both are asserted unique by `_swap`, so the manifest
# breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """  let mut G : Expr := one
  let mut p' := p
  let mut q' := q
  match extractFactor p q with
  | Except.ok g =>
      G := g
      if g ≠ one then
        p' := reduceByFactor p g
        q' := reduceByFactor q g
  | Except.error () =>
      G := one
  return Except.ok (G, p', q')"""

_GOLD_PROOF = """  intro p q
  unfold problem_spec_factorReduce implementation_factorReduce
  cases h : extractFactor p q with
  | ok g =>
      by_cases hg : g = one
      · simp only [Id.run, hg, ne_eq, not_true_eq_false, if_false, if_true]
        rfl
      · simp only [Id.run, hg, ne_eq, if_false]
        rfl
  | error e =>
      cases e
      rfl"""

# The whole declaration head + body, for the one positive that leaves the
# imperative `Id.run do` shape entirely.
_GOLD_DECL = ("def implementation_factorReduce (p q : Expr) :\n"
              "    Except Unit (Expr × Expr × Expr) := Id.run do\n")


def _impl(body):
    """A variant differing from the frozen solution ONLY in the impl region."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """A variant that reshapes the impl and REPROVES the same obligation."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


def _prepend_proof(extra):
    """The frozen impl, with `extra` tactics run BEFORE the frozen proof body.

    For the admissibility positive: the impl region is untouched (the frozen
    implementation is the subject), and the frozen tactic script is left
    byte-identical and still closes the obligation — `extra` only adds a `have`
    ahead of it. So the case cannot pass by weakening anything; it passes only
    if the added obligation-at-a-concrete-input is genuinely dischargeable.
    """
    return _swap(_BASE, _GOLD_PROOF, extra + _GOLD_PROOF)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped input ----
    # `correct_factorReduce` binds `∀ (p q : Expr)` with no hypothesis, so there
    # is no precondition an admissibility case could show a caller establishes.
    # The analogue on a TOTAL carrier is the one this case tests: that the
    # obligation is not unsatisfiable at exactly the input shape the F2P
    # exercises. The discriminating input here is the one where the helper
    # routine signals it cannot produce a factor — clause ERR's sub-domain, the
    # load-bearing clause — and PRECOND-TOO-STRONG on this carrier would show up
    # as clause ERR being impossible to discharge there while the frozen
    # obligation still closes vacuously for some other reason.
    #
    # So the case discharges `problem_spec_factorReduce` AT that concrete point,
    # by evaluation, as a `have`, BEFORE closing the frozen obligation verbatim.
    # The impl region is untouched and the frozen tactic body is byte-identical
    # and still closes the theorem; the `have`s are pure addition.
    #
    # Each `have` pins the CONCRETE answer on its right-hand side rather than
    # naming `implementation_factorReduce`'s own output. That distinction is
    # load-bearing and is the failure mode this lane has been audited for
    # elsewhere in the corpus: a `have` of the form
    # `problem_spec_f <lit> (implementation_f <lit>)` is the frozen theorem
    # specialized at one input, so it is a weaker RESTATEMENT of an obligation
    # the frozen script already closes everywhere and it never forces the spec
    # to be evaluated. Pinning `Except.ok (one, p, q)` makes the case fail if
    # the spec pins anything else there.
    #
    # Demonstrated non-vacuous by three measured negative probes: replacing the
    # pinned answer with `Except.error ()` (the failure escaping), with the first
    # input expression recorded as the factor, or with the two expressions
    # swapped, each FAILS to close. MUST verify; rejection is
    # PRECOND-TOO-STRONG.
    {
        "id": "admiss-tolerated-failure-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _prepend_proof(
            "  have hadm_err : extractFactor { repr := \"pw\" }"
            " { repr := \"zz\" } = Except.error () →\n"
            "      problem_spec_factorReduce { repr := \"pw\" } { repr := \"zz\" }\n"
            "        (Except.ok (one, { repr := \"pw\" }, { repr := \"zz\" }))"
            " := by\n"
            "    intro hfail\n"
            "    unfold problem_spec_factorReduce\n"
            "    rw [hfail]\n"
            "  have hadm_unit : extractFactor { repr := \"pw\" }"
            " { repr := \"zz\" } = Except.ok one →\n"
            "      problem_spec_factorReduce { repr := \"pw\" } { repr := \"zz\" }\n"
            "        (Except.ok (one, { repr := \"pw\" }, { repr := \"zz\" }))"
            " := by\n"
            "    intro hok\n"
            "    unfold problem_spec_factorReduce\n"
            "    rw [hok]\n"
            "    simp\n"),
        "rationale": "the total-carrier analogue of nagini's "
                     "`admiss-incode-range`. There is no precondition to "
                     "establish, so what this positive tests is that the "
                     "obligation is SATISFIABLE at an F2P-shaped input rather "
                     "than unsatisfiable there. Two ground instances at one "
                     "concrete pair, each pinned to the LITERAL answer the spec "
                     "gives (not to the implementation's own output, which "
                     "would only restate the frozen theorem at one input): "
                     "clause ERR, the load-bearing sub-domain where the helper "
                     "routine signals failure, and clause OK-unit, its "
                     "complement where the helper succeeds with the unit. Both "
                     "pin `ok (one, p, q)`. The frozen obligation is then closed "
                     "with its tactic body byte-identical. Demonstrated "
                     "non-vacuous: pinning `Except.error ()`, the input "
                     "expression as the factor, or the two expressions swapped "
                     "each fails to close. Rejection here is "
                     "PRECOND-TOO-STRONG.",
    },

    # -- SOUNDNESS POSITIVE 1: leave the imperative shape entirely -------------
    # The frozen implementation threads three mutable locals through a `match`
    # and returns once at the end. This positive is the same behavior as a pure
    # functional definition: no `Id.run do`, no `let mut`, each arm of the match
    # returning its triple directly, and the guard written positively (`if g =
    # one then … else …`) rather than as the negated `if g ≠ one`. That is a
    # genuinely different structure, not a renaming — so the frozen tactic script
    # does NOT close it and the obligation is REPROVEN below (the statement of
    # `theorem correct_factorReduce` is byte-identical; only the tactic body
    # differs). It discharges all three clauses, so it MUST verify; if it does
    # not, the spec is too strong for a correct implementation.
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_DECL + _GOLD_IMPL,
                  "def implementation_factorReduce (p q : Expr) :\n"
                  "    Except Unit (Expr × Expr × Expr) :=\n"
                  "  match extractFactor p q with\n"
                  "  | Except.ok g =>\n"
                  "      if g = one then Except.ok (g, p, q)\n"
                  "      else Except.ok (g, reduceByFactor p g, reduceByFactor q g)\n"
                  "  | Except.error () => Except.ok (one, p, q)"),
            _GOLD_PROOF,
            "  intro p q\n"
            "  unfold problem_spec_factorReduce implementation_factorReduce\n"
            "  cases h : extractFactor p q with\n"
            "  | ok g =>\n"
            "      by_cases hg : g = one\n"
            "      · simp [hg]\n"
            "      · simp [hg]\n"
            "  | error e =>\n"
            "      cases e\n"
            "      rfl"),
        "rationale": "a structurally different but behaviourally identical "
                     "implementation — pure functional pattern match instead of "
                     "mutable locals, positive guard instead of negated, one "
                     "expression per arm instead of a shared tail return. It "
                     "produces the pinned triple on all three sub-domains "
                     "(helper succeeds with the unit, succeeds with a "
                     "non-unit, fails), so all three clauses of "
                     "problem_spec_factorReduce are discharged and it must "
                     "verify. The obligation statement is unchanged and the "
                     "proof is genuinely re-closed for the new shape (no new "
                     "lemma, no assumption); if this is rejected the spec is "
                     "SPEC-TOO-STRONG.",
    },

    # -- SOUNDNESS POSITIVE 2: make both branches of the guard explicit --------
    # Keeps the imperative shape but restates the guard so that BOTH arms assign
    # the result expressions, including the arm where they are assigned back to
    # their own input values, and likewise re-assigns them on the tolerated-
    # failure path. Every assignment is a no-op except the two rewrites, so the
    # behavior is identical — but the redundant assignments change the `do`
    # elaboration enough that the frozen script no longer closes it, so the
    # obligation is REPROVEN. MUST verify.
    {
        "id": "pos-explicit-both-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "  let mut G : Expr := one\n"
            "  let mut pr := p\n"
            "  let mut qr := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      if g = one then\n"
            "        pr := p\n"
            "        qr := q\n"
            "      else\n"
            "        pr := reduceByFactor p g\n"
            "        qr := reduceByFactor q g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "      pr := p\n"
            "      qr := q\n"
            "  return Except.ok (G, pr, qr)",
            "  intro p q\n"
            "  unfold problem_spec_factorReduce implementation_factorReduce\n"
            "  cases h : extractFactor p q with\n"
            "  | ok g =>\n"
            "      by_cases hg : g = one\n"
            "      · simp only [Id.run, hg, if_true]\n"
            "        rfl\n"
            "      · simp only [Id.run, hg, if_false]\n"
            "        rfl\n"
            "  | error e =>\n"
            "      cases e\n"
            "      rfl"),
        "rationale": "the same computation with the guard's positive branch and "
                     "the tolerated-failure path written out as explicit "
                     "(no-op) assignments of each expression to its own input "
                     "value, and the locals renamed. Behaviourally identical on "
                     "every sub-domain, so it discharges the same three clauses "
                     "and must verify; the obligation statement is untouched "
                     "and the proof is re-closed honestly for the reshaped "
                     "`do` block. Rejection here would be SPEC-TOO-STRONG.",
    },

    # -- UNIQUENESS / propagate the failure instead of tolerating it -----------
    # The single most important rival: it is the pre-patch shape. The helper's
    # failure is not tolerated — the step yields `Except.error ()` and the
    # failure escapes. Clause ERR pins the result to `ok (one, p, q)` on exactly
    # that outcome, so this is refutable at any input where the helper fails.
    # MUST be REJECTED; if it verifies the spec cannot see the behavior the
    # issue reports, i.e. SPEC-TOO-WEAK.
    {
        "id": "propagate-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      if g ≠ one then\n"
            "        p' := reduceByFactor p g\n"
            "        q' := reduceByFactor q g\n"
            "  | Except.error () =>\n"
            "      return Except.error ()\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "this is the behavior BEFORE the change: the helper "
                      "routine's inability to produce a result is not "
                      "absorbed, so it propagates out of the simplification "
                      "step and out of the enclosing query. That is precisely "
                      "the observable the F2P test pins — the reported failure "
                      "surfacing out of an ordinary substitution — so the "
                      "faithful real counterpart of this rival is the "
                      "unmodified code and it does NOT resolve.",
        "rationale": "refuted by clause ERR: on the outcome where the helper "
                     "signals failure the spec demands `ok (one, p, q)` (an "
                     "`ok`, with the unit recorded and both expressions "
                     "unchanged) and this rival yields `error ()`, which no "
                     "`ok` equals. The witness states exactly that at a "
                     "concrete input pair, conditioning only on the helper's "
                     "outcome there — the one fact needed to reach the clause. "
                     "SPEC-TOO-WEAK if it verifies.",
        "witness": """-- Conditioned on the carrier, not computed: `extractFactor` is opaque, so no
-- literal input decides which clause applies. The single hypothesis names the
-- helper's outcome at one concrete pair; it constrains nothing else, so it is
-- trivially satisfiable (the gate's inconsistency probe cannot derive False).
--
-- The refutation is stated DIRECTLY over the unfolded implementation: the `do`
-- block is reduced by `dsimp only [Id.run, pure, Id.instMonad]` so the goal
-- becomes a bare equation between the two triples, and the closing `simp` then
-- decides THAT equation. No intermediate `have` restates the rival's result, so
-- the tactic's success or failure tracks the CLAIM rather than the shape of an
-- auxiliary step -- which is what makes the gold-side exit code evidence: on the
-- frozen solution `simp` proves the equation and the `¬` is left unprovable
-- (`⊢ False`), while the flipped claim BUILDS there.
example (he : extractFactor { repr := "u" } { repr := "v" } = Except.error ()) :
    ¬ problem_spec_factorReduce { repr := "u" } { repr := "v" }
        (implementation_factorReduce { repr := "u" } { repr := "v" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp""",
    },

    # -- UNIQUENESS / skip the rewrite entirely (the partial-domain rival) -----
    # Record the factor correctly and tolerate the failure correctly, but never
    # rewrite: both expressions always reach the result as their input values.
    # Clause OK-rewr demands the opaque per-expression rewrite on the non-unit
    # sub-domain, so the rival is refutable wherever that rewrite actually
    # changes the first expression. MUST be REJECTED.
    {
        "id": "keep-both-expressions",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart records the extracted "
                      "factor but never divides it out of either expression. "
                      "The F2P test carries a pre-existing assertion that a "
                      "modulo of two expressions sharing a non-unit factor "
                      "simplifies to that factor times the modulo of the "
                      "REDUCED pair; without the rewrite the pair stays "
                      "unreduced and that assertion fails, so it does NOT "
                      "resolve.",
        "rationale": "refuted by clause OK-rewr, second and third components: "
                     "the spec pins them to `reduceByFactor p g` / "
                     "`reduceByFactor q g` and the rival supplies `p` / `q`. "
                     "Since `reduceByFactor` is opaque, `p = reduceByFactor p "
                     "g` is not a theorem — so the witness assumes the rewrite "
                     "is non-trivial at its input, which is exactly the "
                     "sub-domain where this rival is wrong. SPEC-TOO-WEAK if it "
                     "verifies.",
        "witness": """-- Three hypotheses about three DISTINCT terms: the helper's outcome at this
-- pair, that the extracted factor is not the unit (so clause OK-rewr is the
-- applicable one), and that the rewrite of the first expression by that factor
-- actually changes it. Nothing forces any of the three to conflict, so they are
-- jointly satisfiable. The last is the assumption that makes the refutation
-- meaningful rather than universal: a rewrite that changed nothing would leave
-- this rival correct, and the witness claims only the sub-domain where it is not.
--
-- Stated directly over the unfolded implementation (no restating `have`), so the
-- gold-side failure is `simp` PROVING the pinned equation and leaving `⊢ False`,
-- not a tactic mismatch on an auxiliary step.
example (g : Expr) (hg : g ≠ one)
    (he : extractFactor { repr := "d" } { repr := "e" } = Except.ok g)
    (hr : reduceByFactor { repr := "d" } g ≠ { repr := "d" }) :
    ¬ problem_spec_factorReduce { repr := "d" } { repr := "e" }
        (implementation_factorReduce { repr := "d" } { repr := "e" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [hg, Ne.symm hr]""",
    },

    # -- UNIQUENESS / rewrite only the first expression (asymmetric) -----------
    # A NEAR-MISS of the rival above: it agrees with the frozen solution on the
    # first expression and diverges only on the second, so it is given its own
    # witness at its own input, conditioned on the rewrite of the SECOND
    # expression being non-trivial. Without that separate point the manifest
    # would claim a sub-domain it never demonstrated. MUST be REJECTED.
    {
        "id": "rewrite-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      if g ≠ one then\n"
            "        p' := reduceByFactor p g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart rewrites only the first of "
                      "the two expressions, leaving the second unreduced. The "
                      "F2P assertion on a modulo whose two expressions share a "
                      "non-unit factor pins the reduced form of BOTH, so a "
                      "half-reduced result is a different expression and it "
                      "does NOT resolve.",
        "rationale": "refuted by clause OK-rewr, THIRD component only: the "
                     "second expression must be `reduceByFactor q g` and the "
                     "rival leaves it as `q`. This is the coordinate the "
                     "`keep-both-expressions` rival gets wrong too, but this "
                     "one is correct on the first coordinate, so its witness "
                     "sits at a different input and conditions on the SECOND "
                     "expression's rewrite being non-trivial — otherwise the "
                     "claimed sub-domain would be undemonstrated. "
                     "SPEC-TOO-WEAK if it verifies.",
        "witness": """-- Same shape as the previous witness but the non-triviality hypothesis is about
-- the SECOND expression's rewrite, the only coordinate on which this rival
-- departs from the spec. Distinct input point, distinct discriminating fact.
-- All three hypotheses concern different terms and are jointly satisfiable.
--
-- Stated directly over the unfolded implementation, so the gold-side failure is
-- a decided equation (`⊢ False`) rather than a shape mismatch.
example (g : Expr) (hg : g ≠ one)
    (he : extractFactor { repr := "m" } { repr := "n" } = Except.ok g)
    (hr : reduceByFactor { repr := "n" } g ≠ { repr := "n" }) :
    ¬ problem_spec_factorReduce { repr := "m" } { repr := "n" }
        (implementation_factorReduce { repr := "m" } { repr := "n" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [hg, Ne.symm hr]""",
    },

    # -- UNIQUENESS / cross the two rewrite arguments --------------------------
    # No nagini counterpart: nagini's operands are separate integer parameters
    # whose transforms are pinned individually, but this carrier makes the
    # PAIRING of rewrite-subject to result-component attackable on its own. Both
    # rewrites happen, with the right factor, exactly on the right sub-domain —
    # they are just applied to the wrong expressions, so the two results are
    # swapped. This is the rival that a battery attacking only "is the rewrite
    # present?" would miss entirely. MUST be REJECTED.
    {
        "id": "cross-rewrite-arguments",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      if g ≠ one then\n"
            "        p' := reduceByFactor q g\n"
            "        q' := reduceByFactor p g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart applies the per-expression "
                      "rewrite across the pair, so the reduced first expression "
                      "lands where the reduced second belongs and vice versa. "
                      "The F2P assertion pins a specific reduced pair, and a "
                      "modulo is not symmetric in its two expressions, so the "
                      "swapped result is a different expression and it does NOT "
                      "resolve.",
        "rationale": "refuted by clause OK-rewr as a PAIRING constraint: the "
                     "spec pins the second component to the rewrite of `p` and "
                     "the third to the rewrite of `q`, and this rival exchanges "
                     "them. `reduceByFactor` is opaque and not assumed "
                     "injective, so the refutation is stated where the two "
                     "rewrites differ from each other — the sub-domain in which "
                     "the swap is observable at all. SPEC-TOO-WEAK if it "
                     "verifies.",
        "witness": """-- The discriminating fact is not about either rewrite's value but about the two
-- rewrites DIFFERING from each other -- `reduceByFactor a g ≠ reduceByFactor b g`
-- is not derivable from opacity, and it is not refutable either, so assuming it
-- at one asymmetric pair is consistent (probe cannot derive False). That single
-- assumption separates the swapped triple from the pinned one.
--
-- Stated directly over the unfolded implementation, so the gold-side failure is
-- a decided equation (`⊢ False`) rather than a shape mismatch.
example (g : Expr) (hg : g ≠ one)
    (he : extractFactor { repr := "s" } { repr := "t" } = Except.ok g)
    (hr : reduceByFactor { repr := "t" } g ≠ reduceByFactor { repr := "s" } g) :
    ¬ problem_spec_factorReduce { repr := "s" } { repr := "t" }
        (implementation_factorReduce { repr := "s" } { repr := "t" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [hg, hr]""",
    },

    # -- UNIQUENESS / drop the guard: rewrite unconditionally ------------------
    # No nagini counterpart either: this attacks clause OK-UNIT, the
    # complementary sub-domain of the guard. An implementation could otherwise
    # buy every rewrite obligation by always rewriting, and the battery would
    # never notice that the spec ALSO pins the unit case to leave both
    # expressions alone. This is the only rival refuted on the `g = one`
    # sub-domain, so without it that clause is defended but never attacked.
    # MUST be REJECTED.
    {
        "id": "rewrite-unconditionally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      p' := reduceByFactor p g\n"
            "      q' := reduceByFactor q g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart drops the test that guards "
                      "the rewrite and divides both expressions by the "
                      "extracted factor even when that factor is the unit. The "
                      "rewrite is not the identity map, so it perturbs the "
                      "form of every expression pair with no shared non-unit "
                      "factor — the overwhelming majority of the inputs the "
                      "F2P test's own pre-existing assertions cover — and the "
                      "suite does NOT resolve.",
        "rationale": "refuted by clause OK-UNIT: when the extracted factor is "
                     "the unit the spec pins both expressions to their INPUT "
                     "values, and this rival substitutes their rewrites. This "
                     "is the sole rival attacking that clause and the sole "
                     "witness point on the `g = one` sub-domain, so it is what "
                     "keeps the guard's complementary branch from being an "
                     "unattacked obligation. SPEC-TOO-WEAK if it verifies.",
        "witness": """-- The point where the guard's positive branch applies: the helper succeeds and
-- returns the unit itself, so clause OK-UNIT pins both expressions unchanged.
-- Two hypotheses, two distinct terms, jointly satisfiable -- nothing prevents the
-- helper from returning the unit here while the unit-rewrite still perturbs the
-- first expression, and it is that perturbation the rival commits to unguarded.
--
-- Stated directly over the unfolded implementation, so the gold-side failure is
-- a decided equation (`⊢ False`) rather than a shape mismatch.
example (he : extractFactor { repr := "a" } { repr := "b" } = Except.ok one)
    (hr : reduceByFactor { repr := "a" } one ≠ { repr := "a" }) :
    ¬ problem_spec_factorReduce { repr := "a" } { repr := "b" }
        (implementation_factorReduce { repr := "a" } { repr := "b" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [hr]""",
    },

    # -- UNIQUENESS / rewrite on the tolerated-failure path --------------------
    # Tolerates the failure (so the result is an `ok` and the load-bearing
    # routing is honoured) but corrupts the expressions on that path: they are
    # rewritten by the unit before entering the result, where clause ERR pins
    # them to their input values. This is the closest analogue on this carrier
    # to nagini's "overwrite the read-only operand" probe — and it lands as a
    # POSTCONDITION refutation, since clause ERR pins the expressions' final
    # state, not as any permission or frame violation (there are none here).
    # MUST be REJECTED.
    {
        "id": "rewrite-on-tolerated-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      if g ≠ one then\n"
            "        p' := reduceByFactor p g\n"
            "        q' := reduceByFactor q g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "      p' := reduceByFactor p one\n"
            "      q' := reduceByFactor q one\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart absorbs the helper's "
                      "failure but then divides both expressions by the unit "
                      "before carrying them forward, instead of leaving them "
                      "untouched. On the input the issue reports, the "
                      "simplification is supposed to be left standing over the "
                      "ORIGINAL pair; a perturbed pair changes the value the "
                      "reported expression denotes, so the F2P assertion "
                      "on it does NOT resolve.",
        "rationale": "refuted by clause ERR, second and third components: on "
                     "the failure outcome the spec pins them to `p` and `q`, "
                     "and this rival supplies their rewrites. Distinct from "
                     "`propagate-failure`, which gets the routing wrong while "
                     "this one gets the routing right and the carried values "
                     "wrong — so it needs, and has, its own witness point on "
                     "the failure sub-domain. SPEC-TOO-WEAK if it verifies.",
        "witness": """-- A second, distinct point on the failure sub-domain (`propagate-failure` is
-- refuted at ("u","v"), this at ("j","k")): the two rivals fail on the same
-- clause but for different reasons, so they do not share a witness. Hypotheses
-- name the helper's outcome and the non-triviality of the unit-rewrite -- two
-- unrelated terms, jointly satisfiable.
--
-- Stated directly over the unfolded implementation, so the gold-side failure is
-- a decided equation (`⊢ False`) rather than a shape mismatch.
example (he : extractFactor { repr := "j" } { repr := "k" } = Except.error ())
    (hr : reduceByFactor { repr := "j" } one ≠ { repr := "j" }) :
    ¬ problem_spec_factorReduce { repr := "j" } { repr := "k" }
        (implementation_factorReduce { repr := "j" } { repr := "k" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [hr]""",
    },

    # -- UNIQUENESS / record the unit instead of the extracted factor ----------
    # The opacity attack, ported from nagini's two literal-fabrication rivals.
    # Nagini could substitute an integer literal for the opaque factor; this
    # carrier has no literal to substitute, so the cheat is expressed with the
    # one named carrier value — always record `one` as the factor, while still
    # performing both rewrites with the REAL extracted factor. The rewrites are
    # therefore right and only the first component is wrong, which is what makes
    # it a sharp test of whether the spec pins that component at all.
    # MUST be REJECTED.
    {
        "id": "record-unit-as-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := one\n"
            "      if g ≠ one then\n"
            "        p' := reduceByFactor p g\n"
            "        q' := reduceByFactor q g\n"
            "  | Except.error () =>\n"
            "      G := one\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart reduces both expressions "
                      "by the extracted factor but then reports the unit as "
                      "the factor that was pulled out, so the factor is "
                      "silently discarded from the result the enclosing step "
                      "builds. The F2P assertion pins the factor times the "
                      "reduced modulo; dropping the factor yields the reduced "
                      "modulo alone, a different expression, so it does NOT "
                      "resolve.",
        "rationale": "refuted by clause OK-rewr, FIRST component: the recorded "
                      "factor must be the helper's own opaque output `g`, and "
                      "`one` is not provably that — the witness supplies the "
                      "one fact that separates them (`g ≠ one`), which is also "
                      "precisely the sub-domain on which the rival is wrong. "
                      "Note that the rewrites here are correct, so no "
                      "assumption about `reduceByFactor` is needed: this is the "
                      "cheapest possible refutation and the tightest binder "
                      "set. SPEC-TOO-WEAK if it verifies.",
        "witness": """-- Only TWO hypotheses, both about `extractFactor`'s outcome at this pair and the
-- factor it yields -- no assumption about `reduceByFactor` at all, since this
-- rival performs both rewrites correctly. Satisfiable: nothing stops the helper
-- from returning some non-unit factor here.
--
-- Stated directly over the unfolded implementation, so the gold-side failure is
-- a decided equation (`⊢ False`) rather than a shape mismatch.
example (g : Expr) (hg : g ≠ one)
    (he : extractFactor { repr := "w" } { repr := "x" } = Except.ok g) :
    ¬ problem_spec_factorReduce { repr := "w" } { repr := "x" }
        (implementation_factorReduce { repr := "w" } { repr := "x" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [hg, Ne.symm hg]""",
    },

    # -- UNIQUENESS / record an input expression as the factor -----------------
    # Ported from nagini's wrong-value-on-the-refusal-path rival. The failure is
    # tolerated (routing correct, expressions carried through unchanged) but the
    # recorded factor on that path is the first input expression rather than the
    # unit. Clause ERR pins that component to `one`. This is also the battery's
    # asymmetric input point: it is the one witness whose pair reverses the
    # ordering the others follow, so a rival sensitive to the pair's order
    # cannot hide behind a uniformly-ordered battery. MUST be REJECTED.
    {
        "id": "record-input-as-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let mut G : Expr := one\n"
            "  let mut p' := p\n"
            "  let mut q' := q\n"
            "  match extractFactor p q with\n"
            "  | Except.ok g =>\n"
            "      G := g\n"
            "      if g ≠ one then\n"
            "        p' := reduceByFactor p g\n"
            "        q' := reduceByFactor q g\n"
            "  | Except.error () =>\n"
            "      G := p\n"
            "  return Except.ok (G, p', q')"),
        "refinement": "the faithful real counterpart absorbs the helper's "
                      "failure but falls back to the first expression, rather "
                      "than the unit, as the factor. The enclosing step "
                      "multiplies the recorded factor into what it builds, so "
                      "on the input the issue reports the result is scaled by "
                      "an entire expression instead of being left standing — a "
                      "different value from the one the F2P assertion pins, so "
                      "the suite does NOT resolve.",
        "rationale": "refuted by clause ERR, FIRST component: the recorded "
                     "factor on the failure outcome must be `one`, and this "
                     "rival supplies the input expression `p`. The witness "
                     "assumes only that the two are distinct at its point, "
                     "which is unavoidable given `one` is opaque — and is the "
                     "exact sub-domain of wrongness. Third distinct witness "
                     "point on the failure sub-domain, and the battery's one "
                     "reverse-ordered pair. SPEC-TOO-WEAK if it verifies.",
        "witness": """-- The pair is deliberately reverse-ordered relative to every other witness in
-- this battery, so the input points are not merely distinct but not co-monotone
-- either. Two hypotheses about two distinct terms (the opaque unit's value at
-- this concrete expression, and the helper's outcome), jointly satisfiable.
--
-- Stated directly over the unfolded implementation, so the gold-side failure is
-- a decided equation (`⊢ False`) rather than a shape mismatch.
example (ho : one ≠ { repr := "z" })
    (he : extractFactor { repr := "z" } { repr := "y" } = Except.error ()) :
    ¬ problem_spec_factorReduce { repr := "z" } { repr := "y" }
        (implementation_factorReduce { repr := "z" } { repr := "y" }) := by
  unfold problem_spec_factorReduce implementation_factorReduce
  rw [he]
  dsimp only [Id.run, pure, Id.instMonad]
  simp [Ne.symm ho, ho]""",
    },
]
