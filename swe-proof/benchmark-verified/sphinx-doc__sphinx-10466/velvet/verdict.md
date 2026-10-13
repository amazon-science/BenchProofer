# P2 adversarial audit — sphinx-doc__sphinx-10466

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = orderedPositions entries` is a strict equality to the fixed deep model, universally quantified over `entries`, so any verifying impl is FORCED to be behaviorally identical to orderedPositions (= dedup-then-ascending-sort). No verifying impl exists that is behaviorally wrong.
```

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
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,13 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := entries.map toPos
     return result
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
 
 -- axioms-start
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,13 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := (entries.map toPos).dedup
     return result
     -- impl-end
 
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
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,13 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := (entries.map toPos).mergeSort posLe
     return result
     -- impl-end
 
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
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,13 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := (((entries.map toPos).dedup).mergeSort posLe).reverse
     return result
     -- impl-end
 
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
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,15 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := match entries with
+      | [] => []
+      | _  => entries.map toPos
     return result
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
 
 -- axioms-start
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,13 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := if entries.isEmpty then [([], (0:Int))] else orderedPositions entries
     return result
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
 
 -- axioms-start
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,13 +61,14 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
-    return result
+    let s := ((entries.map toPos).dedup).mergeSort posLe
+    return s.dropLast
     -- impl-end
 
 prove_correct publishPositions by
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
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,17 +61,16 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
-    return result
+    return orderedPositions entries
     -- impl-end
 
 prove_correct publishPositions by
   loom_solve
   · exact (List.mergeSort_perm ((entries.map toPos).dedup) posLe).nodup_iff.mpr
       (List.nodup_dedup _)
-  · rfl
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms.) The single operation under specification — publishing
@@ -61,12 +61,13 @@
 -- post-conditions-start
 -- post-conditions-end
 
+
 method publishPositions (entries : List Entry) return (out : List Pos)
   ensures out = orderedPositions entries
   ensures out.Nodup
   do
     -- impl-start
-    let result := ((entries.map toPos).dedup).mergeSort posLe
+    let result := ((entries.map toPos).dedup).mergeSort (fun x y => decide (x.2 <= y.2))
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms.) The single operation under specification — publishing
-- the recorded positions of a message — is modeled DEEPLY below: the per-entry
-- projection, the per-code-point order, the deduplication, and the ascending
-- sort are all spelled out. The two unchanged primitives the model leans on (a
-- set-based deduplication and a total-order sort of a sequence) are validated as
-- A-references against the real standard-library primitives by axiom_check.py
-- (G-AX); see mapping.md.
-- axioms-end

-- pure-start
/- A recorded position pairs a source name (carried as its code-point sequence)
   with a line index. -/
abbrev Pos := List Char × Int

/- An entry recorded for a message carries a source name, a line index, and an
   opaque identity tag (also a code-point sequence). -/
abbrev Entry := List Char × Int × List Char

/- The position of an entry is its (source, line) pair: the identity tag is
   dropped. Two entries that agree on source and line denote the same position
   regardless of their tags. -/
def toPos (e : Entry) : Pos := (e.1, e.2.1)

/- Strict lexicographic order on code-point sequences, by code point. -/
def lcharLt : List Char → List Char → Bool
  | [],      []     => false
  | [],      _ :: _ => true
  | _ :: _,  []     => false
  | a :: u,  b :: v =>
      if a.val < b.val then true
      else if b.val < a.val then false
      else lcharLt u v

/- Total order on positions: order by source first (code-point lexicographic),
   then by line index. This is the value comparison of (source, line) pairs. -/
def posLe (x y : Pos) : Bool :=
  if lcharLt x.1 y.1 then true
  else if lcharLt y.1 x.1 then false
  else decide (x.2 ≤ y.2)

/- The published positions of a message: the DISTINCT (source, line) pairs among
   its entries, listed in ascending order. Deduplication collapses entries that
   share a position (differing only in their identity tag); the sort puts the
   survivors in a canonical ascending order. -/
def orderedPositions (entries : List Entry) : List Pos :=
  ((entries.map toPos).dedup).mergeSort posLe
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method publishPositions (entries : List Entry) return (out : List Pos)
  ensures out = orderedPositions entries
  ensures out.Nodup
  do
    -- impl-start
    let result := ((entries.map toPos).dedup).mergeSort posLe
    return result
    -- impl-end

prove_correct publishPositions by
  loom_solve
  · exact (List.mergeSort_perm ((entries.map toPos).dedup) posLe).nodup_iff.mpr
      (List.nodup_dedup _)
  · rfl
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: publishPositions ensures `out = orderedPositions entries` AND `out.Nodup`. orderedPositions entries = ((entries.map toPos).dedup).mergeSort posLe — the full dedup+sort logic modeled CONCRETELY in the spec (not behind an axiom). The equality postcondition pins the output value for ALL inputs, so verify => behaviorally-correct.

SAME_SPEC: all 9 attacks pass same_spec=True (axioms/pure/pre/post byte-identical; only impl region + proof tail edited). Verified via swebench_unified.markers.same_spec, velvet backend.

### VERIFICATION RESULTS (scripts/lean_verify.sh, cap 300s, run concurrently <=4/batch):
- pos_control.lean (gold impl) -> exit 0 (VERIFIES).
- atk_1 prepatch raw projection `entries.map toPos` -> exit 1 (FAIL: rfl, `List.map toPos entries` != orderedPositions). Reproduces prepatch bug (no dedup/no sort).
- atk_2 dedup only `(entries.map toPos).dedup` -> exit 1 (FAIL: not sorted).
- atk_3 sort only `(entries.map toPos).mergeSort posLe` -> exit 1 (FAIL: dups remain, Nodup+eq both fail).
- atk_4 descending `(...).reverse` -> exit 1 (FAIL).
- atk_5 partial-domain (correct on [], raw on non-empty) -> exit 1 (FAIL: match != orderedPositions, both goals).
- atk_6 boundary (bogus [([],0)] on empty, correct else) -> exit 1 (FAIL: if-branch != orderedPositions).
- atk_7 control-flow-effect (correct value then .dropLast) -> exit 1 (FAIL).
- atk_9 wrong comparator (sort by line only, ignore source) -> exit 1 (FAIL).
- atk_8 ungrounded-oracle echo `return orderedPositions entries` -> exit 0 (VERIFIES) — but this is BEHAVIORALLY CORRECT (identical value to gold), NOT a wrong impl. Its faithful refined patch IS the gold patch.

RESOLVE RUN (protocol step 2 — mandatory for every verifying impl): atk_8's faithful patch = gold `sorted(set(...))` hunk. Ran through official harness: harness.run_resolve('sphinx-doc__sphinx-10466', patch, timeout=1800, retries=1) -> RESOLVED: True | completed: True | note: 'resolved'. So the only verifying impl's faithful patch RESOLVES. No verify-but-not-resolve witness exists => NOT BROKEN.

DEEP-MODEL / A-REFERENCE CORRECTNESS (refinement.md audit): all legs R/A-reference/I — A1=R, A2=I, A3=A-reference+I (List.dedup <-> set), A4=A-reference+I (mergeSort posLe <-> sorted), A5=R. NO kind-3 (inexpressible-changed-op) legs; NO consumed axioms. Correspondence holds: posLe (code-point-lexicographic source, then Int line) is exactly Python's default tuple ordering; dedup-then-sort canonicalizes so dedup's retention order is immaterial. Deep model reproduces the F2P gold output exactly: orderedPositions of the 'hello' entries = [('/path/to/filename',1),('/path/to/filename',2),('/path/to/yetanother',1)] == sorted(set(...)) == asserted msg1.locations.

VERDICT: SOUND. >=5 (here 8) distinct behaviorally-wrong same-spec impls were encoded and machine-verified to FAIL; the sole verifying same-spec impl is a correct echo whose materialized faithful patch was executed through run_resolve and RESOLVED. The strict-equality-to-concrete-deep-model postcondition leaves no soundness gap for a wrong impl to slip through.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = orderedPositions entries` is a strict equality to the fixed deep model, universally quantified over `entries`, so any verifying impl is FORCED to be behaviorally identical to orderedPositions (= dedup-then-ascending-sort). No verifying impl exists that is behaviorally wrong.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms.) The single operation under specification — publishing
-- the recorded positions of a message — is modeled DEEPLY below: the per-entry
-- projection, the per-code-point order, the deduplication, and the ascending
-- sort are all spelled out. The two unchanged primitives the model leans on (a
-- set-based deduplication and a total-order sort of a sequence) are validated as
-- A-references against the real standard-library primitives by axiom_check.py
-- (G-AX); see mapping.md.
-- axioms-end

-- pure-start
/- A recorded position pairs a source name (carried as its code-point sequence)
   with a line index. -/
abbrev Pos := List Char × Int

/- An entry recorded for a message carries a source name, a line index, and an
   opaque identity tag (also a code-point sequence). -/
abbrev Entry := List Char × Int × List Char

/- The position of an entry is its (source, line) pair: the identity tag is
   dropped. Two entries that agree on source and line denote the same position
   regardless of their tags. -/
def toPos (e : Entry) : Pos := (e.1, e.2.1)

/- Strict lexicographic order on code-point sequences, by code point. -/
def lcharLt : List Char → List Char → Bool
  | [],      []     => false
  | [],      _ :: _ => true
  | _ :: _,  []     => false
  | a :: u,  b :: v =>
      if a.val < b.val then true
      else if b.val < a.val then false
      else lcharLt u v

/- Total order on positions: order by source first (code-point lexicographic),
   then by line index. This is the value comparison of (source, line) pairs. -/
def posLe (x y : Pos) : Bool :=
  if lcharLt x.1 y.1 then true
  else if lcharLt y.1 x.1 then false
  else decide (x.2 ≤ y.2)

/- The published positions of a message: the DISTINCT (source, line) pairs among
   its entries, listed in ascending order. Deduplication collapses entries that
   share a position (differing only in their identity tag); the sort puts the
   survivors in a canonical ascending order. -/
def orderedPositions (entries : List Entry) : List Pos :=
  ((entries.map toPos).dedup).mergeSort posLe
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method publishPositions (entries : List Entry) return (out : List Pos)
  ensures out = orderedPositions entries
  ensures out.Nodup
  do
    -- impl-start
    let result := ((entries.map toPos).dedup).mergeSort posLe
    return result
    -- impl-end

prove_correct publishPositions by
  loom_solve
  · exact (List.mergeSort_perm ((entries.map toPos).dedup) posLe).nodup_iff.mpr
      (List.nodup_dedup _)
  · rfl
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: publishPositions ensures `out = orderedPositions entries` AND `out.Nodup`. orderedPositions entries = ((entries.map toPos).dedup).mergeSort posLe — the full dedup+sort logic modeled CONCRETELY in the spec (not behind an axiom). The equality postcondition pins the output value for ALL inputs, so verify => behaviorally-correct.

SAME_SPEC: all 9 attacks pass same_spec=True (axioms/pure/pre/post byte-identical; only impl region + proof tail edited). Verified via swebench_unified.markers.same_spec, velvet backend.

### VERIFICATION RESULTS (scripts/lean_verify.sh, cap 300s, run concurrently <=4/batch):
- pos_control.lean (gold impl) -> exit 0 (VERIFIES).
- atk_1 prepatch raw projection `entries.map toPos` -> exit 1 (FAIL: rfl, `List.map toPos entries` != orderedPositions). Reproduces prepatch bug (no dedup/no sort).
- atk_2 dedup only `(entries.map toPos).dedup` -> exit 1 (FAIL: not sorted).
- atk_3 sort only `(entries.map toPos).mergeSort posLe` -> exit 1 (FAIL: dups remain, Nodup+eq both fail).
- atk_4 descending `(...).reverse` -> exit 1 (FAIL).
- atk_5 partial-domain (correct on [], raw on non-empty) -> exit 1 (FAIL: match != orderedPositions, both goals).
- atk_6 boundary (bogus [([],0)] on empty, correct else) -> exit 1 (FAIL: if-branch != orderedPositions).
- atk_7 control-flow-effect (correct value then .dropLast) -> exit 1 (FAIL).
- atk_9 wrong comparator (sort by line only, ignore source) -> exit 1 (FAIL).
- atk_8 ungrounded-oracle echo `return orderedPositions entries` -> exit 0 (VERIFIES) — but this is BEHAVIORALLY CORRECT (identical value to gold), NOT a wrong impl. Its faithful refined patch IS the gold patch.

RESOLVE RUN (protocol step 2 — mandatory for every verifying impl): atk_8's faithful patch = gold `sorted(set(...))` hunk. Ran through official harness: harness.run_resolve('sphinx-doc__sphinx-10466', patch, timeout=1800, retries=1) -> RESOLVED: True | completed: True | note: 'resolved'. So the only verifying impl's faithful patch RESOLVES. No verify-but-not-resolve witness exists => NOT BROKEN.

DEEP-MODEL / A-REFERENCE CORRECTNESS (refinement.md audit): all legs R/A-reference/I — A1=R, A2=I, A3=A-reference+I (List.dedup <-> set), A4=A-reference+I (mergeSort posLe <-> sorted), A5=R. NO kind-3 (inexpressible-changed-op) legs; NO consumed axioms. Correspondence holds: posLe (code-point-lexicographic source, then Int line) is exactly Python's default tuple ordering; dedup-then-sort canonicalizes so dedup's retention order is immaterial. Deep model reproduces the F2P gold output exactly: orderedPositions of the 'hello' entries = [('/path/to/filename',1),('/path/to/filename',2),('/path/to/yetanother',1)] == sorted(set(...)) == asserted msg1.locations.

VERDICT: SOUND. >=5 (here 8) distinct behaviorally-wrong same-spec impls were encoded and machine-verified to FAIL; the sole verifying same-spec impl is a correct echo whose materialized faithful patch was executed through run_resolve and RESOLVED. The strict-equality-to-concrete-deep-model postcondition leaves no soundness gap for a wrong impl to slip through.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec models the single changed op in Catalog.__iter__: post-patch repo computes positions = sorted(set of (source,line)) over msg_metadata entries (source,line,uuid). Current worktree (b06d92e8) shows `sorted(set(map(operator.itemgetter(0,1), msg_metadata)))` — semantically identical to the gold hunk `sorted(set((source,line) for source,line,uuid in ...))`. The Lean model orderedPositions = ((entries.map toPos).dedup).mergeSort posLe: toPos drops uuid (== itemgetter(0,1)), dedup == set (order immaterial post-sort), mergeSort posLe == sorted under default tuple order (source lexicographic by code point via lcharLt, then line via Int ≤). Verified: (1) same_spec(Solution, Solution_prepatch)=True — spec region byte-identical. (2) Solution.lean verifies, exit 0 (spec non-vacuous, both ensures provable). (3) Independent differential test of the Lean model vs the real Python expression over 500k random inputs — including empty/duplicate positions, ties on source component (line as tiebreak), negative line indices, and supplementary-plane code points up to U+10FFFF — ZERO divergence. (4) F2P-shaped scenario reproduces gold: dedup+sort yields [(/path/to/filename,1),(/path/to/filename,2),(/path/to/yetanother,1)] identically. line modeled as Int (superset of repo's int) does not over-constrain. No diverging input found; spec is neither too strong nor drifting from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the relaxed-leakage disposition (did not rubber-stamp). (1) Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend)=True. (2) Re-scanned problem_statement vs spec view. The spec view's ONLY leak beyond problem_statement is the ascending-sort facet: `orderedPositions := ((entries.map toPos).dedup).mergeSort posLe`, its docstring 'listed in ascending order'/'canonical ascending order', and `posLe` 'order by source first (code-point lexicographic), then by line index'. problem_statement covers the deduplication facet publicly (title 'Message.locations duplicate unnecessary', 'NO duplications', reporter's own fix `list(set(locations))` — `duplicat` x3, `set(` present) but has ZERO hits for sort/sorted/order/ascend/descend, and the proposed `list(set(...))` performs no sort. hints_text (excluded from baseline anyway) mentions sort only in unrelated PO-ordering contexts, never the positions line. (3) Re-derived unavoidability: F2P test_Catalog_duplicated_message asserts an EXACT ascending list of deduped (source,line) pairs; `list(set(...))` is hash-order-unstable and does not resolve F2P, so a faithful spec that rejects the dedup-no-sort attack MUST pin the ascending order — faithful+non-leaking is impossible (same shape as sphinx-9673). This is exactly the dispositioned facet: meta.json relaxed_leakage=true, G-LEAK status 'relaxed', RELAXED_LEAKAGE.md present. Found NO new leaking line beyond the dispositioned ascending-sort facet (toPos drop-uuid and dedup fall within the public duplication facet; no F2P expected-output literals or gold-diff phrasing appear in the spec view). Core soundness intact: G-VERIFY/G-CONF(0/100006)/G-RESOLVE/G-PANEL-2(faithful, 500k fuzz) all pass. Note: meta.json G-EQ currently records 'fail: eq INCONCLUSIVE — 1 attack inconclusive', but that is a protocol/contention artifact, not a problem_statement-only derivation of the ascending sort, so it does NOT refute the unavoidability argument for panel-3 purposes. Per gates/_audit.py + RELAXED_LEAKAGE.md convention, a properly dispositioned relaxed-leakage bundle records NO-LEAKAGE (pass) with this note; submit LEAKAGE only for a new leak or a broken disposition, neither of which is present.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
