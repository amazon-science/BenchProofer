# P2 adversarial audit — django__django-15503

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The only same-spec impl that verifies (atk_7) is the ungrounded-oracle echo of the postcondition RHS, and its faithful refined patch (= gold patch verbatim) RESOLVES under run_resolve (resolved=True).
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ compilePrefix keys.dropLast ++ keySeg keys.getLast!
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ compilePrefix keys
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ compilePrefix keys ++ memberSeg keys.getLast!
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ memberSeg keys.getLast! ++ compilePrefix keys.dropLast
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return compilePrefix keys.dropLast ++ memberSeg keys.getLast!
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,10 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    if isNumericKey keys.getLast! then
+      return lhsPath ++ compilePrefix keys.dropLast ++ arraySeg keys.getLast!
+    else
+      return lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ compilePrefix keys.dropLast ++ memberSeg (canonicalDigits keys.getLast!)
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
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
 -- axioms-end
@@ -68,11 +68,7 @@
   ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
   do
     -- impl-start
-    let prefixKeys := keys.dropLast
-    let finalKey   := keys.getLast!
-    let prefixPath := compilePrefix prefixKeys
-    let finalSeg   := memberSeg finalKey
-    return lhsPath ++ prefixPath ++ finalSeg
+    return lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.head!
     -- impl-end
 
 prove_correct compileRhsPath by loom_solve
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A key string is "simple" when it is a non-empty run of ASCII letters and
   digits. The modeled path compiler is faithful on exactly this domain (the
   keys the lookups carry); the bijection and its bounds are pinned in
   mapping.md. -/
def isSimpleChar (c : Char) : Bool := c.isDigit || c.isUpper || c.isLower
def isSimpleKey (k : List Char) : Bool := !k.isEmpty && k.all isSimpleChar

/- A key denotes an array position iff it is a non-empty run of digits. -/
def isNumericKey (k : List Char) : Bool := !k.isEmpty && k.all Char.isDigit

/- The integer normal form of an all-digit key (decimal, no leading zeros;
   the empty residue denotes zero). -/
def stripZeros : List Char → List Char
  | []      => []
  | c :: cs => if c = '0' then stripZeros cs else c :: cs

def canonicalDigits (k : List Char) : List Char :=
  match stripZeros k with
  | [] => ['0']
  | r  => r

/- The two ways a path segment can address a key:
   • by array position `[n]` (numeric keys, integer-normalised), or
   • by object member `."k"` (the key wrapped as a quoted JSON string). -/
def arraySeg  (k : List Char) : List Char := '[' :: canonicalDigits k ++ [']']
def memberSeg (k : List Char) : List Char := '.' :: '"' :: k ++ ['"']

/- The general path-compilation rule for an interior key: numeric keys address
   an array element, everything else an object member. -/
def keySeg (k : List Char) : List Char :=
  if isNumericKey k then arraySeg k else memberSeg k

/- The compiled path for a sequence of interior keys (rootless): each key
   contributes its general segment, front-recursively. -/
def compilePrefix : List (List Char) → List Char
  | []      => []
  | k :: ks => keySeg k ++ compilePrefix ks
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the path string that locates a queried key within a JSON document,
   given the already-compiled path `lhsPath` to the enclosing document and the
   non-empty list `keys` reaching the queried key. The keys leading up to the
   queried key follow the document's general path-compilation rule; the queried
   key itself is located by name — as an object member — regardless of its
   spelling. -/
method compileRhsPath (lhsPath : List Char) (keys : List (List Char))
    return (out : List Char)
  require keys ≠ []
  require keys.all isSimpleKey
  ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
  do
    -- impl-start
    let prefixKeys := keys.dropLast
    let finalKey   := keys.getLast!
    let prefixPath := compilePrefix prefixKeys
    let finalSeg   := memberSeg finalKey
    return lhsPath ++ prefixPath ++ finalSeg
    -- impl-end

prove_correct compileRhsPath by loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True confirmed for all 9 attacks + pos_control + prepatch via swebench_unified.markers.same_spec (velvet). Verify cmd: `bash scripts/lean_verify.sh <file>` run concurrently (<=4). RESULTS: pos_control EXIT=0 (verifies, positive control OK). prepatch EXIT=1 (bug reproduced: return lhsPath ++ compilePrefix keys — final key compiled by general array-aware rule; unsolved goals at 79:29).

Attacks (all same-spec): atk_1 final via keySeg (numeric final -> array index) REJECT(unsolved goals 74:29); atk_2 whole-list prepatch REJECT; atk_3 duplicate final segment REJECT; atk_4 swapped assembly order REJECT; atk_5 drops lhsPath prefix REJECT; atk_6 control-flow-effect: numeric final routed to arraySeg REJECT(77:29); atk_7 ungrounded-oracle echo (= postcondition RHS) VERIFY EXIT=0; atk_8 boundary: memberSeg(canonicalDigits final) — wrong on leading-zero numeric final e.g. '007' REJECT; atk_9 uses keys.head! instead of getLast! REJECT. All 8 behaviorally-wrong impls rejected with genuine 'unsolved goals' (postcondition violations), not syntax errors. Only the echo verifies.

PROTOCOL STEP 2: atk_7's faithful refined patch (per refinement.md legs A5 compilePrefix->compile_json_path, A6 memberSeg->compile_json_path_final_key=json.dumps, A7 ++ -> +) is the gold patch verbatim. Ran through official harness: SBU_BENCHMARK=swe_bench_verified python -c 'run_resolve("django__django-15503", patch, run_id="sbu-resolve-audit-eq-c5kr06am-atk_7", timeout=1800)' => RESOLVED: True, DETAIL: resolved. So the one verifying impl's materialized patch DOES resolve — verify=>correct holds, no break.

REFINEMENT.MD AUDIT: legs A1/A2=R, A3/A4/A7=I, A5/A6=A-reference+I; axioms region empty so NO A-consumed; no kind-3 (inexpressible-changed-op) legs — the discriminating changed op (final key by name, A6) is modeled deeply in the pure region (memberSeg) and G-AX-validated == json.dumps, not hidden behind an axiom about the function under change. A-leg correspondence spot-checked in /tmp: memberSeg k == '.%s' % json.dumps(k) exact on the simple ASCII-alnum domain (incl. '007','000','1a', 10^21) and canonicalDigits == str(int()) on numerics. The tight postcondition equation uniquely determines the output, so any behavioral deviation is rejected (attacks atk_1/atk_6/atk_8 directly assault the A6 discriminating clause and all fail).

VERDICT SOUND: >=5 distinct attacks run (9 total, spanning partial-domain/boundary/control-flow-effect/ungrounded-echo classes), the sole verifying impl's faithful patch resolves under the official harness, positive control verifies, prepatch bug reproduced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The only same-spec impl that verifies (atk_7) is the ungrounded-oracle echo of the postcondition RHS, and its faithful refined patch (= gold patch verbatim) RESOLVES under run_resolve (resolved=True).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A key string is "simple" when it is a non-empty run of ASCII letters and
   digits. The modeled path compiler is faithful on exactly this domain (the
   keys the lookups carry); the bijection and its bounds are pinned in
   mapping.md. -/
def isSimpleChar (c : Char) : Bool := c.isDigit || c.isUpper || c.isLower
def isSimpleKey (k : List Char) : Bool := !k.isEmpty && k.all isSimpleChar

/- A key denotes an array position iff it is a non-empty run of digits. -/
def isNumericKey (k : List Char) : Bool := !k.isEmpty && k.all Char.isDigit

/- The integer normal form of an all-digit key (decimal, no leading zeros;
   the empty residue denotes zero). -/
def stripZeros : List Char → List Char
  | []      => []
  | c :: cs => if c = '0' then stripZeros cs else c :: cs

def canonicalDigits (k : List Char) : List Char :=
  match stripZeros k with
  | [] => ['0']
  | r  => r

/- The two ways a path segment can address a key:
   • by array position `[n]` (numeric keys, integer-normalised), or
   • by object member `."k"` (the key wrapped as a quoted JSON string). -/
def arraySeg  (k : List Char) : List Char := '[' :: canonicalDigits k ++ [']']
def memberSeg (k : List Char) : List Char := '.' :: '"' :: k ++ ['"']

/- The general path-compilation rule for an interior key: numeric keys address
   an array element, everything else an object member. -/
def keySeg (k : List Char) : List Char :=
  if isNumericKey k then arraySeg k else memberSeg k

/- The compiled path for a sequence of interior keys (rootless): each key
   contributes its general segment, front-recursively. -/
def compilePrefix : List (List Char) → List Char
  | []      => []
  | k :: ks => keySeg k ++ compilePrefix ks
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the path string that locates a queried key within a JSON document,
   given the already-compiled path `lhsPath` to the enclosing document and the
   non-empty list `keys` reaching the queried key. The keys leading up to the
   queried key follow the document's general path-compilation rule; the queried
   key itself is located by name — as an object member — regardless of its
   spelling. -/
method compileRhsPath (lhsPath : List Char) (keys : List (List Char))
    return (out : List Char)
  require keys ≠ []
  require keys.all isSimpleKey
  ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
  do
    -- impl-start
    let prefixKeys := keys.dropLast
    let finalKey   := keys.getLast!
    let prefixPath := compilePrefix prefixKeys
    let finalSeg   := memberSeg finalKey
    return lhsPath ++ prefixPath ++ finalSeg
    -- impl-end

prove_correct compileRhsPath by loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True confirmed for all 9 attacks + pos_control + prepatch via swebench_unified.markers.same_spec (velvet). Verify cmd: `bash scripts/lean_verify.sh <file>` run concurrently (<=4). RESULTS: pos_control EXIT=0 (verifies, positive control OK). prepatch EXIT=1 (bug reproduced: return lhsPath ++ compilePrefix keys — final key compiled by general array-aware rule; unsolved goals at 79:29).

Attacks (all same-spec): atk_1 final via keySeg (numeric final -> array index) REJECT(unsolved goals 74:29); atk_2 whole-list prepatch REJECT; atk_3 duplicate final segment REJECT; atk_4 swapped assembly order REJECT; atk_5 drops lhsPath prefix REJECT; atk_6 control-flow-effect: numeric final routed to arraySeg REJECT(77:29); atk_7 ungrounded-oracle echo (= postcondition RHS) VERIFY EXIT=0; atk_8 boundary: memberSeg(canonicalDigits final) — wrong on leading-zero numeric final e.g. '007' REJECT; atk_9 uses keys.head! instead of getLast! REJECT. All 8 behaviorally-wrong impls rejected with genuine 'unsolved goals' (postcondition violations), not syntax errors. Only the echo verifies.

PROTOCOL STEP 2: atk_7's faithful refined patch (per refinement.md legs A5 compilePrefix->compile_json_path, A6 memberSeg->compile_json_path_final_key=json.dumps, A7 ++ -> +) is the gold patch verbatim. Ran through official harness: SBU_BENCHMARK=swe_bench_verified python -c 'run_resolve("django__django-15503", patch, run_id="sbu-resolve-audit-eq-c5kr06am-atk_7", timeout=1800)' => RESOLVED: True, DETAIL: resolved. So the one verifying impl's materialized patch DOES resolve — verify=>correct holds, no break.

REFINEMENT.MD AUDIT: legs A1/A2=R, A3/A4/A7=I, A5/A6=A-reference+I; axioms region empty so NO A-consumed; no kind-3 (inexpressible-changed-op) legs — the discriminating changed op (final key by name, A6) is modeled deeply in the pure region (memberSeg) and G-AX-validated == json.dumps, not hidden behind an axiom about the function under change. A-leg correspondence spot-checked in /tmp: memberSeg k == '.%s' % json.dumps(k) exact on the simple ASCII-alnum domain (incl. '007','000','1a', 10^21) and canonicalDigits == str(int()) on numerics. The tight postcondition equation uniquely determines the output, so any behavioral deviation is rejected (attacks atk_1/atk_6/atk_8 directly assault the A6 discriminating clause and all fail).

VERDICT SOUND: >=5 distinct attacks run (9 total, spanning partial-domain/boundary/control-flow-effect/ungrounded-echo classes), the sole verifying impl's faithful patch resolves under the official harness, positive control verifies, prepatch bug reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed to find drift; spec is FAITHFUL (not too strong). Evidence: (1) spec region byte-identical to Solution_prepatch via swebench_unified.markers.same_spec with VelvetBackend.language tables = True. (2) Solution.lean elaborates under lean_verify.sh (exit 0). (3) Postcondition out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast! exactly mirrors gold patch (patched json.py:174-183): interior keys via compile_json_path (array-aware keySeg), final key via compile_json_path_final_key = '.%s'%json.dumps(k) (memberSeg, by-name). G-AX (axiom_check.py) run against the real patched tree passes: compilePrefix==compile_json_path and memberSeg=='.%s'%json.dumps over 24 boundary keys + 8 lists + 20000 fuzz. (5) G-CONF (conformance_check.py) run in the patched tree: R/I shadow agrees with real patched callees over 100013 inputs, 0 disagreements. (6) Independent adversarial differential (400 crafted edge inputs — leading-zero numerics 007/000, 27-digit integers, mixed 1a/a1, digit-only final keys which are the discriminating clause, empty/non-empty lhs, deep multi-key lists) vs the REAL compile_json_path + HasKeyLookup.compile_json_path_final_key: 0 divergences. The precondition `require keys.all isSimpleKey` (non-empty ASCII alphanumeric) correctly bounds the domain to exactly where json.dumps performs no escaping, so the modeled function never overclaims on inputs it does not restrict. No diverging input exists within the guarded domain; the spec does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures) and same_spec(Solution, Solution_prepatch) is True (spec region byte-identical). Semantic review of the velvet spec view: the discriminating content is the postcondition `out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!` and the docstring clause 'the queried key itself is located by name — as an object member — regardless of its spelling.' This is a faithful behavioral encoding of the PUBLIC problem_statement, which explicitly states has_key='1111' (a numeric-string key) must be found just like 'foo' on SQLite/MySQL/Oracle (assertEqual c2, 1). It does not reveal the gold edit beyond the public task: (1) no patched repo symbols appear (HasKeyOrArrayIndex, compile_json_path_final_key, as_sqlite, as_oracle, as_sql — none present); (2) no patched file path django/db/models/fields/json.py or module dotted path; (3) no diff markers, no reproduced gold-patch line (>=8 chars); (4) no bug/fix narration; comments are abstract behavioral prose. The gold mechanism (new HasKeyOrArrayIndex subclass overriding compile_json_path_final_key and rewiring the isnull/as_oracle/as_sqlite call sites) is entirely absent from the spec view; a solver cannot reconstruct it from this view beyond what the problem statement already makes public. The interior-key vs final-key split is an inherent consequence of modeling JSON-path compilation, not a disclosure of the patch's implementation strategy.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
