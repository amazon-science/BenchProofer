# P2 adversarial audit — django__django-13089

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample exists. The single wrong-impl discriminator is on the exceeds-capacity branch: e.g. frequency=2, capacity=1, now=0, entries=[aa,bb,ca,da] all expires=5 -> 4 survivors, 4>1 fires culling, cull_num=4/2=2, boundary = ascending[2] = "ca", so the spec DEMANDS some [ca, da]. atk_4 (skip cull) yields some [aa,bb,ca,da]; atk_2 (>= cap) changes the firing threshold; atk_3 keeps wrong side of boundary; atk_6/atk_7 pick the wrong boundary; atk_8 mis-handles frequency=0; atk_1 (prepatch) returns none on the empty-boundary path (freq=1,capacity=0,entries=[(aa,5)] -> cull_num=1, offset 1 >= len 1 -> none -> spec demands some remaining but impl returns none). ALL 7 wrong impls fail to close correct_cull (exit 1); no same-spec alternative diverges from gold behavior while closing the frozen spec.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,7 +96,7 @@
     let cullNum := remaining.length / frequency
     match cullBoundary remaining cullNum with
     | some k => return some (keepAboveKey k remaining)
-    | none   => return some remaining
+    | none   => return none
   return some remaining
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
   if frequency = 0 then
     return some []
   let remaining := keepUnexpired now entries
-  if (remaining.length : Int) > capacity then
+  if (remaining.length : Int) ≥ capacity then
     let cullNum := remaining.length / frequency
     match cullBoundary remaining cullNum with
     | some k => return some (keepAboveKey k remaining)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
   if (remaining.length : Int) > capacity then
     let cullNum := remaining.length / frequency
     match cullBoundary remaining cullNum with
-    | some k => return some (keepAboveKey k remaining)
+    | some k => return some (remaining.filter (fun e => decide (k < e.key)))
     | none   => return some remaining
   return some remaining
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,11 +92,6 @@
   if frequency = 0 then
     return some []
   let remaining := keepUnexpired now entries
-  if (remaining.length : Int) > capacity then
-    let cullNum := remaining.length / frequency
-    match cullBoundary remaining cullNum with
-    | some k => return some (keepAboveKey k remaining)
-    | none   => return some remaining
   return some remaining
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,16 +88,15 @@
 -- impl-start
 def implementation_cull
     (frequency : Nat) (capacity now : Int) (entries : List Entry) :
-    Option (List Entry) := Id.run do
-  if frequency = 0 then
-    return some []
-  let remaining := keepUnexpired now entries
-  if (remaining.length : Int) > capacity then
-    let cullNum := remaining.length / frequency
-    match cullBoundary remaining cullNum with
-    | some k => return some (keepAboveKey k remaining)
-    | none   => return some remaining
-  return some remaining
+    Option (List Entry) :=
+  if frequency = 0 then some []
+  else
+    let remaining := keepUnexpired now entries
+    if (remaining.length : Int) > capacity then
+      match cullBoundary remaining (remaining.length / frequency) with
+      | some k => some (keepAboveKey k remaining)
+      | none   => some remaining
+    else some remaining
 -- impl-end
 
 -- proof-start
@@ -107,8 +106,7 @@
         (implementation_cull frequency capacity now entries) := by
   intro frequency capacity now entries
   unfold problem_spec_cull implementation_cull
-  simp only [Id.run]
-  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
+  refine ⟨fun h0 => by simp only [h0, if_true], ?_⟩
   intro hne
   simp only [hne, if_false]
   refine ⟨?_, ?_⟩
@@ -116,7 +114,6 @@
     have hgt : ¬ (↑(keepUnexpired now entries).length > capacity) := by
       simp only [not_lt]; exact hle
     simp only [hgt, if_false]
-    rfl
   · intro hgt
     simp only [hgt, if_true]
     cases h : cullBoundary (keepUnexpired now entries)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
     return some []
   let remaining := keepUnexpired now entries
   if (remaining.length : Int) > capacity then
-    let cullNum := remaining.length / frequency
+    let cullNum := (capacity.toNat) / frequency
     match cullBoundary remaining cullNum with
     | some k => return some (keepAboveKey k remaining)
     | none   => return some remaining
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,7 @@
   let remaining := keepUnexpired now entries
   if (remaining.length : Int) > capacity then
     let cullNum := remaining.length / frequency
-    match cullBoundary remaining cullNum with
+    match ((remaining.map (·.key)).mergeSort (· ≥ ·))[cullNum]? with
     | some k => return some (keepAboveKey k remaining)
     | none   => return some remaining
   return some remaining
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     (frequency : Nat) (capacity now : Int) (entries : List Entry) :
     Option (List Entry) := Id.run do
   if frequency = 0 then
-    return some []
+    return some (keepUnexpired now entries)
   let remaining := keepUnexpired now entries
   if (remaining.length : Int) > capacity then
     let cullNum := remaining.length / frequency
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Trimming a size-bounded key/value store back under its capacity.

A persistent store keeps records, each identified by a distinct `key` string and
carrying an `expires` instant. A maintenance pass reduces the store when it has
grown past its configured capacity. The pass works in well-defined stages:

  * if the maintenance frequency is configured as zero, the whole store is
    emptied;
  * otherwise every already-expired record (one whose `expires` instant lies
    strictly before the reference instant `now`) is dropped first;
  * the surviving count is then compared against the capacity. If it is within
    capacity nothing further happens. If it exceeds capacity, a culling boundary
    is chosen and every record whose key sorts strictly below that boundary is
    dropped.

The culling boundary is located by ordering the surviving keys ascending and
taking the one at offset `survivors / frequency`. When that offset addresses an
actual key, that key is the boundary and the lower keys are dropped. When the
offset lies at or beyond the number of survivors, the ordering yields no such
key; in that situation the store is left exactly as it is.

The maintenance pass always completes and reports the resulting set of surviving
records (`some …`); it never aborts.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification as an opaque
-- contract. The capacity, frequency and reference instant enter as plain data;
-- each record's key and expiry enter as plain data. The only nontrivial step is
-- locating the culling boundary, which is the offset-indexed element of the
-- ascending ordering of the surviving keys — modeled directly (sort + index),
-- not axiomatized. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A store record: a distinct key string and an expiry instant. -/
structure Entry where
  key : String
  expires : Int
deriving DecidableEq, Repr, Inhabited

/-- The records that have not yet expired at reference instant `now`: those whose
expiry instant is at or after `now` (the strictly-earlier ones are dropped). -/
def keepUnexpired (now : Int) (entries : List Entry) : List Entry :=
  entries.filter (fun e => decide (now ≤ e.expires))

/-- The culling boundary: the key at position `offset` in the ascending ordering
of the keys of `xs`, or `none` when `offset` is at or beyond the number of
records (the ordering has no such position). -/
def cullBoundary (xs : List Entry) (offset : Nat) : Option String :=
  ((xs.map (·.key)).mergeSort (· ≤ ·))[offset]?

/-- The records kept when culling below `k`: those whose key does not sort
strictly below `k` (the strictly-lower keys are dropped). -/
def keepAboveKey (k : String) (xs : List Entry) : List Entry :=
  xs.filter (fun e => !decide (e.key < k))
-- pure-end

-- post-conditions-start
/-- The maintenance pass result is pinned for every configuration:

  * zero frequency empties the store (`some []`);
  * otherwise, against `remaining` (the survivors after dropping expired
    records): when the survivor count is within capacity the store is exactly
    `remaining`; when it exceeds capacity the store is `remaining` with its
    lowest keys culled below the chosen boundary, or exactly `remaining` when the
    boundary offset addresses no key.

The result is always `some …`: the pass completes for every input. No output
component is left free. -/
def problem_spec_cull
    (frequency : Nat) (capacity now : Int) (entries : List Entry)
    (result : Option (List Entry)) : Prop :=
  let remaining := keepUnexpired now entries
  (frequency = 0 → result = some []) ∧
  (frequency ≠ 0 →
    ((remaining.length : Int) ≤ capacity → result = some remaining) ∧
    ((remaining.length : Int) > capacity →
      result = some (match cullBoundary remaining (remaining.length / frequency) with
                     | some k => keepAboveKey k remaining
                     | none   => remaining)))
-- post-conditions-end

-- impl-start
def implementation_cull
    (frequency : Nat) (capacity now : Int) (entries : List Entry) :
    Option (List Entry) := Id.run do
  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
-- impl-end

-- proof-start
theorem correct_cull :
    ∀ (frequency : Nat) (capacity now : Int) (entries : List Entry),
      problem_spec_cull frequency capacity now entries
        (implementation_cull frequency capacity now entries) := by
  intro frequency capacity now entries
  unfold problem_spec_cull implementation_cull
  simp only [Id.run]
  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
  intro hne
  simp only [hne, if_false]
  refine ⟨?_, ?_⟩
  · intro hle
    have hgt : ¬ (↑(keepUnexpired now entries).length > capacity) := by
      simp only [not_lt]; exact hle
    simp only [hgt, if_false]
    rfl
  · intro hgt
    simp only [hgt, if_true]
    cases h : cullBoundary (keepUnexpired now entries)
        ((keepUnexpired now entries).length / frequency) with
    | none => rfl
    | some k => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_cull pins `result` UNIQUELY across three exhaustive, mutually-exclusive branches (frequency=0 -> some []; freq!=0 & len<=cap -> some remaining; freq!=0 & len>cap -> some (match cullBoundary ... | some k => keepAboveKey k remaining | none => remaining)). Total functional spec, no output component free. axioms=[], deep_model_references=[] (meta.json), G-AX=skip (all R/I). No A-legs to break; the potentially-axiomatizable callees (cache_key_culling_sql, SELECT COUNT(*)) are modeled DEEPLY as mergeSort+[offset]? and .length (I/R), correctly not axiomatized. refinement.md legs all R/I, no kind-3, correspondence to real _cull else-arm verified in mapping.md/verdict.md.

SAME-SPEC: all 8 attacks + positive_control return same_spec=True (spec_view collapses BOTH impl and proof regions to placeholders, so I freely rewrote impl+proof; docstring/axioms/pure/post byte-identical).

### VERIFICATION (scripts/lean_verify.sh, 300s cap, run concurrently <=4):
- positive_control.lean: exit 0 (verifies, no sorry). #print axioms correct_cull = [propext, Classical.choice, Quot.sound] (clean, no sorryAx).
- atk_1 (prepatch bug: none-arm returns none): exit 1 -- does NOT close. PREPATCH REPRODUCED: matches Solution_prepatch.lean bug; rfl fails in the none branch (`match none ... = some (keepUnexpired ...)`).
- atk_2 (>= capacity instead of >): exit 1 -- does NOT close.
- atk_3 (control-flow-effect: keepAboveKey replaced by filter k<key, drops wrong side): exit 1 -- does NOT close.
- atk_4 (partial-domain: skip culling, always return remaining): exit 1 -- does NOT close.
- atk_5 (correct ECHO, non-Id.run control flow, hand-written proof): exit 0 -- CLOSES. #print axioms = [propext, Classical.choice, Quot.sound] (clean). Being extensionally == gold (spec pins result uniquely), its faithful patch IS the gold patch.
- atk_6 (ungrounded cull_num = capacity.toNat/frequency): exit 1 -- does NOT close.
- atk_7 (descending-sort boundary, mergeSort (>=)): exit 1 -- does NOT close.
- atk_8 (frequency=0 returns remaining not []): exit 1 -- does NOT close.

ECHO RESOLVE CHECK: atk_5 is the only attack that verifies. Its faithful refined patch (materialized at atk_5_patch.diff = the gold patch verbatim, since a closing proof against the fully-pinned spec forces extensional equality to gold) RESOLVES: meta.json G-RESOLVE=pass ('resolved'), G-GOLD=pass, patch_equals_gold=True. So the one closing-clean-axiom impl has a materialized faithful patch that DOES resolve -> no verify-not-correct break.

CONCLUSION: 8 attacks run (>=5 required), 7 distinct wrong impls all fail to close, prepatch bug reproduced, the single verifying candidate is a correct echo whose faithful patch resolves. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample exists. The single wrong-impl discriminator is on the exceeds-capacity branch: e.g. frequency=2, capacity=1, now=0, entries=[aa,bb,ca,da] all expires=5 -> 4 survivors, 4>1 fires culling, cull_num=4/2=2, boundary = ascending[2] = "ca", so the spec DEMANDS some [ca, da]. atk_4 (skip cull) yields some [aa,bb,ca,da]; atk_2 (>= cap) changes the firing threshold; atk_3 keeps wrong side of boundary; atk_6/atk_7 pick the wrong boundary; atk_8 mis-handles frequency=0; atk_1 (prepatch) returns none on the empty-boundary path (freq=1,capacity=0,entries=[(aa,5)] -> cull_num=1, offset 1 >= len 1 -> none -> spec demands some remaining but impl returns none). ALL 7 wrong impls fail to close correct_cull (exit 1); no same-spec alternative diverges from gold behavior while closing the frozen spec.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Trimming a size-bounded key/value store back under its capacity.

A persistent store keeps records, each identified by a distinct `key` string and
carrying an `expires` instant. A maintenance pass reduces the store when it has
grown past its configured capacity. The pass works in well-defined stages:

  * if the maintenance frequency is configured as zero, the whole store is
    emptied;
  * otherwise every already-expired record (one whose `expires` instant lies
    strictly before the reference instant `now`) is dropped first;
  * the surviving count is then compared against the capacity. If it is within
    capacity nothing further happens. If it exceeds capacity, a culling boundary
    is chosen and every record whose key sorts strictly below that boundary is
    dropped.

The culling boundary is located by ordering the surviving keys ascending and
taking the one at offset `survivors / frequency`. When that offset addresses an
actual key, that key is the boundary and the lower keys are dropped. When the
offset lies at or beyond the number of survivors, the ordering yields no such
key; in that situation the store is left exactly as it is.

The maintenance pass always completes and reports the resulting set of surviving
records (`some …`); it never aborts.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification as an opaque
-- contract. The capacity, frequency and reference instant enter as plain data;
-- each record's key and expiry enter as plain data. The only nontrivial step is
-- locating the culling boundary, which is the offset-indexed element of the
-- ascending ordering of the surviving keys — modeled directly (sort + index),
-- not axiomatized. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A store record: a distinct key string and an expiry instant. -/
structure Entry where
  key : String
  expires : Int
deriving DecidableEq, Repr, Inhabited

/-- The records that have not yet expired at reference instant `now`: those whose
expiry instant is at or after `now` (the strictly-earlier ones are dropped). -/
def keepUnexpired (now : Int) (entries : List Entry) : List Entry :=
  entries.filter (fun e => decide (now ≤ e.expires))

/-- The culling boundary: the key at position `offset` in the ascending ordering
of the keys of `xs`, or `none` when `offset` is at or beyond the number of
records (the ordering has no such position). -/
def cullBoundary (xs : List Entry) (offset : Nat) : Option String :=
  ((xs.map (·.key)).mergeSort (· ≤ ·))[offset]?

/-- The records kept when culling below `k`: those whose key does not sort
strictly below `k` (the strictly-lower keys are dropped). -/
def keepAboveKey (k : String) (xs : List Entry) : List Entry :=
  xs.filter (fun e => !decide (e.key < k))
-- pure-end

-- post-conditions-start
/-- The maintenance pass result is pinned for every configuration:

  * zero frequency empties the store (`some []`);
  * otherwise, against `remaining` (the survivors after dropping expired
    records): when the survivor count is within capacity the store is exactly
    `remaining`; when it exceeds capacity the store is `remaining` with its
    lowest keys culled below the chosen boundary, or exactly `remaining` when the
    boundary offset addresses no key.

The result is always `some …`: the pass completes for every input. No output
component is left free. -/
def problem_spec_cull
    (frequency : Nat) (capacity now : Int) (entries : List Entry)
    (result : Option (List Entry)) : Prop :=
  let remaining := keepUnexpired now entries
  (frequency = 0 → result = some []) ∧
  (frequency ≠ 0 →
    ((remaining.length : Int) ≤ capacity → result = some remaining) ∧
    ((remaining.length : Int) > capacity →
      result = some (match cullBoundary remaining (remaining.length / frequency) with
                     | some k => keepAboveKey k remaining
                     | none   => remaining)))
-- post-conditions-end

-- impl-start
def implementation_cull
    (frequency : Nat) (capacity now : Int) (entries : List Entry) :
    Option (List Entry) := Id.run do
  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
-- impl-end

-- proof-start
theorem correct_cull :
    ∀ (frequency : Nat) (capacity now : Int) (entries : List Entry),
      problem_spec_cull frequency capacity now entries
        (implementation_cull frequency capacity now entries) := by
  intro frequency capacity now entries
  unfold problem_spec_cull implementation_cull
  simp only [Id.run]
  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
  intro hne
  simp only [hne, if_false]
  refine ⟨?_, ?_⟩
  · intro hle
    have hgt : ¬ (↑(keepUnexpired now entries).length > capacity) := by
      simp only [not_lt]; exact hle
    simp only [hgt, if_false]
    rfl
  · intro hgt
    simp only [hgt, if_true]
    cases h : cullBoundary (keepUnexpired now entries)
        ((keepUnexpired now entries).length / frequency) with
    | none => rfl
    | some k => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_cull pins `result` UNIQUELY across three exhaustive, mutually-exclusive branches (frequency=0 -> some []; freq!=0 & len<=cap -> some remaining; freq!=0 & len>cap -> some (match cullBoundary ... | some k => keepAboveKey k remaining | none => remaining)). Total functional spec, no output component free. axioms=[], deep_model_references=[] (meta.json), G-AX=skip (all R/I). No A-legs to break; the potentially-axiomatizable callees (cache_key_culling_sql, SELECT COUNT(*)) are modeled DEEPLY as mergeSort+[offset]? and .length (I/R), correctly not axiomatized. refinement.md legs all R/I, no kind-3, correspondence to real _cull else-arm verified in mapping.md/verdict.md.

SAME-SPEC: all 8 attacks + positive_control return same_spec=True (spec_view collapses BOTH impl and proof regions to placeholders, so I freely rewrote impl+proof; docstring/axioms/pure/post byte-identical).

### VERIFICATION (scripts/lean_verify.sh, 300s cap, run concurrently <=4):
- positive_control.lean: exit 0 (verifies, no sorry). #print axioms correct_cull = [propext, Classical.choice, Quot.sound] (clean, no sorryAx).
- atk_1 (prepatch bug: none-arm returns none): exit 1 -- does NOT close. PREPATCH REPRODUCED: matches Solution_prepatch.lean bug; rfl fails in the none branch (`match none ... = some (keepUnexpired ...)`).
- atk_2 (>= capacity instead of >): exit 1 -- does NOT close.
- atk_3 (control-flow-effect: keepAboveKey replaced by filter k<key, drops wrong side): exit 1 -- does NOT close.
- atk_4 (partial-domain: skip culling, always return remaining): exit 1 -- does NOT close.
- atk_5 (correct ECHO, non-Id.run control flow, hand-written proof): exit 0 -- CLOSES. #print axioms = [propext, Classical.choice, Quot.sound] (clean). Being extensionally == gold (spec pins result uniquely), its faithful patch IS the gold patch.
- atk_6 (ungrounded cull_num = capacity.toNat/frequency): exit 1 -- does NOT close.
- atk_7 (descending-sort boundary, mergeSort (>=)): exit 1 -- does NOT close.
- atk_8 (frequency=0 returns remaining not []): exit 1 -- does NOT close.

ECHO RESOLVE CHECK: atk_5 is the only attack that verifies. Its faithful refined patch (materialized at atk_5_patch.diff = the gold patch verbatim, since a closing proof against the fully-pinned spec forces extensional equality to gold) RESOLVES: meta.json G-RESOLVE=pass ('resolved'), G-GOLD=pass, patch_equals_gold=True. So the one closing-clean-axiom impl has a materialized faithful patch that DOES resolve -> no verify-not-correct break.

CONCLUSION: 8 attacks run (>=5 required), 7 distinct wrong impls all fail to close, prepatch bug reproduced, the single verifying candidate is a correct echo whose faithful patch resolves. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled spec and the real repo callee (BaseDatabaseCache._cull, else arm) at base_commit 27c09043da / gold 580a4341cb. Evidence: (1) Solution.lean compiles clean (exit 0); #print axioms correct_cull = [propext, Classical.choice, Quot.sound] only — no sorryAx, proof is genuine and non-vacuous. (2) same_spec(Solution, Solution_prepatch, LeanBackend)=True — spec region byte-identical; only the impl none-arm (some remaining vs none) and the proof differ, i.e. the prepatch bug is confined to the impl. (3) Gold db.py _cull matches the modeled patch op-for-op: clear() on freq==0; DELETE WHERE expires<now; SELECT COUNT(*); if num>_max_entries: cull_num=num//freq; cache_key_culling_sql (ORDER BY cache_key LIMIT 1 OFFSET cull_num); if last_cache_key: DELETE WHERE cache_key<k. Every leg maps faithfully: freq=0→some [] ↔ clear(); keepUnexpired now (now≤expires) ↔ DELETE expires<now; remaining.length>capacity ↔ num>_max_entries; offset remaining.length/frequency ↔ num//_cull_frequency; cullBoundary [offset]? (0-indexed, none when offset≥count) ↔ OFFSET cull_num returning no row when cull_num>=count; keepAboveKey (key≥k) ↔ DELETE cache_key<k; the none→some remaining arm ↔ the gold 'if last_cache_key:' guard performing NO delete. (4) conformance_check.py oracle (faithful patched control-flow replica) vs shadow (op-for-op impl transliteration) agree over 120,007 inputs incl. FAIL_TO_PASS edge (empty store, capacity=-1). (5) String ordering boundary is sound universally, not just on the ASCII pool: Lean String.< and Python str both order by Unicode code point. Probed domain boundaries (negative _cull_frequency excluded by Nat per mapping bijection where int≥0; duplicate cache_key excluded by DB PK uniqueness) — both are declared out-of-domain, not repo-reachable divergences. Spec is neither too strong nor too weak: it pins the result for every input (no free component) and matches the gold behavior exactly. meta gates all pass (G-CONF pass, patch_equals_gold True, axioms=[], G-PBT skip).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical prepatch/postpatch (same_spec=True); the audited spec_view is prepatch-neutral. Lexical scan: every gold-edit/problem-statement-specific token is ABSENT from the spec view (cursor, fetchone, cache_key, cache_key_culling_sql, cull_num, NoneType/subscriptable, DELETE FROM, db.py, backends.db, last_cache_key, _max_entries, _cull_frequency, self.clear, connection.ops). The only '_cull' occurrence is the substring inside the def name 'problem_spec_cull'; 'cull' is already public vocabulary in the problem_statement (which literally cites _cull, cull_num, cache_key_culling_sql), so it does not exceed the public boundary. Vocabulary is neutral behavioral prose (size-bounded key/value store, maintenance pass, culling boundary, key/expires records). Semantic check: the spec pins the fix behavior (boundary-offset addresses no key -> none branch -> result = some remaining, store unchanged, never aborts). This behavior is ALREADY fully disclosed by the PUBLIC problem_statement, which identifies that cursor.fetchone() returns no data causing fetchone()[0] to crash and explicitly proposes 'a simple check to see if it contains data would be enough.' Thus the spec reveals nothing about the gold edit beyond the public problem_statement. NOTE: this judgment is over the public problem_statement only; hints_text is empty here and was correctly not used as a leakage baseline.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
