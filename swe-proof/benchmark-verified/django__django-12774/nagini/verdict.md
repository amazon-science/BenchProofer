# P2 adversarial audit — django__django-12774

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8_recurse.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,26 +99,6 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
-    i = 0
-    found = False
-    while i < len(guarantees):
-        # invariants-start
-        Invariant(Acc(list_pred(guarantees), 1 / 2))
-        Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
-        Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
-        if permits_alone(guarantees[i], field_name):
-            found = True
-        i = i + 1
-    return not found
+    # BUG: never consults the declared guarantees (pre-patch behaviour).
+    return True
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,26 +99,8 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
-    i = 0
-    found = False
-    while i < len(guarantees):
-        # invariants-start
-        Invariant(Acc(list_pred(guarantees), 1 / 2))
-        Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
-        Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
-        if permits_alone(guarantees[i], field_name):
-            found = True
-        i = i + 1
-    return not found
+    # BUG: only checks the FIRST declared guarantee, ignoring the rest.
+    if len(guarantees) > 0 and permits_alone(guarantees[0], field_name):
+        return False
+    return True
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,24 +99,12 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
     i = 0
     found = False
-    while i < len(guarantees):
-        # invariants-start
+    while i < len(guarantees) - 1:
         Invariant(Acc(list_pred(guarantees), 1 / 2))
         Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
         Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
         if permits_alone(guarantees[i], field_name):
             found = True
         i = i + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,26 +99,9 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
-    i = 0
-    found = False
-    while i < len(guarantees):
-        # invariants-start
+    # BUG: never delivers the decision on this path (non-terminating loop).
+    while True:
         Invariant(Acc(list_pred(guarantees), 1 / 2))
-        Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
-        Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
-        if permits_alone(guarantees[i], field_name):
-            found = True
-        i = i + 1
-    return not found
+        pass
+    return True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,25 +99,14 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
     i = 0
     found = False
     while i < len(guarantees):
-        # invariants-start
         Invariant(Acc(list_pred(guarantees), 1 / 2))
         Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
         Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
-        if permits_alone(guarantees[i], field_name):
+        # BUG: drops the g[0] unconditional check.
+        if len(guarantees[i][1]) == 1 and guarantees[i][1][0] == field_name:
             found = True
         i = i + 1
     return not found
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,26 +97,13 @@
     # impl-start
     if field_name == PK:
         return False
-    if field_unique:
-        return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
+    # BUG: does not early-accept an individually-unique field.
     i = 0
     found = False
     while i < len(guarantees):
-        # invariants-start
         Invariant(Acc(list_pred(guarantees), 1 / 2))
         Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
         Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
         if permits_alone(guarantees[i], field_name):
             found = True
         i = i + 1
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,26 +99,15 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
     i = 0
     found = False
     while i < len(guarantees):
-        # invariants-start
         Invariant(Acc(list_pred(guarantees), 1 / 2))
         Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
         Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
         if permits_alone(guarantees[i], field_name):
             found = True
         i = i + 1
-    return not found
+    # BUG: returns the found flag directly (inverted decision).
+    return found
     # impl-end
```

Attack 8 — `atk_8_recurse.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,26 +99,6 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
-    i = 0
-    found = False
-    while i < len(guarantees):
-        # invariants-start
-        Invariant(Acc(list_pred(guarantees), 1 / 2))
-        Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
-        Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
-        if permits_alone(guarantees[i], field_name):
-            found = True
-        i = i + 1
-    return not found
+    # Prior BROKEN counterexample: unbounded self-recursion on this path.
+    return should_reject(field_name, field_unique, guarantees)
     # impl-end
```

Attack 9 — `atk_9_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -99,26 +99,15 @@
         return False
     if field_unique:
         return False
-    # Scan the declared guarantees for one that makes this field acceptable on
-    # its own (unconditional and ranging over this single field).
     i = 0
-    found = False
     while i < len(guarantees):
-        # invariants-start
         Invariant(Acc(list_pred(guarantees), 1 / 2))
         Invariant(0 <= i and i <= len(guarantees))
-        # `found` records whether any guarantee in the scanned prefix permits
-        # the field; while it is still False the suffix from i on decides the
-        # full answer (front-recursive unfold links any_permits at 0 and at i).
-        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
-            any_permits(guarantees, i, field_name)))
-        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(guarantees) - i.
+        Invariant(Implies(any_permits(guarantees, 0, field_name) !=
+            any_permits(guarantees, i, field_name), False))
         Invariant(MustTerminate(len(guarantees) - i))
-        # invariants-end
         if permits_alone(guarantees[i], field_name):
-            found = True
+            return False
         i = i + 1
-    return not found
+    return True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12774.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A bulk-lookup helper accepts a lookup field and must accept exactly those
  fields whose value identifies at most one row. It rejects a field (by
  signalling an error) unless AT LEAST ONE of the following holds:

    (1) the field is the primary-key field; or
    (2) the field is individually unique on its own; or
    (3) the field is the SOLE member of an UNCONDITIONAL uniqueness guarantee
        declared on the model (a uniqueness guarantee that applies to every row,
        not one restricted by a condition, and that ranges over that one field
        alone).

  A uniqueness guarantee that is conditional (applies only to a subset of rows)
  or that ranges over several fields together does NOT make any one of its
  fields acceptable on its own; such a field is still rejected unless it also
  satisfies (1) or (2).

Field names are modelled as integer identities (distinct names <-> distinct
integers; the primary-key field is the distinguished identity ``PK``). A
declared uniqueness guarantee is reduced to its two touched attributes carried
as an immutable value pair: ``g[0]`` is True iff it is unconditional, and
``g[1]`` is the (pure) sequence of field identities it ranges over. The decision
is a pure predicate over these; the helper signals rejection by returning
``True``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


PK = 0  # the distinguished primary-key field identity


# axioms-start
# (no @ContractOnly callee axioms: the field's own uniqueness flag and the
#  declared-guarantee list are passed in as data; the unconditional-guarantee
#  filter and the single-field extraction are modelled deeply below.)
# axioms-end


# pure-start
@Pure
def permits_alone(g: Tuple[bool, PSeq[int]], field_name: int) -> bool:
    """Whether the declared guarantee ``g`` makes ``field_name`` acceptable on
    its own: it must be unconditional (``g[0]``) AND range over ``field_name``
    as its sole field (``g[1]`` has length 1 and that single field is
    ``field_name``). Conditional or multi-field guarantees never permit a field
    alone."""
    return g[0] and len(g[1]) == 1 and g[1][0] == field_name


@Pure
def any_permits(guarantees: List[Tuple[bool, PSeq[int]]], idx: int,
                field_name: int) -> bool:
    """Whether SOME declared guarantee from position ``idx`` onward makes
    ``field_name`` acceptable on its own. Front-recursive so a single unfold is
    available per loop step."""
    Requires(Acc(list_pred(guarantees), 1 / 4))
    Requires(0 <= idx and idx <= len(guarantees))
    if idx == len(guarantees):
        return False
    return permits_alone(guarantees[idx], field_name) or \
        any_permits(guarantees, idx + 1, field_name)
# pure-end


def should_reject(field_name: int, field_unique: bool,
                  guarantees: List[Tuple[bool, PSeq[int]]]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(guarantees), 1 / 2))
    # The decision must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition only
    # vacuously by never returning (the scan over the finite guarantee list is
    # bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(guarantees), 1 / 2))
    # The field is rejected exactly when it is neither the primary key, nor
    # individually unique, nor made acceptable on its own by any declared
    # unconditional single-field guarantee.
    Ensures(Result() == (
        field_name != PK and
        not field_unique and
        not any_permits(guarantees, 0, field_name)))
    # A primary-key or individually-unique field is always accepted.
    Ensures(Implies(field_name == PK or field_unique, not Result()))
    # A field that is the sole member of some unconditional guarantee is
    # accepted even if it is neither the primary key nor individually unique.
    Ensures(Implies(any_permits(guarantees, 0, field_name), not Result()))
    # post-conditions-end
    # impl-start
    if field_name == PK:
        return False
    if field_unique:
        return False
    # Scan the declared guarantees for one that makes this field acceptable on
    # its own (unconditional and ranging over this single field).
    i = 0
    found = False
    while i < len(guarantees):
        # invariants-start
        Invariant(Acc(list_pred(guarantees), 1 / 2))
        Invariant(0 <= i and i <= len(guarantees))
        # `found` records whether any guarantee in the scanned prefix permits
        # the field; while it is still False the suffix from i on decides the
        # full answer (front-recursive unfold links any_permits at 0 and at i).
        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
            any_permits(guarantees, i, field_name)))
        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(guarantees) - i.
        Invariant(MustTerminate(len(guarantees) - i))
        # invariants-end
        if permits_alone(guarantees[i], field_name):
            found = True
        i = i + 1
    return not found
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Ran 9 same-spec attacks (all confirmed byte-identical spec signature via `adversary same-spec` exit 0; only the impl region — invariants included — was edited). Positive control (gold impl, pos_control.py) VERIFIES (12.7s). Prepatch bug reproduced and rejected.

SETUP: env, SBU_BENCHMARK_DIR=benchmark-verified, PYTHONPATH=src, python=python. Commands: `python -m swebench_unified.adversary weakness|verify|same-spec nagini django__django-12774 <atk>`; resolve via harness.run_resolve. Weakness runs launched in parallel background batches of <=3 (each spawns a JVM+Z3).

SPEC SHAPE (why sound): the postcondition pins the decision EXACTLY over a TOTAL domain — Ensures(Result() == (field_name != PK and not field_unique and not any_permits(guarantees,0,field_name))) plus two Implies clauses — AND the precondition now carries Requires(MustTerminate(2)). So any TERMINATING wrong impl fails the postcondition, and any non-terminating impl fails the obligation-leak check. No verify-but-wrong escape survives.

### ATTACKS (weakness exit / verify failure):
- atk_1 prepatch (ignore guarantees, return True): exit 2; Postcondition of should_reject might not hold.
- atk_2 partial-domain (check only guarantees[0]): exit 2; Postcondition fails.
- atk_3 boundary off-by-one (scan while i<len-1, misses last): exit 2; Postcondition fails.
- atk_4 control-flow-effect (frozen `while True: pass`): exit 2; 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.'
- atk_5 ungrounded-oracle echo (drops g[0] unconditional flag -> would accept a conditional single-field constraint): exit 2; Postcondition fails.
- atk_6 drop conjunct (no field_unique early-accept): exit 2; Postcondition fails.
- atk_7 inverted result (return found not `not found`): exit 2; Postcondition fails.
- atk_8_recurse THE PRIOR DECISIVE COUNTEREXAMPLE (self-recursion `return should_reject(field_name, field_unique, guarantees)` on the non-pk/non-unique path — this is exactly the atk8_recurse that a prior pass used to record meta.json G-EQ=fail/BROKEN at Aug 13 00:00): exit 2; 'Obligation leak check failed. Callee should_reject might not take all unsatisfied obligations from the caller.' The prior break is REPAIRED — model.py (Aug 13 01:35) added Requires(MustTerminate(2)) + the loop's decreasing measure Invariant(MustTerminate(len(guarantees)-i)), which is the Source-2 fix (strengthen spec to constrain termination). Re-encoding the named counterexample against the CURRENT frozen spec confirms it no longer verifies.
- atk_9_echo correct echo (early-return-False on first permitting guarantee, else True — behaviorally identical to the gold decision): CANDIDATE (verifies, 12.7s). MANDATORY resolve run performed: its faithful refined patch = the gold patch (early-return-on-found is behaviorally identical to `field_name not in unique_fields`). run_resolve(run_id sbueq_atk9echo): RESOLVED=True, COMPLETED=True, F2P test_in_bulk_meta_constraint in FAIL_TO_PASS.success (0 failures). So the only verifying candidate is a correct echo whose materialized patch RESOLVES — NOT a weakness. Log: resolve_atk_9_echo.out.

A-LEG AUDIT (refinement.md): axioms region is EMPTY — no consumed @ContractOnly axioms. A2 (field_unique <-> opts.get_field(field_name).unique) and A3 (any_permits/permits_alone deep model <-> total_unique_constraints single-field extraction + `field_name not in unique_fields` membership) are A-references, validated by axiom_check.py (recorded G-AX=pass, 'deep model agrees with the real Django guard' across single-field-unconditional / conditional(partial) / composite / unique=True configs; I read axiom_check.py and confirmed it executes the REAL callees and asserts reject_real==reject_model on every observation). A1 (R: str<->int name identity, 'pk'<->PK) and A4 (I: raise <-> return True decision) hold. No kind-3 (unexpressible-changed-op) leg — the genuinely-changed op (the new third conjunct) is modeled DEEPLY as an A-reference. Model<->patch correspondence holds.

CONCLUSION: >=5 distinct wrong impls run (9 total, including the prior named BROKEN counterexample); none is a verifying-wrong impl whose faithful patch fails to resolve. verify => correct holds for this frozen spec. NOTE: meta.json still records the STALE pre-fix G-EQ=fail/G-PANEL-1=fail (recorded 00:00, before the 01:35 MustTerminate repair) — a re-audit will flip it to pass.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8_recurse.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_recurse.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12774.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A bulk-lookup helper accepts a lookup field and must accept exactly those
  fields whose value identifies at most one row. It rejects a field (by
  signalling an error) unless AT LEAST ONE of the following holds:

    (1) the field is the primary-key field; or
    (2) the field is individually unique on its own; or
    (3) the field is the SOLE member of an UNCONDITIONAL uniqueness guarantee
        declared on the model (a uniqueness guarantee that applies to every row,
        not one restricted by a condition, and that ranges over that one field
        alone).

  A uniqueness guarantee that is conditional (applies only to a subset of rows)
  or that ranges over several fields together does NOT make any one of its
  fields acceptable on its own; such a field is still rejected unless it also
  satisfies (1) or (2).

Field names are modelled as integer identities (distinct names <-> distinct
integers; the primary-key field is the distinguished identity ``PK``). A
declared uniqueness guarantee is reduced to its two touched attributes carried
as an immutable value pair: ``g[0]`` is True iff it is unconditional, and
``g[1]`` is the (pure) sequence of field identities it ranges over. The decision
is a pure predicate over these; the helper signals rejection by returning
``True``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


PK = 0  # the distinguished primary-key field identity


# axioms-start
# (no @ContractOnly callee axioms: the field's own uniqueness flag and the
#  declared-guarantee list are passed in as data; the unconditional-guarantee
#  filter and the single-field extraction are modelled deeply below.)
# axioms-end


# pure-start
@Pure
def permits_alone(g: Tuple[bool, PSeq[int]], field_name: int) -> bool:
    """Whether the declared guarantee ``g`` makes ``field_name`` acceptable on
    its own: it must be unconditional (``g[0]``) AND range over ``field_name``
    as its sole field (``g[1]`` has length 1 and that single field is
    ``field_name``). Conditional or multi-field guarantees never permit a field
    alone."""
    return g[0] and len(g[1]) == 1 and g[1][0] == field_name


@Pure
def any_permits(guarantees: List[Tuple[bool, PSeq[int]]], idx: int,
                field_name: int) -> bool:
    """Whether SOME declared guarantee from position ``idx`` onward makes
    ``field_name`` acceptable on its own. Front-recursive so a single unfold is
    available per loop step."""
    Requires(Acc(list_pred(guarantees), 1 / 4))
    Requires(0 <= idx and idx <= len(guarantees))
    if idx == len(guarantees):
        return False
    return permits_alone(guarantees[idx], field_name) or \
        any_permits(guarantees, idx + 1, field_name)
# pure-end


def should_reject(field_name: int, field_unique: bool,
                  guarantees: List[Tuple[bool, PSeq[int]]]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(guarantees), 1 / 2))
    # The decision must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition only
    # vacuously by never returning (the scan over the finite guarantee list is
    # bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(guarantees), 1 / 2))
    # The field is rejected exactly when it is neither the primary key, nor
    # individually unique, nor made acceptable on its own by any declared
    # unconditional single-field guarantee.
    Ensures(Result() == (
        field_name != PK and
        not field_unique and
        not any_permits(guarantees, 0, field_name)))
    # A primary-key or individually-unique field is always accepted.
    Ensures(Implies(field_name == PK or field_unique, not Result()))
    # A field that is the sole member of some unconditional guarantee is
    # accepted even if it is neither the primary key nor individually unique.
    Ensures(Implies(any_permits(guarantees, 0, field_name), not Result()))
    # post-conditions-end
    # impl-start
    if field_name == PK:
        return False
    if field_unique:
        return False
    # Scan the declared guarantees for one that makes this field acceptable on
    # its own (unconditional and ranging over this single field).
    i = 0
    found = False
    while i < len(guarantees):
        # invariants-start
        Invariant(Acc(list_pred(guarantees), 1 / 2))
        Invariant(0 <= i and i <= len(guarantees))
        # `found` records whether any guarantee in the scanned prefix permits
        # the field; while it is still False the suffix from i on decides the
        # full answer (front-recursive unfold links any_permits at 0 and at i).
        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
            any_permits(guarantees, i, field_name)))
        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(guarantees) - i.
        Invariant(MustTerminate(len(guarantees) - i))
        # invariants-end
        if permits_alone(guarantees[i], field_name):
            found = True
        i = i + 1
    return not found
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Ran 9 same-spec attacks (all confirmed byte-identical spec signature via `adversary same-spec` exit 0; only the impl region — invariants included — was edited). Positive control (gold impl, pos_control.py) VERIFIES (12.7s). Prepatch bug reproduced and rejected.

SETUP: env, SBU_BENCHMARK_DIR=benchmark-verified, PYTHONPATH=src, python=python. Commands: `python -m swebench_unified.adversary weakness|verify|same-spec nagini django__django-12774 <atk>`; resolve via harness.run_resolve. Weakness runs launched in parallel background batches of <=3 (each spawns a JVM+Z3).

SPEC SHAPE (why sound): the postcondition pins the decision EXACTLY over a TOTAL domain — Ensures(Result() == (field_name != PK and not field_unique and not any_permits(guarantees,0,field_name))) plus two Implies clauses — AND the precondition now carries Requires(MustTerminate(2)). So any TERMINATING wrong impl fails the postcondition, and any non-terminating impl fails the obligation-leak check. No verify-but-wrong escape survives.

### ATTACKS (weakness exit / verify failure):
- atk_1 prepatch (ignore guarantees, return True): exit 2; Postcondition of should_reject might not hold.
- atk_2 partial-domain (check only guarantees[0]): exit 2; Postcondition fails.
- atk_3 boundary off-by-one (scan while i<len-1, misses last): exit 2; Postcondition fails.
- atk_4 control-flow-effect (frozen `while True: pass`): exit 2; 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.'
- atk_5 ungrounded-oracle echo (drops g[0] unconditional flag -> would accept a conditional single-field constraint): exit 2; Postcondition fails.
- atk_6 drop conjunct (no field_unique early-accept): exit 2; Postcondition fails.
- atk_7 inverted result (return found not `not found`): exit 2; Postcondition fails.
- atk_8_recurse THE PRIOR DECISIVE COUNTEREXAMPLE (self-recursion `return should_reject(field_name, field_unique, guarantees)` on the non-pk/non-unique path — this is exactly the atk8_recurse that a prior pass used to record meta.json G-EQ=fail/BROKEN at Aug 13 00:00): exit 2; 'Obligation leak check failed. Callee should_reject might not take all unsatisfied obligations from the caller.' The prior break is REPAIRED — model.py (Aug 13 01:35) added Requires(MustTerminate(2)) + the loop's decreasing measure Invariant(MustTerminate(len(guarantees)-i)), which is the Source-2 fix (strengthen spec to constrain termination). Re-encoding the named counterexample against the CURRENT frozen spec confirms it no longer verifies.
- atk_9_echo correct echo (early-return-False on first permitting guarantee, else True — behaviorally identical to the gold decision): CANDIDATE (verifies, 12.7s). MANDATORY resolve run performed: its faithful refined patch = the gold patch (early-return-on-found is behaviorally identical to `field_name not in unique_fields`). run_resolve(run_id sbueq_atk9echo): RESOLVED=True, COMPLETED=True, F2P test_in_bulk_meta_constraint in FAIL_TO_PASS.success (0 failures). So the only verifying candidate is a correct echo whose materialized patch RESOLVES — NOT a weakness. Log: resolve_atk_9_echo.out.

A-LEG AUDIT (refinement.md): axioms region is EMPTY — no consumed @ContractOnly axioms. A2 (field_unique <-> opts.get_field(field_name).unique) and A3 (any_permits/permits_alone deep model <-> total_unique_constraints single-field extraction + `field_name not in unique_fields` membership) are A-references, validated by axiom_check.py (recorded G-AX=pass, 'deep model agrees with the real Django guard' across single-field-unconditional / conditional(partial) / composite / unique=True configs; I read axiom_check.py and confirmed it executes the REAL callees and asserts reject_real==reject_model on every observation). A1 (R: str<->int name identity, 'pk'<->PK) and A4 (I: raise <-> return True decision) hold. No kind-3 (unexpressible-changed-op) leg — the genuinely-changed op (the new third conjunct) is modeled DEEPLY as an A-reference. Model<->patch correspondence holds.

CONCLUSION: >=5 distinct wrong impls run (9 total, including the prior named BROKEN counterexample); none is a verifying-wrong impl whose faithful patch fails to resolve. verify => correct holds for this frozen spec. NOTE: meta.json still records the STALE pre-fix G-EQ=fail/G-PANEL-1=fail (recorded 00:00, before the 01:35 MustTerminate repair) — a re-audit will flip it to pass.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attempt FAILED: the modeled should_reject agrees with the real repo guard on every constructible input. Model decision: reject <=> field_name != PK and not field_unique and not any_permits(guarantees,0,field_name). Real guard (django/db/models/query.py in_bulk @ base_commit 67f9d076): raise ValueError <=> field_name != 'pk' and not opts.get_field(field_name).unique and field_name not in unique_fields, where unique_fields = [c.fields[0] for c in opts.total_unique_constraints if len(c.fields)==1].

Correspondence verified: (1) any_permits == 'field is sole field of some single-field unconditional constraint' == 'field_name in unique_fields' (total_unique_constraints already filters condition is None, so every encoded g[0]=True); ¬any_permits <=> field_name not in unique_fields. (2) field_unique bridges to the REAL opts.get_field(fn).unique (conformance reads it live per observation). (3) pk collapse: both 'pk' literal and opts.pk.name are accepted by real (pk is unique) and by model (PK early-return) — same outcome. (4) conditional (condition is not None) and composite (len(fields)>1) constraints are excluded by BOTH the real len==1/condition-is-None filter and permits_alone; the model even carries the g[0] flag so it can represent AND correctly reject a conditional element — this makes the model strictly MORE general, never spec-too-strong.

Empirical confirmation against the REAL patched repo: axiom_check.py re-run against the live worktree -> G-AX OK, 20/20 observations agree (single-field-unconditional F2P 'year', partial/conditional, multi-field composite, unique=True). conformance_check.py (recorded meta.json): 100006 inputs, 0 disagreements, seed 12774. same-spec of current model.py exit 0; nagini_verify.sh -> Verification successful (10.9s).

Type-abstraction fidelity: the guard uses only name EQUALITY (field_name!='pk', field_name not in unique_fields, constraint.fields[0]==field_name), so the injective str->int name encoding and the 'pk'/pk.name->PK collapse are faithful; UniqueConstraint->(condition is None, fields) captures exactly the two touched attributes. Edge probe: single-field unique_together (not a UniqueConstraint) is NOT consulted by the real guard and NOT modeled as a guarantee — no divergence.

Note on prior recorded Role-1/Panel-1 fails: those were a TERMINATION weakness (verify⇏correct via a non-terminating same-spec impl, atk8_recurse) because the original spec lacked MustTerminate. The current repaired model.py carries Requires(MustTerminate(2)) + a decreasing loop measure, closing that escape. That is a strengthening of the spec and is orthogonal to faithfulness; it does not make the spec too strong (the postcondition value-equality with the real decision is unchanged and still exact). No spec-too-strong / drift defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (module docstring + type/PK declarations + axioms note + pure permits_alone/any_permits + should_reject pre/post-conditions; impl region elided, refinement.md/mapping.md excluded) does NOT leak the gold edit beyond the public problem_statement. Verified programmatically: the spec view contains NO Django/repo-specific tokens (no in_bulk, UniqueConstraint, total_unique_constraints, get_field, _meta, opts, unique_fields, query.py, 'condition is None', or the guard hunk). It restates behavior in fully abstracted, repo-agnostic terms (a 'bulk-lookup helper' rejecting a 'lookup field' unless (1) primary key, (2) individually unique, or (3) sole member of an unconditional uniqueness guarantee; field names as int identities, constraints as Tuple[bool unconditional-flag, PSeq[int] field-ids]). The public problem_statement already discloses the full behavioral goal: title 'Allow QuerySet.in_bulk() for fields with total UniqueConstraints' ('total' is Django's own term for unconditional constraints), a concrete single-field example (UniqueConstraint(fields=["slug"])), the ValueError failure mode, and the existing unique=True path. The (3) unconditional + single-field discriminators and the conditional/multi-field exclusions are behavioral pinning implied by the public 'total' term + single-field slug example, not code-shape disclosure. The actual edit detail (unique_fields comprehension, total_unique_constraints filter, guard hunk) lives only in the auditor artifacts mapping.md/refinement.md, outside the solver-facing spec view. Mechanical G-LEAK (lexical) also passes ('spec view clean'). Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
