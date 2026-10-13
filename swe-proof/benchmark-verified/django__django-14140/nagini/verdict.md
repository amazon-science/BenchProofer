# P2 adversarial audit — django__django-14140

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,33 +119,24 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
-    i = 0
     n = len(node.children)
-    while i < n:
-        # invariants-start
-        Invariant(Acc(node.children, 1 / 2))
-        Invariant(Acc(list_pred(node.children), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(node.children))
-        Invariant(Acc(list_pred(args)))
-        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
-        args = args + [node.children[i]]
-        i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
-    connector_kwarg = node.connector != node.default
+    connector_kwarg = False  # type: bool
+    if n == 1:
+        connector_kwarg = False
+    else:
+        i = 0
+        while i < n:
+            Invariant(Acc(node.children, 1 / 2))
+            Invariant(Acc(list_pred(node.children), 1 / 2))
+            Invariant(0 <= i and i <= n)
+            Invariant(n == len(node.children))
+            Invariant(Acc(list_pred(args)))
+            Invariant(ToSeq(args) == ToSeq(node.children).take(i))
+            args = args + [node.children[i]]
+            i = i + 1
+        connector_kwarg = node.connector != node.default
     negated_kwarg = node.negated
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,33 +119,20 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
     i = 0
     n = len(node.children)
-    while i < n:
-        # invariants-start
+    while i < n - 1:
         Invariant(Acc(node.children, 1 / 2))
         Invariant(Acc(list_pred(node.children), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(node.children))
         Invariant(Acc(list_pred(args)))
         Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
         args = args + [node.children[i]]
         i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
     connector_kwarg = node.connector != node.default
     negated_kwarg = node.negated
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,33 +119,20 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
     i = 0
     n = len(node.children)
     while i < n:
-        # invariants-start
         Invariant(Acc(node.children, 1 / 2))
         Invariant(Acc(list_pred(node.children), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(node.children))
         Invariant(Acc(list_pred(args)))
         Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
         args = args + [node.children[i]]
         i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
-    connector_kwarg = node.connector != node.default
+    connector_kwarg = node.connector == node.default
     negated_kwarg = node.negated
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,33 +119,20 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
     i = 0
     n = len(node.children)
     while i < n:
-        # invariants-start
         Invariant(Acc(node.children, 1 / 2))
         Invariant(Acc(list_pred(node.children), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(node.children))
         Invariant(Acc(list_pred(args)))
         Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
         args = args + [node.children[i]]
         i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
     connector_kwarg = node.connector != node.default
-    negated_kwarg = node.negated
+    negated_kwarg = False
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,33 +119,20 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
     i = 0
     n = len(node.children)
     while i < n:
-        # invariants-start
         Invariant(Acc(node.children, 1 / 2))
         Invariant(Acc(list_pred(node.children), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(node.children))
         Invariant(Acc(list_pred(args)))
         Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
         args = args + [node.children[i]]
         i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
-    connector_kwarg = node.connector != node.default
+    connector_kwarg = not (node.connector == node.default)
     negated_kwarg = node.negated
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,33 +119,24 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
     i = 0
     n = len(node.children)
     while i < n:
-        # invariants-start
         Invariant(Acc(node.children, 1 / 2))
         Invariant(Acc(list_pred(node.children), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(node.children))
         Invariant(Acc(list_pred(args)))
         Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
         args = args + [node.children[i]]
         i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
-    connector_kwarg = node.connector != node.default
-    negated_kwarg = node.negated
+    if node.negated:
+        connector_kwarg = node.connector != node.default
+        negated_kwarg = True
+    else:
+        connector_kwarg = node.connector != node.default
+        negated_kwarg = False
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,33 +119,23 @@
     Ensures(Result().negated_kwarg == node.negated)
     # post-conditions-end
     # impl-start
-    # Every child becomes a positional argument (a faithful copy of the
-    # children sequence), regardless of how many children there are.
     args = []  # type: List[int]
-    i = 0
     n = len(node.children)
-    while i < n:
-        # invariants-start
-        Invariant(Acc(node.children, 1 / 2))
-        Invariant(Acc(list_pred(node.children), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(node.children))
-        Invariant(Acc(list_pred(args)))
-        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
-        # invariants-end
-        Assert(ToSeq(node.children).take(i + 1) ==
-               ToSeq(node.children).take(i) + PSeq(node.children[i]))
-        args = args + [node.children[i]]
-        i = i + 1
-    Assert(i == n)
-    Assert(n == len(ToSeq(node.children)))
-    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
-    Assert(ToSeq(args) == ToSeq(node.children))
-    # The keyword arguments carry only the connector (when non-default) and the
-    # negation flag; never a child.
-    connector_kwarg = node.connector != node.default
+    if n == 0:
+        connector_kwarg = node.connector != node.default
+    else:
+        i = 0
+        while i < n:
+            Invariant(Acc(node.children, 1 / 2))
+            Invariant(Acc(list_pred(node.children), 1 / 2))
+            Invariant(0 <= i and i <= n)
+            Invariant(n == len(node.children))
+            Invariant(Acc(list_pred(args)))
+            Invariant(ToSeq(args) == ToSeq(node.children).take(i))
+            args = args + [node.children[i]]
+            i = i + 1
+        connector_kwarg = node.connector != node.default
     negated_kwarg = node.negated
     result = Deconstruction(args, connector_kwarg, negated_kwarg)
-    Assert(ToSeq(result.args) == ToSeq(node.children))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for django__django-14140.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logical filter node is taken apart into a reconstruction triple
  ``(path, positional_arguments, keyword_arguments)`` so that an equivalent node
  can later be rebuilt by calling the same class with those arguments. This
  routine concerns the ``positional_arguments`` and ``keyword_arguments`` halves,
  computed from the node's three observable pieces of state: its ordered
  ``children`` (each an opaque sub-condition), its combining ``connector``, and
  whether it is ``negated``.

  The desired behaviour is uniform in the number of children:

    (1) Every child of the node, in order, is a positional argument; the
        positional arguments are exactly the node's children with nothing added,
        dropped, reordered, or relocated. In particular a node holding a single
        child still surfaces that one child positionally -- it is NOT special-
        cased into a keyword argument, so an opaque child that cannot be taken
        apart as a key/value pair is still reproduced faithfully.

    (2) The keyword arguments record only the two pieces of state that are not
        carried by the children themselves: a connector entry is present exactly
        when the node's connector differs from the class default, and a negation
        entry is present exactly when the node is negated. No child ever appears
        among the keyword arguments.

The node is modelled as a minimal class carrying only the touched state: the
``children`` (a ``List[int]`` of opaque child identifiers), the integer
``connector`` and ``default`` connector codes, and the ``negated`` flag. The
positional arguments are returned as a freshly built ``List[int]``; the presence
of each of the two possible keyword entries is returned as a boolean.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The decomposition of a
#  node into its reconstruction arguments is the changed behaviour and is
#  modelled deeply below over the node's own state: the positional arguments are
#  the children verbatim, and the two keyword flags are exact boolean functions
#  of the connector/default relation and the negation flag. There is no
#  @ContractOnly axiom; equality of this deep model to the real method is the
#  refinement boundary documented in mapping.md, checked out-of-band by
#  axiom_check.py / G-AX, an A-reference, not a consumed axiom.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Node:
    """A logical filter node, holding only the state ``deconstruct`` observes."""

    def __init__(self, children: List[int], connector: int, default: int,
                 negated: bool) -> None:
        Requires(Acc(list_pred(children), 1 / 2))
        Ensures(Acc(self.children) and self.children is children)  # type: ignore
        Ensures(Acc(self.connector) and self.connector == connector)  # type: ignore
        Ensures(Acc(self.default) and self.default == default)  # type: ignore
        Ensures(Acc(self.negated) and self.negated == negated)  # type: ignore
        Ensures(Acc(list_pred(children), 1 / 2))
        self.children = children
        self.connector = connector
        self.default = default
        self.negated = negated


class Deconstruction:
    """The argument halves of the reconstruction triple: the positional
    ``args`` (a freshly built list of the node's children) and the presence of
    each of the two possible keyword entries."""

    def __init__(self, args: List[int], connector_kwarg: bool,
                 negated_kwarg: bool) -> None:
        Requires(Acc(list_pred(args)))
        Ensures(Acc(self.args) and self.args is args)  # type: ignore
        Ensures(Acc(self.connector_kwarg) and self.connector_kwarg == connector_kwarg)  # type: ignore
        Ensures(Acc(self.negated_kwarg) and self.negated_kwarg == negated_kwarg)  # type: ignore
        Ensures(Acc(list_pred(args)))
        Ensures(ToSeq(self.args) == Old(ToSeq(args)))  # type: ignore  # content preserved
        self.args = args
        self.connector_kwarg = connector_kwarg
        self.negated_kwarg = negated_kwarg


def deconstruct_arguments(node: Node) -> Deconstruction:
    # pre-conditions-start
    Requires(Acc(node.children, 1 / 2))
    Requires(Acc(list_pred(node.children), 1 / 2))
    Requires(Acc(node.connector, 1 / 2))
    Requires(Acc(node.default, 1 / 2))
    Requires(Acc(node.negated, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The node is read-only: its state is returned untouched at half permission.
    Ensures(Acc(node.children, 1 / 2))
    Ensures(Acc(list_pred(node.children), 1 / 2))
    Ensures(Acc(node.connector, 1 / 2))
    Ensures(Acc(node.default, 1 / 2))
    Ensures(Acc(node.negated, 1 / 2))
    # The result is a freshly built decomposition the caller fully owns.
    Ensures(Acc(Result().args))
    Ensures(Acc(list_pred(Result().args)))
    Ensures(Acc(Result().connector_kwarg))
    Ensures(Acc(Result().negated_kwarg))
    # (1) The positional arguments are exactly the node's children, in order,
    # for every node -- including a single-child node.
    Ensures(ToSeq(Result().args) == ToSeq(node.children))
    # (2) The connector keyword entry is present exactly when the connector
    # differs from the default; the negation entry exactly when negated; no
    # child is ever among the keyword arguments.
    Ensures(Result().connector_kwarg == (node.connector != node.default))
    Ensures(Result().negated_kwarg == node.negated)
    # post-conditions-end
    # impl-start
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    # The keyword arguments carry only the connector (when non-default) and the
    # negation flag; never a child.
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    Assert(ToSeq(result.args) == ToSeq(node.children))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14140 (nagini). env, SBU_BENCHMARK_DIR=.../benchmark-verified, SBU_PYTHON=python.

SPEC SHAPE: model.py postconditions fully pin all three modeled outputs: ToSeq(Result().args)==ToSeq(node.children) (clause 1, every child positional), Result().connector_kwarg==(node.connector!=node.default), Result().negated_kwarg==node.negated (clause 2). No @ContractOnly consumed axiom; the changed method Q.deconstruct is modeled DEEPLY (A-reference), validated by axiom_check.py/G-AX.

POSITIVE CONTROL: bash scripts/nagini_verify.sh model.py => VERIFIED (13.3s).

ATTACKS (all confirmed SAME-SPEC via `adversary same-spec`; then `adversary weakness nagini django__django-14140 <f>`, run 3-at-a-time in background):
 - atk_1.py: prepatch bug (single-child relocated, args left empty) => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). This reproduces the prepatch skeleton; spec rejects it (clause-1 fails on 1-child node). prepatch_reproduced=true.
 - atk_2.py: boundary — drops LAST child (loop i<n-1) => does not verify (exit 2).
 - atk_3.py: ungrounded-oracle echo — connector flag inverted (== instead of !=) => does not verify (exit 2).
 - atk_4.py: negated_kwarg hard-coded False => does not verify (exit 2).
 - atk_5.py: connector flag via `not (connector==default)` (behaviorally == gold) => CANDIDATE (verifies).
 - atk_6.py: control-flow-effect — dead branch on node.negated, both arms compute same connector flag (== gold) => CANDIDATE (verifies).
 - atk_7.py: partial-domain — special-case empty children (args stays [] which equals tuple([])), else loop (== gold) => CANDIDATE (verifies, 14.9s).

MANDATORY RESOLVE STEP for every verifying CANDIDATE: materialized a DISTINCT faithful refined patch mirroring each attack's control flow and ran it through the official harness (run_resolve, retries=0, timeout=1800):
 - patch_atk_5.diff => resolved=true, completed=true
 - patch_atk_6.diff => resolved=true, completed=true
 - patch_atk_7.diff => resolved=true, completed=true
 - gold patch.diff (sanity) => resolved=true, completed=true
Every verifying wrong-shaped-but-equivalent impl's faithful patch RESOLVES; no verifying impl produced a non-resolving faithful patch. Therefore verify does NOT admit an incorrect (non-resolving) impl here.

REFINEMENT.MD AUDIT: legs A1-A5 tagged R / R+I / R / R+I / R; the whole changed method Q.deconstruct is an A-REFERENCE (deep model, no consumed axiom) — confirmed against model.py axioms region (empty, prose only) and axiom_check.py. No kind-3 (unexpressible changed-op) steps. A-reference correspondence holds: axiom_check.py asserts real Q.deconstruct's args==tuple(self.children), kwargs⊆{_connector,_negated} with exact key presence + values, and Q(*args,**kwargs)==self round-trip over 18 boundary nodes (incl. the 3 F2P fixtures and the Exists crash case) + 5000 seeded-fuzz nodes — matching model.py's three postconditions exactly; discriminates the fix (prepatch raises the exact Exists TypeError). mapping.md §2 type abstractions are sound R-refinements (list<->tuple content identity, string-code<->int inequality, key-presence<->boolean).

VERDICT: SOUND. 7 attacks run (4 distinct genuinely-wrong impls all rejected by the tight postconditions; 3 verifying equivalent echoes whose materialized faithful patches all resolve). No verifying impl breaks the spec; every needed resolve run completed. The two trust points (A-reference soundness via G-AX, refinement fidelity via this G-EQ) hold.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for django__django-14140.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logical filter node is taken apart into a reconstruction triple
  ``(path, positional_arguments, keyword_arguments)`` so that an equivalent node
  can later be rebuilt by calling the same class with those arguments. This
  routine concerns the ``positional_arguments`` and ``keyword_arguments`` halves,
  computed from the node's three observable pieces of state: its ordered
  ``children`` (each an opaque sub-condition), its combining ``connector``, and
  whether it is ``negated``.

  The desired behaviour is uniform in the number of children:

    (1) Every child of the node, in order, is a positional argument; the
        positional arguments are exactly the node's children with nothing added,
        dropped, reordered, or relocated. In particular a node holding a single
        child still surfaces that one child positionally -- it is NOT special-
        cased into a keyword argument, so an opaque child that cannot be taken
        apart as a key/value pair is still reproduced faithfully.

    (2) The keyword arguments record only the two pieces of state that are not
        carried by the children themselves: a connector entry is present exactly
        when the node's connector differs from the class default, and a negation
        entry is present exactly when the node is negated. No child ever appears
        among the keyword arguments.

The node is modelled as a minimal class carrying only the touched state: the
``children`` (a ``List[int]`` of opaque child identifiers), the integer
``connector`` and ``default`` connector codes, and the ``negated`` flag. The
positional arguments are returned as a freshly built ``List[int]``; the presence
of each of the two possible keyword entries is returned as a boolean.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The decomposition of a
#  node into its reconstruction arguments is the changed behaviour and is
#  modelled deeply below over the node's own state: the positional arguments are
#  the children verbatim, and the two keyword flags are exact boolean functions
#  of the connector/default relation and the negation flag. There is no
#  @ContractOnly axiom; equality of this deep model to the real method is the
#  refinement boundary documented in mapping.md, checked out-of-band by
#  axiom_check.py / G-AX, an A-reference, not a consumed axiom.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Node:
    """A logical filter node, holding only the state ``deconstruct`` observes."""

    def __init__(self, children: List[int], connector: int, default: int,
                 negated: bool) -> None:
        Requires(Acc(list_pred(children), 1 / 2))
        Ensures(Acc(self.children) and self.children is children)  # type: ignore
        Ensures(Acc(self.connector) and self.connector == connector)  # type: ignore
        Ensures(Acc(self.default) and self.default == default)  # type: ignore
        Ensures(Acc(self.negated) and self.negated == negated)  # type: ignore
        Ensures(Acc(list_pred(children), 1 / 2))
        self.children = children
        self.connector = connector
        self.default = default
        self.negated = negated


class Deconstruction:
    """The argument halves of the reconstruction triple: the positional
    ``args`` (a freshly built list of the node's children) and the presence of
    each of the two possible keyword entries."""

    def __init__(self, args: List[int], connector_kwarg: bool,
                 negated_kwarg: bool) -> None:
        Requires(Acc(list_pred(args)))
        Ensures(Acc(self.args) and self.args is args)  # type: ignore
        Ensures(Acc(self.connector_kwarg) and self.connector_kwarg == connector_kwarg)  # type: ignore
        Ensures(Acc(self.negated_kwarg) and self.negated_kwarg == negated_kwarg)  # type: ignore
        Ensures(Acc(list_pred(args)))
        Ensures(ToSeq(self.args) == Old(ToSeq(args)))  # type: ignore  # content preserved
        self.args = args
        self.connector_kwarg = connector_kwarg
        self.negated_kwarg = negated_kwarg


def deconstruct_arguments(node: Node) -> Deconstruction:
    # pre-conditions-start
    Requires(Acc(node.children, 1 / 2))
    Requires(Acc(list_pred(node.children), 1 / 2))
    Requires(Acc(node.connector, 1 / 2))
    Requires(Acc(node.default, 1 / 2))
    Requires(Acc(node.negated, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The node is read-only: its state is returned untouched at half permission.
    Ensures(Acc(node.children, 1 / 2))
    Ensures(Acc(list_pred(node.children), 1 / 2))
    Ensures(Acc(node.connector, 1 / 2))
    Ensures(Acc(node.default, 1 / 2))
    Ensures(Acc(node.negated, 1 / 2))
    # The result is a freshly built decomposition the caller fully owns.
    Ensures(Acc(Result().args))
    Ensures(Acc(list_pred(Result().args)))
    Ensures(Acc(Result().connector_kwarg))
    Ensures(Acc(Result().negated_kwarg))
    # (1) The positional arguments are exactly the node's children, in order,
    # for every node -- including a single-child node.
    Ensures(ToSeq(Result().args) == ToSeq(node.children))
    # (2) The connector keyword entry is present exactly when the connector
    # differs from the default; the negation entry exactly when negated; no
    # child is ever among the keyword arguments.
    Ensures(Result().connector_kwarg == (node.connector != node.default))
    Ensures(Result().negated_kwarg == node.negated)
    # post-conditions-end
    # impl-start
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: List[int]
    i = 0
    n = len(node.children)
    while i < n:
        # invariants-start
        Invariant(Acc(node.children, 1 / 2))
        Invariant(Acc(list_pred(node.children), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(node.children))
        Invariant(Acc(list_pred(args)))
        Invariant(ToSeq(args) == ToSeq(node.children).take(i))
        # invariants-end
        Assert(ToSeq(node.children).take(i + 1) ==
               ToSeq(node.children).take(i) + PSeq(node.children[i]))
        args = args + [node.children[i]]
        i = i + 1
    Assert(i == n)
    Assert(n == len(ToSeq(node.children)))
    Assert(ToSeq(node.children).take(n) == ToSeq(node.children))
    Assert(ToSeq(args) == ToSeq(node.children))
    # The keyword arguments carry only the connector (when non-default) and the
    # negation flag; never a child.
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    Assert(ToSeq(result.args) == ToSeq(node.children))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14140 (nagini). env, SBU_BENCHMARK_DIR=.../benchmark-verified, SBU_PYTHON=python.

SPEC SHAPE: model.py postconditions fully pin all three modeled outputs: ToSeq(Result().args)==ToSeq(node.children) (clause 1, every child positional), Result().connector_kwarg==(node.connector!=node.default), Result().negated_kwarg==node.negated (clause 2). No @ContractOnly consumed axiom; the changed method Q.deconstruct is modeled DEEPLY (A-reference), validated by axiom_check.py/G-AX.

POSITIVE CONTROL: bash scripts/nagini_verify.sh model.py => VERIFIED (13.3s).

ATTACKS (all confirmed SAME-SPEC via `adversary same-spec`; then `adversary weakness nagini django__django-14140 <f>`, run 3-at-a-time in background):
 - atk_1.py: prepatch bug (single-child relocated, args left empty) => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). This reproduces the prepatch skeleton; spec rejects it (clause-1 fails on 1-child node). prepatch_reproduced=true.
 - atk_2.py: boundary — drops LAST child (loop i<n-1) => does not verify (exit 2).
 - atk_3.py: ungrounded-oracle echo — connector flag inverted (== instead of !=) => does not verify (exit 2).
 - atk_4.py: negated_kwarg hard-coded False => does not verify (exit 2).
 - atk_5.py: connector flag via `not (connector==default)` (behaviorally == gold) => CANDIDATE (verifies).
 - atk_6.py: control-flow-effect — dead branch on node.negated, both arms compute same connector flag (== gold) => CANDIDATE (verifies).
 - atk_7.py: partial-domain — special-case empty children (args stays [] which equals tuple([])), else loop (== gold) => CANDIDATE (verifies, 14.9s).

MANDATORY RESOLVE STEP for every verifying CANDIDATE: materialized a DISTINCT faithful refined patch mirroring each attack's control flow and ran it through the official harness (run_resolve, retries=0, timeout=1800):
 - patch_atk_5.diff => resolved=true, completed=true
 - patch_atk_6.diff => resolved=true, completed=true
 - patch_atk_7.diff => resolved=true, completed=true
 - gold patch.diff (sanity) => resolved=true, completed=true
Every verifying wrong-shaped-but-equivalent impl's faithful patch RESOLVES; no verifying impl produced a non-resolving faithful patch. Therefore verify does NOT admit an incorrect (non-resolving) impl here.

REFINEMENT.MD AUDIT: legs A1-A5 tagged R / R+I / R / R+I / R; the whole changed method Q.deconstruct is an A-REFERENCE (deep model, no consumed axiom) — confirmed against model.py axioms region (empty, prose only) and axiom_check.py. No kind-3 (unexpressible changed-op) steps. A-reference correspondence holds: axiom_check.py asserts real Q.deconstruct's args==tuple(self.children), kwargs⊆{_connector,_negated} with exact key presence + values, and Q(*args,**kwargs)==self round-trip over 18 boundary nodes (incl. the 3 F2P fixtures and the Exists crash case) + 5000 seeded-fuzz nodes — matching model.py's three postconditions exactly; discriminates the fix (prepatch raises the exact Exists TypeError). mapping.md §2 type abstractions are sound R-refinements (list<->tuple content identity, string-code<->int inequality, key-presence<->boolean).

VERDICT: SOUND. 7 attacks run (4 distinct genuinely-wrong impls all rejected by the tight postconditions; 3 verifying equivalent echoes whose materialized faithful patches all resolve). No verifying impl breaks the spec; every needed resolve run completed. The two trust points (A-reference soundness via G-AX, refinement fidelity via this G-EQ) hold.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for django__django-14140 nagini bundle. The modeled function `deconstruct_arguments` models the CHANGED method django.db.models.Q.deconstruct (query_utils.py:83) deeply (no @ContractOnly axiom). The post-patch behavior is: args = tuple(self.children); kwargs gets '_connector' iff connector != default and '_negated' iff negated. The model's three postconditions encode exactly this: ToSeq(Result().args)==ToSeq(node.children), connector_kwarg==(connector!=default), negated_kwarg==negated.

Verification performed:
1. Built a base_commit worktree (45814af6) and applied the gold hunk to get the real patched Q.deconstruct.
2. Ran the bundle's axiom_check.py (G-AX) against the patched repo (PYTHONPATH=worktree): exit 0 — deep model == real Q.deconstruct on 18 boundary + 5000 fuzz nodes (args==tuple(children), kwargs keys subset {_connector,_negated} with exact presence, and reconstruction round-trip Q(*args,**kwargs)==self).
3. Independent adversarial probes against the real patched callee (nested-Q children, forced connector==default, double-negation, multi-child, empty Q, single kwarg/positional/Exists children): 0 divergences.
4. bash scripts/nagini_verify.sh model.py => Verification successful (spec is not vacuous; it is provable by the honest impl).
5. model_prepatch.py reproduces the pre-patch single-child special-case (empty args) and fails exactly the clause-1 postcondition, confirming the spec discriminates the fix rather than being trivially satisfiable.

Type abstractions in mapping.md are order/content-preserving (child objects -> opaque int ids over PSeq; connector string codes -> int inequality; kwargs dict -> two booleans capturing key presence). None weakens or over-strengthens the modeled behavior: the spec agrees with the real callee on every tested input, including the F2P fixtures Q(price__gt=F(...)), ~Q(price__gt=F(...)), Q(Exists(...)) and the empty-Q combinations. No diverging input found; the spec does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Semantic + lexical review of the nagini spec view for django__django-14140.

SPEC REGION VERIFIED: spec_view (impl elided) is intact; the impl-start/impl-end body is stripped to '...' so the consumer never sees the loop. Region hashes present in meta. Mechanical G-LEAK screen (leakage.screen over the frozen row's patch + problem_statement) returns passed=True with zero hard failures: no diff markers, no patched file path (django/db/models/query_utils.py) or dotted module path in view, no verbatim gold-patch line (tuple(self.children), '_connector', '_negated' keys all absent — the model uses opaque connector_kwarg/negated_kwarg booleans over List[int] ids), and no banned narration tokens (bug/fix/patch/regression/etc.).

GOLD EDIT vs PUBLIC PROBLEM_STATEMENT: the gold patch removes the single-child special case so a lone child deconstructs into args (tuple(self.children)) instead of being relocated into kwargs, fixing the 'Exists object is not subscriptable' crash. The public problem_statement ALREADY discloses the entire delta verbatim: 'Q objects with 1 child are treated differently during deconstruct' (with worked (), {'x':1} vs args examples) and 'Patch ... removes the special case, meaning single-child Q objects deconstruct into args instead of kwargs.'

SPEC-VIEW CLAUSES: (1) 'Every child ... is a positional argument ... a single child still surfaces that one child positionally -- it is NOT special-cased into a keyword argument' restates behaviour already public in the task. (2) connector/negation kwargs are the UNCHANGED surrounding contract (the _connector/_negated guards are byte-identical pre/post per refinement.md A3/A4 and the gold diff), so describing them reveals no edit. The spec states desired behaviour (its legitimate function); every discriminating fact it exposes is already in the solver-visible problem_statement. No spec-view line leaks the gold edit beyond problem_statement. G-LEAK screen not relaxed (meta status not 'relaxed'; no RELAXED_LEAKAGE.md).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
