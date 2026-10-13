"""properties.py — G-PBT falsification battery for django__django-15930 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect:"reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

DEFENDED SURFACE (one total function; four inputs, one two-component output):

  resolveBranchCondition
      (conditionSql : String) (conditionParams : List α)
      (trueSql : String) (trueParams : List α) : String × List α
      (conditionSql = "" → result = (trueSql, trueParams))            -- P1
    ∧ (conditionSql ≠ "" → result = (conditionSql, conditionParams))  -- P2

  The rendered guard fragment for one branch of a searched conditional is
  selected here: when it is EMPTY, the branch must instead use an
  always-satisfied stand-in fragment together with its bound parameters
  (`(trueSql, trueParams)`); when it is NON-EMPTY, the branch keeps the guard
  fragment and its own parameters unchanged (`(conditionSql, conditionParams)`).
  The two clauses jointly pin both output components on both sub-domains, so
  neither component is ever left free.

    * P1 (empty sub-domain) pins BOTH components to the stand-in pair; it depends
      on `conditionSql` (the branch selector), `trueSql`, and `trueParams`.
    * P2 (non-empty sub-domain) pins BOTH components to the original pair; it
      depends on `conditionSql`, `conditionParams` (and, contrapositively, the
      guard-fragment text carried through unchanged).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its four inputs are held at fractional
    (read-only) permission, so a rival that appends to one is rejected for
    insufficient permission. Lean is referentially transparent: the four inputs
    are plain immutable values (`String` / `List α`); there is no half-permission
    to violate and no aliasing to exploit, so this class has NO expressible
    instance here. No substitute is fabricated for it (nagini
    `frame-mutate-cons-params`, `frame-mutate-pred` are dropped).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: two
    equalities against pairs built only from the four inputs, with a single
    emptiness split. The bundle declares no `opaque`/`axiom` (meta.json
    axioms == [], deep_model_references == []), so there is no answer key an
    implementation could echo without doing the work.

  * PARTIAL-DOMAIN (the pre-patch, empty-fragment sub-domain) — APPLIES, and is
    the load-bearing rival. The pre-fix spliced the empty guard fragment verbatim
    with NO substitution, so it is correct on every non-empty guard and diverges
    precisely on the empty-fragment sub-domain that the F2P observable exercises
    (nagini `partial-domain-prepatch` → `weak-prepatch-no-substitution`).

  * WRONG NON-EMPTY SLOT — APPLIES. Nagini's `partial-domain-nonempty-slot`
    fills the non-empty guard slot with the wrong fragment; its lean analogue is
    a rival that substitutes the stand-in pair on the NON-EMPTY branch too, or
    that carries the stand-in's parameters for a real guard, each violating P2
    (`weak-always-substitute`, `weak-condition-params-dropped`).

  * PARAMS-CONCATENATION ORDER — OMITTED (carrier narrowing). Nagini's
    `partial-domain-params-order` attacks the ORDER in which the guard's
    parameters and the result fragment's parameters are concatenated into the
    branch's parameter list. That concatenation is downstream of the modeled
    decision: this bundle models only the selection of the `(guard fragment,
    guard parameters)` pair, not how that pair is later merged with the result
    fragment's parameters. There is no binder for it on this carrier, so the
    case has no faithful counterpart and is not fabricated.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen `Id.run
do` form — so a rejection alone attributes nothing to the spec. Every
`expect="reject"` case therefore carries a Lean snippet stating the spec
predicate directly at a `decide`-able concrete input; each was checked to HOLD of
its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). Parameter payloads are instantiated at `List Nat` (the
element type is irrelevant to the decision, which branches only on
`conditionSql = ""`).

BINDER COVERAGE. All four input binders are varied across the reject witnesses:
  * `conditionSql` — `""` (prepatch, sql-only) AND non-empty `"C"`
    (always-substitute, params-dropped).
  * `conditionParams` — `[1]`, `[3]`, `[5]` across the rivals.
  * `trueSql` — `"T"` and `"U"`, so it is not pinned to a single value.
  * `trueParams` — `[2]`, `[4]`, `[6]` across the rivals.
Both top-level clauses are attacked: P1 by `weak-prepatch-no-substitution`
(both components) and `weak-substitute-sql-only` (its parameter component); P2 by
`weak-always-substitute` (both components) and `weak-condition-params-dropped`
(its parameter component). `pts` = 4 distinct input points.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total emptiness test plus wholesale substitution over the
inputs, so there is no axiom-soundness / axiom-containment obligation to probe
here (that lane belongs to G-AX in any case). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-15930"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_resolveBranchCondition {α : Type}\n"
    "    (conditionSql : String) (conditionParams : List α)\n"
    "    (trueSql : String) (trueParams : List α) : String × List α := Id.run do\n"
    "  let mut condSql := conditionSql\n"
    "  let mut condParams := conditionParams\n"
    "  if condSql == \"\" then\n"
    "    condSql := trueSql\n"
    "    condParams := trueParams\n"
    "  return (condSql, condParams)\n"
)

_PROOF_BODY = (
    "  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
    "  refine ⟨fun h => ?_, fun h => ?_⟩\n"
    "  · simp only [Id.run]\n"
    "    rw [show (conditionSql == \"\") = true from by rw [beq_iff_eq]; exact h]\n"
    "    rfl\n"
    "  · simp only [Id.run]\n"
    "    rw [show (conditionSql == \"\") = false from by rw [beq_eq_false_iff_ne]; exact h]\n"
    "    rfl\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with the gold impl body swapped (spec + theorem
    statement untouched; the frozen proof body is carried over and will FAIL to
    close against a wrong impl — the expected reject signal)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes).
# ---------------------------------------------------------------------------

# PREPATCH / NEVER-SUBSTITUTE (= the pre-fix bug): keep the guard fragment and
# its parameters verbatim, with NO empty-fragment substitution. Correct on every
# non-empty guard; on the empty guard it returns ("", conditionParams) instead of
# the stand-in pair — violates P1 on both components.
_NEVER_SUBSTITUTE = (
    "def implementation_resolveBranchCondition {α : Type}\n"
    "    (conditionSql : String) (conditionParams : List α)\n"
    "    (trueSql : String) (trueParams : List α) : String × List α := Id.run do\n"
    "  let mut condSql := conditionSql\n"
    "  let mut condParams := conditionParams\n"
    "  return (condSql, condParams)\n"
)

# ALWAYS-SUBSTITUTE: return the always-satisfied stand-in pair on EVERY input,
# discarding a real non-empty guard fragment and its parameters — violates P2 on
# both components.
_ALWAYS_SUBSTITUTE = (
    "def implementation_resolveBranchCondition {α : Type}\n"
    "    (conditionSql : String) (conditionParams : List α)\n"
    "    (trueSql : String) (trueParams : List α) : String × List α :=\n"
    "  (trueSql, trueParams)\n"
)

# SUBSTITUTE-SQL-ONLY: on the empty guard, replace only the fragment TEXT with the
# stand-in's, but keep the original (empty guard's) parameters — violates P1 on
# its parameter component (the parameters must be the stand-in's `trueParams`).
_SUBSTITUTE_SQL_ONLY = (
    "def implementation_resolveBranchCondition {α : Type}\n"
    "    (conditionSql : String) (conditionParams : List α)\n"
    "    (trueSql : String) (trueParams : List α) : String × List α := Id.run do\n"
    "  let mut condSql := conditionSql\n"
    "  let mut condParams := conditionParams\n"
    "  if condSql == \"\" then\n"
    "    condSql := trueSql\n"
    "  return (condSql, condParams)\n"
)

# CONDITION-PARAMS-DROPPED: always carry the stand-in's parameters, even for a
# real non-empty guard fragment. Correct on the empty branch (P1 holds), but on a
# non-empty guard it returns (conditionSql, trueParams) instead of the guard's own
# parameters — violates P2 on its parameter component.
_CONDITION_PARAMS_DROPPED = (
    "def implementation_resolveBranchCondition {α : Type}\n"
    "    (conditionSql : String) (conditionParams : List α)\n"
    "    (trueSql : String) (trueParams : List α) : String × List α := Id.run do\n"
    "  let mut condSql := conditionSql\n"
    "  let mut condParams := trueParams\n"
    "  if condSql == \"\" then\n"
    "    condSql := trueSql\n"
    "  return (condSql, condParams)\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional expression (no `Id.run do` / `let mut`), spelling the decision
# as one `if … then … else …`. Same value on every input; the frozen script no
# longer applies to the new shape, so the obligation is re-proved (statement
# byte-identical, no new lemma/axiom/assumption token).
_POS_IMPL = (
    "def implementation_resolveBranchCondition {α : Type}\n"
    "    (conditionSql : String) (conditionParams : List α)\n"
    "    (trueSql : String) (trueParams : List α) : String × List α :=\n"
    "  if conditionSql = \"\" then (trueSql, trueParams) else (conditionSql, conditionParams)\n"
)
_POS_PROOF = (
    "  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
    "  refine ⟨fun h => ?_, fun h => ?_⟩\n"
    "  · rw [if_pos h]\n"
    "  · rw [if_neg h]\n"
)

# ADMISSIBILITY: the frozen gold impl, with a ground instance of the spec at the
# F2P-shaped input (an EMPTY guard fragment, which must be replaced by the
# stand-in pair) discharged inside the proof region before the frozen obligation
# is closed verbatim. Confirms the obligation is satisfiable at the exact input
# the F2P exercises, not merely provable in the abstract.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_resolveBranchCondition \"\" ([] : List Nat) \"T\" [7]\n"
    "      (implementation_resolveBranchCondition \"\" ([] : List Nat) \"T\" [7]) := by\n"
    "    unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
    "    decide\n"
) + _PROOF_BODY


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. A rejection here would be SPEC-TOO-STRONG. The
    # `theorem correct_resolveBranchCondition` STATEMENT is byte-identical; only
    # the tactic body is re-proved for the new (functional `if`) shape. No helper
    # lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the `Id.run do` / `let mut` accumulator "
            "and spells the decision as one functional `if conditionSql = \"\" then "
            "(trueSql, trueParams) else (conditionSql, conditionParams)` must "
            "satisfy both clauses; if it cannot, the spec is SPEC-TOO-STRONG. "
            "Proof: after `unfold`, `rw [if_pos h]` / `rw [if_neg h]` close each "
            "clause by reflexivity — no new declaration, axiom, or assumption."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input. The frozen theorem carries NO
    # precondition hypothesis (the behavior is total, so `∀` is unguarded), so
    # nagini's precondition-admission probe has no binder to attack; the honest
    # analogue is to discharge the spec predicate at the F2P ground input (an
    # EMPTY guard fragment) inside the proof region alongside the frozen
    # obligation. If that ground instance could not be discharged, the modeled
    # behavior would be unsatisfiable at exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-empty-guard-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (empty guard "
            "fragment `\"\"`, where the spec requires the always-satisfied stand-in "
            "pair `(\"T\", [7])` rather than the empty pair) by `decide`; then the "
            "frozen obligation is closed verbatim. Verifies (else the spec is "
            "unsatisfiable at the normal input, the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: the theorem STATEMENT is byte-identical, the ground "
            "instance is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-no-substitution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NEVER_SUBSTITUTE),
        "refinement": (
            "this is the pre-fix behavior: the guard fragment and its parameters are "
            "carried through with NO empty-fragment substitution. Its faithful real "
            "patch is the pre-patch code, which splices the EMPTY guard fragment "
            "verbatim into the branch template, producing a malformed template with "
            "the leading keyword immediately followed by the trailing keyword and no "
            "predicate between them — a SQL syntax error. The F2P observable (an "
            "always-true predicate rendered as an empty fragment) then raises rather "
            "than annotating every row. It does NOT resolve — this is the leg's "
            "prepatch."
        ),
        "rationale": (
            "REJECT from P1 (`conditionSql = \"\" → result = (trueSql, trueParams)`): "
            "at `conditionSql = \"\"`, `trueSql = \"T\"`, the spec demands `(\"T\", "
            "[2])`, but the rival returns `(\"\", [1])`. Refuted on the empty-guard "
            "sub-domain — the discriminating input the F2P exercises."
        ),
        "witness": (
            "-- Refuted on the empty guard fragment: the branch must use the\n"
            "-- always-satisfied stand-in pair, but a no-substitution impl keeps the\n"
            "-- empty fragment (and its parameters) unchanged.\n"
            "example : ¬ problem_spec_resolveBranchCondition \"\" ([1] : List Nat) \"T\" [2]\n"
            "    (implementation_resolveBranchCondition \"\" ([1] : List Nat) \"T\" [2]) := by\n"
            "  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-always-substitute",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_SUBSTITUTE),
        "refinement": (
            "always returning the always-satisfied stand-in pair discards a real, "
            "non-empty guard fragment and replaces it with an unconditionally-true "
            "predicate. A faithful patch that did this would make every conditional "
            "branch match every row regardless of its actual guard, silently "
            "returning the wrong values across the annotate/filter/update behaviors "
            "the pre-existing tests assert. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from P2 (`conditionSql ≠ \"\" → result = (conditionSql, "
            "conditionParams)`): at `conditionSql = \"C\"` the spec demands `(\"C\", "
            "[1])`, but the rival returns the stand-in pair `(\"T\", [2])`. Refuted on "
            "the NON-EMPTY sub-domain, confirming P2 pins the non-empty path."
        ),
        "witness": (
            "-- Refuted on a non-empty guard fragment: the branch must keep its own\n"
            "-- fragment and parameters, but an always-substitute impl overwrites\n"
            "-- them with the stand-in pair.\n"
            "example : ¬ problem_spec_resolveBranchCondition \"C\" ([1] : List Nat) \"T\" [2]\n"
            "    (implementation_resolveBranchCondition \"C\" ([1] : List Nat) \"T\" [2]) := by\n"
            "  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-substitute-sql-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SUBSTITUTE_SQL_ONLY),
        "refinement": (
            "on the empty guard, replacing only the fragment TEXT with the stand-in's "
            "while keeping the original (empty) guard's parameter list corresponds to "
            "emitting the stand-in's placeholder without supplying its bound "
            "parameters. The placeholder/parameter counts no longer match, so the "
            "prepared statement binds incorrectly (or errors). It does NOT resolve."
        ),
        "rationale": (
            "REJECT from P1's parameter component: at `conditionSql = \"\"`, `trueSql "
            "= \"U\"`, the spec demands `(\"U\", [4])`, but the rival returns `(\"U\", "
            "[3])` — correct fragment text, wrong parameters. Refuted where the "
            "original and stand-in parameters DIFFER, isolating the parameter half of "
            "P1 (and varying `trueSql` off the value the other rivals use)."
        ),
        "witness": (
            "-- Refuted on the empty guard when the original and stand-in parameters\n"
            "-- differ: substituting only the fragment text leaves the wrong\n"
            "-- parameters bound.\n"
            "example : ¬ problem_spec_resolveBranchCondition \"\" ([3] : List Nat) \"U\" [4]\n"
            "    (implementation_resolveBranchCondition \"\" ([3] : List Nat) \"U\" [4]) := by\n"
            "  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-condition-params-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CONDITION_PARAMS_DROPPED),
        "refinement": (
            "carrying the stand-in's parameters even for a real non-empty guard "
            "corresponds to binding the always-true stand-in's parameters into the "
            "genuine guard's placeholders. The guard would compare/bind the wrong "
            "values, changing which rows the branch matches on any non-trivial "
            "condition, so the pre-existing annotate/filter/update tests fail. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from P2's parameter component: at `conditionSql = \"C\"`, "
            "`conditionParams = [5]`, `trueParams = [6]`, the spec demands `(\"C\", "
            "[5])`, but the rival returns `(\"C\", [6])` — correct fragment text, the "
            "stand-in's parameters. Refuted where the guard and stand-in parameters "
            "DIFFER, exercising `conditionParams` at a value other than the other "
            "rivals'."
        ),
        "witness": (
            "-- Refuted on a non-empty guard when the guard and stand-in parameters\n"
            "-- differ: the branch must keep its own parameters, not the stand-in's.\n"
            "example : ¬ problem_spec_resolveBranchCondition \"C\" ([5] : List Nat) \"T\" [6]\n"
            "    (implementation_resolveBranchCondition \"C\" ([5] : List Nat) \"T\" [6]) := by\n"
            "  unfold problem_spec_resolveBranchCondition implementation_resolveBranchCondition\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the emptiness test and the
# wholesale substitution are modeled directly over the inputs, so there is no
# in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
