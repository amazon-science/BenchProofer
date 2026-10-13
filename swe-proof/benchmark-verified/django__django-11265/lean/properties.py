"""properties.py — PBT falsification manifest for django__django-11265 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY an implementation region (and,
for the positives, the matching proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
This bundle models TWO decisions, each with its own obligation:

    implementation_buildInnerQuery (selfModel : String)
        (selfFilteredRelations : List (String × String))
        (filterExpr : String × String) : InnerQuery

    implementation_selectInnerJoin (firstJoin : JoinProps)
        (relatedFields : List (String × String))
        (aliasOriginal aliasCollapsed : String) : JoinSelection

`problem_spec_buildInnerQuery` pins the WHOLE construction as a composition
applied in a fixed order —

    result = clearOrdering (addFilter
      (withFilteredRelations (freshInnerQuery selfModel) selfFilteredRelations)
      filterExpr)

— and then spells out four framing consequences: `result.model`,
`result.filteredRelations`, `result.appliedFilters`, `result.orderingCleared`.
The load-bearing part is that `addFilter` SNAPSHOTS the named-relation context
present at the moment it runs, so pinning `result.appliedFilters` to
`[(filterExpr, selfFilteredRelations)]` pins the ORDER of the composition, not
merely its final field values. An impl that installs the relations after
applying the filter agrees on every other component and is separated only by
that snapshot.

`problem_spec_selectInnerJoin` is a two-armed implication over the derived
condition `canCollapse = (!keepsOuterRows) && (!carriesRelationCondition)`; each
arm pins BOTH output components (`selectFields` and `selectAlias`) to a
different projection of `relatedFields` and a different one of the two aliases.
So the spec is attackable in three independent places: the condition itself, the
near/far projection choice, and the alias choice.

Both carriers are FULLY TRANSPARENT — every helper (`freshInnerQuery`,
`withFilteredRelations`, `addFilter`, `clearOrdering`, and the boolean guard) is
a concrete deep model over plain `String`/`List`/`Bool`/structure data. There is
no `opaque` callee and no axiom, so no carrier conditioning is needed: every
witness below states the negated spec predicate at concrete literals and closes
by `decide`. Correspondingly every witness's hypothesis set is EMPTY, so the
`witness-inconsistent` failure mode cannot arise here.

PORTING NOTES (which nagini cases port, which are omitted and why)
-----------------------------------------------------------------
The nagini sibling models the same two behaviors but over a different carrier:
its site 1 is a list-copy loop under `ToSeq(Result()) == ToSeq(outer_relations)`,
and its site 2 is a list-prefix builder under four `Implies` clauses. The lean
bundle models site 1 as a whole-construction composition (so ORDER is
observable, which nagini's value-equality carrier cannot see) and site 2 as a
two-armed implication over a derived boolean. The arguments port; the mechanics
are re-expressed.

  * `s1-empty-registry` -> `omit-relation-carry`. Nagini returned the empty
    list; here the rival simply omits the install step, which is the same
    pre-gold behavior on this carrier and the exact discriminating weakness.
  * `s1-drop-first-alias` -> `drop-first-relation`; `s1-drop-last-alias` ->
    `drop-last-relation`. Both port directly as partial-domain attacks on the
    `selfFilteredRelations` binder.
  * `s2-real-bug` -> `ignore-relation-condition`. The headline site-2 weakness:
    the collapse condition consults only whether the join keeps outer rows,
    ignoring whether it carries a relation-level condition.
  * `s2-never-trim` -> `never-collapse` (over-retention: never collapse, even
    when the spec's first arm demands it).
  * `s2-inverted-filter` -> `inverted-relation-condition` (the relation-condition
    conjunct used with the wrong polarity).
  * `s2-drop-downstream` -> `drop-last-field`. Nagini lost a trailing element of
    the downstream-condition list; here the analogue is losing a trailing element
    of the selected-field list, which is the same "correct decision, mangled
    payload" attack against the output component the decision rivals hold fixed.
  * `s1-pos-control` -> `pos-clear-first` and `pos-record-literal`;
    `s2-pos-control` -> `pos-demorgan`. Structurally different but CORRECT impls,
    each with its proof honestly re-closed for the new shape (no obligation was
    weakened, no lemma added; see the per-case rationale for the tactic).
  * `s1-frame-mutation` and `s2-frame-mutation` are VACUOUS on this carrier.
    They attack a write through a half-permission reference; Lean is
    referentially transparent, so there is no aliasing to abuse and no fractional
    permission to violate. Nagini's frame obligation is discharged here
    STRUCTURALLY instead — the spec spells out every output component — and that
    structural framing is what `wrong-model`, `omit-ordering-clear` and
    `swap-filter-components` attack: each drops or mangles a component the
    equality pins, which is the lean-carrier counterpart of the frame hole. No
    substitute was fabricated for the permission mechanics themselves.
  * `s1-admissibility` -> `admiss-relation-context`; `s2-admissibility` ->
    `admiss-retained-join`. These DO port, and an earlier revision of this
    manifest was wrong to drop them. The reason it gave — that both lean
    obligations are `∀ <binders>, problem_spec_... (implementation_... ...)`
    with no precondition hypothesis, so there is no precondition to be too
    strong — describes the absence of nagini's MECHANISM, not the absence of the
    lane. On a total carrier the analogue of PRECOND-TOO-STRONG is the
    obligation being UNSATISFIABLE at an F2P-shaped input, which a positive that
    discharges the obligation at that concrete input — by evaluation, as a
    `have`, before closing the frozen obligation verbatim — tests directly.
    Dropping the lane silently removed one of the three directions this gate
    exists to test, and the coverage reporter flagged it as a finding. Both
    cases are now landed, each two-sided (see their rationales).
  * Divergence / non-termination: the nagini sibling carries no such case, and
    the class is genuinely vacuous here regardless — both `implementation_*` are
    total Lean `def`s, so a diverging implementation cannot be written at all.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.
    (This bundle declares no axioms anyway.)

Cases with NO nagini counterpart, added to close binder-coverage gaps the ported
set leaves open (a binder every witness holds fixed is a binder no rival was
built to abuse):
  * `filter-before-carry` — attacks the composition ORDER, which nagini's carrier
    could not express at all.
  * `wrong-model`, `swap-filter-components` — the `selfModel` and `filterExpr`
    binders.
  * `ignore-outer-rows`, `swap-field-side`, `swap-alias` — the other half of the
    collapse condition, the near/far projection, and the alias choice.
  * `else-arm-alias`, `else-arm-field-side` — added by the independent AUDIT of
    this battery. The ported set's payload rivals all mangle the COLLAPSE arm, so
    the second arm's two pinned components (`selectFields` to the far side,
    `selectAlias` to the original alias) were attacked by no rival at all: an
    impl correct on the decision and on the collapse arm but wrong when the
    collapse is refused would have verified unnoticed. These two also carry the
    battery's only witnesses at keepsOuterRows=true together with
    carriesRelationCondition=true, which is what takes the guard's domain
    coverage from three of four condition points to all four.

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligations
removed. Each was built BOTH ways with scripts/lean_verify.sh and SEEN to
elaborate against its rival (exit 0) and fail against the frozen solution
(exit 1, `decide` reporting the proposition is false).
"""
from pathlib import Path

INSTANCE = "django__django-11265"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl/proof-region substring, and
    assert it matched uniquely so silent drift (Solution.lean edited) fails
    loudly rather than producing a variant that tests nothing."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — every one lies strictly INSIDE an `impl` region, or (for
# the positives) inside the matching `proof` region. The `theorem correct_*`
# STATEMENTS and the whole spec view are never touched.
# ---------------------------------------------------------------------------

# --- buildInnerQuery impl region ---
_B_FRESH = "  let mut query : InnerQuery := freshInnerQuery selfModel\n"
_B_CARRY = "  query := withFilteredRelations query selfFilteredRelations\n"
_B_FILTER = "  query := addFilter query filterExpr\n"
_B_CLEAR = "  query := clearOrdering query\n"
_B_SIG = (
    "def implementation_buildInnerQuery\n"
    "    (selfModel : String) (selfFilteredRelations : List (String × String))\n"
    "    (filterExpr : String × String) : InnerQuery := Id.run do\n"
)
_B_BODY = (
    "  -- A fresh inner query bound to the same model (no named relations yet).\n"
    "  let mut query : InnerQuery := freshInnerQuery selfModel\n"
    "  -- Carry the originating query's named relation definitions onto the inner query\n"
    "  -- so a filter referencing one of them can be resolved here.\n"
    "  query := withFilteredRelations query selfFilteredRelations\n"
    "  -- Apply the supplied filter clause (resolved against the relations now present).\n"
    "  query := addFilter query filterExpr\n"
    "  -- Drop any ordering.\n"
    "  query := clearOrdering query\n"
    "  return query"
)

# --- buildInnerQuery proof body (frozen tactic script) ---
_B_PROOF = (
    "  intro selfModel selfFilteredRelations filterExpr\n"
    "  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery\n"
    "  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,\n"
    "    List.nil_append]\n"
    "  refine ⟨rfl, rfl, rfl, rfl, rfl⟩"
)

# --- selectInnerJoin impl region ---
_S_GUARD = (
    "  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)\n"
    "  if canCollapse then\n"
)
_S_COLLAPSE_ARM = (
    "    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }\n"
)
_S_NOCOLLAPSE_ARM = (
    "    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }\n"
)
_S_BODY = (
    "  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)\n"
    "  if canCollapse then\n"
    "    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }\n"
    "  else\n"
    "    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }"
)

# --- selectInnerJoin proof body (frozen tactic script) ---
_S_PROOF = (
    "  intro firstJoin relatedFields aliasOriginal aliasCollapsed\n"
    "  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin\n"
    "  simp only [Id.run]\n"
    "  split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-clear-first) The ordering is dropped FIRST, before the named relations are
# installed and the filter applied. Observationally identical (the ordering flag
# and the relation/filter components are independent slots), but a different
# statement order. The proof body is unchanged because the frozen script is
# order-agnostic once the helpers are unfolded — it still closes, which is the
# honest outcome, not a weakened obligation.
_POS_CLEAR_FIRST = _swap(
    _BASE, _B_BODY,
    "  let mut query : InnerQuery := freshInnerQuery selfModel\n"
    "  query := clearOrdering query\n"
    "  query := withFilteredRelations query selfFilteredRelations\n"
    "  query := addFilter query filterExpr\n"
    "  return query",
)

# (pos-record-literal) A CORRECT impl in a completely different shape: no
# imperative do-block and no helper composition at all — the result record is
# written out directly, field by field. This is the strongest available soundness
# positive because it shares no syntactic structure with the frozen impl, so if
# the spec were over-fit to the compositional form it would fail here. The proof
# is re-closed (a single `simp` over the four helper definitions); the theorem
# statement is byte-identical.
_POS_RECORD_LITERAL = _swap(
    _swap(
        _BASE, _B_SIG + _B_BODY,
        "def implementation_buildInnerQuery\n"
        "    (selfModel : String) (selfFilteredRelations : List (String × String))\n"
        "    (filterExpr : String × String) : InnerQuery :=\n"
        "  { model := selfModel, filteredRelations := selfFilteredRelations,\n"
        "    appliedFilters := [(filterExpr, selfFilteredRelations)], orderingCleared := true }",
    ),
    _B_PROOF,
    "  intro selfModel selfFilteredRelations filterExpr\n"
    "  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery\n"
    "  simp [freshInnerQuery, withFilteredRelations, addFilter, clearOrdering]",
)

# (pos-demorgan) The collapse condition is expressed as its De Morgan dual — a
# `mustKeep` disjunction — with the two branches consequently SWAPPED. Logically
# the same partition of the input space, opposite branch order. Correct, and the
# proof is re-closed by case-splitting both booleans; the theorem statement is
# byte-identical.
_POS_DEMORGAN = _swap(
    _swap(
        _BASE, _S_BODY,
        "  let mustKeep := firstJoin.keepsOuterRows || firstJoin.carriesRelationCondition\n"
        "  if mustKeep then\n"
        "    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }\n"
        "  else\n"
        "    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }",
    ),
    _S_PROOF,
    "  intro firstJoin relatedFields aliasOriginal aliasCollapsed\n"
    "  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin\n"
    "  simp only [Id.run]\n"
    "  cases hk : firstJoin.keepsOuterRows <;> cases hc : firstJoin.carriesRelationCondition <;>\n"
    "    simp_all [pure]",
)


# ===========================================================================
# ADMISSIBILITY (precond-too-strong probes) — expect "verify"
# ===========================================================================
# Both obligations are bare universals with no precondition hypothesis, so there
# is no `Requires` clause to be too strong. That is the absence of nagini's
# MECHANISM, not of the lane: on a total carrier the counterpart of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at an F2P-shaped
# input. Each case below discharges its obligation at one such input BY
# EVALUATION, as `have`s inside the existing tactic body, and then closes the
# frozen obligation verbatim. Nothing is assumed: no new declaration, no lemma,
# no `sorry`, and the `theorem correct_*` statements stay byte-identical.
#
# Each is THREE-sided so it cannot pass as a definitional tautology about
# whatever the impl happens to return:
#   (a) the spec HOLDS at the input;
#   (b) the impl's value there is pinned to concrete literals;
#   (c) the spec REFUSES, at that same input, the specific wrong answer the
#       corresponding pre-fix behavior would produce.
# Flipping (b) or (c) makes the case fail — measured, not asserted.

# (admiss-relation-context) The F2P-shaped input for the construction: a
# NON-EMPTY named-relation set together with a clause that references one of
# those relations by its alias. That pairing is the configuration the modeled
# behavior exists to serve; if the clause set could not be satisfied there, the
# obligation would be discharged over a domain excluding the load-bearing point.
_ADM_RELATION_CONTEXT = _swap(
    _BASE, _B_PROOF,
    "  -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped input --\n"
    "  -- a non-empty named-relation set plus a clause referencing one of those\n"
    "  -- relations by alias -- discharged by evaluation before the frozen script.\n"
    '  have _adm_holds : problem_spec_buildInnerQuery "AM" [("rel_a", "cond_a")]\n'
    '      ("rel_a__leaf", "target")\n'
    '      (implementation_buildInnerQuery "AM" [("rel_a", "cond_a")]\n'
    '        ("rel_a__leaf", "target")) := by\n'
    "    unfold problem_spec_buildInnerQuery implementation_buildInnerQuery\n"
    "    decide\n"
    "  -- The value at that input, pinned to literals, so the line above asserts\n"
    "  -- something about the result and not merely about its own subject.\n"
    '  have _adm_pinned : implementation_buildInnerQuery "AM" [("rel_a", "cond_a")]\n'
    '      ("rel_a__leaf", "target")\n'
    '      = { model := "AM", filteredRelations := [("rel_a", "cond_a")],\n'
    '          appliedFilters := [(("rel_a__leaf", "target"), [("rel_a", "cond_a")])],\n'
    "          orderingCleared := true } := by\n"
    "    unfold implementation_buildInnerQuery\n"
    "    decide\n"
    "  -- At that SAME input the spec refuses the answer whose applied-filter entry\n"
    "  -- snapshots an empty relation context, so the clause set is discriminating\n"
    "  -- there rather than satisfied by anything.\n"
    '  have _adm_refuses : ¬ problem_spec_buildInnerQuery "AM" [("rel_a", "cond_a")]\n'
    '      ("rel_a__leaf", "target")\n'
    '      { model := "AM", filteredRelations := [("rel_a", "cond_a")],\n'
    '        appliedFilters := [(("rel_a__leaf", "target"), [])],\n'
    "        orderingCleared := true } := by\n"
    "    unfold problem_spec_buildInnerQuery\n"
    "    decide\n"
    + _B_PROOF)

# (admiss-retained-join) The F2P-shaped input for the decision: the leading join
# that keeps no outer rows but DOES carry a relation-level condition — the point
# at which the collapse must be refused, and the one the modeled behavior turns
# on. Both arms of the implication have to be jointly satisfiable there.
_ADM_RETAINED_JOIN = _swap(
    _BASE, _S_PROOF,
    "  -- ADMISSIBILITY: the two-armed clause set is SATISFIABLE at an F2P-shaped\n"
    "  -- input -- a leading join carrying a relation-level condition and keeping no\n"
    "  -- outer rows, i.e. the point at which the collapse must be refused.\n"
    "  have _adm_holds : problem_spec_selectInnerJoin\n"
    "      { keepsOuterRows := false, carriesRelationCondition := true }\n"
    '      [("near_a", "far_a")] "AO" "AC"\n'
    "      (implementation_selectInnerJoin\n"
    "        { keepsOuterRows := false, carriesRelationCondition := true }\n"
    '        [("near_a", "far_a")] "AO" "AC") := by\n'
    "    unfold problem_spec_selectInnerJoin implementation_selectInnerJoin\n"
    "    decide\n"
    "  -- The selection at that input, pinned to literals.\n"
    "  have _adm_pinned : implementation_selectInnerJoin\n"
    "      { keepsOuterRows := false, carriesRelationCondition := true }\n"
    '      [("near_a", "far_a")] "AO" "AC"\n'
    '      = { selectFields := ["far_a"], selectAlias := "AO" } := by\n'
    "    unfold implementation_selectInnerJoin\n"
    "    decide\n"
    "  -- And at that SAME input the spec refuses the COLLAPSED answer, so the\n"
    "  -- satisfiable point is the discriminating one.\n"
    "  have _adm_refuses : ¬ problem_spec_selectInnerJoin\n"
    "      { keepsOuterRows := false, carriesRelationCondition := true }\n"
    '      [("near_a", "far_a")] "AO" "AC"\n'
    '      { selectFields := ["near_a"], selectAlias := "AC" } := by\n'
    "    unfold problem_spec_selectInnerJoin\n"
    "    decide\n"
    + _S_PROOF)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# --- buildInnerQuery: the construction ---

# (omit-relation-carry) The install step is dropped entirely: the inner query
# keeps the fresh empty named-relation set. THE discriminating weakness on this
# obligation.
_R_OMIT_CARRY = _swap(_BASE, _B_CARRY, "")

# (filter-before-carry) The relations ARE installed, but AFTER the filter is
# applied. Every final field value except the snapshot agrees with gold; only
# `result.appliedFilters` separates them.
_R_FILTER_FIRST = _swap(
    _BASE, _B_BODY,
    "  let mut query : InnerQuery := freshInnerQuery selfModel\n"
    "  query := addFilter query filterExpr\n"
    "  query := withFilteredRelations query selfFilteredRelations\n"
    "  query := clearOrdering query\n"
    "  return query",
)

# (drop-first-relation) Installs the named relations minus the first one.
_R_DROP_FIRST = _swap(
    _BASE, _B_CARRY,
    "  query := withFilteredRelations query (selfFilteredRelations.drop 1)\n")

# (drop-last-relation) Installs the named relations minus the last one.
_R_DROP_LAST = _swap(
    _BASE, _B_CARRY,
    "  query := withFilteredRelations query selfFilteredRelations.dropLast\n")

# (omit-ordering-clear) Correct on the relation/filter components; the ordering
# is never dropped. Attacks the `orderingCleared` component of the equality.
_R_OMIT_CLEAR = _swap(_BASE, _B_CLEAR, "")

# (wrong-model) The inner query is bound to a constant rather than the supplied
# model. Attacks the `selfModel` binder, which every other witness holds at a
# value the rival happens to reproduce.
_R_WRONG_MODEL = _swap(
    _BASE, _B_FRESH,
    '  let mut query : InnerQuery := freshInnerQuery ""\n')

# (swap-filter-components) The two components of the filter clause are applied
# transposed. Attacks the `filterExpr` binder.
_R_SWAP_FILTER = _swap(
    _BASE, _B_FILTER,
    "  query := addFilter query (filterExpr.2, filterExpr.1)\n")

# --- selectInnerJoin: the collapse decision ---

# (ignore-relation-condition) The condition consults only whether the join keeps
# outer rows; the relation-condition observable is never read. Correct on the
# whole `carriesRelationCondition = false` sub-domain, WRONG whenever it is set.
_R_IGNORE_RELCOND = _swap(
    _BASE, _S_GUARD,
    "  let canCollapse := (!firstJoin.keepsOuterRows)\n  if canCollapse then\n")

# (ignore-outer-rows) The mirror-image partial-domain rival: only the
# relation-condition half of the condition is consulted, so an outer-keeping join
# is collapsed. Varies the `keepsOuterRows` binder the other decision rivals hold
# at false.
_R_IGNORE_OUTER = _swap(
    _BASE, _S_GUARD,
    "  let canCollapse := (!firstJoin.carriesRelationCondition)\n  if canCollapse then\n")

# (never-collapse) Over-retention: the collapse is never taken, even on the
# sub-domain where the spec's first arm demands it.
_R_NEVER_COLLAPSE = _swap(
    _BASE, _S_GUARD, "  let canCollapse := false\n  if canCollapse then\n")

# (inverted-relation-condition) The relation-condition conjunct is used with the
# WRONG polarity: collapse iff the join keeps no outer rows AND carries a
# relation condition. Wrong on both halves of that split.
_R_INVERTED = _swap(
    _BASE, _S_GUARD,
    "  let canCollapse := (!firstJoin.keepsOuterRows) && firstJoin.carriesRelationCondition\n"
    "  if canCollapse then\n")

# (swap-field-side) Correct decision, wrong projection: the collapse arm selects
# the FAR-side names where the spec pins the near side. Attacks the
# `relatedFields` binder and the `selectFields` component.
_R_SWAP_SIDE = _swap(
    _BASE, _S_COLLAPSE_ARM,
    "    return { selectFields := relatedFields.map (·.2), selectAlias := aliasCollapsed }\n")

# (swap-alias) Correct decision and projection, wrong alias: the collapse arm
# selects against the ORIGINAL alias where the spec pins the collapsed one.
# Attacks the two alias binders, which the projection rivals hold fixed.
_R_SWAP_ALIAS = _swap(
    _BASE, _S_COLLAPSE_ARM,
    "    return { selectFields := relatedFields.map (·.1), selectAlias := aliasOriginal }\n")

# (drop-last-field) Correct decision, correct projection, but the final selected
# name is lost. The payload-mangling analogue of nagini's dropped trailing
# downstream condition.
_R_DROP_FIELD = _swap(
    _BASE, _S_COLLAPSE_ARM,
    "    return { selectFields := (relatedFields.map (·.1)).dropLast,"
    " selectAlias := aliasCollapsed }\n")

# --- second-arm payload rivals (added by audit) ---
# Every payload rival above mangles the COLLAPSE arm, so the second arm's two
# pinned components had no rival of their own: an impl correct on the decision and
# on the collapse arm but wrong in the no-collapse arm was unattacked. These two
# close that, and they are also the only rivals refuted at a condition point
# involving carriesRelationCondition=true together with keepsOuterRows=true.

# (else-arm-alias) Correct everywhere except the no-collapse arm's ALIAS: the
# far-side names are selected, but against the collapsed alias the spec's second
# arm forbids there.
_R_ELSE_ALIAS = _swap(
    _BASE, _S_NOCOLLAPSE_ARM,
    "    return { selectFields := relatedFields.map (·.2), selectAlias := aliasCollapsed }\n")

# (else-arm-field-side) Correct everywhere except the no-collapse arm's
# PROJECTION: the near-side names are selected where the second arm pins the far
# side. Refuted at (true, true) — the condition point no other witness reaches.
_R_ELSE_SIDE = _swap(
    _BASE, _S_NOCOLLAPSE_ARM,
    "    return { selectFields := relatedFields.map (·.1), selectAlias := aliasOriginal }\n")


# ---------------------------------------------------------------------------
# WITNESSES — each negates the spec predicate at one concrete input and closes
# by `decide` (the carrier is fully transparent; no hypotheses, hence no
# consistency question). Checked in a file with the frozen obligations removed.
# ---------------------------------------------------------------------------

def _wit_build(model: str, rels: str, lhs: str, rhs: str) -> str:
    return (
        f'example : ¬ problem_spec_buildInnerQuery "{model}" {rels} ("{lhs}", "{rhs}")\n'
        f'    (implementation_buildInnerQuery "{model}" {rels} ("{lhs}", "{rhs}")) := by\n'
        "  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery\n"
        "  decide"
    )


def _wit_join(keeps: str, carries: str, fields: str,
              ao: str, ac: str) -> str:
    j = (f"{{ keepsOuterRows := {keeps},"
         f" carriesRelationCondition := {carries} }}")
    return (
        "example : ¬ problem_spec_selectInnerJoin\n"
        f"    {j}\n"
        f'    {fields} "{ao}" "{ac}"\n'
        "    (implementation_selectInnerJoin\n"
        f"      {j}\n"
        f'      {fields} "{ao}" "{ac}") := by\n'
        "  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin\n"
        "  decide"
    )


# Each build-site witness probes a DIFFERENT point: a different model string, a
# different named-relation list (including the empty one, and two-element lists
# where the head/last attacks need them), and a different filter clause. Holding
# any of these fixed across the set would leave a binder no rival probes.
_W_OMIT_CARRY = _wit_build("M1", '[("author", "c1")]', "f", "v")
_W_FILTER_FIRST = _wit_build("M2", '[("book", "c2")]', "g", "w")
_W_DROP_FIRST = _wit_build("M3", '[("p", "c1"), ("q", "c2")]', "h", "x")
_W_DROP_LAST = _wit_build("M4", '[("r", "c3"), ("s", "c4")]', "i", "y")
# The empty relation list: this rival is wrong regardless of the relation set, so
# its witness probes the degenerate value none of the others reach.
_W_OMIT_CLEAR = _wit_build("M5", "[]", "j", "z")
_W_WRONG_MODEL = _wit_build("M6", '[("t", "c5")]', "k", "u")
# Asymmetric clause components, so the transposition is actually observable.
_W_SWAP_FILTER = _wit_build("M7", '[("v", "c6")]', "lhs", "rhs")

# The join-site witnesses span three of the four condition points —
# (false, true), (false, false) and (true, false) — so no rival is refuted only
# where another already is, and the `keepsOuterRows` / `carriesRelationCondition`
# binders both move across the set. Field lists and alias pairs also differ per
# witness so those binders are varied too.
_W_IGNORE_RELCOND = _wit_join("false", "true", '[("n1", "f1")]', "T1", "T2")
_W_NEVER_COLLAPSE = _wit_join("false", "false", '[("n2", "f2")]', "U1", "U2")
_W_INVERTED = _wit_join("false", "true",
                        '[("n3", "f3"), ("n4", "f4")]', "V1", "V2")
_W_IGNORE_OUTER = _wit_join("true", "false", '[("n5", "f5")]', "W1", "W2")
_W_SWAP_SIDE = _wit_join("false", "false", '[("n6", "f6")]', "X1", "X2")
_W_SWAP_ALIAS = _wit_join("false", "false", '[("n7", "f7")]', "Y1", "Y2")
_W_DROP_FIELD = _wit_join("false", "false",
                          '[("n8", "f8"), ("n9", "f9")]', "Z1", "Z2")
# The second-arm rivals are wrong only where the collapse is REFUSED, so their
# witnesses sit in the no-collapse half of the domain. `else-arm-field-side` takes
# (true, true) — the fourth condition point, which no other witness in this
# battery reaches, so with these two cases all four points of the guard's domain
# are probed.
_W_ELSE_ALIAS = _wit_join("true", "false", '[("na", "fa")]', "P1", "P2")
_W_ELSE_SIDE = _wit_join("true", "true", '[("nb", "fb")]', "R1", "R2")


SPEC_TESTS = [
    # ================= POSITIVE CONTROLS (must VERIFY) =================
    {"id": "pos-clear-first", "kind": "soundness", "expect": "verify",
     "module": _POS_CLEAR_FIRST,
     "rationale": "A correct impl that drops the ordering FIRST, before installing the named "
                  "relations and applying the filter. The equality clause constrains the "
                  "relative order of the install and the filter (via the snapshot recorded in "
                  "`result.appliedFilters`) but says nothing about where the ordering flag is "
                  "set, so this must verify. If it failed, the spec would be over-fit to one "
                  "statement order => SPEC-TOO-STRONG. The frozen proof body still closes "
                  "unchanged; the theorem statement is byte-identical. Built and seen to "
                  "elaborate (exit 0)."},
    {"id": "pos-record-literal", "kind": "soundness", "expect": "verify",
     "module": _POS_RECORD_LITERAL,
     "rationale": "A correct impl in a completely different SHAPE: no imperative do-block and "
                  "no helper composition — the result record is written out field by field. It "
                  "shares no syntactic structure with the frozen impl, so it is the strongest "
                  "available check that the spec pins BEHAVIOR rather than the compositional "
                  "form; a failure would be SPEC-TOO-STRONG. The proof is honestly re-closed "
                  "for the new shape with a single `simp` over the four helper definitions — no "
                  "lemma added, no `sorry`, no obligation weakened, statement byte-identical. "
                  "Built and seen to elaborate (exit 0)."},
    {"id": "pos-demorgan", "kind": "soundness", "expect": "verify",
     "module": _POS_DEMORGAN,
     "rationale": "A correct impl expressing the collapse condition as its De Morgan dual (a "
                  "`mustKeep` disjunction) with the two branches consequently swapped — the "
                  "same partition of the input space, opposite branch order. Both spec arms are "
                  "stated over the derived condition, not over a branch order, so this must "
                  "verify; a failure would be SPEC-TOO-STRONG. The proof is honestly re-closed "
                  "by case-splitting both booleans, statement byte-identical. Built and seen to "
                  "elaborate (exit 0)."},

    # =============== ADMISSIBILITY (must VERIFY) ===============
    {"id": "admiss-relation-context", "kind": "admissibility", "expect": "verify",
     "module": _ADM_RELATION_CONTEXT,
     "rationale": "The ADMISSIBILITY lane for the construction obligation, which an earlier "
                  "revision of this manifest dropped as vacuous on the ground that the "
                  "obligation carries no precondition hypothesis. That reason was wrong: it "
                  "describes the absence of nagini's `Requires` MECHANISM, not the absence of "
                  "the lane. On this total carrier the counterpart of PRECOND-TOO-STRONG is the "
                  "obligation being UNSATISFIABLE at an F2P-shaped input, so this case "
                  "discharges it at one — a NON-EMPTY named-relation set together with a clause "
                  "that references one of those relations by its alias, which is the "
                  "configuration the modeled behavior exists to serve. Three-sided, so it is not "
                  "a tautology about whatever the impl returns: the spec HOLDS there, the impl's "
                  "value there is pinned to concrete literals, and the spec REFUSES at that same "
                  "input the answer whose applied-filter entry snapshots an empty relation "
                  "context. All three are `have`s closed by `decide` inside the existing tactic "
                  "body; the frozen script then closes the obligation verbatim, the statement is "
                  "byte-identical, and no declaration, lemma or `sorry` is added. If this FAILED "
                  "=> PRECOND-TOO-STRONG (the clause set cannot be met at a shape the change "
                  "must handle). Built and seen to elaborate (exit 0); flipping the refusal "
                  "clause makes the case FAIL (exit 1), which is what shows the `have`s are "
                  "load-bearing rather than inert."},
    {"id": "admiss-retained-join", "kind": "admissibility", "expect": "verify",
     "module": _ADM_RETAINED_JOIN,
     "rationale": "The same lane for the decision obligation, and dropped by the same wrong "
                  "reason. The F2P-shaped input is the leading join that keeps no outer rows but "
                  "DOES carry a relation-level condition — the condition point at which the "
                  "collapse must be refused, and the one the modeled behavior turns on. Both "
                  "arms of the two-armed implication must be jointly satisfiable there, which a "
                  "spec whose arms overlapped inconsistently would fail. Three-sided as above: "
                  "the clause set holds at that input, the selection there is pinned to concrete "
                  "literals, and the COLLAPSED answer is refused at that same input, so the "
                  "satisfiable point is also the discriminating one. Statement byte-identical, "
                  "nothing assumed. A failure would be PRECOND-TOO-STRONG. Built and seen to "
                  "elaborate (exit 0); flipping either the pinned value or the refusal clause "
                  "makes the case FAIL (exit 1), measured, so neither `have` is inert."},

    # ============ UNIQUENESS: the construction (must be REJECTED) ============
    {"id": "omit-relation-carry", "kind": "uniqueness", "expect": "reject",
     "module": _R_OMIT_CARRY,
     "witness": _W_OMIT_CARRY,
     "refinement": "The named relation definitions are never carried onto the inner query, so "
                   "it keeps the fresh empty set — exactly the pre-gold behavior. Its faithful "
                   "real patch is the unpatched code: a filter clause that references one of "
                   "those named relations cannot be resolved inside the inner query, the "
                   "rewrite raises instead of returning rows, and the F2P FAILS. It would NOT "
                   "resolve, so a verifying rival here would be a true "
                   "verify-does-not-imply-resolve break.",
     "rationale": "THE discriminating weakness on `correct_buildInnerQuery`. Rejection source: "
                  "the equality clause and its spelled-out consequences "
                  "`result.filteredRelations = selfFilteredRelations` and "
                  "`result.appliedFilters = [(filterExpr, selfFilteredRelations)]` — both fail "
                  "at once, since the rival leaves the set empty AND therefore snapshots an "
                  "empty context. Witness at model M1 with one named relation ('author','c1') "
                  "and clause ('f','v'). Seen to elaborate against the rival (exit 0) and fail "
                  "against gold (exit 1)."},
    {"id": "filter-before-carry", "kind": "uniqueness", "expect": "reject",
     "module": _R_FILTER_FIRST,
     "witness": _W_FILTER_FIRST,
     "refinement": "The relations ARE installed, but only after the filter has been applied. "
                   "Its faithful real patch adds the carry-over one statement too late: at the "
                   "moment the clause is resolved the named relations are still absent, so the "
                   "reference is unresolvable and the F2P FAILS exactly as in the unpatched "
                   "case. The end state of the inner query looks right, which is precisely why "
                   "it would NOT resolve while appearing to contain the fix.",
     "rationale": "A NEAR-MISS that agrees with gold on every output component EXCEPT the "
                  "snapshot, so it gets its own witness point rather than sharing "
                  "omit-relation-carry's. Rejection source: the ordering-bearing consequence "
                  "`result.appliedFilters = [(filterExpr, selfFilteredRelations)]` (the rival "
                  "records the empty context) and, through it, the whole-construction "
                  "equality. This attacks a clause nagini's value-equality carrier could not "
                  "express at all. Witness at model M2, relation ('book','c2'), clause ('g','w'). "
                  "Seen to elaborate against the rival (exit 0) and fail against gold (exit 1)."},
    {"id": "drop-first-relation", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROP_FIRST,
     "witness": _W_DROP_FIRST,
     "refinement": "Installs the named relations minus the first. Its faithful real patch "
                   "carries over a truncated set; a clause referencing the omitted relation is "
                   "unresolvable, so the F2P FAILS. Partial propagation is not the whole-set "
                   "propagation gold performs.",
     "rationale": "Attacks the `selfFilteredRelations` binder on a partial sub-domain: correct "
                  "ONLY when that set is empty, wrong at every non-empty set. (An earlier "
                  "revision of this note claimed it was correct at any set of at most one entry "
                  "and that two elements were the smallest observable head-drop; both are false "
                  "and were measured false — a witness at a ONE-element set elaborates against "
                  "this rival, exit 0, since `drop 1` of a singleton is the empty list. The "
                  "empty set is the only agreeing point, confirmed by a witness there failing "
                  "against the rival, exit 1.) Rejection source: "
                  "`result.filteredRelations = selfFilteredRelations` plus the snapshot "
                  "consequence. The witness sits at model M3 with a TWO-element set not because "
                  "a shorter one would fail to discriminate, but because two elements are the "
                  "shortest length at which a head-drop is distinguishable from the TAIL-drop of "
                  "drop-last-relation — so the two mirror rivals are refuted at genuinely "
                  "different points. Seen to elaborate against the rival (exit 0) and fail "
                  "against gold (exit 1)."},
    {"id": "drop-last-relation", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROP_LAST,
     "witness": _W_DROP_LAST,
     "refinement": "Installs the named relations minus the last. Faithful real patch: the same "
                   "truncated carry-over from the other end — a clause referencing the final "
                   "definition is unresolvable and the F2P FAILS.",
     "rationale": "The mirror of drop-first-relation, and given its own witness point (model M4, "
                  "a DIFFERENT two-element set) because the two rivals are wrong at different "
                  "positions of the set: a shared point would let the manifest claim a "
                  "sub-domain it never demonstrated for one of them. Rejection source: "
                  "`result.filteredRelations = selfFilteredRelations` plus the snapshot "
                  "consequence. Seen to elaborate against the rival (exit 0) and fail against "
                  "gold (exit 1)."},
    {"id": "omit-ordering-clear", "kind": "uniqueness", "expect": "reject",
     "module": _R_OMIT_CLEAR,
     "witness": _W_OMIT_CLEAR,
     "refinement": "Correct on the relation and filter components; the ordering is never "
                   "dropped. Its faithful real patch omits the ordering-clearing call, leaving "
                   "the inner query ordered. An ordered subquery in this membership position is "
                   "not what the surrounding rewrite emits, so the behavior diverges from gold "
                   "and the pre-existing P2P coverage of this construction; it would not be a "
                   "resolving patch.",
     "rationale": "Attacks the `result.orderingCleared = true` component — an independent "
                  "conjunct of the postcondition that every relation-set and decision rival "
                  "leaves satisfied, so without this case that clause would go unattacked. "
                  "Wrong regardless of the relation set, so its witness probes the EMPTY set "
                  "(model M5, clause ('j','z')) — the degenerate value no other witness reaches, "
                  "which also confirms the clause does not secretly depend on that binder. Seen "
                  "to elaborate against the rival (exit 0) and fail against gold (exit 1)."},
    {"id": "wrong-model", "kind": "uniqueness", "expect": "reject",
     "module": _R_WRONG_MODEL,
     "witness": _W_WRONG_MODEL,
     "refinement": "Binds the inner query to a constant rather than the supplied model. Its "
                   "faithful real patch builds the nested query against the wrong entity "
                   "entirely, so the membership test compares unrelated rows — every test over "
                   "this rewrite fails, F2P and P2P alike. Plainly not a resolving patch.",
     "rationale": "Attacks the `selfModel` binder via `result.model = selfModel`. This is the "
                  "lean carrier's counterpart of nagini's frame attack: the spec pins the "
                  "unchanged component explicitly, so an impl that fails to reproduce it is "
                  "refuted structurally rather than by a permission rule. Without this case "
                  "`selfModel` would be a binder no rival abuses. Witness at model M6 (a "
                  "non-empty string, so the constant substitution is observable). Seen to "
                  "elaborate against the rival (exit 0) and fail against gold (exit 1)."},
    {"id": "swap-filter-components", "kind": "uniqueness", "expect": "reject",
     "module": _R_SWAP_FILTER,
     "witness": _W_SWAP_FILTER,
     "refinement": "Applies the two components of the filter clause transposed. Its faithful "
                   "real patch applies the clause with its sides exchanged, restricting the "
                   "inner query on the wrong term; the subquery selects the wrong rows and the "
                   "F2P FAILS. Not a resolving patch.",
     "rationale": "Attacks the `filterExpr` binder — the third input of this obligation, and "
                  "one the relation-set and ordering rivals all reproduce faithfully. Rejection "
                  "source: `result.appliedFilters = [(filterExpr, selfFilteredRelations)]`, "
                  "which pins the clause itself and not merely the context it resolved against. "
                  "Witness at model M7 with the ASYMMETRIC clause ('lhs','rhs') — a symmetric "
                  "clause would make the transposition invisible and the witness would not "
                  "discriminate. Seen to elaborate against the rival (exit 0) and fail against "
                  "gold (exit 1)."},

    # ========= UNIQUENESS: the collapse decision (must be REJECTED) =========
    {"id": "ignore-relation-condition", "kind": "uniqueness", "expect": "reject",
     "module": _R_IGNORE_RELCOND,
     "witness": _W_IGNORE_RELCOND,
     "refinement": "The collapse condition consults only whether the leading join keeps outer "
                   "rows; whether it carries a relation-level condition is never read. Its "
                   "faithful real patch is the unpatched guard: a join that exists only to "
                   "apply a named relation's condition gets collapsed into a plain column "
                   "selection, silently discarding that restriction, so the query returns the "
                   "wrong rows and the F2P FAILS. This is the headline weakness on "
                   "`correct_selectInnerJoin` and its faithful patch is exactly the code gold "
                   "replaces.",
     "rationale": "Rejection source: the FIRST arm of the two-armed implication. At "
                  "keepsOuterRows=false, carriesRelationCondition=true the spec's derived "
                  "condition is false, so the second arm demands the far-side names against the "
                  "original alias; the rival's condition is true and it returns the near-side "
                  "names against the collapsed alias, contradicting both components. Correct on "
                  "the whole carriesRelationCondition=false sub-domain, which is why the "
                  "witness must sit at true. Seen to elaborate against the rival (exit 0) and "
                  "fail against gold (exit 1)."},
    {"id": "inverted-relation-condition", "kind": "uniqueness", "expect": "reject",
     "module": _R_INVERTED,
     "witness": _W_INVERTED,
     "refinement": "Uses the relation-condition conjunct with the WRONG polarity: collapse iff "
                   "the join keeps no outer rows AND carries a relation condition. Its faithful "
                   "real patch is the strengthened guard with the negation dropped, so it "
                   "collapses precisely the relation-carrying join that must be kept (F2P FAILS, "
                   "the restriction is lost) while refusing to collapse the plain join gold does "
                   "collapse (the pre-existing P2P coverage of the collapse path diverges). "
                   "Wrong on both halves of the split; not a resolving patch.",
     "rationale": "Rejection source: the same first/second-arm contradiction as "
                  "ignore-relation-condition, and the witness sits at the same condition point "
                  "(keepsOuterRows=false, carriesRelationCondition=true) because both rivals "
                  "really are wrong THERE for the same reason — collapsing a relation-carrying "
                  "join. It is given its own witness anyway, at a two-element field list and a "
                  "distinct alias pair, so the more-wrong rival is refuted at a distinct probed "
                  "point rather than borrowing the near-miss's. Seen to elaborate against the "
                  "rival (exit 0) and fail against gold (exit 1)."},
    {"id": "ignore-outer-rows", "kind": "uniqueness", "expect": "reject",
     "module": _R_IGNORE_OUTER,
     "witness": _W_IGNORE_OUTER,
     "refinement": "The mirror-image partial-domain rival: only the relation-condition half of "
                   "the guard is consulted, so an outer-keeping leading join is collapsed. Its "
                   "faithful real patch drops the outer-keeping half of the condition; "
                   "collapsing such a join discards the rows that have nothing on the inner "
                   "side, so the pre-existing P2P coverage of the collapse path fails. Not a "
                   "resolving patch.",
     "rationale": "Attacks the `keepsOuterRows` field of the `firstJoin` binder — held at false "
                  "by every other decision witness, so a rival mishandling only that observable "
                  "would otherwise verify unnoticed. This is the coverage gap the port would "
                  "have had if it ported nagini's decision rivals alone. Rejection source: the "
                  "second arm, at keepsOuterRows=true, carriesRelationCondition=false — the "
                  "ONLY point in the condition's domain that separates this rival from gold, and "
                  "one no other witness probes. Seen to elaborate against the rival (exit 0) and "
                  "fail against gold (exit 1)."},
    {"id": "never-collapse", "kind": "uniqueness", "expect": "reject",
     "module": _R_NEVER_COLLAPSE,
     "witness": _W_NEVER_COLLAPSE,
     "refinement": "Over-retention: the collapse is never taken. Its faithful real patch "
                   "hard-disables the collapse, so a leading join that gold does collapse "
                   "survives; the emitted nested query keeps a join the pre-existing P2P "
                   "coverage of this path expects collapsed, and that behavior diverges from "
                   "gold. Over-retention is still wrong, so it would not resolve.",
     "rationale": "Rejection source: the FIRST arm of the implication, at keepsOuterRows=false, "
                  "carriesRelationCondition=false — the one condition point where the spec "
                  "demands the collapse, and the sub-domain on which this rival alone is wrong "
                  "(it agrees with gold everywhere else). Seen to elaborate against the rival "
                  "(exit 0) and fail against gold (exit 1)."},
    {"id": "swap-field-side", "kind": "uniqueness", "expect": "reject",
     "module": _R_SWAP_SIDE,
     "witness": _W_SWAP_SIDE,
     "refinement": "The decision is correct; the collapse arm selects the FAR-side names where "
                   "the near side is required. Its faithful real patch selects the wrong side "
                   "of each related-field pair when collapsing, so the collapsed selection "
                   "names columns from the wrong end of the relation and the emitted query is "
                   "wrong on every collapse case. Not a resolving patch.",
     "rationale": "Attacks the `relatedFields` binder and the `selectFields` component of the "
                  "first arm — a component every decision rival reproduces correctly, since "
                  "they err only in WHICH arm fires. Rejection source: the first arm's "
                  "`result.selectFields = relatedFields.map (·.1)`. Witness at the collapse "
                  "point with an asymmetric pair ('n6','f6'), so the near/far distinction is "
                  "observable; a pair with equal components would not discriminate. Seen to "
                  "elaborate against the rival (exit 0) and fail against gold (exit 1)."},
    {"id": "swap-alias", "kind": "uniqueness", "expect": "reject",
     "module": _R_SWAP_ALIAS,
     "witness": _W_SWAP_ALIAS,
     "refinement": "Decision and projection correct; the collapse arm selects against the "
                   "ORIGINAL alias rather than the collapsed one. Its faithful real patch "
                   "resolves the collapsed selection against the alias being collapsed away, "
                   "which no longer carries those columns — the emitted query is wrong on every "
                   "collapse case. Not a resolving patch.",
     "rationale": "Attacks the `aliasOriginal` / `aliasCollapsed` binders via the first arm's "
                  "`result.selectAlias = aliasCollapsed` — the output component that the "
                  "decision and projection rivals all leave satisfied, so without this case the "
                  "two alias binders would be untouched by any rival. Witness at the collapse "
                  "point with a distinct alias pair ('Y1','Y2'); equal aliases would make the "
                  "swap invisible. Seen to elaborate against the rival (exit 0) and fail "
                  "against gold (exit 1)."},
    {"id": "drop-last-field", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROP_FIELD,
     "witness": _W_DROP_FIELD,
     "refinement": "Decision and projection correct, but the final selected name is lost. Its "
                   "faithful real patch builds the collapsed selection one name short, so a "
                   "multi-column relation is matched on a proper subset of its columns — the "
                   "membership test admits rows it must exclude. Wrong on every collapse case "
                   "over a multi-column relation; not a resolving patch.",
     "rationale": "The lean analogue of nagini's dropped trailing downstream condition: a "
                  "correct decision with a mangled payload. Rejection source: the first arm's "
                  "`result.selectFields = relatedFields.map (·.1)`, which pins the list "
                  "EXACTLY, length included. Witness at the collapse point with a TWO-element "
                  "field list. (An earlier revision called two elements 'the shortest length at "
                  "which a trailing drop is observable'; that is false and was measured false — "
                  "a witness at a ONE-element list elaborates against this rival, exit 0, since "
                  "`dropLast` of a singleton is the empty list. The EMPTY field list is the only "
                  "agreeing point: a witness there fails against the rival, exit 1.) Two "
                  "elements are used because they are the shortest length at which the drop "
                  "leaves a non-empty remainder — a truncation rather than a wipe — and because "
                  "no other join witness uses that length, so this case also varies the "
                  "`relatedFields` binder's size rather than only its contents. Seen to "
                  "elaborate against the rival (exit 0) and fail against gold (exit 1)."},
    {"id": "else-arm-alias", "kind": "uniqueness", "expect": "reject",
     "module": _R_ELSE_ALIAS,
     "witness": _W_ELSE_ALIAS,
     "refinement": "Correct on the decision and on the collapse arm; when the collapse is "
                   "REFUSED it selects the far-side names against the collapsed alias instead of "
                   "the original one. Its faithful real patch resolves the retained selection "
                   "against the alias the leading join was not collapsed onto, so the emitted "
                   "nested query names columns against a table the kept join does not select "
                   "from — the membership test is built over the wrong alias on every "
                   "no-collapse case, including the relation-carrying join this bundle's fix "
                   "exists to keep. Not a resolving patch.",
     "rationale": "Added by the audit to close a real gap: every other payload rival mangles the "
                  "COLLAPSE arm, so the second arm's `result.selectAlias = aliasOriginal` was a "
                  "component no rival abused — an impl wrong only there would have verified "
                  "unnoticed. Rejection source: the SECOND arm, at keepsOuterRows=true, "
                  "carriesRelationCondition=false. Witness with a distinct alias pair "
                  "('P1','P2'); equal aliases would make the substitution invisible. Built both "
                  "ways: elaborates against the rival (exit 0), fails against gold (exit 1) with "
                  "`decide` reporting the proposition false."},
    {"id": "else-arm-field-side", "kind": "uniqueness", "expect": "reject",
     "module": _R_ELSE_SIDE,
     "witness": _W_ELSE_SIDE,
     "refinement": "Correct on the decision and on the collapse arm; when the collapse is "
                   "REFUSED it selects the NEAR-side names where the far side is required. Its "
                   "faithful real patch selects the wrong end of each related-field pair on the "
                   "retained-join path, so the nested query matches on columns that do not exist "
                   "on the selected alias — wrong on every no-collapse case. Not a resolving "
                   "patch.",
     "rationale": "The projection half of the same gap: the second arm's "
                  "`result.selectFields = relatedFields.map (·.2)` was likewise unattacked. "
                  "Rejection source: the second arm, at keepsOuterRows=true, "
                  "carriesRelationCondition=true — the FOURTH point of the guard's domain, which "
                  "no other witness in this battery probes, so this case is also what makes the "
                  "condition's coverage exhaustive rather than three-quarters. Witness uses an "
                  "asymmetric pair ('nb','fb') so the near/far distinction is observable. Built "
                  "both ways: elaborates against the rival (exit 0), fails against gold (exit 1) "
                  "with `decide` reporting the proposition false."},
]
