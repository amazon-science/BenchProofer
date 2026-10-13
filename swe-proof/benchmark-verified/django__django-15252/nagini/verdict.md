# P2 adversarial audit — django__django-15252

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -154,15 +149,7 @@
     Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
     # post-conditions-end
     # impl-start
-    if no_pending_records(pending):
-        if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
-            return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
-    else:
-        executor.schema_ensured = True
+    executor.schema_ensured = True
     executor.records_read = True
     return
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -155,14 +150,9 @@
     # post-conditions-end
     # impl-start
     if no_pending_records(pending):
-        if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
-            return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
+        executor.records_read = False
     else:
         executor.schema_ensured = True
-    executor.records_read = True
+        executor.records_read = True
     return
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -154,14 +149,7 @@
     Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
     # post-conditions-end
     # impl-start
-    if no_pending_records(pending):
-        if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
-            return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
-    else:
+    if not no_pending_records(pending):
         executor.schema_ensured = True
     executor.records_read = True
     return
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -154,15 +149,7 @@
     Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
     # post-conditions-end
     # impl-start
-    if no_pending_records(pending):
-        if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
-            return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
-    else:
-        executor.schema_ensured = True
+    executor.schema_ensured = False
     executor.records_read = True
     return
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -155,14 +150,9 @@
     # post-conditions-end
     # impl-start
     if no_pending_records(pending):
+        executor.schema_ensured = True
         if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
             return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
-    else:
-        executor.schema_ensured = True
     executor.records_read = True
     return
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -155,12 +150,7 @@
     # post-conditions-end
     # impl-start
     if no_pending_records(pending):
-        if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
-            return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
+        return
     else:
         executor.schema_ensured = True
     executor.records_read = True
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Executor:
@@ -80,9 +79,6 @@
     """
 
     def __init__(self, table_present: bool) -> None:
-        # Terminates: three field assignments, no loop and no call. Level 2
-        # leaves room beneath any obligated caller (migrate is at 6).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
         Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
         Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
@@ -126,7 +122,6 @@
     # The recording-work argument is read-only (its presence/emptiness is
     # consulted, never mutated): fractional permission, required AND ensured.
     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(executor.table_present, 1 / 2))
@@ -154,14 +149,7 @@
     Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
     # post-conditions-end
     # impl-start
-    if no_pending_records(pending):
-        if not executor.table_present:
-            # No migrations to record and no table present: assemble the result
-            # without touching the connection (no write, no read).
-            return
-        # Table already present: fall through to the read-assembly path below;
-        # no write effect on this branch.
-    else:
+    if not executor.table_present:
         executor.schema_ensured = True
     executor.records_read = True
     return
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15252.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A migration-execution routine runs against ONE database connection. Before it
  records that migrations have been applied, it consults a bookkeeping table.
  Putting that bookkeeping table in place is an OBSERVABLE, SIDE-EFFECTING act
  (it issues schema statements against the connection) and is undesirable on a
  connection that is not supposed to hold the table — there it can create a
  table that is not wanted, or fail outright on a connection without the
  privilege to create one. The bookkeeping table exists only to support
  recording applied migrations, so the side effect is wanted only where there
  are migrations to record.

  Two observable effects of the routine are pinned by this specification:

    (A) the table-ensuring WRITE effect (it puts the bookkeeping table in
        place); and
    (B) a record-reading QUERY effect (it consults the recorded data while it
        assembles its result).

  The desired behaviour, per connection:

    * this connection has NO migrations to record: the routine must NOT perform
      the table-ensuring write effect. Moreover, if in that situation the
      bookkeeping table is not already in place, the routine must assemble its
      result WITHOUT issuing the record-reading query effect either (the table
      it would read does not exist, so the routine must not touch the
      connection at all on this path).

    * this connection's recording work is UNDETERMINED (yet to be computed) OR
      there ARE migrations to record: the routine puts the bookkeeping table in
      place (the write effect) when there are migrations to record, and in all
      these cases proceeds to assemble its result via the record-reading query
      effect, exactly as before.

  Reading back the observable effects:
    * the table-ensuring write effect occurred IF AND ONLY IF this connection
      was NOT determined to have no migrations to record;
    * the record-reading query effect occurred EXCEPT on the one path where the
      connection has no migrations to record AND the table is not already in
      place (there the routine assembles its result without touching the
      connection at all).

Modelling choices (Nagini fragment):
  * The executor is a minimal object carrying only the touched facets: a
    read-only flag for whether the bookkeeping table is already in place, a
    mutable flag recording whether the table-ensuring WRITE effect has occurred
    (it starts un-occurred), and a mutable flag recording whether the
    record-reading QUERY effect has occurred (it starts un-occurred).
  * The recording-work argument is an ``Optional[List[int]]``: ``None`` means
    "undetermined for this connection" (yet to be computed); a present list is
    the determined recording work, and ``len(...) == 0`` distinguishes the case
    where this connection has NO migrations to record. Only its presence and
    emptiness are observed (mapping.md §2), so a list of opaque integer record
    tokens is the faithful carrier.

The table-presence flag is read-only and held at fractional permission. The
two effect flags are genuinely mutated and held at full permission with their
exact post-state stated. There is no axiomatised callee: the table-ensuring
write, the table-presence query, and the record-reading result assembly are
each reduced to the observation this specification pins, and the decision over
those observations is the changed behaviour, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Executor:
    """Minimal executor object carrying only the touched facets.

    `table_present` — whether the bookkeeping table is already in place
        (read-only query result). `schema_ensured` — whether the table-ensuring
        WRITE effect has occurred (the observable write effect; starts False).
    `records_read` — whether the record-reading QUERY effect has occurred
        (the observable read effect; starts False).
    """

    def __init__(self, table_present: bool) -> None:
        Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
        Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
        Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
        self.table_present = table_present          # type: bool
        self.schema_ensured = False                 # type: bool
        self.records_read = False                   # type: bool


# axioms-start
# (no @ContractOnly axioms are consumed: the unchanged primitives this routine
# consults — querying whether the bookkeeping table is already in place, the
# table-ensuring write effect, and the record-reading result assembly — are
# each reduced to the boolean observation this specification pins. The decision
# over those observations is the changed behaviour and is modelled deeply in
# the impl region.)
# axioms-end


# pure-start
@Pure
def no_pending_records(pending: Optional[List[int]]) -> bool:
    # This connection has NO migrations to record: the argument is present (not
    # None) and conveys no recording work (a present, length-zero carrier). A
    # None argument is 'undetermined' (yet to be computed), NOT a determination
    # that there are none.
    Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 4)))
    return pending is not None and len(pending) == 0
# pure-end


def migrate(executor: Executor, pending: Optional[List[int]]) -> None:
    # pre-conditions-start
    # The table-presence flag is a read-only query result (fractional).
    Requires(Acc(executor.table_present, 1 / 2))
    # The two effect flags are mutated; full permission, and they start
    # un-occurred (no effect has happened yet on entry).
    Requires(Acc(executor.schema_ensured))
    Requires(executor.schema_ensured is False)
    Requires(Acc(executor.records_read))
    Requires(executor.records_read is False)
    # The recording-work argument is read-only (its presence/emptiness is
    # consulted, never mutated): fractional permission, required AND ensured.
    Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(executor.table_present, 1 / 2))
    Ensures(Acc(executor.schema_ensured))
    Ensures(Acc(executor.records_read))
    Ensures(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
    # The table-presence query is read-only: its result is unchanged.
    Ensures(executor.table_present == Old(executor.table_present))

    # (1) THE pinned behaviour: the table-ensuring WRITE effect occurred IF AND
    #     ONLY IF this connection was NOT determined to have no migrations to
    #     record. Equivalently, the write effect is skipped exactly when this
    #     connection has been determined to have no migrations to record
    #     (whether or not the table is already in place).
    Ensures(executor.schema_ensured == (not no_pending_records(pending)))

    # (2) The record-reading QUERY effect occurred EXCEPT on the single path
    #     where this connection has no migrations to record AND the table is not
    #     already in place — there the routine assembles its result without
    #     touching the connection at all (no write effect by (1), and no read
    #     effect here).
    Ensures(executor.records_read ==
            (not (no_pending_records(pending) and not Old(executor.table_present))))
    # On that no-touch path, neither effect occurs.
    Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
    # post-conditions-end
    # impl-start
    executor.schema_ensured = not no_pending_records(pending)
    if no_pending_records(pending) and not executor.table_present:
        return
    executor.records_read = True
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT/A-LEG AUDIT: refinement.md §C declares no kind-3 steps and NO consumed axiom / NO A-reference; all legs A1-A7 are R or R+I. The three callees (has_table, ensure_schema, record-reading assembly) are reduced to deep-modeled boolean observations (Executor.table_present / schema_ensured / records_read), not axiomatized. The A-substitute is the G-AX decision-logic-equivalence check axiom_check.py, which I RAN: exit 0 -- model observations == gold-patched observations on all 6 (work-list-shape {None,[],[non-empty]} x table-existence {F,T}) combos, plus the F2P test_migrate_skips_schema_creation witness (gold 0 ensure_schema calls vs prepatch 1). model<->patch correspondence holds. The FROZEN spec pins BOTH observables as exact boolean functions of the inputs: schema_ensured == not no_pending_records(pending); records_read == not(no_pending_records(pending) and not Old(table_present)); plus the no-touch coupling clause Implies(not records_read, schema_ensured is False). This leaves no slack for a verifying-but-wrong impl.

ATTACKS: 7 DISTINCT same-spec wrong impls, edited ONLY in impl region (axioms/@Pure/Requires/Ensures byte-identical; confirmed via `adversary same-spec` rc=0 for all 7). Classes: atk_1 prepatch bug (schema+records unconditionally True); atk_2 partial-domain (records=False on np, ignores table-present case so np&table gives records=False, wrong); atk_3 control-flow-effect (drops early-return, always reads on np&no-table); atk_4 ungrounded-oracle echo (schema=False, records=True constants); atk_5 inverted guard (schema set on np instead of not-np); atk_6 boundary (early-return on BOTH np paths, so np&table skips read wrongly); atk_7 wrong discriminant (gates schema on table_present instead of no_pending_records).

Command per attack (run <=3 concurrently as background Bash jobs, each JVM+Z3): `python -m swebench_unified.adversary weakness nagini django__django-15252 <path>`. RESULTS: all 7 returned exit 2 (NOT-A-COUNTEREXAMPLE: attack does not verify -- spec rejected). NO CANDIDATE (no impl both shares spec AND verifies while wrong), therefore NO faithful-patch materialization / run_resolve was required per protocol step 2.

POSITIVE CONTROL pos_control.py (correct, differently-written: direct schema_ensured = not no_pending_records(pending), separate short-circuit) is same-spec (rc=0) AND verifies (`nagini_verify.sh` exit 0, 15.25s) -- confirms the harness is live and the spec is satisfiable by a correct impl. PREPATCH bug reproduced: atk_1 = prepatch skeleton fails verification (rejected), matching model_prepatch.py's documented failure at the schema_ensured postcondition.

Verdict SOUND: >=5 (7) distinct attacks run, none is a verifying wrong impl; verify does not admit an incorrect impl here. axiom_check G-AX passed; positive control verifies.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15252.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A migration-execution routine runs against ONE database connection. Before it
  records that migrations have been applied, it consults a bookkeeping table.
  Putting that bookkeeping table in place is an OBSERVABLE, SIDE-EFFECTING act
  (it issues schema statements against the connection) and is undesirable on a
  connection that is not supposed to hold the table — there it can create a
  table that is not wanted, or fail outright on a connection without the
  privilege to create one. The bookkeeping table exists only to support
  recording applied migrations, so the side effect is wanted only where there
  are migrations to record.

  Two observable effects of the routine are pinned by this specification:

    (A) the table-ensuring WRITE effect (it puts the bookkeeping table in
        place); and
    (B) a record-reading QUERY effect (it consults the recorded data while it
        assembles its result).

  The desired behaviour, per connection:

    * this connection has NO migrations to record: the routine must NOT perform
      the table-ensuring write effect. Moreover, if in that situation the
      bookkeeping table is not already in place, the routine must assemble its
      result WITHOUT issuing the record-reading query effect either (the table
      it would read does not exist, so the routine must not touch the
      connection at all on this path).

    * this connection's recording work is UNDETERMINED (yet to be computed) OR
      there ARE migrations to record: the routine puts the bookkeeping table in
      place (the write effect) when there are migrations to record, and in all
      these cases proceeds to assemble its result via the record-reading query
      effect, exactly as before.

  Reading back the observable effects:
    * the table-ensuring write effect occurred IF AND ONLY IF this connection
      was NOT determined to have no migrations to record;
    * the record-reading query effect occurred EXCEPT on the one path where the
      connection has no migrations to record AND the table is not already in
      place (there the routine assembles its result without touching the
      connection at all).

Modelling choices (Nagini fragment):
  * The executor is a minimal object carrying only the touched facets: a
    read-only flag for whether the bookkeeping table is already in place, a
    mutable flag recording whether the table-ensuring WRITE effect has occurred
    (it starts un-occurred), and a mutable flag recording whether the
    record-reading QUERY effect has occurred (it starts un-occurred).
  * The recording-work argument is an ``Optional[List[int]]``: ``None`` means
    "undetermined for this connection" (yet to be computed); a present list is
    the determined recording work, and ``len(...) == 0`` distinguishes the case
    where this connection has NO migrations to record. Only its presence and
    emptiness are observed (mapping.md §2), so a list of opaque integer record
    tokens is the faithful carrier.

The table-presence flag is read-only and held at fractional permission. The
two effect flags are genuinely mutated and held at full permission with their
exact post-state stated. There is no axiomatised callee: the table-ensuring
write, the table-presence query, and the record-reading result assembly are
each reduced to the observation this specification pins, and the decision over
those observations is the changed behaviour, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Executor:
    """Minimal executor object carrying only the touched facets.

    `table_present` — whether the bookkeeping table is already in place
        (read-only query result). `schema_ensured` — whether the table-ensuring
        WRITE effect has occurred (the observable write effect; starts False).
    `records_read` — whether the record-reading QUERY effect has occurred
        (the observable read effect; starts False).
    """

    def __init__(self, table_present: bool) -> None:
        Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
        Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
        Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
        self.table_present = table_present          # type: bool
        self.schema_ensured = False                 # type: bool
        self.records_read = False                   # type: bool


# axioms-start
# (no @ContractOnly axioms are consumed: the unchanged primitives this routine
# consults — querying whether the bookkeeping table is already in place, the
# table-ensuring write effect, and the record-reading result assembly — are
# each reduced to the boolean observation this specification pins. The decision
# over those observations is the changed behaviour and is modelled deeply in
# the impl region.)
# axioms-end


# pure-start
@Pure
def no_pending_records(pending: Optional[List[int]]) -> bool:
    # This connection has NO migrations to record: the argument is present (not
    # None) and conveys no recording work (a present, length-zero carrier). A
    # None argument is 'undetermined' (yet to be computed), NOT a determination
    # that there are none.
    Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 4)))
    return pending is not None and len(pending) == 0
# pure-end


def migrate(executor: Executor, pending: Optional[List[int]]) -> None:
    # pre-conditions-start
    # The table-presence flag is a read-only query result (fractional).
    Requires(Acc(executor.table_present, 1 / 2))
    # The two effect flags are mutated; full permission, and they start
    # un-occurred (no effect has happened yet on entry).
    Requires(Acc(executor.schema_ensured))
    Requires(executor.schema_ensured is False)
    Requires(Acc(executor.records_read))
    Requires(executor.records_read is False)
    # The recording-work argument is read-only (its presence/emptiness is
    # consulted, never mutated): fractional permission, required AND ensured.
    Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(executor.table_present, 1 / 2))
    Ensures(Acc(executor.schema_ensured))
    Ensures(Acc(executor.records_read))
    Ensures(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
    # The table-presence query is read-only: its result is unchanged.
    Ensures(executor.table_present == Old(executor.table_present))

    # (1) THE pinned behaviour: the table-ensuring WRITE effect occurred IF AND
    #     ONLY IF this connection was NOT determined to have no migrations to
    #     record. Equivalently, the write effect is skipped exactly when this
    #     connection has been determined to have no migrations to record
    #     (whether or not the table is already in place).
    Ensures(executor.schema_ensured == (not no_pending_records(pending)))

    # (2) The record-reading QUERY effect occurred EXCEPT on the single path
    #     where this connection has no migrations to record AND the table is not
    #     already in place — there the routine assembles its result without
    #     touching the connection at all (no write effect by (1), and no read
    #     effect here).
    Ensures(executor.records_read ==
            (not (no_pending_records(pending) and not Old(executor.table_present))))
    # On that no-touch path, neither effect occurs.
    Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
    # post-conditions-end
    # impl-start
    executor.schema_ensured = not no_pending_records(pending)
    if no_pending_records(pending) and not executor.table_present:
        return
    executor.records_read = True
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT/A-LEG AUDIT: refinement.md §C declares no kind-3 steps and NO consumed axiom / NO A-reference; all legs A1-A7 are R or R+I. The three callees (has_table, ensure_schema, record-reading assembly) are reduced to deep-modeled boolean observations (Executor.table_present / schema_ensured / records_read), not axiomatized. The A-substitute is the G-AX decision-logic-equivalence check axiom_check.py, which I RAN: exit 0 -- model observations == gold-patched observations on all 6 (work-list-shape {None,[],[non-empty]} x table-existence {F,T}) combos, plus the F2P test_migrate_skips_schema_creation witness (gold 0 ensure_schema calls vs prepatch 1). model<->patch correspondence holds. The FROZEN spec pins BOTH observables as exact boolean functions of the inputs: schema_ensured == not no_pending_records(pending); records_read == not(no_pending_records(pending) and not Old(table_present)); plus the no-touch coupling clause Implies(not records_read, schema_ensured is False). This leaves no slack for a verifying-but-wrong impl.

ATTACKS: 7 DISTINCT same-spec wrong impls, edited ONLY in impl region (axioms/@Pure/Requires/Ensures byte-identical; confirmed via `adversary same-spec` rc=0 for all 7). Classes: atk_1 prepatch bug (schema+records unconditionally True); atk_2 partial-domain (records=False on np, ignores table-present case so np&table gives records=False, wrong); atk_3 control-flow-effect (drops early-return, always reads on np&no-table); atk_4 ungrounded-oracle echo (schema=False, records=True constants); atk_5 inverted guard (schema set on np instead of not-np); atk_6 boundary (early-return on BOTH np paths, so np&table skips read wrongly); atk_7 wrong discriminant (gates schema on table_present instead of no_pending_records).

Command per attack (run <=3 concurrently as background Bash jobs, each JVM+Z3): `python -m swebench_unified.adversary weakness nagini django__django-15252 <path>`. RESULTS: all 7 returned exit 2 (NOT-A-COUNTEREXAMPLE: attack does not verify -- spec rejected). NO CANDIDATE (no impl both shares spec AND verifies while wrong), therefore NO faithful-patch materialization / run_resolve was required per protocol step 2.

POSITIVE CONTROL pos_control.py (correct, differently-written: direct schema_ensured = not no_pending_records(pending), separate short-circuit) is same-spec (rc=0) AND verifies (`nagini_verify.sh` exit 0, 15.25s) -- confirms the harness is live and the spec is satisfiable by a correct impl. PREPATCH bug reproduced: atk_1 = prepatch skeleton fails verification (rejected), matching model_prepatch.py's documented failure at the schema_ensured postcondition.

Verdict SOUND: >=5 (7) distinct attacks run, none is a verifying wrong impl; verify does not admit an incorrect impl here. axiom_check G-AX passed; positive control verifies.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo) audit for django__django-15252 nagini bundle. The modeled function migrate(executor, pending) pins three observable effects via postconditions: (1) schema_ensured == not no_pending_records(pending); (2) records_read == not (no_pending_records(pending) and not Old(table_present)); (3) not records_read => not schema_ensured. no_pending_records(pending) := pending is not None and len(pending)==0.

Real repo behavior (base_commit 361bb8f, + gold patch.diff): the gold prologue is `if plan == []: { if not has_table(): return _create_project_state(with_applied_migrations=False) } else: ensure_schema()` then the normal record-reading assembly tail. I traced this by hand and enumerated all {None, [], [non-empty]} x {table absent, present} combinations independently (not trusting the bundle's own axiom_check):
  plan=None : (schema=T, read=T, early=F) both
  plan=[] table absent : (F, F, early=T) both -- short-circuit, no write, no read
  plan=[] table present: (F, T, F) both -- skip write, still read records
  plan=[non-empty] : (T, T, F) both
Model postconditions match the real callee on ALL six inputs; no diverging input exists. The Optional[List[int]] carrier is faithful: only presence/emptiness gate behavior, matching `plan is None` / `plan == []`; None models 'undetermined' (falls into else -> ensure_schema, matching gold where plan==[] is False for None). The spec is neither too strong nor drifted.

Machine checks all pass: scripts/nagini_verify.sh model.py -> 'Verification successful' (exit 0); axiom_check.py -> G-AX OK across 6 combos + F2P witness (exit 0); model_prepatch.py fails at line 139 postcondition (schema_ensured == not no_pending_records) confirming the spec discriminates the gold fix from the unconditional-ensure_schema bug (G-DIFF). Spec regions verified via same-spec markers implicitly through the passing verify.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Properly-dispositioned relaxed-leakage bundle (meta.relaxed_leakage=true, RELAXED_LEAKAGE.md present, gates.G-LEAK.status="relaxed"). Independently re-verified, not rubber-stamped. CORE SOUNDNESS: G-VERIFY pass (model.py verifies, exit 0, 13.1s); G-DIFF pass (model_prepatch.py shares byte-identical spec — same_spec TRUE — and FAILS on postcondition `executor.schema_ensured == (not no_pending_records(pending))` at model_prepatch.py:139); G-AX pass (axiom_check.py RC=0: model observations == gold observations on all 6 work-list-shape x table-existence combos + F2P witness gold ensure_schema_calls=0 vs prepatch=1). Mechanical G-LEAK screen PASSES (hard_failures=[]). UNAVOIDABILITY RE-DERIVED: gold discriminator = the determined-no-work gate (plan==[]) + no-table no-touch short-circuit. Confirmed by token scan that the gold trigger vocabulary is ABSENT from the solver-visible problem_statement ('no migrations','empty','plan','pending','has_table','project state','with_applied','skip' all ABSENT), while the PS frames the entire defect around allow_migrate/router/db_router (all PRESENT) — the gold does NOT even call allow_migrate. A faithful spec (prepatch fails; no wrong impl verifies) MUST pin the no-work gate, which is a hints_text/gold-internal concept; a non-leaking spec (judged vs problem_statement only) cannot. Faithful+non-leaking is therefore genuinely impossible — a PS<->gold mismatch, not a de-narration gap. NEW-LEAK HUNT (beyond the dispositioned facet): scanned the spec view (impl region elided) — NO patched repo symbol appears (plan/ensure_schema/has_table/_create_project_state/with_applied/recorder/MigrationExecutor/router/allow_migrate/django_migrations all absent), NO diff line quoted, NO diff markers, NO bug/fix narration terms. The only leaked content is the semantic no-work/no-touch discriminator expressed in the model's own neutral vocabulary (pending, no_pending_records, schema_ensured, records_read + the two effect postconditions) — exactly the dispositioned facet, nothing more. No leak beyond the facet and no broken-disposition indicator found. Honest recording per gates/_audit.py convention: NO-LEAKAGE (pass) + note.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
