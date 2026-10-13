# P2 adversarial audit — sphinx-doc__sphinx-9229

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_1_hard.lean`, `atk_2_hard.lean`, `atk_3_hard.lean`, `atk_4_hard.lean`, `atk_5_hard.lean`, `atk_6_hard.lean`, `atk_7_hard.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,10 +47,7 @@
     (normalDoc : Option (List (List String))) :
     Option (List (List String)) := Id.run do
   if docAsAttr then
-    if commentPresent comment then
-      return some []
-    else
-      return none
+    return some []
   return normalDoc
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,10 +47,7 @@
     (normalDoc : Option (List (List String))) :
     Option (List (List String)) := Id.run do
   if docAsAttr then
-    if commentPresent comment then
-      return some []
-    else
-      return none
+    return none
   return normalDoc
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,9 +48,9 @@
     Option (List (List String)) := Id.run do
   if docAsAttr then
     if commentPresent comment then
+      return none
+    else
       return some []
-    else
-      return none
   return normalDoc
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
 def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
-  if docAsAttr && (! commentPresent comment) then
+  if docAsAttr then
     return some ["alias of " ++ aliasText]
   return incoming
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,8 +92,6 @@
 def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
-  if docAsAttr && (! commentPresent comment) then
-    return some ["alias of " ++ aliasText]
   return incoming
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
   if docAsAttr && (! commentPresent comment) then
-    return some ["alias of " ++ aliasText]
+    return some ["alias of " ++ aliasText ++ "!"]
   return incoming
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
   if docAsAttr && (! commentPresent comment) then
-    return some ["alias of " ++ aliasText]
+    return some []
   return incoming
 -- impl-end
 
```

Attack 8 — `atk_1_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,10 +47,7 @@
     (normalDoc : Option (List (List String))) :
     Option (List (List String)) := Id.run do
   if docAsAttr then
-    if commentPresent comment then
-      return some []
-    else
-      return none
+    return some []
   return normalDoc
 -- impl-end
 
@@ -61,10 +58,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -104,10 +102,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

Attack 9 — `atk_2_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,10 +47,7 @@
     (normalDoc : Option (List (List String))) :
     Option (List (List String)) := Id.run do
   if docAsAttr then
-    if commentPresent comment then
-      return some []
-    else
-      return none
+    return none
   return normalDoc
 -- impl-end
 
@@ -61,10 +58,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -104,10 +102,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

Attack 10 — `atk_3_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,9 +48,9 @@
     Option (List (List String)) := Id.run do
   if docAsAttr then
     if commentPresent comment then
+      return none
+    else
       return some []
-    else
-      return none
   return normalDoc
 -- impl-end
 
@@ -61,10 +61,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -104,10 +105,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

Attack 11 — `atk_4_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -92,7 +93,7 @@
 def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
-  if docAsAttr && (! commentPresent comment) then
+  if docAsAttr then
     return some ["alias of " ++ aliasText]
   return incoming
 -- impl-end
@@ -104,10 +105,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

Attack 12 — `atk_5_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -92,8 +93,6 @@
 def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
-  if docAsAttr && (! commentPresent comment) then
-    return some ["alias of " ++ aliasText]
   return incoming
 -- impl-end
 
@@ -104,10 +103,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

Attack 13 — `atk_6_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -93,7 +94,7 @@
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
   if docAsAttr && (! commentPresent comment) then
-    return some ["alias of " ++ aliasText]
+    return some ["alias of " ++ aliasText ++ "!"]
   return incoming
 -- impl-end
 
@@ -104,10 +105,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

Attack 14 — `atk_7_hard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,11 @@
       (implementation_getDoc docAsAttr comment normalDoc) := by
   intro docAsAttr comment normalDoc
   unfold problem_spec_getDoc implementation_getDoc
-  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
-  · simp only [Id.run, hattr, hc, if_true]; rfl
-  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
-  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
 
 -- post-conditions-start
@@ -93,7 +94,7 @@
     (aliasText : String) (incoming : Option (List String)) :
     Option (List String) := Id.run do
   if docAsAttr && (! commentPresent comment) then
-    return some ["alias of " ++ aliasText]
+    return some []
   return incoming
 -- impl-end
 
@@ -104,10 +105,9 @@
       (implementation_addContent docAsAttr comment aliasText incoming) := by
   intro docAsAttr comment aliasText incoming
   unfold problem_spec_addContent implementation_addContent
-  refine ⟨fun h => ?_, fun h => ?_⟩
-  · obtain ⟨h1, h2⟩ := h
-    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
-  · rcases h with h | h
-    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
-    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
+  cases docAsAttr <;> cases comment <;>
+    first
+    | (rename_i x; cases x) <;> simp_all [Id.run, commentPresent] <;> try rfl
+    | simp_all [Id.run, commentPresent]
+  all_goals (try rfl); all_goals (try decide); all_goals simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The two affected
-- procedures branch on (a) a looked-up documentation comment for the object and
-- (b) the rendered description of an alias target; both are supplied to the
-- modeled decision logic as abstract inputs (their values come from the
-- caller/environment), while the decision logic itself is modeled DEEPLY below.
-- The proof agent may add `_prop` axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
/-- A looked-up documentation comment for a name is "present" exactly when the
lookup succeeded and produced at least one line. A failed lookup (`none`) and a
successful-but-empty lookup (`some []`) both count as absent — this mirrors the
truthiness test applied to such a value in the reference language. -/
def commentPresent (comment : Option (List String)) : Bool :=
  match comment with
  | some (_ :: _) => true
  | _             => false
-- pure-end

-- post-conditions-start
/-- Specification of the documentation-block selection for a documented object.

`docAsAttr` indicates the object is being documented as an alias rather than in
its own right. `comment` is the looked-up documentation comment for the object
(a failed lookup is `none`). `normalDoc` is the documentation block produced by
the ordinary path taken when the object is documented in its own right.

When the object is documented as an alias, the result is an empty block
(`some []`) when a documentation comment is present, and "no documentation"
(`none`) when it is absent. When the object is documented in its own right, the
result is exactly the ordinary block. -/
def problem_spec_getDoc (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String)))
    (result : Option (List (List String))) : Prop :=
  (docAsAttr = true →
      (commentPresent comment = true  → result = some []) ∧
      (commentPresent comment = false → result = none)) ∧
  (docAsAttr = false → result = normalDoc)
-- post-conditions-end

-- impl-start
def implementation_getDoc (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String))) :
    Option (List (List String)) := Id.run do
  if docAsAttr then
    if commentPresent comment then
      return some []
    else
      return none
  return normalDoc
-- impl-end

-- proof-start
theorem correct_getDoc : ∀ (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String))),
    problem_spec_getDoc docAsAttr comment normalDoc
      (implementation_getDoc docAsAttr comment normalDoc) := by
  intro docAsAttr comment normalDoc
  unfold problem_spec_getDoc implementation_getDoc
  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
  · simp only [Id.run, hattr, hc, if_true]; rfl
  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
-- proof-end

-- post-conditions-start
/-- Specification of the supplementary content forwarded for a documented object.

`docAsAttr` indicates the object is being documented as an alias. `comment` is
the looked-up documentation comment for the object. `aliasText` is the rendered
description of the alias target. `incoming` is the supplementary content already
supplied by the caller.

When the object is documented as an alias AND no documentation comment is
present, the forwarded content is a single line describing the alias target.
Otherwise the forwarded content is exactly the caller-supplied content,
unchanged. -/
def problem_spec_addContent (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String))
    (result : Option (List String)) : Prop :=
  (docAsAttr = true ∧ commentPresent comment = false →
      result = some ["alias of " ++ aliasText]) ∧
  ((docAsAttr = false ∨ commentPresent comment = true) →
      result = incoming)
-- post-conditions-end

-- impl-start
def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String)) :
    Option (List String) := Id.run do
  if docAsAttr && (! commentPresent comment) then
    return some ["alias of " ++ aliasText]
  return incoming
-- impl-end

-- proof-start
theorem correct_addContent : ∀ (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String)),
    problem_spec_addContent docAsAttr comment aliasText incoming
      (implementation_addContent docAsAttr comment aliasText incoming) := by
  intro docAsAttr comment aliasText incoming
  unfold problem_spec_addContent implementation_addContent
  refine ⟨fun h => ?_, fun h => ?_⟩
  · obtain ⟨h1, h2⟩ := h
    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
  · rcases h with h | h
    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is total & deterministic: problem_spec_getDoc pins result in all 3 domain cases (docAsAttr=true × commentPresent∈{T,F}; docAsAttr=false→normalDoc); problem_spec_addContent pins result in all cases (alias∧!comment→some["alias of "++aliasText]; else→incoming). Frame conjuncts close non-alias / guard-false paths, so no wrong impl can slip through.

Positive control pos_control.lean (=gold): `bash scripts/lean_verify.sh .../pos_control.lean` exit 0. `#print axioms correct_getDoc/correct_addContent` → [propext] only (clean; no sorry, no custom _prop axioms).

A-LEG AUDIT: `grep -nE '^\s*(axiom|opaque)\b' Solution.lean` → NONE. No opaque callees / no deep-model references declared. refinement.md correctly tags every leg R or I (no A-consumed, no A-reference, no kind-3). Model uses comment/aliasText/normalDoc/incoming as universally-quantified abstract inputs (matches mapping.md: get_variable_comment truthiness ↔ commentPresent; restify ↔ aliasText; unchanged paths ↔ normalDoc/incoming pinned by frame conjuncts) — faithful and maximally strong; no callee-correspondence to break.

ATTACKS (7 distinct same-spec wrong impls, all same_spec=True): atk_1 getDoc always some[] (boundary); atk_2 getDoc always none (=prepatch bug 1); atk_3 getDoc inverted branches (control-flow); atk_4 addContent drops comment guard (=prepatch bug 2); atk_5 addContent never emits alias (partial-domain); atk_6 addContent wrong string "...!" (ungrounded content); atk_7 addContent emits some[] not alias line (partial-domain). Each violates the spec on ≥1 input.

COMMANDS/RESULTS: Each attack verified TWICE, run concurrently in batches ≤4.
(a) with gold proof body: `bash scripts/lean_verify.sh .../atk_N.lean` → exit 1 for N=1..7.
(b) with aggressive automation proof (intro; unfold; cases docAsAttr <;> cases comment <;> [rename_i; cases]/simp_all[Id.run,commentPresent]; all_goals try rfl/decide/simp_all): `.../atk_N_hard.lean` → exit 1 for N=1..7. Residual goals are genuinely-false equalities (e.g. atk_1: `pure (some []) = none`; atk_6: `some ["alias of x!"] = some ["alias of x"]`; atk_6_hard: simp_all made no progress).

No wrong impl closed with clean axioms, so the resolve-trigger never fired → patches={} and no run_resolve executions were required (nothing to falsify). prepatch_reproduced=true: the two prepatch bugs are exactly atk_2 (getDoc) and atk_4 (addContent), both unprovable/unclosable here, matching G-DIFF Solution_prepatch{,_2}.lean.

verify ⇒ correct holds. ≥5 distinct attacks run, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_1_hard.lean`, `atk_2_hard.lean`, `atk_3_hard.lean`, `atk_4_hard.lean`, `atk_5_hard.lean`, `atk_6_hard.lean`, `atk_7_hard.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_1_hard.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_2_hard.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_3_hard.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_4_hard.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_5_hard.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_6_hard.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_7_hard.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The two affected
-- procedures branch on (a) a looked-up documentation comment for the object and
-- (b) the rendered description of an alias target; both are supplied to the
-- modeled decision logic as abstract inputs (their values come from the
-- caller/environment), while the decision logic itself is modeled DEEPLY below.
-- The proof agent may add `_prop` axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
/-- A looked-up documentation comment for a name is "present" exactly when the
lookup succeeded and produced at least one line. A failed lookup (`none`) and a
successful-but-empty lookup (`some []`) both count as absent — this mirrors the
truthiness test applied to such a value in the reference language. -/
def commentPresent (comment : Option (List String)) : Bool :=
  match comment with
  | some (_ :: _) => true
  | _             => false
-- pure-end

-- post-conditions-start
/-- Specification of the documentation-block selection for a documented object.

`docAsAttr` indicates the object is being documented as an alias rather than in
its own right. `comment` is the looked-up documentation comment for the object
(a failed lookup is `none`). `normalDoc` is the documentation block produced by
the ordinary path taken when the object is documented in its own right.

When the object is documented as an alias, the result is an empty block
(`some []`) when a documentation comment is present, and "no documentation"
(`none`) when it is absent. When the object is documented in its own right, the
result is exactly the ordinary block. -/
def problem_spec_getDoc (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String)))
    (result : Option (List (List String))) : Prop :=
  (docAsAttr = true →
      (commentPresent comment = true  → result = some []) ∧
      (commentPresent comment = false → result = none)) ∧
  (docAsAttr = false → result = normalDoc)
-- post-conditions-end

-- impl-start
def implementation_getDoc (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String))) :
    Option (List (List String)) := Id.run do
  if docAsAttr then
    if commentPresent comment then
      return some []
    else
      return none
  return normalDoc
-- impl-end

-- proof-start
theorem correct_getDoc : ∀ (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String))),
    problem_spec_getDoc docAsAttr comment normalDoc
      (implementation_getDoc docAsAttr comment normalDoc) := by
  intro docAsAttr comment normalDoc
  unfold problem_spec_getDoc implementation_getDoc
  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
  · simp only [Id.run, hattr, hc, if_true]; rfl
  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
-- proof-end

-- post-conditions-start
/-- Specification of the supplementary content forwarded for a documented object.

`docAsAttr` indicates the object is being documented as an alias. `comment` is
the looked-up documentation comment for the object. `aliasText` is the rendered
description of the alias target. `incoming` is the supplementary content already
supplied by the caller.

When the object is documented as an alias AND no documentation comment is
present, the forwarded content is a single line describing the alias target.
Otherwise the forwarded content is exactly the caller-supplied content,
unchanged. -/
def problem_spec_addContent (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String))
    (result : Option (List String)) : Prop :=
  (docAsAttr = true ∧ commentPresent comment = false →
      result = some ["alias of " ++ aliasText]) ∧
  ((docAsAttr = false ∨ commentPresent comment = true) →
      result = incoming)
-- post-conditions-end

-- impl-start
def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String)) :
    Option (List String) := Id.run do
  if docAsAttr && (! commentPresent comment) then
    return some ["alias of " ++ aliasText]
  return incoming
-- impl-end

-- proof-start
theorem correct_addContent : ∀ (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String)),
    problem_spec_addContent docAsAttr comment aliasText incoming
      (implementation_addContent docAsAttr comment aliasText incoming) := by
  intro docAsAttr comment aliasText incoming
  unfold problem_spec_addContent implementation_addContent
  refine ⟨fun h => ?_, fun h => ?_⟩
  · obtain ⟨h1, h2⟩ := h
    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
  · rcases h with h | h
    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is total & deterministic: problem_spec_getDoc pins result in all 3 domain cases (docAsAttr=true × commentPresent∈{T,F}; docAsAttr=false→normalDoc); problem_spec_addContent pins result in all cases (alias∧!comment→some["alias of "++aliasText]; else→incoming). Frame conjuncts close non-alias / guard-false paths, so no wrong impl can slip through.

Positive control pos_control.lean (=gold): `bash scripts/lean_verify.sh .../pos_control.lean` exit 0. `#print axioms correct_getDoc/correct_addContent` → [propext] only (clean; no sorry, no custom _prop axioms).

A-LEG AUDIT: `grep -nE '^\s*(axiom|opaque)\b' Solution.lean` → NONE. No opaque callees / no deep-model references declared. refinement.md correctly tags every leg R or I (no A-consumed, no A-reference, no kind-3). Model uses comment/aliasText/normalDoc/incoming as universally-quantified abstract inputs (matches mapping.md: get_variable_comment truthiness ↔ commentPresent; restify ↔ aliasText; unchanged paths ↔ normalDoc/incoming pinned by frame conjuncts) — faithful and maximally strong; no callee-correspondence to break.

ATTACKS (7 distinct same-spec wrong impls, all same_spec=True): atk_1 getDoc always some[] (boundary); atk_2 getDoc always none (=prepatch bug 1); atk_3 getDoc inverted branches (control-flow); atk_4 addContent drops comment guard (=prepatch bug 2); atk_5 addContent never emits alias (partial-domain); atk_6 addContent wrong string "...!" (ungrounded content); atk_7 addContent emits some[] not alias line (partial-domain). Each violates the spec on ≥1 input.

COMMANDS/RESULTS: Each attack verified TWICE, run concurrently in batches ≤4.
(a) with gold proof body: `bash scripts/lean_verify.sh .../atk_N.lean` → exit 1 for N=1..7.
(b) with aggressive automation proof (intro; unfold; cases docAsAttr <;> cases comment <;> [rename_i; cases]/simp_all[Id.run,commentPresent]; all_goals try rfl/decide/simp_all): `.../atk_N_hard.lean` → exit 1 for N=1..7. Residual goals are genuinely-false equalities (e.g. atk_1: `pure (some []) = none`; atk_6: `some ["alias of x!"] = some ["alias of x"]`; atk_6_hard: simp_all made no progress).

No wrong impl closed with clean axioms, so the resolve-trigger never fired → patches={} and no run_resolve executions were required (nothing to falsify). prepatch_reproduced=true: the two prepatch bugs are exactly atk_2 (getDoc) and atk_4 (addContent), both unprovable/unclosable here, matching G-DIFF Solution_prepatch{,_2}.lean.

verify ⇒ correct holds. ≥5 distinct attacks run, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sphinx-doc__sphinx-9229 lean bundle. Two modeled functions from ClassDocumenter (post-patch @ base 876fa81e + gold patch, which patch_equals_gold=true).

### Verification done
- Solution.lean compiles: scripts/lean_verify.sh exit 0.
- #print axioms correct_getDoc / correct_addContent -> only [propext]; NO sorryAx (proofs are real).
- same_spec(a,a,LeanTables) = True; spec_view hash matches recorded region_hashes (3cfa7f7a...); post-conditions/pure/impl/axioms hashes all match meta.json.
- conformance_check.py: 120000 inputs, 0 disagreements (seed=9229).
- Cross-checked spec against the REAL repo source at base commit (pre-patch code) plus the gold patch.diff.

### Boundary-by-boundary faithfulness
1. get_doc alias branch. Real post-patch: `if comment: return []; else return None`; `if comment:` truthiness is None->F, []->F, [x..]->T. Model commentPresent (some(_::_)->true, else false) reproduces all three. docAsAttr=false collapses the untouched ordinary path to abstract input normalDoc, pinned by frame conjunct `docAsAttr=false -> result=normalDoc`. Agrees on every input.
2. add_content. Real guard `if self.doc_as_attr and not self.get_variable_comment():` -> not on None/[]=True, [x]=False. Model `docAsAttr && !commentPresent comment` matches. Alias line some ["alias of "++aliasText] <-> StringList([_('alias of %s') % restify(self.object)]) (gettext id = identity format here); non-guard case pinned to incoming. Agrees on every input.

CLOSEST SOFT SPOT (examined, judged NOT a defect): real add_content wraps the alias-line assignment in a pre-existing `try: ... except AttributeError: pass` ('Invalid class object'). On that exception more_content stays = incoming, whereas the spec mandates result = some ["alias of "++aliasText] unconditionally on the docAsAttr && not-present branch. But restify(self.object) is modeled as a TOTAL abstract input aliasText:String (documented in mapping.md), the try/except is untouched by the patch, and there is no input in the modeled domain (docAsAttr, comment, aliasText, incoming) that represents 'restify raises AttributeError'. Within the entire modeled input space the spec and the real callee agree on every input. This is a legitimate documented abstraction boundary, not spec over-strengthening on any reachable modeled input.

No diverging input exists within the modeled domain. Spec is faithful (neither too strong nor drifted). Note: spec is appropriately tight via frame conjuncts (no leave-output-unconstrained hole), consistent with G-PANEL-3/G-EQ passing.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (rep.passed=True, zero hard failures) on the lean spec view. Verified independently: (1) no diff markers; (2) no verbatim gold-patch line reproduced (len>=8 normalized) — confirmed by leakage.screen; (3) patched file path sphinx/ext/autodoc/__init__.py and its dotted module path do NOT appear in the spec view; (4) patched changed symbols are ['get_doc','get_object_members','get_variable_comment'] — none appears in the spec view: the Lean idents getDoc/addContent do not lexically embed get_doc/add_content (underscore-stripped collision check clears), and crucially the newly-introduced helper get_variable_comment is nowhere named — comments describe it abstractly as a 'looked-up documentation comment' (an environment-supplied abstract input), i.e. behavior not the edit; (5) no bug/fix narration terms in comments.

Semantic check (the part the lexical screen can miss): the spec view describes only the CORRECTED BEHAVIOR — for an alias, return an empty doc block / suppress the 'alias of ...' line when a documentation comment is present, else fall back to the alias text. This is exactly what the public problem_statement already demands ('The docs should show the contents in the docstrings for all the type aliases instead of the alias of ... default text'). Both the docstring-vs-'alias of' behaviors and the desired switch are public via problem_statement. Specifying the target behavior is the legitimate job of a spec and does not reveal the gold implementation strategy: the spec does not disclose the introduced helper get_variable_comment, ModuleAnalyzer.for_module, attr_docs, get_real_modname, the objpath key, or the two specific edit loci (get_doc alias branch return + add_content guard). A solver must still discover HOW and WHERE. No RELAXED_LEAKAGE.md present and none required. Spec view is clean beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
