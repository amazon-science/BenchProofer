# P2 adversarial audit — django__django-13449

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,15 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
+    # WRONG (prepatch bug): cast wraps operand alone, not the whole OVER clause.
+    d = list(operand)  # type: List[int]
+    inner = d  # type: List[int]
     if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
-        inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
-        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
-        result = [67, 65, 83, 84, 40] + over + \
+        inner = [67, 65, 83, 84, 40] + d + \
             [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
-    else:
-        # No outer cast: the operand renders by its own declared type.
-        raw = list(operand)  # type: List[int]
-        inner2 = raw  # type: List[int]
-        if operand_decimal:
-            inner2 = [67, 65, 83, 84, 40] + raw + \
-                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
-        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
+    elif operand_decimal:
+        inner = [67, 65, 83, 84, 40] + d + \
+            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
+    result = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,12 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
-    if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
-        inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
-        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
-        result = [67, 65, 83, 84, 40] + over + \
+    # WRONG: decimal branch renders no outer cast at all.
+    d = list(operand)  # type: List[int]
+    inner = d  # type: List[int]
+    if not decimal_out and operand_decimal:
+        inner = [67, 65, 83, 84, 40] + d + \
             [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
-    else:
-        # No outer cast: the operand renders by its own declared type.
-        raw = list(operand)  # type: List[int]
-        inner2 = raw  # type: List[int]
-        if operand_decimal:
-            inner2 = [67, 65, 83, 84, 40] + raw + \
-                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
-        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
+    result = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,12 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
-    if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
-        inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
-        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
+    # WRONG: guard inverted — outer cast applied on the non-decimal branch.
+    d = list(operand)  # type: List[int]
+    over = d + [32, 79, 86, 69, 82, 32, 40] + window + [41]  # type: List[int]
+    result = over  # type: List[int]
+    if not decimal_out:
         result = [67, 65, 83, 84, 40] + over + \
             [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
-    else:
-        # No outer cast: the operand renders by its own declared type.
-        raw = list(operand)  # type: List[int]
-        inner2 = raw  # type: List[int]
-        if operand_decimal:
-            inner2 = [67, 65, 83, 84, 40] + raw + \
-                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
-        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,15 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
+    # WRONG: non-decimal branch always renders operand verbatim, dropping the
+    # operand's own cast when operand_decimal is True.
     if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
         inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
         over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
         result = [67, 65, 83, 84, 40] + over + \
             [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
     else:
-        # No outer cast: the operand renders by its own declared type.
         raw = list(operand)  # type: List[int]
-        inner2 = raw  # type: List[int]
-        if operand_decimal:
-            inner2 = [67, 65, 83, 84, 40] + raw + \
-                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
-        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
+        result = raw + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,16 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
+    # WRONG: on decimal branch the operand also carries its own cast (double).
+    d = list(operand)  # type: List[int]
+    inner = d  # type: List[int]
+    if decimal_out or operand_decimal:
+        inner = [67, 65, 83, 84, 40] + d + \
+            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
+    over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]  # type: List[int]
+    result = over  # type: List[int]
     if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
-        inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
-        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
         result = [67, 65, 83, 84, 40] + over + \
             [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
-    else:
-        # No outer cast: the operand renders by its own declared type.
-        raw = list(operand)  # type: List[int]
-        inner2 = raw  # type: List[int]
-        if operand_decimal:
-            inner2 = [67, 65, 83, 84, 40] + raw + \
-                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
-        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,18 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
+    # WRONG: cast closer missing its leading space (byte-off-by-one boundary)
     if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
         inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
         over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
         result = [67, 65, 83, 84, 40] + over + \
-            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
+            [65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
     else:
-        # No outer cast: the operand renders by its own declared type.
         raw = list(operand)  # type: List[int]
         inner2 = raw  # type: List[int]
         if operand_decimal:
             inner2 = [67, 65, 83, 84, 40] + raw + \
                 [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
         result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(operand), 1 / 2))
     Requires(Acc(list_pred(window), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(operand), 1 / 2))
@@ -128,27 +126,18 @@
             ToSeq(window))))
     # post-conditions-end
     # impl-start
+    # WRONG: non-decimal branch casts the operand iff operand_decimal is False.
     if decimal_out:
-        # The operand is compiled with a non-decimal output: the decimal cast
-        # it would otherwise carry is absorbed by the outer cast, so verbatim.
         inner = list(operand)  # type: List[int]
-        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
         over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
-        Assert(ToSeq(over) == over_clause(
-            compile_operand(ToSeq(operand), False), ToSeq(window)))
         result = [67, 65, 83, 84, 40] + over + \
             [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
     else:
-        # No outer cast: the operand renders by its own declared type.
         raw = list(operand)  # type: List[int]
         inner2 = raw  # type: List[int]
-        if operand_decimal:
+        if not operand_decimal:
             inner2 = [67, 65, 83, 84, 40] + raw + \
                 [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
-        else:
-            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
         result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-13449.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A windowed expression renders, on a backend that needs numeric values cast,
  as a fragment of the shape `<inner> OVER (<window>)`. When the windowed
  expression's declared output is the fixed-precision decimal type, the numeric
  cast that the backend requires must enclose the WHOLE windowed fragment, not
  the inner operand:

        CAST( <inner> OVER (<window>) AS NUMERIC)

  and the inner operand must be rendered WITHOUT its own decimal cast (its
  decimal-ness is absorbed by the outer cast, so the operand is rendered as a
  plain floating-point value). When the windowed expression's declared output
  is not the decimal type, NO outer cast is added and the inner operand renders
  by its OWN declared type: it carries its own numeric cast iff its own
  declared output is the decimal type (the two declared outputs can differ,
  e.g. a non-decimal windowed output over a decimal-typed operand), so the
  fragment is `<operand-rendered-by-its-own-type> OVER (<window>)`.

  The discriminating property: the OUTER cast wrapper, when present, surrounds
  the entire `... OVER (...)` clause -- never just the operand -- and it is
  present exactly when the windowed output is the decimal type. For a decimal
  windowed output, a wrapper enclosing the operand alone (leaving
  `CAST(<inner> AS NUMERIC) OVER ...`) is excluded.

SQL fragments are modelled as `List[int]` / `PSeq[int]` token sequences (Nagini
bans `str` indexing). The boolean `decimal_out` abstracts "the windowed
expression's declared output is the fixed-precision decimal type"; the boolean
`operand_decimal` abstracts the same property of the INNER operand's own
declared output. The inner operand's own rendering on this backend
(cast-or-not by its own declared type) is the unchanged callee, axiomatized as
`compile_operand`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def kw_over() -> PSeq[int]:
    # the token sequence ' OVER (' (space O V E R space open-paren)
    return PSeq(32, 79, 86, 69, 82, 32, 40)


@Pure
def kw_over_close() -> PSeq[int]:
    # the closing ')'
    return PSeq(41)


@Pure
def cast_open() -> PSeq[int]:
    # 'CAST('
    return PSeq(67, 65, 83, 84, 40)


@Pure
def cast_close() -> PSeq[int]:
    # ' AS NUMERIC)'
    return PSeq(32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41)


@Pure
def cast_numeric(x: PSeq[int]) -> PSeq[int]:
    """Wrap a fragment in the numeric cast: CAST(<x> AS NUMERIC)."""
    return cast_open() + x + cast_close()


@Pure
def over_clause(inner: PSeq[int], window: PSeq[int]) -> PSeq[int]:
    """The windowed fragment without any cast: <inner> OVER (<window>)."""
    return inner + kw_over() + window + kw_over_close()
# pure-end


# axioms-start
@Pure
@ContractOnly
def compile_operand(operand: PSeq[int], operand_is_decimal: bool) -> PSeq[int]:
    """Rendering of the inner operand on the cast-requiring backend (the
    UNCHANGED callee that compiles a source expression). If the operand's own
    declared output is the decimal type it is wrapped in the numeric cast;
    otherwise it is rendered verbatim. The decimal-output branch of the
    windowed rendering consumes only the NON-decimal case (it forces the
    operand to a floating-point output first, so the operand comes back
    un-cast); the non-decimal-output branch consumes the case matching the
    operand's own declared type.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(not operand_is_decimal, Result() == operand))
    Ensures(Implies(operand_is_decimal, Result() == cast_numeric(operand)))
# axioms-end


def render_windowed_with_numeric_cast(operand: List[int], window: List[int],
                                      decimal_out: bool,
                                      operand_decimal: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(operand), 1 / 2))
    Requires(Acc(list_pred(window), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operand), 1 / 2))
    Ensures(Acc(list_pred(window), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When the windowed output is the decimal type, the numeric cast encloses
    # the ENTIRE `<inner> OVER (<window>)` fragment, and the inner operand is
    # rendered WITHOUT its own cast (its output forced to floating point
    # first, regardless of the operand's own declared type).
    Ensures(Implies(
        decimal_out,
        ToSeq(Result()) == cast_numeric(
            over_clause(compile_operand(ToSeq(operand), False),
                        ToSeq(window)))))
    # When the windowed output is not the decimal type, there is no OUTER
    # cast; the operand renders by its OWN declared type (cast iff the
    # operand's own declared output is the decimal type).
    Ensures(Implies(
        not decimal_out,
        ToSeq(Result()) == over_clause(
            compile_operand(ToSeq(operand), operand_decimal),
            ToSeq(window))))
    # post-conditions-end
    # impl-start
    if decimal_out:
        # The operand is compiled with a non-decimal output: the decimal cast
        # it would otherwise carry is absorbed by the outer cast, so verbatim.
        inner = list(operand)  # type: List[int]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        Assert(ToSeq(over) == over_clause(
            compile_operand(ToSeq(operand), False), ToSeq(window)))
        result = [67, 65, 83, 84, 40] + over + \
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
    else:
        # No outer cast: the operand renders by its own declared type.
        raw = list(operand)  # type: List[int]
        inner2 = raw  # type: List[int]
        if operand_decimal:
            inner2 = [67, 65, 83, 84, 40] + raw + \
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
        else:
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-13449 (nagini). Bundle spec pins ToSeq(Result()) byte-exactly on BOTH branches: decimal_out -> cast_numeric(over_clause(compile_operand(operand,False), window)); not decimal_out -> over_clause(compile_operand(operand, operand_decimal), window). The single axiom compile_operand is grounded (both branches) -> spec is a total function of inputs with NO behavioral freedom, so verify => exact gold bytes => resolves.

POSITIVE CONTROL: atk_pos.py = gold impl. `bash scripts/nagini_verify.sh atk_pos.py` -> exit 0 (Verification successful, 15.1s).

7 DISTINCT wrong impls (impl region only; axioms/@Pure/Requires/Ensures byte-identical; all confirmed SAME by `adversary same-spec`):
- atk_1 prepatch bug: cast wraps operand alone -> CAST(<inner> AS NUMERIC) OVER (...).
- atk_2 decimal branch omits outer cast entirely.
- atk_3 control-flow: guard inverted, outer cast on non-decimal branch.
- atk_4 partial-domain: non-decimal branch ignores operand_decimal (drops operand's own cast).
- atk_5 ungrounded-oracle echo: double cast (operand keeps its cast under outer cast) on decimal branch.
- atk_6 boundary: cast_close missing leading space (byte off-by-one).
- atk_7 non-decimal branch inverts operand cast (casts iff NOT operand_decimal).

Commands: `python -m swebench_unified.adversary weakness nagini django__django-13449 atk_N.py` for each -> ALL exit 2 (NOT-A-COUNTEREXAMPLE: does not verify). Confirmed the rejections are GENUINE SEMANTIC failures (not infra/type errors) via direct `bash scripts/nagini_verify.sh atk_N.py`: every one reports 'Postcondition of render_windowed_with_numeric_cast might not hold' (atk_1/2/5/6 on the decimal_out implication; atk_3/4/7 on the not-decimal_out implication). NOTE: initial atk_1/2/3/5 first failed on a Nagini type error (variable 'raw' redeclared across branches) — rewritten with single-declaration well-typed bodies and re-run so the falsification is semantic, not a translation artifact.

No CANDIDATE emerged (nothing shares the spec AND verifies), so there is NO verifying-wrong-impl to materialize a faithful refined patch for; the run_resolve step is vacuous by construction (patches={}). prepatch_reproduced=true: atk_1 encodes the prepatch shape (matches model_prepatch.py) and is correctly rejected by the postcondition, matching G-DIFF.

refinement.md audit: legs A1/A2/A4 = R (str<->List[int] tokens, %-template<->concat, bool abstractions); A3/A5/A6 = A-consumed on the single axiom compile_operand; no A-reference, no dead axiom, no kind-3 (the genuinely-changed op — cast placement relative to OVER — is expressed structurally via cast_numeric/over_clause over PSeq[int], A4/A5). A-leg correspondence holds: compile_operand's Ensures (decimal->cast_numeric(operand); non-decimal->verbatim) is exactly what axiom_check.py executes against the REAL SQLiteNumericMixin.as_sqlite (7 boundary + 2000 fuzz operands x {Decimal,Float,Int}) plus the end-to-end Window.as_sqlite cast-placement check.

VERDICT: SOUND. >=5 (7) distinct verifying-wrong-impl attacks run, positive control verifies, none is a candidate; verify<=>correct holds for this frozen spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-13449.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A windowed expression renders, on a backend that needs numeric values cast,
  as a fragment of the shape `<inner> OVER (<window>)`. When the windowed
  expression's declared output is the fixed-precision decimal type, the numeric
  cast that the backend requires must enclose the WHOLE windowed fragment, not
  the inner operand:

        CAST( <inner> OVER (<window>) AS NUMERIC)

  and the inner operand must be rendered WITHOUT its own decimal cast (its
  decimal-ness is absorbed by the outer cast, so the operand is rendered as a
  plain floating-point value). When the windowed expression's declared output
  is not the decimal type, NO outer cast is added and the inner operand renders
  by its OWN declared type: it carries its own numeric cast iff its own
  declared output is the decimal type (the two declared outputs can differ,
  e.g. a non-decimal windowed output over a decimal-typed operand), so the
  fragment is `<operand-rendered-by-its-own-type> OVER (<window>)`.

  The discriminating property: the OUTER cast wrapper, when present, surrounds
  the entire `... OVER (...)` clause -- never just the operand -- and it is
  present exactly when the windowed output is the decimal type. For a decimal
  windowed output, a wrapper enclosing the operand alone (leaving
  `CAST(<inner> AS NUMERIC) OVER ...`) is excluded.

SQL fragments are modelled as `List[int]` / `PSeq[int]` token sequences (Nagini
bans `str` indexing). The boolean `decimal_out` abstracts "the windowed
expression's declared output is the fixed-precision decimal type"; the boolean
`operand_decimal` abstracts the same property of the INNER operand's own
declared output. The inner operand's own rendering on this backend
(cast-or-not by its own declared type) is the unchanged callee, axiomatized as
`compile_operand`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def kw_over() -> PSeq[int]:
    # the token sequence ' OVER (' (space O V E R space open-paren)
    return PSeq(32, 79, 86, 69, 82, 32, 40)


@Pure
def kw_over_close() -> PSeq[int]:
    # the closing ')'
    return PSeq(41)


@Pure
def cast_open() -> PSeq[int]:
    # 'CAST('
    return PSeq(67, 65, 83, 84, 40)


@Pure
def cast_close() -> PSeq[int]:
    # ' AS NUMERIC)'
    return PSeq(32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41)


@Pure
def cast_numeric(x: PSeq[int]) -> PSeq[int]:
    """Wrap a fragment in the numeric cast: CAST(<x> AS NUMERIC)."""
    return cast_open() + x + cast_close()


@Pure
def over_clause(inner: PSeq[int], window: PSeq[int]) -> PSeq[int]:
    """The windowed fragment without any cast: <inner> OVER (<window>)."""
    return inner + kw_over() + window + kw_over_close()
# pure-end


# axioms-start
@Pure
@ContractOnly
def compile_operand(operand: PSeq[int], operand_is_decimal: bool) -> PSeq[int]:
    """Rendering of the inner operand on the cast-requiring backend (the
    UNCHANGED callee that compiles a source expression). If the operand's own
    declared output is the decimal type it is wrapped in the numeric cast;
    otherwise it is rendered verbatim. The decimal-output branch of the
    windowed rendering consumes only the NON-decimal case (it forces the
    operand to a floating-point output first, so the operand comes back
    un-cast); the non-decimal-output branch consumes the case matching the
    operand's own declared type.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(not operand_is_decimal, Result() == operand))
    Ensures(Implies(operand_is_decimal, Result() == cast_numeric(operand)))
# axioms-end


def render_windowed_with_numeric_cast(operand: List[int], window: List[int],
                                      decimal_out: bool,
                                      operand_decimal: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(operand), 1 / 2))
    Requires(Acc(list_pred(window), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operand), 1 / 2))
    Ensures(Acc(list_pred(window), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When the windowed output is the decimal type, the numeric cast encloses
    # the ENTIRE `<inner> OVER (<window>)` fragment, and the inner operand is
    # rendered WITHOUT its own cast (its output forced to floating point
    # first, regardless of the operand's own declared type).
    Ensures(Implies(
        decimal_out,
        ToSeq(Result()) == cast_numeric(
            over_clause(compile_operand(ToSeq(operand), False),
                        ToSeq(window)))))
    # When the windowed output is not the decimal type, there is no OUTER
    # cast; the operand renders by its OWN declared type (cast iff the
    # operand's own declared output is the decimal type).
    Ensures(Implies(
        not decimal_out,
        ToSeq(Result()) == over_clause(
            compile_operand(ToSeq(operand), operand_decimal),
            ToSeq(window))))
    # post-conditions-end
    # impl-start
    if decimal_out:
        # The operand is compiled with a non-decimal output: the decimal cast
        # it would otherwise carry is absorbed by the outer cast, so verbatim.
        inner = list(operand)  # type: List[int]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        Assert(ToSeq(over) == over_clause(
            compile_operand(ToSeq(operand), False), ToSeq(window)))
        result = [67, 65, 83, 84, 40] + over + \
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
    else:
        # No outer cast: the operand renders by its own declared type.
        raw = list(operand)  # type: List[int]
        inner2 = raw  # type: List[int]
        if operand_decimal:
            inner2 = [67, 65, 83, 84, 40] + raw + \
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
        else:
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-13449 (nagini). Bundle spec pins ToSeq(Result()) byte-exactly on BOTH branches: decimal_out -> cast_numeric(over_clause(compile_operand(operand,False), window)); not decimal_out -> over_clause(compile_operand(operand, operand_decimal), window). The single axiom compile_operand is grounded (both branches) -> spec is a total function of inputs with NO behavioral freedom, so verify => exact gold bytes => resolves.

POSITIVE CONTROL: atk_pos.py = gold impl. `bash scripts/nagini_verify.sh atk_pos.py` -> exit 0 (Verification successful, 15.1s).

7 DISTINCT wrong impls (impl region only; axioms/@Pure/Requires/Ensures byte-identical; all confirmed SAME by `adversary same-spec`):
- atk_1 prepatch bug: cast wraps operand alone -> CAST(<inner> AS NUMERIC) OVER (...).
- atk_2 decimal branch omits outer cast entirely.
- atk_3 control-flow: guard inverted, outer cast on non-decimal branch.
- atk_4 partial-domain: non-decimal branch ignores operand_decimal (drops operand's own cast).
- atk_5 ungrounded-oracle echo: double cast (operand keeps its cast under outer cast) on decimal branch.
- atk_6 boundary: cast_close missing leading space (byte off-by-one).
- atk_7 non-decimal branch inverts operand cast (casts iff NOT operand_decimal).

Commands: `python -m swebench_unified.adversary weakness nagini django__django-13449 atk_N.py` for each -> ALL exit 2 (NOT-A-COUNTEREXAMPLE: does not verify). Confirmed the rejections are GENUINE SEMANTIC failures (not infra/type errors) via direct `bash scripts/nagini_verify.sh atk_N.py`: every one reports 'Postcondition of render_windowed_with_numeric_cast might not hold' (atk_1/2/5/6 on the decimal_out implication; atk_3/4/7 on the not-decimal_out implication). NOTE: initial atk_1/2/3/5 first failed on a Nagini type error (variable 'raw' redeclared across branches) — rewritten with single-declaration well-typed bodies and re-run so the falsification is semantic, not a translation artifact.

No CANDIDATE emerged (nothing shares the spec AND verifies), so there is NO verifying-wrong-impl to materialize a faithful refined patch for; the run_resolve step is vacuous by construction (patches={}). prepatch_reproduced=true: atk_1 encodes the prepatch shape (matches model_prepatch.py) and is correctly rejected by the postcondition, matching G-DIFF.

refinement.md audit: legs A1/A2/A4 = R (str<->List[int] tokens, %-template<->concat, bool abstractions); A3/A5/A6 = A-consumed on the single axiom compile_operand; no A-reference, no dead axiom, no kind-3 (the genuinely-changed op — cast placement relative to OVER — is expressed structurally via cast_numeric/over_clause over PSeq[int], A4/A5). A-leg correspondence holds: compile_operand's Ensures (decimal->cast_numeric(operand); non-decimal->verbatim) is exactly what axiom_check.py executes against the REAL SQLiteNumericMixin.as_sqlite (7 boundary + 2000 fuzz operands x {Decimal,Float,Int}) plus the end-to-end Window.as_sqlite cast-placement check.

VERDICT: SOUND. >=5 (7) distinct verifying-wrong-impl attacks run, positive control verifies, none is a candidate; verify<=>correct holds for this frozen spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (G-PANEL-2) check of render_windowed_with_numeric_cast vs the real patched Window.as_sqlite (django/db/models/expressions.py @ base_commit 2a55431a, gold patch applied). Empirically rendered the REAL Window.as_sqlite over an in-memory sqlite backend for all four combinations of (decimal_out, operand_decimal):
  A decimal_out=T, source decimal  -> CAST(LAG(dprice) OVER (...) AS NUMERIC)   [outer cast wraps WHOLE OVER clause, operand un-cast]
  B decimal_out=T, source float    -> CAST(LAG(fprice) OVER (...) AS NUMERIC)   [operand un-cast regardless of source type]
  C decimal_out=F(FloatField), source decimal -> CAST(LAG(dprice) AS NUMERIC) OVER (...)   [inner cast only, no outer]
  D decimal_out=F(FloatField), source float   -> LAG(fprice) OVER (...)   [no cast anywhere]

Spec postconditions:
  Implies(decimal_out, Result == cast_numeric(over_clause(compile_operand(op,False),win)))  -> CAST(<op verbatim> OVER (win) AS NUMERIC)
  Implies(not decimal_out, Result == over_clause(compile_operand(op,operand_decimal),win))  -> <op-by-own-type> OVER (win)

Mapping A->spec(decimal branch, op un-cast) MATCHES; B->spec(decimal branch deliberately uses compile_operand(op,False) ignoring operand_decimal) MATCHES the real code which forces source_expressions[0].output_field=FloatField() before compiling so the operand always returns un-cast; C->spec(non-decimal branch, operand_decimal=True keeps own cast) MATCHES; D->spec(non-decimal branch, operand_decimal=False) MATCHES.

Token constants decoded from the model verified byte-identical to the rendered literals: CAST( , ' OVER (' , ')' , ' AS NUMERIC)'. compile_operand axiom is the byte-for-byte unchanged SQLiteNumericMixin.as_sqlite (cast iff DecimalField else verbatim), independently validated by G-AX. List[int]<->str and %-template<->concat refinements and the two-bool abstraction capture exactly the properties the branches read; params are threaded unchanged and observationally irrelevant. Positive control: model.py verifies with the pinned Nagini verifier (Verification successful, 14.8s). No input found on which the modeled function disagrees with the real callee. Spec is neither too strong nor drifted.

  A decimal_out=T, source decimal  -> CAST(LAG(dprice) OVER (...) AS NUMERIC)   [outer cast wraps WHOLE OVER clause, operand un-cast]
  B decimal_out=T, source float    -> CAST(LAG(fprice) OVER (...) AS NUMERIC)   [operand un-cast regardless of source type]
  C decimal_out=F(FloatField), source decimal -> CAST(LAG(dprice) AS NUMERIC) OVER (...)   [inner cast only, no outer]
  D decimal_out=F(FloatField), source float   -> LAG(fprice) OVER (...)   [no cast anywhere]

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction assessment of the nagini spec view for django__django-13449 (docstring + pure helpers + compile_operand axiom + pre/post-conditions; impl-start..impl-end elided).

Public problem_statement discloses: (a) 'the CAST() statement ends after LAG whereas it should be around the whole statement up until w' -> the numeric cast must wrap the WHOLE windowed clause, not the operand; (b) 'This only applies where the lagged field is a DecimalField'; (c) the reporter's own workaround 'adding output_field=FloatField() to the Lag function'; (d) the pasted buggy SQL CAST(LAG(...) AS NUMERIC) OVER (PARTITION BY ... ORDER BY ...).

Spec view behavioral facts and their public-source derivation:
- Cast wraps entire `<inner> OVER (<window>)` when decimal_out (docstring lines 6-11, post-cond 114-118) = reporter's diagnosis 'around the whole statement up until w'.
- Decimal-type trigger (decimal_out flag) = 'only applies where the lagged field is a DecimalField'.
- Operand rendered without own cast, 'as a plain floating-point value' / 'output forced to floating point first' (lines 13-14, 112-113) = the FloatField() workaround the reporter states verbatim.
- Excluded wrong shape CAST(<inner> AS NUMERIC) OVER (lines 24-26) = the buggy SQL literally pasted in the report.
- Non-decimal branch adds no outer cast, operand by own type = generalization, not gold-specific.

Lexical scan of the spec view found NONE of the gold-patch identifiers: SQLiteNumericMixin, as_sqlite, super(Window, copy), get/set_source_expressions, .copy(), output_field, Window, FloatField, DecimalField, expressions.py. Those live only in mapping.md/meta.json/refinement.md (not solver-facing). Model is abstracted to List[int]/PSeq[int] token sequences and the bools decimal_out/operand_decimal; the concrete gold edit (subclass SQLiteNumericMixin + delegate to super().as_sqlite) is NOT reconstructable from the spec view beyond the public bug report. G-LEAK gate also reports 'spec view clean'. The spec view stays within the public problem_statement's disclosure envelope.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
