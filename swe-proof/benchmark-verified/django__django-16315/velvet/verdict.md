# P2 adversarial audit — django__django-16315

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -67,10 +67,9 @@
       invariant 0 ≤ i ∧ i ≤ fields.length
       invariant acc = dbColumns (fields.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := fields[i - 1]!
-      acc := [f.column] ++ acc
+      acc := [f.attr] ++ acc
       i := i - 1
     return acc
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -61,17 +61,7 @@
   ensures out = dbColumns fields
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut i := fields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ fields.length
-      invariant acc = dbColumns (fields.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := fields[i - 1]!
-      acc := [f.column] ++ acc
-      i := i - 1
+    let acc : List (List Char) := []
     return acc
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -62,16 +62,15 @@
   do
     -- impl-start
     let mut acc : List (List Char) := []
-    let mut i := fields.length
-    while i > 0
+    let mut i := 0
+    while i < fields.length
       invariant 0 ≤ i ∧ i ≤ fields.length
-      invariant acc = dbColumns (fields.drop i)
-      done_with i = 0
-      decreasing i
+      invariant acc = (dbColumns (fields.take i)).reverse
+      done_with i = fields.length
     do
-      let f := fields[i - 1]!
+      let f := fields[i]!
       acc := [f.column] ++ acc
-      i := i - 1
+      i := i + 1
     return acc
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -63,11 +63,10 @@
     -- impl-start
     let mut acc : List (List Char) := []
     let mut i := fields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ fields.length
+    while i > 1
+      invariant 1 ≤ i ∧ i ≤ fields.length
       invariant acc = dbColumns (fields.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let f := fields[i - 1]!
       acc := [f.column] ++ acc
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -67,10 +67,9 @@
       invariant 0 ≤ i ∧ i ≤ fields.length
       invariant acc = dbColumns (fields.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := fields[i - 1]!
-      acc := [f.column] ++ acc
+      acc := [f.column, f.column] ++ acc
       i := i - 1
     return acc
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -67,10 +67,9 @@
       invariant 0 ≤ i ∧ i ≤ fields.length
       invariant acc = dbColumns (fields.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := fields[i - 1]!
-      acc := [f.column] ++ acc
+      acc := [f.column] ++ [f.attr] ++ acc
       i := i - 1
     return acc
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -67,10 +67,10 @@
       invariant 0 ≤ i ∧ i ≤ fields.length
       invariant acc = dbColumns (fields.drop i)
       done_with i = 0
-      decreasing i
     do
       let f := fields[i - 1]!
-      acc := [f.column] ++ acc
+      let tok := if i = 1 then f.attr else f.column
+      acc := [tok] ++ acc
       i := i - 1
     return acc
     -- impl-end
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
 -- (No axiomatized callees. The list of fields whose conflict-resolution tokens
@@ -61,18 +61,7 @@
   ensures out = dbColumns fields
   do
     -- impl-start
-    let mut acc : List (List Char) := []
-    let mut i := fields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ fields.length
-      invariant acc = dbColumns (fields.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := fields[i - 1]!
-      acc := [f.column] ++ acc
-      i := i - 1
-    return acc
+    return dbColumns fields
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the field at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The list of fields whose conflict-resolution tokens
--  are built is a FREE INPUT: how each field was obtained from the caller's
--  request is UNCHANGED and upstream of the modeled boundary, so the spec makes
--  no behavioural claim about it. Each field exposes two observable string
--  attributes (its model attribute name and its database column); both are plain
--  projections carried directly by the `Field` structure, so there is nothing to
--  validate against a real callee — hence no G-AX.)
-- axioms-end

-- pure-start
/- A persisted field, abstracted to its two observable string attributes: the
   model-side attribute name (`attr`) and the database column name (`column`).
   For a field declared with an explicit database column these differ (e.g. a
   mixed-case column under a lower-case attribute); otherwise the column equals
   the attribute. Only these two strings are observable to a consumer of the
   generated conflict-resolution clause, so this is the faithful carrier. -/
structure Field where
  attr   : List Char
  column : List Char
deriving DecidableEq, Inhabited

/- The database-column tokens of a sequence of fields: the database column of
   each field, taken in order. Written front-recursively so a single unfold is
   available per loop step (the backward fold pattern, plan §5.4). Empty
   sequence ⇒ empty result. -/
def dbColumns : List Field → List (List Char)
  | []      => []
  | f :: fs => [f.column] ++ dbColumns fs

@[grind] lemma dbColumns_nil : dbColumns [] = [] := rfl
@[grind] lemma dbColumns_cons (f : Field) (fs : List Field) :
    dbColumns (f :: fs) = [f.column] ++ dbColumns fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the list of tokens that identify each field in a generated
   conflict-resolution clause (the target of the conflict and the columns it
   updates). Each field must be referred to by its DATABASE COLUMN, taken in the
   given order — NOT by its model attribute name, which may differ from the
   column. The SAME operation produces both the conflict-target tokens and the
   updated-column tokens, so one model covers both argument positions
   (refinement.md §A).

   `fields` is read-only (directive 5): the operation reads each field's column
   and never mutates the input sequence. -/
method conflictColumns (fields : List Field) return (out : List (List Char))
  ensures out = dbColumns fields
  do
    -- impl-start
    let mut acc : List (List Char) := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant acc = dbColumns (fields.drop i)
      done_with i = 0
    do
      let f := fields[i - 1]!
      acc := [f.column] ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the field at
   `i-1` on the front, so `dbColumns` peels one column. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma dbColumns_drop_step (fields : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    dbColumns (fields.drop (i - 1)) = [fields[i - 1]!.column] ++ dbColumns (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, dbColumns_cons]

prove_correct conflictColumns by
  loom_solve
  rw [dbColumns_drop_step fields i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit (velvet, django__django-16315), project root. Spec pins `ensures out = dbColumns fields` where dbColumns(f::fs)=[f.column]++dbColumns fs -- an EXACT equality with a transparent total function. Any verifying impl is therefore behaviourally identical to dbColumns fields = the gold comprehension (f.column for f in fields). NO verifying-but-wrong impl exists, so there is no faithful patch to run through the harness; verify=>correct holds. Hence patches={} (nothing to resolve-run).

SAME-SPEC: all 8 attacks + prepatch + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec(velvet); impl region only edited, axioms/pure/pre/post byte-identical.

CMD each: bash scripts/lean_verify.sh <file> (run concurrently in batches of 4; interference-safe, read-only lean_shared).

### RESULTS (verify exit codes):
- pos_control.lean (gold column-emitting backward fold): exit 0 VERIFIES -> spec non-vacuous, admits correct impl.
- prepatch.lean: exit 1, unsolved goal (fields[i-1]?.getD default).attr = (...).column (literally f.attr=f.column) -> column-vs-name discriminator; prepatch bug reproduced for the right reason.
- atk_1 (emit f.attr = prepatch bug): exit 1, goal f.attr=f.column.
- atk_2 (return []): exit 1, goal [] = dbColumns fields.
- atk_3 (reversed order, forward prepend): exit 1, goal [fields[i]!.column]++acc = (dbColumns(take(i+1))).reverse.
- atk_4 (off-by-one, skip first field, while i>1): exit 1, goal i_1 = dbColumns fields.
- atk_5 (emit each column twice): exit 1, loop step reduces to False.
- atk_6 (emit [f.column,f.attr] per field): exit 1, loop step reduces to False.
- atk_7 (partial-domain: attr only on first field, if i=1 then f.attr): exit 1, goal i=1 -> f.attr=f.column.
- atk_8 (ungrounded-oracle echo: return dbColumns fields): exit 1, error 'No goals to be solved' -- behaviourally CORRECT; fails only because the frozen consumer-supplied proof tail (rw dbColumns_drop_step) no longer matches a loopless impl. NOT a spec weakness; a genuinely-wrong echo would still be caught by the postcondition equality.

A-LEG / CORRESPONDENCE AUDIT: meta.json has axioms:[], deep_model_references:[], G-AX skip -> there are NO A-legs to attack. refinement.md legs all R/I (A1 type-refinement List Field <-> resolved Field list; A2 R+I, changed op modeled deeply as concrete dbColumns fold over Field.column; A3 I, one model covers update_fields+unique_fields). No kind-3. The single free-input boundary (get_field, name->Field) is UNCHANGED and only relocated by the patch (query.py hunks), correctly excluded; on_conflict_suffix_sql unchanged/downstream. Field.column is a plain R carried projection. G-CONF (meta: pass, 100009 inputs, 0 disagreements) differential-tests the shadow (column=db_column or name) against real Django Field.column (get_attname_column: db_column or attname; attname==name for valid idents) -> correspondence holds.

CONCLUSION: exact-equality postcondition over a transparent total function => verify implies behavioural equality to gold => resolves (G-RESOLVE pass). No verifying wrong impl, no A-leg unsoundness, no kind-3, correspondence sound. Verdict SOUND. >=5 distinct attacks (8) run and reported; none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The list of fields whose conflict-resolution tokens
--  are built is a FREE INPUT: how each field was obtained from the caller's
--  request is UNCHANGED and upstream of the modeled boundary, so the spec makes
--  no behavioural claim about it. Each field exposes two observable string
--  attributes (its model attribute name and its database column); both are plain
--  projections carried directly by the `Field` structure, so there is nothing to
--  validate against a real callee — hence no G-AX.)
-- axioms-end

-- pure-start
/- A persisted field, abstracted to its two observable string attributes: the
   model-side attribute name (`attr`) and the database column name (`column`).
   For a field declared with an explicit database column these differ (e.g. a
   mixed-case column under a lower-case attribute); otherwise the column equals
   the attribute. Only these two strings are observable to a consumer of the
   generated conflict-resolution clause, so this is the faithful carrier. -/
structure Field where
  attr   : List Char
  column : List Char
deriving DecidableEq, Inhabited

/- The database-column tokens of a sequence of fields: the database column of
   each field, taken in order. Written front-recursively so a single unfold is
   available per loop step (the backward fold pattern, plan §5.4). Empty
   sequence ⇒ empty result. -/
def dbColumns : List Field → List (List Char)
  | []      => []
  | f :: fs => [f.column] ++ dbColumns fs

@[grind] lemma dbColumns_nil : dbColumns [] = [] := rfl
@[grind] lemma dbColumns_cons (f : Field) (fs : List Field) :
    dbColumns (f :: fs) = [f.column] ++ dbColumns fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the list of tokens that identify each field in a generated
   conflict-resolution clause (the target of the conflict and the columns it
   updates). Each field must be referred to by its DATABASE COLUMN, taken in the
   given order — NOT by its model attribute name, which may differ from the
   column. The SAME operation produces both the conflict-target tokens and the
   updated-column tokens, so one model covers both argument positions
   (refinement.md §A).

   `fields` is read-only (directive 5): the operation reads each field's column
   and never mutates the input sequence. -/
method conflictColumns (fields : List Field) return (out : List (List Char))
  ensures out = dbColumns fields
  do
    -- impl-start
    let mut acc : List (List Char) := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant acc = dbColumns (fields.drop i)
      done_with i = 0
    do
      let f := fields[i - 1]!
      acc := [f.column] ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the field at
   `i-1` on the front, so `dbColumns` peels one column. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma dbColumns_drop_step (fields : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    dbColumns (fields.drop (i - 1)) = [fields[i - 1]!.column] ++ dbColumns (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, dbColumns_cons]

prove_correct conflictColumns by
  loom_solve
  rw [dbColumns_drop_step fields i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit (velvet, django__django-16315), project root. Spec pins `ensures out = dbColumns fields` where dbColumns(f::fs)=[f.column]++dbColumns fs -- an EXACT equality with a transparent total function. Any verifying impl is therefore behaviourally identical to dbColumns fields = the gold comprehension (f.column for f in fields). NO verifying-but-wrong impl exists, so there is no faithful patch to run through the harness; verify=>correct holds. Hence patches={} (nothing to resolve-run).

SAME-SPEC: all 8 attacks + prepatch + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec(velvet); impl region only edited, axioms/pure/pre/post byte-identical.

CMD each: bash scripts/lean_verify.sh <file> (run concurrently in batches of 4; interference-safe, read-only lean_shared).

### RESULTS (verify exit codes):
- pos_control.lean (gold column-emitting backward fold): exit 0 VERIFIES -> spec non-vacuous, admits correct impl.
- prepatch.lean: exit 1, unsolved goal (fields[i-1]?.getD default).attr = (...).column (literally f.attr=f.column) -> column-vs-name discriminator; prepatch bug reproduced for the right reason.
- atk_1 (emit f.attr = prepatch bug): exit 1, goal f.attr=f.column.
- atk_2 (return []): exit 1, goal [] = dbColumns fields.
- atk_3 (reversed order, forward prepend): exit 1, goal [fields[i]!.column]++acc = (dbColumns(take(i+1))).reverse.
- atk_4 (off-by-one, skip first field, while i>1): exit 1, goal i_1 = dbColumns fields.
- atk_5 (emit each column twice): exit 1, loop step reduces to False.
- atk_6 (emit [f.column,f.attr] per field): exit 1, loop step reduces to False.
- atk_7 (partial-domain: attr only on first field, if i=1 then f.attr): exit 1, goal i=1 -> f.attr=f.column.
- atk_8 (ungrounded-oracle echo: return dbColumns fields): exit 1, error 'No goals to be solved' -- behaviourally CORRECT; fails only because the frozen consumer-supplied proof tail (rw dbColumns_drop_step) no longer matches a loopless impl. NOT a spec weakness; a genuinely-wrong echo would still be caught by the postcondition equality.

A-LEG / CORRESPONDENCE AUDIT: meta.json has axioms:[], deep_model_references:[], G-AX skip -> there are NO A-legs to attack. refinement.md legs all R/I (A1 type-refinement List Field <-> resolved Field list; A2 R+I, changed op modeled deeply as concrete dbColumns fold over Field.column; A3 I, one model covers update_fields+unique_fields). No kind-3. The single free-input boundary (get_field, name->Field) is UNCHANGED and only relocated by the patch (query.py hunks), correctly excluded; on_conflict_suffix_sql unchanged/downstream. Field.column is a plain R carried projection. G-CONF (meta: pass, 100009 inputs, 0 disagreements) differential-tests the shadow (column=db_column or name) against real Django Field.column (get_attname_column: db_column or attname; attname==name for valid idents) -> correspondence holds.

CONCLUSION: exact-equality postcondition over a transparent total function => verify implies behavioural equality to gold => resolves (G-RESOLVE pass). No verifying wrong impl, no A-leg unsoundness, no kind-3, correspondence sound. Verdict SOUND. >=5 distinct attacks (8) run and reported; none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS = FAITHFUL. No input where the modeled function disagrees with the real callee.

Mechanical checks (this run):
- same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True. The two variants differ ONLY inside the elided impl-start/impl-end region (acc := [f.column]++acc vs acc := [f.attr]++acc). Spec view carries only `ensures out = dbColumns fields`, empty pre/post regions, no leaked repo symbols; spec_view SHA matches meta.json.
- Solution.lean verifies via scripts/lean_verify.sh: exit 0.
- Solution_prepatch.lean fails for the RIGHT reason: unsolved goal `(fields[i-1]?.getD default).attr = (fields[i-1]?.getD default).column` (literally f.attr = f.column, the column-vs-name discriminator). exit 1.

Boundary faithfulness (spec vs real repo at base_commit 7d5329852f):
- Gold patch (compiler.py:1725-1729, SQLInsertCompiler.as_sql) changes the ON CONFLICT / DO UPDATE SET args from name strings to `(f.column for f in self.query.update_fields)` / `(... unique_fields)`. Spec `out = dbColumns fields`, with dbColumns(f::fs)=[f.column]++dbColumns fs, is exactly `[f.column for f in fields]` — the changed op modeled deeply/concretely (R/I), applied once to cover both identical-shaped argument positions.
- `on_conflict_suffix_sql` (quoting/joining) UNCHANGED and downstream — correctly not modeled.
- `get_field` (name->Field) UNCHANGED; query.py hunks only relocate resolution up into bulk_create so Field objects (not strings) propagate. Upstream free input, cannot cause resolve/not-resolve divergence — correctly not axiomatized. meta.json axioms:[], deep_model_references:[].

Why no drift is possible: Field.column is carried as a FREE INPUT string in the Lean Field structure (attr, column), not derived from attr. Under mapping.md §2 bijection f ↦ {attr:=f.name.toList, column:=f.column.toList}, the spec output equals [f.column for f in fields] by construction for ANY real field. The projection is transparent; there is no algorithm to mis-model.

Independent real-repo verification (Django 4.2a1 installed to, matching base_commit dev line; not trusting bundled G-CONF alone):
- inspect.getsource confirms get_attname_column: `attname = self.get_attname(); column = self.db_column or attname`. This is exactly the shadow `db_column or name`.
- Direct differential test of real IntegerField(db_column=db).set_attributes_from_name(name).column vs shadow across edge cases: ('rank','rAnK')->rAnK, ('name',None)->name, ('','X')->X, ('a b','a b')->'a b', ('x','0')->'0', ('sectorid',None)->sectorid, ('foo','')->foo (empty db_column falls back to attname — matches Lean truthiness `if db_column else name` and Python `or`), ('__x__',None)->__x__, ('field','FIELD')->FIELD, ('n','')->n. ALL MATCH.

One subtlety checked: empty-string db_column. Python `self.db_column or attname` treats '' as falsy -> attname; the shadow `db_column if db_column else name` and Lean impl's use of the carried column both agree, and the bijection maps empty str to [] which the free-input Field would carry as column=[] only if the real column were '' — but the real column is never '' (it falls back to attname). Since column is a free input, the spec makes no claim tying it to attr, so it admits the true value on every constructible input. No diverging input exists.

Spec is neither too strong (empty preconditions; total exact equality matching a total deterministic real callee; a structurally distinct correct impl verifies per G-EQ) nor drifting. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified byte-identical to the recorded G-HYGIENE spec_view hash (a416527b39467cace72d3fa6369726e78e135506ffb9fbdd502b3858b8d0b87a); impl and prove_correct bodies correctly elide to placeholders. Assessed leakage against the PUBLIC problem_statement only (not hints_text). The problem_statement itself already fully discloses the discriminating content of the gold edit: it states 'The code which is generated for ON CONFLICT uses the field name and not the db_column' and gives the desired output 'ON CONFLICT("BlacklistID") DO UPDATE SET "SectorID"...', i.e. the fix is explicitly to emit each field's database column instead of its attribute name, in both the conflict-target and update-set positions. The spec view (dbColumns emitting f.column per field in order; docstring 'DATABASE COLUMN ... NOT by its model attribute name', covering both argument positions) is a faithful model of exactly that publicly-known behaviour and grants no reconstruction advantage beyond the public statement. The spec view contains NO gold-patch specifics absent from problem_statement: no file paths/line numbers, no on_conflict_suffix_sql, no get_field, no generator-comprehension syntax, no self.query.update_fields/unique_fields code, and no mention of the query.py relocation hunks (those live only in hints_text, which is out of scope). Internal cross-refs (refinement.md §A, plan §5.4) point to bundle docs, not gold code. G-LEAK lexical screen passed with empty failures. The postcondition necessarily encodes the fix's intent, but that is the benchmark's premise and does not exceed the public disclosure.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
