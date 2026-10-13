# P2 adversarial audit — django__django-15629

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -131,8 +129,8 @@
     # post-conditions-end
     # impl-start
     result = {}  # type: Dict[int, int]
-    result[key_type()] = own_type
-    result[key_check()] = own_check
+    result[key_type()] = own_check
+    result[key_check()] = own_type
     result[key_collation()] = target_params[key_collation()]
     return result
     # impl-end
@@ -141,7 +139,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -133,7 +131,7 @@
     result = {}  # type: Dict[int, int]
     result[key_type()] = own_type
     result[key_check()] = own_check
-    result[key_collation()] = target_params[key_collation()]
+    result[key_collation()] = none_value()
     return result
     # impl-end
 
@@ -141,7 +139,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -134,6 +132,7 @@
     result[key_type()] = own_type
     result[key_check()] = own_check
     result[key_collation()] = target_params[key_collation()]
+    result[99] = own_type
     return result
     # impl-end
 
@@ -141,7 +140,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -141,7 +139,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
@@ -159,5 +156,5 @@
                     not Result()))
     # post-conditions-end
     # impl-start
-    return differs(old_type, new_type) or differs(old_collation, new_collation)
+    return True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -141,7 +139,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
@@ -159,5 +156,5 @@
                     not Result()))
     # post-conditions-end
     # impl-start
-    return differs(old_type, new_type) or differs(old_collation, new_collation)
+    return differs(old_type, new_type) and differs(old_collation, new_collation)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -141,7 +139,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
@@ -159,5 +156,5 @@
                     not Result()))
     # post-conditions-end
     # impl-start
-    return differs(old_type, new_type) or differs(old_collation, new_collation)
+    return differs(old_collation, new_collation)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # The referenced column reports a collation entry (possibly the empty
     # sentinel).
     Requires(key_collation() in target_params)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(target_params), 1 / 2))
@@ -133,7 +131,7 @@
     result = {}  # type: Dict[int, int]
     result[key_type()] = own_type
     result[key_check()] = own_check
-    result[key_collation()] = target_params[key_collation()]
+    result[key_collation()] = own_type
     return result
     # impl-end
 
@@ -141,7 +139,6 @@
 def references_need_rebuild(old_type: int, new_type: int,
                             old_collation: int, new_collation: int) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (2) Columns referencing an altered column must be re-derived whenever a
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-15629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field that references another model's column borrows that
  column's storage characteristics. The database parameters a relational field
  reports for its own column must therefore include the SAME collation as the
  column it points at — alongside the type and the check it already reported.
  When the referenced column declares no collation, the relational field
  reports no collation either (the two agree on "absent").

  Two consequences are pinned, because two consumers read these parameters:

    (1) Column emission. The storage definition emitted for a column carries an
        explicit collation clause exactly when that column's parameters declare
        a collation. Hence a relational field's column gets a collation clause
        precisely when, and matching, the column it references — so a freshly
        created reference agrees with its target out of the box.

    (2) Re-derivation on change. When an existing referenced column is altered,
        every column referencing it must be re-derived (dropped and rebuilt to
        match) when the referenced column's type or its collation differs
        between the old and new shape.

Modelling choices (Nagini fragment):
  * A column's database parameters are a ``Dict[int, int]`` from a
    parameter-name token (module-level constants: type / check / collation) to
    its abstract value. A key being ABSENT means "this parameter is not reported
    at all"; a key present with the sentinel ``none_value()`` means "declared,
    but empty (no collation)". Absent vs. present-but-equal is an observable
    distinction here, so the carrier separates ``k in d`` membership from
    ``d[k]``.
  * A type / collation identity is an ``int``: ``none_value()`` is "no
    collation"/"no type"; every other int is a distinct identity. Only equality
    and membership are observed (mapping.md §2), so integer identity is faithful
    and ``!=`` is plain integer comparison.

The referenced column's own parameters are read, not mutated; held at fractional
permission. The behaviour is modelled deeply (the dict construction and the
change-decision are spelled out in the impl regions); there is no axiomatised
callee. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: both modeled behaviours are spelled out deeply in the impl
# regions. There is no unchanged opaque callee the proof relies on.
# axioms-end


# pure-start
@Pure
def key_type() -> int:
    # Parameter-name token for the storage type.
    return 1


@Pure
def key_check() -> int:
    # Parameter-name token for the column check.
    return 2


@Pure
def key_collation() -> int:
    # Parameter-name token for the column collation.
    return 3


@Pure
def none_value() -> int:
    # Sentinel value meaning "declared, but empty" (no type / no collation).
    return 0


@Pure
def differs(before: int, after: int) -> bool:
    # Whether a storage characteristic changed between the old and new shape.
    return before != after


@Pure
def emits_collation_clause(params: Dict[int, int]) -> bool:
    """A column's storage definition carries an explicit collation clause
    exactly when its parameters declare a (non-empty) collation: the clause is
    emitted iff the collation key is present AND its value is not the empty
    sentinel."""
    Requires(Acc(dict_pred(params), 1 / 4))
    return key_collation() in params and params[key_collation()] != none_value()
# pure-end


def reported_reference_parameters(target_params: Dict[int, int],
                                  own_type: int,
                                  own_check: int) -> Dict[int, int]:
    # pre-conditions-start
    # The referenced column's parameters are read only (fractional permission).
    Requires(Acc(dict_pred(target_params), 1 / 2))
    # The referenced column reports a collation entry (possibly the empty
    # sentinel).
    Requires(key_collation() in target_params)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(target_params), 1 / 2))
    Ensures(dict_pred(Result()))
    # The reported parameters expose exactly the three expected entries, and
    # each carries the expected value (membership precedes each lookup).
    Ensures(key_type() in Result())
    Ensures(Result()[key_type()] == own_type)
    Ensures(key_check() in Result())
    Ensures(Result()[key_check()] == own_check)
    Ensures(key_collation() in Result())
    # The referenced column still reports its collation entry (read-only).
    Ensures(key_collation() in target_params)
    # (1) The reported collation is exactly the referenced column's collation
    #     — the discriminating clause: same value, and present (not absent).
    Ensures(Result()[key_collation()] == target_params[key_collation()])
    # No spurious entries are reported.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
            k == key_type() or k == key_check() or k == key_collation()))))
    # (1') Consequently the field's column emits a collation clause exactly when
    #      the referenced column does, with the matching value. This is the
    #      property the create-time column emission depends on.
    Ensures(emits_collation_clause(Result())
            == (key_collation() in target_params
                and target_params[key_collation()] != none_value()))
    # post-conditions-end
    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result
    # impl-end


def references_need_rebuild(old_type: int, new_type: int,
                            old_collation: int, new_collation: int) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (2) Columns referencing an altered column must be re-derived whenever a
    #     storage characteristic differs between the old and new shape — its
    #     type OR its collation. The clauses below fully characterise the
    #     decision by cases (complete, so the spec is tight).
    # A type change triggers a rebuild.
    Ensures(Implies(differs(old_type, new_type), Result()))
    # A collation change ALSO triggers a rebuild, including the case where the
    # type is unchanged.
    Ensures(Implies(differs(old_collation, new_collation), Result()))
    # When NEITHER characteristic differs, no rebuild is triggered.
    Ensures(Implies(not differs(old_type, new_type)
                    and not differs(old_collation, new_collation),
                    not Result()))
    # post-conditions-end
    # impl-start
    return differs(old_type, new_type) or differs(old_collation, new_collation)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity) audit of nagini bundle django__django-15629. Project root, SBU_BENCHMARK_DIR=benchmark-verified, verifier python python.

Positive control verified with `bash scripts/nagini_verify.sh atk_pc.py`.

### Results
- atk_pc.py (correct model, copy of model.py): same-spec exit 0; nagini_verify exit 0 (VERIFIED 10.45s). Positive control confirms the spec is NOT vacuously unsat.
- atk_prepatch.py (fn1 omits `result[key_collation()]=target[...]`, the real pre-patch bug): weakness exit 2 = does-not-verify. PREPATCH BUG REPRODUCED (spec senses the regression).
- atk_prepatch2.py (fn2 `return differs(old_type,new_type)` only, real pre-patch bug 2): weakness exit 2 = does-not-verify. PREPATCH BUG 2 REPRODUCED.
- atk_1 (fn1 swaps type/check values): weakness exit 2 (rejected).
- atk_2 (fn1 collation=none_value()): exit 2 (rejected).
- atk_3 (fn1 adds spurious key 99): exit 2 (rejected by no-spurious-key forall).
- atk_4 (fn2 return True, over-approx): exit 2 (rejected by 'neither differs => not Result' clause).
- atk_5 (fn2 and-instead-of-or): exit 2 (rejected).
- atk_6 (fn2 drops type disjunct, partial-domain): exit 2 (rejected).
- atk_7 (fn1 collation=own_type, ungrounded echo): exit 2 (rejected).

All 7 attacks verified to edit ONLY the impl region (spec+contracts byte-identical outside impl-start/impl-end; confirmed by diff). Every `weakness` run printed 'attack does not verify' NOT 'changed the spec', so the same-spec gate held for each — they are genuine same-spec wrong-impls that the spec correctly rejects.

NO CANDIDATE emerged (no same-spec impl both shares spec AND verifies except the correct one), so no faithful refined patch / run_resolve was mandated by the protocol. Root reason the spec is airtight: both modeled functions are FULLY PINNED by their postconditions. reported_reference_parameters: Result determined on the entire domain — key_type()->own_type, key_check()->own_check, key_collation()->target_params[key_collation()], plus Forall no-spurious-key. references_need_rebuild: complete truth table (Result iff type differs OR collation differs, with the neither-differs=>not-Result closing clause). Any verifying impl is therefore extensionally equal to the gold patch on all inputs => resolves.

A-LEG AUDIT (refinement.md / mapping.md): No consumed axiom (kind A-consumed absent by construction). Every leg is R, A-reference, or I — NO kind-3 (unexpressible-changed-op). The two changed ops (FK reporting target collation; re-derive trigger gaining collation disjunct) are modeled DEEPLY in the impl regions, not hidden behind an axiom. The two A-references' correspondence to real callees HOLDS: patch.diff (read at instance root) confirms ForeignKey.db_parameters(related.py:1182) now returns {type,check,collation: target.get('collation')} and BaseDatabaseSchemaEditor._alter_field + sqlite3 guard gain `(old_type!=new_type) or (old_collation!=new_collation)` — exactly the hunks quoted in refinement.md §A/§C and mapping.md §3. axiom_check.py's deep shadows (deep_reported_reference_parameters, deep_references_need_rebuild) mirror model.py's impl regions verbatim and are validated against the real gold-patched Django (6 boundary + 120 fuzz model pairs incl. COLLATE-emission tracking; full 3x3x3x3 identity truth table). emits_collation_clause (§B, A-reference) mirrors the unchanged _iter_column_sql COLLATE branch.

VERDICT: SOUND. ≥5 distinct same-spec wrong impls (7 + 2 prepatch) all rejected by the verifier; positive control verifies; both prepatch bugs reproduced; no verifying wrong impl exists, so verify=>correct holds for this bundle. No resolve run was required because no CANDIDATE was produced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-15629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field that references another model's column borrows that
  column's storage characteristics. The database parameters a relational field
  reports for its own column must therefore include the SAME collation as the
  column it points at — alongside the type and the check it already reported.
  When the referenced column declares no collation, the relational field
  reports no collation either (the two agree on "absent").

  Two consequences are pinned, because two consumers read these parameters:

    (1) Column emission. The storage definition emitted for a column carries an
        explicit collation clause exactly when that column's parameters declare
        a collation. Hence a relational field's column gets a collation clause
        precisely when, and matching, the column it references — so a freshly
        created reference agrees with its target out of the box.

    (2) Re-derivation on change. When an existing referenced column is altered,
        every column referencing it must be re-derived (dropped and rebuilt to
        match) when the referenced column's type or its collation differs
        between the old and new shape.

Modelling choices (Nagini fragment):
  * A column's database parameters are a ``Dict[int, int]`` from a
    parameter-name token (module-level constants: type / check / collation) to
    its abstract value. A key being ABSENT means "this parameter is not reported
    at all"; a key present with the sentinel ``none_value()`` means "declared,
    but empty (no collation)". Absent vs. present-but-equal is an observable
    distinction here, so the carrier separates ``k in d`` membership from
    ``d[k]``.
  * A type / collation identity is an ``int``: ``none_value()`` is "no
    collation"/"no type"; every other int is a distinct identity. Only equality
    and membership are observed (mapping.md §2), so integer identity is faithful
    and ``!=`` is plain integer comparison.

The referenced column's own parameters are read, not mutated; held at fractional
permission. The behaviour is modelled deeply (the dict construction and the
change-decision are spelled out in the impl regions); there is no axiomatised
callee. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: both modeled behaviours are spelled out deeply in the impl
# regions. There is no unchanged opaque callee the proof relies on.
# axioms-end


# pure-start
@Pure
def key_type() -> int:
    # Parameter-name token for the storage type.
    return 1


@Pure
def key_check() -> int:
    # Parameter-name token for the column check.
    return 2


@Pure
def key_collation() -> int:
    # Parameter-name token for the column collation.
    return 3


@Pure
def none_value() -> int:
    # Sentinel value meaning "declared, but empty" (no type / no collation).
    return 0


@Pure
def differs(before: int, after: int) -> bool:
    # Whether a storage characteristic changed between the old and new shape.
    return before != after


@Pure
def emits_collation_clause(params: Dict[int, int]) -> bool:
    """A column's storage definition carries an explicit collation clause
    exactly when its parameters declare a (non-empty) collation: the clause is
    emitted iff the collation key is present AND its value is not the empty
    sentinel."""
    Requires(Acc(dict_pred(params), 1 / 4))
    return key_collation() in params and params[key_collation()] != none_value()
# pure-end


def reported_reference_parameters(target_params: Dict[int, int],
                                  own_type: int,
                                  own_check: int) -> Dict[int, int]:
    # pre-conditions-start
    # The referenced column's parameters are read only (fractional permission).
    Requires(Acc(dict_pred(target_params), 1 / 2))
    # The referenced column reports a collation entry (possibly the empty
    # sentinel).
    Requires(key_collation() in target_params)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(target_params), 1 / 2))
    Ensures(dict_pred(Result()))
    # The reported parameters expose exactly the three expected entries, and
    # each carries the expected value (membership precedes each lookup).
    Ensures(key_type() in Result())
    Ensures(Result()[key_type()] == own_type)
    Ensures(key_check() in Result())
    Ensures(Result()[key_check()] == own_check)
    Ensures(key_collation() in Result())
    # The referenced column still reports its collation entry (read-only).
    Ensures(key_collation() in target_params)
    # (1) The reported collation is exactly the referenced column's collation
    #     — the discriminating clause: same value, and present (not absent).
    Ensures(Result()[key_collation()] == target_params[key_collation()])
    # No spurious entries are reported.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
            k == key_type() or k == key_check() or k == key_collation()))))
    # (1') Consequently the field's column emits a collation clause exactly when
    #      the referenced column does, with the matching value. This is the
    #      property the create-time column emission depends on.
    Ensures(emits_collation_clause(Result())
            == (key_collation() in target_params
                and target_params[key_collation()] != none_value()))
    # post-conditions-end
    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result
    # impl-end


def references_need_rebuild(old_type: int, new_type: int,
                            old_collation: int, new_collation: int) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (2) Columns referencing an altered column must be re-derived whenever a
    #     storage characteristic differs between the old and new shape — its
    #     type OR its collation. The clauses below fully characterise the
    #     decision by cases (complete, so the spec is tight).
    # A type change triggers a rebuild.
    Ensures(Implies(differs(old_type, new_type), Result()))
    # A collation change ALSO triggers a rebuild, including the case where the
    # type is unchanged.
    Ensures(Implies(differs(old_collation, new_collation), Result()))
    # When NEITHER characteristic differs, no rebuild is triggered.
    Ensures(Implies(not differs(old_type, new_type)
                    and not differs(old_collation, new_collation),
                    not Result()))
    # post-conditions-end
    # impl-start
    return differs(old_type, new_type) or differs(old_collation, new_collation)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity) audit of nagini bundle django__django-15629. Project root, SBU_BENCHMARK_DIR=benchmark-verified, verifier python python.

Positive control verified with `bash scripts/nagini_verify.sh atk_pc.py`.

### Results
- atk_pc.py (correct model, copy of model.py): same-spec exit 0; nagini_verify exit 0 (VERIFIED 10.45s). Positive control confirms the spec is NOT vacuously unsat.
- atk_prepatch.py (fn1 omits `result[key_collation()]=target[...]`, the real pre-patch bug): weakness exit 2 = does-not-verify. PREPATCH BUG REPRODUCED (spec senses the regression).
- atk_prepatch2.py (fn2 `return differs(old_type,new_type)` only, real pre-patch bug 2): weakness exit 2 = does-not-verify. PREPATCH BUG 2 REPRODUCED.
- atk_1 (fn1 swaps type/check values): weakness exit 2 (rejected).
- atk_2 (fn1 collation=none_value()): exit 2 (rejected).
- atk_3 (fn1 adds spurious key 99): exit 2 (rejected by no-spurious-key forall).
- atk_4 (fn2 return True, over-approx): exit 2 (rejected by 'neither differs => not Result' clause).
- atk_5 (fn2 and-instead-of-or): exit 2 (rejected).
- atk_6 (fn2 drops type disjunct, partial-domain): exit 2 (rejected).
- atk_7 (fn1 collation=own_type, ungrounded echo): exit 2 (rejected).

All 7 attacks verified to edit ONLY the impl region (spec+contracts byte-identical outside impl-start/impl-end; confirmed by diff). Every `weakness` run printed 'attack does not verify' NOT 'changed the spec', so the same-spec gate held for each — they are genuine same-spec wrong-impls that the spec correctly rejects.

NO CANDIDATE emerged (no same-spec impl both shares spec AND verifies except the correct one), so no faithful refined patch / run_resolve was mandated by the protocol. Root reason the spec is airtight: both modeled functions are FULLY PINNED by their postconditions. reported_reference_parameters: Result determined on the entire domain — key_type()->own_type, key_check()->own_check, key_collation()->target_params[key_collation()], plus Forall no-spurious-key. references_need_rebuild: complete truth table (Result iff type differs OR collation differs, with the neither-differs=>not-Result closing clause). Any verifying impl is therefore extensionally equal to the gold patch on all inputs => resolves.

A-LEG AUDIT (refinement.md / mapping.md): No consumed axiom (kind A-consumed absent by construction). Every leg is R, A-reference, or I — NO kind-3 (unexpressible-changed-op). The two changed ops (FK reporting target collation; re-derive trigger gaining collation disjunct) are modeled DEEPLY in the impl regions, not hidden behind an axiom. The two A-references' correspondence to real callees HOLDS: patch.diff (read at instance root) confirms ForeignKey.db_parameters(related.py:1182) now returns {type,check,collation: target.get('collation')} and BaseDatabaseSchemaEditor._alter_field + sqlite3 guard gain `(old_type!=new_type) or (old_collation!=new_collation)` — exactly the hunks quoted in refinement.md §A/§C and mapping.md §3. axiom_check.py's deep shadows (deep_reported_reference_parameters, deep_references_need_rebuild) mirror model.py's impl regions verbatim and are validated against the real gold-patched Django (6 boundary + 120 fuzz model pairs incl. COLLATE-emission tracking; full 3x3x3x3 identity truth table). emits_collation_clause (§B, A-reference) mirrors the unchanged _iter_column_sql COLLATE branch.

VERDICT: SOUND. ≥5 distinct same-spec wrong impls (7 + 2 prepatch) all rejected by the verifier; positive control verifies; both prepatch bugs reproduced; no verifying wrong impl exists, so verify=>correct holds for this bundle. No resolve run was required because no CANDIDATE was produced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break attack: no divergence found. Two deep-modeled functions, both spelled out (no consumed axiom).

SETUP: worktree is at base_commit 694cf458f16b8d340a3195244196980b2dec34fd with the gold patch applied to the working tree. Model verifies under pinned Nagini (10.53s). axiom_check.py (G-AX) runs green against the gold-patched worktree.

(1) reported_reference_parameters <-> ForeignKey.db_parameters (related.py:1182 gold): real code returns {"type": self.db_type(connection), "check": self.db_check(connection), "collation": target_db_parameters.get("collation")}. Model impl writes exactly type=own_type, check=own_check, collation=target_params[key_collation()], and postconditions pin the 3-entry dict + collation==target collation + emits-COLLATE-iff-target-declares. The precondition `key_collation() in target_params` narrows the domain, but this is a legitimate modeling boundary, NOT a disagreement: the FK's target_field is a CharField/TextField whose db_parameters (fields/__init__.py:1185-1188, 2369-2372) ALWAYS sets db_params["collation"]=self.db_collation (key present, value None when no collation). On that domain, target_params[key_collation()] == .get("collation"), so model output == real output for present-key (incl. none_value<->None). Integer-PK targets (absent key) are excluded by precondition, not mis-modeled. No in-domain input diverges.

(2) references_need_rebuild <-> _alter_field re-derive trigger (base/schema.py:826-833 gold + sqlite3/schema.py:458): model returns differs(old_type,new_type) or differs(old_collation,new_collation) = (old_type!=new_type) or (old_collation!=new_collation), byte-identical to the gold disjunction. Postconditions fully characterize the truth table (type-change=>rebuild, collation-change=>rebuild, neither=>no rebuild). G-AX validates the full 3x3x3x3 grid incl. the discriminating pure-collation-change case. No divergence.

Spec is not too strong: it is exactly the gold post-patch behavior, refined by the documented int/dict abstraction. The only narrowing (collation-key present) is a faithful modeling boundary matching the real FK-target field types, and model_prepatch(_2) correctly FAIL the discriminating postconditions (G-DIFF), so the spec is not spuriously satisfiable by the pre-patch impl. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent audit confirms NO-LEAKAGE. (1) Spec region intact: markers.region_hashes spec_view == recorded e6b71fc0848332e482cf7571806fb8374babb1868aab181c9e6011d547c669a9. (2) Mechanical screen reproduced independently: swebench_unified.leakage.screen(model.py, nagini, gold patch, problem_statement) => passed=True, hard_failures=[], warnings=[]. (3) Spec view is elided model.py only: docstring + pure helpers (key_type/key_check/key_collation/none_value/differs/emits_collation_clause) + pre/post-conditions for reported_reference_parameters and references_need_rebuild; both impl regions replaced by '...'. No patched file path (related.py/base/schema.py/sqlite3/schema.py absent), no patched repo symbol (db_parameters/_alter_field/db_type/db_check/DatabaseFeatures) in any identifier or comment, no gold phrasing ('.get("collation")', 'old_type != new_type'), no diff markers, no bug/fix narration. Auditor artifacts (refinement.md/mapping.md/meta.json) that DO quote gold hunks and name repo symbols are NOT part of the consumer spec view, so they cannot leak. (4) Semantic check: every substantive spec claim is derivable from the PUBLIC problem_statement, not the gold edit. The issue verbatim states 'The collation of the pk must match the collation of the fk otherwise an error will occur', shows the failing vs fixed 'MODIFY ... COLLATE' SQL side by side, and is framed around altering a PK's db_collation and the referencing FK columns. The spec abstracts this into three behavioral facts: reported reference params carry the referenced column's collation alongside type/check; a column emits a collation clause iff its params declare a non-empty collation (create-time consequence); re-derivation triggers when type OR collation differs (alter-time consequence). The 'type OR collation differs' trigger — the detail closest to the specific disjunction edit — is a behavioral consequence a solver infers from the public issue, not a pointer to the repo edit location. Vocabulary is deliberately abstract and never echoes patched symbols/files/diff text; docstring is explicitly 'stated as desired behaviour, not as an edit.' No spec-view line reconstructs the gold edit beyond the public problem_statement. (G-PANEL-2 empty-collation faithfulness fail is a separate, non-leakage concern outside this role.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
