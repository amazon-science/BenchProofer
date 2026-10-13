# P2 adversarial audit — django__django-14122

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,11 +107,10 @@
       continue
     for col in entry.2 do
       expressions := expressions ++ [col]
-  if !metaOrdering then
-    for entry in orderBy do
-      if !entry.1 then
-        for col in entry.2 do
-          expressions := expressions ++ [col]
+  for entry in orderBy do
+    if !entry.1 then
+      for col in entry.2 do
+        expressions := expressions ++ [col]
   for col in having do
     expressions := expressions ++ [col]
   return expressions
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,8 +103,6 @@
       for c in cols do
         expressions := expressions ++ [c]
   for entry in select do
-    if entry.1 then
-      continue
     for col in entry.2 do
       expressions := expressions ++ [col]
   if !metaOrdering then
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,13 +107,13 @@
       continue
     for col in entry.2 do
       expressions := expressions ++ [col]
+  for col in having do
+    expressions := expressions ++ [col]
   if !metaOrdering then
     for entry in orderBy do
       if !entry.1 then
         for col in entry.2 do
           expressions := expressions ++ [col]
-  for col in having do
-    expressions := expressions ++ [col]
   return expressions
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
       expressions := expressions ++ [col]
   if !metaOrdering then
     for entry in orderBy do
-      if !entry.1 then
+      if entry.1 then
         for col in entry.2 do
           expressions := expressions ++ [col]
   for col in having do
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
   let mut expressions : List Col := []
   match gb with
   | GroupBy.isNone => return []
-  | GroupBy.allFields => pure ()
+  | GroupBy.allFields => return []
   | GroupBy.explicit cols =>
       for c in cols do
         expressions := expressions ++ [c]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,27 +94,8 @@
 def implementation_getGroupBy
     (metaOrdering : Bool) (gb : GroupBy)
     (select orderBy : List (Bool × List Col)) (having : List Col) :
-    List Col := Id.run do
-  let mut expressions : List Col := []
-  match gb with
-  | GroupBy.isNone => return []
-  | GroupBy.allFields => pure ()
-  | GroupBy.explicit cols =>
-      for c in cols do
-        expressions := expressions ++ [c]
-  for entry in select do
-    if entry.1 then
-      continue
-    for col in entry.2 do
-      expressions := expressions ++ [col]
-  if !metaOrdering then
-    for entry in orderBy do
-      if !entry.1 then
-        for col in entry.2 do
-          expressions := expressions ++ [col]
-  for col in having do
-    expressions := expressions ++ [col]
-  return expressions
+    List Col :=
+  groupByExpressions metaOrdering gb select orderBy having
 -- impl-end
 
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,8 +100,7 @@
   | GroupBy.isNone => return []
   | GroupBy.allFields => pure ()
   | GroupBy.explicit cols =>
-      for c in cols do
-        expressions := expressions ++ [c]
+      pure ()
   for entry in select do
     if entry.1 then
       continue
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the list of grouping columns for an aggregate query.

When a query aggregates, the database must be told which columns to group rows
by. That grouping list is built up in phases from several sources: an explicit
caller-supplied grouping set, the columns of the selected expressions, the
columns implied by the ordering, and the columns of the post-aggregation filter.
The columns are accumulated in order; a later de-duplication pass (not modeled
here) removes repeats.

The ordering of a query may be supplied explicitly by the caller, or it may be
the model's own implicit default ordering. Only an *explicitly requested*
ordering should contribute its columns to the grouping; an ordering that is
merely the model's implicit default must NOT widen the grouping, since doing so
silently changes which rows are aggregated together. When the grouping source is
"no grouping at all", the result is empty regardless of the other phases.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The columns
-- each selected, ordering, or filter expression contributes to the grouping
-- enter as plain data (the `List Col` carried by each entry), as does the
-- per-entry "already covered by reference" / "references the selected columns"
-- decision (the `Bool` of each entry). The accumulation and gating logic that
-- uses them is modeled directly from this data rather than via a callee
-- contract, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The identity of a single grouping column expression. -/
abbrev Col := Nat

/-- The grouping source: either no grouping at all, "group by all of the
selected fields" (no explicit column list to seed the accumulation), or an
explicit caller-supplied list of grouping columns. -/
inductive GroupBy where
  | isNone
  | allFields
  | explicit (cols : List Col)
deriving DecidableEq, Repr

/-- The columns seeded by an explicit caller-supplied grouping set (empty unless
the grouping source is such a list). -/
def explicitCols (gb : GroupBy) : List Col :=
  match gb with
  | GroupBy.explicit cols => cols
  | _ => []

/-- The columns contributed by the selected expressions: each `select` entry
carries `(coveredByReference, cols)`; an entry already covered by a reference
contributes nothing, otherwise it contributes its columns, in order. -/
def selectCols (select : List (Bool × List Col)) : List Col :=
  (select.filter (fun e => !e.1)).flatMap (fun e => e.2)

/-- The columns contributed by the ordering expressions: each `orderBy` entry
carries `(referencesSelected, cols)`; an entry that merely references the
selected columns contributes nothing (those columns are already grouped),
otherwise it contributes its columns, in order. -/
def orderByCols (orderBy : List (Bool × List Col)) : List Col :=
  (orderBy.filter (fun e => !e.1)).flatMap (fun e => e.2)

/-- The fully-accumulated grouping column list (before the unmodeled
de-duplication pass). With no grouping source the list is empty. Otherwise it is
the explicit seed, then the selected-expression columns, then — only when the
ordering was explicitly requested rather than the model's implicit default — the
ordering columns, then the filter columns. -/
def groupByExpressions (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col) : List Col :=
  match gb with
  | GroupBy.isNone => []
  | _ =>
    explicitCols gb ++ selectCols select
      ++ (if metaOrdering then [] else orderByCols orderBy)
      ++ having
-- pure-end

-- post-conditions-start
/-- The accumulated grouping columns are fully pinned to the inputs: empty when
there is no grouping source; otherwise the explicit grouping seed followed by the
selected-expression columns, then the ordering columns ONLY when the ordering is
an explicit request (`metaOrdering = false`) — an implicit default ordering
contributes nothing — then the filter columns, all in order. -/
def problem_spec_getGroupBy
    (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col)
    (result : List Col) : Prop :=
  result = groupByExpressions metaOrdering gb select orderBy having
-- post-conditions-end

-- impl-start
def implementation_getGroupBy
    (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col) :
    List Col := Id.run do
  let mut expressions : List Col := []
  match gb with
  | GroupBy.isNone => return []
  | GroupBy.allFields => pure ()
  | GroupBy.explicit cols =>
      for c in cols do
        expressions := expressions ++ [c]
  for entry in select do
    if entry.1 then
      continue
    for col in entry.2 do
      expressions := expressions ++ [col]
  if !metaOrdering then
    for entry in orderBy do
      if !entry.1 then
        for col in entry.2 do
          expressions := expressions ++ [col]
  for col in having do
    expressions := expressions ++ [col]
  return expressions
-- impl-end


-- proof-start
theorem forInAppendSingletons_lemma (l : List Col) (acc : List Col) :
    (forIn (m := Id) l acc (fun x s => pure (ForInStep.yield (s ++ [x])))).run
      = acc ++ l := by
  induction l generalizing acc with
  | nil => simp
  | cons x xs ih =>
    simp only [List.forIn_cons]
    have h := ih (acc ++ [x])
    simp only [Id.run, bind, pure] at h ⊢
    rw [h]; simp

theorem forInFilterFlatMap_lemma (es : List (Bool × List Col)) (acc : List Col) :
    (forIn (m := Id) es acc (fun entry s =>
        if entry.1 then pure (ForInStep.yield s)
        else pure (ForInStep.yield
          ((forIn (m := Id) entry.2 s
            (fun c t => pure (ForInStep.yield (t ++ [c])))).run)))).run
      = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
  induction es generalizing acc with
  | nil => simp
  | cons e rest ih =>
    rcases e with ⟨b, cols⟩
    have hcols := forInAppendSingletons_lemma cols acc
    simp only [bind, pure, Id.run, ForInStep.yield] at hcols
    cases b <;>
      simp only [List.forIn_cons, List.filter_cons, Bool.not_true, Bool.not_false,
        reduceIte, bind, pure, Id.run, ForInStep.yield] at ih ⊢ <;>
      simp [ih, hcols, List.flatMap_cons, List.append_assoc]

theorem correct_getGroupBy_isNone (metaOrdering : Bool)
    (select orderBy : List (Bool × List Col)) (having : List Col) :
    implementation_getGroupBy metaOrdering GroupBy.isNone select orderBy having
      = groupByExpressions metaOrdering GroupBy.isNone select orderBy having := by
  rfl

theorem correct_getGroupBy_nonNone (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col)
    (h : gb ≠ GroupBy.isNone) :
    implementation_getGroupBy metaOrdering gb select orderBy having
      = explicitCols gb ++ selectCols select
        ++ (if metaOrdering then [] else orderByCols orderBy) ++ having := by
  have hs : ∀ (l acc : List Col),
      forIn (m := Id) l acc (fun x r => ForInStep.yield (r ++ [x])) = acc ++ l := by
    intro l acc
    rw [List.forIn_yield_eq_foldl]
    induction l generalizing acc with
    | nil => simp
    | cons x xs ih => simp [ih, List.append_assoc]
  have hsel : ∀ (es : List (Bool × List Col)) (acc : List Col),
      forIn (m := Id) es acc (fun entry r =>
          if entry.1 = true then ForInStep.yield r
          else ForInStep.yield (r ++ entry.2))
        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
    intro es; induction es with
    | nil => intro acc; simp; rfl
    | cons e rest ih =>
        intro acc
        rw [List.forIn_cons]
        by_cases he : e.1 = true
        · simp only [he, if_true]
          show forIn (m := Id) rest acc _ = _
          rw [ih]; simp [List.filter, he]
        · simp only [he, if_false]
          show forIn (m := Id) rest (acc ++ e.2) _ = _
          rw [ih]; simp [List.filter, he, List.append_assoc]
  have hord : ∀ (es : List (Bool × List Col)) (acc : List Col),
      forIn (m := Id) es acc (fun entry r =>
          if (!entry.1) = true then ForInStep.yield (r ++ entry.2)
          else ForInStep.yield r)
        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
    intro es; induction es with
    | nil => intro acc; simp; rfl
    | cons e rest ih =>
        intro acc
        rw [List.forIn_cons]
        cases he : e.1
        · simp only [he, Bool.not_false, if_true]
          show forIn (m := Id) rest (acc ++ e.2) _ = _
          rw [ih]; simp [List.filter, he, List.append_assoc]
        · simp only [he, Bool.not_true, Bool.false_eq_true, if_false]
          show forIn (m := Id) rest acc _ = _
          rw [ih]; simp [List.filter, he]
  cases gb with
  | isNone => exact absurd rfl h
  | allFields =>
      simp only [implementation_getGroupBy, explicitCols, Id.run, bind, pure,
        List.nil_append, selectCols, orderByCols]
      cases metaOrdering <;>
        simp only [Bool.not_false, Bool.not_true, if_true, if_false,
          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]
  | explicit cols =>
      simp only [implementation_getGroupBy, explicitCols, Id.run, bind, pure,
        selectCols, orderByCols]
      cases metaOrdering <;>
        simp only [Bool.not_false, Bool.not_true, if_true, if_false,
          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]

theorem correct_getGroupBy :
    ∀ (metaOrdering : Bool) (gb : GroupBy)
      (select orderBy : List (Bool × List Col)) (having : List Col),
      problem_spec_getGroupBy metaOrdering gb select orderBy having
        (implementation_getGroupBy metaOrdering gb select orderBy having) := by
  intro metaOrdering gb select orderBy having
  unfold problem_spec_getGroupBy
  cases gb with
  | isNone => exact correct_getGroupBy_isNone metaOrdering select orderBy having
  | allFields =>
      rw [correct_getGroupBy_nonNone metaOrdering GroupBy.allFields select orderBy having
        (by simp)]
      simp [groupByExpressions]
  | explicit cols =>
      rw [correct_getGroupBy_nonNone metaOrdering (GroupBy.explicit cols) select orderBy having
        (by simp)]
      simp [groupByExpressions]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_getGroupBy is a FULLY-PINNED EXACT FUNCTIONAL EQUALITY: result = groupByExpressions metaOrdering gb select orderBy having. meta.json axioms=[], deep_model_references=[]. refinement.md declares every leg R/I (8 ops, all R or I, no A-consumed / no A-reference). AUDIT FOCUS PER INSTRUCTIONS: there are NO A-legs to falsify here — get_group_by_cols()/resolve_ref outputs and ref_sources/is_ref membership all enter as plain data (List Col / Bool), and the changed logic (accumulation phases + the new `if not self._meta_ordering` guard) is modeled deeply. I audited the R/I correspondence (mapping.md/refinement.md) and it holds; axiom_check.py is a legitimate skip stub since nothing is axiomatized.

SAME-SPEC: all 7 attacks + positive control return same_spec=True via swebench_unified.markers.same_spec (lean backend). Byte-identical axioms/pure/pre/post regions; only the impl region edited.

### ATTACKS (all run via scripts/lean_verify.sh <f>, ran concurrently in 2 background batches of 4):
- atk_1 control-flow-effect = THE PREPATCH BUG (drops `if !metaOrdering then` guard, ORDER BY loop unconditional): EXIT=1, errors atk_1.lean:205/211 unsolved goals. => prepatch_reproduced=true.
- atk_2 drop select ref-covered skip (removes `if entry.1 then continue`): EXIT=1 unsolved goals.
- atk_3 boundary/accumulation-order: emit having before orderBy: EXIT=1 unsolved goals.
- atk_4 invert orderBy guard (`if entry.1` instead of `!entry.1`): EXIT=1 unsolved goals.
- atk_5 partial-domain: GroupBy.allFields => return [] (wrong when select/having nonempty): EXIT=1 atk_5.lean:206 unsolved goals.
- atk_6 ungrounded-oracle echo: impl body replaced by `groupByExpressions metaOrdering gb select orderBy having`: EXIT=1 (carried gold proof `simp only [implementation_getGroupBy,...]` no longer discharges against the non-do-block body). Behaviorally gold-identical regardless.
- atk_7 drop explicit-seed accumulation (GroupBy.explicit cols => pure ()): EXIT=1 atk_7.lean:211 unsolved goals.

POSITIVE CONTROL: pos.lean (gold impl) EXIT=0. `#print axioms correct_getGroupBy` => depends on axioms: [propext, Quot.sound] — clean, standard, NO sorryAx / no custom axioms.

KEY RESULT: NO wrong impl produced a closing clean-axiom proof. Every behaviorally-divergent same-spec impl fails with GENUINE `unsolved goals` (not sorry, not axiom-cheat) because the exact-equality postcondition is unsatisfiable for any impl != groupByExpressions. Therefore there was NO verifying-but-wrong impl whose faithful patch needed to be run through run_resolve (patches={} — nothing to materialize). verify => correct holds for all attacks tried. The tight exact-equality spec + fully R/I refinement leave no room for verify⇏correct.

VERDICT: SOUND (>=5 distinct attacks + prepatch + echo run; positive control verifies with clean axioms; none breaks the spec).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the list of grouping columns for an aggregate query.

When a query aggregates, the database must be told which columns to group rows
by. That grouping list is built up in phases from several sources: an explicit
caller-supplied grouping set, the columns of the selected expressions, the
columns implied by the ordering, and the columns of the post-aggregation filter.
The columns are accumulated in order; a later de-duplication pass (not modeled
here) removes repeats.

The ordering of a query may be supplied explicitly by the caller, or it may be
the model's own implicit default ordering. Only an *explicitly requested*
ordering should contribute its columns to the grouping; an ordering that is
merely the model's implicit default must NOT widen the grouping, since doing so
silently changes which rows are aggregated together. When the grouping source is
"no grouping at all", the result is empty regardless of the other phases.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The columns
-- each selected, ordering, or filter expression contributes to the grouping
-- enter as plain data (the `List Col` carried by each entry), as does the
-- per-entry "already covered by reference" / "references the selected columns"
-- decision (the `Bool` of each entry). The accumulation and gating logic that
-- uses them is modeled directly from this data rather than via a callee
-- contract, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The identity of a single grouping column expression. -/
abbrev Col := Nat

/-- The grouping source: either no grouping at all, "group by all of the
selected fields" (no explicit column list to seed the accumulation), or an
explicit caller-supplied list of grouping columns. -/
inductive GroupBy where
  | isNone
  | allFields
  | explicit (cols : List Col)
deriving DecidableEq, Repr

/-- The columns seeded by an explicit caller-supplied grouping set (empty unless
the grouping source is such a list). -/
def explicitCols (gb : GroupBy) : List Col :=
  match gb with
  | GroupBy.explicit cols => cols
  | _ => []

/-- The columns contributed by the selected expressions: each `select` entry
carries `(coveredByReference, cols)`; an entry already covered by a reference
contributes nothing, otherwise it contributes its columns, in order. -/
def selectCols (select : List (Bool × List Col)) : List Col :=
  (select.filter (fun e => !e.1)).flatMap (fun e => e.2)

/-- The columns contributed by the ordering expressions: each `orderBy` entry
carries `(referencesSelected, cols)`; an entry that merely references the
selected columns contributes nothing (those columns are already grouped),
otherwise it contributes its columns, in order. -/
def orderByCols (orderBy : List (Bool × List Col)) : List Col :=
  (orderBy.filter (fun e => !e.1)).flatMap (fun e => e.2)

/-- The fully-accumulated grouping column list (before the unmodeled
de-duplication pass). With no grouping source the list is empty. Otherwise it is
the explicit seed, then the selected-expression columns, then — only when the
ordering was explicitly requested rather than the model's implicit default — the
ordering columns, then the filter columns. -/
def groupByExpressions (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col) : List Col :=
  match gb with
  | GroupBy.isNone => []
  | _ =>
    explicitCols gb ++ selectCols select
      ++ (if metaOrdering then [] else orderByCols orderBy)
      ++ having
-- pure-end

-- post-conditions-start
/-- The accumulated grouping columns are fully pinned to the inputs: empty when
there is no grouping source; otherwise the explicit grouping seed followed by the
selected-expression columns, then the ordering columns ONLY when the ordering is
an explicit request (`metaOrdering = false`) — an implicit default ordering
contributes nothing — then the filter columns, all in order. -/
def problem_spec_getGroupBy
    (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col)
    (result : List Col) : Prop :=
  result = groupByExpressions metaOrdering gb select orderBy having
-- post-conditions-end

-- impl-start
def implementation_getGroupBy
    (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col) :
    List Col := Id.run do
  let mut expressions : List Col := []
  match gb with
  | GroupBy.isNone => return []
  | GroupBy.allFields => pure ()
  | GroupBy.explicit cols =>
      for c in cols do
        expressions := expressions ++ [c]
  for entry in select do
    if entry.1 then
      continue
    for col in entry.2 do
      expressions := expressions ++ [col]
  if !metaOrdering then
    for entry in orderBy do
      if !entry.1 then
        for col in entry.2 do
          expressions := expressions ++ [col]
  for col in having do
    expressions := expressions ++ [col]
  return expressions
-- impl-end


-- proof-start
theorem forInAppendSingletons_lemma (l : List Col) (acc : List Col) :
    (forIn (m := Id) l acc (fun x s => pure (ForInStep.yield (s ++ [x])))).run
      = acc ++ l := by
  induction l generalizing acc with
  | nil => simp
  | cons x xs ih =>
    simp only [List.forIn_cons]
    have h := ih (acc ++ [x])
    simp only [Id.run, bind, pure] at h ⊢
    rw [h]; simp

theorem forInFilterFlatMap_lemma (es : List (Bool × List Col)) (acc : List Col) :
    (forIn (m := Id) es acc (fun entry s =>
        if entry.1 then pure (ForInStep.yield s)
        else pure (ForInStep.yield
          ((forIn (m := Id) entry.2 s
            (fun c t => pure (ForInStep.yield (t ++ [c])))).run)))).run
      = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
  induction es generalizing acc with
  | nil => simp
  | cons e rest ih =>
    rcases e with ⟨b, cols⟩
    have hcols := forInAppendSingletons_lemma cols acc
    simp only [bind, pure, Id.run, ForInStep.yield] at hcols
    cases b <;>
      simp only [List.forIn_cons, List.filter_cons, Bool.not_true, Bool.not_false,
        reduceIte, bind, pure, Id.run, ForInStep.yield] at ih ⊢ <;>
      simp [ih, hcols, List.flatMap_cons, List.append_assoc]

theorem correct_getGroupBy_isNone (metaOrdering : Bool)
    (select orderBy : List (Bool × List Col)) (having : List Col) :
    implementation_getGroupBy metaOrdering GroupBy.isNone select orderBy having
      = groupByExpressions metaOrdering GroupBy.isNone select orderBy having := by
  rfl

theorem correct_getGroupBy_nonNone (metaOrdering : Bool) (gb : GroupBy)
    (select orderBy : List (Bool × List Col)) (having : List Col)
    (h : gb ≠ GroupBy.isNone) :
    implementation_getGroupBy metaOrdering gb select orderBy having
      = explicitCols gb ++ selectCols select
        ++ (if metaOrdering then [] else orderByCols orderBy) ++ having := by
  have hs : ∀ (l acc : List Col),
      forIn (m := Id) l acc (fun x r => ForInStep.yield (r ++ [x])) = acc ++ l := by
    intro l acc
    rw [List.forIn_yield_eq_foldl]
    induction l generalizing acc with
    | nil => simp
    | cons x xs ih => simp [ih, List.append_assoc]
  have hsel : ∀ (es : List (Bool × List Col)) (acc : List Col),
      forIn (m := Id) es acc (fun entry r =>
          if entry.1 = true then ForInStep.yield r
          else ForInStep.yield (r ++ entry.2))
        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
    intro es; induction es with
    | nil => intro acc; simp; rfl
    | cons e rest ih =>
        intro acc
        rw [List.forIn_cons]
        by_cases he : e.1 = true
        · simp only [he, if_true]
          show forIn (m := Id) rest acc _ = _
          rw [ih]; simp [List.filter, he]
        · simp only [he, if_false]
          show forIn (m := Id) rest (acc ++ e.2) _ = _
          rw [ih]; simp [List.filter, he, List.append_assoc]
  have hord : ∀ (es : List (Bool × List Col)) (acc : List Col),
      forIn (m := Id) es acc (fun entry r =>
          if (!entry.1) = true then ForInStep.yield (r ++ entry.2)
          else ForInStep.yield r)
        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by
    intro es; induction es with
    | nil => intro acc; simp; rfl
    | cons e rest ih =>
        intro acc
        rw [List.forIn_cons]
        cases he : e.1
        · simp only [he, Bool.not_false, if_true]
          show forIn (m := Id) rest (acc ++ e.2) _ = _
          rw [ih]; simp [List.filter, he, List.append_assoc]
        · simp only [he, Bool.not_true, Bool.false_eq_true, if_false]
          show forIn (m := Id) rest acc _ = _
          rw [ih]; simp [List.filter, he]
  cases gb with
  | isNone => exact absurd rfl h
  | allFields =>
      simp only [implementation_getGroupBy, explicitCols, Id.run, bind, pure,
        List.nil_append, selectCols, orderByCols]
      cases metaOrdering <;>
        simp only [Bool.not_false, Bool.not_true, if_true, if_false,
          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]
  | explicit cols =>
      simp only [implementation_getGroupBy, explicitCols, Id.run, bind, pure,
        selectCols, orderByCols]
      cases metaOrdering <;>
        simp only [Bool.not_false, Bool.not_true, if_true, if_false,
          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]

theorem correct_getGroupBy :
    ∀ (metaOrdering : Bool) (gb : GroupBy)
      (select orderBy : List (Bool × List Col)) (having : List Col),
      problem_spec_getGroupBy metaOrdering gb select orderBy having
        (implementation_getGroupBy metaOrdering gb select orderBy having) := by
  intro metaOrdering gb select orderBy having
  unfold problem_spec_getGroupBy
  cases gb with
  | isNone => exact correct_getGroupBy_isNone metaOrdering select orderBy having
  | allFields =>
      rw [correct_getGroupBy_nonNone metaOrdering GroupBy.allFields select orderBy having
        (by simp)]
      simp [groupByExpressions]
  | explicit cols =>
      rw [correct_getGroupBy_nonNone metaOrdering (GroupBy.explicit cols) select orderBy having
        (by simp)]
      simp [groupByExpressions]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_getGroupBy is a FULLY-PINNED EXACT FUNCTIONAL EQUALITY: result = groupByExpressions metaOrdering gb select orderBy having. meta.json axioms=[], deep_model_references=[]. refinement.md declares every leg R/I (8 ops, all R or I, no A-consumed / no A-reference). AUDIT FOCUS PER INSTRUCTIONS: there are NO A-legs to falsify here — get_group_by_cols()/resolve_ref outputs and ref_sources/is_ref membership all enter as plain data (List Col / Bool), and the changed logic (accumulation phases + the new `if not self._meta_ordering` guard) is modeled deeply. I audited the R/I correspondence (mapping.md/refinement.md) and it holds; axiom_check.py is a legitimate skip stub since nothing is axiomatized.

SAME-SPEC: all 7 attacks + positive control return same_spec=True via swebench_unified.markers.same_spec (lean backend). Byte-identical axioms/pure/pre/post regions; only the impl region edited.

### ATTACKS (all run via scripts/lean_verify.sh <f>, ran concurrently in 2 background batches of 4):
- atk_1 control-flow-effect = THE PREPATCH BUG (drops `if !metaOrdering then` guard, ORDER BY loop unconditional): EXIT=1, errors atk_1.lean:205/211 unsolved goals. => prepatch_reproduced=true.
- atk_2 drop select ref-covered skip (removes `if entry.1 then continue`): EXIT=1 unsolved goals.
- atk_3 boundary/accumulation-order: emit having before orderBy: EXIT=1 unsolved goals.
- atk_4 invert orderBy guard (`if entry.1` instead of `!entry.1`): EXIT=1 unsolved goals.
- atk_5 partial-domain: GroupBy.allFields => return [] (wrong when select/having nonempty): EXIT=1 atk_5.lean:206 unsolved goals.
- atk_6 ungrounded-oracle echo: impl body replaced by `groupByExpressions metaOrdering gb select orderBy having`: EXIT=1 (carried gold proof `simp only [implementation_getGroupBy,...]` no longer discharges against the non-do-block body). Behaviorally gold-identical regardless.
- atk_7 drop explicit-seed accumulation (GroupBy.explicit cols => pure ()): EXIT=1 atk_7.lean:211 unsolved goals.

POSITIVE CONTROL: pos.lean (gold impl) EXIT=0. `#print axioms correct_getGroupBy` => depends on axioms: [propext, Quot.sound] — clean, standard, NO sorryAx / no custom axioms.

KEY RESULT: NO wrong impl produced a closing clean-axiom proof. Every behaviorally-divergent same-spec impl fails with GENUINE `unsolved goals` (not sorry, not axiom-cheat) because the exact-equality postcondition is unsatisfiable for any impl != groupByExpressions. Therefore there was NO verifying-but-wrong impl whose faithful patch needed to be run through run_resolve (patches={} — nothing to materialize). verify => correct holds for all attacks tried. The tight exact-equality spec + fully R/I refinement leave no room for verify⇏correct.

VERDICT: SOUND (>=5 distinct attacks + prepatch + echo run; positive control verifies with clean axioms; none breaks the spec).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack (G-PANEL-2 / spec-too-strong-or-drifts) fails to break: the spec is faithful to the real callee.

### Evidence
1. Lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry/error). #print axioms correct_getGroupBy => [propext, Quot.sound] only — no sorryAx; proof is genuine.
2. Spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(A,P,LeanBackend)=True. Control: flipping the metaOrdering guard in the spec makes same_spec return False, so the check discriminates.
3. Gold patch (bc04941..2c7846d, django/db/models/sql/compiler.py) confirmed: the ONLY behavioral change to get_group_by is wrapping the ORDER BY -> expressions loop in `if not self._meta_ordering:`. All other diff hunks (get_order_by refactor, elide_empty, etc.) are outside the modeled accumulation.
4. Modeling boundary sound: spec models the PRE-collapse `expressions` list, a pure function of the observables the real method consumes (metaOrdering=bool(self._meta_ordering), gb in {None,True,list}, per-entry (covered/is_ref, get_group_by_cols()) for select/orderBy, having). Downstream collapse_group_by/dedup is byte-identical pre/post patch and an erroneously-added implicit-ordering column survives dedup, so pre-collapse is the correct comparison point and captures the fix.
5. abstraction bool(self._meta_ordering): in base compiler.py _meta_ordering is only ever None or set to a truthy Meta.ordering list (compiler.py:41,288), so the Bool abstraction loses nothing.
6. Differential conformance: oracle (faithful in-process replica of the patched control flow) vs spec/shadow agree over 120,030 G-CONF inputs (conformance_check.py status=pass), 100,012 independent faith-check inputs, and 7,750 exhaustive small-domain cases (ids{0,1}, up to 2 order terms, both meta polarities). ZERO disagreements across all. No input drives the modeled function apart from the real callee.

No diverging input exists; the spec is precisely the post-patch behavior — not too strong, not drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = wrap the ORDER BY->GROUP BY loop in `if not self._meta_ordering:` (django/db/models/sql/compiler.py) so implicit Meta.ordering fields do not widen GROUP BY. Public problem_statement already discloses the fixed behavior verbatim ('Meta.ordering fields must not be included in GROUP BY clause') and names Meta.ordering + GROUP BY + the wrong-aggregation consequence.

Mechanical screen (swebench_unified.leakage.screen) PASSES: no diff markers, no patched file path/module path, no gold-patch changed line reproduced (>=8-char normalized), and the only distinctive patched symbol `get_group_by` appears in no spec-view identifier or comment. No narration terms (bug/fix/patched/previously) in any spec-view comment.

Semantic/adversarial review: the spec-view flag is named `metaOrdering`, echoing the PUBLIC `Meta.ordering`, never the actual patched attribute `_meta_ordering`. The postcondition encodes 'ordering columns contribute only when explicitly requested, not the model's implicit default' — that is precisely the behavior the problem_statement already states publicly, not information beyond it; a correctness spec must encode desired behavior. Comments describe abstract accumulation phases without narrating bug->fix or naming the edit location/mechanism. The spec view cannot be used to reconstruct the gold edit any more precisely than the public problem_statement already allows.

Due diligence: same_spec(Solution, Solution_prepatch) = True (spec regions byte-identical). changed symbols = {get_group_by}, not present in view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
