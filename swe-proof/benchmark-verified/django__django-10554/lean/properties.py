"""properties.py — PBT falsification manifest for django__django-10554 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function resolves ONE ORDER BY term against a combined query's
column state:

    implementation_resolveOrderColumn
        (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome

pinned by the two load-bearing conjuncts

    result = resolveOutcome q isRef src
    ∧ (inCorrespondence q = true → outcomeUsable q result = true)

`QueryCols` carries the THREE lists that take part, and the point is that the
matched-against list and the mutated list are DIFFERENT lists. `resultCols` are
the columns the term is matched against; a match reports an ordinal in this list
and resolving a term never grows it. `querySelect` and `valuesSelect` are the
query's own selected columns and the value labels naming them — the state a new
order column joins, and the pair the combination hands down to its sub-queries.
`inCorrespondence` says that pair has equal length. `outcomeUsable q` says a
reported position is a genuine 1-based ordinal OF THE RIGHT LIST: of `resultCols`
when the query column state came back untouched, and of `querySelect` (its new
trailing one, the state having grown by exactly one column) when it was extended;
and that where NO position is reported the labels are untouched and at most one
column was added.

`resolveOutcome` is a FULLY TRANSPARENT deep model: it scans `q.resultCols` left
to right carrying the ORDER BY term (realiasing it — dropping the outermost of
the names it stands under — at each column carrying the name it then stands
under, so a term under several names is realiased several times), returns `resolved pos q` at the first matching column,
and on no match either fails (`noMatch`) when the last column it visited carries
an alias, adds the carried expression to the query's column state — appended to
`querySelect` AND named in `valuesSelect` — and resolves to its new trailing
ordinal THERE, or stops with the state untouched where it visited no column at
all and so holds no alias to consult. There is NO opaque callee, so every rival is refutable by `decide`
at a concrete input — no carrier conditioning is needed.

Five carrier facts, each measured against the real callee in the container and
each with its own rival lane below, make the model partial where a total one
would predict behaviour the callee does not have:

  * an optional alias counts as an alias only where it is TESTED FOR TRUTH, so a
    present-but-empty name is no alias (`hasAlias`, not `Option.isSome`);
  * the alias the no-match case consults belongs to the LAST COLUMN THE SCAN
    VISITED, so where there was no column to visit there is no such alias in hand
    and none can be obtained: a term over an empty result-column list neither
    fails nor is added, it STOPS with the state untouched (`aborted q`);
  * the value label an expression contributes is optional AND may not exist at
    all (`OutputLabel`), and the two appends that add a column happen in order,
    so an expression with no label to append leaves the column added and the
    label list behind (`aborted`, via `withPartialResultCol`);
  * the name a reference term is matched by is a property of the wrapper standing
    over it, so it is available exactly while some wrapper remains: realiasing
    reveals the next name if the term stood under more than one, and a reference
    scan can go no further once the term stands under none (`ScanResult.halted`);
  * two expressions are the SAME EXPRESSION exactly when their identities agree,
    and an identity does NOT settle the value label the expression contributes,
    so the scan's comparison reads the identity and nothing else (`QExpr.sameExpr`,
    not structural `==` on the pair). The label of a column the scan MET is never
    observed; the label that is appended on the add path is the label of the term
    in hand. Measured in the patched container: `Col("t", app_label) ==
    Col("t", username)` is TRUE while the two contribute `app_label` and
    `username`, because `BaseExpression.identity` maps a `fields.Field` argument
    to `type(value)` (django/db/models/expressions.py, at base commit
    14d026cccb144c6877294ba4cd4e03ebf0842498) and `__eq__` compares identities.
    See `label-in-match-test`.

The clause pins FIVE independent outcomes and their sub-structure against the
input binders `q` (all three parts), `isRef`, and the `OrderSrc` fields
(`expr`/`refs`/`source`):

  * MATCH — `resolved pos q`: the 1-based position of the first matching
    column, WITH the column state returned UNCHANGED. Two independent facts: the
    position value, and the identity of the returned column state.
  * NO-MATCH / ALIASED LAST-VISITED — `noMatch`: a term that matches nothing and
    whose last visited column is aliased genuinely resolves to no column.
  * NO-MATCH / UNALIASED LAST-VISITED — `addedOutcome q finalCur`: the
    carried comparison expression joins the query's column state in BOTH parts of
    it, `resultCols` is left alone, and the term resolves to the new trailing
    ordinal among the query's selected columns. Four independent facts: the
    appended column's identity, the label added for it, the returned position,
    and WHICH list that position counts.
  * NO-MATCH / NO LABEL TO APPEND — `aborted (withPartialResultCol q finalCur)`:
    the column has joined the selected columns, the label list is as it arrived,
    and no position is reported.
  * SCAN CANNOT CONTINUE, or NOTHING VISITED — `aborted q`: a reference term
    realiased down to a term standing under no name, reaching a further column,
    stops with the state untouched, and so does a term whose result-column list
    was empty, there being no last-visited alias for the no-match suite to
    consult.

Because the result carries the (possibly extended) column state, the frame
obligation (nagini held `cols` at full permission because the append path
mutates it) is discharged here STRUCTURALLY: the MATCH outcome pins the state
UNCHANGED as part of the returned payload, so a rival that mutates it on the
match path is refuted by the equality itself — the referential-transparency
collapse does NOT make this class vacuous, because the state is an OBSERVABLE
component of the result, not an aliased side effect. See `frame-match-extend`.

The second conjunct is not a restatement of the first. It is a behavioural
consequence that holds of the reference outcome for a REASON (proved as
`resolveOutcome_usable`, via `scanCols_bound`): a position is only ever emitted
for a column the scan actually visited, and a new result column enters both
parts of the state together. A rival that adds the column to the selected
columns while leaving the label list behind satisfies the first conjunct's shape
but breaks correspondence, so it emits a position that the arms of the
combination cannot read. See `partial-new-result-col`. It is also what pins the
position to the right list: a rival that counts the extend position off the
matched-against list instead of the query's own selected columns is refuted by
the extend leg of `outcomeUsable`, since the two lists have unrelated lengths.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
  * `pos-reorder` (nagini branch reorder) -> `pos-reorder` — a structurally
    different CORRECT impl (functional form, trailing no-match branches tested in
    the inverted order); proof re-closed. Verifies or the spec is over-fit to one
    branch order (SPEC-TOO-STRONG).
  * added `pos-functional-form` — a second correct impl in a different shape
    (pure functional, no imperative do-block) closing with `rfl`. The carrier is
    transparent so there is no oracle to echo; stands purely as a soundness
    positive of a different impl form.
  * `w5-aliased-append` -> `w5-aliased-append` — adds the unmatched ALIASED term
    instead of failing; attacks the NO-MATCH/ALIASED outcome.
  * `frame-match-write` -> `frame-match-extend` — NOT vacuous here (see above):
    the match path returns an EXTENDED column list where the spec pins it
    unchanged; refuted by the `resolved pos cols` payload.
  * `offby1-match` -> `offby1-match` — returns `pos+1` on the match path.
  * `append-wrong-pos` -> `append-wrong-pos` — adds the column correctly but
    resolves to the pre-append length.
  * `append-wrong-val` -> `append-wrong-val` — appends the wrong column identity.
  * `reject-all` -> `reject-all` — the pre-patch shape: `noMatch` on every
    no-match, even an unaliased last-visited column (the bug the patch fixes).
  * added `drop-alias-switch` — drops the realiasing step, so the scan never
    adopts what the term's name stands for; a rival that varies `isRef=true` and
    the term's wrapper stack, which most witnesses hold fixed. Without it a rival
    mishandling only the reference path would slip by.
  * added by audit `no-ref-compare` — keeps the alias switch but drops the
    `aliasMatch ||` COMPARE-PERMISSION from the scan guard, so the referenced
    column is switched-to and then skipped as merely-aliased. `drop-alias-switch`
    could not catch this: it attacks the switch, this attacks the permission to
    compare, and the two conjuncts of that guard are independent facts.
  * added by repair `partial-new-result-col` — adds the new result column to the
    selected columns ONLY, leaving the value-label list untouched, so the two
    parts of the column state fall out of correspondence and the emitted position
    names a column the arms of the combination never gain. Every other rival
    holds correspondence fixed; without this lane a rival that adds the column to
    just one part of the state satisfies the outcome shape and slips by.
  * added by audit `skip-no-advance` — an aliased column that is SKIPPED does not
    advance the 0-based index, so a later match resolves one position short. No
    shipped rival varied the index accounting across a skipped column; every other
    position rival perturbs the arithmetic uniformly, which a single-column witness
    cannot tell from this.
  * added by panel repair `empty-alias-skips-column` and
    `empty-alias-fails-trailing` — the two places the callee tests an alias FOR
    TRUTH rather than for presence. Both rivals read the alias with
    `Option.isSome`, which is the same function on every non-empty name and
    differs only on a present-but-empty one; the two lanes are independent
    because the scan guard and the trailing dispatch consult the alias for
    different decisions (compare-or-skip vs fail-or-add).
  * added by panel repair `no-columns-fails` and `no-columns-adds` — the alias
    the no-match case consults belongs to the last column the scan VISITED, so
    where there was no column to visit there is no such alias in hand and none can
    be obtained: resolution stops. The two rivals take the two other readings of
    that one-input sub-domain — fail as a genuine no-match, and add the column as
    though the alias were present and falsy. Every other witness has a non-empty
    result-column list, so nothing else pins the outcome there, and neither rival
    can see the other.
  * added by panel repair `scan-past-switch` — keeps scanning after the term has
    been realiased down to one standing under no name, which no other rival does:
    every other reference witness matches (or fails) at the realiased column
    itself, so nothing pinned what happens at the NEXT one.
  * added by the second panel repair `substitute-once` and `substitute-to-base` —
    HOW FAR realiasing goes. The first is the previous revision of the model
    exactly: one realiasing and then stop, which predicts a stop where the real
    scan reads the next name off the term it just substituted in and resolves.
    The second goes too far in one step, straight to the bottom of the chain, so
    it has no name left where the real scan still has one. Both are identical to
    gold on every term standing under at most one name — which every other
    reference witness is — and neither can see the other: on the shared witness
    they stop for different reasons.
  * added by panel repair `label-append-when-undetermined` and
    `anonymous-label-as-empty-name` — the label an added column contributes. The
    first invents a label where there is none to append and so reports a position
    for a state that is out of correspondence; the second appends an empty NAME
    where the label is absent, which is a different value in the list the arms of
    the combination read.
  * added by the third panel repair `label-in-match-test` — the scan's comparison
    reads the expression's IDENTITY and nothing else. The rival tests the whole
    modeled expression, label included, which is the reading the previous revision
    of this model had; it is identical to gold on every pair of expressions that
    either differ in identity or agree in label, which every other witness is, and
    diverges exactly on the pair the real `==` collapses — two expressions of one
    identity contributing different labels. G-CONF draws that pair 949 times in
    200000 cases and the real code matches there, with the label-comparing control
    disagreeing on all 949.
  * nagini `admiss-match` -> `admiss-append-shape` (LANDED BY AUDIT). The lean
    obligation is an unconditional `∀ cols isRef src, problem_spec …`, so there is
    no precondition HYPOTHESIS to be over-strong — but that is not the right test
    on a total carrier, and "no precondition" was the wrong reason to drop the
    lane. The analogue here is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, and that IS testable: discharge `problem_spec` at that
    concrete input by EVALUATION, as a `have`, before closing the frozen
    obligation verbatim. See the case note for the informativeness control.
  * nagini permission-mutation framing is subsumed by `frame-match-extend`
    above; there is no separate fractional-permission class to port.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.

WHERE A RIVAL PUTS ITS EDIT
---------------------------
The added-column outcome is a named spec-region function (`addedOutcome`), which
the frozen impl calls from both legs of its trailing dispatch. A rival that
attacks that outcome therefore declares its OWN impl-region stand-in and calls
that instead (`_rival_added`): `variant_scope` bans new `theorem`/`lemma`/`axiom`
declarations, not a `def` in the impl region, and `same_spec` elides the impl
region, so the spec view stays byte-identical. No witness below names such a
stand-in, so no rejection can rest on a name gold does not have (the rule
`pbt_witness.witness_scope_problems` enforces).

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligation
removed. Each must (1) ELABORATE against the rival and (2) FAIL against the
frozen solution (a real discriminator, not a tautology). All witnesses below
were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1).
The carrier is transparent, so no witness binds a hypothesis (nothing to be
inconsistent).

Every gold-side failure is a FULL KERNEL EVALUATION — `decide` reports the
witness's proposition `is false` — not a stuck reduction, a missing instance, or
a unification failure, so the exit code carries information about the claim. That
was confirmed by the forgery control (audit, re-run by the panel repair over
every lane): the same witness with its `¬` DROPPED, i.e. asserting the frozen
impl is CORRECT at that input, SUCCEEDS on the frozen solution (exit 0) and FAILS
on the rival (exit 1) — the exact inverse of the witness on both sides. So each
rejection is attributable to the spec.
"""
from pathlib import Path

INSTANCE = "django__django-10554"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region (and, for positives,
# the proof body) of Solution.lean.  Each is verified unique across the whole
# file (the proof region carries near-duplicate text for `loopBody` and inside
# the statement of `forIn_cons_unfold`, distinguished by its indentation and by
# whether its branches are written with `return`).
# ---------------------------------------------------------------------------

# The gold trailing dispatch: failure when the last column the scan visited
# carries an alias, the added-column outcome when it carries none, and a stop
# with the state untouched where the scan had no column to visit at all, so that
# there is no such alias in hand and none can be obtained.
_TRAILING = (
    "  match q.resultCols.getLast? with\n"
    "  | some lastCol =>\n"
    "      if hasAlias lastCol.colAlias then\n"
    "        return OrderByOutcome.noMatch\n"
    "      else\n"
    "        return addedOutcome q cur.compared\n"
    "  | none => return OrderByOutcome.aborted q"
)

# The full gold impl body (Id.run do block).
_GOLD_IMPL = (
    "def implementation_resolveOrderColumn\n"
    "    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome := Id.run do\n"
    "  let mut cur : OrderSrc := src\n"
    "  let mut idx : Nat := 0\n"
    "  for col in q.resultCols do\n"
    "    if isRef && cur.refs?.isNone then\n"
    "      return OrderByOutcome.aborted q\n"
    "    let aliasMatch := isRef && cur.refs? == some col.colAlias\n"
    "    if aliasMatch then\n"
    "      cur := cur.stripped\n"
    "    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1\n"
    + _TRAILING
)

# The impl-region reference-alias expression switch (unique: the proof-region
# copies are spelled `let cur' := if aliasMatch then …` or indented deeper).
_ALIAS_SWITCH = (
    "    if aliasMatch then\n"
    "      cur := cur.stripped\n"
)

# The impl-region check that the scan cannot continue once the comparison
# expression has switched away from the reference term.
_HALT_CHECK = (
    "    if isRef && cur.refs?.isNone then\n"
    "      return OrderByOutcome.aborted q\n"
)

# The MATCH return + index bump (unique: proof copies use `resolved (idx + 1) q`
# without the trailing `idx := idx + 1` mutation line).
_MATCH_RETURN = (
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1"
)

# The whole scan guard, with the index bump, for rivals that attack which
# columns may be compared or how the ordinal is counted.
_SCAN_GUARD = (
    "    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1"
)

# The gold proof body (between the markers), replaced wholesale by each positive.
_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers (exclusive of the
    marker lines) with `new_proof_body`. The `theorem correct_*` STATEMENT is
    re-emitted byte-identically inside `new_proof_body`; only the tactic body
    (and helper lemmas dropped) change, which variant_scope permits. The
    reference-side lemmas (`scanCols_bound`, `resolveOutcome_usable`) live in the
    proof region, so a positive that needs them re-emits them."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


def _rival_added(name: str, body: str) -> str:
    """A rival that attacks only the ADDED-COLUMN outcome.

    That outcome is the spec-region `addedOutcome`, which the frozen impl calls
    from the unaliased leg of its trailing dispatch, so the rival declares an
    impl-region stand-in and calls that instead. `body` is the stand-in's
    definition (2-space indented, as `addedOutcome`'s own is) and may use `q`,
    `cur` and `src`. Legal for a variant: `variant_scope` bans new
    theorem/lemma/axiom declarations, not a `def`, and `same_spec` elides the
    whole impl region."""
    if _GOLD_IMPL.count("addedOutcome q cur.compared") != 1:
        raise AssertionError("drift: the gold impl no longer calls addedOutcome once")
    helper = ("/-- Stands in for the added-column outcome. -/\n"
              "def " + name + " (q : QueryCols) (cur : QExpr) (src : OrderSrc)"
              " : OrderByOutcome :=\n" + body + "\n\n")
    return _swap(_BASE, _GOLD_IMPL,
                 helper + _GOLD_IMPL.replace("addedOutcome q cur.compared",
                                             name + " q cur.compared src"))


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# The reference-side lemmas about `resolveOutcome` itself (`scanCols_bound` and
# `resolveOutcome_usable`), sliced out of the frozen proof region. A positive
# control replaces the whole proof region, so it must re-emit them to keep the
# usability conjunct provable; they are NOT new declarations (they exist in the
# frozen file byte-identically), so the variant scope is unchanged. Sliced rather
# than duplicated so a Solution.lean edit cannot leave a stale copy here.
_LEMMA_HEAD = "/-- A matching column's reported position is a genuine 1-based ordinal of a"
_LEMMA_TAIL = "theorem correct_resolveOrderColumn :"
if _LEMMA_HEAD not in _BASE or _LEMMA_TAIL not in _BASE:
    raise AssertionError("drift: reference lemmas no longer locatable in the proof region")
_REF_LEMMAS = _BASE[_BASE.index(_LEMMA_HEAD):_BASE.index(_LEMMA_TAIL)]

# Common: the theorem statement, re-emitted verbatim so the obligation survives.
_THM_STMT = (
    "theorem correct_resolveOrderColumn :\n"
    "    ∀ (q : QueryCols) (isRef : Bool) (src : OrderSrc),\n"
    "      problem_spec_resolveOrderColumn q isRef src\n"
    "        (implementation_resolveOrderColumn q isRef src) := by"
)

# The usability conjunct is discharged the same way by every positive: rewrite
# the impl to the reference outcome, then invoke the reference-side lemma.
_USABLE_TAIL = (
    "  refine ⟨himpl, ?_⟩\n"
    "  intro hq\n"
    "  rw [himpl]\n"
    "  exact resolveOutcome_usable q isRef src hq\n"
)

# (pos-functional-form) A structurally different CORRECT impl: a pure functional
# expression (no `Id.run do`, no `for`/`mut`) whose body is exactly the reference
# outcome. The equality conjunct collapses to `rfl` because impl and spec are
# definitionally equal. If it fails to verify the spec is over-fit to the
# imperative shape => SPEC-TOO-STRONG.
_POS_FUNCTIONAL_IMPL = (
    "def implementation_resolveOrderColumn\n"
    "    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome :=\n"
    "  match scanCols isRef 0 src q.resultCols with\n"
    "  | ScanResult.atPos pos => OrderByOutcome.resolved pos q\n"
    "  | ScanResult.halted => OrderByOutcome.aborted q\n"
    "  | ScanResult.exhausted finalCur =>\n"
    "    match q.resultCols.getLast? with\n"
    "    | some lastCol =>\n"
    "        if hasAlias lastCol.colAlias then\n"
    "          OrderByOutcome.noMatch\n"
    "        else\n"
    "          addedOutcome q finalCur\n"
    "    | none => OrderByOutcome.aborted q"
)
_POS_FUNCTIONAL = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FUNCTIONAL_IMPL),
    _REF_LEMMAS + _THM_STMT + "\n"
    "  intro q isRef src\n"
    "  have himpl : implementation_resolveOrderColumn q isRef src\n"
    "      = resolveOutcome q isRef src := rfl\n"
    + _USABLE_TAIL,
)

# (pos-reorder) The same functional impl but with the trailing dispatch's branches
# tested in the INVERTED order: the nothing-visited case first, then the alias
# test taken negatively. Semantically identical, different source; the proof
# case-splits the trailing branch explicitly. If it fails to verify the spec is
# over-fit to one branch order => SPEC-TOO-STRONG.
_POS_REORDER_IMPL = (
    "def implementation_resolveOrderColumn\n"
    "    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome :=\n"
    "  match scanCols isRef 0 src q.resultCols with\n"
    "  | ScanResult.atPos pos => OrderByOutcome.resolved pos q\n"
    "  | ScanResult.halted => OrderByOutcome.aborted q\n"
    "  | ScanResult.exhausted finalCur =>\n"
    "    match q.resultCols.getLast? with\n"
    "    | none => OrderByOutcome.aborted q\n"
    "    | some lastCol =>\n"
    "        if !hasAlias lastCol.colAlias then\n"
    "          addedOutcome q finalCur\n"
    "        else\n"
    "          OrderByOutcome.noMatch"
)
_POS_REORDER_PROOF = (
    _REF_LEMMAS + _THM_STMT + "\n"
    "  intro q isRef src\n"
    "  have himpl : implementation_resolveOrderColumn q isRef src\n"
    "      = resolveOutcome q isRef src := by\n"
    "    unfold implementation_resolveOrderColumn resolveOutcome\n"
    "    cases scanCols isRef 0 src q.resultCols with\n"
    "    | atPos pos => rfl\n"
    "    | halted => rfl\n"
    "    | exhausted finalCur =>\n"
    "      cases q.resultCols.getLast? with\n"
    "      | none => rfl\n"
    "      | some lastCol => by_cases h : hasAlias lastCol.colAlias <;> simp [h]\n"
    + _USABLE_TAIL
)
_POS_REORDER = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_REORDER_IMPL),
    _POS_REORDER_PROOF,
)


# ===========================================================================
# ADMISSIBILITY — the obligation is SATISFIABLE at F2P-shaped inputs
# ===========================================================================
# Landed by audit. The frozen obligation is an unconditional universal, so there
# is no precondition HYPOTHESIS to be over-strong — but "no precondition" is the
# wrong test on a total carrier. The analogue is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input, which is directly testable:
# discharge `problem_spec` at that concrete input BY EVALUATION, as a `have`,
# before closing the frozen obligation verbatim.
#
# Four inputs, each the shape of a measured run of the real callee against a
# combined query (the values were read off the container, not off this model):
# a non-empty all-unaliased column state IN CORRESPONDENCE with (a) a plain
# order term matching NO column — the added-column outcome, where both parts of
# the state grow together; (b) a plain term matching the trailing column — the
# position outcome; (c) a plain term matching nothing whose expression has no
# label to append — the column added, the labels untouched, no position; and (d)
# a reference term that switches and then meets a further column — the scan
# stopping with the state untouched. The impl region is untouched; the gold
# tactic body follows the `have`s byte-for-byte, so the obligation is reproven,
# not weakened. The `have`s are then `clear`ed so they cannot participate.
#
# INFORMATIVENESS CONTROL (audit, machine-checked): the same `have` shape
# asserting the spec of a WRONG result at input (a) — `noMatch` in place of the
# resolved/extended outcome — does NOT close; `decide` reports the proposition
# `is false` (exit 1). So the step really evaluates the postcondition at these
# inputs rather than discharging anything put in front of it.
# The gold tactic body, re-emitted verbatim after the probes (drift-checked).
_GOLD_TAC = (
    "  intro q isRef src\n"
    "  have himpl : implementation_resolveOrderColumn q isRef src = resolveOutcome q isRef src := by\n"
    "    rw [implementation_resolveOrderColumn,\n"
    "        forIn_cons_unfold isRef q q.resultCols src 0,\n"
    "        loop_eq_scanCols isRef q q.resultCols src 0]\n"
    "    rfl\n"
    "  refine ⟨himpl, ?_⟩\n"
    "  intro hq\n"
    "  rw [himpl]\n"
    "  exact resolveOutcome_usable q isRef src hq\n"
)
# The closing half (everything after `intro`) must survive verbatim: the probes
# are inserted between `intro` and it, so the gold discharge is reproven, not
# replaced. Asserted so a Solution.lean edit fails loudly instead of silently
# shipping an admissibility case whose obligation is closed some other way.
_GOLD_TAC_CLOSE = _GOLD_TAC.split("  intro q isRef src\n", 1)[1]

_Q2 = ('({ resultCols := [{ expr := { id := 1, label := OutputLabel.name "a" }, colAlias := none },'
       ' { expr := { id := 2, label := OutputLabel.name "b" }, colAlias := none }],'
       ' querySelect := [{ id := 1, label := OutputLabel.name "a" },'
       ' { id := 2, label := OutputLabel.name "b" }],'
       ' valuesSelect := [some "a", some "b"] })')
# (d) a two-column state whose FIRST column carries the referenced alias and
# whose expression the term's source does not equal, so the scan switches, fails
# to match there, and cannot examine the second column.
_QREF = ('({ resultCols := [{ expr := { id := 9, label := OutputLabel.name "a" }, colAlias := some "a" },'
         ' { expr := { id := 7, label := OutputLabel.name "b" }, colAlias := none }],'
         ' querySelect := [{ id := 9, label := OutputLabel.name "a" },'
         ' { id := 7, label := OutputLabel.name "b" }],'
         ' valuesSelect := [some "a", some "b"] })')
_ADMISS_PROOF = (
    _THM_STMT + "\n"
    "  intro q isRef src\n"
    "  have admissible_append :\n"
    "      problem_spec_resolveOrderColumn\n"
    "    " + _Q2 + "\n"
    "    false\n"
    '    ({ links := [], base := { id := 5, label := OutputLabel.name "c" } })\n'
    "        (OrderByOutcome.resolved 3\n"
    '    ({ resultCols := [{ expr := { id := 1, label := OutputLabel.name "a" }, colAlias := none },'
    ' { expr := { id := 2, label := OutputLabel.name "b" }, colAlias := none }],'
    ' querySelect := [{ id := 1, label := OutputLabel.name "a" },'
    ' { id := 2, label := OutputLabel.name "b" },'
    ' { id := 5, label := OutputLabel.name "c" }],'
    ' valuesSelect := [some "a", some "b", some "c"] })) := by\n'
    "    unfold problem_spec_resolveOrderColumn\n"
    "    decide\n"
    "  have admissible_match :\n"
    "      problem_spec_resolveOrderColumn\n"
    "    " + _Q2 + "\n"
    "    false\n"
    '    ({ links := [], base := { id := 2, label := OutputLabel.name "b" } })\n'
    "        (OrderByOutcome.resolved 2\n"
    "    " + _Q2 + ") := by\n"
    "    unfold problem_spec_resolveOrderColumn\n"
    "    decide\n"
    "  have admissible_no_label :\n"
    "      problem_spec_resolveOrderColumn\n"
    "    " + _Q2 + "\n"
    "    false\n"
    "    ({ links := [], base := { id := 5, label := OutputLabel.undetermined } })\n"
    "        (OrderByOutcome.aborted\n"
    '    ({ resultCols := [{ expr := { id := 1, label := OutputLabel.name "a" }, colAlias := none },'
    ' { expr := { id := 2, label := OutputLabel.name "b" }, colAlias := none }],'
    ' querySelect := [{ id := 1, label := OutputLabel.name "a" },'
    ' { id := 2, label := OutputLabel.name "b" },'
    " { id := 5, label := OutputLabel.undetermined }],"
    ' valuesSelect := [some "a", some "b"] })) := by\n'
    "    unfold problem_spec_resolveOrderColumn\n"
    "    decide\n"
    "  have admissible_stopped :\n"
    "      problem_spec_resolveOrderColumn\n"
    "    " + _QREF + "\n"
    "    true\n"
    '    ({ links := [{ id := 3, refs := some "a" }],'
    ' base := { id := 4, label := OutputLabel.name "z" } })\n'
    "        (OrderByOutcome.aborted\n"
    "    " + _QREF + ") := by\n"
    "    unfold problem_spec_resolveOrderColumn\n"
    "    decide\n"
    "  have admissible_novisit :\n"
    "      problem_spec_resolveOrderColumn\n"
    '    ({ resultCols := [], querySelect := [{ id := 1, label := OutputLabel.name "a" }],'
    ' valuesSelect := [some "a"] })\n'
    "    false\n"
    '    ({ links := [], base := { id := 5, label := OutputLabel.name "c" } })\n'
    "        (OrderByOutcome.aborted\n"
    '    ({ resultCols := [], querySelect := [{ id := 1, label := OutputLabel.name "a" }],'
    ' valuesSelect := [some "a"] })) := by\n'
    "    unfold problem_spec_resolveOrderColumn\n"
    "    decide\n"
    "  clear admissible_append admissible_match admissible_no_label admissible_stopped admissible_novisit\n"
    + _GOLD_TAC_CLOSE
)
if _GOLD_TAC_CLOSE not in _ADMISS_PROOF:
    raise AssertionError("admissibility proof no longer closes with the gold body")
_ADMISS = _swap(_BASE, _THM_STMT + "\n" + _GOLD_TAC, _ADMISS_PROOF)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (w5-aliased-append) On no match, take the added-column outcome
# UNCONDITIONALLY — drop the alias test on the last visited column. Correct on
# MATCH and wherever that column is unaliased; wrong only on the unmatched
# ALIASED sub-domain, where it adds+resolves instead of signalling `noMatch`.
_RIVAL_W5 = _swap(_BASE, _TRAILING, "  return addedOutcome q cur.compared")

# (frame-match-extend) On the MATCH path, return an EXTENDED column state (add a
# spurious column) alongside the correct position. The spec pins the state
# UNCHANGED in the `resolved pos q` payload, so this is refuted by the frame
# component of the MATCH outcome, not by the position.
_RIVAL_FRAME = _swap(
    _BASE, _MATCH_RETURN,
    "      return OrderByOutcome.resolved (idx + 1) (withNewResultCol q src.compared none)\n"
    "    idx := idx + 1",
)

# (offby1-match) Return `idx + 2` (one past the first matching position) on the
# MATCH path. Correct on the add/no-match path; wrong on every matched term.
_RIVAL_OFFBY1 = _swap(
    _BASE, _MATCH_RETURN,
    "      return OrderByOutcome.resolved (idx + 2) q\n"
    "    idx := idx + 1",
)

# (append-wrong-pos) Add the column correctly but resolve to the PRE-append
# length (`q.querySelect.length`) instead of the new trailing position. Correct
# everywhere else, wrong only on the returned position.
_RIVAL_APPENDPOS = _rival_added(
    "addedOutcomePrePos",
    "  match cur.label with\n"
    "  | OutputLabel.name s =>\n"
    "      let newCols := withNewResultCol q cur (some s)\n"
    "      OrderByOutcome.resolved q.querySelect.length newCols\n"
    "  | OutputLabel.anonymous =>\n"
    "      let newCols := withNewResultCol q cur none\n"
    "      OrderByOutcome.resolved q.querySelect.length newCols\n"
    "  | OutputLabel.undetermined =>\n"
    "      OrderByOutcome.aborted (withPartialResultCol q cur)",
)

# (append-wrong-val) Reach the add path but append a DIFFERENT column identity
# (the term's underlying source expression instead of the carried one). Returns
# the right position and keeps the two parts in correspondence.
_RIVAL_APPENDVAL = _rival_added(
    "addedOutcomeWrongCol",
    "  match cur.label with\n"
    "  | OutputLabel.name s =>\n"
    "      let newCols := withNewResultCol q src.base (some s)\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.anonymous =>\n"
    "      let newCols := withNewResultCol q src.base none\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.undetermined =>\n"
    "      OrderByOutcome.aborted (withPartialResultCol q cur)",
)

# (partial-new-result-col) LANDED BY REPAIR. Add the new result column to the
# SELECTED COLUMNS ONLY, leaving the value-label list untouched, so the two parts
# of the column state fall out of correspondence: the outer query gains a result
# column that the arms of the combination never gain, and the position emitted for
# it therefore names a column those arms cannot read. Correct on MATCH and on the
# aliased failure, and it even reports the same POSITION as gold — it is wrong
# only in that one part of the state is left behind. Refuted by the usability
# conjunct, which no other rival exercises.
_RIVAL_PARTIALCOL = _rival_added(
    "addedOutcomeUnlabelled",
    "  match cur.label with\n"
    "  | OutputLabel.name _ =>\n"
    "      let newCols := withPartialResultCol q cur\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.anonymous =>\n"
    "      let newCols := withPartialResultCol q cur\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.undetermined =>\n"
    "      OrderByOutcome.aborted (withPartialResultCol q cur)",
)

# (reject-all) The PRE-PATCH shape: on any no-match, signal `noMatch` — even
# where the last visited column carries no alias. Diverges on the whole
# unmatched-UNALIASED sub-domain (the point of the change).
_RIVAL_REJECTALL = _swap(_BASE, _TRAILING, "  return OrderByOutcome.noMatch")

# (drop-alias-switch) Drop the reference-alias expression switch, so the scan
# never adopts `src.source` even when the referenced alias is met. Correct on
# every non-reference term; wrong when a reference term's underlying expression
# differs from its initial `src.expr`. The switch is still RECORDED, so the scan
# still stops at the following column: this rival attacks only the substitution.
_RIVAL_DROPSWITCH = _swap(_BASE, _ALIAS_SWITCH, "")

# (no-ref-compare) Added by audit. KEEP the alias switch but drop the
# `aliasMatch ||` COMPARE-PERMISSION from the scan guard, so the referenced
# column is switched-to and then skipped as merely-aliased. That guard is two
# independent facts — which expression is compared, and which columns may be
# compared at all — and `drop-alias-switch` only attacks the first.
_RIVAL_NOREFCOMPARE = _swap(
    _BASE, _SCAN_GUARD,
    "    if (!hasAlias col.colAlias) && cur.compared.sameExpr col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1",
)

# (skip-no-advance) Added by audit. An aliased column that is SKIPPED does not
# advance the 0-based index, so a later matching column resolves one position
# short of its true ordinal.
_RIVAL_SKIPNOADVANCE = _swap(
    _BASE, _SCAN_GUARD,
    "    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    if (aliasMatch || !hasAlias col.colAlias) then\n"
    "      idx := idx + 1",
)

# (empty-alias-skips-column) Added by the panel repair. Read the column's alias
# for PRESENCE instead of for truth in the SCAN GUARD, so a column carrying an
# empty name is skipped as aliased instead of being compared. Identical to gold
# on every absent and every non-empty alias.
_RIVAL_EMPTYSKIP = _swap(
    _BASE, _SCAN_GUARD,
    "    if (aliasMatch || !col.colAlias.isSome) && cur.compared.sameExpr col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1",
)

# (empty-alias-fails-trailing) Added by the panel repair. Read the LAST VISITED
# column's alias for presence instead of for truth, so an unmatched term whose
# last visited column carries an empty name fails instead of adding the column.
# Independent of the scan-guard lane: the two tests decide different things.
_RIVAL_EMPTYTRAILING = _swap(
    _BASE, _TRAILING,
    "  match q.resultCols.getLast? with\n"
    "  | some lastCol =>\n"
    "      if lastCol.colAlias.isSome then\n"
    "        return OrderByOutcome.noMatch\n"
    "      else\n"
    "        return addedOutcome q cur.compared\n"
    "  | none => return addedOutcome q cur.compared",
)

# (no-columns-fails) Added by the panel repair. Where the scan had NO column to
# visit, signal a genuine no-match instead of stopping — i.e. read the alias the
# no-match suite consults as an alias when there is no column to have got one
# from. Identical to gold on every non-empty result-column list, which is what
# every other witness holds fixed.
_RIVAL_NOCOLUMNS = _swap(
    _BASE, _TRAILING,
    "  match q.resultCols.getLast? with\n"
    "  | some lastCol =>\n"
    "      if hasAlias lastCol.colAlias then\n"
    "        return OrderByOutcome.noMatch\n"
    "      else\n"
    "        return addedOutcome q cur.compared\n"
    "  | none => return OrderByOutcome.noMatch",
)

# (no-columns-adds) Added by the panel repair. The other way to be wrong on that
# same one-input sub-domain, and the more tempting one: treat the missing alias
# as a present-and-empty one, so a term over an empty result-column list is ADDED
# to the query's column state and resolved, where the real no-match suite has no
# alias in hand to test at all and stops. Also identical to gold on every
# non-empty result-column list.
_RIVAL_NOCOLUMNSADD = _swap(
    _BASE, _TRAILING,
    "  match q.resultCols.getLast? with\n"
    "  | some lastCol =>\n"
    "      if hasAlias lastCol.colAlias then\n"
    "        return OrderByOutcome.noMatch\n"
    "      else\n"
    "        return addedOutcome q cur.compared\n"
    "  | none => return addedOutcome q cur.compared",
)

# (scan-past-switch) Added by the panel repair. Keep scanning after the
# comparison expression has switched to the reference's source, so a column
# BEYOND the referenced one can be matched (or the term can fall through to the
# trailing dispatch) where the real scan can go no further. Identical to gold
# whenever the referenced column is the last one, or matches, which is what every
# other reference witness holds fixed.
_RIVAL_PASTSWITCH = _swap(_BASE, _HALT_CHECK, "")

# (substitute-once) Added by the panel repair. Carry a one-shot flag instead of
# consulting whether the compared term still stands under a reference wrapper, so
# resolution stops at the FIRST column after any substitution rather than at the
# first column where the term names no alias at all. Identical to gold on every
# term wrapped at most once — which is what every other reference witness holds
# fixed — and wrong on every more deeply wrapped one, where the real scan reads
# the next alias off the term it just substituted in and substitutes again.
_RIVAL_SUBONCE = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_resolveOrderColumn\n"
    "    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome := Id.run do\n"
    "  let mut cur : OrderSrc := src\n"
    "  let mut idx : Nat := 0\n"
    "  let mut switched : Bool := false\n"
    "  for col in q.resultCols do\n"
    "    if isRef && (switched || cur.refs?.isNone) then\n"
    "      return OrderByOutcome.aborted q\n"
    "    let aliasMatch := isRef && cur.refs? == some col.colAlias\n"
    "    if aliasMatch then\n"
    "      cur := cur.stripped\n"
    "      switched := true\n"
    "    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1\n"
    + _TRAILING,
)

# (substitute-to-base) Added by the panel repair. The other way to be wrong about
# how far one substitution goes: on meeting the named alias, drop EVERY reference
# wrapper at once and compare the underlying expression, instead of dropping the
# one wrapper whose name was met. Also identical to gold on every term wrapped at
# most once, and it cannot see `substitute-once`: it substitutes too far in one
# step where that rival substitutes far enough but only once.
_RIVAL_SUBTOBASE = _swap(
    _BASE, _ALIAS_SWITCH,
    "    if aliasMatch then\n"
    "      cur := { links := [], base := cur.base }\n",
)

# (label-append-when-undetermined) Added by the panel repair. Invent a label for
# an expression that has none to append: the column joins the selected columns,
# an absent label is appended for it, and a position is reported. Identical to
# gold on every expression whose label exists.
_RIVAL_LABELINVENT = _rival_added(
    "addedOutcomeAlwaysLabels",
    "  match cur.label with\n"
    "  | OutputLabel.name s =>\n"
    "      let newCols := withNewResultCol q cur (some s)\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.anonymous =>\n"
    "      let newCols := withNewResultCol q cur none\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.undetermined =>\n"
    "      let newCols := withNewResultCol q cur none\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols",
)

# (label-in-match-test) Added by the third panel repair. Compare the WHOLE
# modeled expression in the scan guard — identity and value label together — where
# the callee's `==` compares identities only. This is the previous revision of
# this model exactly. Identical to gold on every pair that differs in identity or
# agrees in label, which is every other witness here; it diverges only where one
# identity carries two different labels, which is precisely what the real
# `identity` does when it collapses a `fields.Field` argument to its class. There
# it refuses a match the real scan makes and falls through to the add path.
_RIVAL_LABELMATCH = _swap(
    _BASE, _SCAN_GUARD,
    "    if (aliasMatch || !hasAlias col.colAlias) && cur.compared == col.expr then\n"
    "      return OrderByOutcome.resolved (idx + 1) q\n"
    "    idx := idx + 1",
)

# (anonymous-label-as-empty-name) Added by the panel repair. Append an empty NAME
# where the added column has no name at all. Same position, same appended column,
# same correspondence — only the label VALUE handed down to the arms differs.
_RIVAL_ANONEMPTY = _rival_added(
    "addedOutcomeEmptyName",
    "  match cur.label with\n"
    "  | OutputLabel.name s =>\n"
    "      let newCols := withNewResultCol q cur (some s)\n"
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.anonymous =>\n"
    '      let newCols := withNewResultCol q cur (some "")\n'
    "      OrderByOutcome.resolved newCols.querySelect.length newCols\n"
    "  | OutputLabel.undetermined =>\n"
    "      OrderByOutcome.aborted (withPartialResultCol q cur)",
)


# --- witnesses (checked with obligation removed) ---------------------------
# Each negates the spec predicate at one concrete input; the carrier is
# transparent, so `decide` closes and no witness binds a hypothesis. Structure
# instances are emitted on ONE line each: a multi-line `{ … }` literal in
# argument position is parsed against the enclosing indentation and does not
# elaborate. No witness names a rival's impl-region stand-in, so no rejection
# can rest on a name gold does not have.

def _wit(q: str, isRef: str, src: str) -> str:
    args = f"    {q}\n    {isRef}\n    {src}"
    return (
        "example : ¬ problem_spec_resolveOrderColumn\n"
        f"{args}\n"
        "    (implementation_resolveOrderColumn\n"
        f"{args}) := by\n"
        "  unfold problem_spec_resolveOrderColumn implementation_resolveOrderColumn\n"
        "  decide"
    )


def _q(cols: str, labels: str, exprs: str = "") -> str:
    """A one-line QueryCols literal, parenthesised for argument position.

    `cols` are the RESULT columns the term is matched against; `exprs`/`labels`
    are the query's own selected columns and their value labels, the state a
    new order column joins. They are independent lists, so a witness sets them
    separately; `exprs` defaults to empty (a query selecting no columns of its
    own, which is what `default_cols` ordering looks like)."""
    return ("({ resultCols := [" + cols + "], querySelect := [" + exprs
            + "], valuesSelect := [" + labels + "] })")


def _lab(name) -> str:
    """The value label an expression contributes: a name, no name at all
    (`None`), or none that can be produced (`"?"`)."""
    if name is None:
        return "OutputLabel.anonymous"
    if name == "?":
        return "OutputLabel.undetermined"
    return 'OutputLabel.name "%s"' % name


def _e(ident: int, field="a") -> str:
    """A one-line QExpr literal, for the query's own selected-column list."""
    return "{ id := %d, label := %s }" % (ident, _lab(field))


def _col(ident: int, field, alias: str) -> str:
    return ("{ expr := { id := %d, label := %s }, colAlias := %s }"
            % (ident, _lab(field), alias))


def _link(ident: int, refs: str) -> str:
    """One reference wrapper: its own identity and the alias name it names."""
    return "{ id := %d, refs := %s }" % (ident, refs)


def _chain(links, ident: int, field) -> str:
    """A one-line OrderSrc literal: a wrapper stack (outermost first) over the
    base expression no wrapper stands over."""
    return ("({ links := [" + ", ".join(links) + "], base := { id := %d,"
            " label := %s } })" % (ident, _lab(field)))


def _src(ident: int, field, refs: str, sid: int, sfield="z") -> str:
    """The two shapes most witnesses need.

    `refs == "none"` builds a term that is no reference at all: the wrapper stack
    is EMPTY and the term is its own base `(ident, field)`. Any other `refs`
    builds a term wrapped ONCE — a wrapper of identity `ident` naming that alias,
    over the base `(sid, sfield)` — so the compared term starts out as the
    wrapper and becomes the base when that alias is met. A wrapper contributes no
    label of its own, so `field` is unused in that shape: the compared wrapper
    reports the base's label, and a witness column it is matched against must
    carry that label too."""
    if refs == "none":
        return _chain([], ident, field)
    return _chain([_link(ident, refs)], sid, sfield)


_A = 'some "a"'
_AB = 'some "a", some "b"'
_ALIAS_A = 'some "a"'
_ALIAS_B = 'some "b"'
_ALIAS_EMPTY = 'some ""'

# Unmatched aliased last-visited column: gold => noMatch, w5 => resolved (adds).
_WIT_W5 = _wit(
    _q(_col(5, "a", _ALIAS_A), _A, _e(5, "a")), "false",
    _src(3, "c", "none", 0))
# A matched term over a 2-column state: gold keeps the state, frame extends it.
_WIT_FRAME = _wit(
    _q(_col(4, "a", "none") + ", " + _col(2, "b", "none"), _AB,
       _e(4, "a") + ", " + _e(2, "b")), "false",
    _src(2, "b", "none", 0))
# A matched term at position 1: gold => resolved 1, offby1 => resolved 2.
_WIT_OFFBY1 = _wit(
    _q(_col(2, "a", "none"), _A, _e(2, "a")), "false",
    _src(2, "a", "none", 0))
# Unmatched unaliased last column => add: gold => resolved 2, wrong-pos => 1.
_WIT_APPENDPOS = _wit(
    _q(_col(1, "a", "none"), _A, _e(1, "a")), "false",
    _src(9, "c", "none", 0))
# Unmatched unaliased last column => add. A REFERENCE term whose named alias no
# column carries, so it is still standing under its wrapper when the add path is
# reached: gold appends the term as it was compared (the wrapper, carrying the
# label the expression under it contributes), the rival appends that underlying
# expression instead. Same label and same position on both sides — only the
# appended column's identity differs.
_WIT_APPENDVAL = _wit(
    _q(_col(1, "a", "none"), _A, _e(1, "a")), "true",
    _chain([_link(8, _ALIAS_A)], 4, "c"))
# (partial-new-result-col) Unmatched unaliased last column => add. Gold names the
# new column in BOTH parts of the state (labels ["a", "c"]); the rival grows only
# the selected columns, so the state leaves out of correspondence and the emitted
# position points past what the arms of the combination select. Same position on
# both sides — only the correspondence differs, which is exactly the fact no other
# witness varies.
_WIT_PARTIALCOL = _wit(
    _q(_col(1, "a", "none"), _A, _e(1, "a")), "false",
    _src(5, "c", "none", 0))
# Unmatched unaliased last column => add: gold => resolved 2, reject-all => noMatch.
_WIT_REJECTALL = _wit(
    _q(_col(4, "a", "none"), _A, _e(4, "a")), "false",
    _src(6, "c", "none", 0))
# A REFERENCE term whose alias matches the column and whose underlying source
# expression equals the column expr but whose initial expr does not.
_WIT_DROPSWITCH = _wit(
    _q(_col(7, "a", _ALIAS_A), _A, _e(7, "a")), "true",
    _src(3, "c", _ALIAS_A, 7, "a"))
# (no-ref-compare) The same reference term: gold switches AND is permitted to
# compare the referenced aliased column, so it matches at position 1.
_WIT_NOREFCOMPARE = _wit(
    _q(_col(7, "a", _ALIAS_A), _A, _e(7, "a")), "true",
    _src(3, "c", _ALIAS_A, 7, "a"))
# (skip-no-advance) A two-column state whose FIRST column is aliased (and so
# skipped) and whose second matches: gold => resolved 2, the rival => resolved 1.
_WIT_SKIPNOADVANCE = _wit(
    _q(_col(5, "a", _ALIAS_A) + ", " + _col(3, "b", "none"), _AB,
       _e(5, "a") + ", " + _e(3, "b")),
    "false", _src(3, "b", "none", 0))
# (empty-alias-skips-column) A single result column carrying an EMPTY name whose
# expression the term equals: gold compares it and matches (resolved 1, state
# untouched); the rival skips it as aliased and, the name still being empty,
# adds instead (resolved 2 over a grown state).
_WIT_EMPTYSKIP = _wit(
    _q(_col(4, "a", _ALIAS_EMPTY), _A, _e(4, "a")), "false",
    _src(4, "a", "none", 0))
# (empty-alias-fails-trailing) A single result column carrying an EMPTY name that
# the term does NOT match: gold adds the column (resolved 2), the rival reads the
# name as an alias and fails (noMatch).
_WIT_EMPTYTRAILING = _wit(
    _q(_col(5, "a", _ALIAS_EMPTY), _A, _e(5, "a")), "false",
    _src(3, "c", "none", 0))
# (no-columns-fails / no-columns-adds) NO result column to visit at all, over a
# query that selects one column of its own: gold stops with the column state
# untouched, one rival fails instead and the other adds and resolves 2. One
# witness serves both lanes — it is the whole sub-domain on which they differ.
_WIT_NOCOLUMNS = _wit(
    _q("", _A, _e(1, "a")), "false", _src(5, "c", "none", 0))
# (scan-past-switch) A reference term that switches at the FIRST column, does not
# match there, and is followed by a column its source DOES equal: gold stops with
# the state untouched, the rival goes on and resolves 2.
_WIT_PASTSWITCH = _wit(
    _q(_col(9, "a", _ALIAS_A) + ", " + _col(7, "b", "none"), _AB,
       _e(9, "a") + ", " + _e(7, "b")),
    "true", _src(3, "c", _ALIAS_A, 7, "b"))
# (substitute-once / substitute-to-base) A term wrapped TWICE, whose outer name is
# carried by the first column and whose inner name is carried by the second, which
# the expression under both wrappers equals. Gold substitutes at the first column,
# reads the next name off what it substituted in, substitutes again at the second
# and matches there (resolved 2, state untouched). `substitute-once` stops at the
# second column instead; `substitute-to-base` goes straight to the underlying
# expression at the first, so nothing names an alias at the second and it stops
# there. One witness serves both lanes: it is the shallowest input on which either
# differs from gold, and every other reference witness is wrapped just once.
_WIT_SUBCHAIN = _wit(
    _q(_col(9, "a", _ALIAS_A) + ", " + _col(7, "b", _ALIAS_B), _AB,
       _e(9, "a") + ", " + _e(7, "b")),
    "true",
    _chain([_link(3, _ALIAS_A), _link(4, _ALIAS_B)], 7, "b"))
# (label-append-when-undetermined) An unmatched term whose expression has no
# label to append, over an unaliased last column: gold leaves the labels alone
# and reports no position, the rival appends an absent label and resolves.
_WIT_LABELINVENT = _wit(
    _q(_col(1, "a", "none"), _A, _e(1, "a")), "false",
    _src(5, "?", "none", 0))
# (anonymous-label-as-empty-name) An unmatched term whose expression has NO NAME:
# gold appends an absent label, the rival appends an empty name.
_WIT_ANONEMPTY = _wit(
    _q(_col(1, "a", "none"), _A, _e(1, "a")), "false",
    _src(5, None, "none", 0))
# (label-in-match-test) ONE result column, unaliased, whose expression has the
# SAME IDENTITY as the term's and contributes a DIFFERENT label ("a" against the
# term's "b"). Gold compares identities, meets the column and resolves 1 with the
# state untouched; the rival compares the label too, refuses the match, and — the
# last visited column carrying no alias — adds the term instead, resolving 2 over
# a grown state whose new label is the TERM's ("b"), not the met column's. This is
# the only witness in which one identity carries two labels.
_WIT_LABELMATCH = _wit(
    _q(_col(1, "a", "none"), _A, _e(1, "a")), "false",
    _src(1, "b", "none", 0))


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a structurally-different but correct impl: a pure functional "
                  "expression (no imperative do-block / for / mut) whose body is "
                  "definitionally the reference outcome, so `correct_` re-closes with "
                  "`rfl`. The carrier is transparent, so there is no oracle to echo; "
                  "this stands purely as a soundness positive of a different impl form. "
                  "If it fails to verify the spec is over-fit to the imperative shape "
                  "=> SPEC-TOO-STRONG."},
    {"id": "pos-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "a second correct impl with the trailing dispatch's branches tested in "
                  "the INVERTED order: the nothing-visited case first and the alias test "
                  "taken negatively. Semantically identical; the equality clause is "
                  "agnostic to branch order. Proof re-closed by case-splitting the scan "
                  "result and the trailing `getLast?`/alias dispatch (`cases …`, "
                  "`by_cases … <;> simp`). If it fails to verify the spec is over-fit to "
                  "one branch order => SPEC-TOO-STRONG."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-append-shape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "landed by audit; the lane was previously dropped for the wrong "
                  "reason (\"the frozen obligation has no precondition\"). The "
                  "obligation IS an unconditional universal, so no hypothesis can be "
                  "over-strong — but the analogue on a total carrier is the obligation "
                  "being UNSATISFIABLE at an F2P-shaped input, and this case tests that "
                  "directly: `problem_spec` is discharged BY EVALUATION (`decide`), as "
                  "four `have`s, at column states whose shape was read off runs of the "
                  "real callee — (a) a plain order term matching nothing (the "
                  "added-column outcome), (b) a plain term matching the trailing "
                  "column (the position outcome), (c) a term whose expression has no "
                  "label to append (the column added, the labels untouched, no position) "
                  "and (d) a reference term that switches and then meets a further "
                  "column (the scan stopping, state untouched); the `have`s are then "
                  "cleared and the frozen tactic body closes the obligation verbatim. "
                  "Informativeness control (audit, machine-checked): the same shape "
                  "asserting the spec of a WRONG result at (a) — `noMatch` — does NOT "
                  "close, `decide` reports the proposition `is false`. If this case "
                  "fails, the obligation is unsatisfiable at exactly the input the fix "
                  "is for => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "w5-aliased-append", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_W5, "witness": _WIT_W5,
     "refinement": "its faithful real patch drops the guard that fails an unmatched "
                   "aliased ORDER BY term and instead unconditionally adds a column and "
                   "renumbers, so a term naming no selected column is silently added and "
                   "resolved to a position. A P2P test asserts that exact path RAISES; "
                   "the patch would fail it and NOT resolve — so a verifying rival here "
                   "is a true verify-does-not-imply-resolve break.",
     "rationale": "attacks the NO-MATCH/ALIASED outcome (`noMatch`). Witness at "
                  "cols=[{5,some \"a\"}], isRef=false, src.expr=3: nothing matches "
                  "and the last visited column is aliased, so gold => noMatch while the "
                  "rival adds and => resolved. Built both ways (rival exit 0, gold "
                  "exit 1)."},
    {"id": "frame-match-extend", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME, "witness": _WIT_FRAME,
     "refinement": "its faithful real patch mutates the selected-column list on the "
                   "MATCH path (adding an already-selected column), shifting every later "
                   "column's ordinal; the position-reading P2P tests would read the "
                   "wrong rows — it would NOT resolve.",
     "rationale": "attacks the FRAME component of the MATCH outcome: the spec pins "
                  "`resolved pos q` with the column state UNCHANGED, so returning an "
                  "extended state violates the equality even though the position is "
                  "right. NOT vacuous under referential transparency because the state is "
                  "an observable component of the result. Witness at a 2-column state "
                  "with a matched term: gold keeps length 2, the rival returns length 3. "
                  "Varies the `q` binder (length 2). Built both ways (rival 0, gold 1)."},
    {"id": "offby1-match", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OFFBY1, "witness": _WIT_OFFBY1,
     "refinement": "its faithful real patch renders the ORDER BY position one past the "
                   "matching column for every matched term; the row-order-comparing P2P "
                   "tests would fail — it would NOT resolve.",
     "rationale": "attacks the POSITION component of the MATCH outcome (`resolved pos "
                  "cols`: pos must be the 1-based first-match index). Witness at a "
                  "matched term at position 1: gold => resolved 1, rival => resolved 2. "
                  "Built both ways (rival 0, gold 1)."},
    {"id": "append-wrong-pos", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_APPENDPOS, "witness": _WIT_APPENDPOS,
     "refinement": "its faithful real patch points the rewritten term at the column "
                   "BEFORE the freshly added one; the union F2P tests assert specific "
                   "ordered rows and would read the wrong column — it would NOT resolve.",
     "rationale": "attacks the POSITION component of the ADD outcome (`resolved "
                  "newCols.querySelect.length newCols`: the result must be the NEW "
                  "trailing position). Adds the column correctly but resolves to the "
                  "pre-append length. Witness at an unmatched unaliased last column: "
                  "gold => resolved 2, rival => resolved 1. Built both ways (rival 0, "
                  "gold 1)."},
    {"id": "append-wrong-val", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_APPENDVAL, "witness": _WIT_APPENDVAL,
     "refinement": "its faithful real patch adds the WRONG expression to the selected "
                   "columns; the values-list F2P tests read the added column back and "
                   "would return wrong values — it would NOT resolve.",
     "rationale": "attacks the added-COLUMN-IDENTITY component of the add outcome: "
                  "the new result column must carry the CARRIED comparison expression. "
                  "Returns the right position and keeps the two parts of the state in "
                  "correspondence, but appends the expression the term's name stands "
                  "for instead of the term as it was compared. Witness at a REFERENCE "
                  "term whose name no result column carries, over an unmatched unaliased "
                  "last column: gold appends the term as compared, the rival appends the "
                  "expression under it, so the returned states differ. "
                  "Built both ways (rival 0, gold 1)."},
    {"id": "partial-new-result-col", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIALCOL, "witness": _WIT_PARTIALCOL,
     "refinement": "its faithful real patch adds the ORDER BY column to the selected "
                   "columns but does not name it in the list of value labels that the "
                   "combination hands down to its sub-queries, so each arm keeps selecting "
                   "the original columns while the outer query selects one more. The "
                   "position the term is rewritten to then points past the end of every "
                   "arm's column list, and the database rejects the ordering term. The "
                   "union-with-values-list F2P tests exercise exactly that path and would "
                   "fail — it would NOT resolve.",
     "rationale": "landed by the repair; this is the rival the previous battery could not "
                  "express. It reports the SAME position as gold and extends the selected "
                  "columns identically, so the position and appended-identity lanes cannot "
                  "see it: it differs only in leaving the value-label list behind, which "
                  "breaks the correspondence between the two parts of the column state. "
                  "Refuted by the usability conjunct, which demands that a reported "
                  "position lie within a resulting state that still corresponds. Witness at "
                  "an unmatched unaliased last column: gold labels the new column (labels "
                  "a, c), the rival leaves the labels at (a) alone. Built both ways "
                  "(rival 0, gold 1)."},
    {"id": "reject-all", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REJECTALL, "witness": _WIT_REJECTALL,
     "refinement": "this IS the pre-patch behaviour (signal failure on every no-match); "
                   "the union-by-plain-column F2P tests raise instead of returning "
                   "ordered rows — it does NOT resolve (it is the bug the patch fixes).",
     "rationale": "attacks the whole NO-MATCH/UNALIASED ADD outcome: the spec demands "
                  "the column be added and resolved to a new position, the rival returns "
                  "`noMatch`. Witness at an unmatched unaliased last column: gold => "
                  "resolved 2, rival => noMatch. Built both ways (rival 0, gold 1)."},
    {"id": "drop-alias-switch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROPSWITCH, "witness": _WIT_DROPSWITCH,
     "refinement": "its faithful real patch omits the realiasing step that substitutes "
                   "a referenced column's underlying expression before comparison, so a "
                   "reference-ORDER-BY term whose name resolves to a differently-keyed "
                   "expression never matches its column; the F2P tests that order by a "
                   "referenced (aliased) column would resolve to the wrong outcome — it "
                   "would NOT resolve.",
     "rationale": "the ONLY rival that varies isRef=true and the term's wrapper stack "
                  "together with a MATCH — every other non-reference witness "
                  "holds isRef=false and an empty wrapper stack, so a rival mishandling "
                  "only the realiasing would otherwise go unnoticed. Witness: a reference "
                  "term standing under the name the column carries, whose underlying expr "
                  "(7) equals the column expr — gold realiases and matches (resolved 1), "
                  "the rival keeps the wrapper (3), never matches, and (aliased last "
                  "column) => noMatch. The rival differs from gold ONLY in whether the "
                  "name is discharged. "
                  "Built both ways (rival 0, gold 1)."},
    {"id": "no-ref-compare", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOREFCOMPARE, "witness": _WIT_NOREFCOMPARE,
     "refinement": "its faithful real patch keeps the realiasing substitution but then "
                   "treats the referenced column as just another named column and skips "
                   "it, so an ORDER BY term referencing a named result column never "
                   "resolves to that column and the term is reported as matching "
                   "nothing; the F2P tests that order by a referenced column would "
                   "raise instead of returning ordered rows — it would NOT resolve.",
     "rationale": "added by audit. The scan guard carries TWO independent facts — which "
                  "expression is compared (the alias switch) and which columns may be "
                  "compared at all (the `aliasMatch ||` permission). `drop-alias-switch` "
                  "attacks only the first, so nothing shipped pinned the second: a rival "
                  "that switched correctly and then refused to compare the referenced "
                  "column would have gone unnoticed. Witness at the reference term whose "
                  "source expr (7) equals the aliased column's expr: gold matches "
                  "(resolved 1), the rival skips it and (aliased last column) => "
                  "noMatch. Built both ways (rival 0, gold 1)."},
    {"id": "skip-no-advance", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SKIPNOADVANCE, "witness": _WIT_SKIPNOADVANCE,
     "refinement": "its faithful real patch advances the result-set ordinal only for "
                   "columns it actually compares, so any named column preceding the "
                   "matched one shifts the rendered position one low and the ORDER BY "
                   "reads the wrong column; the P2P tests that order a combined query "
                   "with a mix of named and plain columns compare ordered rows and would "
                   "fail — it would NOT resolve.",
     "rationale": "added by audit. Pins the index ACCOUNTING across a skipped column: "
                  "the position is the column's ordinal in the FULL column set, not its "
                  "rank among the compared ones. Every shipped position rival perturbs "
                  "the arithmetic uniformly at a single-column input, which cannot "
                  "distinguish this. Witness at a 2-column list whose first column is "
                  "aliased (skipped) and whose second matches: gold => resolved 2, the "
                  "rival => resolved 1. Also the only witness varying `cols` with a "
                  "skipped-then-matching shape. Built both ways (rival 0, gold 1)."},
    {"id": "empty-alias-skips-column", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTYSKIP, "witness": _WIT_EMPTYSKIP,
     "refinement": "its faithful real patch tests the result column's alias for "
                   "PRESENCE instead of for truth, so a column selected under an empty "
                   "name is skipped instead of compared; an ORDER BY term that names "
                   "exactly that column is then added to the selected columns a second "
                   "time and resolved to the wrong position, and the combined query "
                   "selects a column its arms do not — the F2P tests over a query with "
                   "an empty-named extra column read the wrong column and it would NOT "
                   "resolve.",
     "rationale": "added by the panel repair, which measured this against the real "
                  "callee: the scan tests the alias for TRUTH, so a present-but-empty "
                  "name is no alias. This rival differs from gold on exactly that "
                  "sub-domain and nowhere else, so no other witness can see it. Witness "
                  "at a single result column carrying an empty name whose expression the "
                  "term equals: gold compares it and matches (resolved 1, state "
                  "untouched), the rival skips it and adds instead (resolved 2 over a "
                  "grown state). Built both ways (rival 0, gold 1)."},
    {"id": "empty-alias-fails-trailing", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTYTRAILING, "witness": _WIT_EMPTYTRAILING,
     "refinement": "its faithful real patch tests the LAST VISITED column's alias for "
                   "presence instead of for truth, so an unmatched term over a query "
                   "whose last selected column carries an empty name raises instead of "
                   "adding the ORDER BY column; the F2P tests that order such a combined "
                   "query by an unselected column would raise — it would NOT resolve.",
     "rationale": "added by the panel repair. Independent of the scan-guard lane: the "
                  "trailing test decides fail-or-add while the scan test decides "
                  "compare-or-skip, and a rival can get either one wrong alone. Witness "
                  "at a single result column carrying an empty name that the term does "
                  "not match: gold adds the column (resolved 2), the rival reads the "
                  "empty name as an alias and fails (noMatch). Built both ways (rival 0, "
                  "gold 1)."},
    {"id": "no-columns-fails", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOCOLUMNS, "witness": _WIT_NOCOLUMNS,
     "refinement": "its faithful real patch reports a term that had no result column to "
                   "compare against as matching no column and raises the ordering error, "
                   "where the real no-match suite consults the alias of the last column "
                   "the scan VISITED and, no column having been visited, has no such "
                   "alias to consult and cannot obtain one: the query stops there of its "
                   "own accord, with nothing added and no position reported. The two are "
                   "different observable outcomes of the same call, and a P2P test "
                   "asserting the ordering error names the wrong one — it would NOT "
                   "resolve.",
     "rationale": "added by the panel repair. Pins the outcome where the scan visits "
                  "NOTHING, which is the one input class every other witness holds fixed "
                  "(all of them have a non-empty result-column list). Identical to gold "
                  "everywhere else, so no other lane can see it. Witness at an empty "
                  "result-column list over a query selecting one column of its own: gold "
                  "stops with the column state untouched, the rival => noMatch. Built "
                  "both ways (rival 0, gold 1)."},
    {"id": "no-columns-adds", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOCOLUMNSADD, "witness": _WIT_NOCOLUMNS,
     "refinement": "its faithful real patch adds the ORDER BY column to a combined "
                   "query that had no result column to compare against, and resolves the "
                   "term to a position, where the real no-match suite consults the alias "
                   "of the last column the scan VISITED and, no column having been "
                   "visited, has no such alias to consult and cannot obtain one, so the "
                   "query stops with nothing added. A combined query with no result "
                   "columns to scan would be ordered by a column the arms never gained "
                   "instead of stopping — it would NOT resolve.",
     "rationale": "added by the panel repair, as the second of two rivals on the "
                  "one-input sub-domain where the scan visits NOTHING. It is the tempting "
                  "over-total reading: treat the missing alias as a falsy one and take "
                  "the add path. `no-columns-fails` cannot see it (that rival fails on "
                  "the same input, this one adds) and every other witness holds a "
                  "non-empty result-column list, so without this lane the add reading of "
                  "that sub-domain is unpinned. Same witness as `no-columns-fails`: gold "
                  "stops with the state untouched, the rival adds the term's expression "
                  "and resolves 2. Built both ways (rival 0, gold 1)."},
    {"id": "scan-past-switch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PASTSWITCH, "witness": _WIT_PASTSWITCH,
     "refinement": "its faithful real patch keeps comparing result columns after the "
                   "term's referenced alias has been substituted away, which the real "
                   "scan cannot do — the referenced alias is a property of the reference "
                   "term and is gone once it has been replaced by its source. A rival "
                   "that carries on can match a column beyond the referenced one, or add "
                   "the term to the selected columns, where the real query stops; a "
                   "combined query with the same name in two column sources takes that "
                   "path and it would NOT resolve.",
     "rationale": "added by the panel repair, which measured the real callee stopping at "
                  "exactly the column after the switch. Every other reference witness "
                  "either matches at the referenced column or ends the scan there, so "
                  "nothing pinned the NEXT iteration. Witness: a reference term that "
                  "switches at the first of two columns, does not match there, and is "
                  "followed by a column its source DOES equal — gold stops with the "
                  "state untouched, the rival goes on and resolves 2. Built both ways "
                  "(rival 0, gold 1)."},
    {"id": "substitute-once", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SUBONCE, "witness": _WIT_SUBCHAIN,
     "refinement": "its faithful real patch remembers THAT the ORDER BY term was "
                   "realiased once and refuses to look at any further result column, "
                   "instead of asking the term it is now carrying which alias that term "
                   "names. A term naming a column whose own source is itself a named "
                   "reference is realiased again by the real scan and can match a later "
                   "column; this rival stops instead, so a combined query ordered by such "
                   "a term raises where the real one returns ordered rows — it would NOT "
                   "resolve.",
     "rationale": "added by the panel repair, which measured the real callee resolving "
                   "such a term. Pins HOW FAR resolution may continue: not \"one "
                   "realiasing and stop\" but \"as long as the carried term still names "
                   "an alias\". Identical to gold on every term realiased at most once — "
                   "which every other reference witness is — so no other lane can see it. "
                   "Witness: a doubly-named term whose outer name is carried by the first "
                   "column and whose inner name by the second, which the underlying "
                   "expression equals — gold => resolved 2 with the state untouched, the "
                   "rival stops at the second column. Built both ways (rival 0, gold 1)."},
    {"id": "substitute-to-base", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SUBTOBASE, "witness": _WIT_SUBCHAIN,
     "refinement": "its faithful real patch realiases an ORDER BY term straight to the "
                   "expression at the bottom of its chain of names, where the real scan "
                   "replaces the term by what its OWN name stands for — one step. On a "
                   "term naming a column that is itself a named reference the two differ: "
                   "the real scan then still has a name to match against a later column, "
                   "and this rival has none, so it stops where the real query resolves and "
                   "it would NOT resolve.",
     "rationale": "added by the panel repair, as the second of two readings of how far "
                   "one realiasing step goes. It cannot see `substitute-once` and that "
                   "lane cannot see it: this one substitutes too far in a single step, "
                   "that one substitutes far enough but only once, and on the shared "
                   "witness they stop for different reasons (no name left here, the "
                   "one-shot flag there). Also identical to gold on every term realiased "
                   "at most once. Same witness: gold => resolved 2, the rival stops at "
                   "the second column. Built both ways (rival 0, gold 1)."},
    {"id": "label-append-when-undetermined", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LABELINVENT, "witness": _WIT_LABELINVENT,
     "refinement": "its faithful real patch invents a value label for an ORDER BY "
                   "expression that has none to give, so the column and a label for it "
                   "both land and the term resolves to a position; the real code asks "
                   "the expression for its label AFTER the column has landed and cannot "
                   "produce one, so the query stops with the column added and the labels "
                   "as they were. A combined query ordered by an expression of "
                   "undetermined output takes that path and it would NOT resolve.",
     "rationale": "added by the panel repair. Pins the second of the two appends that "
                  "add a column: the label must be the one the expression contributes, "
                  "and an expression with no label to contribute yields no position at "
                  "all. Identical to gold wherever a label exists, so every other "
                  "witness is blind to it. Witness at an unmatched term whose expression "
                  "has no label, over an unaliased last column: gold leaves the labels "
                  "alone and reports no position, the rival appends an absent label and "
                  "resolves 2. Built both ways (rival 0, gold 1)."},
    {"id": "label-in-match-test", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LABELMATCH, "witness": _WIT_LABELMATCH,
     "refinement": "its faithful real patch compares an ORDER BY term against a result "
                   "column with something STRONGER than the expression equality the "
                   "compiler uses — it additionally requires the two to carry the same "
                   "output field name. Django's `BaseExpression.__eq__` compares "
                   "`identity`, and `identity` replaces a field argument by its CLASS, so "
                   "two columns over same-typed fields of the same alias ARE equal while "
                   "naming different fields. A term that the real scan resolves to such a "
                   "column would instead be appended to the selected columns a second "
                   "time and resolved to a position past the arms of the combination, and "
                   "`values_select` would gain a name for a column the arms never gained: "
                   "the union F2P tests that order by an already-selected column take "
                   "exactly that path and it would NOT resolve.",
     "rationale": "added by the third panel repair, which measured the real callee in the "
                  "patched container: for `A = Col(\"t\", app_label)` and "
                  "`SRC = Col(\"t\", username)`, `A == SRC` is TRUE while the labels are "
                  "`app_label` and `username` (django/db/models/expressions.py: `identity` "
                  "maps a `fields.Field` arg to `type(value)`; `__eq__` compares "
                  "identities). So the scan's match test reads the identity and nothing "
                  "else, and the label that is appended on the add path is the TERM's, not "
                  "the met column's. This rival is the previous revision of this model "
                  "exactly — structural equality on the whole pair — and it is the only "
                  "reading of the guard that no other lane can see: every other witness "
                  "either differs in identity or agrees in label, on which the two tests "
                  "coincide. Witness at one unaliased column of the term's identity "
                  "carrying a different label: gold => resolved 1, state untouched; the "
                  "rival falls through and => resolved 2 over a grown state. Built both "
                  "ways (rival 0, gold 1). G-CONF additionally REQUIRES this collapse to "
                  "be drawn (949 of 200000 cases) and requires a label-comparing control "
                  "shadow to disagree with the real code there, so the id-only test is a "
                  "measured fact of the callee rather than a stipulation of the model."},
    {"id": "anonymous-label-as-empty-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ANONEMPTY, "witness": _WIT_ANONEMPTY,
     "refinement": "its faithful real patch names the added column with an empty string "
                   "where the expression contributes no name at all; the label list is "
                   "what the combination hands down to its arms, and an empty name is "
                   "not the same value as no name — the values-list F2P tests read the "
                   "labels back and it would NOT resolve.",
     "rationale": "added by the panel repair. Pins the VALUE of the appended label on "
                  "the sub-domain where the expression has no name: same position, same "
                  "appended column, same correspondence, so the position, identity and "
                  "correspondence lanes are all blind to it. Witness at an unmatched "
                  "term whose expression has no name: gold appends an absent label, the "
                  "rival appends an empty name. Built both ways (rival 0, gold 1)."},
]
