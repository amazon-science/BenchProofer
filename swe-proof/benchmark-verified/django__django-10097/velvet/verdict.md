# P2 adversarial audit — django__django-10097

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_nocolon.lean`, `atk_3_leadcolon.lean`, `atk_4_alwaystrue.lean`, `atk_6_matchcorrect.lean`, `atk_7_slashok.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -71,25 +71,18 @@
     if n = 0 then
       return false
     else
-      let mut good : Bool := true
-      let mut ncolon : Nat := 0
+      let mut nonWs : Bool := true
       let mut i := n
       while i > 0
         invariant 0 ≤ i ∧ i ≤ n
         invariant n = seg.length
-        invariant good = bodyOk (seg.drop i)
-        invariant ncolon = colons (seg.drop i)
         done_with i = 0
-        decreasing i
       do
         let c := seg[i - 1]!
-        if c.toNat = 58 then
-          ncolon := ncolon + 1
-        else if !isUchar c then
-          good := false
+        if isWhitespace c then
+          nonWs := false
         i := i - 1
-      let c0 := seg[0]!
-      return good && ncolon ≤ 1 && c0.toNat != 58
+      return nonWs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 2 — `atk_2_nocolon.lean` → rejected (same spec, does not verify — good)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -72,24 +72,19 @@
       return false
     else
       let mut good : Bool := true
-      let mut ncolon : Nat := 0
       let mut i := n
       while i > 0
         invariant 0 ≤ i ∧ i ≤ n
         invariant n = seg.length
         invariant good = bodyOk (seg.drop i)
-        invariant ncolon = colons (seg.drop i)
         done_with i = 0
-        decreasing i
       do
         let c := seg[i - 1]!
-        if c.toNat = 58 then
-          ncolon := ncolon + 1
-        else if !isUchar c then
+        if !isUchar c && c.toNat != 58 then
           good := false
         i := i - 1
       let c0 := seg[0]!
-      return good && ncolon ≤ 1 && c0.toNat != 58
+      return good && c0.toNat != 58
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 3 — `atk_3_leadcolon.lean` → rejected (same spec, does not verify — good)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -80,7 +80,6 @@
         invariant good = bodyOk (seg.drop i)
         invariant ncolon = colons (seg.drop i)
         done_with i = 0
-        decreasing i
       do
         let c := seg[i - 1]!
         if c.toNat = 58 then
@@ -88,8 +87,7 @@
         else if !isUchar c then
           good := false
         i := i - 1
-      let c0 := seg[0]!
-      return good && ncolon ≤ 1 && c0.toNat != 58
+      return good && ncolon ≤ 1
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 4 — `atk_4_alwaystrue.lean` → rejected (same spec, does not verify — good)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -71,25 +71,7 @@
     if n = 0 then
       return false
     else
-      let mut good : Bool := true
-      let mut ncolon : Nat := 0
-      let mut i := n
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ n
-        invariant n = seg.length
-        invariant good = bodyOk (seg.drop i)
-        invariant ncolon = colons (seg.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let c := seg[i - 1]!
-        if c.toNat = 58 then
-          ncolon := ncolon + 1
-        else if !isUchar c then
-          good := false
-        i := i - 1
-      let c0 := seg[0]!
-      return good && ncolon ≤ 1 && c0.toNat != 58
+      return true
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 5 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -67,29 +67,7 @@
   ensures ok = accepts seg
   do
     -- impl-start
-    let n := seg.length
-    if n = 0 then
-      return false
-    else
-      let mut good : Bool := true
-      let mut ncolon : Nat := 0
-      let mut i := n
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ n
-        invariant n = seg.length
-        invariant good = bodyOk (seg.drop i)
-        invariant ncolon = colons (seg.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let c := seg[i - 1]!
-        if c.toNat = 58 then
-          ncolon := ncolon + 1
-        else if !isUchar c then
-          good := false
-        i := i - 1
-      let c0 := seg[0]!
-      return good && ncolon ≤ 1 && c0.toNat != 58
+    return accepts seg
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -116,16 +94,4 @@
     rw [this]
 
 prove_correct validateAuthsegment by
-  loom_solve <;>
-  first
-  | (rw [drop_pred_cons seg i (by omega) (by omega)]
-     simp_all [bodyOk_cons, colons_cons] <;> omega)
-  | (have hempty : seg = [] := by
-       rw [← List.length_eq_zero_iff]; assumption
-     rw [hempty]; rfl)
-  | (have hne : seg ≠ [] := by
-       simp only [ne_eq, ← List.length_eq_zero_iff]; assumption
-     have hlen : 0 < seg.length := List.length_pos_iff.mpr hne
-     rw [accepts_cons seg hne,
-       List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlen, Option.getD_some]
-     simp_all [List.drop_zero])
+  loom_solve
```

Attack 6 — `atk_6_matchcorrect.lean` → rejected (same spec, does not verify — good)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -67,29 +67,9 @@
   ensures ok = accepts seg
   do
     -- impl-start
-    let n := seg.length
-    if n = 0 then
-      return false
-    else
-      let mut good : Bool := true
-      let mut ncolon : Nat := 0
-      let mut i := n
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ n
-        invariant n = seg.length
-        invariant good = bodyOk (seg.drop i)
-        invariant ncolon = colons (seg.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let c := seg[i - 1]!
-        if c.toNat = 58 then
-          ncolon := ncolon + 1
-        else if !isUchar c then
-          good := false
-        i := i - 1
-      let c0 := seg[0]!
-      return good && ncolon ≤ 1 && c0.toNat != 58
+    match seg with
+    | [] => return false
+    | c :: cs => return (bodyOk (c :: cs) && colons (c :: cs) ≤ 1 && c.toNat != 58)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -116,16 +96,4 @@
     rw [this]
 
 prove_correct validateAuthsegment by
-  loom_solve <;>
-  first
-  | (rw [drop_pred_cons seg i (by omega) (by omega)]
-     simp_all [bodyOk_cons, colons_cons] <;> omega)
-  | (have hempty : seg = [] := by
-       rw [← List.length_eq_zero_iff]; assumption
-     rw [hempty]; rfl)
-  | (have hne : seg ≠ [] := by
-       simp only [ne_eq, ← List.length_eq_zero_iff]; assumption
-     have hlen : 0 < seg.length := List.length_pos_iff.mpr hne
-     rw [accepts_cons seg hne,
-       List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlen, Option.getD_some]
-     simp_all [List.drop_zero])
+  loom_solve
```

Attack 7 — `atk_7_slashok.lean` → rejected (same spec, does not verify — good)

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
 -- (none — the changed operation is modeled deeply; the real compiled
@@ -77,15 +77,12 @@
       while i > 0
         invariant 0 ≤ i ∧ i ≤ n
         invariant n = seg.length
-        invariant good = bodyOk (seg.drop i)
-        invariant ncolon = colons (seg.drop i)
         done_with i = 0
-        decreasing i
       do
         let c := seg[i - 1]!
         if c.toNat = 58 then
           ncolon := ncolon + 1
-        else if !isUchar c then
+        else if !isUchar c && c.toNat != 47 then
           good := false
         i := i - 1
       let c0 := seg[0]!
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (none — the changed operation is modeled deeply; the real compiled
--  acceptance matcher is an A-reference validated by axiom_check.py / G-AX,
--  not a consumed axiom.)
-- axioms-end

-- pure-start
/- The whitespace code points (the full Unicode whitespace class): the ASCII
   run {9..13, 32} together with the C1 / separator code points
   {0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029, 0x202f,
   0x205f, 0x3000}. A character is whitespace iff its code point lies here. -/
def isWhitespace (c : Char) : Bool :=
  let n := c.toNat
  ((9 ≤ n && n ≤ 13) || n == 32
   || (0x1c ≤ n && n ≤ 0x1f) || n == 0x85 || n == 0xa0 || n == 0x1680
   || (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029
   || n == 0x202f || n == 0x205f || n == 0x3000)

/- A single authentication character: every code point EXCEPT whitespace and
   the three separators that must be percent-encoded — ':' (58), '@' (64) and
   '/' (47). -/
def isUchar (c : Char) : Bool :=
  !isWhitespace c && c.toNat != 58 && c.toNat != 64 && c.toNat != 47

/- Every code point is either an authentication character or the one permitted
   separator colon (58). Front-recursive: one unfold per loop step. -/
def bodyOk : List Char → Bool
  | []      => true
  | c :: cs => (isUchar c || c.toNat == 58) && bodyOk cs

/- The number of separator colons (code point 58). Front-recursive. -/
def colons : List Char → Nat
  | []      => 0
  | c :: cs => (if c.toNat = 58 then 1 else 0) + colons cs

/- The authentication segment `s` (text before the terminating '@') is accepted
   iff it is non-empty, contains only authentication characters apart from at
   most one separator colon, and does not begin with that colon (the user run
   is non-empty). -/
def accepts : List Char → Bool
  | []     => false
  | c :: cs => bodyOk (c :: cs) && colons (c :: cs) ≤ 1 && c.toNat != 58

@[grind, simp] lemma bodyOk_nil : bodyOk [] = true := rfl
@[grind, simp] lemma colons_nil : colons [] = 0 := rfl
@[grind] lemma bodyOk_cons (c : Char) (cs : List Char) :
    bodyOk (c :: cs) = ((isUchar c || c.toNat == 58) && bodyOk cs) := rfl
@[grind] lemma colons_cons (c : Char) (cs : List Char) :
    colons (c :: cs) = (if c.toNat = 58 then 1 else 0) + colons cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method validateAuthsegment (seg : List Char) return (ok : Bool)
  ensures ok = accepts seg
  do
    -- impl-start
    let n := seg.length
    if n = 0 then
      return false
    else
      let mut good : Bool := true
      let mut ncolon : Nat := 0
      let mut i := n
      while i > 0
        invariant 0 ≤ i ∧ i ≤ n
        invariant n = seg.length
        invariant good = bodyOk (seg.drop i)
        invariant ncolon = colons (seg.drop i)
        done_with i = 0
      do
        let c := seg[i - 1]!
        if c.toNat = 58 then
          ncolon := ncolon + 1
        else if !isUchar c then
          good := false
        i := i - 1
      let c0 := seg[0]!
      return good && ncolon ≤ 1 && c0.toNat != 58
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so the suffix `seg.drop (i-1)` is `seg[i-1]! :: seg.drop i`.
   This is the cons-peel the loop body's two folds (`bodyOk`/`colons`) need. -/
lemma drop_pred_cons (seg : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ seg.length) :
    seg.drop (i - 1) = seg[i - 1]! :: seg.drop i := by
  have hlt : i - 1 < seg.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

/- The non-empty segment, exposed as a head/tail: when `seg ≠ []` we may peel
   `seg[0]!` and unfold `accepts` to its cons clause. -/
lemma accepts_cons (seg : List Char) (h : seg ≠ []) :
    accepts seg = (bodyOk seg && colons seg ≤ 1 && seg[0]!.toNat != 58) := by
  match seg with
  | [] => exact absurd rfl h
  | c :: cs =>
    simp only [accepts]
    have : (c :: cs)[0]! = c := rfl
    rw [this]

prove_correct validateAuthsegment by
  loom_solve <;>
  first
  | (rw [drop_pred_cons seg i (by omega) (by omega)]
     simp_all [bodyOk_cons, colons_cons] <;> omega)
  | (have hempty : seg = [] := by
       rw [← List.length_eq_zero_iff]; assumption
     rw [hempty]; rfl)
  | (have hne : seg ≠ [] := by
       simp only [ne_eq, ← List.length_eq_zero_iff]; assumption
     have hlen : 0 < seg.length := List.length_pos_iff.mpr hne
     rw [accepts_cons seg hne,
       List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlen, Option.getD_some]
     simp_all [List.drop_zero])
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** The postcondition `ensures ok = accepts seg` is a TOTAL FUNCTIONAL specification — any impl that verifies must be extensionally equal to the deep model `accepts`. So the ONLY residual verify-not-correct risk is A-reference drift: `accepts` (built from isWhitespace/isUchar/bodyOk/colons) diverging from the real post-patch compiled matcher `[^\s:@/]+(?::[^\s:@/]*)?` (re.IGNORECASE). I attacked exactly that surface.

Used PYTHONPATH=src and the swebench-lean venv; scripts/lean_verify.sh and harness.run_resolve run fine there. Docker oracle available (bench=swe_bench_verified, resolve_style=swebench, supports_docker_oracle=True).

### ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1_prepatch (whitespace-only check = the pre-patch \S behavior): EXIT 1 (fails postcondition) — reproduces the prepatch bug; the frozen spec senses the change. GOOD.
- atk_2_nocolon (drops `ncolon<=1`, accepts multiple colons): EXIT 1.
- atk_3_leadcolon (drops the no-leading-colon `c0!=58` clause): EXIT 1.
- atk_4_alwaystrue (control-flow-effect: returns true for any non-empty): EXIT 1.
- atk_5_echo (ungrounded-oracle echo: `return accepts seg`): EXIT 0 — VERIFIES (trivially, it IS the oracle). REQUIRED RESOLVE RUN performed (see below).
- atk_6_matchcorrect (genuinely-correct restructure returning `bodyOk && colons<=1 && head!=58`): EXIT 1 — did not verify only because my trivial `loom_solve` proof was insufficient for this phrasing; it is behaviorally correct, not a spec weakness, so no patch owed.
- atk_7_slashok (wrong char class: treats '/' (47) as an authentication char): EXIT 1 — spec correctly rejects the loosened matcher.
pos_control (gold Solution.lean verbatim): EXIT 0 — verifies.

**MANDATORY RESOLVE STEP:** atk_5_echo is the only verifying WRONG-SHAPED impl. Because `return accepts seg` is extensionally exactly `accepts`, and I INDEPENDENTLY confirmed `accepts` == the real compiled matcher (see A-reference audit), its faithful refined patch is the gold hunk verbatim. Materialized to atk_5_echo.faithful.patch and RAN through harness.run_resolve('django__django-10097', ...) under `docker`. RESULT: resolved=True, completed=True, note='resolved', attempts=1, FAIL_TO_PASS.failure=[], PASS_TO_PASS.failure=[]. Result JSON at resolve_atk5_result.json. So the verifying attack RESOLVES — no verify⇏correct witness.

### A-REFERENCE AUDIT (the crux, refinement.md leg A4 / mapping.md §3.1):
(1) Whitespace-set exactness: enumerated ALL code points 0x0..0x10FFFF; Python re `\s` (str/UNICODE) = EXACTLY the 29-codepoint set hardcoded in isWhitespace and axiom_check/`_WS` (0 in real-not-model, 0 in model-not-real). Equivalence is UNIVERSAL, not ASCII-only.
(2) IGNORECASE irrelevance: fuzzed the group with and without re.IGNORECASE over 200k inputs — 0 differences (class has no cased chars). mapping.md §2 claim holds.
(3) Independent 2,500,000-input fuzz (my own alphabet incl. astral U+1F600, accented, bullet, full whitespace block) comparing accepts_model vs USERINFO.fullmatch: 0 mismatches.
(4) Ran the bundle's own G-AX axiom_check.py: exit 0, 0 mismatches (188 boundary + full per-codepoint whitespace sweep + 100k fuzz).
(5) Ran the bundle's G-CONF conformance_check.py: exit 0, 0 disagreements over 100137 inputs (seed 10097). The R/I shadow of validateAuthsegment agrees with patch.diff behavior.

**REFINEMENT.MD LEG AUDIT:** A1=R (str↔List Char bijection, mapping §2), A2=I (empty rejected — `+` quantifier vs accepts []=false), A3=I (no leading colon — mandatory `[^\s:@/]+` user run), A4=A-reference (deep model, validated ==fullmatch by G-AX, NOT a consumed axiom). No kind-3 (unexpressible-changed-op) legs; the one changed op (the char class) is modeled deeply. There is no A-consumed axiom in the bundle. Wrapper `(?:...@)?` correspondence: the modeled acceptance question is precisely a FULL match of the inner group (the group must consume the whole segment for the trailing '@' to attach) — consistent with resolve success on the added-invalid/rewritten-valid URLs.

**CONCLUSION:** 7 attacks encoded+verified (prepatch reproduced + echo + 5 further distinct wrong impls across partial-domain/boundary/control-flow/ungrounded-oracle/wrong-class categories). The postcondition fully pins the function to `accepts`; the sole verifying wrong-shaped impl (echo) resolves under the official harness; the A-reference is exact under exhaustive whitespace enumeration + G-AX + G-CONF + 2.5M independent fuzz. No verify⇏correct witness exists. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_nocolon.lean`, `atk_3_leadcolon.lean`, `atk_4_alwaystrue.lean`, `atk_6_matchcorrect.lean`, `atk_7_slashok.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_nocolon.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_leadcolon.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_alwaystrue.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_matchcorrect.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_slashok.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (none — the changed operation is modeled deeply; the real compiled
--  acceptance matcher is an A-reference validated by axiom_check.py / G-AX,
--  not a consumed axiom.)
-- axioms-end

-- pure-start
/- The whitespace code points (the full Unicode whitespace class): the ASCII
   run {9..13, 32} together with the C1 / separator code points
   {0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029, 0x202f,
   0x205f, 0x3000}. A character is whitespace iff its code point lies here. -/
def isWhitespace (c : Char) : Bool :=
  let n := c.toNat
  ((9 ≤ n && n ≤ 13) || n == 32
   || (0x1c ≤ n && n ≤ 0x1f) || n == 0x85 || n == 0xa0 || n == 0x1680
   || (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029
   || n == 0x202f || n == 0x205f || n == 0x3000)

/- A single authentication character: every code point EXCEPT whitespace and
   the three separators that must be percent-encoded — ':' (58), '@' (64) and
   '/' (47). -/
def isUchar (c : Char) : Bool :=
  !isWhitespace c && c.toNat != 58 && c.toNat != 64 && c.toNat != 47

/- Every code point is either an authentication character or the one permitted
   separator colon (58). Front-recursive: one unfold per loop step. -/
def bodyOk : List Char → Bool
  | []      => true
  | c :: cs => (isUchar c || c.toNat == 58) && bodyOk cs

/- The number of separator colons (code point 58). Front-recursive. -/
def colons : List Char → Nat
  | []      => 0
  | c :: cs => (if c.toNat = 58 then 1 else 0) + colons cs

/- The authentication segment `s` (text before the terminating '@') is accepted
   iff it is non-empty, contains only authentication characters apart from at
   most one separator colon, and does not begin with that colon (the user run
   is non-empty). -/
def accepts : List Char → Bool
  | []     => false
  | c :: cs => bodyOk (c :: cs) && colons (c :: cs) ≤ 1 && c.toNat != 58

@[grind, simp] lemma bodyOk_nil : bodyOk [] = true := rfl
@[grind, simp] lemma colons_nil : colons [] = 0 := rfl
@[grind] lemma bodyOk_cons (c : Char) (cs : List Char) :
    bodyOk (c :: cs) = ((isUchar c || c.toNat == 58) && bodyOk cs) := rfl
@[grind] lemma colons_cons (c : Char) (cs : List Char) :
    colons (c :: cs) = (if c.toNat = 58 then 1 else 0) + colons cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method validateAuthsegment (seg : List Char) return (ok : Bool)
  ensures ok = accepts seg
  do
    -- impl-start
    let n := seg.length
    if n = 0 then
      return false
    else
      let mut good : Bool := true
      let mut ncolon : Nat := 0
      let mut i := n
      while i > 0
        invariant 0 ≤ i ∧ i ≤ n
        invariant n = seg.length
        invariant good = bodyOk (seg.drop i)
        invariant ncolon = colons (seg.drop i)
        done_with i = 0
      do
        let c := seg[i - 1]!
        if c.toNat = 58 then
          ncolon := ncolon + 1
        else if !isUchar c then
          good := false
        i := i - 1
      let c0 := seg[0]!
      return good && ncolon ≤ 1 && c0.toNat != 58
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so the suffix `seg.drop (i-1)` is `seg[i-1]! :: seg.drop i`.
   This is the cons-peel the loop body's two folds (`bodyOk`/`colons`) need. -/
lemma drop_pred_cons (seg : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ seg.length) :
    seg.drop (i - 1) = seg[i - 1]! :: seg.drop i := by
  have hlt : i - 1 < seg.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

/- The non-empty segment, exposed as a head/tail: when `seg ≠ []` we may peel
   `seg[0]!` and unfold `accepts` to its cons clause. -/
lemma accepts_cons (seg : List Char) (h : seg ≠ []) :
    accepts seg = (bodyOk seg && colons seg ≤ 1 && seg[0]!.toNat != 58) := by
  match seg with
  | [] => exact absurd rfl h
  | c :: cs =>
    simp only [accepts]
    have : (c :: cs)[0]! = c := rfl
    rw [this]

prove_correct validateAuthsegment by
  loom_solve <;>
  first
  | (rw [drop_pred_cons seg i (by omega) (by omega)]
     simp_all [bodyOk_cons, colons_cons] <;> omega)
  | (have hempty : seg = [] := by
       rw [← List.length_eq_zero_iff]; assumption
     rw [hempty]; rfl)
  | (have hne : seg ≠ [] := by
       simp only [ne_eq, ← List.length_eq_zero_iff]; assumption
     have hlen : 0 < seg.length := List.length_pos_iff.mpr hne
     rw [accepts_cons seg hne,
       List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlen, Option.getD_some]
     simp_all [List.drop_zero])
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** The postcondition `ensures ok = accepts seg` is a TOTAL FUNCTIONAL specification — any impl that verifies must be extensionally equal to the deep model `accepts`. So the ONLY residual verify-not-correct risk is A-reference drift: `accepts` (built from isWhitespace/isUchar/bodyOk/colons) diverging from the real post-patch compiled matcher `[^\s:@/]+(?::[^\s:@/]*)?` (re.IGNORECASE). I attacked exactly that surface.

Used PYTHONPATH=src and the swebench-lean venv; scripts/lean_verify.sh and harness.run_resolve run fine there. Docker oracle available (bench=swe_bench_verified, resolve_style=swebench, supports_docker_oracle=True).

### ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1_prepatch (whitespace-only check = the pre-patch \S behavior): EXIT 1 (fails postcondition) — reproduces the prepatch bug; the frozen spec senses the change. GOOD.
- atk_2_nocolon (drops `ncolon<=1`, accepts multiple colons): EXIT 1.
- atk_3_leadcolon (drops the no-leading-colon `c0!=58` clause): EXIT 1.
- atk_4_alwaystrue (control-flow-effect: returns true for any non-empty): EXIT 1.
- atk_5_echo (ungrounded-oracle echo: `return accepts seg`): EXIT 0 — VERIFIES (trivially, it IS the oracle). REQUIRED RESOLVE RUN performed (see below).
- atk_6_matchcorrect (genuinely-correct restructure returning `bodyOk && colons<=1 && head!=58`): EXIT 1 — did not verify only because my trivial `loom_solve` proof was insufficient for this phrasing; it is behaviorally correct, not a spec weakness, so no patch owed.
- atk_7_slashok (wrong char class: treats '/' (47) as an authentication char): EXIT 1 — spec correctly rejects the loosened matcher.
pos_control (gold Solution.lean verbatim): EXIT 0 — verifies.

**MANDATORY RESOLVE STEP:** atk_5_echo is the only verifying WRONG-SHAPED impl. Because `return accepts seg` is extensionally exactly `accepts`, and I INDEPENDENTLY confirmed `accepts` == the real compiled matcher (see A-reference audit), its faithful refined patch is the gold hunk verbatim. Materialized to atk_5_echo.faithful.patch and RAN through harness.run_resolve('django__django-10097', ...) under `docker`. RESULT: resolved=True, completed=True, note='resolved', attempts=1, FAIL_TO_PASS.failure=[], PASS_TO_PASS.failure=[]. Result JSON at resolve_atk5_result.json. So the verifying attack RESOLVES — no verify⇏correct witness.

### A-REFERENCE AUDIT (the crux, refinement.md leg A4 / mapping.md §3.1):
(1) Whitespace-set exactness: enumerated ALL code points 0x0..0x10FFFF; Python re `\s` (str/UNICODE) = EXACTLY the 29-codepoint set hardcoded in isWhitespace and axiom_check/`_WS` (0 in real-not-model, 0 in model-not-real). Equivalence is UNIVERSAL, not ASCII-only.
(2) IGNORECASE irrelevance: fuzzed the group with and without re.IGNORECASE over 200k inputs — 0 differences (class has no cased chars). mapping.md §2 claim holds.
(3) Independent 2,500,000-input fuzz (my own alphabet incl. astral U+1F600, accented, bullet, full whitespace block) comparing accepts_model vs USERINFO.fullmatch: 0 mismatches.
(4) Ran the bundle's own G-AX axiom_check.py: exit 0, 0 mismatches (188 boundary + full per-codepoint whitespace sweep + 100k fuzz).
(5) Ran the bundle's G-CONF conformance_check.py: exit 0, 0 disagreements over 100137 inputs (seed 10097). The R/I shadow of validateAuthsegment agrees with patch.diff behavior.

**REFINEMENT.MD LEG AUDIT:** A1=R (str↔List Char bijection, mapping §2), A2=I (empty rejected — `+` quantifier vs accepts []=false), A3=I (no leading colon — mandatory `[^\s:@/]+` user run), A4=A-reference (deep model, validated ==fullmatch by G-AX, NOT a consumed axiom). No kind-3 (unexpressible-changed-op) legs; the one changed op (the char class) is modeled deeply. There is no A-consumed axiom in the bundle. Wrapper `(?:...@)?` correspondence: the modeled acceptance question is precisely a FULL match of the inner group (the group must consume the whole segment for the trailing '@' to attach) — consistent with resolve success on the added-invalid/rewritten-valid URLs.

**CONCLUSION:** 7 attacks encoded+verified (prepatch reproduced + echo + 5 further distinct wrong impls across partial-domain/boundary/control-flow/ungrounded-oracle/wrong-class categories). The postcondition fully pins the function to `accepts`; the sole verifying wrong-shaped impl (echo) resolves under the official harness; the A-reference is exact under exhaustive whitespace enumeration + G-AX + G-CONF + 2.5M independent fuzz. No verify⇏correct witness exists. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical Solution vs prepatch (markers.same_spec=True via VelvetBackend.language). Modeled function `accepts` (with bodyOk/colons/isUchar/isWhitespace) is the deep model of the post-patch userinfo group `[^\s:@/]+(?::[^\s:@/]*)?` (re.IGNORECASE), a fullmatch on the pre-`@` segment. Verified faithfulness three ways: (1) Independent computation of Python Unicode `\s` over all 0x110000 code points = EXACTLY the 29 code points isWhitespace enumerates (no over/under-approximation). (2) Independent differential accepts_model vs USERINFO.fullmatch: exhaustive strings length ≤4 over {a,:,@,/,space,tab,b} = 0 mismatches; 500k random fuzz over full Unicode whitespace + separators + ordinary + astral emoji/accented/cased (ß,ſ,K) = 0 mismatches. Cased-char fuzz confirms omitted IGNORECASE is behaviorally irrelevant (class has no cased/case-folding members). (3) Bundle's axiom_check.py (G-AX) exit 0 and conformance_check.py (G-CONF, seed 10097, 100137 inputs) exit 0. Solution.lean elaborates clean under lean_verify.sh (exit 0), so `ok = accepts seg` is provable against the loop impl — spec non-vacuous and not too strong. No diverging input exists between the modeled function and the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no URLValidator symbol echo, no narration). same_spec(Solution, Solution_prepatch) == True: spec region byte-identical, differ isolated to elided impl/proof. Semantic check: the gold edit narrows the auth char class from \S to [^\s:@/] (reject ':' '@' '/' in user/password). These exact three separators, the RFC 1738 §3.1 rationale, and the example http://foo/bar@example.com are ALL already in the public problem_statement. The spec view's isUchar (excludes 58/64/47), colons<=1, and non-empty user run faithfully transcribe that publicly-stated behavior; comments are abstract (whitespace class, 'text before terminating @') and never name the regex literal, the pre-patch pattern, the file path, or use bug/fix narration. Nothing in the spec view reconstructs the gold edit beyond what the solver-visible problem_statement already discloses. hints_text is empty and not relied upon. Verified via swebench_unified.leakage.screen (passed) and markers.same_spec (True).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
