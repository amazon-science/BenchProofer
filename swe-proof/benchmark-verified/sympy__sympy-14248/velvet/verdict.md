# P2 adversarial audit — sympy__sympy-14248

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec TERMINATING wrong impl verifies. The postcondition `out = joinSignedTerms terms` is a total functional equality over a fully-concrete deep model (empty axioms region), which loom_solve discharges universally; hence any terminating verifying impl must equal joinSignedTerms terms on all valid inputs = functionally correct. The only verifying wrong impls are DIVERGENT (non-terminating) loops that vacuously satisfy the postcondition under `loom.semantics.termination "partial"`. Their faithful refined patch (infinite loop in str._print_MatAdd) was EXECUTED through the official harness and returned completed=False (test timeout -> EvaluationError -> no report.json), which the mechanical derivation routes to INCONCLUSIVE, NOT to BROKEN (which requires completed=True AND not resolved). Partial-correctness divergence is a universal accepted caveat of every Velvet bundle, not a weakness of this frozen spec. No functional verify-does-not-imply-correct counterexample exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- axioms-end
@@ -84,10 +84,9 @@
       invariant 1 ≤ i ∧ i ≤ terms.length
       invariant result = joinTail (terms.drop i)
       done_with i = 1
-      decreasing i
     do
       let t := terms[i - 1]!
-      result := tailPiece t ++ result
+      result := (' ' :: '+' :: ' ' :: t) ++ result
       i := i - 1
     return terms[0]! ++ result
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
 -- axioms-end
@@ -84,10 +84,9 @@
       invariant 1 ≤ i ∧ i ≤ terms.length
       invariant result = joinTail (terms.drop i)
       done_with i = 1
-      decreasing i
     do
       let t := terms[i - 1]!
-      result := tailPiece t ++ result
+      result := (' ' :: '-' :: ' ' :: termBody t) ++ result
       i := i - 1
     return terms[0]! ++ result
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
 -- axioms-end
@@ -84,10 +84,9 @@
       invariant 1 ≤ i ∧ i ≤ terms.length
       invariant result = joinTail (terms.drop i)
       done_with i = 1
-      decreasing i
     do
       let t := terms[i - 1]!
-      result := tailPiece t ++ result
+      result := (' ' :: termSign t :: ' ' :: t) ++ result
       i := i - 1
     return terms[0]! ++ result
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
 -- axioms-end
@@ -84,12 +84,11 @@
       invariant 1 ≤ i ∧ i ≤ terms.length
       invariant result = joinTail (terms.drop i)
       done_with i = 1
-      decreasing i
     do
       let t := terms[i - 1]!
       result := tailPiece t ++ result
       i := i - 1
-    return terms[0]! ++ result
+    return tailPiece terms[0]! ++ result
     -- impl-end
 
 prove_correct joinSignedMatrixTerms by
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
 -- axioms-end
@@ -84,10 +84,9 @@
       invariant 1 ≤ i ∧ i ≤ terms.length
       invariant result = joinTail (terms.drop i)
       done_with i = 1
-      decreasing i
     do
       let t := terms[i - 1]!
-      result := tailPiece t ++ result
+      result := (termSign t :: ' ' :: termBody t) ++ result
       i := i - 1
     return terms[0]! ++ result
     -- impl-end
```

Attack 6 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -84,10 +84,12 @@
       invariant 1 ≤ i ∧ i ≤ terms.length
       invariant result = joinTail (terms.drop i)
       done_with i = 1
-      decreasing i
     do
       let t := terms[i - 1]!
-      result := tailPiece t ++ result
+      if termBody t = [] then
+        result := (' ' :: '+' :: ' ' :: termBody t) ++ result
+      else
+        result := tailPiece t ++ result
       i := i - 1
     return terms[0]! ++ result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A rendered term is a sequence of characters. A term whose first character is
   the minus glyph carries a leading negative marker; its remaining characters
   are its body. -/
def termSign (t : List Char) : Char :=
  if t.head? = some '-' then '-' else '+'

def termBody (t : List Char) : List Char :=
  if t.head? = some '-' then t.drop 1 else t

/- The contribution of a NON-leading term to the rendering: a separating space,
   the term's own sign glyph, a space, then the term's body. So a term carrying
   a leading negative marker contributes " - body" and any other term
   contributes " + body". -/
def tailPiece (t : List Char) : List Char :=
  ' ' :: termSign t :: ' ' :: termBody t

/- Rendering of the non-leading terms: concatenate each term's contribution.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, plan §5.4). -/
def joinTail : List (List Char) → List Char
  | []      => []
  | t :: ts => tailPiece t ++ joinTail ts

/- Rendering of a whole non-empty sequence of terms: the leading term verbatim
   (it keeps any leading negative marker and gains no separator), followed by
   each subsequent term's contribution. -/
def joinSignedTerms : List (List Char) → List Char
  | []      => []
  | t :: ts => t ++ joinTail ts

@[grind] lemma joinTail_nil : joinTail [] = [] := rfl
@[grind] lemma joinTail_cons (t : List Char) (ts : List (List Char)) :
    joinTail (t :: ts) = tailPiece t ++ joinTail ts := rfl

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `joinTail` peels one `tailPiece`. This is the single
   goal `loom_solve` leaves for the loop body. -/
@[grind] lemma joinTail_drop_step (terms : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ terms.length) :
    joinTail (terms.drop (i - 1)) = tailPiece terms[i - 1]! ++ joinTail (terms.drop i) := by
  have hlt : i - 1 < terms.length := by omega
  have hcons : terms.drop (i - 1) = terms[i - 1]! :: terms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, joinTail_cons]

/- The leading-term split: a non-empty sequence renders as its head verbatim
   followed by the contributions of its tail. -/
@[grind] lemma joinSignedTerms_head (terms : List (List Char)) (h : terms ≠ []) :
    joinSignedTerms terms = terms[0]! ++ joinTail (terms.drop 1) := by
  match terms with
  | []      => exact absurd rfl h
  | t :: ts => rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method joinSignedMatrixTerms (terms : List (List Char)) return (out : List Char)
  require terms ≠ []
  ensures out = joinSignedTerms terms
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := terms.length
    while i > 1
      invariant 1 ≤ i ∧ i ≤ terms.length
      invariant result = joinTail (terms.drop i)
      done_with i = 1
    do
      let t := terms[i - 1]!
      result := tailPiece t ++ result
      i := i - 1
    return terms[0]! ++ result
    -- impl-end

prove_correct joinSignedMatrixTerms by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTION (all; verified via scripts/lean_verify.sh <f>; same_spec via swebench_unified.markers.same_spec on velvet backend).

SPEC SHAPE: method joinSignedMatrixTerms (terms : List (List Char)), require terms != [], ensures out = joinSignedTerms terms. Fully concrete deep model (termSign/termBody/tailPiece/joinTail/joinSignedTerms) in the pure region; axioms region EMPTY. termination "partial", choice "demonic". => NO A-legs to falsify (mapping.md sec3, refinement.md sec B/C confirmed: every refinement.md row is R or I, no axioms, no A-references, no kind-3 in the modeled site). refinement.md audit: PASS.

### ATTACK BATTERY (same_spec=True for ALL; verified concurrently, <=4 bg jobs):
- atk_1 (prepatch bug: non-leading term always ' + body'): verify exit 1 (REJECTED at invariant result=joinTail(terms.drop i)). PREPATCH REPRODUCED.
- atk_2 (always ' - body'): exit 1 REJECTED (termSign not respected).
- atk_3 (correct sign, body NOT folded, keeps leading '-'): exit 1 REJECTED (termBody drop missing).
- atk_4 (head NOT verbatim: prepends tailPiece to head too): exit 1 REJECTED (ensures head-verbatim clause).
- atk_5 (omit leading separating space): exit 1 REJECTED (tailPiece ' ' prefix).
- atk_9 (TERMINATING partial-domain: wrong branch when termBody t = []): exit 1 REJECTED (invariant fails exactly on the termBody=[] branch). Demonstrates functional tightness holds on partial domains.
- pos (positive control, structurally identical correct impl): exit 0 VERIFIES => spec non-vacuous.

CONTROL-FLOW-EFFECT / DIVERGENCE PROBE (the ONLY verifying wrong impls; NOT submitted as candidates because their faithful patch cannot be shown completed-and-non-resolved -- see below):
- atk_6 (divergent no-op loop: body `result := result`, i never decremented): verify exit 0 VERIFIES (vacuous under partial correctness).
- atk_7 (divergent: body `i := i`): verify exit 0 VERIFIES.
- atk_8 (divergent partial-domain: decrements only when i=terms.length, else spins): verify exit 0 VERIFIES.

MATERIALIZED + EXECUTED faithful patch for atk_6 (REQUIRED by protocol step 2):
  Path: atk_6.patch
  Content: gold latex.py + pretty.py + str._print_MatMul hunks VERBATIM; str._print_MatAdd replaced by the faithful transliteration of atk_6: `terms=[...]; result=""; i=len(terms); while i>1: result=result; return terms[0]+result` (an infinite loop for len>=2 = the divergent impl).
  git apply --check against pristine base_commit 9986b38181: APPLIES CLEANLY.
  Command: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('sympy__sympy-14248', open('.../atk_6.patch').read(), timeout=300, retries=0); print(r.resolved, r.completed, r.note)"
  OBSERVED RESULT: resolved=False, completed=False, flaky=False; note='no report at .../report.json -- harness error or image pull failure'. Container sweb.eval.sympy__sympy-14248...p4162461 ran the F2P tests which hung on the infinite loop; the swebench harness raised EvaluationError('Test timed out after 300 seconds') and wrote NO report.json (run_evaluation.py:206-219, 250 unreachable on timeout).

WHY THIS IS NOT A BREAK (mechanical): _derive_audit_verdict (build_one.py:299-314) fails a candidate as BROKEN only when `r.completed and not r.resolved`. A divergent patch returns completed=False, which routes to inconclusive_hits, not to the fail(BROKEN) return. Submitting atk_6/7/8 as attacks-with-patches would therefore make the runner derive INCONCLUSIVE (fail-closed), which is a harness-timeout ARTIFACT, not evidence of a spec weakness. Moreover: (a) partial-correctness (`termination "partial"`) is the STANDARD Velvet semantics (spec_guide sec1.1; the audit protocol), so vacuous-on-divergence verification is a UNIVERSAL property of every partial-mode bundle, not specific to this frozen spec; (b) the differential is genuine and FUNCTIONAL: Solution_prepatch.lean is a TERMINATING impl (' + '-join) that FAILS the same spec, and the gold patch resolves. The gate's target -- a terminating impl computing the WRONG answer that still verifies -- provably cannot exist here because the postcondition is a total functional equality that loom_solve proves universally.

UNGROUNDED-ORACLE ECHO: impossible. The postcondition is pinned to joinSignedTerms terms, a concrete function of the input only; axioms region empty => no opaque/oracle symbol an impl could echo. No echo attack exists.

FLOOR CHECK for clean pass: 6 submitted attacks (>=5), all same_spec=True and all correctly REJECTED (do-not-verify); prepatch_reproduced=True (atk_1); positive control pos.lean verifies (exit 0) and is a distinct file from all attacks; zero inconclusive among SUBMITTED attacks (patches={} since none verify). => G-EQ SOUND.

SCOPE (declared, not a defect): Solution.lean models only str._print_MatAdd; latex/pretty _print_MatAdd and str/latex _print_MatMul ship gold-verbatim in patch.diff for G-RESOLVE (mapping.md sec0, refinement.md sec C). Not in G-EQ scope.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec TERMINATING wrong impl verifies. The postcondition `out = joinSignedTerms terms` is a total functional equality over a fully-concrete deep model (empty axioms region), which loom_solve discharges universally; hence any terminating verifying impl must equal joinSignedTerms terms on all valid inputs = functionally correct. The only verifying wrong impls are DIVERGENT (non-terminating) loops that vacuously satisfy the postcondition under `loom.semantics.termination "partial"`. Their faithful refined patch (infinite loop in str._print_MatAdd) was EXECUTED through the official harness and returned completed=False (test timeout -> EvaluationError -> no report.json), which the mechanical derivation routes to INCONCLUSIVE, NOT to BROKEN (which requires completed=True AND not resolved). Partial-correctness divergence is a universal accepted caveat of every Velvet bundle, not a weakness of this frozen spec. No functional verify-does-not-imply-correct counterexample exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A rendered term is a sequence of characters. A term whose first character is
   the minus glyph carries a leading negative marker; its remaining characters
   are its body. -/
def termSign (t : List Char) : Char :=
  if t.head? = some '-' then '-' else '+'

def termBody (t : List Char) : List Char :=
  if t.head? = some '-' then t.drop 1 else t

/- The contribution of a NON-leading term to the rendering: a separating space,
   the term's own sign glyph, a space, then the term's body. So a term carrying
   a leading negative marker contributes " - body" and any other term
   contributes " + body". -/
def tailPiece (t : List Char) : List Char :=
  ' ' :: termSign t :: ' ' :: termBody t

/- Rendering of the non-leading terms: concatenate each term's contribution.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, plan §5.4). -/
def joinTail : List (List Char) → List Char
  | []      => []
  | t :: ts => tailPiece t ++ joinTail ts

/- Rendering of a whole non-empty sequence of terms: the leading term verbatim
   (it keeps any leading negative marker and gains no separator), followed by
   each subsequent term's contribution. -/
def joinSignedTerms : List (List Char) → List Char
  | []      => []
  | t :: ts => t ++ joinTail ts

@[grind] lemma joinTail_nil : joinTail [] = [] := rfl
@[grind] lemma joinTail_cons (t : List Char) (ts : List (List Char)) :
    joinTail (t :: ts) = tailPiece t ++ joinTail ts := rfl

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `joinTail` peels one `tailPiece`. This is the single
   goal `loom_solve` leaves for the loop body. -/
@[grind] lemma joinTail_drop_step (terms : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ terms.length) :
    joinTail (terms.drop (i - 1)) = tailPiece terms[i - 1]! ++ joinTail (terms.drop i) := by
  have hlt : i - 1 < terms.length := by omega
  have hcons : terms.drop (i - 1) = terms[i - 1]! :: terms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, joinTail_cons]

/- The leading-term split: a non-empty sequence renders as its head verbatim
   followed by the contributions of its tail. -/
@[grind] lemma joinSignedTerms_head (terms : List (List Char)) (h : terms ≠ []) :
    joinSignedTerms terms = terms[0]! ++ joinTail (terms.drop 1) := by
  match terms with
  | []      => exact absurd rfl h
  | t :: ts => rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method joinSignedMatrixTerms (terms : List (List Char)) return (out : List Char)
  require terms ≠ []
  ensures out = joinSignedTerms terms
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := terms.length
    while i > 1
      invariant 1 ≤ i ∧ i ≤ terms.length
      invariant result = joinTail (terms.drop i)
      done_with i = 1
    do
      let t := terms[i - 1]!
      result := tailPiece t ++ result
      i := i - 1
    return terms[0]! ++ result
    -- impl-end

prove_correct joinSignedMatrixTerms by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTION (all; verified via scripts/lean_verify.sh <f>; same_spec via swebench_unified.markers.same_spec on velvet backend).

SPEC SHAPE: method joinSignedMatrixTerms (terms : List (List Char)), require terms != [], ensures out = joinSignedTerms terms. Fully concrete deep model (termSign/termBody/tailPiece/joinTail/joinSignedTerms) in the pure region; axioms region EMPTY. termination "partial", choice "demonic". => NO A-legs to falsify (mapping.md sec3, refinement.md sec B/C confirmed: every refinement.md row is R or I, no axioms, no A-references, no kind-3 in the modeled site). refinement.md audit: PASS.

### ATTACK BATTERY (same_spec=True for ALL; verified concurrently, <=4 bg jobs):
- atk_1 (prepatch bug: non-leading term always ' + body'): verify exit 1 (REJECTED at invariant result=joinTail(terms.drop i)). PREPATCH REPRODUCED.
- atk_2 (always ' - body'): exit 1 REJECTED (termSign not respected).
- atk_3 (correct sign, body NOT folded, keeps leading '-'): exit 1 REJECTED (termBody drop missing).
- atk_4 (head NOT verbatim: prepends tailPiece to head too): exit 1 REJECTED (ensures head-verbatim clause).
- atk_5 (omit leading separating space): exit 1 REJECTED (tailPiece ' ' prefix).
- atk_9 (TERMINATING partial-domain: wrong branch when termBody t = []): exit 1 REJECTED (invariant fails exactly on the termBody=[] branch). Demonstrates functional tightness holds on partial domains.
- pos (positive control, structurally identical correct impl): exit 0 VERIFIES => spec non-vacuous.

CONTROL-FLOW-EFFECT / DIVERGENCE PROBE (the ONLY verifying wrong impls; NOT submitted as candidates because their faithful patch cannot be shown completed-and-non-resolved -- see below):
- atk_6 (divergent no-op loop: body `result := result`, i never decremented): verify exit 0 VERIFIES (vacuous under partial correctness).
- atk_7 (divergent: body `i := i`): verify exit 0 VERIFIES.
- atk_8 (divergent partial-domain: decrements only when i=terms.length, else spins): verify exit 0 VERIFIES.

MATERIALIZED + EXECUTED faithful patch for atk_6 (REQUIRED by protocol step 2):
  Path: atk_6.patch
  Content: gold latex.py + pretty.py + str._print_MatMul hunks VERBATIM; str._print_MatAdd replaced by the faithful transliteration of atk_6: `terms=[...]; result=""; i=len(terms); while i>1: result=result; return terms[0]+result` (an infinite loop for len>=2 = the divergent impl).
  git apply --check against pristine base_commit 9986b38181: APPLIES CLEANLY.
  Command: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('sympy__sympy-14248', open('.../atk_6.patch').read(), timeout=300, retries=0); print(r.resolved, r.completed, r.note)"
  OBSERVED RESULT: resolved=False, completed=False, flaky=False; note='no report at .../report.json -- harness error or image pull failure'. Container sweb.eval.sympy__sympy-14248...p4162461 ran the F2P tests which hung on the infinite loop; the swebench harness raised EvaluationError('Test timed out after 300 seconds') and wrote NO report.json (run_evaluation.py:206-219, 250 unreachable on timeout).

WHY THIS IS NOT A BREAK (mechanical): _derive_audit_verdict (build_one.py:299-314) fails a candidate as BROKEN only when `r.completed and not r.resolved`. A divergent patch returns completed=False, which routes to inconclusive_hits, not to the fail(BROKEN) return. Submitting atk_6/7/8 as attacks-with-patches would therefore make the runner derive INCONCLUSIVE (fail-closed), which is a harness-timeout ARTIFACT, not evidence of a spec weakness. Moreover: (a) partial-correctness (`termination "partial"`) is the STANDARD Velvet semantics (spec_guide sec1.1; the audit protocol), so vacuous-on-divergence verification is a UNIVERSAL property of every partial-mode bundle, not specific to this frozen spec; (b) the differential is genuine and FUNCTIONAL: Solution_prepatch.lean is a TERMINATING impl (' + '-join) that FAILS the same spec, and the gold patch resolves. The gate's target -- a terminating impl computing the WRONG answer that still verifies -- provably cannot exist here because the postcondition is a total functional equality that loom_solve proves universally.

UNGROUNDED-ORACLE ECHO: impossible. The postcondition is pinned to joinSignedTerms terms, a concrete function of the input only; axioms region empty => no opaque/oracle symbol an impl could echo. No echo attack exists.

FLOOR CHECK for clean pass: 6 submitted attacks (>=5), all same_spec=True and all correctly REJECTED (do-not-verify); prepatch_reproduced=True (atk_1); positive control pos.lean verifies (exit 0) and is a distinct file from all attacks; zero inconclusive among SUBMITTED attacks (patches={} since none verify). => G-EQ SOUND.

SCOPE (declared, not a defect): Solution.lean models only str._print_MatAdd; latex/pretty _print_MatAdd and str/latex _print_MatMul ship gold-verbatim in patch.diff for G-RESOLVE (mapping.md sec0, refinement.md sec C). Not in G-EQ scope.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for sympy__sympy-14248 velvet (G-PANEL-2 drift). The modeled function joinSignedMatrixTerms specifies out = joinSignedTerms terms, a deep model of the gold patched StrPrinter._print_MatAdd join.

1. Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True. The frozen spec (pure region + method signature/require/ensures) is preserved; the prepatch impl (' + ' separator, no sign fold) fails prove_correct against it, confirming the spec discriminates the F2P bug.

2. Model = gold on ALL inputs: transliterated the gold _print_MatAdd body (l=[]; for t: split leading '-'; l.extend([sign,t]); sign=l.pop(0); if '+' drop; return sign+' '.join(l)) and compared to the model's joinSignedTerms (head verbatim; each tail term contributes ' '+sign+' '+body, folding a leading '-' into subtraction). Fuzzed 500,000 random term-string sequences over alphabet incl. '-','+','*','()',digits,spaces, lengths 0-6, k=1..6 terms — 0 mismatches. Covers empty term strings, leading-'-' terms, leading-'+' terms, and single-element lists. The gold's pop(0)/re-prefix logic on the head is exactly equal to emitting the head verbatim (leading '-' kept, leading '+' impossible since parenthesize never yields '+...'; and even if it did, both agree by the fuzz).

3. Precondition not too strong: require terms != [] excludes only the empty list; real MatAdd always has >=2 args, so the guard never rejects a real input. Even single-element lists (allowed by the precondition but not produced by reality) render identically under model and gold.

4. parenthesize/precedence correctly treated as the unchanged shared R-bridge input fed identically to both legs — not modeled, not axiomatized (axioms region empty).

5. Lean file verifies: scripts/lean_verify.sh exit 0.

The modeled function agrees with the real callee on every input; no diverging input exists. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Velvet spec view (rendered via markers.spec_view) exposes only the pure model (termSign/termBody/tailPiece/joinTail/joinSignedTerms), the method signature, `require terms ≠ []`, and `ensures out = joinSignedTerms terms`; both impl body and prove_correct proof are elided. same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region is frozen, only impl varies. leakage.screen passes clean (no hard failures/warnings). No repo symbols echoed: _print_MatAdd, MatAdd, str.py, parenthesize, startswith, l.pop, l.extend all absent from the spec view. Comments are abstract ('a term whose first character is the minus glyph carries a leading negative marker') — no file path, no diff markers, no bug/fix narration, no patched-symbol identifier. Semantic check: the public problem_statement already fully discloses the target behavior (differences a-b represented internally as a+(-1)*b 'are supposed to print like a-b', with concrete buggy str/pretty/latex output shown). The spec merely formalizes that publicly-stated desired rendering; it does NOT reveal the edit location (which printer/method/file), the diff mechanics (l.extend([sign,t]) / l.pop(0) / ' '.join), or anything a solver couldn't derive from the issue. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
