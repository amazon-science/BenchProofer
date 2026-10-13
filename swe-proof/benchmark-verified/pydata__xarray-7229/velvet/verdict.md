# P2 adversarial audit — pydata__xarray-7229

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a total function of its inputs, so no verifying-but-divergent twin exists. Postconditions pin EVERY field of the output Obj (which has exactly gattrs/vars/coords): `out.gattrs = rebuiltGlobal promote xGAttrs`; `out.vars.size = resVars.size` + `∀ i < resVars.size, out.vars[i]! = rebuiltVar ...`; `out.coords.size = resCoords.size` + `∀ i < resCoords.size, out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)`. Any verifying impl must therefore produce the identical Obj. Empirically: 7 distinct wrong impls all fail to verify with genuine unsolved postcondition goals (e.g. atk_2's unsolved goal is exactly `resCoords[i]! = rebuiltCoord xCoords resCoords[i]!`, the coord clause it violates), while the byte-identical positive control verifies.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,29 +86,27 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- prepatch bug: single global-metadata stamp threaded onto EVERY level
+    let stamp : Nat := if promote then 0 else xGAttrs
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
       invariant i ≤ resVars.size
       invariant outVars.size = resVars.size
-      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
+      invariant ∀ j, j < i → outVars[j]! = (⟨(resVars[j]!).name, stamp⟩ : Lvl)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
-      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
+      outVars[i] := ⟨(resVars[i]!).name, stamp⟩
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
     let mut outCoords := resCoords
     let mut k := 0
     while k < resCoords.size
       invariant k ≤ resCoords.size
       invariant outCoords.size = resCoords.size
-      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
+      invariant ∀ j, j < k → outCoords[j]! = (⟨(resCoords[j]!).name, stamp⟩ : Lvl)
       done_with k = resCoords.size
-      decreasing resCoords.size - k
     do
-      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
+      outCoords[k] := ⟨(resCoords[k]!).name, stamp⟩
       k := k + 1
     return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
     -- impl-end
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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,7 +86,7 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- partial-domain: rebuild vars correctly but leave coords as-is (no by-name fill)
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
@@ -94,23 +94,10 @@
       invariant outVars.size = resVars.size
       invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
       outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
-    let mut outCoords := resCoords
-    let mut k := 0
-    while k < resCoords.size
-      invariant k ≤ resCoords.size
-      invariant outCoords.size = resCoords.size
-      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
-      done_with k = resCoords.size
-      decreasing resCoords.size - k
-    do
-      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
-      k := k + 1
-    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
+    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := resCoords }
     -- impl-end
 
 prove_correct rebuildAttrs by
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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,7 +86,7 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- boundary: coord loop skips index 0 (off-by-one start)
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
@@ -94,19 +94,16 @@
       invariant outVars.size = resVars.size
       invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
       outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
     let mut outCoords := resCoords
-    let mut k := 0
+    let mut k := 1
     while k < resCoords.size
       invariant k ≤ resCoords.size
       invariant outCoords.size = resCoords.size
-      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
+      invariant ∀ j, 1 ≤ j → j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
       done_with k = resCoords.size
-      decreasing resCoords.size - k
     do
       outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
       k := k + 1
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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,7 +86,7 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- control-flow-effect: global metadata always xGAttrs (ignores promotion reset to 0)
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
@@ -94,11 +94,9 @@
       invariant outVars.size = resVars.size
       invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
       outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
     let mut outCoords := resCoords
     let mut k := 0
     while k < resCoords.size
@@ -106,11 +104,10 @@
       invariant outCoords.size = resCoords.size
       invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
       done_with k = resCoords.size
-      decreasing resCoords.size - k
     do
       outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
       k := k + 1
-    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
+    return { gattrs := xGAttrs, vars := outVars, coords := outCoords }
     -- impl-end
 
 prove_correct rebuildAttrs by
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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,7 +86,7 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- ungrounded-oracle echo: coord metadata echoes the result's own level attrs
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
@@ -94,21 +94,18 @@
       invariant outVars.size = resVars.size
       invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
       outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
     let mut outCoords := resCoords
     let mut k := 0
     while k < resCoords.size
       invariant k ≤ resCoords.size
       invariant outCoords.size = resCoords.size
-      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
+      invariant ∀ j, j < k → outCoords[j]! = (⟨(resCoords[j]!).name, (resCoords[j]!).attrs⟩ : Lvl)
       done_with k = resCoords.size
-      decreasing resCoords.size - k
     do
-      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
+      outCoords[k] := ⟨(resCoords[k]!).name, (resCoords[k]!).attrs⟩
       k := k + 1
     return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
     -- impl-end
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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,29 +86,26 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- swap: variable levels filled from xCoords by-name; coord levels filled per rebuiltVar
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
       invariant i ≤ resVars.size
       invariant outVars.size = resVars.size
-      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
+      invariant ∀ j, j < i → outVars[j]! = rebuiltCoord xCoords (resVars[j]!)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
-      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
+      outVars[i] := rebuiltCoord xCoords (resVars[i]!)
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
     let mut outCoords := resCoords
     let mut k := 0
     while k < resCoords.size
       invariant k ≤ resCoords.size
       invariant outCoords.size = resCoords.size
-      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
+      invariant ∀ j, j < k → outCoords[j]! = rebuiltVar promote xName xGAttrs xVars (resCoords[j]!)
       done_with k = resCoords.size
-      decreasing resCoords.size - k
     do
-      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
+      outCoords[k] := rebuiltVar promote xName xGAttrs xVars (resCoords[k]!)
       k := k + 1
     return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
     -- impl-end
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
 
 attribute [solverHint] Array.get_set_c
 
@@ -86,19 +86,17 @@
   ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
   do
     -- impl-start
-    -- variable levels: each named level takes the source's equally-named metadata
+    -- wrong source: non-promote variable metadata looked up in xCoords instead of xVars
     let mut outVars := resVars
     let mut i := 0
     while i < resVars.size
       invariant i ≤ resVars.size
       invariant outVars.size = resVars.size
-      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
+      invariant ∀ j, j < i → outVars[j]! = (⟨(resVars[j]!).name, if promote then (if (resVars[j]!).name = xName then xGAttrs else (resVars[j]!).attrs) else lookupAttrs xCoords.toList (resVars[j]!).name⟩ : Lvl)
       done_with i = resVars.size
-      decreasing resVars.size - i
     do
-      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
+      outVars[i] := ⟨(resVars[i]!).name, if promote then (if (resVars[i]!).name = xName then xGAttrs else (resVars[i]!).attrs) else lookupAttrs xCoords.toList (resVars[i]!).name⟩
       i := i + 1
-    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
     let mut outCoords := resCoords
     let mut k := 0
     while k < resCoords.size
@@ -106,7 +104,6 @@
       invariant outCoords.size = resCoords.size
       invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
       done_with k = resCoords.size
-      decreasing resCoords.size - k
     do
       outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
       k := k + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

attribute [solverHint] Array.get_set_c

/- A labelled metadata level of a structured array value: a `name` (the level's
   identifier) and an opaque `attrs` token standing for that level's metadata
   mapping. Distinct tokens model distinct metadata mappings; `0` is the empty
   mapping. Provenance + the value bijection used by the executable checks:
   mapping.md (G-CONF / G-AX). -/
structure Lvl where
  name  : Nat
  attrs : Nat
deriving Inhabited, DecidableEq, Repr

/- A structured array value, reduced to the metadata that the operation touches:
   the global metadata token `gattrs`, the variable levels `vars`, and the
   coordinate levels `coords`. A plain (single-variable) value has `vars = #[]`. -/
structure Obj where
  gattrs : Nat
  vars   : Array Lvl
  coords : Array Lvl
deriving Inhabited

-- axioms-start
-- axioms-end

-- pure-start
/- The metadata token carried by the first level named `nm` in `lvls`, or the
   empty mapping `0` when no level carries that name. This is the by-name
   metadata selection from a designated source value: the metadata of the
   equally-named level, and the empty mapping when the source has no such level. -/
def lookupAttrs : List Lvl → Nat → Nat
  | [],      _  => 0
  | l :: ls, nm => if l.name = nm then l.attrs else lookupAttrs ls nm

/- The rebuilt coordinate level: keep its name, take its metadata from the
   equally-named coordinate level of the source `xCoords` (empty if absent). -/
def rebuiltCoord (xCoords : Array Lvl) (c : Lvl) : Lvl :=
  ⟨c.name, lookupAttrs xCoords.toList c.name⟩

/- The rebuilt variable level. In the ordinary case its metadata comes from the
   equally-named variable level of the source `xVars`. In the promotion case
   (the source is a single-variable value combined into a multi-variable result)
   only the source-named variable receives the source's global metadata; the
   other variables are left as the combination produced them. -/
def rebuiltVar (promote : Bool) (xName xGAttrs : Nat) (xVars : Array Lvl) (v : Lvl) : Lvl :=
  ⟨v.name,
    if promote then (if v.name = xName then xGAttrs else v.attrs)
    else lookupAttrs xVars.toList v.name⟩

/- The rebuilt global metadata: empty under promotion, otherwise the source's
   global metadata. -/
def rebuiltGlobal (promote : Bool) (xGAttrs : Nat) : Nat :=
  if promote then 0 else xGAttrs
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rebuild the per-level metadata of a combined result `(resVars, resCoords)`
   from one designated source value described by `(xName, xGAttrs, xVars,
   xCoords)`, under the promotion flag `promote`.

   Coordinate levels ALWAYS take their metadata from the equally-named source
   coordinate (`rebuiltCoord`); variable levels take theirs per `rebuiltVar`;
   the global metadata per `rebuiltGlobal`. Names are preserved and the level
   counts are unchanged. -/
method rebuildAttrs
    (promote : Bool) (xName : Nat) (xGAttrs : Nat)
    (xVars : Array Lvl) (xCoords : Array Lvl)
    (resVars : Array Lvl) (resCoords : Array Lvl)
    return (out : Obj)
  ensures out.gattrs = rebuiltGlobal promote xGAttrs
  ensures out.vars.size = resVars.size
  ensures out.coords.size = resCoords.size
  ensures ∀ i, i < resVars.size → out.vars[i]! = rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
  ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
  do
    -- impl-start
    -- variable levels: each named level takes the source's equally-named metadata
    let mut outVars := resVars
    let mut i := 0
    while i < resVars.size
      invariant i ≤ resVars.size
      invariant outVars.size = resVars.size
      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
      done_with i = resVars.size
    do
      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
      i := i + 1
    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
    let mut outCoords := resCoords
    let mut k := 0
    while k < resCoords.size
      invariant k ≤ resCoords.size
      invariant outCoords.size = resCoords.size
      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
      done_with k = resCoords.size
    do
      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
      k := k + 1
    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
    -- impl-end

prove_correct rebuildAttrs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files (pos_control + atk_1..7) return same_spec=True vs bundle Solution.lean (velvet backend). Command: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ...". Only the impl region was edited; axioms/pure/pre/post byte-identical.

### VERIFY (bash scripts/lean_verify.sh <f>, run concurrently ≤4 at a time in two batches):
  pos_control.lean -> exit 0 (VERIFIES)
  atk_1.lean (prepatch bug: single global-metadata stamp onto every level incl coords/vars) -> exit 1 (unsolved goals @ prove_correct L114)
  atk_2.lean (partial-domain: coords left as identity resCoords) -> exit 1 (unsolved: `resCoords[i]! = rebuiltCoord xCoords resCoords[i]!`)
  atk_3.lean (boundary off-by-one: coord loop starts k:=1, element 0 unrebuilt) -> exit 1
  atk_4.lean (control-flow-effect: gattrs := xGAttrs always, ignores promotion reset to 0) -> exit 1
  atk_5.lean (ungrounded-oracle echo: coord attrs echo the result's own resCoords[k].attrs instead of by-name from xCoords) -> exit 1
  atk_6.lean (var/coord swap: vars use rebuiltCoord, coords use rebuiltVar) -> exit 1
  atk_7.lean (wrong source: non-promote var metadata looked up in xCoords instead of xVars) -> exit 1
All failures are genuine unsolved prove_correct/loom_solve postcondition goals (verified by reading the .out files), NOT parse/syntax errors.

STEP 2 (materialize+resolve faithful patch for every VERIFYING wrong impl): VACUOUS — zero wrong impls verified, so there is no verifying-wrong-impl faithful patch to run. patches={} accordingly. This is NOT a tooling INCONCLUSIVE: the official resolve path was exercised as a positive control — run_resolve('pydata__xarray-7229', gold patch.diff) => RESOLVED=True COMPLETED=True (Docker oracle operational).

REFINEMENT.MD AUDIT: axioms region empty; bundle ships no axiom_check.py; G-AX skips (consistent with meta.json axioms=[], deep_model_references=[]). Legs A1-A5 are all R/I (no A-consumed, no A-reference), so the A-leg correspondence audit is vacuous. No kind-3 leg: the changed op (per-level by-name metadata rebuild) is modeled DEEPLY via rebuiltCoord/rebuiltVar/rebuiltGlobal/lookupAttrs and grounded in structural inputs (resVars/resCoords/xVars/xCoords), not hidden behind an oracle axiom about the function under change (SPEC_GUIDE §0.8). R/I legs are G-CONF's domain — G-CONF passed (100007 inputs, 0 disagreements, seed 7229).

NOTE ON RECORDED PANEL FAILS: meta.json shows G-PANEL-2 (faithfulness) and G-PANEL-3 (leakage) as recorded fails. Those are OUT OF SCOPE for this G-EQ (refinement-fidelity / verify⇒correct) audit and do not affect this verdict; G-PANEL-2's claim (coord ensures demands x's by-name coord attrs while real gold xr.where yields x's GLOBAL attrs on the coord) is a spec-faithfulness question for the panel_2 lane, not a same-spec verifying-twin that resolves differently.

VERDICT: SOUND — ≥5 (7) distinct same-spec attacks encoded and verified; none verifies against the frozen spec, so none can break verify⇒correct; the spec fully determines the output (total function of inputs); positive control verifies; harness resolve path confirmed live via gold control.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a total function of its inputs, so no verifying-but-divergent twin exists. Postconditions pin EVERY field of the output Obj (which has exactly gattrs/vars/coords): `out.gattrs = rebuiltGlobal promote xGAttrs`; `out.vars.size = resVars.size` + `∀ i < resVars.size, out.vars[i]! = rebuiltVar ...`; `out.coords.size = resCoords.size` + `∀ i < resCoords.size, out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)`. Any verifying impl must therefore produce the identical Obj. Empirically: 7 distinct wrong impls all fail to verify with genuine unsolved postcondition goals (e.g. atk_2's unsolved goal is exactly `resCoords[i]! = rebuiltCoord xCoords resCoords[i]!`, the coord clause it violates), while the byte-identical positive control verifies.
```

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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

attribute [solverHint] Array.get_set_c

/- A labelled metadata level of a structured array value: a `name` (the level's
   identifier) and an opaque `attrs` token standing for that level's metadata
   mapping. Distinct tokens model distinct metadata mappings; `0` is the empty
   mapping. Provenance + the value bijection used by the executable checks:
   mapping.md (G-CONF / G-AX). -/
structure Lvl where
  name  : Nat
  attrs : Nat
deriving Inhabited, DecidableEq, Repr

/- A structured array value, reduced to the metadata that the operation touches:
   the global metadata token `gattrs`, the variable levels `vars`, and the
   coordinate levels `coords`. A plain (single-variable) value has `vars = #[]`. -/
structure Obj where
  gattrs : Nat
  vars   : Array Lvl
  coords : Array Lvl
deriving Inhabited

-- axioms-start
-- axioms-end

-- pure-start
/- The metadata token carried by the first level named `nm` in `lvls`, or the
   empty mapping `0` when no level carries that name. This is the by-name
   metadata selection from a designated source value: the metadata of the
   equally-named level, and the empty mapping when the source has no such level. -/
def lookupAttrs : List Lvl → Nat → Nat
  | [],      _  => 0
  | l :: ls, nm => if l.name = nm then l.attrs else lookupAttrs ls nm

/- The rebuilt coordinate level: keep its name, take its metadata from the
   equally-named coordinate level of the source `xCoords` (empty if absent). -/
def rebuiltCoord (xCoords : Array Lvl) (c : Lvl) : Lvl :=
  ⟨c.name, lookupAttrs xCoords.toList c.name⟩

/- The rebuilt variable level. In the ordinary case its metadata comes from the
   equally-named variable level of the source `xVars`. In the promotion case
   (the source is a single-variable value combined into a multi-variable result)
   only the source-named variable receives the source's global metadata; the
   other variables are left as the combination produced them. -/
def rebuiltVar (promote : Bool) (xName xGAttrs : Nat) (xVars : Array Lvl) (v : Lvl) : Lvl :=
  ⟨v.name,
    if promote then (if v.name = xName then xGAttrs else v.attrs)
    else lookupAttrs xVars.toList v.name⟩

/- The rebuilt global metadata: empty under promotion, otherwise the source's
   global metadata. -/
def rebuiltGlobal (promote : Bool) (xGAttrs : Nat) : Nat :=
  if promote then 0 else xGAttrs
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rebuild the per-level metadata of a combined result `(resVars, resCoords)`
   from one designated source value described by `(xName, xGAttrs, xVars,
   xCoords)`, under the promotion flag `promote`.

   Coordinate levels ALWAYS take their metadata from the equally-named source
   coordinate (`rebuiltCoord`); variable levels take theirs per `rebuiltVar`;
   the global metadata per `rebuiltGlobal`. Names are preserved and the level
   counts are unchanged. -/
method rebuildAttrs
    (promote : Bool) (xName : Nat) (xGAttrs : Nat)
    (xVars : Array Lvl) (xCoords : Array Lvl)
    (resVars : Array Lvl) (resCoords : Array Lvl)
    return (out : Obj)
  ensures out.gattrs = rebuiltGlobal promote xGAttrs
  ensures out.vars.size = resVars.size
  ensures out.coords.size = resCoords.size
  ensures ∀ i, i < resVars.size → out.vars[i]! = rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
  ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)
  do
    -- impl-start
    -- variable levels: each named level takes the source's equally-named metadata
    let mut outVars := resVars
    let mut i := 0
    while i < resVars.size
      invariant i ≤ resVars.size
      invariant outVars.size = resVars.size
      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)
      done_with i = resVars.size
    do
      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)
      i := i + 1
    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata
    let mut outCoords := resCoords
    let mut k := 0
    while k < resCoords.size
      invariant k ≤ resCoords.size
      invariant outCoords.size = resCoords.size
      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)
      done_with k = resCoords.size
    do
      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)
      k := k + 1
    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }
    -- impl-end

prove_correct rebuildAttrs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files (pos_control + atk_1..7) return same_spec=True vs bundle Solution.lean (velvet backend). Command: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ...". Only the impl region was edited; axioms/pure/pre/post byte-identical.

### VERIFY (bash scripts/lean_verify.sh <f>, run concurrently ≤4 at a time in two batches):
  pos_control.lean -> exit 0 (VERIFIES)
  atk_1.lean (prepatch bug: single global-metadata stamp onto every level incl coords/vars) -> exit 1 (unsolved goals @ prove_correct L114)
  atk_2.lean (partial-domain: coords left as identity resCoords) -> exit 1 (unsolved: `resCoords[i]! = rebuiltCoord xCoords resCoords[i]!`)
  atk_3.lean (boundary off-by-one: coord loop starts k:=1, element 0 unrebuilt) -> exit 1
  atk_4.lean (control-flow-effect: gattrs := xGAttrs always, ignores promotion reset to 0) -> exit 1
  atk_5.lean (ungrounded-oracle echo: coord attrs echo the result's own resCoords[k].attrs instead of by-name from xCoords) -> exit 1
  atk_6.lean (var/coord swap: vars use rebuiltCoord, coords use rebuiltVar) -> exit 1
  atk_7.lean (wrong source: non-promote var metadata looked up in xCoords instead of xVars) -> exit 1
All failures are genuine unsolved prove_correct/loom_solve postcondition goals (verified by reading the .out files), NOT parse/syntax errors.

STEP 2 (materialize+resolve faithful patch for every VERIFYING wrong impl): VACUOUS — zero wrong impls verified, so there is no verifying-wrong-impl faithful patch to run. patches={} accordingly. This is NOT a tooling INCONCLUSIVE: the official resolve path was exercised as a positive control — run_resolve('pydata__xarray-7229', gold patch.diff) => RESOLVED=True COMPLETED=True (Docker oracle operational).

REFINEMENT.MD AUDIT: axioms region empty; bundle ships no axiom_check.py; G-AX skips (consistent with meta.json axioms=[], deep_model_references=[]). Legs A1-A5 are all R/I (no A-consumed, no A-reference), so the A-leg correspondence audit is vacuous. No kind-3 leg: the changed op (per-level by-name metadata rebuild) is modeled DEEPLY via rebuiltCoord/rebuiltVar/rebuiltGlobal/lookupAttrs and grounded in structural inputs (resVars/resCoords/xVars/xCoords), not hidden behind an oracle axiom about the function under change (SPEC_GUIDE §0.8). R/I legs are G-CONF's domain — G-CONF passed (100007 inputs, 0 disagreements, seed 7229).

NOTE ON RECORDED PANEL FAILS: meta.json shows G-PANEL-2 (faithfulness) and G-PANEL-3 (leakage) as recorded fails. Those are OUT OF SCOPE for this G-EQ (refinement-fidelity / verify⇒correct) audit and do not affect this verdict; G-PANEL-2's claim (coord ensures demands x's by-name coord attrs while real gold xr.where yields x's GLOBAL attrs on the coord) is a spec-faithfulness question for the panel_2 lane, not a same-spec verifying-twin that resolves differently.

VERDICT: SOUND — ≥5 (7) distinct same-spec attacks encoded and verified; none verifies against the frozen spec, so none can break verify⇒correct; the spec fully determines the output (total function of inputs); positive control verifies; harness resolve path confirmed live via gold control.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/too-strong) audit for pydata__xarray-7229 velvet. Steps: (1) Spec-region byte-identity confirmed via swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet backend) = True — the frozen spec (Lvl/Obj structures, empty axioms, pure helpers lookupAttrs/rebuiltCoord/rebuiltVar/rebuiltGlobal, empty pre/post-condition regions, rebuildAttrs signature + 5 ensures clauses) is identical between the verifying solution and the buggy twin; only impl/proof differ. Worktree is at base_commit 3aa75c8d with the gold `where` patch applied (per-level by-name metadata rebuild in xarray/core/computation.py). (3) Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (global-stamp impl) FAILS (exit 1, unmet coord/var by-name ensures) — spec is tight yet satisfiable, not vacuous or unprovable. (4) Model<->real-callee agreement: ran conformance_check.py shadow (rebuiltGlobal/rebuiltVar/rebuiltCoord/lookupAttrs transliterated) vs patched xr.where(keep_attrs=True) — 0 disagreements over boundary matrix + 2007 fuzz inputs. (5) Adversarial differential probes directly against the patched real repo, targeting cases the pinned corpus never exercises: both-multi-var Datasets, promotion with x.name IN result vars, promotion with x.name NOT in result vars, promotion with an extra non-x-name variable u (model uses keep_attrs=False skeleton; gold leaves apply_ufunc(keep_attrs=True) value — both {} in every config tried), x with extra non-dim coord, y with extra coord absent from x, scalar x. ALL matched the gold. No diverging input found: the modeled rebuildAttrs (coords ALWAYS by-name, vars by-name/promotion, global {}-on-promote-else-x) exactly captures the gold post-apply_ufunc rebuild. Spec does not drift from and is not stronger than the real gold-patched behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, "Scope of what is disclosed":

> The spec view discloses: at each level of the combined result, metadata is rebuilt from the equally-named level of the designated source value — coordinates always by name, variables by name, the global token from the source — AND a promotion sub-case in which a single-variable source combined into a multi-variable result empties the global metadata and fills only the source-named variable. The "rebuild each level by name, coordinates included" half is PS-derivable and does not leak; the **promotion sub-case** (the `promote` flag, the `rebuiltGlobal` empty-under-promotion clause, and the `rebuiltVar` promotion branch) is the relaxed disclosure.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "Why faithful + non-leaking is impossible":

> The sole FAIL_TO_PASS `xarray/tests/test_computation.py::test_where_attrs` contains the "2 DataArrays and 1 Dataset (promotion)" assertion, so a spec that did not model the promotion case (global attrs emptied, only the `x.name`-named variable filled) would admit a wrong implementation that verifies yet fails the F2P test — violating G-EQ / `verify ⟹ correct`.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `5a3783cb649c`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Counterexample / evidence:

```
Reconstruction test. A reader given ONLY the public problem_statement — title '`xr.where(..., keep_attrs=True)` overwrites coordinate attributes', 'Coordinate attributes should be preserved', and the sole example `xr.where(True, ds.air, ds.air, keep_attrs=True)` (a same-type Dataset⊗Dataset op) — can derive the coordinate-preservation half of the fix (rebuild each level by name from x, coordinates included) but has NO way to derive the PROMOTION special-case: when a single-variable source x (DataArray) is combined into a multi-variable result because y is a Dataset, the result's GLOBAL attrs are emptied and only the x.name-named variable receives x's global attrs. The spec view hands this sub-case over verbatim via the `promote` flag: `rebuiltGlobal promote xGAttrs = if promote then 0 else xGAttrs` mirrors the gold `result.attrs = {}`, and `rebuiltVar` with `if promote then (if v.name = xName then xGAttrs else v.attrs)` mirrors the gold `if getattr(x,'name',None) in result.data_vars: result[x.name].attrs = getattr(x,'attrs',{})`. This is exactly the discriminator pinned by the hidden FAIL_TO_PASS test_where_attrs '2 DataArrays + 1 Dataset (promotion)' case. Token scan of problem_statement (and hints_text) confirms absence: 0 occurrences of promot/promoted, data_var, x.name, single/multi-variable, isinstance; hints_text discusses only the scalar-x / attrs[1] / _get_all_of_type diagnosis of the original bug — not the promotion branch. The promotion behavior is present only in the gold diff's `isinstance(y, Dataset) and not isinstance(x, Dataset)` branch and the hidden test_patch. A doc-block comment in the spec view even narrates it: 'In the promotion case (the source is a single-variable value combined into a multi-variable result) only the source-named variable receives the source's global metadata; the other variables are left as the combination produced them.'
```

same_spec(Solution.lean, Solution_prepatch.lean) = True (verified via swebench_unified.markers.same_spec with VelvetBackend) — the spec region is byte-identical, so this leakage judgment is over a legitimate frozen spec view. The lexical G-LEAK screen passes: no xarray/where/keep_attrs/apply_ufunc/Dataset/getattr/isinstance identifier appears; the leak is SEMANTIC (the modeled behavior itself), not lexical. The 'rebuild each level by name, coordinates included' content is PS-derivable and does NOT leak; the leaking increment is strictly the promotion sub-case (promote flag + rebuiltGlobal's empty-under-promotion + rebuiltVar's promotion branch). This is a genuine LEAKAGE beyond problem_statement.

The bundle itself concedes it: relaxed_leakage=true, RELAXED_LEAKAGE.md documents the unavoidable-leak disposition, and recorded G-PANEL-3 = LEAKAGE / G-PANEL-2 = UNFAITHFUL. Per the 2026-08-06 policy, G-PANEL-3 defers to the accepted RELAXED_LEAKAGE.md on this relaxed bundle and the derivation records pass+note rather than fail — but the honest attacker verdict on the question 'does the spec view leak the gold edit beyond problem_statement' is LEAKAGE. (Note also G-PANEL-2 faithfulness fail flags a distinct real concern about the coord ensures vs. real xr.where on the air_temperature case; that is outside my leakage role.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.
