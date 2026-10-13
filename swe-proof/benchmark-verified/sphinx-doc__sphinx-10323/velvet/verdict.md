# P2 adversarial audit — sphinx-doc__sphinx-10323

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so there is no verifying-but-wrong impl whose faithful patch could fail to resolve. The verify=>correct direction was additionally closed concretely: the positive control's faithful patch (identical to the gold filter-reorder patch) RESOLVES under the official harness (run_resolve: RESOLVED=True, COMPLETED=True).
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,12 +77,10 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
+    let withHead := addPrefix prefixText body
     let withTail := addSuffix suffixText withHead
-    return joinLines withTail
+    let trimmed  := removeIndent indent withTail
+    return joinLines trimmed
     -- impl-end
 
 prove_correct assembleBlock by
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,12 +77,10 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
     let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
-    return joinLines withTail
+    let withTail := addSuffix suffixText trimmed
+    let withHead := addPrefix prefixText withTail
+    return joinLines withHead
     -- impl-end
 
 prove_correct assembleBlock by
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,10 +77,7 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
+    let withHead := addPrefix prefixText body
     let withTail := addSuffix suffixText withHead
     return joinLines withTail
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,12 +77,7 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
-    return joinLines withTail
+    return joinLines body
     -- impl-end
 
 prove_correct assembleBlock by
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,11 +77,9 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
+    let withHead := addPrefix prefixText body
+    let trimmed  := removeIndent indent withHead
+    let withTail := addSuffix suffixText trimmed
     return joinLines withTail
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,12 +77,9 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
     let trimmed  := removeIndent indent body
     let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
-    return joinLines withTail
+    return joinLines withHead
     -- impl-end
 
 prove_correct assembleBlock by
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,12 +77,13 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
-    return joinLines withTail
+    match indent with
+    | none   => return joinLines body
+    | some _ =>
+      let trimmed  := removeIndent indent body
+      let withHead := addPrefix prefixText trimmed
+      let withTail := addSuffix suffixText withHead
+      return joinLines withTail
     -- impl-end
 
 prove_correct assembleBlock by
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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,11 +77,9 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
+    let withHead := addPrefix prefixText body
+    let trimmed  := removeIndent indent withHead
+    let withTail := addSuffix suffixText trimmed
     return joinLines withTail
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,11 +77,9 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
     let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
+    let withHead := addPrefix suffixText trimmed
+    let withTail := addSuffix prefixText withHead
     return joinLines withTail
     -- impl-end
 
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The three line-list transformations composed here are
@@ -77,12 +77,8 @@
   ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
   do
     -- impl-start
-    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
-    -- before/after lines added, so they escape the removal.
-    let trimmed  := removeIndent indent body
-    let withHead := addPrefix prefixText trimmed
-    let withTail := addSuffix suffixText withHead
-    return joinLines withTail
+    let t := removeIndent indent body
+    return joinLines (addPrefix prefixText (addSuffix suffixText t))
     -- impl-end
 
 prove_correct assembleBlock by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The three line-list transformations composed here are
--  modeled DEEPLY in the `pure` region as closed, computable functions of their
--  inputs: removing a chosen amount of leading indentation from each line of a
--  body, adding one caller-supplied line before the body, and adding one
--  caller-supplied line after it. Each is an unchanged library routine the
--  assembly delegates to, modeled as an A-reference: `removeIndent`, `addPrefix`
--  and `addSuffix` are validated equal to the real library routines by
--  axiom_check.py / G-AX. Nothing is consumed as an axiom — see refinement.md §C
--  and mapping.md §3.)
-- axioms-end

-- pure-start
/- Remove `n` leading characters from a single line. A line that is emptied by
   the removal but originally carried a trailing newline keeps that newline (so
   a blank separator line is preserved rather than collapsed away). -/
def removeIndentLine (n : Nat) (line : List Char) : List Char :=
  let dropped := line.drop n
  if dropped.isEmpty && (line.getLast? == some '\n') then ['\n'] else dropped

/- Remove `n` leading characters from every line of the body. When no indentation
   amount is supplied the body is left untouched. -/
def removeIndent (n : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match n with
  | none   => lines
  | some k => lines.map (removeIndentLine k)

/- Add one caller-supplied line (terminated by a newline) before the body. An
   empty text adds nothing. -/
def addPrefix (prefixText : List Char) (lines : List (List Char)) : List (List Char) :=
  if prefixText.isEmpty then lines else (prefixText ++ ['\n']) :: lines

/- Add one caller-supplied line (terminated by a newline) after the body. An
   empty text adds nothing. -/
def addSuffix (suffixText : List Char) (lines : List (List Char)) : List (List Char) :=
  if suffixText.isEmpty then lines else lines ++ [suffixText ++ ['\n']]

/- Concatenate the lines back into a single character sequence. Each line by now
   carries its own terminating newline, so joining is plain concatenation.
   Front-recursive so a single unfold is available (the Velvet fold pattern). -/
def joinLines : List (List Char) → List Char
  | []      => []
  | l :: ls => l ++ joinLines ls

@[grind] lemma joinLines_nil : joinLines [] = [] := rfl
@[grind] lemma joinLines_cons (l : List Char) (ls : List (List Char)) :
    joinLines (l :: ls) = l ++ joinLines ls := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble an included block of text. The body has a chosen amount of leading
   indentation removed from each of its lines; then a caller-supplied line is
   added before the body and another after it. Crucially, the indentation
   removal applies ONLY to the body — the lines added before and after are
   exempt, so their own leading whitespace is preserved exactly as supplied.
   The result is the assembled lines concatenated into one character sequence.

   All four inputs are inspected only (none `mut`): the routine derives a fresh
   assembled sequence and returns it, mutating nothing (directive 5). `indent`
   is `none` when no indentation amount is supplied; `prefixText`/`suffixText`
   are empty when nothing is to be added. -/
method assembleBlock (body : List (List Char)) (prefixText : List Char)
    (suffixText : List Char) (indent : Option Nat) return (out : List Char)
  ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
  do
    -- impl-start
    return joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
    -- impl-end

prove_correct assembleBlock by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: single EXACT functional-equation postcondition `ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))`. All four spec functions (removeIndent/removeIndentLine, addPrefix, addSuffix, joinLines) are concrete computable `def`s in the pure region -- NO opaque/axiomatized oracle to echo. axioms=[]; three A-reference deep models only. This is an extremely tight spec: any impl-region computation must equal the exact composition in the exact order.

SAME-SPEC: all 10 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend); only the impl region differs, axioms/pure/pre/post byte-identical.

### VERIFICATIONS (scripts/lean_verify.sh <f>, run concurrently <=4 at a time; exit codes captured):
- atk_1 (PREPATCH BUG: dedent LAST over assembled block)  -> rc=1 FAIL (unsolved goals @ return). Reproduces the gold bug.
- atk_2 (swap prepend/append order: append then prepend)   -> rc=1 FAIL. Behaviorally CORRECT (addPrefix/addSuffix commute by list assoc) but grind does not auto-prove the commutation -> correct-but-unverifying (false negative; irrelevant to verify=>correct).
- atk_3 (skip dedent entirely)                             -> rc=1 FAIL (unsolved goals).
- atk_4 (ungrounded/identity: joinLines body)              -> rc=1 FAIL (unsolved goals).
- atk_5 (partial reorder: dedent after prepend, before append) -> rc=1 FAIL.
- atk_6 (drop suffix/append)                               -> rc=1 FAIL.
- atk_7 (control-flow-effect: match indent; on none forget prefix/suffix) -> rc=1 FAIL.
- atk_8 (boundary: dedent applied to withHead so prefix trimmed too) -> rc=1 FAIL.
- atk_9 (boundary: swap prefix/suffix TEXTS)               -> rc=1 FAIL.
- atk_10 (swap prepend/append, nested-expr form)           -> rc=1 FAIL. Behaviorally correct commuted variant; unverifying like atk_2.
- pos.lean (correct, restructured single nested expression) -> rc=0 PASS (spec non-vacuous / satisfiable).
All 8 genuinely-wrong impls fail with 'error: unsolved goals' at the return (genuine postcondition violations, not syntax/elaboration errors).

RESOLVE STEP: no wrong impl VERIFIES, so the protocol's 'materialize faithful patch and run_resolve for every verifying wrong impl' is vacuously satisfied (patches={}). To positively close verify=>correct I ran the positive control's faithful patch through the OFFICIAL harness. The correct impl transliterates exactly to the gold change (move dedent_filter before prepend/append in the filters list), i.e. the verbatim gold patch. Command: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-10323', gold_patch, timeout=1800, retries=0). RESULT: RESOLVED=True, COMPLETED=True, note='resolved'. So verifying against this spec => resolves.

REFINEMENT AUDIT (refinement.md / mapping.md against real repo @ base_commit 31eba1a...; verified 07983a5a HEAD is the base worktree): every leg is R / A-reference / I -- NO A-consumed axiom, NO kind-3 (inexpressible-changed-op). A-reference correspondence to real callees CONFIRMED: dedent_lines(lines,k) body = per-line line[dedent:] with the 'emptied line keeps lone \n' special case == removeIndentLine; prepend_filter inserts prepend+'\n' at 0 == addPrefix; append_filter appends append+'\n' == addSuffix; ''.join == joinLines. The genuinely-changed operation (relative ORDER of dedent vs prepend/append) is expressed DIRECTLY by the do-block order (A3 before A4/A5), not hidden behind an axiom. meta.json G-AX=pass (12 boundary bodies + 20000 fuzz), G-CONF=pass (100010 inputs, 0 disagreements), G-DIFF=pass.

CONCLUSION: no verifying-but-wrong impl found across the prepatch bug + 4-6+ distinct wrong-impl classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, skip-op, drop-op, partial-reorder); positive control verifies AND its faithful/gold patch resolves. verify=>correct holds. Spec is SOUND (refinement-fidelity, A-legs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so there is no verifying-but-wrong impl whose faithful patch could fail to resolve. The verify=>correct direction was additionally closed concretely: the positive control's faithful patch (identical to the gold filter-reorder patch) RESOLVES under the official harness (run_resolve: RESOLVED=True, COMPLETED=True).
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The three line-list transformations composed here are
--  modeled DEEPLY in the `pure` region as closed, computable functions of their
--  inputs: removing a chosen amount of leading indentation from each line of a
--  body, adding one caller-supplied line before the body, and adding one
--  caller-supplied line after it. Each is an unchanged library routine the
--  assembly delegates to, modeled as an A-reference: `removeIndent`, `addPrefix`
--  and `addSuffix` are validated equal to the real library routines by
--  axiom_check.py / G-AX. Nothing is consumed as an axiom — see refinement.md §C
--  and mapping.md §3.)
-- axioms-end

-- pure-start
/- Remove `n` leading characters from a single line. A line that is emptied by
   the removal but originally carried a trailing newline keeps that newline (so
   a blank separator line is preserved rather than collapsed away). -/
def removeIndentLine (n : Nat) (line : List Char) : List Char :=
  let dropped := line.drop n
  if dropped.isEmpty && (line.getLast? == some '\n') then ['\n'] else dropped

/- Remove `n` leading characters from every line of the body. When no indentation
   amount is supplied the body is left untouched. -/
def removeIndent (n : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match n with
  | none   => lines
  | some k => lines.map (removeIndentLine k)

/- Add one caller-supplied line (terminated by a newline) before the body. An
   empty text adds nothing. -/
def addPrefix (prefixText : List Char) (lines : List (List Char)) : List (List Char) :=
  if prefixText.isEmpty then lines else (prefixText ++ ['\n']) :: lines

/- Add one caller-supplied line (terminated by a newline) after the body. An
   empty text adds nothing. -/
def addSuffix (suffixText : List Char) (lines : List (List Char)) : List (List Char) :=
  if suffixText.isEmpty then lines else lines ++ [suffixText ++ ['\n']]

/- Concatenate the lines back into a single character sequence. Each line by now
   carries its own terminating newline, so joining is plain concatenation.
   Front-recursive so a single unfold is available (the Velvet fold pattern). -/
def joinLines : List (List Char) → List Char
  | []      => []
  | l :: ls => l ++ joinLines ls

@[grind] lemma joinLines_nil : joinLines [] = [] := rfl
@[grind] lemma joinLines_cons (l : List Char) (ls : List (List Char)) :
    joinLines (l :: ls) = l ++ joinLines ls := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble an included block of text. The body has a chosen amount of leading
   indentation removed from each of its lines; then a caller-supplied line is
   added before the body and another after it. Crucially, the indentation
   removal applies ONLY to the body — the lines added before and after are
   exempt, so their own leading whitespace is preserved exactly as supplied.
   The result is the assembled lines concatenated into one character sequence.

   All four inputs are inspected only (none `mut`): the routine derives a fresh
   assembled sequence and returns it, mutating nothing (directive 5). `indent`
   is `none` when no indentation amount is supplied; `prefixText`/`suffixText`
   are empty when nothing is to be added. -/
method assembleBlock (body : List (List Char)) (prefixText : List Char)
    (suffixText : List Char) (indent : Option Nat) return (out : List Char)
  ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
  do
    -- impl-start
    return joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
    -- impl-end

prove_correct assembleBlock by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: single EXACT functional-equation postcondition `ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))`. All four spec functions (removeIndent/removeIndentLine, addPrefix, addSuffix, joinLines) are concrete computable `def`s in the pure region -- NO opaque/axiomatized oracle to echo. axioms=[]; three A-reference deep models only. This is an extremely tight spec: any impl-region computation must equal the exact composition in the exact order.

SAME-SPEC: all 10 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend); only the impl region differs, axioms/pure/pre/post byte-identical.

### VERIFICATIONS (scripts/lean_verify.sh <f>, run concurrently <=4 at a time; exit codes captured):
- atk_1 (PREPATCH BUG: dedent LAST over assembled block)  -> rc=1 FAIL (unsolved goals @ return). Reproduces the gold bug.
- atk_2 (swap prepend/append order: append then prepend)   -> rc=1 FAIL. Behaviorally CORRECT (addPrefix/addSuffix commute by list assoc) but grind does not auto-prove the commutation -> correct-but-unverifying (false negative; irrelevant to verify=>correct).
- atk_3 (skip dedent entirely)                             -> rc=1 FAIL (unsolved goals).
- atk_4 (ungrounded/identity: joinLines body)              -> rc=1 FAIL (unsolved goals).
- atk_5 (partial reorder: dedent after prepend, before append) -> rc=1 FAIL.
- atk_6 (drop suffix/append)                               -> rc=1 FAIL.
- atk_7 (control-flow-effect: match indent; on none forget prefix/suffix) -> rc=1 FAIL.
- atk_8 (boundary: dedent applied to withHead so prefix trimmed too) -> rc=1 FAIL.
- atk_9 (boundary: swap prefix/suffix TEXTS)               -> rc=1 FAIL.
- atk_10 (swap prepend/append, nested-expr form)           -> rc=1 FAIL. Behaviorally correct commuted variant; unverifying like atk_2.
- pos.lean (correct, restructured single nested expression) -> rc=0 PASS (spec non-vacuous / satisfiable).
All 8 genuinely-wrong impls fail with 'error: unsolved goals' at the return (genuine postcondition violations, not syntax/elaboration errors).

RESOLVE STEP: no wrong impl VERIFIES, so the protocol's 'materialize faithful patch and run_resolve for every verifying wrong impl' is vacuously satisfied (patches={}). To positively close verify=>correct I ran the positive control's faithful patch through the OFFICIAL harness. The correct impl transliterates exactly to the gold change (move dedent_filter before prepend/append in the filters list), i.e. the verbatim gold patch. Command: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-10323', gold_patch, timeout=1800, retries=0). RESULT: RESOLVED=True, COMPLETED=True, note='resolved'. So verifying against this spec => resolves.

REFINEMENT AUDIT (refinement.md / mapping.md against real repo @ base_commit 31eba1a...; verified 07983a5a HEAD is the base worktree): every leg is R / A-reference / I -- NO A-consumed axiom, NO kind-3 (inexpressible-changed-op). A-reference correspondence to real callees CONFIRMED: dedent_lines(lines,k) body = per-line line[dedent:] with the 'emptied line keeps lone \n' special case == removeIndentLine; prepend_filter inserts prepend+'\n' at 0 == addPrefix; append_filter appends append+'\n' == addSuffix; ''.join == joinLines. The genuinely-changed operation (relative ORDER of dedent vs prepend/append) is expressed DIRECTLY by the do-block order (A3 before A4/A5), not hidden behind an axiom. meta.json G-AX=pass (12 boundary bodies + 20000 fuzz), G-CONF=pass (100010 inputs, 0 disagreements), G-DIFF=pass.

CONCLUSION: no verifying-but-wrong impl found across the prepatch bug + 4-6+ distinct wrong-impl classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, skip-op, drop-op, partial-reorder); positive control verifies AND its faithful/gold patch resolves. verify=>correct holds. Spec is SOUND (refinement-fidelity, A-legs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Role: faithfulness-break attacker (does the modeled function disagree with the real callee / drift too strong?). Bundle: sphinx-doc__sphinx-10323 (velvet).

Modeled function `assembleBlock` specifies out = joinLines(addSuffix suffixText (addPrefix prefixText (removeIndent indent body))), i.e. the patched filter order dedent -> prepend -> append -> ''.join. The gold patch reorders the `filters` list in LiteralIncludeReader.read so dedent_filter runs BEFORE prepend/append (verified byte-identical to dataset patch).

### VERIFICATION PERFORMED (against the REAL repo at base_commit 31eba1a76, worktree):
1. same_spec(Solution, Solution_prepatch, lean tables) = True => spec region is frozen/byte-identical; the spec was not weakened relative to the discriminating prepatch.
2. Solution.lean elaborates clean (lean_verify.sh exit 0). Solution_prepatch.lean FAILS with the expected G-DIFF goal joinLines(removeIndent indent (addSuffix.. (addPrefix.. body))) = joinLines(addSuffix.. (addPrefix.. (removeIndent indent body))) -> spec is genuinely discriminating on filter order.
3. axiom_check.py (G-AX) run against REAL imported sphinx.directives.code at base_commit: PASS. removeIndent==dedent_lines, addPrefix==prepend_filter, addSuffix==append_filter over 12 boundary bodies + 20000 fuzz. Deep models are faithful to the real callees.
4. conformance_check.py (G-CONF) run against REAL PATCHED read(): PASS, 0 disagreements over 100010 inputs (seed 10323).
5. INDEPENDENT adversarial differential test (my own, not the pinned fuzzers): 5040 cases over hostile bodies (CR '\r', VT '\v', FF '\f', 0x1c, NEL, unicode/emoji, no-trailing-newline, blank/whitespace-only lines) x prepends/appends with tabs/CR/unicode x dedents {None,0..10}, comparing the exact Lean model transliteration against the real filters (dedent_filter/prepend_filter/append_filter) composed directly over `body` in the patched order. 0 divergences.

NOTE on apparent counterexamples: routing hostile bodies through the G-CONF-style oracle (which re-reads a temp file) produced ~520 '\r'-related mismatches, but these are an artifact of Python universal-newline translation ('\r'->'\n') during file re-read, NOT a spec defect. Such bodies are not fixed points of read_file's splitlines(True) and lie OUTSIDE the modeled domain (mapping.md §2: body = post-selection splitlines(True) output). Applied to the true modeled callee (the filter composition over the given body), the model agrees exactly (test #5). The dedent=None auto-textwrap branch is explicitly excluded from the modeled domain and correctly not claimed.

Conclusion: the modeled function does NOT drift from real repo behavior on any input in the modeled domain. No diverging input found. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous leakage/gold-reconstruction review of the velvet spec view for sphinx-doc__sphinx-10323.

Gold edit: reorder the `filters` list in `LiteralIncludeReader.read` (sphinx/directives/code.py) so `dedent_filter` runs BEFORE `prepend_filter`/`append_filter` — i.e. dedent applies to the body only, not to the prepended/appended boundary lines.

Mechanical screen: G-LEAK meta status = pass ('spec view clean', no failures); re-ran leakage.screen on the live spec_view — clean. No RELAXED_LEAKAGE.md, relaxed_leakage=None. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical; the prepatch differs only inside the elided impl region, so no structural leak via the diff of the two files' spec views). No hints_text present, so no risk of judging against hints.

Semantic judgment (the part the lexical screen can miss):
- The public problem_statement ALREADY discloses the full expected behavior: 'dedent applied only to the literalinclude and not to the prepend and append content' and 'Expect leading white space to be preserved in output.' The desired fixed behavior is therefore public, not a hidden discriminator.
- The spec's `ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))` and the docstring 'indentation removal applies ONLY to the body — the lines added before and after are exempt, so their own leading whitespace is preserved exactly as supplied' are a formalization/paraphrase of that public expected behavior. Formalizing publicly-stated expected behavior is the legitimate function of a spec, not leakage.
- The spec view exposes NO repo-specific edit-localization: no diff markers, no patched path (sphinx/directives/code.py) or module dotted-path, no `filters`-list reordering mechanism, and no real repo symbols. The Lean helpers (removeIndent/addPrefix/addSuffix/joinLines/assembleBlock) are abstract A-reference models, none of which lexically embeds the patched callees (dedent_filter/prepend_filter/append_filter/read). No narration terms (bug/fix/wrong/...).
- All repo-revealing detail (the diff hunk, code.py, dedent_filter, the pre-patch dedent-last ordering) lives only in mapping.md and refinement.md — auditor docs OUTSIDE the consumer spec view — so it does not count as spec-view leakage.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
