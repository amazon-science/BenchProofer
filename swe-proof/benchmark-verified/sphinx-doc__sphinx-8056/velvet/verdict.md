# P2 adversarial audit — sphinx-doc__sphinx-8056

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed callee contracts. The two community string operations this module
@@ -108,10 +108,11 @@
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
-      result := expandOne multiple f ++ result
+      let kept : List Field :=
+        if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else []
+      result := kept ++ result
       i := i - 1
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
 /- No consumed callee contracts. The two community string operations this module
@@ -108,10 +108,9 @@
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
-      result := expandOne multiple f ++ result
+      result := expandOne false f ++ result
       i := i - 1
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
 /- No consumed callee contracts. The two community string operations this module
@@ -108,10 +108,14 @@
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
-      result := expandOne multiple f ++ result
+      let contrib : List Field :=
+        if multiple ∧ f.name ≠ [] then
+          (splitOnComma f.name).map (fun nm => { f with name := nm })
+        else
+          if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else []
+      result := contrib ++ result
       i := i - 1
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
 /- No consumed callee contracts. The two community string operations this module
@@ -104,11 +104,10 @@
     -- impl-start
     let mut result : List Field := []
     let mut i := raw.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
       result := expandOne multiple f ++ result
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
 /- No consumed callee contracts. The two community string operations this module
@@ -108,10 +108,9 @@
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
-      result := expandOne multiple f ++ result
+      result := result ++ expandOne multiple f
       i := i - 1
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
 /- No consumed callee contracts. The two community string operations this module
@@ -108,10 +108,9 @@
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
-      result := expandOne multiple f ++ result
+      result := [f] ++ result
       i := i - 1
     return result
     -- impl-end
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
 /- No consumed callee contracts. The two community string operations this module
@@ -102,18 +102,7 @@
   ensures out = expandFields multiple raw
   do
     -- impl-start
-    let mut result : List Field := []
-    let mut i := raw.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ raw.length
-      invariant result = expandFields multiple (raw.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := raw[i - 1]!
-      result := expandOne multiple f ++ result
-      i := i - 1
-    return result
+    return expandFields multiple raw
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -133,8 +122,6 @@
 
 prove_correct splitSharedNameFields by
   loom_solve
-  rw [expandFields_drop_step multiple raw i (by omega) (by omega)]
-  simp_all
 
 /- Produce the field sequence for a parameter section, given an abstract Boolean
    `splitNames` selecting whether a single declaration that lists several
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
 /- No consumed callee contracts. The two community string operations this module
@@ -108,7 +108,6 @@
       invariant 0 ≤ i ∧ i ≤ raw.length
       invariant result = expandFields multiple (raw.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := raw[i - 1]!
       result := expandOne multiple f ++ result
@@ -146,8 +145,7 @@
   ensures out = expandFields splitNames raw
   do
     -- impl-start
-    let fields ← splitSharedNameFields splitNames raw
-    return fields
+    return raw
     -- impl-end
 
 prove_correct buildParameterFieldSeq by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed callee contracts. The two community string operations this module
   leans on — splitting a name on the comma separator and trimming surrounding
   whitespace from a name fragment — are modeled DEEPLY in the `pure` region
   (`splitOnComma`, `stripWs`) and validated equal to their standard-library
   counterparts by axiom_check.py (G-AX, A-reference). The sequence of raw
   fields the section scanner yields is taken as a FREE INPUT (`raw`), so the
   spec makes no behavioural claim about the unchanged scanner, and there is no
   module-level `axiom` whose `ensures` the proof consumes. -/
-- axioms-end

-- pure-start
/- One documented field: a name fragment, a type fragment, and the description
   lines that accompany it. Names and types are sequences of code points; the
   description is a sequence of lines (each itself a sequence of code points). -/
structure Field where
  name : List Char
  typ  : List Char
  desc : List (List Char)
deriving DecidableEq, Inhabited

/- The whitespace code points trimmed from the ends of a name fragment: exactly
   the code points the standard-library no-argument trim treats as whitespace —
   the ASCII whitespace, the FS/GS/RS/US separator controls, next-line, the
   no-break space, and the Unicode space/line/paragraph separators. -/
def isWs (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c = '\r' || c = '\x0b' || c = '\x0c' ||
  (0x1c ≤ c.val && c.val ≤ 0x1f) ||        -- file/group/record/unit separators
  c.val = 0x85 ||                          -- next line (NEL)
  c.val = 0xa0 ||                          -- no-break space
  c.val = 0x1680 ||                        -- ogham space mark
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||    -- en quad .. hair space
  c.val = 0x2028 || c.val = 0x2029 ||      -- line / paragraph separator
  c.val = 0x202f || c.val = 0x205f ||      -- narrow no-break / math space
  c.val = 0x3000                           -- ideographic space

/- Trim leading and trailing whitespace from a fragment (the ends only; interior
   whitespace is preserved). A deep model of the standard-library trim
   (mapping.md §3.2, A-reference). -/
def stripWs (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/- Split a fragment on the comma separator into its pieces, in order, keeping
   every piece (including empty ones between adjacent separators and at the
   ends). A string with no comma yields a single piece equal to the whole
   string. A deep model of the standard-library single-character split
   (mapping.md §3.1, A-reference). -/
def splitOnComma : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    if c = ',' then [] :: splitOnComma cs
    else
      match splitOnComma cs with
      | []      => [[c]]
      | g :: gs => (c :: g) :: gs

/- The fields a single raw field contributes, given whether comma-separated
   names should each become their own field:
   - when expansion is requested AND the name is non-empty, every comma-piece of
     the name, trimmed, becomes its own field carrying the SHARED type and
     description;
   - otherwise the raw field is kept verbatim, but only when it carries some
     content (a name, a type, or a description); an entirely empty raw field is
     dropped. -/
def expandOne (multiple : Bool) (f : Field) : List Field :=
  if multiple ∧ f.name ≠ [] then
    (splitOnComma f.name).map (fun nm => { f with name := stripWs nm })
  else
    if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else []

/- The full output field sequence: each raw field expanded and the results
   concatenated, in order. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern, plan §5.4). -/
def expandFields (multiple : Bool) : List Field → List Field
  | []      => []
  | f :: fs => expandOne multiple f ++ expandFields multiple fs

@[grind] lemma expandFields_nil (m : Bool) : expandFields m [] = [] := rfl
@[grind] lemma expandFields_cons (m : Bool) (f : Field) (fs : List Field) :
    expandFields m (f :: fs) = expandOne m f ++ expandFields m fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the documented field sequence, optionally letting a single declaration
   that lists several comma-separated names become one field per name. `multiple`
   and `raw` are read-only (not `mut`); nothing handed in is mutated
   (directive 5). The result is the per-field expansion `expandFields`. -/
method splitSharedNameFields (multiple : Bool) (raw : List Field) return (out : List Field)
  ensures out = expandFields multiple raw
  do
    -- impl-start
    let mut result : List Field := []
    let mut i := raw.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ raw.length
      invariant result = expandFields multiple (raw.drop i)
      done_with i = 0
    do
      let f := raw[i - 1]!
      result := expandOne multiple f ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expandFields` peels one `expandOne`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma expandFields_drop_step (multiple : Bool) (raw : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ raw.length) :
    expandFields multiple (raw.drop (i - 1))
      = expandOne multiple raw[i - 1]! ++ expandFields multiple (raw.drop i) := by
  have hlt : i - 1 < raw.length := by omega
  have hcons : raw.drop (i - 1) = raw[i - 1]! :: raw.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expandFields_cons]

prove_correct splitSharedNameFields by
  loom_solve
  rw [expandFields_drop_step multiple raw i (by omega) (by omega)]
  simp_all

/- Produce the field sequence for a parameter section, given an abstract Boolean
   `splitNames` selecting whether a single declaration that lists several
   comma-separated names should become one field per name. The downstream
   renderer is an unchanged function of this field sequence (mapping.md §3.3), so
   the field sequence is the behaviour pinned here. `splitNames` and `raw` are
   read-only (directive 5). -/
method buildParameterFieldSeq (splitNames : Bool) (raw : List Field) return (out : List Field)
  ensures out = expandFields splitNames raw
  do
    -- impl-start
    let fields ← splitSharedNameFields splitNames raw
    return fields
    -- impl-end

prove_correct buildParameterFieldSeq by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sphinx-doc__sphinx-8056 (velvet). Spec is an EXACT functional equality: `ensures out = expandFields multiple raw` (and the buildParameterFieldSeq caller `out = expandFields splitNames raw`). This is the tightest possible spec shape — a wrong impl cannot verify because it would require proving a false equality. All 8 attacks + positive control confirmed same_spec=True (swebench_unified.markers.same_spec via velvet backend); only impl/proof regions edited, axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (scripts/lean_verify.sh, 300s, run concurrently ≤4 at a time):
- pos_control.lean (gold impl): EXIT=0 VERIFIES ✓ (positive control).
- atk_1 (PREPATCH BUG: collector has no multi-name capability, always keeps verbatim, never splits): EXIT=1 REJECTED. Unsolved goal exactly `[f] = expandOne multiple f` under multiple∧name≠[] — matches Solution_prepatch.lean / refinement.md §A discriminator. prepatch_reproduced=true.
- atk_2 (ignore `multiple` param, always expandOne false): EXIT=1 REJECTED (goal: expandOne false = expandOne multiple).
- atk_3 (partial-domain: split but SKIP stripWs trim — name:=nm not stripWs nm): EXIT=1 REJECTED.
- atk_4 (boundary/off-by-one: while i>1 skips first element): EXIT=1 REJECTED (done_with fails: ¬i>1 ⊬ i=0).
- atk_5 (control-flow-effect: wrong concat order, result ++ expandOne instead of expandOne ++ result): EXIT=1 REJECTED.
- atk_6 (drop empty-field filter: always [f] ++ result, no split, no empty-drop): EXIT=1 REJECTED.
- atk_7 (UNGROUNDED-ORACLE ECHO: `return expandFields multiple raw` verbatim; proof trailing rw/simp_all dropped since loom_solve closes it): EXIT=0 VERIFIES. This is the ONLY verifying attack — and it is FUNCTIONALLY CORRECT (computes exactly the spec function).
- atk_8 (caller buildParameterFieldSeq returns `raw` directly, no expansion): EXIT=1 REJECTED (goal: raw = expandFields splitNames raw).

MANDATORY RESOLVE STEP for the one verifying attack (atk_7): its faithful refined patch is the exact gold transliteration — `return expandFields multiple raw` refines to `_consume_fields(multiple=...)` with the post-patch loop body (expandOne per field, concatenated) plus the caller threading multiple=True under napoleon_use_param — i.e. patch.diff verbatim. RAN through official harness: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8056', <atk_7_faithful.patch>, timeout=2400). Retried: RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1. FAIL_TO_PASS test_multiple_parameters PASSED, all 40 PASS_TO_PASS passed, 0 failures.

A-LEG AUDIT (refinement.md): every leg is R / A-reference / I; NO A-consumed (no module-level axiom whose ensures the proof consumes) and NO kind-3. The two changed string callees are modeled DEEPLY in the pure region (splitOnComma == str.split(','), stripWs == str.strip()) as A-reference. G-AX validated: axiom_check.py EXIT=0 (25 boundary + 50000 fuzz inputs; Lean isWs enumeration == Python _WS, asserted == full str.strip() whitespace set over range(0x110000)). Correspondence to real callees holds (incl. non-ASCII whitespace U+00A0/NEL/em/ideographic and ZWSP-kept). R/I legs cross-checked: conformance_check.py EXIT=0 (G-CONF, 100012 inputs seed=8056, shadow expandFields/buildParameterFieldSeq == gold loop body, 0 disagreements). The unchanged scanner is a free input (raw); downstream renderer is identity-on-fields boundary (mapping.md §3.3).

CONCLUSION: The equality spec admits only functionally-correct implementations; the single verifying wrong-shaped candidate (echo) is behaviorally identical to gold and its faithful patch resolves. No verifying same-spec impl has a non-resolving faithful patch. ≥5 distinct wrong impls (partial-domain atk_3, boundary atk_4, control-flow-effect atk_5, ungrounded-oracle echo atk_7, plus atk_1/2/6/8) attacked; none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed callee contracts. The two community string operations this module
   leans on — splitting a name on the comma separator and trimming surrounding
   whitespace from a name fragment — are modeled DEEPLY in the `pure` region
   (`splitOnComma`, `stripWs`) and validated equal to their standard-library
   counterparts by axiom_check.py (G-AX, A-reference). The sequence of raw
   fields the section scanner yields is taken as a FREE INPUT (`raw`), so the
   spec makes no behavioural claim about the unchanged scanner, and there is no
   module-level `axiom` whose `ensures` the proof consumes. -/
-- axioms-end

-- pure-start
/- One documented field: a name fragment, a type fragment, and the description
   lines that accompany it. Names and types are sequences of code points; the
   description is a sequence of lines (each itself a sequence of code points). -/
structure Field where
  name : List Char
  typ  : List Char
  desc : List (List Char)
deriving DecidableEq, Inhabited

/- The whitespace code points trimmed from the ends of a name fragment: exactly
   the code points the standard-library no-argument trim treats as whitespace —
   the ASCII whitespace, the FS/GS/RS/US separator controls, next-line, the
   no-break space, and the Unicode space/line/paragraph separators. -/
def isWs (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c = '\r' || c = '\x0b' || c = '\x0c' ||
  (0x1c ≤ c.val && c.val ≤ 0x1f) ||        -- file/group/record/unit separators
  c.val = 0x85 ||                          -- next line (NEL)
  c.val = 0xa0 ||                          -- no-break space
  c.val = 0x1680 ||                        -- ogham space mark
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||    -- en quad .. hair space
  c.val = 0x2028 || c.val = 0x2029 ||      -- line / paragraph separator
  c.val = 0x202f || c.val = 0x205f ||      -- narrow no-break / math space
  c.val = 0x3000                           -- ideographic space

/- Trim leading and trailing whitespace from a fragment (the ends only; interior
   whitespace is preserved). A deep model of the standard-library trim
   (mapping.md §3.2, A-reference). -/
def stripWs (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/- Split a fragment on the comma separator into its pieces, in order, keeping
   every piece (including empty ones between adjacent separators and at the
   ends). A string with no comma yields a single piece equal to the whole
   string. A deep model of the standard-library single-character split
   (mapping.md §3.1, A-reference). -/
def splitOnComma : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    if c = ',' then [] :: splitOnComma cs
    else
      match splitOnComma cs with
      | []      => [[c]]
      | g :: gs => (c :: g) :: gs

/- The fields a single raw field contributes, given whether comma-separated
   names should each become their own field:
   - when expansion is requested AND the name is non-empty, every comma-piece of
     the name, trimmed, becomes its own field carrying the SHARED type and
     description;
   - otherwise the raw field is kept verbatim, but only when it carries some
     content (a name, a type, or a description); an entirely empty raw field is
     dropped. -/
def expandOne (multiple : Bool) (f : Field) : List Field :=
  if multiple ∧ f.name ≠ [] then
    (splitOnComma f.name).map (fun nm => { f with name := stripWs nm })
  else
    if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else []

/- The full output field sequence: each raw field expanded and the results
   concatenated, in order. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern, plan §5.4). -/
def expandFields (multiple : Bool) : List Field → List Field
  | []      => []
  | f :: fs => expandOne multiple f ++ expandFields multiple fs

@[grind] lemma expandFields_nil (m : Bool) : expandFields m [] = [] := rfl
@[grind] lemma expandFields_cons (m : Bool) (f : Field) (fs : List Field) :
    expandFields m (f :: fs) = expandOne m f ++ expandFields m fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the documented field sequence, optionally letting a single declaration
   that lists several comma-separated names become one field per name. `multiple`
   and `raw` are read-only (not `mut`); nothing handed in is mutated
   (directive 5). The result is the per-field expansion `expandFields`. -/
method splitSharedNameFields (multiple : Bool) (raw : List Field) return (out : List Field)
  ensures out = expandFields multiple raw
  do
    -- impl-start
    let mut result : List Field := []
    let mut i := raw.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ raw.length
      invariant result = expandFields multiple (raw.drop i)
      done_with i = 0
    do
      let f := raw[i - 1]!
      result := expandOne multiple f ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expandFields` peels one `expandOne`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma expandFields_drop_step (multiple : Bool) (raw : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ raw.length) :
    expandFields multiple (raw.drop (i - 1))
      = expandOne multiple raw[i - 1]! ++ expandFields multiple (raw.drop i) := by
  have hlt : i - 1 < raw.length := by omega
  have hcons : raw.drop (i - 1) = raw[i - 1]! :: raw.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expandFields_cons]

prove_correct splitSharedNameFields by
  loom_solve
  rw [expandFields_drop_step multiple raw i (by omega) (by omega)]
  simp_all

/- Produce the field sequence for a parameter section, given an abstract Boolean
   `splitNames` selecting whether a single declaration that lists several
   comma-separated names should become one field per name. The downstream
   renderer is an unchanged function of this field sequence (mapping.md §3.3), so
   the field sequence is the behaviour pinned here. `splitNames` and `raw` are
   read-only (directive 5). -/
method buildParameterFieldSeq (splitNames : Bool) (raw : List Field) return (out : List Field)
  ensures out = expandFields splitNames raw
  do
    -- impl-start
    let fields ← splitSharedNameFields splitNames raw
    return fields
    -- impl-end

prove_correct buildParameterFieldSeq by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sphinx-doc__sphinx-8056 (velvet). Spec is an EXACT functional equality: `ensures out = expandFields multiple raw` (and the buildParameterFieldSeq caller `out = expandFields splitNames raw`). This is the tightest possible spec shape — a wrong impl cannot verify because it would require proving a false equality. All 8 attacks + positive control confirmed same_spec=True (swebench_unified.markers.same_spec via velvet backend); only impl/proof regions edited, axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (scripts/lean_verify.sh, 300s, run concurrently ≤4 at a time):
- pos_control.lean (gold impl): EXIT=0 VERIFIES ✓ (positive control).
- atk_1 (PREPATCH BUG: collector has no multi-name capability, always keeps verbatim, never splits): EXIT=1 REJECTED. Unsolved goal exactly `[f] = expandOne multiple f` under multiple∧name≠[] — matches Solution_prepatch.lean / refinement.md §A discriminator. prepatch_reproduced=true.
- atk_2 (ignore `multiple` param, always expandOne false): EXIT=1 REJECTED (goal: expandOne false = expandOne multiple).
- atk_3 (partial-domain: split but SKIP stripWs trim — name:=nm not stripWs nm): EXIT=1 REJECTED.
- atk_4 (boundary/off-by-one: while i>1 skips first element): EXIT=1 REJECTED (done_with fails: ¬i>1 ⊬ i=0).
- atk_5 (control-flow-effect: wrong concat order, result ++ expandOne instead of expandOne ++ result): EXIT=1 REJECTED.
- atk_6 (drop empty-field filter: always [f] ++ result, no split, no empty-drop): EXIT=1 REJECTED.
- atk_7 (UNGROUNDED-ORACLE ECHO: `return expandFields multiple raw` verbatim; proof trailing rw/simp_all dropped since loom_solve closes it): EXIT=0 VERIFIES. This is the ONLY verifying attack — and it is FUNCTIONALLY CORRECT (computes exactly the spec function).
- atk_8 (caller buildParameterFieldSeq returns `raw` directly, no expansion): EXIT=1 REJECTED (goal: raw = expandFields splitNames raw).

MANDATORY RESOLVE STEP for the one verifying attack (atk_7): its faithful refined patch is the exact gold transliteration — `return expandFields multiple raw` refines to `_consume_fields(multiple=...)` with the post-patch loop body (expandOne per field, concatenated) plus the caller threading multiple=True under napoleon_use_param — i.e. patch.diff verbatim. RAN through official harness: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8056', <atk_7_faithful.patch>, timeout=2400). Retried: RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1. FAIL_TO_PASS test_multiple_parameters PASSED, all 40 PASS_TO_PASS passed, 0 failures.

A-LEG AUDIT (refinement.md): every leg is R / A-reference / I; NO A-consumed (no module-level axiom whose ensures the proof consumes) and NO kind-3. The two changed string callees are modeled DEEPLY in the pure region (splitOnComma == str.split(','), stripWs == str.strip()) as A-reference. G-AX validated: axiom_check.py EXIT=0 (25 boundary + 50000 fuzz inputs; Lean isWs enumeration == Python _WS, asserted == full str.strip() whitespace set over range(0x110000)). Correspondence to real callees holds (incl. non-ASCII whitespace U+00A0/NEL/em/ideographic and ZWSP-kept). R/I legs cross-checked: conformance_check.py EXIT=0 (G-CONF, 100012 inputs seed=8056, shadow expandFields/buildParameterFieldSeq == gold loop body, 0 disagreements). The unchanged scanner is a free input (raw); downstream renderer is identity-on-fields boundary (mapping.md §3.3).

CONCLUSION: The equality spec admits only functionally-correct implementations; the single verifying wrong-shaped candidate (echo) is behaviorally identical to gold and its faithful patch resolves. No verifying same-spec impl has a non-resolving faithful patch. ≥5 distinct wrong impls (partial-domain atk_3, boundary atk_4, control-flow-effect atk_5, ungrounded-oracle echo atk_7, plus atk_1/2/6/8) attacked; none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet) = True. (2) Solution.lean elaborates clean (lean_verify exit 0); prove_correct discharges `out = expandFields multiple raw` for splitSharedNameFields and the wiring for buildParameterFieldSeq. (3) Deep models validated == real callees: independently confirmed isWs code-point set EXACTLY equals real str.strip() whitespace over full 0..0x10FFFF (empty symmetric difference); splitOnComma == str.split(','). axiom_check.py (G-AX) passes 25 boundary + 50000 fuzz. (4) conformance_check.py (G-CONF) passes 100012 inputs seed=8056, 0 disagreements; my own adversarial 300k-input cross-check of full expandOne (Lean deep-models vs real str.split/str.strip) with exotic Unicode whitespace + ZWSP/ZWNJ/BOM found 0 divergences. (5) Modeling boundaries sound: raw (unchanged scanner output) taken as free input so no over-claim; unchanged renderers _format_docutils_params/_format_fields correctly abstracted as identity-on-fields (deterministic in the field sequence the F2P test observes); ensures pins exactly the changed loop body incl. list truthiness (desc≠[] mirrors Python List[str] truthiness, not per-element). Spec is neither too strong nor drifting from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the accepted relaxed-leakage disposition (meta.relaxed_leakage=true, RELAXED_LEAKAGE.md present, G-LEAK status=relaxed). Not a rubber-stamp: (1) Core soundness intact — G-VERIFY/G-DIFF/G-EQ/G-AX/G-CONF/G-RESOLVE all pass; G-EQ is tight functional equality out=expandFields multiple raw over free inputs, G-DIFF prepatch fails precisely on the split clause. (2) Unavoidability re-derived: problem_statement reports only the COMBINING symptom and a COMBINED expected output (x1, x2 rendered as ONE entry), hints_text empty — it never asks to SPLIT x1,x2 into separate params. The gold's tested discriminator (F2P test_multiple_parameters, napoleon_use_param=True leg) is the opposite: SPLIT into two :param entries. A PS-faithful solver would render combined, so the comma-split expansion is a gold-internal choice not PS-derivable; any faithful spec MUST encode it (expandOne under multiple ∧ name≠[] = (splitOnComma f.name).map (stripWs ·)). Disclosure cannot be de-narrated away. (3) No leak beyond the dispositioned split facet: mechanical leakage.screen(velvet) returns passed=True, hard_failures=[]; grep of spec view finds NO residual napoleon/_consume_fields/_parse_parameters_section/docstring.py/use_param/rendering-style narration (D1/D2 de-narration confirmed: neutral names splitSharedNameFields/buildParameterFieldSeq and flag splitNames). Everything still disclosed is exactly the split discriminator the disposition covers. Per RELAXED_LEAKAGE.md + gates/_audit.py, a properly dispositioned relaxed-leakage panel_3 records as pass/NO-LEAKAGE. No new leaking line and disposition unbroken.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.
