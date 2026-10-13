# P2 adversarial audit — django__django-14434

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,7 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: record opaque holder (plain=False) -- prepatch bug
+    part = ConstraintPart(False, db_table, columns)  # type: ConstraintPart
     return part
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,8 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: partial-domain -- plain only when columns nonempty
+    plain = len(columns) > 0  # type: bool
+    part = ConstraintPart(plain, db_table, columns)  # type: ConstraintPart
     return part
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,7 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: boundary -- record columns.drop(1) instead of columns
+    part = ConstraintPart(True, db_table, columns.drop(1))  # type: ConstraintPart
     return part
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,8 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: ungrounded -- record a fresh empty table list, breaking identity
+    other = []  # type: List[int]
+    part = ConstraintPart(True, other, columns)  # type: ConstraintPart
     return part
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,10 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: control-flow -- plain=False exactly when columns are nonempty
+    if len(columns) == 0:
+        part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    else:
+        part = ConstraintPart(False, db_table, columns)  # type: ConstraintPart
     return part
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,7 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: ungrounded -- record columns ++ columns (duplicated), wrong value
+    part = ConstraintPart(True, db_table, columns + columns)  # type: ConstraintPart
     return part
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ConstraintPart:
@@ -47,7 +46,6 @@
 
     def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
         Requires(Acc(list_pred(table), 1 / 2))
-        Requires(MustTerminate(1))
         Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
         Ensures(Acc(self.table) and self.table is table)            # type: ignore
         Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
@@ -95,7 +93,6 @@
 def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
     # pre-conditions-start
     Requires(Acc(list_pred(db_table), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
@@ -124,8 +121,8 @@
     Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
     # post-conditions-end
     # impl-start
-    # Record the table as the plain table name (value-comparable), and the
-    # constraint's column set, against which membership is tested.
-    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
+    # ATTACK: control-flow -- plain False when columns nonempty and cols[0]==0
+    plain = not (len(columns) > 0 and columns[0] == 0)  # type: bool
+    part = ConstraintPart(plain, db_table, columns)  # type: ConstraintPart
     return part
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14434.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deferred schema statement that constrains the columns of a table records,
  for its column-bearing part, the IDENTIFIER of the table those columns belong
  to together with the set of constrained columns. The query "does this part
  constrain column C of table T?" is answered by comparing the recorded table
  identifier against the queried table identifier BY VALUE and testing C for
  membership in the recorded column set.

  The desired guarantee: after building the column-bearing part of a unique
  constraint over a table named ``db_table`` with column set ``columns``,

    * for every ``c`` in ``columns``, the part constrains column ``c`` of table
      ``db_table`` (returns ``True``);
    * for any ``c`` NOT in ``columns``, or any other table name, the part does
      NOT constrain it (returns ``False``);
    * the companion table query for ``db_table`` returns ``True``.

  For the value comparison to succeed, the table recorded against the columns
  must be the same plain identifier the rest of the system names the table by.

A table identifier is modelled as ``List[int]`` of code points (Nagini bans
``str`` indexing); the constrained column set is modelled as a ``PSeq[int]`` of
column-identifier codes. The column-bearing part is a minimal class carrying
only the touched facets: the recorded table identifier, the constrained column
set, and a flag stating whether the recorded identifier is a plain name
(value-comparable to a queried name) or an opaque holder (which never
value-equals a plain name). One unchanged callee — membership of a column code
in the recorded set — is modelled deeply over the sequence (front-recursive),
validated out of band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class ConstraintPart:
    """The column-bearing part of a deferred statement, restricted to its
    observed facets. ``plain`` records whether ``table`` is a plain table name
    (value-comparable to a queried name) or an opaque holder (never value-equal
    to a plain name); ``table`` is the recorded table identifier; ``columns`` is
    the constrained column set as a sequence of column-identifier codes."""

    def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
        Requires(Acc(list_pred(table), 1 / 2))
        Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
        Ensures(Acc(self.table) and self.table is table)            # type: ignore
        Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
        Ensures(Acc(self.columns) and self.columns == columns)      # type: ignore
        self.plain = plain
        self.table = table
        self.columns = columns


# axioms-start
# (no @ContractOnly axioms: the only callee — membership of a column code in
# the recorded column set — is modelled deeply by the front-recursive @Pure
# `member` below and validated == real membership by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def member(c: int, cols: PSeq[int]) -> bool:
    """Whether the column code ``c`` occurs in the column set ``cols``.
    Front-recursive over ``PSeq`` so a single unfold is available to callers."""
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols.drop(1))


@Pure
def constrains_column(plain: bool, table: PSeq[int], cols: PSeq[int],
                      q_table: PSeq[int], q_col: int) -> bool:
    """The column query on a column-bearing part: the recorded table identifier
    must be a plain name AND value-equal the queried table identifier, and the
    queried column code must be a member of the recorded column set. An opaque
    holder (``plain == False``) never value-equals a plain queried name."""
    return plain and table == q_table and member(q_col, cols)


@Pure
def constrains_table(table: PSeq[int], q_table: PSeq[int]) -> bool:
    """The table query on a part holding a table identifier: the recorded
    identifier value-equals the queried one."""
    return table == q_table
# pure-end


def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
    # pre-conditions-start
    Requires(Acc(list_pred(db_table), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
    # The recorded table identifier IS the constraint's table name (the
    # db_table the caller passed); the read-only half-permission flows through.
    Ensures(Result().table is db_table)
    Ensures(Acc(list_pred(Result().table), 1 / 2))
    # The recorded column set is exactly the constraint's column set.
    Ensures(Result().columns == columns)
    # The discriminating guarantee: every column the constraint constrains is
    # reported for THIS table, by value.
    Ensures(Forall(int, lambda c: (
        Implies(member(c, columns),
                constrains_column(Result().plain, ToSeq(Result().table),
                                  Result().columns, ToSeq(db_table), c)),
        [[member(c, columns)]])))
    # A column NOT constrained, or a different table name, is NOT reported —
    # the query stays a faithful conjunction, not a constant True.
    Ensures(Forall(int, lambda c: (
        Implies(not member(c, columns),
                not constrains_column(Result().plain, ToSeq(Result().table),
                                      Result().columns, ToSeq(db_table), c)),
        [[member(c, columns)]])))
    # The companion table query holds for this table (the part identifies the
    # constraint's own table).
    Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
    # post-conditions-end
    # impl-start
    # Record the table as the plain table name (value-comparable), and the
    # constraint's column set, against which membership is tested.
    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
    return part
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec is extremely tight: the impl region can only vary the arguments to ConstraintPart(plain, table, columns). Postconditions pin (Result().table is db_table) [identity], (Result().columns == columns) [value], and the first Forall forces plain=True whenever columns is nonempty (there exists a member). plain is free ONLY when columns is empty (member always False), which the F2P test never exercises.

ENV: run with SBU_BENCHMARK_DIR=benchmark-verified, PY=python (the nagini env lacks swebench_unified), concurrent runs. Verifications run concurrently in batches of <=3 JVMs.

### ATTACKS (all same-spec CONFIRMED via `adversary same-spec` exit 0; impl region only):
- atk_1.py PREPATCH BUG echo, ConstraintPart(False,...): `adversary weakness` exit 2 (NOT-A-COUNTEREXAMPLE, does not verify). `adversary verify` => Postcondition first Forall(member(c,columns) => constrains_column(...)) might not hold. PREPATCH REPRODUCED.
- atk_2.py partial-domain, plain=len(columns)>0: `adversary weakness` exit 0 => CANDIDATE (shares spec AND verifies, 15.8s). MATERIALIZED faithful refined patch (atk_2.patch: records bare model._meta.db_table when columns truthy, i.e. exactly at the guarded `if columns:` construction site) and RAN run_resolve(timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', FAIL_TO_PASS test_unique_constraint SUCCESS, all PASS_TO_PASS success, 0 failures. => verify=>correct holds; NOT a counterexample. (The construction site is inside `if columns:`, so plain is always True there, byte-behaviourally identical to gold on every reachable state and on the tested inputs.)
- atk_3.py boundary, columns.drop(1): weakness exit 2; verify => Postcondition (Result().columns == columns) might not hold.
- atk_4.py ungrounded/identity, fresh other=[]: weakness exit 2; verify => Postcondition (Result().table is db_table) might not hold.
- atk_5.py control-flow-effect (plain=False on nonempty via if/else, re-assign part): weakness exit 2 (Nagini SSA type error 'Name part already defined' — genuine non-verify). Superseded by atk_7 for a clean spec-ground rejection.
- atk_6.py ungrounded, columns+columns: weakness exit 2; verify => Postcondition (Result().columns == columns) might not hold.
- atk_7.py clean single-assignment control-flow, plain=not(len(columns)>0 and columns[0]==0): same-spec exit 0; weakness exit 2 (does not verify) => first Forall fails on the cols[0]==0 branch. Confirms the control-flow category is rejected on true spec grounds.
Positive control pos_control.py (== model.py): VERIFIES (15.5s).

Summary: exactly ONE attack (atk_2) is a verifying candidate; its materialized faithful patch RESOLVES under the official harness (run_resolve executed, not speculated). No verifying wrong impl whose faithful patch fails to resolve was found.

REFINEMENT.MD LEG AUDIT: A1 (str<->List[int]) = R; A2 (col names -> int codes) = R; A3 (ConstraintPart(True,...) ~= Columns via _index_columns(bare name)) = R+I; A4 (constrains_column <-> TableColumns.references_column) = R+A-reference; A4' (member <-> Python `in`) = A-reference; A5 (constrains_table <-> Table.references_table) = R+A-reference. NO consumed @ContractOnly axiom, NO kind-3 (unexpressible-changed-op) step. The one genuinely changed op (bare-name vs Table-handle recorded value + its ==) is modeled deeply via the `plain` flag.
A-REFERENCE CORRESPONDENCE VALIDATED: axiom_check.py (G-AX) exits 0: member==Python `in`, constrains_column/constrains_table == real ddl_references on 1512 boundary reference queries + 20000 fuzz; pre-patch references_column always False, post-patch True for constrained columns. The decisive Table-has-no-__eq__ fact is exercised directly against the reproduced class. axiom_check imports only stdlib (random, sys) — no repo/network import. Correspondence to real callees holds.

VERDICT: SOUND — >=5 distinct wrong-impl attacks run (7 total: prepatch echo + partial-domain + boundary + control-flow x2 + ungrounded x2), the sole verifying candidate's faithful patch was materialized AND resolve-run and it RESOLVES, refinement legs are all R/A-reference/I with no kind-3, and G-AX validates the A-references. No evidence the spec admits an incorrect impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14434.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deferred schema statement that constrains the columns of a table records,
  for its column-bearing part, the IDENTIFIER of the table those columns belong
  to together with the set of constrained columns. The query "does this part
  constrain column C of table T?" is answered by comparing the recorded table
  identifier against the queried table identifier BY VALUE and testing C for
  membership in the recorded column set.

  The desired guarantee: after building the column-bearing part of a unique
  constraint over a table named ``db_table`` with column set ``columns``,

    * for every ``c`` in ``columns``, the part constrains column ``c`` of table
      ``db_table`` (returns ``True``);
    * for any ``c`` NOT in ``columns``, or any other table name, the part does
      NOT constrain it (returns ``False``);
    * the companion table query for ``db_table`` returns ``True``.

  For the value comparison to succeed, the table recorded against the columns
  must be the same plain identifier the rest of the system names the table by.

A table identifier is modelled as ``List[int]`` of code points (Nagini bans
``str`` indexing); the constrained column set is modelled as a ``PSeq[int]`` of
column-identifier codes. The column-bearing part is a minimal class carrying
only the touched facets: the recorded table identifier, the constrained column
set, and a flag stating whether the recorded identifier is a plain name
(value-comparable to a queried name) or an opaque holder (which never
value-equals a plain name). One unchanged callee — membership of a column code
in the recorded set — is modelled deeply over the sequence (front-recursive),
validated out of band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class ConstraintPart:
    """The column-bearing part of a deferred statement, restricted to its
    observed facets. ``plain`` records whether ``table`` is a plain table name
    (value-comparable to a queried name) or an opaque holder (never value-equal
    to a plain name); ``table`` is the recorded table identifier; ``columns`` is
    the constrained column set as a sequence of column-identifier codes."""

    def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
        Requires(Acc(list_pred(table), 1 / 2))
        Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
        Ensures(Acc(self.table) and self.table is table)            # type: ignore
        Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
        Ensures(Acc(self.columns) and self.columns == columns)      # type: ignore
        self.plain = plain
        self.table = table
        self.columns = columns


# axioms-start
# (no @ContractOnly axioms: the only callee — membership of a column code in
# the recorded column set — is modelled deeply by the front-recursive @Pure
# `member` below and validated == real membership by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def member(c: int, cols: PSeq[int]) -> bool:
    """Whether the column code ``c`` occurs in the column set ``cols``.
    Front-recursive over ``PSeq`` so a single unfold is available to callers."""
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols.drop(1))


@Pure
def constrains_column(plain: bool, table: PSeq[int], cols: PSeq[int],
                      q_table: PSeq[int], q_col: int) -> bool:
    """The column query on a column-bearing part: the recorded table identifier
    must be a plain name AND value-equal the queried table identifier, and the
    queried column code must be a member of the recorded column set. An opaque
    holder (``plain == False``) never value-equals a plain queried name."""
    return plain and table == q_table and member(q_col, cols)


@Pure
def constrains_table(table: PSeq[int], q_table: PSeq[int]) -> bool:
    """The table query on a part holding a table identifier: the recorded
    identifier value-equals the queried one."""
    return table == q_table
# pure-end


def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
    # pre-conditions-start
    Requires(Acc(list_pred(db_table), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
    # The recorded table identifier IS the constraint's table name (the
    # db_table the caller passed); the read-only half-permission flows through.
    Ensures(Result().table is db_table)
    Ensures(Acc(list_pred(Result().table), 1 / 2))
    # The recorded column set is exactly the constraint's column set.
    Ensures(Result().columns == columns)
    # The discriminating guarantee: every column the constraint constrains is
    # reported for THIS table, by value.
    Ensures(Forall(int, lambda c: (
        Implies(member(c, columns),
                constrains_column(Result().plain, ToSeq(Result().table),
                                  Result().columns, ToSeq(db_table), c)),
        [[member(c, columns)]])))
    # A column NOT constrained, or a different table name, is NOT reported —
    # the query stays a faithful conjunction, not a constant True.
    Ensures(Forall(int, lambda c: (
        Implies(not member(c, columns),
                not constrains_column(Result().plain, ToSeq(Result().table),
                                      Result().columns, ToSeq(db_table), c)),
        [[member(c, columns)]])))
    # The companion table query holds for this table (the part identifies the
    # constraint's own table).
    Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
    # post-conditions-end
    # impl-start
    # Record the table as the plain table name (value-comparable), and the
    # constraint's column set, against which membership is tested.
    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
    return part
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec is extremely tight: the impl region can only vary the arguments to ConstraintPart(plain, table, columns). Postconditions pin (Result().table is db_table) [identity], (Result().columns == columns) [value], and the first Forall forces plain=True whenever columns is nonempty (there exists a member). plain is free ONLY when columns is empty (member always False), which the F2P test never exercises.

ENV: run with SBU_BENCHMARK_DIR=benchmark-verified, PY=python (the nagini env lacks swebench_unified), concurrent runs. Verifications run concurrently in batches of <=3 JVMs.

### ATTACKS (all same-spec CONFIRMED via `adversary same-spec` exit 0; impl region only):
- atk_1.py PREPATCH BUG echo, ConstraintPart(False,...): `adversary weakness` exit 2 (NOT-A-COUNTEREXAMPLE, does not verify). `adversary verify` => Postcondition first Forall(member(c,columns) => constrains_column(...)) might not hold. PREPATCH REPRODUCED.
- atk_2.py partial-domain, plain=len(columns)>0: `adversary weakness` exit 0 => CANDIDATE (shares spec AND verifies, 15.8s). MATERIALIZED faithful refined patch (atk_2.patch: records bare model._meta.db_table when columns truthy, i.e. exactly at the guarded `if columns:` construction site) and RAN run_resolve(timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', FAIL_TO_PASS test_unique_constraint SUCCESS, all PASS_TO_PASS success, 0 failures. => verify=>correct holds; NOT a counterexample. (The construction site is inside `if columns:`, so plain is always True there, byte-behaviourally identical to gold on every reachable state and on the tested inputs.)
- atk_3.py boundary, columns.drop(1): weakness exit 2; verify => Postcondition (Result().columns == columns) might not hold.
- atk_4.py ungrounded/identity, fresh other=[]: weakness exit 2; verify => Postcondition (Result().table is db_table) might not hold.
- atk_5.py control-flow-effect (plain=False on nonempty via if/else, re-assign part): weakness exit 2 (Nagini SSA type error 'Name part already defined' — genuine non-verify). Superseded by atk_7 for a clean spec-ground rejection.
- atk_6.py ungrounded, columns+columns: weakness exit 2; verify => Postcondition (Result().columns == columns) might not hold.
- atk_7.py clean single-assignment control-flow, plain=not(len(columns)>0 and columns[0]==0): same-spec exit 0; weakness exit 2 (does not verify) => first Forall fails on the cols[0]==0 branch. Confirms the control-flow category is rejected on true spec grounds.
Positive control pos_control.py (== model.py): VERIFIES (15.5s).

Summary: exactly ONE attack (atk_2) is a verifying candidate; its materialized faithful patch RESOLVES under the official harness (run_resolve executed, not speculated). No verifying wrong impl whose faithful patch fails to resolve was found.

REFINEMENT.MD LEG AUDIT: A1 (str<->List[int]) = R; A2 (col names -> int codes) = R; A3 (ConstraintPart(True,...) ~= Columns via _index_columns(bare name)) = R+I; A4 (constrains_column <-> TableColumns.references_column) = R+A-reference; A4' (member <-> Python `in`) = A-reference; A5 (constrains_table <-> Table.references_table) = R+A-reference. NO consumed @ContractOnly axiom, NO kind-3 (unexpressible-changed-op) step. The one genuinely changed op (bare-name vs Table-handle recorded value + its ==) is modeled deeply via the `plain` flag.
A-REFERENCE CORRESPONDENCE VALIDATED: axiom_check.py (G-AX) exits 0: member==Python `in`, constrains_column/constrains_table == real ddl_references on 1512 boundary reference queries + 20000 fuzz; pre-patch references_column always False, post-patch True for constrained columns. The decisive Table-has-no-__eq__ fact is exercised directly against the reproduced class. axiom_check imports only stdlib (random, sys) — no repo/network import. Correspondence to real callees holds.

VERDICT: SOUND — >=5 distinct wrong-impl attacks run (7 total: prepatch echo + partial-domain + boundary + control-flow x2 + ungrounded x2), the sole verifying candidate's faithful patch was materialized AND resolve-run and it RESOLVES, refinement legs are all R/A-reference/I with no kind-3, and G-AX validates the A-references. No evidence the spec admits an incorrect impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) check for django__django-14434 nagini bundle.

Base commit confirmed 5e04e84d67da8163f365e9f5fcd169e2630e2873. Real callees read directly: TableColumns.references_column = 'self.table == table and column in self.columns' (ddl_references.py:63-64); Table.references_table = 'self.table == table' (49-50); Reference base returns False. Gold patch (from dataset) changes _create_unique_sql so the columns-bearing part records the BARE db_table string instead of a Table handle (which defines no __eq__) — fixing the references_column-always-false bug.

Model predicates faithfully reproduce this: constrains_column(plain,table,cols,q_table,q_col)=plain and table==q_table and member(q_col,cols); constrains_table(table,q_table)=table==q_table; member is front-recursive membership. plain=True models the bare (value-comparable) name (post-patch), plain=False models the opaque handle (pre-patch). model_prepatch uses plain=False and correctly fails the postcondition Forall(member(c,columns) => constrains_column(...)), mirroring the real bug (G-DIFF ok).

Independent faithfulness test: imported the REAL unchanged django.db.backends.ddl_references Table/TableColumns/Columns from the worktree and fuzzed 50,000 random (db_table, columns, q_table, q_col) triples comparing Columns.references_column and references_table against the model predicates for BOTH post-patch (bare) and pre-patch (Table handle) wirings — ZERO divergence. G-AX (axiom_check.py) passes: member==Python `in` and constrains_column/constrains_table==real ddl_references on 1512 boundary + 20000 fuzz. model.py verifies in Nagini (14.6s, exit 0).

Type refinement (str<->List[int]/PSeq[int] via ToSeq; column names -> injective int codes) preserves exactly the equality/membership the F2P test test_unique_constraint observes (sql.references_column(table,'name') is True). The spec is not too strong and does not drift from real repo behavior. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen against the frozen problem_statement, NOT hints_text) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path/module, no spec-view identifier embedding a patched repo symbol, no narration terms.

Semantic review: Public problem_statement already discloses the buggy site (_create_unique_sql), the symptom (references_column always false), AND the root cause + fix direction ('an instance of Table is passed as an argument to Columns when a string is expected'). Gold edit changes `table = Table(model._meta.db_table, self.quote_name)` -> `table = model._meta.db_table` (record the bare string, wrap in Table only for the Statement table= kwarg).

The spec view (model.py docstring + ConstraintPart.plain + constrains_column) restates this in ABSTRACTED carriers (List[int]/PSeq[int] code points, a `plain` bool = 'plain value-comparable name' vs 'opaque holder that never value-equals a plain name'). This is at equal-or-lower specificity than the already-public problem statement: the 'opaque holder never value-equals a plain name' distinction is exactly the public 'Table instance vs string expected' fact. Model symbols (build_constraint_columns, ConstraintPart, constrains_column, member, constrains_table) are abstract, none echo the patched repo symbols (schema.py callee create_unique_name/_index_columns/_create_unique_sql, ddl_references Table/Columns/TableColumns/Statement) beyond what the public statement names. No gold-diff line, path, or bug/fix narration appears in the spec view. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
