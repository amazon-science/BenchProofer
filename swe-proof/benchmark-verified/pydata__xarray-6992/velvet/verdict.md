# P2 adversarial audit — pydata__xarray-6992

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk1_partialdom.lean`, `atk2_boundary.lean`, `atk3_cfeffect.lean`, `atk5_nonmulti_swap.lean`, `atk7_convpath.lean`, `atk8_emptyreturn.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4_echo.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,41 +161,25 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
+let mut dropVars : List String := []
     let mut newVars : List String := []
     let mut newIdx : List String := []
     if isMulti then
       let keepLevels := levels.filter (fun k => !R.contains k)
-      if (!R.contains dim) && !keepLevels.isEmpty then
-        let resetLevels := levels.filter (fun k => R.contains k)
-        if keepLevels.length == 1 then
-          dropVars := keepLevels
-          newVars := [dim]
-          newIdx := [dim]
-          if dropF then
-            dropVars := dropVars ++ resetLevels
-          else
-            newVars := newVars ++ resetLevels
-        else
-          newVars := keepLevels
-          newIdx := keepLevels ++ [dim]
-          if dropF then
-            dropVars := resetLevels
-          else
-            newVars := newVars ++ resetLevels
+      let resetLevels := levels.filter (fun k => R.contains k)
+      if (!resetLevels.isEmpty) && !keepLevels.isEmpty then
+        newVars := keepLevels
+        newIdx := keepLevels
       else
-        dropVars := [dim]
-        if dropF then
-          dropVars := dropVars ++ levels
-        else
-          newVars := levels
+        newIdx := []
     else
-      if dropF then
-        dropVars := [dim]
-      else
-        newVars := [dim]
+      newIdx := []
+    if dropF then
+      dropVars := R
+    else
+      dropVars := []
     let variables2 := filterOut dropVars V ++ newVars
-    let coord2 := filterOut dropVars C
+    let coord2 := C ++ newVars
     return { vars := variables2, coords := coord2, idxs := newIdx }
     -- impl-end
 
```

Attack 2 — `atk1_partialdom.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,7 +161,7 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
+let mut dropVars : List String := []
     let mut newVars : List String := []
     let mut newIdx : List String := []
     if isMulti then
@@ -178,7 +178,7 @@
             newVars := newVars ++ resetLevels
         else
           newVars := keepLevels
-          newIdx := keepLevels ++ [dim]
+          newIdx := keepLevels        -- BUG: forgot ++ [dim]
           if dropF then
             dropVars := resetLevels
           else
```

Attack 3 — `atk2_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,14 +161,14 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
+let mut dropVars : List String := []
     let mut newVars : List String := []
     let mut newIdx : List String := []
     if isMulti then
       let keepLevels := levels.filter (fun k => !R.contains k)
       if (!R.contains dim) && !keepLevels.isEmpty then
         let resetLevels := levels.filter (fun k => R.contains k)
-        if keepLevels.length == 1 then
+        if keepLevels.length <= 1 then      -- BUG: <= instead of ==
           dropVars := keepLevels
           newVars := [dim]
           newIdx := [dim]
```

Attack 4 — `atk3_cfeffect.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,7 +161,7 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
+let mut dropVars : List String := []
     let mut newVars : List String := []
     let mut newIdx : List String := []
     if isMulti then
@@ -195,7 +195,7 @@
       else
         newVars := [dim]
     let variables2 := filterOut dropVars V ++ newVars
-    let coord2 := filterOut dropVars C
+    let coord2 := C                 -- BUG: coords not filtered (the actual issue bug)
     return { vars := variables2, coords := coord2, idxs := newIdx }
     -- impl-end
 
```

Attack 5 — `atk4_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,42 +161,7 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
-    let mut newVars : List String := []
-    let mut newIdx : List String := []
-    if isMulti then
-      let keepLevels := levels.filter (fun k => !R.contains k)
-      if (!R.contains dim) && !keepLevels.isEmpty then
-        let resetLevels := levels.filter (fun k => R.contains k)
-        if keepLevels.length == 1 then
-          dropVars := keepLevels
-          newVars := [dim]
-          newIdx := [dim]
-          if dropF then
-            dropVars := dropVars ++ resetLevels
-          else
-            newVars := newVars ++ resetLevels
-        else
-          newVars := keepLevels
-          newIdx := keepLevels ++ [dim]
-          if dropF then
-            dropVars := resetLevels
-          else
-            newVars := newVars ++ resetLevels
-      else
-        dropVars := [dim]
-        if dropF then
-          dropVars := dropVars ++ levels
-        else
-          newVars := levels
-    else
-      if dropF then
-        dropVars := [dim]
-      else
-        newVars := [dim]
-    let variables2 := filterOut dropVars V ++ newVars
-    let coord2 := filterOut dropVars C
-    return { vars := variables2, coords := coord2, idxs := newIdx }
+return computeNameSets isMulti dim levels R V C dropF
     -- impl-end
 
 prove_correct dropIndexNameSets by
```

Attack 6 — `atk5_nonmulti_swap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,7 +161,7 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
+let mut dropVars : List String := []
     let mut newVars : List String := []
     let mut newIdx : List String := []
     if isMulti then
@@ -191,9 +191,9 @@
           newVars := levels
     else
       if dropF then
-        dropVars := [dim]
+        newVars := [dim]          -- BUG: swapped
       else
-        newVars := [dim]
+        dropVars := [dim]         -- BUG: swapped
     let variables2 := filterOut dropVars V ++ newVars
     let coord2 := filterOut dropVars C
     return { vars := variables2, coords := coord2, idxs := newIdx }
```

Attack 7 — `atk7_convpath.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,7 +161,7 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
+let mut dropVars : List String := []
     let mut newVars : List String := []
     let mut newIdx : List String := []
     if isMulti then
@@ -195,7 +195,8 @@
       else
         newVars := [dim]
     let variables2 := filterOut dropVars V ++ newVars
-    let coord2 := filterOut dropVars C
+    -- BUG: only filter coords when dropping; on convert path leave C unfiltered
+    let coord2 := if dropF then filterOut dropVars C else C
     return { vars := variables2, coords := coord2, idxs := newIdx }
     -- impl-end
 
```

Attack 8 — `atk8_emptyreturn.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- This bundle models the name-set bookkeeping of the operation that removes one
    (multi-)index from a labelled-array container and recomputes the container's
@@ -161,42 +161,7 @@
   ensures out = computeNameSets isMulti dim levels R V C dropF
   do
     -- impl-start
-    let mut dropVars : List String := []
-    let mut newVars : List String := []
-    let mut newIdx : List String := []
-    if isMulti then
-      let keepLevels := levels.filter (fun k => !R.contains k)
-      if (!R.contains dim) && !keepLevels.isEmpty then
-        let resetLevels := levels.filter (fun k => R.contains k)
-        if keepLevels.length == 1 then
-          dropVars := keepLevels
-          newVars := [dim]
-          newIdx := [dim]
-          if dropF then
-            dropVars := dropVars ++ resetLevels
-          else
-            newVars := newVars ++ resetLevels
-        else
-          newVars := keepLevels
-          newIdx := keepLevels ++ [dim]
-          if dropF then
-            dropVars := resetLevels
-          else
-            newVars := newVars ++ resetLevels
-      else
-        dropVars := [dim]
-        if dropF then
-          dropVars := dropVars ++ levels
-        else
-          newVars := levels
-    else
-      if dropF then
-        dropVars := [dim]
-      else
-        newVars := [dim]
-    let variables2 := filterOut dropVars V ++ newVars
-    let coord2 := filterOut dropVars C
-    return { vars := variables2, coords := coord2, idxs := newIdx }
+return { vars := [], coords := [], idxs := [] }
     -- impl-end
 
 prove_correct dropIndexNameSets by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- This bundle models the name-set bookkeeping of the operation that removes one
   (multi-)index from a labelled-array container and recomputes the container's
   variable / coordinate / index name-sets. A labelled-array container carries
   three name-sets that must obey one structural invariant: every coordinate
   name is also a variable name (`coords ⊆ vars`). The modeled operation must
   keep that invariant intact for every input. The carrier is `List String`
   (names are opaque string identifiers); the index being removed is described
   abstractly by its dimension name `dim`, whether it is a multi-level index,
   and (for a multi-level index) its level coordinate names `levels`. The full
   coordinate footprint of the index is `{dim} ∪ levels` — the property an
   unchanged neighbouring helper supplies (validated in axiom_check.py / G-AX).
   Duplicate-freeness of the carriers is irrelevant to the name-sets, so plain
   `List String` with membership/`filter` semantics is the faithful model. -/

-- axioms-start
-- (No consumed axioms. The operation under change is modeled DEEPLY as concrete
--  list bookkeeping over `List String`, spelled out in the `pure` region; no
--  library callee's `ensures` is consumed by the proof. The single UNCHANGED
--  neighbouring callee the model relies on — the index-footprint helper that
--  reports a (multi-)index's full coordinate set as `{dim} ∪ levels` — is an
--  A-reference, validated == its real counterpart by axiom_check.py (G-AX). The
--  changed bookkeeping itself (including the single-level-reduction renaming of a
--  kept level coordinate to the dimension name) is part of this deep model and is
--  refuted against the real operation by conformance_check.py (G-CONF), not an
--  axiom.)
-- axioms-end

-- pure-start
/- Remove from a name list, in order, every name that occurs in `drop`. Empty
   `drop` removes nothing. Front-recursive so a single unfold is available. -/
def filterOut (drop : List String) : List String → List String
  | []      => []
  | x :: xs => (if drop.contains x then [] else [x]) ++ filterOut drop xs

@[grind] lemma filterOut_nil (d : List String) : filterOut d [] = [] := rfl
@[grind] lemma filterOut_cons (d : List String) (x : String) (xs : List String) :
    filterOut d (x :: xs) = (if d.contains x then [] else [x]) ++ filterOut d xs := rfl

/- Membership characterisation: a name survives `filterOut` iff it was present
   and is not among the dropped names. -/
lemma mem_filterOut (d : List String) (xs : List String) (k : String) :
    k ∈ filterOut d xs ↔ (k ∈ xs ∧ d.contains k = false) := by
  induction xs with
  | nil => simp [filterOut]
  | cons x xs ih =>
    rw [filterOut_cons]
    by_cases hc : d.contains x = true
    · rw [if_pos hc]; simp only [List.nil_append, ih, List.mem_cons]
      constructor
      · rintro ⟨hmem, hcon⟩; exact ⟨Or.inr hmem, hcon⟩
      · rintro ⟨h, hcon⟩; rcases h with h | h
        · subst h; rw [hc] at hcon; exact absurd hcon (by simp)
        · exact ⟨h, hcon⟩
    · rw [if_neg hc]; simp only [List.singleton_append, List.mem_cons, ih]
      simp only [Bool.not_eq_true] at hc
      constructor
      · rintro (h | ⟨hmem, hcon⟩)
        · subst h; exact ⟨Or.inl rfl, hc⟩
        · exact ⟨Or.inr hmem, hcon⟩
      · rintro ⟨h, hcon⟩; rcases h with h | h
        · exact Or.inl h
        · exact Or.inr ⟨h, hcon⟩

/- The three recomputed name-sets of the container after the index is removed. -/
structure NameSets where
  vars : List String
  coords : List String
  idxs : List String
deriving DecidableEq

/- The recomputed (variables, coordinate-names, index-keys) after removing the
   index whose dimension is `dim`. `R` is the set of requested names to reset.
   `V`/`C` are the prior variable / coordinate name-sets. `dropF` selects "drop"
   (discard the de-indexed coordinates) versus "convert" (retain them as plain
   variables). Written as one nested-if mirroring the operation's control flow:

   * non-multi index: its single coordinate `dim` is dropped (`dropF`) or
     retained as a plain variable (else); no index remains.
   * multi-level index, with at least one kept level and the dimension itself
     not requested: the index is rebuilt on the kept levels.
       - exactly one kept level: it reduces to a single index whose coordinate
         is renamed to `dim`; the old kept-level name is removed; the reset
         levels are dropped/converted.
       - more than one kept level: the multi-index is rebuilt on the kept levels
         (names unchanged) and the reset levels are dropped/converted.
   * multi-level index otherwise (dimension requested, or no level kept): the
     whole index goes; the dimension variable is always removed and the levels
     are dropped/converted.

   In every branch the SAME drop-set `dv` is subtracted from BOTH `V` and `C`,
   which is exactly what keeps `coords ⊆ vars` intact (see `subsetPreserved`). -/
def computeNameSets (isMulti : Bool) (dim : String) (levels R V C : List String)
    (dropF : Bool) : NameSets :=
  let mk := fun (dv nv ni : List String) =>
    ({ vars := filterOut dv V ++ nv, coords := filterOut dv C, idxs := ni } : NameSets)
  if isMulti then
    let keepLevels := levels.filter (fun k => !R.contains k)
    if (!R.contains dim) && !keepLevels.isEmpty then
      let resetLevels := levels.filter (fun k => R.contains k)
      if keepLevels.length == 1 then
        if dropF then mk (keepLevels ++ resetLevels) [dim] [dim]
                 else mk keepLevels ([dim] ++ resetLevels) [dim]
      else
        if dropF then mk resetLevels keepLevels (keepLevels ++ [dim])
                 else mk [] (keepLevels ++ resetLevels) (keepLevels ++ [dim])
    else
      if dropF then mk (dim :: levels) [] []
               else mk [dim] levels []
  else
    if dropF then mk [dim] [] []
             else mk [] [dim] []

/- The structural guarantee the operation must preserve: if every coordinate
   name was a variable name beforehand (`coords ⊆ vars`), then every recomputed
   coordinate name is a recomputed variable name. This is the invariant whose
   violation by a defective bookkeeping makes a downstream length computation
   negative; the deep model restores it for ALL inputs. Proved once, branch by
   branch, from `mem_filterOut` and the fact that the same drop-set is removed
   from both name-sets. -/
theorem subsetPreserved (isMulti : Bool) (dim : String) (levels R V C : List String)
    (dropF : Bool) (hCV : ∀ k, k ∈ C → k ∈ V) :
    ∀ k, k ∈ (computeNameSets isMulti dim levels R V C dropF).coords →
         k ∈ (computeNameSets isMulti dim levels R V C dropF).vars := by
  have key : ∀ (dv nv : List String) (k : String),
      k ∈ filterOut dv C → k ∈ filterOut dv V ++ nv := by
    intro dv nv k hk
    rw [mem_filterOut] at hk
    apply List.mem_append_left
    rw [mem_filterOut]
    exact ⟨hCV k hk.1, hk.2⟩
  simp only [computeNameSets]
  split_ifs <;> intro k hk <;> exact key _ _ _ hk
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recompute the variable / coordinate / index name-sets of the container after
   removing the index on dimension `dim`. The result must equal the name-set
   bookkeeping `computeNameSets` describes — in particular every dropped name is
   subtracted from BOTH the variable set and the coordinate set, so that the
   structural invariant `coords ⊆ vars` is preserved (`subsetPreserved`).

   All inputs (`isMulti`, `dim`, `levels`, `R`, `V`, `C`, `dropF`) are read-only
   descriptions of the prior state and the request; the operation builds fresh
   name-sets and mutates none of them (directive 5). -/
method dropIndexNameSets (isMulti : Bool) (dim : String) (levels : List String)
    (R : List String) (V : List String) (C : List String) (dropF : Bool)
    return (out : NameSets)
  ensures out = computeNameSets isMulti dim levels R V C dropF
  do
    -- impl-start
    let mut dropVars : List String := []
    let mut newVars : List String := []
    let mut newIdx : List String := []
    if isMulti then
      let keepLevels := levels.filter (fun k => !R.contains k)
      if (!R.contains dim) && !keepLevels.isEmpty then
        let resetLevels := levels.filter (fun k => R.contains k)
        if keepLevels.length == 1 then
          dropVars := keepLevels
          newVars := [dim]
          newIdx := [dim]
          if dropF then
            dropVars := dropVars ++ resetLevels
          else
            newVars := newVars ++ resetLevels
        else
          newVars := keepLevels
          newIdx := keepLevels ++ [dim]
          if dropF then
            dropVars := resetLevels
          else
            newVars := newVars ++ resetLevels
      else
        dropVars := [dim]
        if dropF then
          dropVars := dropVars ++ levels
        else
          newVars := levels
    else
      if dropF then
        dropVars := [dim]
      else
        newVars := [dim]
    let variables2 := filterOut dropVars V ++ newVars
    let coord2 := filterOut dropVars C
    return { vars := variables2, coords := coord2, idxs := newIdx }
    -- impl-end

prove_correct dropIndexNameSets by
  loom_solve <;> simp_all [computeNameSets]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec is a TOTAL functional-equality postcondition `ensures out = computeNameSets isMulti dim levels R V C dropF` over `NameSets` (deriving DecidableEq) with NO precondition, under loom.semantics.termination "partial" / demonic choice. This pins the impl extremely tightly: any TERMINATING same-spec impl that verifies must equal computeNameSets on every input.

 Verify cmd: `bash scripts/lean_verify.sh <file>`. same_spec confirmed True for all attacks via swebench_unified.markers.same_spec(velvet backend). Positive control pos.lean = frozen Solution.lean, verifies EXIT=0 (27s).

### ATTACKS (authoritative DIRECT exit codes; the ≤4 background wrapper mis-captured $? on some jobs, so all were re-run one-by-one):
- atk_prepatch (the reported bug: coord2 := C ++ newVars, coords never shrink) -> EXIT=1 FAIL VERIFY (bug correctly rejected; prepatch reproduced). same_spec=True.
- atk1_partialdom (>1-kept-level branch: newIdx := keepLevels, forgot ++[dim]) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk2_boundary (keepLevels.length <= 1 instead of == 1) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk3_cfeffect (coord2 := C, coords never filtered) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk5_nonmulti_swap (non-multi drop/convert branches swapped) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk7_convpath (coords filtered only on the drop path, left C on convert) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk8_emptyreturn (return {vars:=[],coords:=[],idxs:=[]}) -> EXIT=1 FAIL VERIFY. same_spec=True. (Doubles as the terminating rendering of atk6 — see below.)
- atk4_echo (ungrounded-oracle echo: `return computeNameSets ...`) -> EXIT=0 VERIFIES. same_spec=True. Its faithful refined patch is the gold patch (behaviorally identical). RESOLVE RUN: `python -m swebench_unified.harness.run_resolve('pydata__xarray-6992', gold)` via `docker` run_evaluation -> COMPLETED=True, RESOLVED=True; all 12 FAIL_TO_PASS pass, error=0 (test_reset_index, test_reset_index_drop_dims, all 8 test_reset_index_drop_convert params, test_groupby_drops_nans). First attempt hit a transient harness error (no report — heavy container contention from a concurrent audit concurrent runs; 42 active containers); the immediate retry (run_id sbu-atk4-dbg) completed cleanly and resolved. => atk4 is a CORRECT ECHO of the gold, NOT a spec weakness (matches build_one._derive_audit_verdict: candidate whose patch resolves).

DIVERGENCE PROBE (NOT counted as an attack; documented for completeness): atk6_diverge (`let mut i:=0; while true do i:=i+1; return {..}`) -> EXIT=0 VERIFIES, same_spec=True. It verifies SOLELY via partial-correctness vacuity: I proved this by encoding atk8_emptyreturn, which is atk6 with the `while true` removed (the only terminating rendering) — atk8 FAILS to verify (EXIT=1). So atk6's verification is entirely due to non-termination under loom.semantics.termination "partial", NOT any weakness of this spec's refinement map. A `while true` loop corresponds to NO leg of refinement.md (R/A-reference/I) — it refines to no gold-patch operation, hence admits no faithful refined patch to resolve-check. This loophole is UNIVERSAL to every velvet bundle using the standard partial-correctness setting (spec_guide §1.1 sanctions it); if it counted as a break no velvet bundle could pass G-EQ. It is therefore out of scope for refinement fidelity and is excluded from `attacks` (including it with any patch — divergent patch would hang -> not completed -> inconclusive; gold patch would be a dishonest mapping — so exclusion is the honest disposition).

REFINEMENT.MD AUDIT (task 3): all legs are R / A-reference / I — NO kind-3, NO consumed axioms.
- A1 params (name-sets<->List String, flags<->Bool, read-only/functional): R. Legitimate type refinement.
- A2 dim/levels = index footprint {dim}∪levels <- self.xindexes.get_all_coords(name) (indexes.py:1111, UNCHANGED by patch): A-REFERENCE — the sole kind-A leg. Independently validated by axiom_check.py (G-AX): runs the REAL unpatched callee over boundary shapes (1/2/3-level multi, plain PandasIndex, disjoint/extra-coord datasets) + 4000-fuzz, asserting set(get_all_coords(name)) == {index.dim} ∪ {level names}; meta.json records G-AX pass on 10735 observations. Correspondence to the real callee HOLDS.
- A3-A7 branch bookkeeping incl. the single-level rename (keepLevels.length==1 -> newVars:=[dim], newIdx:=[dim], old kept-level name dropped) and THE FIX (same drop-set dv subtracted from BOTH V and C via filterOut dv V / filterOut dv C): I. Refuted by conformance_check.py (G-CONF), which builds real xarray.Datasets, runs the patched reset_index as oracle, and compares name-sets vs the computeNameSets shadow over ≥1e5 inputs (seed 6992); meta.json records G-CONF pass, 0/100000 disagreements. The changed operation is modeled DEEPLY (computeNameSets + subsetPreserved), not axiomatized.

CONCLUSION: Every behaviorally-distinct terminating wrong impl (the bug + partial-domain + boundary + control-flow-effect + swap variants) FAILS to verify — the functional-equality spec is tight. The only verifying same-spec impl with an actual refinement (atk4 echo) resolves under the official harness. The one further verifier (atk6) is a partial-correctness divergence artifact with no faithful refinement leg, not a per-bundle defect. No verifying wrong impl's faithful refined patch fails to resolve => verify does NOT ⇏ correct here. ≥5 attacks run (8 same-spec attacks), prepatch reproduced, positive control verifies, refinement.md A-legs sound. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk1_partialdom.lean`, `atk2_boundary.lean`, `atk3_cfeffect.lean`, `atk5_nonmulti_swap.lean`, `atk7_convpath.lean`, `atk8_emptyreturn.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4_echo.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1_partialdom.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3_cfeffect.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk5_nonmulti_swap.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_convpath.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_emptyreturn.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- This bundle models the name-set bookkeeping of the operation that removes one
   (multi-)index from a labelled-array container and recomputes the container's
   variable / coordinate / index name-sets. A labelled-array container carries
   three name-sets that must obey one structural invariant: every coordinate
   name is also a variable name (`coords ⊆ vars`). The modeled operation must
   keep that invariant intact for every input. The carrier is `List String`
   (names are opaque string identifiers); the index being removed is described
   abstractly by its dimension name `dim`, whether it is a multi-level index,
   and (for a multi-level index) its level coordinate names `levels`. The full
   coordinate footprint of the index is `{dim} ∪ levels` — the property an
   unchanged neighbouring helper supplies (validated in axiom_check.py / G-AX).
   Duplicate-freeness of the carriers is irrelevant to the name-sets, so plain
   `List String` with membership/`filter` semantics is the faithful model. -/

-- axioms-start
-- (No consumed axioms. The operation under change is modeled DEEPLY as concrete
--  list bookkeeping over `List String`, spelled out in the `pure` region; no
--  library callee's `ensures` is consumed by the proof. The single UNCHANGED
--  neighbouring callee the model relies on — the index-footprint helper that
--  reports a (multi-)index's full coordinate set as `{dim} ∪ levels` — is an
--  A-reference, validated == its real counterpart by axiom_check.py (G-AX). The
--  changed bookkeeping itself (including the single-level-reduction renaming of a
--  kept level coordinate to the dimension name) is part of this deep model and is
--  refuted against the real operation by conformance_check.py (G-CONF), not an
--  axiom.)
-- axioms-end

-- pure-start
/- Remove from a name list, in order, every name that occurs in `drop`. Empty
   `drop` removes nothing. Front-recursive so a single unfold is available. -/
def filterOut (drop : List String) : List String → List String
  | []      => []
  | x :: xs => (if drop.contains x then [] else [x]) ++ filterOut drop xs

@[grind] lemma filterOut_nil (d : List String) : filterOut d [] = [] := rfl
@[grind] lemma filterOut_cons (d : List String) (x : String) (xs : List String) :
    filterOut d (x :: xs) = (if d.contains x then [] else [x]) ++ filterOut d xs := rfl

/- Membership characterisation: a name survives `filterOut` iff it was present
   and is not among the dropped names. -/
lemma mem_filterOut (d : List String) (xs : List String) (k : String) :
    k ∈ filterOut d xs ↔ (k ∈ xs ∧ d.contains k = false) := by
  induction xs with
  | nil => simp [filterOut]
  | cons x xs ih =>
    rw [filterOut_cons]
    by_cases hc : d.contains x = true
    · rw [if_pos hc]; simp only [List.nil_append, ih, List.mem_cons]
      constructor
      · rintro ⟨hmem, hcon⟩; exact ⟨Or.inr hmem, hcon⟩
      · rintro ⟨h, hcon⟩; rcases h with h | h
        · subst h; rw [hc] at hcon; exact absurd hcon (by simp)
        · exact ⟨h, hcon⟩
    · rw [if_neg hc]; simp only [List.singleton_append, List.mem_cons, ih]
      simp only [Bool.not_eq_true] at hc
      constructor
      · rintro (h | ⟨hmem, hcon⟩)
        · subst h; exact ⟨Or.inl rfl, hc⟩
        · exact ⟨Or.inr hmem, hcon⟩
      · rintro ⟨h, hcon⟩; rcases h with h | h
        · exact Or.inl h
        · exact Or.inr ⟨h, hcon⟩

/- The three recomputed name-sets of the container after the index is removed. -/
structure NameSets where
  vars : List String
  coords : List String
  idxs : List String
deriving DecidableEq

/- The recomputed (variables, coordinate-names, index-keys) after removing the
   index whose dimension is `dim`. `R` is the set of requested names to reset.
   `V`/`C` are the prior variable / coordinate name-sets. `dropF` selects "drop"
   (discard the de-indexed coordinates) versus "convert" (retain them as plain
   variables). Written as one nested-if mirroring the operation's control flow:

   * non-multi index: its single coordinate `dim` is dropped (`dropF`) or
     retained as a plain variable (else); no index remains.
   * multi-level index, with at least one kept level and the dimension itself
     not requested: the index is rebuilt on the kept levels.
       - exactly one kept level: it reduces to a single index whose coordinate
         is renamed to `dim`; the old kept-level name is removed; the reset
         levels are dropped/converted.
       - more than one kept level: the multi-index is rebuilt on the kept levels
         (names unchanged) and the reset levels are dropped/converted.
   * multi-level index otherwise (dimension requested, or no level kept): the
     whole index goes; the dimension variable is always removed and the levels
     are dropped/converted.

   In every branch the SAME drop-set `dv` is subtracted from BOTH `V` and `C`,
   which is exactly what keeps `coords ⊆ vars` intact (see `subsetPreserved`). -/
def computeNameSets (isMulti : Bool) (dim : String) (levels R V C : List String)
    (dropF : Bool) : NameSets :=
  let mk := fun (dv nv ni : List String) =>
    ({ vars := filterOut dv V ++ nv, coords := filterOut dv C, idxs := ni } : NameSets)
  if isMulti then
    let keepLevels := levels.filter (fun k => !R.contains k)
    if (!R.contains dim) && !keepLevels.isEmpty then
      let resetLevels := levels.filter (fun k => R.contains k)
      if keepLevels.length == 1 then
        if dropF then mk (keepLevels ++ resetLevels) [dim] [dim]
                 else mk keepLevels ([dim] ++ resetLevels) [dim]
      else
        if dropF then mk resetLevels keepLevels (keepLevels ++ [dim])
                 else mk [] (keepLevels ++ resetLevels) (keepLevels ++ [dim])
    else
      if dropF then mk (dim :: levels) [] []
               else mk [dim] levels []
  else
    if dropF then mk [dim] [] []
             else mk [] [dim] []

/- The structural guarantee the operation must preserve: if every coordinate
   name was a variable name beforehand (`coords ⊆ vars`), then every recomputed
   coordinate name is a recomputed variable name. This is the invariant whose
   violation by a defective bookkeeping makes a downstream length computation
   negative; the deep model restores it for ALL inputs. Proved once, branch by
   branch, from `mem_filterOut` and the fact that the same drop-set is removed
   from both name-sets. -/
theorem subsetPreserved (isMulti : Bool) (dim : String) (levels R V C : List String)
    (dropF : Bool) (hCV : ∀ k, k ∈ C → k ∈ V) :
    ∀ k, k ∈ (computeNameSets isMulti dim levels R V C dropF).coords →
         k ∈ (computeNameSets isMulti dim levels R V C dropF).vars := by
  have key : ∀ (dv nv : List String) (k : String),
      k ∈ filterOut dv C → k ∈ filterOut dv V ++ nv := by
    intro dv nv k hk
    rw [mem_filterOut] at hk
    apply List.mem_append_left
    rw [mem_filterOut]
    exact ⟨hCV k hk.1, hk.2⟩
  simp only [computeNameSets]
  split_ifs <;> intro k hk <;> exact key _ _ _ hk
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recompute the variable / coordinate / index name-sets of the container after
   removing the index on dimension `dim`. The result must equal the name-set
   bookkeeping `computeNameSets` describes — in particular every dropped name is
   subtracted from BOTH the variable set and the coordinate set, so that the
   structural invariant `coords ⊆ vars` is preserved (`subsetPreserved`).

   All inputs (`isMulti`, `dim`, `levels`, `R`, `V`, `C`, `dropF`) are read-only
   descriptions of the prior state and the request; the operation builds fresh
   name-sets and mutates none of them (directive 5). -/
method dropIndexNameSets (isMulti : Bool) (dim : String) (levels : List String)
    (R : List String) (V : List String) (C : List String) (dropF : Bool)
    return (out : NameSets)
  ensures out = computeNameSets isMulti dim levels R V C dropF
  do
    -- impl-start
    let mut dropVars : List String := []
    let mut newVars : List String := []
    let mut newIdx : List String := []
    if isMulti then
      let keepLevels := levels.filter (fun k => !R.contains k)
      if (!R.contains dim) && !keepLevels.isEmpty then
        let resetLevels := levels.filter (fun k => R.contains k)
        if keepLevels.length == 1 then
          dropVars := keepLevels
          newVars := [dim]
          newIdx := [dim]
          if dropF then
            dropVars := dropVars ++ resetLevels
          else
            newVars := newVars ++ resetLevels
        else
          newVars := keepLevels
          newIdx := keepLevels ++ [dim]
          if dropF then
            dropVars := resetLevels
          else
            newVars := newVars ++ resetLevels
      else
        dropVars := [dim]
        if dropF then
          dropVars := dropVars ++ levels
        else
          newVars := levels
    else
      if dropF then
        dropVars := [dim]
      else
        newVars := [dim]
    let variables2 := filterOut dropVars V ++ newVars
    let coord2 := filterOut dropVars C
    return { vars := variables2, coords := coord2, idxs := newIdx }
    -- impl-end

prove_correct dropIndexNameSets by
  loom_solve <;> simp_all [computeNameSets]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec is a TOTAL functional-equality postcondition `ensures out = computeNameSets isMulti dim levels R V C dropF` over `NameSets` (deriving DecidableEq) with NO precondition, under loom.semantics.termination "partial" / demonic choice. This pins the impl extremely tightly: any TERMINATING same-spec impl that verifies must equal computeNameSets on every input.

 Verify cmd: `bash scripts/lean_verify.sh <file>`. same_spec confirmed True for all attacks via swebench_unified.markers.same_spec(velvet backend). Positive control pos.lean = frozen Solution.lean, verifies EXIT=0 (27s).

### ATTACKS (authoritative DIRECT exit codes; the ≤4 background wrapper mis-captured $? on some jobs, so all were re-run one-by-one):
- atk_prepatch (the reported bug: coord2 := C ++ newVars, coords never shrink) -> EXIT=1 FAIL VERIFY (bug correctly rejected; prepatch reproduced). same_spec=True.
- atk1_partialdom (>1-kept-level branch: newIdx := keepLevels, forgot ++[dim]) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk2_boundary (keepLevels.length <= 1 instead of == 1) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk3_cfeffect (coord2 := C, coords never filtered) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk5_nonmulti_swap (non-multi drop/convert branches swapped) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk7_convpath (coords filtered only on the drop path, left C on convert) -> EXIT=1 FAIL VERIFY. same_spec=True.
- atk8_emptyreturn (return {vars:=[],coords:=[],idxs:=[]}) -> EXIT=1 FAIL VERIFY. same_spec=True. (Doubles as the terminating rendering of atk6 — see below.)
- atk4_echo (ungrounded-oracle echo: `return computeNameSets ...`) -> EXIT=0 VERIFIES. same_spec=True. Its faithful refined patch is the gold patch (behaviorally identical). RESOLVE RUN: `python -m swebench_unified.harness.run_resolve('pydata__xarray-6992', gold)` via `docker` run_evaluation -> COMPLETED=True, RESOLVED=True; all 12 FAIL_TO_PASS pass, error=0 (test_reset_index, test_reset_index_drop_dims, all 8 test_reset_index_drop_convert params, test_groupby_drops_nans). First attempt hit a transient harness error (no report — heavy container contention from a concurrent audit concurrent runs; 42 active containers); the immediate retry (run_id sbu-atk4-dbg) completed cleanly and resolved. => atk4 is a CORRECT ECHO of the gold, NOT a spec weakness (matches build_one._derive_audit_verdict: candidate whose patch resolves).

DIVERGENCE PROBE (NOT counted as an attack; documented for completeness): atk6_diverge (`let mut i:=0; while true do i:=i+1; return {..}`) -> EXIT=0 VERIFIES, same_spec=True. It verifies SOLELY via partial-correctness vacuity: I proved this by encoding atk8_emptyreturn, which is atk6 with the `while true` removed (the only terminating rendering) — atk8 FAILS to verify (EXIT=1). So atk6's verification is entirely due to non-termination under loom.semantics.termination "partial", NOT any weakness of this spec's refinement map. A `while true` loop corresponds to NO leg of refinement.md (R/A-reference/I) — it refines to no gold-patch operation, hence admits no faithful refined patch to resolve-check. This loophole is UNIVERSAL to every velvet bundle using the standard partial-correctness setting (spec_guide §1.1 sanctions it); if it counted as a break no velvet bundle could pass G-EQ. It is therefore out of scope for refinement fidelity and is excluded from `attacks` (including it with any patch — divergent patch would hang -> not completed -> inconclusive; gold patch would be a dishonest mapping — so exclusion is the honest disposition).

REFINEMENT.MD AUDIT (task 3): all legs are R / A-reference / I — NO kind-3, NO consumed axioms.
- A1 params (name-sets<->List String, flags<->Bool, read-only/functional): R. Legitimate type refinement.
- A2 dim/levels = index footprint {dim}∪levels <- self.xindexes.get_all_coords(name) (indexes.py:1111, UNCHANGED by patch): A-REFERENCE — the sole kind-A leg. Independently validated by axiom_check.py (G-AX): runs the REAL unpatched callee over boundary shapes (1/2/3-level multi, plain PandasIndex, disjoint/extra-coord datasets) + 4000-fuzz, asserting set(get_all_coords(name)) == {index.dim} ∪ {level names}; meta.json records G-AX pass on 10735 observations. Correspondence to the real callee HOLDS.
- A3-A7 branch bookkeeping incl. the single-level rename (keepLevels.length==1 -> newVars:=[dim], newIdx:=[dim], old kept-level name dropped) and THE FIX (same drop-set dv subtracted from BOTH V and C via filterOut dv V / filterOut dv C): I. Refuted by conformance_check.py (G-CONF), which builds real xarray.Datasets, runs the patched reset_index as oracle, and compares name-sets vs the computeNameSets shadow over ≥1e5 inputs (seed 6992); meta.json records G-CONF pass, 0/100000 disagreements. The changed operation is modeled DEEPLY (computeNameSets + subsetPreserved), not axiomatized.

CONCLUSION: Every behaviorally-distinct terminating wrong impl (the bug + partial-domain + boundary + control-flow-effect + swap variants) FAILS to verify — the functional-equality spec is tight. The only verifying same-spec impl with an actual refinement (atk4 echo) resolves under the official harness. The one further verifier (atk6) is a partial-correctness divergence artifact with no faithful refinement leg, not a per-bundle defect. No verifying wrong impl's faithful refined patch fails to resolve => verify does NOT ⇏ correct here. ≥5 attacks run (8 same-spec attacks), prepatch reproduced, positive control verifies, refinement.md A-legs sound. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pydata__xarray-6992 velvet bundle. Modeled site: Dataset.reset_index name-set bookkeeping (xarray/core/dataset.py:4108). Method dropIndexNameSets ensures out = computeNameSets ..., a deep model of the (variables, coord_names, indexes) recomputation.

Verification performed:
1. Spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True; spec signature len 8244. Prepatch shares the frozen spec region.
2. Non-vacuity: scripts/lean_verify.sh on Solution.lean -> exit 0 (clean elaboration, no sorry/error).
3. Fidelity to REAL callee: created worktree at base_commit 45c0a114e2b7b27b83c9618bc05b36afac82183c, git-applied the gold patch, imported the real patched xarray, and compared the model's compute_name_sets (Python transliteration of computeNameSets, verified equivalent to the Lean branches) against the real patched Dataset.reset_index observed name-sets (set(_variables), set(_coord_names), set(_indexes)).
   - Pinned 100k conformance inputs (conformance_check.py seed 6992): 0 disagreements.
   - ADVERSARIAL shapes NOT covered by conformance families (attacker blind-spot probing): 4-, 5-, 6-level multi-indexes; datasets with extra data variables and extra non-index coordinates; varied dimension names; single-index with extras -- ~4250 exhaustive footprint-subset x drop-flag inputs: 0 disagreements.
   - 4000 additional randomized inputs (seed 12345) over 1-6 level multi/single indexes with random extras: 0 disagreements.

All branches match the real repo: non-multi drop/convert; multi 1-kept-level rename (kept level coord -> dim, index keyed [dim], old level name dropped); multi >1-kept rebuild (surviving index keys = kept ∪ {dim}); whole-index removal (dim variable always dropped, levels drop/convert per dropF). The same drop-set is subtracted from BOTH V and C, matching the gold fix coord_names = self._coord_names - drop_variables. The A-referenced footprint (get_all_coords -> {dim} ∪ levels) is taken from the real index object in the shadow (A leg with G-AX) and matched observed behavior.

No diverging input found. The modeled function does NOT disagree with the real callee on any tested input, including shapes beyond the conformance envelope. The spec is neither too strong nor drifting from repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous review of the velvet spec view for pydata__xarray-6992. Integrity: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical). Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES with zero hard failures; recorded G-LEAK=pass; no relaxed_leakage flag/RELAXED_LEAKAGE.md. Semantic checks over the spec view: NO patched repo symbol appears (reset_index/set_index/keep_levels/get_all_coords/Dataset/_variables/_coord_names/xindexes/to_base_variable/drop_variables/MultiIndex/DataVariables/__len__ all count 0); NO patched file path (dataset.py, indexes.py absent — the only .py tokens are bundle-local axiom_check.py/conformance_check.py); no gold-patch line reproduced; no diff markers; no bug/fix narration. The carrier is fully abstracted to List String / NameSets / computeNameSets / dropIndexNameSets and none of it echoes the repo. The invariant the spec pins (coords ⊆ vars, avoiding more coord_names than variables → 'ValueError: __len__() should return >= 0') is ALREADY public via the problem_statement, so not extra leakage. The additional behavioral detail (single-kept-level rename to dim, drop-vs-convert split) is expressed in the model's own abstract vocabulary as the required correct behavior — the inherent job of a behavioral spec, not edit-localization: it never names the changed method/file/line. A solver must still reconstruct the mapping and implementation. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
