# P2 adversarial audit — sympy__sympy-13551

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -93,23 +91,30 @@
     Ensures(Result() == prod_of_totals(ToSeq(base), ToSeq(comp)))
     # post-conditions-end
     # impl-start
-    result = 1
+    pb = 1
     i = len(base)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(comp), 1 / 2))
         Invariant(len(base) == len(comp))
         Invariant(0 <= i and i <= len(base))
-        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
-                                           ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(pb == prod_one(ToSeq(base).drop(i)))
         Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
-        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
         Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
-        result = (base[i - 1] + comp[i - 1]) * result
+        pb = base[i - 1] * pb
         i = i - 1
+    pc = 1
+    j = len(comp)
+    while j > 0:
+        Invariant(Acc(list_pred(base), 1 / 2))
+        Invariant(Acc(list_pred(comp), 1 / 2))
+        Invariant(len(base) == len(comp))
+        Invariant(0 <= j and j <= len(comp))
+        Invariant(pc == prod_one(ToSeq(comp).drop(j)))
+        Assert(ToSeq(comp).drop(j - 1)[0] == comp[j - 1])
+        Assert(ToSeq(comp).drop(j - 1).drop(1) == ToSeq(comp).drop(j))
+        pc = comp[j - 1] * pc
+        j = j - 1
+    result = pb + pc
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -94,22 +92,5 @@
     # post-conditions-end
     # impl-start
     result = 1
-    i = len(base)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(base), 1 / 2))
-        Invariant(Acc(list_pred(comp), 1 / 2))
-        Invariant(len(base) == len(comp))
-        Invariant(0 <= i and i <= len(base))
-        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
-                                           ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
-        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
-        result = (base[i - 1] + comp[i - 1]) * result
-        i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -95,16 +93,13 @@
     # impl-start
     result = 1
     i = len(base)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(comp), 1 / 2))
         Invariant(len(base) == len(comp))
-        Invariant(0 <= i and i <= len(base))
+        Invariant(1 <= i and i <= len(base))
         Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                            ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
         Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
         Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -96,20 +94,11 @@
     result = 1
     i = len(base)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(comp), 1 / 2))
         Invariant(len(base) == len(comp))
         Invariant(0 <= i and i <= len(base))
-        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
-                                           ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
-        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
         result = (base[i - 1] + comp[i - 1]) * result
-        i = i - 1
+        return result
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -96,20 +94,14 @@
     result = 1
     i = len(base)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(comp), 1 / 2))
         Invariant(len(base) == len(comp))
         Invariant(0 <= i and i <= len(base))
-        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
-                                           ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(result == prod_one(ToSeq(base).drop(i)))
         Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
-        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
         Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
-        result = (base[i - 1] + comp[i - 1]) * result
+        result = base[i - 1] * result
         i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -93,23 +91,6 @@
     Ensures(Result() == prod_of_totals(ToSeq(base), ToSeq(comp)))
     # post-conditions-end
     # impl-start
-    result = 1
-    i = len(base)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(base), 1 / 2))
-        Invariant(Acc(list_pred(comp), 1 / 2))
-        Invariant(len(base) == len(comp))
-        Invariant(0 <= i and i <= len(base))
-        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
-                                           ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
-        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
-        result = (base[i - 1] + comp[i - 1]) * result
-        i = i - 1
+    result = prod_of_totals(ToSeq(base), ToSeq(comp))
     return result
     # impl-end
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     # outside the modeled domain (mapping.md §2).
     Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                            base[i] + comp[i] != 0)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -94,22 +92,15 @@
     # post-conditions-end
     # impl-start
     result = 1
-    i = len(base)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(base):
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(comp), 1 / 2))
         Invariant(len(base) == len(comp))
         Invariant(0 <= i and i <= len(base))
-        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
-                                           ToSeq(comp).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
-        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
-        result = (base[i - 1] + comp[i - 1]) * result
-        i = i - 1
+        Invariant(result == prod_of_totals(ToSeq(base).take(i),
+                                           ToSeq(comp).take(i)))
+        result = result * (base[i] + comp[i])
+        i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Reducing a finite product whose multiplicand is a *sum* of two parts.

  Over an index that ranges across a finite set of values, the multiplicand at
  each index is the arithmetic sum of two contributions: a base contribution
  `base[i]` and a companion contribution `comp[i]`. The product being evaluated
  is therefore

        result = (base[0]+comp[0]) * (base[1]+comp[1]) * ... * (base[L-1]+comp[L-1])

  i.e. the product, over every index, of the per-index TOTAL.

  The single property that matters: the product of the per-index totals is NOT
  the same number as the total of the two per-part products
  (`prod(base) + prod(comp)`). A correct reduction multiplies the per-index
  totals together; it must not distribute the product across the two parts of
  the sum. (For example for base=[1,2], comp=[1,3] the product of totals is
  (1+1)*(2+3)=10, whereas the total of the part-products is (1*2)+(1*3)=5.)

  Domain boundary: the multiplicand is nonzero at every index. When some
  per-index total is zero the repo's reduction yields an undefined symbolic
  value rather than the integer 0, so such inputs are outside the modeled
  scenario; the precondition excludes them (mapping.md §2).

Modelling choices (Nagini fragment):
  * The index ranges over a finite set; the value the i-th part-contribution
    takes at each index is carried in a parallel `List[int]` (`base`, `comp`),
    one entry per index. A multiplicand that is a sum splits into exactly two
    such parts (a leading part and the remaining part); this binary split is the
    faithful skeleton (mapping.md / refinement.md).
  * The per-index total `base[i] + comp[i]` and its running product are spelled
    out deeply: `prod_of_totals` is a `@Pure` front-recursive fold so a single
    unfold is available to the verified loop. There is no axiom for the product
    operation -- it is modelled directly.

No string indexing is used (Nagini bans it). List access under quantifiers is
guarded by explicit in-bounds conjuncts. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def prod_of_totals(base: PSeq[int], comp: PSeq[int]) -> int:
    """Product, over every index, of the per-index TOTAL `base[i] + comp[i]`.
    Front-recursive so a single unfold is available to callers. The empty
    product is 1."""
    Requires(len(base) == len(comp))
    if len(base) == 0:
        return 1
    return (base[0] + comp[0]) * prod_of_totals(base.drop(1), comp.drop(1))


@Pure
def prod_one(xs: PSeq[int]) -> int:
    """Product of a single part's contributions across every index. Used only
    to STATE the property that distributing the product across the sum (the
    total of the two part-products) is a different number; never the answer."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod_one(xs.drop(1))
# pure-end


def product_of_sum(base: List[int], comp: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(comp), 1 / 2))
    # The two parts describe the same indices.
    Requires(len(base) == len(comp))
    # Every per-index total is nonzero: a vanishing multiplicand makes the
    # repo's reduction undefined (not the integer 0), so zero totals are
    # outside the modeled domain (mapping.md §2).
    Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                           base[i] + comp[i] != 0)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(comp), 1 / 2))
    Ensures(len(base) == len(comp))
    # The reduction returns the product of the per-index totals.
    Ensures(Result() == prod_of_totals(ToSeq(base), ToSeq(comp)))
    # post-conditions-end
    # impl-start
    result = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. All attacks copied model.py verbatim and edited ONLY the impl region (axioms/@Pure/Requires/Ensures/invariants byte-identical); all 7 attacks + positive_control confirmed same-spec exit 0 via `adversary same-spec`. Positive control = model.py impl verbatim; verifies in 11s (bash scripts/nagini_verify.sh).

The frozen postcondition `Result() == prod_of_totals(ToSeq(base), ToSeq(comp))` byte-pins the exact return value, so any faithfully-refinable wrong impl MUST be rejected; the only genuine break vector would be vacuity/unsoundness.

Command per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-13551 <path>` (run concurrently, <=3 JVMs at a time in 3 batches). Results:
- atk_1.py (PREPATCH bug: distribute product over sum -> prod_one(base)+prod_one(comp), the 9/2-vs-15/2 F2P bug): NOT-A-COUNTEREXAMPLE, does not verify (postcondition fails). prepatch_reproduced=true.
- atk_2.py (ungrounded constant: return 1, empty-product): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_3.py (boundary off-by-one: loop while i>1, skips index 0): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_4.py (control-flow-effect: early `return` inside first loop iteration): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_5.py (partial/wrong-distribution: product of base only, drops comp): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_8.py (forward-loop correct-intent variant with take()-based invariant): NOT-A-COUNTEREXAMPLE, does not verify (spec correctly demands a discharged proof).
- atk_6.py (ungrounded-oracle ECHO: `return prod_of_totals(ToSeq(base), ToSeq(comp))`): CANDIDATE (shares spec AND verifies, 12.6s). Its faithful refined patch IS the gold patch (atk_6 computes exactly the spec value = the genuine product of per-index totals = exp(Sum(log(p)))). Ran the gold/faithful patch through the OFFICIAL harness: `run_resolve('sympy__sympy-13551', <gold patch>)` -> completed=True, resolved=True, note='resolved'. => correct echo of the gold, NOT a spec weakness (per the fixed _derive_audit_verdict: a candidate whose faithful patch RESOLVES is not a weakness).

atk_7.py (`Assume(False)`) was ENCODED and run: it comes back CANDIDATE (shares spec AND verifies, 12.6s) but ONLY via `Assume(` — an explicitly BANNED verification-faking token (nagini backend banned_tokens=('Assume(','Refute('); G-HYGIENE rejects it via AST _banned_calls, confirmed: banned calls in atk_7 = ['Assume']). An Assume(False) impl fakes verification for ANY spec, corresponds to no real repo code, and has no faithful refined patch; it would trivially 'break' every bundle in the benchmark and is therefore NOT a legitimate G-EQ counterexample. I deliberately EXCLUDE it from the submitted attacks list rather than fabricate a non-resolving patch for it (which would manufacture a false BROKEN — the inverse of a rubber-stamp). It is retained on disk at atk_7.py for auditability.

refinement.md leg audit: A1/A2/A2b = R (2-tuple as_coeff_Add split -> base/comp; finite index range -> list indices; zero-total domain boundary excluded by Requires, matching real exp(zoo) undefinedness). A3 = A-reference: deep model prod_of_totals (spelled-out @Pure fold + verified loop) validated == real callee exp(Sum(log(p),(k,a,n))); NO consumed product axiom. axiom_check.py imports only sympy, asserts prod_of_totals == Product.doit / exp(Sum(log)) on 317 in-domain inputs (incl. F2P shape 1+c*2**k and negative constant parts), confirms the pre-patch sum-of-part-products differs on the discriminating witnesses, and confirms the zero-total boundary yields exp(zoo). A4 = I (unchanged `return p/q`). NO kind-3 legs. The A-reference correspondence to the real fixed callee is independently corroborated by the gold patch resolving. axioms region is empty (# axioms-start/# axioms-end) — consistent with 'deep model, no consumed axiom'.

Conclusion: >=5 genuine same-spec wrong impls run and ALL rejected by the spec; the only genuine verifying candidate (atk_6) is a correct echo whose materialized faithful patch RESOLVES under the official harness; positive control verifies; prepatch reproduced. No verifying wrong impl's faithful patch fails to resolve. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Reducing a finite product whose multiplicand is a *sum* of two parts.

  Over an index that ranges across a finite set of values, the multiplicand at
  each index is the arithmetic sum of two contributions: a base contribution
  `base[i]` and a companion contribution `comp[i]`. The product being evaluated
  is therefore

        result = (base[0]+comp[0]) * (base[1]+comp[1]) * ... * (base[L-1]+comp[L-1])

  i.e. the product, over every index, of the per-index TOTAL.

  The single property that matters: the product of the per-index totals is NOT
  the same number as the total of the two per-part products
  (`prod(base) + prod(comp)`). A correct reduction multiplies the per-index
  totals together; it must not distribute the product across the two parts of
  the sum. (For example for base=[1,2], comp=[1,3] the product of totals is
  (1+1)*(2+3)=10, whereas the total of the part-products is (1*2)+(1*3)=5.)

  Domain boundary: the multiplicand is nonzero at every index. When some
  per-index total is zero the repo's reduction yields an undefined symbolic
  value rather than the integer 0, so such inputs are outside the modeled
  scenario; the precondition excludes them (mapping.md §2).

Modelling choices (Nagini fragment):
  * The index ranges over a finite set; the value the i-th part-contribution
    takes at each index is carried in a parallel `List[int]` (`base`, `comp`),
    one entry per index. A multiplicand that is a sum splits into exactly two
    such parts (a leading part and the remaining part); this binary split is the
    faithful skeleton (mapping.md / refinement.md).
  * The per-index total `base[i] + comp[i]` and its running product are spelled
    out deeply: `prod_of_totals` is a `@Pure` front-recursive fold so a single
    unfold is available to the verified loop. There is no axiom for the product
    operation -- it is modelled directly.

No string indexing is used (Nagini bans it). List access under quantifiers is
guarded by explicit in-bounds conjuncts. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def prod_of_totals(base: PSeq[int], comp: PSeq[int]) -> int:
    """Product, over every index, of the per-index TOTAL `base[i] + comp[i]`.
    Front-recursive so a single unfold is available to callers. The empty
    product is 1."""
    Requires(len(base) == len(comp))
    if len(base) == 0:
        return 1
    return (base[0] + comp[0]) * prod_of_totals(base.drop(1), comp.drop(1))


@Pure
def prod_one(xs: PSeq[int]) -> int:
    """Product of a single part's contributions across every index. Used only
    to STATE the property that distributing the product across the sum (the
    total of the two part-products) is a different number; never the answer."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod_one(xs.drop(1))
# pure-end


def product_of_sum(base: List[int], comp: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(comp), 1 / 2))
    # The two parts describe the same indices.
    Requires(len(base) == len(comp))
    # Every per-index total is nonzero: a vanishing multiplicand makes the
    # repo's reduction undefined (not the integer 0), so zero totals are
    # outside the modeled domain (mapping.md §2).
    Requires(Forall(int, lambda i: Implies(0 <= i and i < len(base),
                                           base[i] + comp[i] != 0)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(comp), 1 / 2))
    Ensures(len(base) == len(comp))
    # The reduction returns the product of the per-index totals.
    Ensures(Result() == prod_of_totals(ToSeq(base), ToSeq(comp)))
    # post-conditions-end
    # impl-start
    result = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. All attacks copied model.py verbatim and edited ONLY the impl region (axioms/@Pure/Requires/Ensures/invariants byte-identical); all 7 attacks + positive_control confirmed same-spec exit 0 via `adversary same-spec`. Positive control = model.py impl verbatim; verifies in 11s (bash scripts/nagini_verify.sh).

The frozen postcondition `Result() == prod_of_totals(ToSeq(base), ToSeq(comp))` byte-pins the exact return value, so any faithfully-refinable wrong impl MUST be rejected; the only genuine break vector would be vacuity/unsoundness.

Command per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-13551 <path>` (run concurrently, <=3 JVMs at a time in 3 batches). Results:
- atk_1.py (PREPATCH bug: distribute product over sum -> prod_one(base)+prod_one(comp), the 9/2-vs-15/2 F2P bug): NOT-A-COUNTEREXAMPLE, does not verify (postcondition fails). prepatch_reproduced=true.
- atk_2.py (ungrounded constant: return 1, empty-product): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_3.py (boundary off-by-one: loop while i>1, skips index 0): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_4.py (control-flow-effect: early `return` inside first loop iteration): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_5.py (partial/wrong-distribution: product of base only, drops comp): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_8.py (forward-loop correct-intent variant with take()-based invariant): NOT-A-COUNTEREXAMPLE, does not verify (spec correctly demands a discharged proof).
- atk_6.py (ungrounded-oracle ECHO: `return prod_of_totals(ToSeq(base), ToSeq(comp))`): CANDIDATE (shares spec AND verifies, 12.6s). Its faithful refined patch IS the gold patch (atk_6 computes exactly the spec value = the genuine product of per-index totals = exp(Sum(log(p)))). Ran the gold/faithful patch through the OFFICIAL harness: `run_resolve('sympy__sympy-13551', <gold patch>)` -> completed=True, resolved=True, note='resolved'. => correct echo of the gold, NOT a spec weakness (per the fixed _derive_audit_verdict: a candidate whose faithful patch RESOLVES is not a weakness).

atk_7.py (`Assume(False)`) was ENCODED and run: it comes back CANDIDATE (shares spec AND verifies, 12.6s) but ONLY via `Assume(` — an explicitly BANNED verification-faking token (nagini backend banned_tokens=('Assume(','Refute('); G-HYGIENE rejects it via AST _banned_calls, confirmed: banned calls in atk_7 = ['Assume']). An Assume(False) impl fakes verification for ANY spec, corresponds to no real repo code, and has no faithful refined patch; it would trivially 'break' every bundle in the benchmark and is therefore NOT a legitimate G-EQ counterexample. I deliberately EXCLUDE it from the submitted attacks list rather than fabricate a non-resolving patch for it (which would manufacture a false BROKEN — the inverse of a rubber-stamp). It is retained on disk at atk_7.py for auditability.

refinement.md leg audit: A1/A2/A2b = R (2-tuple as_coeff_Add split -> base/comp; finite index range -> list indices; zero-total domain boundary excluded by Requires, matching real exp(zoo) undefinedness). A3 = A-reference: deep model prod_of_totals (spelled-out @Pure fold + verified loop) validated == real callee exp(Sum(log(p),(k,a,n))); NO consumed product axiom. axiom_check.py imports only sympy, asserts prod_of_totals == Product.doit / exp(Sum(log)) on 317 in-domain inputs (incl. F2P shape 1+c*2**k and negative constant parts), confirms the pre-patch sum-of-part-products differs on the discriminating witnesses, and confirms the zero-total boundary yields exp(zoo). A4 = I (unchanged `return p/q`). NO kind-3 legs. The A-reference correspondence to the real fixed callee is independently corroborated by the gold patch resolving. axioms region is empty (# axioms-start/# axioms-end) — consistent with 'deep model, no consumed axiom'.

Conclusion: >=5 genuine same-spec wrong impls run and ALL rejected by the spec; the only genuine verifying candidate (atk_6) is a correct echo whose materialized faithful patch RESOLVES under the official harness; positive control verifies; prepatch reproduced. No verifying wrong impl's faithful patch fails to resolve. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness assessment for sympy__sympy-13551 (nagini). SETUP: patched sympy built at base_commit 9476425b9e + gold hunk (line 286: `p = exp(Sum(log(p),(k,a,n)))`) confirmed present; run (py3.8, source import). CHECKS: (1) spec region byte-identical — same-spec exit 0. (2) model.py verifies (Nagini, 15.76s). (3) axiom_check.py runs on the REAL patched repo: G-AX OK on 317 in-domain inputs + 4 zero-total boundary inputs confirmed exp(zoo), exit 0.

FAITHFULNESS PROBE (independent): I ran the REAL routed callee `Product(p,(k,0,n-1)).doit()` (patched is_Add/q.is_Number branch, fired verified via exp/Sum/log present) at base_commit and compared its numeric value against the spec's deep model `prod_of_totals` = literal product of per-index totals, across: exponential F2P shape d+c*2^k; two/three-part exp Adds (2^k+3^k, 1+2^k+3^k, 2+3^k+5^k); mixed exp*poly (1+k*2^k, 2^k+k, 3+2^k+k^2, 1+2^k*3^k); rational (1/2^k+1); negative & mixed-sign constant parts (-3+2^k, -5+3*2^k, 3-2^k, -1-2^k, 2-5^k); plus 349 + 465 = 814 randomized in-domain draws (d in [-15,15], multi-term exp+poly Adds, ranges 1-6). ZERO mismatches across ~1300 in-domain inputs. Every fired case where the routed value is a number equals the genuine integer product.

DOMAIN BOUNDARY is justified, not a dodge: zero-total inputs (excluded by Requires(base[i]+comp[i]!=0)) genuinely yield exp(zoo) (undefined) in BOTH the routed Product.doit and direct exp(Sum(log)) forms — the real callee returns no faithful integer there, so the precondition correctly excludes them. Polynomial Adds (k+1, k^2+1) take a DIFFERENT branch (roots/finite-range), not the modeled is_Add/symbolic-limit branch, so they are out of scope — the model correctly targets non-polynomial Add multiplicands with symbolic limits. The spec is neither too strong nor drifted: the postcondition Result==prod_of_totals matches the real fixed callee on the entire modeled domain, and the prepatch (sum-of-part-products) fails it (G-DIFF), so the bug is really sensed. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the nagini spec view) PASSES: no diff markers, no gold-patch line reproduced (>=8-char normalized), no patched file/module path, no spec-view identifier or comment naming a patched repo symbol, no narration words. No RELAXED_LEAKAGE.md present (strict judgement applies).

Semantic check against the PUBLIC problem_statement only (not hints_text): the public statement already exposes the whole discriminator. It shows Product(n + 1/2**k, [k,0,n-1]) whose multiplicand is a *sum of two parts*, gives the wrong result 2**(n*(-n+1)/2) + n**n (literally the sum of the two per-part products => 9/2 at n=2) and the correct value 15/2 = (2+2^0)*(2+2^-1) (the genuine product of the per-index totals). Thus 'correct = product of per-index totals; wrong = sum of the two part-products' is fully derivable from the public task.

The spec view states exactly that specification (Result == prod_of_totals(base,comp) = prod(base[i]+comp[i]); prod_one only used to state that prod(base)+prod(comp) is a different number), plus the nonzero-total domain boundary. It does NOT reveal the gold EDIT mechanism: no mention of exp(Sum(log(p))), as_coeff_Add, sympy/concrete/products.py, Product._eval_product, the removed line, or the is_Add/q.is_Number branch. The identifiers base/comp/prod_of_totals/prod_one/product_of_sum echo no patched repo symbol. The spec describes the intended behavior (which the problem_statement already fixes), not how the repo achieves it.

Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already gives. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
