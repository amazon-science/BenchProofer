# P2 adversarial audit — pytest-dev__pytest-7521

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,8 @@
       decreasing i
     do
       let c := text[i - 1]!
-      result := c :: result
+      let t : Char := if c = '\r' then '\n' else c
+      result := t :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
       done_with i = 0
       decreasing i
     do
-      let c := text[i - 1]!
+      let c := text[i]!
       result := c :: result
       i := i - 1
     return result
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := text.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = readback (text.drop i)
       done_with i = 0
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,18 +47,7 @@
   ensures out = text
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = readback (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return readback text
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -77,5 +66,3 @@
 
 prove_correct readbackStream by
   loom_solve
-  rw [readback_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,18 +47,7 @@
   ensures out = text
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = readback (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return text
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -77,5 +66,3 @@
 
 prove_correct readbackStream by
   loom_solve
-  rw [readback_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,16 +48,16 @@
   do
     -- impl-start
     let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
+    let mut i := 0
+    while i < text.length
       invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = readback (text.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = readback (text.take i)
+      done_with i = text.length
+      decreasing text.length - i
     do
-      let c := text[i - 1]!
-      result := c :: result
-      i := i - 1
+      let c := text[i]!
+      result := result ++ [c]
+      i := i + 1
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,18 +47,21 @@
   ensures out = text
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = readback (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    if text.length = 0 then
+      return ['A']
+    else
+      let mut result : List Char := []
+      let mut i := text.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ text.length
+        invariant result = readback (text.drop i)
+        done_with i = 0
+        decreasing i
+      do
+        let c := text[i - 1]!
+        result := c :: result
+        i := i - 1
+      return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single operation whose behavior is pinned here — the
   read-back of buffered stream content — is modeled DEEPLY in the `pure` region
   (`readback`) and validated against the real platform text-stream reader by
   axiom_check.py (G-AX), so it is an A-reference, not a consumed axiom
   (mapping.md §3.1). -/
-- axioms-end

-- pure-start
/- The content recovered when buffered stream text is read back: every code
   point is returned exactly as it was buffered — no code point is rewritten,
   inserted, dropped, or merged with a neighbour. Written front-recursively so a
   single unfold is available per loop step (the backward-fold pattern). -/
def readback : List Char → List Char
  | []      => []
  | c :: cs => c :: readback cs

@[grind] lemma readback_nil : readback [] = [] := rfl
@[grind] lemma readback_cons (c : Char) (cs : List Char) :
    readback (c :: cs) = c :: readback cs := rfl

/- Read-back returns the buffered content unchanged: the recovered sequence is
   the input sequence itself. Marked `@[grind]` so `loom_solve` can use it to
   discharge the postcondition. -/
@[grind] lemma readback_id (cs : List Char) : readback cs = cs := by
  induction cs with
  | nil => rfl
  | cons c cs ih => rw [readback_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method readbackStream (text : List Char) return (out : List Char)
  ensures out = readback text
  ensures out = text
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = readback (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `readback` peels one code point. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma readback_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    readback (text.drop (i - 1)) = text[i - 1]! :: readback (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, readback_cons]

prove_correct readbackStream by
  loom_solve
  rw [readback_drop_step text i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins out=text uniquely over the FULL domain (no preconditions; postconds out=readback text AND out=text with readback_id: readback=id). Hence every verifying impl returns exactly text = verbatim per-code-point read-back = behaviorally identical to gold.

Attacks (all same_spec=True, verified via scripts/lean_verify.sh, run concurrently ≤4):
- atk_1 prepatch/control-flow-effect ('\r'→'\n' universal-newline translation): EXIT=1, unsolved goal `¬ text[i-1]?.getD 'A' = '\x0d'` — cannot rule out carriage return. Reproduces the prepatch bug.
- atk_2 boundary/index-shift (peel text[i]! not text[i-1]!): EXIT=1.
- atk_3 loop-bound off (while i>1, drops last char): EXIT=1.
- atk_6 forward-reverse fold (result++[c] over take i): EXIT=1.
- atk_7 partial-domain (returns ['A'] on empty text, correct otherwise): EXIT=1 — spec pins out=[] on empty input.
- atk_4 ungrounded-oracle echo `return readback text`: EXIT=0 (VERIFIES).
- atk_5 ungrounded-oracle echo `return text`: EXIT=0 (VERIFIES).
pos_control (byte copy of Solution.lean): EXIT=0.

MANDATORY resolve step: both verifying echoes (atk_4, atk_5) have faithful refined patch = the gold patch verbatim (identity read-back refines to `newline=""` addition at src/_pytest/capture.py:388). Materialized and RAN through official harness via swebench_unified.harness.run_resolve('pytest-dev__pytest-7521', patch): RESOLVED=True, COMPLETED=True. FAIL_TO_PASS test_cafd_preserves_newlines[\r] and [\r\n] both success; all PASS_TO_PASS success; zero failures. (Single resolve run covers both attacks since the two faithful patches are byte-identical to the gold patch.)

refinement.md leg audit: A1=R (str↔List Char, mapping §2), A2=A-reference+I (deep model `readback` == real newline="" TextIOWrapper read-back; fold ops I), A3=A-reference+I. NO A-consumed leg, NO kind-3 leg. The A-reference correspondence holds: G-AX (axiom_check.py) validates readback==identity against the real patched stream over all newline forms + 20k fuzz, plus the negative check that the prepatch default-newline wrapper translates \r→\n. This matches the actual behavioral change the FAIL_TO_PASS tests exercise.

No verifying same-spec impl exists whose faithful patch fails to resolve; the only verifying impls are behaviorally-correct echoes whose patch resolves. verify ⇒ correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single operation whose behavior is pinned here — the
   read-back of buffered stream content — is modeled DEEPLY in the `pure` region
   (`readback`) and validated against the real platform text-stream reader by
   axiom_check.py (G-AX), so it is an A-reference, not a consumed axiom
   (mapping.md §3.1). -/
-- axioms-end

-- pure-start
/- The content recovered when buffered stream text is read back: every code
   point is returned exactly as it was buffered — no code point is rewritten,
   inserted, dropped, or merged with a neighbour. Written front-recursively so a
   single unfold is available per loop step (the backward-fold pattern). -/
def readback : List Char → List Char
  | []      => []
  | c :: cs => c :: readback cs

@[grind] lemma readback_nil : readback [] = [] := rfl
@[grind] lemma readback_cons (c : Char) (cs : List Char) :
    readback (c :: cs) = c :: readback cs := rfl

/- Read-back returns the buffered content unchanged: the recovered sequence is
   the input sequence itself. Marked `@[grind]` so `loom_solve` can use it to
   discharge the postcondition. -/
@[grind] lemma readback_id (cs : List Char) : readback cs = cs := by
  induction cs with
  | nil => rfl
  | cons c cs ih => rw [readback_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method readbackStream (text : List Char) return (out : List Char)
  ensures out = readback text
  ensures out = text
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = readback (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `readback` peels one code point. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma readback_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    readback (text.drop (i - 1)) = text[i - 1]! :: readback (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, readback_cons]

prove_correct readbackStream by
  loom_solve
  rw [readback_drop_step text i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Spec pins out=text uniquely over the FULL domain (no preconditions; postconds out=readback text AND out=text with readback_id: readback=id). Hence every verifying impl returns exactly text = verbatim per-code-point read-back = behaviorally identical to gold.

Attacks (all same_spec=True, verified via scripts/lean_verify.sh, run concurrently ≤4):
- atk_1 prepatch/control-flow-effect ('\r'→'\n' universal-newline translation): EXIT=1, unsolved goal `¬ text[i-1]?.getD 'A' = '\x0d'` — cannot rule out carriage return. Reproduces the prepatch bug.
- atk_2 boundary/index-shift (peel text[i]! not text[i-1]!): EXIT=1.
- atk_3 loop-bound off (while i>1, drops last char): EXIT=1.
- atk_6 forward-reverse fold (result++[c] over take i): EXIT=1.
- atk_7 partial-domain (returns ['A'] on empty text, correct otherwise): EXIT=1 — spec pins out=[] on empty input.
- atk_4 ungrounded-oracle echo `return readback text`: EXIT=0 (VERIFIES).
- atk_5 ungrounded-oracle echo `return text`: EXIT=0 (VERIFIES).
pos_control (byte copy of Solution.lean): EXIT=0.

MANDATORY resolve step: both verifying echoes (atk_4, atk_5) have faithful refined patch = the gold patch verbatim (identity read-back refines to `newline=""` addition at src/_pytest/capture.py:388). Materialized and RAN through official harness via swebench_unified.harness.run_resolve('pytest-dev__pytest-7521', patch): RESOLVED=True, COMPLETED=True. FAIL_TO_PASS test_cafd_preserves_newlines[\r] and [\r\n] both success; all PASS_TO_PASS success; zero failures. (Single resolve run covers both attacks since the two faithful patches are byte-identical to the gold patch.)

refinement.md leg audit: A1=R (str↔List Char, mapping §2), A2=A-reference+I (deep model `readback` == real newline="" TextIOWrapper read-back; fold ops I), A3=A-reference+I. NO A-consumed leg, NO kind-3 leg. The A-reference correspondence holds: G-AX (axiom_check.py) validates readback==identity against the real patched stream over all newline forms + 20k fuzz, plus the negative check that the prepatch default-newline wrapper translates \r→\n. This matches the actual behavioral change the FAIL_TO_PASS tests exercise.

No verifying same-spec impl exists whose faithful patch fails to resolve; the only verifying impls are behaviorally-correct echoes whose patch resolves. verify ⇒ correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the modeled function readbackStream (postconditions out = readback text ∧ out = text, with readback proven == identity by readback_id) against the real post-patch callee: io.TextIOWrapper(BytesIO, encoding='utf-8', errors='replace', newline='', write_through=True) write→read round-trip (src/_pytest/capture.py:388, FDCaptureBinary.__init__ feeding FDCapture.snap).

Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True. Solution.lean verifies (lean_verify exit 0); prepatch fails on goal ¬ text[i-1]?.getD = '\x0d' (G-DIFF holds — the pre-patch universal-newline translation of U+000D breaks out = text).

Empirical faithfulness testing of readback == real newline='' read-back:
- Curated edge chars (\x0b \x0c \x1c \x1d \x1e control chars, NEL \x85, LS 
, PS 
, every newline form \n \r \r\n \n\r, doubled/mixed): ALL identity — newline='' disables translation in both directions, and TextIOWrapper.read() only ever translates \r/\r\n/\n, none of which occurs under newline=''.
- Non-BMP (😀 U+1F600), ￿: identity.
- 200,000-input fuzz over ALL valid Unicode scalar values (0..0x10FFFF minus D800-DFFF surrogates), lengths 0-8, seed 999: 0 divergences. Round-trip is exactly identity across the entire refined domain.

Only divergence found: lone/embedded surrogates (\ud800, \udfff → '?' via errors='replace'). These are OUT OF DOMAIN — Lean's Char type is restricted to valid Unicode scalar values (excludes surrogates by construction) and the bijection Char.ofNat(ord ch) in mapping.md §2 only covers valid scalars. Surrogates therefore cannot be represented as List Char inputs and cannot witness a divergence.

Conclusion: within the type abstraction the spec commits to (List Char = valid Unicode scalar values), the modeled function agrees with the real callee on every input. The postcondition out = text is not too strong — it is precisely the post-patch behavior (verbatim read-back), and it is exactly the property the F2P tests test_cafd_preserves_newlines[\r]/[\r\n] exercise. No diverging input exists in the modeled domain. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view of Solution.lean is clean. Mechanical leakage.screen(velvet) passes with zero hard_failures: no diff markers, the sole changed gold line 'newline="",' is absent from the view, patched file/module path absent, patched-symbols set is empty (hunk touches no def/class), no narration tokens in comments. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the frozen spec (contracts + pure readback/readback_id + method signature) is byte-identical across patched/prepatch; only the elided impl/proof regions differ. Semantic check: none of newline/carriage/\r/U+000D/capture/tmpfile/TextIOWrapper/EncodedFile/snap/readouterr/capfd/translation/universal appear in the spec view. The view only pins the abstract behavioral goal (out = readback text = text, i.e. verbatim read-back preserving carriage returns), which is exactly the behavior the PUBLIC problem_statement already discloses (capfd.readouterr() converting \r->\n; reproducer asserts out.endswith('\r')). Formalizing the publicly-stated desired post-condition does not reveal the gold edit mechanism (newline="") or its location beyond problem_statement. The concrete newline-translation mechanism lives only in Solution_prepatch.lean's elided impl region and audit docs (refinement.md/mapping.md), not in the consumer spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
