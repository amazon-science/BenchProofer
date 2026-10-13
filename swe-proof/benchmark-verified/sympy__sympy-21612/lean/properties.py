# properties.py — G-PBT falsification battery for sympy__sympy-21612 (lean).
#
# PORTED from the nagini sibling (nagini/properties.py), re-expressed against the
# Lean carrier. The modeled surface here is the purely functional bracketing
# decision for ONE denominator factor:
#
#   problem_spec_printDenominatorFactor render base cnt isProduct isPower result :=
#     result = (if needsBrackets cnt isProduct isPower
#               then "(" ++ render base ++ ")" else render base)
#   needsBrackets cnt isProduct isPower := cnt ≠ 1 ∧ (isProduct = true ∨ isPower = true)
#
# Input binders of the spec predicate: `baseComponentCount : Nat`,
# `baseIsProduct : Bool`, `baseIsPower : Bool` (and the universally-quantified
# `render`/`base`, whose result is pinned to `render base` on both branches).
# The single obligation is `theorem correct_printDenominatorFactor`.
#
# Region-surgery (_swap on _BASE) edits ONLY inside the impl region (and, for the
# soundness positive, the proof body), so `same_spec` holds by construction and
# every rejection/verification is attributable to the spec, never a touched
# postcondition.
from pathlib import Path

INSTANCE = "sympy__sympy-21612"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchor: the per-factor decision line, strictly inside the impl region. Editing
# only this keeps the frozen spec verbatim, so same_spec holds and any rejection
# is attributable to the impl change alone.
# ---------------------------------------------------------------------------
_DECISION = (
    "  let needParen := baseComponentCount ≠ 1 ∧ "
    "(baseIsProduct = true ∨ baseIsPower = true)\n"
)

# The frozen proof body (reused unchanged by every reject variant — the proof
# will fail to build for them, which is why each ships a witness instead).
_PROOF = (
    "  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets\n"
    "  simp only [Id.run]\n"
    "  split <;> rfl\n"
)


# ===========================================================================
# (A) PARTIAL-DOMAIN — drop the power disjunct, keeping only the product test.
# This is the literal PRE-PATCH bracketing decision. Correct on every atomic /
# product-form / count-1 factor, WRONG only on a multi-component POWER factor
# (isPower = true, isProduct = false, count ≠ 1): the spec pins the result
# bracketed there, this impl leaves it bare.
# ===========================================================================
_partial_product_only = _swap(
    _BASE,
    _DECISION,
    "  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true)\n",
)

# ===========================================================================
# (B) OVER-WIDE — bracket whenever the component count ≠ 1, ignoring whether the
# base is a compound product/power at all. This attacks the second top-level
# conjunct `(isProduct ∨ isPower)`: on a multi-component base that is NEITHER a
# product NOR a power (both flags false), the spec leaves it bare but this impl
# brackets it. Faithful real-patch analogue: a widened structural test that also
# brackets a denominator base of an unrelated kind the gold guard leaves bare;
# the existing rendering assertions for those bases would then mismatch, so it
# does NOT resolve.
# ===========================================================================
_partial_overwide = _swap(
    _BASE,
    _DECISION,
    "  let needParen := baseComponentCount ≠ 1\n",
)

# ===========================================================================
# (C) PART-COUNT MASK — replace `count ≠ 1` with `count ≠ 0`. Agrees with the
# spec on every multi-component reciprocal (the common case) but FLIPS on a
# single-component compound (count = 1, isProduct/isPower true): the spec leaves
# it bare, this brackets it. Attacks the `baseComponentCount ≠ 1` conjunct at
# its exact boundary.
# ===========================================================================
_partcount_mask = _swap(
    _BASE,
    _DECISION,
    "  let needParen := baseComponentCount ≠ 0 ∧ "
    "(baseIsProduct = true ∨ baseIsPower = true)\n",
)

# ===========================================================================
# (D) CONSTANT-FALSE cheapest-wrong — never bracket anything. Trivially correct
# on factors that genuinely need no brackets; WRONG on every factor the spec
# pins bracketed. The result-shape (a String either way) is preserved, so only
# the value pin catches it.
# ===========================================================================
_const_false = _swap(
    _BASE,
    _DECISION,
    "  let needParen : Prop := False\n",
)

# ===========================================================================
# (E) SOUNDNESS positive — structurally DIFFERENT but CORRECT: the two top-level
# conjuncts of the decision are COMMUTED (`(isProduct ∨ isPower) ∧ count ≠ 1`).
# Observationally equal to gold, so it MUST verify; the proof commutes the
# conjunction (`and_comm`) before splitting. If a faithful correct impl of this
# shape could not verify, the postcondition would be SPEC-TOO-STRONG. The frozen
# `theorem correct_printDenominatorFactor` STATEMENT is byte-identical; only the
# impl decision expression and the tactic body change.
# ===========================================================================
_pos_ctrl = _swap(
    _BASE,
    _DECISION,
    "  let needParen := (baseIsProduct = true ∨ baseIsPower = true) ∧ "
    "baseComponentCount ≠ 1\n",
)
# ===========================================================================
# (F) FRAGMENT-CONTENT / frame-discipline — replace the inner fragment
# `render base` with a constant string, keeping the bracketing decision intact.
# The spec pins the result CONTENT to `render base` (wrapped or not); a rival
# that emits anything else violates the equality regardless of the decision.
# This is the only rival that attacks the fragment-content clause rather than
# the `needsBrackets` predicate, so its witness is also the only one that VARIES
# the `render` and `base` binders.
# ===========================================================================
_frag_const = _swap(
    _BASE,
    "  let baseStr := render base\n",
    '  let baseStr := "?"\n',
)


_pos_ctrl = _swap(
    _pos_ctrl,
    _PROOF,
    "  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets\n"
    "  simp only [Id.run, and_comm]\n"
    "  split <;> rfl\n",
)

# ===========================================================================
# (G) COUNT-ZERO BOUNDARY — `2 ≤ count` in place of `count ≠ 1`. Agrees with the
# spec on every count ≥ 2 and on count = 1, and FLIPS only at count = 0: the spec
# brackets a zero-component compound base (0 ≠ 1 holds), this impl leaves it
# bare. The `≠ 1` guard has TWO sides and the battery's other count rival
# (`partcount-mask`) only probes the count = 1 side, so count = 0 was an
# unattacked point of the same conjunct.
# ===========================================================================
_count_ge_two = _swap(
    _BASE,
    _DECISION,
    "  let needParen := 2 ≤ baseComponentCount ∧ "
    "(baseIsProduct = true ∨ baseIsPower = true)\n",
)

# ===========================================================================
# (H) EXCLUSIVE-OR of the two structural flags. Agrees with the spec wherever at
# most one flag is set — which is every point the other rivals visit — and flips
# only where BOTH are true: the spec brackets (the disjunction holds), this impl
# leaves it bare. That both-flags-true corner is the one combination of the
# `(isProduct ∨ isPower)` conjunct no other case reaches, so it is what
# distinguishes an inclusive disjunction from an exclusive one.
# ===========================================================================
_xor_flags = _swap(
    _BASE,
    _DECISION,
    "  let needParen := baseComponentCount ≠ 1 ∧ "
    "((baseIsProduct ^^ baseIsPower) = true)\n",
)


# ===========================================================================
# (I) ADMISSIBILITY positive — the frozen obligation must be SATISFIABLE at
# concrete inputs of the shape the modeled decision actually meets, not merely
# provable as a universally-quantified statement. On a total carrier there is no
# precondition to be too strong, so the analogue of PRECOND-TOO-STRONG is the
# obligation being unsatisfiable at exactly such an input: a spec whose two
# branches were jointly unsatisfiable there (a pinned value no impl can produce,
# a decision predicate that is false at every point) would still let the
# universal statement be discharged vacuously in shape while pinning nothing
# reachable.
#
# So this case discharges the obligation AT four concrete input points BY
# EVALUATION first — one per cell of the decision table: a multi-component power
# base and a multi-component product base (both bracketed), a single-component
# base and a multi-component base that is neither (both bare) — each `have`
# pinning the produced string as well as the spec, and only THEN closes the
# frozen obligation verbatim. If any of those four points were unsatisfiable the
# `decide` would fail; the frozen tactic body is appended unchanged, so nothing
# about the positive weakens what is proven.
# ===========================================================================
def _admiss_have(name, cnt, prod, power, value):
    inp = f'(fun _ : Unit => "r") () {cnt} {prod} {power}'
    return (
        f"  have {name} : implementation_printDenominatorFactor {inp} = {value} ∧\n"
        f"      problem_spec_printDenominatorFactor {inp}\n"
        f"        (implementation_printDenominatorFactor {inp}) := by\n"
        "    unfold problem_spec_printDenominatorFactor "
        "implementation_printDenominatorFactor needsBrackets\n"
        "    exact ⟨by decide, by decide⟩\n"
    )


_admiss = _swap(
    _BASE,
    _PROOF,
    _admiss_have("hPowerBase", 2, "false", "true", '"(r)"')
    + _admiss_have("hProductBase", 2, "true", "false", '"(r)"')
    + _admiss_have("hSingleComponent", 1, "true", "false", '"r"')
    + _admiss_have("hPlainBase", 2, "false", "false", '"r"')
    + _PROOF,
)


def _witness(cnt, prod, power):
    """A refutation stated at one concrete input: the rival's result differs
    from the spec value there. Elaborates against the rival (`decide` closes the
    inequality), fails against gold (the spec holds of gold at every input)."""
    inp = f'(fun _ : Unit => "r") () {cnt} {prod} {power}'
    return (
        "example : ¬ problem_spec_printDenominatorFactor\n"
        f"    {inp}\n"
        f"    (implementation_printDenominatorFactor {inp}) := by\n"
        "  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets\n"
        "  decide\n"
    )


SPEC_TESTS = [
    {
        "id": "partial-product-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_product_only,
        "rationale": (
            "Rejection comes from the postcondition equality. Dropping the power "
            "disjunct leaves the decision `count ≠ 1 ∧ isProduct`; on a "
            "multi-component power factor (baseComponentCount = 2, baseIsProduct "
            "= false, baseIsPower = true) `needsBrackets` is true so the spec "
            "pins the bracketed string, but this impl yields the bare fragment. "
            "Attacks the `isPower` half of the second conjunct."
        ),
        "refinement": (
            "This is exactly the pre-patch behavior: the widening from a "
            "product-only structural test to product-or-power is the fix itself, "
            "so a faithful real patch of this shape renders the reported "
            "power-in-denominator case bare instead of bracketed and the F2P "
            "rendering assertion fails — it does NOT resolve."
        ),
        "witness": _witness(2, "false", "true"),
    },
    {
        "id": "partial-overwide-clause",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_overwide,
        "rationale": (
            "Rejection from the postcondition. Dropping the whole "
            "`(isProduct ∨ isPower)` conjunct brackets on count alone; at "
            "baseComponentCount = 2, baseIsProduct = false, baseIsPower = false "
            "`needsBrackets` is false so the spec pins the bare fragment, but "
            "this impl brackets it. Attacks the second top-level conjunct in the "
            "opposite direction from (A), and is the only rival probing a factor "
            "that is neither a product nor a power."
        ),
        "refinement": (
            "The faithful real-patch analogue over-widens the structural test to "
            "also bracket a denominator base of a kind the gold guard leaves "
            "bare; the existing rendering assertions for those bases would then "
            "mismatch, so it does NOT resolve."
        ),
        "witness": _witness(2, "false", "false"),
    },
    {
        "id": "partcount-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partcount_mask,
        "rationale": (
            "Rejection from the postcondition. `count ≠ 0` in place of "
            "`count ≠ 1` flips exactly at count = 1: at baseComponentCount = 1, "
            "baseIsProduct = true, baseIsPower = false the spec pins the bare "
            "fragment (a single-component base is left un-bracketed) but this "
            "impl brackets it. Attacks the `baseComponentCount ≠ 1` conjunct at "
            "its boundary — the only rival probing count = 1."
        ),
        "refinement": (
            "The faithful real correspondent drops the component-count guard, so "
            "a single-component product/power base would be bracketed where the "
            "gold guard leaves it bare; the single-component invariants the F2P "
            "suite pins would mismatch, so it does NOT resolve."
        ),
        "witness": _witness(1, "true", "false"),
    },
    {
        "id": "const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _const_false,
        "rationale": (
            "Rejection from the postcondition. Never bracketing ignores every "
            "binder; at baseComponentCount = 2, baseIsProduct = true, "
            "baseIsPower = false the spec pins the bracketed string but this "
            "impl yields the bare fragment. The result is a String either way, "
            "so the value pin (not any shape check) is what catches it."
        ),
        "refinement": (
            "Corresponds to deleting the extra-bracket collection entirely, so "
            "every compound denominator renders bare — both the reported case "
            "and the multi-component product regressions the F2P suite pins. It "
            "does NOT resolve."
        ),
        "witness": _witness(2, "true", "false"),
    },
    {
        "id": "fragment-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frag_const,
        "rationale": (
            "Rejection from the postcondition's frame-discipline clause: the "
            "result CONTENT is pinned to `render base` (bracketed or bare). "
            "Emitting a constant fragment violates the equality at "
            "render = (fun s => s), base = \"z\", baseComponentCount = 1 "
            "(needsBrackets false, so the spec pins exactly `render base` = "
            "\"z\") — this impl yields the constant. This is the only rival that "
            "varies the `render`/`base` binders, so it is what discriminates the "
            "fragment-content clause the other four leave fixed."
        ),
        "refinement": (
            "A faithful real patch that stops splicing the base's own rendered "
            "fragment (emitting some fixed text instead of the sub-expression) "
            "would render every such denominator with the wrong content and fail "
            "every rendering assertion in the F2P suite, so it does NOT resolve."
        ),
        "witness": (
            "example : ¬ problem_spec_printDenominatorFactor\n"
            '    (fun s : String => s) "z" 1 true false\n'
            "    (implementation_printDenominatorFactor "
            '(fun s : String => s) "z" 1 true false) := by\n'
            "  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets\n"
            "  decide\n"
        ),
    },
    {
        "id": "count-zero-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _count_ge_two,
        "rationale": (
            "Rejection from the postcondition. `2 ≤ count` agrees with "
            "`count ≠ 1` on count = 1 and on every count ≥ 2, so it flips at "
            "exactly one point: at baseComponentCount = 0, baseIsProduct = "
            "true, baseIsPower = false the spec pins the bracketed string "
            "(0 ≠ 1 holds, and the product flag is set) but this impl yields "
            "the bare fragment. The `≠ 1` guard has two sides and the other "
            "count rival (`partcount-mask`) only attacks the count = 1 side, "
            "so this is the sole case reaching count = 0."
        ),
        "refinement": (
            "The faithful real correspondent replaces the component-count "
            "inequality with a lower-bound test, so a compound denominator base "
            "carrying no components is spliced in bare where the gold guard "
            "brackets it; the rendering assertions for those bases mismatch, so "
            "it does NOT resolve."
        ),
        "witness": _witness(0, "true", "false"),
    },
    {
        "id": "xor-structural-flags",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _xor_flags,
        "rationale": (
            "Rejection from the postcondition. Reading the two structural flags "
            "exclusively instead of inclusively agrees with the spec wherever at "
            "most one flag is set — which covers every point the other rivals "
            "visit — and flips only where both are set: at baseComponentCount = "
            "2, baseIsProduct = true, baseIsPower = true the spec brackets (the "
            "disjunction holds) but this impl leaves the fragment bare. That "
            "corner is the one cell of `(isProduct ∨ isPower)` no other case "
            "reaches, so it is what pins the disjunction as inclusive."
        ),
        "refinement": (
            "The faithful real correspondent tests the two structural kinds "
            "exclusively rather than as a membership test, so a denominator base "
            "answering to both kinds renders bare where the gold guard brackets "
            "it and the corresponding rendering assertion fails: it does NOT "
            "resolve."
        ),
        "witness": _witness(2, "true", "true"),
    },
    {
        "id": "admiss-obligation-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "The frozen obligation must be SATISFIABLE at concrete inputs of the "
            "shape the modeled decision actually meets, not merely dischargeable "
            "as a universal statement. This carrier is total, so there is no "
            "precondition to be too strong; the analogue is the obligation being "
            "unsatisfiable at exactly such an input, which this case tests "
            "directly by discharging it AT four concrete points BY EVALUATION — "
            "one per cell of the decision table: a multi-component power base and "
            "a multi-component product base (both pinned to the bracketed "
            "string), a single-component base and a multi-component base that is "
            "neither kind (both pinned bare). Each `have` pins the produced value "
            "as well as the spec, so an unsatisfiable point would fail `decide`; "
            "the frozen tactic body then closes the obligation verbatim, so "
            "nothing proven is weakened. If any of the four could not be "
            "discharged the spec would be PRECOND-TOO-STRONG in its total-carrier "
            "form."
        ),
    },
    {
        "id": "pos-control-commute",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl,
        "rationale": (
            "A structurally-different but CORRECT impl: the two top-level "
            "conjuncts of the bracketing decision are commuted "
            "(`(isProduct ∨ isPower) ∧ count ≠ 1`), which is provably equal to "
            "the frozen decision, so `correct_printDenominatorFactor` still "
            "discharges (the proof commutes the conjunction with `and_comm` "
            "before the branch split). It MUST verify; if it cannot, the "
            "postcondition is SPEC-TOO-STRONG. Equivalent-expression reshape "
            "only — the theorem STATEMENT is byte-identical."
        ),
    },
]
