# P2 adversarial audit — django__django-12741

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -114,18 +112,15 @@
     Ensures(ToSeq(self.connection.executed) == ToSeq(sql_list))
     # post-conditions-end
     # impl-start
-    self.connection.scoped_alias = self.connection.alias
+    self.connection.scoped_alias = self.connection.caller_alias
     self.connection.scoped_savepoint = self.connection.supports_rollback
     executed = []  # type: List[int]
     i = 0
     while i < len(sql_list):
-        # invariants-start
         Invariant(Acc(list_pred(sql_list), 1 / 2))
         Invariant(Acc(list_pred(executed)))
         Invariant(0 <= i and i <= len(sql_list))
         Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
         executed.append(sql_list[i])
         i = i + 1
     self.connection.executed = executed
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -115,17 +113,14 @@
     # post-conditions-end
     # impl-start
     self.connection.scoped_alias = self.connection.alias
-    self.connection.scoped_savepoint = self.connection.supports_rollback
+    self.connection.scoped_savepoint = True
     executed = []  # type: List[int]
     i = 0
     while i < len(sql_list):
-        # invariants-start
         Invariant(Acc(list_pred(sql_list), 1 / 2))
         Invariant(Acc(list_pred(executed)))
         Invariant(0 <= i and i <= len(sql_list))
         Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
         executed.append(sql_list[i])
         i = i + 1
     self.connection.executed = executed
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -118,14 +116,11 @@
     self.connection.scoped_savepoint = self.connection.supports_rollback
     executed = []  # type: List[int]
     i = 0
-    while i < len(sql_list):
-        # invariants-start
+    while i < len(sql_list) - 1:
         Invariant(Acc(list_pred(sql_list), 1 / 2))
         Invariant(Acc(list_pred(executed)))
         Invariant(0 <= i and i <= len(sql_list))
         Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
         executed.append(sql_list[i])
         i = i + 1
     self.connection.executed = executed
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -119,13 +117,10 @@
     executed = []  # type: List[int]
     i = 0
     while i < len(sql_list):
-        # invariants-start
         Invariant(Acc(list_pred(sql_list), 1 / 2))
         Invariant(Acc(list_pred(executed)))
         Invariant(0 <= i and i <= len(sql_list))
-        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
+        executed.append(sql_list[i])
         executed.append(sql_list[i])
         i = i + 1
     self.connection.executed = executed
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -117,16 +115,5 @@
     self.connection.scoped_alias = self.connection.alias
     self.connection.scoped_savepoint = self.connection.supports_rollback
     executed = []  # type: List[int]
-    i = 0
-    while i < len(sql_list):
-        # invariants-start
-        Invariant(Acc(list_pred(sql_list), 1 / 2))
-        Invariant(Acc(list_pred(executed)))
-        Invariant(0 <= i and i <= len(sql_list))
-        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
-        executed.append(sql_list[i])
-        i = i + 1
     self.connection.executed = executed
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -116,17 +114,5 @@
     # impl-start
     self.connection.scoped_alias = self.connection.alias
     self.connection.scoped_savepoint = self.connection.supports_rollback
-    executed = []  # type: List[int]
-    i = 0
-    while i < len(sql_list):
-        # invariants-start
-        Invariant(Acc(list_pred(sql_list), 1 / 2))
-        Invariant(Acc(list_pred(executed)))
-        Invariant(0 <= i and i <= len(sql_list))
-        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
-        executed.append(sql_list[i])
-        i = i + 1
-    self.connection.executed = executed
+    self.connection.executed = sql_list
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -114,18 +112,16 @@
     Ensures(ToSeq(self.connection.executed) == ToSeq(sql_list))
     # post-conditions-end
     # impl-start
+    self.connection.alias = 0
     self.connection.scoped_alias = self.connection.alias
     self.connection.scoped_savepoint = self.connection.supports_rollback
     executed = []  # type: List[int]
     i = 0
     while i < len(sql_list):
-        # invariants-start
         Invariant(Acc(list_pred(sql_list), 1 / 2))
         Invariant(Acc(list_pred(executed)))
         Invariant(0 <= i and i <= len(sql_list))
         Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
         executed.append(sql_list[i])
         i = i + 1
     self.connection.executed = executed
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Connection:
@@ -88,7 +87,6 @@
     Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
     Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
     Requires(Acc(list_pred(sql_list), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.connection))
@@ -117,16 +115,12 @@
     self.connection.scoped_alias = self.connection.alias
     self.connection.scoped_savepoint = self.connection.supports_rollback
     executed = []  # type: List[int]
-    i = 0
-    while i < len(sql_list):
-        # invariants-start
+    i = len(sql_list) - 1
+    while i >= 0:
         Invariant(Acc(list_pred(sql_list), 1 / 2))
         Invariant(Acc(list_pred(executed)))
-        Invariant(0 <= i and i <= len(sql_list))
-        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
-        Invariant(MustTerminate(len(sql_list) - i + 1))
-        # invariants-end
+        Invariant(-1 <= i and i < len(sql_list))
         executed.append(sql_list[i])
-        i = i + 1
+        i = i - 1
     self.connection.executed = executed
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database-operations helper exposes a routine that runs a prepared batch of
  flush statements against the database. The database the batch runs against is
  the helper's OWN connection — its identity is taken from the connection the
  helper is bound to, not supplied separately by the caller. Concretely, once
  the routine returns:

    (1) the atomic block it opened was scoped to the helper's own connection:
        the database identifier the block ran under equals the connection's
        own identifier;

    (2) the block's rollback-savepoint behaviour matched the connection's
        declared capability;

    (3) every statement in the supplied batch was executed, in the order given,
        and exactly those statements (no statement dropped, reordered, or
        invented).

The connection is modelled as a minimal class carrying only the touched
facets: its own database identifier, its rollback-savepoint capability flag,
and two observation recorders standing for the effect of the unchanged
callees — the database identifier the opened atomic block ran under, the
savepoint flag it was opened with, and the ordered list of statements that were
executed. The helper is a minimal class holding only that connection.

The two unchanged callees the routine invokes — opening an atomic block scoped
to a database, and executing one statement against the database — are not
themselves changed by the behaviour under specification; their observable
effects (which database the block was scoped to, which statements ran, in what
order) are recorded so the contract can pin them. SQL statements are modelled
as integer identifiers (opaque tokens); the specification is carried by
``PSeq[int]`` via ``ToSeq``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Connection:
    def __init__(self, alias: int, supports_rollback: bool, caller_alias: int) -> None:
        Ensures(Acc(self.alias) and self.alias == alias)                       # type: ignore
        Ensures(Acc(self.supports_rollback) and self.supports_rollback == supports_rollback)  # type: ignore
        Ensures(Acc(self.caller_alias) and self.caller_alias == caller_alias)  # type: ignore
        Ensures(Acc(self.scoped_alias))                                        # type: ignore
        Ensures(Acc(self.scoped_savepoint))                                    # type: ignore
        Ensures(Acc(self.executed) and Acc(list_pred(self.executed)))          # type: ignore
        Ensures(len(self.executed) == 0)                                       # type: ignore
        self.alias = alias                       # the connection's own database identifier
        self.supports_rollback = supports_rollback # declared rollback-savepoint capability
        self.caller_alias = caller_alias         # a database identifier supplied externally (caller-threaded)
        self.scoped_alias = 0                    # recorder: database the atomic block ran under
        self.scoped_savepoint = False            # recorder: savepoint flag the block opened with
        self.executed = []  # type: List[int]    # recorder: statements executed, in order


class DatabaseOperations:
    def __init__(self, connection: Connection) -> None:
        Requires(Acc(connection.alias) and Acc(connection.supports_rollback))
        Requires(Acc(connection.caller_alias))
        Requires(Acc(connection.scoped_alias) and Acc(connection.scoped_savepoint))
        Requires(Acc(connection.executed) and Acc(list_pred(connection.executed)))
        Ensures(Acc(self.connection) and self.connection is connection)        # type: ignore
        self.connection = connection


# axioms-start
# (no @ContractOnly callee axioms are required: the unchanged callees the
# routine invokes are modelled by their observable effects on the recorders,
# validated against the real callees out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def execute_statement_batch(self: DatabaseOperations, sql_list: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(self.connection))
    Requires(Acc(self.connection.alias, 1 / 2) and Acc(self.connection.supports_rollback, 1 / 2))
    Requires(Acc(self.connection.caller_alias, 1 / 2))
    Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
    Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
    Requires(Acc(list_pred(sql_list), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.connection))
    # frame: the routine runs the batch against the helper's OWN connection — the
    # helper's connection identity is unchanged (it is not rebound to a different
    # object). Without this, a fake connection satisfying the recorders below
    # would vacuously discharge the contract.
    Ensures(self.connection is Old(self.connection))
    Ensures(Acc(self.connection.alias, 1 / 2) and Acc(self.connection.supports_rollback, 1 / 2))
    Ensures(Acc(self.connection.caller_alias, 1 / 2))
    Ensures(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
    Ensures(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
    Ensures(Acc(list_pred(sql_list), 1 / 2))
    # (1) the atomic block was scoped to the helper's OWN connection: the
    # database it ran under is the connection's own identifier — derived
    # internally, never supplied by the caller.
    Ensures(self.connection.scoped_alias == self.connection.alias)
    # (2) the block's savepoint behaviour matched the connection's declared
    # rollback capability.
    Ensures(self.connection.scoped_savepoint == self.connection.supports_rollback)
    # (3) exactly the supplied batch ran, in order: the recorded execution list
    # equals the input batch element-wise.
    Ensures(ToSeq(self.connection.executed) == ToSeq(sql_list))
    # post-conditions-end
    # impl-start
    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT FOCUS: A-legs (axioms/deep-model references) + model<->patch correspondence; R/I legs deferred to G-CONF.

SPEC SHAPE (tight): preconditions grant only 1/2 (READ-ONLY) permission on self.connection.alias, supports_rollback, caller_alias, and list_pred(sql_list); FULL permission only on recorders scoped_alias/scoped_savepoint/executed. Postconditions pin all three recorders exactly to gold: (1) scoped_alias == self.connection.alias (own alias, derived internally), (2) scoped_savepoint == supports_rollback, (3) ToSeq(executed) == ToSeq(sql_list) (exact elements + order). Frame Ensures(self.connection is Old(self.connection)) blocks fake-connection substitution.

TOOLING: python=python; SBU_BENCHMARK_DIR=benchmark-verified;

POSITIVE CONTROL: cp of model.py. `bash scripts/nagini_verify.sh .../positive_control.py` => Verification successful (22.4s), exit 0. same-spec => SAME.

ATTACKS (all copy model.py, edit ONLY impl region; axioms/@Pure/Requires/Ensures/Invariant byte-identical). All 8 confirmed same-spec (exit 0). Command each: `python -m swebench_unified.adversary weakness nagini django__django-12741 <atk>`. ALL 8 returned exit 2 = NOT-A-COUNTEREXAMPLE (does not verify) => spec rejected. Detail per attack:
- atk_1 PREPATCH BUG: scoped_alias = caller_alias (externally threaded). Rejected => clause (1) scoped_alias==alias fails. PREPATCH REPRODUCED.
- atk_2 ungrounded-oracle: scoped_savepoint = True constant. Rejected (clause 2).
- atk_3 boundary off-by-one: loop `i < len(sql_list)-1` drops last stmt. Rejected (clause 3, invariant).
- atk_4 control-flow-effect: appends each stmt twice. Rejected (clause 3).
- atk_5 partial-domain no-op: leaves executed empty. Rejected (clause 3).
- atk_6 aliasing echo: executed = sql_list directly. Direct verify => `error: Postcondition ... insufficient permission to access list_pred(self.connection.executed)` (only 1/2 perm on sql_list; cannot alias-transfer).
- atk_7 read-only-defense probe: overwrite self.connection.alias=0 then scope. Direct verify => `error: Assignment might fail ... insufficient permission to access self.connection.alias` (impl holds only 1/2 read-only perm; cannot game clause 1 by rewriting own identity).
- atk_8 reorder: append in REVERSE order. Rejected (clause 3 order).

No attack came back CANDIDATE (none verified while sharing spec), so there is NO verifying wrong impl and therefore NO faithful refined patch to materialize/run_resolve; patches={} accordingly. The verify=>correct falsification path never opened.

G-AX (A-reference correspondence) EXECUTED against the real callee: ` /usr/bin/python3.12 axiom_check.py` => `G-AX OK ... sound over 5072 observations` exit 0. Real post-patch BaseDatabaseOperations.execute_sql_flush confirmed: signature is (self, sql_list) with NO `using` param; block scoped to self.connection.alias; savepoint == features.can_rollback_ddl; exactly sql_list executed in order. (swebench-lean py3.11 SKIPs G-AX due to django import incompat; py3.12 run against checkout HEAD 4bbc27c868 which carries the post-patch signature is the real check.)

REFINEMENT.MD LEG AUDIT: A1=R (helper/connection<->touched fields); A2=I-under-R (drop `using`; real sig verified by grep + G-AX assertion); A3=A-reference (scoped_alias==alias <-> atomic(using=self.connection.alias), G-AX validated); A4=A-reference+I (savepoint <-> can_rollback_ddl, G-AX validated); A5=A-reference+I (loop <-> cursor.execute in order, G-AX validated). Every leg is R / A-reference / I. axioms region is EMPTY (no @ContractOnly): NO A-consumed leg, NO dead axiom, NO kind-3 step. §C claim holds; A-legs' correspondence to real callees confirmed sound.

VERDICT: SOUND. 8 distinct same-spec wrong impls (prepatch, ungrounded-oracle x2, boundary, control-flow-effect, partial-domain, aliasing-echo, reorder) all fail to verify; positive control verifies; prepatch reproduced; G-AX A-references validated against the real Django callee over 5072 observations.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database-operations helper exposes a routine that runs a prepared batch of
  flush statements against the database. The database the batch runs against is
  the helper's OWN connection — its identity is taken from the connection the
  helper is bound to, not supplied separately by the caller. Concretely, once
  the routine returns:

    (1) the atomic block it opened was scoped to the helper's own connection:
        the database identifier the block ran under equals the connection's
        own identifier;

    (2) the block's rollback-savepoint behaviour matched the connection's
        declared capability;

    (3) every statement in the supplied batch was executed, in the order given,
        and exactly those statements (no statement dropped, reordered, or
        invented).

The connection is modelled as a minimal class carrying only the touched
facets: its own database identifier, its rollback-savepoint capability flag,
and two observation recorders standing for the effect of the unchanged
callees — the database identifier the opened atomic block ran under, the
savepoint flag it was opened with, and the ordered list of statements that were
executed. The helper is a minimal class holding only that connection.

The two unchanged callees the routine invokes — opening an atomic block scoped
to a database, and executing one statement against the database — are not
themselves changed by the behaviour under specification; their observable
effects (which database the block was scoped to, which statements ran, in what
order) are recorded so the contract can pin them. SQL statements are modelled
as integer identifiers (opaque tokens); the specification is carried by
``PSeq[int]`` via ``ToSeq``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Connection:
    def __init__(self, alias: int, supports_rollback: bool, caller_alias: int) -> None:
        Ensures(Acc(self.alias) and self.alias == alias)                       # type: ignore
        Ensures(Acc(self.supports_rollback) and self.supports_rollback == supports_rollback)  # type: ignore
        Ensures(Acc(self.caller_alias) and self.caller_alias == caller_alias)  # type: ignore
        Ensures(Acc(self.scoped_alias))                                        # type: ignore
        Ensures(Acc(self.scoped_savepoint))                                    # type: ignore
        Ensures(Acc(self.executed) and Acc(list_pred(self.executed)))          # type: ignore
        Ensures(len(self.executed) == 0)                                       # type: ignore
        self.alias = alias                       # the connection's own database identifier
        self.supports_rollback = supports_rollback # declared rollback-savepoint capability
        self.caller_alias = caller_alias         # a database identifier supplied externally (caller-threaded)
        self.scoped_alias = 0                    # recorder: database the atomic block ran under
        self.scoped_savepoint = False            # recorder: savepoint flag the block opened with
        self.executed = []  # type: List[int]    # recorder: statements executed, in order


class DatabaseOperations:
    def __init__(self, connection: Connection) -> None:
        Requires(Acc(connection.alias) and Acc(connection.supports_rollback))
        Requires(Acc(connection.caller_alias))
        Requires(Acc(connection.scoped_alias) and Acc(connection.scoped_savepoint))
        Requires(Acc(connection.executed) and Acc(list_pred(connection.executed)))
        Ensures(Acc(self.connection) and self.connection is connection)        # type: ignore
        self.connection = connection


# axioms-start
# (no @ContractOnly callee axioms are required: the unchanged callees the
# routine invokes are modelled by their observable effects on the recorders,
# validated against the real callees out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def execute_statement_batch(self: DatabaseOperations, sql_list: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(self.connection))
    Requires(Acc(self.connection.alias, 1 / 2) and Acc(self.connection.supports_rollback, 1 / 2))
    Requires(Acc(self.connection.caller_alias, 1 / 2))
    Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
    Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
    Requires(Acc(list_pred(sql_list), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.connection))
    # frame: the routine runs the batch against the helper's OWN connection — the
    # helper's connection identity is unchanged (it is not rebound to a different
    # object). Without this, a fake connection satisfying the recorders below
    # would vacuously discharge the contract.
    Ensures(self.connection is Old(self.connection))
    Ensures(Acc(self.connection.alias, 1 / 2) and Acc(self.connection.supports_rollback, 1 / 2))
    Ensures(Acc(self.connection.caller_alias, 1 / 2))
    Ensures(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
    Ensures(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
    Ensures(Acc(list_pred(sql_list), 1 / 2))
    # (1) the atomic block was scoped to the helper's OWN connection: the
    # database it ran under is the connection's own identifier — derived
    # internally, never supplied by the caller.
    Ensures(self.connection.scoped_alias == self.connection.alias)
    # (2) the block's savepoint behaviour matched the connection's declared
    # rollback capability.
    Ensures(self.connection.scoped_savepoint == self.connection.supports_rollback)
    # (3) exactly the supplied batch ran, in order: the recorded execution list
    # equals the input batch element-wise.
    Ensures(ToSeq(self.connection.executed) == ToSeq(sql_list))
    # post-conditions-end
    # impl-start
    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT FOCUS: A-legs (axioms/deep-model references) + model<->patch correspondence; R/I legs deferred to G-CONF.

SPEC SHAPE (tight): preconditions grant only 1/2 (READ-ONLY) permission on self.connection.alias, supports_rollback, caller_alias, and list_pred(sql_list); FULL permission only on recorders scoped_alias/scoped_savepoint/executed. Postconditions pin all three recorders exactly to gold: (1) scoped_alias == self.connection.alias (own alias, derived internally), (2) scoped_savepoint == supports_rollback, (3) ToSeq(executed) == ToSeq(sql_list) (exact elements + order). Frame Ensures(self.connection is Old(self.connection)) blocks fake-connection substitution.

TOOLING: python=python; SBU_BENCHMARK_DIR=benchmark-verified;

POSITIVE CONTROL: cp of model.py. `bash scripts/nagini_verify.sh .../positive_control.py` => Verification successful (22.4s), exit 0. same-spec => SAME.

ATTACKS (all copy model.py, edit ONLY impl region; axioms/@Pure/Requires/Ensures/Invariant byte-identical). All 8 confirmed same-spec (exit 0). Command each: `python -m swebench_unified.adversary weakness nagini django__django-12741 <atk>`. ALL 8 returned exit 2 = NOT-A-COUNTEREXAMPLE (does not verify) => spec rejected. Detail per attack:
- atk_1 PREPATCH BUG: scoped_alias = caller_alias (externally threaded). Rejected => clause (1) scoped_alias==alias fails. PREPATCH REPRODUCED.
- atk_2 ungrounded-oracle: scoped_savepoint = True constant. Rejected (clause 2).
- atk_3 boundary off-by-one: loop `i < len(sql_list)-1` drops last stmt. Rejected (clause 3, invariant).
- atk_4 control-flow-effect: appends each stmt twice. Rejected (clause 3).
- atk_5 partial-domain no-op: leaves executed empty. Rejected (clause 3).
- atk_6 aliasing echo: executed = sql_list directly. Direct verify => `error: Postcondition ... insufficient permission to access list_pred(self.connection.executed)` (only 1/2 perm on sql_list; cannot alias-transfer).
- atk_7 read-only-defense probe: overwrite self.connection.alias=0 then scope. Direct verify => `error: Assignment might fail ... insufficient permission to access self.connection.alias` (impl holds only 1/2 read-only perm; cannot game clause 1 by rewriting own identity).
- atk_8 reorder: append in REVERSE order. Rejected (clause 3 order).

No attack came back CANDIDATE (none verified while sharing spec), so there is NO verifying wrong impl and therefore NO faithful refined patch to materialize/run_resolve; patches={} accordingly. The verify=>correct falsification path never opened.

G-AX (A-reference correspondence) EXECUTED against the real callee: ` /usr/bin/python3.12 axiom_check.py` => `G-AX OK ... sound over 5072 observations` exit 0. Real post-patch BaseDatabaseOperations.execute_sql_flush confirmed: signature is (self, sql_list) with NO `using` param; block scoped to self.connection.alias; savepoint == features.can_rollback_ddl; exactly sql_list executed in order. (swebench-lean py3.11 SKIPs G-AX due to django import incompat; py3.12 run against checkout HEAD 4bbc27c868 which carries the post-patch signature is the real check.)

REFINEMENT.MD LEG AUDIT: A1=R (helper/connection<->touched fields); A2=I-under-R (drop `using`; real sig verified by grep + G-AX assertion); A3=A-reference (scoped_alias==alias <-> atomic(using=self.connection.alias), G-AX validated); A4=A-reference+I (savepoint <-> can_rollback_ddl, G-AX validated); A5=A-reference+I (loop <-> cursor.execute in order, G-AX validated). Every leg is R / A-reference / I. axioms region is EMPTY (no @ContractOnly): NO A-consumed leg, NO dead axiom, NO kind-3 step. §C claim holds; A-legs' correspondence to real callees confirmed sound.

VERDICT: SOUND. 8 distinct same-spec wrong impls (prepatch, ungrounded-oracle x2, boundary, control-flow-effect, partial-domain, aliasing-echo, reorder) all fail to verify; positive control verifies; prepatch reproduced; G-AX A-references validated against the real Django callee over 5072 observations.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical with the bundle (swebench_unified.adversary same-spec exit 0). The modeled function execute_statement_batch pins exactly three facets of the real routine BaseDatabaseOperations.execute_sql_flush (django/db/backends/base/operations.py:403, post-patch): (1) scoped_alias == connection.alias, (2) scoped_savepoint == supports_rollback (features.can_rollback_ddl), (3) ToSeq(executed) == ToSeq(sql_list). I ran conformance_check.py against the REAL patched repo routine (worktree @ base_commit 537d422942...,, asgiref available in swebench-lean venv): G-CONF OK over 100,192 inputs (192 boundary + 100k fuzz, seed 12741) — shadow == real routine on all three facets, zero disagreements. I also directly drove the real execute_sql_flush with recording stand-ins for transaction.atomic/cursor across edge cases (empty batch, duplicates, multiple aliases, both savepoint values) — all three clauses hold exactly. Signature refinement is faithful: real routine takes exactly one non-self param 'sql_list' and no 'using' (verified via inspect.signature). The spec is NOT too strong: it constrains only what the real routine actually determines. The caller_alias field is modeled but unconstrained/unused by the post-patch impl (it exists only for the prepatch differential witness), so it introduces no over-specification. No diverging input exists between the modeled function and the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, zero hard failures): no diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file/module path in spec view, no changed-symbol echo, no bug/fix narration. Changed symbols {execute_sql_flush, sql_flush, handle} do not appear in the spec view; the repo names are all renamed to behavioural twins (execute_statement_batch, DatabaseOperations, Connection.scoped_alias/caller_alias/supports_rollback).

Semantic judgment: the spec view leaks NOTHING beyond the public problem_statement, which is itself already fully explicit about the gold edit. The public problem_statement states verbatim: old signature `def execute_sql_flush(self, using, sql_list)`, the fix 'The using argument can be dropped and inferred by the calling instance: self.connection.alias', and new signature `def execute_sql_flush(self, sql_list)`. The spec view merely restates this behaviourally: clause (1) scoped_alias==alias (block scoped to the connection's own identifier, derived internally, not the caller-threaded value), plus unchanged behaviour clauses (2) savepoint==supports_rollback and (3) executed==sql_list. The caller_alias recorder models the old `using` value — also fully public via the stated old signature. No pre/post-patch narration, no reference to the F2P test in the spec view, no hints_text echo. The refinement.md/mapping.md docs are NOT part of the spec view and are auditor-facing.

Verified spec region is the byte-identical frozen spec (spec_view rendered from model.py; markers intact). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
