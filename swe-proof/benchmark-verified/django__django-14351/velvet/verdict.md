# P2 adversarial audit — django__django-14351

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a COMPLETE functional specification: it pins BOTH observables as exact equalities to pure functions of free inputs (ensures rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields rhsSelectOld pkCol; ensures out = contributedCols rhsIsExpr lhsCols rhsCols) with NO preconditions. Every input (rhsSelectOld, rhsIsExpr, rhsHasSelectFields, lhsCols, rhsCols, pkCol) is universally quantified, so any verifying impl is behaviorally identical to gold on the two modeled observables (returned grouping cols + rhs select-clause post-state). No degree of freedom for a verifying-but-wrong impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,19 +99,9 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
     let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
     if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
-      if !rhsHasSelectFields then
-        rhsSelect := [pkCol]
-      else
-        rhsSelect := rhsSelect
+      rhsSelect := rhsSelect
       cols := cols ++ rhsCols
     else
       rhsSelect := rhsSelect
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,16 +99,9 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
     let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
     if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
-      if !rhsHasSelectFields then
+      if rhsHasSelectFields then
         rhsSelect := [pkCol]
       else
         rhsSelect := rhsSelect
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,20 +99,12 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
     let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
     if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
       if !rhsHasSelectFields then
         rhsSelect := [pkCol]
       else
         rhsSelect := rhsSelect
-      cols := cols ++ rhsCols
     else
       rhsSelect := rhsSelect
     return cols
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,22 +99,10 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
     let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
+    rhsSelect := [pkCol]
     if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
-      if !rhsHasSelectFields then
-        rhsSelect := [pkCol]
-      else
-        rhsSelect := rhsSelect
       cols := cols ++ rhsCols
-    else
-      rhsSelect := rhsSelect
     return cols
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,17 +99,10 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
     let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
     if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
       if !rhsHasSelectFields then
-        rhsSelect := [pkCol]
+        rhsSelect := []
       else
         rhsSelect := rhsSelect
       cols := cols ++ rhsCols
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,20 +99,13 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
     let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
     if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
       if !rhsHasSelectFields then
         rhsSelect := [pkCol]
       else
         rhsSelect := rhsSelect
-      cols := cols ++ rhsCols
+      cols := rhsCols ++ cols
     else
       rhsSelect := rhsSelect
     return cols
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -99,22 +99,14 @@
   ensures out = contributedCols rhsIsExpr lhsCols rhsCols
   do
     -- impl-start
-    -- Start the contributed grouping columns from the left operand's columns.
-    let mut cols : List Col := lhsCols
-    -- Only when the right operand is itself a column-contributing sub-result do
-    -- we reconcile its output shape and fold in its columns.
-    if rhsIsExpr then
-      -- A sub-result that names no explicit output columns would expose every
-      -- default output column; clamp its output list to the single key column so
-      -- it is a well-formed single-column operand. A sub-result that already
-      -- names its output columns is left untouched.
-      if !rhsHasSelectFields then
-        rhsSelect := [pkCol]
-      else
-        rhsSelect := rhsSelect
-      cols := cols ++ rhsCols
+    -- Behavioural echo of the gold rule, restructured: single guarded
+    -- assignment to the mutable select carrier, and the contributed cols as
+    -- one conditional expression. Behaviour identical to the reference.
+    if rhsIsExpr && !rhsHasSelectFields then
+      rhsSelect := [pkCol]
     else
       rhsSelect := rhsSelect
+    let cols : List Col := if rhsIsExpr then lhsCols ++ rhsCols else lhsCols
     return cols
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged steps this operation delegates to — asking the left operand, and the
   right operand, each for the columns it contributes to a grouping clause — are
   modeled as FREE inputs (`lhsCols`, `rhsCols`). The behaviour pinned here holds
   for EVERY value of those inputs, so they are owed no contract: the spec is
   strictly weaker than any concrete implementation of either delegated step
   (directive 7). The behaviour actually pinned — that when the right operand is a
   column-contributing sub-result that names no explicit output columns, its
   output-column list must be clamped to the single key column before it is used,
   and otherwise left exactly as it was — is stated directly in the
   postconditions. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque identity for a column that may appear in an output list or a
   grouping clause. Only identity matters here (whether two such columns are the
   same object); nothing about internal content is constrained, because this
   operation neither inspects nor builds column content — it only decides WHICH
   columns appear and, conditionally, rewrites the right operand's output list. -/
structure Col where
  ref : Nat
  deriving DecidableEq, Inhabited

/- Whether the right operand's output-column list must be clamped before use:
   true exactly when the right operand is a column-contributing sub-result
   (`rhsIsExpr`) that does NOT already name an explicit output-column list
   (`¬ rhsHasSelectFields`). A direct value list contributes nothing to clamp; a
   sub-result that already names its output columns is left as-is. -/
def mustClamp (rhsIsExpr rhsHasSelectFields : Bool) : Bool :=
  rhsIsExpr && !rhsHasSelectFields

/- The right operand's output-column list after the operation, given the list it
   named on entry (`selectOld`) and the single key column. When the clamp
   applies, the output list becomes exactly the one key column; otherwise it is
   preserved unchanged. -/
def clampedSelect (rhsIsExpr rhsHasSelectFields : Bool)
    (selectOld : List Col) (pkCol : Col) : List Col :=
  if mustClamp rhsIsExpr rhsHasSelectFields then [pkCol] else selectOld

/- The columns this operation contributes to the grouping clause: always the left
   operand's columns, followed — only when the right operand is a
   column-contributing sub-result — by the right operand's columns. A direct value
   right operand contributes nothing. This is independent of the clamp: clamping
   the sub-result's output list does not change WHICH column object the
   sub-result contributes to the grouping clause. -/
def contributedCols (rhsIsExpr : Bool) (lhsCols rhsCols : List Col) : List Col :=
  if rhsIsExpr then lhsCols ++ rhsCols else lhsCols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The grouping columns a membership test against a right operand contributes,
   with the output-shape reconciliation the desired behaviour demands.

   Two effects.

   First, the contributed grouping columns are assembled: the left operand's
   columns always, extended by the right operand's columns exactly when the right
   operand is itself a column-contributing sub-result (`rhsIsExpr`). A right
   operand that is a direct list of values contributes no grouping columns. This
   is the long-standing behaviour and is independent of the clamp below.

   Second — and this is the behaviour the desired outcome demands — when the right
   operand is a column-contributing sub-result that names NO explicit output
   columns, it would otherwise expose every default output column; used as a
   single-column membership operand or placed in a grouping clause this is
   ill-formed (it would return more than one column). So its output-column list
   must be clamped to the single key column before it is used. When the right
   operand already names an explicit output-column list, or is not a
   column-contributing sub-result at all, its output-column list is preserved
   exactly.

   `rhsSelect` is the right operand's output-column list — the one mutable carrier
   the operation writes (declared `mut`). It is pinned exactly per the
   reconciliation rule: the single key column when the clamp applies, and its
   entry value `rhsSelectOld` otherwise (directive 5: the changed frame to its
   exact post-state, the preserved frame against the entry value). The contributed
   grouping columns `out` are pinned to the assembly above. The delegated column
   observations `lhsCols`, `rhsCols` are read-only free inputs (not `mut`); the
   key column `pkCol` and the shape flags `rhsIsExpr`, `rhsHasSelectFields` are
   read-only. -/
method inGroupByCols (mut rhsSelect : List Col) (rhsIsExpr : Bool)
    (rhsHasSelectFields : Bool) (lhsCols : List Col) (rhsCols : List Col)
    (pkCol : Col) return (out : List Col)
  ensures rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields rhsSelectOld pkCol
  ensures out = contributedCols rhsIsExpr lhsCols rhsCols
  do
    -- impl-start
    -- Start the contributed grouping columns from the left operand's columns.
    let mut cols : List Col := lhsCols
    -- Only when the right operand is itself a column-contributing sub-result do
    -- we reconcile its output shape and fold in its columns.
    if rhsIsExpr then
      -- A sub-result that names no explicit output columns would expose every
      -- default output column; clamp its output list to the single key column so
      -- it is a well-formed single-column operand. A sub-result that already
      -- names its output columns is left untouched.
      if !rhsHasSelectFields then
        rhsSelect := [pkCol]
      else
        rhsSelect := rhsSelect
      cols := cols ++ rhsCols
    else
      rhsSelect := rhsSelect
    return cols
    -- impl-end

prove_correct inGroupByCols by
  loom_solve
  all_goals simp_all [clampedSelect, mustClamp, contributedCols]
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for django__django-14351 velvet bundle. Root: (env swebench-lean).

SAME-SPEC: all 7 attacks verified same_spec=True via swebench_unified.markers.same_spec (velvet lang) against the frozen Solution.lean (impl-region-only edits; axioms/pure/pre/post byte-identical).

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of <=4 as bg jobs:
 - pos_control.lean (=frozen Solution.lean): exit 0 (VERIFIES) -> positive control good.
 - prepatch.lean (=Solution_prepatch.lean): exit 1 at ensures_2 (rhsSelect = clampedSelect...) -> PREPATCH BUG REPRODUCED (no-clamp leaves rhsSelectOld where spec demands [pkCol]).
 - atk_1 no-clamp/prepatch bug: exit 1, ensures_2.
 - atk_2 inverted clamp cond (clamp when rhsHasSelectFields): exit 1, ensures_2.
 - atk_3 partial-domain out (drop rhsCols, out=lhsCols always): exit 1, ensures_1.
 - atk_4 control-flow-effect (clamp rhsSelect UNCONDITIONALLY): exit 1, ensures_2.
 - atk_5 boundary/wrong clamp value ([] instead of [pkCol]): exit 1, ensures_2.
 - atk_6 out order swap (rhsCols++lhsCols): exit 1, ensures_1.
 All 6 wrong impls FAIL verification on the pinned postconditions -> spec is tight.

VERIFY-then-RESOLVE mandate: atk_7 (behavioral echo of gold, restructured: single guarded assignment `if rhsIsExpr && !rhsHasSelectFields then rhsSelect:=[pkCol] else rhsSelect:=rhsSelect` + `cols := if rhsIsExpr then lhsCols++rhsCols else lhsCols`) VERIFIES (exit 0, no sorry). Materialized its faithful refined patch (transliterated back via mapping.md R/I map = the gold In.get_group_by_cols hunk; byte-identical to bundle patch.diff) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-14351', patch, retries=1) -> RESOLVED=True, COMPLETED=True, note='resolved'. So the one verifying same-spec impl's faithful patch RESOLVES. No verify-but-not-resolve break.

REFINEMENT.MD AUDIT: all legs R or I with directive-7 free inputs (lhsCols/rhsCols); NO consumed axioms, NO deep-model references (correctly declared 'none' - A legs n/a). A-leg correspondence corroborated against base repo: Lookup.get_group_by_cols (lookups.py:117) = cols=self.lhs.get_group_by_cols() then UNCONDITIONAL cols.extend (no clamp) exactly as prepatch models; In.process_rhs (lookups.py:~404) already carries the same clear_select_clause()/add_fields(['pk']) clamp pattern the gold get_group_by_cols mirrors -> clampedSelect [pkCol] modeling is faithful. Pure defs clampedSelect/contributedCols grounded structurally in inputs (directive 8, not ungrounded oracle). No kind-3 (inexpressible-changed-op) legs: the changed op (conditional clamp + contributed-cols assembly) is expressed directly, not hidden behind an axiom.

VERDICT: SOUND. The spec is a complete functional spec pinning both observables to exact functions of universally-quantified free inputs; verify<=>correct here. >=6 distinct verifying-wrong-impl attacks all rejected on the pinned postconditions; the sole verifying same-spec echo's faithful patch executes to RESOLVED=True. verify DOES imply correct for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a COMPLETE functional specification: it pins BOTH observables as exact equalities to pure functions of free inputs (ensures rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields rhsSelectOld pkCol; ensures out = contributedCols rhsIsExpr lhsCols rhsCols) with NO preconditions. Every input (rhsSelectOld, rhsIsExpr, rhsHasSelectFields, lhsCols, rhsCols, pkCol) is universally quantified, so any verifying impl is behaviorally identical to gold on the two modeled observables (returned grouping cols + rhs select-clause post-state). No degree of freedom for a verifying-but-wrong impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged steps this operation delegates to — asking the left operand, and the
   right operand, each for the columns it contributes to a grouping clause — are
   modeled as FREE inputs (`lhsCols`, `rhsCols`). The behaviour pinned here holds
   for EVERY value of those inputs, so they are owed no contract: the spec is
   strictly weaker than any concrete implementation of either delegated step
   (directive 7). The behaviour actually pinned — that when the right operand is a
   column-contributing sub-result that names no explicit output columns, its
   output-column list must be clamped to the single key column before it is used,
   and otherwise left exactly as it was — is stated directly in the
   postconditions. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque identity for a column that may appear in an output list or a
   grouping clause. Only identity matters here (whether two such columns are the
   same object); nothing about internal content is constrained, because this
   operation neither inspects nor builds column content — it only decides WHICH
   columns appear and, conditionally, rewrites the right operand's output list. -/
structure Col where
  ref : Nat
  deriving DecidableEq, Inhabited

/- Whether the right operand's output-column list must be clamped before use:
   true exactly when the right operand is a column-contributing sub-result
   (`rhsIsExpr`) that does NOT already name an explicit output-column list
   (`¬ rhsHasSelectFields`). A direct value list contributes nothing to clamp; a
   sub-result that already names its output columns is left as-is. -/
def mustClamp (rhsIsExpr rhsHasSelectFields : Bool) : Bool :=
  rhsIsExpr && !rhsHasSelectFields

/- The right operand's output-column list after the operation, given the list it
   named on entry (`selectOld`) and the single key column. When the clamp
   applies, the output list becomes exactly the one key column; otherwise it is
   preserved unchanged. -/
def clampedSelect (rhsIsExpr rhsHasSelectFields : Bool)
    (selectOld : List Col) (pkCol : Col) : List Col :=
  if mustClamp rhsIsExpr rhsHasSelectFields then [pkCol] else selectOld

/- The columns this operation contributes to the grouping clause: always the left
   operand's columns, followed — only when the right operand is a
   column-contributing sub-result — by the right operand's columns. A direct value
   right operand contributes nothing. This is independent of the clamp: clamping
   the sub-result's output list does not change WHICH column object the
   sub-result contributes to the grouping clause. -/
def contributedCols (rhsIsExpr : Bool) (lhsCols rhsCols : List Col) : List Col :=
  if rhsIsExpr then lhsCols ++ rhsCols else lhsCols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The grouping columns a membership test against a right operand contributes,
   with the output-shape reconciliation the desired behaviour demands.

   Two effects.

   First, the contributed grouping columns are assembled: the left operand's
   columns always, extended by the right operand's columns exactly when the right
   operand is itself a column-contributing sub-result (`rhsIsExpr`). A right
   operand that is a direct list of values contributes no grouping columns. This
   is the long-standing behaviour and is independent of the clamp below.

   Second — and this is the behaviour the desired outcome demands — when the right
   operand is a column-contributing sub-result that names NO explicit output
   columns, it would otherwise expose every default output column; used as a
   single-column membership operand or placed in a grouping clause this is
   ill-formed (it would return more than one column). So its output-column list
   must be clamped to the single key column before it is used. When the right
   operand already names an explicit output-column list, or is not a
   column-contributing sub-result at all, its output-column list is preserved
   exactly.

   `rhsSelect` is the right operand's output-column list — the one mutable carrier
   the operation writes (declared `mut`). It is pinned exactly per the
   reconciliation rule: the single key column when the clamp applies, and its
   entry value `rhsSelectOld` otherwise (directive 5: the changed frame to its
   exact post-state, the preserved frame against the entry value). The contributed
   grouping columns `out` are pinned to the assembly above. The delegated column
   observations `lhsCols`, `rhsCols` are read-only free inputs (not `mut`); the
   key column `pkCol` and the shape flags `rhsIsExpr`, `rhsHasSelectFields` are
   read-only. -/
method inGroupByCols (mut rhsSelect : List Col) (rhsIsExpr : Bool)
    (rhsHasSelectFields : Bool) (lhsCols : List Col) (rhsCols : List Col)
    (pkCol : Col) return (out : List Col)
  ensures rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields rhsSelectOld pkCol
  ensures out = contributedCols rhsIsExpr lhsCols rhsCols
  do
    -- impl-start
    -- Start the contributed grouping columns from the left operand's columns.
    let mut cols : List Col := lhsCols
    -- Only when the right operand is itself a column-contributing sub-result do
    -- we reconcile its output shape and fold in its columns.
    if rhsIsExpr then
      -- A sub-result that names no explicit output columns would expose every
      -- default output column; clamp its output list to the single key column so
      -- it is a well-formed single-column operand. A sub-result that already
      -- names its output columns is left untouched.
      if !rhsHasSelectFields then
        rhsSelect := [pkCol]
      else
        rhsSelect := rhsSelect
      cols := cols ++ rhsCols
    else
      rhsSelect := rhsSelect
    return cols
    -- impl-end

prove_correct inGroupByCols by
  loom_solve
  all_goals simp_all [clampedSelect, mustClamp, contributedCols]
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for django__django-14351 velvet bundle. Root: (env swebench-lean).

SAME-SPEC: all 7 attacks verified same_spec=True via swebench_unified.markers.same_spec (velvet lang) against the frozen Solution.lean (impl-region-only edits; axioms/pure/pre/post byte-identical).

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in 2 batches of <=4 as bg jobs:
 - pos_control.lean (=frozen Solution.lean): exit 0 (VERIFIES) -> positive control good.
 - prepatch.lean (=Solution_prepatch.lean): exit 1 at ensures_2 (rhsSelect = clampedSelect...) -> PREPATCH BUG REPRODUCED (no-clamp leaves rhsSelectOld where spec demands [pkCol]).
 - atk_1 no-clamp/prepatch bug: exit 1, ensures_2.
 - atk_2 inverted clamp cond (clamp when rhsHasSelectFields): exit 1, ensures_2.
 - atk_3 partial-domain out (drop rhsCols, out=lhsCols always): exit 1, ensures_1.
 - atk_4 control-flow-effect (clamp rhsSelect UNCONDITIONALLY): exit 1, ensures_2.
 - atk_5 boundary/wrong clamp value ([] instead of [pkCol]): exit 1, ensures_2.
 - atk_6 out order swap (rhsCols++lhsCols): exit 1, ensures_1.
 All 6 wrong impls FAIL verification on the pinned postconditions -> spec is tight.

VERIFY-then-RESOLVE mandate: atk_7 (behavioral echo of gold, restructured: single guarded assignment `if rhsIsExpr && !rhsHasSelectFields then rhsSelect:=[pkCol] else rhsSelect:=rhsSelect` + `cols := if rhsIsExpr then lhsCols++rhsCols else lhsCols`) VERIFIES (exit 0, no sorry). Materialized its faithful refined patch (transliterated back via mapping.md R/I map = the gold In.get_group_by_cols hunk; byte-identical to bundle patch.diff) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-14351', patch, retries=1) -> RESOLVED=True, COMPLETED=True, note='resolved'. So the one verifying same-spec impl's faithful patch RESOLVES. No verify-but-not-resolve break.

REFINEMENT.MD AUDIT: all legs R or I with directive-7 free inputs (lhsCols/rhsCols); NO consumed axioms, NO deep-model references (correctly declared 'none' - A legs n/a). A-leg correspondence corroborated against base repo: Lookup.get_group_by_cols (lookups.py:117) = cols=self.lhs.get_group_by_cols() then UNCONDITIONAL cols.extend (no clamp) exactly as prepatch models; In.process_rhs (lookups.py:~404) already carries the same clear_select_clause()/add_fields(['pk']) clamp pattern the gold get_group_by_cols mirrors -> clampedSelect [pkCol] modeling is faithful. Pure defs clampedSelect/contributedCols grounded structurally in inputs (directive 8, not ungrounded oracle). No kind-3 (inexpressible-changed-op) legs: the changed op (conditional clamp + contributed-cols assembly) is expressed directly, not hidden behind an axiom.

VERDICT: SOUND. The spec is a complete functional spec pinning both observables to exact functions of universally-quantified free inputs; verify<=>correct here. >=6 distinct verifying-wrong-impl attacks all rejected on the pinned postconditions; the sole verifying same-spec echo's faithful patch executes to RESOLVED=True. verify DOES imply correct for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec with velvet LanguageTables = True). Solution.lean elaborates (exit 0); prepatch fails precisely on `ensures rhsSelect = clampedSelect ...` (the omitted clamp), so G-DIFF is a genuine bug detector, not a spec artifact. Faithfulness vs gold In.get_group_by_cols at base_commit 06fd4df4: (1) out = contributedCols rhsIsExpr lhsCols rhsCols exactly mirrors `cols=lhs.get_group_by_cols(); if hasattr(rhs,'get_group_by_cols'): cols.extend(rhs.get_group_by_cols())`; (2) rhsSelect = clampedSelect = [pkCol] iff (hasattr ∧ not getattr(rhs,'has_select_fields',True)) else preserved, mirroring clear_select_clause()+add_fields(['pk']) (single pk col, default_cols=False) vs no-mutation. lhsCols/rhsCols are directive-7 free inputs so the spec is strictly weaker there; the return is clamp-independent because the exercised non-aggregating subquery's get_group_by_cols returns [self] whose identity survives the mutation. No composite PK at this Django version, so add_fields(['pk']) yields exactly one column, matching [pkCol]. G-CONF: R/I shadow agreed with real patched code over 100000 inputs (seed 14351), 0 disagreements. No diverging input could be constructed; the spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view = velvet spec_view(Solution.lean): imports/open, set_options, axioms region (prose), pure region (Col struct, mustClamp, clampedSelect, contributedCols defs), empty pre/post regions, the inGroupByCols method signature + two `ensures` clauses, with the impl `do` body and `prove_correct` body ELIDED (verified by spec_view rendering; impl-start/impl-end collapse to 'implementation elided', prove_correct body to 'proof elided'). same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec region is byte-identical and not drifting to embed the fix. Mechanical G-LEAK screen PASSES (no diff markers, no gold-patch line reproduced, patched path django/db/models/lookups.py absent, patched symbols get_group_by_cols/process_rhs absent from both spec-view identifiers and comments, no narration tokens). Semantic leakage judged vs PUBLIC problem_statement only (not hints_text): the gold edit's entire discriminating content is already public. problem_statement states verbatim the error 'subquery must return only one column', that the __in subquery pulls all default columns (select_fields [0..6], default_cols=True) whereas the working id__in case yields one column (select_fields [0]), the GROUP BY/HAVING subquery context, and the user's own single-column workaround (cols=[cols[0]] / values_list('id')). The spec view describes precisely this in abstract, repo-agnostic terms ('right operand'/'column-contributing sub-result naming no explicit output columns'/'clamp to the single key column'/'grouping clause'/'would return more than one column') and names no patched symbol, file, module, or diff line. The mechanism details (has_select_fields / clear_select_clause / add_fields) are not surfaced. No spec-view line reveals the gold edit beyond what the public problem_statement already discloses. Recorded meta status G-LEAK=pass, G-PANEL-3 agent_verdict=NO-LEAKAGE — concur.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
