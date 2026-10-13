# properties.py — G-PBT falsification battery for sympy__sympy-19783 (lean).
#
# NOT a Lean module: a manifest of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each SPEC_TESTS entry is a FULL
# Solution.lean variant built by region surgery — it edits ONLY an impl region
# (and, where a reshaped impl needs it, the matching proof body), so the frozen
# spec (docstring / axioms / pure / post-conditions) stays byte-identical,
# same_spec holds by construction, and BOTH `theorem correct_*` STATEMENTS are
# preserved verbatim. No case introduces sorry / admit / native_decide / axiom,
# nor any new theorem or lemma beyond the frozen pair.
#
# ---------------------------------------------------------------- port note ---
# CARRIER NARROWING vs the nagini sibling. The nagini battery contracts the same
# two products over an integer kind tag 0..3 and returns a four-field `Product`
# record (is_mul, result_kind, left_kind, right_kind), with a `Requires` pinning
# the tag to the valid range. This Lean bundle models the SAME two decisions on a
# purely functional carrier: a finite `Operand` (identity / operator / conjugate /
# other) in, a finite `Result` (lhs / rhs / product) out. The record's four
# facets collapse into the single `Result` value — "did it collapse" and "which
# factor survived" are one and the same observation here — and the range
# precondition is discharged by TYPING rather than by a hypothesis. So each
# nagini rival ports as an attack on which `Result` constructor is produced at
# which `Operand`, and several nagini cases that split the is_mul facet from the
# surviving-factor facet merge into one point on this carrier.
#
# ------------------------------------------------------------ obligations ------
# Two independent obligations, each an unconditional `∀ (other : Operand)`:
#
#   correct_conjugateProduct   over  problem_spec_conjugateProduct other result
#     clause C-then : other is the identity element   ->  result = Result.lhs
#     clause C-else : any other right factor          ->  result = Result.product
#
#   correct_identityProduct    over  problem_spec_identityProduct other result
#     clause I-then : other is operator-like (an operator, the identity element
#                     itself, or a conjugated operator)  ->  result = Result.rhs
#     clause I-else : a non-operator right factor         ->  result = Result.product
#
# DEFENDED SURFACE (what every rival attacks): the exact partition of the four
# operand kinds between "a factor is returned unchanged" and "the product is left
# unevaluated", AND — on the collapse side — WHICH of the two factors is the one
# returned. The two products partition the SAME four kinds differently: the
# operator-like class that drives the second product includes a conjugated
# operator, while only the bare identity element drives the first. Every rival
# below moves exactly one kind across one of those two boundaries, or keeps the
# boundary and swaps the surviving factor.
#
# BINDER COVERAGE. Each spec predicate has one input binder, `other : Operand`.
# The reject witnesses vary it over ALL FOUR constructors for BOTH predicates —
# conjugateProduct is refuted at identity, operator, conjugate and other;
# identityProduct at identity, operator, conjugate and other — so no kind is held
# at a fixed value across the battery and a rival that mishandled only one kind
# cannot hide.
#
# OMITTED nagini cases and why (repeated in the payload `assessment`):
#   * FRAME / permission-mutation: VACUOUS here. Lean is referentially
#     transparent — no aliasing, no fractional permission, nothing read-only to
#     overwrite — so there is no counterpart rival to author. (The nagini sibling
#     already records this class as N/A for the same behavioral reason: each
#     product builds a fresh result and never mutates a factor.)
#   * DIVERGENCE / non-termination: NOT SHIPPABLE, and the reason is narrower
#     than "it cannot be written". Corrected by audit: an earlier revision of
#     this manifest claimed a diverging rival "cannot be written at all" because
#     both `implementation_*` are total `def`s. That claim is false as written and
#     was measured false. Three constructions, all built:
#       (i)  a self-recursive plain `def` — the elaborator refuses it
#            (`fail to show termination for`), so this much of the old reason
#            does hold: no TOTAL diverging rival exists;
#       (ii) `partial def implementation_conjugateProduct other :=
#            implementation_conjugateProduct other` — refused for a different
#            reason (`failed to compile 'partial' definition`, no `Inhabited
#            Result`), i.e. a tooling wall, not a spec verdict;
#       (iii) the same `partial def` PLUS an impl-region `instance : Inhabited
#            Result := ⟨Result.product⟩`. This one ELABORATES, and
#            `variant_scope.variant_problems` returns [] for it — a `partial`
#            rival IS expressible and scope-admissible on this carrier, since
#            `partial` is not an assumption token.
#     So the class is not empty. What makes it unshippable is that (iii) cannot
#     be given a DISCRIMINATING witness, which was also measured rather than
#     argued. A `partial def` is opaque to reduction: the frozen obligation
#     cannot be closed for it (four tactic attempts, all failing with
#     `unfold`/`decide`/`rfl` errors — so it is genuinely REJECTED, not
#     vacuously verified, and there is no spec hole here), but by the same
#     opacity the evaluation-shaped witness this battery uses also fails against
#     it (`Tactic 'unfold' failed to unfold`). Conditioning the witness on a
#     hypothesis instead — `(h : implementation_conjugateProduct Operand.identity
#     ≠ Result.lhs)` — elaborates against the rival (exit 0) but ALSO elaborates
#     against the frozen solution (exit 0), because `h` contradicts nothing an
#     opaque term exposes; it is therefore a tautology over the shared vocabulary
#     and not a discriminator. A `witness_reference` cannot rescue it either: the
#     same hypothesis witness elaborates against a REDUCING correct reference
#     (the enumeration reshape) too, exit 0. So a diverging rival here would be a
#     reject case whose rejection attributes to the carrier's opacity rather than
#     to the spec — exactly what the witness requirement exists to exclude — and
#     it is deliberately not shipped. Recorded as a KNOWN LIMIT of this lane on
#     this carrier, not as a vacuous class and not as a spec hole.
#   * ADMISSIBILITY: LANDED (see `admiss-both-products-f2p-shaped-inputs`). An
#     earlier revision of this manifest dropped the lane, reasoning that both
#     obligations are unconditional `∀ (other : Operand)` so no precondition
#     could be too strong. That reason is wrong: it describes why the NAGINI
#     shape (a `Requires` discharged at a call site) has no counterpart, not why
#     the DIRECTION is untestable. The analogue on a total carrier is the
#     obligation being UNSATISFIABLE at exactly an F2P-shaped input, and that is
#     testable directly — discharge each spec predicate BY EVALUATION, as a
#     `have`, at the concrete operand the pinned behavior turns on, then close
#     the frozen obligation with its tactic body verbatim. Without this case the
#     battery tested only SPEC-TOO-WEAK and SPEC-TOO-STRONG, i.e. two of the
#     three directions this gate exists to cover.
#   * `uniq-site1-wrong-left-operand-kind` (nagini): INEXPRESSIBLE, and
#     demonstrably so rather than merely hard. That rival keeps the nagini
#     record's `is_mul` and `result_kind` facets correct and corrupts only
#     `left_kind`. This carrier has no such facet to corrupt: `Result` has
#     exactly three constructors (`lhs` / `rhs` / `product`), none of which
#     records an operand KIND, and which factor "lhs" denotes is fixed by WHICH
#     obligation is being discharged rather than by anything an impl returns. So
#     the distinction is collapsed by the carrier, not skipped — there is no
#     Result value a rival could produce that mis-states its left factor while
#     agreeing with gold on the collapse decision and the surviving factor.
#   * AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and this bundle ships
#     no consumed axiom (the axioms region is empty; the dispatch is modeled
#     structurally over the finite carriers).
from pathlib import Path

INSTANCE = "sympy__sympy-19783"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies strictly INSIDE one impl region (or one proof
# region) of the frozen Solution.lean and is unique in the file, so the manifest
# breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

_IMPL_CONJ = """def implementation_conjugateProduct (other : Operand) : Result := Id.run do
  if isIdentityKind other then
    return Result.lhs
  return Result.product"""

_IMPL_ID = """def implementation_identityProduct (other : Operand) : Result := Id.run do
  if isOperatorKind other || isConjugateKind other then
    return Result.rhs
  return Result.product"""

_PROOF_CONJ = """  intro other
  unfold problem_spec_conjugateProduct implementation_conjugateProduct
  simp only [Id.run]
  by_cases h : isIdentityKind other <;> simp [h] <;> rfl"""

_PROOF_ID = """  intro other
  unfold problem_spec_identityProduct implementation_identityProduct
  simp only [Id.run]
  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl"""


# ===========================================================================
# ADMISSIBILITY. Both frozen obligations are unconditional universals, so there
# is no precondition hypothesis a rival could over-strengthen; the analogue on a
# total carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input. This case tests that directly: each spec predicate is discharged BY
# EVALUATION, as a `have`, at the concrete operand its pinned behavior turns on
# — the first product against the identity element on the right, the second
# against a conjugated right factor, which are the two points the newly-pinned
# behavior lives at — and only then is the frozen obligation closed with its
# tactic body VERBATIM. Nothing is assumed and no statement moves.
#
# The `have` is INFORMATIVE rather than a tautology, checked by control: the same
# `have` shape asserting each spec predicate of the WRONG result value
# (`Result.product` at both points) does NOT close — `decide` reports the
# proposition false — so what closes here is the concrete obligation and not the
# shape of the step.
_ADMISS_PROOF_CONJ = """  have admissible_f2p :
      problem_spec_conjugateProduct Operand.identity
        (implementation_conjugateProduct Operand.identity) := by
    unfold problem_spec_conjugateProduct implementation_conjugateProduct
    decide
""" + _PROOF_CONJ

_ADMISS_PROOF_ID = """  have admissible_f2p :
      problem_spec_identityProduct Operand.conjugate
        (implementation_identityProduct Operand.conjugate) := by
    unfold problem_spec_identityProduct implementation_identityProduct
    decide
""" + _PROOF_ID


def _admiss_module():
    """Both impls stay FROZEN; each proof region gains a leading ground `have`."""
    src = _swap(_BASE, _PROOF_CONJ, _ADMISS_PROOF_CONJ)
    return _swap(src, _PROOF_ID, _ADMISS_PROOF_ID)


def _conj(body):
    """Swap ONLY the first product's impl region; the second stays frozen."""
    return _swap(
        _BASE, _IMPL_CONJ,
        "def implementation_conjugateProduct (other : Operand) : Result := "
        "Id.run do\n" + body)


def _ident(body):
    """Swap ONLY the second product's impl region; the first stays frozen."""
    return _swap(
        _BASE, _IMPL_ID,
        "def implementation_identityProduct (other : Operand) : Result := "
        "Id.run do\n" + body)


# ===========================================================================
# SOUNDNESS positives — structurally DIFFERENT but behaviourally IDENTICAL.
# Ports the nagini positive control (`pos-control-enumerate-both-sites`), which
# rewrote both functions as an explicit per-kind enumeration with the branch
# order changed. On this backend a reshaped impl also needs a proof that closes
# for the NEW shape, so each positive reproves inside the proof regions, keeping
# both `theorem correct_*` statements byte-identical. Two shapes are shipped
# because they stress the two clauses differently: the enumeration discharges
# every kind separately (no shared guard at all), the negated guard keeps the
# guard but inverts which arm is the early return.
#
# DEPTH OF EACH RESHAPE, measured by audit rather than asserted. Neither reshape
# is definitionally equal to the frozen impl: `example : negConj =
# implementation_conjugateProduct := by rfl` FAILS for both shapes and for both
# products (`Tactic 'rfl' failed`), so neither positive is the frozen impl
# spelled differently and neither passes for free. They are NOT of equal
# strength, though, and the difference is worth recording because it bounds what
# the negated-guard case proves:
#   * the ENUMERATION reshape genuinely requires reproving — rebuilt with the
#     frozen tactic bodies left in place, it FAILS (`simp made no progress`), so
#     its `cases other <;> decide` proof is doing real work;
#   * the NEGATED-GUARD reshape does NOT require reproving — rebuilt with the
#     frozen tactic bodies it still VERIFIES (exit 0), because `by_cases` on the
#     guard closes either arm order. It remains a legitimate SPEC-TOO-STRONG
#     probe (the spec must not pin arm order, and it does not), but it is the
#     SHALLOWER of the two: the enumeration is the case that would actually catch
#     a spec pinning the `Id.run do` shape.
# ===========================================================================

# (a) Explicit per-kind enumeration: drop the `Id.run do` early-return shape and
# the shared disjunction entirely, answering each of the four kinds directly.
_POS_ENUM_CONJ = """def implementation_conjugateProduct (other : Operand) : Result :=
  match other with
  | .identity => Result.lhs
  | .operator => Result.product
  | .conjugate => Result.product
  | .other => Result.product"""

_POS_ENUM_ID = """def implementation_identityProduct (other : Operand) : Result :=
  match other with
  | .identity => Result.rhs
  | .operator => Result.rhs
  | .conjugate => Result.rhs
  | .other => Result.product"""

_POS_ENUM_PROOF_CONJ = """  intro other
  unfold problem_spec_conjugateProduct implementation_conjugateProduct
  cases other <;> decide"""

_POS_ENUM_PROOF_ID = """  intro other
  unfold problem_spec_identityProduct implementation_identityProduct
  cases other <;> decide"""


def _pos_enum_module():
    src = _swap(_BASE, _IMPL_CONJ, _POS_ENUM_CONJ)
    src = _swap(src, _IMPL_ID, _POS_ENUM_ID)
    src = _swap(src, _PROOF_CONJ, _POS_ENUM_PROOF_CONJ)
    src = _swap(src, _PROOF_ID, _POS_ENUM_PROOF_ID)
    return src


# (b) Negated guard / inverted branch order: keep the guard but make the
# unevaluated-product case the early return, so the collapse case falls through.
_POS_NEG_CONJ = """  if !isIdentityKind other then
    return Result.product
  return Result.lhs"""

_POS_NEG_ID = """  if !(isOperatorKind other || isConjugateKind other) then
    return Result.product
  return Result.rhs"""

_POS_NEG_PROOF_CONJ = """  intro other
  unfold problem_spec_conjugateProduct implementation_conjugateProduct
  simp only [Id.run]
  cases other <;> decide"""

_POS_NEG_PROOF_ID = """  intro other
  unfold problem_spec_identityProduct implementation_identityProduct
  simp only [Id.run]
  cases other <;> decide"""


def _pos_negated_module():
    src = _swap(
        _BASE, _IMPL_CONJ,
        "def implementation_conjugateProduct (other : Operand) : Result := "
        "Id.run do\n" + _POS_NEG_CONJ)
    src = _swap(
        src, _IMPL_ID,
        "def implementation_identityProduct (other : Operand) : Result := "
        "Id.run do\n" + _POS_NEG_ID)
    src = _swap(src, _PROOF_CONJ, _POS_NEG_PROOF_CONJ)
    src = _swap(src, _PROOF_ID, _POS_NEG_PROOF_ID)
    return src


# ===========================================================================
# UNIQUENESS rivals. Each edits exactly ONE impl region and leaves the other
# product frozen, so the rejection is attributable to one obligation.
# ===========================================================================

# --- second product (identity element on the left) --------------------------

# The narrowed-classification rival: treat only a plain operator (or the
# identity element itself) as absorbable, so a conjugated right factor is left
# as an unevaluated product. This is the pre-patch skeleton of the second
# behavior (`Solution_prepatch_2.lean`).
_REJ_ID_NARROW = """  if isOperatorKind other then
    return Result.rhs
  return Result.product"""

# Over-absorb: collapse for EVERY right factor, including a non-operator.
_REJ_ID_ABSORB_ALL = """  return Result.rhs"""

# Keep the collapse boundary exactly right, but return the WRONG factor: the
# left factor (the identity element) instead of the right one.
_REJ_ID_WRONG_FACTOR = """  if isOperatorKind other || isConjugateKind other then
    return Result.lhs
  return Result.product"""

# Never collapse: every product is left unevaluated.
_REJ_ID_NEVER = """  return Result.product"""

# --- first product (conjugated operator on the left) ------------------------

# Never collapse: no dedicated rule for a conjugated left factor, so even the
# identity element on the right is left as an unevaluated product. This is the
# pre-patch skeleton of the first behavior (`Solution_prepatch_1.lean`).
_REJ_CONJ_NEVER = """  return Result.product"""

# Keep the collapse boundary exactly right, but return the WRONG factor: the
# right factor (the identity element) instead of the left one.
_REJ_CONJ_WRONG_FACTOR = """  if isIdentityKind other then
    return Result.rhs
  return Result.product"""

# Over-absorb across the operator boundary: also collapse when the right factor
# is a plain operator, not just the identity element.
_REJ_CONJ_ABSORB_OP = """  if isOperatorKind other then
    return Result.lhs
  return Result.product"""

# Over-absorb across the conjugate boundary: also collapse when the right factor
# is itself a conjugated operator.
_REJ_CONJ_ABSORB_CONJ = """  if isIdentityKind other || isConjugateKind other then
    return Result.lhs
  return Result.product"""

# Whole-domain over-absorb: collapse for every right factor whatsoever.
_REJ_CONJ_ABSORB_ALL = """  return Result.lhs"""


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate directly at ONE concrete operand and
# is fully `decide`-able (both carriers are finite inductives with DecidableEq
# and the spec is a decidable equality under an `if`), so no hypothesis binder is
# needed and there are no assumptions that could be jointly unsatisfiable.
#
# Every witness below was built twice by hand before shipping: it ELABORATES
# against its rival, and on the frozen solution it fails with
# `Tactic 'decide' proved that the proposition ... is false` — i.e. gold provably
# SATISFIES the spec at that operand, which is exactly the discrimination the
# gate re-checks.
#
# Independently re-derived by audit with 36 real builds (9 rivals x 4 files).
# Each witness: rival exit 0, gold exit 1 with that plain evaluation error, no
# stuck reduction / missing instance / unknown identifier anywhere in the logs.
# And the FORGERY pair for each: the same snippet with the `¬` DROPPED — the
# claim that gold is CORRECT at that operand — builds at exit 0 against the
# frozen solution and exit 1 against the rival, the exact inverse. So gold's
# exit code tracks the CLAIM rather than the file, which is what makes it
# admissible evidence rather than a syntactic accident.
#
# EVERY RIVAL IS OBSERVABLY WRONG, not merely reshaped. Re-derived by audit by
# `#eval`-ing each rival's impl against the frozen impl at all four operands in
# one file, rather than inferring it from the rejection. Each of the 9 rivals
# differs from gold at >=1 operand, each witness sits at a kind where that
# rival's value genuinely differs, and no rival is observationally equal to gold
# on the whole carrier — so no case is vacuous under attack C. The two rivals
# that share the `identity` witness point (conjugateproduct never-collapse and
# wrong-surviving-factor) are still distinct impls there: `Result.product` vs
# `Result.rhs` against gold's `Result.lhs`.
#
# WHY NO SPEC HOLE EXISTS IN EITHER DIRECTION, proved rather than sampled. The
# audit discharged both obligations' uniqueness as Lean theorems against the
# frozen spec (built, exit 0):
#     (f : Operand → Result) (hf : ∀ o, problem_spec_conjugateProduct o (f o))
#       → ∀ o, f o = implementation_conjugateProduct o
# and the same for `identityProduct`. Each spec predicate therefore pins its
# result UNIQUELY at every operand, which settles both probe directions for the
# whole carrier at once: no wrong impl can satisfy the spec anywhere
# (SPEC-TOO-WEAK is impossible — 6 further hand-written rivals not in this
# battery, including cross-wired dispatch and two-kind corruptions, were all
# rejected by plain evaluation), and every faithful correct impl satisfies it
# (SPEC-TOO-STRONG is impossible; 3 further correct reshapes were built, of which
# the two computable ones verify). The one reshape that did NOT build —
# `Operand.rec` — fails with `code generator does not support recursor` and
# verifies once marked `noncomputable` (exit 0), i.e. a code-generator limit of
# the carrier, never a rejection by the spec.
# ---------------------------------------------------------------------------

def _witness(fn, operand):
    return (
        "example : ¬ problem_spec_%s Operand.%s\n"
        "    (implementation_%s Operand.%s) := by\n"
        "  unfold problem_spec_%s implementation_%s\n"
        "  decide" % (fn, operand, fn, operand, fn, fn))


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # ---------------------------------------------------------------- soundness
    {
        "id": "pos-control-enumerate-both-products",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_enum_module(),
        "rationale": (
            "Ports the nagini positive control. BOTH products are rewritten as "
            "an explicit per-kind enumeration: the `Id.run do` early-return "
            "shape and the shared disjunction guard are dropped entirely and "
            "each of the four operand kinds is answered directly, in a "
            "different branch order than the frozen guard would visit them. "
            "Behaviourally identical — the first product still collapses to the "
            "left factor exactly on the identity element, the second still "
            "collapses to the right factor exactly on the three operator-like "
            "kinds. There is no loop or fold, so no induction lemma is needed; "
            "both proofs close by case-splitting the finite operand carrier and "
            "deciding each clause, with both `theorem correct_*` statements "
            "byte-identical. MUST verify: if a faithful correct reshape could "
            "not satisfy the two clause pairs, the spec would be "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-negated-guard-both-products",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_negated_module(),
        "rationale": (
            "The second nagini positive shape: keep each guard but NEGATE it, "
            "so the unevaluated-product case becomes the early return and the "
            "collapse case falls through — the opposite arm order from the "
            "frozen impl, with the same partition of the four kinds. Shipped "
            "alongside the enumeration positive because the two stress the "
            "clauses differently: the enumeration removes the guard, this one "
            "keeps it and inverts which arm is reached first. Both must verify; "
            "a rejection here would be SPEC-TOO-STRONG, i.e. the spec pinning "
            "an incidental syntactic shape rather than the behavior."
        ),
    },

    # ------------------------------------------------------------ admissibility
    {
        "id": "admiss-both-products-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_module(),
        "rationale": (
            "Added by audit: the battery carried NO admissibility case, so "
            "PRECOND-TOO-STRONG — one of the three directions this gate exists "
            "to test — was untested, and the reason recorded for dropping it "
            "(both obligations are unconditional, so no precondition can be too "
            "strong) described the absence of the nagini SHAPE rather than the "
            "absence of the direction. On a total carrier the analogue is the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input, and "
            "that is what this case checks. BOTH impls stay frozen; each proof "
            "region gains a leading ground `have` that discharges its own spec "
            "predicate BY EVALUATION at the concrete operand its pinned "
            "behavior turns on — the first product at `identity` (its entire "
            "collapse domain, the point where the conjugated left factor must "
            "survive) and the second at `conjugate` (the kind the wider "
            "operator-like classification newly admits) — after which the "
            "frozen obligation is closed with its tactic body VERBATIM. No new "
            "declaration, no axiom, no `sorry`; both `theorem correct_*` "
            "statements byte-identical. The step is informative rather than a "
            "tautology, checked by control: the same `have` shape asserting "
            "each predicate of the WRONG result value (`Result.product` at "
            "both points) does NOT close — `decide` reports the proposition "
            "false. MUST verify; if the two clauses could not be satisfied at "
            "the very operands the modeled behavior is pinned at, the spec "
            "would be unsatisfiable at a normal input it has to admit."
        ),
    },

    # ------------------------------- uniqueness, second product (identity left)
    {
        "id": "uniq-identityproduct-narrowed-classification",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ident(_REJ_ID_NARROW),
        "refinement": (
            "This is the pre-patch skeleton of the second behavior: the "
            "operator-like classification is narrowed so that a conjugated "
            "right factor is no longer recognised as absorbable. A faithful "
            "real patch with this narrower classification leaves the identity "
            "element times a conjugated operator as the unevaluated product of "
            "the two factors instead of the conjugated operator itself — which "
            "is precisely the equality the newly-failing test pins (that "
            "product must equal the conjugated operator). It would therefore "
            "NOT resolve, so a verifying rival here is a true "
            "verify-does-not-imply-resolve break, not an artifact. This rival "
            "is also, verbatim, the bundle's own prepatch impl for this "
            "behavior."
        ),
        "rationale": (
            "Rejected by clause I-then. On `other = conjugate` the spec's guard "
            "`isOperatorKind other || isConjugateKind other` is TRUE (the "
            "second disjunct fires), so it demands `Result.rhs`, whereas the "
            "rival — consulting the first disjunct only — falls through to "
            "`Result.product`. Genuine partial-domain rival: it agrees with the "
            "spec at identity, operator and other, and is wrong at exactly one "
            "kind. Witness varies the binder to `conjugate`, the only point "
            "that separates the two disjuncts."
        ),
        "witness": _witness("identityProduct", "conjugate"),
    },
    {
        "id": "uniq-identityproduct-absorb-every-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ident(_REJ_ID_ABSORB_ALL),
        "refinement": (
            "The complementary over-absorption: collapse for EVERY right "
            "factor, so even a non-operator (a scalar or generic expression) is "
            "absorbed. A faithful real patch dropping the classification test "
            "altogether would make the identity element times a plain scalar "
            "return that scalar rather than an unevaluated product — breaking "
            "the standing assertion in the same failing test file that such a "
            "product remains an unevaluated product. It would NOT resolve."
        ),
        "rationale": (
            "Rejected by clause I-else, the arm the other three rivals against "
            "this obligation never reach. On `other = other` the guard is "
            "FALSE, so the spec demands `Result.product`, whereas the rival "
            "returns `Result.rhs`. Witness moves the binder to the single "
            "non-operator kind."
        ),
        "witness": _witness("identityProduct", "other"),
    },
    {
        "id": "uniq-identityproduct-wrong-surviving-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ident(_REJ_ID_WRONG_FACTOR),
        "refinement": (
            "Ports the nagini wrong-surviving-operand rival. The collapse "
            "BOUNDARY is left exactly right — this rival collapses on precisely "
            "the three operator-like kinds and on no other — so any check that "
            "only asks *whether* the product was evaluated is blind to it; what "
            "it gets wrong is WHICH factor survives, returning the left factor "
            "(the identity element) instead of the right one. A faithful real "
            "patch returning the left factor makes the identity element times a "
            "plain operator equal the identity element rather than that "
            "operator, so the long-standing assertion that this product equals "
            "the right-hand operator fails outright in the same test as the new "
            "conjugated-factor assertion. It would NOT resolve."
        ),
        "rationale": (
            "Rejected by clause I-then on its VALUE rather than its guard: the "
            "spec pins `result = Result.rhs`, the rival yields `Result.lhs`. "
            "Attacks the surviving-factor facet that the collapse boundary does "
            "not constrain. Witness at `operator`, a point where the rival "
            "differs from gold AND where the corresponding real behavior is "
            "observably wrong — distinct from the `conjugate` point of the "
            "narrowed-classification rival, which this rival handles correctly."
        ),
        "witness": _witness("identityProduct", "operator"),
    },
    {
        "id": "uniq-identityproduct-never-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ident(_REJ_ID_NEVER),
        "refinement": (
            "Whole-domain near-miss on the collapse side: no product is ever "
            "evaluated. A faithful real patch of this shape leaves the identity "
            "element times an operator, times the identity element itself, and "
            "times a conjugated operator ALL unsimplified, so both the "
            "long-standing and the newly-added absorption assertions fail. It "
            "would NOT resolve. Kept as the cheap whole-domain supporting case "
            "the nagini sibling also carries — it subsumes the narrowed rival's "
            "sub-domain but is not a substitute for it, and its witness sits at "
            "a kind no other rival for this obligation probes."
        ),
        "rationale": (
            "Rejected by clause I-then on the whole operator-like domain. "
            "Witness at `identity`: the guard is TRUE there (the identity "
            "element is itself an operator, so the classification includes it), "
            "the spec demands `Result.rhs`, the rival returns `Result.product`. "
            "That point is untouched by the other three rivals for this "
            "obligation, so it is what varies this binder over its fourth and "
            "last value."
        ),
        "witness": _witness("identityProduct", "identity"),
    },

    # ------------------------------- uniqueness, first product (conjugate left)
    {
        "id": "uniq-conjugateproduct-never-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _conj(_REJ_CONJ_NEVER),
        "refinement": (
            "This is the pre-patch skeleton of the first behavior: a "
            "conjugated left factor has no product rule of its own, so it falls "
            "back on the generic construction and every product — including one "
            "whose right factor is the identity element — is left unevaluated. "
            "That is exactly the behavior the issue reports. A faithful real "
            "patch of this shape leaves a conjugated operator times the "
            "identity element unsimplified, failing both the newly-added "
            "assertion that this product equals the conjugated operator and the "
            "companion assertion routed through a conjugated identity element. "
            "It would NOT resolve. This rival is also, verbatim, the bundle's "
            "own prepatch impl for this behavior."
        ),
        "rationale": (
            "Rejected by clause C-then. On `other = identity` the spec demands "
            "`Result.lhs`; the rival returns `Result.product`. The whole "
            "collapse domain of this obligation is the single kind `identity`, "
            "so that is the only point at which this rival can be refuted."
        ),
        "witness": _witness("conjugateProduct", "identity"),
    },
    {
        "id": "uniq-conjugateproduct-wrong-surviving-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _conj(_REJ_CONJ_WRONG_FACTOR),
        "refinement": (
            "Ports the nagini wrong-surviving-operand rival for this product. "
            "The collapse boundary is left exactly right — it collapses on the "
            "identity element and on nothing else — but the surviving factor is "
            "the RIGHT one (the identity element) instead of the left one (the "
            "conjugated operator). A faithful real patch returning the right "
            "factor makes a conjugated operator times the identity element "
            "equal the identity element, so the newly-added assertion that this "
            "product equals the conjugated operator fails, as does its "
            "companion routed through a conjugated identity element. It would "
            "NOT resolve."
        ),
        "rationale": (
            "Rejected by clause C-then on its VALUE rather than its guard: the "
            "spec pins `result = Result.lhs`, the rival yields `Result.rhs`. "
            "Shares the `identity` witness point with the never-collapse rival "
            "— unavoidably, since that is this obligation's entire collapse "
            "domain — but for a genuinely different reason and with a different "
            "wrong value: never-collapse fails to evaluate at all, this one "
            "evaluates and keeps the wrong factor. Neither is a near-miss of "
            "the other: both agree with the spec on the whole non-identity "
            "domain and differ from it only here, so there is no input at which "
            "one is right and the other wrong."
        ),
        "witness": _witness("conjugateProduct", "identity"),
    },
    {
        "id": "uniq-conjugateproduct-absorb-operator-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _conj(_REJ_CONJ_ABSORB_OP),
        "refinement": (
            "Ports the nagini over-absorb rival for this product: widen the "
            "absorption test from the identity element to any operator, so a "
            "plain operator on the right is absorbed too. A faithful real patch "
            "of this shape returns the conjugated operator for a conjugated "
            "operator times a plain operator, instead of their unevaluated "
            "product; the newly-added test pins that product's canonical form "
            "by multiplying it further by the identity element and comparing "
            "against the explicitly-constructed unevaluated product, and that "
            "comparison fails once the inner product has collapsed to a single "
            "factor. It would NOT resolve."
        ),
        "rationale": (
            "Rejected by clause C-else. On `other = operator` the spec demands "
            "`Result.product`; the rival returns `Result.lhs`. Partial-domain "
            "rival on a DISJOINT sub-domain from the two collapse-side rivals "
            "above: it is correct at identity and wrong at operator, which is "
            "precisely the reverse. Witness at `operator`."
        ),
        "witness": _witness("conjugateProduct", "operator"),
    },
    {
        "id": "uniq-conjugateproduct-absorb-conjugate-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _conj(_REJ_CONJ_ABSORB_CONJ),
        "refinement": (
            "The over-absorption that the second product's WIDER classification "
            "would license if it were reused here: also absorb a right factor "
            "that is itself a conjugated operator. This is the mirror of the "
            "narrowed-classification rival on the other obligation, and it "
            "matters because the two products deliberately classify this kind "
            "differently. A faithful real patch of this shape returns a single "
            "conjugated operator for a conjugated operator times itself, "
            "instead of that factor squared — failing the newly-added assertion "
            "that pins the squared form. It would NOT resolve."
        ),
        "rationale": (
            "Rejected by clause C-else at `other = conjugate`: the spec demands "
            "`Result.product` (only the identity element triggers absorption "
            "for this product), the rival returns `Result.lhs`. A sub-domain no "
            "other rival for this obligation is wrong on — the over-absorb-"
            "operator rival is correct here, and this one is correct at "
            "`operator` — so the witness must sit at `conjugate`."
        ),
        "witness": _witness("conjugateProduct", "conjugate"),
    },
    {
        "id": "uniq-conjugateproduct-absorb-every-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _conj(_REJ_CONJ_ABSORB_ALL),
        "refinement": (
            "Whole-domain over-absorption: every product collapses to the "
            "conjugated left factor. A faithful real patch of this shape "
            "returns the conjugated operator for a conjugated operator times "
            "ANY factor, so both canonical forms the newly-added test pins (the "
            "unevaluated product against a plain operator, and the squared form "
            "against a second conjugated operator) are destroyed, and a "
            "conjugated operator times an ordinary scalar silently loses the "
            "scalar. It would NOT resolve."
        ),
        "rationale": (
            "Rejected by clause C-else on its entire domain. Witness at `other` "
            "— the non-operator kind — which is the point that distinguishes "
            "this rival from the two narrower over-absorb rivals above: both of "
            "those are CORRECT there, so refuting this one at `operator` or "
            "`conjugate` would claim a sub-domain the manifest already covers "
            "and would leave the fourth value of this binder unprobed."
        ),
        "witness": _witness("conjugateProduct", "other"),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job, and this bundle consumes no axiom at
# all — the axioms region is empty and both decisions are modeled structurally
# over the finite operand/result carriers, so there is no callee contract a
# runtime probe could falsify from here.
AXIOM_TESTS = []
