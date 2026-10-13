# P2 adversarial audit — django__django-15554

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_first_cand.lean`, `atk_4_no_own_pref.lean`, `atk_5_no_filter_waiver.lean`, `atk_6_registry_effect.lean`, `atk_7_ignore_permission.lean`, `atk_8_append_not_store.lean`, `atk_11_store_reinsert.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9_oracle_echo.lean`, `atk_10_alt_shape.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no same-spec wrong impl with a closing clean-axiom proof has a faithful refined patch that fails to resolve. The two attacks whose proofs DO close (atk_9_oracle_echo, atk_10_alt_shape) are both extensionally EQUAL to the spec oracle `registrationOutcome` over a brute-forced 318,720-input domain, and each one's materialized faithful patch RESOLVED under the official harness on the first attempt: run_resolve('django__django-15554', <patch>) => {'resolved': True, 'completed': True, 'note': 'resolved', 'attempts': 1, 'flaky': False} for both (resolve_atk_9.json, resolve_atk_10.json). Notably atk_10's patch is NOT the gold text — it is an independent transliteration of atk_10's own single-comprehension Lean shape (`(reuse is None or a in reuse) and j.equals(join) and (reuse_with_filtered_relation or j == join)` in one comprehension, vs gold's two-branch if/else) — and it still resolves, which is evidence the spec's licensed implementation space maps onto genuinely-fixing code rather than onto a single syntactic echo. So verify=>correct holds on every closing impl found.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,21 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
-    if restrictedTraversal then some permittedAliases
-    else if multiValued then some permittedAliases
-    else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+    if multiValued then some permittedAliases else none
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
-      if registry.any (fun p => p.1 == freshAlias) then
-        registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
-      else
-        registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+    (freshAlias, registry ++ [(freshAlias, newJoin)])
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +206,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,35 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
-  let reuse : Option (List Alias) :=
-    if restrictedTraversal then some permittedAliases
-    else if multiValued then some permittedAliases
-    else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
-  if cands.isEmpty then
-    return (freshAlias,
+    : Alias × List (Alias × JoinKey) :=
+  if !restrictedTraversal then
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else
+    let reuse : Option (List Alias) :=
+      if restrictedTraversal then some permittedAliases
+      else if multiValued then some permittedAliases
+      else none
+    let cands : List Alias :=
+      registry.filterMap (fun p =>
+        let permitted : Bool := match reuse with
+          | none   => true
+          | some s => s.contains p.1
+        if permitted && p.2.base == newJoin.base
+                     && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
+    if cands.isEmpty then
+      (freshAlias,
+        if registry.any (fun p => p.1 == freshAlias) then
+          registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
+        else
+          registry ++ [(freshAlias, newJoin)])
+    else if cands.contains newJoinAlias then
+      (newJoinAlias, registry)
+    else
+      (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +220,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 3 — `atk_3_first_cand.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,28 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.headD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +213,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 4 — `atk_4_no_own_pref.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,26 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +211,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 5 — `atk_5_no_filter_waiver.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,28 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && p.2.filt == newJoin.filt then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +213,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 6 — `atk_6_registry_effect.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,29 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry ++ [(newJoinAlias, newJoin)])
+  else
+    (cands.getLastD freshAlias,
+      registry ++ [(cands.getLastD freshAlias, newJoin)])
 -- impl-end
 
 
@@ -225,24 +214,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 7 — `atk_7_ignore_permission.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,26 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := true
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +211,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 8 — `atk_8_append_not_store.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,24 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
-      if registry.any (fun p => p.1 == freshAlias) then
-        registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
-      else
-        registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+    (freshAlias, registry ++ [(freshAlias, newJoin)])
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +209,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 9 — `atk_11_store_reinsert.lean` → rejected (same spec, does not verify — good)

```diff
@@ -177,40 +177,25 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
-      if registry.any (fun p => p.1 == freshAlias) then
-        registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
-      else
-        registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+    (freshAlias,
+      (registry.filter (fun p => p.1 != freshAlias)) ++ [(freshAlias, newJoin)])
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +210,10 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
   simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
     chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
+  try rfl
+  try decide
   rfl
 
 -- proof-end
```

Attack 10 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -177,40 +177,9 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
-  let reuse : Option (List Alias) :=
-    if restrictedTraversal then some permittedAliases
-    else if multiValued then some permittedAliases
-    else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
-  if cands.isEmpty then
-    return (freshAlias,
-      if registry.any (fun p => p.1 == freshAlias) then
-        registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
-      else
-        registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+    : Alias × List (Alias × JoinKey) :=
+  registrationOutcome registry newJoin newJoinAlias freshAlias
+    permittedAliases multiValued restrictedTraversal
 -- impl-end
 
 
@@ -225,24 +194,6 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
-  simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
-    chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
   rfl
 
 -- proof-end
```

Attack 11 — `atk_10_alt_shape.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -177,40 +177,28 @@
     (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
     (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
     (multiValued : Bool) (restrictedTraversal : Bool)
-    : Alias × List (Alias × JoinKey) := Id.run do
-  -- The aliases permission is confined to, one circumstance at a time: a
-  -- traversal carrying a restriction of its own is governed by the supplied
-  -- set; a multi-valued traversal likewise; failing both, every registered
-  -- alias is permitted.
+    : Alias × List (Alias × JoinKey) :=
   let reuse : Option (List Alias) :=
     if restrictedTraversal then some permittedAliases
     else if multiValued then some permittedAliases
     else none
-  -- Collect the aliases that may be reused: permitted, on the same base
-  -- relation, and carrying the same filter tag — that last requirement waived
-  -- on a traversal carrying a restriction of its own.
-  let mut cands : List Alias := []
-  for p in registry do
-    let permitted : Bool := match reuse with
-      | none   => true
-      | some s => s.contains p.1
-    if permitted && p.2.base == newJoin.base
-                 && (restrictedTraversal || p.2.filt == newJoin.filt) then
-      cands := cands ++ [p.1]
-  -- None may be reused: allocate a fresh alias and STORE the new join under it
-  -- in the name-keyed registry — replacing in place any join already held under
-  -- that name, otherwise adding a last entry.
+  let cands : List Alias :=
+    registry.filterMap (fun p =>
+      let permitted : Bool := match reuse with
+        | none   => true
+        | some s => s.contains p.1
+      if permitted && p.2.base == newJoin.base
+                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
   if cands.isEmpty then
-    return (freshAlias,
+    (freshAlias,
       if registry.any (fun p => p.1 == freshAlias) then
         registry.map (fun p => if p.1 == freshAlias then (freshAlias, newJoin) else p)
       else
         registry ++ [(freshAlias, newJoin)])
-  -- An alias may be reused; the registry is unchanged. Prefer the new join's
-  -- own alias if it is itself among them, otherwise the most recent one.
-  if cands.contains newJoinAlias then
-    return (newJoinAlias, registry)
-  return (cands.getLastD freshAlias, registry)
+  else if cands.contains newJoinAlias then
+    (newJoinAlias, registry)
+  else
+    (cands.getLastD freshAlias, registry)
 -- impl-end
 
 
@@ -225,24 +213,6 @@
           permittedAliases multiValued restrictedTraversal) := by
   intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
     restrictedTraversal
-  have key : ∀ (pred : (Alias × JoinKey) → Bool) (l : List (Alias × JoinKey))
-      (acc : List Alias),
-      (forIn l acc (fun p r =>
-        (if pred p = true
-         then do pure PUnit.unit; pure (ForInStep.yield (r ++ [p.1]))
-         else do pure PUnit.unit; pure (ForInStep.yield r) : Id _)))
-      = pure (acc ++ l.filterMap (fun p =>
-          if pred p = true then some p.1 else none)) := by
-    intro pred l
-    induction l with
-    | nil => intro acc; simp
-    | cons hd tl ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filterMap_cons]
-      split <;> simp_all
-  simp only [problem_spec_addJoin, implementation_addJoin, registrationOutcome,
-    chooseAlias, matchCandidates, permittedReuse, eligible, registryStore]
-  rw [key _ registry []]
   rfl
 
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Mathlib
-- imports-end

/-!
Allocating a query alias when registering one join.

A query keeps an ordered registry of joins it has already introduced. Each
registered join is stored under a distinct **alias** (a name), together with a
key describing the join's shape.

The key has two parts:

  * a *base* part — the table, the parent it hangs off, and the relating field;
  * an optional *filter* tag — an extra condition attached to this particular
    join (two joins on the same base relation may carry different filter tags).

Registering a new join either reuses an alias the registry already holds or
allocates a fresh one. An already-registered alias may be reused only when all
three of the following hold of the join it stands for:

  * it is PERMITTED. Permission is governed by a set of aliases supplied with
    the registration whenever the traversal introducing the join is
    multi-valued, or is itself a traversal carrying a restriction of its own;
    failing both circumstances no supplied set governs permission at all and
    every registered alias is permitted;
  * it stands on the SAME BASE relation as the new join;
  * it carries the SAME FILTER tag as the new join — a requirement waived when
    the join is introduced while traversing a relation that carries a
    restriction of its own.

Allocation then proceeds as follows:

  * if one or more aliases may be reused the registry is left unchanged, and the
    alias reused is the new join's own alias when that is itself among them,
    otherwise the most recently registered one;
  * otherwise an alias is allocated and the new join is STORED IN THE REGISTRY
    UNDER IT. The registry is a name-keyed store, so a name holds at most one
    join: storing under a name the registry does not yet hold adds a last entry,
    while storing under a name it already holds replaces that entry's join where
    it already sits — the join that name held on entry is discarded and the
    order of names is unchanged. Nothing constrains the allocated name to be one
    the registry does not already hold.

The consequence that matters: two joins on the same base relation carrying
different filter tags each receive their OWN alias, never a single shared one.
A query attaching two differently-filtered joins to one relation therefore gets
a distinct join for each, rather than only the first with the other dropped.
-/

-- axioms-start
-- No unchanged outside callee contributes a property the specification consumes.
-- The reuse decision (which alias a freshly registered join lands on) and the
-- registry update are modeled DEEPLY over the data — the registry, the
-- permitted-reuse set, and the joins' keys — so there is no `opaque`/`axiom`
-- callee contract here.
-- axioms-end

-- pure-start
/-- An alias (a join name). Modeled as a `Nat` identity; only equality of
aliases is observed. -/
abbrev Alias := Nat

/-- The key of a registered join, restricted to the touched parts:
* `base` — the table / parent / relating-field shape (an injective encoding into
  `Nat`; only equality is observed);
* `filt` — an optional filter tag distinguishing two joins on the same base. -/
structure JoinKey where
  base : Nat
  filt : Option Nat
deriving DecidableEq, Repr

/-- The aliases permission is confined to, taken one circumstance at a time:
* on a traversal carrying a restriction of its own the supplied set governs
  permission;
* on a multi-valued traversal the supplied set likewise governs permission;
* failing both, no set governs (`none`) and every registered alias is
  permitted. -/
def permittedReuse (permittedAliases : List Alias)
    (multiValued restrictedTraversal : Bool) : Option (List Alias) :=
  if restrictedTraversal then some permittedAliases
  else if multiValued then some permittedAliases
  else none

/-- Whether one registered entry may be reused for `newJoin`. Three conditions,
all required:
* PERMISSION — `reuse` names the aliases permission is confined to (`none` =
  every registered alias is permitted);
* the SAME BASE relation;
* the SAME filter tag — waived when the join is introduced while traversing a
  relation that carries a restriction of its own, so where that waiver does not
  apply two joins sharing a base but carrying different filter tags may never be
  reused for one another. -/
def eligible (reuse : Option (List Alias)) (restrictedTraversal : Bool)
    (newJoin : JoinKey) (p : Alias × JoinKey) : Bool :=
  let permitted : Bool := match reuse with
    | none   => true
    | some s => s.contains p.1
  permitted && p.2.base == newJoin.base
            && (restrictedTraversal || p.2.filt == newJoin.filt)

/-- Storing `newJoin` in the registry under the name `a`.

The registry is a NAME-KEYED STORE: a name holds at most one join, so this is
not an unconditional append. Storing under a name the registry does not yet hold
adds a last entry; storing under a name it already holds REPLACES that entry's
join where it already sits, discarding the join that name held on entry and
leaving the order of names unchanged. Nothing constrains the name being
allocated to be one the registry does not already hold, so both cases occur. -/
def registryStore (registry : List (Alias × JoinKey)) (a : Alias) (k : JoinKey)
    : List (Alias × JoinKey) :=
  if registry.any (fun p => p.1 == a) then
    registry.map (fun p => if p.1 == a then (a, k) else p)
  else
    registry ++ [(a, k)]

/-- The aliases that may be reused, in registration order. -/
def matchCandidates (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (reuse : Option (List Alias)) (restrictedTraversal : Bool) : List Alias :=
  registry.filterMap (fun p =>
    if eligible reuse restrictedTraversal newJoin p then some p.1 else none)

/-- The allocation outcome for `newJoin` given the permitted-reuse set `reuse`.
`newJoinAlias` is the alias the new join already carries (its own name). When at
least one alias may be reused the registry is left unchanged and:
* if the new join's own alias is itself among them, it is reused (preferred);
* otherwise the most recently registered one is reused.
When none may be reused, `freshAlias` is allocated and the new join is STORED in
the registry under it (`registryStore`): a last entry when the registry does not
already hold that name, a replacement in place when it does. -/
def chooseAlias (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (reuse : Option (List Alias))
    (restrictedTraversal : Bool) : Alias × List (Alias × JoinKey) :=
  let cands := matchCandidates registry newJoin reuse restrictedTraversal
  if cands.isEmpty then
    (freshAlias, registryStore registry freshAlias newJoin)
  else if cands.contains newJoinAlias then
    (newJoinAlias, registry)
  else
    (cands.getLastD freshAlias, registry)

/-- The registration outcome, on EITHER governing regime: the permitted-reuse
set is `permittedReuse`. -/
def registrationOutcome (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued restrictedTraversal : Bool)
    : Alias × List (Alias × JoinKey) :=
  chooseAlias registry newJoin newJoinAlias freshAlias
    (permittedReuse permittedAliases multiValued restrictedTraversal)
    restrictedTraversal
-- pure-end

-- post-conditions-start
/-- The registration outcome for `newJoin`, on BOTH governing regimes.

`result` is exactly `registrationOutcome`: an already-registered alias may be
reused only when it is permitted, stands on the same base relation, and carries
the same filter tag — that last requirement waived where the join is introduced
while traversing a relation carrying a restriction of its own; permission is
governed by `permittedAliases` on such a traversal and on a multi-valued one,
and by nothing at all ("every alias") when neither circumstance holds. Among
the aliases that may be reused the new join's own alias wins if itself among
them, else the most recent one; the registry is left untouched whenever an alias
is reused, and otherwise the new join is STORED under the allocated name in the
name-keyed registry — a last entry when that name is not already held, a
replacement of the join held there, in place, when it is. -/
def problem_spec_addJoin
    (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued : Bool) (restrictedTraversal : Bool)
    (result : Alias × List (Alias × JoinKey)) : Prop :=
  result = registrationOutcome registry newJoin newJoinAlias freshAlias
             permittedAliases multiValued restrictedTraversal
-- post-conditions-end

-- impl-start
def implementation_addJoin
    (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued : Bool) (restrictedTraversal : Bool)
    : Alias × List (Alias × JoinKey) :=
  let reuse : Option (List Alias) :=
    if restrictedTraversal then some permittedAliases
    else if multiValued then some permittedAliases
    else none
  let cands : List Alias :=
    registry.filterMap (fun p =>
      let permitted : Bool := match reuse with
        | none   => true
        | some s => s.contains p.1
      if permitted && p.2.base == newJoin.base
                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
  if cands.isEmpty then
    (freshAlias, registryStore registry freshAlias newJoin)
  else if cands.contains newJoinAlias then
    (newJoinAlias, registry)
  else
    (cands.getLastD freshAlias, registry)
-- impl-end

-- proof-start
theorem correct_addJoin :
    ∀ (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
      (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
      (multiValued : Bool) (restrictedTraversal : Bool),
      problem_spec_addJoin registry newJoin newJoinAlias freshAlias
          permittedAliases multiValued restrictedTraversal
        (implementation_addJoin registry newJoin newJoinAlias freshAlias
          permittedAliases multiValued restrictedTraversal) := by
  intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
    restrictedTraversal
  rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-15554 / lean. VERDICT: SOUND. Assigned focus: the A legs and the model<->patch correspondence (R/I legs are G-CONF's).

**SPEC SHAPE.** `problem_spec_addJoin ... result := result = registrationOutcome registry newJoin newJoinAlias freshAlias permittedAliases multiValued restrictedTraversal` — an EXACT FUNCTIONAL EQUALITY against a total, computable oracle modeled deeply over the data (permittedReuse / eligible / matchCandidates / chooseAlias / registryStore). There is NO precondition: correct_addJoin quantifies over all of multiValued/restrictedTraversal, so behavior is pinned on the FULL domain, and any impl that verifies is extensionally the oracle. mapping.md:98-104 now states this correctly ('The spec/theorem is UNCONDITIONAL'), so the doc defect a prior pass recorded on this point has been REPAIRED in the shipped artifact.

A-LEG AUDIT (my focus). `grep -nE '^\s*(axiom|opaque)\b|sorry|admit|native_decide|Assume|Refute' Solution.lean` => NONE. meta.json: axioms=[], deep_model_references=[], conf_skip=false; gates.G-AX recorded skip, exit 0. axiom_check.py is a consistent skip stub. So there are ZERO A-consumed and ZERO A-reference legs, and no kind-3 leg can exist. This is the SOUND choice rather than an evasion: the only callee whose property the reuse decision genuinely depends on is `Join.equals`, and it is modeled INLINE (as the `base` comparison in `eligible`) rather than axiomatized — per SPEC_GUIDE a deeply-modeled changed op's callee must not become a consumed axiom. The two genuinely-unchanged callees contribute nothing the spec consumes: `table_alias` is replaced by `freshAlias` supplied AS DATA (its behavior is an input, not an assumption — and the model does not even assume freshAlias is absent from the registry, which is why registryStore has two legs), and `ref_alias` only bumps a refcount that is not part of the modeled value (alias + registry). Refinement-leg tally: 6 rows, tags I,R,R,R,R,R — all R or I, zero kind-3, zero A-legs. Correct.

MODEL<->PATCH CORRESPONDENCE — EXECUTED, not asserted. I extracted the base_commit sources (git show 59ab3fd0e9e6:... into src: query.py join :1014-1054, table_alias :792-817, setup_joins reuse-line :1843, datastructures.py identity/`__eq__`/equals :146-166, query_utils.py FilteredRelation.as_sql :336-340) and, rather than eyeballing the rows, transliterated the GOLD Python `setup_joins` reuse-line + `join()` directly into Python and brute-forced it against the Lean oracle over the same 318,720-input domain (registries up to length 2 with distinct names over 15 alias/key entries, 5 keys, 4 own-aliases, 3 fresh aliases, 8 permitted sets, both booleans). RESULT: 'Lean oracle vs GOLD-python transliteration: AGREE everywhere' (0 mismatches; equiv.txt). That transliteration deliberately reproduces Python's EMPTY-SET FALSINESS (`if reuse_with_filtered_relation and reuse:` takes the else branch when reuse==set()), which the Lean model has no direct analogue of — and the two still agree, because on rt=true with an empty permitted set both routes yield no candidates. So the one place the model could plausibly have drifted from the real callee semantics is closed by execution.

PROTOCOL / EXECUTED EVIDENCE. Every file built by copying Solution.lean and editing ONLY the impl region plus the proof TACTIC body (the theorem STATEMENT is byte-identical; unsound_evasions enforces this). same_spec=True and unsound_evasions=[] for all 12 files.

Verifier command for each: `bash scripts/lean_verify.sh <file>`, run 4-at-a-time as concurrent background jobs; logs kept per file under logs/. atk_1_prepatch.lean          exit=1  PREPATCH BUG re-encoded (reuse confined only on a multi-valued traversal, filter tag never consulted, plain append) — impl region matches Solution_prepatch.lean modulo comments. atk_2_partial_domain.lean    exit=1  PARTIAL DOMAIN: correct only on restrictedTraversal=true, fresh alias elsewhere. atk_3_first_cand.lean        exit=1  BOUNDARY: reuse_aliases[0] instead of [-1]. atk_4_no_own_pref.lean       exit=1  CONTROL FLOW: drops the `join.table_alias in reuse_aliases` preference. atk_5_no_filter_waiver.lean  exit=1  the restricted-traversal filter waiver never applied (j == join on every route). atk_6_registry_effect.lean   exit=1  CONTROL-FLOW EFFECT: writes the registry on the REUSE route too (must be untouched). atk_7_ignore_permission.lean exit=1  permitted-reuse set computed then never consulted. atk_8_append_not_store.lean  exit=1  the name-keyed STORE degraded to an unconditional append (replace-in-place leg of registryStore dropped) — attacks refinement.md row 4's hardest claim. atk_11_store_reinsert.lean   exit=1  STORE ORDER: filter-out-then-append instead of replace in place, i.e. the 'order of names unchanged' clause violated (differs only in key ORDER). atk_9_oracle_echo.lean       exit=0, `#print axioms correct_addJoin` => "'correct_addJoin' does not depend on any axioms" (axchk_atk_9_oracle_echo.lean, exit 0).

UNGROUNDED ORACLE ECHO. atk_10_alt_shape.lean        exit=0, axioms clean (axchk_atk_10_alt_shape.lean, exit 0). ALTERNATIVE SAME-SPEC IMPL in a different shape (filterMap + inlined store, proof `rfl`). pc_correct.lean (POSITIVE CONTROL) exit=0, axioms clean (axchk_pc_correct.lean) — correct impl in a THIRD shape (calls the pure helper registryStore instead of inlining it). Every exit=1 is SEMANTIC ("error: Tactic `rfl` failed: The left-hand side") on the postcondition, never a syntax/elaboration error. Official mechanical re-check agrees on all 12 (adversary.check_attack: same_spec=True, admissible=True, verify_completed=True for every file; verifies=False for the 9 wrong impls, True for atk_9/atk_10/pc_correct) — logs/check_attack.txt.

MANDATORY RESOLVE RUNS (both verifying attacks, not just one). Command per patch: `python3 -c "from swebench_unified.harness import run_resolve; run_resolve('django__django-15554', open(<patch>).read())"`, the two run concurrently.
  atk_9_faithful.patch  (atk_9_faithful.patch, 4836 B; regenerated from the base_commit worktree, semantically the gold change) => {'resolved': True, 'completed': True, 'note': 'resolved', 'attempts': 1, 'flaky': False}
  atk_10_faithful.patch (atk_10_faithful.patch, 3159 B; an INDEPENDENT transliteration of atk_10's own Lean shape — one comprehension with `and (reuse_with_filtered_relation or j == join)` as the waiver conjunct, NOT gold's if/else split) => {'resolved': True, 'completed': True, 'note': 'resolved', 'attempts': 1, 'flaky': False}
Both resolved on the first attempt, non-flaky (resolve_atk_9.json, resolve_atk_10.json). G-RESOLVE is recorded pass on gold for this instance, so the oracle can refute here — a not-resolved verdict would have carried information. No BROKEN condition is met.

FALSE-REJECTION CONTROL (why the 9 rejections are real). An exit=1 can measure a weak tactic script rather than the specification, so I brute-forced every impl against the oracle in Python (equiv.py, 318,720 inputs each): all 9 rejected attacks DIFFER on a concrete witness ('FALSE-REJECTION SUSPECTS: none'), and all 3 verifying impls are EQUAL over the whole domain. Sample witnesses — atk_3: registry=[(0,(0,None)),(1,(0,None))], nja=2 => oracle 1 vs attack 0; atk_8 on rt=true with freshAlias already held: oracle (0,[(0,(0,None))]) vs attack (0,[(0,(0,None)),(0,(0,None))]); atk_11: oracle [(0,..),(1,..)] vs attack [(1,..),(0,..)]. F2P-shaped witness (the test_multiple collapse) computed separately in logs/f2p_witness.txt: registry=[(0,(base 0,filt 0))], newJoin=(base 0, filt 1), nja=5, freshAlias=9, permitted=[7] (relation-2's own path), mv=false, rt=true => oracle (9, [(0,(0,0)),(9,(0,1))]) i.e. TWO joins, while atk_1_prepatch and atk_7_ignore_permission both give (0, [(0,(0,0))]) i.e. ONE collapsed join — exactly the reported bug. So the prepatch bug is reproduced AND the spec rejects it for the right reason.

DOC DEFECT (not a G-EQ break; for the faithfulness/hygiene roles). refinement.md and mapping.md are IDENTIFIER-ROTTEN: they discuss `isM2M` (4/4 occurrences), `reuseWithFilteredRelation` (3/4), `canReuse` (5/5) and `keysEqual` (3/4), none of which exist in Solution.lean (counts 0/0/0/0); the shipped parameters are `multiValued`, `restrictedTraversal`, `permittedAliases` and the comparison is inlined in `eligible`. Worse, refinement.md's "Lean impl" code block (lines 39-47) is presented as a verbatim quote of implementation_addJoin but is NOT the artifact: it omits the own-alias preference that its own row 5 then tags, and uses the nonexistent names. Every row's asserted correspondence is still SOUND under the obvious renaming (I re-derived all six against the base-commit source and the gold transliteration above), so no leg is misattributed and this does not weaken the obligation — but a reader diffing the quoted block against Solution.lean would find it does not match. The precondition claim a prior pass flagged in mapping.md is FIXED (it now says UNCONDITIONAL).

**FLOOR:** 9 admissible same-spec wrong impls REJECTED for a genuine, witnessed behavioral difference (>= 5 required), covering partial-domain, boundary, control-flow, control-flow-effect, permission-ignoring, store-degradation and store-order classes; 2 admissible VERIFYING attacks (one an ungrounded oracle echo, one an alternative shape) each with a materialized faithful patch that RESOLVED; prepatch bug reproduced (atk_1); positive control verifies with clean axioms in a distinct file. Nothing inconclusive: every verifier run and both resolve runs reached a verdict. the temporary git worktree was removed and the repo tree is clean of stray files.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_first_cand.lean`, `atk_4_no_own_pref.lean`, `atk_5_no_filter_waiver.lean`, `atk_6_registry_effect.lean`, `atk_7_ignore_permission.lean`, `atk_8_append_not_store.lean`, `atk_11_store_reinsert.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9_oracle_echo.lean`, `atk_10_alt_shape.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no same-spec wrong impl with a closing clean-axiom proof has a faithful refined patch that fails to resolve. The two attacks whose proofs DO close (atk_9_oracle_echo, atk_10_alt_shape) are both extensionally EQUAL to the spec oracle `registrationOutcome` over a brute-forced 318,720-input domain, and each one's materialized faithful patch RESOLVED under the official harness on the first attempt: run_resolve('django__django-15554', <patch>) => {'resolved': True, 'completed': True, 'note': 'resolved', 'attempts': 1, 'flaky': False} for both (resolve_atk_9.json, resolve_atk_10.json). Notably atk_10's patch is NOT the gold text — it is an independent transliteration of atk_10's own single-comprehension Lean shape (`(reuse is None or a in reuse) and j.equals(join) and (reuse_with_filtered_relation or j == join)` in one comprehension, vs gold's two-branch if/else) — and it still resolves, which is evidence the spec's licensed implementation space maps onto genuinely-fixing code rather than onto a single syntactic echo. So verify=>correct holds on every closing impl found.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_first_cand.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_no_own_pref.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_no_filter_waiver.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_registry_effect.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_ignore_permission.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_append_not_store.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_11_store_reinsert.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_10_alt_shape.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Mathlib
-- imports-end

/-!
Allocating a query alias when registering one join.

A query keeps an ordered registry of joins it has already introduced. Each
registered join is stored under a distinct **alias** (a name), together with a
key describing the join's shape.

The key has two parts:

  * a *base* part — the table, the parent it hangs off, and the relating field;
  * an optional *filter* tag — an extra condition attached to this particular
    join (two joins on the same base relation may carry different filter tags).

Registering a new join either reuses an alias the registry already holds or
allocates a fresh one. An already-registered alias may be reused only when all
three of the following hold of the join it stands for:

  * it is PERMITTED. Permission is governed by a set of aliases supplied with
    the registration whenever the traversal introducing the join is
    multi-valued, or is itself a traversal carrying a restriction of its own;
    failing both circumstances no supplied set governs permission at all and
    every registered alias is permitted;
  * it stands on the SAME BASE relation as the new join;
  * it carries the SAME FILTER tag as the new join — a requirement waived when
    the join is introduced while traversing a relation that carries a
    restriction of its own.

Allocation then proceeds as follows:

  * if one or more aliases may be reused the registry is left unchanged, and the
    alias reused is the new join's own alias when that is itself among them,
    otherwise the most recently registered one;
  * otherwise an alias is allocated and the new join is STORED IN THE REGISTRY
    UNDER IT. The registry is a name-keyed store, so a name holds at most one
    join: storing under a name the registry does not yet hold adds a last entry,
    while storing under a name it already holds replaces that entry's join where
    it already sits — the join that name held on entry is discarded and the
    order of names is unchanged. Nothing constrains the allocated name to be one
    the registry does not already hold.

The consequence that matters: two joins on the same base relation carrying
different filter tags each receive their OWN alias, never a single shared one.
A query attaching two differently-filtered joins to one relation therefore gets
a distinct join for each, rather than only the first with the other dropped.
-/

-- axioms-start
-- No unchanged outside callee contributes a property the specification consumes.
-- The reuse decision (which alias a freshly registered join lands on) and the
-- registry update are modeled DEEPLY over the data — the registry, the
-- permitted-reuse set, and the joins' keys — so there is no `opaque`/`axiom`
-- callee contract here.
-- axioms-end

-- pure-start
/-- An alias (a join name). Modeled as a `Nat` identity; only equality of
aliases is observed. -/
abbrev Alias := Nat

/-- The key of a registered join, restricted to the touched parts:
* `base` — the table / parent / relating-field shape (an injective encoding into
  `Nat`; only equality is observed);
* `filt` — an optional filter tag distinguishing two joins on the same base. -/
structure JoinKey where
  base : Nat
  filt : Option Nat
deriving DecidableEq, Repr

/-- The aliases permission is confined to, taken one circumstance at a time:
* on a traversal carrying a restriction of its own the supplied set governs
  permission;
* on a multi-valued traversal the supplied set likewise governs permission;
* failing both, no set governs (`none`) and every registered alias is
  permitted. -/
def permittedReuse (permittedAliases : List Alias)
    (multiValued restrictedTraversal : Bool) : Option (List Alias) :=
  if restrictedTraversal then some permittedAliases
  else if multiValued then some permittedAliases
  else none

/-- Whether one registered entry may be reused for `newJoin`. Three conditions,
all required:
* PERMISSION — `reuse` names the aliases permission is confined to (`none` =
  every registered alias is permitted);
* the SAME BASE relation;
* the SAME filter tag — waived when the join is introduced while traversing a
  relation that carries a restriction of its own, so where that waiver does not
  apply two joins sharing a base but carrying different filter tags may never be
  reused for one another. -/
def eligible (reuse : Option (List Alias)) (restrictedTraversal : Bool)
    (newJoin : JoinKey) (p : Alias × JoinKey) : Bool :=
  let permitted : Bool := match reuse with
    | none   => true
    | some s => s.contains p.1
  permitted && p.2.base == newJoin.base
            && (restrictedTraversal || p.2.filt == newJoin.filt)

/-- Storing `newJoin` in the registry under the name `a`.

The registry is a NAME-KEYED STORE: a name holds at most one join, so this is
not an unconditional append. Storing under a name the registry does not yet hold
adds a last entry; storing under a name it already holds REPLACES that entry's
join where it already sits, discarding the join that name held on entry and
leaving the order of names unchanged. Nothing constrains the name being
allocated to be one the registry does not already hold, so both cases occur. -/
def registryStore (registry : List (Alias × JoinKey)) (a : Alias) (k : JoinKey)
    : List (Alias × JoinKey) :=
  if registry.any (fun p => p.1 == a) then
    registry.map (fun p => if p.1 == a then (a, k) else p)
  else
    registry ++ [(a, k)]

/-- The aliases that may be reused, in registration order. -/
def matchCandidates (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (reuse : Option (List Alias)) (restrictedTraversal : Bool) : List Alias :=
  registry.filterMap (fun p =>
    if eligible reuse restrictedTraversal newJoin p then some p.1 else none)

/-- The allocation outcome for `newJoin` given the permitted-reuse set `reuse`.
`newJoinAlias` is the alias the new join already carries (its own name). When at
least one alias may be reused the registry is left unchanged and:
* if the new join's own alias is itself among them, it is reused (preferred);
* otherwise the most recently registered one is reused.
When none may be reused, `freshAlias` is allocated and the new join is STORED in
the registry under it (`registryStore`): a last entry when the registry does not
already hold that name, a replacement in place when it does. -/
def chooseAlias (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (reuse : Option (List Alias))
    (restrictedTraversal : Bool) : Alias × List (Alias × JoinKey) :=
  let cands := matchCandidates registry newJoin reuse restrictedTraversal
  if cands.isEmpty then
    (freshAlias, registryStore registry freshAlias newJoin)
  else if cands.contains newJoinAlias then
    (newJoinAlias, registry)
  else
    (cands.getLastD freshAlias, registry)

/-- The registration outcome, on EITHER governing regime: the permitted-reuse
set is `permittedReuse`. -/
def registrationOutcome (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued restrictedTraversal : Bool)
    : Alias × List (Alias × JoinKey) :=
  chooseAlias registry newJoin newJoinAlias freshAlias
    (permittedReuse permittedAliases multiValued restrictedTraversal)
    restrictedTraversal
-- pure-end

-- post-conditions-start
/-- The registration outcome for `newJoin`, on BOTH governing regimes.

`result` is exactly `registrationOutcome`: an already-registered alias may be
reused only when it is permitted, stands on the same base relation, and carries
the same filter tag — that last requirement waived where the join is introduced
while traversing a relation carrying a restriction of its own; permission is
governed by `permittedAliases` on such a traversal and on a multi-valued one,
and by nothing at all ("every alias") when neither circumstance holds. Among
the aliases that may be reused the new join's own alias wins if itself among
them, else the most recent one; the registry is left untouched whenever an alias
is reused, and otherwise the new join is STORED under the allocated name in the
name-keyed registry — a last entry when that name is not already held, a
replacement of the join held there, in place, when it is. -/
def problem_spec_addJoin
    (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued : Bool) (restrictedTraversal : Bool)
    (result : Alias × List (Alias × JoinKey)) : Prop :=
  result = registrationOutcome registry newJoin newJoinAlias freshAlias
             permittedAliases multiValued restrictedTraversal
-- post-conditions-end

-- impl-start
def implementation_addJoin
    (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
    (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
    (multiValued : Bool) (restrictedTraversal : Bool)
    : Alias × List (Alias × JoinKey) :=
  let reuse : Option (List Alias) :=
    if restrictedTraversal then some permittedAliases
    else if multiValued then some permittedAliases
    else none
  let cands : List Alias :=
    registry.filterMap (fun p =>
      let permitted : Bool := match reuse with
        | none   => true
        | some s => s.contains p.1
      if permitted && p.2.base == newJoin.base
                   && (restrictedTraversal || p.2.filt == newJoin.filt) then some p.1 else none)
  if cands.isEmpty then
    (freshAlias, registryStore registry freshAlias newJoin)
  else if cands.contains newJoinAlias then
    (newJoinAlias, registry)
  else
    (cands.getLastD freshAlias, registry)
-- impl-end

-- proof-start
theorem correct_addJoin :
    ∀ (registry : List (Alias × JoinKey)) (newJoin : JoinKey)
      (newJoinAlias freshAlias : Alias) (permittedAliases : List Alias)
      (multiValued : Bool) (restrictedTraversal : Bool),
      problem_spec_addJoin registry newJoin newJoinAlias freshAlias
          permittedAliases multiValued restrictedTraversal
        (implementation_addJoin registry newJoin newJoinAlias freshAlias
          permittedAliases multiValued restrictedTraversal) := by
  intro registry newJoin newJoinAlias freshAlias permittedAliases multiValued
    restrictedTraversal
  rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-15554 / lean. VERDICT: SOUND. Assigned focus: the A legs and the model<->patch correspondence (R/I legs are G-CONF's).

**SPEC SHAPE.** `problem_spec_addJoin ... result := result = registrationOutcome registry newJoin newJoinAlias freshAlias permittedAliases multiValued restrictedTraversal` — an EXACT FUNCTIONAL EQUALITY against a total, computable oracle modeled deeply over the data (permittedReuse / eligible / matchCandidates / chooseAlias / registryStore). There is NO precondition: correct_addJoin quantifies over all of multiValued/restrictedTraversal, so behavior is pinned on the FULL domain, and any impl that verifies is extensionally the oracle. mapping.md:98-104 now states this correctly ('The spec/theorem is UNCONDITIONAL'), so the doc defect a prior pass recorded on this point has been REPAIRED in the shipped artifact.

A-LEG AUDIT (my focus). `grep -nE '^\s*(axiom|opaque)\b|sorry|admit|native_decide|Assume|Refute' Solution.lean` => NONE. meta.json: axioms=[], deep_model_references=[], conf_skip=false; gates.G-AX recorded skip, exit 0. axiom_check.py is a consistent skip stub. So there are ZERO A-consumed and ZERO A-reference legs, and no kind-3 leg can exist. This is the SOUND choice rather than an evasion: the only callee whose property the reuse decision genuinely depends on is `Join.equals`, and it is modeled INLINE (as the `base` comparison in `eligible`) rather than axiomatized — per SPEC_GUIDE a deeply-modeled changed op's callee must not become a consumed axiom. The two genuinely-unchanged callees contribute nothing the spec consumes: `table_alias` is replaced by `freshAlias` supplied AS DATA (its behavior is an input, not an assumption — and the model does not even assume freshAlias is absent from the registry, which is why registryStore has two legs), and `ref_alias` only bumps a refcount that is not part of the modeled value (alias + registry). Refinement-leg tally: 6 rows, tags I,R,R,R,R,R — all R or I, zero kind-3, zero A-legs. Correct.

MODEL<->PATCH CORRESPONDENCE — EXECUTED, not asserted. I extracted the base_commit sources (git show 59ab3fd0e9e6:... into src: query.py join :1014-1054, table_alias :792-817, setup_joins reuse-line :1843, datastructures.py identity/`__eq__`/equals :146-166, query_utils.py FilteredRelation.as_sql :336-340) and, rather than eyeballing the rows, transliterated the GOLD Python `setup_joins` reuse-line + `join()` directly into Python and brute-forced it against the Lean oracle over the same 318,720-input domain (registries up to length 2 with distinct names over 15 alias/key entries, 5 keys, 4 own-aliases, 3 fresh aliases, 8 permitted sets, both booleans). RESULT: 'Lean oracle vs GOLD-python transliteration: AGREE everywhere' (0 mismatches; equiv.txt). That transliteration deliberately reproduces Python's EMPTY-SET FALSINESS (`if reuse_with_filtered_relation and reuse:` takes the else branch when reuse==set()), which the Lean model has no direct analogue of — and the two still agree, because on rt=true with an empty permitted set both routes yield no candidates. So the one place the model could plausibly have drifted from the real callee semantics is closed by execution.

PROTOCOL / EXECUTED EVIDENCE. Every file built by copying Solution.lean and editing ONLY the impl region plus the proof TACTIC body (the theorem STATEMENT is byte-identical; unsound_evasions enforces this). same_spec=True and unsound_evasions=[] for all 12 files.

Verifier command for each: `bash scripts/lean_verify.sh <file>`, run 4-at-a-time as concurrent background jobs; logs kept per file under logs/. atk_1_prepatch.lean          exit=1  PREPATCH BUG re-encoded (reuse confined only on a multi-valued traversal, filter tag never consulted, plain append) — impl region matches Solution_prepatch.lean modulo comments. atk_2_partial_domain.lean    exit=1  PARTIAL DOMAIN: correct only on restrictedTraversal=true, fresh alias elsewhere. atk_3_first_cand.lean        exit=1  BOUNDARY: reuse_aliases[0] instead of [-1]. atk_4_no_own_pref.lean       exit=1  CONTROL FLOW: drops the `join.table_alias in reuse_aliases` preference. atk_5_no_filter_waiver.lean  exit=1  the restricted-traversal filter waiver never applied (j == join on every route). atk_6_registry_effect.lean   exit=1  CONTROL-FLOW EFFECT: writes the registry on the REUSE route too (must be untouched). atk_7_ignore_permission.lean exit=1  permitted-reuse set computed then never consulted. atk_8_append_not_store.lean  exit=1  the name-keyed STORE degraded to an unconditional append (replace-in-place leg of registryStore dropped) — attacks refinement.md row 4's hardest claim. atk_11_store_reinsert.lean   exit=1  STORE ORDER: filter-out-then-append instead of replace in place, i.e. the 'order of names unchanged' clause violated (differs only in key ORDER). atk_9_oracle_echo.lean       exit=0, `#print axioms correct_addJoin` => "'correct_addJoin' does not depend on any axioms" (axchk_atk_9_oracle_echo.lean, exit 0).

UNGROUNDED ORACLE ECHO. atk_10_alt_shape.lean        exit=0, axioms clean (axchk_atk_10_alt_shape.lean, exit 0). ALTERNATIVE SAME-SPEC IMPL in a different shape (filterMap + inlined store, proof `rfl`). pc_correct.lean (POSITIVE CONTROL) exit=0, axioms clean (axchk_pc_correct.lean) — correct impl in a THIRD shape (calls the pure helper registryStore instead of inlining it). Every exit=1 is SEMANTIC ("error: Tactic `rfl` failed: The left-hand side") on the postcondition, never a syntax/elaboration error. Official mechanical re-check agrees on all 12 (adversary.check_attack: same_spec=True, admissible=True, verify_completed=True for every file; verifies=False for the 9 wrong impls, True for atk_9/atk_10/pc_correct) — logs/check_attack.txt.

MANDATORY RESOLVE RUNS (both verifying attacks, not just one). Command per patch: `python3 -c "from swebench_unified.harness import run_resolve; run_resolve('django__django-15554', open(<patch>).read())"`, the two run concurrently.
  atk_9_faithful.patch  (atk_9_faithful.patch, 4836 B; regenerated from the base_commit worktree, semantically the gold change) => {'resolved': True, 'completed': True, 'note': 'resolved', 'attempts': 1, 'flaky': False}
  atk_10_faithful.patch (atk_10_faithful.patch, 3159 B; an INDEPENDENT transliteration of atk_10's own Lean shape — one comprehension with `and (reuse_with_filtered_relation or j == join)` as the waiver conjunct, NOT gold's if/else split) => {'resolved': True, 'completed': True, 'note': 'resolved', 'attempts': 1, 'flaky': False}
Both resolved on the first attempt, non-flaky (resolve_atk_9.json, resolve_atk_10.json). G-RESOLVE is recorded pass on gold for this instance, so the oracle can refute here — a not-resolved verdict would have carried information. No BROKEN condition is met.

FALSE-REJECTION CONTROL (why the 9 rejections are real). An exit=1 can measure a weak tactic script rather than the specification, so I brute-forced every impl against the oracle in Python (equiv.py, 318,720 inputs each): all 9 rejected attacks DIFFER on a concrete witness ('FALSE-REJECTION SUSPECTS: none'), and all 3 verifying impls are EQUAL over the whole domain. Sample witnesses — atk_3: registry=[(0,(0,None)),(1,(0,None))], nja=2 => oracle 1 vs attack 0; atk_8 on rt=true with freshAlias already held: oracle (0,[(0,(0,None))]) vs attack (0,[(0,(0,None)),(0,(0,None))]); atk_11: oracle [(0,..),(1,..)] vs attack [(1,..),(0,..)]. F2P-shaped witness (the test_multiple collapse) computed separately in logs/f2p_witness.txt: registry=[(0,(base 0,filt 0))], newJoin=(base 0, filt 1), nja=5, freshAlias=9, permitted=[7] (relation-2's own path), mv=false, rt=true => oracle (9, [(0,(0,0)),(9,(0,1))]) i.e. TWO joins, while atk_1_prepatch and atk_7_ignore_permission both give (0, [(0,(0,0))]) i.e. ONE collapsed join — exactly the reported bug. So the prepatch bug is reproduced AND the spec rejects it for the right reason.

DOC DEFECT (not a G-EQ break; for the faithfulness/hygiene roles). refinement.md and mapping.md are IDENTIFIER-ROTTEN: they discuss `isM2M` (4/4 occurrences), `reuseWithFilteredRelation` (3/4), `canReuse` (5/5) and `keysEqual` (3/4), none of which exist in Solution.lean (counts 0/0/0/0); the shipped parameters are `multiValued`, `restrictedTraversal`, `permittedAliases` and the comparison is inlined in `eligible`. Worse, refinement.md's "Lean impl" code block (lines 39-47) is presented as a verbatim quote of implementation_addJoin but is NOT the artifact: it omits the own-alias preference that its own row 5 then tags, and uses the nonexistent names. Every row's asserted correspondence is still SOUND under the obvious renaming (I re-derived all six against the base-commit source and the gold transliteration above), so no leg is misattributed and this does not weaken the obligation — but a reader diffing the quoted block against Solution.lean would find it does not match. The precondition claim a prior pass flagged in mapping.md is FIXED (it now says UNCONDITIONAL).

**FLOOR:** 9 admissible same-spec wrong impls REJECTED for a genuine, witnessed behavioral difference (>= 5 required), covering partial-domain, boundary, control-flow, control-flow-effect, permission-ignoring, store-degradation and store-order classes; 2 admissible VERIFYING attacks (one an ungrounded oracle echo, one an alternative shape) each with a materialized faithful patch that RESOLVED; prepatch bug reproduced (atk_1); positive control verifies with clean axioms in a distinct file. Nothing inconclusive: every verifier run and both resolve runs reached a verdict. the temporary git worktree was removed and the repo tree is clean of stray files.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE: compared the model against the base_commit worktree with patch.diff (gold, from data/swe_bench_verified/test.jsonl) APPLIED -- verified the applied diff's +/- content lines are byte-equal to the gold patch (47/47 lines match). Base commit 59ab3fd0e9 used only for untouched callees (Join.identity/equals/`__eq__`, table_alias, FilteredRelation), which the patch does not modify.

**ARTIFACT CHECKS:** (1) scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). (2) `#print axioms correct_addJoin` -> [propext, Quot.sound] -- CLEAN, no sorryAx, so the proof is real. (3) markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True -- the spec region is byte-identical between gold and prepatch, so the discriminator is a pure impl change and the spec is not tuned to the fix. meta.json declares axioms=[] and deep_model_references=[], consistent with the axioms region being a prose no-op stub -- there is no axiom whose contract could be over-strong.

PRIMARY DIFFERENTIAL (real code, not a replica): built real_diff2.py driving the REAL patched Query.join on a real Query with real Join objects (real FilteredRelation, real Join.identity/equals/`__eq__`), stubbing only table_alias (to pin the allocated name to the modeled `freshAlias`, which the spec takes as data) and join_field (a minimal stand-in whose equality is the observed relation). Applied setup_joins' patched reuse line `reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None`. Projected the resulting alias_map back to (base, filt) keys and compared BOTH components of the modeled value (chosen alias AND resulting registry) against implementation_addJoin.

**EXHAUSTIVE RESULT:** 3,527,424 cases -- registries of length 0..3 with distinct aliases over 3 alias names x 6 keys (2 bases x 3 filter tags incl. None), all newJoin keys, newJoinAlias and freshAlias over 4 names (incl. names present AND absent from the registry), 6 permitted-reuse sets, and both booleans (m2m x rwfr, all four regimes). ZERO mismatches. This exercises both registryStore legs: the append leg AND the in-place-replace leg (freshAlias already held), confirming the non-obvious dict-store modeling and the `join.table_alias in reuse_aliases` preference (chooseAlias's cands.contains newJoinAlias branch) against real code.

(An earlier harness reported ~178k mismatches; that was MY bug -- I had tied FilteredRelation.alias to each entry's table_alias, which collapsed distinct filter tags. With filt an injective encoding of the whole FilteredRelation as mapping.md specifies, divergences went to 0. Recording this so the number is not misread as a finding.)

HARDEST PROBE -- the one real gap, and why it is not a defect: the patched guard is `if reuse_with_filtered_relation and reuse` (Python TRUTHINESS of reuse), whereas the Lean guard is just `restrictedTraversal`. These differ when rwfr=True and reuse is falsy. Two falsy shapes:
  * reuse = set() (empty): exhaustively tested 18,360 cases -- ZERO divergences. Empty reuse permits nothing, so both the then-branch (a in reuse) and the else-branch (a in reuse, since reuse is not None) yield no candidates; the guard is immaterial.
  * reuse = None: DOES diverge (4,320/18,360 cases with the faithful all-permitted encoding). Smallest: registry=[(A,(base=1,filt=1))], newJoin=(base=1,filt=2), rwfr=True, can_reuse=None -> real allocates a fresh alias (else-branch uses filter-SENSITIVE `j == join`), model reuses A (waives the filter). BUT this input is UNREACHABLE, established two independent ways: (a) STRUCTURALLY -- rwfr=True originates at exactly one site, build_filtered_relation_q's build_filter(..., reuse_with_filtered_relation=True), and its `reuse` comes from FilteredRelation.as_sql's `build_filtered_relation_q(self.condition, reuse=set(self.path))`, a set literal, never None; grep confirms these are the only two call sites. (b) EMPIRICALLY -- instrumented the real patched Query.join to log (rwfr, reuse) and ran the ORM suites queries/filtered_relation/aggregation/annotations/lookup/many_to_many/select_related/prefetch_related/expressions: 6,210 real join() calls, of which 75 had rwfr=True and ALL 75 had a non-None reuse; ZERO calls had rwfr=True with reuse None or empty. Note this is the direction that would make the spec WEAKER-than-real on an unreachable input, not stronger -- it cannot license a wrong implementation on reachable behavior. Instrumentation was reverted and the worktree confirmed byte-identical to the clean patched state.

**ADDITIONAL RIGOR:** (1) Join.identity excludes join_type, so the join_type/LOUTER-promotion mutation in join() cannot affect the alias decision -- confirmed by re-running the real join with join_type=INNER live and a registered parent_alias: alias choice unchanged and matching the model. (2) The base triple is independently significant -- differing parent_alias or join_field alone makes equals/`__eq__` False, while differing ONLY in table_alias leaves them equal, exactly justifying JoinKey.base as an injective encoding of (table_name, parent_alias, join_field) that omits table_alias. (3) Query.join's other caller (combine(), line 648) passes a set and rwfr defaults False, staying inside the modeled regimes; BaseTable.equals is alias-sensitive, but combine() skips the base table (rhs_tables = list(rhs.alias_map)[1:]) and setup_joins always constructs a Join, so no BaseTable reaches the modeled slice. (4) F2P test test_multiple passes on the patched tree (43 tests OK).

No diverging input on any reachable configuration. Spec is not too strong and does not drift from real post-patch behavior.

UNRELATED HOUSEKEEPING (not a faithfulness defect, does not affect this gate): meta.json['region_hashes'] is STALE relative to the shipped Solution.lean -- recomputed hashes (spec_view 4644754f20c4...) match neither the meta values nor any of HEAD..HEAD~5, so the meta was not refreshed after the last spec edit. Worth a bundle-hygiene fix so region-hash provenance checks do not fail spuriously.

**REFERENCE DISCIPLINE:** compared the model against the base_commit worktree with patch.diff (gold, from data/swe_bench_verified/test.jsonl) APPLIED -- verified the applied diff's +/- content lines are byte-equal to the gold patch (47/47 lines match). Base commit 59ab3fd0e9 used only for untouched callees (Join.identity/equals/`__eq__`, table_alias, FilteredRelation), which the patch does not modify.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** django__django-15554 / lean. NO relaxation in this bundle: meta.json has no `relaxed_leakage` key, gates.G-LEAK.status = "pass" (strict), and no RELAXED_LEAKAGE.md exists anywhere under the instance dir (`find -iname '*RELAX*'` empty). So this is an ordinary strict leakage judgement, not an inherited disposition. No file in the bundle addresses me or instructs how to record; the only panel-facing text is verdict.md's archived note from a PRIOR run, and that run judged a DIFFERENT artifact (its recorded spec_view a027f9eb..., G-EQ Solution.lean 18d9952c...), whereas the live Solution.lean is 207638c80d8c... with spec_view 4644754f20c4... -- the spec was revised after that note (registryStore/dict-replace, i.e. the panel-2 UNFAITHFUL repair), so I re-derived everything from scratch rather than reusing it.

### MECHANICAL (all re-run by me, all clean):
1. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True -> the spec region (everything outside impl+proof) is byte-identical across the twins, so the view I judged is the only view. markers.region_hashes recomputed and match meta.json G-HYGIENE exactly, incl. spec_view 4644754f20c4c91bc509cd189b5bc798927a9df46beb2ec0a0098a08af64f16b.
2. Proof is real: scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms correct_addJoin` -> "depends on axioms: [propext, Quot.sound]" (no sorryAx, no bundle axiom; axioms region is a comment-only stub). Prepatch twin: elaborates but "declaration uses 'sorry'" -> lean_verify reports sorry, so the discriminator is genuinely load-bearing.
3. local patch.diff == instance.json['patch'] byte-for-byte, so leakage was judged against the true gold.
4. leakage.screen(view, LeanBackend, gold_patch, problem_statement) re-run independently: passed, 0 hard failures, 0 warnings. Re-derived by hand: no @@ / 'diff --git' / '+++ ' / '\nindex '; no normalized gold changed-line (len>=8) occurs in the normalized view (checked every added/removed line via unidiff); no patched path or symbol -- grepped the view for query.py, django/db, sql/query, setup_joins, build_filter, build_filtered_relation_q, reuse_with_filtered_relation, can_reuse, alias_map, table_alias, filtered_relation, FilteredRelation, m2m, reuse_aliases, Join.equals, ref_alias, alias_prefix, refcount, LOUTER, names_to_path, split_subq, allow_many: ZERO hits (only 'identity' as the English word in "Modeled as a `Nat` identity", and 'identity' does not occur in the patch at all).
5. Hints-only / test-only vocabulary: zero hits for test_multiple, book_title_alice/jane, Author, tests.py, the 0c71e0f9 regression commit, assertSequenceEqual -- so nothing echoes hints_text (which I read only to confirm absence).
6. Token intersection of the view with gold changed lines is entirely generic English/spec vocabulary: alias, else, given, join, joins, names, only, relation, reuse, reused, then, when. Of the non-function words, alias/join/relation/only all appear in the public problem_statement; 'reuse'/'reused' are not def/class names, are not introduced by the patch (`reuse` is a pre-existing `Query.join` parameter visible at base_commit), and localize no edit.

SEMANTIC (the part the lexical screen cannot reach). The strongest LEAKAGE candidate is the docstring + `permittedReuse` clause that the supplied set governs permission "whenever the traversal introducing the join is multi-valued, or is itself a traversal carrying a restriction of its own", together with the same-filter-tag requirement being waived on such a traversal -- structurally the gold's `reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None` plus the `reuse_with_filtered_relation and reuse` branch. I weighed it and it does not clear the bar:

  (a) Strip test: I re-derived unavoidability rather than assuming it. Deleting the restrictedTraversal disjunct leaves exactly the base_commit rule (`some canReuse` iff multiValued), which is precisely Solution_prepatch.lean's impl -- and same_spec = True means the prepatch twin is checked against this identical spec region, where it fails (sorry). So the clause is load-bearing: without it the PRE-patch impl satisfies the spec and G-DIFF collapses. A faithful, G-DIFF-passing spec cannot omit it.

  (b) The observable consequence paragraph (two same-base joins with different filter tags each get their OWN alias, "rather than only the first with the other dropped") is content the public problem_statement already states verbatim in substance ("it actually just generates a single SQL JOIN ... and ignores the other", and the reporter asks for the two-JOIN behavior). Nothing there exceeds problem_statement.

  (c) It is de-narrated and strictly weaker than the edit: no flag name, no threading path (build_filtered_relation_q -> build_filter -> setup_joins -> join), no file/function, and it does not mention the gold's second, else-branch change (`j.equals(join)` -> `j == join`). It states abstract desired behavior, not the diagnosis or the edit.

  (d) The new registryStore prose (a name-keyed store; storing under a held name replaces in place and discards the prior join; nothing constrains the allocated name to be fresh) concerns UNCHANGED callees (`table_alias`, `alias_map[alias] = join`) that the patch does not touch, so it localizes nothing about the gold edit -- it is faithfulness to code the solver already sees at base_commit.

**CONCLUSION:** NO-LEAKAGE. No spec-view line quotes the gold, names the patched file/function/symbol, echoes hints-only or test-only vocabulary, or narrates bug->fix mechanism; the one mechanism-shaped clause is abstract behavior the spec provably cannot drop (strip test above) and stays within what problem_statement already exposes. Scratch: view_15554.lean, ax15554.lean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
