# properties.py — G-PBT falsification battery for django__django-11490 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each case is a
# FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, for a positive that reproves, the tactic body — is edited), checked
# by variant_scope before the verifier runs. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the postcondition and not to a
# tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read off Solution.lean / mapping.md / instance.json)
#   implementation_propagateColumns
#       (parts : List QueryPart) (composedColumns : List String)
#       : List (QueryPart × QueryPart)
#   ONE obligation, `theorem correct_propagateColumns`, with NO precondition
#   hypothesis: the statement is ∀ parts composedColumns, problem_spec … . Two input
#   binders, both freely varying.
#
#   The modeled behavior: evaluating a composed query for a chosen column list over
#   its parts. Each result entry belongs to one part and carries TWO components —
#   `.fst`, the query actually built for THIS evaluation, and `.snd`, the part
#   definition carried forward. The three independent top-level clauses of
#   problem_spec_propagateColumns:
#     (A) length  — exactly one result entry per part;
#     (B) .fst    — the built query adopts `composedColumns` precisely when the part
#                   fixes no column list of its own AND a specific list is requested;
#                   otherwise the part is used as given (pinned to its input);
#     (C) .snd    — EVERY part definition is carried forward equal to its input, so a
#                   later evaluation is free to choose a different column list.
#   Clause (C) is the load-bearing one: it is the pure-setting encoding of "producing
#   one evaluation never alters a shared part", i.e. the property whose absence is the
#   regression the F2P test pins. Clause (B) is what makes the chosen list actually
#   take effect, and (A)+(B) together pin the per-part correspondence positionally.
#
#   The oracle is TRANSPARENT and total: `QueryPart` derives DecidableEq and the spec
#   is a decidable equality between concrete lists, with no opaque callee and no
#   answer-key. So `decide` computes both sides at any literal input and no witness
#   needs to condition on the carrier — every witness below is stated at literal
#   inputs and therefore binds nothing (no consistency probe applies).
#
# CARRIER NARROWING vs the nagini sibling (why the case set is reshaped, not thinned)
#   Nagini modeled THREE functions behind fractional permissions — a per-evaluation
#   builder plus two deep models of unchanged callees (a detach-a-copy helper and a
#   record-the-column-list helper) — and its headline class was FRAME-MUTATION:
#   `cached` and `fields` were held read-only (Acc(…,1/2) / Acc(…,1/4)), so a rival
#   that wrote the chosen list onto the SHARED part had to reject for insufficient
#   permission. This bundle models only the purely functional core: ONE obligation,
#   the two helpers absorbed (a part is observed solely by the column list it
#   projects, so neither helper contributes a separate contract). Consequently the
#   nagini cases attached to those two helpers have no counterpart here, and the
#   aliasing the nagini battery attacked through permissions is attacked here through
#   clause (C) — the `.snd` frame conjunct — which is the pure-setting observable that
#   replaces it. See 'LANES THAT DO NOT PORT' below for the full disposition.
#
# LANES THAT DO NOT PORT
#   * FRAME/PERMISSION-MUTATION as a MECHANISM (nagini's cfs-frame-realbug,
#     cfs-frame-direct, dc-frame-mutation, wc-frame-mutation). Lean is referentially
#     transparent: there is no aliasing and no fractional permission, so "store into
#     a read-only input" is not expressible and no rival can be rejected FOR a
#     permission violation. The class is vacuous AS A MECHANISM. Its ARGUMENT is not
#     lost, though — the two rivals nagini rejected on permissions because they left
#     the shared part altered are re-expressed here as value-level violations of
#     clause (C): see `weak-carry-forward-altered` (the direct counterpart of
#     cfs-frame-realbug, and of the bundle's own prepatch shape) and
#     `weak-drop-used-as-given-entry`.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries no diverge-*/nonterm-*/
#     weak-diverge case, and on this backend the class is genuinely vacuous regardless:
#     `implementation_propagateColumns` is a total Lean `def`, so a diverging
#     implementation cannot be written at all. This is NOT the velvet
#     `loom.semantics.termination "partial"` known spec hole (the corpus-wide termination-semantics finding).
#   * ADMISSIBILITY DOES PORT — and it is now carried, as `adm-f2p-shaped-input`.
#     (AUDIT CORRECTION. The port originally recorded this lane as N/A on the ground
#     that `theorem correct_propagateColumns` binds no precondition hypothesis, so
#     nothing could be PRECOND-TOO-STRONG. That reason is wrong: on a TOTAL carrier
#     the analogue of a too-strong precondition is the obligation being UNSATISFIABLE
#     at an F2P-shaped input — a spec that no implementation can discharge there is
#     just as broken, and a universally-quantified statement does not by itself
#     demonstrate otherwise. The positive below discharges the obligation at that
#     concrete input BY EVALUATION, as a `have`, before closing the frozen obligation
#     verbatim, which tests it directly. Nagini's cfs-admissibility is therefore
#     ported in substance, not dropped.)
#   * The nagini helper cases with no modeled counterpart: dc-alias-not-copy,
#     dc-pos-control, wc-pos-control. The detach-a-copy and record-the-column-list
#     helpers are not separate functions in this model, so "aliased the container
#     instead of copying it" is not a statement about anything this bundle contracts.
#   * NAGINI CASES THE CARRIER COLLAPSES (demonstrated, not asserted). Two nagini
#     rivals are not merely unported — they are, on this carrier, THE SAME FUNCTION
#     as a rival already present, so shipping them would add a duplicate rather than
#     a distinct attack:
#       - cfs-wrong-list (record the part's OWN list rather than the requested one)
#         is pointwise equal to `weak-never-adopt`: on the adopting arm the part's
#         own list is `[]` by the guard, so `{ part with columns := part.columns }`
#         is just `part`.
#       - cfs-frame-direct (APPEND the requested list onto the part definition rather
#         than replace it) is pointwise equal to `weak-carry-forward-altered`: on the
#         adopting arm `part.columns = []`, so `[] ++ composedColumns` is
#         `composedColumns`.
#     Both collapses were machine-checked as `∀ parts cc, impl₁ … = impl₂ …`.
#   * wc-drop-last DOES port and is NOT covered by `weak-never-adopt`. Its argument
#     (the built query carries a list that is neither the part's own nor the
#     requested one) is a strictly TIGHTER near-miss: a drop-last rival AGREES with
#     `weak-never-adopt` at every request of at most one column and diverges only at
#     a request of two or more. It ships below as `weak-truncate-requested-list`.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them, and this
#     bundle has no consumed axiom or axiomatized reference anyway (meta.axioms == []).
from pathlib import Path

INSTANCE = "django__django-11490"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors -----------------------------------------------------------
# Each lies ENTIRELY inside impl-start/impl-end and is unique in the frozen file, so
# every variant below edits only the implementation and `same_spec` holds by
# construction.
_ACC_INIT = "  let mut out : List (QueryPart × QueryPart) := []\n"
_GUARD = "    if part.columns = [] ∧ composedColumns ≠ [] then\n"
_ADOPT_ARM = (
    "      let derived := { part with columns := composedColumns }\n"
    "      out := out ++ [(derived, part)]\n"
)
_GIVEN_ARM = "      out := out ++ [(part, part)]\n"
for _a in (_ACC_INIT, _GUARD, _ADOPT_ARM, _GIVEN_ARM):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The whole frozen impl body (the accumulator + the loop + the return), used by the
# positive that replaces the imperative shape wholesale.
_IMPL_BODY = (
    "  let mut out : List (QueryPart × QueryPart) := []\n"
    "  for part in parts do\n"
    "    if part.columns = [] ∧ composedColumns ≠ [] then\n"
    "      -- This part fixes no column list of its own and the composed query requests\n"
    "      -- one: build this evaluation's query from a fresh copy carrying the composed\n"
    "      -- column list, while carrying the part's own definition forward unchanged.\n"
    "      let derived := { part with columns := composedColumns }\n"
    "      out := out ++ [(derived, part)]\n"
    "    else\n"
    "      -- The part already fixes its own columns (or none are requested): use it as\n"
    "      -- given and carry it forward unchanged.\n"
    "      out := out ++ [(part, part)]\n"
    "  return out\n"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl body anchor drifted"

# The impl's signature line, so a positive may drop `Id.run do` for a direct traversal.
_IMPL_SIG = "    : List (QueryPart × QueryPart) := Id.run do\n"
assert _BASE.count(_IMPL_SIG) == 1, "impl signature anchor drifted"

# --- the obligation's tactic body -------------------------------------------------
# `_OBLIGATION_HEAD` is the byte-identical theorem STATEMENT that variant_scope
# requires every variant to preserve; `_TACTICS` is everything after it inside the
# proof region, i.e. the only part a positive may honestly re-author.
_OBLIGATION_HEAD = (
    "theorem correct_propagateColumns :\n"
    "    ∀ (parts : List QueryPart) (composedColumns : List String),\n"
    "      problem_spec_propagateColumns parts composedColumns\n"
    "        (implementation_propagateColumns parts composedColumns) := by\n"
)
assert _BASE.count(_OBLIGATION_HEAD) == 1, "obligation head drifted"
_TACTICS = _BASE[_BASE.index(_OBLIGATION_HEAD) + len(_OBLIGATION_HEAD):
                 _BASE.index("-- proof-end")]
assert _TACTICS.strip(), "frozen tactic body not found"


def _wit(parts, composed, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a CONCRETE pair
    of literal inputs, closed by `decide`.

    The carrier is fully transparent (`QueryPart` derives DecidableEq; the spec is a
    decidable equality of concrete lists), so no conditioning on an opaque term is
    needed and the head binds NOTHING — there are no hypotheses that could be jointly
    unsatisfiable. Elaborates against a rival whose output differs from the pinned one
    at this point; fails on the frozen solution, which satisfies the spec everywhere.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_propagateColumns\n"
        f"    {parts} {composed}\n"
        f"    (implementation_propagateColumns {parts} {composed}) := by\n"
        f"  unfold problem_spec_propagateColumns implementation_propagateColumns\n"
        f"  decide"
    )


# Literal input points the witnesses probe. Both binders are varied across them:
# `parts` ranges over one part fixing no list, one part fixing its own list, two parts
# fixing no list, and a mixed pair; `composedColumns` ranges over a one-element
# request, a two-element request, and no request at all.
_P_NOLIST = "[({ columns := [] } : QueryPart)]"
_P_OWNLIST = '[({ columns := ["x"] } : QueryPart)]'
_P_NOLIST2 = "[({ columns := [] } : QueryPart), ({ columns := [] } : QueryPart)]"
_P_MIXED = '[({ columns := [] } : QueryPart), ({ columns := ["x"] } : QueryPart)]'


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each edits only the impl region and leaves the frozen tactic body in place (which
# will not close for a reshaped impl — that is why the witness, not the build, is what
# attributes the rejection to the spec).
# ===========================================================================

# (1) Carries the ALTERED part forward: the adopting arm puts the derived query in
# BOTH components, so the part definition handed on is the rewritten one. This is the
# direct counterpart of nagini's cfs-frame-realbug and the shape of the bundle's own
# prepatch. Attacks clause (C).
_RIV_CARRY_ALTERED = _swap(
    _BASE, _ADOPT_ARM,
    "      let derived := { part with columns := composedColumns }\n"
    "      out := out ++ [(derived, derived)]\n",
)

# (2) Never adopts the requested column list: the adopting arm carries the part
# through unchanged in both components, so the query built for this evaluation still
# projects the part's own (empty) list. Attacks clause (B).
_RIV_NEVER_ADOPT = _swap(_BASE, _ADOPT_ARM, _GIVEN_ARM.lstrip("\n"))

# (3) Drops the "part fixes no column list of its own" half of the branch condition:
# a part that DOES fix its own list is overwritten with the requested one instead of
# being used as given. Attacks clause (B)'s used-as-given arm.
_RIV_OVERWRITE_OWN = _swap(_BASE, _GUARD, "    if composedColumns ≠ [] then\n")

# (4) Emits no entry at all in the used-as-given arm. Attacks clause (A) — and clause
# (C) with it, since a part whose entry is missing has no definition carried forward.
_RIV_DROP_GIVEN = _swap(_BASE, _GIVEN_ARM, "      out := out\n")

# (5) Adopts the requested list for the FIRST eligible part only; every later eligible
# part is used as given. Attacks clause (B) on a MULTI-part input — the sub-domain
# where a rival that is right about one part can still be wrong about the rest.
_RIV_FIRST_ONLY = _swap(
    _swap(
        _swap(_BASE, _ACC_INIT, _ACC_INIT + "  let mut adopted : Bool := false\n"),
        _GUARD,
        "    if part.columns = [] ∧ composedColumns ≠ [] ∧ !adopted then\n",
    ),
    _ADOPT_ARM,
    _ADOPT_ARM + "      adopted := true\n",
)

# (6a) Builds the query for an adopting part from the requested column list with its
# LAST column dropped. Attacks clause (B) at a point NO other rival reaches: unlike
# (2), which returns the part unchanged, this rival does adopt a list derived from the
# request — just the wrong one. It agrees with (2) at every request of at most one
# column, so it is only refutable at a request of two or more, and it is refuted here
# at three to keep it clear of (2)'s own two-element witness point.
_RIV_TRUNCATE_REQUEST = _swap(
    _BASE, _ADOPT_ARM,
    "      let derived := { part with columns := composedColumns.dropLast }\n"
    "      out := out ++ [(derived, part)]\n",
)

# (6b) AUDIT ADDITION. Carries a BLANK part definition forward on the used-as-given
# arm: the built query is right, but the part handed on projects nothing. Every other
# rival that attacks clause (C) does so on the ADOPTING arm (it carries the rewritten
# part), so the frame conjunct was demonstrated only on the branch that rewrites
# anything. This rival isolates (C) on the OTHER branch — a part used exactly as given
# still has its definition pinned to its input — which is the half of the frame clause
# no shipped case reached. Its faithful real counterpart replaces a part definition it
# never needed to touch at all with a blank one, so a later evaluation of the composed
# query finds that part projecting nothing.
_RIV_BLANK_CARRY_GIVEN = _swap(
    _BASE, _GIVEN_ARM,
    "      out := out ++ [(part, ({ columns := [] } : QueryPart))]\n",
)

# (6) Builds the result back-to-front: same number of entries and the same entries as
# a multiset, but the per-part correspondence is reversed. Attacks the POSITIONAL
# force of clauses (B) and (C) — the property that makes each entry belong to ITS part.
_RIV_REVERSED = _swap(
    _swap(
        _BASE, _ADOPT_ARM,
        "      let derived := { part with columns := composedColumns }\n"
        "      out := [(derived, part)] ++ out\n",
    ),
    _GIVEN_ARM,
    "      out := [(part, part)] ++ out\n",
)


# ===========================================================================
# SOUNDNESS POSITIVES — must VERIFY (else SPEC-TOO-STRONG). Each is a genuinely
# different executable shape whose obligation is RE-PROVEN honestly: the
# `theorem correct_propagateColumns` STATEMENT is byte-identical, and no new
# axiom / lemma / sorry / native_decide is introduced (variant_scope enforces both).
# ===========================================================================

# (P1) Direct traversal: drops the mutable accumulator and the `for` loop entirely,
# producing the entry list by mapping over the parts. Observationally identical on
# every input; a different executable shape a faithful patch could equally take. The
# frozen proof's whole first half is the `forIn`-reduction lemma, which no longer
# applies, so the tactic body is re-authored around the traversal directly.
_POS_TRAVERSAL = _swap(
    _swap(
        _swap(_BASE, _IMPL_SIG, "    : List (QueryPart × QueryPart) :=\n"),
        _IMPL_BODY,
        "  -- One entry per part, produced by a direct traversal rather than by\n"
        "  -- accumulating into a working list.\n"
        "  parts.map (fun part =>\n"
        "    if part.columns = [] ∧ composedColumns ≠ []\n"
        "    then ({ part with columns := composedColumns }, part)\n"
        "    else (part, part))\n",
    ),
    _TACTICS,
    "  intro parts cc\n"
    "  unfold problem_spec_propagateColumns implementation_propagateColumns\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · simp\n"
    "  · simp only [List.map_map, Function.comp_def]\n"
    "    apply List.map_congr_left\n"
    "    intro part _\n"
    "    by_cases h : part.columns = [] ∧ cc ≠ [] <;> simp [h]\n"
    "  · simp only [List.map_map, Function.comp_def]\n"
    "    conv_rhs => rw [← List.map_id parts]\n"
    "    apply List.map_congr_left\n"
    "    intro part _\n"
    "    by_cases h : part.columns = [] ∧ cc ≠ [] <;> simp [h]\n",
)

# (P2) Same imperative accumulator, but the branch condition is NEGATED and the two
# arms are SWAPPED, so the used-as-given case is handled first and the adopting arm
# inlines its derived query instead of naming it. Identical result on every input;
# only the branch form changes. The frozen reduction lemma is rebased on the negated
# test (`if_neg (not_not_intro h)` where the frozen script used `if_pos h`), which is
# a genuine reproof of the SAME obligation, not a weakening.
_POS_NEGATED = _swap(
    _swap(
        _BASE, _IMPL_BODY,
        "  let mut out : List (QueryPart × QueryPart) := []\n"
        "  for part in parts do\n"
        "    if ¬(part.columns = [] ∧ composedColumns ≠ []) then\n"
        "      -- The part already fixes its own columns (or none are requested): use it\n"
        "      -- as given and carry it forward unchanged.\n"
        "      out := out ++ [(part, part)]\n"
        "    else\n"
        "      -- This part fixes no column list of its own and the composed query\n"
        "      -- requests one: build this evaluation's query from a fresh copy carrying\n"
        "      -- the composed column list, while carrying the part's own definition\n"
        "      -- forward unchanged.\n"
        "      out := out ++ [({ part with columns := composedColumns }, part)]\n"
        "  return out\n",
    ),
    _TACTICS,
    "  intro parts cc\n"
    "  have helper : ∀ (init : List (QueryPart × QueryPart)),\n"
    "      Id.run (forIn parts init (fun part r =>\n"
    "        (if ¬(part.columns = [] ∧ cc ≠ []) then\n"
    "          pure (ForInStep.yield (r ++ [(part, part)]))\n"
    "        else\n"
    "          pure (ForInStep.yield (r ++ [(({ part with columns := cc } : QueryPart), part)]))) : Id _))\n"
    "        = init ++ parts.map (fun part =>\n"
    "            ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by\n"
    "    intro init\n"
    "    induction parts generalizing init with\n"
    "    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "    | cons a as ih =>\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      by_cases h : a.columns = [] ∧ cc ≠ []\n"
    "      · rw [if_neg (not_not_intro h)]\n"
    "        simp only [ih, if_pos h, List.map_cons]\n"
    "        rw [List.append_assoc]; rfl\n"
    "      · rw [if_pos h]\n"
    "        simp only [ih, if_neg h, List.map_cons]\n"
    "        rw [List.append_assoc]; rfl\n"
    "  have himpl : implementation_propagateColumns parts cc\n"
    "      = parts.map (fun part =>\n"
    "          ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by\n"
    "    have hb := helper []\n"
    "    rw [List.nil_append] at hb\n"
    "    rw [← hb]\n"
    "    rfl\n"
    "  unfold problem_spec_propagateColumns\n"
    "  rw [himpl]\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · simp [List.length_map]\n"
    "  · simp only [List.map_map, Function.comp_def]\n"
    "  · simp only [List.map_map, Function.comp_def]\n"
    "    exact List.map_id_fun' ▸ rfl\n",
)


# (P3) AUDIT ADDITION — the ADMISSIBILITY positive. Discharges the frozen obligation
# at a concrete F2P-shaped input (a part fixing no list of its own alongside a part
# that fixes its own, with a specific multi-column list requested) BY EVALUATION, as a
# `have`, and only then closes the frozen obligation with the frozen tactic body
# verbatim. Nothing is assumed: no new declaration, no new axiom/sorry, and the
# `theorem correct_propagateColumns` statement is byte-identical.
_POS_ADMISSIBLE = _swap(
    _BASE, _TACTICS,
    "  -- The obligation is SATISFIABLE at an F2P-shaped input, discharged here by\n"
    "  -- evaluation before the general obligation is closed below.\n"
    "  have _ground : problem_spec_propagateColumns\n"
    "      [({ columns := [] } : QueryPart), ({ columns := [\"x\"] } : QueryPart)] [\"a\", \"b\"]\n"
    "      (implementation_propagateColumns\n"
    "        [({ columns := [] } : QueryPart), ({ columns := [\"x\"] } : QueryPart)] [\"a\", \"b\"]) := by\n"
    "    unfold problem_spec_propagateColumns implementation_propagateColumns\n"
    "    decide\n"
    + _TACTICS,
)


SPEC_TESTS = [
    # ---------------- soundness positives (must VERIFY) ----------------
    {
        "id": "pos-direct-traversal",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TRAVERSAL,
        "rationale": (
            "Structurally DIFFERENT but CORRECT: the mutable accumulator and the loop "
            "are replaced by a direct traversal that maps each part to its entry. The "
            "result is identical on every input — one entry per part (A), the same "
            "adopt-or-use-as-given decision per part (B), the same part definition "
            "carried forward (C) — so all three clauses hold. The frozen tactic body "
            "is dominated by a loop-reduction lemma that no longer applies, so it is "
            "honestly re-authored over the traversal; the `theorem "
            "correct_propagateColumns` STATEMENT is byte-identical and no new "
            "axiom/lemma/sorry/native_decide is introduced. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition would be over-fit to one execution "
            "shape rather than to the behavior). Ports nagini's cfs-pos-control, whose "
            "argument was the same: a correct impl that reaches the result by an "
            "entirely different route must still verify."
        ),
    },
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEGATED,
        "rationale": (
            "Structurally DIFFERENT but CORRECT: the imperative shape is kept, but the "
            "branch test is NEGATED and the two arms SWAPPED so the used-as-given case "
            "is handled first, with the adopting arm inlining its derived query instead "
            "of naming it. The decision taken per part is unchanged, so clauses (A), "
            "(B) and (C) all still hold pointwise. The loop-reduction lemma is rebased "
            "on the negated test — a genuine reproof of the same obligation (statement "
            "byte-identical, no new axiom/lemma/sorry). If it FAILS => SPEC-TOO-STRONG "
            "(the postcondition would be over-fit to one branch order). Ports the "
            "shape-invariance argument behind nagini's dc-pos-control / wc-pos-control, "
            "which are otherwise unmodeled here."
        ),
    },

    {
        "id": "adm-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISSIBLE,
        "rationale": (
            "ADMISSIBILITY. On this total carrier the analogue of a PRECOND-TOO-STRONG "
            "obligation is one that is UNSATISFIABLE at an F2P-shaped input: a spec no "
            "implementation could discharge exactly where the behavior matters is "
            "broken in the precondition direction even though the statement binds no "
            "hypothesis. This positive tests that directly — it discharges "
            "`problem_spec_propagateColumns` at the concrete input (one part fixing no "
            "column list of its own, one part fixing its own, with a specific "
            "two-column list requested) BY EVALUATION as a `have`, and only then "
            "closes the frozen obligation with the frozen tactic body verbatim. Both "
            "arms of the branch are live at that single input, so the evaluation "
            "exercises the adopt decision and the used-as-given decision together. If "
            "the `have` FAILED the spec would be unsatisfiable at exactly the shape "
            "the behavior is about => PRECOND-TOO-STRONG. Ports nagini's "
            "cfs-admissibility, whose self-call made the same claim on the "
            "permission-carrying side."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "weak-carry-forward-altered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CARRY_ALTERED,
        "refinement": (
            "The adopting arm hands the REWRITTEN query on as the part definition, so "
            "the part carried forward is the one bearing this evaluation's column list "
            "rather than its own. Its faithful real counterpart is the pre-change "
            "behavior: the requested column list is recorded onto the part definition "
            "that is SHARED across repeated evaluations of the same composed query, "
            "instead of onto a per-evaluation copy of it. A second evaluation of the "
            "same composed query asking for a DIFFERENT column list then finds the part "
            "already carrying a list, takes the used-as-given route, and silently "
            "projects the stale one — which is exactly the F2P regression (the second "
            "single-column projection must yield that one column and would instead "
            "yield the earlier multi-column list). So this rival does NOT resolve, and "
            "if it verified that would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (C), `result.map Prod.snd = parts`: for a part fixing "
            "no column list of its own and a non-empty requested list, the carried-"
            "forward component is the rewritten part, not the input part. Clause (A) "
            "still holds and clause (B) still holds, so (C) alone is what refutes it — "
            "the pure-setting encoding of the aliasing that nagini's cfs-frame-realbug "
            "attacked through read-only permissions. Attacks the `parts` binder on the "
            "fixes-no-list sub-domain with the `composedColumns` binder non-empty. If "
            "it VERIFIES => SPEC-TOO-WEAK (the frame clause would be hollow and the "
            "spec would admit the bug it exists to exclude)."
        ),
        # one part fixing no list of its own + a one-column request: gold carries the
        # input part forward, the rival carries the rewritten one.
        "witness": _wit(_P_NOLIST, '["c"]',
                        "part fixes no list, one column requested: the rival carries "
                        "the rewritten part forward where the spec pins the input part"),
    },
    {
        "id": "weak-never-adopt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEVER_ADOPT,
        "refinement": (
            "The adopting arm degenerates to the used-as-given arm: a part that fixes "
            "no column list of its own is left projecting nothing even though the "
            "composed query requested a specific list. Its faithful real counterpart "
            "takes the per-evaluation copy but never records the requested column list "
            "on it, so the composed query renders its default columns rather than the "
            "requested ones — the F2P projection assertion fails outright. Note this "
            "rival satisfies the frame clause perfectly (it alters nothing at all), so "
            "it is the complement of the case above: it does NOT resolve, and it is "
            "the reason clause (C) cannot be the spec's only pin."
        ),
        "rationale": (
            "REJECTED by clause (B), the `result.map Prod.fst` pin: on a part fixing no "
            "column list with a non-empty request, the spec pins the built query to one "
            "carrying the requested list while the rival returns the part unchanged. "
            "Clauses (A) and (C) hold, so (B) alone refutes it. Attacks the "
            "`composedColumns` binder at a two-element request (a distinct point from "
            "the case above, whose request is one element, since this rival is wrong "
            "for a different reason and on the other output component). Ports the "
            "argument of nagini's cfs-no-setvalues — the per-evaluation query is taken "
            "but the requested list is never recorded on it. It does NOT subsume "
            "nagini's wc-drop-last: this rival adopts no derived list at all, whereas "
            "wc-drop-last adopts the WRONG derived list, and the two coincide at every "
            "request of at most one column. That tighter near-miss ships separately as "
            "`weak-truncate-requested-list`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit(_P_NOLIST, '["a", "b"]',
                        "part fixes no list, two columns requested: the rival builds "
                        "the query without the requested list"),
    },
    {
        "id": "weak-truncate-requested-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRUNCATE_REQUEST,
        "refinement": (
            "The adopting arm records the requested column list with its LAST column "
            "dropped, so the query built for this evaluation projects a list that is "
            "neither the part's own nor the one requested. Its faithful real "
            "counterpart takes the per-evaluation copy and records a truncated form of "
            "the requested column list on it, so the composed query renders one fewer "
            "column than was asked for: a projection of two or more columns comes back "
            "short. The F2P projection assertion compares the projected columns "
            "exactly, so a list one column short fails it — this rival does NOT "
            "resolve. It satisfies the frame clause perfectly (it alters no part "
            "definition), so like the never-adopt rival it isolates clause (B)."
        ),
        "rationale": (
            "REJECTED by clause (B), the `result.map Prod.fst` pin: the spec pins the "
            "built query for an adopting part to one carrying `composedColumns` "
            "EXACTLY, and a proper prefix of that list is not it. Clauses (A) and (C) "
            "hold, so (B) alone refutes it. This is the port of nagini's wc-drop-last, "
            "and it is NOT redundant with `weak-never-adopt`: that rival adopts nothing, "
            "this one adopts the wrong derived list, and the two are pointwise EQUAL at "
            "every request of at most one column — so this is the strictly tighter "
            "near-miss and it is refutable only at a request of two or more columns. "
            "Attacks the `composedColumns` binder at a THREE-element request, a length "
            "no other case in the battery probes, which is also what keeps its witness "
            "point disjoint from `weak-never-adopt`'s two-element one. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the pin would constrain only that SOME list derived from "
            "the request is adopted, not WHICH)."
        ),
        "witness": _wit(_P_NOLIST, '["a", "b", "c"]',
                        "part fixes no list, three columns requested: the rival builds "
                        "the query with the requested list truncated by one column"),
    },
    {
        "id": "weak-overwrite-own-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OVERWRITE_OWN,
        "refinement": (
            "Drops the 'part fixes no column list of its own' half of the branch "
            "condition, so a part that DOES fix its own list is overwritten with the "
            "composed query's list instead of being used as given. Its faithful real "
            "counterpart applies the composed column list unconditionally to every "
            "part, discarding the list a part explicitly projects. That breaks the "
            "surrounding behavior the P2P suite pins — a part built to project its own "
            "columns would silently project the composed query's instead — so it does "
            "NOT resolve; the gold change narrows WHICH parts adopt the list, it does "
            "not widen it."
        ),
        "rationale": (
            "REJECTED by clause (B): the pin's `if` guard has TWO conjuncts, and the "
            "spec pins a part with a non-empty own column list to the used-as-given "
            "arm (built query = the input part). The rival overwrites it. Attacks the "
            "`parts` binder on the fixes-its-OWN-list sub-domain — the half of that "
            "binder's domain no other rival's witness reaches at all. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the first conjunct of the guard would be untested and "
            "an impl ignoring it would pass)."
        ),
        "witness": _wit(_P_OWNLIST, '["c"]',
                        "part fixes its own list: the rival overwrites it with the "
                        "requested list where the spec pins it to the input part"),
    },
    {
        "id": "weak-drop-used-as-given-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_GIVEN,
        "refinement": (
            "Emits NO entry for a part that takes the used-as-given route, so that part "
            "contributes neither a built query nor a carried-forward definition. Its "
            "faithful real counterpart silently omits such a part from the evaluation, "
            "which loses one component of the composed query entirely; the composed "
            "result would then be built from fewer parts than it has, so it does NOT "
            "resolve — and a part dropped from the result has no definition carried "
            "forward either, which is the same staleness exposure by omission."
        ),
        "rationale": (
            "REJECTED by clause (A), `result.length = parts.length`, and by clause (C) "
            "with it: the result is shorter than the input part list, so the "
            "carried-forward list cannot equal `parts`. Attacks the `composedColumns` "
            "binder at the EMPTY request — the sub-domain where no part adopts anything "
            "and every part takes the used-as-given route, which no other witness "
            "probes. If it VERIFIES => SPEC-TOO-WEAK (the one-entry-per-part clause "
            "would be hollow)."
        ),
        "witness": _wit(_P_OWNLIST, "[]",
                        "no column list requested: the rival emits no entry for a part "
                        "the spec requires one for"),
    },
    {
        "id": "weak-blank-carry-used-as-given",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BLANK_CARRY_GIVEN,
        "refinement": (
            "On the used-as-given arm the built query is correct but the part "
            "definition carried forward is a BLANK one, projecting no columns. Its "
            "faithful real counterpart overwrites a part definition it never needed to "
            "touch — the branch that adopts nothing — with an emptied one, so a later "
            "evaluation of the same composed query finds that part projecting nothing "
            "and cannot recover the list it was defined with. It does NOT resolve: the "
            "part definitions are shared across evaluations, so blanking one on the "
            "pass-through branch is the same class of carried-forward corruption as "
            "rewriting one on the adopting branch, reached from the other side."
        ),
        "rationale": (
            "REJECTED by clause (C), `result.map Prod.snd = parts`. AUDIT ADDITION: "
            "every other rival that attacks (C) does so on the ADOPTING arm "
            "(`weak-carry-forward-altered` carries the rewritten part; "
            "`weak-drop-used-as-given-entry` removes the entry outright and is caught "
            "by (A) first), so the frame conjunct was demonstrated only where the impl "
            "rewrites something. This rival pins (C) on the pass-through branch — a "
            "part used exactly as given must still have its definition carried forward "
            "unchanged — while clauses (A) and (B) both still hold, so (C) alone "
            "refutes it. Attacks the `parts` binder on the fixes-its-OWN-list "
            "sub-domain against a non-empty request, the one point where the "
            "used-as-given arm is taken while adoption is otherwise enabled. If it "
            "VERIFIES => SPEC-TOO-WEAK (the frame clause would constrain only the "
            "branch that rewrites a part, leaving the other branch's carried-forward "
            "component free)."
        ),
        "witness": _wit(_P_OWNLIST, '["c"]',
                        "part fixes its own list, so the used-as-given arm is taken: "
                        "the rival carries a blank part definition forward where the "
                        "spec pins the input part"),
    },
    {
        "id": "weak-adopt-first-part-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRST_ONLY,
        "refinement": (
            "Adopts the requested column list for the FIRST eligible part only; every "
            "later eligible part is used as given. Its faithful real counterpart "
            "records the requested list once and then treats the composed query as "
            "already settled, so the remaining parts of the composed query project "
            "their default columns. A composed query over more than one such part then "
            "combines parts whose projections disagree, so it does NOT resolve. This is "
            "a NEAR-MISS of the frozen behavior: it agrees with it on every "
            "single-part input, which is why it is refuted at a two-part point rather "
            "than sharing a witness with the rivals above."
        ),
        "rationale": (
            "REJECTED by clause (B): the pin is a pointwise map over `parts`, so EVERY "
            "eligible part must adopt the requested list, not just the first. Attacks "
            "the `parts` binder in its LENGTH/position dimension — a multi-part input "
            "where a rival that is right about the first part is still wrong about the "
            "second. If it VERIFIES => SPEC-TOO-WEAK (the pin would only constrain a "
            "prefix, and a per-evaluation copy taken once instead of per part would "
            "pass)."
        ),
        "witness": _wit(_P_NOLIST2, '["c"]',
                        "two parts both fixing no list: the rival adopts the requested "
                        "list only for the first"),
    },
    {
        "id": "weak-reversed-correspondence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSED,
        "refinement": (
            "Builds the entry list back-to-front. The number of entries is right and "
            "the entries are the right ones as a MULTISET, but each is attributed to "
            "the wrong part. Its faithful real counterpart pairs each part's built "
            "query with a different part's definition, so a part that fixes its own "
            "column list would be built from another part's, and the composed query "
            "would combine parts in an order the caller did not ask for. It does NOT "
            "resolve. Included because a spec that pinned only lengths and multisets "
            "would admit it while the F2P behavior does not."
        ),
        "rationale": (
            "REJECTED by clauses (B) and (C) jointly, both of which are POSITIONAL "
            "equalities of mapped lists (`result.map Prod.fst = parts.map …` and "
            "`result.map Prod.snd = parts`), not multiset or length claims. Attacks the "
            "`parts` binder on a MIXED input — one part fixing no list, one fixing its "
            "own — where reversal is observable; on a homogeneous input this rival "
            "agrees with the frozen behavior, which is why its witness sits at a point "
            "no other case uses. If it VERIFIES => SPEC-TOO-WEAK (the per-part "
            "correspondence would be unpinned)."
        ),
        "witness": _wit(_P_MIXED, '["c"]',
                        "mixed parts, one column requested: the rival attributes each "
                        "entry to the wrong part"),
    },
]


# No consumed callee axiom and no axiomatized reference (meta.axioms == []): a part is
# observed solely by the list of columns it projects, so the callees the modeled step
# uses contribute nothing beyond that list and need no contract. The axiom lane is
# G-AX's job regardless; this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
