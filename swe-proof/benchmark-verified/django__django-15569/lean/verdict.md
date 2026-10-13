# P2 adversarial audit — django__django-15569

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
   let mut st := s
-  -- remove the named entry from the underlying table
   st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
-  st := { st with cache := none }
+  -- BUG: reader snapshot left untouched (missing cache := none)
   return st
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +91,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
   let mut st := s
-  -- remove the named entry from the underlying table
   st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
-  st := { st with cache := none }
+  -- WRONG: re-prime the memo with a precomputed snapshot instead of clearing it
+  st := { st with cache := some (eraseKey s.classLookups lookupName) }
   return st
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +92,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
   let mut st := s
-  -- remove the named entry from the underlying table
-  st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
+  -- WRONG: keeps only entries whose name EQUALS lookupName (predicate flipped)
+  st := { st with classLookups := s.classLookups.filter (fun p => p.1 == lookupName) }
   st := { st with cache := none }
   return st
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +92,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
-  let mut st := s
-  -- remove the named entry from the underlying table
-  st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
-  st := { st with cache := none }
-  return st
+  -- WRONG: only invalidate/erase when the name is present; otherwise no-op
+  if (keys s.classLookups).contains lookupName then
+    return { classLookups := eraseKey s.classLookups lookupName, cache := none }
+  else
+    return s
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +92,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
-  let mut st := s
-  -- remove the named entry from the underlying table
-  st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
-  st := { st with cache := none }
-  return st
+  -- WRONG: returns the input unchanged (no removal, no invalidation)
+  return s
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +89,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
   let mut st := s
-  -- remove the named entry from the underlying table
-  st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
+  -- WRONG: erase but reverse the surviving entries' order
+  st := { st with classLookups := (eraseKey st.classLookups lookupName).reverse }
   st := { st with cache := none }
   return st
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +92,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
-procedure: drop the entry from the underlying table, then invalidate the reader
-snapshot so subsequent reads reflect the current table. -/
 def implementation_unregisterLookup
     (s : LookupState) (lookupName : String) : LookupState := Id.run do
   let mut st := s
-  -- remove the named entry from the underlying table
-  st := { st with classLookups := eraseKey st.classLookups lookupName }
-  -- invalidate the reader snapshot
+  -- WRONG: erase then re-append the removed name with a dummy id
+  st := { st with classLookups := eraseKey st.classLookups lookupName ++ [(lookupName, 0)] }
   st := { st with cache := none }
   return st
 -- impl-end
-
 -- proof-start
 theorem correct_unregisterLookup :
     ∀ (s : LookupState) (lookupName : String),
@@ -97,10 +92,6 @@
   rintro p ⟨_, hne⟩ rfl
   exact hne rfl
 
-/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
-any `result` satisfying it equals the (gold) implementation's output. Hence no
-same-spec implementation with observably wrong behavior can verify — a
-verifying same-spec variant is extensionally the gold behavior. -/
 theorem spec_unregisterLookup_deterministic :
     ∀ (s : LookupState) (lookupName : String) (r : LookupState),
       problem_spec_unregisterLookup s lookupName r →
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
# Removing a registered lookup from a lookup registry

A lookup registry holds, per class, a table of registered named lookups
(`classLookups`) together with a memoized view of the table that readers consult
(`cache`). When a name is removed from the registry, two things must hold for the
registry to behave correctly: the name must be gone from the underlying table,
and the value subsequently seen by readers must reflect the current table rather
than a stale snapshot.

This bundle models the removal operation and pins exactly that behavior.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the memo-invalidation effect is
-- modeled deeply (the reader view is recomputed from the current table), and the
-- table edit is modeled deeply via `eraseKey`.
-- axioms-end

-- pure-start
/-- A registry for one class: the underlying table of named entries
(`classLookups`) and a memoized snapshot consulted by readers (`cache`); `none`
means "no snapshot — readers recompute from the table". Entry identities are
abstracted to `Nat` ids. -/
structure LookupState where
  classLookups : List (String × Nat)
  cache : Option (List (String × Nat))
deriving Repr, DecidableEq

/-- Drop every entry whose name equals `k` from a table. -/
def eraseKey (xs : List (String × Nat)) (k : String) : List (String × Nat) :=
  xs.filter (fun p => p.1 != k)

/-- The list of names currently present in a table. -/
def keys (xs : List (String × Nat)) : List String := xs.map Prod.fst

/-- The table value seen by readers: the memoized snapshot if present, otherwise
the freshly recomputed table. -/
def getLookups (s : LookupState) : List (String × Nat) :=
  s.cache.getD s.classLookups
-- pure-end

-- post-conditions-start
/-- Correctness of removing the entry named `lookupName` from registry `s`,
producing `result`.

1. the underlying table is exactly the input table with every entry named
   `lookupName` dropped — all other entries preserved in order, nothing added;
2. the memoized reader snapshot is invalidated (cleared, not re-primed with a
   precomputed value): readers recompute from the table, so subsequent table
   changes are also visible;
3. readers see the current table, not a stale snapshot: the reader view equals
   the (recomputed) underlying table, and in particular no longer reports the
   removed name.

Note for reviewers: clauses 1–2 pin BOTH fields of `result`, so this spec is
DETERMINISTIC — any `result` satisfying it is a single, fully determined
state. A same-spec implementation can verify only by computing exactly that
state (extensionally identical output); a verifying same-spec variant is
therefore a positive control, not evidence of spec weakness. -/
def problem_spec_unregisterLookup
    (s : LookupState) (lookupName : String) (result : LookupState) : Prop :=
  result.classLookups = eraseKey s.classLookups lookupName ∧
  result.cache = none ∧
  getLookups result = result.classLookups ∧
  lookupName ∉ keys (getLookups result)
-- post-conditions-end

-- impl-start
/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
procedure: drop the entry from the underlying table, then invalidate the reader
snapshot so subsequent reads reflect the current table. -/
def implementation_unregisterLookup
    (s : LookupState) (lookupName : String) : LookupState := Id.run do
  let mut st := s
  -- remove the named entry from the underlying table
  st := { st with classLookups := eraseKey st.classLookups lookupName }
  -- invalidate the reader snapshot
  st := { st with cache := none }
  return st
-- impl-end

-- proof-start
theorem correct_unregisterLookup :
    ∀ (s : LookupState) (lookupName : String),
      problem_spec_unregisterLookup s lookupName
        (implementation_unregisterLookup s lookupName) := by
  intro s lookupName
  unfold problem_spec_unregisterLookup implementation_unregisterLookup
  simp only [Id.run, getLookups, Option.getD_none, pure]
  refine ⟨trivial, trivial, trivial, ?_⟩
  simp only [eraseKey, keys, List.mem_map, List.mem_filter, bne_iff_ne, ne_eq,
    not_exists, not_and]
  rintro p ⟨_, hne⟩ rfl
  exact hne rfl

/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
any `result` satisfying it equals the (gold) implementation's output. Hence no
same-spec implementation with observably wrong behavior can verify — a
verifying same-spec variant is extensionally the gold behavior. -/
theorem spec_unregisterLookup_deterministic :
    ∀ (s : LookupState) (lookupName : String) (r : LookupState),
      problem_spec_unregisterLookup s lookupName r →
        r = implementation_unregisterLookup s lookupName := by
  intro s lookupName r h
  obtain ⟨h1, h2, -, -⟩ := h
  unfold implementation_unregisterLookup
  simp only [Id.run, pure]
  cases r
  simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is DETERMINISTIC: problem_spec_unregisterLookup pins BOTH result fields exactly (clause1 result.classLookups = eraseKey s.classLookups lookupName exact-list equality; clause2 result.cache = none). Solution.lean proves spec_unregisterLookup_deterministic (axioms [propext]) => any result satisfying the spec equals the gold impl output. Hence no observably-wrong same-spec impl can verify, and there is no wrong impl whose proof closes with clean axioms => zero candidate patches to resolve-run (patches={} legitimately). Harness correspondence still positively validated below.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True via swebench_unified.markers.same_spec (impl AND proof regions are both elided from the lean spec view, so editing them preserves the spec signature; axioms/pure/post-conditions left byte-identical).

ATTACKS (7 distinct same-spec wrong impls; each carries the gold proof block verbatim). Command per file: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently, <=4 at a time, 2 batches). atk_1 (control-flow-effect: prepatch bug, drops `cache := none`) -> exit 1 (postcondition obligation unprovable; reproduces the prepatch bug: cache stays stale, clauses 2/3/4 fail). atk_2 (ungrounded-oracle echo: re-primes memo `cache := some (eraseKey ...)` instead of clearing) -> exit 1 (clause2 result.cache=none fails). atk_3 (predicate flip / boundary: keeps only entries whose name EQUALS lookupName) -> exit 1. atk_4 (partial-domain: only erase+invalidate when name present, else return s) -> exit 1. atk_5 (identity no-op: return s) -> exit 1. atk_6 (order attack: (eraseKey ...).reverse) -> exit 1 (exact-list clause1 fails on reorder). atk_7 (ungrounded add: re-append (lookupName,0) after erase) -> exit 1 (clause1 exact-list + clause4 membership fail).

All 7 fail with genuine goal/obligation errors (Application type mismatch in the refine + `cases`/unsolved-goals on the pinned fields), NOT superficial syntax breakage — confirmed by inspecting each .out. No wrong impl produced a closing clean-axiom proof, so none required a materialized resolve run.

POSITIVE CONTROL (gold impl, byte-identical to Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0 (verifies, no sorry). `#print axioms` on pos_axck.lean: correct_unregisterLookup depends on [propext, Quot.sound]; spec_unregisterLookup_deterministic depends on [propext] — clean (no sorryAx/native).

HARNESS CORRESPONDENCE (verify=>correct positively demonstrated): the positive control's faithful patch IS the gold patch.diff (adds `cls._clear_cached_lookups()` after `del cls.class_lookups[lookup_name]`). Ran it through the official harness (python -m swebench_unified.run_evaluation, image swebench/sweb.eval.x86_64.django_1776_django-15569:latest). Result: report.json resolved=true, FAIL_TO_PASS success=[test_get_transforms, test_lookups_caching] (0 failures), all 231 PASS_TO_PASS success, 0 failures. Harness stdout: 'Instances resolved: 1'. (The wrapper run_resolve earlier reported 'no report' due to a report-path lookup quirk on that run_id; the direct harness invocation is authoritative and resolves.)

REFINEMENT.MD AUDIT (against real callee query_utils.py:150-219): 4 legs, all R or I, NO A-consumed / A-reference / kind-3 legs (consistent with empty axioms region and G-AX skip=pass). Leg1 (mut state <-> cls class_lookups+lru-cache) R ok; Leg2 (eraseKey <-> del cls.class_lookups[lookup_name] line 219) R ok — del removes the key, eraseKey drops pairs with that key, faithful; Leg3 (cache := none <-> cls._clear_cached_lookups() the ADDED fix line) R deep-model ok — real callee walks subclasses(cls) calling get_lookups.cache_clear(); the single-class observable effect pinned by F2P test_lookups_caching (assertNotIn removed name in field.get_lookups()) is 'memo emptied', modeled deeply as cache:=none, correctly NOT axiomatized since it is the operation the patch adds the call to; Leg4 (return st <-> implicit return) I ok. No A-legs to validate correspondence for.

CONCLUSION: >=5 (7) distinct same-spec attacks run and verified to FAIL; positive control verifies with clean axioms and its faithful=gold patch RESOLVES; no clean-axiom-closing wrong impl exists; refinement legs all R/I with faithful correspondence. verify=>correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
# Removing a registered lookup from a lookup registry

A lookup registry holds, per class, a table of registered named lookups
(`classLookups`) together with a memoized view of the table that readers consult
(`cache`). When a name is removed from the registry, two things must hold for the
registry to behave correctly: the name must be gone from the underlying table,
and the value subsequently seen by readers must reflect the current table rather
than a stale snapshot.

This bundle models the removal operation and pins exactly that behavior.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the memo-invalidation effect is
-- modeled deeply (the reader view is recomputed from the current table), and the
-- table edit is modeled deeply via `eraseKey`.
-- axioms-end

-- pure-start
/-- A registry for one class: the underlying table of named entries
(`classLookups`) and a memoized snapshot consulted by readers (`cache`); `none`
means "no snapshot — readers recompute from the table". Entry identities are
abstracted to `Nat` ids. -/
structure LookupState where
  classLookups : List (String × Nat)
  cache : Option (List (String × Nat))
deriving Repr, DecidableEq

/-- Drop every entry whose name equals `k` from a table. -/
def eraseKey (xs : List (String × Nat)) (k : String) : List (String × Nat) :=
  xs.filter (fun p => p.1 != k)

/-- The list of names currently present in a table. -/
def keys (xs : List (String × Nat)) : List String := xs.map Prod.fst

/-- The table value seen by readers: the memoized snapshot if present, otherwise
the freshly recomputed table. -/
def getLookups (s : LookupState) : List (String × Nat) :=
  s.cache.getD s.classLookups
-- pure-end

-- post-conditions-start
/-- Correctness of removing the entry named `lookupName` from registry `s`,
producing `result`.

1. the underlying table is exactly the input table with every entry named
   `lookupName` dropped — all other entries preserved in order, nothing added;
2. the memoized reader snapshot is invalidated (cleared, not re-primed with a
   precomputed value): readers recompute from the table, so subsequent table
   changes are also visible;
3. readers see the current table, not a stale snapshot: the reader view equals
   the (recomputed) underlying table, and in particular no longer reports the
   removed name.

Note for reviewers: clauses 1–2 pin BOTH fields of `result`, so this spec is
DETERMINISTIC — any `result` satisfying it is a single, fully determined
state. A same-spec implementation can verify only by computing exactly that
state (extensionally identical output); a verifying same-spec variant is
therefore a positive control, not evidence of spec weakness. -/
def problem_spec_unregisterLookup
    (s : LookupState) (lookupName : String) (result : LookupState) : Prop :=
  result.classLookups = eraseKey s.classLookups lookupName ∧
  result.cache = none ∧
  getLookups result = result.classLookups ∧
  lookupName ∉ keys (getLookups result)
-- post-conditions-end

-- impl-start
/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
procedure: drop the entry from the underlying table, then invalidate the reader
snapshot so subsequent reads reflect the current table. -/
def implementation_unregisterLookup
    (s : LookupState) (lookupName : String) : LookupState := Id.run do
  let mut st := s
  -- remove the named entry from the underlying table
  st := { st with classLookups := eraseKey st.classLookups lookupName }
  -- invalidate the reader snapshot
  st := { st with cache := none }
  return st
-- impl-end

-- proof-start
theorem correct_unregisterLookup :
    ∀ (s : LookupState) (lookupName : String),
      problem_spec_unregisterLookup s lookupName
        (implementation_unregisterLookup s lookupName) := by
  intro s lookupName
  unfold problem_spec_unregisterLookup implementation_unregisterLookup
  simp only [Id.run, getLookups, Option.getD_none, pure]
  refine ⟨trivial, trivial, trivial, ?_⟩
  simp only [eraseKey, keys, List.mem_map, List.mem_filter, bne_iff_ne, ne_eq,
    not_exists, not_and]
  rintro p ⟨_, hne⟩ rfl
  exact hne rfl

/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
any `result` satisfying it equals the (gold) implementation's output. Hence no
same-spec implementation with observably wrong behavior can verify — a
verifying same-spec variant is extensionally the gold behavior. -/
theorem spec_unregisterLookup_deterministic :
    ∀ (s : LookupState) (lookupName : String) (r : LookupState),
      problem_spec_unregisterLookup s lookupName r →
        r = implementation_unregisterLookup s lookupName := by
  intro s lookupName r h
  obtain ⟨h1, h2, -, -⟩ := h
  unfold implementation_unregisterLookup
  simp only [Id.run, pure]
  cases r
  simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is DETERMINISTIC: problem_spec_unregisterLookup pins BOTH result fields exactly (clause1 result.classLookups = eraseKey s.classLookups lookupName exact-list equality; clause2 result.cache = none). Solution.lean proves spec_unregisterLookup_deterministic (axioms [propext]) => any result satisfying the spec equals the gold impl output. Hence no observably-wrong same-spec impl can verify, and there is no wrong impl whose proof closes with clean axioms => zero candidate patches to resolve-run (patches={} legitimately). Harness correspondence still positively validated below.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True via swebench_unified.markers.same_spec (impl AND proof regions are both elided from the lean spec view, so editing them preserves the spec signature; axioms/pure/post-conditions left byte-identical).

ATTACKS (7 distinct same-spec wrong impls; each carries the gold proof block verbatim). Command per file: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently, <=4 at a time, 2 batches). atk_1 (control-flow-effect: prepatch bug, drops `cache := none`) -> exit 1 (postcondition obligation unprovable; reproduces the prepatch bug: cache stays stale, clauses 2/3/4 fail). atk_2 (ungrounded-oracle echo: re-primes memo `cache := some (eraseKey ...)` instead of clearing) -> exit 1 (clause2 result.cache=none fails). atk_3 (predicate flip / boundary: keeps only entries whose name EQUALS lookupName) -> exit 1. atk_4 (partial-domain: only erase+invalidate when name present, else return s) -> exit 1. atk_5 (identity no-op: return s) -> exit 1. atk_6 (order attack: (eraseKey ...).reverse) -> exit 1 (exact-list clause1 fails on reorder). atk_7 (ungrounded add: re-append (lookupName,0) after erase) -> exit 1 (clause1 exact-list + clause4 membership fail).

All 7 fail with genuine goal/obligation errors (Application type mismatch in the refine + `cases`/unsolved-goals on the pinned fields), NOT superficial syntax breakage — confirmed by inspecting each .out. No wrong impl produced a closing clean-axiom proof, so none required a materialized resolve run.

POSITIVE CONTROL (gold impl, byte-identical to Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0 (verifies, no sorry). `#print axioms` on pos_axck.lean: correct_unregisterLookup depends on [propext, Quot.sound]; spec_unregisterLookup_deterministic depends on [propext] — clean (no sorryAx/native).

HARNESS CORRESPONDENCE (verify=>correct positively demonstrated): the positive control's faithful patch IS the gold patch.diff (adds `cls._clear_cached_lookups()` after `del cls.class_lookups[lookup_name]`). Ran it through the official harness (python -m swebench_unified.run_evaluation, image swebench/sweb.eval.x86_64.django_1776_django-15569:latest). Result: report.json resolved=true, FAIL_TO_PASS success=[test_get_transforms, test_lookups_caching] (0 failures), all 231 PASS_TO_PASS success, 0 failures. Harness stdout: 'Instances resolved: 1'. (The wrapper run_resolve earlier reported 'no report' due to a report-path lookup quirk on that run_id; the direct harness invocation is authoritative and resolves.)

REFINEMENT.MD AUDIT (against real callee query_utils.py:150-219): 4 legs, all R or I, NO A-consumed / A-reference / kind-3 legs (consistent with empty axioms region and G-AX skip=pass). Leg1 (mut state <-> cls class_lookups+lru-cache) R ok; Leg2 (eraseKey <-> del cls.class_lookups[lookup_name] line 219) R ok — del removes the key, eraseKey drops pairs with that key, faithful; Leg3 (cache := none <-> cls._clear_cached_lookups() the ADDED fix line) R deep-model ok — real callee walks subclasses(cls) calling get_lookups.cache_clear(); the single-class observable effect pinned by F2P test_lookups_caching (assertNotIn removed name in field.get_lookups()) is 'memo emptied', modeled deeply as cache:=none, correctly NOT axiomatized since it is the operation the patch adds the call to; Leg4 (return st <-> implicit return) I ok. No A-legs to validate correspondence for.

CONCLUSION: >=5 (7) distinct same-spec attacks run and verified to FAIL; positive control verifies with clean axioms and its faithful=gold patch RESOLVES; no clean-axiom-closing wrong impl exists; refinement legs all R/I with faithful correspondence. verify=>correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Bundle for django__django-15569, RegisterLookupMixin._unregister_lookup, fix adds cls._clear_cached_lookups() after del cls.class_lookups[lookup_name].

Mechanical checks (all pass):
- lean_verify.sh Solution.lean: exit 0 (compiles, no sorry).
- #print axioms: correct_unregisterLookup -> [propext, Quot.sound]; spec_unregisterLookup_deterministic -> [propext]. NO sorryAx; both within STANDARD_AXIOMS. Proof is real.
- same_spec(Solution, Solution_prepatch, LeanBackend.language) = True: spec region byte-identical, only impl/proof differ (prepatch drops `cache := none` and has `sorry`). Legit refinement pair.
- Recorded gates: G-EQ fail (echo/attack-set artifact, pre-fixed-derivation), all panels pass, G-RESOLVE/G-VERIFY/G-GOLD pass, patch_equals_gold=True.

Faithfulness analysis against the real repo (base_commit 884b4c27, django/db/models/query_utils.py:211-219 pre-fix; fix adds _clear_cached_lookups):
The spec pins post-patch behavior via 4 clauses: (1) classLookups = eraseKey s.classLookups lookupName (exact, order-preserving); (2) cache = none (memo cleared); (3) getLookups result = result.classLookups; (4) lookupName not in keys(getLookups result).

Sought diverging inputs; the only disagreements with the real callee are OUTSIDE the documented model domain:
(a) Absent key: real `del d[name]` raises KeyError; model's eraseKey is a no-op. Divergence, but the issue/F2P (test_lookups_caching) always unregisters a present lookup — out of scope.
(b) Parent-MRO shadowing: real get_lookups() merges over inspect.getmro(cls); if a parent also registers lookupName, after unregistering from the subclass get_lookups() still reports it, so clauses 3-4 would fail. mapping.md EXPLICITLY scopes the model to a single class with no parent lookups (merge_dicts degenerates to class_lookups), which is exactly what the F2P test exercises (Article author field, single-class). Documented modeling boundary, not drift.
(c) cache := none faithfully models cache_clear() (empty lru-cache; the fix clears, does not re-prime).

On every in-domain input (single class, key present, unique keys, no parent lookups) the modeled function matches the real post-fix callee on all clauses. The exact-list clause 1 (vs membership-iff) is justified: Python dicts are insertion-ordered and del preserves remaining order — this is real behavior, and it correctly kills the re-prime and reorder/dup attacks without over-tightening past real behavior. Determinism lemma (proved, [propext]) confirms the spec pins both result fields exactly, so no observably-wrong same-spec impl can verify; a verifying same-spec variant is a positive control (gold-equivalent), consistent with the resolved echo-attack policy. Spec is neither too strong nor drifting from repo behavior within its declared scope. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no diff markers, no reproduced gold-patch line, no patched file path, no narration, no identifier embedding a patched symbol; the only distinctive changed symbol `unregister_lookup` is already public in the problem_statement). same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical between buggy and fixed variants, so the spec view is impl-independent. Semantically, the spec view discloses nothing beyond the SOLVER-VISIBLE problem_statement: the statement itself explicitly names the fix ('the cache is not cleared, which should be done, as it is done in register_lookup'), and the spec's clause 2 (`result.cache = none`) is exactly that publicly-requested behavior. Docstrings describe desired behavior abstractly with no bug/fix narration. The gold edit (`cls._clear_cached_lookups()`) is not leaked beyond what the public task already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.