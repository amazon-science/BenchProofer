# P2 adversarial audit — django__django-15554

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -125,10 +125,9 @@
       invariant 0 ≤ i ∧ i ≤ registry.length
       invariant result = eligibleEntries req allowed restricted (registry.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
+      let keep := (allowed.isNone || allowedMember allowed e.1) && matchesStructural e.2 req
       result := (if keep then [e.1] else []) ++ result
       i := i - 1
     return result
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -125,10 +125,9 @@
       invariant 0 ≤ i ∧ i ≤ registry.length
       invariant result = eligibleEntries req allowed restricted (registry.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
+      let keep := (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req
       result := (if keep then [e.1] else []) ++ result
       i := i - 1
     return result
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -119,19 +119,7 @@
   ensures out = eligibleEntries req allowed restricted registry
   do
     -- impl-start
-    let mut result : List Nat := []
-    let mut i := registry.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ registry.length
-      invariant result = eligibleEntries req allowed restricted (registry.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
-      result := (if keep then [e.1] else []) ++ result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -153,5 +141,3 @@
 
 prove_correct computeEligible by
   loom_solve
-  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
-  simp_all
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -119,19 +119,7 @@
   ensures out = eligibleEntries req allowed restricted registry
   do
     -- impl-start
-    let mut result : List Nat := []
-    let mut i := registry.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ registry.length
-      invariant result = eligibleEntries req allowed restricted (registry.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
-      result := (if keep then [e.1] else []) ++ result
-      i := i - 1
-    return result
+    return registry.map (·.1)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -153,5 +141,3 @@
 
 prove_correct computeEligible by
   loom_solve
-  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -125,10 +125,10 @@
       invariant 0 ≤ i ∧ i ≤ registry.length
       invariant result = eligibleEntries req allowed restricted (registry.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
+      let keep := if restrictedMode allowed restricted then matchesStructural e.2 req
+                  else (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req
       result := (if keep then [e.1] else []) ++ result
       i := i - 1
     return result
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -120,17 +120,15 @@
   do
     -- impl-start
     let mut result : List Nat := []
-    let mut i := registry.length
-    while i > 0
+    let mut i := 0
+    while i < registry.length
       invariant 0 ≤ i ∧ i ≤ registry.length
-      invariant result = eligibleEntries req allowed restricted (registry.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = registry.length
     do
-      let e := registry[i - 1]!
+      let e := registry[i]!
       let keep := entryEligible req allowed restricted e
-      result := (if keep then [e.1] else []) ++ result
-      i := i - 1
+      result := result ++ (if keep then [e.1] else [])
+      i := i + 1
     return result
     -- impl-end
 
@@ -153,5 +151,3 @@
 
 prove_correct computeEligible by
   loom_solve
-  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -125,10 +125,10 @@
       invariant 0 ≤ i ∧ i ≤ registry.length
       invariant result = eligibleEntries req allowed restricted (registry.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
+      let keep := if restricted then allowedMember allowed e.1 && matchesStructural e.2 req
+                  else (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req
       result := (if keep then [e.1] else []) ++ result
       i := i - 1
     return result
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -125,10 +125,11 @@
       invariant 0 ≤ i ∧ i ≤ registry.length
       invariant result = eligibleEntries req allowed restricted (registry.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
+      let keep := if e.2.refineTag == 0 then
+                    (allowed.isNone || allowedMember allowed e.1) && matchesStructural e.2 req
+                  else entryEligible req allowed restricted e
       result := (if keep then [e.1] else []) ++ result
       i := i - 1
     return result
```

Attack 9 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees and no deep-model reference to an unchanged callee.
@@ -119,19 +119,7 @@
   ensures out = eligibleEntries req allowed restricted registry
   do
     -- impl-start
-    let mut result : List Nat := []
-    let mut i := registry.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ registry.length
-      invariant result = eligibleEntries req allowed restricted (registry.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := registry[i - 1]!
-      let keep := entryEligible req allowed restricted e
-      result := (if keep then [e.1] else []) ++ result
-      i := i - 1
-    return result
+    return eligibleEntries req allowed restricted registry
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -153,5 +141,3 @@
 
 prove_correct computeEligible by
   loom_solve
-  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model reference to an unchanged callee.
--  The computation under specification — selecting which existing entries a
--  requested entry may share — is modeled DEEPLY below (`eligibleEntries` /
--  `entryEligible` ARE the selection). The only repository semantics it leans
--  on are the two entry-comparison relations, modeled directly as
--  `matchesStructural` / `matchesExact`; their fidelity to the real comparison
--  methods is checked executably by axiom_check.py (G-AX). See mapping.md §3.)
-- axioms-end

-- pure-start
/- A registry entry's observable identity, abstracted to exactly the two
   components the sharing decision inspects:
   * `structKey`  — the structural identity of the entry (everything that makes
                    two entries refer to "the same underlying thing").
   * `refineTag`  — an additional refinement tag that further distinguishes two
                    entries that are otherwise structurally identical. Two
                    entries can share a `structKey` yet carry different
                    `refineTag`s. Only equality of each component is ever
                    observed, so a numeric carrier is faithful (mapping.md §2). -/
structure EntryId where
  structKey : Nat
  refineTag : Nat
  deriving DecidableEq, Inhabited

/- Structural match: two entries agree on their structural identity, IGNORING
   the refinement tag. -/
def matchesStructural (a b : EntryId) : Bool := a.structKey == b.structKey

/- Exact match: two entries agree on BOTH their structural identity AND their
   refinement tag. This is strictly finer than `matchesStructural`: entries that
   differ only in their refinement tag match structurally but NOT exactly. -/
def matchesExact (a b : EntryId) : Bool :=
  a.structKey == b.structKey && a.refineTag == b.refineTag

/- Whether an id is permitted by the allowance. The allowance is either absent
   (`none` — every id permitted) or an explicit list of permitted ids. -/
def allowedMember (allowed : Option (List Nat)) (id : Nat) : Bool :=
  match allowed with
  | none   => false
  | some l => l.contains id

/- Restricted-selection mode is in force only when it is requested AND an
   explicit, non-empty allowance is supplied. An absent or empty allowance falls
   back to the default mode. -/
def restrictedMode (allowed : Option (List Nat)) (restricted : Bool) : Bool :=
  restricted && (match allowed with | none => false | some l => !l.isEmpty)

/- Whether one existing entry `(id, desc)` is eligible to be shared by the
   requested entry `req`, under the allowance and the mode flag.

   * Restricted mode: the entry must be explicitly permitted by the allowance
     AND match the request structurally (refinement tag ignored).
   * Default mode: the entry must be permitted (either the allowance is absent,
     so all are permitted, or it lists this id) AND match the request EXACTLY —
     structural identity AND refinement tag both. In particular, an existing
     entry that matches the request structurally but carries a DIFFERENT
     refinement tag is NOT eligible in default mode. -/
def entryEligible (req : EntryId) (allowed : Option (List Nat)) (restricted : Bool)
    (e : Nat × EntryId) : Bool :=
  if restrictedMode allowed restricted then
    allowedMember allowed e.1 && matchesStructural e.2 req
  else
    (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req

/- The selection: the ids of all eligible existing entries, in registry order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def eligibleEntries (req : EntryId) (allowed : Option (List Nat)) (restricted : Bool) :
    List (Nat × EntryId) → List Nat
  | []      => []
  | e :: es =>
      (if entryEligible req allowed restricted e then [e.1] else [])
        ++ eligibleEntries req allowed restricted es

@[grind] lemma eligibleEntries_nil (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) : eligibleEntries req allowed restricted [] = [] := rfl

@[grind] lemma eligibleEntries_cons (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) (e : Nat × EntryId) (es : List (Nat × EntryId)) :
    eligibleEntries req allowed restricted (e :: es)
      = (if entryEligible req allowed restricted e then [e.1] else [])
          ++ eligibleEntries req allowed restricted es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute which existing registry entries a requested entry may share.

   `registry` is the ordered list of existing entries, each an `(id, desc)`
   pair. `req` is the requested entry's identity. `allowed` is the allowance
   (`none` = every entry permitted; `some l` = only the ids in `l`). `restricted`
   requests restricted-selection mode.

   The result is the ids of the eligible entries, in registry order, as defined
   by `eligibleEntries`. The behaviour that the selection must honour: in default
   mode an existing entry is eligible only when it matches the request EXACTLY,
   so two existing entries that are structurally identical but carry different
   refinement tags are kept distinct (the request shares only the one with the
   matching tag); in restricted mode the request shares an explicitly-permitted
   entry that matches structurally.

   All four inputs are read-only — none is `mut`; the routine reads them and
   builds a fresh list, mutating nothing it is handed (directive 5). -/
method computeEligible (registry : List (Nat × EntryId)) (req : EntryId)
    (allowed : Option (List Nat)) (restricted : Bool) return (out : List Nat)
  ensures out = eligibleEntries req allowed restricted registry
  do
    -- impl-start
    let mut result : List Nat := []
    let mut i := registry.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ registry.length
      invariant result = eligibleEntries req allowed restricted (registry.drop i)
      done_with i = 0
    do
      let e := registry[i - 1]!
      let keep := entryEligible req allowed restricted e
      result := (if keep then [e.1] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `eligibleEntries` peels one entry. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma eligibleEntries_drop_step (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) (registry : List (Nat × EntryId)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ registry.length) :
    eligibleEntries req allowed restricted (registry.drop (i - 1))
      = (if entryEligible req allowed restricted registry[i - 1]! then [registry[i - 1]!.1] else [])
          ++ eligibleEntries req allowed restricted (registry.drop i) := by
  have hlt : i - 1 < registry.length := by omega
  have hcons : registry.drop (i - 1) = registry[i - 1]! :: registry.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, eligibleEntries_cons]

prove_correct computeEligible by
  loom_solve
  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinned postcondition `out = eligibleEntries req allowed restricted registry`. eligibleEntries/entryEligible are concrete pure Lean functions encoding the exact restricted/default selection rule (matchesStructural vs matchesExact; restrictedMode requires a non-empty allowance). Output is TOTALLY determined by the inputs, so the spec is maximally tight: any impl that verifies has output byte-equal to eligibleEntries, i.e. behaviorally identical to gold. axioms block is empty; no consumed axiom, no deep-model reference to an unchanged callee.

SAME-SPEC: all 10 files (atk_1..atk_8, atk_echo, atk_pos) return same_spec=True vs the frozen Solution.lean (spec_signature identical; only the impl region + prove_correct body edited).

atk_1 (prepatch bug: structural match, no restricted mode)         -> exit 1 (unsolved invariant `result = eligibleEntries ... (registry.drop i)`). PREPATCH REPRODUCED.
- atk_2 (matchesExact even in restricted mode)                        -> exit 1 (same invariant).
- atk_3 (return [])                                                   -> exit 1 (ensures_1 unsolved).
- atk_4 (return registry.map (·.1) = all ids)                         -> exit 1.
- atk_5 (restricted branch drops allowedMember; control-flow-effect)  -> exit 1.
- atk_6 (forward iteration -> reversed order; boundary/order)         -> exit 1 (order pinned).
- atk_7 (bare `restricted` instead of restrictedMode; wrong on none/empty allowance) -> exit 1.
- atk_8 (partial-domain: exact only when refineTag==0 else structural) -> exit 1.
- atk_echo (ungrounded-oracle echo: `return eligibleEntries req allowed restricted registry`) -> exit 0 VERIFIES.
- atk_pos (correct impl, original loop+proof)                         -> exit 0 VERIFIES (non-vacuity).

No VERIFYING-BUT-WRONG impl exists. The only two verifiers (atk_echo, atk_pos) both produce output == eligibleEntries, i.e. the correct selection. atk_echo is an intentional echo; because the postcondition RHS IS the correct deep model of the real selection rule (not an answer-key/oracle over hidden behavior), echoing it yields correct behavior. Its faithful refined patch is therefore the gold patch.

RESOLVE (protocol step 2 — executed, not speculated): the faithful refined patch of the sole verifying wrong-shaped attack (atk_echo) is the gold patch (behaviorally identical). Ran it through the official harness:
  cmd: run_resolve('django__django-15554', gold_patch, timeout=1800, retries=1) on benchmark swe_bench_verified (supports_docker_oracle=True)
  result: RESOLVED=True, COMPLETED=True, FLAKY=False, NOTE='resolved'.
So the materialized faithful patch of every verifying impl RESOLVES => no verify⇏/correct break.

A-LEG / model↔callee correspondence (protocol step 3): refinement.md steps A1-A8 are all R / I / A-reference; no kind-3. The only repo semantics leaned on are the two comparison methods (Join.equals, Join.__eq__), modeled directly by matchesStructural/matchesExact and validated executably:
  - G-AX (axiom_check.py) against REAL django Join objects: `G-AX OK ... 18225 boundary pairs + 20000 fuzz pairs; structural-only matches confirmed equals-True/==-False`, exit 0. Confirms equals drops filtered_relation while == keeps it (the property the whole spec turns on).
  - G-CONF (conformance_check.py) R/I shadow vs VERBATIM post-patch comprehension over REAL Join objects: `G-CONF OK ... 100002 inputs (seed=15554), 0 disagreements`, exit 0.
Both run with (base_commit worktree). patch.diff is the gold patch verbatim.

VERDICT: SOUND. ≥9 same-spec attacks encoded and verified; the 8 behaviorally-wrong ones are all rejected by the pinned postcondition; the only verifiers are behaviorally-correct and their faithful patch (= gold) resolves under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model reference to an unchanged callee.
--  The computation under specification — selecting which existing entries a
--  requested entry may share — is modeled DEEPLY below (`eligibleEntries` /
--  `entryEligible` ARE the selection). The only repository semantics it leans
--  on are the two entry-comparison relations, modeled directly as
--  `matchesStructural` / `matchesExact`; their fidelity to the real comparison
--  methods is checked executably by axiom_check.py (G-AX). See mapping.md §3.)
-- axioms-end

-- pure-start
/- A registry entry's observable identity, abstracted to exactly the two
   components the sharing decision inspects:
   * `structKey`  — the structural identity of the entry (everything that makes
                    two entries refer to "the same underlying thing").
   * `refineTag`  — an additional refinement tag that further distinguishes two
                    entries that are otherwise structurally identical. Two
                    entries can share a `structKey` yet carry different
                    `refineTag`s. Only equality of each component is ever
                    observed, so a numeric carrier is faithful (mapping.md §2). -/
structure EntryId where
  structKey : Nat
  refineTag : Nat
  deriving DecidableEq, Inhabited

/- Structural match: two entries agree on their structural identity, IGNORING
   the refinement tag. -/
def matchesStructural (a b : EntryId) : Bool := a.structKey == b.structKey

/- Exact match: two entries agree on BOTH their structural identity AND their
   refinement tag. This is strictly finer than `matchesStructural`: entries that
   differ only in their refinement tag match structurally but NOT exactly. -/
def matchesExact (a b : EntryId) : Bool :=
  a.structKey == b.structKey && a.refineTag == b.refineTag

/- Whether an id is permitted by the allowance. The allowance is either absent
   (`none` — every id permitted) or an explicit list of permitted ids. -/
def allowedMember (allowed : Option (List Nat)) (id : Nat) : Bool :=
  match allowed with
  | none   => false
  | some l => l.contains id

/- Restricted-selection mode is in force only when it is requested AND an
   explicit, non-empty allowance is supplied. An absent or empty allowance falls
   back to the default mode. -/
def restrictedMode (allowed : Option (List Nat)) (restricted : Bool) : Bool :=
  restricted && (match allowed with | none => false | some l => !l.isEmpty)

/- Whether one existing entry `(id, desc)` is eligible to be shared by the
   requested entry `req`, under the allowance and the mode flag.

   * Restricted mode: the entry must be explicitly permitted by the allowance
     AND match the request structurally (refinement tag ignored).
   * Default mode: the entry must be permitted (either the allowance is absent,
     so all are permitted, or it lists this id) AND match the request EXACTLY —
     structural identity AND refinement tag both. In particular, an existing
     entry that matches the request structurally but carries a DIFFERENT
     refinement tag is NOT eligible in default mode. -/
def entryEligible (req : EntryId) (allowed : Option (List Nat)) (restricted : Bool)
    (e : Nat × EntryId) : Bool :=
  if restrictedMode allowed restricted then
    allowedMember allowed e.1 && matchesStructural e.2 req
  else
    (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req

/- The selection: the ids of all eligible existing entries, in registry order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def eligibleEntries (req : EntryId) (allowed : Option (List Nat)) (restricted : Bool) :
    List (Nat × EntryId) → List Nat
  | []      => []
  | e :: es =>
      (if entryEligible req allowed restricted e then [e.1] else [])
        ++ eligibleEntries req allowed restricted es

@[grind] lemma eligibleEntries_nil (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) : eligibleEntries req allowed restricted [] = [] := rfl

@[grind] lemma eligibleEntries_cons (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) (e : Nat × EntryId) (es : List (Nat × EntryId)) :
    eligibleEntries req allowed restricted (e :: es)
      = (if entryEligible req allowed restricted e then [e.1] else [])
          ++ eligibleEntries req allowed restricted es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute which existing registry entries a requested entry may share.

   `registry` is the ordered list of existing entries, each an `(id, desc)`
   pair. `req` is the requested entry's identity. `allowed` is the allowance
   (`none` = every entry permitted; `some l` = only the ids in `l`). `restricted`
   requests restricted-selection mode.

   The result is the ids of the eligible entries, in registry order, as defined
   by `eligibleEntries`. The behaviour that the selection must honour: in default
   mode an existing entry is eligible only when it matches the request EXACTLY,
   so two existing entries that are structurally identical but carry different
   refinement tags are kept distinct (the request shares only the one with the
   matching tag); in restricted mode the request shares an explicitly-permitted
   entry that matches structurally.

   All four inputs are read-only — none is `mut`; the routine reads them and
   builds a fresh list, mutating nothing it is handed (directive 5). -/
method computeEligible (registry : List (Nat × EntryId)) (req : EntryId)
    (allowed : Option (List Nat)) (restricted : Bool) return (out : List Nat)
  ensures out = eligibleEntries req allowed restricted registry
  do
    -- impl-start
    let mut result : List Nat := []
    let mut i := registry.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ registry.length
      invariant result = eligibleEntries req allowed restricted (registry.drop i)
      done_with i = 0
    do
      let e := registry[i - 1]!
      let keep := entryEligible req allowed restricted e
      result := (if keep then [e.1] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `eligibleEntries` peels one entry. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma eligibleEntries_drop_step (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) (registry : List (Nat × EntryId)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ registry.length) :
    eligibleEntries req allowed restricted (registry.drop (i - 1))
      = (if entryEligible req allowed restricted registry[i - 1]! then [registry[i - 1]!.1] else [])
          ++ eligibleEntries req allowed restricted (registry.drop i) := by
  have hlt : i - 1 < registry.length := by omega
  have hcons : registry.drop (i - 1) = registry[i - 1]! :: registry.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, eligibleEntries_cons]

prove_correct computeEligible by
  loom_solve
  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinned postcondition `out = eligibleEntries req allowed restricted registry`. eligibleEntries/entryEligible are concrete pure Lean functions encoding the exact restricted/default selection rule (matchesStructural vs matchesExact; restrictedMode requires a non-empty allowance). Output is TOTALLY determined by the inputs, so the spec is maximally tight: any impl that verifies has output byte-equal to eligibleEntries, i.e. behaviorally identical to gold. axioms block is empty; no consumed axiom, no deep-model reference to an unchanged callee.

SAME-SPEC: all 10 files (atk_1..atk_8, atk_echo, atk_pos) return same_spec=True vs the frozen Solution.lean (spec_signature identical; only the impl region + prove_correct body edited).

atk_1 (prepatch bug: structural match, no restricted mode)         -> exit 1 (unsolved invariant `result = eligibleEntries ... (registry.drop i)`). PREPATCH REPRODUCED.
- atk_2 (matchesExact even in restricted mode)                        -> exit 1 (same invariant).
- atk_3 (return [])                                                   -> exit 1 (ensures_1 unsolved).
- atk_4 (return registry.map (·.1) = all ids)                         -> exit 1.
- atk_5 (restricted branch drops allowedMember; control-flow-effect)  -> exit 1.
- atk_6 (forward iteration -> reversed order; boundary/order)         -> exit 1 (order pinned).
- atk_7 (bare `restricted` instead of restrictedMode; wrong on none/empty allowance) -> exit 1.
- atk_8 (partial-domain: exact only when refineTag==0 else structural) -> exit 1.
- atk_echo (ungrounded-oracle echo: `return eligibleEntries req allowed restricted registry`) -> exit 0 VERIFIES.
- atk_pos (correct impl, original loop+proof)                         -> exit 0 VERIFIES (non-vacuity).

No VERIFYING-BUT-WRONG impl exists. The only two verifiers (atk_echo, atk_pos) both produce output == eligibleEntries, i.e. the correct selection. atk_echo is an intentional echo; because the postcondition RHS IS the correct deep model of the real selection rule (not an answer-key/oracle over hidden behavior), echoing it yields correct behavior. Its faithful refined patch is therefore the gold patch.

RESOLVE (protocol step 2 — executed, not speculated): the faithful refined patch of the sole verifying wrong-shaped attack (atk_echo) is the gold patch (behaviorally identical). Ran it through the official harness:
  cmd: run_resolve('django__django-15554', gold_patch, timeout=1800, retries=1) on benchmark swe_bench_verified (supports_docker_oracle=True)
  result: RESOLVED=True, COMPLETED=True, FLAKY=False, NOTE='resolved'.
So the materialized faithful patch of every verifying impl RESOLVES => no verify⇏/correct break.

A-LEG / model↔callee correspondence (protocol step 3): refinement.md steps A1-A8 are all R / I / A-reference; no kind-3. The only repo semantics leaned on are the two comparison methods (Join.equals, Join.__eq__), modeled directly by matchesStructural/matchesExact and validated executably:
  - G-AX (axiom_check.py) against REAL django Join objects: `G-AX OK ... 18225 boundary pairs + 20000 fuzz pairs; structural-only matches confirmed equals-True/==-False`, exit 0. Confirms equals drops filtered_relation while == keeps it (the property the whole spec turns on).
  - G-CONF (conformance_check.py) R/I shadow vs VERBATIM post-patch comprehension over REAL Join objects: `G-CONF OK ... 100002 inputs (seed=15554), 0 disagreements`, exit 0.
Both run with (base_commit worktree). patch.diff is the gold patch verbatim.

VERDICT: SOUND. ≥9 same-spec attacks encoded and verified; the 8 behaviorally-wrong ones are all rejected by the pinned postcondition; the only verifiers are behaviorally-correct and their faithful patch (= gold) resolves under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on computeEligible (models post-patch reuse_aliases candidate computation in Query.join, query.py:1014/1027; base commit 59ab3fd0e9).

Spec integrity: same_spec(Solution, Solution_prepatch, velvet backend) = True (spec region byte-identical/frozen); lean_verify.sh Solution.lean -> exit 0.

Source-level fidelity confirmed against the real repo:
- Join.equals (datastructures.py:164) = identity[:-1] equality, dropping filtered_relation -> matchesStructural (structKey only). CONFIRMED in worktree source.
- Join.__eq__ (datastructures.py:156) = full identity equality (filtered_relation included) -> matchesExact (structKey + refineTag). CONFIRMED.
- Default branch (allowed.isNone||member)&&matchesExact <-> (reuse is None or a in reuse) and j==join; restricted branch member&&matchesStructural <-> a in reuse and j.equals(join). Exact transliteration.
- restrictedMode = restricted && (allowance present & non-empty) exactly mirrors Python truthiness `reuse_with_filtered_relation and reuse` (None and empty set both falsy -> default branch). CONFIRMED in query.py source.
- Order preserved (registry order = alias_map.items() insertion order); all the unchanged downstream (reuse_aliases[-1]) consumes.

DID NOT trust G-CONF: ran an INDEPENDENT 300,000-input differential fuzz (seed 999, distinct from the pinned 15554) against the real callee in a fresh base-commit worktree (@ 59ab3fd0e9). Deliberately targeted the coverage gap the panel flagged: heterogeneous registries mixing BaseTable and Join objects, cross-type requests (BaseTable request vs Join entries and vice versa), duplicate/==-equal FilteredRelation instances, None reuse, empty-set reuse, random reuse subsets, both flag values. RESULT: total=300000, bad=0 divergences. BaseTable.__eq__/equals return NotImplemented/False against Join (verified in source), faithfully reproduced by distinct Nat carriers -> a BaseTable maps to a unique (structKey,refineTag) that matches no Join, introducing no divergence.

The spec pins the full ordered eligible-id list over the entire (reuse, restricted) input space -- tight but not too strong; it agrees with the real callee on every input tested including adversarial heterogeneous shapes. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently regenerated the velvet spec view (impl + prove_correct proof elided) via markers.spec_view; spec_view sha256=b4b389b0…0601a4a, byte-identical to meta.json G-HYGIENE.region_hashes.spec_view, and same_spec(Solution, Solution_prepatch)=True (spec frozen, prepatch-shared — encodes no post-patch-only content). Mechanical leakage.screen against the REAL problem_statement passes (0 hard failures). No repo localization anywhere in the view: no query.py / alias_map / reuse_aliases / Join / .equals / __eq__ / FilteredRelation / reuse_with_filtered_relation / datastructures, no file paths, no diff markers, no quoted gold-patch/problem-statement phrasing; comment refs point only to internal audit docs (mapping.md/plan §). Substantively, the discriminating concept — structurally-identical entries with different refinement tags must be kept distinct (matchesExact vs matchesStructural) — is exactly what the public problem_statement already discloses ('multiple FilteredRelation with different filters but for same relation is ignored … single SQL JOIN'), so it is NOT disclosed beyond public. The gold patch's second coordinated change (new reuse_with_filtered_relation restricted branch) is abstracted to a generic 'restricted' flag + 'allowed' allowance specified over the entire (allowed, restricted) input space — a behaviour contract, not a reconstruction of the concrete repo hunk, parameter name, file, or function. A spec necessarily encodes correct behaviour; that is intrinsic, not leakage of the edit. Nothing in the view reconstructs the gold edit beyond the public problem_statement. Concur with recorded G-PANEL-3 pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
