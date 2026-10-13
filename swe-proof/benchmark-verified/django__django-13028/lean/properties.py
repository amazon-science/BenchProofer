"""properties.py — G-PBT falsification battery for django__django-13028 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_checkFilterable``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total structural fold over a recursive candidate carrier):

  checkFilterable (e : Expr) : Bool
    result = raises e
    where  raises (mk q f children) = (q && !f) || raisesAny children

  A candidate value ``e`` is modeled by three observable facets: ``isQueryExpr``
  (``q`` — whether it is a genuine query expression), ``filterable`` (``f`` —
  absence of the marking folds to ``true``), and ``children`` (its nested source
  sub-expressions). The single postcondition clause ``result = raises e`` folds
  three inseparable sub-decisions, each pinned to a distinct facet of the carrier:

    * OWN-ACCOUNT REJECTION requires BOTH conjuncts — a node forces rejection on
      its own account exactly when it is a query expression (``q``) AND is marked
      non-admissible (``!f``). Pinned by ``q`` and ``f`` jointly; dropping either
      conjunct, or widening the ``&&`` to ``||``, is a distinct defect.
    * RECURSIVE PROPAGATION — rejection propagates from any nested sub-expression
      that independently warrants it (``raisesAny children``). Pinned by
      ``children``; a rival that never inspects the children misses it.
    * COMBINATION — the two are OR-combined; a node clean on its own account is
      still rejected if some child warrants it, and vice versa.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an input-write
    attack MANDATORY because its modeled inputs are held at fractional (read-only)
    permission, so a rival that overwrites one is rejected for insufficient
    permission. Lean is referentially transparent: ``e : Expr`` is a plain
    immutable value, there is no half-permission to violate and no aliasing to
    exploit, so this class has NO expressible instance here. No substitute is
    fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term (``raises e``) built structurally from the carrier's own three
    facets and fully transparent. The bundle declares no ``opaque``/``axiom``
    (mapping.md: no consumed callee), so there is no answer key an implementation
    could echo without doing the work; the traversal, the two-conjunct guard, and
    the ``none``/recurse combination are all transparent to ``decide``. The honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * CONTROL-FLOW-EFFECT / prepatch bug — APPLIES, load-bearing. The pre-fix guard
    dropped the query-expression conjunct, rejecting on ``!f`` alone. It ports
    directly and is refuted on a plain value (``q = false``) marked non-admissible.

  * PARTIAL-DOMAIN — APPLIES on two axes of the recursive carrier. The nagini
    skip-FIRST (screen only the sub-operands, skip the top-level operand) becomes
    a rival that recurses into ``children`` but never checks the node on its own
    account. The nagini skip-LAST (an off-by-one that leaves a visited operand
    unscreened) becomes a rival that checks the node but never recurses, leaving
    every child unscreened. Each is correct on part of the domain and refuted on
    its own sub-domain.

  * WIDEN CONJUNCTION TO DISJUNCTION — APPLIES. Rejecting on ``q || !f`` over-rejects
    an admissible query expression and a plain non-admissible value; refuted on a
    permitted query expression the spec accepts.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen mutual-recursion script is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``-able concrete ``Expr`` literal; the carrier and
the fold are fully transparent, so ``decide`` reduces both sides. Each was checked
to HOLD of its rival and to FAIL on the frozen solution (so it discriminates
rather than asserting a tautology); ``native_decide`` is banned and not used.

BINDER / FACET COVERAGE. The single spec binder is the candidate ``e``; its three
facets are each varied across the reject witnesses so the battery exercises the
spec's dependence on each rather than probing one point repeatedly:
  * ``isQueryExpr`` (``q``) — refuted at ``false`` (drop-conjunct, skip-self-root)
    AND at ``true`` (widen-to-or, skip-self).
  * ``filterable`` (``f``) — refuted at ``false`` (drop-conjunct, skip-self) AND at
    ``true`` (widen-to-or; and the clean root of the drop-recursion witness).
  * ``children`` — refuted at ``[]`` (drop-conjunct, widen, skip-self) AND at a
    NON-EMPTY list carrying a disallowed child (drop-recursion), so the recursive
    leg is not probed at the empty list alone.
``pts`` = 4 distinct input points.

AXIOM lane: DROPPED. mapping.md declares no consumed callee (axioms region empty);
the modeled behavior is a total structural fold over the carrier's own facets, so
there is no axiom-soundness / axiom-containment obligation, and that lane belongs
to G-AX in any case. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-13028"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full node-equation of the impl region's mutual block, the full tactic body
# of the per-node proof lemma, and the full frozen `correct_*` tactic body, so
# every replacement lands entirely inside the region it means to edit. The list
# equation (implementation_checkFilterableAny) is kept verbatim in every variant.
_IMPL_NODE = (
    "def implementation_checkFilterable : Expr → Bool\n"
    "  | .mk q f children => Id.run do\n"
    "    if q && !f then\n"
    "      return true\n"
    "    return implementation_checkFilterableAny children\n"
)

_PROOF_NODE = (
    "    simp only [implementation_checkFilterable, raises, Id.run]\n"
    "    by_cases h : q && !f\n"
    "    · simp only [h, if_true, Bool.true_or]; rfl\n"
    "    · simp only [h, Bool.false_or]\n"
    "      exact impl_any_eq_raisesAny children\n"
)

_CORRECT_BODY = (
    "  intro e\n"
    "  unfold problem_spec_checkFilterable\n"
    "  exact impl_eq_raises e\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_NODE) == 1, "impl node anchor drifted; update _IMPL_NODE"
assert _BASE.count(_PROOF_NODE) == 1, "proof node anchor drifted; update _PROOF_NODE"
assert _BASE.count(_CORRECT_BODY) == 1, "correct body anchor drifted; update _CORRECT_BODY"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl. The
# node equation is spelled as one functional expression with the OR operands
# COMMUTED (recurse-first, own-account-second) — same Bool value on every input,
# no `Id.run do` / early return. The frozen per-node script is tuned to the
# early-return form, so the node lemma is re-proved for the new shape via
# `Bool.or_comm` (a core lemma, no new declaration); the list lemma and the
# `correct_*` body are untouched.
# ---------------------------------------------------------------------------
_POS_NODE = (
    "def implementation_checkFilterable : Expr → Bool\n"
    "  | .mk q f children => implementation_checkFilterableAny children || (q && !f)\n"
)
_POS_PROOF = (
    "    simp only [implementation_checkFilterable, raises]\n"
    "    rw [impl_any_eq_raisesAny children]\n"
    "    exact Bool.or_comm _ _\n"
)


# ---------------------------------------------------------------------------
# Rival node equations (each replaces only the node equation; the list equation
# `implementation_checkFilterableAny` stays verbatim, so the spec and the
# `theorem correct_checkFilterable` STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PREPATCH / DROP-CONJUNCT: reject on `!f` alone, dropping the query-expression
# conjunct. This is the pre-fix guard.
_DROP_CONJUNCT = (
    "def implementation_checkFilterable : Expr → Bool\n"
    "  | .mk q f children => Id.run do\n"
    "    if !f then\n"
    "      return true\n"
    "    return implementation_checkFilterableAny children\n"
)

# WIDEN-TO-OR: reject on `q || !f`, over-rejecting a permitted query expression
# and a plain non-admissible value.
_WIDEN_TO_OR = (
    "def implementation_checkFilterable : Expr → Bool\n"
    "  | .mk q f children => Id.run do\n"
    "    if q || !f then\n"
    "      return true\n"
    "    return implementation_checkFilterableAny children\n"
)

# SKIP-LAST analogue — DROP-RECURSION: check the node on its own account but never
# recurse into the children, so a disallowed sub-expression is never screened.
_DROP_RECURSION = (
    "def implementation_checkFilterable : Expr → Bool\n"
    "  | .mk q f children => Id.run do\n"
    "    if q && !f then\n"
    "      return true\n"
    "    return false\n"
)

# SKIP-FIRST analogue — SKIP-SELF: recurse into the children but never check the
# node on its own account, so a disallowed top-level candidate is missed.
_SKIP_SELF = (
    "def implementation_checkFilterable : Expr → Bool\n"
    "  | .mk _q _f children => implementation_checkFilterableAny children\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_checkFilterable`
    # STATEMENT is byte-identical; only the per-node lemma's tactic body is
    # re-tuned for the reshaped (functional, commuted-OR) equation. No helper
    # lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-commuted-or-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_NODE, _POS_NODE), _PROOF_NODE, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the `Id.run do` early-return and spells "
            "the node decision as one functional expression with the OR operands "
            "commuted (`raisesAny children || (q && !f)`) yields the same Bool on "
            "every input, so `result = raises e` still holds; if it could not "
            "verify the spec would be SPEC-TOO-STRONG. Re-proved because the frozen "
            "per-node script matches the early-return branch order: the new shape "
            "closes after `rw [impl_any_eq_raisesAny children]` via `Bool.or_comm` "
            "(a core lemma, no new declaration); the list lemma and the "
            "`correct_checkFilterable` body are untouched."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only provable in
    # the abstract. The frozen theorem carries NO precondition hypothesis (the
    # fold is total, so `∀` is unguarded), so nagini's precondition-admission probe
    # has no binder to attack here; the honest analogue is to discharge the spec
    # predicate at the representative F2P-shaped input — a plain value (not a query
    # expression) marked non-admissible, which the fixed behavior ACCEPTS — inside
    # the proof region alongside the frozen obligation. If that ground instance
    # could not be discharged, the modeled behavior would be unsatisfiable at
    # exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-plain-nonadmissible-accepted",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _CORRECT_BODY,
            "  have _ground : problem_spec_checkFilterable (Expr.mk false false [])\n"
            "      (implementation_checkFilterable (Expr.mk false false [])) := by\n"
            "    unfold problem_spec_checkFilterable\n"
            "    decide\n"
            + _CORRECT_BODY,
        ),
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground input — a plain "
            "value that is NOT a query expression (`isQueryExpr = false`) yet is "
            "marked non-admissible (`filterable = false`) with no children — where "
            "the fixed behavior must ACCEPT (result `false`), by `decide`; then the "
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
    # refutation witness pinning the violation at one concrete `Expr` literal.
    # =====================================================================
    {
        "id": "weak-prepatch-drop-queryexpr-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_NODE, _DROP_CONJUNCT),
        "refinement": (
            "this is the literal pre-fix guard: reject whenever the value is marked "
            "non-admissible, WITHOUT first checking that it is a genuine query "
            "expression. On the F2P input a plain stored value that merely owns a "
            "like-named admissibility marker set falsey is rejected, so the query "
            "that filters on it wrongly raises the disallowed-in-filter error and "
            "the F2P observable (that value being usable in a filter clause) FAILS. "
            "The faithful real patch is exactly the pre-patch code; it does NOT "
            "resolve — a verifying rival here is a true verify⇏resolve break."
        ),
        "rationale": (
            "REJECT from `result = raises e`: dropping the query-expression conjunct "
            "rejects on `!f` alone, so at `q = false`, `f = false` (a plain value "
            "marked non-admissible, no children) the rival returns `true` where "
            "`raises` requires `false`. Attacks the OWN-ACCOUNT two-conjunct leg, "
            "specifically the `q` conjunct. Refuted at `isQueryExpr = false`, "
            "`filterable = false`, `children = []`."
        ),
        "witness": (
            "-- A plain value (not a query expression) marked non-admissible must be\n"
            "-- ACCEPTED: `raises` needs the query-expression conjunct, which this\n"
            "-- input fails. The prepatch guard wrongly rejects it.\n"
            "example : ¬ problem_spec_checkFilterable (Expr.mk false false [])\n"
            "    (implementation_checkFilterable (Expr.mk false false [])) := by\n"
            "  unfold problem_spec_checkFilterable\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-widen-conjunction-to-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_NODE, _WIDEN_TO_OR),
        "refinement": (
            "widening the own-account guard from `q && !f` to `q || !f` rejects "
            "EVERY query expression (even an admissible one) and every non-admissible "
            "plain value. The faithful real patch (reject on being a query "
            "expression OR being non-admissible) breaks the many pre-existing "
            "queries that legitimately filter on admissible query expressions, and "
            "also over-rejects the plain-value case, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = raises e`: the disjunction rejects a permitted "
            "query expression `q = true`, `f = true` (admissible, no children), "
            "where `raises` requires `false`. Attacks the OWN-ACCOUNT leg by "
            "widening the conjunction. Refuted at `isQueryExpr = true`, "
            "`filterable = true`, `children = []` — varying both facets to `true`, "
            "off the values the drop-conjunct rival uses."
        ),
        "witness": (
            "-- An admissible query expression must be ACCEPTED: `raises` is\n"
            "-- `q && !f = true && !true = false`. The widened `q || !f = true`\n"
            "-- wrongly rejects it.\n"
            "example : ¬ problem_spec_checkFilterable (Expr.mk true true [])\n"
            "    (implementation_checkFilterable (Expr.mk true true [])) := by\n"
            "  unfold problem_spec_checkFilterable\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-recursion-skip-children",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_NODE, _DROP_RECURSION),
        "refinement": (
            "checking the node on its own account but never recursing into the "
            "nested source sub-expressions is the tree-carrier analogue of an "
            "off-by-one that leaves a visited operand unscreened: a disallowed "
            "query expression appearing as a nested sub-expression is missed, and a "
            "compound value gold rejects is accepted. That diverges from gold on the "
            "disallowed-nested-expression rejection the graded suite pins "
            "(test_ticket8439-style rejection of a disallowed expression), so it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = raises e`: with recursion dropped, at a clean "
            "root (`q = false`, `f = true`) carrying one disallowed child "
            "(`q = true`, `f = false`) the rival returns `false` where `raises` "
            "requires `true` (the child warrants rejection). Attacks the RECURSIVE "
            "PROPAGATION leg. Refuted at `children` NON-EMPTY, so that facet is not "
            "probed only at the empty list."
        ),
        "witness": (
            "-- A clean root with a disallowed nested sub-expression must be\n"
            "-- REJECTED: `raisesAny` propagates from the child. Dropping the\n"
            "-- recursion misses it.\n"
            "example : ¬ problem_spec_checkFilterable (Expr.mk false true [Expr.mk true false []])\n"
            "    (implementation_checkFilterable (Expr.mk false true [Expr.mk true false []])) := by\n"
            "  unfold problem_spec_checkFilterable\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-skip-self-only-recurse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_NODE, _SKIP_SELF),
        "refinement": (
            "recursing into the nested sub-expressions but never checking the value "
            "on its own account is the tree-carrier analogue of screening only the "
            "sub-operands and skipping the top-level operand: a disallowed candidate "
            "supplied directly (at the root) is let through. That diverges from gold "
            "on the root-level disallowed-expression rejection, so the faithful real "
            "patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = raises e`: skipping the own-account check, at a "
            "disallowed root (`q = true`, `f = false`, no children) the rival "
            "returns `false` (empty `raisesAny`) where `raises` requires `true`. "
            "Attacks the OWN-ACCOUNT leg from the opposite side of the drop-conjunct "
            "rival (own check omitted entirely). Refuted at `isQueryExpr = true`, "
            "`filterable = false`, `children = []`."
        ),
        "witness": (
            "-- A disallowed query expression at the root must be REJECTED on its own\n"
            "-- account: `raises` is `true && !false = true`. Recursing only into an\n"
            "-- empty child list wrongly accepts it.\n"
            "example : ¬ problem_spec_checkFilterable (Expr.mk true false [])\n"
            "    (implementation_checkFilterable (Expr.mk true false [])) := by\n"
            "  unfold problem_spec_checkFilterable\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references (mapping.md: no unchanged
# external callee whose behavior the proof must assume). The modeled behavior is
# a total structural fold over the carrier's own facets, so there is no in-model
# axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
