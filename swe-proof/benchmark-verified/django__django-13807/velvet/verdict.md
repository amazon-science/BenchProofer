# P2 adversarial audit — django__django-13807

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

Counterexample / evidence:

```
None found. The only same-spec wrong impl that VERIFIES is atk_7 (ungrounded-oracle echo: buildCheckStatements returns `checkStmts tables` and buildViolationStatements returns `violationStmts violations` directly). Its faithful refined patch is byte-identical to the gold patch (every SQL identifier routed through self.ops.quote_name), and it RESOLVES under the official harness (run_resolve: resolved=True, completed=True, attempts=1, flaky=False). An echo of the gold that resolves is NOT a spec weakness (per the resolved G-PANEL-1 echo-attack policy / G-EQ candidate->resolve check). All 6 genuinely-wrong impls (atk_3..atk_8, plus the two prepatch bugs atk_1/atk_2) FAIL verification, so verify does not admit a non-resolving impl.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,10 @@
       decreasing i
     do
       let t := tables[i - 1]!
-      result := fkCheckSql t :: result
+      -- Pre-image skeleton: the table identifier is embedded into the statement
+      -- raw, NOT through the identifier quoter. The frozen spec requires
+      -- `checkStmts` (whose `fkCheckSql` quotes), so prove_correct MUST fail.
+      result := ("PRAGMA foreign_key_check(".toList ++ t ++ ")".toList) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,7 +125,14 @@
       decreasing i
     do
       let v := violations[i - 1]!
-      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
+      -- Pre-image skeleton: the table/column identifiers are embedded raw, NOT
+      -- through the identifier quoter, in both the listing statement and the
+      -- value-fetch SELECT. The frozen spec requires `violationStmts` (which
+      -- quotes via fkListSql/selectSql), so prove_correct MUST fail.
+      let rawList := "PRAGMA foreign_key_list(".toList ++ v.table ++ ")".toList
+      let rawSelect := "SELECT ".toList ++ v.pk ++ ", ".toList ++ v.col
+        ++ " FROM ".toList ++ v.table ++ " WHERE rowid = %s".toList
+      result := rawList :: rawSelect :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -116,17 +116,9 @@
   ensures out = violationStmts violations
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := violations.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ violations.length
-      invariant result = violationStmts (violations.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let v := violations[i - 1]!
-      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
-      i := i - 1
+    -- Partial-domain attack: correct only when the list is empty; returns the
+    -- empty statement sequence unconditionally.
+    let result : List (List Char) := []
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,9 @@
       done_with i = 0
       decreasing i
     do
-      let t := tables[i - 1]!
+      -- Boundary/off-by-one attack: reads the wrong element (index i, not i-1),
+      -- so the assembled sequence is shifted / uses out-of-range default.
+      let t := tables[i]!
       result := fkCheckSql t :: result
       i := i - 1
     return result
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,10 @@
       done_with i = 0
       decreasing i
     do
+      -- Control-flow-effect attack: emits the two per-row statements in the
+      -- WRONG order (value-fetch before the fk-listing).
       let v := violations[i - 1]!
-      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
+      result := selectSql v.pk v.col v.table :: fkListSql v.table :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,10 @@
       done_with i = 0
       decreasing i
     do
+      -- Wrong-wiring attack: swaps pk and col in the value-fetch SELECT, so the
+      -- two identifier positions are transposed relative to the gold template.
       let v := violations[i - 1]!
-      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
+      result := fkListSql v.table :: selectSql v.col v.pk v.table :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,18 +94,10 @@
   ensures out = checkStmts tables
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := tables.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ tables.length
-      invariant result = checkStmts (tables.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let t := tables[i - 1]!
-      result := fkCheckSql t :: result
-      i := i - 1
-    return result
+    -- Ungrounded-oracle echo: return the spec function directly. Behaviourally
+    -- identical to the gold (same quoted statements), so its faithful patch
+    -- must resolve — included to confirm the echo path is not falsely broken.
+    return checkStmts tables
     -- impl-end
 
 /- Build, in order, the per-row statements (listing then value-fetch) for each
@@ -116,18 +108,7 @@
   ensures out = violationStmts violations
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := violations.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ violations.length
-      invariant result = violationStmts (violations.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let v := violations[i - 1]!
-      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
-      i := i - 1
-    return result
+    return violationStmts violations
     -- impl-end
 
 /- Backward-fold step: dropping one fewer table exposes the table at `i-1` on the
@@ -162,10 +143,6 @@
 
 prove_correct buildCheckStatements by
   loom_solve
-  rw [checkStmts_drop_step tables i (by omega) (by omega)]
-  simp_all
 
 prove_correct buildViolationStatements by
   loom_solve
-  rw [violationStmts_drop_step violations i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,8 +102,10 @@
       done_with i = 0
       decreasing i
     do
+      -- Wrong-builder attack: emits the foreign_key_LIST statement where the
+      -- integrity-check (foreign_key_CHECK) statement is required.
       let t := tables[i - 1]!
-      result := fkCheckSql t :: result
+      result := fkListSql t :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the real statement builders are finite passes
-- over the input lists that always return their statement sequences (the F2P
-- test observes those return values), so the spec must also rule out
-- implementations that diverge — under partial correctness a non-terminating
-- body would vacuously satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized. The one routine the construction below
   relies on — the backend's SQL identifier quoter — is modeled DEEPLY by
   `quoteIdent` (pure region), validated `quoteIdent == the real quoter` by
   axiom_check.py (G-AX). It is therefore an A-reference, not a consumed axiom
   (mapping.md §3). Everything observable is computed from the inputs; nothing
   is borrowed from an oracle. -/
-- axioms-end

-- pure-start
/- The backend's SQL identifier quoter (deep model, A-reference). A bare
   identifier is wrapped in double quotes so it cannot collide with reserved
   words; an identifier that is already double-quoted is returned unchanged
   (quoting once is enough). This is the per-identifier transform the statement
   builders below apply at every position where an identifier is embedded in a
   statement. Soundness vs the real quoter: mapping.md §3 / axiom_check.py. -/
def quoteIdent (name : List Char) : List Char :=
  if name.head? = some '"' ∧ name.getLast? = some '"' then name
  else '"' :: (name ++ ['"'])

/- The integrity-check statement for one table: a constant prefix, the table
   identifier (quoted), and the closing parenthesis. -/
def fkCheckSql (table : List Char) : List Char :=
  "PRAGMA foreign_key_check(".toList ++ quoteIdent table ++ ")".toList

/- The foreign-key-listing statement for one table (quoted identifier). -/
def fkListSql (table : List Char) : List Char :=
  "PRAGMA foreign_key_list(".toList ++ quoteIdent table ++ ")".toList

/- The value-fetch statement for one offending row: a SELECT of the primary-key
   column and the referencing column from the table, all three identifiers
   quoted, with the row addressed by a bound parameter. -/
def selectSql (pk col table : List Char) : List Char :=
  "SELECT ".toList ++ quoteIdent pk ++ ", ".toList ++ quoteIdent col
    ++ " FROM ".toList ++ quoteIdent table ++ " WHERE rowid = %s".toList

/- The list of integrity-check statements produced for a list of table names:
   one statement per table, in order. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def checkStmts : List (List Char) → List (List Char)
  | []      => []
  | t :: ts => fkCheckSql t :: checkStmts ts

@[grind] lemma checkStmts_nil : checkStmts [] = [] := rfl
@[grind] lemma checkStmts_cons (t : List Char) (ts : List (List Char)) :
    checkStmts (t :: ts) = fkCheckSql t :: checkStmts ts := rfl

/- One offending row, identified by the three identifiers the value-fetch needs:
   the table, its primary-key column, and the referencing column. -/
structure Violation where
  table : List Char
  pk : List Char
  col : List Char
deriving Inhabited, DecidableEq

/- The statements produced while processing a list of offending rows: per row,
   first its foreign-key-listing statement, then its value-fetch statement, in
   that order. Front-recursive (two statements peeled per row). -/
def violationStmts : List Violation → List (List Char)
  | []      => []
  | v :: vs => fkListSql v.table :: selectSql v.pk v.col v.table :: violationStmts vs

@[grind] lemma violationStmts_nil : violationStmts [] = [] := rfl
@[grind] lemma violationStmts_cons (v : Violation) (vs : List Violation) :
    violationStmts (v :: vs)
      = fkListSql v.table :: selectSql v.pk v.col v.table :: violationStmts vs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build, in order, the integrity-check statement for each table name. The input
   `tables` is read-only (not `mut`): the method threads a fresh accumulator and
   never mutates what it is handed (directive 5). Each table identifier embedded
   in a statement is the quoted form, so a reserved word used as a table name is
   safe. -/
method buildCheckStatements (tables : List (List Char)) return (out : List (List Char))
  ensures out = checkStmts tables
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := tables.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ tables.length
      invariant result = checkStmts (tables.drop i)
      done_with i = 0
      decreasing i
    do
      let t := tables[i - 1]!
      result := fkCheckSql t :: result
      i := i - 1
    return result
    -- impl-end

/- Build, in order, the per-row statements (listing then value-fetch) for each
   offending row. `violations` is read-only (not `mut`). Every identifier — the
   table, the primary-key column, the referencing column — embedded in a
   statement is the quoted form. -/
method buildViolationStatements (violations : List Violation) return (out : List (List Char))
  ensures out = violationStmts violations
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := violations.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ violations.length
      invariant result = violationStmts (violations.drop i)
      done_with i = 0
      decreasing i
    do
      let v := violations[i - 1]!
      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
      i := i - 1
    return result
    -- impl-end

/- Backward-fold step: dropping one fewer table exposes the table at `i-1` on the
   front, so `checkStmts` peels one statement. The single goal `loom_solve`
   leaves for the loop body. -/
lemma checkStmts_drop_step (tables : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ tables.length) :
    checkStmts (tables.drop (i - 1)) = fkCheckSql tables[i - 1]! :: checkStmts (tables.drop i) := by
  have hlt : i - 1 < tables.length := by omega
  have hcons : tables.drop (i - 1) = tables[i - 1]! :: tables.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, checkStmts_cons]

/- Backward-fold step for the per-row statements: dropping one fewer row exposes
   the row at `i-1`, so `violationStmts` peels its two statements. -/
lemma violationStmts_drop_step (violations : List Violation) (i : Nat)
    (hi : 0 < i) (hle : i ≤ violations.length) :
    violationStmts (violations.drop (i - 1))
      = fkListSql violations[i - 1]!.table
          :: selectSql violations[i - 1]!.pk violations[i - 1]!.col violations[i - 1]!.table
          :: violationStmts (violations.drop i) := by
  have hlt : i - 1 < violations.length := by omega
  have hcons : violations.drop (i - 1) = violations[i - 1]! :: violations.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, violationStmts_cons]

prove_correct buildCheckStatements by
  loom_solve
  rw [checkStmts_drop_step tables i (by omega) (by omega)]
  simp_all

prove_correct buildViolationStatements by
  loom_solve
  rw [violationStmts_drop_step violations i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-13807 velvet.

SPEC SHAPE: The two methods carry FULL functional postconditions `ensures out = checkStmts tables` / `ensures out = violationStmts violations` with total-correctness + demonic-choice semantics and no precondition. This pins the output exactly (statement text, order, per-element expansion, and identifier quoting via quoteIdent inside fkCheckSql/fkListSql/selectSql). A wrong impl cannot diverge (total correctness) or return a different sequence.

SAME-SPEC: All 8 attack files + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec on velvet.language (impl regions + prove_correct bodies are elided from the spec view, so editing them is spec-preserving).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean: exit 0 (VERIFIES) — positive control.
- atk_1.lean (prepatch site1, table inserted raw/unquoted): exit 1.
- atk_2.lean (prepatch sites 2+3, identifiers raw/unquoted): exit 1.
- atk_3.lean (partial-domain: buildViolationStatements returns [] always): exit 1.
- atk_4.lean (boundary/off-by-one: tables[i]! instead of tables[i-1]!): exit 1.
- atk_5.lean (control-flow-effect: emits the two per-row statements in swapped order, selectSql before fkListSql): exit 1.
- atk_6.lean (wrong-wiring: selectSql v.col v.pk v.table — pk/col transposed): exit 1.
- atk_7.lean (ungrounded-oracle echo: returns spec functions directly; proofs reduced to loom_solve): exit 0 (VERIFIES), same_spec re-confirmed True after proof-body edit.
- atk_8.lean (wrong-builder: fkListSql used where fkCheckSql required): exit 1.

RESOLVE (protocol step 2 — for the ONE verifying wrong impl, atk_7): materialized its faithful patch at atk_7_faithful.patch and ran swebench_unified.harness.run_resolve('django__django-13807', patch, timeout=1800, retries=1). RESULT: resolved=True, completed=True, note='resolved', flaky=False, attempts=1. Patch applied cleanly; hidden FAIL_TO_PASS+PASS_TO_PASS passed. So the verifying impl's faithful patch DOES resolve -> spec is NOT broken by it.

Docker under contention from a concurrent (other-backend containers present); load ~38, healthy; resolve completed cleanly in ~25min wall.

REFINEMENT.MD AUDIT (A-legs / model<->patch correspondence): Every leg is R, A-reference, or I; no kind-3. A1/B1 = R (list[str] <-> List (List Char); Violation{table,pk,col} <-> the three quoted identifier positions; rowid/foreign_key_index/referenced_table_name correctly excluded as non-identifiers). A3/A4/B4/B5 = I (literal fragments + identifier positions transliterated 1:1; order pk,col,table matches the gold tuple; %%s -> literal ` rowid = %s` bound param). A2/B2/B3 = A-reference: the identifier quoter is modeled DEEPLY by quoteIdent in the pure region (NOT a consumed axiom), validated quoteIdent==quote_name by axiom_check.py (G-AX).

I hand-checked the correspondence against the base_commit source in mapping.md 3.1: quote_name returns name unchanged iff it starts and ends with '"' else '"%s"' % name; quoteIdent returns name iff head?=some '"' and getLast?=some '"' else '"' :: (name ++ ['"']). Boundary cases agree: empty '' -> '""' (Lean [] head?=none -> else -> ['"','"']); single '"' -> returned unchanged both sides; keywords order/select/where -> '"order"' etc. Correspondence holds. There is genuinely no consumed axiom (axioms region is empty prose); the only foreign callee (quote_name) is unchanged by the patch and G-AX-validated. §D 'no kind-3' claim is accurate: the changed operation (adding quoting) is modeled in the pure spec, not hidden behind an axiom about check_constraints (which is never axiomatized).

CONCLUSION: verify => resolved holds. Every genuinely-wrong impl (partial-domain, boundary, control-flow-effect, wrong-wiring, wrong-builder, plus both prepatch bugs) FAILS to verify against the exact functional postcondition; the sole verifying same-spec impl is a gold-equivalent echo whose materialized faithful patch RESOLVES. No verify-but-not-resolve counterexample exists. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only same-spec wrong impl that VERIFIES is atk_7 (ungrounded-oracle echo: buildCheckStatements returns `checkStmts tables` and buildViolationStatements returns `violationStmts violations` directly). Its faithful refined patch is byte-identical to the gold patch (every SQL identifier routed through self.ops.quote_name), and it RESOLVES under the official harness (run_resolve: resolved=True, completed=True, attempts=1, flaky=False). An echo of the gold that resolves is NOT a spec weakness (per the resolved G-PANEL-1 echo-attack policy / G-EQ candidate->resolve check). All 6 genuinely-wrong impls (atk_3..atk_8, plus the two prepatch bugs atk_1/atk_2) FAIL verification, so verify does not admit a non-resolving impl.
```

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

-- Total-correctness semantics: the real statement builders are finite passes
-- over the input lists that always return their statement sequences (the F2P
-- test observes those return values), so the spec must also rule out
-- implementations that diverge — under partial correctness a non-terminating
-- body would vacuously satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized. The one routine the construction below
   relies on — the backend's SQL identifier quoter — is modeled DEEPLY by
   `quoteIdent` (pure region), validated `quoteIdent == the real quoter` by
   axiom_check.py (G-AX). It is therefore an A-reference, not a consumed axiom
   (mapping.md §3). Everything observable is computed from the inputs; nothing
   is borrowed from an oracle. -/
-- axioms-end

-- pure-start
/- The backend's SQL identifier quoter (deep model, A-reference). A bare
   identifier is wrapped in double quotes so it cannot collide with reserved
   words; an identifier that is already double-quoted is returned unchanged
   (quoting once is enough). This is the per-identifier transform the statement
   builders below apply at every position where an identifier is embedded in a
   statement. Soundness vs the real quoter: mapping.md §3 / axiom_check.py. -/
def quoteIdent (name : List Char) : List Char :=
  if name.head? = some '"' ∧ name.getLast? = some '"' then name
  else '"' :: (name ++ ['"'])

/- The integrity-check statement for one table: a constant prefix, the table
   identifier (quoted), and the closing parenthesis. -/
def fkCheckSql (table : List Char) : List Char :=
  "PRAGMA foreign_key_check(".toList ++ quoteIdent table ++ ")".toList

/- The foreign-key-listing statement for one table (quoted identifier). -/
def fkListSql (table : List Char) : List Char :=
  "PRAGMA foreign_key_list(".toList ++ quoteIdent table ++ ")".toList

/- The value-fetch statement for one offending row: a SELECT of the primary-key
   column and the referencing column from the table, all three identifiers
   quoted, with the row addressed by a bound parameter. -/
def selectSql (pk col table : List Char) : List Char :=
  "SELECT ".toList ++ quoteIdent pk ++ ", ".toList ++ quoteIdent col
    ++ " FROM ".toList ++ quoteIdent table ++ " WHERE rowid = %s".toList

/- The list of integrity-check statements produced for a list of table names:
   one statement per table, in order. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def checkStmts : List (List Char) → List (List Char)
  | []      => []
  | t :: ts => fkCheckSql t :: checkStmts ts

@[grind] lemma checkStmts_nil : checkStmts [] = [] := rfl
@[grind] lemma checkStmts_cons (t : List Char) (ts : List (List Char)) :
    checkStmts (t :: ts) = fkCheckSql t :: checkStmts ts := rfl

/- One offending row, identified by the three identifiers the value-fetch needs:
   the table, its primary-key column, and the referencing column. -/
structure Violation where
  table : List Char
  pk : List Char
  col : List Char
deriving Inhabited, DecidableEq

/- The statements produced while processing a list of offending rows: per row,
   first its foreign-key-listing statement, then its value-fetch statement, in
   that order. Front-recursive (two statements peeled per row). -/
def violationStmts : List Violation → List (List Char)
  | []      => []
  | v :: vs => fkListSql v.table :: selectSql v.pk v.col v.table :: violationStmts vs

@[grind] lemma violationStmts_nil : violationStmts [] = [] := rfl
@[grind] lemma violationStmts_cons (v : Violation) (vs : List Violation) :
    violationStmts (v :: vs)
      = fkListSql v.table :: selectSql v.pk v.col v.table :: violationStmts vs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build, in order, the integrity-check statement for each table name. The input
   `tables` is read-only (not `mut`): the method threads a fresh accumulator and
   never mutates what it is handed (directive 5). Each table identifier embedded
   in a statement is the quoted form, so a reserved word used as a table name is
   safe. -/
method buildCheckStatements (tables : List (List Char)) return (out : List (List Char))
  ensures out = checkStmts tables
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := tables.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ tables.length
      invariant result = checkStmts (tables.drop i)
      done_with i = 0
      decreasing i
    do
      let t := tables[i - 1]!
      result := fkCheckSql t :: result
      i := i - 1
    return result
    -- impl-end

/- Build, in order, the per-row statements (listing then value-fetch) for each
   offending row. `violations` is read-only (not `mut`). Every identifier — the
   table, the primary-key column, the referencing column — embedded in a
   statement is the quoted form. -/
method buildViolationStatements (violations : List Violation) return (out : List (List Char))
  ensures out = violationStmts violations
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := violations.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ violations.length
      invariant result = violationStmts (violations.drop i)
      done_with i = 0
      decreasing i
    do
      let v := violations[i - 1]!
      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result
      i := i - 1
    return result
    -- impl-end

/- Backward-fold step: dropping one fewer table exposes the table at `i-1` on the
   front, so `checkStmts` peels one statement. The single goal `loom_solve`
   leaves for the loop body. -/
lemma checkStmts_drop_step (tables : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ tables.length) :
    checkStmts (tables.drop (i - 1)) = fkCheckSql tables[i - 1]! :: checkStmts (tables.drop i) := by
  have hlt : i - 1 < tables.length := by omega
  have hcons : tables.drop (i - 1) = tables[i - 1]! :: tables.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, checkStmts_cons]

/- Backward-fold step for the per-row statements: dropping one fewer row exposes
   the row at `i-1`, so `violationStmts` peels its two statements. -/
lemma violationStmts_drop_step (violations : List Violation) (i : Nat)
    (hi : 0 < i) (hle : i ≤ violations.length) :
    violationStmts (violations.drop (i - 1))
      = fkListSql violations[i - 1]!.table
          :: selectSql violations[i - 1]!.pk violations[i - 1]!.col violations[i - 1]!.table
          :: violationStmts (violations.drop i) := by
  have hlt : i - 1 < violations.length := by omega
  have hcons : violations.drop (i - 1) = violations[i - 1]! :: violations.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, violationStmts_cons]

prove_correct buildCheckStatements by
  loom_solve
  rw [checkStmts_drop_step tables i (by omega) (by omega)]
  simp_all

prove_correct buildViolationStatements by
  loom_solve
  rw [violationStmts_drop_step violations i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-13807 velvet.

SPEC SHAPE: The two methods carry FULL functional postconditions `ensures out = checkStmts tables` / `ensures out = violationStmts violations` with total-correctness + demonic-choice semantics and no precondition. This pins the output exactly (statement text, order, per-element expansion, and identifier quoting via quoteIdent inside fkCheckSql/fkListSql/selectSql). A wrong impl cannot diverge (total correctness) or return a different sequence.

SAME-SPEC: All 8 attack files + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec on velvet.language (impl regions + prove_correct bodies are elided from the spec view, so editing them is spec-preserving).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean: exit 0 (VERIFIES) — positive control.
- atk_1.lean (prepatch site1, table inserted raw/unquoted): exit 1.
- atk_2.lean (prepatch sites 2+3, identifiers raw/unquoted): exit 1.
- atk_3.lean (partial-domain: buildViolationStatements returns [] always): exit 1.
- atk_4.lean (boundary/off-by-one: tables[i]! instead of tables[i-1]!): exit 1.
- atk_5.lean (control-flow-effect: emits the two per-row statements in swapped order, selectSql before fkListSql): exit 1.
- atk_6.lean (wrong-wiring: selectSql v.col v.pk v.table — pk/col transposed): exit 1.
- atk_7.lean (ungrounded-oracle echo: returns spec functions directly; proofs reduced to loom_solve): exit 0 (VERIFIES), same_spec re-confirmed True after proof-body edit.
- atk_8.lean (wrong-builder: fkListSql used where fkCheckSql required): exit 1.

RESOLVE (protocol step 2 — for the ONE verifying wrong impl, atk_7): materialized its faithful patch at atk_7_faithful.patch and ran swebench_unified.harness.run_resolve('django__django-13807', patch, timeout=1800, retries=1). RESULT: resolved=True, completed=True, note='resolved', flaky=False, attempts=1. Patch applied cleanly; hidden FAIL_TO_PASS+PASS_TO_PASS passed. So the verifying impl's faithful patch DOES resolve -> spec is NOT broken by it.

Docker under contention from a concurrent (other-backend containers present); load ~38, healthy; resolve completed cleanly in ~25min wall.

REFINEMENT.MD AUDIT (A-legs / model<->patch correspondence): Every leg is R, A-reference, or I; no kind-3. A1/B1 = R (list[str] <-> List (List Char); Violation{table,pk,col} <-> the three quoted identifier positions; rowid/foreign_key_index/referenced_table_name correctly excluded as non-identifiers). A3/A4/B4/B5 = I (literal fragments + identifier positions transliterated 1:1; order pk,col,table matches the gold tuple; %%s -> literal ` rowid = %s` bound param). A2/B2/B3 = A-reference: the identifier quoter is modeled DEEPLY by quoteIdent in the pure region (NOT a consumed axiom), validated quoteIdent==quote_name by axiom_check.py (G-AX).

I hand-checked the correspondence against the base_commit source in mapping.md 3.1: quote_name returns name unchanged iff it starts and ends with '"' else '"%s"' % name; quoteIdent returns name iff head?=some '"' and getLast?=some '"' else '"' :: (name ++ ['"']). Boundary cases agree: empty '' -> '""' (Lean [] head?=none -> else -> ['"','"']); single '"' -> returned unchanged both sides; keywords order/select/where -> '"order"' etc. Correspondence holds. There is genuinely no consumed axiom (axioms region is empty prose); the only foreign callee (quote_name) is unchanged by the patch and G-AX-validated. §D 'no kind-3' claim is accurate: the changed operation (adding quoting) is modeled in the pure spec, not hidden behind an axiom about check_constraints (which is never axiomatized).

CONCLUSION: verify => resolved holds. Every genuinely-wrong impl (partial-domain, boundary, control-flow-effect, wrong-wiring, wrong-builder, plus both prepatch bugs) FAILS to verify against the exact functional postcondition; the sole verifying same-spec impl is a gold-equivalent echo whose materialized faithful patch RESOLVES. No verify-but-not-resolve counterexample exists. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13807 (velvet). No diverging input found; spec is FAITHFUL to the real repo behavior.

Method & evidence:
1) Spec-region hygiene: same_spec(Solution.lean, Solution_prepatch_1.lean, velvet)=True and same_spec(..., prepatch_2, ...)=True. Both prepatch variants share a byte-identical spec region with Solution.lean; the fix discriminator lives only in the impl regions. Spec is not tailored per-variant.

2) quoteIdent deep model vs real callee. Real DatabaseOperations.quote_name at base_commit 89fc144 (django/db/backends/sqlite3/operations.py:170):
   def quote_name(self,name):
     if name.startswith('"') and name.endswith('"'): return name
     return '"%s"' % name
 Lean quoteIdent = (if head?=some '"' /\ getLast?=some '"' then name else '"'::(name++['"'])). Ran quote_name vs quoteIdent on 200,018 inputs (seed 13807 fuzz + boundary cases: '', '"', '""', '"x', 'x"', '"x"', 'order','select','where', quote-embedded strings, whitespace). ZERO mismatches. Note startswith/endswith on the single char '"' returns True in both languages (name[0]==name[-1]=='"'), and empty string agrees (both wrap to '""'). No over-/under-strengthening at the quoter boundary.

3) Statement builders vs gold post-patch templates (base.py check_constraints): fkCheckSql='PRAGMA foreign_key_check(' ++ q ++ ')', fkListSql='PRAGMA foreign_key_list(' ++ q ++ ')', selectSql='SELECT ' ++ qpk ++ ', ' ++ qcol ++ ' FROM ' ++ qtable ++ ' WHERE rowid = %s'. These match the gold '%'-format assemblies exactly (%%s -> literal %s; identifier order pk,col,table == gold tuple (primary_key_column_name, column_name, table_name)).

4) Scope of Violation {table,pk,col} is correct/not-too-strong: rowid (bound param), foreign_key_index (list index), referenced_table_name (only in the error message) are legitimately excluded — none is an identifier embedded in constructed SQL.

5) Termination: loom.semantics.termination=total is faithful — the real construction is a finite terminating pass over the input lists returning statement sequences the F2P test observes; total correctness rules out divergent same-spec impls the tests would reject. Not spuriously strong.

6) Solution.lean verifies (lean_verify.sh exit 0).

No input exists where the modeled function disagrees with the real repo. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit for django__django-13807 (velvet). Spec region verified byte-identical: markers.same_spec(velvet) == True for both Solution_prepatch_1.lean and Solution_prepatch_2.lean vs Solution.lean. Rendered the leakage-relevant spec view via markers.spec_view(velvet) and ran leakage.screen against the frozen gold patch + problem_statement: rep.passed == True, hard_failures empty (no L1/L2/L3/L5). G-LEAK meta status = pass, strict; not a relaxed bundle (relaxed_leakage None, no RELAXED_LEAKAGE.md).

Gold edit: route every SQL identifier through the backend quoter (self.ops.quote_name(...), double-quote wrap) at three sites in check_constraints (base.py:327-348).

The public problem_statement already discloses the essence of the fix: it states table name 'order' 'is not quoted properly', names the root cause as 'missing back ticks around %s in the SQL statement PRAGMA foreign_key_check(%s)', and prints the literal buggy SQL for both PRAGMA sites with full code context. So 'quote the embedded identifiers' is already public.

Spec view exposure: quoteIdent (double-quote-wrap, idempotent), fkCheckSql/fkListSql/selectSql applying it at each identifier position, and the ordered folds. This is a faithful formalization of the already-public quoting fix, not new gold leakage. Checks: (1) no diff markers; (2) no gold-patch line reproduced (>=8 normalized chars) — none matched; (3) patched file path django/db/backends/sqlite3/base.py and dotted module absent from view; (4) the only distinctive changed symbol is 'check_constraints' (len>=4) and it does NOT appear anywhere in the spec view — the spec uses buildCheckStatements/buildViolationStatements/checkStmts/violationStmts, none embedding it; (5) comments describe behavior abstractly ('wrapped in double quotes so it cannot collide with reserved words') with no _NARRATION terms (bug/fix/wrong/broken/etc.) and no repo-symbol names. The third SELECT column-quoting site (not literally shown in the problem statement) is a faithful generalization of the disclosed 'quote the identifiers' fix, not a leaked gold-patch specific. Spec reveals nothing beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.