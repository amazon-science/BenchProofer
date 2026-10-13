# P2 adversarial audit — django__django-14787

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_prepatch.lean`, `atk_partial_domain.lean`, `atk_two_state.lean`, `atk_observed_only.lean`, `atk_ownentry_only.lean`, `atk_order_swapped.lean`, `atk_wrapped_false.lean`, `atk_selfsuff_from_source.lean`, `atk_reversed.lean`, `atk_module_fallback.lean`, `atk_crosswired.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo_literal.lean`, `atk_double.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no counterexample exists, and this is a THEOREM rather than the outcome of a finite search. determinacy.lean (lean_verify exit=0, `#print axioms spec_is_functionally_determined` => "does not depend on any axioms") machine-proves `spec_is_functionally_determined : ∀ impl, problem_spec_total_attachIdentity impl → ∀ source, impl source = implementation_attachIdentity source`. The postcondition pins ALL EIGHT leaves of `CallableAttrs` (name/module/qualname × {observed, ownEntry}, plus `wrapped` and `selfSufficient` — that is every field of the record) to CLOSED functions of `source`, and `callable_ext` cashes that into record equality. So the frozen spec admits exactly ONE function up to pointwise equality: no same-spec impl can verify and differ from gold anywhere in the domain. The two attacks that DO verify are proved equal to gold in the same file (`echo_equals_gold`, `double_equals_gold`, both axiom-clean), and both RESOLVE under the official harness, as required.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,12 +202,10 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
-def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
+-- ATTACK (prepatch bug): the pre-patch line `bound_method = partial(...)` with NO
+-- identity transfer at all: hand back the freshly synthesised callable as-is.
+def implementation_attachIdentity (_source : CallableAttrs) : CallableAttrs := Id.run do
   let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
   return bound
 -- impl-end
 
@@ -215,14 +213,14 @@
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 2 — `atk_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,11 +202,12 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (partial-domain): perform the transfer ONLY when the source supplies a
+-- qualified name at one of its layers; otherwise hand back the bare callable.
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
   let mut bound : CallableAttrs := bareCallable
+  if (source.qualname.ownEntry.overlay source.qualname.observed) = .vacant then
+    return bound
   bound := copyIdentity source bound
   return bound
 -- impl-end
@@ -215,14 +216,14 @@
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 3 — `atk_two_state.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,36 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (boundary / two-state collapse): model the attribute space with TWO
+-- states instead of three -- an entry whose content is nothing in particular is
+-- treated as no entry at all, so it is not the entry handed on.
+def AttrSlot.collapse : AttrSlot -> AttrSlot
+  | .filled none => .vacant
+  | s            => s
+
+def IdentityAttr.transferTwoState (src dst : IdentityAttr) : IdentityAttr :=
+  let entry := (AttrSlot.collapse src.ownEntry).overlay
+                 ((AttrSlot.collapse src.observed).overlay dst.ownEntry)
+  { observed := entry.overlay dst.observed, ownEntry := entry }
+
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
-  return bound
+  let bound : CallableAttrs := bareCallable
+  return { name           := source.name.transferTwoState bound.name,
+           module         := source.module.transferTwoState bound.module,
+           qualname       := source.qualname.transferTwoState bound.qualname,
+           wrapped        := true,
+           selfSufficient := bound.selfSufficient }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
-  simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩ <;>
+    simp only [implementation_attachIdentity, IdentityAttr.transferTwoState,
+      transferredEntry, AttrSlot.collapse, bareCallable, Id.run] <;>
+    first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
 -- proof-end
```

Attack 4 — `atk_observed_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,31 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (A-leg amputation, callee step (i) alone): run only the per-attribute
+-- pass from what a reader observes on the original, and never lay the original's
+-- own table over the synthesised callable's table.
+def IdentityAttr.transferObservedOnly (src dst : IdentityAttr) : IdentityAttr :=
+  let entry := src.observed.overlay dst.ownEntry
+  { observed := entry.overlay dst.observed, ownEntry := entry }
+
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
-  return bound
+  let bound : CallableAttrs := bareCallable
+  return { name           := source.name.transferObservedOnly bound.name,
+           module         := source.module.transferObservedOnly bound.module,
+           qualname       := source.qualname.transferObservedOnly bound.qualname,
+           wrapped        := true,
+           selfSufficient := bound.selfSufficient }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
-  simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩ <;>
+    simp only [implementation_attachIdentity, IdentityAttr.transferObservedOnly,
+      transferredEntry, bareCallable, Id.run] <;>
+    first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
 -- proof-end
```

Attack 5 — `atk_ownentry_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,31 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (A-leg amputation, callee step (ii) alone): lay the original's own table
+-- over the synthesised callable's table, and skip the per-attribute pass from what
+-- a reader observes on the original.
+def IdentityAttr.transferTableOnly (src dst : IdentityAttr) : IdentityAttr :=
+  let entry := src.ownEntry.overlay dst.ownEntry
+  { observed := entry.overlay dst.observed, ownEntry := entry }
+
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
-  return bound
+  let bound : CallableAttrs := bareCallable
+  return { name           := source.name.transferTableOnly bound.name,
+           module         := source.module.transferTableOnly bound.module,
+           qualname       := source.qualname.transferTableOnly bound.qualname,
+           wrapped        := true,
+           selfSufficient := bound.selfSufficient }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
-  simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩ <;>
+    simp only [implementation_attachIdentity, IdentityAttr.transferTableOnly,
+      transferredEntry, bareCallable, Id.run] <;>
+    first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
 -- proof-end
```

Attack 6 — `atk_order_swapped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,32 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (A-leg pass ORDER swapped): both passes are run, but in the WRONG order --
+-- the original's own table is laid down FIRST and the per-attribute pass from what a
+-- reader observes on the original is laid over it, so where the original's two layers
+-- disagree it is the observed layer that survives instead of the table entry.
+def IdentityAttr.transferSwapped (src dst : IdentityAttr) : IdentityAttr :=
+  let entry := src.observed.overlay (src.ownEntry.overlay dst.ownEntry)
+  { observed := entry.overlay dst.observed, ownEntry := entry }
+
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
-  return bound
+  let bound : CallableAttrs := bareCallable
+  return { name           := source.name.transferSwapped bound.name,
+           module         := source.module.transferSwapped bound.module,
+           qualname       := source.qualname.transferSwapped bound.qualname,
+           wrapped        := true,
+           selfSufficient := bound.selfSufficient }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
-  simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩ <;>
+    simp only [implementation_attachIdentity, IdentityAttr.transferSwapped,
+      transferredEntry, bareCallable, Id.run] <;>
+    first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
 -- proof-end
```

Attack 7 — `atk_wrapped_false.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,26 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (boundary, callee step (iii) dropped): transfer the identity but never
+-- record that the synthesised callable now stands in for the original.
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
   let mut bound : CallableAttrs := bareCallable
   bound := copyIdentity source bound
-  return bound
+  return { bound with wrapped := false }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 8 — `atk_selfsuff_from_source.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,27 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (control-flow-effect): dress the ORIGINAL instead of the synthesised
+-- callable, so the object handed back needs whatever the original needed -- its call
+-- shape is taken from the original rather than from the synthesised callable.
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
   let mut bound : CallableAttrs := bareCallable
   bound := copyIdentity source bound
-  return bound
+  return { bound with selfSufficient := source.selfSufficient }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 9 — `atk_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,25 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (role reversal): run the transfer the other way round -- lay the freshly
+-- synthesised callable's (empty) identity onto the original and hand THAT back.
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
-  return bound
+  let bound : CallableAttrs := bareCallable
+  return copyIdentity bound source
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 10 — `atk_module_fallback.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,11 +202,16 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (ungrounded destination fallback): treat the synthesised callable as
+-- already answering for the defining module out of the general-purpose machinery it
+-- is made of, so where the original supplies no module the machinery's own answer
+-- shows through instead of nothing at all.
+def bareCallableWithModule : CallableAttrs :=
+  { bareCallable with
+      module := { observed := .filled (some "functools"), ownEntry := .vacant } }
+
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
+  let mut bound : CallableAttrs := bareCallableWithModule
   bound := copyIdentity source bound
   return bound
 -- impl-end
@@ -215,14 +220,14 @@
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 11 — `atk_crosswired.lean` → rejected (same spec, does not verify — good)

```diff
@@ -202,27 +202,27 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (cross-wiring): transfer the identity, but serve the qualified name from
+-- the entry the human-readable name supplied rather than from the original's own
+-- qualified name.
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
   let mut bound : CallableAttrs := bareCallable
   bound := copyIdentity source bound
-  return bound
+  return { bound with qualname := bound.name }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
+  unfold problem_spec_attachIdentity implementation_attachIdentity transferredEntry
   simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
+    (try rfl) <;>
+    (first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
+      | simp_all
+      | rfl)
 -- proof-end
```

Attack 12 — `atk_echo_literal.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -202,27 +202,21 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
-def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
-  let mut bound : CallableAttrs := bareCallable
-  bound := copyIdentity source bound
-  return bound
+-- ATTACK (ungrounded-oracle echo): realise each required entry directly as a record
+-- literal, with no reference to the synthesised callable or to the transfer at all.
+def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs :=
+  { name     := { observed := transferredEntry source.name,
+                  ownEntry := transferredEntry source.name },
+    module   := { observed := transferredEntry source.module,
+                  ownEntry := transferredEntry source.module },
+    qualname := { observed := transferredEntry source.qualname,
+                  ownEntry := transferredEntry source.qualname },
+    wrapped := true, selfSufficient := true }
 -- impl-end
 
 -- proof-start
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
-  simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  exact ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 13 — `atk_double.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -202,11 +202,11 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the callable that acts on behalf of `source`: start from a freshly
--- synthesised callable, which holds no identity of its own at either of its
--- layers, then transfer `source`'s identity onto it.
+-- ATTACK (double transfer): run the identity transfer TWICE onto the synthesised
+-- callable instead of once.
 def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
   let mut bound : CallableAttrs := bareCallable
+  bound := copyIdentity source bound
   bound := copyIdentity source bound
   return bound
 -- impl-end
@@ -215,14 +215,13 @@
 theorem correct_attachIdentity :
     problem_spec_total_attachIdentity implementation_attachIdentity := by
   intro source _
-  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
-    IdentityAttr.transfer transferredEntry bareCallable
-  simp only [Id.run]
-  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
+  show problem_spec_attachIdentity source
+    (copyIdentity source (copyIdentity source bareCallable))
+  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩ <;>
+    simp only [copyIdentity, IdentityAttr.transfer, transferredEntry,
+      bareCallable, AttrSlot.overlay] <;>
+    first
+      | (cases source.name.ownEntry <;> cases source.name.observed <;> rfl)
+      | (cases source.module.ownEntry <;> cases source.module.observed <;> rfl)
+      | (cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a callable that carries identity metadata.

A callable carries a bundle of identity attributes (a human-readable name, the
defining module, and a qualified name), and it may record that it transparently
stands in for another callable. Separately from that metadata, a callable is
either self-sufficient — a caller runs it supplying only the arguments of the call
itself — or it still expects the object it belongs to to be handed in first.

Each identity attribute of a callable sits at TWO layers. The callable's own
attribute table may hold an entry for it, and the kind of thing the callable is may
answer for it as well; which of the two a reader of the attribute is answered from
depends on the callable. So what the callable's own table holds and what a reader
observes are two separate facts about it, and they need not agree.

A freshly synthesised callable holds nothing in its own table, and the
general-purpose machinery it is built out of answers for none of these attributes
either, so a reader of any of them observes nothing at all. It is nonetheless
self-sufficient: the object it acts for is already built into it. When such a
callable is meant to act on behalf of an existing one, the existing callable's
identity is transferred onto it — in two
passes, attribute by attribute from what a reader observes on the original, and
then the original's own table laid over the synthesised callable's table as a
whole — so that downstream code inspecting the synthesised callable observes the
original identity; and the callable handed back is still the self-sufficient one,
because callers go on to run it with the arguments of the call alone.

How much identity the original holds, and at which of its layers, is not assumed.
A plain function is observed to hold all three attributes while its own table holds
none of them; a callable that keeps its identity in its own table may hold entries
for only some of them, may hold an entry whose content is nothing in particular,
and may hold an entry that disagrees with what a reader of it observes. The
required behavior is claimed of every callable the step can be handed.
-/

-- axioms-start
-- No opaque callees are consumed: the metadata transfer is modeled deeply in the
-- `pure` region (see `copyIdentity`), so the corresponding library routine is an
-- A-reference validated by axiom_check.py rather than a consumed axiom.
-- axioms-end

-- pure-start
/-- What is held for one identity attribute at one layer.

A layer either holds no entry at all for an attribute, or holds one. When it holds
one, the entry's content need not be text: an entry whose content is nothing in
particular is perfectly ordinary. So `vacant` (no entry) and `filled none` (an
entry holding nothing in particular) are DISTINCT states, and both are distinct
from `filled (some s)` (an entry holding the text `s`). The distinction is
load-bearing: it is presence of the entry, not textual content, that decides
whether this entry is the one handed on when identity is transferred. -/
inductive AttrSlot where
  | vacant
  | filled (content : Option String)
  deriving DecidableEq, Repr

/-- The entry that survives when `src`'s layer is laid over `dst`'s: `src`'s entry
whenever `src` holds one — content and all, whatever that content is — and
otherwise the entry `dst` already held. Holding an entry is what wins here; what
the entry contains is carried along but never consulted. -/
def AttrSlot.overlay : AttrSlot → AttrSlot → AttrSlot
  | .vacant,   dst => dst
  | .filled c, _   => .filled c

/-- One identity attribute of a callable, at both of its layers.

`observed` is what a reader of that attribute on this callable is answered with,
and is `vacant` when the callable has no such attribute at all. `ownEntry` is what
the callable's OWN attribute table holds for it, and is `vacant` when its table
holds no entry for it, in which case a reader is answered by the kind of thing the
callable is.

The two layers can disagree: the kind of thing a callable is may answer for an
attribute ahead of the callable's own table, and then the table's entry is not what
a reader observes — while it is still the entry that table hands on when the table
as a whole is laid over another callable's. For a callable whose readers are
answered from its own table first — which is the case for a freshly synthesised
one — `observed` is `ownEntry` laid over whatever its kind answers for. -/
structure IdentityAttr where
  observed : AttrSlot
  ownEntry : AttrSlot
  deriving DecidableEq, Repr

/-- The identity metadata a callable carries, together with how it can be run.

Each of the three textual fields is one identity attribute at both of its layers
(see `IdentityAttr`). `wrapped` records whether the callable transparently
delegates to another callable. `selfSufficient` records whether a caller can run
the callable supplying only the arguments of the call itself; a callable that still
expects the object it belongs to to be handed in first is not self-sufficient. -/
structure CallableAttrs where
  name           : IdentityAttr
  module         : IdentityAttr
  qualname       : IdentityAttr
  wrapped        : Bool
  selfSufficient : Bool
  deriving DecidableEq, Repr

/-- A freshly synthesised callable. Its own table holds nothing at all, and the
general-purpose machinery it is made of answers for none of the three attributes
either — so a reader of any of them observes nothing, which is precisely the
identity such a callable lacks. It does not yet delegate to any other callable. It
is self-sufficient: the object it acts for is already built into it, so a caller
runs it with the arguments of the call alone. -/
def bareCallable : CallableAttrs :=
  { name     := { observed := .vacant, ownEntry := .vacant },
    module   := { observed := .vacant, ownEntry := .vacant },
    qualname := { observed := .vacant, ownEntry := .vacant },
    wrapped := false, selfSufficient := true }

/-- Transfer onto `dst` the identity `src` supplies for ONE attribute, in the two
passes the transfer really makes. First the attribute is placed on `dst` from what
a reader observes on `src`, and nothing is placed when `src` has no such attribute.
Then `src`'s own table entry is laid over that placement, so `src`'s table entry is
the one that survives whenever its table holds one. Both passes write to `dst`'s
own table, and what `dst` is then observed to hold is that table's new entry laid
over whatever `dst`'s kind already answered for. -/
def IdentityAttr.transfer (src dst : IdentityAttr) : IdentityAttr :=
  let entry := src.ownEntry.overlay (src.observed.overlay dst.ownEntry)
  { observed := entry.overlay dst.observed, ownEntry := entry }

/-- Transfer onto `dst` the identity that `src` supplies. Each of the three
attributes is transferred as `IdentityAttr.transfer` describes. After the transfer,
`dst` is recorded as delegating to `src`. The transfer concerns identity only: the
callable handed back is `dst`, so how it can be run stays `dst`'s and is unaffected
by `src`. -/
def copyIdentity (src dst : CallableAttrs) : CallableAttrs :=
  { name           := src.name.transfer dst.name,
    module         := src.module.transfer dst.module,
    qualname       := src.qualname.transfer dst.qualname,
    wrapped        := true,
    selfSufficient := dst.selfSufficient }

/-- The entry a callable whose own table starts out empty ends up holding in that
table for one identity attribute of `src`, once `src`'s identity has been
transferred onto it: `src`'s own table entry whenever `src`'s table holds one — the
same content, whatever that content is — and otherwise what a reader observes on
`src`. Both of `src`'s layers are consulted, and the table layer is the one that
survives, because the table is laid over as a whole after the per-attribute pass
has run. -/
def transferredEntry (src : IdentityAttr) : AttrSlot :=
  src.ownEntry.overlay src.observed
-- pure-end

-- pre-conditions-start
/-- Admissibility: none. The step is defined for every callable it can be handed,
whatever entries that callable holds at either layer and however the callable itself
has to be run. In particular a callable holding entries for only some of the three
attributes is admissible; so is one holding an entry whose content is nothing in
particular; so is one whose own table holds an entry that disagrees with what a
reader of it observes; and so is one that is not runnable on its own until the
object it belongs to is handed in. The claim below is therefore made over the whole
domain rather than over a distinguished part of it. -/
def problem_pre_attachIdentity (_source : CallableAttrs) : Prop := True
-- pre-conditions-end

-- post-conditions-start
/-- The callable bound to act on behalf of `source` must expose `source`'s
identity.

For each identity attribute, the entry the result holds in its OWN table is the
entry `source`'s own table holds whenever `source`'s table holds one — the same
content, whatever that content is, and in particular an entry holding nothing in
particular is handed on as such rather than being treated as no entry at all — and
otherwise what a reader observes on `source`. Where `source` supplies nothing at
either layer, the result's table is left as empty of that attribute as the freshly
synthesised callable's was.

What a reader OBSERVES on the result follows from that table, because what is
handed back is the synthesised callable: its readers are answered from its own
table, and the machinery it is made of answers for none of the three attributes on
its own account. So for each of the three a reader observes exactly the transferred
entry — each is held exactly when `source` supplies it at one of its layers, with
the same content, and none is held at all when `source` supplies nothing. The
result is recorded as delegating to `source`.

Carrying that identity must not cost the result its usability: the result is
self-sufficient, so a caller runs it with the arguments of the call alone rather
than having to hand in the object `source` belongs to. This holds no matter how
`source` itself has to be run, because what is handed back is the synthesised
callable wearing `source`'s identity and never `source`. -/
def problem_spec_attachIdentity (source : CallableAttrs) (result : CallableAttrs) : Prop :=
  result.name.ownEntry = transferredEntry source.name ∧
  result.name.observed = transferredEntry source.name ∧
  result.module.ownEntry = transferredEntry source.module ∧
  result.module.observed = transferredEntry source.module ∧
  result.qualname.ownEntry = transferredEntry source.qualname ∧
  result.qualname.observed = transferredEntry source.qualname ∧
  result.wrapped = true ∧
  result.selfSufficient = true

/-- The obligation: the required behavior holds at EVERY admissible callable.
Stating the quantifier and the admissibility condition here, rather than leaving
them to the proof, is what makes the domain of the claim part of the
specification instead of an artifact of how it happens to be proved. -/
def problem_spec_total_attachIdentity (impl : CallableAttrs → CallableAttrs) : Prop :=
  ∀ source, problem_pre_attachIdentity source →
    problem_spec_attachIdentity source (impl source)
-- post-conditions-end

-- impl-start
-- Build the callable that acts on behalf of `source`: start from a freshly
-- synthesised callable, which holds no identity of its own at either of its
-- layers, then transfer `source`'s identity onto it.
def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
  let mut bound : CallableAttrs := bareCallable
  bound := copyIdentity source bound
  return bound
-- impl-end

-- proof-start
theorem correct_attachIdentity :
    problem_spec_total_attachIdentity implementation_attachIdentity := by
  intro source _
  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
    IdentityAttr.transfer transferredEntry bareCallable
  simp only [Id.run]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-14787 lean bundle. Scratch: (worktree at base_commit 004b4620f6 under./wt). VERDICT: SOUND — and stronger than the gate requires: the spec is machine-proved functionally determined, so verify⇒extensionally-gold is a theorem here, not a survived search.

**SAME-SPEC:** all 13 attacks + positive control are byte-identical in spec — swebench_unified.markers.same_spec(gold, atk, lean) == True for every one (13/13, 0 failures). Only the impl+proof regions were edited.

### VERIFY COMMANDS (`bash scripts/lean_verify.sh $S/<f>.lean` from repo root; run concurrently in batches of 4):
  atk_pos                   exit=0 VERIFIES  <- positive control (gold impl+proof verbatim)
  atk_prepatch              exit=1 REJECTED  the real pre-patch bug (return bareCallable, no transfer)
  atk_partial_domain        exit=1 REJECTED  partial-domain (gold only where qualname is supplied)
  atk_two_state             exit=1 REJECTED  boundary: two-state collapse (held-but-None == absent)
  atk_observed_only         exit=1 REJECTED  A-LEG amputation: callee step (i) only, no `__dict__` merge
  atk_ownentry_only         exit=1 REJECTED  A-LEG amputation: callee step (ii) only, no assigned pass
  atk_order_swapped         exit=1 REJECTED  A-LEG pass ORDER swapped (observed laid over table) [NEW this pass]
  atk_wrapped_false         exit=1 REJECTED  boundary: callee step (iii) dropped (`__wrapped__` never set)
  atk_selfsuff_from_source  exit=1 REJECTED  control-flow-effect: call shape taken from SOURCE (= wraps(method)(method))
  atk_reversed              exit=1 REJECTED  role reversal: copyIdentity bound source
  atk_module_fallback       exit=1 REJECTED  ungrounded destination fallback ('functools' observed module)
  atk_crosswired            exit=1 REJECTED  cross-wiring: qualname served from the name entry [NEW this pass]
  atk_echo_literal          exit=0 VERIFIES  ungrounded-oracle echo (postcondition as a record literal)
  atk_double                exit=0 VERIFIES  transfer run TWICE (extensionally gold; overlay is idempotent)

TACTIC-WEAKNESS DISCIPLINE — this is where a rubber-stamp would have mis-scored. Several exit=1 residuals showed UNREDUCED `pure`/`copyIdentity` terms (e.g. atk_wrapped_false is semantically wrong ONLY in the `wrapped` leg, yet its metadata legs also failed), which is the signature of a weak closer, not of semantics. I therefore did NOT accept exit=1 as evidence. wit_all.lean (lean_verify exit=0, ZERO errors) machine-proves, for ALL ELEVEN rejected attacks, BOTH:
  (a) `¬ problem_spec_total_attachIdentity impl_<t>` — a genuine semantic violation, discharged by `decide` on a concrete admissible source, so it cannot be a tactic artifact; and
  (b) `problem_spec_attachIdentity <src> (impl_gold <src>)` — gold SATISFIES that very input, so each witness DISCRIMINATES rather than being an input the spec rejects for everyone.
Witness sources used: src_plain, src_disagree (layers disagree), src_nonecontent (held-but-None), src_nomodule (object.`__init__` shape), src_unbound (not runnable without its instance), src_noqual. All admissible (precondition is `True`).

AXIOMS (files ax_*.lean, `#print axioms correct_attachIdentity` appended, exit=0 each): atk_pos, atk_echo_literal, atk_double all report "'correct_attachIdentity' does not depend on any axioms" — clean, no sorryAx. (One earlier determinacy draft leaked `sorryAx` through a `simp_all`; I caught it via #print axioms and re-proved honestly via structure eta — recorded because it is exactly the failure mode a lazy pass ships.)

MANDATORY RESOLVE RUNS — every impl that verifies with clean axioms had its faithful patch materialized against the real worktree (`git apply --check` rc=0 for each) and RUN through the official harness (swebench_unified.harness.run_resolve), launched concurrently:
  gold             patch_gold.diff             -> resolved=True  completed=True 'resolved'  (accept-direction control)
  atk_echo_literal patch_atk_echo_literal.diff -> resolved=True  completed=True 'resolved'
  atk_double       patch_atk_double.diff       -> resolved=True  completed=True 'resolved'
Both verifying impls RESOLVE, so neither is a spec weakness => NOT a G-EQ fail. Consistent with the determinacy theorem, which says they CANNOT be counterexamples.

ORACLE DISCRIMINATING POWER, both directions (so 'it resolved' is not vacuous):
  negctl      pre-patch behaviour retained, applies cleanly -> resolved=False completed=True (consistent, not flaky)
  wrongcallee wraps(method)(partial(lambda *a, **k: None)) -> resolved=False completed=True (consistent, not flaky)
The reject lane fires, so the three resolved=True verdicts carry information.

COARSENESS PROBE (sharpest remaining lever: CallableAttrs names no carrier for `__doc__`/`__annotations__`/the rest of `__dict__`, and `wrapped: Bool` records only PRESENCE of `__wrapped__`, not its value). patch_atk_coarse.diff realizes the eight pinned components identically to gold while setting `__doc__`=None, `__annotations__`=garbage, `__wrapped__`='not-the-method', and performing NO `__dict__` merge => run_resolve: resolved=True completed=True. So the unmodeled facets are not load-bearing for this instance's F2P/P2P — consistent with the suite: the only `__doc__` assertion (test_preserve_attributes, tests/decorators/tests.py:271) reads Test.method.`__doc__` on the OUTER `_wrapper`, which the untouched update_wrapper(`_wrapper`, method) at decorators.py:48 still sets. Modeling boundary is adequate, not merely convenient.

A-LEG AUDIT (the focus of this role). refinement.md legs: 1,2 = R; 3 = A-reference; 4 = I. NO kind-3 leg, no A-consumed leg, no opaque callee — consistent with meta.json axioms=[] / opaque_callees=[] and with the clean `#print axioms`. The single A-leg (leg 3, `copyIdentity` == functools.update_wrapper) was re-derived step by step AGAINST THE REAL INTERPRETER in the environment of record (instance image, conda testbed, CPython 3.9.20, via docker_exec.run_in_container with the gold patch applied; probe.py, rc=0):

  A. fresh partial observed [`__name__`,`__module__`,`__qualname__`] = ABSENT/ABSENT/ABSENT, `__dict__` == {}  => bareCallable (all vacant at BOTH layers) FAITHFUL

  B. table-transparent on all three (a `__dict__` entry is what getattr answers) = True/True/True     => the `observed:= entry.overlay dst.observed` leg is right

  C. source observed=('held','g') vs table=('held','FROM_TABLE'); result `__name__` == 'FROM_TABLE'    => ownEntry WINS; `transferredEntry = ownEntry.overlay observed` is the RIGHT ORDER, not the reverse (this is the leg atk_order_swapped attacks, and the spec rejects it)

  D. held-but-None `__module__` copied VERBATIM = ('held', None)                                       => three-state AttrSlot REQUIRED; a two-state Option String would be unfaithful (atk_two_state, rejected)

  E. `__wrapped__` beats a bogus source-table `__wrapped__` key = True                                   => `wrapped:= true` faithful (written last)

  F. update_wrapper returns its WRAPPER (is-identity) = True                                         => `selfSufficient:= dst.selfSufficient` faithful

  G. unbound method self_sufficient=False | bound+partial=True | after update_wrapper=True           => the usability leg is non-trivial and correctly oriented
All six match the model. I attacked BOTH halves of the A-leg separately (atk_observed_only drops step ii, atk_ownentry_only drops step i) AND the composition order (atk_order_swapped); the spec rejects all three with machine-proved witnesses, so both passes and their order are genuinely pinned rather than one being decorative.

ENVIRONMENT TRAP (recorded so it is not later mis-read as a defect): the bareCallable carrier fact is interpreter-dependent. On the audit HOST (CPython 3.10.20) a fresh functools.partial DOES answer `__module__` == 'functools'; the instance image pins 3.9.20, where it does not. The shipped bareCallable is exact FOR THE PINNED INTERPRETER, and mapping.md's 'Environment of record' section pins it explicitly. I encoded the 3.10 behaviour as an attack anyway (atk_module_fallback) and the spec REJECTS it — correctly, since that fallback is false of this instance's interpreter.

**DOC NOTE:** the prior pass's doc defect #1 (mapping.md claiming bareCallable observes 'functools', and a `synthesisedModule` constant) is REPAIRED in the current bytes — mapping.md line 40 now states all three vacant at both layers, and grep finds zero `synthesisedModule` in Solution.lean. No outstanding doc defect that could mask a weakness.

**WHY SOUND:** 13 same-spec admissible attacks (>=5 required, 2 of them new this pass: the A-leg pass-order swap and the cross-wiring) spanning partial-domain, boundary x3, control-flow-effect, ungrounded-oracle echo, role reversal, double transfer, both single-pass A-leg amputations, the pass-ORDER swap, cross-wiring, an ungrounded destination fallback, and the re-encoded prepatch bug; all ran to completion with no unresolved timeouts. Positive control verifies with clean axioms; prepatch reproduced and rejected (with a discriminating machine-checked witness). Every one of the 11 rejections is backed by a machine-proved negation rather than by a failed tactic. Both impls that verify with clean axioms had faithful patches materialized and RESOLVED under the official harness, and the oracle demonstrably rejects in the other direction. Above all, the spec is machine-proved to admit exactly one function up to pointwise equality, so no wrong impl with a closing clean-axiom proof can exist => verify⇏correct is NOT broken on this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_prepatch.lean`, `atk_partial_domain.lean`, `atk_two_state.lean`, `atk_observed_only.lean`, `atk_ownentry_only.lean`, `atk_order_swapped.lean`, `atk_wrapped_false.lean`, `atk_selfsuff_from_source.lean`, `atk_reversed.lean`, `atk_module_fallback.lean`, `atk_crosswired.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo_literal.lean`, `atk_double.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no counterexample exists, and this is a THEOREM rather than the outcome of a finite search. determinacy.lean (lean_verify exit=0, `#print axioms spec_is_functionally_determined` => "does not depend on any axioms") machine-proves `spec_is_functionally_determined : ∀ impl, problem_spec_total_attachIdentity impl → ∀ source, impl source = implementation_attachIdentity source`. The postcondition pins ALL EIGHT leaves of `CallableAttrs` (name/module/qualname × {observed, ownEntry}, plus `wrapped` and `selfSufficient` — that is every field of the record) to CLOSED functions of `source`, and `callable_ext` cashes that into record equality. So the frozen spec admits exactly ONE function up to pointwise equality: no same-spec impl can verify and differ from gold anywhere in the domain. The two attacks that DO verify are proved equal to gold in the same file (`echo_equals_gold`, `double_equals_gold`, both axiom-clean), and both RESOLVE under the official harness, as required.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_two_state.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_observed_only.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_ownentry_only.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_order_swapped.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_wrapped_false.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_selfsuff_from_source.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_reversed.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_module_fallback.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_crosswired.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_echo_literal.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_double.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a callable that carries identity metadata.

A callable carries a bundle of identity attributes (a human-readable name, the
defining module, and a qualified name), and it may record that it transparently
stands in for another callable. Separately from that metadata, a callable is
either self-sufficient — a caller runs it supplying only the arguments of the call
itself — or it still expects the object it belongs to to be handed in first.

Each identity attribute of a callable sits at TWO layers. The callable's own
attribute table may hold an entry for it, and the kind of thing the callable is may
answer for it as well; which of the two a reader of the attribute is answered from
depends on the callable. So what the callable's own table holds and what a reader
observes are two separate facts about it, and they need not agree.

A freshly synthesised callable holds nothing in its own table, and the
general-purpose machinery it is built out of answers for none of these attributes
either, so a reader of any of them observes nothing at all. It is nonetheless
self-sufficient: the object it acts for is already built into it. When such a
callable is meant to act on behalf of an existing one, the existing callable's
identity is transferred onto it — in two
passes, attribute by attribute from what a reader observes on the original, and
then the original's own table laid over the synthesised callable's table as a
whole — so that downstream code inspecting the synthesised callable observes the
original identity; and the callable handed back is still the self-sufficient one,
because callers go on to run it with the arguments of the call alone.

How much identity the original holds, and at which of its layers, is not assumed.
A plain function is observed to hold all three attributes while its own table holds
none of them; a callable that keeps its identity in its own table may hold entries
for only some of them, may hold an entry whose content is nothing in particular,
and may hold an entry that disagrees with what a reader of it observes. The
required behavior is claimed of every callable the step can be handed.
-/

-- axioms-start
-- No opaque callees are consumed: the metadata transfer is modeled deeply in the
-- `pure` region (see `copyIdentity`), so the corresponding library routine is an
-- A-reference validated by axiom_check.py rather than a consumed axiom.
-- axioms-end

-- pure-start
/-- What is held for one identity attribute at one layer.

A layer either holds no entry at all for an attribute, or holds one. When it holds
one, the entry's content need not be text: an entry whose content is nothing in
particular is perfectly ordinary. So `vacant` (no entry) and `filled none` (an
entry holding nothing in particular) are DISTINCT states, and both are distinct
from `filled (some s)` (an entry holding the text `s`). The distinction is
load-bearing: it is presence of the entry, not textual content, that decides
whether this entry is the one handed on when identity is transferred. -/
inductive AttrSlot where
  | vacant
  | filled (content : Option String)
  deriving DecidableEq, Repr

/-- The entry that survives when `src`'s layer is laid over `dst`'s: `src`'s entry
whenever `src` holds one — content and all, whatever that content is — and
otherwise the entry `dst` already held. Holding an entry is what wins here; what
the entry contains is carried along but never consulted. -/
def AttrSlot.overlay : AttrSlot → AttrSlot → AttrSlot
  | .vacant,   dst => dst
  | .filled c, _   => .filled c

/-- One identity attribute of a callable, at both of its layers.

`observed` is what a reader of that attribute on this callable is answered with,
and is `vacant` when the callable has no such attribute at all. `ownEntry` is what
the callable's OWN attribute table holds for it, and is `vacant` when its table
holds no entry for it, in which case a reader is answered by the kind of thing the
callable is.

The two layers can disagree: the kind of thing a callable is may answer for an
attribute ahead of the callable's own table, and then the table's entry is not what
a reader observes — while it is still the entry that table hands on when the table
as a whole is laid over another callable's. For a callable whose readers are
answered from its own table first — which is the case for a freshly synthesised
one — `observed` is `ownEntry` laid over whatever its kind answers for. -/
structure IdentityAttr where
  observed : AttrSlot
  ownEntry : AttrSlot
  deriving DecidableEq, Repr

/-- The identity metadata a callable carries, together with how it can be run.

Each of the three textual fields is one identity attribute at both of its layers
(see `IdentityAttr`). `wrapped` records whether the callable transparently
delegates to another callable. `selfSufficient` records whether a caller can run
the callable supplying only the arguments of the call itself; a callable that still
expects the object it belongs to to be handed in first is not self-sufficient. -/
structure CallableAttrs where
  name           : IdentityAttr
  module         : IdentityAttr
  qualname       : IdentityAttr
  wrapped        : Bool
  selfSufficient : Bool
  deriving DecidableEq, Repr

/-- A freshly synthesised callable. Its own table holds nothing at all, and the
general-purpose machinery it is made of answers for none of the three attributes
either — so a reader of any of them observes nothing, which is precisely the
identity such a callable lacks. It does not yet delegate to any other callable. It
is self-sufficient: the object it acts for is already built into it, so a caller
runs it with the arguments of the call alone. -/
def bareCallable : CallableAttrs :=
  { name     := { observed := .vacant, ownEntry := .vacant },
    module   := { observed := .vacant, ownEntry := .vacant },
    qualname := { observed := .vacant, ownEntry := .vacant },
    wrapped := false, selfSufficient := true }

/-- Transfer onto `dst` the identity `src` supplies for ONE attribute, in the two
passes the transfer really makes. First the attribute is placed on `dst` from what
a reader observes on `src`, and nothing is placed when `src` has no such attribute.
Then `src`'s own table entry is laid over that placement, so `src`'s table entry is
the one that survives whenever its table holds one. Both passes write to `dst`'s
own table, and what `dst` is then observed to hold is that table's new entry laid
over whatever `dst`'s kind already answered for. -/
def IdentityAttr.transfer (src dst : IdentityAttr) : IdentityAttr :=
  let entry := src.ownEntry.overlay (src.observed.overlay dst.ownEntry)
  { observed := entry.overlay dst.observed, ownEntry := entry }

/-- Transfer onto `dst` the identity that `src` supplies. Each of the three
attributes is transferred as `IdentityAttr.transfer` describes. After the transfer,
`dst` is recorded as delegating to `src`. The transfer concerns identity only: the
callable handed back is `dst`, so how it can be run stays `dst`'s and is unaffected
by `src`. -/
def copyIdentity (src dst : CallableAttrs) : CallableAttrs :=
  { name           := src.name.transfer dst.name,
    module         := src.module.transfer dst.module,
    qualname       := src.qualname.transfer dst.qualname,
    wrapped        := true,
    selfSufficient := dst.selfSufficient }

/-- The entry a callable whose own table starts out empty ends up holding in that
table for one identity attribute of `src`, once `src`'s identity has been
transferred onto it: `src`'s own table entry whenever `src`'s table holds one — the
same content, whatever that content is — and otherwise what a reader observes on
`src`. Both of `src`'s layers are consulted, and the table layer is the one that
survives, because the table is laid over as a whole after the per-attribute pass
has run. -/
def transferredEntry (src : IdentityAttr) : AttrSlot :=
  src.ownEntry.overlay src.observed
-- pure-end

-- pre-conditions-start
/-- Admissibility: none. The step is defined for every callable it can be handed,
whatever entries that callable holds at either layer and however the callable itself
has to be run. In particular a callable holding entries for only some of the three
attributes is admissible; so is one holding an entry whose content is nothing in
particular; so is one whose own table holds an entry that disagrees with what a
reader of it observes; and so is one that is not runnable on its own until the
object it belongs to is handed in. The claim below is therefore made over the whole
domain rather than over a distinguished part of it. -/
def problem_pre_attachIdentity (_source : CallableAttrs) : Prop := True
-- pre-conditions-end

-- post-conditions-start
/-- The callable bound to act on behalf of `source` must expose `source`'s
identity.

For each identity attribute, the entry the result holds in its OWN table is the
entry `source`'s own table holds whenever `source`'s table holds one — the same
content, whatever that content is, and in particular an entry holding nothing in
particular is handed on as such rather than being treated as no entry at all — and
otherwise what a reader observes on `source`. Where `source` supplies nothing at
either layer, the result's table is left as empty of that attribute as the freshly
synthesised callable's was.

What a reader OBSERVES on the result follows from that table, because what is
handed back is the synthesised callable: its readers are answered from its own
table, and the machinery it is made of answers for none of the three attributes on
its own account. So for each of the three a reader observes exactly the transferred
entry — each is held exactly when `source` supplies it at one of its layers, with
the same content, and none is held at all when `source` supplies nothing. The
result is recorded as delegating to `source`.

Carrying that identity must not cost the result its usability: the result is
self-sufficient, so a caller runs it with the arguments of the call alone rather
than having to hand in the object `source` belongs to. This holds no matter how
`source` itself has to be run, because what is handed back is the synthesised
callable wearing `source`'s identity and never `source`. -/
def problem_spec_attachIdentity (source : CallableAttrs) (result : CallableAttrs) : Prop :=
  result.name.ownEntry = transferredEntry source.name ∧
  result.name.observed = transferredEntry source.name ∧
  result.module.ownEntry = transferredEntry source.module ∧
  result.module.observed = transferredEntry source.module ∧
  result.qualname.ownEntry = transferredEntry source.qualname ∧
  result.qualname.observed = transferredEntry source.qualname ∧
  result.wrapped = true ∧
  result.selfSufficient = true

/-- The obligation: the required behavior holds at EVERY admissible callable.
Stating the quantifier and the admissibility condition here, rather than leaving
them to the proof, is what makes the domain of the claim part of the
specification instead of an artifact of how it happens to be proved. -/
def problem_spec_total_attachIdentity (impl : CallableAttrs → CallableAttrs) : Prop :=
  ∀ source, problem_pre_attachIdentity source →
    problem_spec_attachIdentity source (impl source)
-- post-conditions-end

-- impl-start
-- Build the callable that acts on behalf of `source`: start from a freshly
-- synthesised callable, which holds no identity of its own at either of its
-- layers, then transfer `source`'s identity onto it.
def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do
  let mut bound : CallableAttrs := bareCallable
  bound := copyIdentity source bound
  return bound
-- impl-end

-- proof-start
theorem correct_attachIdentity :
    problem_spec_total_attachIdentity implementation_attachIdentity := by
  intro source _
  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity
    IdentityAttr.transfer transferredEntry bareCallable
  simp only [Id.run]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩
  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl
  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl
  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-14787 lean bundle. Scratch: (worktree at base_commit 004b4620f6 under./wt). VERDICT: SOUND — and stronger than the gate requires: the spec is machine-proved functionally determined, so verify⇒extensionally-gold is a theorem here, not a survived search.

**SAME-SPEC:** all 13 attacks + positive control are byte-identical in spec — swebench_unified.markers.same_spec(gold, atk, lean) == True for every one (13/13, 0 failures). Only the impl+proof regions were edited.

### VERIFY COMMANDS (`bash scripts/lean_verify.sh $S/<f>.lean` from repo root; run concurrently in batches of 4):
  atk_pos                   exit=0 VERIFIES  <- positive control (gold impl+proof verbatim)
  atk_prepatch              exit=1 REJECTED  the real pre-patch bug (return bareCallable, no transfer)
  atk_partial_domain        exit=1 REJECTED  partial-domain (gold only where qualname is supplied)
  atk_two_state             exit=1 REJECTED  boundary: two-state collapse (held-but-None == absent)
  atk_observed_only         exit=1 REJECTED  A-LEG amputation: callee step (i) only, no `__dict__` merge
  atk_ownentry_only         exit=1 REJECTED  A-LEG amputation: callee step (ii) only, no assigned pass
  atk_order_swapped         exit=1 REJECTED  A-LEG pass ORDER swapped (observed laid over table) [NEW this pass]
  atk_wrapped_false         exit=1 REJECTED  boundary: callee step (iii) dropped (`__wrapped__` never set)
  atk_selfsuff_from_source  exit=1 REJECTED  control-flow-effect: call shape taken from SOURCE (= wraps(method)(method))
  atk_reversed              exit=1 REJECTED  role reversal: copyIdentity bound source
  atk_module_fallback       exit=1 REJECTED  ungrounded destination fallback ('functools' observed module)
  atk_crosswired            exit=1 REJECTED  cross-wiring: qualname served from the name entry [NEW this pass]
  atk_echo_literal          exit=0 VERIFIES  ungrounded-oracle echo (postcondition as a record literal)
  atk_double                exit=0 VERIFIES  transfer run TWICE (extensionally gold; overlay is idempotent)

TACTIC-WEAKNESS DISCIPLINE — this is where a rubber-stamp would have mis-scored. Several exit=1 residuals showed UNREDUCED `pure`/`copyIdentity` terms (e.g. atk_wrapped_false is semantically wrong ONLY in the `wrapped` leg, yet its metadata legs also failed), which is the signature of a weak closer, not of semantics. I therefore did NOT accept exit=1 as evidence. wit_all.lean (lean_verify exit=0, ZERO errors) machine-proves, for ALL ELEVEN rejected attacks, BOTH:
  (a) `¬ problem_spec_total_attachIdentity impl_<t>` — a genuine semantic violation, discharged by `decide` on a concrete admissible source, so it cannot be a tactic artifact; and
  (b) `problem_spec_attachIdentity <src> (impl_gold <src>)` — gold SATISFIES that very input, so each witness DISCRIMINATES rather than being an input the spec rejects for everyone.
Witness sources used: src_plain, src_disagree (layers disagree), src_nonecontent (held-but-None), src_nomodule (object.`__init__` shape), src_unbound (not runnable without its instance), src_noqual. All admissible (precondition is `True`).

AXIOMS (files ax_*.lean, `#print axioms correct_attachIdentity` appended, exit=0 each): atk_pos, atk_echo_literal, atk_double all report "'correct_attachIdentity' does not depend on any axioms" — clean, no sorryAx. (One earlier determinacy draft leaked `sorryAx` through a `simp_all`; I caught it via #print axioms and re-proved honestly via structure eta — recorded because it is exactly the failure mode a lazy pass ships.)

MANDATORY RESOLVE RUNS — every impl that verifies with clean axioms had its faithful patch materialized against the real worktree (`git apply --check` rc=0 for each) and RUN through the official harness (swebench_unified.harness.run_resolve), launched concurrently:
  gold             patch_gold.diff             -> resolved=True  completed=True 'resolved'  (accept-direction control)
  atk_echo_literal patch_atk_echo_literal.diff -> resolved=True  completed=True 'resolved'
  atk_double       patch_atk_double.diff       -> resolved=True  completed=True 'resolved'
Both verifying impls RESOLVE, so neither is a spec weakness => NOT a G-EQ fail. Consistent with the determinacy theorem, which says they CANNOT be counterexamples.

ORACLE DISCRIMINATING POWER, both directions (so 'it resolved' is not vacuous):
  negctl      pre-patch behaviour retained, applies cleanly -> resolved=False completed=True (consistent, not flaky)
  wrongcallee wraps(method)(partial(lambda *a, **k: None)) -> resolved=False completed=True (consistent, not flaky)
The reject lane fires, so the three resolved=True verdicts carry information.

COARSENESS PROBE (sharpest remaining lever: CallableAttrs names no carrier for `__doc__`/`__annotations__`/the rest of `__dict__`, and `wrapped: Bool` records only PRESENCE of `__wrapped__`, not its value). patch_atk_coarse.diff realizes the eight pinned components identically to gold while setting `__doc__`=None, `__annotations__`=garbage, `__wrapped__`='not-the-method', and performing NO `__dict__` merge => run_resolve: resolved=True completed=True. So the unmodeled facets are not load-bearing for this instance's F2P/P2P — consistent with the suite: the only `__doc__` assertion (test_preserve_attributes, tests/decorators/tests.py:271) reads Test.method.`__doc__` on the OUTER `_wrapper`, which the untouched update_wrapper(`_wrapper`, method) at decorators.py:48 still sets. Modeling boundary is adequate, not merely convenient.

A-LEG AUDIT (the focus of this role). refinement.md legs: 1,2 = R; 3 = A-reference; 4 = I. NO kind-3 leg, no A-consumed leg, no opaque callee — consistent with meta.json axioms=[] / opaque_callees=[] and with the clean `#print axioms`. The single A-leg (leg 3, `copyIdentity` == functools.update_wrapper) was re-derived step by step AGAINST THE REAL INTERPRETER in the environment of record (instance image, conda testbed, CPython 3.9.20, via docker_exec.run_in_container with the gold patch applied; probe.py, rc=0):

  A. fresh partial observed [`__name__`,`__module__`,`__qualname__`] = ABSENT/ABSENT/ABSENT, `__dict__` == {}  => bareCallable (all vacant at BOTH layers) FAITHFUL

  B. table-transparent on all three (a `__dict__` entry is what getattr answers) = True/True/True     => the `observed:= entry.overlay dst.observed` leg is right

  C. source observed=('held','g') vs table=('held','FROM_TABLE'); result `__name__` == 'FROM_TABLE'    => ownEntry WINS; `transferredEntry = ownEntry.overlay observed` is the RIGHT ORDER, not the reverse (this is the leg atk_order_swapped attacks, and the spec rejects it)

  D. held-but-None `__module__` copied VERBATIM = ('held', None)                                       => three-state AttrSlot REQUIRED; a two-state Option String would be unfaithful (atk_two_state, rejected)

  E. `__wrapped__` beats a bogus source-table `__wrapped__` key = True                                   => `wrapped:= true` faithful (written last)

  F. update_wrapper returns its WRAPPER (is-identity) = True                                         => `selfSufficient:= dst.selfSufficient` faithful

  G. unbound method self_sufficient=False | bound+partial=True | after update_wrapper=True           => the usability leg is non-trivial and correctly oriented
All six match the model. I attacked BOTH halves of the A-leg separately (atk_observed_only drops step ii, atk_ownentry_only drops step i) AND the composition order (atk_order_swapped); the spec rejects all three with machine-proved witnesses, so both passes and their order are genuinely pinned rather than one being decorative.

ENVIRONMENT TRAP (recorded so it is not later mis-read as a defect): the bareCallable carrier fact is interpreter-dependent. On the audit HOST (CPython 3.10.20) a fresh functools.partial DOES answer `__module__` == 'functools'; the instance image pins 3.9.20, where it does not. The shipped bareCallable is exact FOR THE PINNED INTERPRETER, and mapping.md's 'Environment of record' section pins it explicitly. I encoded the 3.10 behaviour as an attack anyway (atk_module_fallback) and the spec REJECTS it — correctly, since that fallback is false of this instance's interpreter.

**DOC NOTE:** the prior pass's doc defect #1 (mapping.md claiming bareCallable observes 'functools', and a `synthesisedModule` constant) is REPAIRED in the current bytes — mapping.md line 40 now states all three vacant at both layers, and grep finds zero `synthesisedModule` in Solution.lean. No outstanding doc defect that could mask a weakness.

**WHY SOUND:** 13 same-spec admissible attacks (>=5 required, 2 of them new this pass: the A-leg pass-order swap and the cross-wiring) spanning partial-domain, boundary x3, control-flow-effect, ungrounded-oracle echo, role reversal, double transfer, both single-pass A-leg amputations, the pass-ORDER swap, cross-wiring, an ungrounded destination fallback, and the re-encoded prepatch bug; all ran to completion with no unresolved timeouts. Positive control verifies with clean axioms; prepatch reproduced and rejected (with a discriminating machine-checked witness). Every one of the 11 rejections is backed by a machine-proved negation rather than by a failed tactic. Both impls that verify with clean axioms had faithful patches materialized and RESOLVED under the official harness, and the oracle demonstrably rejects in the other direction. Above all, the spec is machine-proved to admit exactly one function up to pointwise equality, so no wrong impl with a closing clean-axiom proof can exist => verify⇏correct is NOT broken on this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL(2) faithfulness-break, django__django-14787. Modeled function = the `bound_method` construction line inside `_multi_decorate._wrapper` (django/utils/decorators.py:40). Reference = base_commit 4bfcf5195a (image /testbed) WITH patch.diff applied: `bound_method = wraps(method)(partial(method.__get__(self, type(self))))`. Reference interpreter = the instance image's conda `testbed` env, CPython 3.9.20 (NOT the host 3.10.20 — mapping.md's `Environment of record` section pins this and I honored it; the host interpreter answers `'functools'` for `partial().__module__`, which would have produced a bogus over-strength finding against `bareCallable.module`).

WHAT I TRIED TO BREAK, AND HOW IT HELD:

(1) EXHAUSTIVE differential test of the modeled step against the real `functools.update_wrapper` in the reference interpreter. I transcribed the Lean model (`AttrSlot.overlay`/`IdentityAttr.transfer`/`transferredEntry`/`copyIdentity`) into Python and built REAL source objects whose two attribute layers are INDEPENDENT (a `__getattribute__` override supplies the `observed` layer; the instance `__dict__` supplies `ownEntry`), then ran the actual post-patch expression `wraps(src)(partial(...))` on all 4 x 4 states (vacant / filled None / filled 'S' / filled 'T') at both layers of all three attributes = 4096 inputs, of which 4032 have layers that DISAGREE. I verified each constructed source really realizes its intended layer state before comparing (unrealizable = 0). Result: 4096 inputs, 0 divergences on all eight pinned components (both layers of all three attrs + `wrapped` + `selfSufficient`).

(2) The ORDER claim — the crux of the spec, and the most likely place to find drift. `transferredEntry = src.ownEntry.overlay src.observed` asserts the `__dict__` merge pass wins over the per-attribute `setattr` pass. This is only observable where the source's layers differ, and it is exactly where a lazier model would be wrong. Confirmed on all 4032 layer-disagreeing inputs. I also proved in Lean that the spec REJECTS the observed-layer-only rival (`implementation_observed_only`) at source name = {observed:= filled "slot", ownEntry:= filled "dict"} — so the clause carries content rather than being satisfiable either way.

(3) The carrier facts the spec rests on, MEASURED in the reference interpreter rather than taken from the docs: a fresh `functools.partial` is vacant at BOTH layers for all of `__name__`/`__module__`/`__qualname__` (all three `getattr` raise AttributeError, `__dict__` empty) — so `bareCallable` is exact; and the destination is TABLE-TRANSPARENT (`p.__dict__['__name__']='X'` ⇒ `p.__name__ == 'X'`), which is what licenses `observed:= entry.overlay dst.observed` and makes both passes land in the same storage. Both hold at 3.9.20.

(4) END-TO-END through the PUBLIC api (`method_decorator` → `_multi_decorate` → the patched line), capturing the real `bound_method` handed to a user decorator, on 7 real-object sources: plain function; `__dict__`-shadowed function (layers disagree); `__module__ = None` (the held-but-None state a two-state carrier would collapse); a STACKED method that has already been through this file's own `_update_method_wrapper` + `update_wrapper` pair (the two-layer source the repo itself produces); a source carrying a bogus `__wrapped__` in its own `__dict__` (checks that step (iii) writes last); `object.__init__` (no `__dict__` at all, module vacant at both layers ⇒ spec predicts the result's `__module__` raises AttributeError, and it does); and an unbound class method (`selfSufficient` false on the SOURCE ⇒ spec still claims true on the RESULT, and the real result is callable). All 7 agree with the postcondition. Plus an exhaustive public-API sweep over the reachable subdomain: 1296 inputs, 1260 layer-disagreeing, 0 divergences.

(5) ONE apparent domain gap, examined and dismissed as NOT over-strength. Driving the full 4096-state grid through the public API dies with `TypeError: __qualname__ must be set to a string` for the `filled none` state on `__name__`/`__qualname__`. That failure occurs at decorators.py:49 (`update_wrapper(_wrapper, method)`, whose destination is a FUNCTION, which type-checks those two slots) — i.e. OUTSIDE the modeled step, before it is ever reached. Within the modeled step itself the state is fine and the spec is TRUE there: the destination is a `partial`, whose table accepts anything (I confirmed own `__name__` = None, 42, and a bare `object()` all transfer verbatim). So the spec is not claiming something false at an unreachable input; it is total over a domain on which it was verified. `AttrSlot`'s `content: Option String` restricts modeled values to str-or-None, which narrows the domain rather than strengthening the claim.

(6) Spec-strength legs that could have been echoes of the gold expression, checked to be genuine claims: `selfSufficient = true` is not a restatement — an ALTERNATIVE construction (`implementation_alt`, a plain record literal built from `ownEntry.overlay observed`, taking no route through `copyIdentity`/`bareCallable`) satisfies `problem_spec_total_attachIdentity` by `rfl`, which I verified in Lean. That positive control also establishes the spec is SATISFIABLE, so the two rejection proofs below are non-vacuous rather than artifacts of an unsatisfiable postcondition (my standing concern about guarded/negative obligations verifying while proving nothing).

(7) Mechanical gates. `scripts/lean_verify.sh Solution.lean` exit 0. `#print axioms` on `correct_attachIdentity`, `implementation_attachIdentity`, `problem_spec_attachIdentity`, `copyIdentity`, `transferredEntry`: all report `does not depend on any axioms` — no sorryAx, and the refinement's claim of NO consumed axiom / no opaque callee is accurate (the transfer is modeled deeply, so `functools.update_wrapper` is an A-reference, which is exactly what leg (1) above independently re-validated rather than trusting axiom_check.py).

(8) `markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True` — spec region byte-identical across the pair (spec_signature sha256[:16] = 58228105613d2e9a); the prepatch file differs only in impl (returns `bareCallable`) and carries `sorry`. I independently proved in Lean that the spec rejects that prepatch impl (`¬ problem_spec_total_attachIdentity implementation_pre`, witness: source name observed = filled "f"), so the discrimination is real and not just an unclosable proof.

(9) Repo-level ground truth: `tests/runtests.py decorators.tests.DecoratorsTest.test_wrapper_assignments` FAILS at base and the full `decorators` suite (20 tests) passes with the gold line applied — the F2P observable matches the clause the spec discriminates at (the name attribute absent at both layers pre-patch).

**CONCLUSION:** no input found on which the modeled function disagrees with the real post-patch callee, across 4096 exhaustive states of the modeled domain, 1296 exhaustive public-API states, and 7 hand-built real-object edge cases including the no-`__dict__`, held-but-None, bogus-`__wrapped__`, and stacked-decorator sources. The spec is neither over-strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction), django__django-14787 lean. Gold edit: one line, django/utils/decorators.py:40 in `_multi_decorate`.`_wrapper`, `partial(method.__get__(self, type(self)))` -> `wraps(method)(partial(...))`. VERDICT NO-LEAKAGE on my own re-measurement of the current bytes.

NO RELAXATION IN THIS BUNDLE, verified not assumed. `find` for '*RELAX*' over the whole instance dir returns nothing (only verdict/refinement/mapping/requirements.md files across the four backends), and meta.json has NO `relaxed_leakage` key -- I enumerated top-level keys: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins, and grepped every key path for 'relax'/'leak' (only hit: gates/G-LEAK). So there was no unavoidability argument to re-derive and no facet-limited disposition to inherit; this is a straight full-strength leakage judgement, not a relaxation acceptance.

(1) SPEC-REGION INTEGRITY, measured myself. Built the lean backend via swebench_unified.backends.registry.get_backend('lean') and called markers directly: same_spec(Solution.lean, Solution_prepatch.lean) = True. Per-region hashes: axioms 26c4e834cff2, pure a336953bc5cf, pre-conditions cf9c2c047cf8, post-conditions fa40f044ea3b all SAME across pre/post; only impl and proof differ. markers.region_hashes(Solution.lean) == meta.json['region_hashes'] exactly, all 7 keys OK. spec_view sha256 = 99dfe9169021eecf66bb879dd0099ba3b411dfa83493ae33a0d98e5a1ec0bbea, matching the G-HYGIENE/G-LEAK record. The exposed view is therefore INVARIANT across the pre- and post-patch impls and cannot discriminate the edit by construction.

(2) THE DISCRIMINATOR IS LOAD-BEARING AND THE PROOF IS REAL -- I ran the strip test rather than trusting G-DIFF. scripts/lean_verify.sh on Solution.lean (mktemp dir) exits 0; with `#print axioms correct_attachIdentity` appended it prints "'correct_attachIdentity' does not depend on any axioms" -- no sorryAx, so the closed theorem is genuine. Solution_prepatch.lean exits 3 ("declaration uses 'sorry'"). Because a bare `sorry` is only WEAK evidence of rejection (it shows unproven, not unprovable), I strengthened it: I authored Refute.lean keeping the prepatch spec regions byte-identical and replacing the sorry with `theorem prepatch_refuted: ¬ problem_spec_total_attachIdentity implementation_attachIdentity`, discharged at source = {name:= {observed:= filled (some "m"), ownEntry:= vacant},...}. It COMPILES, exit 0. So the spec provably REFUTES the pre-patch impl -- the spec-view clauses are load-bearing against the PRE-patch impl, which is exactly the condition under which naming the transfer behavior is faithful rather than gratuitous. meta.axioms == [] and opaque_callees == [] are consistent with the deep `copyIdentity` model.

(3) ELISION CONFIRMED. The view's tail is `-- implementation elided — supplied by the consumer` / `-- proof elided — supplied by the consumer`. The gold-shaped construction `copyIdentity source bareCallable` appears ONLY inside the elided impl region, never in the view.

(4) MECHANICAL SCREEN, run by me, with POSITIVE CONTROLS. I first confirmed patch.diff == instance.json['patch'] byte-for-byte (sha 96d2dfb54416) so the screen ran against the real gold. leakage.screen(Solution.lean, lean, gold, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. NOT VACUOUS -- 3 of 4 injections into the shipped file fire: gold line `bound_method = wraps(method)(partial(...))` -> "L1: gold-patch line reproduced"; `django/utils/decorators.py` -> "L2: patched file path"; "This fixes the bug where... previously missing" -> "L3: narration 'fixes'". IMPORTANT CAVEAT I record rather than gloss: my fourth control, a comment reading "copies `__name__`, `__module__`, `__qualname__` via functools.wraps", PASSED the screen (passed=True). So the screen does NOT catch raw attribute/stdlib vocabulary, and the clean screen alone would not have settled my facet -- the hand sweep in (5) is what does, and I ran it because of this gap.

(5) VOCABULARY SWEEP of the spec view by hand (210 lines), since (4) proved the screen blind to it. ABSENT: wraps, functools, update_wrapper, partial, `__name__`, `__module__`, `__qualname__`, `__wrapped__`, `__dict__`, getattr, setattr, method_decorator, `_multi_decorate`, bound_method, decorators.py, django, and even the substring 'decorat'. re.findall over quoted spans returns [] -- the view contains ZERO string literals, so no 'functools' or attribute-name constant survives anywhere.

(This also confirms the bundle no longer carries the `synthesisedModule:= "functools"` literal that its own verdict.md records from an earlier revision -- my literal scan finds none, so I did not inherit that history either.) Test-patch terms absent too: test_wrapper_assignments, 'wrapper assignments', func_name, func_module, assertEqual, hello_world, logger, nonlocal. hints_text is EMPTY (len 0) for this instance, so the never-screen-against-hints rule is moot here. Narration sweep clean: no previously / used to / no longer / fixed / bug / regress / was not / incorrect.

The only 'instead' hit is "specification instead of an artifact of how it happens to be proved" (about proof structure); the only 'copy' hits are the identifier `copyIdentity`; 'after the' hits describe the two-pass ORDER of the transfer, not a before/after-patch framing.

(6) PROBLEM-STATEMENT COVERAGE -- I traced every spec-view facet to public text, and the view is strictly MORE abstract than the statement. The public problem_statement titles itself "method_decorator() should preserve wrapper assignments", states "the function that is passed to the decorator is a partial object and does not have any of the attributes expected from a function i.e. `__name__`, `__module__` etc...", prints "AttributeError: 'functools.partial' object has no attribute '`__name__`'", and its own repro already uses @wraps(func). So publicly visible: the entry point, the pre-state (a synthesised callable observing none of these attributes), the required post-state (it must carry the original's identity), and functools' own vocabulary.

The view's "a freshly synthesised callable holds nothing in its own table... a reader of any of them observes nothing at all" is an abstracted restatement of that public pre-state sentence, naming neither partial nor any attribute. `qualname` falls under the statement's explicit "etc...". The two-layer (observed vs ownEntry) model and the overlay ORDER (ownEntry laid over observed) encode stdlib update_wrapper's assigned/updated pass semantics -- WHAT must hold of the result, never which line to touch or which call to insert; they are also derivable from the public @wraps in the repro, and a solver must still discover the routine and the site. `wrapped = true` and `selfSufficient = true` are required post-state consequences / spec-strength postconditions of the kind G-PANEL-1 demands be stated; stating a required postcondition is not disclosing an edit.

(7) NO FILE IN THIS BUNDLE ADDRESSES ME. leakage.reviewer_directed() is clean ([]) on all of Solution.lean, refinement.md, mapping.md, meta.json, verdict.md, patch.diff and instance.json -- nothing prescribes a verdict, tells me how to record, or argues which verdict is honest. I checked this explicitly because it would be a finding in its own right; there is none. I also did NOT inherit verdict.md's stored panel-3 prose (which is a prior run's text, and is internally stale -- it asserts G-PANEL-2 is fail/UNFAITHFUL whereas current meta records G-PANEL-2 pass); every number above is my own measurement of the current bytes.

OUT-OF-FACET FLAGS (recorded, not re-dispositioning anything). G-EQ fail and G-PANEL-1 fail both carry detail "the audit role did not run); only 0 admissible attacks of 0 submitted" -- an agent-launch/saturation outage recorded as a gate verdict, not a measured spec weakness, and not mine to re-judge. Neither touches leakage in either direction: a spec-too-weak or too-strong dispute is orthogonal to whether the view discloses the edit. The core gates my facet actually leans on I reproduced directly and they are SOUND: region invariance (1), genuine closed proof with clean axioms and a compiling refutation of the prepatch (2), elision (3), non-vacuous screen (4). G-VERIFY pass, G-MUT killed 3/3, G-INTEGRITY (instance.json byte-identical, additions-only) and patch_equals_gold True are consistent with what I measured.

**CONCLUSION:** the spec view is byte-identical across the pre/post impls, contains no gold-patch line, no patched file path, no repo/stdlib identifier, no string literal at all, and no change-narration; every facet it does expose is covered by the public problem_statement at equal or lower specificity, and the clauses are load-bearing (they provably refute the pre-patch impl). No line reconstructs the gold edit beyond the public statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
