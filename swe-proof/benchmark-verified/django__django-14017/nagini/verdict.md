# P2 adversarial audit — django__django-14017

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,18 +138,12 @@
     Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)
     # post-conditions-end
     # impl-start
-    if not (other_is_container or other_is_boolean_operand):
+    # prepatch bug echo: rejects any non-container, ignoring boolean-operand.
+    if not other_is_container:
         raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
     if other_empty:
         return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
     elif self_empty:
         return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+    return Combined(2, conn)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,18 +138,11 @@
     Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)
     # post-conditions-end
     # impl-start
-    if not (other_is_container or other_is_boolean_operand):
+    if not (other_is_container and other_is_boolean_operand):
         raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
     if other_empty:
         return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
     elif self_empty:
         return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+    return Combined(2, conn)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -140,16 +140,9 @@
     # impl-start
     if not (other_is_container or other_is_boolean_operand):
         raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
-    if other_empty:
+    if self_empty:
+        return Combined(1, conn)
+    elif other_empty:
         return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
-    elif self_empty:
-        return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+    return Combined(2, conn)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -140,16 +140,9 @@
     # impl-start
     if not (other_is_container or other_is_boolean_operand):
         raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
     if other_empty:
         return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
     elif self_empty:
         return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+    return Combined(2, conn + 1)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -140,16 +140,10 @@
     # impl-start
     if not (other_is_container or other_is_boolean_operand):
         raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
     if other_empty:
         return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
     elif self_empty:
         return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+    while True:
+        pass
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,18 +138,9 @@
     Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)
     # post-conditions-end
     # impl-start
-    if not (other_is_container or other_is_boolean_operand):
-        raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
     if other_empty:
         return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
     elif self_empty:
         return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+    return Combined(2, conn)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -140,16 +140,9 @@
     # impl-start
     if not (other_is_container or other_is_boolean_operand):
         raise OperandTypeRejected()
-
-    # If the operand is empty, ignore it and just use the container (a copy).
     if other_empty:
-        return Combined(0, conn)
-    # Or if the container is empty, ignore it and just use the operand (a copy).
+        return Combined(0, conn + 12345)
     elif self_empty:
-        return Combined(1, conn)
-
-    # Both sides non-empty: a fresh container under the requested connector,
-    # joining the container and the operand.
-    obj = Combined(2, conn)
-    return obj
+        return Combined(1, conn - 999)
+    return Combined(2, conn)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for django__django-14017.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logical-filter container combines itself with another operand under a
  boolean connector (conjunction or disjunction). The combination must accept
  an operand that is EITHER another container of the same kind OR any object
  that is itself usable directly as a boolean filter condition (a
  boolean-valued operand) — the two are interchangeable as boolean operands and
  the combination is therefore symmetric on such a pair. Only an operand that is
  neither — one that is not a same-kind container AND is not usable as a boolean
  filter condition — is rejected, with a single uniform type-rejection failure
  to the caller.

  When the operand is acceptable, the combination returns normally. The empty
  container is the identity element of both connectors: combining an empty
  operand yields a copy of the container, and combining into an empty container
  yields a copy of the operand. When both sides are non-empty the result is a
  fresh container carrying the requested connector with both operands joined
  under it. The connector of the merged result is exactly the requested one.

  The behaviour pinned here is the ACCEPTANCE decision: an operand that is
  usable directly as a boolean filter condition must be accepted (no rejection)
  exactly as a same-kind container is, and only an operand that is neither a
  same-kind container nor a boolean filter condition is rejected. Whether the
  connector is conjunction or disjunction does not change which operands are
  accepted.

The operand is modelled abstractly by its observable predicates — whether it is
a same-kind container, whether it is usable directly as a boolean filter
condition, and whether it is empty — together with the calling container's own
emptiness; the discriminating observable is purely WHICH outcome the
combination produces (reject vs. which acceptance branch), not the operands'
internal data. The uniform type-rejection failure is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator). The
combination outcome is modelled as a small result object tagging the branch
taken and the connector it carries.

The combination must actually DELIVER its outcome — return or raise — on every
input: a total-correctness obligation, carried as ``MustTerminate`` in the
precondition. Nagini checks partial correctness by default, so without this
obligation a diverging body would satisfy every postcondition vacuously; the
real combination is bounded, loop-free work that always answers.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class OperandTypeRejected(Exception):
    """The single uniform type-rejection failure the combination surfaces to its
    caller whenever the operand is neither a same-kind container nor an operand
    usable directly as a boolean filter condition. User-defined stand-in for the
    type-rejection the desired behaviour requires (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass

class Combined:
    """Observable outcome of an accepted combination (mapping.md §2):

      * ``branch`` tags which acceptance branch produced the result —
        0: the operand was empty, so the result is a copy of the container;
        1: the container was empty (operand non-empty), so the result is a copy
           of the operand;
        2: both sides non-empty, so the result is a fresh container joining both
           operands under the requested connector.
      * ``connector`` is the boolean connector carried by the result. For a
        branch-2 merge it is EXACTLY the requested connector; the identity
        branches carry the copied side's own connector (left abstract here)."""

    def __init__(self, branch: int, connector: int) -> None:
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a result without
        # leaking its own obligation.
        Requires(MustTerminate(1))
        Requires(0 <= branch and branch <= 2)
        Ensures(Acc(self.branch) and Acc(self.connector))
        Ensures(self.branch == branch and self.connector == connector)
        self.branch = branch          # type: int
        self.connector = connector    # type: int

# axioms-start
# (no axiomatized callee: the changed function reads only its operands'
#  observable predicates — same-kind-container test, the boolean-operand test,
#  and emptiness — all modelled abstractly. The downstream identity/merge
#  branches are modelled directly, not via an unchanged library callee.)
# axioms-end

# pure-start
# (no module-level pure helpers required: the combination's decision is stated
#  inline over the operands' boolean observables.)
# pure-end

def combine(other_is_container: bool, other_is_boolean_operand: bool,
            other_empty: bool, self_empty: bool, conn: int) -> Combined:
    # pre-conditions-start
    # The operand and the calling container are characterised by their
    # observable predicates (plain booleans, no heap permission needed):
    #   other_is_container       — the operand is another same-kind container;
    #   other_is_boolean_operand — the operand is usable directly as a boolean
    #                              filter condition (a boolean-valued operand);
    #   other_empty              — the operand is empty (its falsy/identity form);
    #   self_empty               — the calling container is empty.
    # `conn` is the requested boolean connector (an opaque tag).
    # TOTALITY: the combination must actually deliver its outcome (return or
    # raise) on every input. Nagini is a partial-correctness verifier by
    # default, so without this obligation a diverging body (e.g. an endless
    # loop on an accepted branch) would satisfy every postcondition vacuously;
    # the real combination is bounded, loop-free work that always answers.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # ACCEPTANCE: a normal return is reachable for EXACTLY the acceptable
    # operands — a same-kind container OR an operand usable directly as a
    # boolean filter condition. An operand that is neither must NOT return
    # normally.
    Ensures(other_is_container or other_is_boolean_operand)
    # The branch taken is determined by the emptiness observables, identically
    # for either connector: an empty operand -> container copy (branch 0); else
    # an empty container -> operand copy (branch 1); else a merge (branch 2).
    Ensures(Acc(Result().branch) and Acc(Result().connector))
    Ensures(0 <= Result().branch and Result().branch <= 2)
    Ensures(Implies(other_empty, Result().branch == 0))
    Ensures(Implies(not other_empty and self_empty, Result().branch == 1))
    Ensures(Implies(not other_empty and not self_empty, Result().branch == 2))
    # The merge carries EXACTLY the requested connector (pins the result to the
    # caller-supplied connector, not an arbitrary tag).
    Ensures(Implies(Result().branch == 2, Result().connector == conn))
    # REJECTION: an operand that is neither a same-kind container nor usable as a
    # boolean filter condition is surfaced as the uniform type-rejection, and
    # ONLY then.
    Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)
    # post-conditions-end
    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()

    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)

    obj = Combined(2, conn)
    return obj
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

All commands run from there with and env swebench-lean.

SPEC ANALYSIS: model.py `combine` pins (i) REJECT iff (not other_is_container and not other_is_boolean_operand) via Exsures; (ii) normal-return Ensures(other_is_container or other_is_boolean_operand); (iii) branch tag by emptiness — Implies(other_empty, branch==0), Implies(not other_empty and self_empty, branch==1), Implies(not other_empty and not self_empty, branch==2); (iv) Implies(branch==2, connector==conn); (v) totality via Requires(MustTerminate(2)). The ONLY degree of freedom left abstract is the connector value on identity branches 0/1 (model.py:72, refinement A4/A5 state it carries the copied side's own connector, left abstract).

SAME-SPEC: all 7 attacks + positive control confirmed byte-identical spec signature via `adversary same-spec` (only impl region edited; axioms/@Pure/Requires/Ensures/Exsures untouched).

WEAKNESS RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14017 <path>`; run in 3 background batches, <=3 JVMs at a time):
- atk_1 (prepatch bug echo / partial-domain: `if not other_is_container: raise`): EXIT 2, verification FAILED — spec caught it on the Exsures for a boolean-operand-but-non-container operand. PREPATCH REPRODUCED (matches model_prepatch.py + G-DIFF fail).
- atk_2 (partial-domain, conjunction guard `not (oic and obo)`): EXIT 2, verification FAILED — rejects accepted operands.
- atk_3 (boundary, branch-order swap self_empty before other_empty): EXIT 2, verification FAILED — both-empty maps to wrong branch (1 vs required 0).
- atk_4 (wrong merge connector `Combined(2, conn+1)`): EXIT 2, verification FAILED — violates Implies(branch==2, connector==conn).
- atk_5 (control-flow-effect, `while True: pass` on merge branch): EXIT 2, verification FAILED — cannot discharge MustTerminate(2).
- atk_6 (over-acceptance / ungrounded-oracle: drops the guard, never raises): EXIT 2, verification FAILED — violates Ensures(oic or obo) and the Exsures.
- atk_7 (ungrounded-oracle echo / exploits the ONE abstract field: `Combined(0, conn+12345)` on branch 0 and `Combined(1, conn-999)` on branch 1): EXIT 0, CANDIDATE — shares spec AND verifies (spec deliberately leaves branch-0/1 connector unconstrained).
- pos (gold-faithful impl): `adversary weakness` EXIT 0 (verifies) — positive control PASSES.

CANDIDATE atk_7 -> FAITHFUL PATCH -> RESOLVE (mandatory per protocol): atk_7's ONLY deviation from gold is the connector tag on identity branches 0/1. Per refinement A4/A5 + the real base_commit body of Q._combine, branch 0 returns `type(self)(*self.deconstruct())` and branch 1 returns `type(other)(*other.deconstruct())` — copies carrying the COPIED SIDE's own connector; the real code performs NO `obj.connector = conn` assignment on branches 0/1 (only branch 2 does). So atk_7's deviation lives entirely in a modeling field (Combined.connector on branch 0/1) that has NO real callee counterpart => it is UNREFINABLE => its faithful refined patch is exactly the gold patch.

Materialized to atk_7_faithful.patch (byte-identical to benchmark-verified/django__django-14017/patch.diff, verified via diff). RAN through official harness `run_resolve('django__django-14017', <faithful patch>)`: resolved=True, completed=True, attempts=1, note='resolved', patch_successfully_applied=True; FAIL_TO_PASS success=[test_boolean_expression_combined, test_boolean_expression_combined_with_empty_Q], failure=[]; no P2P failures. Report saved at atk_7_resolve_report.json. (Two earlier runs returned completed=False in ~32s = transient contention with a concurrently-running resolve concurrent runs [astropy/django-11820 containers seen in docker ps]; the built-in retry and a clean re-run both returned resolved=True. This is infra flakiness, not a real non-resolve.)

REFINEMENT.MD AUDIT: legs A1-A7 all tagged R / R+I; §B explicitly asserts NO kind-3 (unexpressible-changed-op) steps; mapping.md §3 records an EMPTY axiom inventory (no A-consumed, no A-reference deep model) — the changed guard reads isinstance/getattr/truthiness modeled directly as the input predicates, downstream branches modeled directly as the three Combined outcomes. The single soundness obligation (boolean-predicate abstraction fidelity) is discharged by axiom_check.py / G-AX, recorded PASS (20/20 concrete operand x connector x self-emptiness combos, incl. the discriminating Q()&Exists conditional operand and the rejected non-conditional operands). No kind-3; A-leg correspondence holds.

CONCLUSION: >=5 distinct wrong impls run (7 total, 6 rejected by the spec + 1 verifying candidate whose faithful patch RESOLVES); positive control verifies; prepatch reproduced. verify=>correct holds on this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for django__django-14017.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logical-filter container combines itself with another operand under a
  boolean connector (conjunction or disjunction). The combination must accept
  an operand that is EITHER another container of the same kind OR any object
  that is itself usable directly as a boolean filter condition (a
  boolean-valued operand) — the two are interchangeable as boolean operands and
  the combination is therefore symmetric on such a pair. Only an operand that is
  neither — one that is not a same-kind container AND is not usable as a boolean
  filter condition — is rejected, with a single uniform type-rejection failure
  to the caller.

  When the operand is acceptable, the combination returns normally. The empty
  container is the identity element of both connectors: combining an empty
  operand yields a copy of the container, and combining into an empty container
  yields a copy of the operand. When both sides are non-empty the result is a
  fresh container carrying the requested connector with both operands joined
  under it. The connector of the merged result is exactly the requested one.

  The behaviour pinned here is the ACCEPTANCE decision: an operand that is
  usable directly as a boolean filter condition must be accepted (no rejection)
  exactly as a same-kind container is, and only an operand that is neither a
  same-kind container nor a boolean filter condition is rejected. Whether the
  connector is conjunction or disjunction does not change which operands are
  accepted.

The operand is modelled abstractly by its observable predicates — whether it is
a same-kind container, whether it is usable directly as a boolean filter
condition, and whether it is empty — together with the calling container's own
emptiness; the discriminating observable is purely WHICH outcome the
combination produces (reject vs. which acceptance branch), not the operands'
internal data. The uniform type-rejection failure is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator). The
combination outcome is modelled as a small result object tagging the branch
taken and the connector it carries.

The combination must actually DELIVER its outcome — return or raise — on every
input: a total-correctness obligation, carried as ``MustTerminate`` in the
precondition. Nagini checks partial correctness by default, so without this
obligation a diverging body would satisfy every postcondition vacuously; the
real combination is bounded, loop-free work that always answers.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class OperandTypeRejected(Exception):
    """The single uniform type-rejection failure the combination surfaces to its
    caller whenever the operand is neither a same-kind container nor an operand
    usable directly as a boolean filter condition. User-defined stand-in for the
    type-rejection the desired behaviour requires (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass

class Combined:
    """Observable outcome of an accepted combination (mapping.md §2):

      * ``branch`` tags which acceptance branch produced the result —
        0: the operand was empty, so the result is a copy of the container;
        1: the container was empty (operand non-empty), so the result is a copy
           of the operand;
        2: both sides non-empty, so the result is a fresh container joining both
           operands under the requested connector.
      * ``connector`` is the boolean connector carried by the result. For a
        branch-2 merge it is EXACTLY the requested connector; the identity
        branches carry the copied side's own connector (left abstract here)."""

    def __init__(self, branch: int, connector: int) -> None:
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a result without
        # leaking its own obligation.
        Requires(MustTerminate(1))
        Requires(0 <= branch and branch <= 2)
        Ensures(Acc(self.branch) and Acc(self.connector))
        Ensures(self.branch == branch and self.connector == connector)
        self.branch = branch          # type: int
        self.connector = connector    # type: int

# axioms-start
# (no axiomatized callee: the changed function reads only its operands'
#  observable predicates — same-kind-container test, the boolean-operand test,
#  and emptiness — all modelled abstractly. The downstream identity/merge
#  branches are modelled directly, not via an unchanged library callee.)
# axioms-end

# pure-start
# (no module-level pure helpers required: the combination's decision is stated
#  inline over the operands' boolean observables.)
# pure-end

def combine(other_is_container: bool, other_is_boolean_operand: bool,
            other_empty: bool, self_empty: bool, conn: int) -> Combined:
    # pre-conditions-start
    # The operand and the calling container are characterised by their
    # observable predicates (plain booleans, no heap permission needed):
    #   other_is_container       — the operand is another same-kind container;
    #   other_is_boolean_operand — the operand is usable directly as a boolean
    #                              filter condition (a boolean-valued operand);
    #   other_empty              — the operand is empty (its falsy/identity form);
    #   self_empty               — the calling container is empty.
    # `conn` is the requested boolean connector (an opaque tag).
    # TOTALITY: the combination must actually deliver its outcome (return or
    # raise) on every input. Nagini is a partial-correctness verifier by
    # default, so without this obligation a diverging body (e.g. an endless
    # loop on an accepted branch) would satisfy every postcondition vacuously;
    # the real combination is bounded, loop-free work that always answers.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # ACCEPTANCE: a normal return is reachable for EXACTLY the acceptable
    # operands — a same-kind container OR an operand usable directly as a
    # boolean filter condition. An operand that is neither must NOT return
    # normally.
    Ensures(other_is_container or other_is_boolean_operand)
    # The branch taken is determined by the emptiness observables, identically
    # for either connector: an empty operand -> container copy (branch 0); else
    # an empty container -> operand copy (branch 1); else a merge (branch 2).
    Ensures(Acc(Result().branch) and Acc(Result().connector))
    Ensures(0 <= Result().branch and Result().branch <= 2)
    Ensures(Implies(other_empty, Result().branch == 0))
    Ensures(Implies(not other_empty and self_empty, Result().branch == 1))
    Ensures(Implies(not other_empty and not self_empty, Result().branch == 2))
    # The merge carries EXACTLY the requested connector (pins the result to the
    # caller-supplied connector, not an arbitrary tag).
    Ensures(Implies(Result().branch == 2, Result().connector == conn))
    # REJECTION: an operand that is neither a same-kind container nor usable as a
    # boolean filter condition is surfaced as the uniform type-rejection, and
    # ONLY then.
    Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)
    # post-conditions-end
    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()

    if other_empty:
        return Combined(0, conn)
    elif self_empty:
        return Combined(1, conn)

    obj = Combined(2, conn)
    return obj
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

All commands run from there with and env swebench-lean.

SPEC ANALYSIS: model.py `combine` pins (i) REJECT iff (not other_is_container and not other_is_boolean_operand) via Exsures; (ii) normal-return Ensures(other_is_container or other_is_boolean_operand); (iii) branch tag by emptiness — Implies(other_empty, branch==0), Implies(not other_empty and self_empty, branch==1), Implies(not other_empty and not self_empty, branch==2); (iv) Implies(branch==2, connector==conn); (v) totality via Requires(MustTerminate(2)). The ONLY degree of freedom left abstract is the connector value on identity branches 0/1 (model.py:72, refinement A4/A5 state it carries the copied side's own connector, left abstract).

SAME-SPEC: all 7 attacks + positive control confirmed byte-identical spec signature via `adversary same-spec` (only impl region edited; axioms/@Pure/Requires/Ensures/Exsures untouched).

WEAKNESS RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14017 <path>`; run in 3 background batches, <=3 JVMs at a time):
- atk_1 (prepatch bug echo / partial-domain: `if not other_is_container: raise`): EXIT 2, verification FAILED — spec caught it on the Exsures for a boolean-operand-but-non-container operand. PREPATCH REPRODUCED (matches model_prepatch.py + G-DIFF fail).
- atk_2 (partial-domain, conjunction guard `not (oic and obo)`): EXIT 2, verification FAILED — rejects accepted operands.
- atk_3 (boundary, branch-order swap self_empty before other_empty): EXIT 2, verification FAILED — both-empty maps to wrong branch (1 vs required 0).
- atk_4 (wrong merge connector `Combined(2, conn+1)`): EXIT 2, verification FAILED — violates Implies(branch==2, connector==conn).
- atk_5 (control-flow-effect, `while True: pass` on merge branch): EXIT 2, verification FAILED — cannot discharge MustTerminate(2).
- atk_6 (over-acceptance / ungrounded-oracle: drops the guard, never raises): EXIT 2, verification FAILED — violates Ensures(oic or obo) and the Exsures.
- atk_7 (ungrounded-oracle echo / exploits the ONE abstract field: `Combined(0, conn+12345)` on branch 0 and `Combined(1, conn-999)` on branch 1): EXIT 0, CANDIDATE — shares spec AND verifies (spec deliberately leaves branch-0/1 connector unconstrained).
- pos (gold-faithful impl): `adversary weakness` EXIT 0 (verifies) — positive control PASSES.

CANDIDATE atk_7 -> FAITHFUL PATCH -> RESOLVE (mandatory per protocol): atk_7's ONLY deviation from gold is the connector tag on identity branches 0/1. Per refinement A4/A5 + the real base_commit body of Q._combine, branch 0 returns `type(self)(*self.deconstruct())` and branch 1 returns `type(other)(*other.deconstruct())` — copies carrying the COPIED SIDE's own connector; the real code performs NO `obj.connector = conn` assignment on branches 0/1 (only branch 2 does). So atk_7's deviation lives entirely in a modeling field (Combined.connector on branch 0/1) that has NO real callee counterpart => it is UNREFINABLE => its faithful refined patch is exactly the gold patch.

Materialized to atk_7_faithful.patch (byte-identical to benchmark-verified/django__django-14017/patch.diff, verified via diff). RAN through official harness `run_resolve('django__django-14017', <faithful patch>)`: resolved=True, completed=True, attempts=1, note='resolved', patch_successfully_applied=True; FAIL_TO_PASS success=[test_boolean_expression_combined, test_boolean_expression_combined_with_empty_Q], failure=[]; no P2P failures. Report saved at atk_7_resolve_report.json. (Two earlier runs returned completed=False in ~32s = transient contention with a concurrently-running resolve concurrent runs [astropy/django-11820 containers seen in docker ps]; the built-in retry and a clean re-run both returned resolved=True. This is infra flakiness, not a real non-resolve.)

REFINEMENT.MD AUDIT: legs A1-A7 all tagged R / R+I; §B explicitly asserts NO kind-3 (unexpressible-changed-op) steps; mapping.md §3 records an EMPTY axiom inventory (no A-consumed, no A-reference deep model) — the changed guard reads isinstance/getattr/truthiness modeled directly as the input predicates, downstream branches modeled directly as the three Combined outcomes. The single soundness obligation (boolean-predicate abstraction fidelity) is discharged by axiom_check.py / G-AX, recorded PASS (20/20 concrete operand x connector x self-emptiness combos, incl. the discriminating Q()&Exists conditional operand and the rejected non-conditional operands). No kind-3; A-leg correspondence holds.

CONCLUSION: >=5 distinct wrong impls run (7 total, 6 rejected by the spec + 1 verifying candidate whose faithful patch RESOLVES); positive control verifies; prepatch reproduced. verify=>correct holds on this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) audit of django__django-14017 nagini bundle. The modeled function combine(other_is_container, other_is_boolean_operand, other_empty, self_empty, conn) faithfully models the real post-patch Q._combine (django/db/models/query_utils.py:42, base_commit worktree already carrying the widened guard). Real guard: `if not(isinstance(other, Q) or getattr(other,'conditional',False) is True): raise TypeError(other)`; model guard is the exact De Morgan analogue over the R-refined predicates. Empirical check: drove the REAL Q._combine over all 20 realizable (operand x connector x self-emptiness) combinations — spanning empty/nonempty Q, a conditional-True non-container, a conditional-False expr, and a plain int — and every acceptance decision and branch outcome (branch0 copy-self with children equality; branch1 preserving type(other); branch2 merge carrying exactly conn) matched the model's pinned postconditions with 0 mismatches. Edge case verified: an operand with conditional=1 (truthy but not `is True`) is REJECTED by the real callee, and the model rejects it too (other_is_boolean_operand abstracts `... is True`, which is False) — so the model is not too strong here nor does it over-accept. Model verifies under the pinned Nagini (exit 0, 15.3s); MustTerminate(2) totality obligation present. Spec region confirmed byte-identical via same-spec tooling (impl-only variant accepted, exit 0). No diverging input found: the spec neither over-constrains (rejecting inputs the real callee accepts) nor drifts from real repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no hard_failures, no warnings). Spec view (post-marker projection of model.py) does not leak the gold edit beyond the public problem_statement. (1) No gold-diff line, no diff markers, no patched file path/module path. (2) The fix-keying repo attribute `conditional` is absent — abstracted to the neutral behavioral param `other_is_boolean_operand` / 'usable directly as a boolean filter condition' (D1 scrub); repo symbols isinstance/getattr/_combine/query_utils/TypeError/Exists/__and__/__rand__/commutative are all absent from the spec view. Only `django` hit is the public instance id in the title line. (3) Semantically, the gold discriminator (accept a boolean-condition operand like Exists in addition to a same-kind Q) is ALREADY public: the problem_statement shows the `if not isinstance(other, Q): raise TypeError(other)` guard, demonstrates Q()&Exists(...) raising TypeError, and states the operators should be commutative on Q-Exists pairs. The spec view restates this desired acceptance behavior abstractly and connector-agnostically; it narrates no bug/fix. `conditional` and the pre-patch guard appear only in mapping.md/refinement.md (audit docs, not the consumer spec view). No spec-view line reveals the edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
