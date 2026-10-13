# P2 adversarial audit — sympy__sympy-13031

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
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Stacking two sparse rectangular blocks edge-to-edge.
 
@@ -103,16 +103,12 @@
   ensures out = hstackBlock A B
   do
     -- impl-start
-    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
-    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
-    -- content at the full summed width.  Otherwise the heights already line up
-    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
-    -- width as the SUM `A.cols + B.cols`.
-    if A.cols = 0 ∧ A.rows ≠ B.rows then
-      return { rows := B.rows, cols := A.cols + B.cols,
+    -- ATTACK: reordered control flow (negated guard); same result as gold.
+    if ¬(A.cols = 0 ∧ A.rows ≠ B.rows) then
+      return { rows := A.rows, cols := A.cols + B.cols,
                entries := A.entries ++ B.entries.map (shiftRight A.cols) }
     else
-      return { rows := A.rows, cols := A.cols + B.cols,
+      return { rows := B.rows, cols := A.cols + B.cols,
                entries := A.entries ++ B.entries.map (shiftRight A.cols) }
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Stacking two sparse rectangular blocks edge-to-edge.
 
@@ -103,12 +103,8 @@
   ensures out = hstackBlock A B
   do
     -- impl-start
-    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
-    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
-    -- content at the full summed width.  Otherwise the heights already line up
-    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
-    -- width as the SUM `A.cols + B.cols`.
-    if A.cols = 0 ∧ A.rows ≠ B.rows then
+    -- ATTACK: broadened degenerate guard (`A.cols = 0` alone).
+    if A.cols = 0 then
       return { rows := B.rows, cols := A.cols + B.cols,
                entries := A.entries ++ B.entries.map (shiftRight A.cols) }
     else
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Stacking two sparse rectangular blocks edge-to-edge.
 
@@ -103,17 +103,10 @@
   ensures out = hstackBlock A B
   do
     -- impl-start
-    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
-    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
-    -- content at the full summed width.  Otherwise the heights already line up
-    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
-    -- width as the SUM `A.cols + B.cols`.
-    if A.cols = 0 ∧ A.rows ≠ B.rows then
-      return { rows := B.rows, cols := A.cols + B.cols,
-               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
-    else
-      return { rows := A.rows, cols := A.cols + B.cols,
-               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
+    -- ATTACK: echo of the deep model (unconditional single return).
+    return { rows := if A.cols = 0 then B.rows else A.rows,
+             cols := A.cols + B.cols,
+             entries := A.entries ++ B.entries.map (shiftRight A.cols) }
     -- impl-end
 
 prove_correct stackHorizontally by
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Stacking two sparse rectangular blocks edge-to-edge.
 
@@ -103,17 +103,10 @@
   ensures out = hstackBlock A B
   do
     -- impl-start
-    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
-    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
-    -- content at the full summed width.  Otherwise the heights already line up
-    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
-    -- width as the SUM `A.cols + B.cols`.
-    if A.cols = 0 ∧ A.rows ≠ B.rows then
-      return { rows := B.rows, cols := A.cols + B.cols,
-               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
-    else
-      return { rows := A.rows, cols := A.cols + B.cols,
-               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
+    -- ATTACK: result height taken as B.rows unconditionally (require makes it
+    -- equal to A.rows whenever A.cols ≠ 0).
+    return { rows := B.rows, cols := A.cols + B.cols,
+             entries := A.entries ++ B.entries.map (shiftRight A.cols) }
     -- impl-end
 
 prove_correct stackHorizontally by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- Stacking two sparse rectangular blocks edge-to-edge.
 
@@ -129,10 +129,8 @@
   ensures out = vstackBlock A B
   do
     -- impl-start
-    -- Symmetric to horizontal stacking: a height-zero `A` whose width disagrees
-    -- is re-measured to `B`'s width and then stacked; otherwise `B`'s rows are
-    -- appended below `A`'s.  Both legs accumulate the height as `A.rows + B.rows`.
-    if A.rows = 0 ∧ A.cols ≠ B.cols then
+    -- ATTACK: broadened degenerate guard on vertical (`A.rows = 0` alone).
+    if A.rows = 0 then
       return { rows := A.rows + B.rows, cols := B.cols,
                entries := A.entries ++ B.entries.map (shiftDown A.rows) }
     else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- Stacking two sparse rectangular blocks edge-to-edge.

   A block has a row count, a column count, and a sparse set of stored entries
   (an entry pins one (row, column) cell to a value; absent cells are zero).

   Horizontal stacking places the second block immediately to the RIGHT of the
   first: the combined block is as tall as the operands and as wide as the SUM
   of their widths, with the second block's stored cells shifted right by the
   first block's width. Vertical stacking is the transpose situation: the second
   block goes BELOW the first, the combined height is the SUM of the heights, and
   the second block's cells shift down by the first block's height.

   A degenerate block — one whose width (for horizontal stacking) or height (for
   vertical stacking) is zero — contributes no cells but STILL contributes its
   measured extent: stacking such a block must accumulate the running width/height
   exactly as a non-degenerate block would, never collapse the result to the shape
   of the other operand alone. This is the property the model pins. -/

-- axioms-start
/- No callee is axiomatized. The stacking behavior is pure shape-and-cell
   arithmetic computed entirely from the two operand blocks (extent addition plus
   a coordinate shift of the second block's stored cells); there is no unchanged
   repository callee whose contract the proof must assume. Both legs of the result
   construction are concrete (refinement.md: every row R or I). Soundness of the
   shape arithmetic is exercised executably against the real callees by
   conformance_check.py. -/
-- axioms-end

-- pure-start
/- A rectangular block: `rows` × `cols`, with `entries` the stored (nonzero)
   cells as `((i, j), v)`. The carrier abstracts over storage form — a value is
   recorded the same way whether the real object stores it densely or sparsely. -/
structure Block where
  rows : Nat
  cols : Nat
  entries : List ((Nat × Nat) × Int)
  deriving DecidableEq, Inhabited, Repr

/- Shift a stored cell to the right by `n` columns (used when a block is placed
   to the right of another of width `n`). -/
def shiftRight (n : Nat) (e : (Nat × Nat) × Int) : (Nat × Nat) × Int :=
  ((e.1.1, e.1.2 + n), e.2)

/- Shift a stored cell down by `n` rows (used when a block is placed below
   another of height `n`). -/
def shiftDown (n : Nat) (e : (Nat × Nat) × Int) : (Nat × Nat) × Int :=
  ((e.1.1 + n, e.1.2), e.2)

/- The block obtained by placing `B` immediately to the right of `A`. Width is
   the SUM of the two widths (so a zero-width `A` still contributes its — zero —
   width and the running total is preserved, never replaced by `B`'s width
   alone). Height is `A`'s, except a zero-width `A` carries no height of its own
   and adopts `B`'s. `B`'s cells move right by `A`'s width. -/
def hstackBlock (A B : Block) : Block :=
  { rows := if A.cols = 0 then B.rows else A.rows,
    cols := A.cols + B.cols,
    entries := A.entries ++ B.entries.map (shiftRight A.cols) }

/- The block obtained by placing `B` immediately below `A`. Height is the SUM of
   the two heights; width is `A`'s, except a zero-height `A` adopts `B`'s width.
   `B`'s cells move down by `A`'s height. -/
def vstackBlock (A B : Block) : Block :=
  { rows := A.rows + B.rows,
    cols := if A.rows = 0 then B.cols else A.cols,
    entries := A.entries ++ B.entries.map (shiftDown A.rows) }

@[grind] lemma hstackBlock_eq (A B : Block) :
    hstackBlock A B =
      { rows := if A.cols = 0 then B.rows else A.rows,
        cols := A.cols + B.cols,
        entries := A.entries ++ B.entries.map (shiftRight A.cols) } := rfl

@[grind] lemma vstackBlock_eq (A B : Block) :
    vstackBlock A B =
      { rows := A.rows + B.rows,
        cols := if A.rows = 0 then B.cols else A.cols,
        entries := A.entries ++ B.entries.map (shiftDown A.rows) } := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Place block `B` immediately to the right of block `A`. `A` and `B` are
   read-only operands (neither is `mut`; the result is a fresh block and the
   inputs are unchanged). The operands are compatible when their heights match,
   OR when `A` is degenerate in width — a zero-width block can be stacked beside
   any block, taking on that block's height. The result must have width equal to
   the SUM of the two widths in every admissible case, so a zero-width `A` never
   collapses the result to `B`'s width alone. -/
method stackHorizontally (A : Block) (B : Block) return (out : Block)
  require A.cols = 0 ∨ A.rows = B.rows
  ensures out = hstackBlock A B
  do
    -- impl-start
    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
    -- content at the full summed width.  Otherwise the heights already line up
    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
    -- width as the SUM `A.cols + B.cols`.
    if A.cols = 0 ∧ A.rows ≠ B.rows then
      return { rows := B.rows, cols := A.cols + B.cols,
               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
    else
      return { rows := A.rows, cols := A.cols + B.cols,
               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
    -- impl-end

prove_correct stackHorizontally by
  loom_solve

/- Place block `B` immediately below block `A`. `A` and `B` are read-only
   operands (neither is `mut`). The operands are compatible when their widths
   match, OR when `A` is degenerate in height. The result must have height equal
   to the SUM of the two heights in every admissible case, so a zero-height `A`
   never collapses the result to `B`'s height alone. -/
method stackVertically (A : Block) (B : Block) return (out : Block)
  require A.rows = 0 ∨ A.cols = B.cols
  ensures out = vstackBlock A B
  do
    -- impl-start
    -- Symmetric to horizontal stacking: a height-zero `A` whose width disagrees
    -- is re-measured to `B`'s width and then stacked; otherwise `B`'s rows are
    -- appended below `A`'s.  Both legs accumulate the height as `A.rows + B.rows`.
    if A.rows = 0 ∧ A.cols ≠ B.cols then
      return { rows := A.rows + B.rows, cols := B.cols,
               entries := A.entries ++ B.entries.map (shiftDown A.rows) }
    else
      return { rows := A.rows + B.rows, cols := A.cols,
               entries := A.entries ++ B.entries.map (shiftDown A.rows) }
    -- impl-end

prove_correct stackVertically by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ (refinement-fidelity / A-leg) audit of velvet sympy__sympy-13031.

SPEC SHAPE (why it is hard to break): postcondition is EXACT functional equality to a TOTAL deep model, `out = hstackBlock A B` / `out = vstackBlock A B`, over a `require` domain (`A.cols=0 ∨ A.rows=B.rows` / transposed) that equals the callee's non-raising domain. Any impl that verifies is therefore behaviourally identical to the total model on the ENTIRE tested domain. meta.json `axioms: []`; the two deep_model_references are tagged kind='deep-model (concrete R/I, not A-reference)'. G-AX legitimately skip (no axiom_check.py; SPEC_GUIDE directive-7 + django-11603 precedent: a deeply-modeled CHANGED function is validated by G-CONF, which git-applies patch.diff first, not by G-AX against the buggy base-commit callee).

A-LEG AUDIT (refinement.md): legs A1/A2/B1/B2 = R (type refinement, (rows,cols,_smat)↔Block bijection), A3/A4/B3/B4 = I (identical concrete op). NO A-consumed, NO A-reference, NO kind-3 rows — consistent with zero axioms. Model↔callee correspondence confirmed empirically: gold patch RESOLVED=True, and the summed-extent arithmetic of hstackBlock/vstackBlock matches post-patch row_join/col_join.

SAME-SPEC: all 12 files (5 verifying attacks + 4 wrong + 2 prepatch + pos-control) same_spec=True (spec regions byte-identical; only impl edited).

### LEAN VERIFY (scripts/lean_verify.sh, 300s cap):
- pos_control EXIT=0 (verifies)
- atk_1 (negated-guard control-flow reorder) EXIT=0
- atk_2 (broadened horizontal guard `A.cols=0`) EXIT=0
- atk_3 (ungrounded-oracle ECHO: unconditional single return of the model form) EXIT=0
- atk_4 (rows:=B.rows unconditional; require forces equality) EXIT=0
- atk_5 (broadened vertical guard `A.rows=0`) EXIT=0
- atk_w1 (boundary: else-branch collapses width to B.cols) EXIT=1 (rejected)
- atk_w2 (wrong shift offset shiftRight B.cols) EXIT=1 (rejected)
- atk_w3 (partial-domain: rows:=A.rows always) EXIT=1 (rejected)
- atk_w4 (partial-domain: drops B's cells) EXIT=1 (rejected)
- prepatch1/prepatch2 EXIT=1 (prepatch bug reproduced: `if A.rows=0 ∨ A.cols=0 then return B` fails summed-extent clause)
The 4 genuinely-wrong impls and both prepatches all FAIL to verify — the exact-equality-to-total-model postcondition is tight; no partial-domain/boundary/effect/echo divergence survives.

### HARNESS RESOLVE (swebench_unified.harness.run_resolve, official oracle, retries=1):
- gold patch (faithful patch for atk_1/atk_3/atk_4 — pure control-flow & echo restructurings of the exact gold VALUE, no guard/value change): RESOLVED=True COMPLETED=True.
- atk2_faithful (broadened-horizontal-guard, direct faithful transliteration handling dense `other` by re-measuring self and falling through the shared main body — non-recursive, terminating): RESOLVED=True COMPLETED=True (run sbu_atk2_faithful_r2t3q3).
- atk5_faithful (broadened-vertical-guard): RESOLVED=True COMPLETED=True (run sbu_atk5_faithful_r2t3q3).
EVERY verifying attack's faithful patch RESOLVES. No verify⇏correct witness found.

ADVERSARIAL NOTES / near-misses investigated:
1. loom.semantics.termination='partial' (partial correctness) means a non-terminating impl could verify vacuously — but all impls here are straight-line returns (no loops/recursion), so this lever is not reachable via the impl region.
2. The broadened guard is termination-load-bearing for gold's RECURSIVE realization (`self._new(...).row_join(other)`): dropping the `self.rows!=other.rows` conjunct causes infinite recursion (I reproduced RecursionError on the null-stack case). However the FAITHFUL transliteration of the verifying Lean is a DIRECT value build (the Lean `return {...}` does not self-call), which I materialized as a re-measure-then-fall-through patch; it terminates and RESOLVES. My first (v1) direct-build patches accessed `other._smat` and broke on the dense-`other` assertion at test_sparse.py:24 (`MutableSparseMatrix([]).row_join(MutableDenseMatrix([1,2]))`) → COMPLETED=True RESOLVED=False; that was MY transliteration bug, not a spec weakness — the corrected v2 (routing dense `other` through the shared main body exactly as gold's recursion does) resolves. Recorded here for transparency.
3. require domain = non-raising domain, so off-domain ShapeError behaviour lives in UNCHANGED code the patch never touches; a faithful patch preserves it automatically (test_sparse.py raises-ShapeError assertions in P2P are untouched).
Earlier COMPLETED=False runs on atk2/atk5 were transient harness/infra errors under heavy concurrent-audit load (200+ procs, no report.json written); re-run singly they completed and resolved.

Protocol: ≥5 distinct verifying attacks (control-flow reorder, broadened-guard ×2, ungrounded echo, require-exploiting height) all run; 4 distinct wrong impls + 2 prepatches confirmed rejected; every verifying attack's faithful patch executed through run_resolve and RESOLVED. Spec is not broken by verify⇏correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- Stacking two sparse rectangular blocks edge-to-edge.

   A block has a row count, a column count, and a sparse set of stored entries
   (an entry pins one (row, column) cell to a value; absent cells are zero).

   Horizontal stacking places the second block immediately to the RIGHT of the
   first: the combined block is as tall as the operands and as wide as the SUM
   of their widths, with the second block's stored cells shifted right by the
   first block's width. Vertical stacking is the transpose situation: the second
   block goes BELOW the first, the combined height is the SUM of the heights, and
   the second block's cells shift down by the first block's height.

   A degenerate block — one whose width (for horizontal stacking) or height (for
   vertical stacking) is zero — contributes no cells but STILL contributes its
   measured extent: stacking such a block must accumulate the running width/height
   exactly as a non-degenerate block would, never collapse the result to the shape
   of the other operand alone. This is the property the model pins. -/

-- axioms-start
/- No callee is axiomatized. The stacking behavior is pure shape-and-cell
   arithmetic computed entirely from the two operand blocks (extent addition plus
   a coordinate shift of the second block's stored cells); there is no unchanged
   repository callee whose contract the proof must assume. Both legs of the result
   construction are concrete (refinement.md: every row R or I). Soundness of the
   shape arithmetic is exercised executably against the real callees by
   conformance_check.py. -/
-- axioms-end

-- pure-start
/- A rectangular block: `rows` × `cols`, with `entries` the stored (nonzero)
   cells as `((i, j), v)`. The carrier abstracts over storage form — a value is
   recorded the same way whether the real object stores it densely or sparsely. -/
structure Block where
  rows : Nat
  cols : Nat
  entries : List ((Nat × Nat) × Int)
  deriving DecidableEq, Inhabited, Repr

/- Shift a stored cell to the right by `n` columns (used when a block is placed
   to the right of another of width `n`). -/
def shiftRight (n : Nat) (e : (Nat × Nat) × Int) : (Nat × Nat) × Int :=
  ((e.1.1, e.1.2 + n), e.2)

/- Shift a stored cell down by `n` rows (used when a block is placed below
   another of height `n`). -/
def shiftDown (n : Nat) (e : (Nat × Nat) × Int) : (Nat × Nat) × Int :=
  ((e.1.1 + n, e.1.2), e.2)

/- The block obtained by placing `B` immediately to the right of `A`. Width is
   the SUM of the two widths (so a zero-width `A` still contributes its — zero —
   width and the running total is preserved, never replaced by `B`'s width
   alone). Height is `A`'s, except a zero-width `A` carries no height of its own
   and adopts `B`'s. `B`'s cells move right by `A`'s width. -/
def hstackBlock (A B : Block) : Block :=
  { rows := if A.cols = 0 then B.rows else A.rows,
    cols := A.cols + B.cols,
    entries := A.entries ++ B.entries.map (shiftRight A.cols) }

/- The block obtained by placing `B` immediately below `A`. Height is the SUM of
   the two heights; width is `A`'s, except a zero-height `A` adopts `B`'s width.
   `B`'s cells move down by `A`'s height. -/
def vstackBlock (A B : Block) : Block :=
  { rows := A.rows + B.rows,
    cols := if A.rows = 0 then B.cols else A.cols,
    entries := A.entries ++ B.entries.map (shiftDown A.rows) }

@[grind] lemma hstackBlock_eq (A B : Block) :
    hstackBlock A B =
      { rows := if A.cols = 0 then B.rows else A.rows,
        cols := A.cols + B.cols,
        entries := A.entries ++ B.entries.map (shiftRight A.cols) } := rfl

@[grind] lemma vstackBlock_eq (A B : Block) :
    vstackBlock A B =
      { rows := A.rows + B.rows,
        cols := if A.rows = 0 then B.cols else A.cols,
        entries := A.entries ++ B.entries.map (shiftDown A.rows) } := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Place block `B` immediately to the right of block `A`. `A` and `B` are
   read-only operands (neither is `mut`; the result is a fresh block and the
   inputs are unchanged). The operands are compatible when their heights match,
   OR when `A` is degenerate in width — a zero-width block can be stacked beside
   any block, taking on that block's height. The result must have width equal to
   the SUM of the two widths in every admissible case, so a zero-width `A` never
   collapses the result to `B`'s width alone. -/
method stackHorizontally (A : Block) (B : Block) return (out : Block)
  require A.cols = 0 ∨ A.rows = B.rows
  ensures out = hstackBlock A B
  do
    -- impl-start
    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
    -- content at the full summed width.  Otherwise the heights already line up
    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
    -- width as the SUM `A.cols + B.cols`.
    if A.cols = 0 ∧ A.rows ≠ B.rows then
      return { rows := B.rows, cols := A.cols + B.cols,
               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
    else
      return { rows := A.rows, cols := A.cols + B.cols,
               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
    -- impl-end

prove_correct stackHorizontally by
  loom_solve

/- Place block `B` immediately below block `A`. `A` and `B` are read-only
   operands (neither is `mut`). The operands are compatible when their widths
   match, OR when `A` is degenerate in height. The result must have height equal
   to the SUM of the two heights in every admissible case, so a zero-height `A`
   never collapses the result to `B`'s height alone. -/
method stackVertically (A : Block) (B : Block) return (out : Block)
  require A.rows = 0 ∨ A.cols = B.cols
  ensures out = vstackBlock A B
  do
    -- impl-start
    -- Symmetric to horizontal stacking: a height-zero `A` whose width disagrees
    -- is re-measured to `B`'s width and then stacked; otherwise `B`'s rows are
    -- appended below `A`'s.  Both legs accumulate the height as `A.rows + B.rows`.
    if A.rows = 0 ∧ A.cols ≠ B.cols then
      return { rows := A.rows + B.rows, cols := B.cols,
               entries := A.entries ++ B.entries.map (shiftDown A.rows) }
    else
      return { rows := A.rows + B.rows, cols := A.cols,
               entries := A.entries ++ B.entries.map (shiftDown A.rows) }
    -- impl-end

prove_correct stackVertically by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ (refinement-fidelity / A-leg) audit of velvet sympy__sympy-13031.

SPEC SHAPE (why it is hard to break): postcondition is EXACT functional equality to a TOTAL deep model, `out = hstackBlock A B` / `out = vstackBlock A B`, over a `require` domain (`A.cols=0 ∨ A.rows=B.rows` / transposed) that equals the callee's non-raising domain. Any impl that verifies is therefore behaviourally identical to the total model on the ENTIRE tested domain. meta.json `axioms: []`; the two deep_model_references are tagged kind='deep-model (concrete R/I, not A-reference)'. G-AX legitimately skip (no axiom_check.py; SPEC_GUIDE directive-7 + django-11603 precedent: a deeply-modeled CHANGED function is validated by G-CONF, which git-applies patch.diff first, not by G-AX against the buggy base-commit callee).

A-LEG AUDIT (refinement.md): legs A1/A2/B1/B2 = R (type refinement, (rows,cols,_smat)↔Block bijection), A3/A4/B3/B4 = I (identical concrete op). NO A-consumed, NO A-reference, NO kind-3 rows — consistent with zero axioms. Model↔callee correspondence confirmed empirically: gold patch RESOLVED=True, and the summed-extent arithmetic of hstackBlock/vstackBlock matches post-patch row_join/col_join.

SAME-SPEC: all 12 files (5 verifying attacks + 4 wrong + 2 prepatch + pos-control) same_spec=True (spec regions byte-identical; only impl edited).

### LEAN VERIFY (scripts/lean_verify.sh, 300s cap):
- pos_control EXIT=0 (verifies)
- atk_1 (negated-guard control-flow reorder) EXIT=0
- atk_2 (broadened horizontal guard `A.cols=0`) EXIT=0
- atk_3 (ungrounded-oracle ECHO: unconditional single return of the model form) EXIT=0
- atk_4 (rows:=B.rows unconditional; require forces equality) EXIT=0
- atk_5 (broadened vertical guard `A.rows=0`) EXIT=0
- atk_w1 (boundary: else-branch collapses width to B.cols) EXIT=1 (rejected)
- atk_w2 (wrong shift offset shiftRight B.cols) EXIT=1 (rejected)
- atk_w3 (partial-domain: rows:=A.rows always) EXIT=1 (rejected)
- atk_w4 (partial-domain: drops B's cells) EXIT=1 (rejected)
- prepatch1/prepatch2 EXIT=1 (prepatch bug reproduced: `if A.rows=0 ∨ A.cols=0 then return B` fails summed-extent clause)
The 4 genuinely-wrong impls and both prepatches all FAIL to verify — the exact-equality-to-total-model postcondition is tight; no partial-domain/boundary/effect/echo divergence survives.

### HARNESS RESOLVE (swebench_unified.harness.run_resolve, official oracle, retries=1):
- gold patch (faithful patch for atk_1/atk_3/atk_4 — pure control-flow & echo restructurings of the exact gold VALUE, no guard/value change): RESOLVED=True COMPLETED=True.
- atk2_faithful (broadened-horizontal-guard, direct faithful transliteration handling dense `other` by re-measuring self and falling through the shared main body — non-recursive, terminating): RESOLVED=True COMPLETED=True (run sbu_atk2_faithful_r2t3q3).
- atk5_faithful (broadened-vertical-guard): RESOLVED=True COMPLETED=True (run sbu_atk5_faithful_r2t3q3).
EVERY verifying attack's faithful patch RESOLVES. No verify⇏correct witness found.

ADVERSARIAL NOTES / near-misses investigated:
1. loom.semantics.termination='partial' (partial correctness) means a non-terminating impl could verify vacuously — but all impls here are straight-line returns (no loops/recursion), so this lever is not reachable via the impl region.
2. The broadened guard is termination-load-bearing for gold's RECURSIVE realization (`self._new(...).row_join(other)`): dropping the `self.rows!=other.rows` conjunct causes infinite recursion (I reproduced RecursionError on the null-stack case). However the FAITHFUL transliteration of the verifying Lean is a DIRECT value build (the Lean `return {...}` does not self-call), which I materialized as a re-measure-then-fall-through patch; it terminates and RESOLVES. My first (v1) direct-build patches accessed `other._smat` and broke on the dense-`other` assertion at test_sparse.py:24 (`MutableSparseMatrix([]).row_join(MutableDenseMatrix([1,2]))`) → COMPLETED=True RESOLVED=False; that was MY transliteration bug, not a spec weakness — the corrected v2 (routing dense `other` through the shared main body exactly as gold's recursion does) resolves. Recorded here for transparency.
3. require domain = non-raising domain, so off-domain ShapeError behaviour lives in UNCHANGED code the patch never touches; a faithful patch preserves it automatically (test_sparse.py raises-ShapeError assertions in P2P are untouched).
Earlier COMPLETED=False runs on atk2/atk5 were transient harness/infra errors under heavy concurrent-audit load (200+ procs, no report.json written); re-run singly they completed and resolved.

Protocol: ≥5 distinct verifying attacks (control-flow reorder, broadened-guard ×2, ungrounded echo, require-exploiting height) all run; 4 distinct wrong impls + 2 prepatches confirmed rejected; every verifying attack's faithful patch executed through run_resolve and RESOLVED. Spec is not broken by verify⇏correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for sympy__sympy-13031/velvet. Modeled functions stackHorizontally↔SparseMatrix.row_join and stackVertically↔SparseMatrix.col_join (deep-modeled changed functions; G-AX correctly skipped per directive-7, validated against POST-patch callee). Checks performed: (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True with the Lean LanguageTables. (2) Solution.lean elaborates cleanly via scripts/lean_verify.sh (exit 0, no sorry/error). Fuzz equivalence against the REAL patched callee: built as base_commit worktree + git apply patch.diff, then compared hstackBlock/vstackBlock semantics (rows, cols, and the SET of stored cells with shiftRight/shiftDown) against the actual patched row_join/col_join over ~32k valid operand pairs (dims 0..6, negative/repeated int cell values, seed 13031). Result: 0 shape mismatches, 0 cell-set mismatches for both horizontal and vertical. Degenerate cases (A.cols=0 / A.rows=0) — the gold-patch fix locus — produce the SUMMED extent in the model, matching the real patched callee's re-measured-null recursion (e.g. row_join((0,1),(0,2)) -> (0,3), not the pre-patch collapse to (0,2)). (4) Require domain fidelity: every outside-require input (A.cols!=0 ∧ A.rows!=B.rows for horizontal) raises ShapeError in the real code (2524/2524), and the model only asserts behavior inside require; the require predicate is exactly the non-raising domain. The spec is neither too strong nor drifting: no input found where the modeled function disagrees with the real patched callee within the modeled domain. Type-abstraction bijection (rows/cols identity on ℕ, _smat as order-insensitive cell set, Integer↔Int) is sound for integer-valued sparse matrices as tested.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed frozen: same_spec(Solution vs prepatch_1)=True, same_spec(Solution vs prepatch_2)=True (velvet backend). Judged the projected spec view (impl/proof regions elided).

The public problem_statement already discloses the entire correct behavior: hstack(0×0,0×1,0×2,0×3).shape must be (0,6) not (0,3), and hstack(1×0,...,1×3).shape must be (1,6) — i.e. widths must SUM and a degenerate (zero-area) operand must still contribute its extent instead of collapsing the result to the other operand's shape. This is the fixed behavior, publicly given via worked examples.

The spec view formalizes exactly this public behavior abstractly, via a generic `Block` carrier and `stackHorizontally`/`stackVertically` methods whose `ensures` reference `hstackBlock`/`vstackBlock` (result extent = A.cols+B.cols / A.rows+B.rows, with degenerate-operand re-measure). The prose comments ('as wide as the SUM of their widths', 'a degenerate block STILL contributes its measured extent … never collapse the result') restate the public property, nothing more.

No gold-edit specifics leak beyond problem_statement: grep of Solution.lean finds NONE of #10770, `not self`, `type(self)(other)`, `row_join`/`col_join`, `sparse.py`, `_new`, `SparseMatrix`, or `reduce`. The removed pre-patch guard and the exact patch mechanics appear only in mapping.md/refinement.md (auditor docs, outside the spec view); mapping.md explicitly states the bug locus is 'recorded here for the refinement audit, not named in the spec view.' The spec discloses only the corrected semantics, which are equivalent to the public examples and are precisely what any spec must state. No line pins the gold edit site, the removed `if not self` guard, or any patch-specific construct.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
