# P2 adversarial audit — django__django-14787

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,6 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    bound = FuncIdentity(False, 0, method.has_module, method.module)
     return bound
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,6 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    bound = FuncIdentity(True, 0, True, method.module)
     return bound
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,6 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    bound = FuncIdentity(True, method.module, True, method.name)
     return bound
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,7 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    method.name = method.name
+    bound = FuncIdentity(True, method.name, True, method.module)
     return bound
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,9 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    if method.name == method.module:
+        bound = FuncIdentity(True, method.name, True, method.module)
+    else:
+        bound = FuncIdentity(True, method.module, True, method.name)
     return bound
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,6 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    bound = FuncIdentity(True, method.name, False, 0)
     return bound
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -29,14 +29,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FuncIdentity:
     def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it needs no room beneath it; callers (level 6) sit strictly above.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
         Ensures(Acc(self.name) and self.name == name)                  # type: ignore
         Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
@@ -66,7 +62,6 @@
     # The original method carries its identity metadata (both attributes exist).
     Requires(method.has_name)
     Requires(method.has_module)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
@@ -85,17 +80,12 @@
     Ensures(Result().module == method.module)
     # post-conditions-end
     # impl-start
-    # The assembled callable is a plain partial application that on its own
-    # exposes no function-identity metadata; the wrapper-update copies, from the
-    # method onto it, each identity attribute the method possesses. The method
-    # has both attributes (precondition), so the assembled callable ends up
-    # carrying both — its name and module marked present and equal to the
-    # method's own (the spelled-out per-attribute copy, collapsed to its result
-    # for the contracted domain).
-    has_name = method.has_name
-    name = method.name
-    has_module = method.has_module
-    module = method.module
-    bound = FuncIdentity(has_name, name, has_module, module)
+    bound = FuncIdentity(True, method.name, True, method.module)
+    if method.has_name:
+        bound.has_name = True
+        bound.name = method.name
+    if method.has_module:
+        bound.has_module = True
+        bound.module = method.module
     return bound
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14787.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a function decorator is turned into a method decorator, the callable that
  is handed to that decorator (the per-instance bound callable assembled for the
  decorated method) must carry the same function-identity metadata as the
  original method. Concretely, the standard wrapper-identity attributes — the
  callable's name and its defining module — must be present on the assembled
  callable and equal to the original method's, rather than absent.

  A freshly assembled bound callable starts with NONE of these identity
  attributes (it is a plain partial application that exposes no function
  metadata). The desired behaviour copies, from the original method onto the
  assembled callable, each identity attribute that the method possesses, so a
  decorator inspecting the callable it receives observes the method's own name
  and module.

A callable's relevant identity is modelled as a minimal class carrying the two
touched, behaviour-bearing facets — its name and its defining module — each as
a presence flag (whether the attribute exists on the object) and a value. The
original method has both attributes present; the freshly assembled bound
callable has both absent. The identity-copying step is the unchanged
standard-library wrapper-update primitive; it is modelled DEEPLY here (the
per-attribute copy is spelled out) and validated equal to the real primitive
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class FuncIdentity:
    def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
        Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
        Ensures(Acc(self.name) and self.name == name)                  # type: ignore
        Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
        Ensures(Acc(self.module) and self.module == module)            # type: ignore
        self.has_name = has_name
        self.name = name
        self.has_module = has_module
        self.module = module


# axioms-start
# (no consumed @ContractOnly axiom: the wrapper-identity copy is modelled
#  deeply below — see the impl — and validated == the real standard-library
#  primitive by axiom_check.py / G-AX as an A-reference, not consumed here.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def assemble_bound_callable(method: FuncIdentity) -> FuncIdentity:
    # pre-conditions-start
    Requires(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
    Requires(Acc(method.has_module, 1 / 2) and Acc(method.module, 1 / 2))
    # The original method carries its identity metadata (both attributes exist).
    Requires(method.has_name)
    Requires(method.has_module)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
    Ensures(Acc(method.has_module, 1 / 2) and Acc(method.module, 1 / 2))
    # The method is read-only: its identity is unchanged.
    Ensures(method.has_name == Old(method.has_name) and method.name == Old(method.name))
    Ensures(method.has_module == Old(method.has_module) and method.module == Old(method.module))
    # The assembled callable is a fresh object the caller fully owns.
    Ensures(Acc(Result().has_name) and Acc(Result().name))
    Ensures(Acc(Result().has_module) and Acc(Result().module))
    # The assembled callable carries the method's identity metadata: its name
    # and module attributes are present and equal to the method's own.
    Ensures(Result().has_name)
    Ensures(Result().has_module)
    Ensures(Result().name == method.name)
    Ensures(Result().module == method.module)
    # post-conditions-end
    # impl-start
    # The assembled callable is a plain partial application that on its own
    # exposes no function-identity metadata; the wrapper-update copies, from the
    # method onto it, each identity attribute the method possesses. The method
    # has both attributes (precondition), so the assembled callable ends up
    # carrying both — its name and module marked present and equal to the
    # method's own (the spelled-out per-attribute copy, collapsed to its result
    # for the contracted domain).
    has_name = method.has_name
    name = method.name
    has_module = method.has_module
    module = method.module
    bound = FuncIdentity(has_name, name, has_module, module)
    return bound
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit for django__django-14787 (nagini).

SPEC SHAPE: assemble_bound_callable(method: FuncIdentity) -> FuncIdentity. Postconditions fully pin the abstract result: Result().has_name, Result().has_module, Result().name == method.name, Result().module == method.module, and method is read-only (Old-equalities held under fractional Acc(method.*,1/2) so no write is permitted). Attacks edit ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical (same-spec confirmed for the candidate).

BASELINES: positive_control (=model.py impl) verifies (nagini_verify exit 0, 16.3s). prepatch (=model_prepatch.py, drops the identity copy) FAILS on prepatch.py:77 'Result().has_name might not hold' (exit 1) => bug is sensed (prepatch_reproduced=true). G-AX: `python axiom_check.py` exit 0 — deep model == real functools.wraps/update_wrapper over 6 boundary + 20000 fuzz methods; method unmodified; bare partial has no __name__.

ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14787 <path>`; direct verify cross-checked with `bash scripts/nagini_verify.sh <path>`):
- atk_1.py drop name copy (prepatch-shaped): exit 2, rejected (has_name/name).
- atk_2.py ungrounded name token FuncIdentity(True,0,...): exit 2, rejected on 'Result().name == method.name' (atk_2.py:79).
- atk_3.py swap name<->module tokens: exit 2, rejected on 'Result().name == method.name' (atk_3.py:79).
- atk_4.py control-flow-effect, writes method.name: exit 2, rejected 'insufficient permission to access method.name' (atk_4.py:83) — read-only enforced by 1/2 perm.
- atk_5.py partial-domain (correct iff name==module else swapped): exit 2, rejected on 'Result().name == method.name' (atk_5.py:79).
- atk_6.py boundary, module absent FuncIdentity(True,name,False,0): exit 2, rejected on 'Result().has_module' (atk_6.py:78).
- atk_7.py faithful gold-equivalent echo: constructs the fresh result then guarded per-attribute copy (if method.has_name: bound.has_name=True; bound.name=method.name; likewise module) — exactly the deep-model A3 == update_wrapper. weakness exit 0 = CANDIDATE (shares spec AND verifies, 16.2s); same-spec exit 0 SAME.

MANDATORY CANDIDATE RESOLVE: atk_7 is behaviourally identical to gold (copies both present facets onto a fresh callable, method unchanged), so its faithful refined patch IS the gold hunk (decorators.py:40, partial(...) -> wraps(method)(partial(...))). Materialized as atk_7_faithful_patch.diff and RUN through the official harness: `run_resolve('django__django-14787', patch)` => RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. So the only verifying candidate's faithful patch DOES resolve — not a weakness (resolving gold echo, per G-PANEL-1/eq policy).

REFINEMENT AUDIT (refinement.md): meta.json axioms=[] (no consumed @ContractOnly axiom). Legs A1,A2,A4 = R (type refinement of the method arg, the bare partial as all-absent FuncIdentity, and the returned assembled callable). Leg A3 = A-reference: the spelled-out per-attribute copy is the DEEP model of functools.update_wrapper/wraps, validated == the real callee by axiom_check.py/G-AX (passes). No kind-3 (unexpressible-changed-op) legs; the operation under change (the _wrapper assembly) is modelled deeply, not axiomatized. A-reference correspondence to the real callee holds (WRAPPER_ASSIGNMENTS includes __name__,__module__; copy + read-only confirmed by G-AX).

CONCLUSION: 7 distinct attacks executed (partial-domain, boundary, control-flow-effect/mutation, ungrounded-oracle echo, token-swap, prepatch bug, faithful gold echo). The 6 wrong impls are all rejected on their intended discriminating postconditions; the sole verifying candidate's materialized faithful patch resolves under the official harness. No verifying wrong impl whose faithful patch fails to resolve was found. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14787.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a function decorator is turned into a method decorator, the callable that
  is handed to that decorator (the per-instance bound callable assembled for the
  decorated method) must carry the same function-identity metadata as the
  original method. Concretely, the standard wrapper-identity attributes — the
  callable's name and its defining module — must be present on the assembled
  callable and equal to the original method's, rather than absent.

  A freshly assembled bound callable starts with NONE of these identity
  attributes (it is a plain partial application that exposes no function
  metadata). The desired behaviour copies, from the original method onto the
  assembled callable, each identity attribute that the method possesses, so a
  decorator inspecting the callable it receives observes the method's own name
  and module.

A callable's relevant identity is modelled as a minimal class carrying the two
touched, behaviour-bearing facets — its name and its defining module — each as
a presence flag (whether the attribute exists on the object) and a value. The
original method has both attributes present; the freshly assembled bound
callable has both absent. The identity-copying step is the unchanged
standard-library wrapper-update primitive; it is modelled DEEPLY here (the
per-attribute copy is spelled out) and validated equal to the real primitive
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class FuncIdentity:
    def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
        Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
        Ensures(Acc(self.name) and self.name == name)                  # type: ignore
        Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
        Ensures(Acc(self.module) and self.module == module)            # type: ignore
        self.has_name = has_name
        self.name = name
        self.has_module = has_module
        self.module = module


# axioms-start
# (no consumed @ContractOnly axiom: the wrapper-identity copy is modelled
#  deeply below — see the impl — and validated == the real standard-library
#  primitive by axiom_check.py / G-AX as an A-reference, not consumed here.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def assemble_bound_callable(method: FuncIdentity) -> FuncIdentity:
    # pre-conditions-start
    Requires(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
    Requires(Acc(method.has_module, 1 / 2) and Acc(method.module, 1 / 2))
    # The original method carries its identity metadata (both attributes exist).
    Requires(method.has_name)
    Requires(method.has_module)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
    Ensures(Acc(method.has_module, 1 / 2) and Acc(method.module, 1 / 2))
    # The method is read-only: its identity is unchanged.
    Ensures(method.has_name == Old(method.has_name) and method.name == Old(method.name))
    Ensures(method.has_module == Old(method.has_module) and method.module == Old(method.module))
    # The assembled callable is a fresh object the caller fully owns.
    Ensures(Acc(Result().has_name) and Acc(Result().name))
    Ensures(Acc(Result().has_module) and Acc(Result().module))
    # The assembled callable carries the method's identity metadata: its name
    # and module attributes are present and equal to the method's own.
    Ensures(Result().has_name)
    Ensures(Result().has_module)
    Ensures(Result().name == method.name)
    Ensures(Result().module == method.module)
    # post-conditions-end
    # impl-start
    # The assembled callable is a plain partial application that on its own
    # exposes no function-identity metadata; the wrapper-update copies, from the
    # method onto it, each identity attribute the method possesses. The method
    # has both attributes (precondition), so the assembled callable ends up
    # carrying both — its name and module marked present and equal to the
    # method's own (the spelled-out per-attribute copy, collapsed to its result
    # for the contracted domain).
    has_name = method.has_name
    name = method.name
    has_module = method.has_module
    module = method.module
    bound = FuncIdentity(has_name, name, has_module, module)
    return bound
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit for django__django-14787 (nagini).

SPEC SHAPE: assemble_bound_callable(method: FuncIdentity) -> FuncIdentity. Postconditions fully pin the abstract result: Result().has_name, Result().has_module, Result().name == method.name, Result().module == method.module, and method is read-only (Old-equalities held under fractional Acc(method.*,1/2) so no write is permitted). Attacks edit ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical (same-spec confirmed for the candidate).

BASELINES: positive_control (=model.py impl) verifies (nagini_verify exit 0, 16.3s). prepatch (=model_prepatch.py, drops the identity copy) FAILS on prepatch.py:77 'Result().has_name might not hold' (exit 1) => bug is sensed (prepatch_reproduced=true). G-AX: `python axiom_check.py` exit 0 — deep model == real functools.wraps/update_wrapper over 6 boundary + 20000 fuzz methods; method unmodified; bare partial has no __name__.

ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14787 <path>`; direct verify cross-checked with `bash scripts/nagini_verify.sh <path>`):
- atk_1.py drop name copy (prepatch-shaped): exit 2, rejected (has_name/name).
- atk_2.py ungrounded name token FuncIdentity(True,0,...): exit 2, rejected on 'Result().name == method.name' (atk_2.py:79).
- atk_3.py swap name<->module tokens: exit 2, rejected on 'Result().name == method.name' (atk_3.py:79).
- atk_4.py control-flow-effect, writes method.name: exit 2, rejected 'insufficient permission to access method.name' (atk_4.py:83) — read-only enforced by 1/2 perm.
- atk_5.py partial-domain (correct iff name==module else swapped): exit 2, rejected on 'Result().name == method.name' (atk_5.py:79).
- atk_6.py boundary, module absent FuncIdentity(True,name,False,0): exit 2, rejected on 'Result().has_module' (atk_6.py:78).
- atk_7.py faithful gold-equivalent echo: constructs the fresh result then guarded per-attribute copy (if method.has_name: bound.has_name=True; bound.name=method.name; likewise module) — exactly the deep-model A3 == update_wrapper. weakness exit 0 = CANDIDATE (shares spec AND verifies, 16.2s); same-spec exit 0 SAME.

MANDATORY CANDIDATE RESOLVE: atk_7 is behaviourally identical to gold (copies both present facets onto a fresh callable, method unchanged), so its faithful refined patch IS the gold hunk (decorators.py:40, partial(...) -> wraps(method)(partial(...))). Materialized as atk_7_faithful_patch.diff and RUN through the official harness: `run_resolve('django__django-14787', patch)` => RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. So the only verifying candidate's faithful patch DOES resolve — not a weakness (resolving gold echo, per G-PANEL-1/eq policy).

REFINEMENT AUDIT (refinement.md): meta.json axioms=[] (no consumed @ContractOnly axiom). Legs A1,A2,A4 = R (type refinement of the method arg, the bare partial as all-absent FuncIdentity, and the returned assembled callable). Leg A3 = A-reference: the spelled-out per-attribute copy is the DEEP model of functools.update_wrapper/wraps, validated == the real callee by axiom_check.py/G-AX (passes). No kind-3 (unexpressible-changed-op) legs; the operation under change (the _wrapper assembly) is modelled deeply, not axiomatized. A-reference correspondence to the real callee holds (WRAPPER_ASSIGNMENTS includes __name__,__module__; copy + read-only confirmed by G-AX).

CONCLUSION: 7 distinct attacks executed (partial-domain, boundary, control-flow-effect/mutation, ungrounded-oracle echo, token-swap, prepatch bug, faithful gold echo). The 6 wrong impls are all rejected on their intended discriminating postconditions; the sole verifying candidate's materialized faithful patch resolves under the official harness. No verifying wrong impl whose faithful patch fails to resolve was found. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec exit 0). The modeled assemble_bound_callable, on its defended domain (precondition: method.has_name ∧ method.has_module — a real method reached via __get__ always carries __name__/__module__), agrees with the real repo's post-patch behavior: the gold patch wraps the bare partial via wraps(method)(...) ⇒ functools.update_wrapper, which copies __name__/__module__ onto the assembled callable and leaves the method unchanged. The model's postconditions (Result().has_name, Result().name==method.name, Result().has_module, Result().module==method.module, and read-only method) exactly mirror this. Independent verification: (a) 200k randomized fuzz of the model's asserted postconditions vs. the real functools.update_wrapper over fuzzed name/module tokens → 0 disagreements; (b) G-AX passes (20006 fixtures, real functools); (c) G-CONF passes (100011 checks, 0 disagreements, seed 14787). The str→(presence,int-token) refinement is faithful for the F2P observations (equality-to-method-name and module-not-None). No input in the contracted domain makes the modeled function diverge from the real callee. Precondition is not over-strong — it matches repo reality and correctly excludes the degenerate no-metadata case that never arises for a bound method. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view scope: G-LEAK/panel-3 screens the CONSUMER spec view = spec_view(model.py) with impl elided (docstring + FuncIdentity class + assemble_bound_callable pre/post-conditions). refinement.md and mapping.md (which DO name decorators.py:40, _wrapper, method_decorator, quote the gold hunk `wraps(method)(partial(...))`) are auditor docs, NOT part of the solver-visible spec view, so they are out of scope. Mechanical screen: leakage.screen() PASSES (no hard failures); only patch-changed distinctive symbol is 'wrapper' (from _wrapper), which does not appear in the spec view. Semantic check vs public problem_statement: the problem_statement is highly explicit — title 'method_decorator() should preserve wrapper assignments', body states the callable passed to the decorator 'is a partial object and does not have any of the attributes expected from a function i.e. __name__, __module__', shows `@wraps(func)` in the example, and gives the exact `AttributeError: 'functools.partial' object has no attribute '__name__'`. Everything the spec view discloses is already public: (1) the assembled callable is a partial exposing no name/module metadata; (2) it must carry name+module equal to the original method (== 'preserve wrapper assignments'); (3) an unchanged standard-library wrapper-update primitive copies the identity attributes (== the public `@wraps` usage). The spec view does NOT quote the gold line, does NOT name the patched file path django/utils/decorators.py, does NOT name repo symbols (_multi_decorate/_wrapper/method_decorator), uses only abstract names (assemble_bound_callable, FuncIdentity), and contains no diff markers or bug/fix narration. No spec-view line reveals the gold edit beyond what the problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
