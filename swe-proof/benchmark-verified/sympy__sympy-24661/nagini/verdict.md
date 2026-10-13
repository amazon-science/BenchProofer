# P2 adversarial audit — sympy__sympy-24661

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
@@ -170,11 +170,5 @@
     Ensures(Result().op == node.op)
     # post-conditions-end
     # impl-start
-    if is_relational(node.op):
-        sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
     return Node(False, REL_NONE, False, node.left, node.right, node.op)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,10 +171,12 @@
     # post-conditions-end
     # impl-start
     if is_relational(node.op):
-        sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
+        if node.op == OP_LT:
+            sympy_class = REL_GT
+        elif node.op == OP_GT:
+            sympy_class = REL_LT
+        else:
+            sympy_class = rel_class_of(node.op)
+        return Node(True, sympy_class, False, node.left, node.right, node.op)
     return Node(False, REL_NONE, False, node.left, node.right, node.op)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -172,9 +172,6 @@
     # impl-start
     if is_relational(node.op):
         sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
+        return Node(True, sympy_class, False, node.right, node.left, node.op)
     return Node(False, REL_NONE, False, node.left, node.right, node.op)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -172,9 +172,6 @@
     # impl-start
     if is_relational(node.op):
         sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
+        return Node(True, sympy_class, True, node.left, node.right, node.op)
     return Node(False, REL_NONE, False, node.left, node.right, node.op)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -170,11 +170,8 @@
     Ensures(Result().op == node.op)
     # post-conditions-end
     # impl-start
-    if is_relational(node.op):
+    if is_relational(node.op) and node.op != OP_EQ:
         sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
+        return Node(True, sympy_class, False, node.left, node.right, node.op)
     return Node(False, REL_NONE, False, node.left, node.right, node.op)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -170,11 +170,6 @@
     Ensures(Result().op == node.op)
     # post-conditions-end
     # impl-start
-    if is_relational(node.op):
-        sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
-    return Node(False, REL_NONE, False, node.left, node.right, node.op)
+    sympy_class = rel_class_of(node.op)
+    return Node(True, sympy_class, False, node.left, node.right, node.op)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -170,11 +170,9 @@
     Ensures(Result().op == node.op)
     # post-conditions-end
     # impl-start
-    if is_relational(node.op):
-        sympy_class = rel_class_of(node.op)
-        right = node.right
-        left = node.left
-        new_node = Node(True, sympy_class, False, left, right, node.op)
-        return new_node
-    return Node(False, REL_NONE, False, node.left, node.right, node.op)
+    rc = rel_call = rel_class_of(node.op)
+    conv = rel_call != REL_NONE
+    if conv:
+        return Node(True, rel_call, False, node.left, node.right, node.op)
+    return Node(False, rel_call, False, node.left, node.right, node.op)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-24661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a symbolic expression is parsed in a non-evaluating mode, a comparison
  between two operands must be preserved as the corresponding symbolic
  comparison object rather than being collapsed to a concrete truth value.

  Concretely, the parse step that rewrites a syntax node so that the operation
  stays symbolic receives a comparison node carrying one comparison operator
  and two operands. For each of the six comparison operators

      strict-less, less-or-equal, strict-greater, greater-or-equal,
      not-equal, equal

  the rewritten node is a *call* to the matching symbolic-comparison
  constructor, applied to the (independently rewritten) left and right
  operands, with the non-evaluating flag set. The operator-to-constructor
  correspondence is the prescribed bijection

      strict-less -> Lt,  less-or-equal -> Le,  strict-greater -> Gt,
      greater-or-equal -> Ge,  not-equal -> Ne,  equal -> Eq.

  A comparison whose operator is none of these six (e.g. membership or
  identity) is returned unchanged: it is NOT turned into a symbolic-comparison
  call.

The comparison syntax node and its rewritten form are modelled as small
classes carrying only the fields the rewrite touches (the operator code, the
constructor code, the non-evaluating flag, and the two operand nodes). The
operand nodes are opaque carriers; the rewrite recurses into them but their
internal structure is irrelevant to the property under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# Operator codes for the comparison operators a comparison node may carry.
OP_LT = 0   # strict-less
OP_LE = 1   # less-or-equal
OP_GT = 2   # strict-greater
OP_GE = 3   # greater-or-equal
OP_NE = 4   # not-equal
OP_EQ = 5   # equal
# Any operator code >= 6 denotes a comparison operator outside the relational
# set (e.g. membership / identity), which must NOT be converted.

# Constructor codes for the produced symbolic-comparison call.
REL_LT = 100
REL_LE = 101
REL_GT = 102
REL_GE = 103
REL_NE = 104
REL_EQ = 105
REL_NONE = -1   # sentinel: no symbolic-comparison constructor (node unchanged)


class Expr:
    """An opaque operand expression node (rewrite recurses into it; its
    internal structure is irrelevant to the property under specification)."""

    def __init__(self) -> None:
        Ensures(Acc(self.tag) and self.tag == 0)  # type: ignore[name-defined]
        self.tag = 0  # type: int


class Compare:
    """A comparison syntax node: one comparison operator and two operands."""

    def __init__(self, op: int, left: Expr, right: Expr) -> None:
        Requires(Acc(left.tag, 1 / 2) and Acc(right.tag, 1 / 2))
        Ensures(Acc(self.op) and self.op == op)  # type: ignore[name-defined]
        Ensures(Acc(self.left) and self.left is left)  # type: ignore[name-defined]
        Ensures(Acc(self.right) and self.right is right)  # type: ignore[name-defined]
        Ensures(Acc(left.tag, 1 / 2) and Acc(right.tag, 1 / 2))
        self.op = op        # type: int
        self.left = left    # type: Expr
        self.right = right  # type: Expr


class Node:
    """The rewritten node. Either a symbolic-comparison call
    (is_call == True), carrying the constructor code, the non-evaluating flag,
    and the two (visited) operands; or the unchanged comparison node
    (is_call == False)."""

    def __init__(self, is_call: bool, rel_class: int, evaluate: bool,
                 left: Optional[Expr], right: Optional[Expr],
                 op: int) -> None:
        Ensures(Acc(self.is_call) and self.is_call == is_call)  # type: ignore[name-defined]
        Ensures(Acc(self.rel_class) and self.rel_class == rel_class)  # type: ignore[name-defined]
        Ensures(Acc(self.evaluate) and self.evaluate == evaluate)  # type: ignore[name-defined]
        Ensures(Acc(self.left) and self.left is left)  # type: ignore[name-defined]
        Ensures(Acc(self.right) and self.right is right)  # type: ignore[name-defined]
        Ensures(Acc(self.op) and self.op == op)  # type: ignore[name-defined]
        self.is_call = is_call      # type: bool
        self.rel_class = rel_class  # type: int
        self.evaluate = evaluate    # type: bool
        self.left = left            # type: Optional[Expr]
        self.right = right          # type: Optional[Expr]
        self.op = op                # type: int


# axioms-start
# (no axioms: the rewrite is a pure, fully-expressible AST transformation;
#  it calls no unchanged external callee.)
# axioms-end


# pure-start
@Pure
def is_relational(op: int) -> bool:
    """The operator codes that name a symbolic comparison constructor."""
    return op == OP_LT or op == OP_LE or op == OP_GT or \
        op == OP_GE or op == OP_NE or op == OP_EQ


@Pure
def rel_class_of(op: int) -> int:
    """The prescribed operator-to-constructor correspondence."""
    if op == OP_LT:
        return REL_LT
    if op == OP_LE:
        return REL_LE
    if op == OP_GT:
        return REL_GT
    if op == OP_GE:
        return REL_GE
    if op == OP_NE:
        return REL_NE
    if op == OP_EQ:
        return REL_EQ
    return REL_NONE
# pure-end


def rewrite_comparison(node: Compare) -> Node:
    # pre-conditions-start
    Requires(Acc(node.op, 1 / 2))
    Requires(Acc(node.left, 1 / 2) and Acc(node.right, 1 / 2))
    Requires(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.op, 1 / 2))
    Ensures(Acc(node.left, 1 / 2) and Acc(node.right, 1 / 2))
    Ensures(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    Ensures(Acc(Result().is_call) and Acc(Result().rel_class) and
            Acc(Result().evaluate) and Acc(Result().left) and
            Acc(Result().right) and Acc(Result().op))
    # A relational comparison is converted to a symbolic-comparison call ...
    Ensures(Result().is_call == is_relational(node.op))
    # ... whose constructor matches the operator under the prescribed bijection.
    Ensures(Result().rel_class == rel_class_of(node.op))
    # The non-evaluating flag is set: a produced symbolic-comparison call never
    # evaluates its operands.
    Ensures(Result().evaluate == False)
    # ... applied to the two visited operands, in original left/right order.
    # The operand pin is UNCONDITIONAL: a produced symbolic-comparison call
    # carries the two operands in source order, and an unchanged non-relational
    # comparison keeps its own operands (the real rewrite returns the node
    # itself, operands included). Leaving the operands free on either branch
    # would admit an implementation that drops or reorders them.
    Ensures(Result().left is node.left and Result().right is node.right)
    # The operator code is preserved UNCONDITIONALLY: an unchanged
    # non-relational comparison keeps its operator, and a produced call records
    # the operator it was built from. This pins every field of the result as a
    # function of the input, leaving no unconstrained channel.
    Ensures(Result().op == node.op)
    # post-conditions-end
    # impl-start
    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY — sympy__sympy-24661 nagini G-EQ (refinement fidelity, focus on A-legs + model<->patch correspondence). Verdict SOUND.

SBU_BENCHMARK_DIR=benchmark-verified; python python;

SPEC SHAPE: rewrite_comparison's postconditions pin EVERY output field of the result Node as a function of the input, UNCONDITIONALLY: is_call==is_relational(op); rel_class==rel_class_of(op); evaluate==False; Result().left is node.left AND Result().right is node.right; Result().op==node.op. There is no free/unconstrained channel on either branch, so any verifying impl must reproduce gold-equivalent field values.

ATTACKS (7 distinct wrong impls; each copied model.py editing ONLY the impl region; same-spec confirmed byte-identical for all 7 + positive control). Command form: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24661 <path>` (verify runs concurrent, <=3 JVM+Z3 jobs at a time).
- atk_1.py PREPATCH bug (never convert; is_call always False): NOT-A-COUNTEREXAMPLE (verification failed) => prepatch reproduced, spec senses the change (G-DIFF).
- atk_2.py swapped bijection (OP_LT->REL_GT, OP_GT->REL_LT): NOT-A-COUNTEREXAMPLE (verification failed; fails rel_class==rel_class_of).
- atk_3.py swapped operand order (left/right reversed): NOT-A-COUNTEREXAMPLE (verification failed; fails Result().left is node.left).
- atk_4.py evaluate=True on the produced call: NOT-A-COUNTEREXAMPLE (verification failed; fails evaluate==False).
- atk_5.py partial-domain/boundary (convert all relational EXCEPT OP_EQ): NOT-A-COUNTEREXAMPLE (verification failed; fails is_call==is_relational on OP_EQ).
- atk_6.py control-flow-effect (always Node(True,...) even for non-relational, rel_class=rel_class_of=REL_NONE): NOT-A-COUNTEREXAMPLE (verification failed; fails is_call==is_relational on non-relational op).
- atk_7.py ungrounded-oracle ECHO (rel_call=rel_class_of(op); conv = rel_call!=REL_NONE; Node(conv,...) each branch): CANDIDATE-COUNTEREXAMPLE — shares spec AND verifies (19.2s).

MANDATORY RESOLVE ON THE CANDIDATE: atk_7 is behaviorally identical to gold (conv == is_relational; produces the same Node field values as the model on both branches). Materialized its faithful refined patch (atk_7_patch.diff, a .get()-based reformulation of the gold visit_Compare — same behavior) and RAN it through the official harness via swebench_unified.harness.run_resolve:
  ATK7: resolved=True completed=True note=resolved
  GOLD baseline: resolved=True completed=True note=resolved
The verifying wrong impl's faithful patch RESOLVES => it is a gold-equivalent echo, NOT a weakness (per the 2026-08-06 echo policy: a same-spec verifying attack fails the gate only if its refined patch does NOT resolve). No BROKEN condition triggered.

POSITIVE CONTROL: positive_control.py = verbatim model.py; `adversary verify` => VERIFIED in 21.5s.

A-LEG / deep-model AUDIT (refinement.md focus): NO consumed @ContractOnly axiom (axioms region empty by design). Sole A-leg is B1 A-REFERENCE: the model's rel_class_of/is_relational + produced-node shape == the real post-patch EvaluateFalseTransformer.visit_Compare. Re-ran G-AX FRESH (gates.ax.run, ax_apply_gold=True, in the instance Docker image) => status=pass: 'matches the model on all 6 relational operators (Lt/Le/Gt/Ge/Ne/Eq, evaluate=False, left/right order) and 4 non-relational operators (unchanged).' Correspondence to the real callee holds.

REFINEMENT.MD LEG AUDIT: rows A1-A6 are all R (type refinement: ast.Compare<->Compare, dict<->rel_class_of/is_relational, class-name str<->int constructor code, ast.Call<->Node) or I (row A4/C: self.visit(operand) identity on integer-literal operands, the F2P test_issue_24288 domain, encoded via opaque Expr carrier). Section C's operand self.visit is a transparently-disclosed I-step scoped to the tested domain (non-leaf operands would recurse, but the conversion property is independent of operand recursion). Section D: no kind-3 (unexpressible-changed-op) step — the genuinely-changed op is deeply modeled, not hidden behind an axiom. All legs classify R / I / A-reference; no A-consumed, no kind-3. Correspondence sound.

CONCLUSION: 7 attacks run (>=5 distinct wrong-impl classes: prepatch, wrong-bijection, operand-reorder, wrong-flag, partial-domain/boundary, control-flow-effect, ungrounded-oracle echo). 6 rejected by the verifier; the 1 CANDIDATE (echo) had its faithful patch executed through the official harness and RESOLVED. Positive control verifies; A-reference re-validated by fresh G-AX. No verifying wrong impl whose faithful patch fails to resolve exists. verify => correct holds. VERDICT: SOUND.

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
"""Twin-artifact model for sympy__sympy-24661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a symbolic expression is parsed in a non-evaluating mode, a comparison
  between two operands must be preserved as the corresponding symbolic
  comparison object rather than being collapsed to a concrete truth value.

  Concretely, the parse step that rewrites a syntax node so that the operation
  stays symbolic receives a comparison node carrying one comparison operator
  and two operands. For each of the six comparison operators

      strict-less, less-or-equal, strict-greater, greater-or-equal,
      not-equal, equal

  the rewritten node is a *call* to the matching symbolic-comparison
  constructor, applied to the (independently rewritten) left and right
  operands, with the non-evaluating flag set. The operator-to-constructor
  correspondence is the prescribed bijection

      strict-less -> Lt,  less-or-equal -> Le,  strict-greater -> Gt,
      greater-or-equal -> Ge,  not-equal -> Ne,  equal -> Eq.

  A comparison whose operator is none of these six (e.g. membership or
  identity) is returned unchanged: it is NOT turned into a symbolic-comparison
  call.

The comparison syntax node and its rewritten form are modelled as small
classes carrying only the fields the rewrite touches (the operator code, the
constructor code, the non-evaluating flag, and the two operand nodes). The
operand nodes are opaque carriers; the rewrite recurses into them but their
internal structure is irrelevant to the property under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# Operator codes for the comparison operators a comparison node may carry.
OP_LT = 0   # strict-less
OP_LE = 1   # less-or-equal
OP_GT = 2   # strict-greater
OP_GE = 3   # greater-or-equal
OP_NE = 4   # not-equal
OP_EQ = 5   # equal
# Any operator code >= 6 denotes a comparison operator outside the relational
# set (e.g. membership / identity), which must NOT be converted.

# Constructor codes for the produced symbolic-comparison call.
REL_LT = 100
REL_LE = 101
REL_GT = 102
REL_GE = 103
REL_NE = 104
REL_EQ = 105
REL_NONE = -1   # sentinel: no symbolic-comparison constructor (node unchanged)


class Expr:
    """An opaque operand expression node (rewrite recurses into it; its
    internal structure is irrelevant to the property under specification)."""

    def __init__(self) -> None:
        Ensures(Acc(self.tag) and self.tag == 0)  # type: ignore[name-defined]
        self.tag = 0  # type: int


class Compare:
    """A comparison syntax node: one comparison operator and two operands."""

    def __init__(self, op: int, left: Expr, right: Expr) -> None:
        Requires(Acc(left.tag, 1 / 2) and Acc(right.tag, 1 / 2))
        Ensures(Acc(self.op) and self.op == op)  # type: ignore[name-defined]
        Ensures(Acc(self.left) and self.left is left)  # type: ignore[name-defined]
        Ensures(Acc(self.right) and self.right is right)  # type: ignore[name-defined]
        Ensures(Acc(left.tag, 1 / 2) and Acc(right.tag, 1 / 2))
        self.op = op        # type: int
        self.left = left    # type: Expr
        self.right = right  # type: Expr


class Node:
    """The rewritten node. Either a symbolic-comparison call
    (is_call == True), carrying the constructor code, the non-evaluating flag,
    and the two (visited) operands; or the unchanged comparison node
    (is_call == False)."""

    def __init__(self, is_call: bool, rel_class: int, evaluate: bool,
                 left: Optional[Expr], right: Optional[Expr],
                 op: int) -> None:
        Ensures(Acc(self.is_call) and self.is_call == is_call)  # type: ignore[name-defined]
        Ensures(Acc(self.rel_class) and self.rel_class == rel_class)  # type: ignore[name-defined]
        Ensures(Acc(self.evaluate) and self.evaluate == evaluate)  # type: ignore[name-defined]
        Ensures(Acc(self.left) and self.left is left)  # type: ignore[name-defined]
        Ensures(Acc(self.right) and self.right is right)  # type: ignore[name-defined]
        Ensures(Acc(self.op) and self.op == op)  # type: ignore[name-defined]
        self.is_call = is_call      # type: bool
        self.rel_class = rel_class  # type: int
        self.evaluate = evaluate    # type: bool
        self.left = left            # type: Optional[Expr]
        self.right = right          # type: Optional[Expr]
        self.op = op                # type: int


# axioms-start
# (no axioms: the rewrite is a pure, fully-expressible AST transformation;
#  it calls no unchanged external callee.)
# axioms-end


# pure-start
@Pure
def is_relational(op: int) -> bool:
    """The operator codes that name a symbolic comparison constructor."""
    return op == OP_LT or op == OP_LE or op == OP_GT or \
        op == OP_GE or op == OP_NE or op == OP_EQ


@Pure
def rel_class_of(op: int) -> int:
    """The prescribed operator-to-constructor correspondence."""
    if op == OP_LT:
        return REL_LT
    if op == OP_LE:
        return REL_LE
    if op == OP_GT:
        return REL_GT
    if op == OP_GE:
        return REL_GE
    if op == OP_NE:
        return REL_NE
    if op == OP_EQ:
        return REL_EQ
    return REL_NONE
# pure-end


def rewrite_comparison(node: Compare) -> Node:
    # pre-conditions-start
    Requires(Acc(node.op, 1 / 2))
    Requires(Acc(node.left, 1 / 2) and Acc(node.right, 1 / 2))
    Requires(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(node.op, 1 / 2))
    Ensures(Acc(node.left, 1 / 2) and Acc(node.right, 1 / 2))
    Ensures(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    Ensures(Acc(Result().is_call) and Acc(Result().rel_class) and
            Acc(Result().evaluate) and Acc(Result().left) and
            Acc(Result().right) and Acc(Result().op))
    # A relational comparison is converted to a symbolic-comparison call ...
    Ensures(Result().is_call == is_relational(node.op))
    # ... whose constructor matches the operator under the prescribed bijection.
    Ensures(Result().rel_class == rel_class_of(node.op))
    # The non-evaluating flag is set: a produced symbolic-comparison call never
    # evaluates its operands.
    Ensures(Result().evaluate == False)
    # ... applied to the two visited operands, in original left/right order.
    # The operand pin is UNCONDITIONAL: a produced symbolic-comparison call
    # carries the two operands in source order, and an unchanged non-relational
    # comparison keeps its own operands (the real rewrite returns the node
    # itself, operands included). Leaving the operands free on either branch
    # would admit an implementation that drops or reorders them.
    Ensures(Result().left is node.left and Result().right is node.right)
    # The operator code is preserved UNCONDITIONALLY: an unchanged
    # non-relational comparison keeps its operator, and a produced call records
    # the operator it was built from. This pins every field of the result as a
    # function of the input, leaving no unconstrained channel.
    Ensures(Result().op == node.op)
    # post-conditions-end
    # impl-start
    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY — sympy__sympy-24661 nagini G-EQ (refinement fidelity, focus on A-legs + model<->patch correspondence). Verdict SOUND.

SBU_BENCHMARK_DIR=benchmark-verified; python python;

SPEC SHAPE: rewrite_comparison's postconditions pin EVERY output field of the result Node as a function of the input, UNCONDITIONALLY: is_call==is_relational(op); rel_class==rel_class_of(op); evaluate==False; Result().left is node.left AND Result().right is node.right; Result().op==node.op. There is no free/unconstrained channel on either branch, so any verifying impl must reproduce gold-equivalent field values.

ATTACKS (7 distinct wrong impls; each copied model.py editing ONLY the impl region; same-spec confirmed byte-identical for all 7 + positive control). Command form: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24661 <path>` (verify runs concurrent, <=3 JVM+Z3 jobs at a time).
- atk_1.py PREPATCH bug (never convert; is_call always False): NOT-A-COUNTEREXAMPLE (verification failed) => prepatch reproduced, spec senses the change (G-DIFF).
- atk_2.py swapped bijection (OP_LT->REL_GT, OP_GT->REL_LT): NOT-A-COUNTEREXAMPLE (verification failed; fails rel_class==rel_class_of).
- atk_3.py swapped operand order (left/right reversed): NOT-A-COUNTEREXAMPLE (verification failed; fails Result().left is node.left).
- atk_4.py evaluate=True on the produced call: NOT-A-COUNTEREXAMPLE (verification failed; fails evaluate==False).
- atk_5.py partial-domain/boundary (convert all relational EXCEPT OP_EQ): NOT-A-COUNTEREXAMPLE (verification failed; fails is_call==is_relational on OP_EQ).
- atk_6.py control-flow-effect (always Node(True,...) even for non-relational, rel_class=rel_class_of=REL_NONE): NOT-A-COUNTEREXAMPLE (verification failed; fails is_call==is_relational on non-relational op).
- atk_7.py ungrounded-oracle ECHO (rel_call=rel_class_of(op); conv = rel_call!=REL_NONE; Node(conv,...) each branch): CANDIDATE-COUNTEREXAMPLE — shares spec AND verifies (19.2s).

MANDATORY RESOLVE ON THE CANDIDATE: atk_7 is behaviorally identical to gold (conv == is_relational; produces the same Node field values as the model on both branches). Materialized its faithful refined patch (atk_7_patch.diff, a .get()-based reformulation of the gold visit_Compare — same behavior) and RAN it through the official harness via swebench_unified.harness.run_resolve:
  ATK7: resolved=True completed=True note=resolved
  GOLD baseline: resolved=True completed=True note=resolved
The verifying wrong impl's faithful patch RESOLVES => it is a gold-equivalent echo, NOT a weakness (per the 2026-08-06 echo policy: a same-spec verifying attack fails the gate only if its refined patch does NOT resolve). No BROKEN condition triggered.

POSITIVE CONTROL: positive_control.py = verbatim model.py; `adversary verify` => VERIFIED in 21.5s.

A-LEG / deep-model AUDIT (refinement.md focus): NO consumed @ContractOnly axiom (axioms region empty by design). Sole A-leg is B1 A-REFERENCE: the model's rel_class_of/is_relational + produced-node shape == the real post-patch EvaluateFalseTransformer.visit_Compare. Re-ran G-AX FRESH (gates.ax.run, ax_apply_gold=True, in the instance Docker image) => status=pass: 'matches the model on all 6 relational operators (Lt/Le/Gt/Ge/Ne/Eq, evaluate=False, left/right order) and 4 non-relational operators (unchanged).' Correspondence to the real callee holds.

REFINEMENT.MD LEG AUDIT: rows A1-A6 are all R (type refinement: ast.Compare<->Compare, dict<->rel_class_of/is_relational, class-name str<->int constructor code, ast.Call<->Node) or I (row A4/C: self.visit(operand) identity on integer-literal operands, the F2P test_issue_24288 domain, encoded via opaque Expr carrier). Section C's operand self.visit is a transparently-disclosed I-step scoped to the tested domain (non-leaf operands would recurse, but the conversion property is independent of operand recursion). Section D: no kind-3 (unexpressible-changed-op) step — the genuinely-changed op is deeply modeled, not hidden behind an axiom. All legs classify R / I / A-reference; no A-consumed, no kind-3. Correspondence sound.

CONCLUSION: 7 attacks run (>=5 distinct wrong-impl classes: prepatch, wrong-bijection, operand-reorder, wrong-flag, partial-domain/boundary, control-flow-effect, ungrounded-oracle echo). 6 rejected by the verifier; the 1 CANDIDATE (echo) had its faithful patch executed through the official harness and RESOLVED. Positive control verifies; A-reference re-validated by fresh G-AX. No verifying wrong impl whose faithful patch fails to resolve exists. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Machine checks: model.py verifies under Nagini (14.9s); axiom_check.py passes against the REAL post-patch EvaluateFalseTransformer.visit_Compare in the worktree at base_commit a36caf5c (all 6 relational ops -> correct constructor, evaluate=False, left/right order; 4 non-relational ops unchanged). Gold patch.diff matches the modeled function. Empirically confirmed on the F2P domain (integer-literal operands 1<2..1==2): out.args[0] is node.left and out.args[1] is node.comparators[0] are BOTH True for all six operators, so operand identity genuinely holds where resolution requires it. Postconditions is_call==is_relational(op), rel_class==rel_class_of(op), evaluate==False all match the real callee exactly. The unconditional operand-identity pin is stronger than the real callee in general (non-leaf operands rewrite), but this is a disclosed I-step on the opaque Expr carrier, valid on the resolution domain, and the gold patch satisfies the spec under this refinement (so the spec is not too strong to reject gold). Result().op==node.op is a harmless bookkeeping pin (real ast.Call has no .op field). No consumed axiom; the A-reference is machine-validated == the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view is a purely behavioral specification. Mechanical G-LEAK screen passes clean (no hard failures, no warnings): no diff markers, no gold changed lines, no patched-file path, no narration words, no spec-view identifier colliding with the gold's distinctive symbols. The gold edit lives in sympy/parsing/sympy_parser.py as EvaluateFalseTransformer.visit_Compare + a relational_operators dict — NONE of these appear in the spec view, which uses generic modeling names (rewrite_comparison, Compare, Node, Expr, is_relational, rel_class_of, OP_*/REL_* codes). The spec does NOT reveal the edit's location, the visitor/NodeTransformer mechanism, or the dict-lookup implementation strategy.

Assessed the one candidate concern: the spec enumerates the full six-operator bijection (Lt/Le/Gt/Ge/Ne/Eq) while the public problem_statement literally shows only `Lt(1,2,evaluate=False)`. This is NOT leakage beyond problem_statement: (a) the issue title already scopes the defect to "relationals" (plural) and links related issues #22305/#22098; (b) Lt/Le/Gt/Ge/Ne/Eq are public SymPy relational constructor names any solver knows; (c) the enumeration specifies the DESIRED BEHAVIOR (what a correct fix must achieve) rather than localizing the gold edit. Stating target behavior derivable from the public issue is the spec view's legitimate function, not gold-edit disclosure. A solver seeing this spec still must independently discover where and how to implement the fix in the real repo.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
