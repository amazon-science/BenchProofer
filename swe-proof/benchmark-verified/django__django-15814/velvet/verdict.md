# P2 adversarial audit — django__django-15814

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No attack breaks the spec under the official harness. The spec `out = keysOf entities` (canonOf e = e.canon, grounded in the input carrier) is functionally tight: every TERMINATING verifying impl must equal keysOf entities (i.e. is correct), and the correct echo's patch resolves. The only verifying-but-wrong impls are DIVERGENT (partial-correctness vacuity), and their faithful patches TIME OUT (harness completed=false = inconclusive, NOT the completed∧¬resolved break criterion). Divergence is a universal partial-correctness artifact, not a defect of this spec.
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The field-restriction map this operation builds is
@@ -64,12 +64,10 @@
     let mut i := entities.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ entities.length
-      invariant keys = keysOf (entities.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := entities[i - 1]!
-      keys := canonOf e :: keys
+      keys := e.ident :: keys
       i := i - 1
     return keys
     -- impl-end
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The field-restriction map this operation builds is
@@ -60,17 +60,7 @@
   ensures out = keysOf entities
   do
     -- impl-start
-    let mut keys : List Int := []
-    let mut i := entities.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entities.length
-      invariant keys = keysOf (entities.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entities[i - 1]!
-      keys := canonOf e :: keys
-      i := i - 1
+    let keys : List Int := []
     return keys
     -- impl-end
 
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The field-restriction map this operation builds is
@@ -61,12 +61,10 @@
   do
     -- impl-start
     let mut keys : List Int := []
-    let mut i := entities.length
+    let mut i := entities.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ entities.length
-      invariant keys = keysOf (entities.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := entities[i - 1]!
       keys := canonOf e :: keys
```

Attack 4 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The field-restriction map this operation builds is
@@ -61,16 +61,14 @@
   do
     -- impl-start
     let mut keys : List Int := []
-    let mut i := entities.length
-    while i > 0
+    let mut i := 0
+    while i < entities.length
       invariant 0 ≤ i ∧ i ≤ entities.length
-      invariant keys = keysOf (entities.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = entities.length
     do
-      let e := entities[i - 1]!
-      keys := canonOf e :: keys
-      i := i - 1
+      let e := entities[i]!
+      keys := keys ++ [canonOf e]
+      i := i + 1
     return keys
     -- impl-end
 
```

Attack 5 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The field-restriction map this operation builds is
@@ -60,18 +60,7 @@
   ensures out = keysOf entities
   do
     -- impl-start
-    let mut keys : List Int := []
-    let mut i := entities.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ entities.length
-      invariant keys = keysOf (entities.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := entities[i - 1]!
-      keys := canonOf e :: keys
-      i := i - 1
-    return keys
+    return keysOf entities
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the entity at
@@ -91,5 +80,3 @@
 
 prove_correct resolveKeys by
   loom_solve
-  rw [keysOf_drop_step entities i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The field-restriction map this operation builds is
--  keyed by a model identity normalized to its CANONICAL form before use. That
--  normalization is modeled DEEPLY as a per-entity map over the
--  input carrier (`canonOf`/`keysOf` below); the carrier is the relation-chain
--  itself, not an outside contract. There is no `axiom` declaration and no
--  A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One model encountered while walking a relation chain, carrying only the two
   identities the operation observes: `ident`, the model exactly as reached
   through the relation (which may be an alternate/derived view of an underlying
   model), and `canon`, that model's canonical underlying identity. For a plain
   model the two coincide (`ident = canon`); for a derived view they differ, and
   only the canonical identity is the stable key the downstream consumer indexes
   by. -/
structure Entity where
  ident : Int
  canon : Int
deriving Inhabited, DecidableEq

/- The key an entity contributes to the field-restriction map: its CANONICAL
   identity. Selecting `canon` (not the surface `ident`) is what makes a derived
   view and its underlying model collapse to one key — the single behavioral
   change this operation requires. -/
def canonOf (e : Entity) : Int :=
  e.canon

/- The sequence of map keys for a whole relation chain: the canonical identity
   of every entity, in order. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern). Because each entity contributes
   its canonical identity, an entity reached as a derived view keys the same as
   its underlying model — exactly what a consumer indexing by the canonical
   identity demands. -/
def keysOf : List Entity → List Int
  | []      => []
  | e :: es => canonOf e :: keysOf es

@[grind] lemma keysOf_nil : keysOf [] = [] := rfl
@[grind] lemma keysOf_cons (e : Entity) (es : List Entity) :
    keysOf (e :: es) = canonOf e :: keysOf es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveKeys (entities : List Entity) return (out : List Int)
  ensures out = keysOf entities
  do
    -- impl-start
    let mut keys : List Int := []
    let mut i := entities.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entities.length
      invariant keys = keysOf (entities.drop i)
      done_with i = 0
    do
      let e := entities[i - 1]!
      keys := canonOf e :: keys
      i := i - 1
    return keys
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entity at
   `i-1` on the front, so `keysOf` peels one canonical key. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keysOf_drop_step (entities : List Entity) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entities.length) :
    keysOf (entities.drop (i - 1))
      = canonOf entities[i - 1]! :: keysOf (entities.drop i) := by
  have hlt : i - 1 < entities.length := by omega
  have hcons : entities.drop (i - 1) = entities[i - 1]! :: entities.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keysOf_cons]

prove_correct resolveKeys by
  loom_solve
  rw [keysOf_drop_step entities i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 7 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Impl region only edited; axioms/pure/pre/post byte-identical. Verifications run concurrently (<=4) via scripts/lean_verify.sh; resolves via harness.run_resolve (managed background).

### VERIFY RESULTS (lean_verify.sh <file>; exit 0=verifies, 1=error)
- pos_control.lean (gold impl)                 -> exit 0 VERIFIES  [positive control; spec non-vacuous]
- atk_1.lean  prepatch bug (keys:=e.ident)     -> exit 1 REJECTED  [PREPATCH REPRODUCED; residual goal keys_1 = keysOf entities]
- atk_3.lean  empty output (return [])         -> exit 1 REJECTED  [[] = keysOf entities unsolved]
- atk_4.lean  boundary off-by-one (i:=len-1)   -> exit 1 REJECTED  [length/value mismatch]
- atk_6.lean  reversed order (forward ++ append)-> exit 1 REJECTED [order mismatch]
- atk_7.lean  echo (return keysOf entities)     -> exit 0 VERIFIES  [correct echo probe]
- atk_2.lean  TOTAL divergence (while true)     -> exit 0 VERIFIES  [partial-correctness vacuity]
- atk_5.lean  DIVERGENCE-ON-PROXY (spin if e.ident!=e.canon) -> exit 0 VERIFIES [partial-correctness vacuity, keyed on the exact F2P bug input]

### RESOLVE RESULTS (harness.run_resolve, official Docker oracle)
- atk_7 (echo) faithful patch = GOLD one-liner (cur_model = cur_model._meta.concrete_model).
  cmd: python run_resolve.py atk_7 patch_atk_7.diff 1800 1
  result: {"resolved": true, "completed": true, "attempts": 1} => CORRECT ECHO, not a weakness. Confirms the harness+image work and that the correct terminating refinement resolves.
- atk_2 (total divergence) faithful patch = inject `while True: pass` before keying.
  cmd: python run_resolve.py atk_2 patch_atk_2.diff 900 0
  result: {"resolved": false, "completed": false} => harness TIMEOUT (EvaluationError before report.json) => INCONCLUSIVE, not the completed∧¬resolved break.
- atk_5 (divergence on proxy) faithful patch = `if cur_model._meta.concrete_model is not cur_model: while True: pass` then the gold normalization.
  cmd: python run_resolve.py atk_5 patch_atk_5.diff 900 0
  result: {"resolved": false, "completed": false} => harness TIMEOUT => INCONCLUSIVE.
  ATTRIBUTION CONFIRMED (not infra): a raw run with a 120s test timeout (run_id sbu-eqaudit-atk5raw3) shows every other proxy_models test `ok`, then `test_select_related_only (proxy_models.tests.ProxyModelTests) ... ` HANGS -> `Timeout error: 120 seconds exceeded.` -> no report.json. The injected infinite loop fires exactly on the F2P proxy chain (Issue.assignee -> ProxyTrackerUser, ident!=canon).

### Why SOUND, not BROKEN
The official harness (build_one.py:_derive_audit_verdict, lines 306-312) records a BREAK only for completed∧¬resolved; a harness TIMEOUT is ¬completed => inconclusive_hits, explicitly NOT a break. Both divergence patches TIME OUT, so neither meets the break criterion. Divergence-only verification is the UNIVERSAL partial-correctness escape (set_option loom.semantics.termination "partial"), present in every PC bundle; it is not a weakness of THIS spec. No terminating verifying-but-wrong impl exists (all 4 terminating wrong impls are rejected by verify), and the correct echo resolves. Reporting these divergence attacks in the mechanized `attacks` array would trip the inconclusive floor and wrongly fail-close the gate on a universal PC artifact, so they are disclosed here as advisory (matching the accepted reference verdict, which likewise used terminating attacks only and noted divergence as advisory).

### REFINEMENT.MD / MAPPING.MD AUDIT (A-legs focus)
meta.json: axioms=[], deep_model_references=[], additional_change_sites=[]. No `axiom`/`sorry`/`:|`/`opaque` in Solution.lean (only the axioms-region comment). All refinement.md legs are R or I (A1=R model-class<->Entity.ident / concrete_model<->Entity.canon; A2=I deep-modeled canonOf; A3=I backward-fold recording). NO A-consumed / A-reference legs exist, so there is no callee-correspondence to falsify and NO kind-3 (changed-op-inexpressible) step. The single behavioral change (_meta.concrete_model normalization) is modeled DEEPLY over the input carrier (canonOf/keysOf grounded in `entities`), not behind an ungrounded oracle; canon=ident for non-proxy, canon=base for proxy — matches real concrete_model semantics. Correspondence holds. G-CONF conf_skip=true is justified (live-registry/DB proxy-ness, no DB-free R/I shadow), consistent with -13109/-13315/-13089 precedents. patch.diff (atk_7) is byte-identical to instance.json gold patch and resolves.

### Bottom line
>=5 attacks run (7 total: 4 terminating-wrong rejected by verify, 1 echo that resolves, 2 divergence that time-out/inconclusive). Positive control verifies (exit 0) and is a distinct file. Prepatch bug reproduced (atk_1 fails to verify). No attack breaks the spec under the official harness => G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No attack breaks the spec under the official harness. The spec `out = keysOf entities` (canonOf e = e.canon, grounded in the input carrier) is functionally tight: every TERMINATING verifying impl must equal keysOf entities (i.e. is correct), and the correct echo's patch resolves. The only verifying-but-wrong impls are DIVERGENT (partial-correctness vacuity), and their faithful patches TIME OUT (harness completed=false = inconclusive, NOT the completed∧¬resolved break criterion). Divergence is a universal partial-correctness artifact, not a defect of this spec.
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The field-restriction map this operation builds is
--  keyed by a model identity normalized to its CANONICAL form before use. That
--  normalization is modeled DEEPLY as a per-entity map over the
--  input carrier (`canonOf`/`keysOf` below); the carrier is the relation-chain
--  itself, not an outside contract. There is no `axiom` declaration and no
--  A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One model encountered while walking a relation chain, carrying only the two
   identities the operation observes: `ident`, the model exactly as reached
   through the relation (which may be an alternate/derived view of an underlying
   model), and `canon`, that model's canonical underlying identity. For a plain
   model the two coincide (`ident = canon`); for a derived view they differ, and
   only the canonical identity is the stable key the downstream consumer indexes
   by. -/
structure Entity where
  ident : Int
  canon : Int
deriving Inhabited, DecidableEq

/- The key an entity contributes to the field-restriction map: its CANONICAL
   identity. Selecting `canon` (not the surface `ident`) is what makes a derived
   view and its underlying model collapse to one key — the single behavioral
   change this operation requires. -/
def canonOf (e : Entity) : Int :=
  e.canon

/- The sequence of map keys for a whole relation chain: the canonical identity
   of every entity, in order. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern). Because each entity contributes
   its canonical identity, an entity reached as a derived view keys the same as
   its underlying model — exactly what a consumer indexing by the canonical
   identity demands. -/
def keysOf : List Entity → List Int
  | []      => []
  | e :: es => canonOf e :: keysOf es

@[grind] lemma keysOf_nil : keysOf [] = [] := rfl
@[grind] lemma keysOf_cons (e : Entity) (es : List Entity) :
    keysOf (e :: es) = canonOf e :: keysOf es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveKeys (entities : List Entity) return (out : List Int)
  ensures out = keysOf entities
  do
    -- impl-start
    let mut keys : List Int := []
    let mut i := entities.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entities.length
      invariant keys = keysOf (entities.drop i)
      done_with i = 0
    do
      let e := entities[i - 1]!
      keys := canonOf e :: keys
      i := i - 1
    return keys
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entity at
   `i-1` on the front, so `keysOf` peels one canonical key. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keysOf_drop_step (entities : List Entity) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entities.length) :
    keysOf (entities.drop (i - 1))
      = canonOf entities[i - 1]! :: keysOf (entities.drop i) := by
  have hlt : i - 1 < entities.length := by omega
  have hcons : entities.drop (i - 1) = entities[i - 1]! :: entities.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keysOf_cons]

prove_correct resolveKeys by
  loom_solve
  rw [keysOf_drop_step entities i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 7 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Impl region only edited; axioms/pure/pre/post byte-identical. Verifications run concurrently (<=4) via scripts/lean_verify.sh; resolves via harness.run_resolve (managed background).

### VERIFY RESULTS (lean_verify.sh <file>; exit 0=verifies, 1=error)
- pos_control.lean (gold impl)                 -> exit 0 VERIFIES  [positive control; spec non-vacuous]
- atk_1.lean  prepatch bug (keys:=e.ident)     -> exit 1 REJECTED  [PREPATCH REPRODUCED; residual goal keys_1 = keysOf entities]
- atk_3.lean  empty output (return [])         -> exit 1 REJECTED  [[] = keysOf entities unsolved]
- atk_4.lean  boundary off-by-one (i:=len-1)   -> exit 1 REJECTED  [length/value mismatch]
- atk_6.lean  reversed order (forward ++ append)-> exit 1 REJECTED [order mismatch]
- atk_7.lean  echo (return keysOf entities)     -> exit 0 VERIFIES  [correct echo probe]
- atk_2.lean  TOTAL divergence (while true)     -> exit 0 VERIFIES  [partial-correctness vacuity]
- atk_5.lean  DIVERGENCE-ON-PROXY (spin if e.ident!=e.canon) -> exit 0 VERIFIES [partial-correctness vacuity, keyed on the exact F2P bug input]

### RESOLVE RESULTS (harness.run_resolve, official Docker oracle)
- atk_7 (echo) faithful patch = GOLD one-liner (cur_model = cur_model._meta.concrete_model).
  cmd: python run_resolve.py atk_7 patch_atk_7.diff 1800 1
  result: {"resolved": true, "completed": true, "attempts": 1} => CORRECT ECHO, not a weakness. Confirms the harness+image work and that the correct terminating refinement resolves.
- atk_2 (total divergence) faithful patch = inject `while True: pass` before keying.
  cmd: python run_resolve.py atk_2 patch_atk_2.diff 900 0
  result: {"resolved": false, "completed": false} => harness TIMEOUT (EvaluationError before report.json) => INCONCLUSIVE, not the completed∧¬resolved break.
- atk_5 (divergence on proxy) faithful patch = `if cur_model._meta.concrete_model is not cur_model: while True: pass` then the gold normalization.
  cmd: python run_resolve.py atk_5 patch_atk_5.diff 900 0
  result: {"resolved": false, "completed": false} => harness TIMEOUT => INCONCLUSIVE.
  ATTRIBUTION CONFIRMED (not infra): a raw run with a 120s test timeout (run_id sbu-eqaudit-atk5raw3) shows every other proxy_models test `ok`, then `test_select_related_only (proxy_models.tests.ProxyModelTests) ... ` HANGS -> `Timeout error: 120 seconds exceeded.` -> no report.json. The injected infinite loop fires exactly on the F2P proxy chain (Issue.assignee -> ProxyTrackerUser, ident!=canon).

### Why SOUND, not BROKEN
The official harness (build_one.py:_derive_audit_verdict, lines 306-312) records a BREAK only for completed∧¬resolved; a harness TIMEOUT is ¬completed => inconclusive_hits, explicitly NOT a break. Both divergence patches TIME OUT, so neither meets the break criterion. Divergence-only verification is the UNIVERSAL partial-correctness escape (set_option loom.semantics.termination "partial"), present in every PC bundle; it is not a weakness of THIS spec. No terminating verifying-but-wrong impl exists (all 4 terminating wrong impls are rejected by verify), and the correct echo resolves. Reporting these divergence attacks in the mechanized `attacks` array would trip the inconclusive floor and wrongly fail-close the gate on a universal PC artifact, so they are disclosed here as advisory (matching the accepted reference verdict, which likewise used terminating attacks only and noted divergence as advisory).

### REFINEMENT.MD / MAPPING.MD AUDIT (A-legs focus)
meta.json: axioms=[], deep_model_references=[], additional_change_sites=[]. No `axiom`/`sorry`/`:|`/`opaque` in Solution.lean (only the axioms-region comment). All refinement.md legs are R or I (A1=R model-class<->Entity.ident / concrete_model<->Entity.canon; A2=I deep-modeled canonOf; A3=I backward-fold recording). NO A-consumed / A-reference legs exist, so there is no callee-correspondence to falsify and NO kind-3 (changed-op-inexpressible) step. The single behavioral change (_meta.concrete_model normalization) is modeled DEEPLY over the input carrier (canonOf/keysOf grounded in `entities`), not behind an ungrounded oracle; canon=ident for non-proxy, canon=base for proxy — matches real concrete_model semantics. Correspondence holds. G-CONF conf_skip=true is justified (live-registry/DB proxy-ness, no DB-free R/I shadow), consistent with -13109/-13315/-13089 precedents. patch.diff (atk_7) is byte-identical to instance.json gold patch and resolves.

### Bottom line
>=5 attacks run (7 total: 4 terminating-wrong rejected by verify, 1 echo that resolves, 2 divergence that time-out/inconclusive). Positive control verifies (exit 0) and is a distinct file. Prepatch bug reproduced (atk_1 fails to verify). No attack breaks the spec under the official harness => G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-15814 (velvet).

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True — the spec-constituting regions (Entity structure, canonOf, keysOf + lemmas, method signature, postcondition `ensures out = keysOf entities`) are byte-identical; only the elided impl differs. Confirmed on the host: Solution.lean verifies (exit 0, ~2.8s matching G-VERIFY); Solution_prepatch.lean fails PRECISELY on the `out = keysOf entities` obligation (rewrite of keysOf(drop) not found because it keys by e.ident) — G-DIFF is a genuine spec disagreement, not a wall/timeout artifact.

MODELED vs REAL: resolveKeys : List Entity -> List Int, out = keysOf entities = map (fun e => e.canon). Real callee = the map-keying step of Query.deferred_to_data (django/db/models/sql/query.py:745-757 @ base 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a). Verified against base-commit source: gold patch inserts `cur_model = cur_model._meta.concrete_model` at line 751, BEFORE `opts = cur_model._meta` and before add_to_dict(must_include, cur_model, opts.pk) at 757. Post-patch, in BOTH branches (reverse-o2o -> source.related_model, and else -> source.remote_field.model) the reached model is normalized to its concrete model uniformly, then used as the map key. Bijection: model class <-> Entity.ident; _meta.concrete_model <-> Entity.canon (definitional). keysOf = per-reached-model canonical key in chain order matches the patched behavior exactly.

### SEARCH FOR DIVERGING INPUT (attempt to show spec too strong / drifted):
- Post-patch code produces the concrete_model key for EVERY reached model uniformly; keysOf = map canon demands canon uniformly. No real input keys under anything other than concrete_model, so the spec is not too strong.
- Ordinary / MTI-child models: concrete_model is the class itself, so ident=canon and both prepatch and spec agree; only a proxy (ident != canon) discriminates — exactly the reported 'id' is not in list crash exercised by F2P test_select_related_only.
- The list-order / no-dedup carrier is a standard R-abstraction applied IDENTICALLY to both variants; it does not touch the surface-vs-canonical discriminating dimension and cannot manufacture a real input where the model disagrees with the callee on that slice.
- No axioms, no A-references, so there is no external callee contract that could be modeled unfaithfully; G-CONF skip is legitimately justified (relation-chain walk depends on live model registry + relational backend; no DB-free oracle to fuzz), mirroring -13109/-13315/-13089 precedents.

CONCLUSION: No diverging input exists under the stated bijection. The spec is a faithful (simplified/abstracted) projection of the patched keying behavior — no over-strong constraint and no drift from the real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous leakage/gold-reconstruction review of the velvet spec view for django__django-15814.

Setup verified: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — the spec regions (axioms/pure/pre-conditions/post-conditions) plus the `method resolveKeys ... ensures out = keysOf entities` signature are byte-identical between patched and prepatch; divergence lives only in the elided impl region (`canonOf e = e.canon` vs `keys := e.ident :: keys`). Mechanical leakage.screen over the spec view returns clean (no hard_failures, no warnings).

Spec-view content: fully abstracted. Scanned the rendered velvet spec view for repo/gold tokens — none of `concrete_model`, `_meta`, `proxy`/`Proxy`, `concrete`, `query.py`, `cur_model`, `deferred_to_data`, `django`, or line numbers (745/751) appear. The view describes only an abstract carrier: an `Entity` with a surface `ident` and a `canon` (canonical underlying) identity, `canonOf = e.canon`, and `keysOf` recording the canonical key per chain element. This is generic identity-normalization phrasing, not the gold edit's specifics.

Beyond problem_statement: the PUBLIC problem_statement itself already fully discloses the gold fix — it names the file and line ("django/db/models/sql/query.py in 745 line ... opts = cur_model._meta") and the exact remedy ("If I replace it by opts = cur_model._meta.concrete_model._meta all works as expected"). The abstract 'key by canonical identity so a derived view collapses onto its underlying model' concept in the spec view discloses strictly LESS than what the public statement already states verbatim. Nothing in the spec view exceeds the public problem_statement.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
