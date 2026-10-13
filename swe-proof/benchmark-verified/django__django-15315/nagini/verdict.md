# P2 adversarial audit — django__django-15315

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,5 +105,9 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
+    # ATTACK: owner-dependent located-value (prepatch bug). Folds owner attrs
+    # into the hash on the attached branch -> violates order-only postcondition.
+    if self.has_owner:
+        return hash_int(self.order + self.owner_label + self.owner_name)
     return hash_int(self.order)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,5 +105,10 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
+    # ATTACK: reads an owner-derived attribute UNCONDITIONALLY (no has_owner
+    # guard). Models the real unguarded self.model._meta.* read that raises
+    # AttributeError on an unattached field. Spec grants that permission only
+    # under has_owner, so this must be rejected for insufficient permission.
+    shadow = self.owner_label  # type: ignore
     return hash_int(self.order)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,5 +105,9 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
+    # ATTACK: diverges instead of returning. Under partial correctness this
+    # would satisfy the postcondition vacuously; MustTerminate(2) must reject it.
+    while True:
+        pass
     return hash_int(self.order)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,5 +105,7 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
-    return hash_int(self.order)
+    # ATTACK: hashes order+1 instead of order (boundary). Result differs from
+    # hash_int(self.order) -> postcondition must reject.
+    return hash_int(self.order + 1)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,5 +105,8 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
-    return hash_int(self.order)
+    # ATTACK: ungrounded constant. Not a function of order -> postcondition
+    # must reject (unless it happens to equal hash_int(self.order), which the
+    # verifier cannot assume for the opaque hash_int).
+    return 0
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,5 +105,11 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
+    # ATTACK (candidate echo): a guarded owner read (the model analogue of the
+    # hasattr(self,'model') guard) whose result is discarded, then the gold
+    # order-only return. Reads owner attrs only under has_owner, so permission
+    # holds; returns hash_int(self.order), so postcondition holds. VERIFIES.
+    if self.has_owner:
+        shadow = self.owner_label + self.owner_name  # type: ignore
     return hash_int(self.order)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,5 +105,10 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
+    # ATTACK: control-flow divergence in value. On the attached branch returns
+    # hash of an owner attribute; else order. Attached-branch result != order
+    # hash -> postcondition must reject.
+    if self.has_owner:
+        return hash_int(self.owner_label)
     return hash_int(self.order)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,5 +105,11 @@
     Ensures(Result() == hash_int(self.order))
     # post-conditions-end
     # impl-start
+    # ATTACK (candidate): distinct verifying shape. Establishes attachment,
+    # touches both owner attrs (guarded, discarded), returns order-only hash.
+    if self.has_owner:
+        a = self.owner_label  # type: ignore
+        b = self.owner_name   # type: ignore
+        c = a + b
     return hash_int(self.order)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A descriptor object owns a constant integer identity assigned once at
  creation (its creation order). It MAY later be attached to an owner class, at
  which point it gains owner-derived attributes (an owning-class label and
  name).

  The required behaviour: the value used to locate the object in a hash-based
  container is a function of the creation-order identity ALONE. It must NOT
  depend on whether the object has been attached to an owner, nor on any
  owner-derived attribute. Consequently the located-value is stable across the
  later attachment of the object to an owner: an object placed in a hash
  container before attachment remains findable in it afterwards.

The descriptor is modelled as a minimal class carrying only the touched
fields: the creation-order identity (``int``), an attachment flag
(``has_owner``), and the two owner-derived attributes that become available
once attached (modelled as ``int`` identities). Crucially, the owner-derived
attributes EXIST only once the object is attached: in the real program an
unattached object simply lacks the owner attribute, and reading it raises an
error. The spec mirrors this by granting read permission on the owner-derived
attributes only under ``has_owner`` — an implementation may observe them only
after establishing attachment. The unchanged standard hashing primitive over a
single integer is axiomatized.

The operation is a bounded, straight-line delegation to that primitive: it
MUST terminate (a total-correctness obligation, carried as MustTerminate in
the precondition). An implementation that diverges — e.g. loops or recurses
forever instead of returning the located-value — would satisfy the value
postconditions only vacuously and would hang every hash-container lookup
(and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Descriptor:
    def __init__(self, order: int, has_owner: bool, owner_label: int,
                 owner_name: int) -> None:
        # The constructor is a bounded sequence of field stores; it carries a
        # termination obligation so callers under their own termination
        # obligation may construct descriptors.
        Requires(MustTerminate(1))
        Ensures(Acc(self.order) and self.order == order)            # type: ignore
        Ensures(Acc(self.has_owner) and self.has_owner == has_owner)  # type: ignore
        Ensures(Acc(self.owner_label) and self.owner_label == owner_label)  # type: ignore
        Ensures(Acc(self.owner_name) and self.owner_name == owner_name)  # type: ignore
        self.order = order
        self.has_owner = has_owner
        self.owner_label = owner_label
        self.owner_name = owner_name

# axioms-start
@Pure
@ContractOnly
def hash_int(value: int) -> int:
    """The unchanged standard hashing primitive applied to a single integer.
    It is a deterministic pure function of that integer alone (Nagini treats a
    @Pure function as deterministic, so the spec need not restate it).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def located_value(self: Descriptor) -> int:
    # pre-conditions-start
    # Read-only: the operation never mutates the descriptor, so only a
    # fractional permission is required (and returned) on every field.
    # The owner-derived attributes exist ONLY once the object is attached
    # (in the real program an unattached object lacks them and reading them
    # raises), so read permission on them is granted only under the
    # attachment flag: an implementation may touch them only after
    # establishing attachment, never unconditionally.
    Requires(Acc(self.order, 1 / 2))
    Requires(Acc(self.has_owner, 1 / 2))
    Requires(Implies(self.has_owner, Acc(self.owner_label, 1 / 2)))
    Requires(Implies(self.has_owner, Acc(self.owner_name, 1 / 2)))
    # Total correctness: the operation is a bounded delegation to the
    # hashing primitive and must TERMINATE. Without this obligation a
    # diverging implementation (infinite loop or unbounded self-recursion)
    # satisfies every value postcondition vacuously yet would hang every
    # hash-container lookup (and the F2P test) forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.order, 1 / 2))
    Ensures(Acc(self.has_owner, 1 / 2))
    Ensures(Implies(self.has_owner, Acc(self.owner_label, 1 / 2)))
    Ensures(Implies(self.has_owner, Acc(self.owner_name, 1 / 2)))
    # The located-value is a function of the creation-order identity ALONE:
    # it is exactly the standard hash of that identity, independent of the
    # attachment flag and of either owner-derived attribute. This is precisely
    # the stability-under-attachment guarantee the behaviour demands.
    Ensures(Result() == hash_int(self.order))
    # post-conditions-end
    # impl-start
    return hash_int(self.order)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

8 same-spec attacks (all byte-identical spec via `same-spec`), run via `python -m swebench_unified.adversary weakness nagini django__django-15315 <atk>` in 3 background batches of ≤3 (JVM+Z3). Rejected-by-spec (does NOT verify): atk_1 prepatch owner-dependent hash (the prepatch bug reproduced faithfully -> fails order-only postcondition); atk_2 unconditional owner-attribute read (rejected for insufficient permission -- the model analogue of the real AttributeError on an unattached field); atk_3 infinite loop (rejected by MustTerminate(2)); atk_4 hash_int(order+1) off-by-one (postcondition); atk_5 constant 0 (postcondition); atk_7 attached-branch returns hash_int(owner_label) (postcondition).

CANDIDATES (share spec AND verify): atk_6 (guarded discarded owner read then order-only return, 18.5s) and atk_8 (guarded read of both owner attrs then order-only return, 17.5s). Per protocol both candidates' faithful refined patches were materialized and RUN through the official harness (run_resolve): atk_6 -> resolved=True completed=True; atk_8 -> resolved=True completed=True. (atk_8's first patch had a miscounted hunk header +542,10 causing a malformed-patch apply error = harness error, NOT a non-resolve; corrected to +542,11 and it resolved.) Positive controls: gold patch.diff resolved=True completed=True; pos_control.py (=model.py) verifies exit 0 in 13.1s.

Both verifying candidates are legitimate guarded-read 'echoes' whose real patches resolve -> NOT weaknesses (consistent with the 2026-08-06 G-PANEL-1 echo policy). No verifying wrong-impl's faithful patch failed to resolve. refinement.md audit: legs A1=R (Field<->Descriptor, creation_counter<->order identity), A2=A-consumed+R (hash_int<->builtin hash on one int; proof consumes only @Pure determinism), A3=I (identical return); NO kind-3 steps; the changed op (hash order alone) is expressed directly by the order-only postcondition. A-consumed axiom correspondence (hash_int <-> hash(int)) and A-reference stability-under-attachment oracle are executably validated by axiom_check.py (20 boundary + 20000 fuzz ints determinism; fixed value invariant, prefix value changes). Correspondence holds. Verdict SOUND after 8 attacks + 2 candidate resolves + gold/verify positive controls all completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A descriptor object owns a constant integer identity assigned once at
  creation (its creation order). It MAY later be attached to an owner class, at
  which point it gains owner-derived attributes (an owning-class label and
  name).

  The required behaviour: the value used to locate the object in a hash-based
  container is a function of the creation-order identity ALONE. It must NOT
  depend on whether the object has been attached to an owner, nor on any
  owner-derived attribute. Consequently the located-value is stable across the
  later attachment of the object to an owner: an object placed in a hash
  container before attachment remains findable in it afterwards.

The descriptor is modelled as a minimal class carrying only the touched
fields: the creation-order identity (``int``), an attachment flag
(``has_owner``), and the two owner-derived attributes that become available
once attached (modelled as ``int`` identities). Crucially, the owner-derived
attributes EXIST only once the object is attached: in the real program an
unattached object simply lacks the owner attribute, and reading it raises an
error. The spec mirrors this by granting read permission on the owner-derived
attributes only under ``has_owner`` — an implementation may observe them only
after establishing attachment. The unchanged standard hashing primitive over a
single integer is axiomatized.

The operation is a bounded, straight-line delegation to that primitive: it
MUST terminate (a total-correctness obligation, carried as MustTerminate in
the precondition). An implementation that diverges — e.g. loops or recurses
forever instead of returning the located-value — would satisfy the value
postconditions only vacuously and would hang every hash-container lookup
(and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Descriptor:
    def __init__(self, order: int, has_owner: bool, owner_label: int,
                 owner_name: int) -> None:
        # The constructor is a bounded sequence of field stores; it carries a
        # termination obligation so callers under their own termination
        # obligation may construct descriptors.
        Requires(MustTerminate(1))
        Ensures(Acc(self.order) and self.order == order)            # type: ignore
        Ensures(Acc(self.has_owner) and self.has_owner == has_owner)  # type: ignore
        Ensures(Acc(self.owner_label) and self.owner_label == owner_label)  # type: ignore
        Ensures(Acc(self.owner_name) and self.owner_name == owner_name)  # type: ignore
        self.order = order
        self.has_owner = has_owner
        self.owner_label = owner_label
        self.owner_name = owner_name

# axioms-start
@Pure
@ContractOnly
def hash_int(value: int) -> int:
    """The unchanged standard hashing primitive applied to a single integer.
    It is a deterministic pure function of that integer alone (Nagini treats a
    @Pure function as deterministic, so the spec need not restate it).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def located_value(self: Descriptor) -> int:
    # pre-conditions-start
    # Read-only: the operation never mutates the descriptor, so only a
    # fractional permission is required (and returned) on every field.
    # The owner-derived attributes exist ONLY once the object is attached
    # (in the real program an unattached object lacks them and reading them
    # raises), so read permission on them is granted only under the
    # attachment flag: an implementation may touch them only after
    # establishing attachment, never unconditionally.
    Requires(Acc(self.order, 1 / 2))
    Requires(Acc(self.has_owner, 1 / 2))
    Requires(Implies(self.has_owner, Acc(self.owner_label, 1 / 2)))
    Requires(Implies(self.has_owner, Acc(self.owner_name, 1 / 2)))
    # Total correctness: the operation is a bounded delegation to the
    # hashing primitive and must TERMINATE. Without this obligation a
    # diverging implementation (infinite loop or unbounded self-recursion)
    # satisfies every value postcondition vacuously yet would hang every
    # hash-container lookup (and the F2P test) forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.order, 1 / 2))
    Ensures(Acc(self.has_owner, 1 / 2))
    Ensures(Implies(self.has_owner, Acc(self.owner_label, 1 / 2)))
    Ensures(Implies(self.has_owner, Acc(self.owner_name, 1 / 2)))
    # The located-value is a function of the creation-order identity ALONE:
    # it is exactly the standard hash of that identity, independent of the
    # attachment flag and of either owner-derived attribute. This is precisely
    # the stability-under-attachment guarantee the behaviour demands.
    Ensures(Result() == hash_int(self.order))
    # post-conditions-end
    # impl-start
    return hash_int(self.order)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

8 same-spec attacks (all byte-identical spec via `same-spec`), run via `python -m swebench_unified.adversary weakness nagini django__django-15315 <atk>` in 3 background batches of ≤3 (JVM+Z3). Rejected-by-spec (does NOT verify): atk_1 prepatch owner-dependent hash (the prepatch bug reproduced faithfully -> fails order-only postcondition); atk_2 unconditional owner-attribute read (rejected for insufficient permission -- the model analogue of the real AttributeError on an unattached field); atk_3 infinite loop (rejected by MustTerminate(2)); atk_4 hash_int(order+1) off-by-one (postcondition); atk_5 constant 0 (postcondition); atk_7 attached-branch returns hash_int(owner_label) (postcondition).

CANDIDATES (share spec AND verify): atk_6 (guarded discarded owner read then order-only return, 18.5s) and atk_8 (guarded read of both owner attrs then order-only return, 17.5s). Per protocol both candidates' faithful refined patches were materialized and RUN through the official harness (run_resolve): atk_6 -> resolved=True completed=True; atk_8 -> resolved=True completed=True. (atk_8's first patch had a miscounted hunk header +542,10 causing a malformed-patch apply error = harness error, NOT a non-resolve; corrected to +542,11 and it resolved.) Positive controls: gold patch.diff resolved=True completed=True; pos_control.py (=model.py) verifies exit 0 in 13.1s.

Both verifying candidates are legitimate guarded-read 'echoes' whose real patches resolve -> NOT weaknesses (consistent with the 2026-08-06 G-PANEL-1 echo policy). No verifying wrong-impl's faithful patch failed to resolve. refinement.md audit: legs A1=R (Field<->Descriptor, creation_counter<->order identity), A2=A-consumed+R (hash_int<->builtin hash on one int; proof consumes only @Pure determinism), A3=I (identical return); NO kind-3 steps; the changed op (hash order alone) is expressed directly by the order-only postcondition. A-consumed axiom correspondence (hash_int <-> hash(int)) and A-reference stability-under-attachment oracle are executably validated by axiom_check.py (20 boundary + 20000 fuzz ints determinism; fixed value invariant, prefix value changes). Correspondence holds. Verdict SOUND after 8 attacks + 2 candidate resolves + gold/verify positive controls all completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** faithfulness-break attacker: no drift found. The bundle models gold-patched Field.__hash__ (django/db/models/fields/__init__.py:544). At base_commit 652c68ff the real callee is the PRE-patch 3-tuple hash((creation_counter, app_label|None, model_name|None)); the gold patch reduces it to `return hash(self.creation_counter)`. The modeled located_value returns hash_int(self.order) == hash(self.creation_counter) under identity refinement (order<->creation_counter, hash_int<->builtin hash, A-consumed determinism only). Checks: (1) Value agreement — modeled result equals the gold callee's result on EVERY field; no distinguishing input exists. (2) Existence-conditioned permissions (Implies(has_owner, Acc(owner_label/owner_name,1/2))) faithfully mirror AttributeError on unattached fields (F2P test_hash_immutability hashes an unattached field first); a guarded read+order-only return remains admitted, so the spec is not over-tightened. (3) MustTerminate(2) is faithful — real hash site is bounded straight-line delegation that always returns. (4) Gold model VERIFIES (Nagini: Verification successful, 16.4s) and same-spec accepts it (exit 0), so the frozen spec admits the faithful gold-equivalent impl and rejects only genuinely non-resolving impls (unconditional owner read errors F2P; divergence hangs it). Spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures). Semantic check: the public problem_statement already fully discloses the fix ('Field.__hash__() should be immutable'; hash 'changes value when a field is assigned to a model class'; 'we can revert the __hash__ change from #31750'), i.e. hash on the invariant creation-time identity alone. The consumer spec view (model.py docstring + spec regions with impl elided) reveals nothing beyond this: no patched file path (django/db/models/fields/__init__.py is abstracted to 'a descriptor object'), no repo symbols (Field/__hash__/creation_counter/app_label/model_name absent — neutral carriers Descriptor/located_value/order/has_owner/owner_label/owner_name used instead), no reproduced gold-diff line, no diff markers, no bug/fix narration. The postcondition Result()==hash_int(self.order) specifies the required behaviour (located-value depends on the creation-order constant alone) which is exactly the immutability guarantee the public task demands — a spec, not an edit leak. The auditor docs mapping.md/refinement.md that name creation_counter, the file path, and the diff are NOT part of the consumer spec view and are out of scope for G-LEAK. Verified spec-region delimiters via markers.spec_view; screen run against the frozen dataset row.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.