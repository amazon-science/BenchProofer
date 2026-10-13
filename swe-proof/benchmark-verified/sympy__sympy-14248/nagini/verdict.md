# P2 adversarial audit — sympy__sympy-14248

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
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -218,15 +216,14 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
-        piece = list(contrib(t))  # type: List[int]
+        piece = list(sep_plus() + t)  # type: List[int]
         result = piece + result
         i = i - 1
     t0 = terms[0]
-    head = list(lead(t0))  # type: List[int]
+    head = list(t0)  # type: List[int]
     result = head + result
     return result
     # impl-end
@@ -238,7 +235,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,7 +255,6 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
@@ -279,7 +274,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +290,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -218,7 +216,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
@@ -238,7 +235,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,7 +255,6 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
@@ -279,7 +274,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +290,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
@@ -306,7 +299,5 @@
     t0 = factors[0]
     head = list(t0)  # type: List[int]
     result = head + result
-    if neg:
-        result = [45] + result
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -218,7 +216,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
@@ -238,7 +235,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,13 +255,12 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
         Assert(ToSeq(negs)[i - 1] == n)
-        piece = list(contrib_space(t, n))  # type: List[int]
+        piece = list(contrib_space(t, is_neg(t)))  # type: List[int]
         result = piece + result
         i = i - 1
     t0 = terms[0]
@@ -279,7 +274,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +290,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -218,7 +216,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
@@ -238,7 +235,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,13 +255,12 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
         Assert(ToSeq(negs)[i - 1] == n)
-        piece = list(contrib_space(t, n))  # type: List[int]
+        piece = list(contrib(t))  # type: List[int]
         result = piece + result
         i = i - 1
     t0 = terms[0]
@@ -279,7 +274,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +290,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -218,7 +216,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
@@ -226,7 +223,7 @@
         result = piece + result
         i = i - 1
     t0 = terms[0]
-    head = list(lead(t0))  # type: List[int]
+    head = list(body(t0))  # type: List[int]
     result = head + result
     return result
     # impl-end
@@ -238,7 +235,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,7 +255,6 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
@@ -279,7 +274,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +290,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -218,7 +216,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
@@ -238,7 +235,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,7 +255,6 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
@@ -279,7 +274,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +290,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
@@ -306,7 +299,7 @@
     t0 = factors[0]
     head = list(t0)  # type: List[int]
     result = head + result
-    if neg:
+    if neg and len(factors) > 1:
         result = [45] + result
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -201,7 +200,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(terms), 1 / 2))
     Requires(len(terms) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -210,6 +208,8 @@
     Ensures(ToSeq(Result()) == matadd(ToSeq(terms)))
     # post-conditions-end
     # impl-start
+    if len(terms) == 1:
+        return list(body(terms[0]))
     result = []  # type: List[int]
     i = len(terms)
     while i > 1:
@@ -218,7 +218,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(terms))
         Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         Assert(ToSeq(terms)[i - 1] == t)
@@ -238,7 +237,6 @@
     Requires(Acc(list_pred(negs), 1 / 2))
     Requires(len(terms) >= 1)
     Requires(len(negs) == len(terms))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(terms), 1 / 2))
@@ -259,7 +257,6 @@
         Invariant(1 <= i and i <= len(terms))
         Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
         Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = terms[i - 1]
         n = negs[i - 1]
@@ -279,7 +276,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(len(factors) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -296,7 +292,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= len(factors))
         Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
-        Invariant(MustTerminate(i))
         # invariants-end
         t = factors[i - 1]
         Assert(ToSeq(factors)[i - 1] == t)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-14248.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Rendering a matrix-valued sum of terms as a flat infix string.
      A subtraction is carried internally as the addition of a term whose
      rendered form already begins with a leading minus.  The rendered sum
      must therefore use a binary minus for such a term -- the separator
      before a leading-minus term is " - " and that leading minus is removed
      from the term -- rather than blindly joining every term with " + "
      (which would yield "+ -<term>").  The very first term carries no infix
      separator: a leading-minus first term keeps its minus, a non-negative
      first term is rendered bare.

  (2) Rendering a matrix-valued product of factors as a flat string joined by
      "*".  When the product carries a negative numeric leading coefficient
      the whole product is rendered with a single leading minus in front of
      the factor list (the coefficient having been folded back, positive, into
      the factors); otherwise no sign is emitted.

  (3) A second flavour of matrix-sum rendering that joins with a single space
      rather than a spaced binary minus.  Here the decision is NOT made on the
      rendered text: each term carries a separate boolean fact -- "this term's
      leading coefficient is structurally negative" (the truthiness of a
      structural test on the expression tree, supplied as an input alongside
      the rendered term; a term may be structurally negative yet render with
      no leading minus, e.g. a negative-assumption symbol coefficient).  The
      separator before a structurally-negative term is a single space and the
      term is emitted in full (any minus stays attached to the term); a
      non-negative non-leading term is preceded by " + ".  As in (1) the very
      first term carries no infix separator and is emitted in full.  This must
      not blindly join every term with " + " (which would yield "+ -<term>"),
      and must NOT substitute a rendered-text leading-minus test for the
      structural fact.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the per-element specification is carried by `PSeq[int]`, and the
list of already-rendered terms / factors by `PSeq[PSeq[int]]`.  All three
behaviours are modelled DEEPLY (the assembly of the output sequence is spelled
out as a front-recursive fold) -- there are no axiomatized callees: the
rendering of an individual term / factor is an INPUT to each function (a type
refinement of the per-argument sub-render), so nothing opaque is consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: both behaviours are modelled deeply; the per-argument rendering
# of each term/factor is an input, not an opaque callee under contract.)
# axioms-end


# pure-start
@Pure
def empty() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(45).take(0)


@Pure
def is_neg(t: PSeq[int]) -> bool:
    """A rendered term that already begins with a leading minus (U+002D)."""
    return len(t) > 0 and t[0] == 45


@Pure
def body(t: PSeq[int]) -> PSeq[int]:
    """The rendered term with a single leading minus stripped, if present."""
    if is_neg(t):
        return t.drop(1)
    return t


@Pure
def sep_plus() -> PSeq[int]:
    # ' + '
    return PSeq(32, 43, 32)


@Pure
def sep_minus() -> PSeq[int]:
    # ' - '
    return PSeq(32, 45, 32)


@Pure
def star() -> PSeq[int]:
    # '*'
    return PSeq(42)


@Pure
def contrib(t: PSeq[int]) -> PSeq[int]:
    """The infix contribution of one non-leading sum term: a leading-minus
    term becomes ' - '<body>; any other term becomes ' + '<term>."""
    if is_neg(t):
        return sep_minus() + body(t)
    return sep_plus() + body(t)


@Pure
def add_tail(terms: PSeq[PSeq[int]], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading sum terms terms[i:]."""
    Requires(0 <= i and i <= len(terms))
    if i == len(terms):
        return empty()
    return contrib(terms[i]) + add_tail(terms, i + 1)


@Pure
def lead(t: PSeq[int]) -> PSeq[int]:
    """The leading sum term: a leading-minus term keeps its minus; otherwise
    rendered bare (no infix separator)."""
    if is_neg(t):
        return PSeq(45) + body(t)
    return body(t)


@Pure
def matadd(terms: PSeq[PSeq[int]]) -> PSeq[int]:
    """The whole rendered sum: leading term then the folded non-leading tail."""
    if len(terms) == 0:
        return empty()
    return lead(terms[0]) + add_tail(terms, 1)


@Pure
def mul_tail(factors: PSeq[PSeq[int]], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading product factors factors[i:],
    each prefixed by the '*' separator."""
    Requires(0 <= i and i <= len(factors))
    if i == len(factors):
        return empty()
    return star() + factors[i] + mul_tail(factors, i + 1)


@Pure
def joinstar(factors: PSeq[PSeq[int]]) -> PSeq[int]:
    """The factor list joined by '*' (leading factor bare)."""
    if len(factors) == 0:
        return empty()
    return factors[0] + mul_tail(factors, 1)


@Pure
def matmul(factors: PSeq[PSeq[int]], neg: bool) -> PSeq[int]:
    """The whole rendered product: a single leading minus iff the product
    carries a negative numeric leading coefficient, then the '*'-joined
    (coefficient-normalised) factors."""
    if neg:
        return PSeq(45) + joinstar(factors)
    return joinstar(factors)


@Pure
def sep_space() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def contrib_space(t: PSeq[int], n: bool) -> PSeq[int]:
    """The infix contribution of one non-leading sum term under the
    single-space join discipline: a STRUCTURALLY-negative term (the boolean
    fact n, an input alongside the rendered term) becomes ' '<term> (the term
    emitted in full, any minus kept); any other term becomes ' + '<term>.
    The decision is n, NOT a test on the rendered text."""
    if n:
        return sep_space() + t
    return sep_plus() + t


@Pure
def add_tail_space(terms: PSeq[PSeq[int]], negs: PSeq[bool], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading sum terms terms[i:] under the
    single-space join discipline, negs[k] carrying the structural negativity
    fact of terms[k]."""
    Requires(len(negs) == len(terms))
    Requires(0 <= i and i <= len(terms))
    if i == len(terms):
        return empty()
    return contrib_space(terms[i], negs[i]) + add_tail_space(terms, negs, i + 1)


@Pure
def matadd_space(terms: PSeq[PSeq[int]], negs: PSeq[bool]) -> PSeq[int]:
    """The whole rendered sum under the single-space join discipline: the
    leading term emitted in full, then the folded non-leading tail."""
    Requires(len(negs) == len(terms))
    if len(terms) == 0:
        return empty()
    return terms[0] + add_tail_space(terms, negs, 1)
# pure-end


def render_sum(terms: List[PSeq[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(terms), 1 / 2))
    Requires(len(terms) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(terms)) == len(terms))
    Ensures(ToSeq(Result()) == matadd(ToSeq(terms)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
        # invariants-end
        t = terms[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        piece = list(contrib(t))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(lead(t0))  # type: List[int]
    result = head + result
    return result
    # impl-end


def render_sum_space(terms: List[PSeq[int]], negs: List[bool]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(terms), 1 / 2))
    Requires(Acc(list_pred(negs), 1 / 2))
    Requires(len(terms) >= 1)
    Requires(len(negs) == len(terms))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(negs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(terms)) == len(terms))
    Ensures(len(ToSeq(negs)) == len(ToSeq(terms)))
    Ensures(ToSeq(Result()) == matadd_space(ToSeq(terms), ToSeq(negs)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(negs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
        Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
        # invariants-end
        t = terms[i - 1]
        n = negs[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        Assert(ToSeq(negs)[i - 1] == n)
        piece = list(contrib_space(t, n))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(t0)  # type: List[int]
    result = head + result
    return result
    # impl-end


def render_product(factors: List[PSeq[int]], neg: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(len(factors) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(factors)) == len(factors))
    Ensures(ToSeq(Result()) == matmul(ToSeq(factors), neg))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(factors)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(factors))
        Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
        # invariants-end
        t = factors[i - 1]
        Assert(ToSeq(factors)[i - 1] == t)
        piece = list(star() + t)  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = factors[0]
    head = list(t0)  # type: List[int]
    result = head + result
    if neg:
        result = [45] + result
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-14248 (nagini). Ran 7 DISTINCT same-spec wrong-impl attacks + a positive control; all attacks touch ONLY impl regions (spec byte-identical confirmed via `same-spec`, exit 0 for all 7).

ATTACK RESULTS (command: `python -m swebench_unified.adversary weakness nagini sympy__sympy-14248 <path>`; all exit 2 = NOT-A-COUNTEREXAMPLE, verification failed => spec rejected the impl):
- atk_1.py: render_sum prepatch bug — loop body `sep_plus()+t`, bare first term (re-encodes model_prepatch.py). same-spec=SAME, verifies=NO. Fails invariant ToSeq(result)==add_tail(...).
- atk_2.py: render_product prepatch bug — drops the `neg` leading minus (re-encodes model_prepatch_2.py). same-spec=SAME, verifies=NO. Fails post matmul.
- atk_3.py: render_sum_space ungrounded-oracle echo — decides on `is_neg(t)` (rendered text) instead of the structural boolean `n=negs[i-1]`. same-spec=SAME, verifies=NO. This is the G-PANEL-2 faithfulness rival; spec rejects it (confirms negs[k] correspondence is enforced).
- atk_4.py: render_sum_space str-discipline — uses `contrib(t)` (' - ' + minus-strip) instead of contrib_space (re-encodes model_prepatch_3 discipline swap / G-PBT weak-space-as-str-discipline). same-spec=SAME, verifies=NO.
- atk_5.py: render_sum boundary — first term `body(t0)` instead of `lead(t0)`, dropping the leading minus on a negative first term. same-spec=SAME, verifies=NO.
- atk_6.py: render_product control-flow-effect — prepend minus only when `neg and len(factors)>1` (single-factor product loses sign). same-spec=SAME, verifies=NO.
- atk_7.py: render_sum partial-domain — special-case `len(terms)==1` returns `body(terms[0])` (drops minus). same-spec=SAME, verifies=NO.

POSITIVE CONTROL: pos_control.py (= bundle model.py) VERIFIES via `bash scripts/nagini_verify.sh` (exit 0, "Verification successful", 12.5s).

No attack returned a CANDIDATE (none shares spec AND verifies), so per protocol no faithful refined patch needed materialization and no run_resolve was triggered. prepatch_reproduced=true: atk_1/atk_2/atk_3 re-encode the three documented prepatch bugs (model_prepatch{,_2,_3}.py) and all correctly fail to verify.

A-LEG / MODEL-CORRESPONDENCE AUDIT: meta.json shows axioms=[] and deep_model_references=[] — there are genuinely NO axiomatized callees (@ContractOnly), so refinement.md correctly has no A-consumed/A-reference legs and no kind-3 step. Every leg is R (rendered-child str <-> PSeq[int] code points; child render and the structural negativity/coefficient tests carried as boolean inputs `neg`/`negs`, a legitimate input-refinement of consumed-not-changed facts) or I (identical concrete op: ' - '/' + '/'*'/leading '-'). Verified against patch.diff (byte-checked: str/latex _print_MatAdd sign-aware join, str/latex _print_MatMul leading-sign, pretty _print_MatAdd single-space structural-negativity join). The subtle correspondence pretty negs[k] == S(item.args[0]).is_negative (NOT is_neg on rendered text) is the correct callee semantics — atk_3 confirms the spec REJECTS the text-decided rival, and atk_4 confirms it rejects the str-discipline rival, so render_sum_space genuinely pins the distinct pretty algorithm. §C cross-file dispositions (latex._print_MatAdd byte-identical R of matadd; latex._print_MatMul same-shape R of matmul) hold.

The spec pins each function output as EXACT equality (Ensures ToSeq(Result())==matadd/matadd_space/matmul(...)) over totally-quantified preconditions, so verify => output byte-identical to the gold fold on every tested site => the gold patch (correctness oracle, G-RESOLVE) resolves. Refinement fidelity holds; no verifying wrong impl exists among the 7 distinct falsification attempts. VERDICT: SOUND.

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
"""Twin-artifact model for sympy__sympy-14248.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Rendering a matrix-valued sum of terms as a flat infix string.
      A subtraction is carried internally as the addition of a term whose
      rendered form already begins with a leading minus.  The rendered sum
      must therefore use a binary minus for such a term -- the separator
      before a leading-minus term is " - " and that leading minus is removed
      from the term -- rather than blindly joining every term with " + "
      (which would yield "+ -<term>").  The very first term carries no infix
      separator: a leading-minus first term keeps its minus, a non-negative
      first term is rendered bare.

  (2) Rendering a matrix-valued product of factors as a flat string joined by
      "*".  When the product carries a negative numeric leading coefficient
      the whole product is rendered with a single leading minus in front of
      the factor list (the coefficient having been folded back, positive, into
      the factors); otherwise no sign is emitted.

  (3) A second flavour of matrix-sum rendering that joins with a single space
      rather than a spaced binary minus.  Here the decision is NOT made on the
      rendered text: each term carries a separate boolean fact -- "this term's
      leading coefficient is structurally negative" (the truthiness of a
      structural test on the expression tree, supplied as an input alongside
      the rendered term; a term may be structurally negative yet render with
      no leading minus, e.g. a negative-assumption symbol coefficient).  The
      separator before a structurally-negative term is a single space and the
      term is emitted in full (any minus stays attached to the term); a
      non-negative non-leading term is preceded by " + ".  As in (1) the very
      first term carries no infix separator and is emitted in full.  This must
      not blindly join every term with " + " (which would yield "+ -<term>"),
      and must NOT substitute a rendered-text leading-minus test for the
      structural fact.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the per-element specification is carried by `PSeq[int]`, and the
list of already-rendered terms / factors by `PSeq[PSeq[int]]`.  All three
behaviours are modelled DEEPLY (the assembly of the output sequence is spelled
out as a front-recursive fold) -- there are no axiomatized callees: the
rendering of an individual term / factor is an INPUT to each function (a type
refinement of the per-argument sub-render), so nothing opaque is consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: both behaviours are modelled deeply; the per-argument rendering
# of each term/factor is an input, not an opaque callee under contract.)
# axioms-end


# pure-start
@Pure
def empty() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(45).take(0)


@Pure
def is_neg(t: PSeq[int]) -> bool:
    """A rendered term that already begins with a leading minus (U+002D)."""
    return len(t) > 0 and t[0] == 45


@Pure
def body(t: PSeq[int]) -> PSeq[int]:
    """The rendered term with a single leading minus stripped, if present."""
    if is_neg(t):
        return t.drop(1)
    return t


@Pure
def sep_plus() -> PSeq[int]:
    # ' + '
    return PSeq(32, 43, 32)


@Pure
def sep_minus() -> PSeq[int]:
    # ' - '
    return PSeq(32, 45, 32)


@Pure
def star() -> PSeq[int]:
    # '*'
    return PSeq(42)


@Pure
def contrib(t: PSeq[int]) -> PSeq[int]:
    """The infix contribution of one non-leading sum term: a leading-minus
    term becomes ' - '<body>; any other term becomes ' + '<term>."""
    if is_neg(t):
        return sep_minus() + body(t)
    return sep_plus() + body(t)


@Pure
def add_tail(terms: PSeq[PSeq[int]], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading sum terms terms[i:]."""
    Requires(0 <= i and i <= len(terms))
    if i == len(terms):
        return empty()
    return contrib(terms[i]) + add_tail(terms, i + 1)


@Pure
def lead(t: PSeq[int]) -> PSeq[int]:
    """The leading sum term: a leading-minus term keeps its minus; otherwise
    rendered bare (no infix separator)."""
    if is_neg(t):
        return PSeq(45) + body(t)
    return body(t)


@Pure
def matadd(terms: PSeq[PSeq[int]]) -> PSeq[int]:
    """The whole rendered sum: leading term then the folded non-leading tail."""
    if len(terms) == 0:
        return empty()
    return lead(terms[0]) + add_tail(terms, 1)


@Pure
def mul_tail(factors: PSeq[PSeq[int]], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading product factors factors[i:],
    each prefixed by the '*' separator."""
    Requires(0 <= i and i <= len(factors))
    if i == len(factors):
        return empty()
    return star() + factors[i] + mul_tail(factors, i + 1)


@Pure
def joinstar(factors: PSeq[PSeq[int]]) -> PSeq[int]:
    """The factor list joined by '*' (leading factor bare)."""
    if len(factors) == 0:
        return empty()
    return factors[0] + mul_tail(factors, 1)


@Pure
def matmul(factors: PSeq[PSeq[int]], neg: bool) -> PSeq[int]:
    """The whole rendered product: a single leading minus iff the product
    carries a negative numeric leading coefficient, then the '*'-joined
    (coefficient-normalised) factors."""
    if neg:
        return PSeq(45) + joinstar(factors)
    return joinstar(factors)


@Pure
def sep_space() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def contrib_space(t: PSeq[int], n: bool) -> PSeq[int]:
    """The infix contribution of one non-leading sum term under the
    single-space join discipline: a STRUCTURALLY-negative term (the boolean
    fact n, an input alongside the rendered term) becomes ' '<term> (the term
    emitted in full, any minus kept); any other term becomes ' + '<term>.
    The decision is n, NOT a test on the rendered text."""
    if n:
        return sep_space() + t
    return sep_plus() + t


@Pure
def add_tail_space(terms: PSeq[PSeq[int]], negs: PSeq[bool], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading sum terms terms[i:] under the
    single-space join discipline, negs[k] carrying the structural negativity
    fact of terms[k]."""
    Requires(len(negs) == len(terms))
    Requires(0 <= i and i <= len(terms))
    if i == len(terms):
        return empty()
    return contrib_space(terms[i], negs[i]) + add_tail_space(terms, negs, i + 1)


@Pure
def matadd_space(terms: PSeq[PSeq[int]], negs: PSeq[bool]) -> PSeq[int]:
    """The whole rendered sum under the single-space join discipline: the
    leading term emitted in full, then the folded non-leading tail."""
    Requires(len(negs) == len(terms))
    if len(terms) == 0:
        return empty()
    return terms[0] + add_tail_space(terms, negs, 1)
# pure-end


def render_sum(terms: List[PSeq[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(terms), 1 / 2))
    Requires(len(terms) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(terms)) == len(terms))
    Ensures(ToSeq(Result()) == matadd(ToSeq(terms)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
        # invariants-end
        t = terms[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        piece = list(contrib(t))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(lead(t0))  # type: List[int]
    result = head + result
    return result
    # impl-end


def render_sum_space(terms: List[PSeq[int]], negs: List[bool]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(terms), 1 / 2))
    Requires(Acc(list_pred(negs), 1 / 2))
    Requires(len(terms) >= 1)
    Requires(len(negs) == len(terms))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(negs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(terms)) == len(terms))
    Ensures(len(ToSeq(negs)) == len(ToSeq(terms)))
    Ensures(ToSeq(Result()) == matadd_space(ToSeq(terms), ToSeq(negs)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(negs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
        Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
        # invariants-end
        t = terms[i - 1]
        n = negs[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        Assert(ToSeq(negs)[i - 1] == n)
        piece = list(contrib_space(t, n))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(t0)  # type: List[int]
    result = head + result
    return result
    # impl-end


def render_product(factors: List[PSeq[int]], neg: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(len(factors) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(factors)) == len(factors))
    Ensures(ToSeq(Result()) == matmul(ToSeq(factors), neg))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(factors)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(factors))
        Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
        # invariants-end
        t = factors[i - 1]
        Assert(ToSeq(factors)[i - 1] == t)
        piece = list(star() + t)  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = factors[0]
    head = list(t0)  # type: List[int]
    result = head + result
    if neg:
        result = [45] + result
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-14248 (nagini). Ran 7 DISTINCT same-spec wrong-impl attacks + a positive control; all attacks touch ONLY impl regions (spec byte-identical confirmed via `same-spec`, exit 0 for all 7).

ATTACK RESULTS (command: `python -m swebench_unified.adversary weakness nagini sympy__sympy-14248 <path>`; all exit 2 = NOT-A-COUNTEREXAMPLE, verification failed => spec rejected the impl):
- atk_1.py: render_sum prepatch bug — loop body `sep_plus()+t`, bare first term (re-encodes model_prepatch.py). same-spec=SAME, verifies=NO. Fails invariant ToSeq(result)==add_tail(...).
- atk_2.py: render_product prepatch bug — drops the `neg` leading minus (re-encodes model_prepatch_2.py). same-spec=SAME, verifies=NO. Fails post matmul.
- atk_3.py: render_sum_space ungrounded-oracle echo — decides on `is_neg(t)` (rendered text) instead of the structural boolean `n=negs[i-1]`. same-spec=SAME, verifies=NO. This is the G-PANEL-2 faithfulness rival; spec rejects it (confirms negs[k] correspondence is enforced).
- atk_4.py: render_sum_space str-discipline — uses `contrib(t)` (' - ' + minus-strip) instead of contrib_space (re-encodes model_prepatch_3 discipline swap / G-PBT weak-space-as-str-discipline). same-spec=SAME, verifies=NO.
- atk_5.py: render_sum boundary — first term `body(t0)` instead of `lead(t0)`, dropping the leading minus on a negative first term. same-spec=SAME, verifies=NO.
- atk_6.py: render_product control-flow-effect — prepend minus only when `neg and len(factors)>1` (single-factor product loses sign). same-spec=SAME, verifies=NO.
- atk_7.py: render_sum partial-domain — special-case `len(terms)==1` returns `body(terms[0])` (drops minus). same-spec=SAME, verifies=NO.

POSITIVE CONTROL: pos_control.py (= bundle model.py) VERIFIES via `bash scripts/nagini_verify.sh` (exit 0, "Verification successful", 12.5s).

No attack returned a CANDIDATE (none shares spec AND verifies), so per protocol no faithful refined patch needed materialization and no run_resolve was triggered. prepatch_reproduced=true: atk_1/atk_2/atk_3 re-encode the three documented prepatch bugs (model_prepatch{,_2,_3}.py) and all correctly fail to verify.

A-LEG / MODEL-CORRESPONDENCE AUDIT: meta.json shows axioms=[] and deep_model_references=[] — there are genuinely NO axiomatized callees (@ContractOnly), so refinement.md correctly has no A-consumed/A-reference legs and no kind-3 step. Every leg is R (rendered-child str <-> PSeq[int] code points; child render and the structural negativity/coefficient tests carried as boolean inputs `neg`/`negs`, a legitimate input-refinement of consumed-not-changed facts) or I (identical concrete op: ' - '/' + '/'*'/leading '-'). Verified against patch.diff (byte-checked: str/latex _print_MatAdd sign-aware join, str/latex _print_MatMul leading-sign, pretty _print_MatAdd single-space structural-negativity join). The subtle correspondence pretty negs[k] == S(item.args[0]).is_negative (NOT is_neg on rendered text) is the correct callee semantics — atk_3 confirms the spec REJECTS the text-decided rival, and atk_4 confirms it rejects the str-discipline rival, so render_sum_space genuinely pins the distinct pretty algorithm. §C cross-file dispositions (latex._print_MatAdd byte-identical R of matadd; latex._print_MatMul same-shape R of matmul) hold.

The spec pins each function output as EXACT equality (Ensures ToSeq(Result())==matadd/matadd_space/matmul(...)) over totally-quantified preconditions, so verify => output byte-identical to the gold fold on every tested site => the gold patch (correctness oracle, G-RESOLVE) resolves. Refinement fidelity holds; no verifying wrong impl exists among the 7 distinct falsification attempts. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness assessment of the sympy__sympy-14248 nagini bundle. The model specifies three distinct rendering behaviours as deep front-recursive folds and binds them to the real patched repo callees (mapping.md §1): render_sum → StrPrinter._print_MatAdd (spaced-binary-minus join, minus stripped), render_product → StrPrinter._print_MatMul (leading-'-' on negative numeric coefficient), render_sum_space → PrettyPrinter._print_MatAdd (single-space join keyed on the STRUCTURAL fact S(item.args[0]).is_negative, term kept whole).

Key subtlety handled correctly: the pretty site's separator decision is the structural test S(item.args[0]).is_negative, NOT the rendered text. The model faithfully carries this as a boolean INPUT (negs[k]) rather than an is_neg(t) test on the term text — the earlier is_neg abstraction was already caught and rejected (documented in mapping.md §2.2 / refinement.md §A2), and the divergence witness -A + y*B (y negative) confirms text-vs-structural disagreement is respected. Likewise render_product carries neg as a boolean input for the coefficient-normalised factor list.

Verification performed on the real repo at base_commit 9986b38 with the gold patch applied (python3.8):
- Rebuilt the model's shadow (byte-exact impl regions) and the conformance type-bridge independently.
- Targeted edge probes: coefficients I, pi, sqrt(2), rationals, floats, assumption symbols (negative/positive/unknown sign), S(0), single-child sums/products, -1 folding. The real repo RAISES TypeError on complex coeffs (I) — both sides raise, so no string divergence (repo behaviour, not spec drift).
- Independent fuzz with a DIFFERENT seed (20260812) and an enlarged coefficient pool: 200000 sum inputs (check_sum), 200000 sum inputs (check_space), 177451 product inputs (check_prod). ZERO disagreements between the modeled functions and the real callees.
- This is on top of the recorded G-CONF pass (105000 inputs, seed 1424814248, 0 disagreements).

The pure specs (matadd, matmul) are byte-exact translations of the real Python join/sign logic under the code-point refinement, so they cannot diverge from the real callee on the modeled inputs; the only non-trivial abstraction (structural negativity as an input) is faithfully modeled. model.py verifies under pinned Nagini (12.73s). same-spec identity check passes. No diverging input found; the spec is not too strong and does not drift from real repo behaviour. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: the consumer-facing spec view is derived purely from model.py via markers.spec_view(model.py, nagini) — I regenerated it and confirmed all three impl regions are elided ('...  # implementation elided — supplied by the consumer') so no implementation code is disclosed. mapping.md/refinement.md (which carry the verbatim gold hunks, file:line refs like str.py:314, and internal APIs _print_MatAdd/as_coeff_mmul/_keep_coeff/S(item.args[0]).is_negative/stringPict) are separate audit artifacts, NOT part of the spec view, so they are out of scope for this gate.

Public problem_statement already discloses: the bug (MatrixSymbol differences print with (-1) coefficient / '+ -B' style), all THREE affected printers by name (str, pretty, latex), the intended behaviour ('supposed to print like a-b'), and the concrete wrong outputs for A - A*B - B in each printer.

The spec view describes the three target behaviours — (1) spaced binary-minus sum join with the leading minus stripped; (2) matrix-product leading-sign extraction; (3) single-space sum join keyed on a structural-negativity boolean — but ENTIRELY in the model's own abstract vocabulary (PSeq[int] code points, terms/factors, front-recursive folds). It never names any sympy file, function, line, or internal API, never reproduces gold-patch code or identifiers, and explicitly frames everything as 'desired behaviour, not as an edit'.

The only non-obvious detail is behaviour (3)'s note that the negativity decision is a STRUCTURAL test on the expression tree (a term may be structurally negative yet render with no leading minus, e.g. a negative-assumption symbol coefficient). This is an abstract behavioural specification — precisely pinning target behaviour is the spec's proper job — and does NOT reconstruct the gold edit: a solver still must locate the three functions and discover the actual APIs (is_negative, as_coeff_mmul, _keep_coeff, stringPict) unaided. Naming the three printers and the 'print like a-b' goal is already public in the problem_statement.

No spec-view line discloses solution specifics (code, paths, symbols, or edit locations) beyond what the problem_statement already makes public. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
