# P2 adversarial audit — django__django-12155

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. The resolve-run break-leg is therefore vacuously satisfied.
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -118,7 +118,7 @@
   do
     -- impl-start
     let lines := splitLines text
-    let margin := commonIndent (lines.drop 1)
+    let margin := commonIndent lines
     let dedented := dedentLines margin lines
     let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
     return joinNL trimmed
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -117,11 +117,7 @@
   ensures out = cleanDocModel text
   do
     -- impl-start
-    let lines := splitLines text
-    let margin := commonIndent (lines.drop 1)
-    let dedented := dedentLines margin lines
-    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
-    return joinNL trimmed
+    return text
     -- impl-end
 
 prove_correct normalizeIndentation by
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -120,7 +120,7 @@
     let lines := splitLines text
     let margin := commonIndent (lines.drop 1)
     let dedented := dedentLines margin lines
-    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
+    let trimmed := dropTrailingBlank dedented
     return joinNL trimmed
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -120,7 +120,7 @@
     let lines := splitLines text
     let margin := commonIndent (lines.drop 1)
     let dedented := dedentLines margin lines
-    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
+    let trimmed := dropLeadingBlank dedented
     return joinNL trimmed
     -- impl-end
 
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -118,7 +118,7 @@
   do
     -- impl-start
     let lines := splitLines text
-    let margin := commonIndent (lines.drop 1)
+    let margin := commonIndent (lines.drop 2)
     let dedented := dedentLines margin lines
     let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
     return joinNL trimmed
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -118,8 +118,7 @@
   do
     -- impl-start
     let lines := splitLines text
-    let margin := commonIndent (lines.drop 1)
-    let dedented := dedentLines margin lines
+    let dedented := dedentLines none lines
     let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
     return joinNL trimmed
     -- impl-end
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -121,7 +121,7 @@
     let margin := commonIndent (lines.drop 1)
     let dedented := dedentLines margin lines
     let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
-    return joinNL trimmed
+    return joinNL trimmed ++ ['\n']
     -- impl-end
 
 prove_correct normalizeIndentation by
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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -119,7 +119,9 @@
     -- impl-start
     let lines := splitLines text
     let margin := commonIndent (lines.drop 1)
-    let dedented := dedentLines margin lines
+    let dedented := match margin with
+      | none   => lines
+      | some m => lines.map (fun l => l.drop m)
     let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
     return joinNL trimmed
     -- impl-end
```

Attack 9 — `atk_echo.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The normalization performed here is modeled DEEPLY
@@ -117,11 +117,7 @@
   ensures out = cleanDocModel text
   do
     -- impl-start
-    let lines := splitLines text
-    let margin := commonIndent (lines.drop 1)
-    let dedented := dedentLines margin lines
-    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
-    return joinNL trimmed
+    return cleanDocModel text
     -- impl-end
 
 prove_correct normalizeIndentation by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The normalization performed here is modeled DEEPLY
--  in the `pure` region as a closed, computable function of its input text:
--  split into lines, find the common leading indentation shared by the lines
--  AFTER the first, remove that indentation from those lines while stripping the
--  first line, then drop surrounding blank lines and rejoin. The standard-library
--  routine this models (an unchanged callee the routine delegates to) is an
--  A-reference: the deep model `cleanDocModel` is validated equal to the real
--  library routine by axiom_check.py / G-AX. Nothing is consumed as an axiom —
--  see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Number of leading space characters of a line. -/
def leadingSpaces : List Char → Nat
  | []      => 0
  | c :: cs => if c = ' ' then leadingSpaces cs + 1 else 0

/- Drop the leading space characters of a line. -/
def stripLeadingSpaces : List Char → List Char
  | []      => []
  | c :: cs => if c = ' ' then stripLeadingSpaces cs else c :: cs

/- A line "has content" iff it contains at least one non-space character, i.e.
   stripping its leading spaces leaves something. -/
def hasContent (l : List Char) : Bool := !(stripLeadingSpaces l).isEmpty

/- Split a character sequence into lines on the newline separator. Always
   returns at least one line (an empty sequence is a single empty line). -/
def splitLines : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
      let rest := splitLines cs
      if c = '\n' then [] :: rest
      else
        match rest with
        | []      => [[c]]
        | r :: rs => (c :: r) :: rs

/- The common leading indentation shared by the content lines of a list: the
   minimum number of leading spaces over the lines that have content, or `none`
   when there is no such line. -/
def commonIndent : List (List Char) → Option Nat
  | []      => none
  | l :: ls =>
      let rest := commonIndent ls
      if hasContent l then
        match rest with
        | none   => some (leadingSpaces l)
        | some m => some (Nat.min (leadingSpaces l) m)
      else rest

/- Remove the common indentation: always strip the leading spaces of the first
   line; remove `margin` leading characters from every subsequent line when a
   common indentation exists (otherwise leave the subsequent lines untouched). -/
def dedentLines (margin : Option Nat) : List (List Char) → List (List Char)
  | []            => []
  | first :: tail =>
      let f := stripLeadingSpaces first
      let t := match margin with
        | none   => tail
        | some m => tail.map (fun l => l.drop m)
      f :: t

/- Drop trailing blank (empty) lines. -/
def dropTrailingBlank (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (fun l => l.isEmpty)).reverse

/- Drop leading blank (empty) lines. -/
def dropLeadingBlank (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (fun l => l.isEmpty)

/- Rejoin lines with the newline separator. -/
def joinNL : List (List Char) → List Char
  | []      => []
  | [l]     => l
  | l :: ls => l ++ '\n' :: joinNL ls

/- The deep model of the standard normalization (A-reference, validated equal to
   the real library routine by axiom_check.py / G-AX): split into lines, compute
   the common indentation of the lines AFTER the first, strip that indentation
   while stripping the first line, then drop surrounding blank lines and rejoin.
   The common indentation is taken over the lines after the first so that a
   first line that begins at column zero does not force the shared indentation to
   zero — the behaviour the issue requires. -/
def cleanDocModel (text : List Char) : List Char :=
  let lines := splitLines text
  let margin := commonIndent (lines.drop 1)
  let dedented := dedentLines margin lines
  joinNL (dropLeadingBlank (dropTrailingBlank dedented))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Uniformly normalize the indentation of a multi-line block of text. The first
   line is stripped of its leading whitespace; the indentation common to all the
   remaining non-blank lines is removed from those lines; surrounding blank lines
   are dropped. Crucially the common indentation is measured from the lines AFTER
   the first, so a block whose text begins on the very first line is dedented
   correctly rather than left indented.

   The input `text` is read-only (not `mut`): the routine derives a fresh
   normalized sequence and returns it, mutating nothing (directive 5). -/
method normalizeIndentation (text : List Char) return (out : List Char)
  ensures out = cleanDocModel text
  do
    -- impl-start
    return joinNL (dropLeadingBlank (dropTrailingBlank
      (dedentLines (commonIndent ((splitLines text).drop 1)) (splitLines text))))
    -- impl-end

prove_correct normalizeIndentation by
  loom_solve
  unfold cleanDocModel
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

### AUDIT PROTOCOL SUMMARY (velvet, django__django-12155).

SPEC SHAPE: single postcondition `out = cleanDocModel text` where cleanDocModel is a fully concrete, closed, computable deep model (splitLines/commonIndent/dedentLines/dropLeadingBlank/dropTrailingBlank/joinNL) in the pure region. The proof is a pinned `loom_solve; unfold cleanDocModel; rfl`. Verify => definitional equality to the exact model => behavioral equality. There is NO opaque/axiomatized oracle in the postcondition to echo.

SAME_SPEC: all 10 files (9 attacks + atk_pos) confirmed True via swebench_unified.markers.same_spec (velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.

VERIFY RESULTS (bash scripts/lean_verify.sh <f>), run concurrently in batches of <=4:
- atk_1 EXIT=1 FAIL  (prepatch bug: `commonIndent lines`, margin over ALL lines, no drop 1 -> rejected by exact discriminating clause LHS commonIndent(splitLines text) vs RHS commonIndent(List.drop 1 lines)). PREPATCH REPRODUCED.
- atk_2 EXIT=1 FAIL  (identity `return text`).
- atk_3 EXIT=1 FAIL  (dropLeadingBlank omitted; partial-domain).
- atk_4 EXIT=1 FAIL  (dropTrailingBlank omitted).
- atk_5 EXIT=1 FAIL  (off-by-one boundary: margin over lines.drop 2).
- atk_6 EXIT=1 FAIL  (body never dedented: dedentLines none lines).
- atk_7 EXIT=1 FAIL  (control-flow-effect: append spurious trailing '\n').
- atk_8 EXIT=1 FAIL  (control-flow: drop margin from ALL lines incl first, no lstrip of first).
- atk_echo EXIT=1 FAIL  (ungrounded-oracle echo: `return cleanDocModel text`; this impl is behaviorally CORRECT but fails only on proof fragility -- pinned `rfl` yields 'No goals to be solved'. This is verify-CONSERVATIVE, not verify=>incorrect, so no break).
- atk_pos EXIT=0 PASS  (correct fully-inlined single expression; proves spec non-vacuous).
All 8 wrong impls' error messages confirm rfl rejects the exact behavioral divergence (not a syntax artifact); logs retained at atk_*.log.

RESOLVE-RUN LEG: Step 2 of protocol requires materializing+run_resolve on every VERIFYING wrong impl. Zero same-spec wrong impls verify, so this leg is vacuously satisfied -- there is no verifying wrong impl whose refined patch could fail to resolve. patches={} accordingly.

A-LEG AUDIT (the only place verify=>correct could hide): the sole kind-A element is the A-reference cleanDocModel == inspect.cleandoc (no consumed axioms).
- G-AX axiom_check.py: EXIT=0, deep model == real inspect.cleandoc on 17 boundary + 200000 fuzz inputs.
- G-CONF conformance_check.py: EXIT=0, R/I shadow agrees with patch.diff behaviour on 100012 inputs (seed=12155), 0 disagreements.
- INDEPENDENT ADVERSARIAL FUZZ (mine): re-transliterated cleanDocModel from the Lean pure region and compared to real inspect.cleandoc over the modeled domain (space+newline+printables, no tab/\r/\v/\f/unicode-ws) across 7 seeds x 300000 (=2.1M) + 16 targeted boundary shapes -> 0 mismatches. A-reference correspondence to the real callee HOLDS.

REFINEMENT.MD AUDIT: legs A1=R, A2=R+I, A3=A-reference+I, A4=I, A5=I, A6=R+I. No kind-3 (inexpressible-changed-op). The single genuinely-changed op (margin over lines[1:] vs all lines) is modeled DEEPLY (spelled-out cleanDocModel), not hidden behind a consumed axiom. §B views.py site rides the same A-reference; §C confirms no consumed axioms. Correspondence of the A-reference to the real callee (inspect.cleandoc, Lib/inspect.py, called at utils.py:46 / views.py:260) holds per G-AX + independent fuzz above.

VERDICT: SOUND. >=5 distinct wrong impls (8 wrong + 1 correct-echo, spanning partial-domain, boundary, control-flow-effect, off-by-one, identity, prepatch, ungrounded-oracle echo) all verified; none is a verifying-but-wrong impl; the prepatch bug is reproduced and rejected on the discriminating clause; the A-reference is faithful under 2.1M+ independent inputs; refinement.md has no kind-3 leg. verify does NOT diverge from correct for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. The resolve-run break-leg is therefore vacuously satisfied.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The normalization performed here is modeled DEEPLY
--  in the `pure` region as a closed, computable function of its input text:
--  split into lines, find the common leading indentation shared by the lines
--  AFTER the first, remove that indentation from those lines while stripping the
--  first line, then drop surrounding blank lines and rejoin. The standard-library
--  routine this models (an unchanged callee the routine delegates to) is an
--  A-reference: the deep model `cleanDocModel` is validated equal to the real
--  library routine by axiom_check.py / G-AX. Nothing is consumed as an axiom —
--  see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Number of leading space characters of a line. -/
def leadingSpaces : List Char → Nat
  | []      => 0
  | c :: cs => if c = ' ' then leadingSpaces cs + 1 else 0

/- Drop the leading space characters of a line. -/
def stripLeadingSpaces : List Char → List Char
  | []      => []
  | c :: cs => if c = ' ' then stripLeadingSpaces cs else c :: cs

/- A line "has content" iff it contains at least one non-space character, i.e.
   stripping its leading spaces leaves something. -/
def hasContent (l : List Char) : Bool := !(stripLeadingSpaces l).isEmpty

/- Split a character sequence into lines on the newline separator. Always
   returns at least one line (an empty sequence is a single empty line). -/
def splitLines : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
      let rest := splitLines cs
      if c = '\n' then [] :: rest
      else
        match rest with
        | []      => [[c]]
        | r :: rs => (c :: r) :: rs

/- The common leading indentation shared by the content lines of a list: the
   minimum number of leading spaces over the lines that have content, or `none`
   when there is no such line. -/
def commonIndent : List (List Char) → Option Nat
  | []      => none
  | l :: ls =>
      let rest := commonIndent ls
      if hasContent l then
        match rest with
        | none   => some (leadingSpaces l)
        | some m => some (Nat.min (leadingSpaces l) m)
      else rest

/- Remove the common indentation: always strip the leading spaces of the first
   line; remove `margin` leading characters from every subsequent line when a
   common indentation exists (otherwise leave the subsequent lines untouched). -/
def dedentLines (margin : Option Nat) : List (List Char) → List (List Char)
  | []            => []
  | first :: tail =>
      let f := stripLeadingSpaces first
      let t := match margin with
        | none   => tail
        | some m => tail.map (fun l => l.drop m)
      f :: t

/- Drop trailing blank (empty) lines. -/
def dropTrailingBlank (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (fun l => l.isEmpty)).reverse

/- Drop leading blank (empty) lines. -/
def dropLeadingBlank (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (fun l => l.isEmpty)

/- Rejoin lines with the newline separator. -/
def joinNL : List (List Char) → List Char
  | []      => []
  | [l]     => l
  | l :: ls => l ++ '\n' :: joinNL ls

/- The deep model of the standard normalization (A-reference, validated equal to
   the real library routine by axiom_check.py / G-AX): split into lines, compute
   the common indentation of the lines AFTER the first, strip that indentation
   while stripping the first line, then drop surrounding blank lines and rejoin.
   The common indentation is taken over the lines after the first so that a
   first line that begins at column zero does not force the shared indentation to
   zero — the behaviour the issue requires. -/
def cleanDocModel (text : List Char) : List Char :=
  let lines := splitLines text
  let margin := commonIndent (lines.drop 1)
  let dedented := dedentLines margin lines
  joinNL (dropLeadingBlank (dropTrailingBlank dedented))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Uniformly normalize the indentation of a multi-line block of text. The first
   line is stripped of its leading whitespace; the indentation common to all the
   remaining non-blank lines is removed from those lines; surrounding blank lines
   are dropped. Crucially the common indentation is measured from the lines AFTER
   the first, so a block whose text begins on the very first line is dedented
   correctly rather than left indented.

   The input `text` is read-only (not `mut`): the routine derives a fresh
   normalized sequence and returns it, mutating nothing (directive 5). -/
method normalizeIndentation (text : List Char) return (out : List Char)
  ensures out = cleanDocModel text
  do
    -- impl-start
    return joinNL (dropLeadingBlank (dropTrailingBlank
      (dedentLines (commonIndent ((splitLines text).drop 1)) (splitLines text))))
    -- impl-end

prove_correct normalizeIndentation by
  loom_solve
  unfold cleanDocModel
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

### AUDIT PROTOCOL SUMMARY (velvet, django__django-12155).

SPEC SHAPE: single postcondition `out = cleanDocModel text` where cleanDocModel is a fully concrete, closed, computable deep model (splitLines/commonIndent/dedentLines/dropLeadingBlank/dropTrailingBlank/joinNL) in the pure region. The proof is a pinned `loom_solve; unfold cleanDocModel; rfl`. Verify => definitional equality to the exact model => behavioral equality. There is NO opaque/axiomatized oracle in the postcondition to echo.

SAME_SPEC: all 10 files (9 attacks + atk_pos) confirmed True via swebench_unified.markers.same_spec (velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.

VERIFY RESULTS (bash scripts/lean_verify.sh <f>), run concurrently in batches of <=4:
- atk_1 EXIT=1 FAIL  (prepatch bug: `commonIndent lines`, margin over ALL lines, no drop 1 -> rejected by exact discriminating clause LHS commonIndent(splitLines text) vs RHS commonIndent(List.drop 1 lines)). PREPATCH REPRODUCED.
- atk_2 EXIT=1 FAIL  (identity `return text`).
- atk_3 EXIT=1 FAIL  (dropLeadingBlank omitted; partial-domain).
- atk_4 EXIT=1 FAIL  (dropTrailingBlank omitted).
- atk_5 EXIT=1 FAIL  (off-by-one boundary: margin over lines.drop 2).
- atk_6 EXIT=1 FAIL  (body never dedented: dedentLines none lines).
- atk_7 EXIT=1 FAIL  (control-flow-effect: append spurious trailing '\n').
- atk_8 EXIT=1 FAIL  (control-flow: drop margin from ALL lines incl first, no lstrip of first).
- atk_echo EXIT=1 FAIL  (ungrounded-oracle echo: `return cleanDocModel text`; this impl is behaviorally CORRECT but fails only on proof fragility -- pinned `rfl` yields 'No goals to be solved'. This is verify-CONSERVATIVE, not verify=>incorrect, so no break).
- atk_pos EXIT=0 PASS  (correct fully-inlined single expression; proves spec non-vacuous).
All 8 wrong impls' error messages confirm rfl rejects the exact behavioral divergence (not a syntax artifact); logs retained at atk_*.log.

RESOLVE-RUN LEG: Step 2 of protocol requires materializing+run_resolve on every VERIFYING wrong impl. Zero same-spec wrong impls verify, so this leg is vacuously satisfied -- there is no verifying wrong impl whose refined patch could fail to resolve. patches={} accordingly.

A-LEG AUDIT (the only place verify=>correct could hide): the sole kind-A element is the A-reference cleanDocModel == inspect.cleandoc (no consumed axioms).
- G-AX axiom_check.py: EXIT=0, deep model == real inspect.cleandoc on 17 boundary + 200000 fuzz inputs.
- G-CONF conformance_check.py: EXIT=0, R/I shadow agrees with patch.diff behaviour on 100012 inputs (seed=12155), 0 disagreements.
- INDEPENDENT ADVERSARIAL FUZZ (mine): re-transliterated cleanDocModel from the Lean pure region and compared to real inspect.cleandoc over the modeled domain (space+newline+printables, no tab/\r/\v/\f/unicode-ws) across 7 seeds x 300000 (=2.1M) + 16 targeted boundary shapes -> 0 mismatches. A-reference correspondence to the real callee HOLDS.

REFINEMENT.MD AUDIT: legs A1=R, A2=R+I, A3=A-reference+I, A4=I, A5=I, A6=R+I. No kind-3 (inexpressible-changed-op). The single genuinely-changed op (margin over lines[1:] vs all lines) is modeled DEEPLY (spelled-out cleanDocModel), not hidden behind a consumed axiom. §B views.py site rides the same A-reference; §C confirms no consumed axioms. Correspondence of the A-reference to the real callee (inspect.cleandoc, Lib/inspect.py, called at utils.py:46 / views.py:260) holds per G-AX + independent fuzz above.

VERDICT: SOUND. >=5 distinct wrong impls (8 wrong + 1 correct-echo, spanning partial-domain, boundary, control-flow-effect, off-by-one, identity, prepatch, ungrounded-oracle echo) all verified; none is a verifying-but-wrong impl; the prepatch bug is reproduced and rejected on the discriminating clause; the A-reference is faithful under 2.1M+ independent inputs; refinement.md has no kind-3 leg. verify does NOT diverge from correct for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec: out = cleanDocModel text, a deep model of the post-patch callee inspect.cleandoc (admindocs/utils.py:46, views.py:260). Verified: (1) same_spec(Solution, prepatch, velvet)=True — spec region byte-identical, and prepatch encodes the pre-fix margin-over-all-lines behavior and fails the frozen spec, so the discriminating fix (margin over lines.drop 1 = lines[1:]) is genuinely pinned. (2) Solution.lean elaborates exit 0, prove_correct closes by rfl (impl computes cleanDocModel verbatim). (3) axiom_check.py (G-AX) passes: deep model == real inspect.cleandoc on 17 boundary + 200000 fuzz. (4) Independent fuzz over the declared domain: 0 divergences in 700k inputs. The only divergences are out-of-declared-domain (tabs/\r/Unicode ws), openly documented in mapping.md §2.1 (the real cleandoc's expandtabs step is not modeled but the domain is restricted to tab-free space-indented \n-separated text, which is exactly what post-expandtabs Python docstrings and the F2P test inputs reduce to). This is a disclosed domain restriction honored by G-AX and G-CONF, not spec drift. Modeled function agrees with the real callee on all in-scope inputs. Verdict FAITHFUL.

Counterexample / evidence:

```
In-domain: none found. 200k random + 500k targeted in-domain fuzz (ragged indentation, blank lines, first-line-at-col-0) plus 17 boundary + 200k G-AX fuzz all agree: cleanDocModel == inspect.cleandoc. Out-of-domain (disclaimed): inspect.cleandoc('a\t  ')='a         ' vs cleanDocModel='a\t  '.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold lines, no patched file paths, no patched def/class symbols in view). same_spec(Solution, Solution_prepatch)=True — discriminator is entirely in the elided impl. Crucially, the public problem_statement already discloses the ENTIRE behavioral fix verbatim in code: it names the culprit `indent = min(... for line in lines if line.lstrip())`, states 'the indentation of the first line is 0', and gives the solution 'skip the first line: ... for line in lines[1:] ...'. The spec view models exactly this (margin over lines.drop 1) and its comments ('common indentation measured from the lines AFTER the first', 'the behaviour the issue requires') stay strictly within that public disclosure. The hints-only implementation choice `inspect.cleandoc` is NOT named in the spec view — comments say only 'standard-library routine' abstractly, and the pure helper is `cleanDocModel`, a generic descriptive name (clean doc[string]), not a verbatim echo of the imported/called symbol `cleandoc`; it discloses nothing about the fix beyond what the public issue already provides. Nothing in the spec view leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
