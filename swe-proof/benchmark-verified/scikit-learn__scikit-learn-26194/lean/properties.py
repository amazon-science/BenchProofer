# properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-26194 (lean).
#
# Ported from the nagini sibling battery. The modeled surface here is the purely
# functional core: one obligation `correct_rocCurveThresholds` over the frozen
# spec `problem_spec_rocCurveThresholds ts result := result = <sentinel> :: ts.map <finite>`.
#
# Defended surface: the returned threshold vector is the positive-infinity
# sentinel followed, in order, by the finite score thresholds `ts` (each wrapped
# by the finite constructor). The single equality decomposes into three
# independent top-level clauses:
#   (H) the leading entry is the sentinel constructor (not a finite value);
#   (L) the tail has exactly `ts.length` entries;
#   (T) each tail entry equals the corresponding input threshold, in order.
#
# Only the impl region is edited by each variant (via _swap), so markers.same_spec
# holds by construction and every `theorem correct_rocCurveThresholds` keeps a
# byte-identical statement; only impl bytes differ. The frozen proof body is a
# bare `rfl`, tuned to the frozen impl's syntactic form — so a merely RESHAPED
# impl already breaks `rfl` identically to a WRONG one. Every reject case
# therefore ships a `witness` that has been SEEN to discriminate: it elaborates
# against the rival and fails against the frozen solution.
#
# Single input binder: `ts : List ℚ`. Reject witnesses probe six distinct points
# ([1,0], [2,1], [3,2], [5], [], [4,1]) so the battery exercises the spec's
# dependence on the binder rather than refuting every rival at one input. The
# empty list is included deliberately: the obligation is TOTAL over `ts`, so a
# rival free to return anything at `[]` is a real gap the other points miss.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-26194"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1. FINITE-LEAD (the pre-patch behaviour, restated as a uniqueness rival).
#    Leads with a FINITE value (headD + 1) instead of the sentinel constructor.
#    Attacks clause (H): the head must be the sentinel, and a finite constructor
#    can never equal it. This is exactly the defect the gold change removes.
# ---------------------------------------------------------------------------
_finite_lead = _swap(
    _BASE,
    "  out := Thr.posInf :: out",
    "  out := Thr.finite (ts.headD 0 + 1) :: out",
)


# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN (drop the first tail element). Copies from index 1, so the
#    largest finite threshold is skipped. Attacks clauses (L) and (T): the tail
#    is shorter by one and misaligned.
# ---------------------------------------------------------------------------
_drop_first = _swap(
    _BASE,
    "  let mut out := ts.map Thr.finite",
    "  let mut out := (ts.drop 1).map Thr.finite",
)


# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN (last tail element corrupted to a constant). Structure and
#    length intact, but the final entry is planted as a fixed finite value.
#    Attacks clause (T): one tail entry diverges from the input threshold.
#    The planted constant is deliberately NOT 0: the observable score tails this
#    routine is exercised on end at the smallest score, which is commonly 0, so
#    a planted 0 would be a value the downstream observation cannot see. A
#    constant outside the score range keeps the near-miss observable.
# ---------------------------------------------------------------------------
_last_wrong = _swap(
    _BASE,
    "  out := Thr.posInf :: out\n  return out",
    "  out := out.set (out.length - 1) (Thr.finite 99)\n  out := Thr.posInf :: out\n  return out",
)


# ---------------------------------------------------------------------------
# 4. NO-PREPEND (return the finite thresholds unchanged, length n not n+1).
#    Attacks clauses (H) and (L): no sentinel is prepended and the length is one
#    short.
# ---------------------------------------------------------------------------
_no_prepend = _swap(
    _BASE,
    "  out := Thr.posInf :: out\n  return out",
    "  return out",
)


# ---------------------------------------------------------------------------
# 5. EMPTY-INPUT SLACK (totality probe). Correct on every non-empty input and
#    wrong ONLY at `ts = []`, where it returns the empty vector instead of the
#    lone sentinel. The obligation is TOTAL over `ts : List ℚ` (no non-emptiness
#    hypothesis), so this is the one rival the other four cannot catch: each of
#    them is refuted at a non-empty point, and a rival free to do anything at
#    `[]` would slip past all of them. Attacks clauses (H) and (L) at the single
#    input the rest of the battery never reaches.
# ---------------------------------------------------------------------------
_empty_slack = _swap(
    _BASE,
    "  return out",
    "  if ts.isEmpty then\n    return []\n  return out",
)


# ---------------------------------------------------------------------------
# 6. TAIL ORDER REVERSED. Length and head are correct and the tail is even the
#    right MULTISET of thresholds — only the order is wrong. Attacks clause (T)
#    alone, isolated from (H) and (L), which no other rival does: cases 2 and 3
#    also perturb length or a value, so this is what pins that the spec fixes
#    the ORDER of the tail and not merely its contents.
# ---------------------------------------------------------------------------
_tail_reversed = _swap(
    _BASE,
    "  let mut out := ts.map Thr.finite",
    "  let mut out := (ts.map Thr.finite).reverse",
)


# ---------------------------------------------------------------------------
# 7. POSITIVE CONTROL (soundness): structurally different but CORRECT impl.
#    Bind the sentinel to a local `let` first, then prepend it. Same forward
#    construction, so the frozen proof still closes. MUST VERIFY.
# ---------------------------------------------------------------------------
_reordered = _swap(
    _BASE,
    "  let mut out := ts.map Thr.finite\n  out := Thr.posInf :: out\n  return out",
    "  let lead := Thr.posInf\n  let mut out := ts.map Thr.finite\n  out := lead :: out\n  return out",
)


# ---------------------------------------------------------------------------
# 8. POSITIVE CONTROL (cheapest honest impl). Drop the `Id.run do` scaffold and
#    the mutable temporary; construct the vector directly with `::`. A correct
#    minimal impl that does the genuine work. MUST VERIFY.
# ---------------------------------------------------------------------------
_cheapest = _swap(
    _BASE,
    "def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do\n"
    "  let mut out := ts.map Thr.finite\n"
    "  out := Thr.posInf :: out\n"
    "  return out",
    "def implementation_rocCurveThresholds (ts : List ℚ) : List Thr :=\n"
    "  Thr.posInf :: ts.map Thr.finite",
)


# ---------------------------------------------------------------------------
# 9. POSITIVE CONTROL (soundness) whose proof is NOT `rfl`. Both positives above
#    are definitionally equal to the frozen impl, so the frozen `rfl` closes them
#    unchanged — honest, but it means neither tests whether the spec admits an
#    impl that is only PROPOSITIONALLY equal. This one builds the tail by `foldr`
#    instead of `map`: extensionally the same vector, but not definitionally, so
#    `rfl` no longer closes and the proof is a real induction on `ts`. If the spec
#    rejected this it would be SPEC-TOO-STRONG in the way that actually matters —
#    pinning a construction rather than a result. Reproves inside the proof
#    region, which variant_scope permits (the STATEMENT is byte-identical).
# ---------------------------------------------------------------------------
_foldr_tail = _swap(
    _BASE,
    "def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do\n"
    "  let mut out := ts.map Thr.finite\n"
    "  out := Thr.posInf :: out\n"
    "  return out",
    "def implementation_rocCurveThresholds (ts : List ℚ) : List Thr :=\n"
    "  Thr.posInf :: ts.foldr (fun q acc => Thr.finite q :: acc) []",
)
_foldr_tail = _swap(
    _foldr_tail,
    "  intro ts\n"
    "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
    "  rfl",
    "  intro ts\n"
    "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
    "  induction ts with\n"
    "  | nil => rfl\n"
    "  | cons q qs ih =>\n"
    "    simp only [List.foldr_cons, List.map_cons, List.cons.injEq, true_and] at *\n"
    "    exact ih",
)


# ---------------------------------------------------------------------------
# 10. ADMISSIBILITY at an observation-shaped input. The nagini sibling carried an
#     admissibility case (a self-call establishing the precondition on a normal
#     descending threshold tail). It would have been easy to record that lane as
#     inexpressible here, since this obligation has NO precondition to be too
#     strong — but the lane's real question survives the difference: is the spec
#     SATISFIABLE at a concrete observation-shaped input, or has it been stated so
#     that nothing can meet it? A postcondition can be unsatisfiable at a reachable
#     input all by itself, and that failure is invisible to both other lanes (a
#     uniqueness rival is refuted at such a point too, and a positive control is
#     only ever checked against the same universally-quantified obligation).
#     So the lane is landed, not dropped: discharge the spec at a descending tail
#     of the shape the routine is actually observed on, against the vector the
#     spec demands. Lives in the impl region as a `have`, so no new top-level
#     theorem is introduced and variant_scope is satisfied. MUST VERIFY.
# ---------------------------------------------------------------------------
_admissible = _swap(
    _BASE,
    "def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do",
    "def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do\n"
    "  have _admissible :\n"
    "      problem_spec_rocCurveThresholds [1, 7/10, 0]\n"
    "        (Thr.posInf :: ([1, 7/10, 0] : List ℚ).map Thr.finite) := by\n"
    "    unfold problem_spec_rocCurveThresholds\n"
    "    rfl",
)


SPEC_TESTS = [
    {
        "id": "finite-lead-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _finite_lead,
        "rationale": (
            "Rejection from the leading-entry clause (H): the spec fixes the head "
            "to the sentinel constructor, and a finite constructor value can never "
            "equal it. The rival leads with a finite value derived from the input."
        ),
        "refinement": (
            "This IS the pre-patch behaviour: the leading position is a finite "
            "value (largest score + 1) rather than the +inf sentinel. The F2P "
            "regression test asserts the leading threshold is infinite; a finite "
            "lead makes that False, so a faithful real patch keeping this behaviour "
            "would NOT resolve. A verifying rival here would be a "
            "verify-does-not-resolve break."
        ),
        "witness": (
            "example : ¬ problem_spec_rocCurveThresholds [1, 0]\n"
            "    (implementation_rocCurveThresholds [1, 0]) := by\n"
            "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
            "  decide"
        ),
    },
    {
        "id": "partial-domain-drop-first-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop_first,
        "rationale": (
            "Rejection from the length clause (L) AND the tail-alignment clause "
            "(T): mapping over the input with its first element dropped yields a "
            "tail one element short and misaligned with the input thresholds."
        ),
        "refinement": (
            "Dropping the first (largest) finite threshold produces a tail that is "
            "one entry short. The F2P exact-array assertion on the full threshold "
            "vector would see the shorter/misaligned tail and fail, so a faithful "
            "real patch would NOT resolve."
        ),
        "witness": (
            "example : ¬ problem_spec_rocCurveThresholds [2, 1]\n"
            "    (implementation_rocCurveThresholds [2, 1]) := by\n"
            "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
            "  decide"
        ),
    },
    {
        "id": "partial-domain-last-element-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _last_wrong,
        "rationale": (
            "Rejection from the tail-alignment clause (T): the final tail entry is "
            "overwritten with a fixed finite value, so it no longer equals the "
            "corresponding input threshold. Length and head are intact — a "
            "value-level near-miss, refuted at an input whose last threshold "
            "differs from the planted constant so the corruption is observable."
        ),
        "refinement": (
            "Planting a constant for the final (smallest) threshold gives a tail "
            "that diverges at the last index. The exact-array observation on the "
            "returned vector reads every tail index, so a faithful real patch "
            "carrying this defect would report the planted value where the input "
            "score belongs and would NOT resolve. Note the constant matters: the "
            "score tails this routine is observed on end at the smallest score, "
            "which is frequently 0, so a planted 0 would sit exactly where the "
            "observation already expects 0 and the near-miss would be invisible "
            "downstream while still being refuted on this carrier. The constant "
            "here is outside the score range, so the divergence is real in both "
            "places."
        ),
        "witness": (
            "example : ¬ problem_spec_rocCurveThresholds [3, 2]\n"
            "    (implementation_rocCurveThresholds [3, 2]) := by\n"
            "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
            "  decide"
        ),
    },
    {
        "id": "no-prepend-length-n",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_prepend,
        "rationale": (
            "Rejection from the head clause (H) and the length clause (L): with no "
            "sentinel prepended, the result has n entries (not n+1) and its head is "
            "a finite value rather than the sentinel. Cheap supporting near-miss, "
            "but with a real refinement."
        ),
        "refinement": (
            "Omitting the leading entry returns the curve un-anchored (n entries, "
            "not n+1) with a finite leading threshold; both F2P observations (the "
            "exact array AND the infinite-leading-threshold assertion) fail, so a "
            "faithful real patch would NOT resolve."
        ),
        "witness": (
            "example : ¬ problem_spec_rocCurveThresholds [5]\n"
            "    (implementation_rocCurveThresholds [5]) := by\n"
            "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
            "  decide"
        ),
    },
    {
        "id": "empty-input-slack",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _empty_slack,
        "rationale": (
            "Rejection from clauses (H) and (L) at the empty input: the obligation "
            "is total over `ts`, so the spec pins the result at `[]` to the lone "
            "sentinel, and this rival returns the empty vector there. Correct on "
            "every non-empty input, so the four near-misses above — all refuted at "
            "non-empty points — cannot catch it; this case is what removes the "
            "partial-domain slack a total theorem would otherwise leave."
        ),
        "refinement": (
            "Stated precisely, because this case's justification is NOT an "
            "observable-test one: upstream always yields at least one threshold, "
            "so the empty input is not reachable in the real routine and a patch "
            "carrying this defect would still pass the observable tests. What this "
            "case defends is the TOTALITY of the obligation, which is quantified "
            "over all of `List ℚ` with no non-emptiness hypothesis. The modeled "
            "construction is itself total — prepending the sentinel to an empty "
            "threshold vector yields the one-element vector holding just the "
            "sentinel — so demanding the right answer at `[]` over-strengthens "
            "nothing. Without this case the total theorem leaves a rival free to "
            "return anything at `[]` while still verifying, which is precisely the "
            "partial-domain slack a precondition would have introduced. The claim "
            "here is spec strength, not resolution."
        ),
        "witness": (
            "example : ¬ problem_spec_rocCurveThresholds ([] : List ℚ)\n"
            "    (implementation_rocCurveThresholds ([] : List ℚ)) := by\n"
            "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
            "  decide"
        ),
    },
    {
        "id": "tail-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tail_reversed,
        "rationale": (
            "Rejection from the tail-alignment clause (T) in isolation: the head is "
            "the sentinel, the length is exactly n+1, and the tail even carries the "
            "right multiset of thresholds — only the ORDER is wrong. Cases 2 and 3 "
            "each also perturb length or a value, so this is the case that pins "
            "that the spec fixes the tail's order and not just its contents."
        ),
        "refinement": (
            "The returned thresholds are documented and observed as DECREASING; "
            "reversing the tail makes them increasing after the leading position. "
            "The exact-array observation compares index by index, so an ascending "
            "tail diverges at the first index for any input with two distinct "
            "thresholds, and a faithful real patch would NOT resolve. Note that on "
            "a one-element tail this rival agrees with the spec, which is why the "
            "witness is stated at a two-element input."
        ),
        "witness": (
            "example : ¬ problem_spec_rocCurveThresholds [4, 1]\n"
            "    (implementation_rocCurveThresholds [4, 1]) := by\n"
            "  unfold problem_spec_rocCurveThresholds implementation_rocCurveThresholds\n"
            "  decide"
        ),
    },
    {
        "id": "pos-control-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _reordered,
        "rationale": (
            "Structurally different (the sentinel is bound to a local before "
            "prepending) but behaviourally identical correct impl; the frozen proof "
            "still closes. MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-cheapest-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _cheapest,
        "rationale": (
            "Cheapest honest impl: drop the imperative scaffold and construct the "
            "vector directly. Genuinely does the work (prepends the sentinel to the "
            "mapped input). Frozen proof closes unchanged. MUST verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-foldr-tail-nonrfl",
        "kind": "soundness",
        "expect": "verify",
        "module": _foldr_tail,
        "rationale": (
            "The load-bearing positive: builds the tail by `foldr` rather than "
            "`map`, so it is only PROPOSITIONALLY equal to the frozen impl, not "
            "definitionally — the frozen `rfl` no longer closes and the proof is a "
            "real induction on `ts`. The other two positives are definitionally "
            "equal to the frozen impl, so they would verify even under a spec that "
            "pinned the construction rather than the result; this one would not. "
            "MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-observation-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admissible,
        "rationale": (
            "This obligation carries no precondition, so PRECOND-TOO-STRONG in its "
            "literal form is unreachable — but the lane's question is not. The case "
            "discharges the spec at a concrete descending threshold tail of the "
            "shape the routine is observed on, confirming the postcondition is "
            "SATISFIABLE at a reachable input rather than stated so that nothing "
            "meets it. That failure mode is invisible to the other two lanes: a "
            "uniqueness rival is refuted at an unsatisfiable point too, and the "
            "positives only ever re-check the same quantified obligation. MUST "
            "verify, else the spec is unsatisfiable where it must hold."
        ),
    },
]
