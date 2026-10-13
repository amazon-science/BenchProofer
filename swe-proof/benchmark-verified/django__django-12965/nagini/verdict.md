# P2 adversarial audit — django__django-12965

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.py`, `atk_2.py`, `atk_3.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying implementation produces a faithful refined patch that fails to resolve. All 5 verifying candidates (atk_4/5/6/7/8) resolve under the official harness (run_resolve, resolved=True).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -76,7 +74,7 @@
     Ensures(Result() == (query.extra_active == 0))
     # post-conditions-end
     # impl-start
-    query.primary_present = True
+    # PREPATCH BUG: base table NOT ensured present before count is read
     return active_tables(query.primary_present, query.extra_active) == 1
     # impl-end
 
@@ -86,7 +84,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -77,6 +75,8 @@
     # post-conditions-end
     # impl-start
     query.primary_present = True
+    while True:
+        pass
     return active_tables(query.primary_present, query.extra_active) == 1
     # impl-end
 
@@ -86,7 +86,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -86,7 +84,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
@@ -98,6 +95,8 @@
     Ensures(Implies(Old(query.extra_active) == 0, Result() is False))
     # post-conditions-end
     # impl-start
+    while True:
+        pass
     if references_single_table(query):
         return False
     return True
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -77,7 +75,7 @@
     # post-conditions-end
     # impl-start
     query.primary_present = True
-    return active_tables(query.primary_present, query.extra_active) == 1
+    return active_tables(query.primary_present, query.extra_active) <= 1
     # impl-end
 
 
@@ -86,7 +84,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -77,7 +75,9 @@
     # post-conditions-end
     # impl-start
     query.primary_present = True
-    return active_tables(query.primary_present, query.extra_active) == 1
+    if query.extra_active == 0:
+        return True
+    return False
     # impl-end
 
 
@@ -86,7 +86,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -86,7 +84,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
@@ -98,7 +95,5 @@
     Ensures(Implies(Old(query.extra_active) == 0, Result() is False))
     # post-conditions-end
     # impl-start
-    if references_single_table(query):
-        return False
-    return True
+    return query.extra_active != 0
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -77,7 +75,7 @@
     # post-conditions-end
     # impl-start
     query.primary_present = True
-    return active_tables(query.primary_present, query.extra_active) == 1
+    return query.extra_active < 1
     # impl-end
 
 
@@ -86,7 +84,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -26,7 +26,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class TableRefs:
@@ -61,7 +60,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The primary table is ensured present before the count is read, so its
@@ -77,6 +75,8 @@
     # post-conditions-end
     # impl-start
     query.primary_present = True
+    if query.extra_active < 0:
+        return False
     return active_tables(query.primary_present, query.extra_active) == 1
     # impl-end
 
@@ -86,7 +86,6 @@
     Requires(Acc(query.primary_present))
     Requires(Acc(query.extra_active))
     Requires(query.extra_active >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.primary_present))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12965.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A whole-table row removal (a removal whose selection has no extra joined
  tables and therefore references only the primary table) must be emitted as a
  direct single-table removal — it must NOT be wrapped in a self-referential
  subquery over the same table.

  The decision is governed by an "exactly one active table" predicate over the
  removal's table-reference bookkeeping. Before that predicate is read, the
  primary table must be ensured present in the bookkeeping (its reference count
  made positive). With the primary table accounted for and no additional joined
  tables active, the number of active tables is exactly one, so the predicate
  holds and the direct single-table form is chosen; the subquery form is taken
  only when more than one table is active.

The removal's table-reference bookkeeping is modelled as a minimal object
carrying only the two touched aggregate quantities: whether the primary table
is currently accounted for (its reference count positive), and how many
additional joined tables are currently active. "Ensuring the primary table is
present" and the "exactly one active table" count are spelled out directly;
there is no opaque library callee whose unchanged behaviour the proof relies
on, so this bundle consumes no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class TableRefs:
    def __init__(self, primary_present: bool, extra_active: int) -> None:
        Requires(extra_active >= 0)
        Ensures(Acc(self.primary_present) and self.primary_present is primary_present)  # type: ignore
        Ensures(Acc(self.extra_active) and self.extra_active == extra_active)  # type: ignore
        self.primary_present = primary_present
        self.extra_active = extra_active


# axioms-start
# (no axioms: the decision is pure table-reference bookkeeping, modelled
#  directly; there is no unchanged opaque callee the proof depends on)
# axioms-end


# pure-start
@Pure
def active_tables(primary_present: bool, extra_active: int) -> int:
    """Number of active tables: the primary table (one when accounted for) plus
    the additional joined tables that are currently active."""
    Requires(extra_active >= 0)
    Ensures(Result() >= extra_active)
    Ensures(Result() == (1 if primary_present else 0) + extra_active)
    return (1 if primary_present else 0) + extra_active
# pure-end


def references_single_table(query: TableRefs) -> bool:
    # pre-conditions-start
    Requires(Acc(query.primary_present))
    Requires(Acc(query.extra_active))
    Requires(query.extra_active >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The primary table is ensured present before the count is read, so its
    # reference count is positive regardless of the entry state.
    Ensures(Acc(query.primary_present))
    Ensures(Acc(query.extra_active))
    Ensures(query.extra_active == Old(query.extra_active))
    Ensures(query.primary_present is True)
    # The predicate is true exactly when, with the primary table accounted for,
    # no additional joined tables are active.
    Ensures(Result() == (active_tables(query.primary_present, query.extra_active) == 1))
    Ensures(Result() == (query.extra_active == 0))
    # post-conditions-end
    # impl-start
    query.primary_present = True
    return active_tables(query.primary_present, query.extra_active) == 1
    # impl-end


def delete_uses_subquery(query: TableRefs) -> bool:
    # pre-conditions-start
    Requires(Acc(query.primary_present))
    Requires(Acc(query.extra_active))
    Requires(query.extra_active >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(query.primary_present))
    Ensures(Acc(query.extra_active))
    Ensures(query.extra_active == Old(query.extra_active))
    # A whole-table removal (no additional joined tables active) emits the
    # direct single-table form: no self-referential subquery is used.
    Ensures(Result() == (query.extra_active != 0))
    Ensures(Implies(Old(query.extra_active) == 0, Result() is False))
    # post-conditions-end
    # impl-start
    if references_single_table(query):
        return False
    return True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

patch.diff lives at benchmark-verified/django__django-12965/patch.diff (instance dir), not in the nagini/ bundle dir.

**SPEC ANALYSIS:** The frozen spec is FULLY DETERMINISTIC on its abstract domain. references_single_table forces (a) query.primary_present is True, (b) query.extra_active == Old(extra_active), (c) Result() == (extra_active == 0). delete_uses_subquery forces Result() == (extra_active != 0). There is zero freedom in the observable return values or final state for any input (extra_active >= 0, either primary_present). Therefore every TERMINATING verifying impl is behaviourally identical to gold on the whole abstraction domain -> refines to the gold patch -> resolves. The only real falsification levers are (1) the partial-correctness / non-termination loophole and (2) an abstraction/refinement gap. Both are closed (see below).

### ATTACKS (all same-spec confirmed via `adversary same-spec` exit 0; verified via `adversary weakness`; project root cwd):
- atk_1 (prepatch bug: drop `query.primary_present = True`): weakness exit 2 (does NOT verify). Spec catches the exact reported bug -> prepatch_reproduced=True. Cmd: `python -m swebench_unified.adversary weakness nagini django__django-12965 atk_1.py`.
- atk_2 (non-termination `while True: pass` in references_single_table before return): weakness exit 2 (does NOT verify). Nagini MustTerminate rejects the diverging impl -> the partial-correctness loophole (a diverging single_alias that vacuously satisfies postconditions but whose faithful patch would hang the harness) is CLOSED.
- atk_3 (non-termination in delete_uses_subquery): weakness exit 2 (does NOT verify). Same loophole closed for the caller.
- atk_4 (boundary: `active_tables(...) <= 1` instead of `== 1`): CANDIDATE (exit 0, 9.2s). Since after primary_present:=True the count is 1+extra_active>=1, `<=1` <=> extra_active==0 <=> `==1`. Faithful patch (get_initial_alias + `<= 1`): run_resolve -> completed=True resolved=True.
- atk_5 (control-flow-effect: set primary_present:=True then `if extra_active==0: return True else return False`): CANDIDATE (exit 0). Faithful patch (get_initial_alias + branch on non-base active count == 0): resolved=True.
- atk_6 (caller rewrite: delete_uses_subquery returns `query.extra_active != 0` directly, bypassing the predicate call; references_single_table byte-identical to gold): CANDIDATE (exit 0). delete_uses_subquery maps to the UNCHANGED as_sql caller; its behaviourally-equivalent rewrite introduces no repo edit, so the faithful patch is the gold patch itself: resolved=True.
- atk_7 (ungrounded-oracle-echo/boundary: return `query.extra_active < 1`): CANDIDATE (exit 0). Equivalent to extra_active==0. Faithful patch (get_initial_alias + non-base active count < 1): resolved=True.
- atk_8 (dead-branch: `if non_base_active < 0: return False` guard, unreachable since count>=0, then gold `==1`): CANDIDATE (exit 0). Faithful patch with the dead guard: resolved=True.

**MANDATORY RESOLVE PROTOCOL EXECUTED:** gold patch sanity run_resolve -> resolved=True. All 5 CANDIDATE faithful patches materialized as real repo diffs on compiler.py and run through the OFFICIAL harness (swebench_unified.harness.run_resolve, timeout 1800, run_ids sbu-audit-atk{4,5,6,7,8}-12965): ALL resolved=True, completed=True. No verifying wrong impl produced a non-resolving faithful patch. verify => correct holds for every candidate exhibited.

**POSITIVE CONTROL:** pos_control.py = model.py verbatim; `nagini_verify.sh` -> Verification successful (6.44s), exit 0.

**REFINEMENT.MD AUDIT:** legs A1(R), A2(R), A3(R+I), A4(R), B1(R+I), B2(R+I). No A-consumed leg (axioms region empty, verified byte-for-byte between axioms-start/axioms-end). The single trust point is the A-reference refinement claim for get_initial_alias (net effect = base table accounted, primary_present:=True; other active-table count unchanged), validated by axiom_check.py executing REAL Django (asserts single_alias True for whole-table delete + no nested SELECT; extra_after==extra_before; control multi-table -> single_alias False + subquery). No kind-3 (unexpressible-changed-op) legs. Model<->patch correspondence (Query alias dicts -> (primary_present, extra_active); dict-sum -> active_tables; direct/subquery branch -> boolean discriminator) is faithful and independently corroborated by the 5 resolving materialized patches spanning boundary, control-flow, caller-bypass, oracle-echo and dead-branch shapes.

**VERDICT:** SOUND. >=5 attacks run (8 total: 2 rejected-as-bug, 1 prepatch, 5 candidates all resolving), positive control verifies, prepatch reproduced, non-termination loophole closed by MustTerminate, no verifying wrong impl breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.py`, `atk_2.py`, `atk_3.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying implementation produces a faithful refined patch that fails to resolve. All 5 verifying candidates (atk_4/5/6/7/8) resolve under the official harness (run_resolve, resolved=True).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12965.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A whole-table row removal (a removal whose selection has no extra joined
  tables and therefore references only the primary table) must be emitted as a
  direct single-table removal — it must NOT be wrapped in a self-referential
  subquery over the same table.

  The decision is governed by an "exactly one active table" predicate over the
  removal's table-reference bookkeeping. Before that predicate is read, the
  primary table must be ensured present in the bookkeeping (its reference count
  made positive). With the primary table accounted for and no additional joined
  tables active, the number of active tables is exactly one, so the predicate
  holds and the direct single-table form is chosen; the subquery form is taken
  only when more than one table is active.

The removal's table-reference bookkeeping is modelled as a minimal object
carrying only the two touched aggregate quantities: whether the primary table
is currently accounted for (its reference count positive), and how many
additional joined tables are currently active. "Ensuring the primary table is
present" and the "exactly one active table" count are spelled out directly;
there is no opaque library callee whose unchanged behaviour the proof relies
on, so this bundle consumes no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class TableRefs:
    def __init__(self, primary_present: bool, extra_active: int) -> None:
        Requires(extra_active >= 0)
        Ensures(Acc(self.primary_present) and self.primary_present is primary_present)  # type: ignore
        Ensures(Acc(self.extra_active) and self.extra_active == extra_active)  # type: ignore
        self.primary_present = primary_present
        self.extra_active = extra_active


# axioms-start
# (no axioms: the decision is pure table-reference bookkeeping, modelled
#  directly; there is no unchanged opaque callee the proof depends on)
# axioms-end


# pure-start
@Pure
def active_tables(primary_present: bool, extra_active: int) -> int:
    """Number of active tables: the primary table (one when accounted for) plus
    the additional joined tables that are currently active."""
    Requires(extra_active >= 0)
    Ensures(Result() >= extra_active)
    Ensures(Result() == (1 if primary_present else 0) + extra_active)
    return (1 if primary_present else 0) + extra_active
# pure-end


def references_single_table(query: TableRefs) -> bool:
    # pre-conditions-start
    Requires(Acc(query.primary_present))
    Requires(Acc(query.extra_active))
    Requires(query.extra_active >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The primary table is ensured present before the count is read, so its
    # reference count is positive regardless of the entry state.
    Ensures(Acc(query.primary_present))
    Ensures(Acc(query.extra_active))
    Ensures(query.extra_active == Old(query.extra_active))
    Ensures(query.primary_present is True)
    # The predicate is true exactly when, with the primary table accounted for,
    # no additional joined tables are active.
    Ensures(Result() == (active_tables(query.primary_present, query.extra_active) == 1))
    Ensures(Result() == (query.extra_active == 0))
    # post-conditions-end
    # impl-start
    query.primary_present = True
    return active_tables(query.primary_present, query.extra_active) == 1
    # impl-end


def delete_uses_subquery(query: TableRefs) -> bool:
    # pre-conditions-start
    Requires(Acc(query.primary_present))
    Requires(Acc(query.extra_active))
    Requires(query.extra_active >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(query.primary_present))
    Ensures(Acc(query.extra_active))
    Ensures(query.extra_active == Old(query.extra_active))
    # A whole-table removal (no additional joined tables active) emits the
    # direct single-table form: no self-referential subquery is used.
    Ensures(Result() == (query.extra_active != 0))
    Ensures(Implies(Old(query.extra_active) == 0, Result() is False))
    # post-conditions-end
    # impl-start
    if references_single_table(query):
        return False
    return True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

patch.diff lives at benchmark-verified/django__django-12965/patch.diff (instance dir), not in the nagini/ bundle dir.

**SPEC ANALYSIS:** The frozen spec is FULLY DETERMINISTIC on its abstract domain. references_single_table forces (a) query.primary_present is True, (b) query.extra_active == Old(extra_active), (c) Result() == (extra_active == 0). delete_uses_subquery forces Result() == (extra_active != 0). There is zero freedom in the observable return values or final state for any input (extra_active >= 0, either primary_present). Therefore every TERMINATING verifying impl is behaviourally identical to gold on the whole abstraction domain -> refines to the gold patch -> resolves. The only real falsification levers are (1) the partial-correctness / non-termination loophole and (2) an abstraction/refinement gap. Both are closed (see below).

### ATTACKS (all same-spec confirmed via `adversary same-spec` exit 0; verified via `adversary weakness`; project root cwd):
- atk_1 (prepatch bug: drop `query.primary_present = True`): weakness exit 2 (does NOT verify). Spec catches the exact reported bug -> prepatch_reproduced=True. Cmd: `python -m swebench_unified.adversary weakness nagini django__django-12965 atk_1.py`.
- atk_2 (non-termination `while True: pass` in references_single_table before return): weakness exit 2 (does NOT verify). Nagini MustTerminate rejects the diverging impl -> the partial-correctness loophole (a diverging single_alias that vacuously satisfies postconditions but whose faithful patch would hang the harness) is CLOSED.
- atk_3 (non-termination in delete_uses_subquery): weakness exit 2 (does NOT verify). Same loophole closed for the caller.
- atk_4 (boundary: `active_tables(...) <= 1` instead of `== 1`): CANDIDATE (exit 0, 9.2s). Since after primary_present:=True the count is 1+extra_active>=1, `<=1` <=> extra_active==0 <=> `==1`. Faithful patch (get_initial_alias + `<= 1`): run_resolve -> completed=True resolved=True.
- atk_5 (control-flow-effect: set primary_present:=True then `if extra_active==0: return True else return False`): CANDIDATE (exit 0). Faithful patch (get_initial_alias + branch on non-base active count == 0): resolved=True.
- atk_6 (caller rewrite: delete_uses_subquery returns `query.extra_active != 0` directly, bypassing the predicate call; references_single_table byte-identical to gold): CANDIDATE (exit 0). delete_uses_subquery maps to the UNCHANGED as_sql caller; its behaviourally-equivalent rewrite introduces no repo edit, so the faithful patch is the gold patch itself: resolved=True.
- atk_7 (ungrounded-oracle-echo/boundary: return `query.extra_active < 1`): CANDIDATE (exit 0). Equivalent to extra_active==0. Faithful patch (get_initial_alias + non-base active count < 1): resolved=True.
- atk_8 (dead-branch: `if non_base_active < 0: return False` guard, unreachable since count>=0, then gold `==1`): CANDIDATE (exit 0). Faithful patch with the dead guard: resolved=True.

**MANDATORY RESOLVE PROTOCOL EXECUTED:** gold patch sanity run_resolve -> resolved=True. All 5 CANDIDATE faithful patches materialized as real repo diffs on compiler.py and run through the OFFICIAL harness (swebench_unified.harness.run_resolve, timeout 1800, run_ids sbu-audit-atk{4,5,6,7,8}-12965): ALL resolved=True, completed=True. No verifying wrong impl produced a non-resolving faithful patch. verify => correct holds for every candidate exhibited.

**POSITIVE CONTROL:** pos_control.py = model.py verbatim; `nagini_verify.sh` -> Verification successful (6.44s), exit 0.

**REFINEMENT.MD AUDIT:** legs A1(R), A2(R), A3(R+I), A4(R), B1(R+I), B2(R+I). No A-consumed leg (axioms region empty, verified byte-for-byte between axioms-start/axioms-end). The single trust point is the A-reference refinement claim for get_initial_alias (net effect = base table accounted, primary_present:=True; other active-table count unchanged), validated by axiom_check.py executing REAL Django (asserts single_alias True for whole-table delete + no nested SELECT; extra_after==extra_before; control multi-table -> single_alias False + subquery). No kind-3 (unexpressible-changed-op) legs. Model<->patch correspondence (Query alias dicts -> (primary_present, extra_active); dict-sum -> active_tables; direct/subquery branch -> boolean discriminator) is faithful and independently corroborated by the 5 resolving materialized patches spanning boundary, control-flow, caller-bypass, oracle-echo and dead-branch shapes.

**VERDICT:** SOUND. >=5 attacks run (8 total: 2 rejected-as-bug, 1 prepatch, 5 candidates all resolving), positive control verifies, prepatch reproduced, non-termination loophole closed by MustTerminate, no verifying wrong impl breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for nagini django__django-12965. Spec region confirmed byte-identical (same-spec on a verbatim model.py copy returns SAME, exit 0).

**Modeled functions:** references_single_table sets primary_present:=True and returns active_tables(True, extra_active)==1 i.e. (extra_active==0) — models the post-fix SQLDeleteCompiler.single_alias. delete_uses_subquery returns (extra_active != 0) — models the unchanged as_sql direct-vs-subquery choice. Domain: Requires(extra_active >= 0) (natural non-negative alias count; excludes no realizable state), for either primary_present value.

Independent real-repo cross-check: built base_commit 437196da… worktree, applied gold patch.diff (adds self.query.get_initial_alias() before the alias_refcount sum), and drove the REAL patched SQLDeleteCompiler.single_alias and as_sql (in-memory sqlite, SQL compiled only) over the full abstract grid primary_present∈{False,True} × extra_active∈0..11. State construction verified via the same alias-map/refcount abstraction the bundle uses. Result: real single_alias matched spec (True iff extra_active==0) on every state; real as_sql emitted a nested SELECT iff extra_active!=0 — matching delete_uses_subquery. 0 divergences. After get_initial_alias the base alias is always accounted, so count = 1 + extra_active, which is ==1 exactly when extra_active==0; this holds across the whole domain.

This reproduces the recorded G-CONF pass (100090 states, boundary+fuzz, seed 12965, 0 disagreements, shadow=direct contract-stripped impl) and G-AX (whole-table delete → single_alias=True, no subquery; multi-table → single_alias=False, subquery). Bundle consumes no axioms; the sole trust point is the R-refinement (Query alias dicts → (primary_present, extra_active); get_initial_alias net effect → primary_present:=True with extra_active fixed), which I independently confirmed against real Django.

The spec is neither too strong nor domain-restricted; no input in the modeled domain makes the modeled function disagree with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) passes: no hard failures. Manual G-PANEL-3 review of the consumer spec view confirms no reconstruction of the gold edit beyond the public problem_statement.

**Gold edit:** in SQLDeleteCompiler.single_alias (django/db/models/sql/compiler.py) add `# Ensure base table is in aliases.` + `self.query.get_initial_alias()` before `sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1`.

Leak baseline = problem_statement only (hints_text excluded). The public task already states the full observable: Model.objects.all().delete() emits `DELETE FROM ... WHERE id IN (SELECT ...)` (subquery/perf regression) instead of the plain `DELETE FROM ...`, and asks to prevent the subquery for a single alias.

Spec-view findings:
- No diff markers, no patched file path (compiler.py absent), no patched module path.
- No patched repo symbols echoed: spec uses abstract carriers TableRefs/primary_present/extra_active/active_tables/references_single_table/delete_uses_subquery; none embeds single_alias, get_initial_alias, alias_map, alias_refcount, or SQLDeleteCompiler (mapping.md notes the deliberate rename).
- No fix/bug/regression narration in spec-view comments/docstrings.
- The described required behavior ('whole-table removal must be a direct single-table form, not a self-referential subquery') is already public verbatim in the problem statement (both SQL forms shown).
- The mechanism clause ('the primary table must be ensured present / reference count made positive before the predicate is read') is the abstract behavioral requirement the twin-artifact spec must encode to sense the bug (G-DIFF). It localizes nothing to the repo: no file, no symbol, no 'call get_initial_alias'. Specifying required corrected behavior at the model level is not gold-edit reconstruction.

**Conclusion:** the spec view leaks no repo-localizing information about the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
