# P2 adversarial audit — django__django-12708

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,13 +63,12 @@
     Except Nat String := Id.run do
   let mut names : List String := []
   for c in constraints do
-    if isDropCandidate cols c then
+    if (c.columns == cols) && c.isIndex && (!c.excluded) then
       names := names ++ [c.name]
   if names.length != 1 then
     return Except.error names.length
   return Except.ok names.head!
 -- impl-end
-
 
 -- proof-start
 theorem correct_dropComposedIndex :
@@ -123,5 +122,4 @@
     show (if (ns.length != 1) = true then _ else _) = _
     rw [hb]
     rfl
-
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,13 +63,12 @@
     Except Nat String := Id.run do
   let mut names : List String := []
   for c in constraints do
-    if isDropCandidate cols c then
+    if (c.columns == cols) && c.isIndex && (!c.isUnique) then
       names := names ++ [c.name]
   if names.length != 1 then
     return Except.error names.length
   return Except.ok names.head!
 -- impl-end
-
 
 -- proof-start
 theorem correct_dropComposedIndex :
@@ -123,5 +122,4 @@
     show (if (ns.length != 1) = true then _ else _) = _
     rw [hb]
     rfl
-
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,11 +65,10 @@
   for c in constraints do
     if isDropCandidate cols c then
       names := names ++ [c.name]
-  if names.length != 1 then
+  if names.length > 1 then
     return Except.error names.length
   return Except.ok names.head!
 -- impl-end
-
 
 -- proof-start
 theorem correct_dropComposedIndex :
@@ -123,5 +122,4 @@
     show (if (ns.length != 1) = true then _ else _) = _
     rw [hb]
     rfl
-
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,16 +60,9 @@
 -- impl-start
 def implementation_dropComposedIndex
     (constraints : List DbConstraint) (cols : List String) :
-    Except Nat String := Id.run do
-  let mut names : List String := []
-  for c in constraints do
-    if isDropCandidate cols c then
-      names := names ++ [c.name]
-  if names.length != 1 then
-    return Except.error names.length
-  return Except.ok names.head!
+    Except Nat String :=
+  Except.error 0
 -- impl-end
-
 
 -- proof-start
 theorem correct_dropComposedIndex :
@@ -123,5 +116,4 @@
     show (if (ns.length != 1) = true then _ else _) = _
     rw [hb]
     rfl
-
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,10 +66,9 @@
     if isDropCandidate cols c then
       names := names ++ [c.name]
   if names.length != 1 then
-    return Except.error names.length
+    return Except.error 0
   return Except.ok names.head!
 -- impl-end
-
 
 -- proof-start
 theorem correct_dropComposedIndex :
@@ -123,5 +122,4 @@
     show (if (ns.length != 1) = true then _ else _) = _
     rw [hb]
     rfl
-
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,13 +63,12 @@
     Except Nat String := Id.run do
   let mut names : List String := []
   for c in constraints do
-    if isDropCandidate cols c then
+    if (c.columns == cols) && c.isIndex && c.isUnique && (!c.excluded) then
       names := names ++ [c.name]
   if names.length != 1 then
     return Except.error names.length
   return Except.ok names.head!
 -- impl-end
-
 
 -- proof-start
 theorem correct_dropComposedIndex :
@@ -123,5 +122,4 @@
     show (if (ns.length != 1) = true then _ else _) = _
     rw [hb]
     rfl
-
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The selection of the
-- database constraint to drop is a total filter over the table's introspected
-- constraints (each carrying its name, the columns it covers, and its
-- index/unique flags) followed by an exactly-one count check; it is modeled
-- concretely below (R/I in refinement.md). The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An introspected table constraint, projected onto the components the deletion
selection inspects: its `name`, the ordered list of `columns` it covers, whether
it backs an `index`, whether it backs a `unique` constraint, and whether it is
`excluded` from selection because it is declared via the model's explicit
constraint/index meta options. -/
structure DbConstraint where
  name : String
  columns : List String
  isIndex : Bool
  isUnique : Bool
  excluded : Bool
  deriving Repr, DecidableEq

/-- Whether a constraint is a candidate for deletion when removing the
composed-index entry over the columns `cols`: it covers exactly `cols`, it backs
an ordinary (non-unique) index, it does NOT back a unique constraint, and it is
not excluded by the model's explicit meta options. (Pinning the non-unique
requirement is what keeps a unique constraint over the same columns out of the
candidate set.) -/
def isDropCandidate (cols : List String) (c : DbConstraint) : Bool :=
  (c.columns == cols) && c.isIndex && (!c.isUnique) && (!c.excluded)

/-- The names of all candidate constraints to drop, in table order. -/
def dropCandidateNames (constraints : List DbConstraint) (cols : List String) :
    List String :=
  (constraints.filter (isDropCandidate cols)).map (·.name)
-- pure-end

-- post-conditions-start
/-- Removing the composed index over the columns `cols` selects, among the
table's introspected `constraints`, every constraint that covers exactly `cols`,
backs an ordinary index, is not itself a unique constraint, and is not excluded
by the model's explicit meta options. Exactly one such constraint must exist:
when it does, the result names that single constraint to delete; otherwise the
result reports the number of matching constraints found (the count that makes the
operation refuse to proceed). Both branches are pinned to the input selection, so
no result can omit the non-unique requirement, target an unrelated constraint, or
fabricate a count. -/
def problem_spec_dropComposedIndex
    (constraints : List DbConstraint) (cols : List String)
    (result : Except Nat String) : Prop :=
  let ns := dropCandidateNames constraints cols
  (ns.length = 1 → result = Except.ok ns.head!) ∧
  (ns.length ≠ 1 → result = Except.error ns.length)
-- post-conditions-end

-- impl-start
def implementation_dropComposedIndex
    (constraints : List DbConstraint) (cols : List String) :
    Except Nat String := Id.run do
  let mut names : List String := []
  for c in constraints do
    if isDropCandidate cols c then
      names := names ++ [c.name]
  if names.length != 1 then
    return Except.error names.length
  return Except.ok names.head!
-- impl-end


-- proof-start
theorem correct_dropComposedIndex :
    ∀ (constraints : List DbConstraint) (cols : List String),
      problem_spec_dropComposedIndex constraints cols
        (implementation_dropComposedIndex constraints cols) := by
  intro constraints cols
  simp only [problem_spec_dropComposedIndex, implementation_dropComposedIndex, Id.run]
  have key : ∀ (cs : List DbConstraint) (acc : List String),
      (forIn cs acc fun c r ↦
        if isDropCandidate cols c = true then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [c.name]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r) : Id (List String)) =
      acc ++ (cs.filter (isDropCandidate cols)).map (·.name) := by
    intro cs
    induction cs with
    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
    | cons c cs ih =>
      intro acc
      rw [List.forIn_cons, List.filter_cons]
      by_cases h : isDropCandidate cols c = true
      · simp only [h, if_true]
        show (forIn cs (acc ++ [c.name]) _ : Id _) = _
        rw [ih (acc ++ [c.name])]
        simp [List.append_assoc]
      · simp only [h, Bool.false_eq_true, if_false]
        show (forIn cs acc _ : Id _) = _
        rw [ih acc]
  have hrun : (forIn constraints [] fun c r ↦
        if isDropCandidate cols c = true then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [c.name]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r) : Id (List String)) = dropCandidateNames constraints cols := by
    rw [key constraints []]
    simp only [List.nil_append, dropCandidateNames]
  rw [hrun]
  set ns := dropCandidateNames constraints cols with hns
  constructor
  · intro hlen
    have hb : (ns.length != 1) = false := by simp [hlen]
    show (if (ns.length != 1) = true then _ else _) = _
    rw [hb]
    rfl
  · intro hlen
    have hb : (ns.length != 1) = true := by simp [hlen]
    show (if (ns.length != 1) = true then _ else _) = _
    rw [hb]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-12708 (lean). SPEC IS TOTAL & FULLY DETERMINED: spec_view collapses BOTH impl and proof regions (verified via _lean_spec_view), so attacks freely rewrite impl+proof while the imports/axioms/pure/post-conditions prefix stays byte-identical (same_spec=True confirmed for all 6 attacks + pos_control via swebench_unified.markers.same_spec, lean backend). The postcondition `(ns.length=1 → result=Except.ok ns.head!) ∧ (ns.length≠1 → result=Except.error ns.length)` with ns := (!isUnique)-filtered dropCandidateNames has antecedents that PARTITION the input domain and each consequent PINS `result` to an exact computed value — hence any behaviorally-different impl makes correct_* a FALSE proposition, unprovable without sorry/axioms by Lean soundness.

POSITIVE CONTROL: pos_control.lean (gold impl+proof) → lean_verify.sh EXIT=0; `#print axioms correct_dropComposedIndex` = [propext, Quot.sound] — clean, no sorryAx/_prop.

SIX SAME-SPEC WRONG IMPLS, each with a best-effort gold-style closing proof attempt; command `bash scripts/lean_verify.sh <atk>.lean`:
 - atk_1 PREPATCH bug (omit !isUnique) → EXIT=1. Witness [idx,uniq]/[pink,weight]: spec=ok"pony_idx", impl=error 2. (prepatch_reproduced)
 - atk_2 omit !excluded → EXIT=1. Witness [exc,idx]: spec=ok"pony_idx", impl=error 2.
 - atk_3 boundary (names.length>1 as error test) → EXIT=1. Witness []: spec=error 0, impl=ok"".
 - atk_4 ungrounded-oracle echo (always Except.error 0) → EXIT=1. Witness [idx]: spec=ok"pony_idx", impl=error 0.
 - atk_5 partial-domain (error branch reports fixed 0 not names.length) → EXIT=1. Witness [idx,idx2]: spec=error 2, impl=error 0.
 - atk_6 control-flow-effect (require isUnique, target wrong constraint) → EXIT=1. Witness [idx]: spec=ok"pony_idx", impl=error 0.

All 6 divergences machine-checked via eval_div.lean #eval (spec value, impl value) pairs. Because ALL SIX proofs FAIL to close (EXIT=1) — i.e. NO wrong impl has a closing clean-axiom proof — protocol step 2 (materialize+resolve-run a faithful patch) has no trigger; patches={} accordingly. Ran concurrently in 2 background batches of ≤4.

REFINEMENT.MD A-LEG AUDIT: rows are I(1) / R(2,4,5) / A-reference(3) — no A-consumed, no kind-3 (inexpressible) legs. Axioms region empty (matches Solution.lean, axiom_check.py is skip stub). Row-3 A-reference models the UNCHANGED _constraint_names filter deeply as isDropCandidate = columns==cols ∧ isIndex ∧ !isUnique ∧ !excluded; verdict.md G-PANEL-2 documents conjunct-by-conjunct match against real _constraint_names at base_commit 447980e7 (schema.py:1142), and the sqlite3 introspection mechanism (unique index reported with index=True ∧ unique=True) is confirmed. A-reference correspondence to the real callee holds; nothing axiomatized.

VERDICT: SOUND. ≥6 distinct same-spec wrong impls attacked (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug, exclude-drop); none closes. Spec forces extensional equality to gold in both branches — verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The selection of the
-- database constraint to drop is a total filter over the table's introspected
-- constraints (each carrying its name, the columns it covers, and its
-- index/unique flags) followed by an exactly-one count check; it is modeled
-- concretely below (R/I in refinement.md). The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An introspected table constraint, projected onto the components the deletion
selection inspects: its `name`, the ordered list of `columns` it covers, whether
it backs an `index`, whether it backs a `unique` constraint, and whether it is
`excluded` from selection because it is declared via the model's explicit
constraint/index meta options. -/
structure DbConstraint where
  name : String
  columns : List String
  isIndex : Bool
  isUnique : Bool
  excluded : Bool
  deriving Repr, DecidableEq

/-- Whether a constraint is a candidate for deletion when removing the
composed-index entry over the columns `cols`: it covers exactly `cols`, it backs
an ordinary (non-unique) index, it does NOT back a unique constraint, and it is
not excluded by the model's explicit meta options. (Pinning the non-unique
requirement is what keeps a unique constraint over the same columns out of the
candidate set.) -/
def isDropCandidate (cols : List String) (c : DbConstraint) : Bool :=
  (c.columns == cols) && c.isIndex && (!c.isUnique) && (!c.excluded)

/-- The names of all candidate constraints to drop, in table order. -/
def dropCandidateNames (constraints : List DbConstraint) (cols : List String) :
    List String :=
  (constraints.filter (isDropCandidate cols)).map (·.name)
-- pure-end

-- post-conditions-start
/-- Removing the composed index over the columns `cols` selects, among the
table's introspected `constraints`, every constraint that covers exactly `cols`,
backs an ordinary index, is not itself a unique constraint, and is not excluded
by the model's explicit meta options. Exactly one such constraint must exist:
when it does, the result names that single constraint to delete; otherwise the
result reports the number of matching constraints found (the count that makes the
operation refuse to proceed). Both branches are pinned to the input selection, so
no result can omit the non-unique requirement, target an unrelated constraint, or
fabricate a count. -/
def problem_spec_dropComposedIndex
    (constraints : List DbConstraint) (cols : List String)
    (result : Except Nat String) : Prop :=
  let ns := dropCandidateNames constraints cols
  (ns.length = 1 → result = Except.ok ns.head!) ∧
  (ns.length ≠ 1 → result = Except.error ns.length)
-- post-conditions-end

-- impl-start
def implementation_dropComposedIndex
    (constraints : List DbConstraint) (cols : List String) :
    Except Nat String := Id.run do
  let mut names : List String := []
  for c in constraints do
    if isDropCandidate cols c then
      names := names ++ [c.name]
  if names.length != 1 then
    return Except.error names.length
  return Except.ok names.head!
-- impl-end


-- proof-start
theorem correct_dropComposedIndex :
    ∀ (constraints : List DbConstraint) (cols : List String),
      problem_spec_dropComposedIndex constraints cols
        (implementation_dropComposedIndex constraints cols) := by
  intro constraints cols
  simp only [problem_spec_dropComposedIndex, implementation_dropComposedIndex, Id.run]
  have key : ∀ (cs : List DbConstraint) (acc : List String),
      (forIn cs acc fun c r ↦
        if isDropCandidate cols c = true then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [c.name]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r) : Id (List String)) =
      acc ++ (cs.filter (isDropCandidate cols)).map (·.name) := by
    intro cs
    induction cs with
    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
    | cons c cs ih =>
      intro acc
      rw [List.forIn_cons, List.filter_cons]
      by_cases h : isDropCandidate cols c = true
      · simp only [h, if_true]
        show (forIn cs (acc ++ [c.name]) _ : Id _) = _
        rw [ih (acc ++ [c.name])]
        simp [List.append_assoc]
      · simp only [h, Bool.false_eq_true, if_false]
        show (forIn cs acc _ : Id _) = _
        rw [ih acc]
  have hrun : (forIn constraints [] fun c r ↦
        if isDropCandidate cols c = true then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [c.name]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r) : Id (List String)) = dropCandidateNames constraints cols := by
    rw [key constraints []]
    simp only [List.nil_append, dropCandidateNames]
  rw [hrun]
  set ns := dropCandidateNames constraints cols with hns
  constructor
  · intro hlen
    have hb : (ns.length != 1) = false := by simp [hlen]
    show (if (ns.length != 1) = true then _ else _) = _
    rw [hb]
    rfl
  · intro hlen
    have hb : (ns.length != 1) = true := by simp [hlen]
    show (if (ns.length != 1) = true then _ else _) = _
    rw [hb]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-12708 (lean). SPEC IS TOTAL & FULLY DETERMINED: spec_view collapses BOTH impl and proof regions (verified via _lean_spec_view), so attacks freely rewrite impl+proof while the imports/axioms/pure/post-conditions prefix stays byte-identical (same_spec=True confirmed for all 6 attacks + pos_control via swebench_unified.markers.same_spec, lean backend). The postcondition `(ns.length=1 → result=Except.ok ns.head!) ∧ (ns.length≠1 → result=Except.error ns.length)` with ns := (!isUnique)-filtered dropCandidateNames has antecedents that PARTITION the input domain and each consequent PINS `result` to an exact computed value — hence any behaviorally-different impl makes correct_* a FALSE proposition, unprovable without sorry/axioms by Lean soundness.

POSITIVE CONTROL: pos_control.lean (gold impl+proof) → lean_verify.sh EXIT=0; `#print axioms correct_dropComposedIndex` = [propext, Quot.sound] — clean, no sorryAx/_prop.

SIX SAME-SPEC WRONG IMPLS, each with a best-effort gold-style closing proof attempt; command `bash scripts/lean_verify.sh <atk>.lean`:
 - atk_1 PREPATCH bug (omit !isUnique) → EXIT=1. Witness [idx,uniq]/[pink,weight]: spec=ok"pony_idx", impl=error 2. (prepatch_reproduced)
 - atk_2 omit !excluded → EXIT=1. Witness [exc,idx]: spec=ok"pony_idx", impl=error 2.
 - atk_3 boundary (names.length>1 as error test) → EXIT=1. Witness []: spec=error 0, impl=ok"".
 - atk_4 ungrounded-oracle echo (always Except.error 0) → EXIT=1. Witness [idx]: spec=ok"pony_idx", impl=error 0.
 - atk_5 partial-domain (error branch reports fixed 0 not names.length) → EXIT=1. Witness [idx,idx2]: spec=error 2, impl=error 0.
 - atk_6 control-flow-effect (require isUnique, target wrong constraint) → EXIT=1. Witness [idx]: spec=ok"pony_idx", impl=error 0.

All 6 divergences machine-checked via eval_div.lean #eval (spec value, impl value) pairs. Because ALL SIX proofs FAIL to close (EXIT=1) — i.e. NO wrong impl has a closing clean-axiom proof — protocol step 2 (materialize+resolve-run a faithful patch) has no trigger; patches={} accordingly. Ran concurrently in 2 background batches of ≤4.

REFINEMENT.MD A-LEG AUDIT: rows are I(1) / R(2,4,5) / A-reference(3) — no A-consumed, no kind-3 (inexpressible) legs. Axioms region empty (matches Solution.lean, axiom_check.py is skip stub). Row-3 A-reference models the UNCHANGED _constraint_names filter deeply as isDropCandidate = columns==cols ∧ isIndex ∧ !isUnique ∧ !excluded; verdict.md G-PANEL-2 documents conjunct-by-conjunct match against real _constraint_names at base_commit 447980e7 (schema.py:1142), and the sqlite3 introspection mechanism (unique index reported with index=True ∧ unique=True) is confirmed. A-reference correspondence to the real callee holds; nothing axiomatized.

VERDICT: SOUND. ≥6 distinct same-spec wrong impls attacked (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug, exclude-drop); none closes. Spec forces extensional equality to gold in both branches — verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verified for django__django-12708 lean bundle (modeled fn: _delete_composed_index index-removal selection, post-patch kwargs {'index':True,'unique':False}).

### Checks
1. Lean compiles via scripts/lean_verify.sh (exit 0); `#print axioms correct_dropComposedIndex` -> [propext, Quot.sound] only, NO sorryAx — real proof, not fake.
2. same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — spec region (axioms/pure/post-conditions) is byte-identical between patched and prepatch; the only difference is the impl/proof `(!c.isUnique)` conjunct (the patch discriminator). Spec view hash stable.
3. Extracted the REAL base-commit callee at 447980e7: _constraint_names (schema.py:1142-1170) and _delete_composed_index worktree. Hand-transcribed faithfully including EVERY keyword arm — primary_key/check/foreign_key/type_ are all None at this call site (identity filters, correctly not modeled per SPEC_GUIDE §2), only unique=False & index=True active — plus the exclude set (meta_constraint_names|meta_index_names, modeled as `excluded`).
4. Independent differential test (my own port, seed 999, 300,000 random cases) feeding the model only the projected fields while feeding the real port the FULL infodict with extra random primary_key/check/foreign_key/type keys: 0 divergences. Includes F2P scenario (unique+index over same columns). Bundled conformance_check.py (120k, seed 12708) also passes 0 disagreements.

The spec pins both branches exactly: len(candidates)==1 -> Except.ok head! (the single dropped name) matches real constraint_names[0] delete; len!=1 -> Except.error len matches ValueError(len) refusal. Selection order irrelevant (only single element / count observable). No input where the modeled function disagrees with the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view confirmed via swebench_unified.markers: same_spec(Solution, Solution_prepatch)=True and spec region byte-identical (impl/proof elided). Spec view = imports + empty axioms + pure defs (DbConstraint, isDropCandidate, dropCandidateNames) + postcondition problem_spec_dropComposedIndex. The gold edit is {'index': True} -> {'index': True, 'unique': False} in _delete_composed_index, i.e. exclude unique constraints from the deletion candidate set; the spec's discriminating feature is the (!c.isUnique) conjunct in isDropCandidate. The PUBLIC problem_statement already discloses this target behavior verbatim: it says the migration crashes deleting index_together when a unique_together exists on the same fields, that _delete_composed_index raises 'Found wrong number (2) of constraints' because it finds BOTH 'the _uniq and the _idx one', and that deleting index_together should be possible alone. The spec's (!isUnique) filter is a direct semantic restatement of that publicly-described bug/fix, not a disclosure beyond problem_statement. Lexical tokens (unique/index) in the spec are already present in the problem_statement (unique_together/index_together, _uniq/_idx). The Python-specific edit identifiers (_delete_composed_index, alter_index_together, the {'index':True,'unique':False} kwargs) appear only in refinement.md/mapping.md, which are NOT part of the spec view. The docstring comments restate the public scenario abstractly, not the concrete edit. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
