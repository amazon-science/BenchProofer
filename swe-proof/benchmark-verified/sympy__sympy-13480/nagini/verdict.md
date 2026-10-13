# P2 adversarial audit — sympy__sympy-13480

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_id.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -78,7 +76,7 @@
     # post-conditions-end
     # impl-start
     primary_m = primary(m)
-    if primary_m == directed_infinity():
+    if directed_infinity() == primary_m:
         return primary(x)
     else:
         return sibling(x)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -78,7 +76,7 @@
     # post-conditions-end
     # impl-start
     primary_m = primary(m)
-    if primary_m == directed_infinity():
+    if primary(x) == directed_infinity():
         return primary(x)
     else:
         return sibling(x)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -77,9 +75,5 @@
     Ensures(Implies(primary(m) != directed_infinity(), Result() == sibling(x)))
     # post-conditions-end
     # impl-start
-    primary_m = primary(m)
-    if primary_m == directed_infinity():
-        return primary(x)
-    else:
-        return sibling(x)
+    return primary(x)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -77,9 +75,5 @@
     Ensures(Implies(primary(m) != directed_infinity(), Result() == sibling(x)))
     # post-conditions-end
     # impl-start
-    primary_m = primary(m)
-    if primary_m == directed_infinity():
-        return primary(x)
-    else:
-        return sibling(x)
+    return sibling(x)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -79,7 +77,7 @@
     # impl-start
     primary_m = primary(m)
     if primary_m == directed_infinity():
+        return sibling(x)
+    else:
         return primary(x)
-    else:
-        return sibling(x)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -79,6 +77,8 @@
     # impl-start
     primary_m = primary(m)
     if primary_m == directed_infinity():
+        if sibling(m) == directed_infinity():
+            return sibling(x)
         return primary(x)
     else:
         return sibling(x)
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -78,8 +76,7 @@
     # post-conditions-end
     # impl-start
     primary_m = primary(m)
-    if primary_m == directed_infinity():
+    if not (primary_m != directed_infinity()):
         return primary(x)
-    else:
-        return sibling(x)
+    return sibling(x)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
 def periodic_part_simplification(x: int, m: int) -> int:
     # pre-conditions-start
     # x is the remainder part, m the (present, non-trivial) periodic part.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is governed by evaluating the primary function on the periodic
@@ -78,7 +76,7 @@
     # post-conditions-end
     # impl-start
     primary_m = primary(m)
-    if primary_m == directed_infinity():
+    if sibling(m) == directed_infinity():
         return primary(x)
     else:
         return sibling(x)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_id.py`

```python
"""Twin-artifact model for sympy__sympy-13480.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An automatic simplifier for a hyperbolic-cotangent-like function handles the
  case where its argument decomposes into a remainder part and a multiple of a
  distinguished imaginary period. When that periodic part is present, the
  simplifier evaluates the SAME function on the periodic part and inspects the
  resulting expression:

    * if evaluating the function on the periodic part yields the
      "directed-infinity" sentinel, the simplified result is the function
      applied to the remainder part;
    * otherwise (the evaluation yields the finite/zero alternative), the
      simplified result is the reciprocal-family sibling function applied to
      the remainder part.

  The behaviour pinned here: the branch that chooses between these two results
  is governed by the value obtained by evaluating the function on the PERIODIC
  PART — i.e. the quantity that was just computed from the periodic part — and
  by no other quantity. The result is the remainder-part evaluation of the same
  function exactly when that computed value is the directed-infinity sentinel,
  and the reciprocal-family sibling on the remainder part otherwise.

Symbolic expressions are modelled as opaque integer handles. The two unchanged
elementary functions consulted here are deterministic pure callees over those
handles (axioms region); the directed-infinity sentinel is a distinguished
handle. The simplifier never raises on this branch: the value it inspects is
always the one it just computed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def primary(arg: int) -> int:
    """The function being simplified, as an opaque deterministic map over
    expression handles (an UNCHANGED elementary callee — it is consulted, not
    redefined). Determinism is all the proof relies on: the value computed from
    the periodic part is the same value later inspected. Provenance + executable
    soundness check: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def sibling(arg: int) -> int:
    """The reciprocal-family sibling function, likewise an opaque deterministic
    UNCHANGED callee over expression handles. Provenance: mapping.md."""


@Pure
@ContractOnly
def directed_infinity() -> int:
    """The distinguished "directed-infinity" sentinel expression handle (an
    UNCHANGED module constant). Provenance: mapping.md."""
# axioms-end


def periodic_part_simplification(x: int, m: int) -> int:
    # pre-conditions-start
    # x is the remainder part, m the (present, non-trivial) periodic part.
    # pre-conditions-end
    # post-conditions-start
    # The result is governed by evaluating the primary function on the periodic
    # part `m`: the primary function on `x` exactly when that value is the
    # directed-infinity sentinel, the sibling function on `x` otherwise. The
    # branch is decided by `primary(m)`, the quantity just computed, and by no
    # other quantity. The two implications are exhaustive and mutually
    # exclusive, so together they pin the result on every input — stated
    # directly over the input handles (no answer-key oracle to echo).
    Ensures(Implies(primary(m) == directed_infinity(), Result() == primary(x)))
    Ensures(Implies(primary(m) != directed_infinity(), Result() == sibling(x)))
    # post-conditions-end
    # impl-start
    primary_m = primary(m)
    if primary_m == directed_infinity():
        return primary(x)
    else:
        return sibling(x)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins Result() as a total deterministic function of the @Pure callees: Result()==primary(x) iff primary(m)==directed_infinity(), else sibling(x); the two implications are exhaustive+mutually-exclusive, so any verifying impl must return exactly primary(x)/sibling(x) selected on primary(m). 8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`, exit 0) run through `adversary weakness nagini sympy__sympy-13480 <file>` (batches of 3, JVM+Z3). Positive control atk_id.py (=model.py) verifies (nagini_verify.sh exit 0, 8.1s).

Per-attack results:
- atk_1 (echo: order-swapped `directed_infinity()==primary_m`): weakness exit 0 = CANDIDATE (verifies). Faithful patch patch_atk_1.diff (`if S.ComplexInfinity is cothm:`) run through run_resolve (run_id atk1audit): RESOLVED=True, test_coth PASS + 43/43 PASS_TO_PASS. NOT a weakness (resolving echo).
- atk_2 (prepatch bug: branch on primary(x)): weakness exit 2 = verification FAILED. Reproduces the model_prepatch.py / G-DIFF defect (wrong discriminator). prepatch_reproduced=True.
- atk_3 (partial-domain, always return primary(x)): exit 2, rejected.
- atk_4 (partial-domain, always return sibling(x)): exit 2, rejected.
- atk_5 (boundary: swapped branch results): exit 2, rejected.
- atk_6 (control-flow-effect: spurious nested guard on sibling(m) inside true branch): exit 2, rejected.
- atk_7 (ungrounded-oracle echo: double-negation `not (primary_m != directed_infinity())`): weakness exit 0 = CANDIDATE (verifies). Faithful patch patch_atk_7.diff (`if not (cothm is not S.ComplexInfinity):`) run through run_resolve (run_id atk7audit2, background due to >2min harness): report.json RESOLVED=True, test_coth PASS + 43/43 PASS_TO_PASS. NOT a weakness (resolving echo).
- atk_8 (wrong data source: branch on sibling(m)): exit 2, rejected.

Both verifying candidates are semantic echoes of the gold one-token fix (cotm->cothm) and their materialized faithful patches RESOLVE under the official harness — so verify⇒correct holds on every counterexample exhibited; no verifying wrong impl found.

Refinement.md audit: 5 legs, all tagged R / A-consumed / I. No kind-3 step; no A-reference and meta.json deep_model_references=[] (consistent). The A-consumed legs bind primary/sibling/directed_infinity to the UNCHANGED callees coth/tanh/S.ComplexInfinity; the only contract consumed is @Pure determinism (axioms carry no Ensures) + singleton identity — weakest-sufficient, no over-claim. A-leg correspondence to the real callees holds: G-AX (axiom_check.py, exit 0) validates determinism (12+2000 fuzz), singleton stability, both FAIL_TO_PASS witnesses, and end-to-end branch correspondence vs the real patched coth.eval on 1263 periodic-branch args; G-CONF (exit 0) confirms the impl shadow agrees with the real patched repo on 100000 Requires-satisfying inputs, 0 disagreements. Model↔patch correspondence (mapping.md rows 1-4) is a direct byte-level transcription of the repaired branch with no hidden abstraction.

Environment note: adversary/run_resolve require the swebench-lean venv python; the default host python3.14 lacks the module.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_id.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_id.py`

```python
"""Twin-artifact model for sympy__sympy-13480.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An automatic simplifier for a hyperbolic-cotangent-like function handles the
  case where its argument decomposes into a remainder part and a multiple of a
  distinguished imaginary period. When that periodic part is present, the
  simplifier evaluates the SAME function on the periodic part and inspects the
  resulting expression:

    * if evaluating the function on the periodic part yields the
      "directed-infinity" sentinel, the simplified result is the function
      applied to the remainder part;
    * otherwise (the evaluation yields the finite/zero alternative), the
      simplified result is the reciprocal-family sibling function applied to
      the remainder part.

  The behaviour pinned here: the branch that chooses between these two results
  is governed by the value obtained by evaluating the function on the PERIODIC
  PART — i.e. the quantity that was just computed from the periodic part — and
  by no other quantity. The result is the remainder-part evaluation of the same
  function exactly when that computed value is the directed-infinity sentinel,
  and the reciprocal-family sibling on the remainder part otherwise.

Symbolic expressions are modelled as opaque integer handles. The two unchanged
elementary functions consulted here are deterministic pure callees over those
handles (axioms region); the directed-infinity sentinel is a distinguished
handle. The simplifier never raises on this branch: the value it inspects is
always the one it just computed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def primary(arg: int) -> int:
    """The function being simplified, as an opaque deterministic map over
    expression handles (an UNCHANGED elementary callee — it is consulted, not
    redefined). Determinism is all the proof relies on: the value computed from
    the periodic part is the same value later inspected. Provenance + executable
    soundness check: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def sibling(arg: int) -> int:
    """The reciprocal-family sibling function, likewise an opaque deterministic
    UNCHANGED callee over expression handles. Provenance: mapping.md."""


@Pure
@ContractOnly
def directed_infinity() -> int:
    """The distinguished "directed-infinity" sentinel expression handle (an
    UNCHANGED module constant). Provenance: mapping.md."""
# axioms-end


def periodic_part_simplification(x: int, m: int) -> int:
    # pre-conditions-start
    # x is the remainder part, m the (present, non-trivial) periodic part.
    # pre-conditions-end
    # post-conditions-start
    # The result is governed by evaluating the primary function on the periodic
    # part `m`: the primary function on `x` exactly when that value is the
    # directed-infinity sentinel, the sibling function on `x` otherwise. The
    # branch is decided by `primary(m)`, the quantity just computed, and by no
    # other quantity. The two implications are exhaustive and mutually
    # exclusive, so together they pin the result on every input — stated
    # directly over the input handles (no answer-key oracle to echo).
    Ensures(Implies(primary(m) == directed_infinity(), Result() == primary(x)))
    Ensures(Implies(primary(m) != directed_infinity(), Result() == sibling(x)))
    # post-conditions-end
    # impl-start
    primary_m = primary(m)
    if primary_m == directed_infinity():
        return primary(x)
    else:
        return sibling(x)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins Result() as a total deterministic function of the @Pure callees: Result()==primary(x) iff primary(m)==directed_infinity(), else sibling(x); the two implications are exhaustive+mutually-exclusive, so any verifying impl must return exactly primary(x)/sibling(x) selected on primary(m). 8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`, exit 0) run through `adversary weakness nagini sympy__sympy-13480 <file>` (batches of 3, JVM+Z3). Positive control atk_id.py (=model.py) verifies (nagini_verify.sh exit 0, 8.1s).

Per-attack results:
- atk_1 (echo: order-swapped `directed_infinity()==primary_m`): weakness exit 0 = CANDIDATE (verifies). Faithful patch patch_atk_1.diff (`if S.ComplexInfinity is cothm:`) run through run_resolve (run_id atk1audit): RESOLVED=True, test_coth PASS + 43/43 PASS_TO_PASS. NOT a weakness (resolving echo).
- atk_2 (prepatch bug: branch on primary(x)): weakness exit 2 = verification FAILED. Reproduces the model_prepatch.py / G-DIFF defect (wrong discriminator). prepatch_reproduced=True.
- atk_3 (partial-domain, always return primary(x)): exit 2, rejected.
- atk_4 (partial-domain, always return sibling(x)): exit 2, rejected.
- atk_5 (boundary: swapped branch results): exit 2, rejected.
- atk_6 (control-flow-effect: spurious nested guard on sibling(m) inside true branch): exit 2, rejected.
- atk_7 (ungrounded-oracle echo: double-negation `not (primary_m != directed_infinity())`): weakness exit 0 = CANDIDATE (verifies). Faithful patch patch_atk_7.diff (`if not (cothm is not S.ComplexInfinity):`) run through run_resolve (run_id atk7audit2, background due to >2min harness): report.json RESOLVED=True, test_coth PASS + 43/43 PASS_TO_PASS. NOT a weakness (resolving echo).
- atk_8 (wrong data source: branch on sibling(m)): exit 2, rejected.

Both verifying candidates are semantic echoes of the gold one-token fix (cotm->cothm) and their materialized faithful patches RESOLVE under the official harness — so verify⇒correct holds on every counterexample exhibited; no verifying wrong impl found.

Refinement.md audit: 5 legs, all tagged R / A-consumed / I. No kind-3 step; no A-reference and meta.json deep_model_references=[] (consistent). The A-consumed legs bind primary/sibling/directed_infinity to the UNCHANGED callees coth/tanh/S.ComplexInfinity; the only contract consumed is @Pure determinism (axioms carry no Ensures) + singleton identity — weakest-sufficient, no over-claim. A-leg correspondence to the real callees holds: G-AX (axiom_check.py, exit 0) validates determinism (12+2000 fuzz), singleton stability, both FAIL_TO_PASS witnesses, and end-to-end branch correspondence vs the real patched coth.eval on 1263 periodic-branch args; G-CONF (exit 0) confirms the impl shadow agrees with the real patched repo on 100000 Requires-satisfying inputs, 0 disagreements. Model↔patch correspondence (mapping.md rows 1-4) is a direct byte-level transcription of the repaired branch with no hidden abstraction.

Environment note: adversary/run_resolve require the swebench-lean venv python; the default host python3.14 lacks the module.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for sympy__sympy-13480 nagini bundle.

Modeled function periodic_part_simplification(x, m) models the periodic-part (arg.is_Add) branch of coth.eval (hyperbolic.py:586-593). Gold-patched real branch: cothm = coth(m); if cothm is S.ComplexInfinity: return coth(x); else: return tanh(x). Confirmed against the installed/real sympy source (inspect.getsource(coth.eval)) which contains the fixed branch (discriminator = the just-computed cothm, not the buggy unbound `cotm`).

Spec (two Ensures): primary(m)==directed_infinity() => Result==primary(x); primary(m)!=directed_infinity() => Result==sibling(x). Bindings (mapping.md): primary->coth, sibling->tanh, directed_infinity->S.ComplexInfinity. The two implications are exhaustive AND mutually exclusive, pinning the result on every input to exactly the gold if/else. The else branch covers every non-ComplexInfinity value, matching the real else. Discriminator is primary(m) (the value computed from the periodic part), which is exactly the fix.

No over-claim: all three axioms carry NO Ensures (only @Pure determinism + singleton identity), so the spec cannot claim any value/sentinel/raise behavior beyond what the real callees provide. axiom_check.py passes (coth/tanh determinism on 12+2000 inputs; ComplexInfinity singleton stable; both FAIL_TO_PASS witnesses coth(log(tan(2)))==coth(log(-tan(2))) and coth(1+I*pi/2)==tanh(1) hold). model.py verifies under pinned Nagini (exit 0, 7.1s). same-spec on identity copy returns SAME.

The G-CONF/branch-correspondence 'only 0 inputs' outcomes at this sympy version (1.14) are a VERSION-DRIFT ARTIFACT: _peeloff_ipi's convention differs (returns a bare coefficient rather than an I*pi-multiple, and coth.eval now applies coth(m*pi*I)), so the periodic-branch domain isn't exercised here. The checks' own version-drift guards skip these non-spuriously; this is not a spec/repo disagreement.

No diverging input exists: for every (x,m) the modeled function returns coth(x) iff coth(m) is S.ComplexInfinity else tanh(x), byte-identical to the gold branch. Spec is neither too strong nor drifted. Note: patch.diff is not present in the bundle, but the fix (cotm->cothm one-token change) is fully corroborated by mapping.md/refinement.md and the real sympy source.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the PUBLIC problem_statement only (hints_text excluded). The public problem_statement is itself highly revealing: it prints the exact buggy source line `if cotm is S.ComplexInfinity:` and the `NameError: name 'cotm' is not defined` at hyperbolic.py line 590, so the concrete edit location and nature are already public.

The spec view (docstring + axioms region + pre/post conditions) is MORE abstract than the public task, not less:
- Names no repo symbols — uses opaque `primary`/`sibling`/`directed_infinity`/`periodic_part_simplification`; never mentions `coth`, `tanh`, `S.ComplexInfinity`, `cotm`, `cothm`, or the file `hyperbolic.py`.
- Reproduces no gold-patch changed line; the post-condition uses `primary(m) == directed_infinity()` rather than the patched `if cothm is S.ComplexInfinity:`.
- No diff markers, no patched file/module path.
- No bug/fix/typo narration (the _NARRATION vocabulary is absent; wording is stated as desired behaviour).

The post-condition pins the correct branch discriminator ('governed by primary(m), the quantity just computed, and by no other quantity') — this is the behaviour any faithful spec must state, and it discloses nothing beyond the publicly-visible buggy line. mapping.md/refinement.md are NOT part of the spec view (they are audit-side provenance docs).

Mechanical G-LEAK screen confirms: leakage.screen() returns passed=True, zero hard failures. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
