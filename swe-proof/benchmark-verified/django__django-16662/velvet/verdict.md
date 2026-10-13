# P2 adversarial audit — django__django-16662

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `out = sortImports imports` is an EXACT functional equality that pins any verifying impl to be Lean-provably extensionally equal to `imports.mergeSort keyLe`. Every behaviorally-divergent attack fails verification; the only impls that verify are extensionally identical to gold and their faithful patches resolve.
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
 
 -- axioms-start
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,11 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    let result := imports.mergeSort (fun x y => lcharLe (moduleTok x) (moduleTok y))
     return result
     -- impl-end
 
 prove_correct orderImportLines by
   loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
+  · exact (List.mergeSort_perm imports (fun x y => lcharLe (moduleTok x) (moduleTok y)))
   · rfl
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
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,13 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    let result := imports.mergeSort (fun x y =>
+      if isQualified x = isQualified y then lcharLe (moduleTok x) (moduleTok y)
+      else (isQualified x == true))
     return result
     -- impl-end
 
 prove_correct orderImportLines by
   loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
+  · exact (List.mergeSort_perm imports _)
   · rfl
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
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,11 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    let result := imports.mergeSort (fun x y => lcharLe (firstTok x) (firstTok y))
     return result
     -- impl-end
 
 prove_correct orderImportLines by
   loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
+  · exact (List.mergeSort_perm imports (fun x y => lcharLe (firstTok x) (firstTok y)))
   · rfl
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,11 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    let result := match imports with
+      | [] => []
+      | xs => xs.mergeSort keyLe
     return result
     -- impl-end
 
 prove_correct orderImportLines by
-  loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
-  · rfl
+  loom_solve <;> cases imports <;> simp_all [sortImports, List.mergeSort_perm]
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
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,11 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    let result := (imports.mergeSort keyLe).reverse
     return result
     -- impl-end
 
 prove_correct orderImportLines by
   loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
+  · simp [sortImports]
   · rfl
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
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,16 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    -- strict variant of keyLe: whole-module group first, then strict lex on moduleTok
+    let keyLt := fun (x y : List Char) =>
+      if isQualified x = isQualified y then
+        (lcharLe (moduleTok x) (moduleTok y) && ! (lcharLe (moduleTok y) (moduleTok x)))
+      else (isQualified x == false)
+    let result := imports.mergeSort keyLt
     return result
     -- impl-end
 
 prove_correct orderImportLines by
   loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
+  · exact (List.mergeSort_perm imports _)
   · rfl
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed axioms.) The single operation under specification — ordering a
@@ -73,11 +73,12 @@
   ensures List.Perm out imports
   do
     -- impl-start
-    let result := imports.mergeSort keyLe
+    let result := sortImports imports
     return result
     -- impl-end
 
 prove_correct orderImportLines by
   loom_solve
-  · exact (List.mergeSort_perm imports keyLe)
-  · rfl
+  all_goals first
+    | rfl
+    | (unfold sortImports; exact (List.mergeSort_perm imports keyLe))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms.) The single operation under specification — ordering a
-- collection of import-statement lines — is modeled DEEPLY below: the token
-- split, the per-character ordering, and the stable sort are all spelled out.
-- The two unchanged primitives they stand in for (a whitespace token split and
-- a stable key-sort of a sequence) are validated as A-references against the
-- real standard-library primitives by axiom_check.py (G-AX); see mapping.md.
-- axioms-end

-- pure-start
/- An import-statement line is carried as its sequence of code points
   (`List Char`). A line is "qualified" when its first whitespace-delimited
   token is the word `from` (i.e. it brings named objects in from a module);
   otherwise it names a whole module directly. The public coding-style rule
   asks that whole-module lines be grouped ahead of qualified lines, and that
   within each group the ordering follows the module token. -/

/- The first whitespace-delimited token of a line. -/
def firstTok : List Char → List Char
  | [] => []
  | c :: cs => if c = ' ' then [] else c :: firstTok cs

/- Everything after the first whitespace-delimited token (its delimiter
   consumed). -/
def afterFirst : List Char → List Char
  | [] => []
  | c :: cs => if c = ' ' then cs else afterFirst cs

/- The second whitespace-delimited token: the module token the ordering keys
   on (the part after the leading keyword). -/
def moduleTok (l : List Char) : List Char := firstTok (afterFirst l)

/- A line is qualified iff its leading token is the word `from`. -/
def isQualified (l : List Char) : Bool := firstTok l == "from".toList

/- Lexicographic order on code-point sequences, by code point. Total: every
   pair is comparable, mirroring value comparison of the module tokens. -/
def lcharLe : List Char → List Char → Bool
  | [], _ => true
  | _ :: _, [] => false
  | a :: u, b :: v =>
      if a.val < b.val then true
      else if b.val < a.val then false
      else lcharLe u v

/- The ordering key: whole-module lines (`isQualified = false`) sort ahead of
   qualified lines (`isQualified = true`); within each group the module token
   under `lcharLe` decides the order. This is the composite-key comparison. -/
def keyLe (x y : List Char) : Bool :=
  if isQualified x = isQualified y then lcharLe (moduleTok x) (moduleTok y)
  else (isQualified x == false)

/- The fully ordered collection: a stable sort of the lines under `keyLe`. -/
def sortImports (l : List (List Char)) : List (List Char) := l.mergeSort keyLe
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method orderImportLines (imports : List (List Char)) return (out : List (List Char))
  ensures out = sortImports imports
  ensures List.Perm out imports
  do
    -- impl-start
    let result := imports.mergeSort keyLe
    return result
    -- impl-end

prove_correct orderImportLines by
  loom_solve
  · exact (List.mergeSort_perm imports keyLe)
  · rfl
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Same_spec=True confirmed for all 7 attacks + pos_control (swebench_unified.markers.same_spec, velvet). Verified each with `bash scripts/lean_verify.sh <f>` from project root.

VERIFY RESULTS (rc): pos_control=0 (verifies). atk_1 (prepatch bug: moduleTok-only, no grouping)=1 FAIL. atk_2 (reversed grouping, qualified-first)=1 FAIL. atk_3 (wrong token: firstTok key)=1 FAIL. atk_4 (partial-domain: `match []=>[] | xs=>xs.mergeSort keyLe`)=0 VERIFIES. atk_5 (control-flow-effect: `(mergeSort keyLe).reverse`)=1 FAIL. atk_6 (boundary: strict lex comparator keyLt)=1 FAIL. atk_7 (ungrounded-oracle echo: `sortImports imports` directly)=0 VERIFIES. All failures are on the `out = sortImports imports` goal (exact-equality rejects behavioral divergence), confirming the spec is tight.

RESOLVE RESULTS (for the 2 verifying attacks; run_resolve, timeout 1800, SERIAL). NOTE: an initial parallel batch returned completed=false (harness concurrency race — harness.py itself warns concurrent runs corrupt each other; NOT counted). Re-run SOLO: atk_7 patch (byte-identical to gold) => resolved=true, completed=true, attempts=1, note="resolved" (also serves as harness sanity/positive-resolve control). atk_4 patch (empty-guard around identical composite-key sorted()) => resolved=true, completed=true, attempts=1, note="resolved". Commands: `python3 -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-16662", <patch>, run_id=..., timeout=1800)'`.

WHY SOUND: postcondition `out = sortImports imports` (= `imports.mergeSort keyLe`) is exact functional equality, so verify FORCES extensional equality to gold. The two verifying impls (atk_4 [] guard — `[].mergeSort=[]` so identical; atk_7 direct oracle echo) are extensionally gold; their faithful refined patches both resolve. No verifying-but-wrong impl exists => no verify⇏ correct gap.

REFINEMENT.MD LEG AUDIT: 6 legs, all R/A-reference/I, NO kind-3, NO consumed axioms. A1 (set[str]<->List(List Char), input-order-immaterial, out~imports frame)=R. A2 (firstTok/moduleTok token split)=A-reference+I. A3 (isQualified == 'from')=I. A4 (composite keyLe grouping — the CHANGED behavior)=I, concrete, G-CONF-tested (NOT axiomatized — correct: the genuine change is modeled concretely). A5 (mergeSort keyLe == stable sorted)=A-reference+I. A6 (render/join + Perm frame)=R. A-reference correspondence independently re-checked in Python (seed 16662): firstTok==split()[0], moduleTok==split()[1] over 20000 fuzzed single-space import lines, and mergeSort-key stable-sort == sorted(key=composite) over 5000 lists — 0 mismatches. axiom_check.py imports only stdlib (random, sys). Prepatch bug reproduced (atk_1) and correctly fails verification; matches Solution_prepatch.lean intent.

Verdict SOUND: >=5 distinct attacks (7 total: partial-domain, boundary, control-flow-effect, wrong-token, reversed-grouping, ungrounded-oracle echo, prepatch) all run and verified; every verifying attack's faithful patch materialized and resolve-RUN to completion; none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `out = sortImports imports` is an EXACT functional equality that pins any verifying impl to be Lean-provably extensionally equal to `imports.mergeSort keyLe`. Every behaviorally-divergent attack fails verification; the only impls that verify are extensionally identical to gold and their faithful patches resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms.) The single operation under specification — ordering a
-- collection of import-statement lines — is modeled DEEPLY below: the token
-- split, the per-character ordering, and the stable sort are all spelled out.
-- The two unchanged primitives they stand in for (a whitespace token split and
-- a stable key-sort of a sequence) are validated as A-references against the
-- real standard-library primitives by axiom_check.py (G-AX); see mapping.md.
-- axioms-end

-- pure-start
/- An import-statement line is carried as its sequence of code points
   (`List Char`). A line is "qualified" when its first whitespace-delimited
   token is the word `from` (i.e. it brings named objects in from a module);
   otherwise it names a whole module directly. The public coding-style rule
   asks that whole-module lines be grouped ahead of qualified lines, and that
   within each group the ordering follows the module token. -/

/- The first whitespace-delimited token of a line. -/
def firstTok : List Char → List Char
  | [] => []
  | c :: cs => if c = ' ' then [] else c :: firstTok cs

/- Everything after the first whitespace-delimited token (its delimiter
   consumed). -/
def afterFirst : List Char → List Char
  | [] => []
  | c :: cs => if c = ' ' then cs else afterFirst cs

/- The second whitespace-delimited token: the module token the ordering keys
   on (the part after the leading keyword). -/
def moduleTok (l : List Char) : List Char := firstTok (afterFirst l)

/- A line is qualified iff its leading token is the word `from`. -/
def isQualified (l : List Char) : Bool := firstTok l == "from".toList

/- Lexicographic order on code-point sequences, by code point. Total: every
   pair is comparable, mirroring value comparison of the module tokens. -/
def lcharLe : List Char → List Char → Bool
  | [], _ => true
  | _ :: _, [] => false
  | a :: u, b :: v =>
      if a.val < b.val then true
      else if b.val < a.val then false
      else lcharLe u v

/- The ordering key: whole-module lines (`isQualified = false`) sort ahead of
   qualified lines (`isQualified = true`); within each group the module token
   under `lcharLe` decides the order. This is the composite-key comparison. -/
def keyLe (x y : List Char) : Bool :=
  if isQualified x = isQualified y then lcharLe (moduleTok x) (moduleTok y)
  else (isQualified x == false)

/- The fully ordered collection: a stable sort of the lines under `keyLe`. -/
def sortImports (l : List (List Char)) : List (List Char) := l.mergeSort keyLe
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method orderImportLines (imports : List (List Char)) return (out : List (List Char))
  ensures out = sortImports imports
  ensures List.Perm out imports
  do
    -- impl-start
    let result := imports.mergeSort keyLe
    return result
    -- impl-end

prove_correct orderImportLines by
  loom_solve
  · exact (List.mergeSort_perm imports keyLe)
  · rfl
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Same_spec=True confirmed for all 7 attacks + pos_control (swebench_unified.markers.same_spec, velvet). Verified each with `bash scripts/lean_verify.sh <f>` from project root.

VERIFY RESULTS (rc): pos_control=0 (verifies). atk_1 (prepatch bug: moduleTok-only, no grouping)=1 FAIL. atk_2 (reversed grouping, qualified-first)=1 FAIL. atk_3 (wrong token: firstTok key)=1 FAIL. atk_4 (partial-domain: `match []=>[] | xs=>xs.mergeSort keyLe`)=0 VERIFIES. atk_5 (control-flow-effect: `(mergeSort keyLe).reverse`)=1 FAIL. atk_6 (boundary: strict lex comparator keyLt)=1 FAIL. atk_7 (ungrounded-oracle echo: `sortImports imports` directly)=0 VERIFIES. All failures are on the `out = sortImports imports` goal (exact-equality rejects behavioral divergence), confirming the spec is tight.

RESOLVE RESULTS (for the 2 verifying attacks; run_resolve, timeout 1800, SERIAL). NOTE: an initial parallel batch returned completed=false (harness concurrency race — harness.py itself warns concurrent runs corrupt each other; NOT counted). Re-run SOLO: atk_7 patch (byte-identical to gold) => resolved=true, completed=true, attempts=1, note="resolved" (also serves as harness sanity/positive-resolve control). atk_4 patch (empty-guard around identical composite-key sorted()) => resolved=true, completed=true, attempts=1, note="resolved". Commands: `python3 -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-16662", <patch>, run_id=..., timeout=1800)'`.

WHY SOUND: postcondition `out = sortImports imports` (= `imports.mergeSort keyLe`) is exact functional equality, so verify FORCES extensional equality to gold. The two verifying impls (atk_4 [] guard — `[].mergeSort=[]` so identical; atk_7 direct oracle echo) are extensionally gold; their faithful refined patches both resolve. No verifying-but-wrong impl exists => no verify⇏ correct gap.

REFINEMENT.MD LEG AUDIT: 6 legs, all R/A-reference/I, NO kind-3, NO consumed axioms. A1 (set[str]<->List(List Char), input-order-immaterial, out~imports frame)=R. A2 (firstTok/moduleTok token split)=A-reference+I. A3 (isQualified == 'from')=I. A4 (composite keyLe grouping — the CHANGED behavior)=I, concrete, G-CONF-tested (NOT axiomatized — correct: the genuine change is modeled concretely). A5 (mergeSort keyLe == stable sorted)=A-reference+I. A6 (render/join + Perm frame)=R. A-reference correspondence independently re-checked in Python (seed 16662): firstTok==split()[0], moduleTok==split()[1] over 20000 fuzzed single-space import lines, and mergeSort-key stable-sort == sorted(key=composite) over 5000 lists — 0 mismatches. axiom_check.py imports only stdlib (random, sys). Prepatch bug reproduced (atk_1) and correctly fails verification; matches Solution_prepatch.lean intent.

Verdict SOUND: >=5 distinct attacks (7 total: partial-domain, boundary, control-flow-effect, wrong-token, reversed-grouping, ungrounded-oracle echo, prepatch) all run and verified; every verifying attack's faithful patch materialized and resolve-RUN to completion; none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16662 velvet bundle. FINDINGS:

1. SPEC INTEGRITY: region_hashes recomputed via markers.region_hashes(VelvetBackend) match meta.json exactly (spec_view=a92f59b8..., pure, impl, axioms all identical). Solution.lean verifies clean (lean_verify.sh exit 0). No consumed axioms (axioms=[]).

2. REAL CALLEE: base_commit 0eb3e9bd is an ancestor of the worktree HEAD; writer.py pre-patch = `sorted(imports, key=lambda i: i.split()[1])`. Gold fix commit b295b31171 changes it to `sorted(imports, key=lambda i: (i.split()[0]=="from", i.split()[1]))` — matches refinement.md hunk VERBATIM. Modeled function = MigrationWriter.as_string import-ordering step.

3. MODEL vs REAL — no over-strengthening / no drift on the reachable domain:
   - G-CONF: 100,007 fuzzed inputs, 0 disagreements (rerun locally, exit 0).
   - I independently #eval'd the ACTUAL spec term `List.mergeSort keyLe` in Lean (not the Python shadow) against Python gold `sorted(...)` on tie-heavy and stability-sensitive inputs (duplicate lines, interleaved qualified/unqualified same-module, all-equal-key payload-order preservation). EXACT match on every case: grouping direction (import<from via False<True), lcharLe module-token order, and STABILITY all agree. Lean List.mergeSort tie-break == CPython sorted stability here.

4. Only theoretical model/callee divergence: multi-whitespace lines (e.g. 'import  datetime' -> moduleTok='' but str.split()[1]='datetime'). UNREACHABLE: the writer always emits single-space-separated import lines ('import %s', 'from django.db import migrations, models'); Python module tokens cannot contain whitespace. This is exactly the A-reference boundary G-AX validates on real-shaped lines. Not a genuine diverging input.

Conclusion: the modeled function agrees with the real callee on every input the real code can produce; the postcondition (out = sortImports imports AND out ~ imports) pins gold behavior without being too strong. No diverging input exists. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes with zero hard failures (leakage.screen over the velvet spec_view). No diff markers, no gold-patch line reproduced (verbatim tuple key `(i.split()[0]=='from', i.split()[1])` absent), no patched file path/module (`writer.py`, `django.db.migrations.writer`) in view, no repo symbol echo. Only `.py` occurrence is `axiom_check.py`, an audit-script reference, not the patched file. Confirmed absent from spec view: writer, migration, as_string, django, sorted_imports. same_spec(Solution.lean, Solution_prepatch.lean) = True — the projected spec view (incl. the pure `keyLe`/`isQualified` model) is identical between buggy and fixed versions, so the spec view cannot disclose the direction/content of the edit; the pre-patch module-token-only key does not appear. The discriminating behavior the spec encodes (group whole-module `import` lines ahead of qualified `from ... import` lines, then order by module token) is ALREADY public verbatim in problem_statement ('Place all import module statements before from module import objects in each section') plus its before/after example — a spec legitimately encoding the publicly-described desired behavior is not leakage. Nothing in the spec view reveals gold-edit specifics beyond problem_statement (hints_text not consulted). meta G-LEAK status: pass; relaxed_leakage: not set.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
