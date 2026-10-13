# P2 adversarial audit — scikit-learn__scikit-learn-26323

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
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -109,20 +107,15 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
         c = children[i]
         if is_configurable(c):
             c.cfg = requested
         i = i + 1
-    if is_configurable(leftover):
-        leftover.cfg = requested
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -98,7 +96,7 @@
     # post-conditions-end
     # impl-start
     i = 0
-    while i < len(children):
+    while i < len(children) - 1:
         # invariants-start
         Invariant(Acc(list_pred(children)))
         Invariant(len(children) == Old(len(children)))
@@ -109,15 +107,12 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
         c = children[i]
         if is_configurable(c):
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -109,20 +107,15 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
         c = children[i]
-        if is_configurable(c):
-            c.cfg = requested
+        c.cfg = requested
         i = i + 1
-    if is_configurable(leftover):
-        leftover.cfg = requested
+    leftover.cfg = requested
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -109,19 +107,13 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
-        c = children[i]
-        if is_configurable(c):
-            c.cfg = requested
         i = i + 1
     if is_configurable(leftover):
         leftover.cfg = requested
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -109,20 +107,16 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
         c = children[i]
         if is_configurable(c):
             c.cfg = requested
         i = i + 1
-    if is_configurable(leftover):
-        leftover.cfg = requested
+    leftover.cfg = requested
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -109,20 +107,17 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
         c = children[i]
         if is_configurable(c):
             c.cfg = requested
         i = i + 1
-    if is_configurable(leftover):
+    if len(children) > 0 and is_configurable(leftover):
         leftover.cfg = requested
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(leftover.cfg == 0)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             leftover is not children[k]), [[children[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(children)))
@@ -97,6 +95,8 @@
     Ensures(Implies(leftover.kind == 0, leftover.cfg == 0))
     # post-conditions-end
     # impl-start
+    if is_configurable(leftover):
+        leftover.cfg = requested
     i = 0
     while i < len(children):
         # invariants-start
@@ -109,20 +109,15 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  children[k].kind == Old(children[k].kind))
                                          , [[children[k]]])))
-        # children already visited: estimators configured, sentinels still unset
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                  children[k].cfg == requested), [[children[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                  children[k].cfg == 0), [[children[k]]])))
-        # children not yet visited: still at their unconfigured default
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                  children[k].cfg == 0), [[children[k]]])))
-        Invariant(MustTerminate(len(children) - i + 1))
         # invariants-end
         c = children[i]
         if is_configurable(c):
             c.cfg = requested
         i = i + 1
-    if is_configurable(leftover):
-        leftover.cfg = requested
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-26323.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite transformer propagates an output-container configuration to its
  child transformers. The configuration must reach EVERY child that is an
  actual estimator -- including the child that handles the columns left over
  after the explicitly-listed children have claimed theirs. Children that are
  not estimators but mere routing sentinels (the "pass the columns through
  unchanged" and "discard the columns" markers) carry no output container and
  are left untouched.

  Concretely, after the configuration call:
    * every explicitly-listed child that is an estimator has its output code
      set to the requested code;
    * the leftover-columns child, when it too is an estimator, has its output
      code set to the requested code as well;
    * every sentinel child keeps whatever it had (it is never configured).

A child is modelled as a small object exposing two observable fields: a `kind`
flag distinguishing a configurable estimator (1) from a routing sentinel (0),
and `cfg`, the integer code of the output container currently configured on it
(a distinguished value 0 meaning "unconfigured / default"). The requested
output code is an integer.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none) The configuration propagation is modelled deeply; the per-child
# configuration primitive is a plain field write, so there is no unchanged
# opaque callee consumed as an axiom (see refinement.md A-reference rows).
# axioms-end


# pure-start
class Child:
    def __init__(self, kind: int, cfg: int) -> None:
        Requires(kind == 0 or kind == 1)
        Ensures(Acc(self.kind) and Acc(self.cfg))
        Ensures(self.kind == kind and self.cfg == cfg)
        self.kind = kind  # type: int  # 1 == configurable estimator, 0 == sentinel
        self.cfg = cfg    # type: int  # configured output code; 0 == default/unset


@Pure
def is_configurable(c: Child) -> bool:
    Requires(Acc(c.kind, 1 / 4))
    return c.kind == 1
# pure-end


def configure_output(children: List[Child], leftover: Child, requested: int) -> None:
    # pre-conditions-start
    # `requested` is a genuine output-container code, distinct from the
    # distinguished UNSET code 0, so a child that was configured is observably
    # different from one left at its default.
    Requires(requested != 0)
    Requires(Acc(list_pred(children)))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             Acc(children[k].kind) and Acc(children[k].cfg))
                                     , [[children[k]]])))
    # entering this configuration step, no child carries a container yet
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            children[k].cfg == 0), [[children[k]]])))
    Requires(Acc(leftover.kind) and Acc(leftover.cfg))
    Requires(leftover.cfg == 0)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            leftover is not children[k]), [[children[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(children)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            Acc(children[k].kind) and Acc(children[k].cfg))
                                    , [[children[k]]])))
    Ensures(Acc(leftover.kind) and Acc(leftover.cfg))
    Ensures(len(children) == Old(len(children)))
    # the kind classification of every child is preserved
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                           children[k].kind == Old(children[k].kind))
                                   , [[children[k]]])))
    Ensures(leftover.kind == Old(leftover.kind))
    # every explicitly-listed estimator child carries the requested container;
    # every sentinel child remains unconfigured (it is never set up)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children) and children[k].kind == 1,
                                           children[k].cfg == requested), [[children[k]]])))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children) and children[k].kind == 0,
                                           children[k].cfg == 0), [[children[k]]])))
    # the leftover-columns child: configured iff it is an estimator, else left
    # unconfigured -- this is the clause the leftover-columns handling must meet
    Ensures(Implies(leftover.kind == 1, leftover.cfg == requested))
    Ensures(Implies(leftover.kind == 0, leftover.cfg == 0))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(children):
        # invariants-start
        Invariant(Acc(list_pred(children)))
        Invariant(len(children) == Old(len(children)))
        Invariant(0 <= i and i <= len(children))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  Acc(children[k].kind) and Acc(children[k].cfg))
                                          , [[children[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                 children[k].kind == Old(children[k].kind))
                                         , [[children[k]]])))
        # children already visited: estimators configured, sentinels still unset
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                 children[k].cfg == requested), [[children[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                 children[k].cfg == 0), [[children[k]]])))
        # children not yet visited: still at their unconfigured default
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                 children[k].cfg == 0), [[children[k]]])))
        # invariants-end
        c = children[i]
        if is_configurable(c):
            c.cfg = requested
        i = i + 1
    if is_configurable(leftover):
        leftover.cfg = requested
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins the post-state: all children start at cfg==0 (Requires), and the postconditions fix the final cfg of EVERY listed child and the leftover purely by kind (kind==1 => cfg==requested; kind==0 => cfg==0), plus kind-preservation and len-preservation. So any impl verifying against this byte-identical spec produces exactly the gold observable configuration on the modeled (unfitted) domain.

Protocol: 7 same-spec attacks (same-spec exit 0 for all; pos also same-spec) built by editing ONLY the impl region of model.py; verified concurrently in batches of <=3 JVM jobs.
 Command per attack: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-26323 atk_N.py` (run with the swebench-lean venv python).

Results:
- atk_1 prepatch bug (drop the leftover write): weakness exit 2 — verification FAILED, spec catches it (postcondition Implies(leftover.kind==1, leftover.cfg==requested) unmet). prepatch_reproduced=true.
- atk_2 boundary/off-by-one (loop `while i < len(children)-1`, last child missed): exit 2 — rejected.
- atk_3 control-flow-effect (configure everything incl sentinels, no guard): exit 2 — rejected (sentinel-unchanged postcondition unmet).
- atk_4 partial-domain (loop body no-op, children never configured): exit 2 — rejected.
- atk_5 ungrounded-oracle echo (children correct, leftover configured UNCONDITIONALLY): exit 2 — rejected (Implies(leftover.kind==0, leftover.cfg==0) unmet).
- atk_6 partial-domain (leftover configured only when len(children)>0): exit 2 — rejected.
- atk_7 reorder (configure leftover FIRST, then loop over children) — semantically equal to gold since leftover is distinct from every listed child (Requires leftover is not children[k]): weakness exit 0 = CANDIDATE (shares spec AND verifies, 27.2s).
- pos (correct impl = model.py verbatim): weakness exit 0 = verifies (positive control).

Mandatory candidate->resolve: atk_7 is the only verifying wrong-shaped (reordered) impl. Materialized its faithful refined patch (guarded remainder write inserted BEFORE the transformers loop instead of after — the only faithful refinement of leftover-first) at atk_7.patch and ran the OFFICIAL harness: `run_resolve('scikit-learn__scikit-learn-26323', patch)` => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. The candidate's patch RESOLVES, so it does NOT break the spec.

refinement.md audit: legs A1=R, A2=R+A-reference, A3=R+A-reference (behaviour-bearing), A4=I. No kind-3 (unexpressible-changed-op) steps; axioms region empty (no consumed @ContractOnly axioms) — confirmed in model.py. A-reference correspondence holds and is executable: axiom_check.py runs the REAL callees — check_safe_set_output_primitive (real _safe_set_output records requested container on StandardScaler for both 'pandas'/'default'), check_sentinel_classification ('passthrough'/'drop' excluded, StandardScaler/VarianceThreshold included), and check_composite_behaviour_estimator_remainder (end-to-end issue reproducer: leftover VarianceThreshold estimator preserved as DataFrame under set_output('pandas')). These map exactly to A2/A3.

No verifying same-spec impl whose faithful patch fails to resolve was found; the single candidate resolves. verify => correct holds on this bundle.

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
"""Twin-artifact model for scikit-learn__scikit-learn-26323.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite transformer propagates an output-container configuration to its
  child transformers. The configuration must reach EVERY child that is an
  actual estimator -- including the child that handles the columns left over
  after the explicitly-listed children have claimed theirs. Children that are
  not estimators but mere routing sentinels (the "pass the columns through
  unchanged" and "discard the columns" markers) carry no output container and
  are left untouched.

  Concretely, after the configuration call:
    * every explicitly-listed child that is an estimator has its output code
      set to the requested code;
    * the leftover-columns child, when it too is an estimator, has its output
      code set to the requested code as well;
    * every sentinel child keeps whatever it had (it is never configured).

A child is modelled as a small object exposing two observable fields: a `kind`
flag distinguishing a configurable estimator (1) from a routing sentinel (0),
and `cfg`, the integer code of the output container currently configured on it
(a distinguished value 0 meaning "unconfigured / default"). The requested
output code is an integer.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none) The configuration propagation is modelled deeply; the per-child
# configuration primitive is a plain field write, so there is no unchanged
# opaque callee consumed as an axiom (see refinement.md A-reference rows).
# axioms-end


# pure-start
class Child:
    def __init__(self, kind: int, cfg: int) -> None:
        Requires(kind == 0 or kind == 1)
        Ensures(Acc(self.kind) and Acc(self.cfg))
        Ensures(self.kind == kind and self.cfg == cfg)
        self.kind = kind  # type: int  # 1 == configurable estimator, 0 == sentinel
        self.cfg = cfg    # type: int  # configured output code; 0 == default/unset


@Pure
def is_configurable(c: Child) -> bool:
    Requires(Acc(c.kind, 1 / 4))
    return c.kind == 1
# pure-end


def configure_output(children: List[Child], leftover: Child, requested: int) -> None:
    # pre-conditions-start
    # `requested` is a genuine output-container code, distinct from the
    # distinguished UNSET code 0, so a child that was configured is observably
    # different from one left at its default.
    Requires(requested != 0)
    Requires(Acc(list_pred(children)))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             Acc(children[k].kind) and Acc(children[k].cfg))
                                     , [[children[k]]])))
    # entering this configuration step, no child carries a container yet
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            children[k].cfg == 0), [[children[k]]])))
    Requires(Acc(leftover.kind) and Acc(leftover.cfg))
    Requires(leftover.cfg == 0)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            leftover is not children[k]), [[children[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(children)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            Acc(children[k].kind) and Acc(children[k].cfg))
                                    , [[children[k]]])))
    Ensures(Acc(leftover.kind) and Acc(leftover.cfg))
    Ensures(len(children) == Old(len(children)))
    # the kind classification of every child is preserved
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                           children[k].kind == Old(children[k].kind))
                                   , [[children[k]]])))
    Ensures(leftover.kind == Old(leftover.kind))
    # every explicitly-listed estimator child carries the requested container;
    # every sentinel child remains unconfigured (it is never set up)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children) and children[k].kind == 1,
                                           children[k].cfg == requested), [[children[k]]])))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children) and children[k].kind == 0,
                                           children[k].cfg == 0), [[children[k]]])))
    # the leftover-columns child: configured iff it is an estimator, else left
    # unconfigured -- this is the clause the leftover-columns handling must meet
    Ensures(Implies(leftover.kind == 1, leftover.cfg == requested))
    Ensures(Implies(leftover.kind == 0, leftover.cfg == 0))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(children):
        # invariants-start
        Invariant(Acc(list_pred(children)))
        Invariant(len(children) == Old(len(children)))
        Invariant(0 <= i and i <= len(children))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  Acc(children[k].kind) and Acc(children[k].cfg))
                                          , [[children[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                 children[k].kind == Old(children[k].kind))
                                         , [[children[k]]])))
        # children already visited: estimators configured, sentinels still unset
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                 children[k].cfg == requested), [[children[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                 children[k].cfg == 0), [[children[k]]])))
        # children not yet visited: still at their unconfigured default
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                 children[k].cfg == 0), [[children[k]]])))
        # invariants-end
        c = children[i]
        if is_configurable(c):
            c.cfg = requested
        i = i + 1
    if is_configurable(leftover):
        leftover.cfg = requested
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins the post-state: all children start at cfg==0 (Requires), and the postconditions fix the final cfg of EVERY listed child and the leftover purely by kind (kind==1 => cfg==requested; kind==0 => cfg==0), plus kind-preservation and len-preservation. So any impl verifying against this byte-identical spec produces exactly the gold observable configuration on the modeled (unfitted) domain.

Protocol: 7 same-spec attacks (same-spec exit 0 for all; pos also same-spec) built by editing ONLY the impl region of model.py; verified concurrently in batches of <=3 JVM jobs.
 Command per attack: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-26323 atk_N.py` (run with the swebench-lean venv python).

Results:
- atk_1 prepatch bug (drop the leftover write): weakness exit 2 — verification FAILED, spec catches it (postcondition Implies(leftover.kind==1, leftover.cfg==requested) unmet). prepatch_reproduced=true.
- atk_2 boundary/off-by-one (loop `while i < len(children)-1`, last child missed): exit 2 — rejected.
- atk_3 control-flow-effect (configure everything incl sentinels, no guard): exit 2 — rejected (sentinel-unchanged postcondition unmet).
- atk_4 partial-domain (loop body no-op, children never configured): exit 2 — rejected.
- atk_5 ungrounded-oracle echo (children correct, leftover configured UNCONDITIONALLY): exit 2 — rejected (Implies(leftover.kind==0, leftover.cfg==0) unmet).
- atk_6 partial-domain (leftover configured only when len(children)>0): exit 2 — rejected.
- atk_7 reorder (configure leftover FIRST, then loop over children) — semantically equal to gold since leftover is distinct from every listed child (Requires leftover is not children[k]): weakness exit 0 = CANDIDATE (shares spec AND verifies, 27.2s).
- pos (correct impl = model.py verbatim): weakness exit 0 = verifies (positive control).

Mandatory candidate->resolve: atk_7 is the only verifying wrong-shaped (reordered) impl. Materialized its faithful refined patch (guarded remainder write inserted BEFORE the transformers loop instead of after — the only faithful refinement of leftover-first) at atk_7.patch and ran the OFFICIAL harness: `run_resolve('scikit-learn__scikit-learn-26323', patch)` => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. The candidate's patch RESOLVES, so it does NOT break the spec.

refinement.md audit: legs A1=R, A2=R+A-reference, A3=R+A-reference (behaviour-bearing), A4=I. No kind-3 (unexpressible-changed-op) steps; axioms region empty (no consumed @ContractOnly axioms) — confirmed in model.py. A-reference correspondence holds and is executable: axiom_check.py runs the REAL callees — check_safe_set_output_primitive (real _safe_set_output records requested container on StandardScaler for both 'pandas'/'default'), check_sentinel_classification ('passthrough'/'drop' excluded, StandardScaler/VarianceThreshold included), and check_composite_behaviour_estimator_remainder (end-to-end issue reproducer: leftover VarianceThreshold estimator preserved as DataFrame under set_output('pandas')). These map exactly to A2/A3.

No verifying same-spec impl whose faithful patch fails to resolve was found; the single candidate resolves. verify => correct holds on this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness assessment for the modeled function `configure_output` (models ColumnTransformer.set_output propagation). Spec: sets cfg==requested for every child/leftover with kind==1, leaves kind==0 (sentinels) unconfigured; deep-model write `cfg=requested` abstracts `_safe_set_output(trans, transform=transform)`, guard `is_configurable` abstracts `trans not in {'passthrough','drop'}`.

FACT-BASED RE-RUN: The swebench-lean env (sklearn 1.3.0) contains the patched real `set_output` (`if self.remainder not in {'passthrough','drop'}: _safe_set_output(self.remainder, transform=transform)`). I re-ran the bundle's own conformance harness (byte-copied) against the REAL repo callee: `G-CONF OK: shadow impl == real configuration propagation on 100248 inputs (248 boundary + 100000 fuzz, seed 26323), 0 disagreements.` So over the entire modeled domain (real transformer children/remainder using the standard `_sklearn_output_config` record), the modeled function agrees exactly with the real callee. Probed 8 common real transformers (StandardScaler, Normalizer, MaxAbsScaler, MinMaxScaler, VarianceThreshold, PCA, OneHotEncoder, KBinsDiscretizer): all get cfg==requested from real `_safe_set_output` — zero divergences.

BOUNDARY NOTE (not a defect): the prose gloss `kind==1 <-> 'an estimator object'` slightly over-approximates the word 'estimator'. A non-transformer estimator (e.g. LogisticRegression) is `not in {'passthrough','drop'}` (would nominally map to kind==1) yet real `_safe_set_output` early-returns and records NO config (verified: `_sklearn_output_config` stays None). This is a documentation over-approximation, NOT a spec-too-strong defect: (1) mapping.md §2 and the conformance pool bind kind==1 to standard-record TRANSFORMER instances, not arbitrary estimators; (2) a non-transformer child/remainder is outside the modeled/tested domain — such a ColumnTransformer does not resolve (fails at fit_transform), so it cannot produce a false green; (3) within the documented domain the abstraction holds on every input tested. verify(model) => resolve is preserved. Spec matches real behavior on all in-domain inputs.

Gates cross-checked: G-AX pass (real _safe_set_output + sentinel classification + end-to-end reproducer), G-DIFF pass (model_prepatch drops A3 leftover write and fails postcondition), G-EQ pass (8 attacks, none break spec). Spec region confirmed via bundle markers; no evidence the spec is too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (leakage.screen: hard_failures=[], passed=True); only patched symbol is 'set_output', which is already public via the problem_statement title. Semantic review of the full spec view (spec_view over model.py) confirms NO leak beyond the public problem_statement: (1) The public issue already names the method (`ColumnTransformer.set_output`), the `remainder`, the exact failure ('ignores the remainder if it's an estimator'), the expected corrected behavior, AND links the source file — so the desired behavior is fully public. (2) The spec view states this behavior abstractly as a requirement, not an edit: 'the configuration must reach EVERY child that is an actual estimator -- including the child that handles the columns left over', with sentinels left untouched. This is co-extensive with the public issue, not additional edit localization. (3) Carrier names are neutral (configure_output, Child, is_configurable, leftover, requested/cfg/kind) — none echoes the patched repo symbols (`remainder`, `_safe_set_output`) or the sentinel string literals `"passthrough"`/`"drop"`; those are only paraphrased ('pass the columns through unchanged'/'discard the columns'), which is standard ColumnTransformer domain knowledge. (4) No diff markers, no patched file path/module, no reproduced gold-patch line, no verbatim patched symbol in identifiers or comments. The A3 postcondition (Implies(leftover.kind==1, leftover.cfg==requested)) is the spec sensing the desired behavior, which any faithful spec must express — it restates the public bug as a requirement, not the gold edit's specifics. No RELAXED_LEAKAGE deferral needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
