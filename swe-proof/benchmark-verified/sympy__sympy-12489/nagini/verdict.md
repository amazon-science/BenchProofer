# P2 adversarial audit — sympy__sympy-12489

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -78,7 +75,7 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = Arrangement(kind, array)  # type: Arrangement
+    result = Arrangement(0, array)  # type: Arrangement
     return result
     # impl-end
 
@@ -91,7 +88,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -91,7 +88,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
@@ -106,6 +102,6 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = make(self.kind, product)  # type: Arrangement
+    result = make(0, product)  # type: Arrangement
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -91,7 +88,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
@@ -106,6 +102,6 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = make(self.kind, product)  # type: Arrangement
+    result = make(other.kind, product)  # type: Arrangement
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -78,7 +75,7 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = Arrangement(kind, array)  # type: Arrangement
+    result = Arrangement(kind + 1, array)  # type: Arrangement
     return result
     # impl-end
 
@@ -91,7 +88,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -78,7 +75,17 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = Arrangement(kind, array)  # type: Arrangement
+    fresh = []  # type: List[int]
+    i = 0
+    n = len(array)  # type: int
+    while i < n:
+        Invariant(0 <= i and i <= n)
+        Invariant(Acc(list_pred(array), 1 / 2))
+        Invariant(n == len(array))
+        Invariant(Acc(list_pred(fresh)))
+        fresh.append(array[i])
+        i += 1
+    result = Arrangement(kind, fresh)  # type: Arrangement
     return result
     # impl-end
 
@@ -91,7 +98,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -91,7 +88,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
@@ -106,6 +102,6 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = make(self.kind, product)  # type: Arrangement
+    result = Arrangement(self.kind, other.array)  # type: Arrangement
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,13 +35,11 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Arrangement:
     def __init__(self, kind: int, array: List[int]) -> None:
         Requires(Acc(list_pred(array), 1 / 2))
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
         Ensures(Acc(self.array) and self.array is array)     # type: ignore
         Ensures(Acc(list_pred(array), 1 / 2))
@@ -66,7 +64,6 @@
     identifier and a finished array of points."""
     # pre-conditions-start
     Requires(Acc(list_pred(array), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().kind) and Acc(Result().array))
@@ -91,7 +88,6 @@
     Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
     Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
     Requires(Acc(list_pred(product), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
@@ -106,6 +102,7 @@
     Ensures(Acc(list_pred(Result().array), 1 / 2))
     # post-conditions-end
     # impl-start
-    result = make(self.kind, product)  # type: Arrangement
-    return result
+    if self.kind == other.kind:
+        return make(self.kind, product)
+    return make(0, product)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-12489.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite arrangement value is described by two observable attributes: the
  KIND of value it is (its runtime construction family — the plain family, or
  any specialised family derived from it) and its CONTENT (the array of points
  0..n-1 in their rearranged order).

  When such a value is produced by the family's own internal builder — the
  routine other operations funnel through to mint a fresh value from a finished
  array of points — the freshly-minted value must belong to the SAME family the
  builder was reached through, not to a single privileged family. Concretely:

    (1) The internal builder, invoked on a family identifier and a finished
        array, yields a value whose family identifier is exactly the one it was
        invoked with, and whose content is exactly that array. It does not
        collapse every result onto one privileged family.

    (2) A binary combination of two values, evaluated as a method of the
        left-hand value, produces its result through the left-hand value's own
        family, so the combination of two values of a specialised family is
        again a value of that specialised family (and its content is the
        combined array). The combination must reach the builder THROUGH the
        left operand's family, not through one privileged family reference.

A value is modelled as a minimal class carrying only the two touched
attributes: ``kind`` (the family identifier, an int; a distinguished base
family is 0, any other int is a derived family) and ``array`` (the array form
as a ``List[int]``). The array content of the combination is the unchanged
numeric product and is carried through directly; the property under
specification is the propagation of the family identifier.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class Arrangement:
    def __init__(self, kind: int, array: List[int]) -> None:
        Requires(Acc(list_pred(array), 1 / 2))
        Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
        Ensures(Acc(self.array) and self.array is array)     # type: ignore
        Ensures(Acc(list_pred(array), 1 / 2))
        self.kind = kind
        self.array = array

# axioms-start
# (none) — the family-propagating construction is modelled deeply; no callee is
# axiomatized. The unchanged numeric product carried by the combination is an
# R-refinement (refinement.md), not a consumed axiom.
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def make(kind: int, array: List[int]) -> Arrangement:
    """The family's internal builder: mint a fresh value from a family
    identifier and a finished array of points."""
    # pre-conditions-start
    Requires(Acc(list_pred(array), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().kind) and Acc(Result().array))
    # (1) The minted value belongs to exactly the family the builder was reached
    # through, and carries exactly the supplied array — every family identifier
    # is honoured, not collapsed onto one privileged family.
    Ensures(Result().kind == kind)
    Ensures(Result().array is array)
    Ensures(Acc(list_pred(Result().array), 1 / 2))
    # post-conditions-end
    # impl-start
    result = Arrangement(kind, array)  # type: Arrangement
    return result
    # impl-end

def combine(self: Arrangement, other: Arrangement,
            product: List[int]) -> Arrangement:
    """Binary combination of two values as a method of ``self``: the combined
    content ``product`` is minted as a value of ``self``'s own family."""
    # pre-conditions-start
    Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
    Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
    Requires(Acc(list_pred(product), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
    Ensures(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().array))
    # (2) The combination is produced through the LEFT operand's family, so its
    # family identifier is exactly ``self``'s — a combination of two values of a
    # derived family is again a value of that derived family.
    Ensures(Result().kind == self.kind)
    # Its content is exactly the combined array (the unchanged numeric product).
    Ensures(Result().array is product)
    Ensures(Acc(list_pred(Result().array), 1 / 2))
    # post-conditions-end
    # impl-start
    result = make(self.kind, product)  # type: Arrangement
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for sympy__sympy-12489 (nagini). All work Adversary CLI run with the MAIN env python python (the nagini-verifier env lacks swebench_unified) and SBU_BENCHMARK_DIR=benchmark-verified, from project root.

SPEC SHAPE: two impl regions (make, combine). Postconditions pin BOTH observables exactly: make -> Result().kind == kind AND Result().array is array (reference identity); combine -> Result().kind == self.kind AND Result().array is product. Only the two impl regions were edited in every attack; axioms(none)/@Pure(none)/Requires/Ensures left byte-identical (same-spec exit 0 confirmed for all 7 + pos_control).

7 DISTINCT wrong impls, each run through `python -m swebench_unified.adversary weakness nagini sympy__sympy-12489 <atk>`; ALL returned exit 2 (NOT-A-COUNTEREXAMPLE: shares spec but does NOT verify). Direct nagini_verify.sh confirmed each failure is a genuine semantic postcondition rejection (not translation/infra error): atk_1 partial-domain / PREPATCH BUG site1 (make mints onto fixed base family 0): rejected 'Postcondition of make ... Result().kind == kind might not hold' (reproduces model_prepatch.py:73).

PREPATCH REPRODUCED. atk_2 partial-domain / PREPATCH BUG site2 (combine reaches builder via fixed family 0): rejected 'Result().kind == self.kind' (reproduces model_prepatch_2.py:99). atk_3 wrong-operand (combine uses other.kind): rejected 'Result().kind == self.kind' at combine:99. atk_4 off-by-one family (make uses kind+1): rejected 'Result().kind == kind' at make:73. atk_5 array-identity break (make builds a fresh list with identical content, correct kind, well-formed loop invariants): rejected precisely on 'Result().array is array' at make:74 -- proves the reference-identity postcondition has teeth. atk_6 ungrounded-oracle echo (combine returns Arrangement(self.kind, other.array) instead of product): rejected (insufficient permission to list_pred(array); the echo abandons the product carrier). atk_7 control-flow-effect / F2P-breaking (combine propagates self.kind only when self.kind==other.kind, else collapses to base 0 -- exactly the type(p*q) mixed-pairing bug): rejected 'Result().kind == self.kind' at combine:99. (First draft had a double `result` declaration causing a TRANSLATION error, which is not a valid semantic test; rewritten to early-return form and re-verified -> genuine postcondition rejection.)

NO CANDIDATE emerged (no same-spec impl both shares the spec AND verifies), so there is no verifying-wrong-impl whose faithful refined patch needed a run_resolve execution; patches={} accordingly. Positive control (exact gold impl = model.py copy) VERIFIES: nagini_verify.sh exit 0, 'Verification successful' in 9.39s.

REFINEMENT.MD AUDIT (A-legs): every leg is R / A-reference / I -- NO kind-3 (unexpressible-changed-op), and NO consumed axiom (no @ContractOnly -> no axiom-soundness trust point). Two A-reference legs, both validated by G-AX/axiom_check.py against the REAL patched callees: A2 make ~ Permutation._af_new via Basic.__new__(cls,perm): axiom_check asserts type(Cls._af_new(perm)) is Cls + array preserved, exhaustive sizes 0..5 + 3000 fuzz; corresponds to model postcond Result().kind==kind. B2 combine ~ Permutation.__mul__ via self._af_new: axiom_check asserts type(left*right) is type(left) over all family pairings + F2P witnesses type(p*q) is CustomPermutation / type(q*p) is Permutation; corresponds to Result().kind==self.kind. axiom_check.py is documented discriminating (PASSES on patched source, FAILS on prepatch 'builder lost family'). Model->patch correspondence faithful; kind<->type(obj) and array<->_array_form R-refinements hold. patch.diff is gold verbatim (G-RESOLVE oracle).

VERDICT: SOUND -- >=5 (7) distinct same-spec attacks (incl. both prepatch bugs and a clean identity break) all run through the official weakness harness; none verifies, so verify=>correct is not broken. No resolve run was required because no attack was a CANDIDATE.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-12489.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite arrangement value is described by two observable attributes: the
  KIND of value it is (its runtime construction family — the plain family, or
  any specialised family derived from it) and its CONTENT (the array of points
  0..n-1 in their rearranged order).

  When such a value is produced by the family's own internal builder — the
  routine other operations funnel through to mint a fresh value from a finished
  array of points — the freshly-minted value must belong to the SAME family the
  builder was reached through, not to a single privileged family. Concretely:

    (1) The internal builder, invoked on a family identifier and a finished
        array, yields a value whose family identifier is exactly the one it was
        invoked with, and whose content is exactly that array. It does not
        collapse every result onto one privileged family.

    (2) A binary combination of two values, evaluated as a method of the
        left-hand value, produces its result through the left-hand value's own
        family, so the combination of two values of a specialised family is
        again a value of that specialised family (and its content is the
        combined array). The combination must reach the builder THROUGH the
        left operand's family, not through one privileged family reference.

A value is modelled as a minimal class carrying only the two touched
attributes: ``kind`` (the family identifier, an int; a distinguished base
family is 0, any other int is a derived family) and ``array`` (the array form
as a ``List[int]``). The array content of the combination is the unchanged
numeric product and is carried through directly; the property under
specification is the propagation of the family identifier.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class Arrangement:
    def __init__(self, kind: int, array: List[int]) -> None:
        Requires(Acc(list_pred(array), 1 / 2))
        Ensures(Acc(self.kind) and self.kind == kind)        # type: ignore
        Ensures(Acc(self.array) and self.array is array)     # type: ignore
        Ensures(Acc(list_pred(array), 1 / 2))
        self.kind = kind
        self.array = array

# axioms-start
# (none) — the family-propagating construction is modelled deeply; no callee is
# axiomatized. The unchanged numeric product carried by the combination is an
# R-refinement (refinement.md), not a consumed axiom.
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def make(kind: int, array: List[int]) -> Arrangement:
    """The family's internal builder: mint a fresh value from a family
    identifier and a finished array of points."""
    # pre-conditions-start
    Requires(Acc(list_pred(array), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().kind) and Acc(Result().array))
    # (1) The minted value belongs to exactly the family the builder was reached
    # through, and carries exactly the supplied array — every family identifier
    # is honoured, not collapsed onto one privileged family.
    Ensures(Result().kind == kind)
    Ensures(Result().array is array)
    Ensures(Acc(list_pred(Result().array), 1 / 2))
    # post-conditions-end
    # impl-start
    result = Arrangement(kind, array)  # type: Arrangement
    return result
    # impl-end

def combine(self: Arrangement, other: Arrangement,
            product: List[int]) -> Arrangement:
    """Binary combination of two values as a method of ``self``: the combined
    content ``product`` is minted as a value of ``self``'s own family."""
    # pre-conditions-start
    Requires(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
    Requires(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
    Requires(Acc(list_pred(product), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.kind, 1 / 2) and Acc(self.array, 1 / 2))
    Ensures(Acc(other.kind, 1 / 2) and Acc(other.array, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().array))
    # (2) The combination is produced through the LEFT operand's family, so its
    # family identifier is exactly ``self``'s — a combination of two values of a
    # derived family is again a value of that derived family.
    Ensures(Result().kind == self.kind)
    # Its content is exactly the combined array (the unchanged numeric product).
    Ensures(Result().array is product)
    Ensures(Acc(list_pred(Result().array), 1 / 2))
    # post-conditions-end
    # impl-start
    result = make(self.kind, product)  # type: Arrangement
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for sympy__sympy-12489 (nagini). All work Adversary CLI run with the MAIN env python python (the nagini-verifier env lacks swebench_unified) and SBU_BENCHMARK_DIR=benchmark-verified, from project root.

SPEC SHAPE: two impl regions (make, combine). Postconditions pin BOTH observables exactly: make -> Result().kind == kind AND Result().array is array (reference identity); combine -> Result().kind == self.kind AND Result().array is product. Only the two impl regions were edited in every attack; axioms(none)/@Pure(none)/Requires/Ensures left byte-identical (same-spec exit 0 confirmed for all 7 + pos_control).

7 DISTINCT wrong impls, each run through `python -m swebench_unified.adversary weakness nagini sympy__sympy-12489 <atk>`; ALL returned exit 2 (NOT-A-COUNTEREXAMPLE: shares spec but does NOT verify). Direct nagini_verify.sh confirmed each failure is a genuine semantic postcondition rejection (not translation/infra error): atk_1 partial-domain / PREPATCH BUG site1 (make mints onto fixed base family 0): rejected 'Postcondition of make ... Result().kind == kind might not hold' (reproduces model_prepatch.py:73).

PREPATCH REPRODUCED. atk_2 partial-domain / PREPATCH BUG site2 (combine reaches builder via fixed family 0): rejected 'Result().kind == self.kind' (reproduces model_prepatch_2.py:99). atk_3 wrong-operand (combine uses other.kind): rejected 'Result().kind == self.kind' at combine:99. atk_4 off-by-one family (make uses kind+1): rejected 'Result().kind == kind' at make:73. atk_5 array-identity break (make builds a fresh list with identical content, correct kind, well-formed loop invariants): rejected precisely on 'Result().array is array' at make:74 -- proves the reference-identity postcondition has teeth. atk_6 ungrounded-oracle echo (combine returns Arrangement(self.kind, other.array) instead of product): rejected (insufficient permission to list_pred(array); the echo abandons the product carrier). atk_7 control-flow-effect / F2P-breaking (combine propagates self.kind only when self.kind==other.kind, else collapses to base 0 -- exactly the type(p*q) mixed-pairing bug): rejected 'Result().kind == self.kind' at combine:99. (First draft had a double `result` declaration causing a TRANSLATION error, which is not a valid semantic test; rewritten to early-return form and re-verified -> genuine postcondition rejection.)

NO CANDIDATE emerged (no same-spec impl both shares the spec AND verifies), so there is no verifying-wrong-impl whose faithful refined patch needed a run_resolve execution; patches={} accordingly. Positive control (exact gold impl = model.py copy) VERIFIES: nagini_verify.sh exit 0, 'Verification successful' in 9.39s.

REFINEMENT.MD AUDIT (A-legs): every leg is R / A-reference / I -- NO kind-3 (unexpressible-changed-op), and NO consumed axiom (no @ContractOnly -> no axiom-soundness trust point). Two A-reference legs, both validated by G-AX/axiom_check.py against the REAL patched callees: A2 make ~ Permutation._af_new via Basic.__new__(cls,perm): axiom_check asserts type(Cls._af_new(perm)) is Cls + array preserved, exhaustive sizes 0..5 + 3000 fuzz; corresponds to model postcond Result().kind==kind. B2 combine ~ Permutation.__mul__ via self._af_new: axiom_check asserts type(left*right) is type(left) over all family pairings + F2P witnesses type(p*q) is CustomPermutation / type(q*p) is Permutation; corresponds to Result().kind==self.kind. axiom_check.py is documented discriminating (PASSES on patched source, FAILS on prepatch 'builder lost family'). Model->patch correspondence faithful; kind<->type(obj) and array<->_array_form R-refinements hold. patch.diff is gold verbatim (G-RESOLVE oracle).

VERDICT: SOUND -- >=5 (7) distinct same-spec attacks (incl. both prepatch bugs and a clean identity break) all run through the official weakness harness; none verifies, so verify=>correct is not broken. No resolve run was required because no attack was a CANDIDATE.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical (probed the bundle's own model.py, which verifies in Nagini, 9.85s). Faithfulness checked empirically against the gold-patched real callees in a base_commit worktree (base = aa9780761a; patched source). make ↔ Permutation._af_new: model postconditions Result().kind==kind and Result().array is array exactly match the real @classmethod _af_new (type(cls._af_new(perm)) is cls; p._array_form = perm sets list identity). combine ↔ Permutation.__mul__: Result().kind==self.kind and Result().array is product match type(self*other) is type(self) and _array_form is the passed perm list. Adversarial fuzz of 40,000 randomized inputs across families {Permutation, Sub(overriding __call__/__eq__/__hash__), Sub2} — 20k _af_new calls (type + array-identity) and 20k __mul__ calls (left-family type + array content vs [b[i] for i in a]+b[len(a):]) — found NO divergence between the modeled functions and the real callees. Preconditions impose only Acc ownership permissions, no artificial input narrowing, so the spec is not too strong. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py) is byte-identical spec region confirmed and the mechanical leak screen passes clean (no diff markers, no verbatim gold-patch lines >=8 normalized chars, no patched file/module path, no narration words, no spec-view identifier or comment embedding any patched repo symbol — af_new/_af_new, __mul__, mul_inv, unrank_lex, josephus, etc. all absent). Semantic judgment: the spec view is a STRICT ABSTRACTION of what the public problem_statement already discloses. The issue text itself spells out the entire gold edit: it says object creation goes through Permutation._af_new -> Basic.__new__(Perm, perm) with Perm a fixed reference to Permutation, that this breaks subclassing, and that 'the elegant solution [is to] use classmethods where appropriate (__new__ is one) and use the mandatory reference to the class (the first argument of a classmethod) the method is called on for instance creation.' model.py reveals nothing beyond this — indeed less: it drops every concrete repo symbol and speaks only in generic terms ('family identifier', 'internal builder', 'binary combination evaluated as a method of the left-hand value', 'the SAME family the builder was reached through, not a single privileged family'). The abstract Arrangement/kind/array/make/combine vocabulary does not localize the edit any more precisely than the publicly-disclosed 'use cls instead of the fixed Permutation reference'. No leakage of the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.