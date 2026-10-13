"""properties.py — G-PBT falsification battery for django__django-16661 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS case is a
FULL ``Solution.lean`` variant built by region-surgery over the frozen file: a
case edits ONLY text inside the ``-- impl-start`` / ``-- impl-end`` region and
(for the reproven / ground-instance positives) inside the ``-- proof-start`` /
``-- proof-end`` region, so ``markers.same_spec`` holds by construction and the
``theorem correct_lookupAllowed`` STATEMENT stays byte-identical. Any
verify/reject outcome is therefore attributable to the postcondition, not to a
tampered spec. ``expect="verify"`` passes iff (in scope AND the file elaborates
with the obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (see Solution.lean / mapping.md):

  lookupAllowed
      (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool)
      : Bool

  A chain of components is walked left-to-right, accumulating the components that
  name a genuine relational HOP; the walk decides whether the chain resolves to a
  declarable filter. The single postcondition clause pins the result to the pure
  reference walk+decision:

      result = lookupDecision steps validLookups fkeyAllowed

  ``lookupDecision`` unfolds into four top-level sub-decisions, each pinned to
  distinct binders and attacked by some rival (and each of clause (D)'s
  conjuncts, the walk's halt, and the accumulation order attacked separately):

    (A) EARLY ALLOWANCE — when ``fkeyAllowed`` is set the chain is permitted
        outright. Pinned by ``fkeyAllowed``.
    (B) LOCAL-FILTER SHORT-CIRCUIT — a chain resolving to at most one relation
        part is permitted. Pinned by ``steps`` (via the accumulated length).
    (C) DECLARED-FILTER MATCH — otherwise the accumulated relation parts, with OR
        without the final trailing component, must match a declared allowed
        filter. Pinned by ``validLookups`` and by the trailing component.
    (D) HOP-RETENTION — which components join the relation parts: a component
        after the first is retained only when the previous field is a relation
        AND the reached value does not already collapse into the local model
        (not a parent link, not the model's synthesised key, and — when the model
        has a synthesised key — not one of the previous relation's target
        columns). This is the LOAD-BEARING decision the fix reshapes. Pinned by
        the per-component metadata carried in ``steps``.

  The pre-fix retention test collapsed a relation whenever the reached field was
  one of the previous relation's target columns; the fix replaces that coarse
  test with the three precise collapse conditions, so a relation whose own key is
  itself a relation (a foreign key used as the primary key) is correctly kept as
  a genuine hop.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds all six fact
    vectors at a fractional (read-only) permission and makes a MANDATORY rival
    WRITE to one, expecting rejection for insufficient permission. Lean is
    referentially transparent: ``steps`` / ``validLookups`` / ``fkeyAllowed``
    carry no heap permission, there is no read-only fraction to overwrite and no
    aliasing to exploit. That class has NO expressible instance here and no
    substitute is fabricated for it (see ``assessment``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED:
    ``lookupDecision`` is a total pure function of the inputs alone, fully
    unfolded from the walk fold and the membership test; the bundle declares no
    ``opaque``/``axiom`` callee, so there is no answer key to echo. Its honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN retention rivals — APPLY, load-bearing. The nagini
    pre-patch-target-fields, always-retain, drop-a-conjunct and
    never-retain-nonfirst rivals all attack clause (D) and map directly onto the
    retention guard here. Each is refuted at the component configuration where
    gold and the rival disagree. One rival is added beyond the nagini set —
    ``drop-locally-reachable-clause`` — because clause (D) here is a
    three-condition conjunction and the nagini drop-a-conjunct rival attacks only
    one of them; without it the third condition is unattacked and is
    indistinguishable from the constant ``true`` at every other rival's point.

  * NEW COVERAGE of transparent clauses the nagini carrier never separately
    exposed. The lean carrier models the WHOLE decision, not just the retention
    mask, so further rivals attack the clauses outside the retention guard:
    dropping the early allowance (A); dropping the trailing-component
    alternative of the declared filter match (C); widening the local-filter
    cut-off (B); reversing the accumulation order, which (C) observes because it
    compares chains and not sets; dropping the retention guard's
    previous-field-is-a-relation conjunct, the one conjunct every other
    retention rival holds fixed at ``true``; and making an unresolvable
    component a no-op instead of halting the walk, the only sub-decision the
    ``exists_`` binder controls. These vary the ``fkeyAllowed`` and
    ``validLookups`` binders and the ``isRelation`` / ``exists_`` component
    metadata, all of which the retention rivals hold fixed.

  * POSITIVE CONTROLS, two of them, because one is not enough here. Returning
    the reference ``lookupDecision`` verbatim closes by ``rfl``, which probes
    whether the spec pins the right VALUE but not whether it tolerates a
    different PRESENTATION of that value. The second control keeps its own
    decision structure (short-circuiting ``||`` for the early allowance, the two
    join-keys checked in the opposite order) and must still be accepted.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen fold-bridge proof is tuned to the frozen
``Id.run do`` / ``for`` / ``mut`` shape — so a rejection alone attributes nothing
to the spec. Every ``expect="reject"`` case therefore carries a Lean snippet
proving the rival CONTRADICTS the spec at one concrete, all-literal input. Each
was checked (two real builds) to ELABORATE against its rival and to FAIL against
the frozen solution, so it is a genuine discriminator, not a tautology. The
imperative ``Id.run do`` impl reduces fully under ``decide`` at a ground input,
so each witness ``unfold``s the spec predicate and closes the negated equality by
``decide``.

BINDER COVERAGE. All three input binders of the spec predicate are varied across
the reject witnesses so the battery exercises the spec's dependence on each:
  * ``steps`` — varied across the component configurations the walk reads: a
    prior-target-column component, a parent-link component, a synthesised-key
    component, a locally-reachable-column component (the third collapse
    condition's only live point), a clean continuing hop, a
    processed-but-dropped trailing component, a NON-RELATIONAL first component
    (the only point at which the guard's ``pr`` conjunct is observable), and an
    UNRESOLVABLE middle component (the only point at which the walk's halt is
    observable).
  * ``validLookups`` — held ``[]`` where the length short-circuit or a mismatch
    already refutes, and NON-empty (``[[0,1,2]]`` / ``[[0,1]]``) for the two
    rivals that attack the declared-filter match and the accumulation order,
    where its contents are load-bearing.
  * ``fkeyAllowed`` — held ``false`` for ten rivals and ``true`` for the
    early-allowance rival, the only value at which that clause is observable.

Varying a binder is only coverage if the variation MOVES the spec's verdict, so
the check that matters is per-SUB-DECISION, not the binder count. Each of the
following is live at exactly one witness point, and at every OTHER point in the
battery it is indistinguishable from a constant:

  * the third collapse condition — ``modelHasAutoField`` and
    ``partInPrevToFields`` are both true only at ``drop-locally-reachable-clause``;
    every other point leaves ``(!modelHasAutoField || !partInPrevToFields)`` TRUE,
    where dropping the condition changes nothing.
  * the guard's ``pr`` conjunct (the previous field is a relation) — every
    retention rival's first component IS a relation, so ``pr`` is fixed at
    ``true`` for all of them. ``drop-prev-relation-conjunct`` is the only point
    that moves it.
  * the local-filter cut-off VALUE — every other rival reaches clause (B) only in
    the direction that already permits, so ``≤ 1`` and ``≤ 2`` agree at their
    points. ``threshold-off-by-one`` pins the constant.
  * the walk's halt on an unresolvable component — every other point holds
    ``exists_ = true``, where the halt guard is a no-op.
    ``nonexistent-does-not-halt`` is the only point that moves it. (The
    ``hasPathInfos = false`` trailing component observes the OTHER halt path, not
    this one: it exercises a component that is processed and then ends the walk,
    which cannot separate a skip from a halt because nothing follows it.)
  * the accumulation ORDER, which clause (C) observes since it compares chains
    and not sets — ``reversed-accumulation`` is the only case that moves it; every
    other rival changes which components are retained or how the chain is
    matched, and at their points the short-circuit or the mismatch decides before
    order could.

REALIZABILITY of the witness points. The spec is total over ``PathStep``, so a
witness at any value is a valid refutation for the gate — but a rationale that
names a sub-domain is only as strong as that sub-domain's reachability, so each
point is chosen consistent with the metadata reads (mapping.md). In particular a
component that IS the model's synthesised key entails the model HAS one and is a
terminal non-relational column, and the inheritance link is a relation that
continues the walk; the ``_S1_AUTO`` / ``_S2_DROP`` configurations are set
accordingly rather than left at the helper's defaults.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
model-graph metadata is supplied as input ``PathStep`` data and the decision is
modeled directly, so there is no in-model axiom obligation for the PBT axiom lane
to re-discharge (that lane belongs to G-AX in any case). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-16661"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen region anchors (each unique inside Solution.lean; verified at load).
# ---------------------------------------------------------------------------

# The FK early-allowance branch at the top of the do-block (clause A).
_EARLY = (
    "    if fkeyAllowed then\n"
    "      return true\n"
)

# The whole retention guard block (clause D). Replaced wholesale by the
# always-retain and never-retain-nonfirst rivals.
_APPEND_BLOCK = (
    "          let appendIt : Bool :=\n"
    "            match prev with\n"
    "            | none => true\n"
    "            | some pr =>\n"
    "                pr && !step.inParents && !step.isAutoField &&\n"
    "                  (!step.modelHasAutoField || !step.partInPrevToFields)\n"
)

# The `some pr` arm of the retention guard alone (clause D, finer). Replaced by
# the pre-patch and drop-a-conjunct rivals.
_SOME_PR = (
    "            | some pr =>\n"
    "                pr && !step.inParents && !step.isAutoField &&\n"
    "                  (!step.modelHasAutoField || !step.partInPrevToFields)"
)

# The post-loop declared-filter match, checking BOTH join-keys (clause C).
_TAIL = (
    "    return (validLookups.contains relationParts) ||\n"
    "           (validLookups.contains (relationParts ++ [lastPart]))"
)

# The local-filter short-circuit threshold (clause B) — the only place the
# "at most one relation part" cut-off is written.
_THRESHOLD = (
    "    if relationParts.length ≤ 1 then\n"
    "      return true\n"
)

# The halt on a component that does not resolve to a field (clause D's guard on
# the walk continuing at all).
_EXISTS_HALT = (
    "        if !step.exists_ then\n"
    "          stopped := true\n"
)

# The accumulation of a retained component onto the relation parts, in order.
_APPEND_ACTION = (
    "          if appendIt then\n"
    "            relationParts := relationParts ++ [step.part]\n"
)

# The whole impl def block — anchor for the functional-reshape positive.
_FULL_IMPL = _BASE[
    _BASE.index("def implementation_lookupAllowed"):
    _BASE.index(_TAIL) + len(_TAIL)
]

# The whole proof-region body (between the markers) — anchor for the positive's
# re-proof and the admissibility ground instance.
_PS = "-- proof-start\n"
_PE = "-- proof-end\n"
_PROOF_BODY = _BASE[_BASE.index(_PS) + len(_PS): _BASE.index(_PE)]

# The frozen `correct_lookupAllowed` entry (unique); admissibility prepends a
# ground `have` here.
_PROOF_INTRO = (
    "  intro steps validLookups fkeyAllowed\n"
    "  unfold problem_spec_lookupAllowed\n"
    "  rw [impl_loopBridge]\n"
)

for _a, _nm in [
    (_EARLY, "_EARLY"), (_APPEND_BLOCK, "_APPEND_BLOCK"), (_SOME_PR, "_SOME_PR"),
    (_TAIL, "_TAIL"), (_FULL_IMPL, "_FULL_IMPL"), (_PROOF_BODY, "_PROOF_BODY"),
    (_PROOF_INTRO, "_PROOF_INTRO"), (_THRESHOLD, "_THRESHOLD"),
    (_EXISTS_HALT, "_EXISTS_HALT"), (_APPEND_ACTION, "_APPEND_ACTION"),
]:
    assert _BASE.count(_a) == 1, f"anchor drift: {_nm}"


# ---------------------------------------------------------------------------
# PathStep literal helper (field order matches the frozen structure).
# ---------------------------------------------------------------------------
def _ps(part, exists_=True, isRelation=True, hasPathInfos=True,
        inTargetFields=False, inParents=False, isAutoField=False,
        modelHasAutoField=False, partInPrevToFields=False):
    def b(x):
        return "true" if x else "false"
    return (
        "{ part := %d, exists_ := %s, isRelation := %s, hasPathInfos := %s, "
        "inTargetFields := %s, inParents := %s, isAutoField := %s, "
        "modelHasAutoField := %s, partInPrevToFields := %s }" % (
            part, b(exists_), b(isRelation), b(hasPathInfos), b(inTargetFields),
            b(inParents), b(isAutoField), b(modelHasAutoField),
            b(partInPrevToFields)))


# Component configurations the retention clause reads.
#
# REALIZABILITY. The spec is total over every `PathStep` value, so a witness at
# any value is a valid refutation for the gate. But a rationale that claims a
# named sub-domain is only as strong as that sub-domain's reachability in the
# real system, so each configuration below is chosen to be one the metadata can
# actually present (mapping.md gives the reads). Two constraints bind:
#   * a component that IS the model's synthesised key entails the model HAS one
#     (`isAutoField -> modelHasAutoField`), and such a column is not a relation
#     and does not continue the walk (`isRelation = hasPathInfos = false`);
#   * the link realising concrete inheritance IS a relation that continues the
#     walk, so `inParents` comes with `isRelation = hasPathInfos = true`.
_S0 = _ps(0)                                  # clean first hop (prev = none)
_S1_CLEAN = _ps(1)                            # clean continuing hop -> gold keeps
_S1_TARGET = _ps(1, inTargetFields=True)      # prior-target col: prepatch drops, gold keeps
_S1_PARENT = _ps(1, inParents=True)           # parent link -> gold drops
# The synthesised key reached as a non-relational terminal column: gold drops it.
_S1_AUTO = _ps(1, isRelation=False, hasPathInfos=False,
               isAutoField=True, modelHasAutoField=True)
# Processed but NOT appended, so it sets the trailing component to 2 while
# staying out of the relation parts: the reached model's synthesised key, a
# terminal non-relational column.
_S2_DROP = _ps(2, isRelation=False, hasPathInfos=False,
               isAutoField=True, modelHasAutoField=True)
_S2_CLEAN = _ps(2)                            # clean continuing hop (admiss)
# A component that does not resolve to a field at all: the walk must HALT here,
# so a later component is never processed. Pins the halt propagation.
_S1_MISSING = _ps(1, exists_=False)
# The THIRD collapse condition's only live point: the model has a synthesised
# key AND the component names one of the previous relation's declared target
# columns, so `(!modelHasAutoField || !partInPrevToFields)` is FALSE and gold
# drops the component. Every other configuration leaves that disjunction true,
# which is why a battery holding these two booleans false cannot separate the
# third condition from the constant `true`.
_S1_LOCALCOL = _ps(1, modelHasAutoField=True, partInPrevToFields=True)


def _steps(*items):
    return "[" + ", ".join(items) + "]"


def _witness(steps, vl, fk):
    return (
        f"example : ¬ problem_spec_lookupAllowed {steps} {vl} {fk}\n"
        f"    (implementation_lookupAllowed {steps} {vl} {fk}) := by\n"
        f"  unfold problem_spec_lookupAllowed\n"
        f"  decide\n"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally-different but CORRECT impl —
# drop the entire `Id.run do` / `let mut` / `for` scaffold and return the pure
# reference `lookupDecision` directly (GROUNDED: a total function of the inputs,
# not an opaque answer key). Observationally identical on every input, so it must
# satisfy the exact postcondition; if it cannot the spec is SPEC-TOO-STRONG. The
# frozen fold-bridge proof no longer applies to the new shape, so the obligation
# is re-proved (STATEMENT byte-identical, no new axiom/theorem/lemma): after
# unfolding both sides the goal is a syntactic identity closed by `rfl`.
# ---------------------------------------------------------------------------
_POS_IMPL = (
    "def implementation_lookupAllowed\n"
    "    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool) : Bool :=\n"
    "  lookupDecision steps validLookups fkeyAllowed"
)
_POS_PROOF = (
    "theorem correct_lookupAllowed :\n"
    "    ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),\n"
    "      problem_spec_lookupAllowed steps validLookups fkeyAllowed\n"
    "        (implementation_lookupAllowed steps validLookups fkeyAllowed) := by\n"
    "  intro steps validLookups fkeyAllowed\n"
    "  unfold problem_spec_lookupAllowed implementation_lookupAllowed\n"
    "  rfl\n"
)
_POS_CONTROL = _swap(_swap(_BASE, _FULL_IMPL, _POS_IMPL), _PROOF_BODY, _POS_PROOF)


# ---------------------------------------------------------------------------
# SECOND POSITIVE CONTROL (soundness): a correct reshape that is NOT the
# reference function restated. `pos-functional-reference` returns
# `lookupDecision` verbatim, so its proof closes by `rfl` and it cannot detect a
# spec that is too strong about the SHAPE of the decision — only one that is too
# strong about its value. This one keeps its own decision structure while
# reshaping two things the frozen spec writes in a fixed form:
#   * the early allowance becomes a short-circuiting `||` rather than an `if`;
#   * the two declared-filter join-keys are checked in the opposite order.
# Both are value-preserving (`||` is commutative on Bool and the early allowance
# dominates), so a faithful spec must accept it. If it cannot, the spec is
# SPEC-TOO-STRONG about presentation rather than behavior. Proof: unfold both
# sides, split on `fkeyAllowed`, and commute the disjunction.
# ---------------------------------------------------------------------------
_POS2_IMPL = (
    "def implementation_lookupAllowed\n"
    "    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool) : Bool :=\n"
    "  fkeyAllowed ||\n"
    "    (let st := runLoop steps\n"
    "     if st.relationParts.length ≤ 1 then true\n"
    "     else (validLookups.contains (st.relationParts ++ [st.lastPart])) ||\n"
    "          (validLookups.contains st.relationParts))"
)
_POS2_PROOF = (
    "theorem correct_lookupAllowed :\n"
    "    ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),\n"
    "      problem_spec_lookupAllowed steps validLookups fkeyAllowed\n"
    "        (implementation_lookupAllowed steps validLookups fkeyAllowed) := by\n"
    "  intro steps validLookups fkeyAllowed\n"
    "  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision\n"
    "  cases fkeyAllowed <;> simp [Bool.or_comm]\n"
)
_POS_CONTROL_2 = _swap(_swap(_BASE, _FULL_IMPL, _POS2_IMPL), _PROOF_BODY, _POS2_PROOF)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (positive control): discharge the spec predicate at the normal
# F2P-shaped ground input (a three-hop chain in which the middle relation's own
# key is itself a relation — so that component names one of the previous
# relation's target columns, yet no collapse condition applies and every
# component is a genuine hop, matching a declared allowed filter) inside the
# proof region,
# alongside the frozen obligation. The frozen theorem binds NO precondition
# hypothesis (the behavior is total), so nagini's precondition-admission probe
# has no binder to attack; the honest analogue is to confirm the obligation is
# SATISFIABLE (non-vacuous) at exactly the input the F2P exercises. Nothing is
# assumed: the STATEMENT is byte-identical, the ground instance is a `have`
# inside the existing tactic body closed by `unfold … ; decide`, and no new
# declaration/axiom/`sorry` is introduced.
# ---------------------------------------------------------------------------
# The middle component carries `inTargetFields = true`: that is what makes this
# the F2P-SHAPED input rather than a generic three-hop chain. With all three
# components "clean" the walk is insensitive to the retention reshape entirely
# (the coarse `!inTargetFields` test and the three precise collapse conditions
# agree there), so such a ground instance would confirm satisfiability at a point
# that is not the one the behavior turns on. Here the middle component IS one of
# the previous relation's target columns while none of the three collapse
# conditions applies, so it stays a genuine hop and the chain matches `[[0,1,2]]`.
_ADM_STEPS = _steps(_S0, _S1_TARGET, _S2_CLEAN)
_ADM_GROUND = (
    "  have _ground : problem_spec_lookupAllowed\n"
    f"      {_ADM_STEPS} [[0, 1, 2]] false\n"
    "      (implementation_lookupAllowed\n"
    f"        {_ADM_STEPS} [[0, 1, 2]] false) := by\n"
    "    unfold problem_spec_lookupAllowed; decide\n"
)
_ADM = _swap(_BASE, _PROOF_INTRO, _ADM_GROUND + _PROOF_INTRO)


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (each a full variant; only the impl body changes, so the
# spec and the theorem STATEMENT stay byte-identical). Each carries a witness
# SEEN to discriminate (elaborates on the rival, fails on gold).
# ---------------------------------------------------------------------------

# (D) PRE-PATCH: the coarse pre-fix retention test — a non-first relational
# component is kept iff it is NOT one of the previous relation's target columns.
_PREPATCH = _swap(_BASE, _SOME_PR,
                  "            | some pr => pr && !step.inTargetFields")
_W_PREPATCH = _witness(_steps(_S0, _S1_TARGET), "[]", "false")

# (D) ALWAYS-RETAIN: every existing component is retained (guard forced true),
# even ones the fix collapses into the local model.
_ALWAYS = _swap(_BASE, _APPEND_BLOCK,
                "          let appendIt : Bool := true\n")
_W_ALWAYS = _witness(_steps(_S0, _S1_PARENT), "[]", "false")

# (D) DROP-A-CONJUNCT: the synthesised-key collapse condition (`!isAutoField`)
# is removed from the retention guard.
_DROP_CONJ = _swap(_BASE, _SOME_PR,
                   "            | some pr =>\n"
                   "                pr && !step.inParents &&\n"
                   "                  (!step.modelHasAutoField || !step.partInPrevToFields)")
_W_DROP_CONJ = _witness(_steps(_S0, _S1_AUTO), "[]", "false")

# (D) DROP-LOCALLY-REACHABLE-CLAUSE: the THIRD collapse condition — the model
# has a synthesised key AND the component names one of the previous relation's
# declared target columns — is removed from the retention guard, leaving only the
# parent-link and synthesised-key conditions. This is the one sub-decision the
# other four retention rivals cannot reach: each of their witness points leaves
# `(!modelHasAutoField || !partInPrevToFields)` TRUE, so at those points the
# clause is indistinguishable from the constant `true` and dropping it changes
# nothing. Refuted at the only configuration where the disjunction is false.
_DROP_LOCALCOL = _swap(_BASE, _SOME_PR,
                       "            | some pr =>\n"
                       "                pr && !step.inParents && !step.isAutoField")
_W_DROP_LOCALCOL = _witness(_steps(_S0, _S1_LOCALCOL), "[]", "false")

# (D) NEVER-RETAIN-NONFIRST: only the first component is retained; every
# continuing hop is dropped.
_NEVER = _swap(_BASE, _APPEND_BLOCK,
               "          let appendIt : Bool :=\n"
               "            match prev with\n"
               "            | none => true\n"
               "            | some _ => false\n")
_W_NEVER = _witness(_steps(_S0, _S1_CLEAN), "[]", "false")

# (A) IGNORE-FKEY: the FK early-allowance branch no longer permits the chain
# (it is a no-op), so the decision is taken purely from the walk.
_IGNORE_FKEY = _swap(_BASE, _EARLY,
                     "    if fkeyAllowed then\n"
                     "      pure ()\n")
_W_IGNORE_FKEY = _witness(_steps(_S0, _S1_CLEAN), "[]", "true")

# (C) MEMBERSHIP-DROPS-TRAILING: only the accumulated relation parts are matched
# against the declared filters; the trailing-component alternative is dropped.
_DROP_TRAILING = _swap(_BASE, _TAIL,
                       "    return validLookups.contains relationParts")
_W_DROP_TRAILING = _witness(_steps(_S0, _S1_CLEAN, _S2_DROP), "[[0, 1, 2]]", "false")

# (D) DROP-PREV-RELATION-CONJUNCT: the retention guard no longer requires the
# PREVIOUS field to be a relation, so a component reached through a
# non-relational field is counted as a fresh hop. This is the one conjunct of
# clause (D) that predates the change and that every other retention rival
# holds fixed at `true` (all their first components are relations), so at their
# points `pr` is indistinguishable from the constant `true`.
_DROP_PR = _swap(_BASE, _SOME_PR,
                 "            | some _ =>\n"
                 "                !step.inParents && !step.isAutoField &&\n"
                 "                  (!step.modelHasAutoField || !step.partInPrevToFields)")
# Refuted where the previous field is NOT a relation: gold stops counting hops,
# the rival keeps counting.
_W_DROP_PR = _witness(_steps(_ps(0, isRelation=False), _S1_CLEAN), "[]", "false")

# (B) THRESHOLD-OFF-BY-ONE: the local-filter short-circuit permits a chain
# resolving to at most TWO relation parts instead of at most one, so a genuine
# two-hop chain is permitted without ever consulting the declared filters.
# Clause (B) is otherwise only ever read in the direction that HELPS the rivals
# (they reach it at length ≤ 1), so no existing case moves the cut-off itself.
_THRESH_TWO = _swap(_BASE, _THRESHOLD,
                    "    if relationParts.length ≤ 2 then\n"
                    "      return true\n")
_W_THRESH_TWO = _witness(_steps(_S0, _S1_CLEAN), "[]", "false")

# (D) NONEXISTENT-DOES-NOT-HALT: a component that does not resolve to a field no
# longer halts the walk, so later components keep being processed. No existing
# case varies `exists_` at all (every witness point holds it `true`), which
# leaves the halt propagation unpinned: at those points the guard is
# indistinguishable from a no-op.
_NO_HALT = _swap(_BASE, _EXISTS_HALT,
                 "        if !step.exists_ then\n"
                 "          pure ()\n")
# Refuted on a chain whose MIDDLE component does not resolve: gold halts with a
# single relation part (permitted), the rival walks on and accumulates a second.
_W_NO_HALT = _witness(_steps(_S0, _S1_MISSING, _S2_CLEAN), "[]", "false")

# (C/D) REVERSED-ACCUMULATION: retained components are accumulated in reverse
# order, so the relation parts are the right SET at the right length but the
# wrong chain. Every existing rival changes WHICH components are retained or how
# the result is matched; none changes the ORDER, and order is exactly what the
# declared-filter equality observes.
_REVERSED = _swap(_BASE, _APPEND_ACTION,
                  "          if appendIt then\n"
                  "            relationParts := [step.part] ++ relationParts\n")
# Refuted against a declared filter that matches gold's order and not the
# reverse: `[0,1]` is declared, gold permits, the rival computes `[1,0]`.
_W_REVERSED = _witness(_steps(_S0, _S1_CLEAN), "[[0, 1]]", "false")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-functional-reference",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` "
            "walk and returns the grounded pure reference `lookupDecision` "
            "directly. Same value on every input, so it must satisfy the "
            "postcondition `result = lookupDecision …`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Proof: after unfolding both sides the goal is a "
            "syntactic identity closed by `rfl` — no new declaration, axiom, or "
            "assumption token; the `theorem correct_lookupAllowed` STATEMENT is "
            "byte-identical (only the impl and proof regions change)."
        ),
    },

    {
        "id": "pos-shortcircuit-commuted-keys",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL_2,
        "rationale": (
            "a correct reshape that keeps its OWN decision structure instead of "
            "restating the reference: the early allowance becomes a "
            "short-circuiting `||` rather than an `if`, and the two "
            "declared-filter join-keys are checked in the opposite order. Both "
            "moves preserve the value (`||` is commutative on `Bool`, and the "
            "early allowance dominates the walk), so a faithful spec must accept "
            "it. This is the control `pos-functional-reference` cannot be: that "
            "one returns `lookupDecision` verbatim and closes by `rfl`, so it "
            "probes the spec's VALUE and not its tolerance for a different "
            "presentation of the same value. Proof: unfold both sides, split on "
            "`fkeyAllowed`, commute the disjunction — no new declaration, axiom, "
            "or assumption token; the STATEMENT is byte-identical."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal F2P-shaped ground input.
    # =====================================================================
    {
        "id": "admiss-foreign-primary-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "the obligation is discharged at the F2P-SHAPED ground input (a "
            "three-hop chain whose middle relation's own key is itself a relation "
            "— so that component IS one of the previous relation's target columns "
            "while none of the three collapse conditions applies, and all three "
            "components stay genuine hops, matching the declared filter "
            "`[[0,1,2]]` -> permitted) by `unfold … ; decide`; "
            "then the frozen obligation is closed verbatim. Verifies (else the "
            "spec is unsatisfiable at the normal input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, no new declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "prepatch-target-columns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PREPATCH,
        "witness": _W_PREPATCH,
        "refinement": (
            "this is the pre-fix retention test verbatim: keep a non-first "
            "relational component iff it is NOT one of the previous relation's "
            "target columns. On the target scenario — a relation whose own key is "
            "itself a relation — that test collapses the component that must stay "
            "a genuine hop, shortening the accumulated relation parts to a chain "
            "that is not a declared filter, so the very lookup the fix must permit "
            "is wrongly disallowed. It is exactly the pre-patch bug and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (D): at a two-component chain whose second "
            "component IS a previous-target column (`inTargetFields = true`) but "
            "none of the three collapse conditions applies, the spec keeps it "
            "(relation parts of length 2, unmatched -> not permitted) while the "
            "rival drops it (length 1 -> permitted). Refuted precisely on the "
            "prior-target sub-domain."
        ),
    },
    {
        "id": "always-retain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ALWAYS,
        "witness": _W_ALWAYS,
        "refinement": (
            "forcing the retention guard true keeps components the fix collapses "
            "into the local model — a parent link, a synthesised key, or a "
            "locally-reachable column — lengthening the accumulated relation "
            "parts. A faithful patch that retained every component would flip the "
            "declared-filter verdict on the existing lookups that depend on those "
            "components being dropped, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (D): at a two-component chain whose second "
            "component is a parent link (`inParents = true`) the spec drops it "
            "(length 1 -> permitted) while the rival keeps it (length 2, "
            "unmatched -> not permitted). Refuted on the parent-link collapse "
            "sub-domain."
        ),
    },
    {
        "id": "drop-auto-key-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_CONJ,
        "witness": _W_DROP_CONJ,
        "refinement": (
            "removing the synthesised-key collapse condition re-admits retention "
            "of the component that IS the reached model's synthesised key, which "
            "the fix explicitly collapses. A faithful patch omitting that "
            "condition lengthens the relation parts on any chain reaching a "
            "synthesised-key component and flips the declared-filter verdict on "
            "the existing lookups relying on that collapse, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (D): at a two-component chain whose second "
            "component IS the synthesised key (`isAutoField = true`, other "
            "conditions non-collapsing) the spec drops it (length 1 -> permitted) "
            "while the rival keeps it (length 2, unmatched -> not permitted). "
            "Refuted precisely on the synthesised-key sub-domain, distinct from "
            "the parent-link and prior-target points."
        ),
    },
    {
        "id": "drop-locally-reachable-clause",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_LOCALCOL,
        "witness": _W_DROP_LOCALCOL,
        "refinement": (
            "dropping the third collapse condition re-admits retention of a "
            "component whose value is already reachable from the previous "
            "relation's local column on a model that has a synthesised key — the "
            "case the reshaped retention test folds into the local model. A "
            "faithful patch omitting that condition lengthens the relation parts "
            "on exactly those chains and flips the declared-filter verdict on the "
            "existing lookups that rely on the collapse, so it does NOT resolve. "
            "Note it is ALSO not the pre-fix behavior: the coarse pre-fix test "
            "keyed on a different metadata read, so this rival is a third, "
            "distinct retention rule rather than either endpoint of the change."
        ),
        "rationale": (
            "REJECT from clause (D), third condition: at a two-component chain "
            "whose second component has `modelHasAutoField = true` AND "
            "`partInPrevToFields = true` (and is neither a parent link nor the "
            "synthesised key), the disjunction "
            "`(!modelHasAutoField || !partInPrevToFields)` is FALSE, so the spec "
            "drops the component (length 1 -> permitted) while the rival keeps it "
            "(length 2, unmatched -> not permitted). This is the ONLY "
            "configuration at which that condition is observable: the other four "
            "retention rivals' witness points all leave the disjunction true, so "
            "they hold `modelHasAutoField` and `partInPrevToFields` fixed at "
            "`false` and cannot separate this condition from the constant `true`."
        ),
    },
    {
        "id": "never-retain-nonfirst",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NEVER,
        "witness": _W_NEVER,
        "refinement": (
            "retaining only the first component drops every genuine continuing "
            "hop, shortening the relation parts so a multi-hop chain no longer "
            "matches its declared filter. A faithful patch that kept only the "
            "first component would wrongly disallow the multi-hop lookups the "
            "existing behavior permits, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (D): at a two-component chain whose second "
            "component is a clean continuing hop (no collapse) the spec keeps it "
            "(length 2, unmatched -> not permitted) while the rival drops it "
            "(length 1 -> permitted). Refuted on the clean-continuing-hop "
            "sub-domain."
        ),
    },
    {
        "id": "ignore-fkey-allowance",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _IGNORE_FKEY,
        "witness": _W_IGNORE_FKEY,
        "refinement": (
            "turning the early allowance into a no-op makes the decision ignore "
            "the raw-id-popup permission and fall through to the walk. A faithful "
            "patch that dropped that early allowance would wrongly disallow the "
            "raw-id popup lookups the existing behavior permits, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (A): at `fkeyAllowed = true` over a chain whose "
            "walk yields unmatched relation parts, the spec permits outright "
            "(`true`) while the rival returns the walk verdict (`false`). Refuted "
            "at the only value where the early allowance is observable, varying "
            "the `fkeyAllowed` binder off the other rivals' `false`."
        ),
    },
    {
        "id": "membership-drops-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_TRAILING,
        "witness": _W_DROP_TRAILING,
        "refinement": (
            "matching only the accumulated relation parts and dropping the "
            "with-trailing-component alternative disallows chains whose declared "
            "filter includes a final non-hop component (e.g. a trailing column "
            "lookup). A faithful patch checking only one of the two join-keys "
            "would wrongly disallow the trailing-component lookups the existing "
            "behavior permits, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (C): at a three-component chain whose relation "
            "parts are `[0,1]` with trailing component `2`, against "
            "`validLookups = [[0,1,2]]`, the spec permits via the "
            "relation-parts-plus-trailing key (`[0,1,2]` matches) while the rival "
            "checks only `[0,1]` (unmatched -> not permitted). Refuted with a "
            "NON-empty `validLookups` and a non-appended trailing component, "
            "varying both those off the retention rivals."
        ),
    },
    {
        "id": "drop-prev-relation-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_PR,
        "witness": _W_DROP_PR,
        "refinement": (
            "dropping the requirement that the PREVIOUS field be a relation "
            "counts a component reached through a plain non-relational field as "
            "a fresh hop. A faithful patch omitting that requirement would "
            "lengthen the relation parts on every chain that continues past a "
            "non-relational field and flip the declared-filter verdict on the "
            "existing lookups, so it does NOT resolve. It is also not either "
            "endpoint of the change: this conjunct is common to both the coarse "
            "and the precise retention test."
        ),
        "rationale": (
            "REJECT from clause (D), the previous-field-is-a-relation conjunct: "
            "at a two-component chain whose FIRST component is not a relation, "
            "the spec stops counting hops (relation parts of length 1 -> "
            "permitted) while the rival counts the second (length 2, unmatched "
            "-> not permitted). This is the only conjunct of the guard that every "
            "other retention rival holds fixed at `true` — all their witness "
            "points have a relational first component, so at those points `pr` is "
            "indistinguishable from the constant `true`. Varies `isRelation`, "
            "which no other case moves on the first component."
        ),
    },
    {
        "id": "threshold-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _THRESH_TWO,
        "witness": _W_THRESH_TWO,
        "refinement": (
            "widening the local-filter short-circuit from at most one relation "
            "part to at most two permits every two-hop chain outright, without "
            "consulting the declared filters at all. A faithful patch that "
            "widened the cut-off would permit chained relational filters nobody "
            "declared — the exact class of lookup the decision exists to "
            "restrict — so it does NOT resolve, and it is a strict weakening "
            "rather than either endpoint of the change."
        ),
        "rationale": (
            "REJECT from clause (B): at a clean two-hop chain with NO declared "
            "filters (`validLookups = []`), the spec falls through to the "
            "declared-filter match and finds none (relation parts `[0,1]`, length "
            "2 -> not permitted) while the rival short-circuits (`length ≤ 2` -> "
            "permitted). This pins the cut-off VALUE, which no other case moves: "
            "every other rival meets clause (B) only in the direction that "
            "already permits, so the threshold itself is unattacked and `≤ 1` is "
            "indistinguishable from `≤ 2` at their points."
        ),
    },
    {
        "id": "nonexistent-does-not-halt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NO_HALT,
        "witness": _W_NO_HALT,
        "refinement": (
            "a component that does not resolve to a field must end the walk; "
            "making it a no-op lets the walk continue and keep accumulating hops "
            "from metadata that was never resolved. A faithful patch that skipped "
            "instead of halting would count components past an unresolvable one "
            "and flip the declared-filter verdict on the existing lookups that "
            "rely on the chain ending there, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the walk's halt propagation: at a three-component chain "
            "whose MIDDLE component does not resolve (`exists_ = false`), the "
            "spec halts with relation parts `[0]` (length 1 -> permitted) while "
            "the rival walks on and accumulates the third (length 2, unmatched -> "
            "not permitted). This is the only case that varies `exists_` off "
            "`true`; at every other witness point the halt guard is "
            "indistinguishable from a no-op, so nothing else pins it."
        ),
    },
    {
        "id": "reversed-accumulation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REVERSED,
        "witness": _W_REVERSED,
        "refinement": (
            "accumulating retained components in reverse yields the right hops in "
            "the wrong ORDER, and the declared-filter match observes the chain, "
            "not the set. A faithful patch that built the chain backwards would "
            "fail to match every declared multi-hop filter, wrongly disallowing "
            "the lookups the existing behavior permits, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the accumulation order, which clause (C) observes: at a "
            "clean two-hop chain against the declared filter `[[0,1]]`, the spec "
            "accumulates `[0,1]` and matches (permitted) while the rival "
            "accumulates `[1,0]` and does not (not permitted). Every other rival "
            "changes WHICH components are retained, or how the accumulated chain "
            "is matched; none changes the order, so at their points a reversing "
            "impl is indistinguishable from the frozen one (their relation parts "
            "are length ≤ 2 with the short-circuit or the mismatch deciding "
            "first, never the order). Uses a NON-empty `validLookups` whose "
            "single entry matches gold's order and not the reverse."
        ),
    },
]


# ===========================================================================
# AXIOM lane — NONE. The bundle declares no callee axiom (axioms region empty,
# meta.json axioms == []); the axiom lane is G-AX's job and this gate ignores
# AXIOM_TESTS.
# ===========================================================================
AXIOM_TESTS = []
