# P2 adversarial audit — django__django-13315

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an exact functional equality that fully pins the output; no same-spec wrong impl closes its proof, so there is no faithful patch to materialize/resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     let mut queryset := base
     if applicable then
       if constraintActive then
-        queryset := queryset.filter qualifies
+        queryset := queryset.flatMap (fun c => List.replicate c.matchRows c)
     return queryset
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,12 +58,7 @@
 -- impl-start
 def implementation_applyChoiceLimit
     (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
-  Id.run do
-    let mut queryset := base
-    if applicable then
-      if constraintActive then
-        queryset := queryset.filter qualifies
-    return queryset
+  base
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     let mut queryset := base
     if applicable then
       if constraintActive then
-        queryset := queryset.filter qualifies
+        queryset := queryset.filter (fun c => c.matchRows > 1)
     return queryset
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,12 +58,7 @@
 -- impl-start
 def implementation_applyChoiceLimit
     (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
-  Id.run do
-    let mut queryset := base
-    if applicable then
-      if constraintActive then
-        queryset := queryset.filter qualifies
-    return queryset
+  if applicable || constraintActive then base.filter qualifies else base
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     let mut queryset := base
     if applicable then
       if constraintActive then
-        queryset := queryset.filter qualifies
+        queryset := queryset.filter (fun c => c.matchRows == 0)
     return queryset
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,12 +58,7 @@
 -- impl-start
 def implementation_applyChoiceLimit
     (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
-  Id.run do
-    let mut queryset := base
-    if applicable then
-      if constraintActive then
-        queryset := queryset.filter qualifies
-    return queryset
+  if applicable && constraintActive then (base.filter qualifies).reverse else base
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,12 +58,7 @@
 -- impl-start
 def implementation_applyChoiceLimit
     (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
-  Id.run do
-    let mut queryset := base
-    if applicable then
-      if constraintActive then
-        queryset := queryset.filter qualifies
-    return queryset
+  if constraintActive then base.filter qualifies else base
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Restricting the set of selectable options for a relational choice field.

A choice field is initialized from a collection of candidate objects. An optional
constraint may be supplied to narrow that collection to the candidates that
satisfy it. When the constraint reaches across a multi-valued relation, a single
candidate can satisfy it through several related rows.

We model each candidate together with the number of related rows that satisfy the
constraint for it (`matchRows`). The narrowing is governed by two gates:

  * `applicable` — whether this field exposes a candidate collection that the
    constraint can be applied to at all; and
  * `constraintActive` — whether a constraint is actually present.

When both gates hold, the candidate collection is narrowed to exactly those
candidates that satisfy the constraint, and each such candidate is offered AT
MOST ONCE — its presence depends only on whether at least one related row
satisfies the constraint, never on how many do. When either gate fails, the
candidate collection is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the narrowing is
-- modeled structurally over the per-candidate match counts the collection already
-- exposes, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A candidate object offered by the choice field, paired with the number of
related rows that satisfy the constraint for it.
* `id` — the candidate's identity;
* `matchRows` — how many related rows satisfy the constraint for this candidate
  (`0` means the candidate does not satisfy the constraint). -/
structure Candidate where
  id : Nat
  matchRows : Nat

/-- A candidate qualifies iff at least one related row satisfies the constraint. -/
def qualifies (c : Candidate) : Bool := c.matchRows != 0
-- pure-end

-- post-conditions-start
/-- When the field is applicable and a constraint is present, the result is the
incoming collection narrowed to the qualifying candidates — each kept exactly as
often as it occurs in the input, i.e. at most once for a collection with distinct
candidates, independent of its match count. Otherwise the collection is unchanged. -/
def problem_spec_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate)
    (result : List Candidate) : Prop :=
  result =
    (if applicable && constraintActive then base.filter qualifies else base)
-- post-conditions-end

-- impl-start
def implementation_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
  Id.run do
    let mut queryset := base
    if applicable then
      if constraintActive then
        queryset := queryset.filter qualifies
    return queryset
-- impl-end

-- proof-start
theorem correct_applyChoiceLimit :
    ∀ (applicable constraintActive : Bool) (base : List Candidate),
      problem_spec_applyChoiceLimit applicable constraintActive base
        (implementation_applyChoiceLimit applicable constraintActive base) := by
  intro applicable constraintActive base
  unfold problem_spec_applyChoiceLimit implementation_applyChoiceLimit
  cases applicable <;> cases constraintActive <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_applyChoiceLimit applicable constraintActive base result := result = (if applicable && constraintActive then base.filter qualifies else base), with qualifies c := c.matchRows != 0. This is a total functional equality that closes the output over the two gate booleans + per-candidate matchRows — zero degrees of freedom, no ungrounded oracle. Any impl whose correct_ proof closes is forced extensionally equal to the gold expression, hence resolves. So verify => correct here structurally.

PROTOCOL RUN. same_spec confirmed True for all 7 attacks (byte-identical axioms/pure/pre/post; only impl region edited).

Positive control (gold Solution.lean copy): `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0. `#print axioms correct_applyChoiceLimit` -> 'does not depend on any axioms' (clean).

7 DISTINCT same-spec wrong impls, each verified via lean_verify.sh (concurrent, <=4 at a time):
- atk_1 PREPATCH BUG: queryset.flatMap (fun c => List.replicate c.matchRows c) on true.true branch (join per-related-row multiplicity duplicates) -> EXIT=1 (unsolved goal, flatMap replicate != filter qualifies). Prepatch reproduced.
- atk_2 ungrounded-oracle echo / do-nothing: `base` -> EXIT=1 (base != filter qualifies on true.true).
- atk_3 boundary/off-by-one: filter (c.matchRows > 1) drops single-match candidates -> EXIT=1.
- atk_4 control-flow-effect: gate `applicable || constraintActive` instead of &&-nesting -> EXIT=1.
- atk_5 inverse oracle: filter (c.matchRows == 0) keeps non-qualifying -> EXIT=1.
- atk_6 order-effect: (base.filter qualifies).reverse -> EXIT=1 (right membership, wrong order).
- atk_7 partial-domain: ignores applicable gate, only checks constraintActive -> EXIT=1.

No attack closed with clean axioms, so per protocol step 2 the resolve step is vacuous (no verifying wrong impl exists to materialize). patches={} accordingly.

refinement.md A-leg audit: NO axioms exist (axioms-region is a comment; conf_skip=false). Every leg is R (1,2,4) or I (3,5,6,7) — no kind-3 leg. The single changed op (step 6, tagged I / deep model) maps List.filter qualifies to post-patch filter(Exists(model._base_manager.filter(complex_filter & Q(pk=OuterRef('pk'))))): a correlated EXISTS subquery yields at-most-once membership (candidate kept iff >=1 related row satisfies constraint), which is exactly qualifies c := matchRows != 0. Faithful; no opaque callee contract for the proof to consume, so no A-reference cross-check to fail. Constraint-normalization (Q(**dict), &Q(pk=OuterRef)) only affects WHICH candidates match (folded into matchRows), not multiplicity — correctly abstracted. Correspondence holds.

Verdict SOUND: >=5 (7) distinct same-spec attacks run, none produced a closing clean-axiom proof, so none could break verify=>correct; A-leg/model-patch correspondence audited and faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an exact functional equality that fully pins the output; no same-spec wrong impl closes its proof, so there is no faithful patch to materialize/resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Restricting the set of selectable options for a relational choice field.

A choice field is initialized from a collection of candidate objects. An optional
constraint may be supplied to narrow that collection to the candidates that
satisfy it. When the constraint reaches across a multi-valued relation, a single
candidate can satisfy it through several related rows.

We model each candidate together with the number of related rows that satisfy the
constraint for it (`matchRows`). The narrowing is governed by two gates:

  * `applicable` — whether this field exposes a candidate collection that the
    constraint can be applied to at all; and
  * `constraintActive` — whether a constraint is actually present.

When both gates hold, the candidate collection is narrowed to exactly those
candidates that satisfy the constraint, and each such candidate is offered AT
MOST ONCE — its presence depends only on whether at least one related row
satisfies the constraint, never on how many do. When either gate fails, the
candidate collection is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the narrowing is
-- modeled structurally over the per-candidate match counts the collection already
-- exposes, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A candidate object offered by the choice field, paired with the number of
related rows that satisfy the constraint for it.
* `id` — the candidate's identity;
* `matchRows` — how many related rows satisfy the constraint for this candidate
  (`0` means the candidate does not satisfy the constraint). -/
structure Candidate where
  id : Nat
  matchRows : Nat

/-- A candidate qualifies iff at least one related row satisfies the constraint. -/
def qualifies (c : Candidate) : Bool := c.matchRows != 0
-- pure-end

-- post-conditions-start
/-- When the field is applicable and a constraint is present, the result is the
incoming collection narrowed to the qualifying candidates — each kept exactly as
often as it occurs in the input, i.e. at most once for a collection with distinct
candidates, independent of its match count. Otherwise the collection is unchanged. -/
def problem_spec_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate)
    (result : List Candidate) : Prop :=
  result =
    (if applicable && constraintActive then base.filter qualifies else base)
-- post-conditions-end

-- impl-start
def implementation_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
  Id.run do
    let mut queryset := base
    if applicable then
      if constraintActive then
        queryset := queryset.filter qualifies
    return queryset
-- impl-end

-- proof-start
theorem correct_applyChoiceLimit :
    ∀ (applicable constraintActive : Bool) (base : List Candidate),
      problem_spec_applyChoiceLimit applicable constraintActive base
        (implementation_applyChoiceLimit applicable constraintActive base) := by
  intro applicable constraintActive base
  unfold problem_spec_applyChoiceLimit implementation_applyChoiceLimit
  cases applicable <;> cases constraintActive <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_applyChoiceLimit applicable constraintActive base result := result = (if applicable && constraintActive then base.filter qualifies else base), with qualifies c := c.matchRows != 0. This is a total functional equality that closes the output over the two gate booleans + per-candidate matchRows — zero degrees of freedom, no ungrounded oracle. Any impl whose correct_ proof closes is forced extensionally equal to the gold expression, hence resolves. So verify => correct here structurally.

PROTOCOL RUN. same_spec confirmed True for all 7 attacks (byte-identical axioms/pure/pre/post; only impl region edited).

Positive control (gold Solution.lean copy): `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0. `#print axioms correct_applyChoiceLimit` -> 'does not depend on any axioms' (clean).

7 DISTINCT same-spec wrong impls, each verified via lean_verify.sh (concurrent, <=4 at a time):
- atk_1 PREPATCH BUG: queryset.flatMap (fun c => List.replicate c.matchRows c) on true.true branch (join per-related-row multiplicity duplicates) -> EXIT=1 (unsolved goal, flatMap replicate != filter qualifies). Prepatch reproduced.
- atk_2 ungrounded-oracle echo / do-nothing: `base` -> EXIT=1 (base != filter qualifies on true.true).
- atk_3 boundary/off-by-one: filter (c.matchRows > 1) drops single-match candidates -> EXIT=1.
- atk_4 control-flow-effect: gate `applicable || constraintActive` instead of &&-nesting -> EXIT=1.
- atk_5 inverse oracle: filter (c.matchRows == 0) keeps non-qualifying -> EXIT=1.
- atk_6 order-effect: (base.filter qualifies).reverse -> EXIT=1 (right membership, wrong order).
- atk_7 partial-domain: ignores applicable gate, only checks constraintActive -> EXIT=1.

No attack closed with clean axioms, so per protocol step 2 the resolve step is vacuous (no verifying wrong impl exists to materialize). patches={} accordingly.

refinement.md A-leg audit: NO axioms exist (axioms-region is a comment; conf_skip=false). Every leg is R (1,2,4) or I (3,5,6,7) — no kind-3 leg. The single changed op (step 6, tagged I / deep model) maps List.filter qualifies to post-patch filter(Exists(model._base_manager.filter(complex_filter & Q(pk=OuterRef('pk'))))): a correlated EXISTS subquery yields at-most-once membership (candidate kept iff >=1 related row satisfies constraint), which is exactly qualifies c := matchRows != 0. Faithful; no opaque callee contract for the proof to consume, so no A-reference cross-check to fail. Constraint-normalization (Q(**dict), &Q(pk=OuterRef)) only affects WHICH candidates match (folded into matchRows), not multiplicity — correctly abstracted. Correspondence holds.

Verdict SOUND: >=5 (7) distinct same-spec attacks run, none produced a closing clean-axiom proof, so none could break verify=>correct; A-leg/model-patch correspondence audited and faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-13315 lean bundle. Modeled function = django.forms.models.apply_limit_choices_to_to_formfield (django/forms/models.py:96, base_commit target verified, both showing the POST-PATCH body: formfield.queryset.filter(Exists(model._base_manager.filter(complex_filter & Q(pk=OuterRef('pk'))))).

Spec: problem_spec_applyChoiceLimit applicable constraintActive base result := result = (if applicable && constraintActive then base.filter qualifies else base); qualifies c := c.matchRows != 0.

Technical preconditions (all PASS):
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_applyChoiceLimit -> 'does not depend on any axioms' (no sorryAx; proof genuinely closes). Reproduced in a scratch file.
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean tables) -> True: axioms/pure/post-conditions regions byte-identical. Spec frozen.
- prepatch impl (flatMap replicate) does not close (G-DIFF pass), so spec discriminates patched from buggy.

Faithfulness check against the REAL post-patch callee (each modeling boundary probed for a diverging input):
- Membership: filter(Exists(subquery)) keeps a candidate iff >=1 related row satisfies the constraint == matchRows != 0. Match.
- At-most-once: correlated EXISTS emits each base row once regardless of join multiplicity == List.filter keeps each element once. Match (this is the exact behavior the fix introduces; prepatch join multiplicity is NOT re-introduced by the modeled function).
- Ordering/identity: adding an EXISTS WHERE clause preserves queryset order; List.filter preserves input order. Match.
- applicable gate: hasattr(queryset) and hasattr(get_limit_choices_to) == applicable; nested-if == &&. Match.
- constraintActive gate: keyed to post-patch truthiness 'if limit_choices_to:' (correct target; empty dict falsy -> base unchanged, as modeled). Match.
- Both gates false -> base unchanged, matching untouched queryset. Match.
- Constraint-construction details (Q(**dict) normalization, & Q(pk=OuterRef('pk'))) affect WHICH candidates match (folded into matchRows), not membership multiplicity -> sound abstraction, not a drift.

Attempted to construct a realizable diverging input (duplicate ids in base, empty-dict constraint, pre-vs-post is-not-None truthiness, ordering permutations, matchRows>=2 multi-related-row case). None divides the modeled function from the real post-patch callee. The list-of-candidates-with-match-counts abstraction is exactly the observable the fix governs; the spec is not too strong and does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified: Lean impl+proof regions elided (impl-start/proof-start replaced with 'elided — supplied by the consumer'); same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with the lean backend LanguageTables, so the spec region is byte-identical across the gold/prepatch pair. Mechanical G-LEAK screen recorded pass ('spec view clean', no hard failures), independently re-derived.

Leakage assessment vs PUBLIC problem_statement (dataset row, NOT hints_text): problem_statement says 'limit_choices_to on a ForeignKey can render duplicate options in formfield ... If you pass a Q object as limit_choices_to on a ForeignKey field involving a join, you may end up with duplicate options.' The spec's postcondition `result = (if applicable && constraintActive then base.filter qualifies else base)` with `qualifies c := c.matchRows != 0`, and the docstring 'each such candidate is offered AT MOST ONCE ... never on how many [related rows match]', encode the CORRECT (no-duplicate) behavior. That dedup semantics is exactly the fix the public issue demands — a faithful spec must state correct behavior, and 'no duplicate options' is a direct restatement of the publicly-announced defect, not information beyond it.

The gold edit's mechanism is fully abstracted and does NOT appear: no Exists, OuterRef, _base_manager, complex_filter, Q(**limit_choices_to), pk=OuterRef('pk'), no subquery construction, no 'Use Exists() to avoid potential duplicates' comment, no diff/patch markers, no gold-patch identifiers. The changed operation is modeled deeply as a `List.filter` over an opaque per-candidate `matchRows` count; an agent reading the spec still must independently invent the filter(Exists(subquery)) implementation. The spec pins only the observable choice-set membership (at-most-once) that the bug report already announces. Conclusion: no gold-reconstruction leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
