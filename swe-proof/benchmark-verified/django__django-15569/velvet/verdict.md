# P2 adversarial audit — django__django-15569

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_prepatch.lean`, `atk_no_erase.lean`, `atk_swap.lean`, `atk_cached_registry.lean`, `atk_cached_inherited.lean`, `atk_cached_empty.lean`, `atk_ignore_inherited.lean`, `atk_clear_registry.lean`, `atk_noop.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -79,8 +79,14 @@
   ensures cached = recomputeLookups inherited registry
   do
     -- impl-start
+    -- Pre-image skeleton: the named binding is dropped from the registry, but
+    -- the cached read-through view is left at its prior value — it is NOT
+    -- re-derived from the now-current registry. The frozen spec requires the
+    -- cached view to equal `recomputeLookups inherited registry` (the view of
+    -- the registry AFTER the removal), so prove_correct MUST fail on the second
+    -- `ensures`: the stale view still exposes the removed name.
     registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
+    cached := cached
     return
     -- impl-end
 
```

Attack 2 — `atk_no_erase.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -79,7 +79,6 @@
   ensures cached = recomputeLookups inherited registry
   do
     -- impl-start
-    registry := eraseKey registry name
     cached := recomputeLookups inherited registry
     return
     -- impl-end
```

Attack 3 — `atk_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -79,8 +79,8 @@
   ensures cached = recomputeLookups inherited registry
   do
     -- impl-start
+    cached := recomputeLookups inherited registry
     registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
     return
     -- impl-end
 
```

Attack 4 — `atk_cached_registry.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -80,7 +80,7 @@
   do
     -- impl-start
     registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
+    cached := registry
     return
     -- impl-end
 
```

Attack 5 — `atk_cached_inherited.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -80,7 +80,7 @@
   do
     -- impl-start
     registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
+    cached := inherited
     return
     -- impl-end
 
```

Attack 6 — `atk_cached_empty.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -80,7 +80,7 @@
   do
     -- impl-start
     registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
+    cached := []
     return
     -- impl-end
 
```

Attack 7 — `atk_ignore_inherited.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -80,7 +80,7 @@
   do
     -- impl-start
     registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
+    cached := recomputeLookups [] registry
     return
     -- impl-end
 
```

Attack 8 — `atk_clear_registry.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -79,7 +79,7 @@
   ensures cached = recomputeLookups inherited registry
   do
     -- impl-start
-    registry := eraseKey registry name
+    registry := []
     cached := recomputeLookups inherited registry
     return
     -- impl-end
```

Attack 9 — `atk_noop.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms: the only derivation this operation defers to — the
@@ -79,8 +79,6 @@
   ensures cached = recomputeLookups inherited registry
   do
     -- impl-start
-    registry := eraseKey registry name
-    cached := recomputeLookups inherited registry
     return
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the only derivation this operation defers to — the
--  recomputation of the read-through view from the registry — is modeled
--  DEEPLY as `recomputeLookups` in the `pure` region and validated against the
--  real callee by G-AX (an A-reference), not consumed as an axiom. See
--  mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Lookup the value bound to `name` in an association list (first binding wins;
   the carriers come from real mappings, whose keys are unique). -/
def lookupKey : List (String × Nat) → String → Option Nat
  | [],             _    => none
  | (k, v) :: rest, name => if k = name then some v else lookupKey rest name

/- Whether `name` is currently bound in the registry. -/
def hasKey (reg : List (String × Nat)) (name : String) : Bool :=
  (lookupKey reg name).isSome

/- Remove every binding for `name` from an association list (keys are unique,
   so this drops exactly the one binding for `name`). -/
def eraseKey : List (String × Nat) → String → List (String × Nat)
  | [],             _    => []
  | (k, v) :: rest, name =>
      if k = name then eraseKey rest name else (k, v) :: eraseKey rest name

/- The recomputed read-through view of the registry: the registry's own
   bindings, overlaid on the inherited bindings (an inherited binding survives
   only when its key is not present in the registry). As a key→value mapping
   this is exactly "inherited defaults updated by the registry's own bindings"
   (the registry's own bindings win). Deep model of the unchanged derivation
   that builds the view; validated equal to that derivation by G-AX
   (A-reference, mapping.md §3.1), so no axiom about it is consumed. -/
def recomputeLookups (inherited registry : List (String × Nat)) : List (String × Nat) :=
  registry ++ inherited.filter (fun kv => (lookupKey registry kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- (removeBinding requires the name to be currently bound, so removing it is
--  well-defined; stated on the method below.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Remove a named binding from a registry while keeping a derived, cached
   read-through view of that registry consistent with it.

   The registry holds the bindings owned at this level; a separate cached view
   exposes those bindings overlaid on the inherited ones (the registry's own
   bindings winning), and is what callers consult. The desired behavior: drop
   the named binding from the registry AND re-derive the cached view from the
   now-current registry, so that a subsequent consultation of the cached view
   reflects the removal (the removed name is no longer exposed unless it is
   independently inherited).

   `registry` is the owned-binding store; it is genuinely mutated — the named
   binding is dropped — and its post-state is pinned EXACTLY to
   `eraseKey registryOld name` (directive 5: the changed frame is stated at its
   exact post-state). `cached` is the read-through view; it is re-derived from
   the updated registry, so it is pinned to `recomputeLookups inherited
   registry` and thereby grounded in the inputs. `inherited` is read-only. -/
method removeBinding
    (mut registry : List (String × Nat))
    (mut cached : List (String × Nat))
    (inherited : List (String × Nat))
    (name : String)
    return (u : Unit)
  require hasKey registry name = true
  ensures registry = eraseKey registryOld name
  ensures cached = recomputeLookups inherited registry
  do
    -- impl-start
    let r := eraseKey registry name
    cached := recomputeLookups inherited r
    registry := r
    return
    -- impl-end

prove_correct removeBinding by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

INSTANCE django__django-15569 — modeled op removeBinding <-> RegisterLookupMixin._unregister_lookup (django/db/models/query_utils.py). Gold patch adds cls._clear_cached_lookups() after del cls.class_lookups[lookup_name], re-syncing the cached get_lookups() view after a binding is removed. The frozen spec has TWO coupled postconditions, both fully pinning the post-state over the whole require-domain: `ensures registry = eraseKey registryOld name` (the delete) and `ensures cached = recomputeLookups inherited registry` (the re-sync, where `registry` here is the POST-delete value). Precondition is only `require hasKey registry name = true`.

same_spec=True confirmed for ALL 10 files (positive control + 9 wrong impls) via swebench_unified.markers.same_spec with backend velvet. Verify command per file: `bash scripts/lean_verify.sh <file>`,. Runs launched concurrently in 3 batches of <=4 background jobs.

### RESULTS (rc: 0=verifies, 1=error/unsolved):
- atk_pc (POSITIVE CONTROL, structurally different+correct: `let r := eraseKey registry name; cached := recomputeLookups inherited r; registry := r`): rc=0 VERIFIES -> spec non-vacuous.
- atk_prepatch (the prepatch bug: erase but `cached := cached`): rc=1, unsolved ensures_1 `cachedOld = recomputeLookups inherited (eraseKey registryOld name)` -> PREPATCH REPRODUCED on the discriminating clause (stale cached view).
- atk_no_erase (control-flow: registry left unchanged, only resync): rc=1, ensures_2 `registryOld = eraseKey registryOld name`.
- atk_swap (control-flow-effect: resync BEFORE erase -> view of stale registry): rc=1, ensures_1 `recomputeLookups inherited registryOld = recomputeLookups inherited (eraseKey registryOld name)`.
- atk_cached_registry (ungrounded-oracle echo: cached := registry, drops inherited overlay): rc=1, ensures_1 `eraseKey registryOld name = recomputeLookups ...`.
- atk_cached_inherited (ungrounded-oracle echo of a subterm: cached := inherited): rc=1, ensures_1 `inherited = recomputeLookups ...`.
- atk_cached_empty (boundary: cached := []): rc=1, ensures_1 `[] = recomputeLookups ...`.
- atk_ignore_inherited (partial-domain: cached := recomputeLookups [] registry — correct only when inherited empty): rc=1, ensures_1 `recomputeLookups [] (eraseKey...) = recomputeLookups inherited (eraseKey...)`.
- atk_clear_registry (partial-domain: registry := [] — correct only when registry was the singleton {name}): rc=1, ensures_2 `[] = eraseKey registryOld name`.
- atk_noop (no-op return): rc=1, BOTH ensures_1 and ensures_2 unsolved.

Every failure is a genuine prove_correct unsolved-goal on a discriminating ensures clause (verified by grepping the elaborator output), not a syntax/type error. Categories covered: partial-domain (ignore_inherited, clear_registry), boundary (cached_empty), control-flow-effect (no_erase, swap), ungrounded-oracle echo (cached_registry, cached_inherited), no-op.

NO verifying-wrong-impl was found, so protocol step 2 (materialize faithful patch + run_resolve) has no candidates — `patches` is intentionally empty; there is no verify-but-does-not-resolve counterexample. Ungrounded-oracle probe: recomputeLookups/lookupKey/eraseKey are concrete total deterministic functions in the pure region (not opaque/axiomatized), and the two ensures are coupled (cached pinned to the view of the POST-erase registry; registry independently pinned to the erased value), so no echo path discharges the postconditions without doing the real work.

REFINEMENT AUDIT (refinement.md): every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op). The one genuinely changed op (re-sync after delete) is modeled directly as the second assignment (A4: I up to the A-reference re-derivation); no consumed axiom. The two A-references check out and correspond to the real callees: (1) recomputeLookups deep model == real get_lookups() reverse-merge (owned wins), G-AX/axiom_check.py rc 0 per meta.json; (2) cache-invalidation plumbing _clear_cached_lookups, G-RESOLVE-exercised. G-CONF/conformance_check.py rc 0 (gold applied, seed 15569, 100,007 inputs, 0 disagreements) per meta.json.

VERDICT: G-EQ = SOUND. 9 same-spec wrong impls run (>=5 required), none verifies; positive control verifies; prepatch reproduced for the right reason; refinement.md legs all R/A-reference/I with A-references validated. Spec is functionally TIGHT (verify => correct on the require-domain).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_prepatch.lean`, `atk_no_erase.lean`, `atk_swap.lean`, `atk_cached_registry.lean`, `atk_cached_inherited.lean`, `atk_cached_empty.lean`, `atk_ignore_inherited.lean`, `atk_clear_registry.lean`, `atk_noop.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_no_erase.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_swap.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_cached_registry.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_cached_inherited.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_cached_empty.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_ignore_inherited.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_clear_registry.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_noop.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the only derivation this operation defers to — the
--  recomputation of the read-through view from the registry — is modeled
--  DEEPLY as `recomputeLookups` in the `pure` region and validated against the
--  real callee by G-AX (an A-reference), not consumed as an axiom. See
--  mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Lookup the value bound to `name` in an association list (first binding wins;
   the carriers come from real mappings, whose keys are unique). -/
def lookupKey : List (String × Nat) → String → Option Nat
  | [],             _    => none
  | (k, v) :: rest, name => if k = name then some v else lookupKey rest name

/- Whether `name` is currently bound in the registry. -/
def hasKey (reg : List (String × Nat)) (name : String) : Bool :=
  (lookupKey reg name).isSome

/- Remove every binding for `name` from an association list (keys are unique,
   so this drops exactly the one binding for `name`). -/
def eraseKey : List (String × Nat) → String → List (String × Nat)
  | [],             _    => []
  | (k, v) :: rest, name =>
      if k = name then eraseKey rest name else (k, v) :: eraseKey rest name

/- The recomputed read-through view of the registry: the registry's own
   bindings, overlaid on the inherited bindings (an inherited binding survives
   only when its key is not present in the registry). As a key→value mapping
   this is exactly "inherited defaults updated by the registry's own bindings"
   (the registry's own bindings win). Deep model of the unchanged derivation
   that builds the view; validated equal to that derivation by G-AX
   (A-reference, mapping.md §3.1), so no axiom about it is consumed. -/
def recomputeLookups (inherited registry : List (String × Nat)) : List (String × Nat) :=
  registry ++ inherited.filter (fun kv => (lookupKey registry kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- (removeBinding requires the name to be currently bound, so removing it is
--  well-defined; stated on the method below.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Remove a named binding from a registry while keeping a derived, cached
   read-through view of that registry consistent with it.

   The registry holds the bindings owned at this level; a separate cached view
   exposes those bindings overlaid on the inherited ones (the registry's own
   bindings winning), and is what callers consult. The desired behavior: drop
   the named binding from the registry AND re-derive the cached view from the
   now-current registry, so that a subsequent consultation of the cached view
   reflects the removal (the removed name is no longer exposed unless it is
   independently inherited).

   `registry` is the owned-binding store; it is genuinely mutated — the named
   binding is dropped — and its post-state is pinned EXACTLY to
   `eraseKey registryOld name` (directive 5: the changed frame is stated at its
   exact post-state). `cached` is the read-through view; it is re-derived from
   the updated registry, so it is pinned to `recomputeLookups inherited
   registry` and thereby grounded in the inputs. `inherited` is read-only. -/
method removeBinding
    (mut registry : List (String × Nat))
    (mut cached : List (String × Nat))
    (inherited : List (String × Nat))
    (name : String)
    return (u : Unit)
  require hasKey registry name = true
  ensures registry = eraseKey registryOld name
  ensures cached = recomputeLookups inherited registry
  do
    -- impl-start
    let r := eraseKey registry name
    cached := recomputeLookups inherited r
    registry := r
    return
    -- impl-end

prove_correct removeBinding by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

INSTANCE django__django-15569 — modeled op removeBinding <-> RegisterLookupMixin._unregister_lookup (django/db/models/query_utils.py). Gold patch adds cls._clear_cached_lookups() after del cls.class_lookups[lookup_name], re-syncing the cached get_lookups() view after a binding is removed. The frozen spec has TWO coupled postconditions, both fully pinning the post-state over the whole require-domain: `ensures registry = eraseKey registryOld name` (the delete) and `ensures cached = recomputeLookups inherited registry` (the re-sync, where `registry` here is the POST-delete value). Precondition is only `require hasKey registry name = true`.

same_spec=True confirmed for ALL 10 files (positive control + 9 wrong impls) via swebench_unified.markers.same_spec with backend velvet. Verify command per file: `bash scripts/lean_verify.sh <file>`,. Runs launched concurrently in 3 batches of <=4 background jobs.

### RESULTS (rc: 0=verifies, 1=error/unsolved):
- atk_pc (POSITIVE CONTROL, structurally different+correct: `let r := eraseKey registry name; cached := recomputeLookups inherited r; registry := r`): rc=0 VERIFIES -> spec non-vacuous.
- atk_prepatch (the prepatch bug: erase but `cached := cached`): rc=1, unsolved ensures_1 `cachedOld = recomputeLookups inherited (eraseKey registryOld name)` -> PREPATCH REPRODUCED on the discriminating clause (stale cached view).
- atk_no_erase (control-flow: registry left unchanged, only resync): rc=1, ensures_2 `registryOld = eraseKey registryOld name`.
- atk_swap (control-flow-effect: resync BEFORE erase -> view of stale registry): rc=1, ensures_1 `recomputeLookups inherited registryOld = recomputeLookups inherited (eraseKey registryOld name)`.
- atk_cached_registry (ungrounded-oracle echo: cached := registry, drops inherited overlay): rc=1, ensures_1 `eraseKey registryOld name = recomputeLookups ...`.
- atk_cached_inherited (ungrounded-oracle echo of a subterm: cached := inherited): rc=1, ensures_1 `inherited = recomputeLookups ...`.
- atk_cached_empty (boundary: cached := []): rc=1, ensures_1 `[] = recomputeLookups ...`.
- atk_ignore_inherited (partial-domain: cached := recomputeLookups [] registry — correct only when inherited empty): rc=1, ensures_1 `recomputeLookups [] (eraseKey...) = recomputeLookups inherited (eraseKey...)`.
- atk_clear_registry (partial-domain: registry := [] — correct only when registry was the singleton {name}): rc=1, ensures_2 `[] = eraseKey registryOld name`.
- atk_noop (no-op return): rc=1, BOTH ensures_1 and ensures_2 unsolved.

Every failure is a genuine prove_correct unsolved-goal on a discriminating ensures clause (verified by grepping the elaborator output), not a syntax/type error. Categories covered: partial-domain (ignore_inherited, clear_registry), boundary (cached_empty), control-flow-effect (no_erase, swap), ungrounded-oracle echo (cached_registry, cached_inherited), no-op.

NO verifying-wrong-impl was found, so protocol step 2 (materialize faithful patch + run_resolve) has no candidates — `patches` is intentionally empty; there is no verify-but-does-not-resolve counterexample. Ungrounded-oracle probe: recomputeLookups/lookupKey/eraseKey are concrete total deterministic functions in the pure region (not opaque/axiomatized), and the two ensures are coupled (cached pinned to the view of the POST-erase registry; registry independently pinned to the erased value), so no echo path discharges the postconditions without doing the real work.

REFINEMENT AUDIT (refinement.md): every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op). The one genuinely changed op (re-sync after delete) is modeled directly as the second assignment (A4: I up to the A-reference re-derivation); no consumed axiom. The two A-references check out and correspond to the real callees: (1) recomputeLookups deep model == real get_lookups() reverse-merge (owned wins), G-AX/axiom_check.py rc 0 per meta.json; (2) cache-invalidation plumbing _clear_cached_lookups, G-RESOLVE-exercised. G-CONF/conformance_check.py rc 0 (gold applied, seed 15569, 100,007 inputs, 0 disagreements) per meta.json.

VERDICT: G-EQ = SOUND. 9 same-spec wrong impls run (>=5 required), none verifies; positive control verifies; prepatch reproduced for the right reason; refinement.md legs all R/A-reference/I with A-references validated. Spec is functionally TIGHT (verify => correct on the require-domain).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on velvet bundle for django__django-15569. Spec region byte-identical (same_spec=True). Solution.lean verifies (exit 0); prepatch stale-view impl fails the second ensures (spec is discriminating, not vacuous). The only A-leg is the A-reference deep model recomputeLookups; ran axiom_check.py (G-AX) against the real worktree django: OK over 9 boundary + 100000 fuzz configs asserting dict(recomputeLookups(inherited,registry))==get_lookups() (real MRO reverse-merge, owned wins). Independently probed a 3-level MRO hierarchy with cross-layer key collisions + the F2P delete step: spec's {**inherited,**registry} matched real get_lookups() exactly before and after removal. Precondition require hasKey registry name mirrors del's KeyError-unless-present; inherited correctly read-only (parents untouched by _unregister_lookup); eraseKey == del cls.class_lookups[name]. No diverging input found — spec is neither too strong (precondition matches del requirement) nor drifting from real behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True); prepatch differs only in impl-region (cached := cached vs recomputeLookups) and its comment, both outside the frozen spec view. Mechanical G-LEAK screen also passes (rep.passed=True, no hard_failures).

Semantic judgment: the public problem_statement already fully discloses the gold discriminator — it states verbatim that '_unregister_lookup() should clear the lookup cache' and that 'the cache is not cleared, which should be done, as it is done in register_lookup.' So the fix (add a cache-clear after the delete so the cached read-through view reflects the removal) is public.

The spec view restates only that publicly-known idea via the second ensures (cached = recomputeLookups inherited registry) using abstract carriers (removeBinding, registry, cached, inherited). It does NOT name any gold-edit specifics: no _unregister_lookup, _clear_cached_lookups, class_lookups, get_lookups, lru_cache, or merge_dicts appear in the spec view — those repo-specific names live only in mapping.md/refinement.md (audit docs, not the screened spec view). recomputeLookups models the UNCHANGED read-through derivation (existing get_lookups overlay semantics), which is background needed to express the postcondition, not the gold edit itself, and its 'own bindings win' overlay is ordinary dict-merge behavior, not a gold-specific secret.

Conclusion: nothing in the spec view leaks the gold edit beyond what problem_statement already states. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
