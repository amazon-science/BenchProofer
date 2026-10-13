# P2 adversarial audit — django__django-13012

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # pre-conditions-start
     # The wrapped node's rule is a bounded two-way case split that must answer
     # (measure 2: it may call only builtin steps, never itself).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -124,7 +124,7 @@
     # The composite must actually answer the grouping request (measure 3:
     # strictly above the wrapped node's rule, so it may invoke that rule but
     # never re-invoke itself).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(node.inner_id, 1 / 2))
@@ -138,6 +138,6 @@
     Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
     # post-conditions-end
     # impl-start
-    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
-    return cols
+    selfcols = [node.node_id]  # type: List[int]
+    return selfcols
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # pre-conditions-start
     # The wrapped node's rule is a bounded two-way case split that must answer
     # (measure 2: it may call only builtin steps, never itself).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -124,7 +124,7 @@
     # The composite must actually answer the grouping request (measure 3:
     # strictly above the wrapped node's rule, so it may invoke that rule but
     # never re-invoke itself).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(node.inner_id, 1 / 2))
@@ -138,6 +138,6 @@
     Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
     # post-conditions-end
     # impl-start
-    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
-    return cols
+    empty = []  # type: List[int]
+    return empty
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # pre-conditions-start
     # The wrapped node's rule is a bounded two-way case split that must answer
     # (measure 2: it may call only builtin steps, never itself).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -124,7 +124,7 @@
     # The composite must actually answer the grouping request (measure 3:
     # strictly above the wrapped node's rule, so it may invoke that rule but
     # never re-invoke itself).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(node.inner_id, 1 / 2))
@@ -138,6 +138,6 @@
     Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
     # post-conditions-end
     # impl-start
-    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
+    cols = base_group_by_cols(node.node_id, node.inner_is_constant, request)
     return cols
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # pre-conditions-start
     # The wrapped node's rule is a bounded two-way case split that must answer
     # (measure 2: it may call only builtin steps, never itself).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -124,7 +124,7 @@
     # The composite must actually answer the grouping request (measure 3:
     # strictly above the wrapped node's rule, so it may invoke that rule but
     # never re-invoke itself).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(node.inner_id, 1 / 2))
@@ -138,6 +138,6 @@
     Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
     # post-conditions-end
     # impl-start
-    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
+    cols = [node.inner_id]  # type: List[int]
     return cols
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # pre-conditions-start
     # The wrapped node's rule is a bounded two-way case split that must answer
     # (measure 2: it may call only builtin steps, never itself).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -107,9 +107,6 @@
     Ensures(ToSeq(Result()) == base_group_cols_seq(node_id, is_constant))
     # post-conditions-end
     # impl-start
-    if is_constant:
-        empty = []  # type: List[int]
-        return empty
     one = [node_id]  # type: List[int]
     return one
     # impl-end
@@ -124,7 +121,7 @@
     # The composite must actually answer the grouping request (measure 3:
     # strictly above the wrapped node's rule, so it may invoke that rule but
     # never re-invoke itself).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(node.inner_id, 1 / 2))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # pre-conditions-start
     # The wrapped node's rule is a bounded two-way case split that must answer
     # (measure 2: it may call only builtin steps, never itself).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,10 +108,10 @@
     # post-conditions-end
     # impl-start
     if is_constant:
-        empty = []  # type: List[int]
-        return empty
-    one = [node_id]  # type: List[int]
-    return one
+        one = [node_id]  # type: List[int]
+        return one
+    empty = []  # type: List[int]
+    return empty
     # impl-end
 
 
@@ -124,7 +124,7 @@
     # The composite must actually answer the grouping request (measure 3:
     # strictly above the wrapped node's rule, so it may invoke that rule but
     # never re-invoke itself).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(node.inner_id, 1 / 2))
```

Attack 7 — `atk_7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```python
"""Twin-artifact model for django__django-13012.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite query node merely *wraps* another query node to attach extra
  context (an output type) to it, without otherwise altering it. When the set
  of columns this composite contributes to a grouping clause is requested, the
  composite must contribute EXACTLY the columns the node it wraps would itself
  contribute for the same grouping request — it forwards the request to the
  wrapped node and returns that node's own answer.

  Over the family of wrapped nodes this specification models — the
  non-aggregate, constant-or-column-like nodes the behaviour above is about —
  the wrapped node's own grouping-column answer follows a simple rule: a bare
  constant node contributes NO grouping columns (its answer is the empty list),
  whereas an ordinary column-like node contributes itself (its answer is the
  one-element list naming that node). The decisive correctness consequence,
  within this modelled family, is therefore: for a wrapped constant the
  composite contributes nothing, and for a wrapped column-like node the
  composite contributes the WRAPPED node — in neither case does it contribute
  the composite object itself.

  This two-case rule, and the independence of the answer from the grouping
  request below, are scoped to that modelled family; they are NOT claimed for
  every conceivable wrapped node. The composite's contract — forwarding the
  request to the wrapped node and returning that node's own answer — holds for
  ANY wrapped node regardless; the two-case rule is just the wrapped node's
  behaviour on the family this bundle models and tests.

  The grouping request (an optional alias) is threaded to the wrapped node
  unchanged; for the modelled family of nodes the answer does not depend on it.

Grouping-column lists are modelled as `List[int]` of node identities (each int
is the identity of one contributed node). A query node carries only the two
data the behaviour touches: its own identity, and — when it is a wrapper — the
identity and constant-ness of the node it wraps. The wrapped node's own
grouping-column rule, on the modelled family, is modelled DEEPLY as the verified
function `base_group_by_cols` (with its pure sequence value
`base_group_cols_seq`), whose equality to the real wrapped-node callees on that
family — and the universal forwarding behaviour of the composite — is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Termination (total correctness): both modelled operations are bounded
computations (a two-way case split, plus for the composite one call into the
wrapped node's own rule) that must actually ANSWER — deliver their
grouping-column list. Nagini is a partial-correctness verifier by default, so
without an explicit obligation a non-terminating implementation (e.g. bare
self-recursion before returning) satisfies every `Ensures` vacuously; the real
operations always complete. The obligation is carried as `MustTerminate` in
each precondition, with strictly decreasing measures so the composite may
invoke the wrapped node's rule but neither routine may re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class WrappingNode:
    def __init__(self, inner_id: int, inner_is_constant: bool, node_id: int) -> None:
        Requires(inner_id != node_id)
        Ensures(Acc(self.inner_id, 1 / 2) and self.inner_id == inner_id)            # type: ignore
        Ensures(Acc(self.inner_is_constant, 1 / 2) and self.inner_is_constant == inner_is_constant)  # type: ignore
        Ensures(Acc(self.node_id, 1 / 2) and self.node_id == node_id)               # type: ignore
        Ensures(self.inner_id != self.node_id)                                       # type: ignore
        self.inner_id = inner_id
        self.inner_is_constant = inner_is_constant
        self.node_id = node_id


# axioms-start
# (no @ContractOnly axiom is consumed: the wrapped node's grouping-column rule
#  is modelled deeply as `base_group_by_cols` below and validated against the
#  real callees out-of-band by axiom_check.py / G-AX — an A-reference, not a
#  consumed axiom.)
# axioms-end


# pure-start
@Pure
def base_group_cols_seq(node_id: int, is_constant: bool) -> PSeq[int]:
    """The grouping columns a wrapped node contributes, as a pure sequence of
    node identities, over the modelled family of non-aggregate
    constant-or-column-like nodes. A bare-constant node contributes nothing (the
    empty sequence); a column-like node in that family contributes itself (the
    one-element sequence naming it). This is the deep model of the WRAPPED
    node's own grouping-column rule on that family (G-AX validates it == the
    real callees on the family; nodes outside it, e.g. alias-dependent ones, are
    out of scope and exercised separately by G-AX via the forwarding contract)."""
    if is_constant:
        return PSeq(0).take(0)
    return PSeq(node_id)
# pure-end


def base_group_by_cols(node_id: int, is_constant: bool, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    # The wrapped node's rule is a bounded two-way case split that must answer
    # (measure 2: it may call only builtin steps, never itself).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The wrapped node's own grouping-column rule: empty for a constant,
    # otherwise the one-element list naming the node itself.
    Ensures(ToSeq(Result()) == base_group_cols_seq(node_id, is_constant))
    # post-conditions-end
    # impl-start
    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id]  # type: List[int]
    return one
    # impl-end


def wrapper_group_by_cols(node: WrappingNode, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(node.inner_id, 1 / 2))
    Requires(Acc(node.inner_is_constant, 1 / 2))
    Requires(Acc(node.node_id, 1 / 2))
    Requires(node.inner_id != node.node_id)
    # The composite must actually answer the grouping request (measure 3:
    # strictly above the wrapped node's rule, so it may invoke that rule but
    # never re-invoke itself).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.inner_id, 1 / 2))
    Ensures(Acc(node.inner_is_constant, 1 / 2))
    Ensures(Acc(node.node_id, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The composite contributes EXACTLY the columns the WRAPPED node itself
    # contributes for the same grouping request: empty for a constant, otherwise
    # the wrapped node. In particular the result is never the composite itself
    # (its identity `node.node_id` differs from the wrapped node's).
    Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
    # post-conditions-end
    # impl-start
    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols
    # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13012.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite query node merely *wraps* another query node to attach extra
  context (an output type) to it, without otherwise altering it. When the set
  of columns this composite contributes to a grouping clause is requested, the
  composite must contribute EXACTLY the columns the node it wraps would itself
  contribute for the same grouping request — it forwards the request to the
  wrapped node and returns that node's own answer.

  Over the family of wrapped nodes this specification models — the
  non-aggregate, constant-or-column-like nodes the behaviour above is about —
  the wrapped node's own grouping-column answer follows a simple rule: a bare
  constant node contributes NO grouping columns (its answer is the empty list),
  whereas an ordinary column-like node contributes itself (its answer is the
  one-element list naming that node). The decisive correctness consequence,
  within this modelled family, is therefore: for a wrapped constant the
  composite contributes nothing, and for a wrapped column-like node the
  composite contributes the WRAPPED node — in neither case does it contribute
  the composite object itself.

  This two-case rule, and the independence of the answer from the grouping
  request below, are scoped to that modelled family; they are NOT claimed for
  every conceivable wrapped node. The composite's contract — forwarding the
  request to the wrapped node and returning that node's own answer — holds for
  ANY wrapped node regardless; the two-case rule is just the wrapped node's
  behaviour on the family this bundle models and tests.

  The grouping request (an optional alias) is threaded to the wrapped node
  unchanged; for the modelled family of nodes the answer does not depend on it.

Grouping-column lists are modelled as `List[int]` of node identities (each int
is the identity of one contributed node). A query node carries only the two
data the behaviour touches: its own identity, and — when it is a wrapper — the
identity and constant-ness of the node it wraps. The wrapped node's own
grouping-column rule, on the modelled family, is modelled DEEPLY as the verified
function `base_group_by_cols` (with its pure sequence value
`base_group_cols_seq`), whose equality to the real wrapped-node callees on that
family — and the universal forwarding behaviour of the composite — is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Termination (total correctness): both modelled operations are bounded
computations (a two-way case split, plus for the composite one call into the
wrapped node's own rule) that must actually ANSWER — deliver their
grouping-column list. Nagini is a partial-correctness verifier by default, so
without an explicit obligation a non-terminating implementation (e.g. bare
self-recursion before returning) satisfies every `Ensures` vacuously; the real
operations always complete. The obligation is carried as `MustTerminate` in
each precondition, with strictly decreasing measures so the composite may
invoke the wrapped node's rule but neither routine may re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class WrappingNode:
    def __init__(self, inner_id: int, inner_is_constant: bool, node_id: int) -> None:
        Requires(inner_id != node_id)
        Ensures(Acc(self.inner_id, 1 / 2) and self.inner_id == inner_id)            # type: ignore
        Ensures(Acc(self.inner_is_constant, 1 / 2) and self.inner_is_constant == inner_is_constant)  # type: ignore
        Ensures(Acc(self.node_id, 1 / 2) and self.node_id == node_id)               # type: ignore
        Ensures(self.inner_id != self.node_id)                                       # type: ignore
        self.inner_id = inner_id
        self.inner_is_constant = inner_is_constant
        self.node_id = node_id


# axioms-start
# (no @ContractOnly axiom is consumed: the wrapped node's grouping-column rule
#  is modelled deeply as `base_group_by_cols` below and validated against the
#  real callees out-of-band by axiom_check.py / G-AX — an A-reference, not a
#  consumed axiom.)
# axioms-end


# pure-start
@Pure
def base_group_cols_seq(node_id: int, is_constant: bool) -> PSeq[int]:
    """The grouping columns a wrapped node contributes, as a pure sequence of
    node identities, over the modelled family of non-aggregate
    constant-or-column-like nodes. A bare-constant node contributes nothing (the
    empty sequence); a column-like node in that family contributes itself (the
    one-element sequence naming it). This is the deep model of the WRAPPED
    node's own grouping-column rule on that family (G-AX validates it == the
    real callees on the family; nodes outside it, e.g. alias-dependent ones, are
    out of scope and exercised separately by G-AX via the forwarding contract)."""
    if is_constant:
        return PSeq(0).take(0)
    return PSeq(node_id)
# pure-end


def base_group_by_cols(node_id: int, is_constant: bool, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    # The wrapped node's rule is a bounded two-way case split that must answer
    # (measure 2: it may call only builtin steps, never itself).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The wrapped node's own grouping-column rule: empty for a constant,
    # otherwise the one-element list naming the node itself.
    Ensures(ToSeq(Result()) == base_group_cols_seq(node_id, is_constant))
    # post-conditions-end
    # impl-start
    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id]  # type: List[int]
    return one
    # impl-end


def wrapper_group_by_cols(node: WrappingNode, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(node.inner_id, 1 / 2))
    Requires(Acc(node.inner_is_constant, 1 / 2))
    Requires(Acc(node.node_id, 1 / 2))
    Requires(node.inner_id != node.node_id)
    # The composite must actually answer the grouping request (measure 3:
    # strictly above the wrapped node's rule, so it may invoke that rule but
    # never re-invoke itself).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.inner_id, 1 / 2))
    Ensures(Acc(node.inner_is_constant, 1 / 2))
    Ensures(Acc(node.node_id, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The composite contributes EXACTLY the columns the WRAPPED node itself
    # contributes for the same grouping request: empty for a constant, otherwise
    # the wrapped node. In particular the result is never the composite itself
    # (its identity `node.node_id` differs from the wrapped node's).
    Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
    # post-conditions-end
    # impl-start
    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Tight value postcondition in BOTH editable impl regions: base_group_by_cols and wrapper_group_by_cols each pin ToSeq(Result()) == base_group_cols_seq(inner_id, inner_is_constant) ([] for constant, [inner_id] for column-like, never [node_id]), plus MustTerminate(2)/(3) blocking vacuity-by-nontermination and 1/2 field permissions. PY=python (only env importing swebench_unified), SBU_BENCHMARK_DIR=benchmark-verified.

SAME-SPEC: all 7 attacks + pos_control pass `adversary same-spec nagini django__django-13012 <f>` (exit 0; only impl regions edited).

WEAKNESS (`adversary weakness nagini django__django-13012 <f>`), run concurrently in batches of <=3 JVMs:
- atk_1 (prepatch bug: wrapper returns [node.node_id], inherited [self]) -> exit 2, NOT-A-COUNTEREXAMPLE (verification failed). prepatch_reproduced=true.
- atk_2 (partial-domain: wrapper always []) -> exit 2, verification failed.
- atk_3 (ungrounded/wrong-arg: delegate with node.node_id instead of inner_id) -> exit 2, verification failed.
- atk_4 (boundary: wrapper always [node.inner_id]) -> exit 2, verification failed.
- atk_5 (control-flow: base_group_by_cols drops constant branch, always [node_id]) -> exit 2, verification failed.
- atk_6 (boundary-swap: base_group_by_cols swaps arms constant->[node_id], else->[]) -> exit 2, verification failed.
- atk_7_echo (impl byte-identical to gold model) -> exit 0, CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 15.7s).
All 6 wrong impls (partial-domain/boundary/control-flow/wrong-arg families) are REJECTED by the spec (fail Nagini verification for the right reason: postcondition not established, not timeout/infra).

POSITIVE CONTROL: pos_control.py (= bundle model.py) verifies (`adversary verify` exit 0).

MANDATORY RESOLVE OF THE ONE CANDIDATE: atk_7_echo's whole file == gold model.py (diff empty), so its faithful refined patch is the gold patch verbatim (materialized at atk_7_echo.patch.diff). Ran through the official harness via swebench_unified.harness.run_resolve('django__django-13012', <gold patch>). Executed result: attempt 0 -> resolved=True, completed=True ('resolved').

REFINEMENT.MD AUDIT: A1 (node<->self) R; A2 (request<->alias) R; A3 (delegation) R + A-reference; A4 (return) I; B1/B2 (deep model base_group_cols_seq) A-reference validated == real Value.get_group_by_cols([]) / BaseExpression non-aggregate branch ([self]) by axiom_check.py/G-AX (two tiers: universal delegation for all node kinds incl. escaping Subquery/OrderBy, scoped dichotomy+alias-inertness for modelled family). No kind-3 leg; the only genuinely-changed op (composite forwarding) is modelled directly and verified. Model<->patch forwarding correspondence holds (self.expression.get_group_by_cols(alias=alias) <-> base_group_by_cols(inner_id, inner_is_constant, request)). No consumed @ContractOnly axiom.

Verdict SOUND: >=6 distinct wrong impls all fail verification; the sole verifying candidate is a gold echo whose materialized patch was executed through run_resolve and RESOLVED (completed=True). verify=>correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13012.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite query node merely *wraps* another query node to attach extra
  context (an output type) to it, without otherwise altering it. When the set
  of columns this composite contributes to a grouping clause is requested, the
  composite must contribute EXACTLY the columns the node it wraps would itself
  contribute for the same grouping request — it forwards the request to the
  wrapped node and returns that node's own answer.

  Over the family of wrapped nodes this specification models — the
  non-aggregate, constant-or-column-like nodes the behaviour above is about —
  the wrapped node's own grouping-column answer follows a simple rule: a bare
  constant node contributes NO grouping columns (its answer is the empty list),
  whereas an ordinary column-like node contributes itself (its answer is the
  one-element list naming that node). The decisive correctness consequence,
  within this modelled family, is therefore: for a wrapped constant the
  composite contributes nothing, and for a wrapped column-like node the
  composite contributes the WRAPPED node — in neither case does it contribute
  the composite object itself.

  This two-case rule, and the independence of the answer from the grouping
  request below, are scoped to that modelled family; they are NOT claimed for
  every conceivable wrapped node. The composite's contract — forwarding the
  request to the wrapped node and returning that node's own answer — holds for
  ANY wrapped node regardless; the two-case rule is just the wrapped node's
  behaviour on the family this bundle models and tests.

  The grouping request (an optional alias) is threaded to the wrapped node
  unchanged; for the modelled family of nodes the answer does not depend on it.

Grouping-column lists are modelled as `List[int]` of node identities (each int
is the identity of one contributed node). A query node carries only the two
data the behaviour touches: its own identity, and — when it is a wrapper — the
identity and constant-ness of the node it wraps. The wrapped node's own
grouping-column rule, on the modelled family, is modelled DEEPLY as the verified
function `base_group_by_cols` (with its pure sequence value
`base_group_cols_seq`), whose equality to the real wrapped-node callees on that
family — and the universal forwarding behaviour of the composite — is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Termination (total correctness): both modelled operations are bounded
computations (a two-way case split, plus for the composite one call into the
wrapped node's own rule) that must actually ANSWER — deliver their
grouping-column list. Nagini is a partial-correctness verifier by default, so
without an explicit obligation a non-terminating implementation (e.g. bare
self-recursion before returning) satisfies every `Ensures` vacuously; the real
operations always complete. The obligation is carried as `MustTerminate` in
each precondition, with strictly decreasing measures so the composite may
invoke the wrapped node's rule but neither routine may re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class WrappingNode:
    def __init__(self, inner_id: int, inner_is_constant: bool, node_id: int) -> None:
        Requires(inner_id != node_id)
        Ensures(Acc(self.inner_id, 1 / 2) and self.inner_id == inner_id)            # type: ignore
        Ensures(Acc(self.inner_is_constant, 1 / 2) and self.inner_is_constant == inner_is_constant)  # type: ignore
        Ensures(Acc(self.node_id, 1 / 2) and self.node_id == node_id)               # type: ignore
        Ensures(self.inner_id != self.node_id)                                       # type: ignore
        self.inner_id = inner_id
        self.inner_is_constant = inner_is_constant
        self.node_id = node_id


# axioms-start
# (no @ContractOnly axiom is consumed: the wrapped node's grouping-column rule
#  is modelled deeply as `base_group_by_cols` below and validated against the
#  real callees out-of-band by axiom_check.py / G-AX — an A-reference, not a
#  consumed axiom.)
# axioms-end


# pure-start
@Pure
def base_group_cols_seq(node_id: int, is_constant: bool) -> PSeq[int]:
    """The grouping columns a wrapped node contributes, as a pure sequence of
    node identities, over the modelled family of non-aggregate
    constant-or-column-like nodes. A bare-constant node contributes nothing (the
    empty sequence); a column-like node in that family contributes itself (the
    one-element sequence naming it). This is the deep model of the WRAPPED
    node's own grouping-column rule on that family (G-AX validates it == the
    real callees on the family; nodes outside it, e.g. alias-dependent ones, are
    out of scope and exercised separately by G-AX via the forwarding contract)."""
    if is_constant:
        return PSeq(0).take(0)
    return PSeq(node_id)
# pure-end


def base_group_by_cols(node_id: int, is_constant: bool, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    # The wrapped node's rule is a bounded two-way case split that must answer
    # (measure 2: it may call only builtin steps, never itself).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The wrapped node's own grouping-column rule: empty for a constant,
    # otherwise the one-element list naming the node itself.
    Ensures(ToSeq(Result()) == base_group_cols_seq(node_id, is_constant))
    # post-conditions-end
    # impl-start
    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id]  # type: List[int]
    return one
    # impl-end


def wrapper_group_by_cols(node: WrappingNode, request: Optional[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(node.inner_id, 1 / 2))
    Requires(Acc(node.inner_is_constant, 1 / 2))
    Requires(Acc(node.node_id, 1 / 2))
    Requires(node.inner_id != node.node_id)
    # The composite must actually answer the grouping request (measure 3:
    # strictly above the wrapped node's rule, so it may invoke that rule but
    # never re-invoke itself).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.inner_id, 1 / 2))
    Ensures(Acc(node.inner_is_constant, 1 / 2))
    Ensures(Acc(node.node_id, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The composite contributes EXACTLY the columns the WRAPPED node itself
    # contributes for the same grouping request: empty for a constant, otherwise
    # the wrapped node. In particular the result is never the composite itself
    # (its identity `node.node_id` differs from the wrapped node's).
    Ensures(ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant))
    # post-conditions-end
    # impl-start
    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Tight value postcondition in BOTH editable impl regions: base_group_by_cols and wrapper_group_by_cols each pin ToSeq(Result()) == base_group_cols_seq(inner_id, inner_is_constant) ([] for constant, [inner_id] for column-like, never [node_id]), plus MustTerminate(2)/(3) blocking vacuity-by-nontermination and 1/2 field permissions. PY=python (only env importing swebench_unified), SBU_BENCHMARK_DIR=benchmark-verified.

SAME-SPEC: all 7 attacks + pos_control pass `adversary same-spec nagini django__django-13012 <f>` (exit 0; only impl regions edited).

WEAKNESS (`adversary weakness nagini django__django-13012 <f>`), run concurrently in batches of <=3 JVMs:
- atk_1 (prepatch bug: wrapper returns [node.node_id], inherited [self]) -> exit 2, NOT-A-COUNTEREXAMPLE (verification failed). prepatch_reproduced=true.
- atk_2 (partial-domain: wrapper always []) -> exit 2, verification failed.
- atk_3 (ungrounded/wrong-arg: delegate with node.node_id instead of inner_id) -> exit 2, verification failed.
- atk_4 (boundary: wrapper always [node.inner_id]) -> exit 2, verification failed.
- atk_5 (control-flow: base_group_by_cols drops constant branch, always [node_id]) -> exit 2, verification failed.
- atk_6 (boundary-swap: base_group_by_cols swaps arms constant->[node_id], else->[]) -> exit 2, verification failed.
- atk_7_echo (impl byte-identical to gold model) -> exit 0, CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 15.7s).
All 6 wrong impls (partial-domain/boundary/control-flow/wrong-arg families) are REJECTED by the spec (fail Nagini verification for the right reason: postcondition not established, not timeout/infra).

POSITIVE CONTROL: pos_control.py (= bundle model.py) verifies (`adversary verify` exit 0).

MANDATORY RESOLVE OF THE ONE CANDIDATE: atk_7_echo's whole file == gold model.py (diff empty), so its faithful refined patch is the gold patch verbatim (materialized at atk_7_echo.patch.diff). Ran through the official harness via swebench_unified.harness.run_resolve('django__django-13012', <gold patch>). Executed result: attempt 0 -> resolved=True, completed=True ('resolved').

REFINEMENT.MD AUDIT: A1 (node<->self) R; A2 (request<->alias) R; A3 (delegation) R + A-reference; A4 (return) I; B1/B2 (deep model base_group_cols_seq) A-reference validated == real Value.get_group_by_cols([]) / BaseExpression non-aggregate branch ([self]) by axiom_check.py/G-AX (two tiers: universal delegation for all node kinds incl. escaping Subquery/OrderBy, scoped dichotomy+alias-inertness for modelled family). No kind-3 leg; the only genuinely-changed op (composite forwarding) is modelled directly and verified. Model<->patch forwarding correspondence holds (self.expression.get_group_by_cols(alias=alias) <-> base_group_by_cols(inner_id, inner_is_constant, request)). No consumed @ContractOnly axiom.

Verdict SOUND: >=6 distinct wrong impls all fail verification; the sole verifying candidate is a gold echo whose materialized patch was executed through run_resolve and RESOLVED (completed=True). verify=>correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the spec (ExpressionWrapper.get_group_by_cols model) checked against the real repo callee, base_commit 22a59c01c00cf9fbefaee0e8e67fab82bbaf1fd2 (base worktree confirmed at that SHA; post-patch tree carries the gold `return self.expression.get_group_by_cols(alias=alias)`).

Evidence:
1. model.py verifies (Nagini exit 0, 18.7s). model_prepatch.py (inherited [self] default) FAILS the postcondition (G-DIFF discriminator is real, not vacuous).
2. axiom_check.py run against the post-patch tree exits 0: 39 (node,alias) delegation cases; deep model base_group_cols_seq validated == real callees on 11 modeled-family nodes (both []/[self] arms exercised); escaping kinds (Subquery alias-dependent, OrderBy(Col) non-dichotomy) assert the domain boundary is demonstrated not assumed.
3. Direct model-vs-real comparison: for every modeled-family input (Value(3), Value(None) -> []; Lower(Value('f')), resolved Col(id) -> [inner]) across alias in {None,'T','alias0'}, the spec postcondition ToSeq(Result())==base_group_cols_seq(inner_id,is_constant) exactly equals the real ExpressionWrapper.get_group_by_cols answer. No divergence.

The spec is correctly SCOPED, not over-strong: inner_is_constant is a free model input and the postcondition only asserts the value for that classification; alias-dependent / non-dichotomy nodes are explicitly excluded from the modeled domain (never wrapped by the model) and only the universal forwarding contract is claimed for them (G-AX confirms). No input exists where the modeled function disagrees with the real callee within its stated domain. Spec region byte-integrity: markers well-formed, model/prepatch share the frozen spec (only impl region differs).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: add ExpressionWrapper.get_group_by_cols(self, alias=None) -> self.expression.get_group_by_cols(alias=alias) in django/db/models/expressions.py. Changed symbols per patch: get_group_by_cols, set_source_expressions.

Lexical G-LEAK screen: PASS (verified via swebench_unified.leakage.screen on the frozen row — hard_failures empty). No relaxation flag (relaxed_leakage=None, no RELAXED_LEAKAGE.md); recorded status 'pass' (not deferred).

Spec view (verified via markers.spec_view — impl regions elided to '...'): contains NO diff markers, NO patch.diff line reproduced, NO patched file path (django/db/models/expressions.py) or module path, and NO spec-view identifier or comment naming the patched repo symbols get_group_by_cols / set_source_expressions. Modeled symbols are abstract renames (wrapper_group_by_cols, base_group_by_cols, base_group_cols_seq, WrappingNode).

Semantic gold-reconstruction check: the spec describes desired BEHAVIOR — the composite forwards the grouping request to the wrapped node and returns that node's own answer (empty for a constant, the wrapped node for a column-like node), never contributing itself. This is entailed by the PUBLIC problem_statement, which already discloses ExpressionWrapper, that a wrapped constant (Value(3)) is wrongly kept in GROUP BY, and — decisively — that the UNWRAPPED expression is handled correctly (Django omits the constant). That public fact directly implies the fix (the wrapper must defer to the wrapped expression's grouping-column behavior). The spec adds no edit-localization beyond the public statement: no method name, no file/line, no code. The []/[self] dichotomy is ordinary behavioral specification of the wrapped-node callee, required for a faithful G-EQ spec, not a disclosure of the gold hunk. Comments describe behavior abstractly (grouping clause/request, composite/wrapped node, output type) rather than the edit.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
