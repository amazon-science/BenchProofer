# P2 adversarial audit — scikit-learn__scikit-learn-15100

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,17 +52,22 @@
 
 -- impl-start
 def implementation_stripAccents (s : List Char) : List Char := Id.run do
-  if s.all isAscii then
+  let normalized := canonDecompose s
+  if normalized = s then
     return s
-  let normalized := canonDecompose s
   return normalized.filter (fun c => !isCombiningMark c)
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,19 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_stripAccents (s : List Char) : List Char := Id.run do
-  if s.all isAscii then
-    return s
-  let normalized := canonDecompose s
-  return normalized.filter (fun c => !isCombiningMark c)
+def implementation_stripAccents (s : List Char) : List Char := s
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,17 +52,22 @@
 
 -- impl-start
 def implementation_stripAccents (s : List Char) : List Char := Id.run do
-  if s.all isAscii then
+  if s.all (fun c => decide (c.toNat ≤ 128)) then
     return s
   let normalized := canonDecompose s
   return normalized.filter (fun c => !isCombiningMark c)
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,17 +52,20 @@
 
 -- impl-start
 def implementation_stripAccents (s : List Char) : List Char := Id.run do
-  if s.all isAscii then
-    return s
   let normalized := canonDecompose s
   return normalized.filter (fun c => !isCombiningMark c)
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,14 +55,19 @@
   if s.all isAscii then
     return s
   let normalized := canonDecompose s
-  return normalized.filter (fun c => !isCombiningMark c)
+  return normalized.filter (fun c => isCombiningMark c)
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,15 +54,19 @@
 def implementation_stripAccents (s : List Char) : List Char := Id.run do
   if s.all isAscii then
     return s
-  let normalized := canonDecompose s
-  return normalized.filter (fun c => !isCombiningMark c)
+  return canonDecompose s
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,20 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_stripAccents (s : List Char) : List Char := Id.run do
-  if s.all isAscii then
-    return s
-  let normalized := canonDecompose s
-  return normalized.filter (fun c => !isCombiningMark c)
+def implementation_stripAccents (s : List Char) : List Char :=
+  (canonDecompose s).filter (fun c => !isCombiningMark c)
 -- impl-end
-
 -- proof-start
 theorem correct_stripAccents :
     ∀ (s : List Char),
       problem_spec_stripAccents s (implementation_stripAccents s) := by
   intro s
   unfold problem_spec_stripAccents implementation_stripAccents
-  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
+  simp only [Id.run, bind, pure]
+  first
+    | (split <;> rfl)
+    | (by_cases h : s.all isAscii <;> simp_all [h])
+    | (by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind])
+    | simp_all
+    | rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Removing accent marks from a text string.

The desired behavior:

* If the string consists only of basic ASCII characters (every code point below
  128), it carries no accents and is returned completely unchanged.
* Otherwise the string is decomposed into its canonical form — each visible
  glyph split into a base character followed by any number of standalone
  combining marks — and every combining mark is then dropped, leaving only the
  base characters.

The point is that the decision to strip is driven by whether the text actually
contains any non-ASCII code point, NOT by whether the text happens to already be
in decomposed form. A glyph that is supplied already split into a base letter
plus a separate combining mark is still non-ASCII, so its combining mark must be
removed just like an accent attached to a pre-composed glyph.
-/

-- axioms-start
/-- Canonical decomposition of a string: each glyph is rewritten as a base
character followed by zero or more standalone combining marks. This is a
standard-library text-normalization routine the specification reads but does not
redefine; only its signature is declared here, and its behavior is exercised
against the real routine by the conformance gate. -/
opaque canonDecompose : List Char → List Char

/-- Whether a single code point is a standalone combining mark (a mark that
attaches to a preceding base character rather than standing on its own). An
unchanged standard-library predicate; signature only. -/
opaque isCombiningMark : Char → Bool
-- axioms-end

-- pure-start
/-- A code point is basic ASCII when its scalar value is below 128. -/
def isAscii (c : Char) : Bool := decide (c.toNat < 128)
-- pure-end

-- post-conditions-start
/-- The result is the input verbatim when every code point is basic ASCII;
otherwise it is the canonical decomposition of the input with every combining
mark removed. -/
def problem_spec_stripAccents (s : List Char) (result : List Char) : Prop :=
  if s.all isAscii then
    result = s
  else
    result = (canonDecompose s).filter (fun c => !isCombiningMark c)
-- post-conditions-end

-- impl-start
def implementation_stripAccents (s : List Char) : List Char := Id.run do
  if s.all isAscii then
    return s
  let normalized := canonDecompose s
  return normalized.filter (fun c => !isCombiningMark c)
-- impl-end

-- proof-start
theorem correct_stripAccents :
    ∀ (s : List Char),
      problem_spec_stripAccents s (implementation_stripAccents s) := by
  intro s
  unfold problem_spec_stripAccents implementation_stripAccents
  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of scikit-learn__scikit-learn-15100 (lean).

SPEC SHAPE: post-conditions region is a SINGLE-VALUED equality postcondition: `if s.all isAscii then result = s else result = (canonDecompose s).filter (fun c => !isCombiningMark c)`. Both branches pin result to a total function of s (canonDecompose/isCombiningMark are FIXED opaque functions, not existentially quantified). Therefore every input has exactly one satisfying result = the gold output; any impl proving `forall s, problem_spec ...` is extensionally equal to gold and cannot diverge at runtime. No behavioral slack => no spec-satisfying-but-non-resolving alternative can exist.

same_spec: confirmed True for all 7 attacks (spec/axioms/pure/post lines 1-51 byte-identical). Discrimination sanity check: mutating the spec constant (c.toNat<128 -> <999) makes same_spec=False, so the marker is not trivially True.

COMMANDS: `bash scripts/lean_verify.sh <file>`, run concurrently in <=4-wide background batches.

POSITIVE CONTROL positive_control.lean (= gold Solution.lean impl): exit 0. `#print axioms correct_stripAccents` => 'depends on axioms: [propext]' (clean; no sorryAx).

ATTACKS (all same_spec=True; ALL FAIL TO PROVE, exit 1 'unsolved goals' — none closes, so protocol step 2 (materialize+resolve) is not triggered for any):
- atk_1 prepatch-bug reproduction (guard `canonDecompose s = s`): exit 1, unsolved goals (both branches). This IS the prepatch bug => prepatch_reproduced=true.
- atk_2 partial-domain `impl s := s` (always return unchanged): exit 1, residual goal `s = filter (!isCombiningMark) (canonDecompose s)` in neg branch — unprovable (opaque callees).
- atk_3 boundary off-by-one guard `c.toNat <= 128`: exit 1, unsolved goals.
- atk_4 control-flow-effect: drop ASCII fast-path, always decompose+filter: exit 1, unsolved goals (ascii branch cannot show filtered-decomp = s).
- atk_5 ungrounded-oracle echo: else-branch filters `isCombiningMark c` (keep marks) instead of `!`: exit 1, unsolved goals.
- atk_6 control-flow-effect: return `canonDecompose s` unfiltered on non-ascii: exit 1, unsolved goals.
- atk_7 ungrounded-oracle echo: unconditional filtered-decomp (no branch): exit 1, unsolved goals (ascii branch requires it equal s).
Each used a strong proof combinator (`first | split<;>rfl | by_cases...simp_all | simp_all | rfl`); none closed. Because canonDecompose/isCombiningMark are opaque, no rewrite forces divergent output to equal the gold expression => the single-valued spec genuinely admits only gold.

REFINEMENT AUDIT (refinement.md): 4 legs — leg1/2 R (ASCII-encodability guard `s.encode('ASCII',strict)`/UnicodeEncodeError refined to total per-code-point `s.all isAscii`, isAscii=c.toNat<128), leg3 A-reference (`unicodedata.normalize('NFKD',s)` <-> opaque canonDecompose, proof consumes no property), leg4 A-reference+I (`unicodedata.combining(c)` <-> opaque isCombiningMark; list-comp+join = List.filter). NO A-consumed, NO kind-3 ungrounded axiom: axioms region ships only opaque signatures, correct_ closes by split<;>rfl consuming no callee property, G-AX is a legitimate skip stub. A-reference correspondence to real unicodedata callees is validated by G-CONF (conformance_check.py: shadow uses REAL unicodedata vs oracle replica of POST-PATCH strip_accents_unicode; checked=120021 disagreements=0, F2P + edge cases covered). R/I legs mechanically covered by G-CONF (per G-CONF's scope) and confirmed here structurally.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7) run under lean_verify concurrently; none produced a closing proof, so verify=>correct holds on this spec (single-valued equality postcondition, zero slack). Positive control verifies with clean [propext] axioms. Refinement legs are all R/A-reference/I with valid callee correspondence; no A-consumed, no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Removing accent marks from a text string.

The desired behavior:

* If the string consists only of basic ASCII characters (every code point below
  128), it carries no accents and is returned completely unchanged.
* Otherwise the string is decomposed into its canonical form — each visible
  glyph split into a base character followed by any number of standalone
  combining marks — and every combining mark is then dropped, leaving only the
  base characters.

The point is that the decision to strip is driven by whether the text actually
contains any non-ASCII code point, NOT by whether the text happens to already be
in decomposed form. A glyph that is supplied already split into a base letter
plus a separate combining mark is still non-ASCII, so its combining mark must be
removed just like an accent attached to a pre-composed glyph.
-/

-- axioms-start
/-- Canonical decomposition of a string: each glyph is rewritten as a base
character followed by zero or more standalone combining marks. This is a
standard-library text-normalization routine the specification reads but does not
redefine; only its signature is declared here, and its behavior is exercised
against the real routine by the conformance gate. -/
opaque canonDecompose : List Char → List Char

/-- Whether a single code point is a standalone combining mark (a mark that
attaches to a preceding base character rather than standing on its own). An
unchanged standard-library predicate; signature only. -/
opaque isCombiningMark : Char → Bool
-- axioms-end

-- pure-start
/-- A code point is basic ASCII when its scalar value is below 128. -/
def isAscii (c : Char) : Bool := decide (c.toNat < 128)
-- pure-end

-- post-conditions-start
/-- The result is the input verbatim when every code point is basic ASCII;
otherwise it is the canonical decomposition of the input with every combining
mark removed. -/
def problem_spec_stripAccents (s : List Char) (result : List Char) : Prop :=
  if s.all isAscii then
    result = s
  else
    result = (canonDecompose s).filter (fun c => !isCombiningMark c)
-- post-conditions-end

-- impl-start
def implementation_stripAccents (s : List Char) : List Char := Id.run do
  if s.all isAscii then
    return s
  let normalized := canonDecompose s
  return normalized.filter (fun c => !isCombiningMark c)
-- impl-end

-- proof-start
theorem correct_stripAccents :
    ∀ (s : List Char),
      problem_spec_stripAccents s (implementation_stripAccents s) := by
  intro s
  unfold problem_spec_stripAccents implementation_stripAccents
  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of scikit-learn__scikit-learn-15100 (lean).

SPEC SHAPE: post-conditions region is a SINGLE-VALUED equality postcondition: `if s.all isAscii then result = s else result = (canonDecompose s).filter (fun c => !isCombiningMark c)`. Both branches pin result to a total function of s (canonDecompose/isCombiningMark are FIXED opaque functions, not existentially quantified). Therefore every input has exactly one satisfying result = the gold output; any impl proving `forall s, problem_spec ...` is extensionally equal to gold and cannot diverge at runtime. No behavioral slack => no spec-satisfying-but-non-resolving alternative can exist.

same_spec: confirmed True for all 7 attacks (spec/axioms/pure/post lines 1-51 byte-identical). Discrimination sanity check: mutating the spec constant (c.toNat<128 -> <999) makes same_spec=False, so the marker is not trivially True.

COMMANDS: `bash scripts/lean_verify.sh <file>`, run concurrently in <=4-wide background batches.

POSITIVE CONTROL positive_control.lean (= gold Solution.lean impl): exit 0. `#print axioms correct_stripAccents` => 'depends on axioms: [propext]' (clean; no sorryAx).

ATTACKS (all same_spec=True; ALL FAIL TO PROVE, exit 1 'unsolved goals' — none closes, so protocol step 2 (materialize+resolve) is not triggered for any):
- atk_1 prepatch-bug reproduction (guard `canonDecompose s = s`): exit 1, unsolved goals (both branches). This IS the prepatch bug => prepatch_reproduced=true.
- atk_2 partial-domain `impl s := s` (always return unchanged): exit 1, residual goal `s = filter (!isCombiningMark) (canonDecompose s)` in neg branch — unprovable (opaque callees).
- atk_3 boundary off-by-one guard `c.toNat <= 128`: exit 1, unsolved goals.
- atk_4 control-flow-effect: drop ASCII fast-path, always decompose+filter: exit 1, unsolved goals (ascii branch cannot show filtered-decomp = s).
- atk_5 ungrounded-oracle echo: else-branch filters `isCombiningMark c` (keep marks) instead of `!`: exit 1, unsolved goals.
- atk_6 control-flow-effect: return `canonDecompose s` unfiltered on non-ascii: exit 1, unsolved goals.
- atk_7 ungrounded-oracle echo: unconditional filtered-decomp (no branch): exit 1, unsolved goals (ascii branch requires it equal s).
Each used a strong proof combinator (`first | split<;>rfl | by_cases...simp_all | simp_all | rfl`); none closed. Because canonDecompose/isCombiningMark are opaque, no rewrite forces divergent output to equal the gold expression => the single-valued spec genuinely admits only gold.

REFINEMENT AUDIT (refinement.md): 4 legs — leg1/2 R (ASCII-encodability guard `s.encode('ASCII',strict)`/UnicodeEncodeError refined to total per-code-point `s.all isAscii`, isAscii=c.toNat<128), leg3 A-reference (`unicodedata.normalize('NFKD',s)` <-> opaque canonDecompose, proof consumes no property), leg4 A-reference+I (`unicodedata.combining(c)` <-> opaque isCombiningMark; list-comp+join = List.filter). NO A-consumed, NO kind-3 ungrounded axiom: axioms region ships only opaque signatures, correct_ closes by split<;>rfl consuming no callee property, G-AX is a legitimate skip stub. A-reference correspondence to real unicodedata callees is validated by G-CONF (conformance_check.py: shadow uses REAL unicodedata vs oracle replica of POST-PATCH strip_accents_unicode; checked=120021 disagreements=0, F2P + edge cases covered). R/I legs mechanically covered by G-CONF (per G-CONF's scope) and confirmed here structurally.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7) run under lean_verify concurrently; none produced a closing proof, so verify=>correct holds on this spec (single-valued equality postcondition, zero slack). Positive control verifies with clean [propext] axioms. Refinement legs are all R/A-reference/I with valid callee correspondence; no A-consumed, no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function = post-patch strip_accents_unicode. Spec: if s.all isAscii then result=s else result=(canonDecompose s).filter(!isCombiningMark). Verification: (1) Solution.lean compiles clean, #print axioms correct_stripAccents = [propext] only (no sorryAx, real proof). (2) same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with lean backend; the ONLY diff between post/pre is the impl guard, spec region byte-identical. (3) Mapping is exact: post-patch guard `s.encode('ASCII', strict)` succeeds iff every code point < 128 iff `s.all isAscii` (isAscii c := c.toNat<128) — faithful R refinement. The unchanged callees unicodedata.normalize('NFKD') and unicodedata.combining are modeled as OPAQUE A-references, so the spec is parametric on them and cannot over-constrain; their real behavior is validated by G-CONF. (4) Differential fuzz for spec-too-strong: conformance_check.py shadow (using REAL unicodedata callees) vs faithful post-patch replica = 120,021 inputs, 0 disagreements. My own adversarial pass added 500k+ inputs across full Unicode incl astral plane (to 0x10FFFF), compatibility/ligature chars (fi, 1/2, superscript-2), fullwidth, and the 0x7f/0x80 ASCII boundary: 0 divergences. No input distinguishes the modeled spec from the real post-patch callee. Spec neither drifts from nor over-strengthens repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean lines 1-51: docstring + opaque callee signatures + isAscii + postcondition) encodes only the required CORRECT behavior, which the public problem_statement already fully specifies. The problem_statement states the bug (strip_accents_unicode fails on strings already in NFKD form), gives the exact reproducer (chr(241) vs chr(110)+chr(771)), and the expected result (both -> 'n'). The docstring's phrasing ('...NOT by whether the text happens to already be in decomposed form') parallels the public 'if those strings are already in NFKD form' — within public scope, not beyond it. The gold MECHANISM (try/except s.encode('ASCII', errors='strict') guard replacement) is NOT revealed: the discriminating clause is expressed as the total predicate `s.all isAscii` (c.toNat < 128), a refinement of the encode mechanism, not the encode/exception approach itself. Lexical scan of lines 1-51 for edit-pointing tokens (encode|try|except|guard|patch|fix|prepatch|early-return|NFKD|unicodedata|combining()) returns nothing. canonDecompose/isCombiningMark appear only as opaque signatures (unchanged A-reference callees), not gold-specific. Encoding the publicly-required correct postcondition is the legitimate job of a spec and is not leakage. Note: leakage is judged over the spec view vs problem_statement, not hints_text — the hints_text does contain the exact fix, but that is excluded by policy and irrelevant. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
