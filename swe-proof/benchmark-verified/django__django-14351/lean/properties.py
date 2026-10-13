"""properties.py — G-PBT falsification battery for django__django-14351 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_membershipGroupColumns``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate). Grouping-key
columns are collected for a membership condition whose right-hand side may be a
nested query. The result is a PAIR: the collected column list (``result.1``) and
the resulting nested-query state (``result.2``). The behavior is pinned by a
two-way dispatch on the optional rhs:

  problem_spec_membershipGroupColumns (lhsCols) (rhs) (result) : Prop
    match rhs with
    | none   => result.1 = lhsCols ∧ result.2 = none
    | some q => result.1 = lhsCols ++ q.groupKeys ∧
                result.2 = some (if q.explicitlySelected then q else normalizeRhs q)

``normalizeRhs`` is a TRANSPARENT frozen pure helper (part of the spec view): it
reduces an implicitly-selected nested query to its single identity column
(``selected := [identityColumn]``, ``explicitlySelected := true``); everything on
this carrier is a concrete ``Nat``/``Bool``/``List``/``structure`` with
``DecidableEq``, so every witness ``decide``s directly with no opaque term to
condition on.

BINDER STRUCTURE (read this before judging binder/clause coverage). The spec has
two input binders — ``lhsCols : List Col`` and ``rhs : Option RhsSubquery`` — and
TWO independent top-level arms selected by ``rhs``, each with two conjuncts:

  * NONE arm (``rhs = none``): (a) ``result.1 = lhsCols`` (the lhs columns are
    returned verbatim) and (b) ``result.2 = none`` (no nested-query state is
    produced).
  * SOME arm (``rhs = some q``): (a) ``result.1 = lhsCols ++ q.groupKeys`` (the
    lhs columns first, then the query's grouping columns) and (b) ``result.2``
    is the query left ``some q`` when it already has an explicit selection, else
    the NORMALIZED query ``some (normalizeRhs q)`` — this last is the
    PRODUCED-BY post-state clause where the fix is observable.

All four conjuncts are attacked. ``lhsCols`` is varied across six distinct
values and ``rhs`` across all three shapes (``none``, ``some`` implicit,
``some`` explicit), so no binder is held fixed by every witness.

ADVERSARIAL READ of the nagini classes on this carrier (see the accounting block
at the bottom for the full sibling-case ledger):

  * FRAME / PERMISSION MUTATION — the PERMISSION MECHANISM is vacuous, the FRAME
    OBLIGATION is not. The nagini sibling holds ``lhs_cols`` and the read-only rhs
    facets at half-permission (``Acc(.,1/2)``) and its mandatory frame-mutation
    rivals WRITE through them, to be rejected for INSUFFICIENT PERMISSION. Lean is
    referentially transparent, so *that rejection mechanism* has no analogue: there
    is no heap, no aliasing, no permission to be short of. But the OBLIGATION those
    rivals carried — "the facets the normalization does not touch survive the call
    unchanged" — is a plain value obligation on ``result.2`` here, because the
    SOME-arm pins ``result.2`` to ``some q`` / ``some (normalizeRhs q)``, i.e. it
    pins ALL FIVE fields of the query state, not just the two ``normalizeRhs``
    writes. It is therefore expressible AND attackable, and is carried by three
    rivals below: unconditional-normalize (the ``selected``/``explicitlySelected``
    facets must be preserved on the already-explicit branch),
    clobber-readonly-rhs-facets (the ``defaultColumns``/``identityColumn`` facets —
    which NO clause of the spec's normalization writes — must survive on every
    some-branch), and fabricate-state-on-none-rhs (no state at all off the query
    branch).

  * ADMISSIBILITY — PORTED (``admiss-ground-implicit-rhs``). It is true that
    ``correct_membershipGroupColumns`` binds ``∀ lhsCols rhs`` with NO
    precondition hypothesis, but that alone does NOT make the lane vacuous: on a
    total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    discharges the obligation at that concrete input — by evaluation, as a
    ``have``, before closing the frozen obligation verbatim — tests directly. The
    case does that at the F2P shape (a nested rhs with no explicit selection
    carrying its model's full multi-column default set) and additionally pins the
    computed pair, so the post-image there is named rather than merely asserted.
    Verified with a real build.

  * DIVERGENCE / NON-TERMINATION — VACUOUS. ``implementation_membershipGroupColumns``
    is a total Lean ``def``; a diverging implementation cannot be written, so
    there is nothing to port (contrast velvet's ``partial`` known-hole).

  * UNGROUNDED-ORACLE ECHO — N/A. Every clause is grounded structurally in the
    inputs (``lhsCols``, ``q.groupKeys``, ``normalizeRhs q``); there is no opaque
    answer-key to echo.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen ``by_cases … <;> exact ⟨rfl, rfl⟩`` is
tuned to the frozen do-block), so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating the
spec predicate directly at one concrete input and ``decide``-ing its negation.
Each was checked with two real ``lake env lean`` builds to ELABORATE against its
rival and to FAIL against the frozen solution (so it discriminates rather than
asserting a tautology). No witness needs a hypothesis — the carrier is fully
concrete — so there is no consistency concern.

AXIOM lane: EMPTY. The changed behavior is modeled DEEPLY in the frozen pure
region (``normalizeRhs`` spelled out over the query-state structure); there is no
consumed axiom and no opaque callee for this gate to probe. ``AXIOM_TESTS`` is
therefore empty (the axiom lane is G-AX's job).
"""
from pathlib import Path

INSTANCE = "django__django-14351"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each unique inside Solution.lean and lying ENTIRELY within
# the `-- impl-start`/`-- impl-end` region (or, for the pos re-proof, the
# `-- proof-start`/`-- proof-end` region), so `same_spec` holds by construction.
# ---------------------------------------------------------------------------

# The two-line normalization block (the fix): discard the implicit selection,
# then select only the identity column. Guarded by `if !q.explicitlySelected`.
_NORM_BLOCK = (
    "      if !q.explicitlySelected then\n"
    "        -- discard the implicit selection …\n"
    "        q := { q with selected := [], explicitlySelected := false }\n"
    "        -- … then select only the identity column.\n"
    "        q := { q with selected := [q.identityColumn], explicitlySelected := true }\n"
)

# The `if` header alone (used to strip only the guard, leaving the body).
_NONE_RETURN = "  | none =>\n      return (cols, none)"
_APPEND_LINE = "      cols := cols ++ q.groupKeys\n"

# The whole gold impl def + gold proof body (used by the functional-reshape
# positive, which re-proves inside the proof region).
_GOLD_IMPL = (
    "def implementation_membershipGroupColumns\n"
    "    (lhsCols : List Col) (rhs : Option RhsSubquery) :\n"
    "    List Col × Option RhsSubquery := Id.run do\n"
    "  let mut cols := lhsCols\n"
    "  match rhs with\n"
    "  | none =>\n"
    "      return (cols, none)\n"
    "  | some q0 =>\n"
    "      let mut q := q0\n"
    "      if !q.explicitlySelected then\n"
    "        -- discard the implicit selection …\n"
    "        q := { q with selected := [], explicitlySelected := false }\n"
    "        -- … then select only the identity column.\n"
    "        q := { q with selected := [q.identityColumn], explicitlySelected := true }\n"
    "      cols := cols ++ q.groupKeys\n"
    "      return (cols, some q)"
)
_GOLD_PROOF = (
    "  intro lhsCols rhs\n"
    "  unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns\n"
    "  cases rhs with\n"
    "  | none => exact ⟨rfl, rfl⟩\n"
    "  | some q =>\n"
    "    simp only [Id.run, normalizeRhs]\n"
    "    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩"
)


# ===========================================================================
# (1) POSITIVE CONTROL — collapse the two-line update into the frozen pure
# helper `normalizeRhs q`. Definitionally identical (normalizeRhs sets
# `selected := [identityColumn]` and `explicitlySelected := true`, exactly the
# post-state the two lines reach), so the frozen proof body still discharges
# UNCHANGED. Must verify, else SPEC-TOO-STRONG.
# ===========================================================================
_POS_HELPER = _swap(
    _BASE,
    _NORM_BLOCK,
    "      if !q.explicitlySelected then\n"
    "        q := normalizeRhs q\n",
)


# ===========================================================================
# (2) POSITIVE CONTROL — a structurally different CORRECT reshape: drop the
# `Id.run do` / `let mut` scaffold entirely and compute the pair directly by a
# pure `match`, choosing the normalized-or-untouched query with a `let`. The
# proof is retuned (proof-region edit is allowed) to the new shape; the theorem
# STATEMENT is byte-identical, no new axiom/lemma/assumption. Must verify.
# ===========================================================================
_POS_FUNCTIONAL = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_membershipGroupColumns\n"
    "    (lhsCols : List Col) (rhs : Option RhsSubquery) :\n"
    "    List Col × Option RhsSubquery :=\n"
    "  match rhs with\n"
    "  | none => (lhsCols, none)\n"
    "  | some q =>\n"
    "      let q' := if q.explicitlySelected then q else normalizeRhs q\n"
    "      (lhsCols ++ q'.groupKeys, some q')",
)
_POS_FUNCTIONAL = _swap(
    _POS_FUNCTIONAL,
    _GOLD_PROOF,
    "  intro lhsCols rhs\n"
    "  unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns\n"
    "  cases rhs with\n"
    "  | none => exact ⟨rfl, rfl⟩\n"
    "  | some q =>\n"
    "    by_cases h : q.explicitlySelected <;> simp [h, normalizeRhs]",
)


# ===========================================================================
# (3) UNIQUENESS — drop the normalization (the prepatch bug). An implicitly
# selected nested rhs is left untouched instead of reduced to its identity
# column. Correct on the explicit / none sub-domains; wrong on the SOME-arm
# result.2 clause whenever `not q.explicitlySelected`.
# ===========================================================================
_R_NO_NORMALIZE = _swap(_BASE, _NORM_BLOCK, "")


# ===========================================================================
# (4) UNIQUENESS — normalize UNCONDITIONALLY (drop the `if !explicitlySelected`
# guard). Correct on the implicit sub-domain, but on an ALREADY-explicit rhs it
# clobbers the caller's selection to the identity column, so result.2 is
# `some (normalizeRhs q)` where the spec demands `some q`. This is the FRAME
# argument (off the normalization branch, the rhs state is preserved) expressed
# as a value obligation on result.2.
# ===========================================================================
_R_UNCOND = _swap(
    _BASE,
    _NORM_BLOCK,
    "      q := { q with selected := [], explicitlySelected := false }\n"
    "      q := { q with selected := [q.identityColumn], explicitlySelected := true }\n",
)


# ===========================================================================
# (5) UNIQUENESS — on the NONE arm, drop the lhs columns (return an empty list).
# Correct on the some arm; wrong on the NONE-arm result.1 clause
# (result.1 = lhsCols).
# ===========================================================================
_R_DROP_LHS_NONE = _swap(_BASE, _NONE_RETURN, "  | none =>\n      return ([], none)")


# ===========================================================================
# (6) UNIQUENESS — on the SOME arm, drop the rhs's grouping-column contribution
# (return `cols` unchanged, without appending `q.groupKeys`). Wrong on the
# SOME-arm result.1 clause (result.1 = lhsCols ++ q.groupKeys).
# ===========================================================================
_R_DROP_GROUPKEYS = _swap(_BASE, _APPEND_LINE, "      cols := cols\n")


# ===========================================================================
# (7) UNIQUENESS — on the SOME arm, drop the lhs PREFIX: return only the rhs's
# grouping columns (`q.groupKeys`), discarding `lhsCols`. A near-miss distinct
# from (6): it gets the groupKeys right but loses the lhs prefix, so its
# distinguishing input has a NON-EMPTY lhs. Wrong on the SOME-arm result.1
# clause (order/prefix).
# ===========================================================================
_R_DROP_LHS_SOME = _swap(_BASE, _APPEND_LINE, "      cols := q.groupKeys\n")


# ===========================================================================
# (8) UNIQUENESS — on the NONE arm, FABRICATE a nested-query state instead of
# leaving `result.2 = none`. result.1 is still correct (= lhsCols), but the
# NONE-arm result.2 clause (result.2 = none) is violated. This is the nagini
# "gratuitous normalization on the literal/non-query branch" frame attack,
# expressed as a value obligation on result.2.
# ===========================================================================
_R_FABRICATE_NONE = _swap(
    _BASE,
    _NONE_RETURN,
    "  | none =>\n"
    "      return (cols, some { explicitlySelected := true, selected := [0],\n"
    "                           defaultColumns := [], groupKeys := [], identityColumn := 0 })",
)


# ===========================================================================
# (9) UNIQUENESS — FRAME on the facets the normalization never writes. Keep the
# gold normalization exactly as-is (so both `result.1` and the two normalized
# facets `selected`/`explicitlySelected` are correct on EVERY input), then
# additionally clobber a facet the behavior only ever READS: the model's
# default-column set. The SOME-arm `result.2` clause pins the query state to
# `some q` / `some (normalizeRhs q)` — which fixes ALL FIVE fields, not merely
# the two the normalization writes — so zeroing `defaultColumns` violates it on
# every some-rhs, including the already-explicit one where nothing is supposed
# to happen at all. This is the nagini read-only-facet frame rival re-expressed
# as a value obligation; the sibling got its rejection from the permission
# system, this carrier gets it from the postcondition. Distinct from
# unconditional-normalize, which corrupts the two WRITTEN facets and leaves the
# read-only ones intact — audited: no other rival in this battery makes
# `defaultColumns` or `identityColumn` differ from the spec's demand.
# ===========================================================================
_R_CLOBBER_READONLY = _swap(
    _BASE,
    _APPEND_LINE,
    "      q := { q with defaultColumns := [] }\n"
    "      cols := cols ++ q.groupKeys\n",
)


# ===========================================================================
# (10) ADMISSIBILITY — the obligation is SATISFIABLE at a concrete F2P-SHAPED
# input, discharged BY EVALUATION as a `have` before the frozen obligation is
# closed verbatim. The frozen theorem binds `∀ lhsCols rhs` with no precondition
# hypothesis, so on this total carrier the analogue of PRECOND-TOO-STRONG is the
# obligation being unsatisfiable at exactly the input shape the F2P test pins: a
# nested rhs with NO explicit selection carrying its model's full (many-column)
# default set — the one shape the behavior must reduce to a single identity
# column. This case pins BOTH the concrete computed pair (`_ground_value`, so the
# post-image is non-degenerate and named, not merely asserted) and the spec
# predicate at that point (`_ground_admissible`), then closes the frozen
# obligation with the frozen script UNCHANGED. If evaluation at that point did
# not satisfy the spec, this case would FAIL while the ∀-obligation still went
# through — which is exactly the PRECOND-TOO-STRONG signal. Nothing is assumed:
# no new declaration, statement byte-identical, only `have`s prepended inside the
# proof region.
# ===========================================================================
# The F2P-shaped nested rhs: no explicit selection, full default column set.
_F2P_Q = ("{ explicitlySelected := false, selected := [], defaultColumns := [1, 2, 3], "
          "groupKeys := [9], identityColumn := 5 }")
# Its normalized post-state: selection reduced to the single identity column.
_F2P_Q_NORM = ("{ explicitlySelected := true, selected := [5], defaultColumns := [1, 2, 3], "
               "groupKeys := [9], identityColumn := 5 }")
_P_INTRO = "  intro lhsCols rhs\n"

_ADMISS = _swap(
    _BASE,
    _P_INTRO,
    f"  have _ground_value : implementation_membershipGroupColumns [4] (some {_F2P_Q})\n"
    f"      = ([4, 9], some {_F2P_Q_NORM}) := by decide\n"
    f"  have _ground_admissible : problem_spec_membershipGroupColumns [4] (some {_F2P_Q})\n"
    f"      (implementation_membershipGroupColumns [4] (some {_F2P_Q})) := by\n"
    "    unfold problem_spec_membershipGroupColumns "
    "implementation_membershipGroupColumns\n"
    "    decide\n"
    + _P_INTRO,
)


# --- concrete RhsSubquery literals used by the witnesses (all decidable) -----
_IMPL_Q = ("{ explicitlySelected := false, selected := [7], defaultColumns := [1,2,3], "
           "groupKeys := [9], identityColumn := 5 }")
_EXPL_Q = ("{ explicitlySelected := true, selected := [7], defaultColumns := [1,2,3], "
           "groupKeys := [9], identityColumn := 5 }")


def _witness(lhs, rhs):
    return (
        f"example : ¬ problem_spec_membershipGroupColumns {lhs} {rhs}\n"
        f"    (implementation_membershipGroupColumns {lhs} {rhs}) := by\n"
        "  unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_membershipGroupColumns` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-normalize-via-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HELPER,
        "rationale": "correct reshape: the two-line in-branch state update is "
                     "collapsed into the frozen pure helper (which sets exactly the "
                     "same normalized fields), so it computes the same pair on every "
                     "input and satisfies the spec — else SPEC-TOO-STRONG. Only the "
                     "impl region changes; the frozen proof body discharges it "
                     "UNCHANGED (verified with a real build), no new axiom/lemma.",
    },
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNCTIONAL,
        "rationale": "structurally different CORRECT reshape: the `Id.run do`/`let "
                     "mut` scaffold is dropped for a direct pure `match` that picks "
                     "the normalized-or-untouched query with a `let`. Definitionally "
                     "the same pair on every input, so the spec holds — else "
                     "SPEC-TOO-STRONG. Proof retuned (proof-region edit) to the new "
                     "shape; theorem STATEMENT byte-identical, no new assumption. "
                     "Verified with a real build.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — the obligation is satisfiable at
    # a concrete F2P-shaped input, discharged by evaluation before the frozen
    # obligation is closed verbatim.
    # =====================================================================
    {
        "id": "admiss-ground-implicit-rhs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged at a concrete F2P-SHAPED input "
                     "— a nested rhs with NO explicit selection carrying its "
                     "model's full multi-column default set, the one shape the "
                     "behavior has to reduce to a single identity column — by "
                     "EVALUATION as two `have`s: `_ground_value` pins the computed "
                     "pair to `([4,9], some {selected := [5], explicitlySelected := "
                     "true, ...})`, so the post-image at that point is named and "
                     "non-degenerate rather than merely asserted, and "
                     "`_ground_admissible` then discharges the spec predicate "
                     "there. The frozen obligation is closed afterwards with the "
                     "frozen script UNCHANGED. On this total carrier that is the "
                     "analogue of PRECOND-TOO-STRONG: if the modeled behavior were "
                     "unsatisfiable at exactly a normal F2P input, this case would "
                     "FAIL while the ∀-obligation still went through, which no "
                     "other lane here would detect. Nothing is assumed — no new "
                     "declaration, statement byte-identical, only `have`s prepended "
                     "inside the proof region. Verified with a real build.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P test. The witnesses vary BOTH
    # binders (lhsCols across six values; rhs across none / some-implicit /
    # some-explicit) and attack all four postcondition conjuncts.
    # =====================================================================
    {
        "id": "no-normalize-implicit-rhs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_NO_NORMALIZE,
        "refinement": "this IS the prepatch behavior: an implicitly-selected nested "
                      "rhs used as a membership condition is left carrying all of its "
                      "model's default columns, so the emitted subquery selects many "
                      "columns and the database rejects it ('subquery must return only "
                      "one column'). A faithful patch that omitted the normalization "
                      "would NOT resolve — it is exactly the RED state the F2P test "
                      "pins.",
        "rationale": "REJECT from the SOME-arm result.2 clause (implicit case: "
                     "result.2 = some (normalizeRhs q)): the rival returns `some q` "
                     "un-normalized. Refuted at an implicitly-selected rhs "
                     "(explicitlySelected := false); binder `rhs` at the some-implicit "
                     "point, `lhsCols = [2]`.",
        "witness": _witness("[2]", f"(some {_IMPL_Q})"),
    },
    {
        "id": "unconditional-normalize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_UNCOND,
        "refinement": "a nested query on which the caller already chose the columns "
                      "carries an explicit selection, and the desired behavior leaves "
                      "it UNTOUCHED. Normalizing unconditionally rewrites that "
                      "query's selection down to the identity column, changing the "
                      "emitted SQL for every membership lookup whose nested query was "
                      "explicitly projected — it would regress those queries rather "
                      "than fix the single-valued requirement, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the SOME-arm result.2 frame clause (explicit case: "
                     "result.2 = some q, untouched): dropping the guard forces "
                     "result.2 = some (normalizeRhs q) on an already-explicit rhs. "
                     "Refuted at an explicitly-selected rhs whose selection differs "
                     "from the identity column; binder `rhs` at the some-explicit "
                     "point, `lhsCols = [3,4]`.",
        "witness": _witness("[3,4]", f"(some {_EXPL_Q})"),
    },
    {
        "id": "drop-lhs-on-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_LHS_NONE,
        "refinement": "when the rhs is not a nested query the collected key is just "
                      "the lhs's grouping columns; dropping them emits the wrong GROUP "
                      "BY for the common non-subquery membership lookup, regressing "
                      "the aggregation tests — not a faithful patch, would NOT "
                      "resolve.",
        "rationale": "REJECT from the NONE-arm result.1 clause (result.1 = lhsCols): "
                     "the rival returns `[]` on the none branch. Refuted at "
                     "`rhs = none` with a non-empty `lhsCols = [1,2,3]`; binder `rhs` "
                     "at the none point.",
        "witness": _witness("[1,2,3]", "none"),
    },
    {
        "id": "drop-groupkeys-on-some",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_GROUPKEYS,
        "refinement": "a nested-query rhs must contribute its grouping columns to the "
                      "key; dropping that contribution omits the subquery from the "
                      "GROUP BY entirely, producing a different aggregate grouping — "
                      "not the gold behavior, would NOT resolve.",
        "rationale": "REJECT from the SOME-arm result.1 clause (result.1 = lhsCols ++ "
                     "q.groupKeys): the rival never appends `q.groupKeys`. Refuted at "
                     "a some rhs with non-empty groupKeys; binder `rhs` at the "
                     "some-explicit point, `lhsCols = [6]`.",
        "witness": _witness("[6]", f"(some {_EXPL_Q})"),
    },
    {
        "id": "drop-lhs-prefix-on-some",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_LHS_SOME,
        "refinement": "the lhs columns are always collected FIRST, then the rhs's; "
                      "returning only the rhs contribution drops the left operand's "
                      "grouping columns and reorders the key, emitting the wrong GROUP "
                      "BY — not a faithful patch, would NOT resolve.",
        "rationale": "REJECT from the SOME-arm result.1 clause (result.1 = lhsCols ++ "
                     "q.groupKeys): the rival returns `q.groupKeys` only, dropping the "
                     "lhs prefix. A near-miss distinct from drop-groupkeys-on-some — "
                     "its distinguishing input has a NON-EMPTY lhs, so it carries its "
                     "own point `lhsCols = [8]` at the some-explicit rhs.",
        "witness": _witness("[8]", f"(some {_EXPL_Q})"),
    },
    {
        "id": "fabricate-state-on-none-rhs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_FABRICATE_NONE,
        "refinement": "when the rhs is not a nested query the desired behavior never "
                      "produces any nested-query state at all — the whole rhs "
                      "contribution is skipped for a non-query operand. Fabricating a "
                      "normalized query state on this branch has no counterpart in the "
                      "intended behavior and would disturb an operand that is supposed "
                      "to be left alone — not a faithful patch.",
        "rationale": "REJECT from the NONE-arm result.2 clause (result.2 = none): the "
                     "rival fabricates `some {...}`. result.1 stays correct, so the "
                     "rejection is attributable solely to the fabricated rhs state. "
                     "Refuted at `rhs = none`, `lhsCols = [5]`; the frame argument the "
                     "nagini permission-mutation rival carried, expressed as a "
                     "result.2 value obligation.",
        "witness": _witness("[5]", "none"),
    },
    {
        "id": "clobber-readonly-rhs-facets",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_CLOBBER_READONLY,
        "refinement": "the normalization only ever replaces a nested query's "
                      "SELECTION state; the model's default-column set is data the "
                      "behavior READS to decide what an unselected query would emit "
                      "and never writes. An impl that also empties that set leaves "
                      "the nested query unable to fall back to its model's columns "
                      "anywhere else it is reused, corrupting unrelated queries over "
                      "the same object while doing nothing for the single-valued "
                      "requirement — not the intended mechanism, and it would not "
                      "resolve.",
        "rationale": "REJECT from the SOME-arm result.2 clause read at FULL width: "
                     "the clause pins result.2 to `some q` / `some (normalizeRhs q)`, "
                     "so all five fields of the query state are fixed, not just the "
                     "two the normalization writes. This rival keeps result.1 and "
                     "both normalized facets exactly right on every input and "
                     "corrupts only `defaultColumns`, so its rejection is "
                     "attributable SOLELY to the frame obligation on the read-only "
                     "facets — the one clause no other rival here touches "
                     "(unconditional-normalize corrupts the WRITTEN facets and "
                     "leaves these intact). Refuted at an ALREADY-EXPLICIT rhs, "
                     "where the spec demands the query come back untouched; binder "
                     "`rhs` at the some-explicit point, `lhsCols = [9]`.",
        "witness": _witness("[9]", f"(some {_EXPL_Q})"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 5 uniqueness rivals) plus a
# 3-case AXIOM lane. That sibling contracts `membership_group_by_cols` over a
# Nagini heap with fractional permissions (`Acc(.,1/2)`) on the read-only
# inputs, so it can attack via ILLEGAL WRITES to those inputs. This bundle
# models the same behavior functionally as `membershipGroupColumns
# (lhsCols) (rhs : Option RhsSubquery)` returning a PAIR `(cols, rhs')`; the
# editable surface is the pure impl, and the referentially-transparent carrier
# has no heap to abuse. Every sibling case is recorded below.
#
#   nagini case                              -> here
#   ---------------------------------------------------------------------
#   pos-control-local-reshape                -> pos-normalize-via-helper,
#                                               pos-functional-reshape   RE-EXPRESSED
#   admiss-fieldless-shaped                  -> admiss-ground-implicit-rhs  RE-EXPRESSED
#   frame-mut-lhs-cols                        -> (none)          VACUOUS (lhs is not in the
#                                                                 result-state component at all)
#   frame-mut-rhs-default-cols                -> clobber-readonly-rhs-facets  RE-EXPRESSED
#   echo-fabricate-pk-no-normalise            -> no-normalize-implicit-rhs  RE-EXPRESSED
#   uncond-normalise-explicit-rhs             -> unconditional-normalize     RE-EXPRESSED
#   partial-domain-drop-lhs-literal           -> drop-lhs-on-none            RE-EXPRESSED
#   gratuitous-normalise-explicit-after-result-> unconditional-normalize     SUBSUMED (P6/result.2)
#   gratuitous-normalise-literal-rhs          -> fabricate-state-on-none-rhs RE-EXPRESSED
#   (added: drop-groupkeys-on-some, drop-lhs-prefix-on-some — attack the SOME-arm
#           result.1 append structure the nagini list-shape didn't isolate)
#   AXIOM_TESTS (3)                           -> (none)          DROPPED (G-AX)
#
# RE-EXPRESSED (positive controls): the nagini local-reshape positive carried
#   the ARGUMENT that a structurally different but faithful impl must verify.
#   Here that is carried by (a) collapsing the two-line update into the frozen
#   helper (proof body unchanged) and (b) a full functional reshape dropping the
#   `Id.run do` scaffold (proof retuned, statement identical). Both verify with
#   real builds.
# RE-EXPRESSED (admissibility): ported as `admiss-ground-implicit-rhs`, after an
#   audit found the earlier "VACUOUS (no precondition)" reading wrong. The
#   premise is right — the frozen theorem carries no precondition hypothesis —
#   but the conclusion does not follow: the lane's job is to detect
#   PRECOND-TOO-STRONG, and on a TOTAL carrier that failure mode presents as the
#   obligation being UNSATISFIABLE at exactly an F2P-shaped input. Discharging
#   the obligation at that concrete input by evaluation, as a `have`, before
#   closing the frozen obligation verbatim tests it directly, and nothing about
#   the absence of a precondition blocks that. Landed at the F2P shape (nested
#   rhs, no explicit selection, full multi-column default set) with the computed
#   pair pinned as well, so the post-image is named and non-degenerate. Real
#   build: exit 0. Dropping this lane silently had removed one of the three
#   directions this gate exists to test.
# FRAME-MUTATION (two nagini cases) — split verdict, one each way. The nagini
#   sibling holds `lhs_cols` and `rhs.default_cols` at Acc(.,1/2) and its rivals
#   WRITE through them to be rejected for INSUFFICIENT PERMISSION. That
#   REJECTION MECHANISM is genuinely absent here (no heap, no aliasing, no
#   permission to be short of), but the mechanism is not the obligation, and the
#   two cases differ on whether the obligation survives:
#     - frame-mut-lhs-cols  -> VACUOUS. `lhsCols` is an immutable input that
#       appears in the result only through `result.1 = lhsCols ++ ...`; there is
#       no second component carrying a post-state for it, so "the caller's lhs
#       list was mutated" has no observable referent to assert. Its value-level
#       shadow (the lhs must be collected verbatim and first) is already carried
#       by drop-lhs-on-none and drop-lhs-prefix-on-some.
#     - frame-mut-rhs-default-cols -> EXPRESSIBLE, and now PORTED as
#       clobber-readonly-rhs-facets. The SOME-arm pins `result.2` to `some q` /
#       `some (normalizeRhs q)`, which fixes ALL FIVE fields of the query state;
#       the facets the normalization never writes (`defaultColumns`,
#       `identityColumn`) are therefore under a real preservation obligation, and
#       an impl that clobbers one is rejected by the postcondition. Confirmed
#       with two builds (witness elaborates against the rival, `decide` refutes
#       it on gold). Recording this class as wholly vacuous understated the
#       carrier: only the permission MECHANISM was vacuous, not the frame clause.
#   Preservation of the two WRITTEN facets on the already-explicit branch is
#   carried by unconditional-normalize; absence of state off the query branch by
#   fabricate-state-on-none-rhs.
# RE-EXPRESSED (uniqueness): echo/uncond/partial/gratuitous rivals all map to a
#   spec-clause attack on this carrier; each ships a `decide`-able witness that
#   ELABORATES against the rival and FAILS against gold (two real builds each).
#   The nagini P4 "produced-by post-state" (rhs mutated to explicit_cols==pk) is
#   the SOME-arm result.2 normalization clause here; the nagini P6 FRAME is the
#   result.2 preservation/absence clauses. Two rivals were ADDED
#   (drop-groupkeys-on-some, drop-lhs-prefix-on-some) because this carrier makes
#   the SOME-arm result.1 = lhsCols ++ q.groupKeys append structure explicit —
#   both the presence of the rhs contribution and the lhs-first ordering are
#   independently attackable, which the nagini list-return shape did not isolate.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the changed behavior is
#   modeled deeply in the frozen pure region (`normalizeRhs`) with no consumed
#   axiom and no opaque callee, so there is nothing for this gate to probe.
#
# COVERAGE: 2 soundness positives + 1 admissibility positive + 7 uniqueness
# rivals, so all three directions this gate tests are represented (SPEC-TOO-STRONG
# via the soundness positives, SPEC-TOO-WEAK via the rivals, PRECOND-TOO-STRONG
# via the admissibility ground instance). Binder `rhs` is varied
# across none (drop-lhs-on-none, fabricate-state-on-none-rhs), some-implicit
# (no-normalize-implicit-rhs), and some-explicit (unconditional-normalize,
# drop-groupkeys-on-some, drop-lhs-prefix-on-some, clobber-readonly-rhs-facets);
# binder `lhsCols` takes seven distinct values ([2],[3,4],[1,2,3],[6],[8],[5],
# [9]). All four postcondition conjuncts are attacked: NONE-arm result.1
# (drop-lhs-on-none), NONE-arm result.2 (fabricate-state-on-none-rhs), SOME-arm
# result.1 (drop-groupkeys-on-some, drop-lhs-prefix-on-some), SOME-arm result.2
# in all three of its independent directions — the implicit-normalize case
# (no-normalize-implicit-rhs), the explicit-preserve case for the WRITTEN facets
# (unconditional-normalize), and the preserve case for the READ-ONLY facets
# (clobber-readonly-rhs-facets).
#
# Each rival was additionally checked for OBSERVABILITY rather than mere reshape:
# every one of the seven differs from the frozen impl on a positive fraction of
# an exhaustively enumerated input grid (lhsCols x all rhs shapes x both flag
# polarities), so none is definitionally equal to gold on this carrier and no
# case rejects merely because a tactic script is tuned to the frozen form.
AXIOM_TESTS = []
