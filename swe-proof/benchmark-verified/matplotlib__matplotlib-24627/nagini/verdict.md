# P2 adversarial audit — matplotlib__matplotlib-24627

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_offbyone.py`, `atk_2_only_host.py`, `atk_3_only_canvas.py`, `atk_4_guarded.py`, `atk_5_no_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6_echo_swap.py`, `atk_7_echo_twoloop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -83,7 +81,7 @@
     old_members = self.members
     self.members = []
     i = 0
-    while i < len(old_members):
+    while i < len(old_members) - 1:
         # invariants-start
         Invariant(Acc(list_pred(old_members), 1 / 2))
         Invariant(0 <= i and i <= len(old_members))
@@ -93,7 +91,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   old_members[k].host is None and old_members[k].canvas is None),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
         # invariants-end
         old_members[i].host = None
         old_members[i].canvas = None
```

Attack 2 — `atk_2_only_host.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -93,9 +91,7 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   old_members[k].host is None and old_members[k].canvas is None),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
         # invariants-end
         old_members[i].host = None
-        old_members[i].canvas = None
         i = i + 1
     # impl-end
```

Attack 3 — `atk_3_only_canvas.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -93,9 +91,7 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   old_members[k].host is None and old_members[k].canvas is None),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
         # invariants-end
-        old_members[i].host = None
         old_members[i].canvas = None
         i = i + 1
     # impl-end
```

Attack 4 — `atk_4_guarded.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -93,9 +91,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   old_members[k].host is None and old_members[k].canvas is None),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
         # invariants-end
-        old_members[i].host = None
-        old_members[i].canvas = None
+        if old_members[i].host is not None:
+            old_members[i].host = None
+            old_members[i].canvas = None
         i = i + 1
     # impl-end
```

Attack 5 — `atk_5_no_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -81,11 +79,10 @@
     # post-conditions-end
     # impl-start
     old_members = self.members
-    self.members = []
     i = 0
     while i < len(old_members):
         # invariants-start
-        Invariant(Acc(list_pred(old_members), 1 / 2))
+        Invariant(Acc(list_pred(old_members)))
         Invariant(0 <= i and i <= len(old_members))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                   Acc(old_members[k].host) and Acc(old_members[k].canvas)),
@@ -93,7 +90,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   old_members[k].host is None and old_members[k].canvas is None),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
         # invariants-end
         old_members[i].host = None
         old_members[i].canvas = None
```

Attack 6 — `atk_6_echo_swap.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -93,9 +91,8 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   old_members[k].host is None and old_members[k].canvas is None),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
         # invariants-end
+        old_members[i].canvas = None
         old_members[i].host = None
-        old_members[i].canvas = None
         i = i + 1
     # impl-end
```

Attack 7 — `atk_7_echo_twoloop.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Element:
@@ -63,7 +62,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
              Acc(self.members[k].host) and Acc(self.members[k].canvas)),
              [[self.members[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.members) and Acc(list_pred(self.members)))
@@ -84,18 +82,26 @@
     self.members = []
     i = 0
     while i < len(old_members):
-        # invariants-start
         Invariant(Acc(list_pred(old_members), 1 / 2))
         Invariant(0 <= i and i <= len(old_members))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                   Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                   [[old_members[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  old_members[k].host is None and old_members[k].canvas is None),
+                  old_members[k].host is None), [[old_members[k]]])))
+        old_members[i].host = None
+        i = i + 1
+    i = 0
+    while i < len(old_members):
+        Invariant(Acc(list_pred(old_members), 1 / 2))
+        Invariant(0 <= i and i <= len(old_members))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
+                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                   [[old_members[k]]])))
-        Invariant(MustTerminate(len(old_members) - i + 1))
-        # invariants-end
-        old_members[i].host = None
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
+                  old_members[k].host is None), [[old_members[k]]])))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                  old_members[k].canvas is None), [[old_members[k]]])))
         old_members[i].canvas = None
         i = i + 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24627.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawing container owns an ordered collection of member elements. Each member
  records two back-references to the owners it is currently parented under: a
  host reference and a canvas reference (each present as an owner, or absent).

  When the container is reset to its empty state, two things must hold once the
  reset returns:

    (1) the container's collection of members is empty, and

    (2) every element that had been a member is fully de-parented: both of its
        back-references are cleared to "absent". A member that is dropped from
        the container must observe the same de-parented state that an element
        removed individually already observes, so a former member is not left
        still claiming an owner it no longer belongs to.

  An element's two back-references are modelled as ``Optional[int]`` owner
  tokens (a present owner ~ a non-``None`` token; absent ~ ``None``); the test
  observes them only via "is an owner" vs. "is absent". The collection is a
  ``List`` of element objects; per-element field permission is carried by a
  guarded ``Forall`` over the collection indices.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Element:
    def __init__(self, host: Optional[int], canvas: Optional[int]) -> None:
        Ensures(Acc(self.host) and self.host is host)        # type: ignore
        Ensures(Acc(self.canvas) and self.canvas is canvas)  # type: ignore
        self.host = host      # type: Optional[int]
        self.canvas = canvas  # type: Optional[int]


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.members) and Acc(list_pred(self.members)))  # type: ignore
        Ensures(len(self.members) == 0)                              # type: ignore
        self.members = []  # type: List[Element]


# axioms-start
# (no callee is axiomatized: the reset is a pure object-graph mutation; the
#  changed behaviour is modelled deeply, not behind a @ContractOnly contract)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def reset_container(self: Container) -> None:
    # pre-conditions-start
    Requires(Acc(self.members) and Acc(list_pred(self.members)))
    # full permission to every current member's two back-references (mutated)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
             Acc(self.members[k].host) and Acc(self.members[k].canvas)),
             [[self.members[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.members) and Acc(list_pred(self.members)))
    # (1) the container's collection is empty afterwards.
    Ensures(len(self.members) == 0)
    # the former members survive as objects (read-only fractional permission).
    Ensures(Acc(list_pred(Old(self.members)), 1 / 2))
    # (2) every former member is fully de-parented: both back-references absent.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Old(self.members)),
            Acc(Old(self.members)[k].host, 1 / 2)
            and Acc(Old(self.members)[k].canvas, 1 / 2)
            and Old(self.members)[k].host is None
            and Old(self.members)[k].canvas is None),
            [[Old(self.members)[k]]])))
    # post-conditions-end
    # impl-start
    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        # invariants-end
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

No verify-but-not-correct counterexample found; spec is SOUND. Setup: correct adversary/harness interpreter is python (the nagini-verifier venv lacks swebench_unified; an earlier same-spec run under the wrong python silently ModuleNotFound'd). All 8 files are byte-identical in the frozen spec regions (same-spec exit 0); only the impl region was edited. Positive control (unmodified model.py) verifies (11.9s).

Attacks & observed results (weakness = same-spec + Nagini-verify in one shot):
- atk_1_offbyone (partial-domain boundary: loop to len-1, last member left parented): weakness exit 2 NOT-A-COUNTEREXAMPLE (spec rejected: postcondition (2) unprovable for last index).
- atk_2_only_host (partial-effect: clears host only): exit 2, rejected (canvas!=None fails postcond 2).
- atk_3_only_canvas (partial-effect: clears canvas only): exit 2, rejected (host!=None fails postcond 2).
- atk_4_guarded (control-flow-effect: only deparent members whose host is not None): exit 2, rejected (shape-2 member host=None,canvas!=None left parented).
- atk_5_no_empty (control-flow: omit self.members=[] rebind, clear refs only): exit 2, rejected (postcond (1) len==0 unprovable).
- atk_prepatch (model_prepatch.py, the pre-patch bug: self.members=[] only, no deparenting loop): weakness exit 2, PREPATCH BUG REPRODUCED — fails postcondition (2) exactly as refinement.md B claims.
- atk_6_echo_swap (semantic echo: per-element write order swapped, canvas then host): weakness exit 0 CANDIDATE (verifies, 16.5s). Faithful refined patch (mapping host<->.axes, canvas<->.figure; swapped attribute writes) RAN through official harness run_resolve -> RESOLVED (completed=true, attempts=1, not flaky).
- atk_7_echo_twoloop (semantic echo: two separate loops, host loop then canvas loop): weakness exit 0 CANDIDATE (verifies, 16.3s). Faithful refined patch (two for-loops, .axes then .figure) RAN through run_resolve -> RESOLVED (completed=true, attempts=1, not flaky).

Health check: gold patch (verbatim) run_resolve -> RESOLVED. Every verifying same-spec impl's materialized faithful patch resolves, so no verify=>correct violation exists.

Commands:
  python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-24627 <atk>.py   # all exit 0
  python -m swebench_unified.adversary weakness  nagini matplotlib__matplotlib-24627 <atk>.py   # results above
  bash scripts/nagini_verify.sh positive_control.py                                          # exit 0, 11.9s
  python resolve_driver.py {gold,atk6,atk7} <patch>.diff  (calls swebench_unified.harness.run_resolve) # all resolved=true
Parallelism: weakness runs launched in background batches of 3 (each spawns JVM+Z3); resolve runs launched 3 concurrently under the bounded sbu-docker slice.

Refinement.md leg audit: 5 legs tagged R/I/I/I/R -- no A-consumed and no kind-3 legs (consistent with meta.json axioms=[] and mapping.md 'Callee provenance: None'). The single deep-model reference is meta.json deep_model_references[0] kind='A-reference': reset_container's per-element clearing models _AxesBase.__clear deparenting hunk (lib/matplotlib/axes/_base.py:1315-1318). Its correspondence to the real callee is validated end-to-end by axiom_check.py (G-AX) running the real Axes.clear() over the F2P twin + line-count fuzz + heterogeneous artists + repeated clears, asserting art.axes is None AND art.figure is None and ax._children emptied. Type abstraction (.axes<->host Optional[int] token, .figure<->canvas) is over real fixed Artist attributes (no dynamic setattr), so the R-refinement is faithful. A-reference correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_offbyone.py`, `atk_2_only_host.py`, `atk_3_only_canvas.py`, `atk_4_guarded.py`, `atk_5_no_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6_echo_swap.py`, `atk_7_echo_twoloop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_offbyone.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_only_host.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_only_canvas.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_guarded.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_no_empty.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo_swap.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_echo_twoloop.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24627.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawing container owns an ordered collection of member elements. Each member
  records two back-references to the owners it is currently parented under: a
  host reference and a canvas reference (each present as an owner, or absent).

  When the container is reset to its empty state, two things must hold once the
  reset returns:

    (1) the container's collection of members is empty, and

    (2) every element that had been a member is fully de-parented: both of its
        back-references are cleared to "absent". A member that is dropped from
        the container must observe the same de-parented state that an element
        removed individually already observes, so a former member is not left
        still claiming an owner it no longer belongs to.

  An element's two back-references are modelled as ``Optional[int]`` owner
  tokens (a present owner ~ a non-``None`` token; absent ~ ``None``); the test
  observes them only via "is an owner" vs. "is absent". The collection is a
  ``List`` of element objects; per-element field permission is carried by a
  guarded ``Forall`` over the collection indices.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Element:
    def __init__(self, host: Optional[int], canvas: Optional[int]) -> None:
        Ensures(Acc(self.host) and self.host is host)        # type: ignore
        Ensures(Acc(self.canvas) and self.canvas is canvas)  # type: ignore
        self.host = host      # type: Optional[int]
        self.canvas = canvas  # type: Optional[int]


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.members) and Acc(list_pred(self.members)))  # type: ignore
        Ensures(len(self.members) == 0)                              # type: ignore
        self.members = []  # type: List[Element]


# axioms-start
# (no callee is axiomatized: the reset is a pure object-graph mutation; the
#  changed behaviour is modelled deeply, not behind a @ContractOnly contract)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def reset_container(self: Container) -> None:
    # pre-conditions-start
    Requires(Acc(self.members) and Acc(list_pred(self.members)))
    # full permission to every current member's two back-references (mutated)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(self.members),
             Acc(self.members[k].host) and Acc(self.members[k].canvas)),
             [[self.members[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.members) and Acc(list_pred(self.members)))
    # (1) the container's collection is empty afterwards.
    Ensures(len(self.members) == 0)
    # the former members survive as objects (read-only fractional permission).
    Ensures(Acc(list_pred(Old(self.members)), 1 / 2))
    # (2) every former member is fully de-parented: both back-references absent.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Old(self.members)),
            Acc(Old(self.members)[k].host, 1 / 2)
            and Acc(Old(self.members)[k].canvas, 1 / 2)
            and Old(self.members)[k].host is None
            and Old(self.members)[k].canvas is None),
            [[Old(self.members)[k]]])))
    # post-conditions-end
    # impl-start
    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        # invariants-end
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

No verify-but-not-correct counterexample found; spec is SOUND. Setup: correct adversary/harness interpreter is python (the nagini-verifier venv lacks swebench_unified; an earlier same-spec run under the wrong python silently ModuleNotFound'd). All 8 files are byte-identical in the frozen spec regions (same-spec exit 0); only the impl region was edited. Positive control (unmodified model.py) verifies (11.9s).

Attacks & observed results (weakness = same-spec + Nagini-verify in one shot):
- atk_1_offbyone (partial-domain boundary: loop to len-1, last member left parented): weakness exit 2 NOT-A-COUNTEREXAMPLE (spec rejected: postcondition (2) unprovable for last index).
- atk_2_only_host (partial-effect: clears host only): exit 2, rejected (canvas!=None fails postcond 2).
- atk_3_only_canvas (partial-effect: clears canvas only): exit 2, rejected (host!=None fails postcond 2).
- atk_4_guarded (control-flow-effect: only deparent members whose host is not None): exit 2, rejected (shape-2 member host=None,canvas!=None left parented).
- atk_5_no_empty (control-flow: omit self.members=[] rebind, clear refs only): exit 2, rejected (postcond (1) len==0 unprovable).
- atk_prepatch (model_prepatch.py, the pre-patch bug: self.members=[] only, no deparenting loop): weakness exit 2, PREPATCH BUG REPRODUCED — fails postcondition (2) exactly as refinement.md B claims.
- atk_6_echo_swap (semantic echo: per-element write order swapped, canvas then host): weakness exit 0 CANDIDATE (verifies, 16.5s). Faithful refined patch (mapping host<->.axes, canvas<->.figure; swapped attribute writes) RAN through official harness run_resolve -> RESOLVED (completed=true, attempts=1, not flaky).
- atk_7_echo_twoloop (semantic echo: two separate loops, host loop then canvas loop): weakness exit 0 CANDIDATE (verifies, 16.3s). Faithful refined patch (two for-loops, .axes then .figure) RAN through run_resolve -> RESOLVED (completed=true, attempts=1, not flaky).

Health check: gold patch (verbatim) run_resolve -> RESOLVED. Every verifying same-spec impl's materialized faithful patch resolves, so no verify=>correct violation exists.

Commands:
  python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-24627 <atk>.py   # all exit 0
  python -m swebench_unified.adversary weakness  nagini matplotlib__matplotlib-24627 <atk>.py   # results above
  bash scripts/nagini_verify.sh positive_control.py                                          # exit 0, 11.9s
  python resolve_driver.py {gold,atk6,atk7} <patch>.diff  (calls swebench_unified.harness.run_resolve) # all resolved=true
Parallelism: weakness runs launched in background batches of 3 (each spawns JVM+Z3); resolve runs launched 3 concurrently under the bounded sbu-docker slice.

Refinement.md leg audit: 5 legs tagged R/I/I/I/R -- no A-consumed and no kind-3 legs (consistent with meta.json axioms=[] and mapping.md 'Callee provenance: None'). The single deep-model reference is meta.json deep_model_references[0] kind='A-reference': reset_container's per-element clearing models _AxesBase.__clear deparenting hunk (lib/matplotlib/axes/_base.py:1315-1318). Its correspondence to the real callee is validated end-to-end by axiom_check.py (G-AX) running the real Axes.clear() over the F2P twin + line-count fuzz + heterogeneous artists + repeated clears, asserting art.axes is None AND art.figure is None and ax._children emptied. Type abstraction (.axes<->host Optional[int] token, .figure<->canvas) is over real fixed Artist attributes (no dynamic setattr), so the R-refinement is faithful. A-reference correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift) check for matplotlib__matplotlib-24627 nagini. Spec region is the bundle's own model.py; the G-CONF shadow is the contract-stripped impl region verbatim. Reconstructed the REAL patched repo at base_commit 9d22ab09 (git worktree from a matplotlib mirror + gold patch applied; base source .py overlaid on a clean matplotlib==3.6.0 venv for compiled extensions/mpl-data, since installed 3.6.3 diverged and did not pre-init _children). Evidence: (1) nagini_verify.sh on model.py => 'Verification successful' (11.3s). (2) conformance_check.py run against the real patched _AxesBase.__clear => 'G-CONF OK ... 100001 inputs, 14278 real clears, 0 disagreements, seed 24627'. Coverage includes decoy owners (member parented to a DIFFERENT live axes/figure — would expose a re-point-instead-of-clear drift), aliased duplicate members, all partial back-reference pre-states (both/one/neither present), boundary lengths 0/1, repeated resets, and publicly-registered artists. (3) F2P test test_cla_clears_children_axes_and_fig passes on the reconstructed patched repo. The two modeled postconditions (len(members)==0; every former member has host is None AND canvas is None) are exactly what the real callee delivers on every tested input — the real chld.axes = chld.figure = None unconditionally clears even decoy-owned members, matching the model. No input found where the modeled function disagrees with the real callee; the spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the solver-visible spec view (computed via spec_view/nagini): the impl region is elided ('implementation elided — supplied by the consumer'), so the gold edit's structure (tuple-capture + de-parenting loop) is NOT shown. Mechanical G-LEAK screen passes (0 hard failures).

Gold edit context: patch changes lib/matplotlib/axes/_base.py __clear, replacing `self._children = []` with a capture + `for chld in old_children: chld.axes = chld.figure = None`. Patched repo symbols/paths: __clear/clear, _children, .axes, .figure, lib/matplotlib/axes/_base.py.

No leakage beyond problem_statement:
- The public problem_statement ALREADY states the target behavior verbatim: 'cla(), clf() should unset the .axes and .figure attributes of deparented artists' and demonstrates that remove() unsets .axes but cla() does not. So the entire desired behavior (clearing de-parents former children, nulling both back-refs) is already public.
- Spec-view names are fully abstracted: Container/members/Element/host/canvas/reset_container. None embed the patched symbol 'clear' (the only distinctive changed symbol), nor _children/.axes/.figure/__clear.
- No repo file path, module path, or diff markers appear in the view.
- Spec-view docstring/comments describe desired behavior (public), with no bug/fix narration and no naming of the edit.
- Repo-specific gold detail (the __clear hunk, _children, .axes/.figure, file:line) lives only in mapping.md/refinement.md, which are AUDITOR artifacts, not part of the consumer spec view.

The postcondition (Forall former member: host is None and canvas is None) is a faithful behavioral encoding of the already-public problem statement, not a disclosure of the edit's mechanism beyond it. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
