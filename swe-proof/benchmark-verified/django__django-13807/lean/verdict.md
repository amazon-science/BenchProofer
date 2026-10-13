# P2 adversarial audit — django__django-13807

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,13 +43,14 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
+  -- ATTACK 1 (prepatch bug): identifiers interpolated RAW, no quoting.
   let fkCheck :=
-    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
+    "PRAGMA foreign_key_check(".toList ++ table ++ [')']
   let fkList :=
-    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
+    "PRAGMA foreign_key_list(".toList ++ table ++ [')']
   let selectRow :=
-    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
-      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
+    "SELECT ".toList ++ primaryKey ++ ", ".toList
+      ++ column ++ " FROM ".toList ++ table
       ++ " WHERE rowid = %s".toList
   return (fkCheck, fkList, selectRow)
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,13 +43,16 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
+  -- ATTACK 2 (partial-domain / control-flow-effect): quote the table but
+  -- interpolate the pk / column raw. Correct only when pk and column are
+  -- already double-quoted; wrong on reserved words like `select`/`where`.
   let fkCheck :=
     "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
   let fkList :=
     "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
   let selectRow :=
-    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
-      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
+    "SELECT ".toList ++ primaryKey ++ ", ".toList
+      ++ column ++ " FROM ".toList ++ quoteIdentifier table
       ++ " WHERE rowid = %s".toList
   return (fkCheck, fkList, selectRow)
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,13 +43,17 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
+  -- ATTACK 3 (boundary): quote UNCONDITIONALLY (always wrap in double quotes),
+  -- dropping the idempotence branch. Diverges from spec on an already-quoted
+  -- identifier like `"order"` (spec leaves it; this double-wraps to `""order""`).
+  let q := fun (s : List Char) => ['"'] ++ s ++ ['"']
   let fkCheck :=
-    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
+    "PRAGMA foreign_key_check(".toList ++ q table ++ [')']
   let fkList :=
-    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
+    "PRAGMA foreign_key_list(".toList ++ q table ++ [')']
   let selectRow :=
-    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
-      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
+    "SELECT ".toList ++ q primaryKey ++ ", ".toList
+      ++ q column ++ " FROM ".toList ++ q table
       ++ " WHERE rowid = %s".toList
   return (fkCheck, fkList, selectRow)
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,13 +43,16 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
+  -- ATTACK 4 (control-flow-effect): SELECT the column before the primary key
+  -- (order swapped). Wrong whenever primaryKey ≠ column (the F2P case uses
+  -- distinct `select`/`where`).
   let fkCheck :=
     "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
   let fkList :=
     "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
   let selectRow :=
-    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
-      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
+    "SELECT ".toList ++ quoteIdentifier column ++ ", ".toList
+      ++ quoteIdentifier primaryKey ++ " FROM ".toList ++ quoteIdentifier table
       ++ " WHERE rowid = %s".toList
   return (fkCheck, fkList, selectRow)
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,10 +43,13 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
+  -- ATTACK 5 (boundary literal): the fkList query uses the WRONG pragma name
+  -- (`foreign_key_check` instead of `foreign_key_list`). Always wrong on
+  -- component .2.1.
   let fkCheck :=
     "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
   let fkList :=
-    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
+    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
   let selectRow :=
     "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
       ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,15 +43,10 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
-  let fkCheck :=
-    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
-  let fkList :=
-    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
-  let selectRow :=
-    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
-      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
-      ++ " WHERE rowid = %s".toList
-  return (fkCheck, fkList, selectRow)
+  -- ATTACK 6 (ungrounded-oracle echo): return a constant triple, ignoring the
+  -- inputs entirely. Only correct for the specific empty-ish inputs; wrong in
+  -- general. If this closes, the spec is vacuous.
+  return ("".toList, "".toList, "".toList)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,12 +43,15 @@
 def implementation_fkCheckQueries
     (table primaryKey column : List Char) :
     List Char × List Char × List Char := Id.run do
+  -- ATTACK 7 (boundary separator): the SELECT joins the two columns with a
+  -- bare "," instead of ", " (missing the trailing space). Always wrong on
+  -- component .2.2.
   let fkCheck :=
     "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
   let fkList :=
     "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
   let selectRow :=
-    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
+    "SELECT ".toList ++ quoteIdentifier primaryKey ++ [',']
       ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
       ++ " WHERE rowid = %s".toList
   return (fkCheck, fkList, selectRow)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the identifier-quoting helper
-- is a tiny, total string operation, so it is modeled DEEPLY (`quoteIdentifier`,
-- below) and validated against the real callee by G-AX (A-reference) rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Render a SQL identifier so that a reserved word is treated as a name rather
than as syntax: the identifier is wrapped in double quotes. If it is already
double-quoted (it both begins and ends with a double-quote character) it is left
unchanged, so quoting is idempotent. -/
def quoteIdentifier (name : List Char) : List Char :=
  if name.head? = some '"' ∧ name.getLast? = some '"' then
    name
  else
    ['"'] ++ name ++ ['"']
-- pure-end

-- post-conditions-start
/-- The three constraint-check query strings built for a single table from its
table name and the relevant primary-key / foreign-key column names. Every
identifier that is substituted into a query is rendered with `quoteIdentifier`;
all surrounding literal SQL text (PRAGMA names, parentheses, separators, the
`SELECT … FROM … WHERE rowid = %s` skeleton) is pinned exactly. -/
def problem_spec_fkCheckQueries
    (table primaryKey column : List Char)
    (result : List Char × List Char × List Char) : Prop :=
  result.1 =
      "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')'] ∧
  result.2.1 =
      "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')'] ∧
  result.2.2 =
      "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
        ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
        ++ " WHERE rowid = %s".toList
-- post-conditions-end

-- impl-start
def implementation_fkCheckQueries
    (table primaryKey column : List Char) :
    List Char × List Char × List Char := Id.run do
  let fkCheck :=
    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
  let fkList :=
    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
  let selectRow :=
    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
      ++ " WHERE rowid = %s".toList
  return (fkCheck, fkList, selectRow)
-- impl-end

-- proof-start
theorem correct_fkCheckQueries :
    ∀ (table primaryKey column : List Char),
    problem_spec_fkCheckQueries table primaryKey column
      (implementation_fkCheckQueries table primaryKey column) := by
  intro table primaryKey column
  refine ⟨?_, ?_, ?_⟩ <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** problem_spec_fkCheckQueries is a TOTAL exact-equality postcondition (no precondition): for ALL (table, primaryKey, column) the output triple must equal the three pinned strings built with the frozen deep model quoteIdentifier. quoteIdentifier is defined in the spec-visible pure region (collapses only impl+proof in the Lean spec view), so any verifying same-spec impl is forced extensionally equal to gold over the entire domain — there is no slack to exploit.

PATH prepends.elan/bin; python.

same_spec (all True) — cmd: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); same_spec(gold, atk, b.language)". atk_1..7 => all True.

VERIFY — cmd: bash scripts/lean_verify.sh <atk>.lean. Results:
- atk_1 (PREPATCH BUG: identifiers interpolated RAW, no quoting): EXIT=1 (fails to close). Reproduces the actual pre-patch defect (PRAGMA foreign_key_check(order) syntax error).
- atk_2 (partial-domain / control-flow-effect: quote table but raw pk/column): EXIT=1.
- atk_3 (boundary: unconditional wrap, drops idempotence branch; diverges on already-quoted like "order"): EXIT=1.
- atk_4 (control-flow-effect: SELECT column,pk order swapped): EXIT=1.
- atk_5 (boundary literal: fkList uses wrong pragma foreign_key_check instead of foreign_key_list): EXIT=1 (goal shows .2.1 mismatch).
- atk_6 (ungrounded-oracle echo: returns constant empty triple ignoring inputs): EXIT=1.
- atk_7 (boundary separator: joins columns with bare ',' instead of ', '): EXIT=1.
ALL 7 same-spec wrong impls FAIL to close. None produced a closing clean-axiom proof, so the mandatory materialize+resolve step is VACUOUS (no verifying-but-nonresolving candidate exists) — patches={}.

**POSITIVE CONTROL:** pos_control.lean (byte copy of gold Solution.lean) verifies EXIT=0. #print axioms correct_fkCheckQueries => 'does not depend on any axioms' (clean; proof is refine + rfl).

A-LEG / refinement.md AUDIT: legs are all R (row1: str<->List Char), A-reference (row2: quote_name <-> quoteIdentifier, validated by G-AX), or I (rows 3-6: %s-into-literal = fixed-order concat). NO A-consumed, NO changed-inexpressible/kind-3; axioms region empty. Ran axiom_check.py (G-AX): checked=60016 inputs (incl. '', '"', '""', reserved words order/select/where, already-quoted names) — quoteIdentifier == real DatabaseOperations.quote_name on every input; status=pass, exit 0. The deep model faithfully matches the real unchanged callee (operations.py:170-173).

**CONCLUSION:** The total exact-equality spec with a faithful frozen deep model admits no same-spec impl that verifies yet deviates from gold behavior. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the identifier-quoting helper
-- is a tiny, total string operation, so it is modeled DEEPLY (`quoteIdentifier`,
-- below) and validated against the real callee by G-AX (A-reference) rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Render a SQL identifier so that a reserved word is treated as a name rather
than as syntax: the identifier is wrapped in double quotes. If it is already
double-quoted (it both begins and ends with a double-quote character) it is left
unchanged, so quoting is idempotent. -/
def quoteIdentifier (name : List Char) : List Char :=
  if name.head? = some '"' ∧ name.getLast? = some '"' then
    name
  else
    ['"'] ++ name ++ ['"']
-- pure-end

-- post-conditions-start
/-- The three constraint-check query strings built for a single table from its
table name and the relevant primary-key / foreign-key column names. Every
identifier that is substituted into a query is rendered with `quoteIdentifier`;
all surrounding literal SQL text (PRAGMA names, parentheses, separators, the
`SELECT … FROM … WHERE rowid = %s` skeleton) is pinned exactly. -/
def problem_spec_fkCheckQueries
    (table primaryKey column : List Char)
    (result : List Char × List Char × List Char) : Prop :=
  result.1 =
      "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')'] ∧
  result.2.1 =
      "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')'] ∧
  result.2.2 =
      "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
        ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
        ++ " WHERE rowid = %s".toList
-- post-conditions-end

-- impl-start
def implementation_fkCheckQueries
    (table primaryKey column : List Char) :
    List Char × List Char × List Char := Id.run do
  let fkCheck :=
    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')']
  let fkList :=
    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')']
  let selectRow :=
    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
      ++ " WHERE rowid = %s".toList
  return (fkCheck, fkList, selectRow)
-- impl-end

-- proof-start
theorem correct_fkCheckQueries :
    ∀ (table primaryKey column : List Char),
    problem_spec_fkCheckQueries table primaryKey column
      (implementation_fkCheckQueries table primaryKey column) := by
  intro table primaryKey column
  refine ⟨?_, ?_, ?_⟩ <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** problem_spec_fkCheckQueries is a TOTAL exact-equality postcondition (no precondition): for ALL (table, primaryKey, column) the output triple must equal the three pinned strings built with the frozen deep model quoteIdentifier. quoteIdentifier is defined in the spec-visible pure region (collapses only impl+proof in the Lean spec view), so any verifying same-spec impl is forced extensionally equal to gold over the entire domain — there is no slack to exploit.

PATH prepends.elan/bin; python.

same_spec (all True) — cmd: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); same_spec(gold, atk, b.language)". atk_1..7 => all True.

VERIFY — cmd: bash scripts/lean_verify.sh <atk>.lean. Results:
- atk_1 (PREPATCH BUG: identifiers interpolated RAW, no quoting): EXIT=1 (fails to close). Reproduces the actual pre-patch defect (PRAGMA foreign_key_check(order) syntax error).
- atk_2 (partial-domain / control-flow-effect: quote table but raw pk/column): EXIT=1.
- atk_3 (boundary: unconditional wrap, drops idempotence branch; diverges on already-quoted like "order"): EXIT=1.
- atk_4 (control-flow-effect: SELECT column,pk order swapped): EXIT=1.
- atk_5 (boundary literal: fkList uses wrong pragma foreign_key_check instead of foreign_key_list): EXIT=1 (goal shows .2.1 mismatch).
- atk_6 (ungrounded-oracle echo: returns constant empty triple ignoring inputs): EXIT=1.
- atk_7 (boundary separator: joins columns with bare ',' instead of ', '): EXIT=1.
ALL 7 same-spec wrong impls FAIL to close. None produced a closing clean-axiom proof, so the mandatory materialize+resolve step is VACUOUS (no verifying-but-nonresolving candidate exists) — patches={}.

**POSITIVE CONTROL:** pos_control.lean (byte copy of gold Solution.lean) verifies EXIT=0. #print axioms correct_fkCheckQueries => 'does not depend on any axioms' (clean; proof is refine + rfl).

A-LEG / refinement.md AUDIT: legs are all R (row1: str<->List Char), A-reference (row2: quote_name <-> quoteIdentifier, validated by G-AX), or I (rows 3-6: %s-into-literal = fixed-order concat). NO A-consumed, NO changed-inexpressible/kind-3; axioms region empty. Ran axiom_check.py (G-AX): checked=60016 inputs (incl. '', '"', '""', reserved words order/select/where, already-quoted names) — quoteIdentifier == real DatabaseOperations.quote_name on every input; status=pass, exit 0. The deep model faithfully matches the real unchanged callee (operations.py:170-173).

**CONCLUSION:** The total exact-equality spec with a faithful frozen deep model admits no same-spec impl that verifies yet deviates from gold behavior. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence; the spec is faithful to the real repo behavior at base_commit 89fc144.

Checks performed:
1. Compile/soundness: scripts/lean_verify.sh Solution.lean -> exit 0. Appended `#print axioms correct_fkCheckQueries` -> 'does not depend on any axioms' (no sorryAx; proof is real, discharged by rfl over the three concatenations).
2. Spec-region byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean-backend) = True. The frozen spec view (axioms/pure/post-conditions) is identical; only impl+proof differ (prepatch interpolates raw identifiers -> unclosable = legitimate G-DIFF signal).
3. Deep-model (A-reference) validation: bundle axiom_check.py (G-AX) passes, quoteIdentifier == real quote_name over 60016 inputs. Confirmed real callee is DatabaseOperations.quote_name (django/db/backends/sqlite3/operations.py:170-173, UNCHANGED by the gold patch).
4. My own adversarial faithfulness fuzz: compared the FULL modeled builder (three ++-concatenations over quoteIdentifier) against the real post-patch Python string construction ('PRAGMA foreign_key_check(%s)' % self.ops.quote_name(table), etc.) using the in-tree django at base_commit. 300k randomized inputs plus targeted adversarial cases where % / ++ could diverge: '%s','%%','%(x)s','%','"%s"', embedded double-quotes, empty, whitespace, unicode. ZERO divergences. Python's `%` inserts substituted values without re-scanning them for further conversions, so it is exactly fixed-order concatenation here; the model is byte-exact.

Modeling-boundary assessment (would spec be 'too strong'/drift?): No. The spec models exactly the per-row/per-table query-string construction that the fix touches. quote_name is total and pure so deep modeling is appropriate. The surrounding cursor IO / chain.from_iterable / IntegrityError message is unchanged by the patch and correctly out of scope. The discriminating F2P behavior (double-quoting reserved-word identifiers such as table 'order', columns 'select'/'where') is faithfully captured. No input exists where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures); spec region byte-identical between Solution.lean and Solution_prepatch.lean via same_spec (True). Spec view pins the correct post-condition (identifiers rendered with quoteIdentifier = double-quoted, idempotent) into the three PRAGMA/SELECT templates. This is the spec's legitimate job and does NOT leak the edit beyond the public problem_statement: the statement already publicly states the table name 'order' is not quoted properly, cites the missing quoting around %s in PRAGMA foreign_key_check(%s), and shows the near "order" syntax error. The gold's edit vehicle (self.ops.quote_name call, check_constraints symbol, base.py/operations.py paths, diff markers) is entirely absent from the spec view; quoteIdentifier is a modeling abstraction, not the repo symbol. SQL literals in the spec (foreign_key_check, foreign_key_list, %s) appear verbatim in the problem_statement. No bug/fix narration in comments. patch_equals_gold=True, relaxed_leakage not set.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
