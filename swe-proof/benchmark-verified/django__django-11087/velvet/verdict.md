# P2 adversarial audit — django__django-11087

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,7 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    return allColumns
     -- impl-end
 
 prove_correct columnsToFetch by
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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,7 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    return referencedColumns
     -- impl-end
 
 prove_correct columnsToFetch by
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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,8 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    let narrow : Bool := !(preDelete || postDelete)
+    if narrow then return referencedColumns else return allColumns
     -- impl-end
 
 prove_correct columnsToFetch by
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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,8 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    let narrow : Bool := !widenedFetch
+    if narrow then return referencedColumns else return allColumns
     -- impl-end
 
 prove_correct columnsToFetch by
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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,8 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    let narrow : Bool := !(widenedFetch && (preDelete || postDelete))
+    if narrow then return referencedColumns else return allColumns
     -- impl-end
 
 prove_correct columnsToFetch by
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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,8 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
     let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    if narrow then return allColumns else return referencedColumns
     -- impl-end
 
 prove_correct columnsToFetch by
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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,8 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    let narrow : Bool := !(widenedFetch || preDelete)
+    if narrow then return referencedColumns else return allColumns
     -- impl-end
 
 prove_correct columnsToFetch by
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The decision modeled here is a closed boolean
@@ -76,13 +76,7 @@
   ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
   do
     -- impl-start
-    -- Narrow to the referenced columns only when the fetch was not widened and
-    -- no exposing subscriber is registered; otherwise keep the full column set.
-    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
-    if narrow then
-      return referencedColumns
-    else
-      return allColumns
+    return columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete
     -- impl-end
 
 prove_correct columnsToFetch by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a closed boolean
--  function of its inputs, and the field set it returns is one of two input
--  lists. The predicate that observes whether change-notification subscribers
--  are registered for a model is itself an added helper, modeled DEEPLY in the
--  `pure` region as the disjunction of its two boolean observations; its
--  callees (the per-kind subscriber-presence queries) are abstracted to the two
--  boolean inputs `preDelete`/`postDelete` (an R refinement, validated against
--  the real registry by conformance_check.py / G-CONF). Nothing is consumed as
--  an axiom — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether any change-notification subscriber that would expose the about-to-be
   removed rows to user code is registered for a model. Two kinds matter: a
   subscriber notified just before removal, and one notified just after. The
   predicate holds iff at least one of the two is present. (Subscribers for the
   set-membership-changed notification are deliberately NOT consulted here: such
   a subscriber never receives the rows under consideration, so it places no
   requirement on which columns are fetched.) -/
@[grind] def hasExposingSubscriber (preDelete postDelete : Bool) : Bool :=
  preDelete || postDelete

/- Whether the column set fetched for the dependent rows may be narrowed to the
   referenced columns only. Narrowing is permitted exactly when the fetch was
   NOT widened to also pull in further related rows (which would make the
   interaction between the two narrowings hard to get right) AND no exposing
   subscriber is registered (which could hand the rows to user code, where any
   column might be read). -/
@[grind] def mayNarrow (widenedFetch preDelete postDelete : Bool) : Bool :=
  !(widenedFetch || hasExposingSubscriber preDelete postDelete)

/- The set of columns actually fetched for the dependent rows. When narrowing is
   permitted, only the referenced columns are fetched; otherwise the full set of
   columns is fetched. `allColumns` and `referencedColumns` model the two column
   sets as identifier lists (mapping.md §2); `referencedColumns ⊆ allColumns` in
   the repo, but the desired behaviour pins the exact set returned, so the model
   needs no subset hypothesis. -/
@[grind] def columnsFetched (allColumns referencedColumns : List Nat)
    (widenedFetch preDelete postDelete : Bool) : List Nat :=
  if mayNarrow widenedFetch preDelete postDelete then referencedColumns
  else allColumns
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choosing which columns to fetch for a batch of dependent rows that must be
   visited to remove them. The desired behaviour: fetch only the columns that
   are actually referenced (a strict optimisation that avoids decoding columns
   the visit never needs) UNLESS either the fetch was widened to also pull in
   further related rows, or a change-notification subscriber that could expose
   the rows to user code is registered for the dependent model — in either of
   those cases the full column set must be fetched.

   All five inputs are read-only (none `mut`): the routine inspects the two
   candidate column lists and the three boolean conditions and decides; it
   mutates none of them (directive 5). The two boolean subscriber observations
   are combined exactly as `hasExposingSubscriber` (the added predicate), and the
   narrowing decision and resulting column set are pinned exactly by `mayNarrow`
   / `columnsFetched`. -/
method columnsToFetch (allColumns : List Nat) (referencedColumns : List Nat)
    (widenedFetch : Bool) (preDelete : Bool) (postDelete : Bool) return (out : List Nat)
  ensures out = columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete
  ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
  do
    -- impl-start
    -- Narrow to the referenced columns only when the fetch was not widened and
    -- no exposing subscriber is registered; otherwise keep the full column set.
    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
    if narrow then
      return referencedColumns
    else
      return allColumns
    -- impl-end

prove_correct columnsToFetch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: columnsToFetch has a tight, TOTAL functional postcondition `out = columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete` (columnsFetched = if mayNarrow then referencedColumns else allColumns; mayNarrow = !(widenedFetch || preDelete || postDelete)), plus a tautological second ensures. No preconditions => no partial domain to exploit; any impl must reproduce the exact function on ALL boolean/list inputs.

ATTACKS (all same_spec=True vs Solution.lean, confirmed via swebench_unified.markers.same_spec; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 `return allColumns` (= prepatch always-full-fetch, prepatch bug) -> exit 1, unsolved goal `allColumns = columnsFetched ...`. PREPATCH REPRODUCED.
- atk_2 `return referencedColumns` (always narrow) -> exit 1.
- atk_3 guard drops widenedFetch `!(preDelete||postDelete)` (partial-domain) -> exit 1.
- atk_4 guard drops subscribers `!widenedFetch` (partial-domain) -> exit 1.
- atk_5 boundary/operator swap `!(widenedFetch && (preDelete||postDelete))` -> exit 1.
- atk_6 control-flow-effect: branches swapped (narrow->allColumns else referencedColumns) -> exit 1.
- atk_7 drops postDelete term `!(widenedFetch||preDelete)` -> exit 1.
- atk_8 ungrounded-oracle echo `return columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete` -> exit 0 (VERIFIES). All 7 wrong impls (atk_1..7) fail with genuine `unsolved goals` on the exact functional postcondition (not syntax errors) — verified from logs.

Positive control pc.lean (bundle Solution.lean impl) -> exit 0 (verifies).

RESOLVE (protocol step 2): the sole verifying wrong impl is atk_8, an oracle echo whose body IS columnsFetched, i.e. behaviorally identical to the gold decision (referenced-only iff mayNarrow, else full). Its faithful refined patch is therefore the gold patch verbatim (materialized as atk_8.patch = benchmark-verified/.../patch.diff). RAN it: `run_resolve('django__django-11087', atk_8.patch, run_id='sbu-resolve-audit-eq-nyuaqi6f-atk8', timeout=1800, retries=1)` => RESOLVED=True COMPLETED=True NOTE='resolved'. The verifying impl's faithful patch RESOLVES => no verify⇏correct break. This is exactly the 2026-08-06 policy case (resolving echo of gold is NOT a weakness).

REFINEMENT.MD AUDIT (step 3): claims NO A-legs; meta.json corroborates axioms=[] and deep_model_references=[]. Every leg is R (A1 column-set/List Nat; A2 select_related/widenedFetch; A3 pre/post has_listeners/Bool) or I-deep-model (A4 mayNarrow guard; A5 columnsFetched column choice; B1 _has_signal_listeners = pre||post). No kind-3 (inexpressible-changed-op) legs. R/I legs are mechanically covered by G-CONF (conformance_check.py present, seed 11087). The intentional exclusion of m2m_changed from the narrowing predicate is justified & bounded to the narrowing site (F2P test_only_referenced_fields_selected observes only the emitted SELECT column list). Model↔patch correspondence holds.

VERDICT: SOUND. 8 distinct attacks run (>=5); 7 correctly rejected by verification with genuine spec-violation goals; the 1 verifying attack (gold-equivalent oracle echo) had its faithful patch executed through the official Docker harness and RESOLVED. No verifying-but-unresolving impl exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a closed boolean
--  function of its inputs, and the field set it returns is one of two input
--  lists. The predicate that observes whether change-notification subscribers
--  are registered for a model is itself an added helper, modeled DEEPLY in the
--  `pure` region as the disjunction of its two boolean observations; its
--  callees (the per-kind subscriber-presence queries) are abstracted to the two
--  boolean inputs `preDelete`/`postDelete` (an R refinement, validated against
--  the real registry by conformance_check.py / G-CONF). Nothing is consumed as
--  an axiom — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether any change-notification subscriber that would expose the about-to-be
   removed rows to user code is registered for a model. Two kinds matter: a
   subscriber notified just before removal, and one notified just after. The
   predicate holds iff at least one of the two is present. (Subscribers for the
   set-membership-changed notification are deliberately NOT consulted here: such
   a subscriber never receives the rows under consideration, so it places no
   requirement on which columns are fetched.) -/
@[grind] def hasExposingSubscriber (preDelete postDelete : Bool) : Bool :=
  preDelete || postDelete

/- Whether the column set fetched for the dependent rows may be narrowed to the
   referenced columns only. Narrowing is permitted exactly when the fetch was
   NOT widened to also pull in further related rows (which would make the
   interaction between the two narrowings hard to get right) AND no exposing
   subscriber is registered (which could hand the rows to user code, where any
   column might be read). -/
@[grind] def mayNarrow (widenedFetch preDelete postDelete : Bool) : Bool :=
  !(widenedFetch || hasExposingSubscriber preDelete postDelete)

/- The set of columns actually fetched for the dependent rows. When narrowing is
   permitted, only the referenced columns are fetched; otherwise the full set of
   columns is fetched. `allColumns` and `referencedColumns` model the two column
   sets as identifier lists (mapping.md §2); `referencedColumns ⊆ allColumns` in
   the repo, but the desired behaviour pins the exact set returned, so the model
   needs no subset hypothesis. -/
@[grind] def columnsFetched (allColumns referencedColumns : List Nat)
    (widenedFetch preDelete postDelete : Bool) : List Nat :=
  if mayNarrow widenedFetch preDelete postDelete then referencedColumns
  else allColumns
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choosing which columns to fetch for a batch of dependent rows that must be
   visited to remove them. The desired behaviour: fetch only the columns that
   are actually referenced (a strict optimisation that avoids decoding columns
   the visit never needs) UNLESS either the fetch was widened to also pull in
   further related rows, or a change-notification subscriber that could expose
   the rows to user code is registered for the dependent model — in either of
   those cases the full column set must be fetched.

   All five inputs are read-only (none `mut`): the routine inspects the two
   candidate column lists and the three boolean conditions and decides; it
   mutates none of them (directive 5). The two boolean subscriber observations
   are combined exactly as `hasExposingSubscriber` (the added predicate), and the
   narrowing decision and resulting column set are pinned exactly by `mayNarrow`
   / `columnsFetched`. -/
method columnsToFetch (allColumns : List Nat) (referencedColumns : List Nat)
    (widenedFetch : Bool) (preDelete : Bool) (postDelete : Bool) return (out : List Nat)
  ensures out = columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete
  ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)
  do
    -- impl-start
    -- Narrow to the referenced columns only when the fetch was not widened and
    -- no exposing subscriber is registered; otherwise keep the full column set.
    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
    if narrow then
      return referencedColumns
    else
      return allColumns
    -- impl-end

prove_correct columnsToFetch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: columnsToFetch has a tight, TOTAL functional postcondition `out = columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete` (columnsFetched = if mayNarrow then referencedColumns else allColumns; mayNarrow = !(widenedFetch || preDelete || postDelete)), plus a tautological second ensures. No preconditions => no partial domain to exploit; any impl must reproduce the exact function on ALL boolean/list inputs.

ATTACKS (all same_spec=True vs Solution.lean, confirmed via swebench_unified.markers.same_spec; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 `return allColumns` (= prepatch always-full-fetch, prepatch bug) -> exit 1, unsolved goal `allColumns = columnsFetched ...`. PREPATCH REPRODUCED.
- atk_2 `return referencedColumns` (always narrow) -> exit 1.
- atk_3 guard drops widenedFetch `!(preDelete||postDelete)` (partial-domain) -> exit 1.
- atk_4 guard drops subscribers `!widenedFetch` (partial-domain) -> exit 1.
- atk_5 boundary/operator swap `!(widenedFetch && (preDelete||postDelete))` -> exit 1.
- atk_6 control-flow-effect: branches swapped (narrow->allColumns else referencedColumns) -> exit 1.
- atk_7 drops postDelete term `!(widenedFetch||preDelete)` -> exit 1.
- atk_8 ungrounded-oracle echo `return columnsFetched allColumns referencedColumns widenedFetch preDelete postDelete` -> exit 0 (VERIFIES). All 7 wrong impls (atk_1..7) fail with genuine `unsolved goals` on the exact functional postcondition (not syntax errors) — verified from logs.

Positive control pc.lean (bundle Solution.lean impl) -> exit 0 (verifies).

RESOLVE (protocol step 2): the sole verifying wrong impl is atk_8, an oracle echo whose body IS columnsFetched, i.e. behaviorally identical to the gold decision (referenced-only iff mayNarrow, else full). Its faithful refined patch is therefore the gold patch verbatim (materialized as atk_8.patch = benchmark-verified/.../patch.diff). RAN it: `run_resolve('django__django-11087', atk_8.patch, run_id='sbu-resolve-audit-eq-nyuaqi6f-atk8', timeout=1800, retries=1)` => RESOLVED=True COMPLETED=True NOTE='resolved'. The verifying impl's faithful patch RESOLVES => no verify⇏correct break. This is exactly the 2026-08-06 policy case (resolving echo of gold is NOT a weakness).

REFINEMENT.MD AUDIT (step 3): claims NO A-legs; meta.json corroborates axioms=[] and deep_model_references=[]. Every leg is R (A1 column-set/List Nat; A2 select_related/widenedFetch; A3 pre/post has_listeners/Bool) or I-deep-model (A4 mayNarrow guard; A5 columnsFetched column choice; B1 _has_signal_listeners = pre||post). No kind-3 (inexpressible-changed-op) legs. R/I legs are mechanically covered by G-CONF (conformance_check.py present, seed 11087). The intentional exclusion of m2m_changed from the narrowing predicate is justified & bounded to the narrowing site (F2P test_only_referenced_fields_selected observes only the emitted SELECT column list). Model↔patch correspondence holds.

VERDICT: SOUND. 8 distinct attacks run (>=5); 7 correctly rejected by verification with genuine spec-violation goals; the 1 verifying attack (gold-equivalent oracle echo) had its faithful patch executed through the official Docker harness and RESOLVED. No verifying-but-unresolving impl exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-11087 velvet bundle.

### Setup confirmed
- Spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(sol, prepatch, LeanTables) = True. The only diff is the impl region (prepatch = unconditional `return allColumns`; solution = the guarded narrowing). Frozen spec is legitimate.
- Solution.lean verifies (lean_verify.sh exit 0); Solution_prepatch.lean fails verification (G-DIFF pass), i.e. the spec is discriminating, not vacuous.

### MODELED FUNCTION vs REAL PATCHED CALLEE (Collector.collect narrowing site + _has_signal_listeners, django/db/models/deletion.py @ gold patch):
- Real guard: narrow (apply .only(referenced_fields)) iff `not (sub_objs.query.select_related or self._has_signal_listeners(related_model))`, where `_has_signal_listeners = signals.pre_delete.has_listeners or signals.post_delete.has_listeners` (m2m_changed DROPPED — verified against gold patch hunk).
- Model: mayNarrow = !(widenedFetch || (preDelete||postDelete)); columnsFetched = referencedColumns if mayNarrow else allColumns; hasExposingSubscriber = preDelete||postDelete.
- Exhaustive boolean truth-table over all 8 configs of (widenedFetch, preDelete, postDelete): mayNarrow ≡ not(select_related or pre or post) on every input; column choice (referenced vs full) matches the patched code on every config. No divergence found.
- The m2m_changed exclusion is faithful: the patched narrowing guard uses _has_signal_listeners (pre/post only), NOT the old can_fast_delete 3-way test. Model correctly omits m2m.
- Type refinement: column sets ↔ List Nat (identity-only observation, faithful carrier since only set membership/identity is observed); select_related truthiness ↔ Bool; has_listeners ↔ Bool. These are R-refinements validated by G-CONF (100016 inputs, seed 11087, 0 disagreements against the REAL patched _has_signal_listeners + signals registry).
- No axiomatized callee is modeled more strongly than reality (axioms=[], deep_model_references=[]). The two callees (_has_signal_listeners, .only/select_related) are modeled deeply as closed functions matching their real bodies, not abstracted behind an over-strong contract.
- Second postcondition `hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)` is a definitional tautology — adds no strength, cannot cause drift.

CONCLUSION: The spec is neither too strong nor drifted. No input exists where the modeled function disagrees with the real patched callee. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction assessment for velvet Solution.lean spec view (django__django-11087).

MECHANICAL: leakage.screen() PASSES with zero hard failures. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical). Impl and prove_correct bodies are elided in the projected spec view.

SPEC-VIEW CONTENT (what the consumer sees): the axioms comment block, the three pure defs (hasExposingSubscriber/mayNarrow/columnsFetched) with their doc-comments, the method signature columnsToFetch with two `ensures` clauses, and elided impl/proof.

NO REPO ARTIFACTS LEAK: spec view contains none of the gold-edit specifics — no file path deletion.py, no changed symbols (_has_signal_listeners, can_fast_delete, collect), no select_related / signals / pre_delete / post_delete / m2m / .only / sub_objs / on_delete / related_model / referenced_fields / get_candidate_relations_to_delete, no django module path, no diff markers, and no gold-patch code line reproduced (verified programmatically). All repo↔Lean binding (the map from widenedFetch->select_related, preDelete/postDelete->signal listeners, .only->referencedColumns, and the collect narrowing site) lives ONLY in mapping.md/refinement.md, which are NOT part of the consumer spec view.

NO NARRATION: no bug/fix/patch/previously/incorrectly/broken-style terms in spec-view comments.

vs PROBLEM_STATEMENT: the public problem_statement already states the intent explicitly — 'Optimize .delete() to use only required fields' and 'Django shouldn't be fetching that field ... not actually needed for the .delete()'. The spec view expresses exactly this desired behavior at an abstract level (fetch only referenced columns UNLESS the fetch was widened or an exposing subscriber is registered, in which case fetch the full set). The two guard conditions (widened fetch, subscriber presence) are the *specification of correct behavior* rendered as opaque boolean inputs and List Nat carriers — they do not name the repo mechanism, do not reconstruct the gold edit, and do not remove the solver's obligation to locate the collect site and wire the real select_related/signals observations. Encoding the correct post-condition is a spec's proper job, not a leak.

CONCLUSION: The spec view does not leak the gold edit beyond the public problem_statement (hints_text not consulted). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
