# P2 adversarial audit — django__django-11299

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl found. The postcondition ToSeq(Result()) == leaf_modes(head, plain) is a FULL functional spec pinning compile_children's output exactly to the frozen leaf_modes fold, so every behavioural deviation is rejected by Nagini.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -151,8 +148,8 @@
         append_all(result, rest)
         Fold(Acc(q_pred(head), 1 / 2))
         return result
-    # group -> descend with the SAME mode, then continue with siblings.
-    sub = compile_children(head.inner, plain)
+    # group -> descend (mode not forwarded), then continue with siblings.
+    sub = compile_children(head.inner, False)
     tail = compile_children(head.nxt, plain)
     Fold(Acc(q_pred(head), 1 / 2))
     append_all(result, sub)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -146,7 +143,7 @@
         return result
     Unfold(Acc(q_pred(head), 1 / 2))
     if head.kind == 0:                          # leaf -> one column reference
-        result.append(plain)
+        result.append(not plain)
         rest = compile_children(head.nxt, plain)
         append_all(result, rest)
         Fold(Acc(q_pred(head), 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -152,7 +149,7 @@
         Fold(Acc(q_pred(head), 1 / 2))
         return result
     # group -> descend with the SAME mode, then continue with siblings.
-    sub = compile_children(head.inner, plain)
+    sub = compile_children(head.inner, not plain)
     tail = compile_children(head.nxt, plain)
     Fold(Acc(q_pred(head), 1 / 2))
     append_all(result, sub)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -155,7 +152,7 @@
     sub = compile_children(head.inner, plain)
     tail = compile_children(head.nxt, plain)
     Fold(Acc(q_pred(head), 1 / 2))
+    append_all(result, tail)
     append_all(result, sub)
-    append_all(result, tail)
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -148,7 +145,6 @@
     if head.kind == 0:                          # leaf -> one column reference
         result.append(plain)
         rest = compile_children(head.nxt, plain)
-        append_all(result, rest)
         Fold(Acc(q_pred(head), 1 / 2))
         return result
     # group -> descend with the SAME mode, then continue with siblings.
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -153,7 +150,7 @@
         return result
     # group -> descend with the SAME mode, then continue with siblings.
     sub = compile_children(head.inner, plain)
-    tail = compile_children(head.nxt, plain)
+    tail = compile_children(head.nxt, False)
     Fold(Acc(q_pred(head), 1 / 2))
     append_all(result, sub)
     append_all(result, tail)
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(result)))
     Requires(Acc(list_pred(src), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(result)))
@@ -121,7 +119,6 @@
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
         # invariants-end
         result.append(src[i])
         i = i + 1
@@ -146,7 +143,7 @@
         return result
     Unfold(Acc(q_pred(head), 1 / 2))
     if head.kind == 0:                          # leaf -> one column reference
-        result.append(plain)
+        result.append(True)
         rest = compile_children(head.nxt, plain)
         append_all(result, rest)
         Fold(Acc(q_pred(head), 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11299.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filter condition is a tree. Each node carries an ordered list of children;
  a child is either a LEAF (an atomic comparison that resolves to a single
  column reference) or a GROUP (a nested sub-condition with its own children).
  When the tree is compiled, a single boolean *plain-column* mode is chosen at
  the top: when it is set, every column reference produced anywhere in the tree
  must be the bare, table-name-free form (the form that is valid inside a check
  constraint); when it is clear, every reference is the fully-qualified form.

  Processing a node walks its children in order, turning each leaf into one
  column reference and processing each group's own children in turn. The desired
  guarantee is that the plain-column mode chosen at the top governs EVERY leaf at
  EVERY depth — a leaf nested two or more levels deep must use the same column
  form as a leaf that is a direct child of the root.

  The observable result is, in left-to-right traversal order, one boolean per
  leaf: True iff that leaf's column reference is the bare plain form. With the
  top-level mode set, every entry must be True regardless of nesting depth; a
  single nested leaf left in the qualified form is the defect this specification
  forbids.

The condition tree is modelled as a small recursive node structure (`QNode`)
in sibling/inner linked form: `kind` (0 = leaf, 1 = group), `inner` (the head
of a group's own child list) and `nxt` (the next sibling in the current child
list). The per-leaf result is a `List[bool]`, with the specification carried
over `PSeq[bool]`. `leaf_modes` is the deep model of the traversal;
`compile_children` is the verified recursive traversal.

No callee is axiomatized: the change is pure tree-traversal logic, modelled
deeply. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The behaviour under specification — every leaf's column
# form is governed by the top plain-column mode at every nesting depth — is
# modelled DEEPLY by the pure `leaf_modes` fold below and the verified recursive
# `compile_children` impl, not behind a @ContractOnly. G-EQ audits the
# refinement to the real compiler.)
# axioms-end


# pure-start
class QNode:
    """One position in a filter-condition tree, in sibling/inner linked form.
    A node is the head of a child list: `nxt` is the next sibling in that list;
    `inner` (for a group) is the head of the group's own child list."""

    def __init__(self, kind: int, inner: 'Optional[QNode]',
                 nxt: 'Optional[QNode]') -> None:
        Requires(Implies(inner is not None, Acc(q_pred(inner))))
        Requires(Implies(nxt is not None, Acc(q_pred(nxt))))
        Ensures(Acc(q_pred(self)))
        Ensures(q_kind(self) == kind)
        self.kind = kind      # 0 = leaf, 1 = group
        self.inner = inner    # head of a group's child list (meaningful if group)
        self.nxt = nxt        # next sibling in the current child list
        Fold(q_pred(self))


@Predicate
def q_pred(n: QNode) -> bool:
    return (Acc(n.kind) and Acc(n.inner) and Acc(n.nxt) and
            Implies(n.inner is not None, q_pred(n.inner)) and
            Implies(n.nxt is not None, q_pred(n.nxt)))


@Pure
def q_kind(n: QNode) -> int:
    Requires(Acc(q_pred(n), 1 / 2))
    return Unfolding(Acc(q_pred(n), 1 / 2), n.kind)


@Pure
def empty_modes() -> PSeq[bool]:
    return PSeq(True).take(0)


@Pure
def leaf_modes(head: Optional[QNode], plain: bool) -> PSeq[bool]:
    """Per-leaf plain-column flags for the child list starting at `head`, in
    left-to-right traversal order, when the surrounding mode is `plain`.

    A leaf contributes one flag equal to the current mode; a group contributes
    the flags of its own children evaluated at the SAME mode, followed by the
    flags of the rest of the list."""
    Requires(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    if head is None:
        return empty_modes()
    if q_kind(head) == 0:                       # leaf: one flag at current mode
        return Unfolding(Acc(q_pred(head), 1 / 2),
                         PSeq(plain) + leaf_modes(head.nxt, plain))
    # group: its children at the SAME mode, then continue with the siblings.
    return Unfolding(Acc(q_pred(head), 1 / 2),
                     leaf_modes(head.inner, plain) + leaf_modes(head.nxt, plain))
# pure-end


def append_all(result: List[bool], src: List[bool]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def compile_children(head: Optional[QNode], plain: bool) -> List[bool]:
    # pre-conditions-start
    Requires(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The traversal yields exactly one flag per leaf, in order, every flag
    # governed by the top mode at every nesting depth.
    Ensures(ToSeq(Result()) == leaf_modes(head, plain))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    if head is None:
        return result
    Unfold(Acc(q_pred(head), 1 / 2))
    if head.kind == 0:                          # leaf -> one column reference
        result.append(plain)
        rest = compile_children(head.nxt, plain)
        append_all(result, rest)
        Fold(Acc(q_pred(head), 1 / 2))
        return result
    # group -> descend with the SAME mode, then continue with siblings.
    sub = compile_children(head.inner, plain)
    tail = compile_children(head.nxt, plain)
    Fold(Acc(q_pred(head), 1 / 2))
    append_all(result, sub)
    append_all(result, tail)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL — all runs with swebench-lean python and SBU_BENCHMARK_DIR=benchmark-verified; each `weakness` run = same-spec + Nagini verify (JVM+Z3), executed in 3 background batches of <=3.

7 same-spec WRONG impls (impl region of compile_children edited ONLY; axioms/@Pure/Requires/Ensures byte-identical — `adversary same-spec` returned exit 0 for all 7 + positive_control):
  atk_1.py = model_prepatch.py = recorded prepatch bug (group inner descends with False, not plain) [control-flow/data]
  atk_2.py = leaf appends `not plain` [boundary / oracle inversion]
  atk_3.py = group inner descends with `not plain` [ungrounded]
  atk_4.py = append order swapped, tail before sub [control-flow-effect: ordering]
  atk_5.py = leaf drops its siblings (removes append_all(rest)) [partial-domain]
  atk_6.py = group siblings (nxt) descend with False [control-flow-effect on nxt]
  atk_7.py = leaf appends constant True, ignoring plain [ungrounded-oracle echo]

Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-11299 <atk>`.
RESULTS: positive_control -> CANDIDATE (verifies, 21.3s); atk_1..atk_7 -> ALL 'NOT-A-COUNTEREXAMPLE: attack does not verify' (exit 2). No CANDIDATE among the wrong impls, therefore NO faithful refined patch needed a resolve run (verify⇏correct gap does not exist). prepatch_reproduced=true: atk_1 (=model_prepatch.py) FAILS verification, so the frozen postcondition senses the gold edit (G-DIFF).

REFINEMENT.MD AUDIT: every leg is R / A-reference / I — no kind-3. There is NO consumed axiom. The single changed op (A5: forwarding the plain-column mode into the recursive descent) is modeled DEEPLY by leaf_modes's group clause (leaf_modes(inner, plain) forwards plain unchanged) and pinned by the full-functional postcondition. The lone A-reference (B1: leaf_modes ↔ real Query.build_where) is validated out-of-band by axiom_check.py (8 trees/26 leaves all SimpleCol at every depth + prepatch discriminator yielding a nested Col) and conformance_check.py (100k+ (tree,mode) inputs, seed 112990, 0 disagreements) — both run the REAL patched Django _add_q; correspondence holds (group clause forwards the mode, matching the gold's appended simple_col). Model↔patch correspondence is sound.

VERDICT: SOUND — >=5 distinct same-spec wrong impls run, prepatch reproduced, positive control verifies, none of the wrong impls verify; A-legs and model↔patch correspondence hold.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl found. The postcondition ToSeq(Result()) == leaf_modes(head, plain) is a FULL functional spec pinning compile_children's output exactly to the frozen leaf_modes fold, so every behavioural deviation is rejected by Nagini.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11299.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filter condition is a tree. Each node carries an ordered list of children;
  a child is either a LEAF (an atomic comparison that resolves to a single
  column reference) or a GROUP (a nested sub-condition with its own children).
  When the tree is compiled, a single boolean *plain-column* mode is chosen at
  the top: when it is set, every column reference produced anywhere in the tree
  must be the bare, table-name-free form (the form that is valid inside a check
  constraint); when it is clear, every reference is the fully-qualified form.

  Processing a node walks its children in order, turning each leaf into one
  column reference and processing each group's own children in turn. The desired
  guarantee is that the plain-column mode chosen at the top governs EVERY leaf at
  EVERY depth — a leaf nested two or more levels deep must use the same column
  form as a leaf that is a direct child of the root.

  The observable result is, in left-to-right traversal order, one boolean per
  leaf: True iff that leaf's column reference is the bare plain form. With the
  top-level mode set, every entry must be True regardless of nesting depth; a
  single nested leaf left in the qualified form is the defect this specification
  forbids.

The condition tree is modelled as a small recursive node structure (`QNode`)
in sibling/inner linked form: `kind` (0 = leaf, 1 = group), `inner` (the head
of a group's own child list) and `nxt` (the next sibling in the current child
list). The per-leaf result is a `List[bool]`, with the specification carried
over `PSeq[bool]`. `leaf_modes` is the deep model of the traversal;
`compile_children` is the verified recursive traversal.

No callee is axiomatized: the change is pure tree-traversal logic, modelled
deeply. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The behaviour under specification — every leaf's column
# form is governed by the top plain-column mode at every nesting depth — is
# modelled DEEPLY by the pure `leaf_modes` fold below and the verified recursive
# `compile_children` impl, not behind a @ContractOnly. G-EQ audits the
# refinement to the real compiler.)
# axioms-end


# pure-start
class QNode:
    """One position in a filter-condition tree, in sibling/inner linked form.
    A node is the head of a child list: `nxt` is the next sibling in that list;
    `inner` (for a group) is the head of the group's own child list."""

    def __init__(self, kind: int, inner: 'Optional[QNode]',
                 nxt: 'Optional[QNode]') -> None:
        Requires(Implies(inner is not None, Acc(q_pred(inner))))
        Requires(Implies(nxt is not None, Acc(q_pred(nxt))))
        Ensures(Acc(q_pred(self)))
        Ensures(q_kind(self) == kind)
        self.kind = kind      # 0 = leaf, 1 = group
        self.inner = inner    # head of a group's child list (meaningful if group)
        self.nxt = nxt        # next sibling in the current child list
        Fold(q_pred(self))


@Predicate
def q_pred(n: QNode) -> bool:
    return (Acc(n.kind) and Acc(n.inner) and Acc(n.nxt) and
            Implies(n.inner is not None, q_pred(n.inner)) and
            Implies(n.nxt is not None, q_pred(n.nxt)))


@Pure
def q_kind(n: QNode) -> int:
    Requires(Acc(q_pred(n), 1 / 2))
    return Unfolding(Acc(q_pred(n), 1 / 2), n.kind)


@Pure
def empty_modes() -> PSeq[bool]:
    return PSeq(True).take(0)


@Pure
def leaf_modes(head: Optional[QNode], plain: bool) -> PSeq[bool]:
    """Per-leaf plain-column flags for the child list starting at `head`, in
    left-to-right traversal order, when the surrounding mode is `plain`.

    A leaf contributes one flag equal to the current mode; a group contributes
    the flags of its own children evaluated at the SAME mode, followed by the
    flags of the rest of the list."""
    Requires(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    if head is None:
        return empty_modes()
    if q_kind(head) == 0:                       # leaf: one flag at current mode
        return Unfolding(Acc(q_pred(head), 1 / 2),
                         PSeq(plain) + leaf_modes(head.nxt, plain))
    # group: its children at the SAME mode, then continue with the siblings.
    return Unfolding(Acc(q_pred(head), 1 / 2),
                     leaf_modes(head.inner, plain) + leaf_modes(head.nxt, plain))
# pure-end


def append_all(result: List[bool], src: List[bool]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def compile_children(head: Optional[QNode], plain: bool) -> List[bool]:
    # pre-conditions-start
    Requires(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(head is not None, Acc(q_pred(head), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The traversal yields exactly one flag per leaf, in order, every flag
    # governed by the top mode at every nesting depth.
    Ensures(ToSeq(Result()) == leaf_modes(head, plain))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    if head is None:
        return result
    Unfold(Acc(q_pred(head), 1 / 2))
    if head.kind == 0:                          # leaf -> one column reference
        result.append(plain)
        rest = compile_children(head.nxt, plain)
        append_all(result, rest)
        Fold(Acc(q_pred(head), 1 / 2))
        return result
    # group -> descend with the SAME mode, then continue with siblings.
    sub = compile_children(head.inner, plain)
    tail = compile_children(head.nxt, plain)
    Fold(Acc(q_pred(head), 1 / 2))
    append_all(result, sub)
    append_all(result, tail)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL — all runs with swebench-lean python and SBU_BENCHMARK_DIR=benchmark-verified; each `weakness` run = same-spec + Nagini verify (JVM+Z3), executed in 3 background batches of <=3.

7 same-spec WRONG impls (impl region of compile_children edited ONLY; axioms/@Pure/Requires/Ensures byte-identical — `adversary same-spec` returned exit 0 for all 7 + positive_control):
  atk_1.py = model_prepatch.py = recorded prepatch bug (group inner descends with False, not plain) [control-flow/data]
  atk_2.py = leaf appends `not plain` [boundary / oracle inversion]
  atk_3.py = group inner descends with `not plain` [ungrounded]
  atk_4.py = append order swapped, tail before sub [control-flow-effect: ordering]
  atk_5.py = leaf drops its siblings (removes append_all(rest)) [partial-domain]
  atk_6.py = group siblings (nxt) descend with False [control-flow-effect on nxt]
  atk_7.py = leaf appends constant True, ignoring plain [ungrounded-oracle echo]

Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-11299 <atk>`.
RESULTS: positive_control -> CANDIDATE (verifies, 21.3s); atk_1..atk_7 -> ALL 'NOT-A-COUNTEREXAMPLE: attack does not verify' (exit 2). No CANDIDATE among the wrong impls, therefore NO faithful refined patch needed a resolve run (verify⇏correct gap does not exist). prepatch_reproduced=true: atk_1 (=model_prepatch.py) FAILS verification, so the frozen postcondition senses the gold edit (G-DIFF).

REFINEMENT.MD AUDIT: every leg is R / A-reference / I — no kind-3. There is NO consumed axiom. The single changed op (A5: forwarding the plain-column mode into the recursive descent) is modeled DEEPLY by leaf_modes's group clause (leaf_modes(inner, plain) forwards plain unchanged) and pinned by the full-functional postcondition. The lone A-reference (B1: leaf_modes ↔ real Query.build_where) is validated out-of-band by axiom_check.py (8 trees/26 leaves all SimpleCol at every depth + prepatch discriminator yielding a nested Col) and conformance_check.py (100k+ (tree,mode) inputs, seed 112990, 0 disagreements) — both run the REAL patched Django _add_q; correspondence holds (group clause forwards the mode, matching the gold's appended simple_col). Model↔patch correspondence is sound.

VERDICT: SOUND — >=5 distinct same-spec wrong impls run, prepatch reproduced, positive control verifies, none of the wrong impls verify; A-legs and model↔patch correspondence hold.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the nagini bundle for django__django-11299. Modeled function compile_children/leaf_modes models Query._add_q (entered via build_where with simple_col=True); the spec claims that with the top plain-column mode set, every leaf at every nesting depth resolves to the bare SimpleCol form (flag True), i.e. the mode is forwarded unchanged into every group descent.

Machine-checkable verification against the REAL patched repo (worktree; git shows the gold hunk applied — 1-token addition of simple_col to the recursive _add_q call — on query.py:1339-1341):
  * same-spec tool on the bundle model.py -> SAME (exit 0): spec region byte-identical / intact.
  * conformance_check.py re-run against the gold worktree: G-CONF OK, 100,044 (tree,mode) inputs (22 boundary shapes: leaves at depth 0..8, empty groups, wide flat lists, sibling groups, staircase nesting; x2 modes + 100,000 seeded fuzz, seed 112990) — 0 disagreements. The contract-stripped impl region equals the real _add_q on every input, and the internal cross-check (impl == pure fold leaf_modes) also holds.
  * axiom_check.py (G-AX): deep model leaf_modes == real build_where on 8 trees / 26 leaves, all SimpleCol at every depth; pre-patch discriminator correctly yields a nested Col.
  * Independent adversarial probes I authored (depth-4 nesting; negated nested groups; double negation ~(A & ~(B | ~C))) all produce all-True flag sequences matching leaf_modes — no leaf reverts to Col under simple_col=True.

One apparent divergence examined and rejected as out-of-carrier: Q(num__gt=F('other')+1) yields a rhs Col because the rhs is a CombinedExpression (Col+Value) whose inner column is not rewritten by the patch. This is NOT a spec defect: (a) the leaf's own column (lhs) is still SimpleCol; (b) the model abstracts each leaf to a SINGLE column reference (its lhs), and both conformance_check.py and the F2P test tests/queries/test_query.py only observe single-column leaves' lhs (and plain-F multi-field lhs/rhs); (c) the gold patch does not touch CombinedExpression column rewriting. The carrier abstraction (Q/WhereNode tree -> QNode sibling/inner; simple_col -> plain; SimpleCol-vs-Col -> bool; connectors/negation held orthogonal) is sound and matches exactly what the resolving test observes. Within the modeled domain no input was found where the modeled function disagrees with the real callee. The spec is neither too strong nor drifted. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Spec view (markers.spec_view over model.py; impl regions elided) verified against the public problem_statement only, NOT hints_text.

Checks:
- Diff markers: none in spec view.
- Gold-patch lines: the sole changed line ('current_negated, allow_joins, split_subq, simple_col)') is not reproduced.
- Patched file/module path: 'django/db/models/sql/query.py' does not appear.
- Changed repo symbol: patch touches only '_add_q' (add_q after strip). Spec-view identifiers are QNode/plain/compile_children/leaf_modes/q_pred/q_kind/append_all/empty_modes — none embed 'add_q'; no spec-view comment names it. Repo symbols simple_col/SimpleCol/Col/build_filter/build_where are absent from the spec view.
- Narration: no screened terms (bug/fix/incorrectly/wrong/broken/patch...). Uses neutral 'defect'/'desired behaviour'.

Semantic leakage assessment: the spec restates only the DESIRED behaviour that the public problem_statement already fully discloses. The problem_statement states the failure is a combination of OR and AND clauses where 'the AND clause items using Col while the OR clause uses SimpleCol', and that the proper output uses the bare/table-name-free column form throughout, including nested clauses. The spec's core guarantee — a single top-level plain-column mode must govern EVERY leaf at EVERY depth (nested leaves use the same bare form as root-level leaves) — is exactly this public requirement expressed abstractly over a generic condition tree. The code-level gold edit (which recursive call receives the mode argument) is hidden: the impl region is elided in the spec view and the changed function/argument names never appear. The spec discloses nothing about the edit's mechanism beyond the public task.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
