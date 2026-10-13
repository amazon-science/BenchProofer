# P2 adversarial audit — sphinx-doc__sphinx-8621

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 12 distinct same-spec wrong impls were encoded and every one was REJECTED (exit 1, 'unsolved goals' on the `ensures_1: out = splitParts false [] text` obligation). The only same-spec impl that VERIFIED (atk_12_echo, the ungrounded-oracle echo `return splitParts false [] text`) had its faithful patch materialized and EXECUTED through the official harness: resolved=true, completed=true, attempts=1, flaky=false. Its faithful patch is byte-identical to the gold patch.diff, because the deep model splitParts is byte-exact with the full patched regex `(?<=.)(-|\+|\^|\s+)(?=.)` including the whitespace-run alternative. Notably this REPAIRS the break a prior pass recorded (G-EQ fail, verdict.md): under the OLD connector-only spec the echo's faithful patch was `(?<=.)(-|\+|\^)(?=.)`, which I re-ran here as a discrimination control and which consistently does NOT resolve (resolved=false, 3/3 attempts, P2P `tests/test_markup.py::test_inline[verify-:kbd:`M-x  M-s`` fails). The frozen spec now models whitespace deeply (isBlank/blankRun/gapFit/isFlank) and pins the resolving behaviour exactly.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,25 +178,28 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 1 (the PREPATCH bug): a connector splits wherever it occurs -- no
+    -- flank test on either side, and whitespace is never a separator. This is
+    -- the pre-image of the gold hunk r'(-|\+|\^|\s+)'.
+    -- Diverges from spec on "-": ["", "-", ""] vs ["-"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
-    let mut leftOk := false
     let mut rest := text
     while rest ≠ []
-      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest
+      invariant True
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
-        cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-      else
-        acc := acc ++ [cur, rest.take L]
-        cur := []
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
+      match rest with
+      | [] => rest := []
+      | c :: cs =>
+        if isSep c = true then
+          acc := acc ++ [cur, [c]]
+          cur := []
+          rest := cs
+        else
+          cur := cur ++ [c]
+          rest := cs
     return acc ++ [cur]
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,10 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 2 (partial domain; GOLD invariant kept byte-identical): connectors
+    -- exactly right, but a whitespace run is NEVER a separator -- exactly the
+    -- restriction refinement.md/mapping.md 2.1 still claim is the modeled domain.
+    -- Diverges from spec on "a a": ["a a"] vs ["a", " ", "a"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -187,8 +191,11 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
+      let s := (match rest with
+            | [] => 0
+            | c :: cs => if leftOk = true then (if isSep c then gapFit (c :: cs) 1 else 0) else 0)
+      let L := if s = 0 then 1 else s
+      if s = 0 then
         cur := cur ++ rest.take L
         leftOk := lastFlank (rest.take L)
         rest := rest.drop L
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,9 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 3 (boundary / one-sided flank): keeps the lookbehind (?<=.) but
+    -- drops the lookahead (?=.) -- no gapFit right-trim.
+    -- Diverges from spec on "a-": ["a", "-", ""] vs ["a-"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -187,8 +190,11 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
+      let s := (match rest with
+            | [] => 0
+            | c :: cs => if leftOk = true then (if isSep c then 1 else if isBlank c then blankRun (c :: cs) else 0) else 0)
+      let L := if s = 0 then 1 else s
+      if s = 0 then
         cur := cur ++ rest.take L
         leftOk := lastFlank (rest.take L)
         rest := rest.drop L
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,10 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 4 (control-flow effect): leftOk is set true unconditionally rather
+    -- than carrying lastFlank of the consumed step, so a line feed stops
+    -- blocking the separator that follows it.
+    -- Diverges from spec on "\n-a": ["\n", "-", "a"] vs ["\n-a"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -187,15 +191,16 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
+      let s := sepLen leftOk rest
+      let L := if s = 0 then 1 else s
+      if s = 0 then
         cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
+        leftOk := true
         rest := rest.drop L
       else
         acc := acc ++ [cur, rest.take L]
         cur := []
-        leftOk := lastFlank (rest.take L)
+        leftOk := true
         rest := rest.drop L
     return acc ++ [cur]
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,10 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 5 (maximal munch broken): a whitespace separator is a SINGLE blank
+    -- character, not the maximal run, so a two-space gap becomes two separators
+    -- with an empty key wedged between them.
+    -- Diverges from spec on "a  a": ["a"," ","", " ","a"] vs ["a","  ","a"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -187,8 +191,11 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
+      let s := (match rest with
+            | [] => 0
+            | c :: cs => if leftOk = true then (if isSep c || isBlank c then gapFit (c :: cs) 1 else 0) else 0)
+      let L := if s = 0 then 1 else s
+      if s = 0 then
         cur := cur ++ rest.take L
         leftOk := lastFlank (rest.take L)
         rest := rest.drop L
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,10 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 6 (isFlank ignores the line feed): a flank is merely "some
+    -- character is there", so a line feed both closes a key on its left and
+    -- opens one on its right.
+    -- Diverges from spec on "a-\n": ["a", "-", "\n"] vs ["a-\n"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -187,15 +191,18 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
+      let s := (match rest with
+            | [] => 0
+            | c :: cs => if leftOk = true then (if isSep c then min 1 cs.length else if isBlank c then min (blankRun (c :: cs)) cs.length else 0) else 0)
+      let L := if s = 0 then 1 else s
+      if s = 0 then
         cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
+        leftOk := true
         rest := rest.drop L
       else
         acc := acc ++ [cur, rest.take L]
         cur := []
-        leftOk := lastFlank (rest.take L)
+        leftOk := true
         rest := rest.drop L
     return acc ++ [cur]
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,9 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 7 (off-by-one emit; GOLD invariant kept): runs the exact spec scan
+    -- but forgets the final partial key whenever anything was split.
+    -- Diverges from spec on "a-a": ["a", "-"] vs ["a", "-", "a"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -197,7 +200,10 @@
         cur := []
         leftOk := lastFlank (rest.take L)
         rest := rest.drop L
-    return acc ++ [cur]
+    if acc ≠ [] then
+      return acc
+    else
+      return acc ++ [cur]
     -- impl-end
 
 prove_correct kbdSplit by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,26 +178,12 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut cur : List Char := []
-    let mut leftOk := false
-    let mut rest := text
-    while rest ≠ []
-      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
-        cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-      else
-        acc := acc ++ [cur, rest.take L]
-        cur := []
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-    return acc ++ [cur]
+    -- ATTACK 8 (straight-line, leftOk seeded true): calls the deep model with
+    -- leftOk = true, i.e. pretends a key character precedes the very first
+    -- character, so a LEADING connector splits. This is the exact lookbehind
+    -- (?<=.) content of the gold patch, removed.
+    -- Diverges on "-a": ["", "-", "a"] vs spec ["-a"]. No loop, no invariant.
+    return splitParts true [] text
     -- impl-end
 
 prove_correct kbdSplit by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,26 +178,9 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut cur : List Char := []
-    let mut leftOk := false
-    let mut rest := text
-    while rest ≠ []
-      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
-        cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-      else
-        acc := acc ++ [cur, rest.take L]
-        cur := []
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-    return acc ++ [cur]
+    -- ATTACK 9 (straight-line, never splits): returns the input as one key.
+    -- Diverges on "a-a": ["a-a"] vs spec ["a", "-", "a"]. No loop.
+    return [text]
     -- impl-end
 
 prove_correct kbdSplit by
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,26 +178,11 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut cur : List Char := []
-    let mut leftOk := false
-    let mut rest := text
-    while rest ≠ []
-      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
-        cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-      else
-        acc := acc ++ [cur, rest.take L]
-        cur := []
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-    return acc ++ [cur]
+    -- ATTACK 10 (straight-line, empty segments filtered): runs the exact spec
+    -- segmentation then drops every empty segment -- a "cosmetic cleanup" that
+    -- destroys re.split's positional key/separator interleaving.
+    -- Diverges on "" : [] vs spec [[]]. No loop.
+    return (splitParts false [] text).filter (fun p => p ≠ [])
     -- impl-end
 
 prove_correct kbdSplit by
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,26 +178,14 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut cur : List Char := []
-    let mut leftOk := false
-    let mut rest := text
-    while rest ≠ []
-      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
-        cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-      else
-        acc := acc ++ [cur, rest.take L]
-        cur := []
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-    return acc ++ [cur]
+    -- ATTACK 11 (straight-line, boundary off-by-one): segments all but the
+    -- final character and appends that character as its own trailing key.
+    -- Diverges on "a" : ["", "a"] vs spec ["a"]. No loop.
+    if text = [] then
+      return splitParts false [] text
+    else
+      return (splitParts false [] (text.take (text.length - 1)))
+             ++ [text.drop (text.length - 1)]
     -- impl-end
 
 prove_correct kbdSplit by
```

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,6 +178,11 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
+    -- ATTACK 13 (fine boundary / partial domain): the blank class is narrowed to
+    -- the ASCII space only, so a NO-BREAK SPACE U+00A0 (or a tab) between two
+    -- keys stops being a separator. This is the subtlest in-domain wrong impl:
+    -- it is correct on every connector AND on ordinary spaces.
+    -- Diverges from spec on "a\u00a0a": ["a\u00a0a"] vs ["a", "\u00a0", "a"].
     let mut acc : List (List Char) := []
     let mut cur : List Char := []
     let mut leftOk := false
@@ -187,8 +192,17 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
+      let s := (match rest with
+            | [] => 0
+            | c :: cs =>
+              if leftOk = true then
+                (if isSep c then gapFit (c :: cs) 1
+                 else if c == ' ' then
+                   gapFit (c :: cs) ((c :: cs).takeWhile (fun d => d == ' ')).length
+                 else 0)
+              else 0)
+      let L := if s = 0 then 1 else s
+      if s = 0 then
         cur := cur ++ rest.take L
         leftOk := lastFlank (rest.take L)
         rest := rest.drop L
```

Attack 13 — `atk_12_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,26 +178,12 @@
   ensures out = splitParts false [] text
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut cur : List Char := []
-    let mut leftOk := false
-    let mut rest := text
-    while rest ≠ []
-      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen leftOk rest
-      if sepLen leftOk rest = 0 then
-        cur := cur ++ rest.take L
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-      else
-        acc := acc ++ [cur, rest.take L]
-        cur := []
-        leftOk := lastFlank (rest.take L)
-        rest := rest.drop L
-    return acc ++ [cur]
+    -- PROBE 12 (ungrounded-oracle echo): returns the deep model directly. This
+    -- is the impl that broke the PRIOR pass (G-EQ fail: its faithful patch
+    -- r'(?<=.)(-|\+|\^)(?=.)' did not resolve, P2P ':kbd:`M-x  M-s`').
+    -- Under the REPAIRED whitespace-deep spec the echo is behaviourally equal
+    -- to the gold patch, so it must VERIFY and its faithful patch must RESOLVE.
+    return splitParts false [] text
     -- impl-end
 
 prove_correct kbdSplit by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** same_spec was confirmed True for ALL 13 attack files + pos_control + prepatch via `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(<gold>).read(), open(<atk>).read(), b.language))"` -> True for every file (only the impl region was edited; axioms/pure/pre/post byte-identical). Verify command for every file: `bash scripts/lean_verify.sh <f>.lean`, run from the repo root, launched as concurrent background jobs 4 at a time as instructed (schedule only; every attack fully verified).

**CONTROLS.** pos_control.lean = shipped impl -> EXIT 0 (VERIFIES; non-vacuity established). prepatch.lean (bundle's Solution_prepatch.lean) -> EXIT 1 (prepatch bug reproduced, G-DIFF). No log contains sorry/admit; no attack log contains a syntax/unknown-identifier error, so every rejection is a genuine proof-obligation failure, not a malformed file.

ATTACKS (path -> observed verify result; each was first differentially checked in Python against BOTH the spec's splitParts and the REAL patched regex, so each is genuinely wrong, not merely different):
- atk_1.lean  PREPATCH BUG re-encode: connector splits wherever it occurs, no flanks, whitespace never a separator. Witness "-" -> ["","-",""] vs spec ["-"]. EXIT 1 REJECTED.
- atk_2.lean  PARTIAL DOMAIN: connectors exact, whitespace run NEVER a separator -- i.e. literally the "modeled domain" refinement.md/mapping.md still claim. Witness "a a" -> ["a a"] vs spec ["a"," ","a"] (50944 diverging inputs of length<=5). EXIT 1 REJECTED.
- atk_3.lean  BOUNDARY one-sided flank: keeps lookbehind (?<=.), drops the lookahead (?=.) right-trim (no gapFit). Witness "a-" -> ["a","-",""] vs spec ["a-"]. EXIT 1 REJECTED.
- atk_4.lean  CONTROL-FLOW EFFECT: leftOk assigned `true` unconditionally instead of lastFlank of the consumed step. Witness "\n-a" -> ["\n","-","a"] vs spec ["\n-a"]. EXIT 1 REJECTED.
- atk_5.lean  MAXIMAL-MUNCH BROKEN: whitespace separator is one blank char, not the maximal run. Witness "a  a" -> ["a"," ",""," ","a"] vs spec ["a","  ","a"]. EXIT 1 REJECTED.
- atk_6.lean  isFlank ADMITS THE LINE FEED (deep-model helper semantics attacked directly). Witness "a-\n" -> ["a","-","\n"] vs spec ["a-\n"]. EXIT 1 REJECTED.
- atk_7.lean  OFF-BY-ONE EMIT: exact spec scan but drops the final partial key when anything split. Witness "a-a" -> ["a","-"] vs spec ["a","-","a"]. EXIT 1 REJECTED.
- atk_8.lean  STRAIGHT-LINE (loop-free) leftOk seeded true = the lookbehind removed. Witness "-a" -> ["","-","a"] vs spec ["-a"]. EXIT 1 REJECTED.
- atk_9.lean  STRAIGHT-LINE never splits: `return [text]`. Witness "a-a". EXIT 1 REJECTED.
- atk_10.lean STRAIGHT-LINE empty-segment filter (destroys re.split positional interleaving). Witness "" -> [] vs spec [[]]. EXIT 1 REJECTED.
- atk_11.lean STRAIGHT-LINE boundary off-by-one (last char always its own key). Witness "a" -> ["","a"] vs spec ["a"]. EXIT 1 REJECTED.
- atk_13.lean FINE BOUNDARY / partial domain: blank class narrowed to the ASCII space, so U+00A0 NO-BREAK SPACE and tab stop separating. Correct on every connector AND on ordinary spaces -- the subtlest rival. Witness "a a" -> ["a a"] vs spec ["a"," ","a"]. EXIT 1 REJECTED.
- atk_12_echo.lean UNGROUNDED-ORACLE ECHO `return splitParts false [] text` -> EXIT 0 VERIFIES. MANDATORY RESOLVE EXECUTED (see below).

MANDATORY RESOLVE RUN (the only verifying same-spec impl). Command: `python do_resolve.py echo_faithful patch_echo_faithful.diff` calling swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8621',...). OBSERVED: {"resolved": true, "completed": true, "attempts": 1, "flaky": false, "note": "resolved"}. The faithful patch is byte-identical to the bundle's gold patch.diff (`diff` reported no difference), which is the correct materialization: the echo returns exactly splitParts, and splitParts is byte-exact with the full patched pattern.

DISCRIMINATION CONTROL RESOLVE (run concurrently). `patch_connector_only.diff` = `(?<=.)(-|\+|\^)(?=.)`, the faithful patch of the OLD connector-only spec that a prior pass recorded as the G-EQ break. OBSERVED: {"resolved": false, "completed": true, "attempts": 3, "flaky": false, "note": "patch did not resolve in 3 attempts (consistent -- not flaky)"}. This proves (a) the harness lane is live and discriminating, not rubber-stamping, and (b) the prior BROKEN finding was real and has since been genuinely REPAIRED by modeling whitespace deeply.

DEEP-MODEL FIDELITY (the real G-EQ trust point, since there are no A legs). I independently re-derived splitParts in Python and diffed it against the REAL patched regex `re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')`: (1) exhaustive over alphabet {a,b,-,+,^,space,\n,\t,U+00A0,U+2009,\r,U+3000} for all lengths 0..4 = 22621 inputs, 0 mismatches; (2) 300000 random inputs (seed 8621, length 0..12, 17-char alphabet incl. \f \v U+2009) 0 mismatches; (3) isBlank compared against Python `\s` over ALL 0x110000 code points (surrogates skipped): 0 mismatches -- the 29-code-point class in the spec comment is exactly Python's `\s`. (4) Every real F2P/P2P:kbd: input is byte-exact: "-"->["-"], "Alt+^"->["Alt","+","^"], "space", "Control+X", "Shift-+", "+", and critically "M-x  M-s"->["M","-","x","  ","M","-","s"] matching the real patched split. The model is faithful on the FULL domain, whitespace runs included.

A-LEG AUDIT (my assigned focus). meta.json `axioms: []` and `deep_model_references: []`; `grep` finds no `axiom`, `sorry`, `admit`, `opaque`, `partial def`, or `@[extern]` in Solution.lean. The axioms region is a prose-only justification. So there are ZERO A-consumed and ZERO A-reference legs, and G-AX's skip stub (axiom_check.py, exit 0) is correct on its own terms: there is no outside callee to validate. The changed operation is NOT axiomatized -- it is modeled deeply from concrete Char/List operations over the input (directive 7 satisfied). Correspondingly there is nothing for an A-leg correspondence attack to falsify; I therefore redirected the effort into deep-model helper semantics (atk_4, atk_6, atk_13 attack isFlank/lastFlank/isBlank/gapFit directly), which is where the equivalent trust would live.

REFINEMENT.MD LEG AUDIT -- every leg is R or I, NO kind-3. Legs 1 (str <-> List Char, R), 2 (isSep <-> connector alternation, I), 3 (flank conjunction <-> lookbehind/lookahead, I), 4 (forward scan <-> re.split interleaving, I). The genuinely changed operation (flank-sensitivity of the split predicate) is modeled deeply, not hidden behind an axiom, so there is no inexpressible-changed-op leg. §D's verify=>resolved argument holds, and I confirmed its conclusion EMPIRICALLY rather than on the prose: the sole verifying same-spec impl resolves.

DOCUMENTATION DEFECT (non-blocking for G-EQ, but should be fixed; ADVISORY). refinement.md, mapping.md and meta.json are STALE relative to the frozen Solution.lean and now UNDERSTATE the spec. They were written for a superseded connector-only spec and still assert the opposite of the truth: refinement.md leg 2 says "The `\s+` whitespace alternative is outside the modeled domain"; §C says "isSep/splitParts model the no-whitespace keystroke domain"; §'Discriminating content' describes a guard `started = true AND cs != []` that NO LONGER EXISTS (it is now `sepLen leftOk rest = 0`); mapping.md §1 writes the signature as `splitParts (started cur)` (wrong arity/names, the frozen one is `splitParts (leftOk) (cur) (rest)`) and mapping.md §2.1 claims "G-CONF does not generate whitespace inputs" and that the maximal-munch/boundary-trim semantics are "deliberately omitted"; meta.json `modeled_domain` and `string_modeling` repeat the same stale claims (string_modeling omits isBlank/blankRun/gapFit/isFlank entirely).

ALL of these are FALSE of the frozen artifact, which models whitespace deeply and byte-exactly (my fuzz above), and the shipped conformance_check.py's own comment says it DOES emit whitespace. The staleness is in the SAFE direction -- the docs claim a NARROWER domain than the spec actually pins, so the fidelity argument is stronger than documented, not weaker -- which is why this is not a G-EQ break. But the docs no longer describe the artifact and the recorded G-EQ/G-PANEL `fail` verdicts in verdict.md/meta.json were computed against Solution.lean sha256 2727d4fa... whereas the file on disk is b535cb68..., so those gate records are stale too and should be re-run and the prose re-synced.

**WHY SOUND.** 12 distinct same-spec wrong impls spanning the required kinds -- prepatch bug (atk_1), partial-domain (atk_2, atk_13), boundary (atk_3, atk_11, atk_13), control-flow-effect (atk_4, atk_6), maximal-munch/aggregation (atk_5), off-by-one emit (atk_7), straight-line/loop-free (atk_8-11), and ungrounded-oracle echo (atk_12) -- were all encoded, same-spec-confirmed, and machine-verified; all 12 were rejected on the postcondition. The single verifying impl's faithful patch was materialized and RUN through the official harness and RESOLVED. Nothing exhibits verify AND NOT resolve, so verify=>correct is upheld for this bundle.

CAVEAT I MUST FLAG (bearing on how much weight the rejections carry). My first-round loop attacks used `invariant True`. I ran a dedicated control, ctl_weakinv.lean = the GOLD impl verbatim with only `invariant True`, and it FAILED (exit 1). So a weakened invariant is a CONFOUND: it alone causes rejection regardless of behaviour. I therefore REGENERATED atk_2..atk_7 and atk_13 with the gold invariant `splitParts false [] text = acc ++ splitParts leftOk cur rest` byte-identical and re-verified all of them -- they still fail (exit 1, same ensures obligation), and those are the results reported above. atk_8..atk_11 are loop-free so carry no invariant at all, and loop-free atk_12 verifies, proving the loop-free lane is not a blanket-reject. atk_1 retains `invariant True` because its impl uses no leftOk/cur state for which the gold invariant is well-formed; its evidence is therefore weaker than the others' and it should be read as the prepatch re-encode (corroborated independently by the bundle's own Solution_prepatch.lean, also exit 1) rather than as a load-bearing discrimination result.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 12 distinct same-spec wrong impls were encoded and every one was REJECTED (exit 1, 'unsolved goals' on the `ensures_1: out = splitParts false [] text` obligation). The only same-spec impl that VERIFIED (atk_12_echo, the ungrounded-oracle echo `return splitParts false [] text`) had its faithful patch materialized and EXECUTED through the official harness: resolved=true, completed=true, attempts=1, flaky=false. Its faithful patch is byte-identical to the gold patch.diff, because the deep model splitParts is byte-exact with the full patched regex `(?<=.)(-|\+|\^|\s+)(?=.)` including the whitespace-run alternative. Notably this REPAIRS the break a prior pass recorded (G-EQ fail, verdict.md): under the OLD connector-only spec the echo's faithful patch was `(?<=.)(-|\+|\^)(?=.)`, which I re-ran here as a discrimination control and which consistently does NOT resolve (resolved=false, 3/3 attempts, P2P `tests/test_markup.py::test_inline[verify-:kbd:`M-x  M-s`` fails). The frozen spec now models whitespace deeply (isBlank/blankRun/gapFit/isFlank) and pins the resolving behaviour exactly.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** same_spec was confirmed True for ALL 13 attack files + pos_control + prepatch via `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(<gold>).read(), open(<atk>).read(), b.language))"` -> True for every file (only the impl region was edited; axioms/pure/pre/post byte-identical). Verify command for every file: `bash scripts/lean_verify.sh <f>.lean`, run from the repo root, launched as concurrent background jobs 4 at a time as instructed (schedule only; every attack fully verified).

**CONTROLS.** pos_control.lean = shipped impl -> EXIT 0 (VERIFIES; non-vacuity established). prepatch.lean (bundle's Solution_prepatch.lean) -> EXIT 1 (prepatch bug reproduced, G-DIFF). No log contains sorry/admit; no attack log contains a syntax/unknown-identifier error, so every rejection is a genuine proof-obligation failure, not a malformed file.

ATTACKS (path -> observed verify result; each was first differentially checked in Python against BOTH the spec's splitParts and the REAL patched regex, so each is genuinely wrong, not merely different):
- atk_1.lean  PREPATCH BUG re-encode: connector splits wherever it occurs, no flanks, whitespace never a separator. Witness "-" -> ["","-",""] vs spec ["-"]. EXIT 1 REJECTED.
- atk_2.lean  PARTIAL DOMAIN: connectors exact, whitespace run NEVER a separator -- i.e. literally the "modeled domain" refinement.md/mapping.md still claim. Witness "a a" -> ["a a"] vs spec ["a"," ","a"] (50944 diverging inputs of length<=5). EXIT 1 REJECTED.
- atk_3.lean  BOUNDARY one-sided flank: keeps lookbehind (?<=.), drops the lookahead (?=.) right-trim (no gapFit). Witness "a-" -> ["a","-",""] vs spec ["a-"]. EXIT 1 REJECTED.
- atk_4.lean  CONTROL-FLOW EFFECT: leftOk assigned `true` unconditionally instead of lastFlank of the consumed step. Witness "\n-a" -> ["\n","-","a"] vs spec ["\n-a"]. EXIT 1 REJECTED.
- atk_5.lean  MAXIMAL-MUNCH BROKEN: whitespace separator is one blank char, not the maximal run. Witness "a  a" -> ["a"," ",""," ","a"] vs spec ["a","  ","a"]. EXIT 1 REJECTED.
- atk_6.lean  isFlank ADMITS THE LINE FEED (deep-model helper semantics attacked directly). Witness "a-\n" -> ["a","-","\n"] vs spec ["a-\n"]. EXIT 1 REJECTED.
- atk_7.lean  OFF-BY-ONE EMIT: exact spec scan but drops the final partial key when anything split. Witness "a-a" -> ["a","-"] vs spec ["a","-","a"]. EXIT 1 REJECTED.
- atk_8.lean  STRAIGHT-LINE (loop-free) leftOk seeded true = the lookbehind removed. Witness "-a" -> ["","-","a"] vs spec ["-a"]. EXIT 1 REJECTED.
- atk_9.lean  STRAIGHT-LINE never splits: `return [text]`. Witness "a-a". EXIT 1 REJECTED.
- atk_10.lean STRAIGHT-LINE empty-segment filter (destroys re.split positional interleaving). Witness "" -> [] vs spec [[]]. EXIT 1 REJECTED.
- atk_11.lean STRAIGHT-LINE boundary off-by-one (last char always its own key). Witness "a" -> ["","a"] vs spec ["a"]. EXIT 1 REJECTED.
- atk_13.lean FINE BOUNDARY / partial domain: blank class narrowed to the ASCII space, so U+00A0 NO-BREAK SPACE and tab stop separating. Correct on every connector AND on ordinary spaces -- the subtlest rival. Witness "a a" -> ["a a"] vs spec ["a"," ","a"]. EXIT 1 REJECTED.
- atk_12_echo.lean UNGROUNDED-ORACLE ECHO `return splitParts false [] text` -> EXIT 0 VERIFIES. MANDATORY RESOLVE EXECUTED (see below).

MANDATORY RESOLVE RUN (the only verifying same-spec impl). Command: `python do_resolve.py echo_faithful patch_echo_faithful.diff` calling swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8621',...). OBSERVED: {"resolved": true, "completed": true, "attempts": 1, "flaky": false, "note": "resolved"}. The faithful patch is byte-identical to the bundle's gold patch.diff (`diff` reported no difference), which is the correct materialization: the echo returns exactly splitParts, and splitParts is byte-exact with the full patched pattern.

DISCRIMINATION CONTROL RESOLVE (run concurrently). `patch_connector_only.diff` = `(?<=.)(-|\+|\^)(?=.)`, the faithful patch of the OLD connector-only spec that a prior pass recorded as the G-EQ break. OBSERVED: {"resolved": false, "completed": true, "attempts": 3, "flaky": false, "note": "patch did not resolve in 3 attempts (consistent -- not flaky)"}. This proves (a) the harness lane is live and discriminating, not rubber-stamping, and (b) the prior BROKEN finding was real and has since been genuinely REPAIRED by modeling whitespace deeply.

DEEP-MODEL FIDELITY (the real G-EQ trust point, since there are no A legs). I independently re-derived splitParts in Python and diffed it against the REAL patched regex `re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')`: (1) exhaustive over alphabet {a,b,-,+,^,space,\n,\t,U+00A0,U+2009,\r,U+3000} for all lengths 0..4 = 22621 inputs, 0 mismatches; (2) 300000 random inputs (seed 8621, length 0..12, 17-char alphabet incl. \f \v U+2009) 0 mismatches; (3) isBlank compared against Python `\s` over ALL 0x110000 code points (surrogates skipped): 0 mismatches -- the 29-code-point class in the spec comment is exactly Python's `\s`. (4) Every real F2P/P2P:kbd: input is byte-exact: "-"->["-"], "Alt+^"->["Alt","+","^"], "space", "Control+X", "Shift-+", "+", and critically "M-x  M-s"->["M","-","x","  ","M","-","s"] matching the real patched split. The model is faithful on the FULL domain, whitespace runs included.

A-LEG AUDIT (my assigned focus). meta.json `axioms: []` and `deep_model_references: []`; `grep` finds no `axiom`, `sorry`, `admit`, `opaque`, `partial def`, or `@[extern]` in Solution.lean. The axioms region is a prose-only justification. So there are ZERO A-consumed and ZERO A-reference legs, and G-AX's skip stub (axiom_check.py, exit 0) is correct on its own terms: there is no outside callee to validate. The changed operation is NOT axiomatized -- it is modeled deeply from concrete Char/List operations over the input (directive 7 satisfied). Correspondingly there is nothing for an A-leg correspondence attack to falsify; I therefore redirected the effort into deep-model helper semantics (atk_4, atk_6, atk_13 attack isFlank/lastFlank/isBlank/gapFit directly), which is where the equivalent trust would live.

REFINEMENT.MD LEG AUDIT -- every leg is R or I, NO kind-3. Legs 1 (str <-> List Char, R), 2 (isSep <-> connector alternation, I), 3 (flank conjunction <-> lookbehind/lookahead, I), 4 (forward scan <-> re.split interleaving, I). The genuinely changed operation (flank-sensitivity of the split predicate) is modeled deeply, not hidden behind an axiom, so there is no inexpressible-changed-op leg. §D's verify=>resolved argument holds, and I confirmed its conclusion EMPIRICALLY rather than on the prose: the sole verifying same-spec impl resolves.

DOCUMENTATION DEFECT (non-blocking for G-EQ, but should be fixed; ADVISORY). refinement.md, mapping.md and meta.json are STALE relative to the frozen Solution.lean and now UNDERSTATE the spec. They were written for a superseded connector-only spec and still assert the opposite of the truth: refinement.md leg 2 says "The `\s+` whitespace alternative is outside the modeled domain"; §C says "isSep/splitParts model the no-whitespace keystroke domain"; §'Discriminating content' describes a guard `started = true AND cs != []` that NO LONGER EXISTS (it is now `sepLen leftOk rest = 0`); mapping.md §1 writes the signature as `splitParts (started cur)` (wrong arity/names, the frozen one is `splitParts (leftOk) (cur) (rest)`) and mapping.md §2.1 claims "G-CONF does not generate whitespace inputs" and that the maximal-munch/boundary-trim semantics are "deliberately omitted"; meta.json `modeled_domain` and `string_modeling` repeat the same stale claims (string_modeling omits isBlank/blankRun/gapFit/isFlank entirely).

ALL of these are FALSE of the frozen artifact, which models whitespace deeply and byte-exactly (my fuzz above), and the shipped conformance_check.py's own comment says it DOES emit whitespace. The staleness is in the SAFE direction -- the docs claim a NARROWER domain than the spec actually pins, so the fidelity argument is stronger than documented, not weaker -- which is why this is not a G-EQ break. But the docs no longer describe the artifact and the recorded G-EQ/G-PANEL `fail` verdicts in verdict.md/meta.json were computed against Solution.lean sha256 2727d4fa... whereas the file on disk is b535cb68..., so those gate records are stale too and should be re-run and the prose re-synced.

**WHY SOUND.** 12 distinct same-spec wrong impls spanning the required kinds -- prepatch bug (atk_1), partial-domain (atk_2, atk_13), boundary (atk_3, atk_11, atk_13), control-flow-effect (atk_4, atk_6), maximal-munch/aggregation (atk_5), off-by-one emit (atk_7), straight-line/loop-free (atk_8-11), and ungrounded-oracle echo (atk_12) -- were all encoded, same-spec-confirmed, and machine-verified; all 12 were rejected on the postcondition. The single verifying impl's faithful patch was materialized and RUN through the official harness and RESOLVED. Nothing exhibits verify AND NOT resolve, so verify=>correct is upheld for this bundle.

CAVEAT I MUST FLAG (bearing on how much weight the rejections carry). My first-round loop attacks used `invariant True`. I ran a dedicated control, ctl_weakinv.lean = the GOLD impl verbatim with only `invariant True`, and it FAILED (exit 1). So a weakened invariant is a CONFOUND: it alone causes rejection regardless of behaviour. I therefore REGENERATED atk_2..atk_7 and atk_13 with the gold invariant `splitParts false [] text = acc ++ splitParts leftOk cur rest` byte-identical and re-verified all of them -- they still fail (exit 1, same ensures obligation), and those are the results reported above. atk_8..atk_11 are loop-free so carry no invariant at all, and loop-free atk_12 verifies, proving the loop-free lane is not a blanket-reject. atk_1 retains `invariant True` because its impl uses no leftOk/cur state for which the gold invariant is well-formed; its evidence is therefore weaker than the others' and it should be read as the prepatch re-encode (corroborated independently by the bundle's own Solution_prepatch.lean, also exit 1) rather than as a load-bearing discrimination result.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** GATE: faithfulness-break (is the spec too strong / does the modeled function disagree with the real callee?). Reference used = base_commit 21698c14461d27933864d73e6fba568a154e83b3 WITH patch.diff applied (pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')), per the anti-false-positive instruction. Verdict: no diverging input found; I could not break faithfulness.

**WHAT IS BOUND.** mapping.md §1 binds kbdSplit (ensures out = splitParts false [] text) to the `parts = self.pattern.split(node[-1].astext())` step of KeyboardTransform.run, sphinx/builders/html/transforms.py:40,42. meta.json: axioms=[], deep_model_references=[], conf_skip=false — so there is no axiom to over-constrain and the whole segmentation is modeled deeply. G-AX is a legitimate skip stub.

**SPEC-REGION INTEGRITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True. region_hashes reproduce meta.json's G-HYGIENE record exactly: pure=00fe9ab7b740108998397beb3e11c026eedac508bb89166955e24dd940c2d798, axioms=e295bde4b459..., spec_view=810671b6060a3120a58569e48dc97e98045a2641ec3f8dc7dab90e25a70ee2cc. sha256(Solution.lean)=b535cb6814fedbb51963dafd5b2da344e5708785a53b2e4d193d1bdb160a8619, matching the current G-GOLD/G-DIFF/G-HYGIENE sources. Solution.lean elaborates clean under scripts/lean_verify.sh (exit 0, only an unused-variable lint).

PRIMARY EVIDENCE — REAL LEAN vs REAL PATCHED CALLEE (not the author's shadow). I did NOT trust conformance_check.py's hand-written Python transliteration. I extracted the `pure` region VERBATIM via markers.region_text and #eval'd splitParts false [] on inputs generated Lean-side, then diffed against the regex object obtained by AST-extracting the `pattern = re.compile(...)` literal straight out of the PATCHED worktree file (so the oracle is the repo's own expression, not one I retyped):
  * Probe2: exhaustive over ['a','-','+','^',' ','\n'] to length 5 — 9331 inputs, 0 disagreements.
  * Probe3: exhaustive over ['a','+','\n','\t','\r',U+00A0] to length 5 plus the real repo test keystrokes — 9352 inputs, 0 disagreements.
Real-Lean results on the repo's own kbd strings all match the real oracle: '-'->['-']; 'Alt+^'->['Alt','+','^']; 'space'->['space']; 'Control+X'->['Control','+','X']; 'M-x  M-s'->['M','-','x','  ','M','-','s'].

**SECONDARY.** Real Lean output == my independent Python re-implementation on all 18683 probe rows (0 disagreements), which licensed a wider fuzz: ~554k inputs (multi-alphabet exhaustive to length 6 + 400k random over the full 29-code-point blank class) and a further ~350k adversarially concentrated on whitespace-run maximal-munch/backtracking, LF-vs-flank interaction, CRLF, and astral/NUL/BOM/ZWSP characters — 0 disagreements throughout.

WHY THE TWO SUBTLE MODELING CHOICES ARE CORRECT, NOT OVER-STRONG. (a) isFlank c:= c != '\n': I verified by exhaustive scan of all 0x110000 code points that the set Python's `.` fails to match is exactly {U+000A}, so isFlank IS the lookbehind/lookahead character class. (b) isBlank: I verified its 29 enumerated code points are exactly {c: re.match(r'\s', chr(c))}, so it IS Python str-mode \s. gapFit's one-character-at-a-time right-trim correctly reproduces the regex engine backtracking a greedy \s+ off a trailing lookahead failure — confirmed empirically on inputs like 'a \n b', 'a-\n-b', '\n \na', 'a'+U+`1680*3`+'b'.

DOC DRIFT OBSERVED (reported, NOT a faithfulness break). mapping.md §2.1 and refinement.md §C both declare a restricted "no-whitespace keystroke domain" in which separators are only '-','+','^', and meta.json.modeled_domain repeats it. That is stale prose: the frozen Solution.lean pure region actually models whitespace FULLY (isBlank, blankRun, maximal-munch runs, gapFit trimming) and my probes confirm it is byte-exact against the real patched split on whitespace inputs too. The drift makes the shipped spec STRONGER than its documentation claims, i.e. it errs toward the safe side for this gate; conformance_check.py's own docstring already describes the total-domain generator and contradicts the two md files. Recommend syncing mapping.md §2.1 / refinement.md §C / meta.json.modeled_domain to drop the withdrawn restriction — an editorial fix, no spec change.

**STALE GATE RECORD NOTED.** meta.json's G-EQ / G-PANEL-1 fail records cite sources Solution.lean=2727d4dafef5..., which is NOT the current artifact (b535cb68...). Their counterexample was an atk_2 impl passing 2/2 F2P but failing P2P tests/test_markup.py::test_inline[verify-:kbd:`M-x  M-s`] — precisely the whitespace-run gap the old restricted spec left open. The current Solution.lean closes that gap (it pins 'M-x  M-s' -> ['M','-','x','  ','M','-','s'] exactly, verified above in real Lean), so that record predates the repair and should be re-run rather than read as a live finding on this artifact.

**CONCLUSION.** Over every input I could construct — including the whitespace, LF-flank, and non-ASCII-space regions the documentation disclaims and where a too-strong spec would most likely show — splitParts agrees with the real patched KeyboardTransform.pattern.split. No diverging input exists to cite, so I cannot support UNFAITHFUL. FAITHFUL.

**GATE:** faithfulness-break (is the spec too strong / does the modeled function disagree with the real callee?). Reference used = base_commit 21698c14461d27933864d73e6fba568a154e83b3 WITH patch.diff applied (pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')), per the anti-false-positive instruction. Verdict: no diverging input found; I could not break faithfulness.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE/PROVENANCE: meta.json has NO `relaxed_leakage` key and there is no RELAXED_LEAKAGE.md in the bundle (ls + key dump), so this is an ordinary leakage judgement with no relaxation to re-derive. No bundle file addresses the reviewer: leakage.reviewer_directed() returned [] for Solution.lean, mapping.md, refinement.md, conformance_check.py, axiom_check.py. verdict.md:2392-2410 contains a PRIOR G-PANEL-3 narrative arguing 'not a leak'; I treated it as a record, not a disposition, and did not read it before forming my own scan -- every claim below is my own measurement.

### WHAT I MEASURED (not inherited):
1. Spec view reconstructed myself via markers.spec_view(Solution.lean, VelvetBackend) -> spec_view_8621.txt. Region hashes recomputed independently with markers.region_hashes match meta G-HYGIENE exactly (spec_view 810671b606..., pure 00fe9ab7b7..., axioms e295bde4b4..., impl 7f7520fb98...), so the view I judged IS the shipped view.
2. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; the only diff is inside impl-start/impl-end (index-scan + `isSep c` alone vs flank-aware scan) plus a prepatch-only impl comment -- inside the elided region, invisible to the consumer.
3. Gate soundness re-run, not trusted: `scripts/lean_verify.sh Solution.lean` -> exit 0, verifies (one unusedVariable warning at 130:5). `scripts/lean_verify.sh Solution_prepatch.lean` -> fails with unsolved goals that are EXACTLY the flank cases (goal `... acc ++ [cur, [text[i]!]] ++ splitParts true [] (drop (i+1) text)` under `isSep text[i]! = true` with no flank hypothesis). So G-DIFF/G-GOLD are sound: the spec really discriminates. Independent leakage.screen(src, velvet, patch.diff, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]), confirming the recorded G-LEAK pass rather than accepting it.
4. Gold-artifact grep over the spec view: ZERO hits for keyboardtransform, transforms.py, sphinx, builders, re.split, re.compile, default_priority, SphinxPostTransform, NodeMatcher, nodes.literal, astext, node.pop, parts.pop, '\\s+', '(?<=', '(?=', docutils, notranslate, and even 'kbd'. No gold-diff line quoted, no patched file/class/attribute named, no identifier echoing a patched repo symbol (isSep/isBlank/isFlank/gapFit/sepLen/splitParts/kbdSplit are all invented). No bug->fix narration vocabulary (no 'bug', 'fix', 'patched', 'previously', 'incorrect', 'wrong'). No test-patch literal echoed: extracted every 3-40 char quoted literal from test_patch and intersected with the spec view -> [].

WHY THE BEHAVIORAL CONTENT IS NOT A LEAK -- facet by facet, each re-derived:

(a) The discriminator itself (a connector splits only when a character flanks it on BOTH sides; a leading/trailing/standalone connector is an ordinary key char) is PUBLIC in problem_statement, not hints_text (hints_text is empty, len 0, so nothing could come from there). problem_statement 'Expected behavior' states verbatim: 'For single keystrokes that use -, + or ^, just a single kbd element should be created' and 'the algorithm should differentiate between -, + and ^ characters appearing in separator vs keystroke positions', with worked examples:kbd:`-`,:kbd:`+`,:kbd:`Shift-+` covering the standalone AND trailing cases; leading is the symmetric completion. I derived the rule from the problem statement alone before reading refinement.md's 'Discriminating content' section, so this is a problem_statement-only derivation -- which is the OPPOSITE of a leak: pinning it is mandated by spec_guide 6 ('state the abstract desired behavior') and a spec that omitted it would be the G-PANEL-1 defect.

(b) The connector set {-,+,^} and the whitespace-run separator class are PRE-EXISTING repo behavior, visible at base_commit (`pattern = re.compile(r'(-|\+|\^|\s+)')`), which the consumer has. Naming them describes the unchanged separator alphabet, not the edit. Extending the flank rule to whitespace runs is the symmetric generalization of the public rule over a repo-visible alternation, not a non-derivable design choice -- and it is required for spec strength: the recorded G-EQ/G-PANEL-1 finding is an attack that passed F2P 2/2 but broke P2P on:kbd:`M-x M-s`, i.e. under-pinning whitespace is the live weakness, so the blank modeling is load-bearing, not decorative.

(c) The one facet NOT derivable from problem_statement is isFlank excluding U+000A. I tested whether it is load-bearing rather than a gold fingerprint: I transliterated the whole pure region to Python and ran a variant with the newline clause removed (flank = any char). It DIVERGES from the real patched pattern on '\n-b' (gives ['\n','-','b'] vs gold ['\n-b']), 'a-\n' (['a','-','\n'] vs ['a-\n']) and 'a\n-\nb'. So dropping the clause makes the spec UNFAITHFUL (a G-PANEL-2 defect) -- it is a faithfulness obligation, stated as observable I/O behavior, not as the edit's mechanism. Decisively for THIS gate: it does not reconstruct the gold form. The spec view never mentions regex, lookaround, or `.`-vs-newline; Solution.lean's own impl satisfies it with a plain character scan and an explicit `c != '\n'` test and no regex at all, so the spec view is consistent with many non-gold implementations. Stating a true behavioral corner is not naming the edit.

(d) The axioms-region scope note ('the downstream rendering... is unchanged control flow') localizes the modeled step, but problem_statement already localizes the fault publicly ('it just treats all these characters as separators using a simple regexp'), so no information beyond public. 'plan 5.4' / 'directive 5' are internal authoring-doc pointers that name nothing in the repo or the diff.

FIDELITY CROSS-CHECK (my own, seed 8621, 200000 random inputs over alphabet a b - + ^ SPACE TAB LF NBSP EM-SPACE X M CR U+001C, len 0-8): my transliteration of the spec's pure region agreed with the REAL patched `re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split` on 200000/200000 inputs, 0 disagreements, including the newline and non-ASCII-whitespace corners; the pre-patch pattern differed from the spec on 161787 of them. Targeted checks all OK: '-'->['-'], '+'->['+'], 'Shift-+'->['Shift','-','+'], 'Alt+^'->['Alt','+','^'], 'M-x M-s', 'space', 'Control+X', ''->[''], 'a-b-'->['a','-','b-']. So the spec view's prose describes exactly the patched behavior and nothing more -- it is a faithful behavioral contract, and every clause in it is either public in problem_statement, visible in the base_commit repo, or a faithfulness-mandated corner that does not reveal the diff's form.

OBSERVATION (not my gate, recorded for routing): G-EQ, G-PANEL, G-PANEL-1, G-PANEL-2 are recorded fail at a STALE Solution.lean hash 2727d4fafef5..., while G-VERIFY/G-DIFF/G-GOLD/G-HYGIENE/G-LEAK/G-MUT/G-PBT/G-INTEGRITY are pass at the current b535cb6814fe.... The spec was evidently repaired after those fails (the flank-aware forward scan). Per lane practice those retained fail labels should be re-run against the current hash before being treated as findings; I did not re-judge them, and they do not bear on leakage either way.

**VERDICT:** NO-LEAKAGE. The spec view leaks nothing about the gold edit beyond the public problem_statement (which is the sole permitted source here; hints_text is empty).

**SCOPE/PROVENANCE:** meta.json has NO `relaxed_leakage` key and there is no RELAXED_LEAKAGE.md in the bundle (ls + key dump), so this is an ordinary leakage judgement with no relaxation to re-derive. No bundle file addresses the reviewer: leakage.reviewer_directed() returned [] for Solution.lean, mapping.md, refinement.md, conformance_check.py, axiom_check.py. verdict.md:2392-2410 contains a PRIOR G-PANEL-3 narrative arguing 'not a leak'; I treated it as a record, not a disposition, and did not read it before forming my own scan -- every claim below is my own measurement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
