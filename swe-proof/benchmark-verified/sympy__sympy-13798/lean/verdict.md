# P2 adversarial audit — sympy__sympy-13798

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,13 +106,11 @@
   let mut latex : String := ""
   match mulSymbolTable ms with
   | some v => latex := v
-  | none   => latex := ms.getD ""
+  | none   => return Except.error ()
   let mut latexNum : String := ""
   match mulSymbolTable (numKey ms) with
   | some v => latexNum := v
-  | none   =>
-      if isSpaceLike (ms.getD "") then latexNum := dotLatex
-      else latexNum := ms.getD ""
+  | none   => return Except.error ()
   return Except.ok (latex, latexNum)
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,7 @@
   let mut latex : String := ""
   match mulSymbolTable ms with
   | some v => latex := v
-  | none   => latex := ms.getD ""
+  | none   => latex := ""
   let mut latexNum : String := ""
   match mulSymbolTable (numKey ms) with
   | some v => latexNum := v
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,9 +110,7 @@
   let mut latexNum : String := ""
   match mulSymbolTable (numKey ms) with
   | some v => latexNum := v
-  | none   =>
-      if isSpaceLike (ms.getD "") then latexNum := dotLatex
-      else latexNum := ms.getD ""
+  | none   => latexNum := dotLatex
   return Except.ok (latex, latexNum)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
 def implementation_initMulSymbol
     (ms : Option String) : Except Unit (String × String) := Id.run do
   let mut latex : String := ""
-  match mulSymbolTable ms with
+  match mulSymbolTable (numKey ms) with
   | some v => latex := v
   | none   => latex := ms.getD ""
   let mut latexNum : String := ""
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,18 +102,8 @@
 
 -- impl-start
 def implementation_initMulSymbol
-    (ms : Option String) : Except Unit (String × String) := Id.run do
-  let mut latex : String := ""
-  match mulSymbolTable ms with
-  | some v => latex := v
-  | none   => latex := ms.getD ""
-  let mut latexNum : String := ""
-  match mulSymbolTable (numKey ms) with
-  | some v => latexNum := v
-  | none   =>
-      if isSpaceLike (ms.getD "") then latexNum := dotLatex
-      else latexNum := ms.getD ""
-  return Except.ok (latex, latexNum)
+    (ms : Option String) : Except Unit (String × String) :=
+  Except.ok (specMulSymbol ms)
 -- impl-end
 
 -- proof-start
@@ -121,10 +111,6 @@
     ∀ (ms : Option String),
       problem_spec_initMulSymbol ms (implementation_initMulSymbol ms) := by
   intro ms
-  unfold problem_spec_initMulSymbol implementation_initMulSymbol specMulSymbol
-  simp only [Id.run, bind, pure]
-  cases h1 : mulSymbolTable ms <;>
-    cases h2 : mulSymbolTable (numKey ms) <;>
-    simp only [] <;>
-    split <;> rfl
+  unfold problem_spec_initMulSymbol implementation_initMulSymbol
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,7 +111,7 @@
   match mulSymbolTable (numKey ms) with
   | some v => latexNum := v
   | none   =>
-      if isSpaceLike (ms.getD "") then latexNum := dotLatex
+      if isSpaceLike (ms.getD "") then latexNum := " \\cdot"
       else latexNum := ms.getD ""
   return Except.ok (latex, latexNum)
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
   | none   =>
       if isSpaceLike (ms.getD "") then latexNum := dotLatex
       else latexNum := ms.getD ""
-  return Except.ok (latex, latexNum)
+  return Except.ok (latexNum, latex)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deriving the two multiplication-separator strings used when rendering a product
to LaTeX, from a single user-supplied separator selector.

A renderer is configured with an optional separator selector. From it, two
output strings are derived:

* the separator placed between general factors, and
* the separator placed between numeric coefficients.

There is a small built-in table of named selectors. The empty/absent selector
maps to a single space for general factors; the named selectors map to their
standard LaTeX forms. For the *numeric* separator the absent/empty selector
behaves as the dotted selector.

The desired behavior is that the selector need NOT be one of the named entries.
Any selector the user supplies is honored:

* for the general-factor separator, an unrecognized selector is used verbatim as
  its own LaTeX form;
* for the numeric separator, an unrecognized selector that is purely a spacing
  command (empty, a blank, or one of the standard LaTeX spacing macros) falls
  back to the dotted form (so adjacent numbers do not run together), while any
  other unrecognized selector is used verbatim.

Configuring the renderer must therefore always succeed for an arbitrary
selector, rather than being restricted to the named entries.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The separator
-- table is a constant literal carried into the model deeply as `mulSymbolTable`,
-- and the derivation is a pure function of the selector. No `opaque`/`axiom`
-- callee contract is needed; the rule is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- The built-in table of named separator selectors → their LaTeX forms.
The absent selector (`none`) maps to a single space; an unrecognized selector
maps to `none` (it is not in the table). -/
def mulSymbolTable : Option String → Option String
  | none          => some " "
  | some "ldot"   => some " \\,.\\, "
  | some "dot"    => some " \\cdot "
  | some "times"  => some " \\times "
  | some _        => none

/-- The key used for the NUMERIC separator: the absent or empty selector behaves
as the named `"dot"` selector; any other selector is used as-is. -/
def numKey : Option String → Option String
  | none     => some "dot"
  | some s   => if s = "" then some "dot" else some s

/-- The whitespace predicate the renderer's trim uses: the full Unicode
whitespace set (`\t`..`\r`, the FS/GS/RS/US separators, space, NEL, NBSP,
Ogham space mark, the U+2000..U+200A spaces, line/paragraph separators,
narrow NBSP, medium mathematical space, and the ideographic space). -/
def pyWhitespace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x20) ||
  c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f ||
  c.val = 0x205f || c.val = 0x3000

/-- Trim surrounding whitespace with the renderer's whitespace set. -/
def pyStrip (s : String) : String :=
  String.mk (((s.toList.dropWhile pyWhitespace).reverse.dropWhile
    pyWhitespace).reverse)

/-- A selector that is purely a spacing command: empty, a blank, or one of the
standard LaTeX spacing macros (compared after trimming surrounding whitespace). -/
def isSpaceLike (s : String) : Bool :=
  ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"].contains (pyStrip s)

/-- The dotted numeric separator (the fallback for spacing-command selectors). -/
def dotLatex : String := " \\cdot "

/-- The two derived separators (general-factor, numeric) for a given selector. -/
def specMulSymbol (ms : Option String) : String × String :=
  let latex :=
    match mulSymbolTable ms with
    | some v => v
    | none   => ms.getD ""
  let latexNum :=
    match mulSymbolTable (numKey ms) with
    | some v => v
    | none   => if isSpaceLike (ms.getD "") then dotLatex else ms.getD ""
  (latex, latexNum)
-- pure-end

-- post-conditions-start
/-- Configuring the renderer always succeeds (`Except.ok`) for any selector, and
yields exactly the two derived separators. -/
def problem_spec_initMulSymbol
    (ms : Option String) (result : Except Unit (String × String)) : Prop :=
  result = Except.ok (specMulSymbol ms)
-- post-conditions-end

-- impl-start
def implementation_initMulSymbol
    (ms : Option String) : Except Unit (String × String) := Id.run do
  let mut latex : String := ""
  match mulSymbolTable ms with
  | some v => latex := v
  | none   => latex := ms.getD ""
  let mut latexNum : String := ""
  match mulSymbolTable (numKey ms) with
  | some v => latexNum := v
  | none   =>
      if isSpaceLike (ms.getD "") then latexNum := dotLatex
      else latexNum := ms.getD ""
  return Except.ok (latex, latexNum)
-- impl-end

-- proof-start
theorem correct_initMulSymbol :
    ∀ (ms : Option String),
      problem_spec_initMulSymbol ms (implementation_initMulSymbol ms) := by
  intro ms
  unfold problem_spec_initMulSymbol implementation_initMulSymbol specMulSymbol
  simp only [Id.run, bind, pure]
  cases h1 : mulSymbolTable ms <;>
    cases h2 : mulSymbolTable (numKey ms) <;>
    simp only [] <;>
    split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_initMulSymbol ms result := result = Except.ok (specMulSymbol ms), quantified over ALL ms:Option String. This is a total-functional equality pin — any verifying impl must equal specMulSymbol pointwise, so a genuinely wrong-behavior impl makes correct_initMulSymbol a FALSE proposition and NO proof can close it. Confirmed empirically.

SAME-SPEC: all 7 attacks pass swebench_unified.markers.same_spec against Solution.lean (only the impl region edited; axioms/pure/pre/post byte-identical).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH BUG (unrecognized selector -> Except.error, constructor fails): exit=1 FAIL. Reproduces the prepatch defect. Goal reduces to Except.error () = Except.ok (...) for ms=some "x" — false.
- atk_2 PARTIAL-DOMAIN (general separator none-branch -> "" instead of ms verbatim): exit=1 FAIL. Wrong for ms=some "x".
- atk_3 BOUNDARY (numeric none-branch always dotLatex, drops isSpaceLike test): exit=1 FAIL. Wrong for ms=some "x" (should be "x").
- atk_4 CONTROL-FLOW-EFFECT (general separator uses numKey table, swaps key): exit=1 FAIL. Wrong for ms=none.
- atk_5 UNGROUNDED-ORACLE ECHO (impl := Except.ok (specMulSymbol ms)): exit=0 VERIFIES; `#print axioms correct_initMulSymbol` => 'does not depend on any axioms' (clean). Per protocol, materialized its faithful refined patch (BYTE-IDENTICAL to gold patch.diff — diff confirms IDENTICAL) and RAN it through run_resolve: completed=True, resolved=True, note='resolved' (attempt 3; attempts 1-2 hit transient docker list_images ImageNotFound races under concurrent runs load ~200-300, not real verdicts). A resolving echo is NOT a weakness (policy). Also matches bundle's recorded G-RESOLVE resolved:true.
- atk_6 OFF-BY-ONE (space-like fallback -> " \\cdot" missing trailing space): exit=1 FAIL. Goal: (val," \cdot")=(val,dotLatex) — false.
- atk_7 TUPLE-SWAP (return (latexNum, latex)): exit=1 FAIL (kernel: declaration has metavariables). Goal: (val2,val1)=(val1,val2) — false when they differ (e.g. ms=none).

POSITIVE CONTROL: real Solution.lean verifies (exit=0); axioms = [propext, Quot.sound] (standard core; clean, no sorry/custom).

REFINEMENT.MD / A-LEG AUDIT: meta.json axioms:[] and deep_model_references:[]; no axiom/opaque/sorry in Solution.lean. Every leg is R or I (no A-consumed, no A-reference, no kind-3). The 'deep model' (mulSymbolTable constant literal, numKey Python truthiness, isSpaceLike via pyStrip/pyWhitespace) is spelled out and validated end-to-end by G-CONF (status=pass checked=120096, incl. cross-check against the REAL sympy.printing.latex.LatexPrinter and exotic-whitespace fuzz). This is legitimate deep modeling, not an ungrounded axiom oracle. Correspondence to the real callee (LatexPrinter.__init__ mul_symbol derivation) holds.

CONCLUSION: The only same-spec attack whose proof closes with clean axioms (atk_5 echo) has a faithful patch that RESOLVES; all genuinely-wrong impls fail to verify. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deriving the two multiplication-separator strings used when rendering a product
to LaTeX, from a single user-supplied separator selector.

A renderer is configured with an optional separator selector. From it, two
output strings are derived:

* the separator placed between general factors, and
* the separator placed between numeric coefficients.

There is a small built-in table of named selectors. The empty/absent selector
maps to a single space for general factors; the named selectors map to their
standard LaTeX forms. For the *numeric* separator the absent/empty selector
behaves as the dotted selector.

The desired behavior is that the selector need NOT be one of the named entries.
Any selector the user supplies is honored:

* for the general-factor separator, an unrecognized selector is used verbatim as
  its own LaTeX form;
* for the numeric separator, an unrecognized selector that is purely a spacing
  command (empty, a blank, or one of the standard LaTeX spacing macros) falls
  back to the dotted form (so adjacent numbers do not run together), while any
  other unrecognized selector is used verbatim.

Configuring the renderer must therefore always succeed for an arbitrary
selector, rather than being restricted to the named entries.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The separator
-- table is a constant literal carried into the model deeply as `mulSymbolTable`,
-- and the derivation is a pure function of the selector. No `opaque`/`axiom`
-- callee contract is needed; the rule is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- The built-in table of named separator selectors → their LaTeX forms.
The absent selector (`none`) maps to a single space; an unrecognized selector
maps to `none` (it is not in the table). -/
def mulSymbolTable : Option String → Option String
  | none          => some " "
  | some "ldot"   => some " \\,.\\, "
  | some "dot"    => some " \\cdot "
  | some "times"  => some " \\times "
  | some _        => none

/-- The key used for the NUMERIC separator: the absent or empty selector behaves
as the named `"dot"` selector; any other selector is used as-is. -/
def numKey : Option String → Option String
  | none     => some "dot"
  | some s   => if s = "" then some "dot" else some s

/-- The whitespace predicate the renderer's trim uses: the full Unicode
whitespace set (`\t`..`\r`, the FS/GS/RS/US separators, space, NEL, NBSP,
Ogham space mark, the U+2000..U+200A spaces, line/paragraph separators,
narrow NBSP, medium mathematical space, and the ideographic space). -/
def pyWhitespace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x20) ||
  c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f ||
  c.val = 0x205f || c.val = 0x3000

/-- Trim surrounding whitespace with the renderer's whitespace set. -/
def pyStrip (s : String) : String :=
  String.mk (((s.toList.dropWhile pyWhitespace).reverse.dropWhile
    pyWhitespace).reverse)

/-- A selector that is purely a spacing command: empty, a blank, or one of the
standard LaTeX spacing macros (compared after trimming surrounding whitespace). -/
def isSpaceLike (s : String) : Bool :=
  ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"].contains (pyStrip s)

/-- The dotted numeric separator (the fallback for spacing-command selectors). -/
def dotLatex : String := " \\cdot "

/-- The two derived separators (general-factor, numeric) for a given selector. -/
def specMulSymbol (ms : Option String) : String × String :=
  let latex :=
    match mulSymbolTable ms with
    | some v => v
    | none   => ms.getD ""
  let latexNum :=
    match mulSymbolTable (numKey ms) with
    | some v => v
    | none   => if isSpaceLike (ms.getD "") then dotLatex else ms.getD ""
  (latex, latexNum)
-- pure-end

-- post-conditions-start
/-- Configuring the renderer always succeeds (`Except.ok`) for any selector, and
yields exactly the two derived separators. -/
def problem_spec_initMulSymbol
    (ms : Option String) (result : Except Unit (String × String)) : Prop :=
  result = Except.ok (specMulSymbol ms)
-- post-conditions-end

-- impl-start
def implementation_initMulSymbol
    (ms : Option String) : Except Unit (String × String) := Id.run do
  let mut latex : String := ""
  match mulSymbolTable ms with
  | some v => latex := v
  | none   => latex := ms.getD ""
  let mut latexNum : String := ""
  match mulSymbolTable (numKey ms) with
  | some v => latexNum := v
  | none   =>
      if isSpaceLike (ms.getD "") then latexNum := dotLatex
      else latexNum := ms.getD ""
  return Except.ok (latex, latexNum)
-- impl-end

-- proof-start
theorem correct_initMulSymbol :
    ∀ (ms : Option String),
      problem_spec_initMulSymbol ms (implementation_initMulSymbol ms) := by
  intro ms
  unfold problem_spec_initMulSymbol implementation_initMulSymbol specMulSymbol
  simp only [Id.run, bind, pure]
  cases h1 : mulSymbolTable ms <;>
    cases h2 : mulSymbolTable (numKey ms) <;>
    simp only [] <;>
    split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_initMulSymbol ms result := result = Except.ok (specMulSymbol ms), quantified over ALL ms:Option String. This is a total-functional equality pin — any verifying impl must equal specMulSymbol pointwise, so a genuinely wrong-behavior impl makes correct_initMulSymbol a FALSE proposition and NO proof can close it. Confirmed empirically.

SAME-SPEC: all 7 attacks pass swebench_unified.markers.same_spec against Solution.lean (only the impl region edited; axioms/pure/pre/post byte-identical).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH BUG (unrecognized selector -> Except.error, constructor fails): exit=1 FAIL. Reproduces the prepatch defect. Goal reduces to Except.error () = Except.ok (...) for ms=some "x" — false.
- atk_2 PARTIAL-DOMAIN (general separator none-branch -> "" instead of ms verbatim): exit=1 FAIL. Wrong for ms=some "x".
- atk_3 BOUNDARY (numeric none-branch always dotLatex, drops isSpaceLike test): exit=1 FAIL. Wrong for ms=some "x" (should be "x").
- atk_4 CONTROL-FLOW-EFFECT (general separator uses numKey table, swaps key): exit=1 FAIL. Wrong for ms=none.
- atk_5 UNGROUNDED-ORACLE ECHO (impl := Except.ok (specMulSymbol ms)): exit=0 VERIFIES; `#print axioms correct_initMulSymbol` => 'does not depend on any axioms' (clean). Per protocol, materialized its faithful refined patch (BYTE-IDENTICAL to gold patch.diff — diff confirms IDENTICAL) and RAN it through run_resolve: completed=True, resolved=True, note='resolved' (attempt 3; attempts 1-2 hit transient docker list_images ImageNotFound races under concurrent runs load ~200-300, not real verdicts). A resolving echo is NOT a weakness (policy). Also matches bundle's recorded G-RESOLVE resolved:true.
- atk_6 OFF-BY-ONE (space-like fallback -> " \\cdot" missing trailing space): exit=1 FAIL. Goal: (val," \cdot")=(val,dotLatex) — false.
- atk_7 TUPLE-SWAP (return (latexNum, latex)): exit=1 FAIL (kernel: declaration has metavariables). Goal: (val2,val1)=(val1,val2) — false when they differ (e.g. ms=none).

POSITIVE CONTROL: real Solution.lean verifies (exit=0); axioms = [propext, Quot.sound] (standard core; clean, no sorry/custom).

REFINEMENT.MD / A-LEG AUDIT: meta.json axioms:[] and deep_model_references:[]; no axiom/opaque/sorry in Solution.lean. Every leg is R or I (no A-consumed, no A-reference, no kind-3). The 'deep model' (mulSymbolTable constant literal, numKey Python truthiness, isSpaceLike via pyStrip/pyWhitespace) is spelled out and validated end-to-end by G-CONF (status=pass checked=120096, incl. cross-check against the REAL sympy.printing.latex.LatexPrinter and exotic-whitespace fuzz). This is legitimate deep modeling, not an ungrounded axiom oracle. Correspondence to the real callee (LatexPrinter.__init__ mul_symbol derivation) holds.

CONCLUSION: The only same-spec attack whose proof closes with clean axioms (atk_5 echo) has a faithful patch that RESOLVES; all genuinely-wrong impls fail to verify. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the Lean model of the mul_symbol derivation in LatexPrinter.__init__ (sympy 13798).

### Checks performed
1. same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the lean backend tables — the spec region (axioms/pure/post-conditions) is byte-identical between patch and prepatch; the fix lives only in the impl region, as intended.
2. lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
3. #print axioms correct_initMulSymbol -> [propext, Quot.sound] only. No sorryAx; the proof is genuine.
4. pyWhitespace: exhaustively enumerated Python's str.strip() whitespace set over all of Unicode -> exactly 29 code points {0x09-0x0d,0x1c-0x20,0x85,0xa0,0x1680,0x2000-0x200a,0x2028,0x2029,0x202f,0x205f,0x3000}, which matches pyWhitespace in the Lean model exactly (unlike Lean's built-in String.trim, which is correctly NOT used).
5. Differential test: transcribed the Lean specMulSymbol (mulSymbolTable/numKey/pyStrip/isSpaceLike) into Python and compared against the EXACT patched-repo derivation snippet (from patch.diff, matching latex.py) over 5025 inputs — named selectors (None/''/dot/ldot/times), LaTeX spacing macros (\,\:\;\quad), exotic whitespace (NBSP, \x0c, \x1c, ideographic space), and 5000 random strings from an alphabet including those exotic chars. Result: 0 mismatches.

The full sympy package cannot import under py3.12 (collections.Mapping removal), but the modeled derivation is self-contained and was executed verbatim from the gold patch, so the differential comparison is against the real post-patch behavior.

Modeling boundary is sound: the KeyError<->none bijection discriminates gold (Except.ok) from prepatch (Except.error) without over-constraining; numKey correctly models Python `or 'dot'` truthiness (None/'' -> 'dot'); the numeric space-like fallback reproduces str.strip()-membership exactly. No input found where the modeled function disagrees with the real callee. The spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (swebench_unified.leakage.screen over the lean spec view) passes: no diff markers, patched file path 'sympy/printing/latex.py' and its dotted module path absent from the view, patch-changed-symbol set is EMPTY (the gold edit only wraps dict subscripts in try/except and touches settings keys — it defines no repo def/class), no bug/fix narration in comments/docstrings, and no verbatim gold-patch line reproduced. same_spec(Solution, Solution_prepatch)=True so I judged the frozen spec region; spec_view elides impl+proof correctly.

Semantic considerations checked by hand:
1) The space-like literal list appears in both the gold patch (`['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']`) and the spec view (`isSpaceLike`: `["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"]`). This is the behavioral contract the consumer must satisfy, not a leak of the *edit*: a spec-consumer benchmark's post-conditions/pure region is expected to encode required behavior fully. G-PANEL-3 guards against revealing the gold DIFF (structure, path, symbols, fix-narration) beyond the public problem_statement, not against a spec being easy to satisfy. The literal differs only by quote char (Lean "" vs Python ''), and encoding it is by-design.
2) The problem_statement already publicly discloses the mul_symbol kwarg, the 'four choices' restriction, and the desired arbitrary/`\,` thin-space behavior — so the spec's high-level narration ('the selector need NOT be one of the named entries', 'any selector is honored') is squarely within what the solver already sees. No content unique to hints_text is echoed.
3) The named table entries (ldot/dot/times, `\cdot`, `\times`) are the pre-existing public API surface, not introduced by the patch.

No spec-view line reconstructs the gold edit beyond the public problem statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
