"""properties.py — G-PBT falsification battery for django__django-12708 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. This is
a PORT of the nagini sibling battery to the lean carrier. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
``theorem correct_dropComposedIndex`` STATEMENT stays byte-identical; only the
tactic body may differ). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function selecting the constraint to drop):

  dropComposedIndex (constraints : List DbConstraint) (cols : List String)
      : Except Nat String

  A ``DbConstraint`` projects one introspected table constraint onto the fields
  the selection inspects: its ``name``, the ordered ``columns`` it covers,
  whether it backs an ordinary index (``isIndex``), whether it backs a unique
  constraint (``isUnique``), and whether it is ``excluded`` by the model's
  explicit meta options. The candidate set is every constraint that covers
  EXACTLY ``cols``, backs an ordinary index, is NOT itself unique, and is not
  excluded (``isDropCandidate``); ``dropCandidateNames`` is that set's names in
  table order. The result names the single candidate when there is exactly one,
  else reports the matching count (the count that makes the operation refuse).

  Two INDEPENDENT top-level clauses (the postcondition is a conjunction of two
  implications):

    * CLAUSE A — exactly-one branch: when the candidate set has length 1, the
      result is ``Except.ok`` of that one name. This is the branch the F2P
      exercises: with a unique constraint and an ordinary index over the same
      columns, the corrected selection admits exactly the ordinary index, so the
      result names it and the removal proceeds.

    * CLAUSE B — refusal branch: when the candidate count is not 1, the result is
      ``Except.error`` carrying that count. This is the pre-existing refuse-to-
      proceed contract; the change narrows WHICH constraints enter the count, so
      a count that wrongly includes or excludes a constraint surfaces here.

  Both branches are pinned to ``dropCandidateNames`` (the modeled selection), so
  no result may omit the non-unique requirement, target an unrelated constraint,
  match the wrong columns, count an excluded name, or fabricate a count.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so rather than
    asserted. Lean is referentially transparent: the input is an immutable
    ``List DbConstraint``; there is no read-only half permission to overwrite
    and no aliasing to exploit. The nagini ``frame-write`` rival (write to the
    read-only ``constraints`` input to satisfy the postcondition vacuously) has
    NO expressible instance here: assigning to the parameter inside the
    ``Id.run do`` block is a compile error in the surgery region — "``constraints``
    cannot be mutated, only variables declared using ``let mut`` can be mutated"
    — so the file does not elaborate for a reason that is about Lean's binder
    rules, not about the spec. The only legal analogue (bind a ``let mut`` COPY
    and clobber that) leaves the caller's list untouched and is therefore just a
    value-level wrong selection — the same class the shipped rivals already
    cover, not a permission failure. So no substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as in nagini. The postcondition is
    GROUNDED: both branches equate the result to a term built purely from the
    input via ``dropCandidateNames`` (a total ``filter``/``map`` over the input
    list). The bundle declares no ``opaque``/``axiom`` (axioms region empty), so
    there is no answer key an implementation could echo without doing the work.
    The nagini ``pos-control-cheapest`` positive (return the grounded fold
    directly) is ported as ``pos-cheapest`` to demonstrate this.

  * PARTIAL-DOMAIN / over-broad selection (nagini ``weak-overbroad-prepatch``) —
    ported as ``weak-overbroad-prepatch``: drop the ``!isUnique`` conjunct so the
    filter admits the co-located unique constraint too. This is the exact
    pre-patch bug. Refuted on the F2P-shaped input (unique + ordinary index over
    the same columns): gold count 1, rival count 2.

  * PARTIAL-DOMAIN / wrong-bit selection (nagini ``weak-pick-unique``) — ported as
    ``weak-pick-unique``: require ``isUnique`` instead of ``!isUnique`` so the
    rival selects the UNIQUE constraint for removal. Refuted where a unique and
    an ordinary index share the columns: gold names the ordinary index, rival
    names the unique constraint (Clause A, wrong ``ok`` payload).

  * PARTIAL-DOMAIN / dropped guard on the first-processed element — the nagini
    ``weak-skip-first`` (guard the increment with ``i > 1``, an artefact of the
    backward index loop, so the first-PROCESSED element is never counted) IS
    faithfully expressible on this ``for c in constraints`` fold: iterating
    ``constraints.tail!`` drops the first-processed constraint from the selection,
    the same partial-domain miss. Ported as ``weak-skip-first``: correct on every
    input whose first element is not the sole candidate, wrong on the sub-domain
    where the only ordinary index is first-iterated ([index] over ['a','b']: gold
    count 1 ⇒ Except.ok, rival count 0 ⇒ Except.error 0). The port ADDITIONALLY
    attacks the three OTHER filter conjuncts the nagini surface did not
    separately model — the column match, the exclusion flag, and the
    index-backing flag — which are genuine independent inputs to
    ``isDropCandidate`` here (``weak-wrong-columns``, ``weak-ignore-excluded``
    and ``weak-ignore-index``), varying ``cols`` and the ``excluded`` /
    ``isIndex`` fields for binder coverage. Every conjunct of the modeled
    selection is therefore attacked by exactly one rival.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that reduces the rival implementation to its
concrete ``Except`` value by ``rfl`` and derives a contradiction from the spec
predicate at that one input; each was built against its rival (must elaborate)
and against the frozen solution (must fail), so it discriminates rather than
asserting a tautology. Every witness states its refutation at fully concrete
literal inputs (no ``opaque`` term is involved), so no hypothesis is assumed and
the consistency probe has nothing to satisfy.

BINDER COVERAGE. The two input binders are ``constraints`` and ``cols``. The
reject witnesses vary BOTH: ``constraints`` differs in list length, in the
``isUnique`` / ``excluded`` / ``isIndex`` fields, and in the ``columns`` values
across the rivals; ``cols`` is ``["a","b"]`` for the over-broad / excluded /
no-index / skip-first rivals, ``["x","y"]`` for the wrong-bit rival, and ``["q"]``
(mismatching the sole constraint's ``["p"]``) for the column-match rival. Both
spec clauses are attacked: Clause A by ``weak-overbroad-prepatch``,
``weak-pick-unique`` and ``weak-skip-first``, Clause B by
``weak-wrong-columns``, ``weak-ignore-excluded``, ``weak-ignore-index`` and
``weak-wrong-error-count``.
Each of the four conjuncts of ``isDropCandidate`` is dropped or inverted by
exactly one rival, and each rival's witness point is one where the rival's
computed ``Except`` value differs OBSERVABLY from the frozen impl's (checked by
evaluation, not by argument).

REFUTATION AXES, and why the last rival exists. A rejection is only as strong as
the part of the result it contradicts, so the rivals are spread over all three
axes the ``Except Nat String`` carrier has:

  * the ``ok``/``error`` TAG — five rivals (``weak-overbroad-prepatch``,
    ``weak-wrong-columns``, ``weak-ignore-excluded``, ``weak-ignore-index``,
    ``weak-skip-first``), each refuted by ``Except.noConfusion``;
  * the ``ok`` payload (WHICH name is selected) — ``weak-pick-unique``, refuted
    by ``Except.ok.inj`` where both sides succeed but name different
    constraints;
  * the ``error`` payload (WHICH count is reported) — ``weak-wrong-error-count``,
    refuted by ``Except.error.inj`` where both sides refuse. Without it, a spec
    that pinned only the refusal's tag — or that bounded the count rather than
    fixing it — would reject every other rival here and still admit a wrong
    impl, so the count Clause B carries would be attested by nothing.

AXIOM lane: EMPTY. The axioms region of Solution.lean is empty and the modeled
selection is a total filter over the input's own data, so there is no
axiom-soundness / axiom-containment obligation for the PBT axiom lane to probe
(and that lane is G-AX's job in any case). AXIOM_TESTS is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-12708"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The whole frozen impl definition (unique). Positive controls replace it with a
# structurally different but equivalent functional form.
_IMPL_GOLD = (
    "def implementation_dropComposedIndex\n"
    "    (constraints : List DbConstraint) (cols : List String) :\n"
    "    Except Nat String := Id.run do\n"
    "  let mut names : List String := []\n"
    "  for c in constraints do\n"
    "    if isDropCandidate cols c then\n"
    "      names := names ++ [c.name]\n"
    "  if names.length != 1 then\n"
    "    return Except.error names.length\n"
    "  return Except.ok names.head!"
)

# Just the loop body + count check (lies ENTIRELY inside the impl region; unique).
# The rivals edit ONLY the filter guard inside this block.
_IMPL_BODY = (
    "  let mut names : List String := []\n"
    "  for c in constraints do\n"
    "    if isDropCandidate cols c then\n"
    "      names := names ++ [c.name]\n"
    "  if names.length != 1 then\n"
    "    return Except.error names.length\n"
    "  return Except.ok names.head!"
)

# The single filter-guard line the rivals rewrite (unique inside the impl region).
_GUARD = "    if isDropCandidate cols c then\n"

# The whole frozen proof region (markers included; unique). Positive controls
# that reshape the impl must re-close the SAME theorem statement, so they replace
# this whole region with a body that keeps the statement byte-identical.
_PROOF_START = _BASE.index("-- proof-start")
_PROOF_END = _BASE.index("-- proof-end")
_PROOF_REGION = _BASE[_PROOF_START:_PROOF_END]

# The first two proof-body lines (inside the proof region; unique). The
# admissibility case inserts a `have` BEFORE them, keeping the theorem statement
# and the rest of the frozen tactic body verbatim.
_PROOF_INTRO = (
    "  intro constraints cols\n"
    "  simp only [problem_spec_dropComposedIndex, implementation_dropComposedIndex, Id.run]"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted"
assert _BASE.count(_IMPL_BODY) == 1, "impl body drifted"
assert _BASE.count(_GUARD) == 1, "filter guard drifted"
assert _BASE.count(_PROOF_REGION) == 1, "proof region drifted"
assert _BASE.count(_PROOF_INTRO) == 1, "proof intro drifted"


def _rival(cond):
    """Frozen file with ONLY the filter guard's condition rewritten."""
    return _swap(_BASE, _GUARD, "    if " + cond + " then\n")


# The frozen theorem STATEMENT (kept byte-identical by every re-proving variant).
_THM_HEAD = (
    "-- proof-start\n"
    "theorem correct_dropComposedIndex :\n"
    "    ∀ (constraints : List DbConstraint) (cols : List String),\n"
    "      problem_spec_dropComposedIndex constraints cols\n"
    "        (implementation_dropComposedIndex constraints cols) := by\n"
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness, expect verify)
# ---------------------------------------------------------------------------

# pos-cheapest: the honest cheapest impl — return the grounded selection
# directly (a pure `if` on `dropCandidateNames`). Because the postcondition is a
# function of the args (grounded, no opaque oracle), returning it IS doing the
# work and MUST verify. Ports nagini `pos-control-cheapest`.
_POS_CHEAPEST = _swap(
    _swap(
        _BASE, _IMPL_GOLD,
        "def implementation_dropComposedIndex\n"
        "    (constraints : List DbConstraint) (cols : List String) :\n"
        "    Except Nat String :=\n"
        "  if (dropCandidateNames constraints cols).length = 1 then\n"
        "    Except.ok (dropCandidateNames constraints cols).head!\n"
        "  else\n"
        "    Except.error (dropCandidateNames constraints cols).length",
    ),
    _PROOF_REGION,
    _THM_HEAD +
    "  intro constraints cols\n"
    "  unfold problem_spec_dropComposedIndex implementation_dropComposedIndex\n"
    "  refine ⟨fun hlen => ?_, fun hlen => ?_⟩\n"
    "  · rw [if_pos hlen]\n"
    "  · rw [if_neg hlen]\n",
)

# pos-filtermap: structurally different but CORRECT — drop the mutable
# accumulator / `for` loop and spell the selection as a `let`-bound inline
# `filter`/`map` (the same computation `dropCandidateNames` performs). Ports
# nagini `pos-control-selects` (a reshape that still meets the grounded spec).
_POS_FILTERMAP = _swap(
    _swap(
        _BASE, _IMPL_GOLD,
        "def implementation_dropComposedIndex\n"
        "    (constraints : List DbConstraint) (cols : List String) :\n"
        "    Except Nat String :=\n"
        "  let names := (constraints.filter (isDropCandidate cols)).map (·.name)\n"
        "  if names.length = 1 then\n"
        "    Except.ok names.head!\n"
        "  else\n"
        "    Except.error names.length",
    ),
    _PROOF_REGION,
    _THM_HEAD +
    "  intro constraints cols\n"
    "  unfold problem_spec_dropComposedIndex implementation_dropComposedIndex dropCandidateNames\n"
    "  refine ⟨fun hlen => ?_, fun hlen => ?_⟩\n"
    "  · rw [if_pos hlen]\n"
    "  · rw [if_neg hlen]\n",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (expect verify) — the obligation is satisfiable at the F2P input
# ---------------------------------------------------------------------------

# admiss-f2p-ground: the frozen theorem carries no precondition (the behavior is
# total, `∀` unguarded), so nagini's precondition-admission probe has no binder
# to attack. The honest analogue is to discharge the spec predicate at the exact
# F2P-shaped input — a unique constraint AND an ordinary index over the same
# columns — inside the proof region as a `have`, then close the frozen obligation
# verbatim. If that ground instance could not be discharged the modeled behavior
# would be unsatisfiable at the very input the F2P exercises. Nothing is assumed:
# the theorem STATEMENT is byte-identical, the `have` is closed by `rfl`, no new
# declaration / axiom / sorry.
_F2P_CS = (
    "[ { name := \"u\", columns := [\"a\",\"b\"], isIndex := true, isUnique := true, excluded := false },\n"
    "        { name := \"i\", columns := [\"a\",\"b\"], isIndex := true, isUnique := false, excluded := false } ] [\"a\",\"b\"]"
)
_ADMISS = _swap(
    _BASE,
    _PROOF_INTRO,
    "  have _ground : problem_spec_dropComposedIndex\n"
    f"      {_F2P_CS}\n"
    "      (implementation_dropComposedIndex\n"
    f"        {_F2P_CS}) := by\n"
    "    unfold problem_spec_dropComposedIndex\n"
    f"    have hi : implementation_dropComposedIndex {_F2P_CS} = Except.ok \"i\" := by rfl\n"
    f"    have hn : dropCandidateNames {_F2P_CS} = [\"i\"] := by rfl\n"
    "    rw [hi, hn]\n"
    "    exact ⟨fun _ => rfl, fun h => absurd rfl h⟩\n"
    "  intro constraints cols\n"
    "  simp only [problem_spec_dropComposedIndex, implementation_dropComposedIndex, Id.run]",
)


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (expect reject) — each with a discriminating witness
# ---------------------------------------------------------------------------

# Constraint literals reused in the witnesses.
_U_AB = '{ name := "u", columns := ["a","b"], isIndex := true, isUnique := true, excluded := false }'
_I_AB = '{ name := "i", columns := ["a","b"], isIndex := true, isUnique := false, excluded := false }'
_U_XY = '{ name := "u2", columns := ["x","y"], isIndex := true, isUnique := true, excluded := false }'
_I_XY = '{ name := "i2", columns := ["x","y"], isIndex := true, isUnique := false, excluded := false }'
_C_P = '{ name := "x", columns := ["p"], isIndex := true, isUnique := false, excluded := false }'
_E_AB = '{ name := "e", columns := ["a","b"], isIndex := true, isUnique := false, excluded := true }'
# Covers exactly ["a","b"], non-unique, not excluded — but backs NO index.
_N_AB = '{ name := "n", columns := ["a","b"], isIndex := false, isUnique := false, excluded := false }'


def _wit_clauseA_ok_vs_error(cs, cols, rival_val):
    """Clause A: gold candidate count is 1, so the result must be `Except.ok`;
    the rival's impl reduces to `Except.error`, contradicting the first
    conjunct. Discriminates because gold's impl is `Except.ok ...`."""
    return (
        "example : ¬ problem_spec_dropComposedIndex\n"
        f"    {cs} {cols}\n"
        f"    (implementation_dropComposedIndex {cs} {cols}) := by\n"
        "  intro h\n"
        f"  have hlen : (dropCandidateNames {cs} {cols}).length = 1 := by rfl\n"
        "  have hres := h.1 hlen\n"
        f"  rw [show implementation_dropComposedIndex {cs} {cols} = {rival_val} from rfl] at hres\n"
        "  exact Except.noConfusion hres\n"
    )


def _wit_clauseA_wrong_name(cs, cols, rival_val, gold_names):
    """Clause A: both gold and rival return `Except.ok`, but of DIFFERENT names;
    the first conjunct pins the result to gold's single candidate name."""
    return (
        "example : ¬ problem_spec_dropComposedIndex\n"
        f"    {cs} {cols}\n"
        f"    (implementation_dropComposedIndex {cs} {cols}) := by\n"
        "  intro h\n"
        f"  have hlen : (dropCandidateNames {cs} {cols}).length = 1 := by rfl\n"
        "  have hres := h.1 hlen\n"
        f"  rw [show implementation_dropComposedIndex {cs} {cols} = {rival_val} from rfl] at hres\n"
        f"  rw [show dropCandidateNames {cs} {cols} = {gold_names} from rfl] at hres\n"
        "  exact absurd (Except.ok.inj hres) (by decide)\n"
    )


def _wit_clauseB_ok_vs_error(cs, cols, rival_val):
    """Clause B: gold candidate count is not 1, so the result must be
    `Except.error`; the rival's impl reduces to `Except.ok`, contradicting the
    second conjunct."""
    return (
        "example : ¬ problem_spec_dropComposedIndex\n"
        f"    {cs} {cols}\n"
        f"    (implementation_dropComposedIndex {cs} {cols}) := by\n"
        "  intro h\n"
        f"  have hlen : (dropCandidateNames {cs} {cols}).length ≠ 1 := by decide\n"
        "  have hres := h.2 hlen\n"
        f"  rw [show implementation_dropComposedIndex {cs} {cols} = {rival_val} from rfl] at hres\n"
        "  exact Except.noConfusion hres\n"
    )


def _wit_clauseB_wrong_count(cs, cols, rival_val, gold_len):
    """Clause B with the ok/error TAG HELD CONSTANT: both gold and the rival
    refuse (`Except.error`), but carry DIFFERENT counts. The second conjunct pins
    the payload to the candidate count, so a rival that refuses with the right
    tag and the wrong number is still refuted. This is the one discrimination
    axis the tag-flip and ok-name witnesses do not exercise: every other reject
    case is refuted by `Except.noConfusion` (a tag clash) or by the `ok`
    payload, so a spec that pinned only the tag would still reject them all."""
    return (
        "example : ¬ problem_spec_dropComposedIndex\n"
        f"    {cs} {cols}\n"
        f"    (implementation_dropComposedIndex {cs} {cols}) := by\n"
        "  intro h\n"
        f"  have hlen : (dropCandidateNames {cs} {cols}).length ≠ 1 := by decide\n"
        "  have hres := h.2 hlen\n"
        f"  rw [show implementation_dropComposedIndex {cs} {cols} = {rival_val} from rfl] at hres\n"
        f"  rw [show (dropCandidateNames {cs} {cols}).length = {gold_len} from rfl] at hres\n"
        "  exact absurd (Except.error.inj hres) (by decide)\n"
    )


# weak-overbroad-prepatch: the EXACT pre-patch bug — drop the `!isUnique`
# conjunct, admitting the co-located unique constraint. Ports nagini
# `weak-overbroad-prepatch`.
_WEAK_OVERBROAD = _rival("(c.columns == cols) && c.isIndex && (!c.excluded)")

# weak-pick-unique: require `isUnique` instead of `!isUnique` — selects the
# UNIQUE constraint for removal. Ports nagini `weak-pick-unique`.
_WEAK_PICK_UNIQUE = _rival("(c.columns == cols) && c.isIndex && c.isUnique && (!c.excluded)")

# weak-wrong-columns: drop the `columns == cols` conjunct — matches constraints
# regardless of which columns they cover. Attacks a filter conjunct the nagini
# surface did not separately model (its carrier passed no column list at all).
_WEAK_WRONG_COLUMNS = _rival("c.isIndex && (!c.isUnique) && (!c.excluded)")

# weak-ignore-index: drop the `c.isIndex` conjunct — selects a constraint that
# covers exactly `cols` and is neither unique nor excluded but does NOT back an
# index at all. This is the ONE conjunct of `isDropCandidate` no other rival
# moves, and the only rival that varies the `isIndex` field.
_WEAK_IGNORE_INDEX = _rival("(c.columns == cols) && (!c.isUnique) && (!c.excluded)")

# weak-ignore-excluded: drop the `!excluded` conjunct — counts a constraint the
# model's explicit meta options exclude from selection. Attacks a filter conjunct
# the nagini surface did not separately model.
_WEAK_IGNORE_EXCLUDED = _rival("(c.columns == cols) && c.isIndex && (!c.isUnique)")

# weak-skip-first: the faithful port of nagini `weak-skip-first`. The nagini
# rival guarded the increment with `i > 1` to never count the first-PROCESSED
# element of a backward index loop; on this `for c in constraints` fold the same
# partial-domain miss is expressed by iterating `constraints.tail!`, which drops
# the first-processed element from the selection. Correct on every input whose
# first element is not the sole candidate; wrong on the sub-domain where the only
# ordinary index is first-processed. Edits only the loop's source list (inside the
# impl region), so `same_spec` holds and the theorem statement is byte-identical.
_WEAK_SKIP_FIRST = _swap(_BASE, "  for c in constraints do\n",
                         "  for c in constraints.tail! do\n")

# weak-wrong-error-count: the selection and the exactly-one CHECK are both left
# correct, and so is the whole `ok` branch; only the REFUSAL branch reports a
# different number — the count of constraints covering `cols` regardless of the
# index / unique / exclusion flags. Added in audit: every other rival is refuted
# either by an `Except` TAG clash (`Except.noConfusion`) or by the `ok` payload,
# so nothing shipped tested that clause B pins the error's Nat payload to the
# candidate count. A spec that constrained only the refusal's tag, or bounded the
# count instead of fixing it, would reject all six of those rivals and admit this
# one. Edits only the error-return line inside the impl region, so `same_spec`
# holds and the theorem statement stays byte-identical.
_WEAK_WRONG_ERROR_COUNT = _swap(
    _BASE,
    "  if names.length != 1 then\n    return Except.error names.length\n",
    "  if names.length != 1 then\n"
    "    return Except.error (constraints.filter (fun c => c.columns == cols)).length\n",
)


SPEC_TESTS = [
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CHEAPEST,
        "rationale": "honest cheapest impl: return the grounded selection "
        "directly via a pure `if` on `dropCandidateNames`. The postcondition is "
        "a function of the args (grounded, no opaque oracle), so returning it IS "
        "doing the work and must verify (else SPEC-TOO-STRONG). Demonstrates "
        "there is no ungrounded answer-key to echo. Re-proved with the theorem "
        "STATEMENT byte-identical (`if_pos`/`if_neg` on each clause); no new "
        "declaration/axiom/sorry.",
    },
    {
        "id": "pos-filtermap",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FILTERMAP,
        "rationale": "structurally-different CORRECT impl: drop the mutable "
        "accumulator and `for` loop, spell the selection as an inline "
        "`filter`/`map` (definitionally `dropCandidateNames`). Must satisfy both "
        "clauses of the spec; if it cannot, SPEC-TOO-STRONG. Proof re-closes the "
        "identical theorem statement after unfolding `dropCandidateNames`; no "
        "new lemma/axiom.",
    },
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged at the exact F2P-shaped input "
        "(a unique constraint AND an ordinary index over the same columns, so the "
        "candidate set is the single ordinary index) as a `have` inside the proof "
        "region, then the frozen obligation is closed verbatim. Verifies (else "
        "the modeled behavior is unsatisfiable at the normal input, the analogue "
        "of PRECOND-TOO-STRONG). Nothing is assumed: theorem STATEMENT "
        "byte-identical, ground instance closed by `rfl`, no new "
        "declaration/axiom/sorry.",
    },
    {
        "id": "weak-overbroad-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_OVERBROAD,
        "refinement": "the faithful real patch is the PRE-patch keyword filter "
        "that omits the non-unique requirement: on a unique + ordinary index over "
        "the same columns it matches BOTH, so the exactly-one check finds 2 and "
        "the operation refuses with a wrong-number error — exactly the bug the "
        "F2P reproduces, so it does NOT resolve.",
        "rationale": "REJECT from CLAUSE A (candidate count = 1 ⇒ result = "
        "Except.ok of the one name). Dropping the `!isUnique` conjunct admits the "
        "co-located unique constraint, so the rival's count is 2 and its impl "
        "returns Except.error 2 where the spec requires Except.ok of the single "
        "ordinary index. Refuted on the F2P input [unique;index] over ['a','b'].",
        "witness": _wit_clauseA_ok_vs_error(f"[ {_U_AB}, {_I_AB} ]", '["a","b"]',
                                            "Except.error 2"),
    },
    {
        "id": "weak-pick-unique",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_PICK_UNIQUE,
        "refinement": "a faithful real patch requiring the unique flag would "
        "select the UNIQUE constraint for removal, dropping the user's unique "
        "constraint and leaving the ordinary index. The F2P asserts the unique "
        "constraint STILL exists and the index is gone, so it would fail.",
        "rationale": "REJECT from CLAUSE A (candidate count = 1 ⇒ result = "
        "Except.ok of the one name). Requiring `isUnique` instead of `!isUnique` "
        "makes the rival select the unique constraint: on [unique;index] over "
        "['x','y'] its single candidate is the unique name, so it returns "
        "Except.ok \"u2\" where the spec pins Except.ok \"i2\" (the ordinary "
        "index). Refuted at the wrong-name point.",
        "witness": _wit_clauseA_wrong_name(f"[ {_U_XY}, {_I_XY} ]", '["x","y"]',
                                           'Except.ok "u2"', '["i2"]'),
    },
    {
        "id": "weak-wrong-columns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_WRONG_COLUMNS,
        "refinement": "a real patch that drops the column match would select "
        "constraints over UNRELATED columns for deletion: removing an index on "
        "columns other than the ones requested corrupts unrelated schema, and it "
        "would not perform the requested index removal correctly, so it does NOT "
        "resolve the F2P (which asserts the index over the specific columns is "
        "gone and everything else is untouched).",
        "rationale": "REJECT from CLAUSE B (candidate count ≠ 1 ⇒ result = "
        "Except.error of the count). Dropping the `columns == cols` conjunct "
        "makes the rival match a constraint whose columns ['p'] differ from the "
        "requested ['q']: the gold candidate set for cols=['q'] is empty (length "
        "0 ≠ 1, so the spec requires Except.error 0), but the rival counts the "
        "['p'] constraint and returns Except.ok. Varies the `cols` binder to a "
        "value no other rival uses.",
        "witness": _wit_clauseB_ok_vs_error(f"[ {_C_P} ]", '["q"]',
                                            'Except.ok "x"'),
    },
    {
        "id": "weak-ignore-excluded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_IGNORE_EXCLUDED,
        "refinement": "a real patch that ignores the exclusion set would count a "
        "constraint the model declares via its explicit meta options, which the "
        "selection must skip; counting it changes the exactly-one result and "
        "could target a constraint the operation must not touch, so a faithful "
        "such patch does NOT resolve the F2P.",
        "rationale": "REJECT from CLAUSE B (candidate count ≠ 1 ⇒ result = "
        "Except.error of the count). Dropping the `!excluded` conjunct counts an "
        "excluded constraint over ['a','b']: the gold candidate set is empty "
        "(length 0 ≠ 1 ⇒ Except.error 0), but the rival counts it and returns "
        "Except.ok. Varies the `excluded` field of `constraints`, which no other "
        "rival moves.",
        "witness": _wit_clauseB_ok_vs_error(f"[ {_E_AB} ]", '["a","b"]',
                                            'Except.ok "e"'),
    },
    {
        "id": "weak-ignore-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_IGNORE_INDEX,
        "refinement": "a real patch that omits the requirement that the "
        "constraint actually back an index would select a same-columns "
        "constraint that is not an index at all, so the removal would target "
        "the wrong kind of object and the requested index would still be "
        "present — the F2P asserts the index over those columns is GONE, so "
        "such a patch does NOT resolve.",
        "rationale": "REJECT from CLAUSE B (candidate count ≠ 1 ⇒ result = "
        "Except.error of the count). Dropping the `c.isIndex` conjunct — the "
        "only conjunct of the modeled selection no other rival moves — makes "
        "the rival count a constraint that covers exactly ['a','b'] and is "
        "neither unique nor excluded but backs NO index: the gold candidate "
        "set is empty (length 0 ≠ 1 ⇒ Except.error 0), while the rival returns "
        "Except.ok \"n\". Varies the `isIndex` field, which no other rival "
        "varies.",
        "witness": _wit_clauseB_ok_vs_error(f"[ {_N_AB} ]", '["a","b"]',
                                           'Except.ok "n"'),
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_SKIP_FIRST,
        "refinement": "a real patch that fails to consider the first candidate "
        "constraint in the column-match loop would miss removing an ordinary "
        "index declared first, leaving the index present — the F2P asserts the "
        "index over the columns is GONE, so whenever the sole ordinary index is "
        "the first-iterated constraint the patch does NOT resolve.",
        "rationale": "REJECT from CLAUSE A (candidate count = 1 ⇒ result = "
        "Except.ok of the one name). Iterating `constraints.tail!` drops the "
        "first-processed constraint from the selection: on the single-element "
        "input [index] over ['a','b'] the gold candidate set is the one ordinary "
        "index (length 1 ⇒ Except.ok \"i\"), but the rival's tail is empty so its "
        "count is 0 and it returns Except.error 0. Partial-domain: correct on "
        "most inputs, wrong on the sub-domain where the only candidate is "
        "first-iterated. Ports nagini `weak-skip-first` (its backward-index "
        "`i > 1` guard, faithful on this fold as dropping the first element).",
        "witness": _wit_clauseA_ok_vs_error(f"[ {_I_AB} ]", '["a","b"]',
                                            "Except.error 0"),
    },
    {
        "id": "weak-wrong-error-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_WRONG_ERROR_COUNT,
        "refinement": "a faithful real patch that refuses with the number of "
        "constraints covering the requested columns — rather than the number "
        "that actually passed the selection filter — reports a count that does "
        "not describe the candidate set it refused over. The refusal is the "
        "operation's diagnostic: it tells the operator how many objects "
        "collided, and a number computed before the index/unique/exclusion "
        "flags are applied names a collision that the corrected selection does "
        "not have. It also does NOT resolve the F2P, because a patch whose "
        "refusal branch counts every same-columns constraint has not narrowed "
        "the selection at all on the refusing sub-domain.",
        "rationale": "REJECT from CLAUSE B (candidate count ≠ 1 ⇒ result = "
        "Except.error of THAT count). The selection, the exactly-one check and "
        "the entire `ok` branch are left CORRECT; only the refusal's payload "
        "changes. On a single EXCLUDED constraint over ['a','b'] the gold "
        "candidate set is empty, so the spec requires Except.error 0, while the "
        "rival counts the column match and returns Except.error 1. Both sides "
        "return `Except.error`, so this is the only rival whose refutation "
        "survives holding the ok/error TAG constant — the axis on which the six "
        "other rejects (five tag flips plus one `ok`-payload clash) attest "
        "nothing.",
        "witness": _wit_clauseB_wrong_count(f"[ {_E_AB} ]", '["a","b"]',
                                            "Except.error 1", "0"),
    },
]


# The axioms region of Solution.lean is empty and the modeled selection is a
# total filter over the input's own data, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge (G-AX owns that lane).
AXIOM_TESTS = []
