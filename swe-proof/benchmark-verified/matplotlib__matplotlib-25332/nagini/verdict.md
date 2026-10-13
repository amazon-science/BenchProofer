# P2 adversarial audit — matplotlib__matplotlib-25332

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,18 +83,15 @@
     out = []  # type: List[int]
     i = 0
     while i < len(ident):
-        # invariants-start
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(ident))
+        Invariant(len(weak) == len(ident))
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
-            Implies(0 <= k and k < i, out[k] == 0)))
-        # invariants-end
-        # Resolving the indirect handle to its target's identity (ident[i]) and
-        # storing it as a direct handle: the captured slot is direct (flag 0).
-        out.append(0)
+            Implies(0 <= k and k < i and k < len(weak), out[k] == weak[k])))
+        out.append(weak[i])
         i = i + 1
     return out
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,18 +127,14 @@
     out = []  # type: List[int]
     i = 0
     while i < len(ident):
-        # invariants-start
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(state_weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(ident))
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
-            Implies(0 <= k and k < i, out[k] == 1)))
-        # invariants-end
-        # Constructing an indirect handle around the target identity ident[i]:
-        # the rebuilt slot is indirect (flag 1).
-        out.append(1)
+            Implies(0 <= k and k < i, out[k] == 0)))
+        out.append(0)
         i = i + 1
     return out
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,18 +83,15 @@
     out = []  # type: List[int]
     i = 0
     while i < len(ident):
-        # invariants-start
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(ident))
         Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k:
-            Implies(0 <= k and k < i, out[k] == 0)))
-        # invariants-end
-        # Resolving the indirect handle to its target's identity (ident[i]) and
-        # storing it as a direct handle: the captured slot is direct (flag 0).
-        out.append(0)
+        if i == 0:
+            out.append(1)
+        else:
+            out.append(0)
         i = i + 1
     return out
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,7 @@
     # impl-start
     out = []  # type: List[int]
     i = 0
-    while i < len(ident):
-        # invariants-start
+    while i < len(ident) and i < len(ident) - 1:
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
@@ -91,9 +90,6 @@
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i, out[k] == 0)))
-        # invariants-end
-        # Resolving the indirect handle to its target's identity (ident[i]) and
-        # storing it as a direct handle: the captured slot is direct (flag 0).
         out.append(0)
         i = i + 1
     return out
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,19 +125,15 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    i = 0
+    i = 1
     while i < len(ident):
-        # invariants-start
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(state_weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(ident))
-        Invariant(len(out) == i)
+        Invariant(1 <= i and i <= len(ident))
+        Invariant(len(out) == i - 1)
         Invariant(Forall(int, lambda k:
-            Implies(0 <= k and k < i, out[k] == 1)))
-        # invariants-end
-        # Constructing an indirect handle around the target identity ident[i]:
-        # the rebuilt slot is indirect (flag 1).
+            Implies(0 <= k and k < i - 1, out[k] == 1)))
         out.append(1)
         i = i + 1
     return out
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,6 @@
     out = []  # type: List[int]
     i = 0
     while i < len(ident):
-        # invariants-start
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
@@ -91,10 +90,8 @@
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i, out[k] == 0)))
-        # invariants-end
-        # Resolving the indirect handle to its target's identity (ident[i]) and
-        # storing it as a direct handle: the captured slot is direct (flag 0).
-        out.append(0)
+        # reads weak[i] but forces direct: still all-0 output (echo of gold)
+        out.append(weak[i] * 0)
         i = i + 1
     return out
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -164,7 +164,17 @@
         Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
     # post-conditions-end
     # impl-start
-    captured = capture_state(ident, weak)
-    restored = restore_state(ident, captured)
-    return restored
+    out = []  # type: List[int]
+    i = 0
+    while i < len(ident):
+        Invariant(Acc(list_pred(ident), 1 / 2))
+        Invariant(Acc(list_pred(weak), 1 / 2))
+        Invariant(Acc(list_pred(out)))
+        Invariant(0 <= i and i <= len(ident))
+        Invariant(len(out) == i)
+        Invariant(Forall(int, lambda k:
+            Implies(0 <= k and k < i, out[k] == 1)))
+        out.append(1)
+        i = i + 1
+    return out
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,19 +81,17 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
+    n = len(ident)
     i = 0
-    while i < len(ident):
-        # invariants-start
+    while i < n:
         Invariant(Acc(list_pred(ident), 1 / 2))
         Invariant(Acc(list_pred(weak), 1 / 2))
         Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(ident))
+        Invariant(n == len(ident))
+        Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i, out[k] == 0)))
-        # invariants-end
-        # Resolving the indirect handle to its target's identity (ident[i]) and
-        # storing it as a direct handle: the captured slot is direct (flag 0).
         out.append(0)
         i = i + 1
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25332.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container keeps its members through *indirect* handles: each stored handle
  does not own its target, it only points at it, and a handle may be resolved to
  the integer identity of the target it points at. Indirect handles are not
  serialisable; a *direct* handle (one that simply IS the target's identity,
  owning nothing extra) is.

  (1) Capturing the container for serialisation must yield a state in which
      every stored handle is DIRECT — i.e. no surviving indirect handle — while
      preserving, slot for slot, the integer identity that each original handle
      pointed at. Element i of the captured state resolves to the same identity
      as original handle i, and is itself direct.

  (2) Restoring the container from such a captured state must rebuild every slot
      as an INDIRECT handle again, preserving, slot for slot, the identity each
      captured direct handle carried. Element i of the restored container
      resolves to the same identity as captured element i, and is itself
      indirect.

  Consequently the capture-then-restore round trip is the identity on the
  resolved identity of every slot: restoring a captured container yields, slot
  for slot, an indirect handle pointing at the same identity as the original.

Modelling. A handle is modelled by two parallel `List[int]`: `ident[i]` is the
integer identity the i-th handle points at (its resolution), and `weak[i]` is
1 iff that handle is indirect (not serialisable) and 0 iff it is direct
(serialisable). The two operations are `capture_state` (resolve every indirect
handle to a direct one) and `restore_state` (wrap every direct handle back into
an indirect one); `roundtrip_weakness` composes them. The identity-resolution of
a handle and the (in)direct discriminator are the modelled carrier of the real
handle-resolution / handle-construction primitives, validated by axiom_check.py
(G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The changed operation is the capture/restore
# of the container's stored handles; it is modelled DEEPLY below — the
# resolution of a handle to an identity and the direct/indirect discriminator
# are spelled out as parallel List[int]. The unchanged primitives these stand
# for — resolving an indirect handle to its target's identity, and constructing
# an indirect handle around a target — are validated against the real handle
# primitives by axiom_check.py (G-AX), not consumed as a contract here.)
# axioms-end


# pure-start
# (No pure helpers needed: the specification is element-wise over the two
# parallel List[int] carriers, expressed directly with Forall + in-bounds
# guards.)
# pure-end


def capture_state(ident: List[int], weak: List[int]) -> List[int]:
    """Capture the container for serialisation: resolve every stored handle to a
    DIRECT handle. Returns the captured directness flags (a fresh List[int] of
    0/1, one per slot). The captured state preserves each slot's resolved
    identity (`ident` is read-only and unchanged) and contains NO indirect
    handle (every returned flag is 0)."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(weak), 1 / 2))
    Requires(len(weak) == len(ident))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The captured state has one directness flag per slot.
    Ensures(len(Result()) == len(ident))
    # Every captured handle is DIRECT (serialisable): no surviving indirect one.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 0)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(weak), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(ident))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i, out[k] == 0)))
        # invariants-end
        # Resolving the indirect handle to its target's identity (ident[i]) and
        # storing it as a direct handle: the captured slot is direct (flag 0).
        out.append(0)
        i = i + 1
    return out
    # impl-end


def restore_state(ident: List[int], state_weak: List[int]) -> List[int]:
    """Restore the container from a captured state: wrap every captured DIRECT
    handle back into an INDIRECT handle. Returns the restored directness flags
    (a fresh List[int] of 0/1, one per slot). The restored container preserves
    each slot's resolved identity (`ident` is read-only and unchanged) and every
    rebuilt handle is INDIRECT (every returned flag is 1)."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(state_weak), 1 / 2))
    Requires(len(state_weak) == len(ident))
    # The captured state being restored consists of DIRECT handles.
    Requires(Forall(int, lambda k:
        Implies(0 <= k and k < len(state_weak), state_weak[k] == 0)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(state_weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(ident))
    # Every restored handle is INDIRECT again (the live container's form).
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(state_weak), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(ident))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i, out[k] == 1)))
        # invariants-end
        # Constructing an indirect handle around the target identity ident[i]:
        # the rebuilt slot is indirect (flag 1).
        out.append(1)
        i = i + 1
    return out
    # impl-end


def roundtrip_weakness(ident: List[int], weak: List[int]) -> List[int]:
    """Capture then restore: the composition of the two operations. Returns the
    directness flags of the restored container. The round trip preserves each
    slot's resolved identity (`ident` unchanged) and the restored container is
    again all-indirect, regardless of the original directness."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(weak), 1 / 2))
    Requires(len(weak) == len(ident))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(ident))
    # The container after a capture/restore round trip is all-indirect again.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
    # post-conditions-end
    # impl-start
    captured = capture_state(ident, weak)
    restored = restore_state(ident, captured)
    return restored
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

DEEP-MODEL bundle (no consumed axiom). Impl region emits only directness flags; postconditions COMPLETELY PIN each function's output: capture_state -> all flags 0, restore_state -> all flags 1, roundtrip_weakness -> all flags 1, each of length len(ident), with ident read-only at 1/2 perm. Identity preservation is delegated to R (ident immutable) + A-reference validated by G-AX. Positive control verifies (11.6s); axiom_check.py (G-AX) exits 0 on 5 boundary + 2000 fuzz handle sets.

8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`), verified via `adversary weakness nagini matplotlib__matplotlib-25332`:
- atk_1 PREPATCH repro (capture appends weak[i], keeping live indirect flags): does NOT verify -> spec rejects, bug sensed (G-DIFF). PREPATCH REPRODUCED.
- atk_2 restore appends 0 (fails all-1 postcond): does NOT verify.
- atk_3 partial-domain (capture flag 1 at slot 0, else 0): does NOT verify.
- atk_4 control-flow-effect (capture loop `i<len-1`, short output): does NOT verify (len(Result())==len(ident) fails).
- atk_5 boundary off-by-one (restore starts i=1, skips a slot): does NOT verify.
- atk_6 ungrounded echo (capture out.append(weak[i]*0) but omits len(weak)==len(ident) invariant so weak[i] bounds unprovable): does NOT verify.
- atk_7 CANDIDATE (roundtrip_weakness rebuilds all-1 directly without composing capture_state/restore_state): shares spec AND verifies (15.0s). Behaviorally an ECHO of gold (byte-identical output). Faithful refined patch = gold patch (roundtrip is getstate then setstate; the observable result is unchanged).
- atk_8 CANDIDATE (capture_state rewritten with hoisted `n=len(ident)` loop bound, same all-0 output): shares spec AND verifies (14.3s). ECHO of gold; faithful patch = gold patch.

BOTH CANDIDATES' materialized faithful patch was RUN through run_resolve (official harness, run_id sbu-eqaudit-atk7-8tsn68eh). Executed result: RESOLVED=True, COMPLETED=True — FAIL_TO_PASS test_complete[png] success, all 181 PASS_TO_PASS success, 0 failures. Since both verifying wrong-shaped impls are behavioral echoes whose faithful patch resolves, neither is a weakness (2026-08-06 echo-attack policy: a same-spec verifying attack fails the gate ONLY if its refined patch does NOT resolve).

refinement.md A-leg audit: A2 (capture_state <-> Grouper.__getstate__, A-reference) and B2 (restore_state <-> Grouper.__setstate__, A-reference) correspond faithfully to the real callees — deref k()/v() yields direct/picklable/identity-preserving handles (flag 0); weakref.ref(k)/map(weakref.ref,vs) yields indirect/unpicklable/identity-preserving handles (flag 1). G-AX (axiom_check.py) independently validates both against real weakref.ref, weakref deref, pickle.dumps on 5 boundary + 2000 fuzz sets (exit 0). C1/C2 are I+A-reference; A1/A3/B1/B3/C3 are R. No kind-3 legs. Patch methods byte-match mapping.md §3 quotes; base_commit 66ba515e6 and F2P test_complete[png] match instance.json.

Conclusion: the postconditions fully pin the tested-relevant projection; the only verifying impls are cosmetic echoes refining to the gold patch, which resolves. verify => resolved holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25332.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container keeps its members through *indirect* handles: each stored handle
  does not own its target, it only points at it, and a handle may be resolved to
  the integer identity of the target it points at. Indirect handles are not
  serialisable; a *direct* handle (one that simply IS the target's identity,
  owning nothing extra) is.

  (1) Capturing the container for serialisation must yield a state in which
      every stored handle is DIRECT — i.e. no surviving indirect handle — while
      preserving, slot for slot, the integer identity that each original handle
      pointed at. Element i of the captured state resolves to the same identity
      as original handle i, and is itself direct.

  (2) Restoring the container from such a captured state must rebuild every slot
      as an INDIRECT handle again, preserving, slot for slot, the identity each
      captured direct handle carried. Element i of the restored container
      resolves to the same identity as captured element i, and is itself
      indirect.

  Consequently the capture-then-restore round trip is the identity on the
  resolved identity of every slot: restoring a captured container yields, slot
  for slot, an indirect handle pointing at the same identity as the original.

Modelling. A handle is modelled by two parallel `List[int]`: `ident[i]` is the
integer identity the i-th handle points at (its resolution), and `weak[i]` is
1 iff that handle is indirect (not serialisable) and 0 iff it is direct
(serialisable). The two operations are `capture_state` (resolve every indirect
handle to a direct one) and `restore_state` (wrap every direct handle back into
an indirect one); `roundtrip_weakness` composes them. The identity-resolution of
a handle and the (in)direct discriminator are the modelled carrier of the real
handle-resolution / handle-construction primitives, validated by axiom_check.py
(G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The changed operation is the capture/restore
# of the container's stored handles; it is modelled DEEPLY below — the
# resolution of a handle to an identity and the direct/indirect discriminator
# are spelled out as parallel List[int]. The unchanged primitives these stand
# for — resolving an indirect handle to its target's identity, and constructing
# an indirect handle around a target — are validated against the real handle
# primitives by axiom_check.py (G-AX), not consumed as a contract here.)
# axioms-end


# pure-start
# (No pure helpers needed: the specification is element-wise over the two
# parallel List[int] carriers, expressed directly with Forall + in-bounds
# guards.)
# pure-end


def capture_state(ident: List[int], weak: List[int]) -> List[int]:
    """Capture the container for serialisation: resolve every stored handle to a
    DIRECT handle. Returns the captured directness flags (a fresh List[int] of
    0/1, one per slot). The captured state preserves each slot's resolved
    identity (`ident` is read-only and unchanged) and contains NO indirect
    handle (every returned flag is 0)."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(weak), 1 / 2))
    Requires(len(weak) == len(ident))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The captured state has one directness flag per slot.
    Ensures(len(Result()) == len(ident))
    # Every captured handle is DIRECT (serialisable): no surviving indirect one.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 0)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(weak), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(ident))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i, out[k] == 0)))
        # invariants-end
        # Resolving the indirect handle to its target's identity (ident[i]) and
        # storing it as a direct handle: the captured slot is direct (flag 0).
        out.append(0)
        i = i + 1
    return out
    # impl-end


def restore_state(ident: List[int], state_weak: List[int]) -> List[int]:
    """Restore the container from a captured state: wrap every captured DIRECT
    handle back into an INDIRECT handle. Returns the restored directness flags
    (a fresh List[int] of 0/1, one per slot). The restored container preserves
    each slot's resolved identity (`ident` is read-only and unchanged) and every
    rebuilt handle is INDIRECT (every returned flag is 1)."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(state_weak), 1 / 2))
    Requires(len(state_weak) == len(ident))
    # The captured state being restored consists of DIRECT handles.
    Requires(Forall(int, lambda k:
        Implies(0 <= k and k < len(state_weak), state_weak[k] == 0)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(state_weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(ident))
    # Every restored handle is INDIRECT again (the live container's form).
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(state_weak), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(ident))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i, out[k] == 1)))
        # invariants-end
        # Constructing an indirect handle around the target identity ident[i]:
        # the rebuilt slot is indirect (flag 1).
        out.append(1)
        i = i + 1
    return out
    # impl-end


def roundtrip_weakness(ident: List[int], weak: List[int]) -> List[int]:
    """Capture then restore: the composition of the two operations. Returns the
    directness flags of the restored container. The round trip preserves each
    slot's resolved identity (`ident` unchanged) and the restored container is
    again all-indirect, regardless of the original directness."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(weak), 1 / 2))
    Requires(len(weak) == len(ident))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(ident))
    # The container after a capture/restore round trip is all-indirect again.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
    # post-conditions-end
    # impl-start
    captured = capture_state(ident, weak)
    restored = restore_state(ident, captured)
    return restored
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

DEEP-MODEL bundle (no consumed axiom). Impl region emits only directness flags; postconditions COMPLETELY PIN each function's output: capture_state -> all flags 0, restore_state -> all flags 1, roundtrip_weakness -> all flags 1, each of length len(ident), with ident read-only at 1/2 perm. Identity preservation is delegated to R (ident immutable) + A-reference validated by G-AX. Positive control verifies (11.6s); axiom_check.py (G-AX) exits 0 on 5 boundary + 2000 fuzz handle sets.

8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`), verified via `adversary weakness nagini matplotlib__matplotlib-25332`:
- atk_1 PREPATCH repro (capture appends weak[i], keeping live indirect flags): does NOT verify -> spec rejects, bug sensed (G-DIFF). PREPATCH REPRODUCED.
- atk_2 restore appends 0 (fails all-1 postcond): does NOT verify.
- atk_3 partial-domain (capture flag 1 at slot 0, else 0): does NOT verify.
- atk_4 control-flow-effect (capture loop `i<len-1`, short output): does NOT verify (len(Result())==len(ident) fails).
- atk_5 boundary off-by-one (restore starts i=1, skips a slot): does NOT verify.
- atk_6 ungrounded echo (capture out.append(weak[i]*0) but omits len(weak)==len(ident) invariant so weak[i] bounds unprovable): does NOT verify.
- atk_7 CANDIDATE (roundtrip_weakness rebuilds all-1 directly without composing capture_state/restore_state): shares spec AND verifies (15.0s). Behaviorally an ECHO of gold (byte-identical output). Faithful refined patch = gold patch (roundtrip is getstate then setstate; the observable result is unchanged).
- atk_8 CANDIDATE (capture_state rewritten with hoisted `n=len(ident)` loop bound, same all-0 output): shares spec AND verifies (14.3s). ECHO of gold; faithful patch = gold patch.

BOTH CANDIDATES' materialized faithful patch was RUN through run_resolve (official harness, run_id sbu-eqaudit-atk7-8tsn68eh). Executed result: RESOLVED=True, COMPLETED=True — FAIL_TO_PASS test_complete[png] success, all 181 PASS_TO_PASS success, 0 failures. Since both verifying wrong-shaped impls are behavioral echoes whose faithful patch resolves, neither is a weakness (2026-08-06 echo-attack policy: a same-spec verifying attack fails the gate ONLY if its refined patch does NOT resolve).

refinement.md A-leg audit: A2 (capture_state <-> Grouper.__getstate__, A-reference) and B2 (restore_state <-> Grouper.__setstate__, A-reference) correspond faithfully to the real callees — deref k()/v() yields direct/picklable/identity-preserving handles (flag 0); weakref.ref(k)/map(weakref.ref,vs) yields indirect/unpicklable/identity-preserving handles (flag 1). G-AX (axiom_check.py) independently validates both against real weakref.ref, weakref deref, pickle.dumps on 5 boundary + 2000 fuzz sets (exit 0). C1/C2 are I+A-reference; A1/A3/B1/B3/C3 are R. No kind-3 legs. Patch methods byte-match mapping.md §3 quotes; base_commit 66ba515e6 and F2P test_complete[png] match instance.json.

Conclusion: the postconditions fully pin the tested-relevant projection; the only verifying impls are cosmetic echoes refining to the gold patch, which resolves. verify => resolved holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. model.py verifies under pinned Nagini (13.6s). Reconstructed the true base_commit callee (matplotlib 3.7.0 Grouper, base structure {weakref.ref(x): [weakref.ref(x)] for x in init} — byte-identical to the 25332 base) and applied the gold patch's __getstate__/__setstate__ verbatim. Ran the bundle's conformance_check.py shadow (contract-stripped impl region) against this REAL patched Grouper: 0 disagreements on 100008 handle sets (8 boundary + 100000 fuzz, seed 25332), including join/merge/duplicate shapes. Slot-for-slot agreement confirmed on all three obligations: capture -> all flags 0 (real k()/v() strong refs, picklable) with cap_ident==ident (identity preserved); restore -> all flags 1 (real weakref.ref rewrap) identity preserved; round trip -> all flags 1, identity preserved. The List[int] abstraction drops grouping structure, but both real methods are dict/list comprehensions that preserve grouping verbatim and iteration order slot-for-slot, and the directness/identity projection is independent of grouping — a faithful tested-relevant projection, NOT an over-strong spec. The postconditions (Result()[k]==0 for capture, ==1 for restore/roundtrip) exactly mirror the gold patch's weakref->strong (capture) and strong->weakref (restore) transforms. No input in the Requires domain (len(weak)==len(ident)) makes the modeled function disagree with the real callee. Note: the /tmp matplotlib worktrees present were stale from OTHER instances (WeakKeyDictionary Grouper, twinx/twiny patch) and were NOT used; reconstruction from 3.7.0 source + gold patch was required and is structurally exact.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Audited the gated spec view (docstring + axioms/pure/pre/post regions, impl elided). Confirmed the computed spec_view SHA256 == the G-HYGIENE-recorded spec_view hash 5361097721a04df25cf70bea8ddd265b2af196270f546499bf1ec1cf7312a5c3, so this is the exact view the auditor sees.

Public problem_statement already discloses the essential nature of the bug AND its fix direction: pickling a figure fails after align_labels() with 'TypeError: cannot pickle weakref.ReferenceType object'; expected outcome is successful pickling. So the weakref/pickle framing — and that the fix must make the weakref-holding object serialisable — is entirely public. The gold edit (add __getstate__ converting weakrefs->strong refs, __setstate__ converting back) is the standard Python idiom that follows directly from that public report.

The spec view stays at or below the public level and reconstructs nothing beyond it:
- Behaviour is stated in fully generic vocabulary: 'indirect handle' (not serialisable) vs 'direct handle' (serialisable), 'capture for serialisation', 'restore', modelled as two parallel List[int] carriers (ident/weak).
- Function names are generic (capture_state / restore_state / roundtrip_weakness).
- Token scan of the spec view is negative for every gold-edit identifier: 'getstate', 'setstate', 'Grouper', 'cbook', '_mapping', 'align_label', 'weakref.ref', 'pickle.dumps', 'vars(self)', '__get' — none appear.

No spec-view line names the changed file, class, methods, or the concrete weakref/pickle primitives; the capture-then-restore structure is a direct consequence of the public 'cannot pickle weakref' report, not information leaked by the spec. G-LEAK (lexical) also passed with no failures. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
