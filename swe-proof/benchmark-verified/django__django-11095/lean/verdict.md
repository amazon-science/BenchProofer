# P2 adversarial audit — django__django-11095

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking impl found. The spec is a total exact-equality functional equation with no precondition: problem_spec_getInlineInstances hasRequest selfInlines hookInlines result := result = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest). Any impl that closes correct_ is forced extensionally equal to the gold post-patch function. Concrete divergence witnesses (all proved by `decide` in disproof.lean, exit 0): prepatch/atk_1 (iterate selfInlines): impl false [{id:=1,vc,add,del}] [] = [{1,false}] but specRHS false [] = [] — exactly the F2P override-returns-[] scenario; atk_2 (drop keepInline filter): under request keeps a no-permission class the spec removes; atk_3 (maxNumZeroed without hasRequest guard): zeroes when hasRequest=false; atk_4 (prepend): reverses output order; atk_5 (continue if !hasAdd): drops a view/delete-only class the spec keeps.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
     (hasRequest : Bool) (selfInlines hookInlines : List Inline) :
     List InlineInstance := Id.run do
   let mut inlineInstances : List InlineInstance := []
-  for inlineClass in hookInlines do
+  for inlineClass in selfInlines do
     let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
     if hasRequest then
       if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,8 +107,6 @@
   for inlineClass in hookInlines do
     let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
     if hasRequest then
-      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
-        continue
       if !inlineClass.hasAdd then
         inst := { inst with maxNumZeroed := true }
     inlineInstances := inlineInstances ++ [inst]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,7 @@
     List InlineInstance := Id.run do
   let mut inlineInstances : List InlineInstance := []
   for inlineClass in hookInlines do
-    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
+    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := !inlineClass.hasAdd }
     if hasRequest then
       if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
         continue
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,7 +111,7 @@
         continue
       if !inlineClass.hasAdd then
         inst := { inst with maxNumZeroed := true }
-    inlineInstances := inlineInstances ++ [inst]
+    inlineInstances := [inst] ++ inlineInstances
   return inlineInstances
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,7 +107,7 @@
   for inlineClass in hookInlines do
     let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
     if hasRequest then
-      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
+      if !inlineClass.hasAdd then
         continue
       if !inlineClass.hasAdd then
         inst := { inst with maxNumZeroed := true }
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,17 +102,8 @@
 -- impl-start
 def implementation_getInlineInstances
     (hasRequest : Bool) (selfInlines hookInlines : List Inline) :
-    List InlineInstance := Id.run do
-  let mut inlineInstances : List InlineInstance := []
-  for inlineClass in hookInlines do
-    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
-    if hasRequest then
-      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
-        continue
-      if !inlineClass.hasAdd then
-        inst := { inst with maxNumZeroed := true }
-    inlineInstances := inlineInstances ++ [inst]
-  return inlineInstances
+    List InlineInstance :=
+  (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
 -- impl-end
 
 -- proof-start
@@ -158,11 +149,5 @@
       problem_spec_getInlineInstances hasRequest selfInlines hookInlines
         (implementation_getInlineInstances hasRequest selfInlines hookInlines) := by
   intro hasRequest selfInlines hookInlines
-  unfold problem_spec_getInlineInstances implementation_getInlineInstances
-  -- The desugared loop body is definitionally equal to the cleaned body, so we can
-  -- `show` the goal in cleaned form and discharge it with the closed-form helper.
-  show Id.run (forIn hookInlines ([] : List InlineInstance)
-        (cleanBody_getInlineInstances hasRequest))
-      = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
-  rw [foldClean_getInlineInstances, List.nil_append]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the list of inline editors to display for an admin page, given a
particular request and the object being edited.

An admin page may attach a number of *inline* editor classes. Which classes are
attached need not be constant: the set of inline classes selected for a page
can depend on the current request and the object being edited, so the page is
given the already-selected list of inline classes for this request/object rather
than reading a static attribute.

For each selected inline class the page constructs one editor. When the call is
made on behalf of a request, an editor is shown only if the viewer is allowed to
interact with it at all — that is, the viewer may view-or-change, add, or delete
through it; an editor the viewer can do none of these with is omitted entirely.
For a shown editor whose viewer may not add new rows through it, the editor's
maximum number of new rows is forced to zero. When there is no request in
context, every selected class yields an editor with no such restriction.

The resulting list preserves the order of the selected inline classes, with the
omitted ones removed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The list of
-- selected inline classes for this request/object enters as plain data
-- (`hookInlines`), as does the static attribute it may override (`selfInlines`).
-- Each inline class carries the three permission outcomes of its editor (view-or-
-- change / add / delete) as booleans, so the per-editor decision is modeled
-- directly from data rather than via a callee contract. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- An inline editor class together with the three permission outcomes its editor
reports for the current request/object. `id` is the class's identity (which class
it is). -/
structure Inline where
  id : Nat
  hasViewOrChange : Bool
  hasAdd : Bool
  hasDelete : Bool
deriving DecidableEq, Repr

/-- A constructed inline editor instance: the class it was built from (`id`) and
whether its maximum number of new rows was forced to zero. -/
structure InlineInstance where
  id : Nat
  maxNumZeroed : Bool
deriving DecidableEq, Repr

/-- Whether an inline class survives the per-request filtering: with no request in
context every class is kept; under a request a class is kept exactly when the
viewer may view-or-change, add, or delete through its editor. -/
def keepInline (hasRequest : Bool) (i : Inline) : Bool :=
  !hasRequest || i.hasViewOrChange || i.hasAdd || i.hasDelete

/-- The editor built for a kept inline class: its maximum number of new rows is
forced to zero exactly when a request is in context and the viewer may not add
through it. -/
def toInstance (hasRequest : Bool) (i : Inline) : InlineInstance :=
  { id := i.id, maxNumZeroed := hasRequest && !i.hasAdd }
-- pure-end

-- post-conditions-start
/-- The selection hook, by default, returns the page's own list of inline classes
unchanged. (It exists to be overridden so that the selected list may depend on the
request/object; its default identity behavior is what is pinned here.) -/
def problem_spec_getInlines
    (selfInlines : List Inline) (result : List Inline) : Prop :=
  result = selfInlines
-- post-conditions-end

-- impl-start
def implementation_getInlines (selfInlines : List Inline) : List Inline := Id.run do
  return selfInlines
-- impl-end

-- proof-start
theorem correct_getInlines :
    ∀ (selfInlines : List Inline),
      problem_spec_getInlines selfInlines (implementation_getInlines selfInlines) := by
  intro selfInlines
  rfl
-- proof-end

-- post-conditions-start
/-- The produced editor list is fully pinned to the inputs: it is exactly the
list of selected inline classes (`hookInlines`, in order), with the classes the
viewer can do nothing with under a request removed (`keepInline`), each surviving
class mapped to its editor with the max-rows restriction applied as appropriate
(`toInstance`). The static attribute `selfInlines` does NOT determine the result —
only the selected list does. -/
def problem_spec_getInlineInstances
    (hasRequest : Bool) (selfInlines hookInlines : List Inline)
    (result : List InlineInstance) : Prop :=
  result = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
-- post-conditions-end

-- impl-start
def implementation_getInlineInstances
    (hasRequest : Bool) (selfInlines hookInlines : List Inline) :
    List InlineInstance := Id.run do
  let mut inlineInstances : List InlineInstance := []
  for inlineClass in hookInlines do
    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
    if hasRequest then
      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
        continue
      if !inlineClass.hasAdd then
        inst := { inst with maxNumZeroed := true }
    inlineInstances := inlineInstances ++ [inst]
  return inlineInstances
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop body (proof scaffolding): definitionally equal to the
desugared `do`-block body of `implementation_getInlineInstances`, but written with
plain `if … then … else` and no `pure PUnit.unit` / `continue` desugaring noise so
it can be reasoned about by induction. -/
private def cleanBody_getInlineInstances
    (hasRequest : Bool) (inlineClass : Inline) (r : List InlineInstance) :
    Id (ForInStep (List InlineInstance)) :=
  if hasRequest then
    if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
      ForInStep.yield r
    else if !inlineClass.hasAdd then
      ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := true }])
    else
      ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := false }])
  else
    ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := false }])

/-- Closed form for the cleaned loop, generalized over the accumulator
(Route B helper): folding `cleanBody_getInlineInstances` over `xs` appends, to the
running accumulator, exactly the kept-and-mapped instances. -/
private theorem foldClean_getInlineInstances
    (hasRequest : Bool) (xs : List Inline) (init : List InlineInstance) :
    Id.run (forIn xs init (cleanBody_getInlineInstances hasRequest))
      = init ++ (xs.filter (keepInline hasRequest)).map (toInstance hasRequest) := by
  induction xs generalizing init with
  | nil =>
    simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, cleanBody_getInlineInstances, List.filter_cons, keepInline,
      toInstance] at ih ⊢
    by_cases h : hasRequest = true <;>
      simp only [h, Bool.not_true, Bool.not_false, Bool.true_and, Bool.false_and,
        Bool.false_or, Bool.true_or, if_true, if_false, ih] <;>
      rcases ha : a.hasViewOrChange <;> rcases hb : a.hasAdd <;> rcases hc : a.hasDelete <;>
        simp_all [toInstance, List.map_cons, List.map_nil, List.nil_append, List.cons_append]

theorem correct_getInlineInstances :
    ∀ (hasRequest : Bool) (selfInlines hookInlines : List Inline),
      problem_spec_getInlineInstances hasRequest selfInlines hookInlines
        (implementation_getInlineInstances hasRequest selfInlines hookInlines) := by
  intro hasRequest selfInlines hookInlines
  unfold problem_spec_getInlineInstances implementation_getInlineInstances
  -- The desugared loop body is definitionally equal to the cleaned body, so we can
  -- `show` the goal in cleaned form and discharge it with the closed-form helper.
  show Id.run (forIn hookInlines ([] : List InlineInstance)
        (cleanBody_getInlineInstances hasRequest))
      = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
  rw [foldClean_getInlineInstances, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total exact-equality functional equation over (hasRequest, hookInlines); selfInlines is an unused-but-faithful parameter (both self.inlines and the hook exist in the real signature; gold get_inline_instances no longer reads self.inlines directly). Python env with swebench_unified: python.

SAME_SPEC: all 6 attacks byte-identical spec (same_spec=True), edited impl region only.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <f>`, run concurrently ≤4):
- atk_1 (prepatch: iterate selfInlines) exit=1 (does NOT close; error at `show` tactic).
- atk_2 (partial-domain: no keepInline filter) exit=1.
- atk_3 (boundary: maxNumZeroed loses hasRequest guard) exit=1.
- atk_4 (control-flow-effect: prepend/reverse order) exit=1.
- atk_5 (wrong filter predicate: continue if !hasAdd) exit=1.
- atk_6 (ungrounded-oracle ECHO: impl = spec RHS directly, gold-equivalent) exit=0, CLOSES.
- positive_control (committed gold Solution.lean) exit=0.

### AXIOMS (appended `#print axioms`, both re-verified exit=0):
- atk_6: correct_getInlineInstances does NOT depend on any axioms; correct_getInlines none. CLEAN.
- positive_control: correct_getInlineInstances depends on [propext, Quot.sound] only (no sorryAx); correct_getInlines none. CLEAN.

MANDATORY RESOLVE (protocol step 2 — only closing wrong impl is atk_6): atk_6 faithful patch = the gold patch (extensionally identical to gold post-patch function). Pre-pulled image (`docker -c docker pull ...` succeeded), RE-RAN: RESOLVED=True, completed=True, note='resolved'.

DISPROOF (disproof.lean, exit=0): each of atk_1..atk_5 proved !=specRHS on a concrete input by `decide`, confirming their correct_ is genuinely UNPROVABLE (not a proof-tailoring artifact) and that prepatch is reproduced.

REFINEMENT.md AUDIT: getInlines leg H1 = I; getInlineInstances legs #1..#8 = R (2,3,4,5,6) / I (1,7,8). No A-consumed, no A-reference, no kind-3 ungrounded-oracle leg. axiom_check.py is a legitimate skip stub — Solution.lean declares no `axiom`/`opaque` callee contract; meta axioms=[], deep_model_references=[]. Permission outcomes (has_view_or_change/add/delete_permission) and the constructor enter as data (the three Inline booleans + id); hook output enters as hookInlines. G-CONF differential test (in bundle): checked=120012, disagreements=0, confirming the R/I data-model faithfully matches the patched control flow. Load-bearing R-leg is op #2 (iterate hookInlines not selfInlines) = the single behavioral change of the gold diff.

CONCLUSION: ≥5 distinct wrong impls (partial-domain, boundary, control-flow-effect/order, wrong-filter, prepatch) all fail to close; only the gold-equivalent echo closes and its faithful (gold) patch RESOLVES. Spec discriminates the bug and admits no closing impl that fails to resolve. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking impl found. The spec is a total exact-equality functional equation with no precondition: problem_spec_getInlineInstances hasRequest selfInlines hookInlines result := result = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest). Any impl that closes correct_ is forced extensionally equal to the gold post-patch function. Concrete divergence witnesses (all proved by `decide` in disproof.lean, exit 0): prepatch/atk_1 (iterate selfInlines): impl false [{id:=1,vc,add,del}] [] = [{1,false}] but specRHS false [] = [] — exactly the F2P override-returns-[] scenario; atk_2 (drop keepInline filter): under request keeps a no-permission class the spec removes; atk_3 (maxNumZeroed without hasRequest guard): zeroes when hasRequest=false; atk_4 (prepend): reverses output order; atk_5 (continue if !hasAdd): drops a view/delete-only class the spec keeps.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the list of inline editors to display for an admin page, given a
particular request and the object being edited.

An admin page may attach a number of *inline* editor classes. Which classes are
attached need not be constant: the set of inline classes selected for a page
can depend on the current request and the object being edited, so the page is
given the already-selected list of inline classes for this request/object rather
than reading a static attribute.

For each selected inline class the page constructs one editor. When the call is
made on behalf of a request, an editor is shown only if the viewer is allowed to
interact with it at all — that is, the viewer may view-or-change, add, or delete
through it; an editor the viewer can do none of these with is omitted entirely.
For a shown editor whose viewer may not add new rows through it, the editor's
maximum number of new rows is forced to zero. When there is no request in
context, every selected class yields an editor with no such restriction.

The resulting list preserves the order of the selected inline classes, with the
omitted ones removed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The list of
-- selected inline classes for this request/object enters as plain data
-- (`hookInlines`), as does the static attribute it may override (`selfInlines`).
-- Each inline class carries the three permission outcomes of its editor (view-or-
-- change / add / delete) as booleans, so the per-editor decision is modeled
-- directly from data rather than via a callee contract. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- An inline editor class together with the three permission outcomes its editor
reports for the current request/object. `id` is the class's identity (which class
it is). -/
structure Inline where
  id : Nat
  hasViewOrChange : Bool
  hasAdd : Bool
  hasDelete : Bool
deriving DecidableEq, Repr

/-- A constructed inline editor instance: the class it was built from (`id`) and
whether its maximum number of new rows was forced to zero. -/
structure InlineInstance where
  id : Nat
  maxNumZeroed : Bool
deriving DecidableEq, Repr

/-- Whether an inline class survives the per-request filtering: with no request in
context every class is kept; under a request a class is kept exactly when the
viewer may view-or-change, add, or delete through its editor. -/
def keepInline (hasRequest : Bool) (i : Inline) : Bool :=
  !hasRequest || i.hasViewOrChange || i.hasAdd || i.hasDelete

/-- The editor built for a kept inline class: its maximum number of new rows is
forced to zero exactly when a request is in context and the viewer may not add
through it. -/
def toInstance (hasRequest : Bool) (i : Inline) : InlineInstance :=
  { id := i.id, maxNumZeroed := hasRequest && !i.hasAdd }
-- pure-end

-- post-conditions-start
/-- The selection hook, by default, returns the page's own list of inline classes
unchanged. (It exists to be overridden so that the selected list may depend on the
request/object; its default identity behavior is what is pinned here.) -/
def problem_spec_getInlines
    (selfInlines : List Inline) (result : List Inline) : Prop :=
  result = selfInlines
-- post-conditions-end

-- impl-start
def implementation_getInlines (selfInlines : List Inline) : List Inline := Id.run do
  return selfInlines
-- impl-end

-- proof-start
theorem correct_getInlines :
    ∀ (selfInlines : List Inline),
      problem_spec_getInlines selfInlines (implementation_getInlines selfInlines) := by
  intro selfInlines
  rfl
-- proof-end

-- post-conditions-start
/-- The produced editor list is fully pinned to the inputs: it is exactly the
list of selected inline classes (`hookInlines`, in order), with the classes the
viewer can do nothing with under a request removed (`keepInline`), each surviving
class mapped to its editor with the max-rows restriction applied as appropriate
(`toInstance`). The static attribute `selfInlines` does NOT determine the result —
only the selected list does. -/
def problem_spec_getInlineInstances
    (hasRequest : Bool) (selfInlines hookInlines : List Inline)
    (result : List InlineInstance) : Prop :=
  result = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
-- post-conditions-end

-- impl-start
def implementation_getInlineInstances
    (hasRequest : Bool) (selfInlines hookInlines : List Inline) :
    List InlineInstance := Id.run do
  let mut inlineInstances : List InlineInstance := []
  for inlineClass in hookInlines do
    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
    if hasRequest then
      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
        continue
      if !inlineClass.hasAdd then
        inst := { inst with maxNumZeroed := true }
    inlineInstances := inlineInstances ++ [inst]
  return inlineInstances
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop body (proof scaffolding): definitionally equal to the
desugared `do`-block body of `implementation_getInlineInstances`, but written with
plain `if … then … else` and no `pure PUnit.unit` / `continue` desugaring noise so
it can be reasoned about by induction. -/
private def cleanBody_getInlineInstances
    (hasRequest : Bool) (inlineClass : Inline) (r : List InlineInstance) :
    Id (ForInStep (List InlineInstance)) :=
  if hasRequest then
    if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
      ForInStep.yield r
    else if !inlineClass.hasAdd then
      ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := true }])
    else
      ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := false }])
  else
    ForInStep.yield (r ++ [{ id := inlineClass.id, maxNumZeroed := false }])

/-- Closed form for the cleaned loop, generalized over the accumulator
(Route B helper): folding `cleanBody_getInlineInstances` over `xs` appends, to the
running accumulator, exactly the kept-and-mapped instances. -/
private theorem foldClean_getInlineInstances
    (hasRequest : Bool) (xs : List Inline) (init : List InlineInstance) :
    Id.run (forIn xs init (cleanBody_getInlineInstances hasRequest))
      = init ++ (xs.filter (keepInline hasRequest)).map (toInstance hasRequest) := by
  induction xs generalizing init with
  | nil =>
    simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, cleanBody_getInlineInstances, List.filter_cons, keepInline,
      toInstance] at ih ⊢
    by_cases h : hasRequest = true <;>
      simp only [h, Bool.not_true, Bool.not_false, Bool.true_and, Bool.false_and,
        Bool.false_or, Bool.true_or, if_true, if_false, ih] <;>
      rcases ha : a.hasViewOrChange <;> rcases hb : a.hasAdd <;> rcases hc : a.hasDelete <;>
        simp_all [toInstance, List.map_cons, List.map_nil, List.nil_append, List.cons_append]

theorem correct_getInlineInstances :
    ∀ (hasRequest : Bool) (selfInlines hookInlines : List Inline),
      problem_spec_getInlineInstances hasRequest selfInlines hookInlines
        (implementation_getInlineInstances hasRequest selfInlines hookInlines) := by
  intro hasRequest selfInlines hookInlines
  unfold problem_spec_getInlineInstances implementation_getInlineInstances
  -- The desugared loop body is definitionally equal to the cleaned body, so we can
  -- `show` the goal in cleaned form and discharge it with the closed-form helper.
  show Id.run (forIn hookInlines ([] : List InlineInstance)
        (cleanBody_getInlineInstances hasRequest))
      = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
  rw [foldClean_getInlineInstances, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total exact-equality functional equation over (hasRequest, hookInlines); selfInlines is an unused-but-faithful parameter (both self.inlines and the hook exist in the real signature; gold get_inline_instances no longer reads self.inlines directly). Python env with swebench_unified: python.

SAME_SPEC: all 6 attacks byte-identical spec (same_spec=True), edited impl region only.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <f>`, run concurrently ≤4):
- atk_1 (prepatch: iterate selfInlines) exit=1 (does NOT close; error at `show` tactic).
- atk_2 (partial-domain: no keepInline filter) exit=1.
- atk_3 (boundary: maxNumZeroed loses hasRequest guard) exit=1.
- atk_4 (control-flow-effect: prepend/reverse order) exit=1.
- atk_5 (wrong filter predicate: continue if !hasAdd) exit=1.
- atk_6 (ungrounded-oracle ECHO: impl = spec RHS directly, gold-equivalent) exit=0, CLOSES.
- positive_control (committed gold Solution.lean) exit=0.

### AXIOMS (appended `#print axioms`, both re-verified exit=0):
- atk_6: correct_getInlineInstances does NOT depend on any axioms; correct_getInlines none. CLEAN.
- positive_control: correct_getInlineInstances depends on [propext, Quot.sound] only (no sorryAx); correct_getInlines none. CLEAN.

MANDATORY RESOLVE (protocol step 2 — only closing wrong impl is atk_6): atk_6 faithful patch = the gold patch (extensionally identical to gold post-patch function). Pre-pulled image (`docker -c docker pull ...` succeeded), RE-RAN: RESOLVED=True, completed=True, note='resolved'.

DISPROOF (disproof.lean, exit=0): each of atk_1..atk_5 proved !=specRHS on a concrete input by `decide`, confirming their correct_ is genuinely UNPROVABLE (not a proof-tailoring artifact) and that prepatch is reproduced.

REFINEMENT.md AUDIT: getInlines leg H1 = I; getInlineInstances legs #1..#8 = R (2,3,4,5,6) / I (1,7,8). No A-consumed, no A-reference, no kind-3 ungrounded-oracle leg. axiom_check.py is a legitimate skip stub — Solution.lean declares no `axiom`/`opaque` callee contract; meta axioms=[], deep_model_references=[]. Permission outcomes (has_view_or_change/add/delete_permission) and the constructor enter as data (the three Inline booleans + id); hook output enters as hookInlines. G-CONF differential test (in bundle): checked=120012, disagreements=0, confirming the R/I data-model faithfully matches the patched control flow. Load-bearing R-leg is op #2 (iterate hookInlines not selfInlines) = the single behavioral change of the gold diff.

CONCLUSION: ≥5 distinct wrong impls (partial-domain, boundary, control-flow-effect/order, wrong-filter, prepatch) all fail to close; only the gold-equivalent echo closes and its faithful (gold) patch RESOLVES. Spec discriminates the bug and admits no closing impl that fails to resolve. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The spec faithfully models ModelAdmin.get_inline_instances at base_commit 7d49ad7656 (post-patch). problem_spec_getInlineInstances = (hookInlines.filter keepInline).map toInstance, with keepInline = !hasRequest || hvc || hadd || hdel and toInstance.maxNumZeroed = hasRequest && !hadd — an exact match to the patched control flow (iterate hook output, drop no-permission classes under a request, zero max_num when add is absent). problem_spec_getInlines = selfInlines matches the default hook body. Independent EXHAUSTIVE enumeration over all 8 permission combos × hasRequest ∈ {T,F} × list lengths 0–3 yielded 0 divergences vs a direct transliteration of the post-patch Python. Conformance check passes (120,012 fuzz+edge cases, seed 11095). Lean compiles with no sorry; #print axioms is clean (propext, Quot.sound only). same_spec(gold, prepatch) = True — spec region byte-identical; only the impl iteration source differs (hookInlines vs selfInlines), which is precisely the modeled bug/fix. No spec-too-strong drift found: the abstraction of the three permission predicates and the twice-called has_add_permission into pure booleans is sound for these deterministic permission checks.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean solver-visible content (docstring lines 4-24, structs Inline/InlineInstance, keepInline/toInstance, problem_spec_getInlines, problem_spec_getInlineInstances). The gold edit is: add ModelAdmin.get_inlines() (default returns self.inlines) and change get_inline_instances's loop from `for inline_class in self.inlines:` to `for inline_class in self.get_inlines(request, obj):`. The public problem_statement ALREADY discloses this exactly: it requests adding a get_inlines(request, obj=None) hook so inlines are chosen dynamically per request/object instead of the static self.inlines, noting the current workaround is overriding get_inline_instances. The spec's core assertion — result built from the selected/hook list (hookInlines) rather than the static attribute (selfInlines) — is precisely the requested feature, not extra reconstruction. problem_spec_getInlines: `result = selfInlines` merely pins the default hook identity behavior, which is implied by 'a hook that lets you set inlines' and is trivial. The permission-filtering / max_num-zeroing behavior in the docstring is UNCHANGED surrounding context, not the gold edit, so describing it leaks nothing about the edit. No gold-diff line is quoted in the solver view (the 'was: self.inlines' quotes live only in refinement.md/mapping.md, which are auditor docs outside the spec view). Symbols are abstracted (hookInlines/selfInlines/keepInline), and the Python names present (get_inlines, get_inline_instances, inlines, request, obj) are already public vocabulary in problem_statement. No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
