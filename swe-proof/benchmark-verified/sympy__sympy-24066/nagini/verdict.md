# P2 adversarial audit — sympy__sympy-24066

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.py`, `atk2_swap.py`, `atk3_boundary.py`, `atk4_reversed.py`, `atk5_overcanon.py`, `atk6_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,10 +155,6 @@
         Invariant(Acc(list_pred(arg_dims), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                   resolvable(arg_dims[k])))))
         Invariant(all_resolvable(ToSeq(arg_dims)))
@@ -169,18 +165,10 @@
         c = arg_dims[i - 1]
         Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
         Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
         Assert(resolvable(c))
         Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
-        if is_dimensionless(c):
-            result = [CANON_ONE()] + result
-        else:
-            result = [c] + result
+        result = [c] + result
         i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
     Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
     Assert(all_resolvable(ToSeq(arg_dims)))
     return result
```

Attack 2 — `atk2_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,10 +155,6 @@
         Invariant(Acc(list_pred(arg_dims), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                   resolvable(arg_dims[k])))))
         Invariant(all_resolvable(ToSeq(arg_dims)))
@@ -167,21 +163,12 @@
         Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
         # invariants-end
         c = arg_dims[i - 1]
-        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
-        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
         Assert(resolvable(c))
         Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
         if is_dimensionless(c):
+            result = [c] + result
+        else:
             result = [CANON_ONE()] + result
-        else:
-            result = [c] + result
         i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
-    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
-    Assert(all_resolvable(ToSeq(arg_dims)))
     return result
     # impl-end
```

Attack 3 — `atk3_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -150,38 +150,21 @@
     # impl-start
     result = []  # type: List[int]
     i = len(arg_dims)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(arg_dims), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
+        Invariant(1 <= i and i <= len(arg_dims))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                   resolvable(arg_dims[k])))))
         Invariant(all_resolvable(ToSeq(arg_dims)))
-        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
-        Invariant(len(result) == len(arg_dims) - i)
-        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
         # invariants-end
         c = arg_dims[i - 1]
-        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
-        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
         Assert(resolvable(c))
-        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
         if is_dimensionless(c):
             result = [CANON_ONE()] + result
         else:
             result = [c] + result
         i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
-    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
-    Assert(all_resolvable(ToSeq(arg_dims)))
     return result
     # impl-end
```

Attack 4 — `atk4_reversed.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,33 +155,16 @@
         Invariant(Acc(list_pred(arg_dims), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                   resolvable(arg_dims[k])))))
         Invariant(all_resolvable(ToSeq(arg_dims)))
-        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
-        Invariant(len(result) == len(arg_dims) - i)
-        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
         # invariants-end
         c = arg_dims[i - 1]
-        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
-        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
         Assert(resolvable(c))
-        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
         if is_dimensionless(c):
-            result = [CANON_ONE()] + result
+            result = result + [CANON_ONE()]
         else:
-            result = [c] + result
+            result = result + [c]
         i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
-    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
-    Assert(all_resolvable(ToSeq(arg_dims)))
     return result
     # impl-end
```

Attack 5 — `atk5_overcanon.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,33 +155,12 @@
         Invariant(Acc(list_pred(arg_dims), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                   resolvable(arg_dims[k])))))
         Invariant(all_resolvable(ToSeq(arg_dims)))
-        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
         Invariant(len(result) == len(arg_dims) - i)
-        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
         # invariants-end
-        c = arg_dims[i - 1]
-        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
-        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
-        Assert(resolvable(c))
-        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
-        if is_dimensionless(c):
-            result = [CANON_ONE()] + result
-        else:
-            result = [c] + result
+        result = [CANON_ONE()] + result
         i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
-    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
-    Assert(all_resolvable(ToSeq(arg_dims)))
     return result
     # impl-end
```

Attack 6 — `atk6_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,39 +149,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(arg_dims)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(arg_dims), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
-                                                  resolvable(arg_dims[k])))))
-        Invariant(all_resolvable(ToSeq(arg_dims)))
-        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
-        Invariant(len(result) == len(arg_dims) - i)
-        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
-        # invariants-end
-        c = arg_dims[i - 1]
-        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
-        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
-        Assert(resolvable(c))
-        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
-        if is_dimensionless(c):
-            result = [CANON_ONE()] + result
-        else:
-            result = [c] + result
-        i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
-    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
-    Assert(all_resolvable(ToSeq(arg_dims)))
     return result
     # impl-end
```

Attack 7 — `atk7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -155,10 +155,6 @@
         Invariant(Acc(list_pred(arg_dims), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(arg_dims))
-        # Every argument dimension code has a dimensionless verdict (the modeled
-        # domain), so each per-element test and the canonicalisation fold below
-        # are well-defined. Kept in both views: element-wise (per-element test)
-        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                   resolvable(arg_dims[k])))))
         Invariant(all_resolvable(ToSeq(arg_dims)))
@@ -169,18 +165,10 @@
         c = arg_dims[i - 1]
         Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
         Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
-        # c is resolvable (element-wise view), so the per-element test below is
-        # defined; and the suffix one longer is all-resolvable (fold view), which
-        # is canon_seq's domain for the next iteration.
         Assert(resolvable(c))
         Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
-        if is_dimensionless(c):
-            result = [CANON_ONE()] + result
-        else:
-            result = [c] + result
+        result = [canon_dim(c)] + result
         i = i - 1
-    # At exit i == 0: the processed suffix is the whole sequence, whose domain
-    # and canonicalisation are exactly those of arg_dims.
     Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
     Assert(all_resolvable(ToSeq(arg_dims)))
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-24066.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the scale factor and the dimension of an expression are collected for a
  unit-bearing applied function (a function symbol applied to a list of
  argument expressions), the dimension reported for each argument must be in
  canonical form: an argument whose dimension is dimensionless must be reported
  with the canonical dimensionless dimension, the one whose name is the unit 1,
  rather than with whatever (possibly non-canonical) dimension expression the
  argument happened to carry. Any argument whose dimension is genuinely NOT
  dimensionless is reported with its own dimension, unchanged.

  This matters because a dimensionless dimension may be carried in a
  non-canonical form (a product/quotient of base dimensions whose net powers all
  cancel) that is structurally unequal to the canonical dimensionless dimension.
  Downstream, two dimensions are compared for structural equality (e.g. when a
  sum requires all addends to share one dimension); a dimensionless argument
  dimension that is not first reduced to the canonical form would compare
  unequal to the canonical dimensionless dimension and be rejected, even though
  it IS dimensionless. Canonicalising each dimensionless argument dimension to
  the canonical form makes that comparison succeed.

Dimensions are abstracted by integer "dimension codes": the canonical
dimensionless dimension (the one whose name is the unit 1) is the distinguished
code ``CANON_ONE``; every other code denotes some other dimension expression. A
code may denote a dimension that is dimensionless yet non-canonical (a code
different from ``CANON_ONE`` for which the dimension system nonetheless reports
dimensionless). Whether a code denotes a dimensionless dimension is decided by
the dimension system, modelled by the unchanged ``is_dimensionless`` callee.

The argument dimensions are a ``List[int]`` of codes; the result is the parallel
``List[int]`` of canonicalised codes (the scale-factor component, which is
unchanged, is not modelled). The structural correspondence to a sum's
all-addends-equal comparison is pinned by the canonical-equality clause.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolvable(code: int) -> bool:
    """Whether the dimension system can compute the dimensional dependencies of
    the dimension denoted by this code WITHOUT signalling an error — i.e. the
    sub-domain on which the dimensionless test below produces a verdict at all.
    The dimensionless test is only a partial predicate: a code that denotes a
    dimension whose dependencies cannot be resolved (a dimension built from
    incompatible or non-resolvable components) has no dimensionless verdict, and
    consulting it for one is a domain error. This opaque predicate carves out the
    domain on which the verdict exists; only codes for which it holds are fed to
    the test. Provenance + executable soundness check: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def is_dimensionless(code: int) -> bool:
    """The dimension system's dimensionless test on a dimension, here on the
    dimension's integer code (the unchanged community callee
    ``get_dimension_system().is_dimensionless``). It is a PARTIAL opaque
    predicate, defined only where the dimension's dependencies are resolvable
    (``resolvable(code)``); outside that domain the dimension system signals a
    domain error rather than returning a verdict, so the test is not invoked
    there. Within its domain the verdict is whatever the dimension system
    decides — a code may denote a dimensionless dimension yet differ from the
    canonical code ``CANON_ONE`` (a non-canonical dimensionless dimension). The
    proof relies on no particular verdict, only that the SAME code yields the
    SAME verdict at every site (function purity). Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    Requires(resolvable(code))
# axioms-end


# pure-start
@Pure
def CANON_ONE() -> int:
    """The code of the canonical dimensionless dimension — the dimension whose
    name is the unit 1. Distinguished so that the result can be compared for
    structural equality against it."""
    return 1


@Pure
def all_resolvable(s: PSeq[int]) -> bool:
    """Whether every code in the sequence has a dimensionless verdict (each is
    ``resolvable``) — the domain on which the whole-sequence canonicalisation is
    defined. Front-recursive so a single unfold exposes the head's resolvability
    and the tail's, matching the canonicalisation fold step-for-step."""
    if len(s) == 0:
        return True
    return resolvable(s[0]) and all_resolvable(s.drop(1))


@Pure
def canon_dim(code: int) -> int:
    """The canonicalised dimension code for one argument: the canonical
    dimensionless code when the argument's dimension is dimensionless, otherwise
    the argument's own code unchanged. Defined only on the domain where the
    dimensionless verdict exists (``resolvable(code)``)."""
    Requires(resolvable(code))
    if is_dimensionless(code):
        return CANON_ONE()
    return code


@Pure
def canon_seq(s: PSeq[int]) -> PSeq[int]:
    """The canonicalisation of a whole sequence of argument dimension codes:
    canonicalise each code. Front-recursive so a single unfold is available to
    callers per loop step. Defined only when every code has a dimensionless
    verdict (``all_resolvable``)."""
    Requires(all_resolvable(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(canon_dim(s[0])) + canon_seq(s.drop(1))
# pure-end


def collect_argument_dimensions(arg_dims: List[int]) -> List[int]:
    # pre-conditions-start
    # Read-only input: the argument dimension codes are not mutated, so they are
    # held at fractional permission, required AND ensured (directive 5).
    Requires(Acc(list_pred(arg_dims), 1 / 2))
    # The dimensionless test is partial: it has a verdict only for codes whose
    # dimensional dependencies resolve. Within the modeled domain every argument
    # dimension is such a code, so the per-element test is always well-defined;
    # codes outside this domain are not handled here (the test would signal a
    # domain error, not a verdict). Stated both element-wise (for the per-element
    # test) and as the fold-shaped ``all_resolvable`` (the domain of the
    # whole-sequence canonicalisation) — two views of the same total domain.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                             resolvable(arg_dims[k])))))
    Requires(all_resolvable(ToSeq(arg_dims)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(arg_dims), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The read-only input is unchanged, so its codes still all have a
    # dimensionless verdict — the domain on which the canonicalisation below is
    # defined (carries the precondition's well-definedness to the post-state).
    Ensures(all_resolvable(ToSeq(arg_dims)))
    # The result is the parallel list of per-argument canonicalised codes,
    # the per-element canonicalisation of the input.
    Ensures(len(Result()) == len(arg_dims))
    Ensures(ToSeq(Result()) == canon_seq(ToSeq(arg_dims)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(arg_dims)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(arg_dims), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(arg_dims))
        # Every argument dimension code has a dimensionless verdict (the modeled
        # domain), so each per-element test and the canonicalisation fold below
        # are well-defined. Kept in both views: element-wise (per-element test)
        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                  resolvable(arg_dims[k])))))
        Invariant(all_resolvable(ToSeq(arg_dims)))
        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
        Invariant(len(result) == len(arg_dims) - i)
        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
        # invariants-end
        c = arg_dims[i - 1]
        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
        # c is resolvable (element-wise view), so the per-element test below is
        # defined; and the suffix one longer is all-resolvable (fold view), which
        # is canon_seq's domain for the next iteration.
        Assert(resolvable(c))
        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
        if is_dimensionless(c):
            result = [CANON_ONE()] + result
        else:
            result = [c] + result
        i = i - 1
    # At exit i == 0: the processed suffix is the whole sequence, whose domain
    # and canonicalisation are exactly those of arg_dims.
    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
    Assert(all_resolvable(ToSeq(arg_dims)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for nagini sympy__sympy-24066. Focused on the A-legs and model<->patch correspondence (R/I legs mechanically covered by G-CONF).

SPEC SHAPE: collect_argument_dimensions carries a TOTAL FUNCTIONAL postcondition: Ensures(len(Result())==len(arg_dims)) AND Ensures(ToSeq(Result())==canon_seq(ToSeq(arg_dims))) with full list_pred(Result()) ownership. canon_seq is the front-recursive fold of canon_dim over the input, so the output is pinned UNIQUELY for every input in the modeled (all_resolvable) domain. This is why verify=>correct is expected to hold, and every genuinely-wrong impl must fail verification.

SAME-SPEC: all 7 attacks + positive control return SAME (spec_signature byte-identical); only the impl region was edited in each.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini sympy__sympy-24066 <path>):
- atk_prepatch.py (PREPATCH BUG, report verbatim `result=[c]+result`): verification FAILED (postcondition/invariant ToSeq(result)==canon_seq(...) violated) -> rejected, exit 2. Prepatch reproduced.
- atk2_swap.py (branch swap: canonicalise the NON-dimensionless, verbatim the dimensionless): FAILED verify -> rejected, exit 2.
- atk3_boundary.py (off-by-one, `while i>1` skips first element): FAILED verify -> rejected, exit 2.
- atk4_reversed.py (control-flow-effect: `result+[..]` backward loop => reversed order): FAILED verify -> rejected, exit 2.
- atk5_overcanon.py (ungrounded-oracle echo: always emit CANON_ONE regardless of is_dimensionless): FAILED verify -> rejected, exit 2.
- atk6_empty.py (partial-domain/constant: return []): FAILED verify (len postcondition) -> rejected, exit 2.
- atk7_echo.py (CORRECT-BUT-DIFFERENT: emit `[canon_dim(c)]+result`, the deep-model call directly): CANDIDATE — shares spec AND verifies (13.7s).

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> Verification successful (13.34s).

MANDATORY RESOLVE OF THE VERIFYING CANDIDATE: atk7_echo computes exactly canon_dim per element (Dimension(1) if is_dimensionless(d[1]) else d[1]), i.e. the gold Function-branch rule, so its faithful refined patch = the gold hunk (atk7_echo.patch). Executed run_resolve('sympy__sympy-24066', patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. FAIL_TO_PASS test_issue_24062 success; PASS_TO_PASS 30/30 success. The only verifying candidate RESOLVES — the spec does NOT admit an incorrect implementation.

REFINEMENT.MD / A-LEG AUDIT: Section C confirms no kind-3 (unexpressible-changed-op) legs; every leg is R / A-consumed / A-reference / I. A2 (is_dimensionless) is A-consumed over the UNCHANGED community callee DimensionSystem.is_dimensionless; its partiality is modeled by the opaque resolvable() domain predicate (Requires(resolvable(code))), and axiom_check.py raise-surface fuzz confirms the real callee raises TypeError exactly off that domain (Dimension(length+mass), Dimension(sin(length)), etc.) and returns a bool on the three resolvable regimes. A3/A5 (canon_dim/canon_seq) are A-references validated == the real gold Function branch element `Dimension(1) if is_dimensionless(d[1]) else d[1]` — the atk7 resolve corroborates that correspondence end-to-end (produces (1+E, Dimension(1))). A1/A4/A6 are R/I (code<->Dimension bijection; verbatim else-branch; unmodeled unchanged head). Correspondence to the real callees holds.

VERDICT: SOUND. 7 attacks encoded and fully verified; 6 wrong impls rejected by verification, the sole verifying candidate's materialized faithful patch was executed through the official harness and RESOLVED. No verifying-but-nonresolving impl exists; verify does not admit an incorrect implementation for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.py`, `atk2_swap.py`, `atk3_boundary.py`, `atk4_reversed.py`, `atk5_overcanon.py`, `atk6_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_swap.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_boundary.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_reversed.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_overcanon.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_empty.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-24066.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the scale factor and the dimension of an expression are collected for a
  unit-bearing applied function (a function symbol applied to a list of
  argument expressions), the dimension reported for each argument must be in
  canonical form: an argument whose dimension is dimensionless must be reported
  with the canonical dimensionless dimension, the one whose name is the unit 1,
  rather than with whatever (possibly non-canonical) dimension expression the
  argument happened to carry. Any argument whose dimension is genuinely NOT
  dimensionless is reported with its own dimension, unchanged.

  This matters because a dimensionless dimension may be carried in a
  non-canonical form (a product/quotient of base dimensions whose net powers all
  cancel) that is structurally unequal to the canonical dimensionless dimension.
  Downstream, two dimensions are compared for structural equality (e.g. when a
  sum requires all addends to share one dimension); a dimensionless argument
  dimension that is not first reduced to the canonical form would compare
  unequal to the canonical dimensionless dimension and be rejected, even though
  it IS dimensionless. Canonicalising each dimensionless argument dimension to
  the canonical form makes that comparison succeed.

Dimensions are abstracted by integer "dimension codes": the canonical
dimensionless dimension (the one whose name is the unit 1) is the distinguished
code ``CANON_ONE``; every other code denotes some other dimension expression. A
code may denote a dimension that is dimensionless yet non-canonical (a code
different from ``CANON_ONE`` for which the dimension system nonetheless reports
dimensionless). Whether a code denotes a dimensionless dimension is decided by
the dimension system, modelled by the unchanged ``is_dimensionless`` callee.

The argument dimensions are a ``List[int]`` of codes; the result is the parallel
``List[int]`` of canonicalised codes (the scale-factor component, which is
unchanged, is not modelled). The structural correspondence to a sum's
all-addends-equal comparison is pinned by the canonical-equality clause.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolvable(code: int) -> bool:
    """Whether the dimension system can compute the dimensional dependencies of
    the dimension denoted by this code WITHOUT signalling an error — i.e. the
    sub-domain on which the dimensionless test below produces a verdict at all.
    The dimensionless test is only a partial predicate: a code that denotes a
    dimension whose dependencies cannot be resolved (a dimension built from
    incompatible or non-resolvable components) has no dimensionless verdict, and
    consulting it for one is a domain error. This opaque predicate carves out the
    domain on which the verdict exists; only codes for which it holds are fed to
    the test. Provenance + executable soundness check: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def is_dimensionless(code: int) -> bool:
    """The dimension system's dimensionless test on a dimension, here on the
    dimension's integer code (the unchanged community callee
    ``get_dimension_system().is_dimensionless``). It is a PARTIAL opaque
    predicate, defined only where the dimension's dependencies are resolvable
    (``resolvable(code)``); outside that domain the dimension system signals a
    domain error rather than returning a verdict, so the test is not invoked
    there. Within its domain the verdict is whatever the dimension system
    decides — a code may denote a dimensionless dimension yet differ from the
    canonical code ``CANON_ONE`` (a non-canonical dimensionless dimension). The
    proof relies on no particular verdict, only that the SAME code yields the
    SAME verdict at every site (function purity). Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    Requires(resolvable(code))
# axioms-end


# pure-start
@Pure
def CANON_ONE() -> int:
    """The code of the canonical dimensionless dimension — the dimension whose
    name is the unit 1. Distinguished so that the result can be compared for
    structural equality against it."""
    return 1


@Pure
def all_resolvable(s: PSeq[int]) -> bool:
    """Whether every code in the sequence has a dimensionless verdict (each is
    ``resolvable``) — the domain on which the whole-sequence canonicalisation is
    defined. Front-recursive so a single unfold exposes the head's resolvability
    and the tail's, matching the canonicalisation fold step-for-step."""
    if len(s) == 0:
        return True
    return resolvable(s[0]) and all_resolvable(s.drop(1))


@Pure
def canon_dim(code: int) -> int:
    """The canonicalised dimension code for one argument: the canonical
    dimensionless code when the argument's dimension is dimensionless, otherwise
    the argument's own code unchanged. Defined only on the domain where the
    dimensionless verdict exists (``resolvable(code)``)."""
    Requires(resolvable(code))
    if is_dimensionless(code):
        return CANON_ONE()
    return code


@Pure
def canon_seq(s: PSeq[int]) -> PSeq[int]:
    """The canonicalisation of a whole sequence of argument dimension codes:
    canonicalise each code. Front-recursive so a single unfold is available to
    callers per loop step. Defined only when every code has a dimensionless
    verdict (``all_resolvable``)."""
    Requires(all_resolvable(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(canon_dim(s[0])) + canon_seq(s.drop(1))
# pure-end


def collect_argument_dimensions(arg_dims: List[int]) -> List[int]:
    # pre-conditions-start
    # Read-only input: the argument dimension codes are not mutated, so they are
    # held at fractional permission, required AND ensured (directive 5).
    Requires(Acc(list_pred(arg_dims), 1 / 2))
    # The dimensionless test is partial: it has a verdict only for codes whose
    # dimensional dependencies resolve. Within the modeled domain every argument
    # dimension is such a code, so the per-element test is always well-defined;
    # codes outside this domain are not handled here (the test would signal a
    # domain error, not a verdict). Stated both element-wise (for the per-element
    # test) and as the fold-shaped ``all_resolvable`` (the domain of the
    # whole-sequence canonicalisation) — two views of the same total domain.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                             resolvable(arg_dims[k])))))
    Requires(all_resolvable(ToSeq(arg_dims)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(arg_dims), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The read-only input is unchanged, so its codes still all have a
    # dimensionless verdict — the domain on which the canonicalisation below is
    # defined (carries the precondition's well-definedness to the post-state).
    Ensures(all_resolvable(ToSeq(arg_dims)))
    # The result is the parallel list of per-argument canonicalised codes,
    # the per-element canonicalisation of the input.
    Ensures(len(Result()) == len(arg_dims))
    Ensures(ToSeq(Result()) == canon_seq(ToSeq(arg_dims)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(arg_dims)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(arg_dims), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(arg_dims))
        # Every argument dimension code has a dimensionless verdict (the modeled
        # domain), so each per-element test and the canonicalisation fold below
        # are well-defined. Kept in both views: element-wise (per-element test)
        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                  resolvable(arg_dims[k])))))
        Invariant(all_resolvable(ToSeq(arg_dims)))
        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
        Invariant(len(result) == len(arg_dims) - i)
        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
        # invariants-end
        c = arg_dims[i - 1]
        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
        # c is resolvable (element-wise view), so the per-element test below is
        # defined; and the suffix one longer is all-resolvable (fold view), which
        # is canon_seq's domain for the next iteration.
        Assert(resolvable(c))
        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
        if is_dimensionless(c):
            result = [CANON_ONE()] + result
        else:
            result = [c] + result
        i = i - 1
    # At exit i == 0: the processed suffix is the whole sequence, whose domain
    # and canonicalisation are exactly those of arg_dims.
    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
    Assert(all_resolvable(ToSeq(arg_dims)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for nagini sympy__sympy-24066. Focused on the A-legs and model<->patch correspondence (R/I legs mechanically covered by G-CONF).

SPEC SHAPE: collect_argument_dimensions carries a TOTAL FUNCTIONAL postcondition: Ensures(len(Result())==len(arg_dims)) AND Ensures(ToSeq(Result())==canon_seq(ToSeq(arg_dims))) with full list_pred(Result()) ownership. canon_seq is the front-recursive fold of canon_dim over the input, so the output is pinned UNIQUELY for every input in the modeled (all_resolvable) domain. This is why verify=>correct is expected to hold, and every genuinely-wrong impl must fail verification.

SAME-SPEC: all 7 attacks + positive control return SAME (spec_signature byte-identical); only the impl region was edited in each.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini sympy__sympy-24066 <path>):
- atk_prepatch.py (PREPATCH BUG, report verbatim `result=[c]+result`): verification FAILED (postcondition/invariant ToSeq(result)==canon_seq(...) violated) -> rejected, exit 2. Prepatch reproduced.
- atk2_swap.py (branch swap: canonicalise the NON-dimensionless, verbatim the dimensionless): FAILED verify -> rejected, exit 2.
- atk3_boundary.py (off-by-one, `while i>1` skips first element): FAILED verify -> rejected, exit 2.
- atk4_reversed.py (control-flow-effect: `result+[..]` backward loop => reversed order): FAILED verify -> rejected, exit 2.
- atk5_overcanon.py (ungrounded-oracle echo: always emit CANON_ONE regardless of is_dimensionless): FAILED verify -> rejected, exit 2.
- atk6_empty.py (partial-domain/constant: return []): FAILED verify (len postcondition) -> rejected, exit 2.
- atk7_echo.py (CORRECT-BUT-DIFFERENT: emit `[canon_dim(c)]+result`, the deep-model call directly): CANDIDATE — shares spec AND verifies (13.7s).

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> Verification successful (13.34s).

MANDATORY RESOLVE OF THE VERIFYING CANDIDATE: atk7_echo computes exactly canon_dim per element (Dimension(1) if is_dimensionless(d[1]) else d[1]), i.e. the gold Function-branch rule, so its faithful refined patch = the gold hunk (atk7_echo.patch). Executed run_resolve('sympy__sympy-24066', patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. FAIL_TO_PASS test_issue_24062 success; PASS_TO_PASS 30/30 success. The only verifying candidate RESOLVES — the spec does NOT admit an incorrect implementation.

REFINEMENT.MD / A-LEG AUDIT: Section C confirms no kind-3 (unexpressible-changed-op) legs; every leg is R / A-consumed / A-reference / I. A2 (is_dimensionless) is A-consumed over the UNCHANGED community callee DimensionSystem.is_dimensionless; its partiality is modeled by the opaque resolvable() domain predicate (Requires(resolvable(code))), and axiom_check.py raise-surface fuzz confirms the real callee raises TypeError exactly off that domain (Dimension(length+mass), Dimension(sin(length)), etc.) and returns a bool on the three resolvable regimes. A3/A5 (canon_dim/canon_seq) are A-references validated == the real gold Function branch element `Dimension(1) if is_dimensionless(d[1]) else d[1]` — the atk7 resolve corroborates that correspondence end-to-end (produces (1+E, Dimension(1))). A1/A4/A6 are R/I (code<->Dimension bijection; verbatim else-branch; unmodeled unchanged head). Correspondence to the real callees holds.

VERDICT: SOUND. 7 attacks encoded and fully verified; 6 wrong impls rejected by verification, the sole verifying candidate's materialized faithful patch was executed through the official harness and RESOLVED. No verifying-but-nonresolving impl exists; verify does not admit an incorrect implementation for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/spec-too-strong audit on nagini sympy__sympy-24066. Modeled function collect_argument_dimensions models the gold Function branch of UnitSystem._collect_factor_and_dimension (unitsystem.py:192-196 post-patch). Postcondition ToSeq(Result())==canon_seq(ToSeq(arg_dims)) with len preserved encodes the element-wise rule canon_dim(d)=CANON_ONE()(==Dimension(1)) if is_dimensionless(d) else d.

Empirical validation against the REAL gold-patched repo: cp'd the base worktree (@ base_commit 514579c655, confirmed unpatched) to and applied the gold hunk. Compared the modeled rule vs the real _collect_factor_and_dimension across all three dimension regimes (canonical dimensionless Dimension(1); non-canonical-but-dimensionless time/(capacitance*impedance), (T/(R*C))**2, R*C/T; genuine length/mass/current/products/powers), single/multi/empty-arg, mixed orderings and repeats: 14 targeted cases + 2000 randomized cases (n=0..8) + the bundle's own conformance_check.py = 100,024 inputs (seed=24066). ZERO divergences in every run; empty-args yields (). No diverging input found.

Domain fidelity: resolvable/all_resolvable are PRECONDITIONS narrowing to inputs where the real callee returns a verdict (no TypeError). This models the real callee's partiality (axiom_check confirms is_dimensionless raises TypeError exactly off that domain: Dimension(length+mass), Dimension(sin(length)), etc.). A strengthened precondition cannot render the postcondition too strong on the callee's actual domain.

Corroborating: bash scripts/nagini_verify.sh model.py -> Verification successful (12.35s); conformance_check.py exit 0 on the gold tree (100024 inputs, 0 disagreements). The spec is FAITHFUL and NOT too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity verified: recomputed markers.spec_view(model.py, nagini) hashes to e482d68d289e957f3dee773e9f2f457d552882a71e2183e60b73aeed8c8d461a, byte-identical to the recorded region_hashes.spec_view; the impl region is fully elided ('... implementation elided — supplied by the consumer'). Leakage judged against the PUBLIC problem_statement only (hints_text empty).

The public issue 'SI._collect_factor_and_dimension() cannot properly detect that exponent is dimensionless' already discloses every discriminating fact the spec view carries: (1) the function under change SI._collect_factor_and_dimension(); (2) the failing regime exp(second/(ohm*farad)) — a Function applied to a dimensionless argument; (3) the canonical test SI.get_dimension_system().is_dimensionless(dim)==True; (4) the concrete non-canonical form Dimension(time/(capacitance*impedance)) (a quotient whose net powers cancel); (5) the required output 'should be Dimension(1)' (canonical dimensionless, name 1); (6) the downstream 100+exp(expr) -> ValueError (Add / structural-equality failure).

The spec view (docstring + axioms/pure/pre/post) only restates this desired observable behaviour through a generic integer 'dimension code' abstraction: canonicalise a dimensionless argument dimension to CANON_ONE()==1, report a non-dimensionless argument verbatim, postcondition ToSeq(Result())==canon_seq(ToSeq(arg_dims)) with length preserved, plus the partial is_dimensionless/resolvable domain modelling. Encoding the target behaviour is intrinsic to any spec and is not leakage; the 'non-dimensionless reported verbatim' clause is the only correct behaviour, not gold-specific solution info.

The spec view does NOT reveal edit location or code beyond the public issue: it never names sympy/physics/units/unitsystem.py, never cites the patched lines (192-196), and never reproduces the gold list comprehension [Dimension(1) if ...is_dimensionless(d[1]) else d[1] for d in fds]. That gold-edit provenance (file:line, verbatim hunk) lives only in mapping.md / refinement.md, which are NOT part of the consumer spec view. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
