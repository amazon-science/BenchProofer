# P2 adversarial audit — sympy__sympy-16886

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -80,10 +80,10 @@
       invariant 0 ≤ i ∧ i ≤ word.length
       invariant result = codesOf (word.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := word[i - 1]!
-      result := codeOf c :: result
+      let e : List Char := if c = '1' then "----".toList else codeOf c
+      result := e :: result
       i := i - 1
     return result
     -- impl-end
@@ -105,4 +105,4 @@
 prove_correct encodeWord by
   loom_solve
   rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  simp_all <;> (try grind)
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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -74,18 +74,7 @@
   ensures out = codesOf word
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := word.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ word.length
-      invariant result = codesOf (word.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := word[i - 1]!
-      result := codeOf c :: result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -103,6 +92,4 @@
   rw [hcons, codesOf_cons]
 
 prove_correct encodeWord by
-  loom_solve
-  rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -80,10 +80,10 @@
       invariant 0 ≤ i ∧ i ≤ word.length
       invariant result = codesOf (word.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := word[i - 1]!
-      result := codeOf c :: result
+      let e : List Char := if c = '2' then "..--".toList else codeOf c
+      result := e :: result
       i := i - 1
     return result
     -- impl-end
@@ -103,6 +103,4 @@
   rw [hcons, codesOf_cons]
 
 prove_correct encodeWord by
-  loom_solve
-  rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -75,16 +75,14 @@
   do
     -- impl-start
     let mut result : List (List Char) := []
-    let mut i := word.length
-    while i > 0
+    let mut i := 0
+    while i < word.length
       invariant 0 ≤ i ∧ i ≤ word.length
-      invariant result = codesOf (word.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = word.length
     do
-      let c := word[i - 1]!
+      let c := word[i]!
       result := codeOf c :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -103,6 +101,4 @@
   rw [hcons, codesOf_cons]
 
 prove_correct encodeWord by
-  loom_solve
-  rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -80,9 +80,8 @@
       invariant 0 ≤ i ∧ i ≤ word.length
       invariant result = codesOf (word.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := word[i - 1]!
+      let c := word[i]!
       result := codeOf c :: result
       i := i - 1
     return result
@@ -103,6 +102,4 @@
   rw [hcons, codesOf_cons]
 
 prove_correct encodeWord by
-  loom_solve
-  rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -76,11 +76,10 @@
     -- impl-start
     let mut result : List (List Char) := []
     let mut i := word.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ word.length
+    while i > 1
+      invariant 1 ≤ i ∨ i = word.length
       invariant result = codesOf (word.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i ≤ 1
     do
       let c := word[i - 1]!
       result := codeOf c :: result
@@ -103,6 +102,4 @@
   rw [hcons, codesOf_cons]
 
 prove_correct encodeWord by
-  loom_solve
-  rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
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
 -- (No consumed axioms. The per-symbol telegraphic-code table is modeled
@@ -74,18 +74,7 @@
   ensures out = codesOf word
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := word.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ word.length
-      invariant result = codesOf (word.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := word[i - 1]!
-      result := codeOf c :: result
-      i := i - 1
-    return result
+    return codesOf word ++ [[]]
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -103,6 +92,4 @@
   rw [hcons, codesOf_cons]
 
 prove_correct encodeWord by
-  loom_solve
-  rw [codesOf_drop_step word i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The per-symbol telegraphic-code table is modeled
--  DEEPLY by `codeOf` in the `pure` region — an A-reference validated
--  `codeOf == the real per-symbol code table` by axiom_check.py (G-AX),
--  NOT a consumed axiom. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The dot/dash code for one source symbol: the canonical telegraphic
   representation of each letter, digit and supported punctuation mark, as a
   sequence of '.' (dot) and '-' (dash) code points. Every other code point has
   no telegraphic representation and maps to the empty sequence (such symbols
   are filtered out before this map is consulted, so the empty image is never
   observed for a represented symbol). Front-recursive companion `codesOf`
   below expands a whole symbol sequence; the deep model is validated against
   the real repository table by axiom_check.py (G-AX). Provenance: mapping.md. -/
def codeOf (c : Char) : List Char :=
  match c with
  | 'A' => ".-".toList     | 'B' => "-...".toList
  | 'C' => "-.-.".toList   | 'D' => "-..".toList
  | 'E' => ".".toList      | 'F' => "..-.".toList
  | 'G' => "--.".toList    | 'H' => "....".toList
  | 'I' => "..".toList     | 'J' => ".---".toList
  | 'K' => "-.-".toList    | 'L' => ".-..".toList
  | 'M' => "--".toList     | 'N' => "-.".toList
  | 'O' => "---".toList    | 'P' => ".--.".toList
  | 'Q' => "--.-".toList   | 'R' => ".-.".toList
  | 'S' => "...".toList    | 'T' => "-".toList
  | 'U' => "..-".toList    | 'V' => "...-".toList
  | 'W' => ".--".toList    | 'X' => "-..-".toList
  | 'Y' => "-.--".toList   | 'Z' => "--..".toList
  | '0' => "-----".toList  | '1' => ".----".toList
  | '2' => "..---".toList  | '3' => "...--".toList
  | '4' => "....-".toList  | '5' => ".....".toList
  | '6' => "-....".toList  | '7' => "--...".toList
  | '8' => "---..".toList  | '9' => "----.".toList
  | '.' => ".-.-.-".toList | ',' => "--..--".toList
  | ':' => "---...".toList | ';' => "-.-.-.".toList
  | '?' => "..--..".toList | '-' => "-....-".toList
  | '_' => "..--.-".toList | '(' => "-.--.".toList
  | ')' => "-.--.-".toList | '\'' => ".----.".toList
  | '=' => "-...-".toList  | '+' => ".-.-.".toList
  | '/' => "-..-.".toList  | '@' => ".--.-.".toList
  | '$' => "...-..-".toList | '!' => "-.-.--".toList
  | _   => []

/- The encoding of a whole symbol sequence: the per-symbol code sequences in
   source order. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern). -/
def codesOf : List Char → List (List Char)
  | []      => []
  | c :: cs => codeOf c :: codesOf cs

@[grind] lemma codesOf_nil : codesOf [] = [] := rfl
@[grind] lemma codesOf_cons (c : Char) (cs : List Char) :
    codesOf (c :: cs) = codeOf c :: codesOf cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method encodeWord (word : List Char) return (out : List (List Char))
  ensures out = codesOf word
  do
    -- impl-start
    return word.map codeOf
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `codesOf` peels one `codeOf`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma codesOf_drop_step (word : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ word.length) :
    codesOf (word.drop (i - 1)) = codeOf word[i - 1]! :: codesOf (word.drop i) := by
  have hlt : i - 1 < word.length := by omega
  have hcons : word.drop (i - 1) = word[i - 1]! :: word.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, codesOf_cons]

prove_correct encodeWord by
  loom_solve
  induction word with
  | nil => rfl
  | cons c cs ih => simp [codesOf_cons, ih]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec surface (velvet same_spec): axioms/pure/pre/post + the frozen `ensures out = codesOf word` clause + the `codesOf_drop_step` lemma are all frozen; only the `encodeWord` impl do-block and the `prove_correct` body are attacker-controlled. Confirmed via markers.same_spec: all 8 files return True. The postcondition is an EXACT functional equality to a frozen, fully-concrete, TOTAL `def` (`codesOf`, built from the 52-arm `codeOf` match), with NO consumed axioms and NO opaque/axiomatized symbol -> there is no ungrounded oracle to echo. Any impl whose output differs from `codesOf word` leaves a genuinely false, unprovable VC.

All verifications run via scripts/lean_verify.sh (budget, timeout 360), launched concurrently in two batches of 4 background jobs. Results:
- atk_1 (prepatch bug: impl maps '1'->"----") exit 1: unsolved goal `word[i-1]?.getD 'A' = '1' -> ['-','-','-','-'] = codeOf '1'` (false; codeOf '1' = ".----"). PREPATCH REPRODUCED, failing on the exact discriminating clause.
- atk_2 (return []) exit 1: `codesOf word = []` (false for nonempty).
- atk_3 (wrong entry '2'->"..--", ungrounded-echo style) exit 1: `(if ...='2' then ['.','.','-','-'] else codeOf ...) :: ... = codesOf (drop (i-1) word)` (false).
- atk_4 (control-flow-effect: forward loop + prepend => reversed output) exit 1: `result_1 = codesOf word` unprovable.
- atk_5 (off-by-one: word[i]! for word[i-1]!) exit 1: `codeOf (word[i]?...) :: ... = codesOf (drop (i-1) word)` (false).
- atk_6 (partial-domain: `while i > 1`, skips first element) exit 1: both the body VC and `result_1 = codesOf word` unprovable.
- atk_7 (boundary: `codesOf word ++ [[]]`) exit 1: reduces to `False`.
  Every wrong impl carried a SHOTGUN proof (`loom_solve <;> simp_all <;> (try omega) <;> (try grind)`; atk_1 also with the real drop-step rewrite) — none closed the false goal, so these are genuine unprovable VCs, not tactic artifacts.
- atk_pc (positive control `return word.map codeOf`, structurally distinct from the reference backward loop, closed by inline `induction word`) exit 0: verifies. Spec is non-vacuous and the canonical answer is provable.

No verifying-but-wrong impl was found, so there is NO faithful refined patch to materialize; the mandatory run_resolve step for verifying wrong impls is vacuously satisfied (empty `patches`). This is the correct SOUND outcome: verify => correct holds for this spec.

Refinement.md audit: A1 = R (str <-> List Char, mapping.md §2); A2 = A-reference + I (table modeled deeply by codeOf/codesOf + concrete fold ops, G-CONF-transliterated); A3 = A-reference (per-entry codeOf == char_morse, entry-for-entry). §B: no consumed axioms (axioms: [] in Solution.lean). §C: no kind-3 — the changed datum is one finite `match` arm codeOf '1', fully expressible.

The A-reference correspondence to the real callee (`mapping[letter]` with `mapping = char_morse`, inverse of module-level morse_char, crypto.py:1538) is validated by axiom_check.py against the BASE repo (key sets coincide 52; codeOf == base char_morse on all 51 UNCHANGED entries; empty off-table; the single changed '1' entry honestly shown as base-bug '----' vs model gold '.----', deferred to G-CONF/G-RESOLVE/G-DIFF) and by G-CONF (a hand-transliterated shadow of codeOf + the unchanged encode_morse I-ops, NOT importing the oracle, diffed vs the real patched encode_morse over 1e5 inputs, seed 16886). Both are genuine differential/soundness checks, not oracle echoes. All legs are R / A-reference / I; A-reference correspondence holds. Real repo verified at base_commit c50643a498 (worktree): base char_morse holds '----':'1' (bug), gold patch flips it to '.----':'1'.

Gold patch.diff = instance.json patch verbatim (single-line table edit); it resolves under G-RESOLVE per meta.json and is not re-run here because no attack produced a distinct faithful patch to resolve-test.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The per-symbol telegraphic-code table is modeled
--  DEEPLY by `codeOf` in the `pure` region — an A-reference validated
--  `codeOf == the real per-symbol code table` by axiom_check.py (G-AX),
--  NOT a consumed axiom. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The dot/dash code for one source symbol: the canonical telegraphic
   representation of each letter, digit and supported punctuation mark, as a
   sequence of '.' (dot) and '-' (dash) code points. Every other code point has
   no telegraphic representation and maps to the empty sequence (such symbols
   are filtered out before this map is consulted, so the empty image is never
   observed for a represented symbol). Front-recursive companion `codesOf`
   below expands a whole symbol sequence; the deep model is validated against
   the real repository table by axiom_check.py (G-AX). Provenance: mapping.md. -/
def codeOf (c : Char) : List Char :=
  match c with
  | 'A' => ".-".toList     | 'B' => "-...".toList
  | 'C' => "-.-.".toList   | 'D' => "-..".toList
  | 'E' => ".".toList      | 'F' => "..-.".toList
  | 'G' => "--.".toList    | 'H' => "....".toList
  | 'I' => "..".toList     | 'J' => ".---".toList
  | 'K' => "-.-".toList    | 'L' => ".-..".toList
  | 'M' => "--".toList     | 'N' => "-.".toList
  | 'O' => "---".toList    | 'P' => ".--.".toList
  | 'Q' => "--.-".toList   | 'R' => ".-.".toList
  | 'S' => "...".toList    | 'T' => "-".toList
  | 'U' => "..-".toList    | 'V' => "...-".toList
  | 'W' => ".--".toList    | 'X' => "-..-".toList
  | 'Y' => "-.--".toList   | 'Z' => "--..".toList
  | '0' => "-----".toList  | '1' => ".----".toList
  | '2' => "..---".toList  | '3' => "...--".toList
  | '4' => "....-".toList  | '5' => ".....".toList
  | '6' => "-....".toList  | '7' => "--...".toList
  | '8' => "---..".toList  | '9' => "----.".toList
  | '.' => ".-.-.-".toList | ',' => "--..--".toList
  | ':' => "---...".toList | ';' => "-.-.-.".toList
  | '?' => "..--..".toList | '-' => "-....-".toList
  | '_' => "..--.-".toList | '(' => "-.--.".toList
  | ')' => "-.--.-".toList | '\'' => ".----.".toList
  | '=' => "-...-".toList  | '+' => ".-.-.".toList
  | '/' => "-..-.".toList  | '@' => ".--.-.".toList
  | '$' => "...-..-".toList | '!' => "-.-.--".toList
  | _   => []

/- The encoding of a whole symbol sequence: the per-symbol code sequences in
   source order. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern). -/
def codesOf : List Char → List (List Char)
  | []      => []
  | c :: cs => codeOf c :: codesOf cs

@[grind] lemma codesOf_nil : codesOf [] = [] := rfl
@[grind] lemma codesOf_cons (c : Char) (cs : List Char) :
    codesOf (c :: cs) = codeOf c :: codesOf cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method encodeWord (word : List Char) return (out : List (List Char))
  ensures out = codesOf word
  do
    -- impl-start
    return word.map codeOf
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `codesOf` peels one `codeOf`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma codesOf_drop_step (word : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ word.length) :
    codesOf (word.drop (i - 1)) = codeOf word[i - 1]! :: codesOf (word.drop i) := by
  have hlt : i - 1 < word.length := by omega
  have hcons : word.drop (i - 1) = word[i - 1]! :: word.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, codesOf_cons]

prove_correct encodeWord by
  loom_solve
  induction word with
  | nil => rfl
  | cons c cs ih => simp [codesOf_cons, ih]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec surface (velvet same_spec): axioms/pure/pre/post + the frozen `ensures out = codesOf word` clause + the `codesOf_drop_step` lemma are all frozen; only the `encodeWord` impl do-block and the `prove_correct` body are attacker-controlled. Confirmed via markers.same_spec: all 8 files return True. The postcondition is an EXACT functional equality to a frozen, fully-concrete, TOTAL `def` (`codesOf`, built from the 52-arm `codeOf` match), with NO consumed axioms and NO opaque/axiomatized symbol -> there is no ungrounded oracle to echo. Any impl whose output differs from `codesOf word` leaves a genuinely false, unprovable VC.

All verifications run via scripts/lean_verify.sh (budget, timeout 360), launched concurrently in two batches of 4 background jobs. Results:
- atk_1 (prepatch bug: impl maps '1'->"----") exit 1: unsolved goal `word[i-1]?.getD 'A' = '1' -> ['-','-','-','-'] = codeOf '1'` (false; codeOf '1' = ".----"). PREPATCH REPRODUCED, failing on the exact discriminating clause.
- atk_2 (return []) exit 1: `codesOf word = []` (false for nonempty).
- atk_3 (wrong entry '2'->"..--", ungrounded-echo style) exit 1: `(if ...='2' then ['.','.','-','-'] else codeOf ...) :: ... = codesOf (drop (i-1) word)` (false).
- atk_4 (control-flow-effect: forward loop + prepend => reversed output) exit 1: `result_1 = codesOf word` unprovable.
- atk_5 (off-by-one: word[i]! for word[i-1]!) exit 1: `codeOf (word[i]?...) :: ... = codesOf (drop (i-1) word)` (false).
- atk_6 (partial-domain: `while i > 1`, skips first element) exit 1: both the body VC and `result_1 = codesOf word` unprovable.
- atk_7 (boundary: `codesOf word ++ [[]]`) exit 1: reduces to `False`.
  Every wrong impl carried a SHOTGUN proof (`loom_solve <;> simp_all <;> (try omega) <;> (try grind)`; atk_1 also with the real drop-step rewrite) — none closed the false goal, so these are genuine unprovable VCs, not tactic artifacts.
- atk_pc (positive control `return word.map codeOf`, structurally distinct from the reference backward loop, closed by inline `induction word`) exit 0: verifies. Spec is non-vacuous and the canonical answer is provable.

No verifying-but-wrong impl was found, so there is NO faithful refined patch to materialize; the mandatory run_resolve step for verifying wrong impls is vacuously satisfied (empty `patches`). This is the correct SOUND outcome: verify => correct holds for this spec.

Refinement.md audit: A1 = R (str <-> List Char, mapping.md §2); A2 = A-reference + I (table modeled deeply by codeOf/codesOf + concrete fold ops, G-CONF-transliterated); A3 = A-reference (per-entry codeOf == char_morse, entry-for-entry). §B: no consumed axioms (axioms: [] in Solution.lean). §C: no kind-3 — the changed datum is one finite `match` arm codeOf '1', fully expressible.

The A-reference correspondence to the real callee (`mapping[letter]` with `mapping = char_morse`, inverse of module-level morse_char, crypto.py:1538) is validated by axiom_check.py against the BASE repo (key sets coincide 52; codeOf == base char_morse on all 51 UNCHANGED entries; empty off-table; the single changed '1' entry honestly shown as base-bug '----' vs model gold '.----', deferred to G-CONF/G-RESOLVE/G-DIFF) and by G-CONF (a hand-transliterated shadow of codeOf + the unchanged encode_morse I-ops, NOT importing the oracle, diffed vs the real patched encode_morse over 1e5 inputs, seed 16886). Both are genuine differential/soundness checks, not oracle echoes. All legs are R / A-reference / I; A-reference correspondence holds. Real repo verified at base_commit c50643a498 (worktree): base char_morse holds '----':'1' (bug), gold patch flips it to '.----':'1'.

Gold patch.diff = instance.json patch verbatim (single-line table edit); it resolves under G-RESOLVE per meta.json and is not re-run here because no attack produced a distinct faithful patch to resolve-test.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-16886 velvet. FINDINGS:

1. same_spec check: spec_view(Solution.lean) == spec_view(Solution_prepatch.lean) canonically (swebench_unified.markers.same_spec via VelvetBackend.language) => True. Spec region byte-identical (blank-line-insensitive canonical signature). Modeled contract is `method encodeWord (word : List Char) return (out : List (List Char)) ensures out = codesOf word`.

2. Real callee: encode_morse's per-symbol loop `morseword.append(mapping[letter])` with mapping = char_morse (post-patch), crypto.py:1578-1583. char_morse = inverse of morse_char; the gold patch corrects morse_char entry `"----": "1"` -> `".----": "1"`.

3. Deep model fidelity: built the POST-patch char_morse from the real repo table + gold hunk and compared to codeOf's match table. Result: key sets identical (52 symbols A-Z,0-9,punct), ZERO value diffs. codeOf '1' = '.----' matches the corrected entry. codeOf returns [] off the represented set.

4. Domain boundary: the loop only ever sees letters surviving translate(msg,None, chars-ok) i.e. letter in set(mapping.keys()); unrepresented symbols are filtered before the table read, so codeOf's [] image is never observed on the real callee's domain — no spurious divergence. Space is split out before the inner loop, never seen inside a word.

5. codesOf front-recursive expansion = per-symbol code sequences in source order = the assembled morseword list. Exact structural correspondence to the loop.

6. Lean verification: Solution.lean elaborates cleanly (scripts/lean_verify.sh exit 0, no sorry/error), so the spec is satisfiable and the impl+proof close against exactly this ensures clause.

The spec neither over-constrains nor drifts from the real repo behavior: on every input in the real callee's domain the modeled function agrees with the post-patch char_morse lookup-and-append. No diverging input exists. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the SOLVER-VISIBLE problem_statement only (not hints_text). The public problem_statement discloses the gold edit VERBATIM: 'contains an incorrect mapping of "----": "1". The correct mapping is ".----": "1".' The full discriminator ('1' -> ".----") is therefore already public.

Spec view (velvet Solution.lean): the modeled change lives in `codeOf` as `| '1' => ".----".toList`, one entry of a complete, standard International-Morse table (A-Z, 0-9, punctuation). The line `| '0' => "-----".toList  | '1' => ".----".toList` echoes exactly the CORRECT mapping the problem statement announces publicly — it reveals nothing beyond the public task, and the surrounding 51 entries are the canonical Morse code widely known independent of the patch. No pre-patch buggy value ("----" for '1') appears in the spec view; that only appears in Solution_prepatch.lean (not part of the consumer spec view).

Mechanical G-LEAK screen: PASS (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier embedding a patched repo symbol, no bug/fix narration). Spec-view comments are abstract behavioral prose ('canonical telegraphic representation', 'no telegraphic representation -> empty sequence'); bug/fix/wrong narration is confined to refinement.md and mapping.md, which are NOT the spec view.

Frozen-spec integrity: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet.language) == True — spec region byte-identical (signature match); the prepatch variant, which restores '1' -> "----", fails the same frozen spec (G-DIFF sound).

Conclusion: the spec necessarily encodes the corrected entry, but that exact datum is already the public content of the problem_statement, so it does not leak the gold edit beyond the public problem.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.