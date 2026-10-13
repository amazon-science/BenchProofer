# P2 adversarial audit — pytest-dev__pytest-6197

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_access_noop.py`, `atk2_access_reload_undo.py`, `atk3_enum_load_restore.py`, `atk4_access_uncond.py`, `atk5_access_double.py`, `atk7_enum_flip_restore.py`, `atk8_access_dec_when_loaded.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6_access_reshape.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_access_noop.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,9 +96,7 @@
     Ensures(Implies(not Old(c.loaded), c.load_count == Old(c.load_count) + 1))
     # post-conditions-end
     # impl-start
-    if not c.loaded:
-        c.loaded = True
-        c.load_count = c.load_count + 1
+    pass
     # impl-end
 
 
@@ -128,7 +126,5 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
     pass
     # impl-end
```

Attack 2 — `atk2_access_reload_undo.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,6 +99,9 @@
     if not c.loaded:
         c.loaded = True
         c.load_count = c.load_count + 1
+    else:
+        c.load_count = c.load_count + 1
+        c.load_count = c.load_count - 1
     # impl-end
 
 
@@ -128,7 +131,5 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
     pass
     # impl-end
```

Attack 3 — `atk3_enum_load_restore.py` → rejected (same spec, does not verify — good)

```diff
@@ -128,7 +128,9 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
-    pass
+    if not c.loaded:
+        c.loaded = True
+        c.load_count = c.load_count + 1
+        c.load_count = c.load_count - 1
+        c.loaded = False
     # impl-end
```

Attack 4 — `atk4_access_uncond.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,9 +96,8 @@
     Ensures(Implies(not Old(c.loaded), c.load_count == Old(c.load_count) + 1))
     # post-conditions-end
     # impl-start
-    if not c.loaded:
-        c.loaded = True
-        c.load_count = c.load_count + 1
+    c.load_count = c.load_count + 1
+    c.loaded = True
     # impl-end
 
 
@@ -128,7 +127,5 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
     pass
     # impl-end
```

Attack 5 — `atk5_access_double.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # impl-start
     if not c.loaded:
         c.loaded = True
-        c.load_count = c.load_count + 1
+        c.load_count = c.load_count + 2
     # impl-end
 
 
@@ -128,7 +128,5 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
     pass
     # impl-end
```

Attack 6 — `atk6_access_reshape.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -97,8 +97,8 @@
     # post-conditions-end
     # impl-start
     if not c.loaded:
+        c.load_count = c.load_count + 1
         c.loaded = True
-        c.load_count = c.load_count + 1
     # impl-end
 
 
@@ -128,7 +128,5 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
     pass
     # impl-end
```

Attack 7 — `atk7_enum_flip_restore.py` → rejected (same spec, does not verify — good)

```diff
@@ -128,7 +128,7 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
-    pass
+    if c.loaded:
+        c.loaded = False
+        c.loaded = True
     # impl-end
```

Attack 8 — `atk8_access_dec_when_loaded.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,6 +99,8 @@
     if not c.loaded:
         c.loaded = True
         c.load_count = c.load_count + 1
+    else:
+        c.load_count = c.load_count - 1
     # impl-end
 
 
@@ -128,7 +130,5 @@
     Ensures(c.loaded == Old(c.loaded))
     # post-conditions-end
     # impl-start
-    # Enumeration of children proceeds without touching the container's own
-    # underlying object; no load is triggered here.
     pass
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-6197.

Behaviour under specification (stated as desired behaviour, not as an edit):

A directory-backed test container is discovered in two distinct phases.

  (1) Enumerating the children of such a container (the discovery phase) must
      NOT load the container's own underlying object. Loading that object is an
      observable, possibly-failing side effect; it must be deferred. After the
      enumeration phase returns, the load side effect has happened exactly as
      many times as it had before the phase began (i.e. discovery performs zero
      loads), and the loaded/unloaded status of the container is unchanged.

  (2) Reading the container's underlying object (the access phase) loads it on
      demand: if it has not yet been loaded, exactly one load side effect is
      performed and the container becomes loaded; if it was already loaded, no
      further load happens. After an access the container is always loaded, and
      the access never performs more than one load.

The container is modelled as a minimal class carrying only the two touched
pieces of state: a boolean recording whether its underlying object has been
loaded, and a counter recording how many times the (side-effecting) load
primitive has run. The load primitive that produces the underlying object is
modelled directly as the single state transition that performs one load.

Both phases are bounded, straight-line operations: each MUST terminate and
return (a total-correctness obligation, carried as MustTerminate in the
preconditions). An implementation that diverges would satisfy the value
postconditions only vacuously and would never hand control back to the
test-collection run.

The load side effect is IRREVERSIBLE: once performed it cannot be undone, so
a merely net-unchanged counter is not the specified behaviour. The contracts
therefore grant each phase write permission on the load state only where a
load is legitimately allowed to happen: nowhere during the enumeration phase
(read-only fractional permission), and only on a not-yet-loaded container
during the access phase. Any body that touches the load state outside those
windows — even if it later restores the old values — fails verification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Container:
    def __init__(self) -> None:
        Requires(MustTerminate(1))  # type: ignore
        Ensures(Acc(self.loaded) and Acc(self.load_count))  # type: ignore
        Ensures(self.loaded is False and self.load_count == 0)  # type: ignore
        self.loaded = False        # underlying object not yet loaded
        self.load_count = 0        # number of load side effects performed

# axioms-start
# (no @ContractOnly callee axioms: the load primitive is modelled deeply below
#  as the in-line state transition `loaded := True; load_count += 1`, so the
#  proof consumes no opaque callee. See refinement.md / mapping.md.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def access_object(c: Container) -> None:
    """The on-demand access phase: load the underlying object iff not already
    loaded, then leave the container loaded. At most one load is performed."""
    # pre-conditions-start
    Requires(Acc(c.loaded))
    Requires(Acc(c.load_count, 1/2))
    # The load side effect is irreversible, so write permission on the load
    # counter is granted only in the window where a load may legitimately
    # happen: when the container is not yet loaded. On an already-loaded
    # container the counter is read-only for this phase, so even a
    # transient, later-reverted touch of it cannot verify.
    Requires(Implies(not c.loaded, Acc(c.load_count, 1/2)))
    Requires(c.load_count >= 0)
    # Total correctness: the access phase must terminate and hand back
    # control. A diverging body would satisfy the value postconditions only
    # vacuously (it never returns), which is not the specified behaviour.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.loaded))
    Ensures(Acc(c.load_count, 1/2))
    Ensures(Implies(not Old(c.loaded), Acc(c.load_count, 1/2)))
    # After an access the container is loaded.
    Ensures(c.loaded is True)
    # A load happens exactly once, and only when it had not been loaded before:
    #   - already loaded  -> no further load
    #   - not yet loaded   -> exactly one load
    Ensures(Implies(Old(c.loaded), c.load_count == Old(c.load_count)))
    Ensures(Implies(not Old(c.loaded), c.load_count == Old(c.load_count) + 1))
    # post-conditions-end
    # impl-start
    if not c.loaded:
        c.loaded = True
        c.load_count = c.load_count + 1
    # impl-end

def enumerate_children(c: Container) -> None:
    """The discovery phase: enumerate the container's children WITHOUT loading
    its own underlying object. No load side effect is performed; the
    loaded/unloaded status is preserved."""
    # pre-conditions-start
    # Discovery may READ the container's load state but must never perform
    # (nor transiently perform-and-revert) a load: the load side effect is
    # irreversible, so a net-unchanged counter is not good enough. Read-only
    # fractional permission makes ANY write to the load state — even one
    # later restored to the old value — a verification failure.
    Requires(Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2))
    Requires(c.load_count >= 0)
    # Total correctness: the discovery phase must terminate and hand back
    # control to the collection run. A diverging body would satisfy the
    # "discovery loads nothing" postconditions only vacuously (discovery
    # never finishes), which is not the specified behaviour.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2))
    # The discriminating guarantee: discovery loads nothing.
    Ensures(c.load_count == Old(c.load_count))
    # The loaded/unloaded status is left untouched by discovery.
    Ensures(c.loaded == Old(c.loaded))
    # post-conditions-end
    # impl-start
    # Enumeration of children proceeds without touching the container's own
    # underlying object; no load is triggered here.
    pass
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for pytest-dev__pytest-6197 nagini. project root (invoked with python -m swebench_unified.adversary).

SPEC SHAPE: same_spec elides ONLY the two impl regions; docstring/contracts/permissions/MustTerminate are frozen. Both functions pin the ENTIRE modeled state by value AND restrict WHERE the load-state may be written via fractional permissions: enumerate_children takes read-only Acc(loaded,1/2)+Acc(load_count,1/2) and ensures load_count==Old & loaded==Old; access_object ensures loaded is True, load_count==Old on Old(loaded) branch and Old+1 otherwise, with write perm on load_count granted only under Implies(not loaded,...). MustTerminate(2) on both. axioms region is EMPTY (no @ContractOnly consumed).

8 same-spec attacks built by editing ONLY impl regions (all confirmed SAME by `adversary same-spec`), covering partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, and equivalent-reshape classes.

### RESULTS (exit 0=CANDIDATE shares-spec+verifies; exit 2=rejected):
- positive_control.py (=frozen model.py): EXIT 0 VERIFIES (correct impl verifies).
- atk_prepatch.py (model_prepatch.py, eager-load at head of discovery): EXIT 2 does not verify => PREPATCH BUG REPRODUCED (fails Ensures load_count==Old).
- atk1_access_noop.py (access = pass; partial-domain): EXIT 2 (fails Ensures loaded is True / +1).
- atk2_access_reload_undo.py (already-loaded branch does +1 then -1; control-flow-effect + irreversibility): EXIT 2 (permission: load_count read-only when loaded).
- atk3_enum_load_restore.py (discovery loads then restores loaded & counter): EXIT 2 (read-only 1/2 perm rejects any write).
- atk4_access_uncond.py (unconditional +1; boundary): EXIT 2 (violates Old(loaded)->unchanged / perm).
- atk5_access_double.py (+2; ungrounded magnitude): EXIT 2 (violates +1).
- atk6_access_reshape.py (EQUIVALENT reorder: load_count+=1 then loaded=True inside the not-loaded guard): EXIT 0 VERIFIES => CANDIDATE.
- atk7_enum_flip_restore.py (discovery flips loaded False then True): EXIT 2 (read-only perm).
- atk8_access_dec_when_loaded.py (already-loaded branch does -1; net wrong): EXIT 2 (perm/value).

MANDATORY RESOLVE ON THE ONLY CANDIDATE (atk6): its faithful real rendering is the gold patch verbatim — the model reorder of the two assignments (loaded:=True; load_count+=1) both map to the single real cache-and-load transition `self._obj = obj = self._getobj()`, which has no orderable sub-effect in real code, so the faithful patch is identical to patch.diff. Materialized to atk6_faithful_patch.diff and RAN through the official harness:
  from swebench_unified.harness import run_resolve; run_resolve('pytest-dev__pytest-6197', <atk6_faithful_patch>)
  => RESOLVED: True, COMPLETED: True (log resolve_atk6.txt; a trailing AttributeError on r.summary is cosmetic and printed AFTER the resolved verdict). Per the 2026-08-06 echo-attack policy a same-spec verifying impl whose refined patch RESOLVES is CORRECT, not a weakness. No verify-and-not-resolve witness exists.

REFINEMENT.MD AUDIT (A-legs focus): axioms region empty => no A-consumed, no dead/mislabelled-axiom risk. Legs: A1=R (collector node<->Container, _obj is None<->not loaded, import side effect<->load_count+=1), A2=I+R (deletion of eager _mount_obj_if_needed rendered as absence of load op in enumerate_children; rest of collect R-refined away as it never reads/mounts self.obj), B1=R (obj is None guard <-> not loaded), B2=R+A-reference (deep load transition validated ==real _getobj/_importtestmodule by axiom_check.py/G-AX; NOT a consumed axiom), B3=R (returned identity + marker bookkeeping R-refined away). §C explicitly asserts no kind-3 step; the changed-timing operation is modelled DEEPLY per SPEC_GUIDE §3, correct.

A-reference correspondence holds: axiom_check.py drives REAL pytest over both PATCHED (discovery zero loads on FAIL_TO_PASS + boundary + fuzz; lazy load still surfaces on access) and UNPATCHED (eager load breaks run) trees — a genuine two-state differential, stdlib-only, harness-style invocation. Permission discipline (§C1b/§4) and termination (§C2/§5) are faithful restrictions matching gold behaviour, not tightenings: they reject the load-then-undo/flip-restore/diverge rivals (empirically atk2/atk3/atk7 rejected) while the gold positive control still verifies. All legs are R / A-reference / I — no kind-3, no A-consumed mislabel.

VERDICT: SOUND. >=5 distinct same-spec attacks run; the 7 genuinely-wrong impls all fail verification; the only verifying same-spec impl is an equivalent reshape whose materialized faithful patch RESOLVED under the official harness; prepatch reproduces; positive control verifies; refinement legs all R/A-reference/I with holding A-reference correspondence. No verify-yet-not-resolve counterexample found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_access_noop.py`, `atk2_access_reload_undo.py`, `atk3_enum_load_restore.py`, `atk4_access_uncond.py`, `atk5_access_double.py`, `atk7_enum_flip_restore.py`, `atk8_access_dec_when_loaded.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6_access_reshape.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_access_noop.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_access_reload_undo.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_enum_load_restore.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_access_uncond.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_access_double.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_access_reshape.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7_enum_flip_restore.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_access_dec_when_loaded.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-6197.

Behaviour under specification (stated as desired behaviour, not as an edit):

A directory-backed test container is discovered in two distinct phases.

  (1) Enumerating the children of such a container (the discovery phase) must
      NOT load the container's own underlying object. Loading that object is an
      observable, possibly-failing side effect; it must be deferred. After the
      enumeration phase returns, the load side effect has happened exactly as
      many times as it had before the phase began (i.e. discovery performs zero
      loads), and the loaded/unloaded status of the container is unchanged.

  (2) Reading the container's underlying object (the access phase) loads it on
      demand: if it has not yet been loaded, exactly one load side effect is
      performed and the container becomes loaded; if it was already loaded, no
      further load happens. After an access the container is always loaded, and
      the access never performs more than one load.

The container is modelled as a minimal class carrying only the two touched
pieces of state: a boolean recording whether its underlying object has been
loaded, and a counter recording how many times the (side-effecting) load
primitive has run. The load primitive that produces the underlying object is
modelled directly as the single state transition that performs one load.

Both phases are bounded, straight-line operations: each MUST terminate and
return (a total-correctness obligation, carried as MustTerminate in the
preconditions). An implementation that diverges would satisfy the value
postconditions only vacuously and would never hand control back to the
test-collection run.

The load side effect is IRREVERSIBLE: once performed it cannot be undone, so
a merely net-unchanged counter is not the specified behaviour. The contracts
therefore grant each phase write permission on the load state only where a
load is legitimately allowed to happen: nowhere during the enumeration phase
(read-only fractional permission), and only on a not-yet-loaded container
during the access phase. Any body that touches the load state outside those
windows — even if it later restores the old values — fails verification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Container:
    def __init__(self) -> None:
        Requires(MustTerminate(1))  # type: ignore
        Ensures(Acc(self.loaded) and Acc(self.load_count))  # type: ignore
        Ensures(self.loaded is False and self.load_count == 0)  # type: ignore
        self.loaded = False        # underlying object not yet loaded
        self.load_count = 0        # number of load side effects performed

# axioms-start
# (no @ContractOnly callee axioms: the load primitive is modelled deeply below
#  as the in-line state transition `loaded := True; load_count += 1`, so the
#  proof consumes no opaque callee. See refinement.md / mapping.md.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def access_object(c: Container) -> None:
    """The on-demand access phase: load the underlying object iff not already
    loaded, then leave the container loaded. At most one load is performed."""
    # pre-conditions-start
    Requires(Acc(c.loaded))
    Requires(Acc(c.load_count, 1/2))
    # The load side effect is irreversible, so write permission on the load
    # counter is granted only in the window where a load may legitimately
    # happen: when the container is not yet loaded. On an already-loaded
    # container the counter is read-only for this phase, so even a
    # transient, later-reverted touch of it cannot verify.
    Requires(Implies(not c.loaded, Acc(c.load_count, 1/2)))
    Requires(c.load_count >= 0)
    # Total correctness: the access phase must terminate and hand back
    # control. A diverging body would satisfy the value postconditions only
    # vacuously (it never returns), which is not the specified behaviour.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.loaded))
    Ensures(Acc(c.load_count, 1/2))
    Ensures(Implies(not Old(c.loaded), Acc(c.load_count, 1/2)))
    # After an access the container is loaded.
    Ensures(c.loaded is True)
    # A load happens exactly once, and only when it had not been loaded before:
    #   - already loaded  -> no further load
    #   - not yet loaded   -> exactly one load
    Ensures(Implies(Old(c.loaded), c.load_count == Old(c.load_count)))
    Ensures(Implies(not Old(c.loaded), c.load_count == Old(c.load_count) + 1))
    # post-conditions-end
    # impl-start
    if not c.loaded:
        c.loaded = True
        c.load_count = c.load_count + 1
    # impl-end

def enumerate_children(c: Container) -> None:
    """The discovery phase: enumerate the container's children WITHOUT loading
    its own underlying object. No load side effect is performed; the
    loaded/unloaded status is preserved."""
    # pre-conditions-start
    # Discovery may READ the container's load state but must never perform
    # (nor transiently perform-and-revert) a load: the load side effect is
    # irreversible, so a net-unchanged counter is not good enough. Read-only
    # fractional permission makes ANY write to the load state — even one
    # later restored to the old value — a verification failure.
    Requires(Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2))
    Requires(c.load_count >= 0)
    # Total correctness: the discovery phase must terminate and hand back
    # control to the collection run. A diverging body would satisfy the
    # "discovery loads nothing" postconditions only vacuously (discovery
    # never finishes), which is not the specified behaviour.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2))
    # The discriminating guarantee: discovery loads nothing.
    Ensures(c.load_count == Old(c.load_count))
    # The loaded/unloaded status is left untouched by discovery.
    Ensures(c.loaded == Old(c.loaded))
    # post-conditions-end
    # impl-start
    # Enumeration of children proceeds without touching the container's own
    # underlying object; no load is triggered here.
    pass
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for pytest-dev__pytest-6197 nagini. project root (invoked with python -m swebench_unified.adversary).

SPEC SHAPE: same_spec elides ONLY the two impl regions; docstring/contracts/permissions/MustTerminate are frozen. Both functions pin the ENTIRE modeled state by value AND restrict WHERE the load-state may be written via fractional permissions: enumerate_children takes read-only Acc(loaded,1/2)+Acc(load_count,1/2) and ensures load_count==Old & loaded==Old; access_object ensures loaded is True, load_count==Old on Old(loaded) branch and Old+1 otherwise, with write perm on load_count granted only under Implies(not loaded,...). MustTerminate(2) on both. axioms region is EMPTY (no @ContractOnly consumed).

8 same-spec attacks built by editing ONLY impl regions (all confirmed SAME by `adversary same-spec`), covering partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, and equivalent-reshape classes.

### RESULTS (exit 0=CANDIDATE shares-spec+verifies; exit 2=rejected):
- positive_control.py (=frozen model.py): EXIT 0 VERIFIES (correct impl verifies).
- atk_prepatch.py (model_prepatch.py, eager-load at head of discovery): EXIT 2 does not verify => PREPATCH BUG REPRODUCED (fails Ensures load_count==Old).
- atk1_access_noop.py (access = pass; partial-domain): EXIT 2 (fails Ensures loaded is True / +1).
- atk2_access_reload_undo.py (already-loaded branch does +1 then -1; control-flow-effect + irreversibility): EXIT 2 (permission: load_count read-only when loaded).
- atk3_enum_load_restore.py (discovery loads then restores loaded & counter): EXIT 2 (read-only 1/2 perm rejects any write).
- atk4_access_uncond.py (unconditional +1; boundary): EXIT 2 (violates Old(loaded)->unchanged / perm).
- atk5_access_double.py (+2; ungrounded magnitude): EXIT 2 (violates +1).
- atk6_access_reshape.py (EQUIVALENT reorder: load_count+=1 then loaded=True inside the not-loaded guard): EXIT 0 VERIFIES => CANDIDATE.
- atk7_enum_flip_restore.py (discovery flips loaded False then True): EXIT 2 (read-only perm).
- atk8_access_dec_when_loaded.py (already-loaded branch does -1; net wrong): EXIT 2 (perm/value).

MANDATORY RESOLVE ON THE ONLY CANDIDATE (atk6): its faithful real rendering is the gold patch verbatim — the model reorder of the two assignments (loaded:=True; load_count+=1) both map to the single real cache-and-load transition `self._obj = obj = self._getobj()`, which has no orderable sub-effect in real code, so the faithful patch is identical to patch.diff. Materialized to atk6_faithful_patch.diff and RAN through the official harness:
  from swebench_unified.harness import run_resolve; run_resolve('pytest-dev__pytest-6197', <atk6_faithful_patch>)
  => RESOLVED: True, COMPLETED: True (log resolve_atk6.txt; a trailing AttributeError on r.summary is cosmetic and printed AFTER the resolved verdict). Per the 2026-08-06 echo-attack policy a same-spec verifying impl whose refined patch RESOLVES is CORRECT, not a weakness. No verify-and-not-resolve witness exists.

REFINEMENT.MD AUDIT (A-legs focus): axioms region empty => no A-consumed, no dead/mislabelled-axiom risk. Legs: A1=R (collector node<->Container, _obj is None<->not loaded, import side effect<->load_count+=1), A2=I+R (deletion of eager _mount_obj_if_needed rendered as absence of load op in enumerate_children; rest of collect R-refined away as it never reads/mounts self.obj), B1=R (obj is None guard <-> not loaded), B2=R+A-reference (deep load transition validated ==real _getobj/_importtestmodule by axiom_check.py/G-AX; NOT a consumed axiom), B3=R (returned identity + marker bookkeeping R-refined away). §C explicitly asserts no kind-3 step; the changed-timing operation is modelled DEEPLY per SPEC_GUIDE §3, correct.

A-reference correspondence holds: axiom_check.py drives REAL pytest over both PATCHED (discovery zero loads on FAIL_TO_PASS + boundary + fuzz; lazy load still surfaces on access) and UNPATCHED (eager load breaks run) trees — a genuine two-state differential, stdlib-only, harness-style invocation. Permission discipline (§C1b/§4) and termination (§C2/§5) are faithful restrictions matching gold behaviour, not tightenings: they reject the load-then-undo/flip-restore/diverge rivals (empirically atk2/atk3/atk7 rejected) while the gold positive control still verifies. All legs are R / A-reference / I — no kind-3, no A-consumed mislabel.

VERDICT: SOUND. >=5 distinct same-spec attacks run; the 7 genuinely-wrong impls all fail verification; the only verifying same-spec impl is an equivalent reshape whose materialized faithful patch RESOLVED under the official harness; prepatch reproduces; positive control verifies; refinement legs all R/A-reference/I with holding A-reference correspondence. No verify-yet-not-resolve counterexample found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of pytest-dev__pytest-6197 nagini bundle. Verdict: FAITHFUL — no input drives the modeled functions to disagree with the real repo callees.

### MECHANICAL FACTS (verified live):
- Spec region byte-identical: `same-spec nagini pytest-dev__pytest-6197 <identity-copy>` exits 0 ("SAME — attack shares the bundle's exact specification").
- model.py verifies under pinned Nagini (scripts/nagini_verify.sh): "Verification successful" in 9.81s.
- Discriminator non-vacuous: model_prepatch.py (eager-load transition restored at head of enumerate_children) FAILS verification — permission error at model_prepatch.py:136 (insufficient permission to write c.loaded during discovery, whose contract grants only read-only 1/2 fractional). So the spec genuinely rejects the buggy eager-load body.
- Empirical against the real base_commit worktree and gold-patched copy, driven with `--assert=plain -p no:cacheprovider`: a package with a raising __init__.py + an unrelated top-level test runs to rc=0 on the PATCHED tree (test passes; discovery performs zero loads of the package's own object) and errors with AssertionError during collection (rc=2) on the BASE tree (eager load). This is exactly the model's discriminating observable.

### FAITHFULNESS REASONING (per modeled function):
- enumerate_children ↔ post-patch Package.collect (src/_pytest/python.py, gold deletes the leading self._mount_obj_if_needed()). Postconditions require load_count == Old(load_count) and loaded == Old(loaded). Confirmed against the real patched source: collect's body enumerates children (this_path.visit loop, yields child Modules) and never mounts the package's own _obj. Abstraction _obj-is-None <-> not-loaded and 'one _getobj()/_importtestmodule() execution <-> load_count+=1' matches reality on the tested observable. NOT too strong.
- access_object ↔ post-patch inlined obj getter: `obj = getattr(self,'_obj',None); if obj is None: self._obj = obj = self._getobj(); ...; return obj`. Model: if not loaded -> exactly one load, set loaded; else no-op; ends loaded; <=1 load. Matches the real 'mount only once' guard exactly (the post-patch getter re-reads self.obj for markers only under the obj-is-None branch, still guarded, so no double load). NOT stronger than reality.
- MustTerminate(2)/MustTerminate(1) and the fractional-permission windows are faithful impl-admissibility constraints: real Package.collect (finite directory visit) and the obj getter (at most one import, then return) are bounded computations returning control to the collection loop; the patched collect never writes the package's own import state and the getter writes it only on the fresh path. G-PBT positive controls (pos-access-reshape, pos-enum-readonly, admiss-fresh-container) all verify, showing the admissibility envelope is not over-tight against faithful gold-shaped bodies. Decisively, the gold-faithful impl (model.py itself) VERIFIES — a too-strong spec would reject the faithful gold translation; it does not (G-GOLD pass).

No divergence input exists between the model and the real callees. NOTE: the recorded defect on this bundle is spec-too-WEAK (G-PANEL-1 atk_2_load_then_undo verifies but its patch does not resolve), which is out of scope for this faithfulness (too-strong/drift) gate and does not affect the FAITHFUL verdict here.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (verified directly via leakage.screen with nagini backend: hard_failures=[], no diff markers, no gold-patch line reproduced, patched file/symbols absent from spec view). Semantic review of the consumer spec view (spec_view projection of model.py, impl elided) confirms NO-LEAKAGE beyond the public problem_statement:

1. The public problem_statement already discloses the observable behaviour: pytest 5.2.3 'tries to import any __init__.py file under the current directory' during collection, breaking collection. So the task already tells the solver that discovery must not import/load __init__.py files.

2. The spec view uses ONLY abstract, non-repo names: class Container with fields loaded/load_count, and functions enumerate_children (discovery loads nothing) and access_object (lazy single load). None of the discriminating gold symbols appear: _mount_obj_if_needed, Package.collect, the obj getter, _ALLOW_MARKERS, Module.__init__ — these live only in refinement.md/mapping.md (auditor docs, NOT the consumer spec view). The patched path src/_pytest/python.py does not appear in the spec view.

3. The behavioral guarantee encoded — 'discovery loads nothing; access loads lazily exactly once' — is a faithful abstraction directly implied by the public issue (no eager import of __init__.py during collection). The lazy-access clause is the standard not-a-silent-drop counterpart, expected spec content, not an edit disclosure. It does not name or localize the specific gold edit (which lines to move where).

4. Spec-view comments describe behaviour (irreversibility of the load side effect, termination) with no bug/fix/regression narration (narration screen clean).

The consumer must still map an abstract two-phase load-timing contract back to real pytest code; that mapping burden is inherent to a formal-spec bundle and is not leakage. No RELAXED_LEAKAGE.md present and none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
