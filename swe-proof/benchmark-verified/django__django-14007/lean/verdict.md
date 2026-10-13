# P2 adversarial audit — django__django-14007

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,16 +101,12 @@
     (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do
   if returningFields.isEmpty then
     return []
-  let mut rows : List Row := []
   if canBatch then
-    rows := batchRows
+    return batchRows
   else if canColumns then
-    rows := [columnsRow]
+    return [columnsRow]
   else
-    rows := [lastIdRow]
-  if anyConverter returningFields then
-    rows := rows.map (convertRow returningFields)
-  return rows
+    return [lastIdRow]
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,10 +102,10 @@
   if returningFields.isEmpty then
     return []
   let mut rows : List Row := []
-  if canBatch then
+  if canColumns then
+    rows := [columnsRow]
+  else if canBatch then
     rows := batchRows
-  else if canColumns then
-    rows := [columnsRow]
   else
     rows := [lastIdRow]
   if anyConverter returningFields then
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,8 +108,7 @@
     rows := [columnsRow]
   else
     rows := [lastIdRow]
-  if anyConverter returningFields then
-    rows := rows.map (convertRow returningFields)
+  rows := rows.map (convertRow returningFields)
   return rows
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,8 +99,6 @@
 def implementation_insertReturnedRows
     (returningFields : List RetField) (canBatch canColumns : Bool)
     (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do
-  if returningFields.isEmpty then
-    return []
   let mut rows : List Row := []
   if canBatch then
     rows := batchRows
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,7 +107,7 @@
   else if canColumns then
     rows := [columnsRow]
   else
-    rows := [lastIdRow]
+    rows := []
   if anyConverter returningFields then
     rows := rows.map (convertRow returningFields)
   return rows
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,7 @@
     rows := [columnsRow]
   else
     rows := [lastIdRow]
-  if anyConverter returningFields then
+  if !(anyConverter returningFields) then
     rows := rows.map (convertRow returningFields)
   return rows
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -101,16 +101,14 @@
     (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do
   if returningFields.isEmpty then
     return []
-  let mut rows : List Row := []
-  if canBatch then
-    rows := batchRows
-  else if canColumns then
-    rows := [columnsRow]
+  let selected : List Row :=
+    if canBatch then batchRows
+    else if canColumns then [columnsRow]
+    else [lastIdRow]
+  if anyConverter returningFields then
+    return selected.map (convertRow returningFields)
   else
-    rows := [lastIdRow]
-  if anyConverter returningFields then
-    rows := rows.map (convertRow returningFields)
-  return rows
+    return selected
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Returning the rows produced by a row-creating database write.

When a row is created, the backend can hand back one or more column values for
that row (for example the freshly assigned primary key). Those values arrive as
a list of rows, each row being a tuple of raw cell values, and they may come from
one of several backend pathways depending on the connection's capabilities:

* a backend that can return several rows at once for a multi-row write returns
  them directly;
* a backend that can return columns for a single-row write returns one such row;
* otherwise a single last-inserted-id value is returned as a one-cell row.

Every field being returned may declare a chain of value converters — the same
converters a field uses to turn a stored value back into its Python form when it
is read by an ordinary query (e.g. a `from_db_value` hook that wraps a raw
integer in a wrapper object). The desired behaviour is that the values handed
back by a creating write are post-processed in exactly the same way as values
read by any other query:

  * the number of rows returned is unchanged;
  * each cell of each row is passed through the converter chain declared for the
    field in that column position (an empty chain leaves the cell unchanged);
  * if no returned field declares any converter, the rows are handed back
    untouched;
  * if no fields are being returned, the result is empty.

In particular a field whose converter wraps the raw value must see that wrapping
applied to the value produced by the creating write, just as it would for a value
fetched by a read.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The pathway
-- that produces the raw returned rows (single id, single returned row, or a
-- batch of returned rows) is upstream of and orthogonal to the modeled
-- behaviour; its result enters as grounded input data (the candidate row
-- values and the branch-selecting capability flags). The converter chain each
-- field declares likewise enters as grounded data. The post-processing itself
-- (applying each field's converter chain to the matching cell) is modeled
-- DEEPLY as a fold/map, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A returned field, carrying the ordered chain of value converters it declares.
A cell in this field's column is passed through `converters` left-to-right; an
empty chain means the cell is returned unchanged. Cell values are modeled as
`Int` (raw database scalars; a converter that "wraps" a value is modeled by the
function it applies). -/
structure RetField where
  converters : List (Int → Int)

/-- One returned row: a tuple of raw cell values, one per returned field. -/
abbrev Row := List Int

/-- Apply a field's converter chain to a single cell value, left-to-right.
An empty chain is the identity. -/
def applyChain (cs : List (Int → Int)) (x : Int) : Int :=
  cs.foldl (fun v f => f v) x

/-- Apply each field's converter chain to the matching cell of one row (the
field in column position `i` converts cell `i`). -/
def convertRow (fields : List RetField) (row : Row) : Row :=
  (fields.zip row).map (fun fc => applyChain fc.1.converters fc.2)

/-- Whether any returned field declares a non-empty converter chain. -/
def anyConverter (fields : List RetField) : Bool :=
  fields.any (fun f => !f.converters.isEmpty)
-- pure-end

-- post-conditions-start
/-- The rows returned by a creating write. `returningFields` are the fields whose
values are returned; `canBatch`/`canColumns` are the capability flags selecting
which backend pathway produced the raw rows; `batchRows`, `columnsRow`, and
`lastIdRow` are the candidate raw outputs of those three pathways. The result is
the selected raw rows with every field's converter chain applied (only if some
field declares a converter), or the empty list when no fields are returned. -/
def problem_spec_insertReturnedRows
    (returningFields : List RetField) (canBatch canColumns : Bool)
    (batchRows : List Row) (columnsRow lastIdRow : Row)
    (result : List Row) : Prop :=
  if returningFields.isEmpty then
    result = []
  else
    let selected : List Row :=
      if canBatch then batchRows
      else if canColumns then [columnsRow]
      else [lastIdRow]
    if anyConverter returningFields then
      result = selected.map (convertRow returningFields)
    else
      result = selected
-- post-conditions-end

-- impl-start
def implementation_insertReturnedRows
    (returningFields : List RetField) (canBatch canColumns : Bool)
    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do
  if returningFields.isEmpty then
    return []
  let mut rows : List Row := []
  if canBatch then
    rows := batchRows
  else if canColumns then
    rows := [columnsRow]
  else
    rows := [lastIdRow]
  if anyConverter returningFields then
    rows := rows.map (convertRow returningFields)
  return rows
-- impl-end

-- proof-start
theorem correct_insertReturnedRows :
    ∀ (returningFields : List RetField) (canBatch canColumns : Bool)
      (batchRows : List Row) (columnsRow lastIdRow : Row),
      problem_spec_insertReturnedRows returningFields canBatch canColumns
        batchRows columnsRow lastIdRow
        (implementation_insertReturnedRows returningFields canBatch canColumns
          batchRows columnsRow lastIdRow) := by
  intro returningFields canBatch canColumns batchRows columnsRow lastIdRow
  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows
  by_cases he : returningFields.isEmpty
  · simp only [he, Id.run, if_true]; rfl
  · by_cases hb : canBatch <;> by_cases hc : canColumns <;>
      by_cases ha : anyConverter returningFields <;>
      simp only [he, hb, hc, ha, Id.run, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_insertReturnedRows is a TOTAL FUNCTIONAL EQUATION: for every input tuple (returningFields, canBatch, canColumns, batchRows, columnsRow, lastIdRow) it pins `result` via `=` to exactly one canonical value. Any same-spec impl whose correct_ theorem closes must therefore be pointwise-equal to the gold function on the whole domain; behavioral divergence cannot coexist with a closing proof.

### Protocol executed
- same_spec: confirmed True for pos_control + all 7 attacks (swebench_unified.markers.same_spec, backend lean). Only the impl region was edited; axioms/pure/pre/post byte-identical.
- Verify cmd per file: `bash scripts/lean_verify.sh <file>`, run concurrently (batches of 4).

### ATTACK RESULTS (exit code; 0=verifies/no-sorry, 1=proof error):
  atk_1 = PREPATCH BUG (partial-domain: each pathway returns raw rows, converter step never runs) -> exit 1 (rfl fails at 126:54). This IS the Solution_prepatch.lean impl body + canonical proof; the bug is genuinely unprovable => prepatch reproduced.
  atk_2 = control-flow-effect: canColumns branch checked before canBatch -> exit 1.
  atk_3 = ungrounded/always-apply: drop the anyConverter guard, always map convertRow -> exit 1.
  atk_4 = boundary: missing returningFields.isEmpty short-circuit -> exit 1.
  atk_5 = wrong-value: last-id pathway returns [] instead of [lastIdRow] -> exit 1.
  atk_6 = negated guard: apply converters only when NO field has a converter -> exit 1.
  atk_7 = ECHO (output-equivalent `let selected`/early-return rewrite of the identical function) -> exit 0.
  pos_control (canonical gold impl) -> exit 0.

AXIOMS of verifying impls (`#print axioms correct_insertReturnedRows`): both pos_control and atk_7 => [propext, Quot.sound]. CLEAN — no sorryAx, no custom axioms.

### RESOLVE RUNS (swebench_unified.harness.run_resolve, SBU_BENCHMARK=swe_bench_verified, Docker oracle, timeout 1500, retries 1):
  GOLD patch.diff -> resolved=True completed=True (baseline sanity: harness+image work).
  atk_7 faithful patch (materialized above, renames rows->selected + early-returns the converter step; behaviorally identical to gold) -> resolved=True completed=True note='resolved'. So the ONLY non-canonical same-spec impl with a closing clean-axiom proof RESOLVES. No verify⇏correct witness exists.

Because all 6 genuinely-wrong impls fail to verify (proof `rfl` errors) and the sole verifying non-canonical impl (atk_7) resolves under the official harness, no same-spec impl with a closing clean-axiom proof has a faithful patch that fails to resolve. verify => correct holds for the exhibited attacks.

REFINEMENT AUDIT (refinement.md): 6 legs, ops 1-5 = R (type refinement), op 6 = I (identical). NO kind-3 (unjustified axiom). axioms region is empty and legitimately so per SPEC_GUIDE §3 — the CHANGED op (converter application) is modeled DEEPLY (convertRow=positional zip + applyChain left-fold; anyConverter=`if converters:` guard), which forbids axiomatizing it. The three UNCHANGED backend pathways (fetch_returned_insert_rows / fetch_returned_insert_columns / last_insert_id) enter as grounded inputs batchRows/columnsRow/lastIdRow, universally quantified in correct_, so no output component is left free or over-constrained. No A-legs to falsify; the deep model's correspondence to apply_converters is corroborated by the gold + atk_7 patches resolving. mapping.md type bijection consistent. R/I legs also covered mechanically by G-CONF (in-process oracle vs shadow, 120k fuzzed inputs, seed 14007).

CONCLUSION: >=5 distinct wrong impls attacked (7 total: prepatch, boundary, 2x control-flow-effect, ungrounded-oracle, negated-guard, echo). None with a closing clean-axiom proof has a non-resolving faithful patch. Spec is a sound total functional equation. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
import Mathlib
-- imports-end

/-!
Returning the rows produced by a row-creating database write.

When a row is created, the backend can hand back one or more column values for
that row (for example the freshly assigned primary key). Those values arrive as
a list of rows, each row being a tuple of raw cell values, and they may come from
one of several backend pathways depending on the connection's capabilities:

* a backend that can return several rows at once for a multi-row write returns
  them directly;
* a backend that can return columns for a single-row write returns one such row;
* otherwise a single last-inserted-id value is returned as a one-cell row.

Every field being returned may declare a chain of value converters — the same
converters a field uses to turn a stored value back into its Python form when it
is read by an ordinary query (e.g. a `from_db_value` hook that wraps a raw
integer in a wrapper object). The desired behaviour is that the values handed
back by a creating write are post-processed in exactly the same way as values
read by any other query:

  * the number of rows returned is unchanged;
  * each cell of each row is passed through the converter chain declared for the
    field in that column position (an empty chain leaves the cell unchanged);
  * if no returned field declares any converter, the rows are handed back
    untouched;
  * if no fields are being returned, the result is empty.

In particular a field whose converter wraps the raw value must see that wrapping
applied to the value produced by the creating write, just as it would for a value
fetched by a read.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The pathway
-- that produces the raw returned rows (single id, single returned row, or a
-- batch of returned rows) is upstream of and orthogonal to the modeled
-- behaviour; its result enters as grounded input data (the candidate row
-- values and the branch-selecting capability flags). The converter chain each
-- field declares likewise enters as grounded data. The post-processing itself
-- (applying each field's converter chain to the matching cell) is modeled
-- DEEPLY as a fold/map, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A returned field, carrying the ordered chain of value converters it declares.
A cell in this field's column is passed through `converters` left-to-right; an
empty chain means the cell is returned unchanged. Cell values are modeled as
`Int` (raw database scalars; a converter that "wraps" a value is modeled by the
function it applies). -/
structure RetField where
  converters : List (Int → Int)

/-- One returned row: a tuple of raw cell values, one per returned field. -/
abbrev Row := List Int

/-- Apply a field's converter chain to a single cell value, left-to-right.
An empty chain is the identity. -/
def applyChain (cs : List (Int → Int)) (x : Int) : Int :=
  cs.foldl (fun v f => f v) x

/-- Apply each field's converter chain to the matching cell of one row (the
field in column position `i` converts cell `i`). -/
def convertRow (fields : List RetField) (row : Row) : Row :=
  (fields.zip row).map (fun fc => applyChain fc.1.converters fc.2)

/-- Whether any returned field declares a non-empty converter chain. -/
def anyConverter (fields : List RetField) : Bool :=
  fields.any (fun f => !f.converters.isEmpty)
-- pure-end

-- post-conditions-start
/-- The rows returned by a creating write. `returningFields` are the fields whose
values are returned; `canBatch`/`canColumns` are the capability flags selecting
which backend pathway produced the raw rows; `batchRows`, `columnsRow`, and
`lastIdRow` are the candidate raw outputs of those three pathways. The result is
the selected raw rows with every field's converter chain applied (only if some
field declares a converter), or the empty list when no fields are returned. -/
def problem_spec_insertReturnedRows
    (returningFields : List RetField) (canBatch canColumns : Bool)
    (batchRows : List Row) (columnsRow lastIdRow : Row)
    (result : List Row) : Prop :=
  if returningFields.isEmpty then
    result = []
  else
    let selected : List Row :=
      if canBatch then batchRows
      else if canColumns then [columnsRow]
      else [lastIdRow]
    if anyConverter returningFields then
      result = selected.map (convertRow returningFields)
    else
      result = selected
-- post-conditions-end

-- impl-start
def implementation_insertReturnedRows
    (returningFields : List RetField) (canBatch canColumns : Bool)
    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do
  if returningFields.isEmpty then
    return []
  let mut rows : List Row := []
  if canBatch then
    rows := batchRows
  else if canColumns then
    rows := [columnsRow]
  else
    rows := [lastIdRow]
  if anyConverter returningFields then
    rows := rows.map (convertRow returningFields)
  return rows
-- impl-end

-- proof-start
theorem correct_insertReturnedRows :
    ∀ (returningFields : List RetField) (canBatch canColumns : Bool)
      (batchRows : List Row) (columnsRow lastIdRow : Row),
      problem_spec_insertReturnedRows returningFields canBatch canColumns
        batchRows columnsRow lastIdRow
        (implementation_insertReturnedRows returningFields canBatch canColumns
          batchRows columnsRow lastIdRow) := by
  intro returningFields canBatch canColumns batchRows columnsRow lastIdRow
  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows
  by_cases he : returningFields.isEmpty
  · simp only [he, Id.run, if_true]; rfl
  · by_cases hb : canBatch <;> by_cases hc : canColumns <;>
      by_cases ha : anyConverter returningFields <;>
      simp only [he, hb, hc, ha, Id.run, if_true] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_insertReturnedRows is a TOTAL FUNCTIONAL EQUATION: for every input tuple (returningFields, canBatch, canColumns, batchRows, columnsRow, lastIdRow) it pins `result` via `=` to exactly one canonical value. Any same-spec impl whose correct_ theorem closes must therefore be pointwise-equal to the gold function on the whole domain; behavioral divergence cannot coexist with a closing proof.

### Protocol executed
- same_spec: confirmed True for pos_control + all 7 attacks (swebench_unified.markers.same_spec, backend lean). Only the impl region was edited; axioms/pure/pre/post byte-identical.
- Verify cmd per file: `bash scripts/lean_verify.sh <file>`, run concurrently (batches of 4).

### ATTACK RESULTS (exit code; 0=verifies/no-sorry, 1=proof error):
  atk_1 = PREPATCH BUG (partial-domain: each pathway returns raw rows, converter step never runs) -> exit 1 (rfl fails at 126:54). This IS the Solution_prepatch.lean impl body + canonical proof; the bug is genuinely unprovable => prepatch reproduced.
  atk_2 = control-flow-effect: canColumns branch checked before canBatch -> exit 1.
  atk_3 = ungrounded/always-apply: drop the anyConverter guard, always map convertRow -> exit 1.
  atk_4 = boundary: missing returningFields.isEmpty short-circuit -> exit 1.
  atk_5 = wrong-value: last-id pathway returns [] instead of [lastIdRow] -> exit 1.
  atk_6 = negated guard: apply converters only when NO field has a converter -> exit 1.
  atk_7 = ECHO (output-equivalent `let selected`/early-return rewrite of the identical function) -> exit 0.
  pos_control (canonical gold impl) -> exit 0.

AXIOMS of verifying impls (`#print axioms correct_insertReturnedRows`): both pos_control and atk_7 => [propext, Quot.sound]. CLEAN — no sorryAx, no custom axioms.

### RESOLVE RUNS (swebench_unified.harness.run_resolve, SBU_BENCHMARK=swe_bench_verified, Docker oracle, timeout 1500, retries 1):
  GOLD patch.diff -> resolved=True completed=True (baseline sanity: harness+image work).
  atk_7 faithful patch (materialized above, renames rows->selected + early-returns the converter step; behaviorally identical to gold) -> resolved=True completed=True note='resolved'. So the ONLY non-canonical same-spec impl with a closing clean-axiom proof RESOLVES. No verify⇏correct witness exists.

Because all 6 genuinely-wrong impls fail to verify (proof `rfl` errors) and the sole verifying non-canonical impl (atk_7) resolves under the official harness, no same-spec impl with a closing clean-axiom proof has a faithful patch that fails to resolve. verify => correct holds for the exhibited attacks.

REFINEMENT AUDIT (refinement.md): 6 legs, ops 1-5 = R (type refinement), op 6 = I (identical). NO kind-3 (unjustified axiom). axioms region is empty and legitimately so per SPEC_GUIDE §3 — the CHANGED op (converter application) is modeled DEEPLY (convertRow=positional zip + applyChain left-fold; anyConverter=`if converters:` guard), which forbids axiomatizing it. The three UNCHANGED backend pathways (fetch_returned_insert_rows / fetch_returned_insert_columns / last_insert_id) enter as grounded inputs batchRows/columnsRow/lastIdRow, universally quantified in correct_, so no output component is left free or over-constrained. No A-legs to falsify; the deep model's correspondence to apply_converters is corroborated by the gold + atk_7 patches resolving. mapping.md type bijection consistent. R/I legs also covered mechanically by G-CONF (in-process oracle vs shadow, 120k fuzzed inputs, seed 14007).

CONCLUSION: >=5 distinct wrong impls attacked (7 total: prepatch, boundary, 2x control-flow-effect, ungrounded-oracle, negated-guard, echo). None with a closing clean-axiom proof has a non-resolving faithful patch. Spec is a sound total functional equation. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks: (1) scripts/lean_verify.sh on Solution.lean -> exit 0, compiles with no sorry/error. (2) #print axioms correct_insertReturnedRows -> [propext, Quot.sound]; NO sorryAx, proof is genuine. (3) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True -> spec region byte-identical; files differ only in impl region (post-patch converter application vs pre-patch immediate return), which is correct.

Faithfulness vs real SQLInsertCompiler.execute_sql at base_commit 619f26d2 (django/db/models/sql/compiler.py:1403-1421, get_converters/apply_converters:1100-1118): the spec models the POST-PATCH return path. Point-by-point: empty returning_fields -> [] (matches returningFields.isEmpty -> []); pathway selection via can_return_rows_from_bulk_insert&len(objs)>1 / can_return_columns_from_insert / last_insert_id (matches canBatch/canColumns/else); get_converters dict truthy iff some field has non-empty chain (matches anyConverter); apply_converters applies each converter position's chain left-to-right leaving other cells unchanged (matches convertRow/applyChain=foldl, empty chain=identity). All agree on the realizable domain where each row has exactly one cell per returning field.

The only modeling boundary is convertRow's fields.zip row truncating on length mismatch vs real apply_converters preserving full row length; this input class cannot arise from the real backend pathways (rows always carry len(returning_fields) cells), so it is not a genuine drift. The spec is neither too strong nor too weak: it is not stronger than reality (no unrealizable constraint is imposed that the real callee violates), and it faithfully pins result on every realizable input. Verdict: FAITHFUL.

Counterexample / evidence:

```
n/a (no realizable diverging input)
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: PASSED=True, no hard failures). Independent semantic review confirms no leak of the gold edit beyond the public problem_statement:

- The public problem_statement already discloses the entire target behavior and bug: 'Database converters (from_db_value) not called for returning_fields on insert ... on insert the returned integer is not passed through any database converters defined for the field'. It even names the single-row (create) and multi-row (bulk_create) pathways. So 'apply the field converter chains to returned rows on a creating write' is already fully public.
- Spec view contains NO diff markers, NO patched file path (django/db/models/sql/compiler.py), NO patched module dotted-path.
- No patched repo symbol appears (execute_sql, get_converters, apply_converters, fetch_returned_insert_rows/columns, last_insert_id). All spec identifiers are abstract Lean names (RetField, convertRow, applyChain, anyConverter, problem_spec_insertReturnedRows).
- No gold-patch changed line is reproduced (the >=8-char normalized substring check finds none).
- No bug/fix narration: the docstring is framed prospectively ('The desired behaviour is that ...'), never 'the bug was'/'previously'/'fixed'.
- The gold-edit SPECIFICS that are NOT in the problem statement (the structural refactor of the three `return X` pathways into `rows = X` so a uniform converter step can run; the `opts = self.query.get_meta()` hoist; `field.get_col(opts.db_table)` + `get_converters` plumbing) are entirely absent from the spec view. The three backend pathways modeled as grounded inputs are pre-existing structure, not the edit.

The spec discloses only the desired behavior, which the problem_statement already makes public, and none of the edit-localization/how-to-fix detail. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
