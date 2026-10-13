# P2 adversarial audit — django__django-11276

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec WRONG impl verifies, so there is no verifying-but-not-resolving patch. The spec's postcondition `out = escapedSeq text` is a COMPLETE functional specification over a DEEP pure model (escapedSeq/entity are Lean defs, not axioms) under total-correctness semantics, so any verifying impl must terminate and return exactly the gold per-code-point substitution (incl. the discriminating change ' -> &#x27;, not the legacy &#39;). All 7 distinct wrong impls fail `prove_correct`; the only verifying impls are behaviorally correct and their faithful patch IS the gold patch, which RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,14 @@
       decreasing i
     do
       let c := text[i - 1]!
-      result := entity c ++ result
+      let e : List Char :=
+        if c = '&' then "&amp;".toList
+        else if c = '<' then "&lt;".toList
+        else if c = '>' then "&gt;".toList
+        else if c = '"' then "&quot;".toList
+        else if c = '\'' then "&#39;".toList
+        else [c]
+      result := e ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := text.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = escapedSeq (text.drop i)
       done_with i = 0
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,18 +74,7 @@
   ensures entityDecode (entity '\'') = ['\'']
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = escapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := entity c ++ result
-      i := i - 1
-    return result
+    return text
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -104,5 +93,3 @@
 
 prove_correct escapeCodepoints by
   loom_solve
-  rw [escapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,18 +74,7 @@
   ensures entityDecode (entity '\'') = ['\'']
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = escapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := entity c ++ result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -104,5 +93,3 @@
 
 prove_correct escapeCodepoints by
   loom_solve
-  rw [escapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,12 @@
       decreasing i
     do
       let c := text[i - 1]!
-      result := entity c ++ result
+      let e : List Char :=
+        if c = '&' then "&amp;".toList
+        else if c = '<' then "&lt;".toList
+        else if c = '>' then "&gt;".toList
+        else [c]
+      result := e ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,15 +76,11 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = escapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
+    while true
+      invariant True
+      done_with False
     do
-      let c := text[i - 1]!
-      result := entity c ++ result
-      i := i - 1
+      result := result
     return result
     -- impl-end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,18 +74,7 @@
   ensures entityDecode (entity '\'') = ['\'']
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = escapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := entity c ++ result
-      i := i - 1
-    return result
+    return entityDecode (escapedSeq text)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -104,5 +93,3 @@
 
 prove_correct escapeCodepoints by
   loom_solve
-  rw [escapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A standard-library HTML entity decoder: the left inverse of the escaper on
   the five entity tokens this module relies on. Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom entityDecode : List Char → List Char
axiom entityDecode_amp  : entityDecode "&amp;".toList  = ['&']
axiom entityDecode_lt   : entityDecode "&lt;".toList   = ['<']
axiom entityDecode_gt   : entityDecode "&gt;".toList   = ['>']
axiom entityDecode_quot : entityDecode "&quot;".toList = ['"']
axiom entityDecode_apos : entityDecode "&#x27;".toList = ['\'']
-- axioms-end

-- pure-start
/- The escape of a single code point: the five significant chars expand, every
   other char passes through. Ampersand handled by the caller's `escape` being
   the per-char substitution (ampersand-first ⇒ emitted '&' never re-escaped),
   so a single entity map is faithful (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/- The escape of a whole sequence: concatenate the per-code-point entity
   sequences. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

@[grind] lemma escapedSeq_nil : escapedSeq [] = [] := rfl
@[grind] lemma escapedSeq_cons (c : Char) (cs : List Char) :
    escapedSeq (c :: cs) = entity c ++ escapedSeq cs := rfl

/- Escape/decode round-trips on the five significant code points. `entity c`
   for a concrete significant char reduces definitionally to the entity token
   (the `if c = …` guards decide), so each round-trip is the matching
   `entityDecode_*` axiom after a `show`. Marked `@[grind]` so `loom_solve`
   discharges the postconditions automatically. -/
@[grind] lemma roundtrip_amp  : entityDecode (entity '&')  = ['&']  := by
  show entityDecode "&amp;".toList = _;  exact entityDecode_amp
@[grind] lemma roundtrip_lt   : entityDecode (entity '<')  = ['<']  := by
  show entityDecode "&lt;".toList = _;   exact entityDecode_lt
@[grind] lemma roundtrip_gt   : entityDecode (entity '>')  = ['>']  := by
  show entityDecode "&gt;".toList = _;   exact entityDecode_gt
@[grind] lemma roundtrip_quot : entityDecode (entity '"')  = ['"']  := by
  show entityDecode "&quot;".toList = _; exact entityDecode_quot
@[grind] lemma roundtrip_apos : entityDecode (entity '\'') = ['\''] := by
  show entityDecode "&#x27;".toList = _; exact entityDecode_apos
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method escapeCodepoints (text : List Char) return (out : List Char)
  ensures out = escapedSeq text
  ensures entityDecode (entity '&')  = ['&']
  ensures entityDecode (entity '<')  = ['<']
  ensures entityDecode (entity '>')  = ['>']
  ensures entityDecode (entity '"')  = ['"']
  ensures entityDecode (entity '\'') = ['\'']
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = escapedSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := entity c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `entity`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    escapedSeq (text.drop (i - 1)) = entity text[i - 1]! ++ escapedSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeCodepoints by
  loom_solve
  rw [escapedSeq_drop_step text i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 venv swebench-lean. same_spec confirmed True for every attack + both positive controls (swebench_unified.markers.same_spec, velvet). patch.diff == frozen dataset gold verbatim.

### ATTACKS (all same_spec=True; verify command: `bash scripts/lean_verify.sh <path>`)
1) atk_1.lean  PREPATCH BUG (partial/wrong-value): apostrophe -> legacy decimal "&#39;" via translate(_html_escapes). EXIT=1 (FAIL). Residual goal: (...if c='\'' then ['&','#','3','9',';']...) = entity c  -> unprovable. This is the prepatch counterexample (prepatch_reproduced=true; mirrors bundle's Solution_prepatch.lean).
2) atk_2.lean  BOUNDARY off-by-one: loop guard `while i > 1` drops first char. EXIT=1 (FAIL). done_with leaves goal i=0 under ¬i>1 -> unprovable.
3) atk_3.lean  CONTROL-FLOW/identity: `return text` (clean loom_solve proof). EXIT=1 (FAIL). Goal: text = escapedSeq text.
4) atk_4.lean  CONTROL-FLOW/empty: `return []` (clean loom_solve proof). EXIT=1 (FAIL). Goal: [] = escapedSeq text.
5) atk_5.lean  PARTIAL-DOMAIN: escapes only & < > ; leaves " and ' unescaped. EXIT=1 (FAIL). Residual entity-mismatch goal.
6) atk_6.lean  CONTROL-FLOW-EFFECT/divergence: `while true` trivial body. EXIT=1 (FAIL). Total semantics rejects: "Decreasing annotations are required in total correctness semantics" + WPGen sorry. (This is exactly the class refinement.md D says total semantics excludes; confirmed.)
8) atk_8.lean  UNGROUNDED-ORACLE ECHO: `return entityDecode (escapedSeq text)` (entityDecode is an uninterpreted axiom pinned only on 5 tokens). EXIT=1 (FAIL). Goal: entityDecode (escapedSeq text) = escapedSeq text -> unprovable (also noncomputable). Confirms the axiom cannot be abused to launder the output.

### POSITIVE CONTROLS (must verify)
- positive_control.lean = frozen Solution.lean impl -> `bash scripts/lean_verify.sh .../positive_control.lean` EXIT=0 (verifies).
- atk_7b_correct_echo.lean = `return escapedSeq text` with fitting `loom_solve` proof -> EXIT=0 (verifies). A CORRECT impl (not a wrong-impl attack); its faithful patch = gold.
(Note: an early atk_7 reused the loop-specific frozen proof body verbatim with a non-loop impl and failed on the stale `rw`; repurposed to atk_7b with a fitting proof. Not counted as a wrong-impl attack.)

### Patches / resolve
ZERO verifying WRONG impls, so no faithful wrong-patch exists to run (patches={}). To close the verify=>resolve loop I materialized the faithful patch of the CORRECT verifying impl (= gold patch, saved gold_patch.diff) and RAN it through the official harness: `run_resolve('django__django-11276', gold, timeout=2400, retries=1)` -> RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1. (First two attempts returned COMPLETED=False 'no report' because the instance image was uncached; fixed by pulling mirror.gcr.io/swebench/sweb.eval.x86_64.django_1776_django-11276 and retagging to swebench/... per host retag convention, then the run completed and resolved.)

### A-LEG / refinement.md AUDIT (focus of this pass)
Every leg is R / A-reference / A-consumed / I; NO kind-3. The one genuinely-changed op (the escaper's char substitution) is modeled DEEPLY as escapedSeq/entity in the pure region (a Lean def, NOT an axiom about the function-under-change) -> A-reference (A3), validated == real html.escape. The only CONSUMED axioms (entityDecode_*) cover the UNCHANGED stdlib callee html.unescape (site B, A-consumed).
- Ran bundle axiom_check.py (G-AX): EXIT=0, 'escaped_seq deep model (== html.escape) + entity_decode axiom sound on 23 boundary + 20000 fuzz inputs and 6 decode tokens'.
- Independent CPython cross-check: html.escape('&','<','>','"',"'") == &amp;,&lt;,&gt;,&quot;,&#x27; (apostrophe -> &#x27; discriminator holds); html.unescape inverts all 5 emitted tokens. The A-reference and A-consumed correspondences to the real callees hold.
- model<->patch correspondence: escapeCodepoints<->escape() html.py:46; escapedSeq<->html.escape; entityDecode<->html.unescape (urlize sites). Consistent with mapping.md.

CONCLUSION: >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow, wrong-value/prepatch, divergence, ungrounded-oracle) all FAIL to verify against the complete functional postcondition; positive controls verify; gold (the faithful patch of the correct verifying impl) RESOLVES; A-legs sound. No verify=>NOT-resolve witness exists. verify=>correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec WRONG impl verifies, so there is no verifying-but-not-resolving patch. The spec's postcondition `out = escapedSeq text` is a COMPLETE functional specification over a DEEP pure model (escapedSeq/entity are Lean defs, not axioms) under total-correctness semantics, so any verifying impl must terminate and return exactly the gold per-code-point substitution (incl. the discriminating change ' -> &#x27;, not the legacy &#39;). All 7 distinct wrong impls fail `prove_correct`; the only verifying impls are behaviorally correct and their faithful patch IS the gold patch, which RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A standard-library HTML entity decoder: the left inverse of the escaper on
   the five entity tokens this module relies on. Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom entityDecode : List Char → List Char
axiom entityDecode_amp  : entityDecode "&amp;".toList  = ['&']
axiom entityDecode_lt   : entityDecode "&lt;".toList   = ['<']
axiom entityDecode_gt   : entityDecode "&gt;".toList   = ['>']
axiom entityDecode_quot : entityDecode "&quot;".toList = ['"']
axiom entityDecode_apos : entityDecode "&#x27;".toList = ['\'']
-- axioms-end

-- pure-start
/- The escape of a single code point: the five significant chars expand, every
   other char passes through. Ampersand handled by the caller's `escape` being
   the per-char substitution (ampersand-first ⇒ emitted '&' never re-escaped),
   so a single entity map is faithful (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/- The escape of a whole sequence: concatenate the per-code-point entity
   sequences. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

@[grind] lemma escapedSeq_nil : escapedSeq [] = [] := rfl
@[grind] lemma escapedSeq_cons (c : Char) (cs : List Char) :
    escapedSeq (c :: cs) = entity c ++ escapedSeq cs := rfl

/- Escape/decode round-trips on the five significant code points. `entity c`
   for a concrete significant char reduces definitionally to the entity token
   (the `if c = …` guards decide), so each round-trip is the matching
   `entityDecode_*` axiom after a `show`. Marked `@[grind]` so `loom_solve`
   discharges the postconditions automatically. -/
@[grind] lemma roundtrip_amp  : entityDecode (entity '&')  = ['&']  := by
  show entityDecode "&amp;".toList = _;  exact entityDecode_amp
@[grind] lemma roundtrip_lt   : entityDecode (entity '<')  = ['<']  := by
  show entityDecode "&lt;".toList = _;   exact entityDecode_lt
@[grind] lemma roundtrip_gt   : entityDecode (entity '>')  = ['>']  := by
  show entityDecode "&gt;".toList = _;   exact entityDecode_gt
@[grind] lemma roundtrip_quot : entityDecode (entity '"')  = ['"']  := by
  show entityDecode "&quot;".toList = _; exact entityDecode_quot
@[grind] lemma roundtrip_apos : entityDecode (entity '\'') = ['\''] := by
  show entityDecode "&#x27;".toList = _; exact entityDecode_apos
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method escapeCodepoints (text : List Char) return (out : List Char)
  ensures out = escapedSeq text
  ensures entityDecode (entity '&')  = ['&']
  ensures entityDecode (entity '<')  = ['<']
  ensures entityDecode (entity '>')  = ['>']
  ensures entityDecode (entity '"')  = ['"']
  ensures entityDecode (entity '\'') = ['\'']
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = escapedSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := entity c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `entity`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    escapedSeq (text.drop (i - 1)) = entity text[i - 1]! ++ escapedSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeCodepoints by
  loom_solve
  rw [escapedSeq_drop_step text i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 venv swebench-lean. same_spec confirmed True for every attack + both positive controls (swebench_unified.markers.same_spec, velvet). patch.diff == frozen dataset gold verbatim.

### ATTACKS (all same_spec=True; verify command: `bash scripts/lean_verify.sh <path>`)
1) atk_1.lean  PREPATCH BUG (partial/wrong-value): apostrophe -> legacy decimal "&#39;" via translate(_html_escapes). EXIT=1 (FAIL). Residual goal: (...if c='\'' then ['&','#','3','9',';']...) = entity c  -> unprovable. This is the prepatch counterexample (prepatch_reproduced=true; mirrors bundle's Solution_prepatch.lean).
2) atk_2.lean  BOUNDARY off-by-one: loop guard `while i > 1` drops first char. EXIT=1 (FAIL). done_with leaves goal i=0 under ¬i>1 -> unprovable.
3) atk_3.lean  CONTROL-FLOW/identity: `return text` (clean loom_solve proof). EXIT=1 (FAIL). Goal: text = escapedSeq text.
4) atk_4.lean  CONTROL-FLOW/empty: `return []` (clean loom_solve proof). EXIT=1 (FAIL). Goal: [] = escapedSeq text.
5) atk_5.lean  PARTIAL-DOMAIN: escapes only & < > ; leaves " and ' unescaped. EXIT=1 (FAIL). Residual entity-mismatch goal.
6) atk_6.lean  CONTROL-FLOW-EFFECT/divergence: `while true` trivial body. EXIT=1 (FAIL). Total semantics rejects: "Decreasing annotations are required in total correctness semantics" + WPGen sorry. (This is exactly the class refinement.md D says total semantics excludes; confirmed.)
8) atk_8.lean  UNGROUNDED-ORACLE ECHO: `return entityDecode (escapedSeq text)` (entityDecode is an uninterpreted axiom pinned only on 5 tokens). EXIT=1 (FAIL). Goal: entityDecode (escapedSeq text) = escapedSeq text -> unprovable (also noncomputable). Confirms the axiom cannot be abused to launder the output.

### POSITIVE CONTROLS (must verify)
- positive_control.lean = frozen Solution.lean impl -> `bash scripts/lean_verify.sh .../positive_control.lean` EXIT=0 (verifies).
- atk_7b_correct_echo.lean = `return escapedSeq text` with fitting `loom_solve` proof -> EXIT=0 (verifies). A CORRECT impl (not a wrong-impl attack); its faithful patch = gold.
(Note: an early atk_7 reused the loop-specific frozen proof body verbatim with a non-loop impl and failed on the stale `rw`; repurposed to atk_7b with a fitting proof. Not counted as a wrong-impl attack.)

### Patches / resolve
ZERO verifying WRONG impls, so no faithful wrong-patch exists to run (patches={}). To close the verify=>resolve loop I materialized the faithful patch of the CORRECT verifying impl (= gold patch, saved gold_patch.diff) and RAN it through the official harness: `run_resolve('django__django-11276', gold, timeout=2400, retries=1)` -> RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1. (First two attempts returned COMPLETED=False 'no report' because the instance image was uncached; fixed by pulling mirror.gcr.io/swebench/sweb.eval.x86_64.django_1776_django-11276 and retagging to swebench/... per host retag convention, then the run completed and resolved.)

### A-LEG / refinement.md AUDIT (focus of this pass)
Every leg is R / A-reference / A-consumed / I; NO kind-3. The one genuinely-changed op (the escaper's char substitution) is modeled DEEPLY as escapedSeq/entity in the pure region (a Lean def, NOT an axiom about the function-under-change) -> A-reference (A3), validated == real html.escape. The only CONSUMED axioms (entityDecode_*) cover the UNCHANGED stdlib callee html.unescape (site B, A-consumed).
- Ran bundle axiom_check.py (G-AX): EXIT=0, 'escaped_seq deep model (== html.escape) + entity_decode axiom sound on 23 boundary + 20000 fuzz inputs and 6 decode tokens'.
- Independent CPython cross-check: html.escape('&','<','>','"',"'") == &amp;,&lt;,&gt;,&quot;,&#x27; (apostrophe -> &#x27; discriminator holds); html.unescape inverts all 5 emitted tokens. The A-reference and A-consumed correspondences to the real callees hold.
- model<->patch correspondence: escapeCodepoints<->escape() html.py:46; escapedSeq<->html.escape; entityDecode<->html.unescape (urlize sites). Consistent with mapping.md.

CONCLUSION: >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow, wrong-value/prepatch, divergence, ungrounded-oracle) all FAIL to verify against the complete functional postcondition; positive controls verify; gold (the faithful patch of the correct verifying impl) RESOLVES; A-legs sound. No verify=>NOT-resolve witness exists. verify=>correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break check for django__django-11276 (velvet). Modeled function escapeCodepoints, spec `out = escapedSeq text`, models django.utils.html.escape = mark_safe(html.escape(str(text))) at base_commit 28d5262fa3315690395f04e3619ed554dbaf725b.

VERDICT: FAITHFUL — no diverging input exists. The spec is neither too strong nor drifted from real repo behavior.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True — spec region (axioms/pure/pre/post + method signature ensures) is byte-identical; the prepatch differs only in the impl (apostrophe -> &#39;).
2. Solution.lean verifies (lean_verify.sh exit 0, total-correctness semantics: terminates and returns escapedSeq text). Solution_prepatch.lean fails exactly at the apostrophe entity (proves the discriminating change &#39; -> &#x27; is captured; G-DIFF holds).
3. Deep-model fidelity escapedSeq == real html.escape: html.escape(quote=True) is a straight ampersand-first .replace chain, hence a per-code-point independent substitution — precisely what escapedSeq/entity encode. Verified exhaustively over ALL code points 0..0x10FFFF minus surrogates (0 single-char mismatches) and by fuzzing 2,000,000 random strings incl. significant chars, already-escaped fragments (double-escaping), whitespace/unicode (0 mismatches). axiom_check.py (G-AX) also passes (exit 0: 23 boundary + 20000 fuzz).
4. entityDecode axioms (A-consumed) match real html.unescape on all five emitted tokens (&amp;->&, &lt;-><, &gt;->>, &quot;->", &#x27;->'). mark_safe/str() are identity on character content the F2P tests observe.

The apostrophe maps to &#x27; (CPython 3.x html.escape), matching the single behavioral change. No input where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean, Velvet tables) is clean; leakage.screen returns 0 hard failures. same_spec(Solution, Solution_prepatch)=True; no relaxed_leakage flag / no RELAXED_LEAKAGE.md, so this is a strict NO-LEAKAGE judgement (not a deferral).

Public problem_statement already discloses essentially the entire gold edit: it names the target 'django.utils.html.escape()', prescribes replacing it with the Python stdlib 'html.escape()', names the .translate->.replace mechanism, AND literally states the discriminator "converts ' to &#x27 rather than &#39". So the bar for 'beyond problem_statement' is high.

Spec-view content vs. gold edit:
- No diff markers, no patched file path (django/utils/html.py), no dotted module path.
- No gold-patch changed line reproduced (>=8 char normalized match): none.
- No patched repo symbol echoed beyond 'escape', which is already public via the problem statement. The gold patch's other touched symbols (urlize's local 'unescape', '_html_escapes', 'html.unescape', 'mark_safe', 'translate', 'smart_urlquote') do NOT appear as spec-view identifiers or in spec-view comments. The decoder is described abstractly as 'a standard-library HTML entity decoder' (entityDecode axioms) — it never names urlize/unescape.
- The '&#x27;' apostrophe value (entity '\'' and entityDecode_apos) is exactly the discriminator the problem_statement itself publishes; the &amp;/&lt;/&gt;/&quot; mappings are the well-known public behavior of the html.escape() the task explicitly directs the solver toward.
- No narration tokens (bug/fix/prepatch/regression/...) in comments; comment rationale is abstract (references mapping.md/plan sections, not the edit).

Conclusion: nothing in the spec view reveals the gold edit beyond what the public problem_statement already states. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
