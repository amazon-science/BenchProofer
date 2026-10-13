# P2 adversarial audit — sympy__sympy-13372

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.py`, `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,25 +99,15 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
     reprec = None  # type: Optional[int]
     if re_kind == 0:
         reprec = None
     elif re_kind == 1:
         reprec = prec
-    else:
-        raise EvalfDeferred()
-    # Classify the imaginary part identically.
     imprec = None  # type: Optional[int]
     if im_kind == 0:
         imprec = None
     elif im_kind == 1:
         imprec = prec
-    else:
-        raise EvalfDeferred()
-    Assert(reprec is part_precision(re_kind, prec))
-    Assert(imprec is part_precision(im_kind, prec))
     return EvalfResult(reprec, imprec)
     # impl-end
```

Attack 2 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,9 +99,6 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
     reprec = None  # type: Optional[int]
     if re_kind == 0:
         reprec = None
@@ -115,15 +106,10 @@
         reprec = prec
     else:
         raise EvalfDeferred()
-    # Classify the imaginary part identically.
     imprec = None  # type: Optional[int]
     if im_kind == 0:
         imprec = None
-    elif im_kind == 1:
+    else:
         imprec = prec
-    else:
-        raise EvalfDeferred()
-    Assert(reprec is part_precision(re_kind, prec))
-    Assert(imprec is part_precision(im_kind, prec))
     return EvalfResult(reprec, imprec)
     # impl-end
```

Attack 3 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,17 +99,13 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
     reprec = None  # type: Optional[int]
     if re_kind == 0:
+        reprec = prec
+    elif re_kind == 1:
         reprec = None
-    elif re_kind == 1:
-        reprec = prec
     else:
         raise EvalfDeferred()
-    # Classify the imaginary part identically.
     imprec = None  # type: Optional[int]
     if im_kind == 0:
         imprec = None
@@ -123,7 +113,5 @@
         imprec = prec
     else:
         raise EvalfDeferred()
-    Assert(reprec is part_precision(re_kind, prec))
-    Assert(imprec is part_precision(im_kind, prec))
     return EvalfResult(reprec, imprec)
     # impl-end
```

Attack 4 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,25 +99,5 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
-    reprec = None  # type: Optional[int]
-    if re_kind == 0:
-        reprec = None
-    elif re_kind == 1:
-        reprec = prec
-    else:
-        raise EvalfDeferred()
-    # Classify the imaginary part identically.
-    imprec = None  # type: Optional[int]
-    if im_kind == 0:
-        imprec = None
-    elif im_kind == 1:
-        imprec = prec
-    else:
-        raise EvalfDeferred()
-    Assert(reprec is part_precision(re_kind, prec))
-    Assert(imprec is part_precision(im_kind, prec))
-    return EvalfResult(reprec, imprec)
+    raise EvalfDeferred()
     # impl-end
```

Attack 5 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,25 +99,11 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
-    reprec = None  # type: Optional[int]
+    reprec = prec  # type: Optional[int]
     if re_kind == 0:
         reprec = None
-    elif re_kind == 1:
-        reprec = prec
-    else:
-        raise EvalfDeferred()
-    # Classify the imaginary part identically.
-    imprec = None  # type: Optional[int]
+    imprec = prec  # type: Optional[int]
     if im_kind == 0:
         imprec = None
-    elif im_kind == 1:
-        imprec = prec
-    else:
-        raise EvalfDeferred()
-    Assert(reprec is part_precision(re_kind, prec))
-    Assert(imprec is part_precision(im_kind, prec))
     return EvalfResult(reprec, imprec)
     # impl-end
```

Attack 6 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,24 +99,10 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
-    reprec = None  # type: Optional[int]
-    if re_kind == 0:
-        reprec = None
-    elif re_kind == 1:
-        reprec = prec
-    else:
+    if re_kind == 2 or im_kind == 2:
         raise EvalfDeferred()
-    # Classify the imaginary part identically.
-    imprec = None  # type: Optional[int]
-    if im_kind == 0:
-        imprec = None
-    elif im_kind == 1:
-        imprec = prec
-    else:
-        raise EvalfDeferred()
+    reprec = prec if re_kind == 1 else None  # type: Optional[int]
+    imprec = prec if im_kind == 1 else None  # type: Optional[int]
     Assert(reprec is part_precision(re_kind, prec))
     Assert(imprec is part_precision(im_kind, prec))
     return EvalfResult(reprec, imprec)
```

Attack 7 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,9 +99,13 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
+    imprec = None  # type: Optional[int]
+    if im_kind == 0:
+        imprec = None
+    elif im_kind == 1:
+        imprec = prec
+    else:
+        raise EvalfDeferred()
     reprec = None  # type: Optional[int]
     if re_kind == 0:
         reprec = None
@@ -115,14 +113,6 @@
         reprec = prec
     else:
         raise EvalfDeferred()
-    # Classify the imaginary part identically.
-    imprec = None  # type: Optional[int]
-    if im_kind == 0:
-        imprec = None
-    elif im_kind == 1:
-        imprec = prec
-    else:
-        raise EvalfDeferred()
     Assert(reprec is part_precision(re_kind, prec))
     Assert(imprec is part_precision(im_kind, prec))
     return EvalfResult(reprec, imprec)
```

Attack 8 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EvalfDeferred(Exception):
@@ -54,10 +53,6 @@
     defined."""
 
     def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
-        # Terminates outright (two field writes, no loop, no call). Level 1 sits
-        # strictly below every caller level so the caller can hand its
-        # obligation down without leaking it.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
         Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
         self.reprec = reprec
@@ -89,7 +84,6 @@
     # Each part is classified into exactly one of the three cases.
     Requires(0 <= re_kind and re_kind <= 2)
     Requires(0 <= im_kind and im_kind <= 2)
-    Requires(MustTerminate(6 - re_kind))
     # pre-conditions-end
     # post-conditions-start
     # A result is assembled (returns normally) only when BOTH parts are
@@ -105,25 +99,11 @@
     Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
     # post-conditions-end
     # impl-start
-    # Classify the real part. The precision component is set only in the
-    # exact-zero and numeric cases; the OTHER case defers before any result is
-    # assembled (so no result is ever built around a missing component).
-    reprec = None  # type: Optional[int]
-    if re_kind == 0:
-        reprec = None
-    elif re_kind == 1:
-        reprec = prec
-    else:
+    if re_kind == 2:
         raise EvalfDeferred()
-    # Classify the imaginary part identically.
-    imprec = None  # type: Optional[int]
-    if im_kind == 0:
-        imprec = None
-    elif im_kind == 1:
-        imprec = prec
-    else:
+    if im_kind == 2:
         raise EvalfDeferred()
-    Assert(reprec is part_precision(re_kind, prec))
-    Assert(imprec is part_precision(im_kind, prec))
+    reprec = part_precision(re_kind, prec)  # type: Optional[int]
+    imprec = part_precision(im_kind, prec)  # type: Optional[int]
     return EvalfResult(reprec, imprec)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-13372.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric evaluator splits an expression into its real and imaginary parts
  and assembles a result that pairs each part with a PRECISION component
  describing how that part was evaluated. Each part independently falls into
  exactly one of three cases:

    * EXACT-ZERO  — the part is the exact zero. Its precision component is
      ABSENT (there is no working precision attached to an exact zero).

    * NUMERIC     — the part is a concrete number. Its precision component is
      the supplied working precision.

    * OTHER       — the part is neither an exact zero nor a concrete number
      (it is still symbolic). There is NO precision component defined for such
      a part.

  The behaviour pinned here: a result is assembled — pairing each part with a
  precision component — ONLY when BOTH parts are exact-zero or numeric, in
  which case each precision component is ABSENT for an exact-zero part and the
  working precision for a numeric part. If EITHER part is the OTHER case, no
  result can be assembled (there is no precision component for that part); the
  evaluation must DEFER instead of assembling a result with a missing precision
  component. Deferral lets the caller fall back to an alternative evaluation;
  assembling a result around a missing precision component is never permitted.

Each part's case is modelled as an integer tag (0 = exact-zero, 1 = numeric,
2 = other). The assembled result is a minimal object carrying only the two
touched precision components, each an `Optional[int]` (absent = None). The
deferral is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class EvalfDeferred(Exception):
    """Signals that a result cannot be assembled because some part is neither
    an exact zero nor a concrete number, so no precision component is defined
    for it. Stands in for the `NotImplementedError` the desired behaviour
    raises to defer to an alternative evaluation; a builtin exception in an
    `Exsures` crashes the Nagini translator (mapping.md §2)."""


class EvalfResult:
    """The assembled result: the two touched precision components. Each is the
    working precision for a numeric part, or absent (None) for an exact-zero
    part. A result is assembled only when both precision components are
    defined."""

    def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
        Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
        Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
        self.reprec = reprec
        self.imprec = imprec


# axioms-start
# (no axioms: the precision-component selection per part is concrete integer
# control flow, modelled directly — no unchanged opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def part_precision(kind: int, prec: int) -> Optional[int]:
    """The precision component for one part: absent (None) for an exact-zero
    part (kind 0), the working precision for a numeric part (kind 1). Defined
    only for the two cases that yield a precision component; the OTHER case
    (kind 2) has no precision component and is excluded by the precondition."""
    Requires(kind == 0 or kind == 1)
    if kind == 0:
        return None
    return prec
# pure-end


def assemble_evalf_result(re_kind: int, im_kind: int, prec: int) -> EvalfResult:
    # pre-conditions-start
    # Each part is classified into exactly one of the three cases.
    Requires(0 <= re_kind and re_kind <= 2)
    Requires(0 <= im_kind and im_kind <= 2)
    # pre-conditions-end
    # post-conditions-start
    # A result is assembled (returns normally) only when BOTH parts are
    # exact-zero or numeric — never when either part is the OTHER case.
    Ensures(re_kind != 2 and im_kind != 2)
    Ensures(Acc(Result().reprec) and Acc(Result().imprec))
    # Each assembled precision component is exactly the one its part's case
    # demands: absent for exact-zero, the working precision for numeric.
    Ensures(Result().reprec is part_precision(re_kind, prec))
    Ensures(Result().imprec is part_precision(im_kind, prec))
    # The evaluation DEFERS exactly when some part is the OTHER case: no result
    # can be assembled because a precision component would be missing.
    Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
    # post-conditions-end
    # impl-start
    # Classify the real part. The precision component is set only in the
    # exact-zero and numeric cases; the OTHER case defers before any result is
    # assembled (so no result is ever built around a missing component).
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    else:
        raise EvalfDeferred()
    # Classify the imaginary part identically.
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    else:
        raise EvalfDeferred()
    Assert(reprec is part_precision(re_kind, prec))
    Assert(imprec is part_precision(im_kind, prec))
    return EvalfResult(reprec, imprec)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Editable region = the impl body of assemble_evalf_result (model.py lines 102-122); spec regions (axioms/@Pure/Requires/Ensures/Exsures) held byte-identical in every attack (adversary same-spec: SAME for all 8 + pos_control). The postconditions fully pin the observable as an exact deterministic function of the case tags: Ensures(re_kind!=2 and im_kind!=2), Ensures(Result().reprec is part_precision(re_kind,prec)), Ensures(Result().imprec is part_precision(im_kind,prec)), Exsures(EvalfDeferred, re_kind==2 or im_kind==2). So the spec is functionally complete: any wrong function is rejected, and any verifying impl computes the gold observable.

WRONG-IMPL ATTACKS (must fail verify), cmd `python -m swebench_unified.adversary weakness nagini sympy__sympy-13372 <path>`:
- atk_prepatch.py (drop both else:raise -> reads unset precision local; the prepatch bug): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch bug REPRODUCED (model_prepatch's failure mode: postcondition unprovable on an OTHER part).
- atk_1.py (partial-domain: im OTHER falls through with imprec=prec, no defer): NOT-A-COUNTEREXAMPLE, fails verify.
- atk_2.py (boundary/swap: reprec = prec for exact-zero, None for numeric): NOT-A-COUNTEREXAMPLE, fails verify.
- atk_3.py (control-flow-effect: unconditionally raise EvalfDeferred): NOT-A-COUNTEREXAMPLE, fails verify (Exsures violated when neither part is OTHER).
- atk_4.py (never-defer: reprec/imprec=prec on OTHER, no raise): NOT-A-COUNTEREXAMPLE, fails verify.

### VERIFYING ECHO CANDIDATES (share spec AND verify -> materialized faithful patch + ran official harness run_resolve):
- atk_5.py (guard-early: raise if either part OTHER, then ternary assign): CANDIDATE (verifies 17.3s). Faithful patch_atk5.diff (guard-early `if (re!=0 and not re.is_number) or (im!=0 and not im.is_number): raise NotImplementedError`) -> run_resolve resolved=true, completed=true.
- atk_6.py (reorder: classify imag chain before real chain, both with else:raise): CANDIDATE (verifies 17.4s). Faithful patch_atk6.diff (imag chain first, real chain second, each with else:raise) -> run_resolve initially returned completed=false ('no report') from a transient concurrency infra hiccup; DIRECT serial harness re-run resolved_instances=1 -> RESOLVED (report sbu_patch.sbu-eqaudit-atk6diag-2053853.json).
- atk_7.py (defer on OTHER then reuse part_precision helper): CANDIDATE (verifies 17.2s). Faithful patch_atk7.diff (== gold: add else:raise to each chain) -> run_resolve resolved=true, completed=true.

Gold control resolves (direct harness resolved_instances=1, report sbu_patch.sbu-eqaudit-golddiag-1967871.json). NOTE on infra: an initial concurrent batch (gold+atk5+atk6 in parallel via run_resolve) returned completed=false for ALL THREE including gold — a pure concurrency artifact of running multiple heavy Docker harness invocations at once (violates 'one backend at a time'); it is NOT non-resolution. Every candidate resolves when run serially/directly. No verifying wrong impl exists whose faithful patch fails to resolve.

REFINEMENT.MD LEG AUDIT: legs A1-A7 are all R or R+I; no kind-3 (unexpressible-changed-op) leg. Per mapping.md §3 and axiom_check.py there is NO consumed @ContractOnly axiom and NO A-reference deep model — the fix is a pure control-flow/definedness change (add `else: raise NotImplementedError` so an OTHER part defers instead of falling through to read an unset reprec/imprec local). The A-legs' correspondence to the real callees therefore reduces to the three-way classification mapping (part==0 -> 0, elif part.is_number -> 1, else -> 2) and the precision selection (None for 0, prec for numeric), which axiom_check.py and conformance_check.py validate against real SymPy evalf (incl. the F2P witness Mul(Max(0,y),x,evaluate=False)). Correspondence holds; NotImplementedError <-> EvalfDeferred stand-in is documented (builtin exception in Exsures crashes the Nagini translator). No trust point beyond refinement fidelity, and fidelity holds.

Evidence: SUMMARY.md, out_*.txt (weakness/verify), res_atk{5,7}.json (run_resolve), atk6diag.out + golddiag.out (direct harness), patch_atk{5,6,7}.diff, evalf_orig.py.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.py`, `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-13372.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric evaluator splits an expression into its real and imaginary parts
  and assembles a result that pairs each part with a PRECISION component
  describing how that part was evaluated. Each part independently falls into
  exactly one of three cases:

    * EXACT-ZERO  — the part is the exact zero. Its precision component is
      ABSENT (there is no working precision attached to an exact zero).

    * NUMERIC     — the part is a concrete number. Its precision component is
      the supplied working precision.

    * OTHER       — the part is neither an exact zero nor a concrete number
      (it is still symbolic). There is NO precision component defined for such
      a part.

  The behaviour pinned here: a result is assembled — pairing each part with a
  precision component — ONLY when BOTH parts are exact-zero or numeric, in
  which case each precision component is ABSENT for an exact-zero part and the
  working precision for a numeric part. If EITHER part is the OTHER case, no
  result can be assembled (there is no precision component for that part); the
  evaluation must DEFER instead of assembling a result with a missing precision
  component. Deferral lets the caller fall back to an alternative evaluation;
  assembling a result around a missing precision component is never permitted.

Each part's case is modelled as an integer tag (0 = exact-zero, 1 = numeric,
2 = other). The assembled result is a minimal object carrying only the two
touched precision components, each an `Optional[int]` (absent = None). The
deferral is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class EvalfDeferred(Exception):
    """Signals that a result cannot be assembled because some part is neither
    an exact zero nor a concrete number, so no precision component is defined
    for it. Stands in for the `NotImplementedError` the desired behaviour
    raises to defer to an alternative evaluation; a builtin exception in an
    `Exsures` crashes the Nagini translator (mapping.md §2)."""


class EvalfResult:
    """The assembled result: the two touched precision components. Each is the
    working precision for a numeric part, or absent (None) for an exact-zero
    part. A result is assembled only when both precision components are
    defined."""

    def __init__(self, reprec: Optional[int], imprec: Optional[int]) -> None:
        Ensures(Acc(self.reprec) and self.reprec is reprec)  # type: ignore
        Ensures(Acc(self.imprec) and self.imprec is imprec)  # type: ignore
        self.reprec = reprec
        self.imprec = imprec


# axioms-start
# (no axioms: the precision-component selection per part is concrete integer
# control flow, modelled directly — no unchanged opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def part_precision(kind: int, prec: int) -> Optional[int]:
    """The precision component for one part: absent (None) for an exact-zero
    part (kind 0), the working precision for a numeric part (kind 1). Defined
    only for the two cases that yield a precision component; the OTHER case
    (kind 2) has no precision component and is excluded by the precondition."""
    Requires(kind == 0 or kind == 1)
    if kind == 0:
        return None
    return prec
# pure-end


def assemble_evalf_result(re_kind: int, im_kind: int, prec: int) -> EvalfResult:
    # pre-conditions-start
    # Each part is classified into exactly one of the three cases.
    Requires(0 <= re_kind and re_kind <= 2)
    Requires(0 <= im_kind and im_kind <= 2)
    # pre-conditions-end
    # post-conditions-start
    # A result is assembled (returns normally) only when BOTH parts are
    # exact-zero or numeric — never when either part is the OTHER case.
    Ensures(re_kind != 2 and im_kind != 2)
    Ensures(Acc(Result().reprec) and Acc(Result().imprec))
    # Each assembled precision component is exactly the one its part's case
    # demands: absent for exact-zero, the working precision for numeric.
    Ensures(Result().reprec is part_precision(re_kind, prec))
    Ensures(Result().imprec is part_precision(im_kind, prec))
    # The evaluation DEFERS exactly when some part is the OTHER case: no result
    # can be assembled because a precision component would be missing.
    Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)
    # post-conditions-end
    # impl-start
    # Classify the real part. The precision component is set only in the
    # exact-zero and numeric cases; the OTHER case defers before any result is
    # assembled (so no result is ever built around a missing component).
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    else:
        raise EvalfDeferred()
    # Classify the imaginary part identically.
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    else:
        raise EvalfDeferred()
    Assert(reprec is part_precision(re_kind, prec))
    Assert(imprec is part_precision(im_kind, prec))
    return EvalfResult(reprec, imprec)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Editable region = the impl body of assemble_evalf_result (model.py lines 102-122); spec regions (axioms/@Pure/Requires/Ensures/Exsures) held byte-identical in every attack (adversary same-spec: SAME for all 8 + pos_control). The postconditions fully pin the observable as an exact deterministic function of the case tags: Ensures(re_kind!=2 and im_kind!=2), Ensures(Result().reprec is part_precision(re_kind,prec)), Ensures(Result().imprec is part_precision(im_kind,prec)), Exsures(EvalfDeferred, re_kind==2 or im_kind==2). So the spec is functionally complete: any wrong function is rejected, and any verifying impl computes the gold observable.

WRONG-IMPL ATTACKS (must fail verify), cmd `python -m swebench_unified.adversary weakness nagini sympy__sympy-13372 <path>`:
- atk_prepatch.py (drop both else:raise -> reads unset precision local; the prepatch bug): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch bug REPRODUCED (model_prepatch's failure mode: postcondition unprovable on an OTHER part).
- atk_1.py (partial-domain: im OTHER falls through with imprec=prec, no defer): NOT-A-COUNTEREXAMPLE, fails verify.
- atk_2.py (boundary/swap: reprec = prec for exact-zero, None for numeric): NOT-A-COUNTEREXAMPLE, fails verify.
- atk_3.py (control-flow-effect: unconditionally raise EvalfDeferred): NOT-A-COUNTEREXAMPLE, fails verify (Exsures violated when neither part is OTHER).
- atk_4.py (never-defer: reprec/imprec=prec on OTHER, no raise): NOT-A-COUNTEREXAMPLE, fails verify.

### VERIFYING ECHO CANDIDATES (share spec AND verify -> materialized faithful patch + ran official harness run_resolve):
- atk_5.py (guard-early: raise if either part OTHER, then ternary assign): CANDIDATE (verifies 17.3s). Faithful patch_atk5.diff (guard-early `if (re!=0 and not re.is_number) or (im!=0 and not im.is_number): raise NotImplementedError`) -> run_resolve resolved=true, completed=true.
- atk_6.py (reorder: classify imag chain before real chain, both with else:raise): CANDIDATE (verifies 17.4s). Faithful patch_atk6.diff (imag chain first, real chain second, each with else:raise) -> run_resolve initially returned completed=false ('no report') from a transient concurrency infra hiccup; DIRECT serial harness re-run resolved_instances=1 -> RESOLVED (report sbu_patch.sbu-eqaudit-atk6diag-2053853.json).
- atk_7.py (defer on OTHER then reuse part_precision helper): CANDIDATE (verifies 17.2s). Faithful patch_atk7.diff (== gold: add else:raise to each chain) -> run_resolve resolved=true, completed=true.

Gold control resolves (direct harness resolved_instances=1, report sbu_patch.sbu-eqaudit-golddiag-1967871.json). NOTE on infra: an initial concurrent batch (gold+atk5+atk6 in parallel via run_resolve) returned completed=false for ALL THREE including gold — a pure concurrency artifact of running multiple heavy Docker harness invocations at once (violates 'one backend at a time'); it is NOT non-resolution. Every candidate resolves when run serially/directly. No verifying wrong impl exists whose faithful patch fails to resolve.

REFINEMENT.MD LEG AUDIT: legs A1-A7 are all R or R+I; no kind-3 (unexpressible-changed-op) leg. Per mapping.md §3 and axiom_check.py there is NO consumed @ContractOnly axiom and NO A-reference deep model — the fix is a pure control-flow/definedness change (add `else: raise NotImplementedError` so an OTHER part defers instead of falling through to read an unset reprec/imprec local). The A-legs' correspondence to the real callees therefore reduces to the three-way classification mapping (part==0 -> 0, elif part.is_number -> 1, else -> 2) and the precision selection (None for 0, prec for numeric), which axiom_check.py and conformance_check.py validate against real SymPy evalf (incl. the F2P witness Mul(Max(0,y),x,evaluate=False)). Correspondence holds; NotImplementedError <-> EvalfDeferred stand-in is documented (builtin exception in Exsures crashes the Nagini translator). No trust point beyond refinement fidelity, and fidelity holds.

Evidence: SUMMARY.md, out_*.txt (weakness/verify), res_atk{5,7}.json (run_resolve), atk6diag.out + golddiag.out (direct harness), patch_atk{5,6,7}.diff, evalf_orig.py.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the modeled function assemble_evalf_result vs the real patched evalf() fallback (sympy/core/evalf.py:1290-1314, worktree at base_commit 30379ea6e2, git diff shows the gold's two added `else: raise NotImplementedError` branches).

Correspondence is exact across all 9 (re_kind, im_kind) combinations:
- re_kind/im_kind==0 (exact zero) ↔ `re==0 -> reprec=None`; part_precision(0,prec)=None. ✓
- kind==1 (numeric) ↔ `elif re.is_number -> reprec=prec`; part_precision(1,prec)=prec. ✓
- kind==2 (other) ↔ the added `else: raise NotImplementedError`; model raises EvalfDeferred. Deferral condition re_kind==2 or im_kind==2 matches. ✓
- both parts in {0,1}: assembles r=(re,im,reprec,imprec) with reprec/imprec in {None, prec} ↔ EvalfResult(part_precision(...), part_precision(...)). ✓

Abstraction boundary checked: the earlier `if re.has(re_) or im.has(im_): raise NotImplementedError` guard fires only for symbolic parts, which are neither ==0 nor is_number (i.e. kind 2), so it is subsumed by the kind-2 deferral the model already represents — introduces no divergence. The value components (re/im themselves) and _to_mpmath conversion are independent of the precision bug and correctly abstracted (mapping.md §2).

The spec pins exactly the changed delta and no more: model verifies (nagini_verify exit 0, 15s), spec region byte-identical (same-spec = SAME). The prepatch model fails the postcondition re_kind!=2 and im_kind!=2 (the correct sensing of the unbound-local bug), confirming the spec is not weaker than the fix. No input exists where the modeled function disagrees with the real patched callee. The spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over model.py, impl region elided) was regenerated and screened. Mechanical G-LEAK screen: leakage.screen(...) => passed=True, zero hard failures. Manual review of the spec view confirms: no diff markers, no patched file path/module (sympy/core/evalf.py), no verbatim gold-patch line, no 'NotImplementedError' string, no narration terms (bug/fix/patch/etc.). The gold edit adds `else: raise NotImplementedError` to the two `if part==0 / elif part.is_number` chains so an OTHER part defers instead of reading an unset reprec/imprec. That edit and even the identifiers reprec/imprec are ALREADY in the PUBLIC problem_statement: it prints the full traceback ending at `r = re, im, reprec, imprec` / `UnboundLocalError: local variable 'reprec' referenced before assignment`, and the reporter explicitly writes 'the elif clauses that define reprec and imprec should have an `else: raise NotImplementedError`. That appears to fix it.' The spec-view prose ('defer instead of assembling a result with a missing precision component'; three-case classification exact-zero/numeric/other) describes the same behavior at an abstract level and reveals nothing beyond the public problem_statement. The patch adds no def/class, so there are no distinctive patched repo symbols for spec identifiers to collide with; assemble_evalf_result / part_precision / EvalfResult / EvalfDeferred are model-local names. refinement.md and mapping.md are auditor documents, not part of the consumer spec view, so their explicit gold-diff quotes are out of scope for G-PANEL-3. Conclusion: no leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
