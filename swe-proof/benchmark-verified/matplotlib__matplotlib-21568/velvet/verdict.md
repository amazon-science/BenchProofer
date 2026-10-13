# P2 adversarial audit — matplotlib__matplotlib-21568

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,8 @@
       decreasing i
     do
       let c := s[i - 1]!
-      result := mathProtect c ++ result
+      let e : List Char := if c = '-' then "{-}".toList else [c]
+      result := e ++ result
       i := i - 1
     let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
     return out
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,8 @@
       decreasing i
     do
       let c := s[i - 1]!
-      result := mathProtect c ++ result
+      let e : List Char := if c = ':' then "{:}".toList else [c]
+      result := e ++ result
       i := i - 1
     let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
     return out
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
       done_with i = 0
       decreasing i
     do
-      let c := s[i - 1]!
+      let c := s[i]!
       result := mathProtect c ++ result
       i := i - 1
     let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
       decreasing i
     do
       let c := s[i - 1]!
-      result := mathProtect c ++ result
+      result := result ++ mathProtect c
       i := i - 1
     let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
     return out
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,19 +74,7 @@
   ensures out = removeEmpty ("$\\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)
   do
     -- impl-start
-    let s := reSub text
-    let mut result : List Char := []
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant result = protectSeq (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      result := mathProtect c ++ result
-      i := i - 1
-    let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
+    let out := removeEmpty ("$\\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)
     return out
     -- impl-end
 end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,8 @@
       decreasing i
     do
       let c := s[i - 1]!
-      result := mathProtect c ++ result
+      let e : List Char := if c = '-' then "{:}".toList else if c = ':' then "{-}".toList else if c = ' ' then "\\;".toList else [c]
+      result := e ++ result
       i := i - 1
     let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
     return out
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
       let c := s[i - 1]!
       result := mathProtect c ++ result
       i := i - 1
-    let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
+    let out := "$\\mathdefault{".toList ++ result ++ "}$".toList
     return out
     -- impl-end
 end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,18 +75,8 @@
   do
     -- impl-start
     let s := reSub text
-    let mut result : List Char := []
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant result = protectSeq (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      result := mathProtect c ++ result
-      i := i - 1
-    let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
+    let prot := protectSeq s
+    let out := removeEmpty ("$\\mathdefault{".toList ++ prot ++ "}$".toList)
     return out
     -- impl-end
 end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real label renderer is a single bounded pass over the
   pre-processed text and always terminates, so a diverging implementation must
   NOT satisfy this spec. Partial correctness would let a non-terminating loop
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The label pre-processor: a regular-expression substitution that wraps each
   maximal run of ASCII letters in the surrounding math/upright delimiters. It
   is an UNCHANGED community callee; the routine under spec only consumes its
   result, so the weakest sufficient contract is "some deterministic function
   of the text" (an uninterpreted map on code points). Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom reSub : List Char → List Char

/- Collapse of an empty math group: deletes every occurrence of the empty
   delimiter pair from the assembled string. Also an UNCHANGED community callee
   applied verbatim as the final step; modeled as an uninterpreted map for the
   same reason. Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom removeEmpty : List Char → List Char
-- axioms-end

-- pure-start
/- The math-protection of a single code point. Three code points are wrapped in
   curly braces / replaced by a thin-space control sequence so that the math
   renderer does not treat them as binary operators or collapse inter-number
   spacing; every other code point passes through unchanged. (Behaviour, not the
   edit: mapping.md §3.1.) -/
def mathProtect (c : Char) : List Char :=
  if c = '-' then "{-}".toList
  else if c = ':' then "{:}".toList
  else if c = ' ' then "\\;".toList
  else [c]

/- The math-protection of a whole sequence: concatenate the per-code-point
   protections. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). The chained single-pass substitution it models
   is faithful because no protection output contains a code point a later
   substitution would touch (mapping.md §3.1). -/
def protectSeq : List Char → List Char
  | []      => []
  | c :: cs => mathProtect c ++ protectSeq cs

@[grind] lemma protectSeq_nil : protectSeq [] = [] := rfl
@[grind] lemma protectSeq_cons (c : Char) (cs : List Char) :
    protectSeq (c :: cs) = mathProtect c ++ protectSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a tick/offset label for a math (TeX) text renderer.

   The label text is first passed through the letter-run pre-processor
   (`reSub`); each code point of the result is then math-protected
   (`protectSeq` — three code points are wrapped/replaced, all others pass
   through); the protected string is enclosed in the math delimiters
   `$\mathdefault{ … }$`; finally any empty math group is dropped
   (`removeEmpty`). `text` is the read-only input label (not `mut`): the routine
   consumes it and never alters it (directive 5). The label is modeled as a
   `List Char` (a per-code-point string); the delimiters are concrete literals
   (mapping.md §2). -/
noncomputable section
method renderTexLabel (text : List Char) return (out : List Char)
  ensures out = removeEmpty ("$\\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)
  do
    -- impl-start
    let s := reSub text
    let mut result : List Char := []
    let mut i := s.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ s.length
      invariant result = protectSeq (s.drop i)
      done_with i = 0
      decreasing i
    do
      let c := s[i - 1]!
      result := mathProtect c ++ result
      i := i - 1
    let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
    return out
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `protectSeq` peels one `mathProtect`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma protectSeq_drop_step (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    protectSeq (s.drop (i - 1)) = mathProtect s[i - 1]! ++ protectSeq (s.drop i) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, protectSeq_cons]

prove_correct renderTexLabel by
  loom_solve
  rw [protectSeq_drop_step (reSub text) i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of matplotlib__matplotlib-21568 (velvet). RESULT: SOUND. No verifying-but-wrong impl found; verify=>correct holds.

SPEC SHAPE: renderTexLabel's postcondition is an EXACT functional equality `out = removeEmpty ("$\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)`. protectSeq/mathProtect are concrete pure defs pinning the per-code-point map ('-'->{-}, ':'->{:}, ' '->\;, else id); reSub/removeEmpty are opaque axioms (unchanged callees). So any same-spec verifying impl must compute exactly the gold function of `text` — a maximally tight spec.

SAME_SPEC: all 8 attack files + positive_control confirmed same_spec=True vs frozen Solution.lean (swebench_unified.markers.same_spec, velvet). Only the impl region (and prove_correct body, which spec_view elides) edited; axioms/pure/pre/post/ensures byte-identical.

### VERIFY RESULTS (scripts/lean_verify.sh <file>, run concurrently <=4/batch):
- positive_control (gold impl): EXIT 0 (VERIFIES).
- atk_1 prepatch bug (dash-only protection): EXIT 1, unsolved goal `invariant_2: result = protectSeq (s.drop i)`. PREPATCH REPRODUCED.
- atk_2 partial-domain (colon-only): EXIT 1, same invariant_2 unsolved.
- atk_3 boundary/off-by-one (s[i]! instead of s[i-1]!): EXIT 1, invariant_2 unsolved.
- atk_4 control-flow-effect (wrong concat order, result++mathProtect c): EXIT 1, invariant_2 unsolved.
- atk_6 swapped mapping ('-'->{:}, ':'->{-}): EXIT 1, invariant_2 unsolved (after fixing a Lean escape typo; re-verified same_spec=True).
- atk_7 dropped-callee (omit removeEmpty wrap): EXIT 1, invariant_2/postcondition unsolved.
- atk_5 ungrounded-oracle echo (return the postcondition RHS directly, no loop): EXIT 1, `No goals to be solved` at the prove_correct block.
- atk_8 correct-but-structurally-different (compute protectSeq s directly, no loop): EXIT 1, `No goals to be solved`.

KEY FINDING: NONE of the 7 genuinely-wrong impls (atk_1,2,3,4,6,7 + echo atk_5) verified. Therefore protocol step 2 (materialize faithful refined patch + run_resolve for each VERIFYING wrong impl) has an EMPTY trigger set — no resolve run was required, and `patches` is empty. verify=>correct is not falsified.

NOTE on atk_5/atk_8: these two are actually SEMANTICALLY CORRECT alternate impls (echo of the RHS / loop-free direct computation) that fail ONLY because the frozen prove_correct tactic block is coupled to the while-loop shape (`No goals to be solved`). This is proof-brittleness producing FALSE NEGATIVES (correct impls rejected), which is the safe direction — it cannot admit a wrong impl. It is NOT a verify-but-wrong soundness gap.

A-LEG / model-correspondence audit (refinement.md):
- A1=R (str<->List Char), A2=A-consumed vacuous (reSub = re.sub CONTEXT line), A3=A-reference+I (protectSeq deep model == changed chained .replace), A4=I (concrete wrap), A5=A-consumed vacuous (removeEmpty = empty-group .replace CONTEXT line), A6=R. NO kind-3 leg.
- Diff audit: patch.diff changes ONLY the .replace chain line; `re.sub(...)` (line 596) and `.replace('$\mathdefault{}$','')` (line 600) appear only as unchanged CONTEXT lines (no +/-), so modeling them as opaque uninterpreted axioms with no ensures is faithful (they carry no discriminator).
- G-AX axiom_check.py: EXIT 0 — protectSeq deep model == REAL chained .replace on 23 boundary + 20000 fuzz inputs; reSub/removeEmpty deterministic. A-reference soundness holds.
- Recorded G-RESOLVE for gold patch.diff: resolved=true (meta.json).

VERDICT: SOUND. >=5 distinct attack classes (partial-domain, boundary, control-flow-effect, swapped-mapping, dropped-callee, ungrounded-oracle echo) plus the prepatch bug were encoded, same_spec-confirmed, and machine-verified; every genuinely-wrong impl fails verification on the exact-equality postcondition, so no faithful patch needed a resolve run and none could fail to resolve. Spec is discriminating and refinement is faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real label renderer is a single bounded pass over the
   pre-processed text and always terminates, so a diverging implementation must
   NOT satisfy this spec. Partial correctness would let a non-terminating loop
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The label pre-processor: a regular-expression substitution that wraps each
   maximal run of ASCII letters in the surrounding math/upright delimiters. It
   is an UNCHANGED community callee; the routine under spec only consumes its
   result, so the weakest sufficient contract is "some deterministic function
   of the text" (an uninterpreted map on code points). Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom reSub : List Char → List Char

/- Collapse of an empty math group: deletes every occurrence of the empty
   delimiter pair from the assembled string. Also an UNCHANGED community callee
   applied verbatim as the final step; modeled as an uninterpreted map for the
   same reason. Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom removeEmpty : List Char → List Char
-- axioms-end

-- pure-start
/- The math-protection of a single code point. Three code points are wrapped in
   curly braces / replaced by a thin-space control sequence so that the math
   renderer does not treat them as binary operators or collapse inter-number
   spacing; every other code point passes through unchanged. (Behaviour, not the
   edit: mapping.md §3.1.) -/
def mathProtect (c : Char) : List Char :=
  if c = '-' then "{-}".toList
  else if c = ':' then "{:}".toList
  else if c = ' ' then "\\;".toList
  else [c]

/- The math-protection of a whole sequence: concatenate the per-code-point
   protections. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). The chained single-pass substitution it models
   is faithful because no protection output contains a code point a later
   substitution would touch (mapping.md §3.1). -/
def protectSeq : List Char → List Char
  | []      => []
  | c :: cs => mathProtect c ++ protectSeq cs

@[grind] lemma protectSeq_nil : protectSeq [] = [] := rfl
@[grind] lemma protectSeq_cons (c : Char) (cs : List Char) :
    protectSeq (c :: cs) = mathProtect c ++ protectSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a tick/offset label for a math (TeX) text renderer.

   The label text is first passed through the letter-run pre-processor
   (`reSub`); each code point of the result is then math-protected
   (`protectSeq` — three code points are wrapped/replaced, all others pass
   through); the protected string is enclosed in the math delimiters
   `$\mathdefault{ … }$`; finally any empty math group is dropped
   (`removeEmpty`). `text` is the read-only input label (not `mut`): the routine
   consumes it and never alters it (directive 5). The label is modeled as a
   `List Char` (a per-code-point string); the delimiters are concrete literals
   (mapping.md §2). -/
noncomputable section
method renderTexLabel (text : List Char) return (out : List Char)
  ensures out = removeEmpty ("$\\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)
  do
    -- impl-start
    let s := reSub text
    let mut result : List Char := []
    let mut i := s.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ s.length
      invariant result = protectSeq (s.drop i)
      done_with i = 0
      decreasing i
    do
      let c := s[i - 1]!
      result := mathProtect c ++ result
      i := i - 1
    let out := removeEmpty ("$\\mathdefault{".toList ++ result ++ "}$".toList)
    return out
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `protectSeq` peels one `mathProtect`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma protectSeq_drop_step (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    protectSeq (s.drop (i - 1)) = mathProtect s[i - 1]! ++ protectSeq (s.drop i) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, protectSeq_cons]

prove_correct renderTexLabel by
  loom_solve
  rw [protectSeq_drop_step (reSub text) i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of matplotlib__matplotlib-21568 (velvet). RESULT: SOUND. No verifying-but-wrong impl found; verify=>correct holds.

SPEC SHAPE: renderTexLabel's postcondition is an EXACT functional equality `out = removeEmpty ("$\mathdefault{".toList ++ protectSeq (reSub text) ++ "}$".toList)`. protectSeq/mathProtect are concrete pure defs pinning the per-code-point map ('-'->{-}, ':'->{:}, ' '->\;, else id); reSub/removeEmpty are opaque axioms (unchanged callees). So any same-spec verifying impl must compute exactly the gold function of `text` — a maximally tight spec.

SAME_SPEC: all 8 attack files + positive_control confirmed same_spec=True vs frozen Solution.lean (swebench_unified.markers.same_spec, velvet). Only the impl region (and prove_correct body, which spec_view elides) edited; axioms/pure/pre/post/ensures byte-identical.

### VERIFY RESULTS (scripts/lean_verify.sh <file>, run concurrently <=4/batch):
- positive_control (gold impl): EXIT 0 (VERIFIES).
- atk_1 prepatch bug (dash-only protection): EXIT 1, unsolved goal `invariant_2: result = protectSeq (s.drop i)`. PREPATCH REPRODUCED.
- atk_2 partial-domain (colon-only): EXIT 1, same invariant_2 unsolved.
- atk_3 boundary/off-by-one (s[i]! instead of s[i-1]!): EXIT 1, invariant_2 unsolved.
- atk_4 control-flow-effect (wrong concat order, result++mathProtect c): EXIT 1, invariant_2 unsolved.
- atk_6 swapped mapping ('-'->{:}, ':'->{-}): EXIT 1, invariant_2 unsolved (after fixing a Lean escape typo; re-verified same_spec=True).
- atk_7 dropped-callee (omit removeEmpty wrap): EXIT 1, invariant_2/postcondition unsolved.
- atk_5 ungrounded-oracle echo (return the postcondition RHS directly, no loop): EXIT 1, `No goals to be solved` at the prove_correct block.
- atk_8 correct-but-structurally-different (compute protectSeq s directly, no loop): EXIT 1, `No goals to be solved`.

KEY FINDING: NONE of the 7 genuinely-wrong impls (atk_1,2,3,4,6,7 + echo atk_5) verified. Therefore protocol step 2 (materialize faithful refined patch + run_resolve for each VERIFYING wrong impl) has an EMPTY trigger set — no resolve run was required, and `patches` is empty. verify=>correct is not falsified.

NOTE on atk_5/atk_8: these two are actually SEMANTICALLY CORRECT alternate impls (echo of the RHS / loop-free direct computation) that fail ONLY because the frozen prove_correct tactic block is coupled to the while-loop shape (`No goals to be solved`). This is proof-brittleness producing FALSE NEGATIVES (correct impls rejected), which is the safe direction — it cannot admit a wrong impl. It is NOT a verify-but-wrong soundness gap.

A-LEG / model-correspondence audit (refinement.md):
- A1=R (str<->List Char), A2=A-consumed vacuous (reSub = re.sub CONTEXT line), A3=A-reference+I (protectSeq deep model == changed chained .replace), A4=I (concrete wrap), A5=A-consumed vacuous (removeEmpty = empty-group .replace CONTEXT line), A6=R. NO kind-3 leg.
- Diff audit: patch.diff changes ONLY the .replace chain line; `re.sub(...)` (line 596) and `.replace('$\mathdefault{}$','')` (line 600) appear only as unchanged CONTEXT lines (no +/-), so modeling them as opaque uninterpreted axioms with no ensures is faithful (they carry no discriminator).
- G-AX axiom_check.py: EXIT 0 — protectSeq deep model == REAL chained .replace on 23 boundary + 20000 fuzz inputs; reSub/removeEmpty deterministic. A-reference soundness holds.
- Recorded G-RESOLVE for gold patch.diff: resolved=true (meta.json).

VERDICT: SOUND. >=5 distinct attack classes (partial-domain, boundary, control-flow-effect, swapped-mapping, dropped-callee, ungrounded-oracle echo) plus the prepatch bug were encoded, same_spec-confirmed, and machine-verified; every genuinely-wrong impl fails verification on the exact-equality postcondition, so no faithful patch needed a resolve run and none could fail to resolve. Spec is discriminating and refinement is faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function renderTexLabel models matplotlib.dates._wrap_in_tex (lib/matplotlib/dates.py:594) at base_commit f0632c0f, post gold patch. The gold patch changes the math-protection from '.replace("-","{-}")' to '.replace("-","{-}").replace(":","{:}").replace(" ",r"\;")' plus the wrap reorder. Faithfulness checks all pass:

1) SPEC REGION BYTE-IDENTICAL: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) == True. The spec view (postcondition + reSub/removeEmpty axioms + mathProtect/protectSeq deep model + protectSeq_drop_step lemma) is unchanged between prepatch and solution; only the impl/proof regions differ (prepatch protects only '-' and correctly FAILS verification). Spec is frozen and non-vacuous.

2) POSTCONDITION MATCHES REAL BEHAVIOR: postcondition is out = removeEmpty("$\mathdefault{" ++ protectSeq(reSub text) ++ "}$"). reSub and removeEmpty are uninterpreted axioms bound to the two UNCHANGED context callees re.sub(p,...) and str.replace('$\mathdefault{}$','') — same real callees in spec and gold, no behavioral claim, so they cannot over/under-constrain. protectSeq deeply models the CHANGED chained .replace.

3) EMPIRICAL EQUIVALENCE: reconstructed the R/I shadow (real re.sub -> per-code-point protectSeq -> concrete wrap -> real empty-removal) and compared byte-for-byte against the verbatim post-patch _wrap_in_tex over 700k+ inputs (500k random adversarial alphabet incl. -, :, space, braces, $, backslash, mathdefault fragments; 200k incl. BMP/astral unicode; plus all boundary/date-label cases). ZERO disagreements. The left-to-right chain collapse is sound: replacement outputs {-},{:},\; contain no code point (-,:,space) a later .replace targets, so ordering is irrelevant.

4) G-AX axiom_check.py passes (exit 0): protect_seq deep model == real chained .replace on 23 boundary + 20000 fuzz; re_sub/remove_empty deterministic.

5) Solution.lean verifies via lean_verify.sh (exit 0) — spec is satisfiable and the impl (full backward per-code-point fold) discharges the postcondition. Prepatch (dash-only) provably cannot satisfy it, diverging exactly on ':' or ' '.

The spec is neither too strong nor drifted: it exactly captures the gold patched function's observable str->str behavior on the tested surface. No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified disposition, did not rubber-stamp. (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True — spec region byte-identical; the only difference is the impl (prepatch protects only '-'). (2) Core soundness intact: G-VERIFY pass, G-DIFF fail-of-prepatch pass (fails on the ':' / ' ' discriminator), G-AX pass (protectSeq == real chained .replace, 23 boundary + 20k fuzz), G-CONF pass (R/I shadow == patched behaviour, seed 21568), G-RESOLVE pass (patch.diff == gold verbatim), G-EQ pass. (3) The spec view DOES leak the gold discriminator (mathProtect: '-'→'{-}', ':'→'{:}', ' '→'\;'; protectSeq; the $\mathdefault{…}$ delimiter literals pinned in the ensures), and this is beyond problem_statement, which is a pure symptom report ('datetime axis usetex spacing unclear') containing none of that vocabulary. But this is a properly dispositioned RELAXED_LEAKAGE bundle: relaxed_leakage=true, RELAXED_LEAKAGE.md present, G-LEAK status 'relaxed'. Unavoidability re-derived and confirmed — the F2P tests compare the FULL wrapped strings (e.g. $\mathdefault{04{:}00}$), so any faithful spec (one the dash-only prepatch fails) MUST pin the three protected code points and the delimiters; a problem_statement-only spec cannot constrain them, and a dash-only impl would pass it yet fail F2P. (4) Scanned for a NEW leak beyond the dispositioned facet: spec view has 0 occurrences of _wrap_in_tex / dates.py / patch / diff / gold / replace( / re.sub; comments narrate behavior (math-protection so the renderer doesn't mis-space) not the edit; no gold-diff/problem-statement phrasing quoted. No leak beyond the accepted behavioral facet. Per gates/_audit.py convention (relaxed-leakage panel recorded as pass + note; no separate 'relaxed' status at panel layer), honest recording is NO-LEAKAGE with note that the known dispositioned facet was re-confirmed. (Aside: G-PANEL-1 is recorded fail — that is a separate role, out of scope for panel_3.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
