"""properties.py — G-PBT falsification battery for django__django-11087 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_collectFieldSelection``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled decision):

  collectFieldSelection (guardA guardB : Bool) (pkColumn : String)
                        (allFields defaultColumns skippedNames : List String)
                        (candidateRelations : List (List String)) : List String
    Chooses the column set the fetch for the objects visited during a cascade
    ends up loading. The postcondition pins the result BY FULL VALUE over the
    WHOLE guard partition, with two independent top-level clauses:
      * (guardA = false ∧ guardB = false) →
            result = loadedColumns pkColumn allFields skippedNames
                                   candidateRelations
        — the restricted branch: what a fetch restricted to the referenced
          columns actually loads;
      * ¬ (guardA = false ∧ guardB = false) →
            result = defaultColumns
        — every other guard combination hands the fetch on untouched, so it
          loads exactly what it loaded by default.
    ``referencedColumns cands = cands.flatten.dedup``,
    ``restrictionNames skip cands =
        (referencedColumns cands).filter (fun c => !skip.contains c)`` and
    ``loadedColumns pk all skip cands = if (restrictionNames skip cands).isEmpty
    then all else (pk :: restrictionNames skip cands).dedup`` are fully grounded
    helpers (flatten, dedup, a filter, an emptiness test and a cons), NOT opaque
    answer-keys: there is nothing an implementation could echo without doing the
    gather, so the ungrounded-oracle-echo class does not apply. There is no
    length-only / value-proxy clause: a partial-domain rival must diverge on a
    real sub-domain (a guard sub-case, the shape of ``candidateRelations``, the
    content of ``skippedNames``, or the three behaviours ``loadedColumns``
    composes — pk retention, the dropping of already-skipped names, and the
    nothing-to-restrict-to case).

  THE RESTRICTED LOAD IS NOT THE BARE REFERENCED SET. Three separate behaviours
  of the real carrier stand between the gathered set and the columns the fetch
  ends up loading, and each has its own reject case below:

    * restricting a fetch to a named column set RETAINS the identifying column
      whether or not a relation points at it (``weak-drop-pk``) — and even when
      the fetch had been told to leave that very column out
      (``weak-drop-pk-when-skipped``), because the retention is applied by the
      fetch after the request has already been reduced;
    * the restriction is a REPLACEMENT, not an addition: a name the fetch had
      already been told to leave out cannot be asked for, so it drops out of the
      request (``weak-ignore-skipped``) — and if that leaves the request naming
      nothing, the fetch is left alone and loads the whole row, including the
      names it had been told to leave out (``weak-restrict-to-nothing``). The
      reduction applies to the REQUEST and not merely to the decision whether to
      restrict at all, which is separable only where the skip set and the
      referenced set overlap PARTIALLY (``weak-referenced-unfiltered``);
    * on the pass-through branch the fetch is handed on EXACTLY as it arrived,
      so the load is that fetch's own default column set, which need not be the
      whole row (``weak-full-branch-allfields``).

  All four were measured against the real carrier rather than assumed: an
  exhaustive sweep over five model shapes (a flat model, a custom-identity
  model, a leaf, and both halves of a multi-table-inheritance pair) × every
  subset of already-skipped names × every subset of referenced names, plus
  chained prior states (skip-then-skip and restrict-then-skip): 33,856 inputs,
  0 disagreements, hitting all three legs of ``loadedColumns``
  (restricted-nonempty 7,364; restricted-empty 1,100; pass-through 25,392). The
  pass-through leg was additionally confirmed end-to-end against the SQL of
  eight real cascade deletes.

CASE-COUNT vs NAGINI (carrier narrowing — see the porting notes below).

  The nagini sibling modeled TWO functions:

    (1) a two-flag boolean helper == the disjunction of its arguments
    (2) the column-selection decision over (the whole row, the referenced
        columns, and the two guard flags)

  On this carrier only the field-selection decision (2) is a first-class
  obligation. The boolean helper (1) is NOT modeled as a function: its value
  enters (2) as the single opaque ``guardB : Bool`` input. So the three nagini
  bool-helper cases (pos-control-bool-demorgan, partial-bool-drop-post,
  partial-bool-always-true) have no free-standing counterpart. Their ADVERSARIAL
  INTENT is preserved, re-expressed against the field-selection guard instead of
  a separate predicate:
    * "drop the post term" (a guard term stops mattering) ports as a rival that
      ignores the ``guardB`` binder — see weak-ignore-guardB;
    * "always-True" (never restrict) is behaviourally the pre-patch
      hand-the-fetch-on impl, which is exactly weak-overfetch here;
    * the De Morgan bool positive ports as a De Morgan reshape of the guard —
      pos-guard-demorgan.

  The two nagini FRAME-MUTATION rivals (a rival that WRITES a read-only,
  half-permission input) are VACUOUS on this carrier: Lean is referentially
  transparent — ``allFields`` and ``candidateRelations`` are passed by value,
  there is no ``Acc(...,1/2)`` half-permission to overwrite and no aliasing to
  exploit. Those rivals have no expressible instance here and no substitute is
  fabricated for them.

  DEMONSTRATED, not merely asserted: the closest expressible analogue is an impl
  that shadows both input binders with ``let mut`` locals and writes them before
  computing the result. Such an impl VERIFIES against the frozen obligation once
  its proof accounts for the reshaped term (checked by an audit: the write-back
  variant elaborates, exit 0). The write is unobservable to any caller because
  the callee received copies, which is exactly why the permission-violation
  outcome that makes the nagini cases meaningful has no analogue here — there is
  no wrong behaviour for a witness to pin. A ``reject`` case built this way would
  be a case that CANNOT be refuted, not a rival.

  There is no DIVERGENCE / non-termination lane in the nagini sibling to port,
  and on lean it would be vacuous regardless: ``implementation_*`` is a total
  Lean ``def``, so a diverging implementation cannot be written at all.

  The nagini axiom lane is empty (AXIOM_TESTS == []) and is out of G-PBT scope
  regardless (that lane belongs to G-AX). No axiom case is ported.

  What DOES port — the partial-domain / value attacks — is instantiated against
  the field-selection obligation and its two independent clauses:
    * weak-overfetch          — never restrict; violates the restricted-branch
      clause. This is the pre-patch impl, byte-for-byte the twin's impl region.
    * weak-ignore-guardA      — restrict even when the first guard holds;
      violates the pass-through clause on the ``guardA = true`` sub-domain;
    * weak-ignore-guardB      — restrict even when the second guard holds;
      violates the pass-through clause on the ``guardB = true`` sub-domain;
    * weak-gather-first-only   — a value-mask on the gather: keep only the FIRST
      candidate relation's target columns, dropping the columns every later
      relation points at. Wrong as a SET, so the divergence survives the
      set-valued reading of the result that this bundle's conformance bridge
      uses (see the note below).
    * weak-guard-flags-agree   — restrict iff the two guard flags AGREE, i.e.
      correct on three of the four guard combinations and wrong at exactly
      (guardA = true, guardB = true). Pins the one guard corner no other rival
      distinguishes.
    * weak-drop-pk             — restrict to the BARE requested set, dropping the
      identifying column. Correct on every input whose requested set happens to
      contain the identifying column, and wrong precisely when no relation
      points at it — the ordinary case of a relation that targets a non-identity
      column. Set-level, so it survives the set-valued reading of the result.
    * weak-restrict-to-nothing — drop the nothing-to-restrict-to case: restrict
      to just the identifying column even when the request names no column at
      all, where the whole row is loaded instead. Wrong only on the
      empty-request sub-domain, which is reachable by a real cascade (a leaf
      with no incoming relation, or a fetch already told to leave out every
      referenced name) and which no other rival probes.
    * weak-ignore-skipped      — gather and request the referenced columns while
      IGNORING the names the fetch had already been told to leave out. Correct
      on every input with an empty ``skippedNames`` — i.e. on the entire
      sub-domain the other rivals inhabit — and wrong exactly where a skipped
      name meets the referenced set. This is the model this bundle shipped
      before the panel repair, so the case exists to keep that reading refuted:
      its witness is the measured input where the two disagree.
    * weak-full-branch-allfields — on the pass-through branch return the whole
      row instead of what the fetch loads by default. Correct whenever the
      incoming fetch had been told nothing (``defaultColumns = allFields``), and
      wrong exactly when it had. The other half of the pre-repair model.
    * weak-referenced-unfiltered — apply the skip reduction only to the DECISION
      (is there anything left to restrict to?) and then load the unreduced
      referenced set. Agrees with the frozen impl when the skip set and the
      referenced set are disjoint AND when the skip covers the referenced set
      entirely, so it is wrong on exactly one sub-domain: a partial overlap.
    * weak-drop-pk-when-skipped — retain the identifying column except when the
      fetch had been told to leave that column out. Agrees with the frozen impl
      everywhere ``weak-drop-pk`` is probed, and is wrong only where the skip set
      contains the identifying column.

  A NOTE ON WHAT COUNTS AS AN OBSERVABLE DIFFERENCE HERE. ``result`` is a
  ``List String`` but the decision it models is a column CHOICE, which is
  membership-determined: ``mapping.md`` records the list↔set bijection and the
  bundle's conformance bridge compares ``set(shadow) == set(oracle)``. A rival
  that differs from the frozen impl only in the ORDER or the MULTIPLICITY of the
  gathered column names therefore models no behavioural difference on the real
  carrier, even though the frozen ``List``-valued postcondition rejects it. An
  audit of this battery replaced an earlier ``flatten``-without-``dedup`` rival
  for exactly that reason: the rejection was real but attributable to the
  list encoding rather than to the modeled decision, and its refinement
  argument (that the un-deduplicated gather would change the emitted query)
  did not hold — the consuming API set-collapses the column names it is handed
  and derives the emitted column order from the model's own field order, so a
  repeated name is absorbed before it can be observed. ``weak-gather-first-only``
  replaces it with a gather rival that drops referenced columns outright, which
  is a set-level divergence and so is wrong under either reading.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at one concrete, ``decide``-able input; each was checked to ELABORATE
against its rival (the rival provably contradicts the spec there) and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). The witnesses spread over EVERY input binder of the predicate, and
over ALL FOUR guard combinations: (false, false) — overfetch,
gather-first-only, drop-pk, restrict-to-nothing, ignore-skipped; (true, false) —
ignore-guardA; (false, true) — ignore-guardB, full-branch-allfields;
(true, true) — guard-flags-agree; and the two rivals that probe how the skip set
and the restriction interact (referenced-unfiltered, drop-pk-when-skipped) are
refuted at (false, false), the branch on which the interaction exists at all. So
the guard partition is probed exhaustively rather than sampled.
``skippedNames`` is exercised at four distinct configurations, chosen so that
each isolates one leg: DISJOINT from the referenced set is the empty case most
witnesses use; COVERING it empties the request (ignore-skipped); PARTIALLY
overlapping it keeps the request non-empty but smaller
(referenced-unfiltered); and CONTAINING the identifying column pits the
reduction against the retention (drop-pk-when-skipped). ``pkColumn``,
``allFields``, ``defaultColumns``,
``skippedNames`` and ``candidateRelations`` are concrete throughout;
``candidateRelations`` additionally takes a multi-relation shape
(gather-first-only), an EMPTY shape (restrict-to-nothing) and a shape whose
gathered set excludes the identifying column (drop-pk), each distinct from the
single-relation shape the others use, so the "which relations contribute"
dimension is exercised and not just the flags. ``pkColumn`` takes a value
absent from the gathered set (drop-pk) and a non-``"id"`` value
(restrict-to-nothing, an inherited-child identifying column), so it is not
pinned to one string across the battery. ``skippedNames`` is non-empty in the
two witnesses whose sub-domain it defines (ignore-skipped,
full-branch-allfields), and in both of those ``defaultColumns`` is a strict
subset of ``allFields`` — the configuration in which the two binders are
distinguishable at all. Four of the witnesses are transcriptions of MEASURED
carrier states rather than constructions (ignore-skipped, full-branch-allfields,
referenced-unfiltered, drop-pk-when-skipped): see mapping.md §3 rows 1, 4, 11
and 12, each of which records the column list the real fetch loads there.

Every witness in this battery closes by ``decide`` on ground data and its
gold-side failure is a plain evaluation — the frozen impl's own reduction shows
the asserted refutation to be false, reported as ``Tactic `decide` proved that
the proposition ¬(...) is false``. Each was additionally re-checked by an audit
in the FORGERY direction (attack B′): the same witness with its ``¬`` dropped —
i.e. asserting the frozen impl IS correct at that input — ELABORATES against the
frozen solution (exit 0) and FAILS against the rival. The gold-side exit code
therefore tracks the claim rather than being a fixed artifact of the file, which
is what makes the discrimination real.
"""
from pathlib import Path

INSTANCE = "django__django-11087"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---- region anchor: the FULL body of the `impl` region (unique in
# Solution.lean). Every replacement below lands entirely inside the impl region,
# so `same_spec` holds and the theorem STATEMENT is untouched. ----
_IMPL_OLD = (
    "  let mut loaded := defaultColumns\n"
    "  if !(guardA || guardB) then\n"
    "    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
    "  return loaded"
)

assert _BASE.count(_IMPL_OLD) == 1, "impl-collectFieldSelection drifted"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify. If a faithful correct
    # implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token. The frozen
    # proof body (`cases guardA <;> cases guardB <;> ...`) closes each because
    # the reshaped `Id.run do` reduces on concrete Bool values.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: initialise the accumulator to the RESTRICTED column set and
        # override it with the pass-through set on the else-of-the-frozen-guard,
        # rather than initialising to the pass-through set and restricting.
        # Computes the SAME value for every guard combination.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
            "  if guardA || guardB then\n"
            "    loaded := defaultColumns\n"
            "  return loaded",
        ),
        "rationale": "A correct reshape of the sole obligation: the accumulator "
                     "is initialised to `loadedColumns pkColumn allFields "
                     "skippedNames candidateRelations` and overridden with "
                     "`defaultColumns` exactly when `guardA || guardB`, so on "
                     "every guard combination it returns the same value as the "
                     "frozen impl (restricted branch iff `guardA=false ∧ "
                     "guardB=false`). If it cannot verify, the postcondition "
                     "is SPEC-TOO-STRONG. Proof: the frozen "
                     "`cases … <;> cases … <;> refine … <;> first | rfl | …` "
                     "closes it because the `Id.run do` reduces on concrete "
                     "Bool values.",
    },
    {
        "id": "pos-guard-demorgan",
        "kind": "soundness",
        "expect": "verify",
        # De Morgan reshape of the guard: `!(a || b)` rewritten as `!a && !b`
        # (the lean analogue of the nagini De Morgan bool positive). Same
        # branch taken on every input.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !guardA && !guardB then\n"
            "    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
            "  return loaded",
        ),
        "rationale": "De Morgan-equal guard `!guardA && !guardB` == "
                     "`!(guardA || guardB)`; the same branch fires on "
                     "every input, so the result equals the frozen impl "
                     "pointwise. If it cannot verify, the postcondition is "
                     "SPEC-TOO-STRONG. The frozen proof closes it (concrete "
                     "Bools reduce the guard).",
    },
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen theorem is unconditional (no precondition binder); the
        # honest analogue of the nagini precondition-admission probe is to
        # discharge the spec at a ground, F2P-shaped input — the restricted
        # branch (both guard flags false) over the exact reported column config
        # (whole row {id, unique_field, large_field}, loaded in full by default,
        # nothing already skipped; one candidate relation referencing
        # {id, unique_field}) — by evaluation, then close the frozen obligation
        # verbatim. The impl region is unchanged; a `have` is prepended inside
        # the existing tactic body, so the theorem STATEMENT is byte-identical
        # and nothing new is declared.
        "module": _swap(
            _BASE,
            "  intro guardA guardB pkColumn allFields defaultColumns skippedNames candidateRelations",
            "  have _ground : problem_spec_collectFieldSelection false false \"id\"\n"
            "      [\"id\", \"unique_field\", \"large_field\"]\n"
            "      [\"id\", \"unique_field\", \"large_field\"] [] [[\"id\", \"unique_field\"]]\n"
            "      (implementation_collectFieldSelection false false \"id\"\n"
            "        [\"id\", \"unique_field\", \"large_field\"]\n"
            "        [\"id\", \"unique_field\", \"large_field\"] [] [[\"id\", \"unique_field\"]]) := by\n"
            "    unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "    decide\n"
            "  intro guardA guardB pkColumn allFields defaultColumns skippedNames candidateRelations",
        ),
        "rationale": "The obligation is discharged at a ground F2P-shaped input "
                     "(both guard flags false; whole row "
                     "{id,unique_field,large_field}, loaded in full by default, "
                     "nothing already skipped; one candidate relation "
                     "referencing {id,unique_field}) by `decide`, then the "
                     "frozen obligation is closed verbatim. Verifies (else the "
                     "spec is unsatisfiable at a normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: the ground "
                     "instance is a `have` inside the existing tactic body, the "
                     "impl region and the theorem statement are unchanged.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete input, checked to elaborate against the rival and fail on the
    # frozen solution.
    # =====================================================================
    {
        "id": "weak-overfetch",
        "kind": "uniqueness",
        "expect": "reject",
        # Never restrict: always hand the fetch on untouched. This is the
        # pre-patch behaviour (== the nagini partial-prepatch-overfetch rival,
        # and behaviourally == its always-True near-miss). Byte-identical to the
        # prepatch twin's impl region.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  return loaded",
        ),
        "refinement": "This IS the pre-patch behaviour: hand the fetch on "
                      "untouched, never restricting it. The sole F2P asserts "
                      "that in the unguarded case the cascade SELECT loads "
                      "ONLY the referenced columns (its captured SQL equals the "
                      "restricted query); loading the fetch's default columns "
                      "produces a different SELECT and fails that assertEqual. "
                      "Its faithful real patch (the un-restricted branch) is "
                      "exactly what does NOT resolve.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations`: when the restricted load differs "
                     "from the fetch's default columns on that sub-domain, "
                     "returning `defaultColumns` violates it. Refuted at "
                     "(false, false, \"id\", {id,unique_field,large_field}, "
                     "default={id,unique_field,large_field}, skipped={}, "
                     "[[id,unique_field]]) — the reported unguarded input, "
                     "where the referenced set omits `large_field`.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"id\"\n"
            "    [\"id\", \"unique_field\", \"large_field\"]\n"
            "    [\"id\", \"unique_field\", \"large_field\"] [] [[\"id\", \"unique_field\"]]\n"
            "    (implementation_collectFieldSelection false false \"id\"\n"
            "      [\"id\", \"unique_field\", \"large_field\"]\n"
            "      [\"id\", \"unique_field\", \"large_field\"] [] [[\"id\", \"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-guardA",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the first term from the guard: restrict whenever the second guard
        # is clear, regardless of the first (== nagini
        # partial-ignore-select-related).
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !guardB then\n"
            "    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
            "  return loaded",
        ),
        "refinement": "Restricting the fetch even when the first guard holds "
                      "puts the restriction in conflict with the machinery that "
                      "guard protects, which the intended behaviour keeps apart "
                      "by handing the fetch on untouched whenever the guard is "
                      "set. A change that restricted under it would load the "
                      "wrong column set for those cascades and would not be the "
                      "resolving change.",
        "rationale": "REJECT from the pass-through clause "
                     "`¬(guardA=false ∧ guardB=false) → "
                     "result = defaultColumns`: on the sub-domain guardA=true, "
                     "guardB=false the rival restricts to "
                     "`loadedColumns …` instead of the required "
                     "`defaultColumns`. Refuted at (true, false, \"id\", "
                     "{id,unique_field}, default={id,unique_field}, "
                     "skipped={}, [[id]]) — the only witness with guardA=true, "
                     "and a distinct `allFields` value (the request names only "
                     "{id} ⊊ allFields={id,unique_field}) so the pass-through "
                     "and restricted values are genuinely different there.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection true false \"id\"\n"
            "    [\"id\", \"unique_field\"] [\"id\", \"unique_field\"] [] [[\"id\"]]\n"
            "    (implementation_collectFieldSelection true false \"id\"\n"
            "      [\"id\", \"unique_field\"] [\"id\", \"unique_field\"] [] [[\"id\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-guardB",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the second term from the guard: restrict whenever the first guard
        # is clear, regardless of the second. The lean re-expression of the
        # nagini "drop the post term" bool rival — the `guardB` binder stops
        # mattering.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !guardA then\n"
            "    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
            "  return loaded",
        ),
        "refinement": "Ignoring the second guard restricts the fetch even when "
                      "that guard is set. The F2P's sub-tests for that "
                      "condition assert that the fetch is left alone so the "
                      "full object is materialised; a patch that restricted "
                      "with the guard set would hide columns from the consumer "
                      "the guard exists for and fail those subtests, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from the pass-through clause "
                     "`¬(guardA=false ∧ guardB=false) → "
                     "result = defaultColumns`: on the sub-domain guardA=false, "
                     "guardB=true the rival restricts to `loadedColumns …` "
                     "instead of the required `defaultColumns`. Refuted at "
                     "(false, true, \"id\", "
                     "{id,unique_field,large_field,extra}, "
                     "default={id,unique_field,large_field,extra}, "
                     "skipped={}, [[id,unique_field]]) — its own `allFields` "
                     "value (carrying an extra column no other witness has), so "
                     "both the guardB and allFields binders are exercised at "
                     "values no other rival probes.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false true \"id\"\n"
            "    [\"id\", \"unique_field\", \"large_field\", \"extra\"]\n"
            "    [\"id\", \"unique_field\", \"large_field\", \"extra\"] []\n"
            "    [[\"id\", \"unique_field\"]]\n"
            "    (implementation_collectFieldSelection false true \"id\"\n"
            "      [\"id\", \"unique_field\", \"large_field\", \"extra\"]\n"
            "      [\"id\", \"unique_field\", \"large_field\", \"extra\"] []\n"
            "      [[\"id\", \"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-gather-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-mask on the gather that is wrong AS A SET: keep only the FIRST
        # candidate relation's target columns and drop every later relation's.
        # Takes the right branch on every guard combination but computes a
        # strictly-too-small column set whenever a second relation contributes a
        # column the first does not. `.dedup` is kept so the ONLY difference from
        # the frozen gather is the dropped relations — not the list encoding.
        #
        # This REPLACES an earlier `flatten`-without-`dedup` rival. That rival
        # was rejected honestly, but its divergence from the frozen impl was pure
        # multiplicity: it returned the same column names with a repeat. Since
        # the modeled decision is a membership-determined column choice (see the
        # set-vs-list note in the module docstring and in mapping.md), a
        # repeat-only difference is not observable on the real carrier, so that
        # rejection attested to the List encoding rather than to the decision.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !(guardA || guardB) then\n"
            "    loaded := loadedColumns pkColumn allFields skippedNames [candidateRelations.headD []]\n"
            "  return loaded",
        ),
        "refinement": "Gathering the target columns of only the first candidate "
                      "relation drops the columns that every other relation "
                      "points at, so the restricted load omits columns some "
                      "relation genuinely needs. That is a strictly smaller "
                      "column SET, not a reordering or a repeat: the cascade "
                      "would then fetch objects missing a column a later "
                      "relation must read to continue the walk. The reported "
                      "scenario has two relations pointing at the related model "
                      "and pins the restricted load to the union of what both "
                      "reference, so a change gathering just the first relation "
                      "loads a smaller set than that and does NOT resolve.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations` where `referencedColumns = "
                     "flatten.dedup` gathers across ALL relations: with two "
                     "relations the rival returns only the first one's columns. "
                     "Refuted at (false, false, \"id\", "
                     "{id,unique_field,large_field}, "
                     "default={id,unique_field,large_field}, skipped={}, "
                     "[[id],[id,unique_field]]) — the rival yields {id} where "
                     "the clause requires {id,unique_field}, a set-level "
                     "difference. The only witness with a multi-relation "
                     "candidateRelations shape.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"id\"\n"
            "    [\"id\", \"unique_field\", \"large_field\"]\n"
            "    [\"id\", \"unique_field\", \"large_field\"] []\n"
            "    [[\"id\"], [\"id\", \"unique_field\"]]\n"
            "    (implementation_collectFieldSelection false false \"id\"\n"
            "      [\"id\", \"unique_field\", \"large_field\"]\n"
            "      [\"id\", \"unique_field\", \"large_field\"] []\n"
            "      [[\"id\"], [\"id\", \"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-guard-flags-agree",
        "kind": "uniqueness",
        "expect": "reject",
        # The one guard corner no other rival distinguishes. Restrict iff the two
        # flags AGREE: correct at (false,false) restricted, correct at
        # (true,false) and (false,true) pass-through, and WRONG at (true,true),
        # where it restricts although the fetch must be handed on. Every other
        # reject case in this battery is refuted at a corner with at most one
        # flag set, so without this one the (true,true) cell of the guard
        # partition is pinned by no witness at all.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if guardA == guardB then\n"
            "    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
            "  return loaded",
        ),
        "refinement": "Restricting when BOTH guards are set is wrong for the "
                      "union of the two reasons the pass-through branch exists, "
                      "so a change of this shape gets the column set wrong on "
                      "exactly the cascades where both conditions hold at once; "
                      "the reported scenario's assertions for those conditions "
                      "fail and it does NOT resolve.",
        "rationale": "REJECT from the pass-through clause "
                     "`¬(guardA=false ∧ guardB=false) → "
                     "result = defaultColumns`: on the sub-domain guardA=true, "
                     "guardB=true the rival restricts to `loadedColumns …` "
                     "instead of the required `defaultColumns`. Refuted at "
                     "(true, true, \"id\", {id,unique_field,large_field}, "
                     "default={id,unique_field,large_field}, skipped={}, "
                     "[[unique_field]]) — the ONLY witness at the (true, true) "
                     "guard corner, and a candidateRelations value whose "
                     "gathered column ({unique_field}) is a strict subset of "
                     "allFields, so the two sides of the clause are genuinely "
                     "distinct there.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection true true \"id\"\n"
            "    [\"id\", \"unique_field\", \"large_field\"]\n"
            "    [\"id\", \"unique_field\", \"large_field\"] [] [[\"unique_field\"]]\n"
            "    (implementation_collectFieldSelection true true \"id\"\n"
            "      [\"id\", \"unique_field\", \"large_field\"]\n"
            "      [\"id\", \"unique_field\", \"large_field\"] [] [[\"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-pk",
        "kind": "uniqueness",
        "expect": "reject",
        # Restrict to the BARE requested set, dropping the identifying column.
        # Takes the right branch on every guard combination, gathers across ALL
        # relations and honours `skippedNames`, so it is wrong ONLY through the
        # identity column, and only when no relation happens to point at it —
        # the ordinary case of a relation targeting a non-identity column.
        # `.dedup` is kept, so the sole difference from the frozen impl is the
        # missing identifying column, not the list encoding.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !(guardA || guardB) then\n"
            "    loaded := restrictionNames skippedNames candidateRelations\n"
            "  return loaded",
        ),
        "refinement": "A fetch cannot be restricted so far that it stops "
                      "identifying the rows it returns: the objects fetched "
                      "during a cascade must still be identifiable, because the "
                      "walk continues from them and they are what finally gets "
                      "deleted. Restricting to the bare requested set omits the "
                      "identifying column whenever no relation points at it, "
                      "which is the ordinary situation for a relation that "
                      "targets some other unique column. A change of this shape "
                      "would load rows that cannot be identified, so it is not "
                      "the resolving change.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations`: `loadedColumns` retains `pkColumn`, "
                     "the rival does not. Refuted at (false, false, \"id\", "
                     "{id,origin_id,unique_field,large_field}, "
                     "default={id,origin_id,unique_field,large_field}, "
                     "skipped={}, [[unique_field]]) — a single relation whose "
                     "only target column is NOT the identifying column, so the "
                     "rival yields {unique_field} where the clause requires "
                     "{id,unique_field}. A set-level difference, and the only "
                     "witness whose gathered set excludes `pkColumn`.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"id\"\n"
            "    [\"id\", \"origin_id\", \"unique_field\", \"large_field\"]\n"
            "    [\"id\", \"origin_id\", \"unique_field\", \"large_field\"] []\n"
            "    [[\"unique_field\"]]\n"
            "    (implementation_collectFieldSelection false false \"id\"\n"
            "      [\"id\", \"origin_id\", \"unique_field\", \"large_field\"]\n"
            "      [\"id\", \"origin_id\", \"unique_field\", \"large_field\"] []\n"
            "      [[\"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-restrict-to-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the nothing-to-restrict-to case: always restrict (to the
        # identifying column alone when the request names nothing) instead of
        # leaving the fetch alone. Correct on every input whose request is
        # non-empty; wrong exactly on the empty-request sub-domain.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !(guardA || guardB) then\n"
            "    loaded := (pkColumn :: restrictionNames skippedNames candidateRelations).dedup\n"
            "  return loaded",
        ),
        "refinement": "When the request names no column there is nothing for "
                      "the restriction to say, and the fetch is left as it is — "
                      "the whole row. A change that instead restricted such a "
                      "fetch to the identifying column alone would strip every "
                      "other column from objects that are fetched with no "
                      "restriction at all in the intended behaviour, which is "
                      "observable for any leaf of the cascade graph (a related "
                      "model nothing else points at, reached whenever it cannot "
                      "be deleted in one step). So it is not the resolving "
                      "change.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations`: on the empty-`candidateRelations` "
                     "sub-domain `loadedColumns` returns `allFields`, while the "
                     "rival returns just `[pkColumn]`. Refuted at (false, "
                     "false, \"base_ptr_id\", "
                     "{id,base_ptr_id,origin_id,large_field}, "
                     "default={id,base_ptr_id,origin_id,large_field}, "
                     "skipped={}, []) — the ONLY witness with an empty gather, "
                     "and the only one whose `pkColumn` is not \"id\" (an "
                     "inherited child's identifying column), so neither binder "
                     "is pinned to a single value across the battery.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"base_ptr_id\"\n"
            "    [\"id\", \"base_ptr_id\", \"origin_id\", \"large_field\"]\n"
            "    [\"id\", \"base_ptr_id\", \"origin_id\", \"large_field\"] [] []\n"
            "    (implementation_collectFieldSelection false false \"base_ptr_id\"\n"
            "      [\"id\", \"base_ptr_id\", \"origin_id\", \"large_field\"]\n"
            "      [\"id\", \"base_ptr_id\", \"origin_id\", \"large_field\"] [] []) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        # Request the referenced columns while IGNORING the names the fetch has
        # already been told to leave out — i.e. `loadedColumns` with an empty
        # skip list. Correct on the whole `skippedNames = []` sub-domain (every
        # other witness in this battery), and wrong exactly where a skipped name
        # meets the referenced set: there the request loses that name, and if
        # that empties the request the fetch is left alone and loads the whole
        # row instead.
        #
        # This is the model this bundle shipped BEFORE the panel repair. The case
        # exists so that reading stays refuted by a machine-checked witness
        # rather than by prose, and its witness is the measured carrier state at
        # which the two disagree (mapping.md §3, row 1).
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !(guardA || guardB) then\n"
            "    loaded := loadedColumns pkColumn allFields [] candidateRelations\n"
            "  return loaded",
        ),
        "refinement": "A restriction cannot ask a fetch for a column it has "
                      "already been told to leave out: the request is reduced "
                      "by those names before it takes effect. A change that "
                      "assumed otherwise would predict a load that never "
                      "happens — for a fetch already told to leave out the very "
                      "column a relation points at, it would claim a two-column "
                      "load where the real fetch, left with nothing to restrict "
                      "to, loads the whole row. Cascades over such a fetch "
                      "would then be driven from a column set the query does "
                      "not have, so this is not the resolving change.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations`: the rival evaluates the same helper "
                     "at `[]` instead of `skippedNames`. Refuted at (false, "
                     "false, \"id\", {id,large_field,origin_id,unique_field}, "
                     "default={id,large_field,origin_id}, "
                     "skipped={unique_field}, [[unique_field]]) — the request "
                     "{unique_field} is emptied by the skip, so the clause "
                     "requires the whole row while the rival returns "
                     "{id,unique_field}. The only sub-domain in the battery "
                     "where `skippedNames` and the referenced set overlap.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"id\"\n"
            "    [\"id\", \"large_field\", \"origin_id\", \"unique_field\"]\n"
            "    [\"id\", \"large_field\", \"origin_id\"] [\"unique_field\"]\n"
            "    [[\"unique_field\"]]\n"
            "    (implementation_collectFieldSelection false false \"id\"\n"
            "      [\"id\", \"large_field\", \"origin_id\", \"unique_field\"]\n"
            "      [\"id\", \"large_field\", \"origin_id\"] [\"unique_field\"]\n"
            "      [[\"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-full-branch-allfields",
        "kind": "uniqueness",
        "expect": "reject",
        # The other half of the pre-repair model: on the pass-through branch,
        # return the whole row rather than what the fetch loads by default.
        # Correct on every input where the fetch had been told nothing
        # (`defaultColumns = allFields`), which is every other witness in this
        # battery, and wrong exactly where it had been.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := allFields\n"
            "  if !(guardA || guardB) then\n"
            "    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations\n"
            "  return loaded",
        ),
        "refinement": "On the pass-through branch nothing is done to the fetch "
                      "at all, so it loads exactly what it was already going to "
                      "load. Claiming the whole row instead asserts that "
                      "handing a fetch on untouched somehow re-adds the columns "
                      "it had been told to leave out. A change of this shape "
                      "predicts a column set the query never selects for every "
                      "cascade whose fetch arrives already narrowed, so it "
                      "cannot be the resolving change: the very column the "
                      "reported failure is about would be claimed as loaded "
                      "where the real query does not load it.",
        "rationale": "REJECT from the pass-through clause "
                     "`¬(guardA=false ∧ guardB=false) → "
                     "result = defaultColumns`: the rival returns `allFields`, "
                     "which coincides with `defaultColumns` only when the fetch "
                     "arrives unrestricted. Refuted at (false, true, \"id\", "
                     "{id,large_field,origin_id,unique_field}, "
                     "default={id,large_field,origin_id}, "
                     "skipped={unique_field}, [[unique_field]]) — a measured "
                     "carrier state (mapping.md §3, row 4) in which "
                     "`defaultColumns` is a strict subset of `allFields`, the "
                     "only configuration where the two binders are "
                     "distinguishable at all.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false true \"id\"\n"
            "    [\"id\", \"large_field\", \"origin_id\", \"unique_field\"]\n"
            "    [\"id\", \"large_field\", \"origin_id\"] [\"unique_field\"]\n"
            "    [[\"unique_field\"]]\n"
            "    (implementation_collectFieldSelection false true \"id\"\n"
            "      [\"id\", \"large_field\", \"origin_id\", \"unique_field\"]\n"
            "      [\"id\", \"large_field\", \"origin_id\"] [\"unique_field\"]\n"
            "      [[\"unique_field\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-referenced-unfiltered",
        "kind": "uniqueness",
        "expect": "reject",
        # A HALF-APPLICATION of the skip reduction: use the reduced request to
        # decide WHETHER there is anything to restrict to, but then load the
        # UNREDUCED referenced set. Correct whenever the skipped names and the
        # referenced names are disjoint (every witness above) and correct again
        # when the skip covers the whole referenced set (the request is empty
        # either way), so it is wrong on exactly one sub-domain: a PARTIAL
        # overlap, where the request keeps some referenced names and loses
        # others. No other rival separates the two roles of the reduction.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !(guardA || guardB) then\n"
            "    loaded := if (restrictionNames skippedNames candidateRelations).isEmpty then allFields\n"
            "      else (pkColumn :: referencedColumns candidateRelations).dedup\n"
            "  return loaded",
        ),
        "refinement": "The names the fetch has been told to leave out are dropped "
                      "from the request itself, not merely consulted to decide "
                      "whether a restriction happens at all. A change that "
                      "restricted to the full referenced set would ask the fetch "
                      "for a column it has already been told to leave out; the "
                      "real reduction drops that name, so the load is smaller "
                      "than this rival claims and a cascade driven from this "
                      "rival's column set would read a column the query does not "
                      "select. Measured: for a related model whose fetch arrives "
                      "already told to leave out one of two referenced columns, "
                      "the real restricted fetch loads {b,id} while this rival "
                      "claims {a,b,id}.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations`: `loadedColumns` restricts to "
                     "`restrictionNames skippedNames candidateRelations`, the "
                     "rival to `referencedColumns candidateRelations`. Refuted at "
                     "(false, false, \"id\", {a,b,big,id}, default={b,big,id}, "
                     "skipped={a}, [[a],[b]]) — a MEASURED carrier state "
                     "(mapping.md §3 row 11) and the only witness in the battery "
                     "where the skip set overlaps the referenced set PARTIALLY: "
                     "the clause requires {b,id} and the rival returns {a,b,id}, "
                     "a set-level difference. Its `candidateRelations` shape (two "
                     "relations with disjoint single target columns) is used by no "
                     "other witness.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"id\"\n"
            "    [\"a\", \"b\", \"big\", \"id\"] [\"b\", \"big\", \"id\"] [\"a\"]\n"
            "    [[\"a\"], [\"b\"]]\n"
            "    (implementation_collectFieldSelection false false \"id\"\n"
            "      [\"a\", \"b\", \"big\", \"id\"] [\"b\", \"big\", \"id\"] [\"a\"]\n"
            "      [[\"a\"], [\"b\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-pk-when-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        # The identifying column is retained UNCONDITIONALLY — including when the
        # fetch had been told to leave that very column out. This rival keeps the
        # retention in general and drops it exactly there, so it agrees with the
        # frozen impl on every input `weak-drop-pk` probes and is wrong only on
        # the sub-domain where the identifying column is itself skipped. That
        # sub-domain is where the two legs of the restriction interact: the skip
        # reduction applies to the REQUEST, while the retention is applied
        # afterwards by the fetch itself, so a skipped identifying column comes
        # back regardless.
        "module": _swap(
            _BASE,
            _IMPL_OLD,
            "  let mut loaded := defaultColumns\n"
            "  if !(guardA || guardB) then\n"
            "    let named := restrictionNames skippedNames candidateRelations\n"
            "    loaded := if named.isEmpty then allFields\n"
            "      else if skippedNames.contains pkColumn then named.dedup\n"
            "      else (pkColumn :: named).dedup\n"
            "  return loaded",
        ),
        "refinement": "Being told to leave the identifying column out does not "
                      "survive a restriction: the restriction REPLACES what the "
                      "fetch had been told, and a restricted fetch always carries "
                      "the identifying column. A change that honoured the earlier "
                      "instruction here would return rows that cannot be "
                      "identified, and the cascade continues from exactly those "
                      "rows. Measured on the real carrier: with the fetch already "
                      "told to leave out the identifying column and two relations "
                      "referencing two other columns, the real restricted fetch "
                      "loads {a,b,id} — the identifying column included — while "
                      "this rival claims {a,b}.",
        "rationale": "REJECT from the restricted-branch clause "
                     "`(guardA=false ∧ guardB=false) → "
                     "result = loadedColumns pkColumn allFields skippedNames "
                     "candidateRelations`: `loadedColumns` conses `pkColumn` on "
                     "whenever the request is non-empty, with no exception for a "
                     "skipped `pkColumn`. Refuted at (false, false, \"id\", "
                     "{a,b,big,id}, default={a,b,big,id}, skipped={id}, "
                     "[[a],[b]]) — a MEASURED carrier state (mapping.md §3 row "
                     "12) and the only witness in the battery whose "
                     "`skippedNames` contains `pkColumn`: the clause requires "
                     "{a,b,id} and the rival returns {a,b}. Complements "
                     "weak-drop-pk, which drops the identifying column "
                     "unconditionally and is refuted where nothing is skipped at "
                     "all.",
        "witness": (
            "example : ¬ problem_spec_collectFieldSelection false false \"id\"\n"
            "    [\"a\", \"b\", \"big\", \"id\"] [\"a\", \"b\", \"big\", \"id\"] [\"id\"]\n"
            "    [[\"a\"], [\"b\"]]\n"
            "    (implementation_collectFieldSelection false false \"id\"\n"
            "      [\"a\", \"b\", \"big\", \"id\"] [\"a\", \"b\", \"big\", \"id\"] [\"id\"]\n"
            "      [[\"a\"], [\"b\"]]) := by\n"
            "  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection\n"
            "  decide\n"
        ),
    },
]

# The nagini axiom lane is empty (AXIOM_TESTS == []); nothing to port, and the
# axiom lane is G-AX's job regardless.
AXIOM_TESTS = []
