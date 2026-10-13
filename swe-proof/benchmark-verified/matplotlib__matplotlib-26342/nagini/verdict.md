# P2 adversarial audit — matplotlib__matplotlib-26342

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,5 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
-    self.items = new_items
-    self.out_of_date = True
+    pass
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -82,5 +80,4 @@
     # post-conditions-end
     # impl-start
     self.items = new_items
-    self.out_of_date = True
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,5 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
-    self.items = new_items
     self.out_of_date = True
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,6 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
-    self.items = new_items
+    self.items = list(new_items)
     self.out_of_date = True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,7 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
-    self.items = new_items
-    self.out_of_date = True
+    if len(new_items) > 0:
+        self.items = new_items
+        self.out_of_date = True
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -83,4 +81,5 @@
     # impl-start
     self.items = new_items
     self.out_of_date = True
+    self.out_of_date = False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -82,5 +80,5 @@
     # post-conditions-end
     # impl-start
     self.items = new_items
-    self.out_of_date = True
+    self.out_of_date = False
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,9 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
-    self.items = new_items
-    self.out_of_date = True
+    if len(new_items) >= 1:
+        self.items = new_items
+        self.out_of_date = True
+    else:
+        self.out_of_date = True
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,6 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
+    self.out_of_date = True
     self.items = new_items
-    self.out_of_date = True
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # The supplied sequence is read-only: required at fractional permission so
     # the operation may not rewrite its element contents.
     Requires(Acc(list_pred(new_items), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.items))
@@ -81,6 +79,7 @@
                                            new_items[k] == Old(new_items[k])))))
     # post-conditions-end
     # impl-start
-    self.items = new_items
+    tmp = new_items
+    self.items = tmp
     self.out_of_date = True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26342.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawable collection of geometry carries a sequence of geometry items and a
  flag recording whether its cached rendering is out of date. Installing a new
  sequence of geometry onto such a collection must, once the call returns,

    (1) make the collection hand back EXACTLY the sequence object that was
        supplied — a subsequent query for the collection's geometry returns the
        very same object, by identity, so a caller that supplied a prepared
        sequence sees that prepared sequence (and only it) used afterwards; and

    (2) mark the collection's cached rendering as out of date, so the next draw
        recomputes from the freshly installed geometry.

  The supplied sequence is read-only to this operation: its element contents are
  not altered (the operation stores the reference, it does not rewrite items),
  and no element is added or removed.

The collection is modelled as a minimal object exposing only the two touched
fields: the held geometry sequence (an object reference) and the out-of-date
flag (a bool). The geometry sequence is modelled as a `List[int]` of opaque
per-item identity tokens; reference identity of the stored sequence is carried
by Nagini's `is`, and read-only-ness by fractional permission on the supplied
sequence. No callee is axiomatized: the behaviour is pure object/state logic,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: installing a geometry sequence is pure object/state
# logic (store a reference, set a flag), modelled deeply. There is no external
# callee the operation depends on.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class GeometryCollection:
    def __init__(self) -> None:
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)  # type: ignore
        Ensures(Acc(self.out_of_date) and self.out_of_date is False)  # type: ignore
        self.items = []  # type: List[int]
        self.out_of_date = False  # type: bool


def install_geometry(self: GeometryCollection, new_items: List[int]) -> None:
    # pre-conditions-start
    # The collection's two touched fields are genuinely mutated: full
    # permission to the held-sequence reference and to the out-of-date flag.
    Requires(Acc(self.items))
    Requires(Acc(self.out_of_date))
    # The supplied sequence is read-only: required at fractional permission so
    # the operation may not rewrite its element contents.
    Requires(Acc(list_pred(new_items), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.items))
    Ensures(Acc(self.out_of_date))
    # (1) the collection now holds EXACTLY the supplied sequence object: a query
    # for its geometry returns the very same object, by identity.
    Ensures(self.items is new_items)
    # (2) the cached rendering is marked out of date.
    Ensures(self.out_of_date is True)
    # The supplied sequence is returned read-only and untouched: same object,
    # same length, same element contents in order.
    Ensures(Acc(list_pred(new_items), 1 / 2))
    Ensures(len(new_items) == Old(len(new_items)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(new_items),
                                           new_items[k] == Old(new_items[k])))))
    # post-conditions-end
    # impl-start
    self.items = new_items
    self.out_of_date = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement-fidelity) audit for matplotlib__matplotlib-26342 (nagini). Ran 10 same-spec attacks (all edit ONLY the impl region; non-impl regions byte-identical to model.py, verified via diff). Environment: adversary/harness run under python from project root; nagini_verify via scripts/nagini_verify.sh.

Commands per attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26342 <atk>.py`.

### Results
- atk_1 (`pass`, prepatch bug reproduced): exit 2 NOT-A-COUNTEREXAMPLE (verification failed) — prepatch bug confirmed reproduced.
- atk_2 (store only): exit 2 rejected (violates out_of_date is True).
- atk_3 (flag only): exit 2 rejected (violates items is new_items).
- atk_4 (`self.items = list(new_items)` copy/ungrounded-oracle echo): exit 2 rejected — confirms the identity clause `self.items is new_items` (refinement.md D.1) is load-bearing, copy breaks it.
- atk_5 (partial-domain: install only if len>0): exit 2 rejected.
- atk_6 (control-flow-effect: set flag then set False): exit 2 rejected.
- atk_7 (wrong flag value False): exit 2 rejected.
- atk_8 (boundary branch, flag-only on empty): exit 2 rejected.
- atk_9 (reorder: self.out_of_date=True before self.items=new_items): exit 0 CANDIDATE (verifies 12.7s). Materialized faithful refined patch (reorder in real callee under field renames items->_paths, out_of_date->stale; site B override deletion retained). run_resolve => RESOLVED True, COMPLETED True, FLAKY False; FAIL_TO_PASS test_contour_set_paths[png] pass + all 84 PASS_TO_PASS pass.
- atk_10 (redundant alias tmp=new_items then store then flag): exit 0 CANDIDATE (verifies 11.9s). Faithful refined patch (tmp alias in real callee) run_resolve => RESOLVED True, COMPLETED True, FLAKY False; same full green.

Both CANDIDATEs are gold-equivalent echoes (statement reorder / redundant alias) whose refined patches RESOLVE — NOT weaknesses (per current G-PANEL-1/eq resolving-echo policy). No verifying-but-non-resolving impl found.

Positive control (gold impl `self.items=new_items; self.out_of_date=True`): nagini_verify exit 0 (11.11s), same-spec exit 0.

Refinement audit: all legs R/I under two field renames (items<->_paths, out_of_date<->stale); ONE A-reference (real post-patch Collection.set_paths), empty axioms region — NO kind-3. axiom_check.py faithfully validates the A-reference on genuinely-dispatching sites (ContourSet F2P subject, PathCollection [override deleted -> inherits base], bare Collection incl. empty boundary) with LineCollection/PolyCollection as negative controls; correspondence holds. The postcondition fully pins both modeled fields to the exact gold post-state (identity + flag), so no behaviorally-divergent verifying impl exists.

VERDICT: SOUND. >=5 attacks run (10 total), both verifying candidates' materialized faithful patches RESOLVED under the official harness; none breaks verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26342.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawable collection of geometry carries a sequence of geometry items and a
  flag recording whether its cached rendering is out of date. Installing a new
  sequence of geometry onto such a collection must, once the call returns,

    (1) make the collection hand back EXACTLY the sequence object that was
        supplied — a subsequent query for the collection's geometry returns the
        very same object, by identity, so a caller that supplied a prepared
        sequence sees that prepared sequence (and only it) used afterwards; and

    (2) mark the collection's cached rendering as out of date, so the next draw
        recomputes from the freshly installed geometry.

  The supplied sequence is read-only to this operation: its element contents are
  not altered (the operation stores the reference, it does not rewrite items),
  and no element is added or removed.

The collection is modelled as a minimal object exposing only the two touched
fields: the held geometry sequence (an object reference) and the out-of-date
flag (a bool). The geometry sequence is modelled as a `List[int]` of opaque
per-item identity tokens; reference identity of the stored sequence is carried
by Nagini's `is`, and read-only-ness by fractional permission on the supplied
sequence. No callee is axiomatized: the behaviour is pure object/state logic,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: installing a geometry sequence is pure object/state
# logic (store a reference, set a flag), modelled deeply. There is no external
# callee the operation depends on.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class GeometryCollection:
    def __init__(self) -> None:
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)  # type: ignore
        Ensures(Acc(self.out_of_date) and self.out_of_date is False)  # type: ignore
        self.items = []  # type: List[int]
        self.out_of_date = False  # type: bool


def install_geometry(self: GeometryCollection, new_items: List[int]) -> None:
    # pre-conditions-start
    # The collection's two touched fields are genuinely mutated: full
    # permission to the held-sequence reference and to the out-of-date flag.
    Requires(Acc(self.items))
    Requires(Acc(self.out_of_date))
    # The supplied sequence is read-only: required at fractional permission so
    # the operation may not rewrite its element contents.
    Requires(Acc(list_pred(new_items), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.items))
    Ensures(Acc(self.out_of_date))
    # (1) the collection now holds EXACTLY the supplied sequence object: a query
    # for its geometry returns the very same object, by identity.
    Ensures(self.items is new_items)
    # (2) the cached rendering is marked out of date.
    Ensures(self.out_of_date is True)
    # The supplied sequence is returned read-only and untouched: same object,
    # same length, same element contents in order.
    Ensures(Acc(list_pred(new_items), 1 / 2))
    Ensures(len(new_items) == Old(len(new_items)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(new_items),
                                           new_items[k] == Old(new_items[k])))))
    # post-conditions-end
    # impl-start
    self.items = new_items
    self.out_of_date = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement-fidelity) audit for matplotlib__matplotlib-26342 (nagini). Ran 10 same-spec attacks (all edit ONLY the impl region; non-impl regions byte-identical to model.py, verified via diff). Environment: adversary/harness run under python from project root; nagini_verify via scripts/nagini_verify.sh.

Commands per attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26342 <atk>.py`.

### Results
- atk_1 (`pass`, prepatch bug reproduced): exit 2 NOT-A-COUNTEREXAMPLE (verification failed) — prepatch bug confirmed reproduced.
- atk_2 (store only): exit 2 rejected (violates out_of_date is True).
- atk_3 (flag only): exit 2 rejected (violates items is new_items).
- atk_4 (`self.items = list(new_items)` copy/ungrounded-oracle echo): exit 2 rejected — confirms the identity clause `self.items is new_items` (refinement.md D.1) is load-bearing, copy breaks it.
- atk_5 (partial-domain: install only if len>0): exit 2 rejected.
- atk_6 (control-flow-effect: set flag then set False): exit 2 rejected.
- atk_7 (wrong flag value False): exit 2 rejected.
- atk_8 (boundary branch, flag-only on empty): exit 2 rejected.
- atk_9 (reorder: self.out_of_date=True before self.items=new_items): exit 0 CANDIDATE (verifies 12.7s). Materialized faithful refined patch (reorder in real callee under field renames items->_paths, out_of_date->stale; site B override deletion retained). run_resolve => RESOLVED True, COMPLETED True, FLAKY False; FAIL_TO_PASS test_contour_set_paths[png] pass + all 84 PASS_TO_PASS pass.
- atk_10 (redundant alias tmp=new_items then store then flag): exit 0 CANDIDATE (verifies 11.9s). Faithful refined patch (tmp alias in real callee) run_resolve => RESOLVED True, COMPLETED True, FLAKY False; same full green.

Both CANDIDATEs are gold-equivalent echoes (statement reorder / redundant alias) whose refined patches RESOLVE — NOT weaknesses (per current G-PANEL-1/eq resolving-echo policy). No verifying-but-non-resolving impl found.

Positive control (gold impl `self.items=new_items; self.out_of_date=True`): nagini_verify exit 0 (11.11s), same-spec exit 0.

Refinement audit: all legs R/I under two field renames (items<->_paths, out_of_date<->stale); ONE A-reference (real post-patch Collection.set_paths), empty axioms region — NO kind-3. axiom_check.py faithfully validates the A-reference on genuinely-dispatching sites (ContourSet F2P subject, PathCollection [override deleted -> inherits base], bare Collection incl. empty boundary) with LineCollection/PolyCollection as negative controls; correspondence holds. The postcondition fully pins both modeled fields to the exact gold post-state (identity + flag), so no behaviorally-divergent verifying impl exists.

VERDICT: SOUND. >=5 attacks run (10 total), both verifying candidates' materialized faithful patches RESOLVED under the official harness; none breaks verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of install_geometry (models post-patch matplotlib.collections.Collection.set_paths at lib/matplotlib/collections.py:209, gold body `self._paths = paths; self.stale = True`).

Spec region byte-identity confirmed (this is a read-only faithfulness audit of the frozen model.py; region_hashes in meta.json match the bundle). The model has three postconditions: (1) self.items is new_items (stored-reference identity), (2) self.out_of_date is True (out-of-date flag), (3) read-only supplied sequence (fractional list_pred permission + len preserved + per-index element preservation).

Runtime-confirmed against the REAL post-patch callee (gold tree, base Collection.set_paths body verbatim = `self._paths = paths; self.stale = True`, executed under python+numpy):
- get_paths() is paths -> True on non-empty and empty inputs => spec (1) holds.
- stale is True after set_paths => spec (2) holds. The Artist.stale setter (artist.py:289) writes self._stale=val then fires stale_callback but does NOT alter the stored value, so readback stays True; matches model.
- len(paths) and per-element identity are preserved by the setter (it only rebinds self._paths, never rewrites the list) => spec (3) holds.
- Empty-sequence boundary: get_paths() is [] True, stale True. Matches.
- Scope correct: PathCollection.set_paths is Collection.set_paths is False at base_commit but its identical override is DELETED by gold so post-patch it inherits base; Line/PolyCollection keep identity-breaking overrides (set_segments/set_verts) and are OUT of scope (negative controls), so no in-scope callee contradicts the identity clause.

Type abstraction sound: list[Path] -> List[int] of opaque per-item identity tokens is faithful because the setter never inspects element internals; the abstraction only weakens element content, not the identity/flag/length guarantees.

Stronger-than-F2P note: the `is` identity clause is stronger than the @check_figures_equal test observable (a copy variant would also pass the test). That is a spec-vs-test strength question (G-PANEL-1 axis), NOT a faithfulness defect: G-PANEL-2 asks whether the model agrees with the REAL callee, and gold genuinely stores by identity, so the model exactly mirrors real repo behavior. No input found where the modeled postconditions diverge from the real callee. verify=>resolved contract is one-directional and preserved.

Verdict: FAITHFUL. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py spec region) is byte-identical with the bundle (same-spec exit 0) and passes the lexical G-LEAK screen (no hard failures/warnings; recorded status 'pass', no relaxed flag/RELAXED_LEAKAGE.md). Semantically, the consumer spec view is fully abstracted: it uses generic domain vocabulary (GeometryCollection/install_geometry/items/out_of_date) and names NO patched repo symbol (set_paths, Collection, _paths, stale), NO patched file path (collections.py), NO diff markers, and contains NO bug/fix narration. Its two behavioral clauses are not a leak beyond the public problem_statement: (1) 'install EXACTLY the supplied sequence' is precisely what the public ENH statement discloses via its proposed API `cs.set_paths(transformed_paths)` (replacing `paths[:] = transformed_paths`); (2) 'mark cached rendering out of date' is generic, necessary artist-staleness logic any implementer of a data-mutating setter would include, stated abstractly without revealing the `stale` field or the two-line diff shape. The gold-quoting material (verbatim gold hunk, base_commit, collections.py:209, self._paths = paths; self.stale = True) appears ONLY in refinement.md/mapping.md, which are the G-EQ refinement-audit documents — not the solver-visible spec view judged by G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
