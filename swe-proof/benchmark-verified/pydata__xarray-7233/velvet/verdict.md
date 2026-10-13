# P2 adversarial audit — pydata__xarray-7233

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `∀ k, (k ∈ out) ↔ (k ∈ coordNames)` pins the output coordinate-name set to be membership-equal to `coordNames` exactly, independent of `requestedDims`. Any impl that verifies must therefore produce a name-set equal to the prior coordinate set, which faithfully refines (mapping.md §2 name-set↔List String bijection) to a Python `should_be_coords` set-equal to `set(self.obj.coords)` — i.e. exactly the gold behaviour, so it resolves. No verifying-but-wrong impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
   do
     -- impl-start
     let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := common
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,8 +71,7 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := requestedDims
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,8 +71,7 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result : List String := []
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,8 +71,7 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := requestedDims ++ coordNames
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,8 +71,8 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := if coordNames.isEmpty then ([] : List String)
+                  else (requestedDims.filter (fun k => coordNames.contains k)) ++ coordNames
     return result
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,8 +71,7 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := coordNames
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,8 +71,7 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := coordNames ++ (requestedDims.filter (fun k => coordNames.contains k))
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,8 +71,7 @@
   ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
   do
     -- impl-start
-    let common := requestedDims.filter (fun k => coordNames.contains k)
-    let result := common ++ coordNames
+    let result := keptCoordNames requestedDims coordNames
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- This bundle models the coordinate-name bookkeeping of the reshaping operation
   that splits a labelled-array dimension into a pair of new dimensions. A
   labelled-array container carries a set of variable names, some of which are
   distinguished as coordinate names. The reshaping rebuilds every variable under
   the new dimension layout and then re-selects which of the rebuilt names are
   coordinates. The behaviour under specification is exactly that re-selection:
   which names end up as coordinates afterwards.

   The desired guarantee is that the coordinate-name set is invariant across the
   reshaping — every name that was a coordinate beforehand is still a coordinate
   afterwards, and no new name becomes one. Names are opaque string identifiers,
   so the faithful carrier is `List String` with membership semantics; duplicate
   structure is irrelevant because only the resulting set of names is observed.
   `requestedDims` are the names of the dimensions being reshaped and `coordNames`
   the prior coordinate names. -/

-- axioms-start
-- (No consumed axioms. The re-selection is concrete set bookkeeping over
--  `List String`, spelled out in the `pure`/`impl` regions. The one neighbouring
--  callee the operation relies on — the routine that installs a chosen name-set
--  as the container's coordinates on an otherwise coordinate-free rebuild — is an
--  UNCHANGED identity on names (the resulting coordinate names equal the chosen
--  set), validated end-to-end by conformance_check.py (G-CONF) against the real
--  callee, not consumed as an axiom. Hence no library callee's `ensures` is used
--  by the proof.)
-- axioms-end

-- pure-start
/- The chosen coordinate name-set for the rebuilt container: the names common to
   the reshaped dimensions and the prior coordinates, together with all the prior
   coordinate names. Written front-recursively via `filter`/`++` so a single
   unfold is available; only membership in the result is observed. -/
def keptCoordNames (requestedDims coordNames : List String) : List String :=
  requestedDims.filter (fun k => coordNames.contains k) ++ coordNames

/- Membership characterisation: a name is among the chosen coordinates iff it was
   a prior coordinate. The common-names component is a subset of the prior
   coordinates, so unioning it back in changes nothing — the chosen set is exactly
   the prior coordinate-name set. This is the structural fact that makes the
   coordinate-name set invariant across the reshaping. -/
@[grind] lemma mem_keptCoordNames (requestedDims coordNames : List String) (k : String) :
    k ∈ keptCoordNames requestedDims coordNames ↔ k ∈ coordNames := by
  simp only [keptCoordNames, List.mem_append, List.mem_filter,
             List.contains_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, h⟩ | h) <;> exact h
  · intro h; exact Or.inr h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Re-select the coordinate names of the rebuilt container. The result must be
   exactly the prior coordinate-name set (membership-wise): every name that was a
   coordinate before is one after, and no other name is introduced. Both inputs
   describe the prior state and the request and are read-only — the operation
   builds a fresh name-set and mutates neither (directive 5). -/
method coordsToKeep (requestedDims : List String) (coordNames : List String)
    return (out : List String)
  ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
  do
    -- impl-start
    let common := requestedDims.filter (fun k => coordNames.contains k)
    let result := common ++ coordNames
    return result
    -- impl-end

prove_correct coordsToKeep by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity, A-legs focus). Byte-identical spec confirmed: same_spec=True for all 8 attacks + pos_control (velvet backend). All verifications via scripts/lean_verify.sh (300s cap), resolves via swebench_unified.harness.run_resolve (official Docker oracle, docker, image sweb.eval.x86_64.pydata_1776_xarray-7233 present).

### VERIFY RESULTS (lean_verify.sh):
- pos_control (gold-faithful `common ++ coordNames`): exit 0 VERIFIES.
- atk_1 intersection-only (== prepatch bug, `result := common`): exit 1 FAIL — prepatch reproduced; unsolved goal `k ∈ filter … requestedDims ↔ k ∈ coordNames`.
- atk_2 `requestedDims`: exit 1 FAIL (partial/wrong set).
- atk_3 `[]` empty: exit 1 FAIL (boundary).
- atk_4 `requestedDims ++ coordNames` (union too wide): exit 1 FAIL — spec's reverse direction (no new name) refutes it.
- atk_5 control-flow-effect (branch on coordNames.isEmpty; else common++coords): exit 0 VERIFIES.
- atk_6 ungrounded-oracle echo (`result := coordNames`): exit 0 VERIFIES.
- atk_7 echo variant (`coordNames ++ common`, order-swapped): exit 0 VERIFIES.
- atk_8 deep-model echo (`keptCoordNames requestedDims coordNames`): exit 0 VERIFIES.

### MANDATORY RESOLVE OF EVERY VERIFYING ATTACK (official harness):
- gold patch.diff (oracle positive control): RESOLVED=True.
- atk_5 faithful patch (branch guard, name-set == coords): RESOLVED=True.
- atk_6 faithful patch (`should_be_coords = set(self.obj.coords)`): RESOLVED=True.
- atk_7 faithful patch (`set(coords) | (window & coords)`): RESOLVED=True.
- atk_8 faithful patch (gold form `(window & coords) | coords`): RESOLVED=True.
All 4 faithful patches confirmed to apply cleanly against base_commit 51d37d1b rolling.py before harness runs.

WHY verify⇒correct HOLDS here: the postcondition is a tight set-equality to `coordNames` with no free slack; the four verifying variants differ only in surface syntax/control-flow but all compute a name-set that is set-equal to `set(self.obj.coords)`, which is exactly what the gold patch computes and what F2P test test_coarsen_construct_keeps_all_coords asserts (`list(da.coords)==list(result.coords)`). An echo of the prior coordinate set IS the fix (per 2026-08-06 policy: a resolving same-spec echo is not a weakness).

REFINEMENT.MD LEG AUDIT (A-leg focus): A1 (R, set(window_dim)↔List String), A2 (R, set(coords)↔List String), A3 (I, ∩↔filter), A4 (I, ∪↔++) — R/I legs mechanically covered by G-CONF (meta.json G-CONF pass, 1500 configs, 0 disagreements). A5 is the sole A-reference: `reshaped.set_coords(should_be_coords)` — an UNCHANGED neighbour callee, NOT consumed as an axiom (proof uses no callee ensures). Its correspondence ('result coords == chosen set' identity on coordinate-free rebuild) is validated by G-AX/axiom_check.py against the REAL xarray.Dataset.set_coords over 19 boundary + 2000 fuzz inputs (meta.json G-AX pass). No kind-3 (inexpressible-changed-op) legs: the genuinely-changed op (the set expression) is modeled deeply via keptCoordNames (I+I), not hidden behind an axiom. A-reference↔real-callee correspondence holds.

VERDICT: SOUND. 8 same-spec attacks encoded (prepatch bug + partial-domain + boundary + over-wide + control-flow-effect + 3 ungrounded-oracle/deep-model echoes); 4 verified; every verifying attack's materialized faithful patch was RUN through run_resolve and RESOLVED. No verifying wrong-impl whose faithful patch fails to resolve exists — verify⇒correct is not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `∀ k, (k ∈ out) ↔ (k ∈ coordNames)` pins the output coordinate-name set to be membership-equal to `coordNames` exactly, independent of `requestedDims`. Any impl that verifies must therefore produce a name-set equal to the prior coordinate set, which faithfully refines (mapping.md §2 name-set↔List String bijection) to a Python `should_be_coords` set-equal to `set(self.obj.coords)` — i.e. exactly the gold behaviour, so it resolves. No verifying-but-wrong impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- This bundle models the coordinate-name bookkeeping of the reshaping operation
   that splits a labelled-array dimension into a pair of new dimensions. A
   labelled-array container carries a set of variable names, some of which are
   distinguished as coordinate names. The reshaping rebuilds every variable under
   the new dimension layout and then re-selects which of the rebuilt names are
   coordinates. The behaviour under specification is exactly that re-selection:
   which names end up as coordinates afterwards.

   The desired guarantee is that the coordinate-name set is invariant across the
   reshaping — every name that was a coordinate beforehand is still a coordinate
   afterwards, and no new name becomes one. Names are opaque string identifiers,
   so the faithful carrier is `List String` with membership semantics; duplicate
   structure is irrelevant because only the resulting set of names is observed.
   `requestedDims` are the names of the dimensions being reshaped and `coordNames`
   the prior coordinate names. -/

-- axioms-start
-- (No consumed axioms. The re-selection is concrete set bookkeeping over
--  `List String`, spelled out in the `pure`/`impl` regions. The one neighbouring
--  callee the operation relies on — the routine that installs a chosen name-set
--  as the container's coordinates on an otherwise coordinate-free rebuild — is an
--  UNCHANGED identity on names (the resulting coordinate names equal the chosen
--  set), validated end-to-end by conformance_check.py (G-CONF) against the real
--  callee, not consumed as an axiom. Hence no library callee's `ensures` is used
--  by the proof.)
-- axioms-end

-- pure-start
/- The chosen coordinate name-set for the rebuilt container: the names common to
   the reshaped dimensions and the prior coordinates, together with all the prior
   coordinate names. Written front-recursively via `filter`/`++` so a single
   unfold is available; only membership in the result is observed. -/
def keptCoordNames (requestedDims coordNames : List String) : List String :=
  requestedDims.filter (fun k => coordNames.contains k) ++ coordNames

/- Membership characterisation: a name is among the chosen coordinates iff it was
   a prior coordinate. The common-names component is a subset of the prior
   coordinates, so unioning it back in changes nothing — the chosen set is exactly
   the prior coordinate-name set. This is the structural fact that makes the
   coordinate-name set invariant across the reshaping. -/
@[grind] lemma mem_keptCoordNames (requestedDims coordNames : List String) (k : String) :
    k ∈ keptCoordNames requestedDims coordNames ↔ k ∈ coordNames := by
  simp only [keptCoordNames, List.mem_append, List.mem_filter,
             List.contains_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, h⟩ | h) <;> exact h
  · intro h; exact Or.inr h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Re-select the coordinate names of the rebuilt container. The result must be
   exactly the prior coordinate-name set (membership-wise): every name that was a
   coordinate before is one after, and no other name is introduced. Both inputs
   describe the prior state and the request and are read-only — the operation
   builds a fresh name-set and mutates neither (directive 5). -/
method coordsToKeep (requestedDims : List String) (coordNames : List String)
    return (out : List String)
  ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
  do
    -- impl-start
    let common := requestedDims.filter (fun k => coordNames.contains k)
    let result := common ++ coordNames
    return result
    -- impl-end

prove_correct coordsToKeep by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity, A-legs focus). Byte-identical spec confirmed: same_spec=True for all 8 attacks + pos_control (velvet backend). All verifications via scripts/lean_verify.sh (300s cap), resolves via swebench_unified.harness.run_resolve (official Docker oracle, docker, image sweb.eval.x86_64.pydata_1776_xarray-7233 present).

### VERIFY RESULTS (lean_verify.sh):
- pos_control (gold-faithful `common ++ coordNames`): exit 0 VERIFIES.
- atk_1 intersection-only (== prepatch bug, `result := common`): exit 1 FAIL — prepatch reproduced; unsolved goal `k ∈ filter … requestedDims ↔ k ∈ coordNames`.
- atk_2 `requestedDims`: exit 1 FAIL (partial/wrong set).
- atk_3 `[]` empty: exit 1 FAIL (boundary).
- atk_4 `requestedDims ++ coordNames` (union too wide): exit 1 FAIL — spec's reverse direction (no new name) refutes it.
- atk_5 control-flow-effect (branch on coordNames.isEmpty; else common++coords): exit 0 VERIFIES.
- atk_6 ungrounded-oracle echo (`result := coordNames`): exit 0 VERIFIES.
- atk_7 echo variant (`coordNames ++ common`, order-swapped): exit 0 VERIFIES.
- atk_8 deep-model echo (`keptCoordNames requestedDims coordNames`): exit 0 VERIFIES.

### MANDATORY RESOLVE OF EVERY VERIFYING ATTACK (official harness):
- gold patch.diff (oracle positive control): RESOLVED=True.
- atk_5 faithful patch (branch guard, name-set == coords): RESOLVED=True.
- atk_6 faithful patch (`should_be_coords = set(self.obj.coords)`): RESOLVED=True.
- atk_7 faithful patch (`set(coords) | (window & coords)`): RESOLVED=True.
- atk_8 faithful patch (gold form `(window & coords) | coords`): RESOLVED=True.
All 4 faithful patches confirmed to apply cleanly against base_commit 51d37d1b rolling.py before harness runs.

WHY verify⇒correct HOLDS here: the postcondition is a tight set-equality to `coordNames` with no free slack; the four verifying variants differ only in surface syntax/control-flow but all compute a name-set that is set-equal to `set(self.obj.coords)`, which is exactly what the gold patch computes and what F2P test test_coarsen_construct_keeps_all_coords asserts (`list(da.coords)==list(result.coords)`). An echo of the prior coordinate set IS the fix (per 2026-08-06 policy: a resolving same-spec echo is not a weakness).

REFINEMENT.MD LEG AUDIT (A-leg focus): A1 (R, set(window_dim)↔List String), A2 (R, set(coords)↔List String), A3 (I, ∩↔filter), A4 (I, ∪↔++) — R/I legs mechanically covered by G-CONF (meta.json G-CONF pass, 1500 configs, 0 disagreements). A5 is the sole A-reference: `reshaped.set_coords(should_be_coords)` — an UNCHANGED neighbour callee, NOT consumed as an axiom (proof uses no callee ensures). Its correspondence ('result coords == chosen set' identity on coordinate-free rebuild) is validated by G-AX/axiom_check.py against the REAL xarray.Dataset.set_coords over 19 boundary + 2000 fuzz inputs (meta.json G-AX pass). No kind-3 (inexpressible-changed-op) legs: the genuinely-changed op (the set expression) is modeled deeply via keptCoordNames (I+I), not hidden behind an axiom. A-reference↔real-callee correspondence holds.

VERDICT: SOUND. 8 same-spec attacks encoded (prepatch bug + partial-domain + boundary + over-wide + control-flow-effect + 3 ungrounded-oracle/deep-model echoes); 4 verified; every verifying attack's materialized faithful patch was RUN through run_resolve and RESOLVED. No verifying wrong-impl whose faithful patch fails to resolve exists — verify⇒correct is not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attacker (spec-too-strong / drift-from-real-callee). Setup verified independently: same_spec(Solution, Solution_prepatch, velvet)=True (spec region byte-identical; only impl/proof differ); Solution.lean elaborates clean (lean_verify exit 0), so the spec is satisfiable. Spec: method coordsToKeep(requestedDims,coordNames) ensures ∀k, k∈out ↔ k∈coordNames.

Modeled site: Coarsen.construct coordinate re-selection (xarray/core/rolling.py:910 at base). Gold replaces `should_be_coords = set(window_dim) & set(self.obj.coords)` with `(set(window_dim) & set(coords)) | set(coords)`, which reduces algebraically to `set(self.obj.coords)` (all prior coordinate names). set_coords then installs exactly that set as the result's coords — G-AX validated the `set(result.coords)==set(chosen)` identity over 19+2000 inputs and the (W∩C)∪C==C identity over 6+20000 pairs.

Divergence hunt for real construct().coords != prior coords: (a) split dims year/month are NOT auto-promoted to coordinates (no coord vars created) → no spurious additions; (b) every variable incl. coords is reshaped and passed through, then re-flagged → no drops; (c) dimension coordinate on the coarsened dim is kept by the union → matches; (d) the DataArray F2P path (issue MVCE) asserts list(da.coords)==list(result.coords). Could not construct any input where the modeled membership set diverges from the real callee's post-construct coordinate names.

Corroboration: G-CONF ran the REAL coarsen().construct() over 1500 configs (seed=7233), including the dimension-coordinate case (~50%), n_extra 0-4, n_data 0-4 → 0 disagreements. G-EQ re-ran 7 attacks, none broke the spec; positive control verifies. G-DIFF: prepatch (result:=common, i.e. intersection only) correctly FAILS the spec's reverse direction for any prior coord not among requestedDims (the issue's `day`).

The spec is neither too strong nor drifted — it exactly characterizes the patched behavior and is the minimal faithful carrier (membership over List String). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: in Coarsen.construct (xarray/core/rolling.py:973), should_be_coords = set(window_dim) & set(self.obj.coords)  ->  (set(window_dim) & set(self.obj.coords)) | set(self.obj.coords). Behavioral discriminator: prior coordinates that are not reshaped dims must remain coordinates.

Public problem_statement ALREADY states the full desired behavior verbatim: 'All variables that were coordinates before the coarsen.construct stay as coordinates afterwards,' plus the MVCE demonstrating construct(time=("year","month")) demoting the non-dimensional coord 'day'. Hints_text is empty.

Spec-view findings:
- Mechanical G-LEAK screen (leakage.screen, velvet/lean flavor): PASSED, zero hard failures. No diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file path/module path, no spec-view identifier embedding a patched repo symbol, no narration words.
- No repo symbols appear in the view: construct, window_dim, should_be_coords, set_coords, Coarsen, rolling.py, self.obj — none present. Symbols are abstracted to requestedDims/coordNames/coordsToKeep/keptCoordNames.
- The only distinctive changed symbol in the patch is 'construct', already public via the problem statement ('coarsen.construct'), so exempt.
- same_spec(Solution.lean, Solution_prepatch.lean) = True: spec region (signature, ensures, pure model) is byte-identical between patched and pre-patch; only impl/proof bodies differ.

Judgment: The pure model keptCoordNames = (requestedDims.filter (contains coordNames)) ++ coordNames and the postcondition (forall k, k in out <-> k in coordNames) formalize exactly the behavior the PUBLIC problem_statement already demands (coordinate-name set invariant across the reshape). Comments describe behavior abstractly ('coordinate-name set is invariant across the reshaping'), naming no edit site, no pre/post expression contrast, no fix narration. This does not reveal the gold edit beyond what the public problem_statement independently provides. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
