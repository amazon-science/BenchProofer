# P2 adversarial audit — sympy__sympy-19040

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,38 +94,27 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
     other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
-    images = factor_list(poly)
+    images = factor_list(other)
     result = []  # type: List[int]
     if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
         blob = lone(poly)
         i = 0
         while i < len(blob):
-            # invariants-start
             Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
+            Invariant(images == factor_list(other))
             Invariant(blob == lone(poly))
             Invariant(0 <= i and i <= len(blob))
             Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
             result = result + [blob[i]]
             i = i + 1
     else:
-        # two or more elements: the complete factor list of the input.
         i = 0
         while i < len(images):
-            # invariants-start
             Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
+            Invariant(images == factor_list(other))
             Invariant(0 <= i and i <= len(images))
             Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
             result = result + [images[i]]
             i = i + 1
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,39 +94,7 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
-    images = factor_list(poly)
     result = []  # type: List[int]
-    if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
-        blob = lone(poly)
-        i = 0
-        while i < len(blob):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(blob == lone(poly))
-            Invariant(0 <= i and i <= len(blob))
-            Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
-            result = result + [blob[i]]
-            i = i + 1
-    else:
-        # two or more elements: the complete factor list of the input.
-        i = 0
-        while i < len(images):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(0 <= i and i <= len(images))
-            Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
-            result = result + [images[i]]
-            i = i + 1
+    result = result + [poly]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,39 +94,15 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
-    images = factor_list(poly)
+    blob = lone(poly)
     result = []  # type: List[int]
-    if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
-        blob = lone(poly)
-        i = 0
-        while i < len(blob):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(blob == lone(poly))
-            Invariant(0 <= i and i <= len(blob))
-            Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
-            result = result + [blob[i]]
-            i = i + 1
-    else:
-        # two or more elements: the complete factor list of the input.
-        i = 0
-        while i < len(images):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(0 <= i and i <= len(images))
-            Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
-            result = result + [images[i]]
-            i = i + 1
+    i = 0
+    while i < len(blob):
+        Invariant(Acc(list_pred(result)))
+        Invariant(blob == lone(poly))
+        Invariant(0 <= i and i <= len(blob))
+        Invariant(ToSeq(result) == blob.take(i))
+        result = result + [blob[i]]
+        i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,39 +94,15 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
     images = factor_list(poly)
     result = []  # type: List[int]
-    if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
-        blob = lone(poly)
-        i = 0
-        while i < len(blob):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(blob == lone(poly))
-            Invariant(0 <= i and i <= len(blob))
-            Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
-            result = result + [blob[i]]
-            i = i + 1
-    else:
-        # two or more elements: the complete factor list of the input.
-        i = 0
-        while i < len(images):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(0 <= i and i <= len(images))
-            Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
-            result = result + [images[i]]
-            i = i + 1
+    i = 0
+    while i < len(images):
+        Invariant(Acc(list_pred(result)))
+        Invariant(images == factor_list(poly))
+        Invariant(0 <= i and i <= len(images))
+        Invariant(ToSeq(result) == images.take(i))
+        result = result + [images[i]]
+        i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,38 +94,26 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
     images = factor_list(poly)
     result = []  # type: List[int]
-    if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
+    if len(images) < 1:
         blob = lone(poly)
         i = 0
         while i < len(blob):
-            # invariants-start
             Invariant(Acc(list_pred(result)))
             Invariant(images == factor_list(poly))
             Invariant(blob == lone(poly))
             Invariant(0 <= i and i <= len(blob))
             Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
             result = result + [blob[i]]
             i = i + 1
     else:
-        # two or more elements: the complete factor list of the input.
         i = 0
         while i < len(images):
-            # invariants-start
             Invariant(Acc(list_pred(result)))
             Invariant(images == factor_list(poly))
             Invariant(0 <= i and i <= len(images))
             Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
             result = result + [images[i]]
             i = i + 1
     return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,38 +94,24 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
     images = factor_list(poly)
     result = []  # type: List[int]
     if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
-        blob = lone(poly)
-        i = 0
-        while i < len(blob):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(blob == lone(poly))
-            Invariant(0 <= i and i <= len(blob))
-            Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
-            result = result + [blob[i]]
-            i = i + 1
-    else:
-        # two or more elements: the complete factor list of the input.
         i = 0
         while i < len(images):
-            # invariants-start
             Invariant(Acc(list_pred(result)))
             Invariant(images == factor_list(poly))
             Invariant(0 <= i and i <= len(images))
             Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
+            result = result + [images[i]]
+            i = i + 1
+    else:
+        i = 0
+        while i < len(images):
+            Invariant(Acc(list_pred(result)))
+            Invariant(images == factor_list(poly))
+            Invariant(0 <= i and i <= len(images))
+            Invariant(ToSeq(result) == images.take(i))
             result = result + [images[i]]
             i = i + 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,38 +94,26 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
     images = factor_list(poly)
     result = []  # type: List[int]
     if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
         blob = lone(poly)
         i = 0
         while i < len(blob):
-            # invariants-start
             Invariant(Acc(list_pred(result)))
             Invariant(images == factor_list(poly))
             Invariant(blob == lone(poly))
             Invariant(0 <= i and i <= len(blob))
             Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
             result = result + [blob[i]]
             i = i + 1
     else:
-        # two or more elements: the complete factor list of the input.
         i = 0
-        while i < len(images):
-            # invariants-start
+        while i < len(images) - 1:
             Invariant(Acc(list_pred(result)))
             Invariant(images == factor_list(poly))
-            Invariant(0 <= i and i <= len(images))
+            Invariant(0 <= i and i <= len(images) - 1)
             Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
             result = result + [images[i]]
             i = i + 1
     return result
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,39 +94,20 @@
     Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
     # post-conditions-end
     # impl-start
-    # `other` is some related polynomial; it must NOT be the polynomial the
-    # factoring is applied to.
-    other = other_poly(poly)
-    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
-    # input's own complete factor list.
-    images = factor_list(poly)
+    fl = factor_list(poly)
     result = []  # type: List[int]
-    if len(images) <= 1:
-        # single element -> the single-element result (correct only when the
-        # input genuinely does not split into more than one factor).
-        blob = lone(poly)
-        i = 0
-        while i < len(blob):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(blob == lone(poly))
-            Invariant(0 <= i and i <= len(blob))
-            Invariant(ToSeq(result) == blob.take(i))
-            # invariants-end
-            result = result + [blob[i]]
-            i = i + 1
+    if len(fl) >= 2:
+        src = fl
     else:
-        # two or more elements: the complete factor list of the input.
-        i = 0
-        while i < len(images):
-            # invariants-start
-            Invariant(Acc(list_pred(result)))
-            Invariant(images == factor_list(poly))
-            Invariant(0 <= i and i <= len(images))
-            Invariant(ToSeq(result) == images.take(i))
-            # invariants-end
-            result = result + [images[i]]
-            i = i + 1
+        src = lone(poly)
+    i = 0
+    while i < len(src):
+        Invariant(Acc(list_pred(result)))
+        Invariant(Implies(len(fl) >= 2, src == fl))
+        Invariant(Implies(len(fl) <= 1, src == lone(poly)))
+        Invariant(0 <= i and i <= len(src))
+        Invariant(ToSeq(result) == src.take(i))
+        result = result + [src[i]]
+        i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-19040.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Factoring a (multivariate) polynomial with an extension must return its
  COMPLETE factor list: the returned list must contain EVERY factor of the
  input — none dropped — AND an input that splits into several factors must be
  returned as all of those separate factors, never collapsed to a single
  element. The leading coefficient is returned unchanged.

A polynomial is identified by an opaque identity (`int`), a value DISTINCT from
the factor list it must produce. The complete factor list OF THE INPUT is the
result of the (unchanged) factoring operation `factor_list` applied TO THAT
INPUT. The contract pins the result to that input-driven factoring: the returned
list equals `factor_list(poly)` whenever it has two or more elements, and equals
the single-element result `lone(poly)` otherwise (the legitimate case of an
input that does not split). Returning the input unchanged, returning it as a
length-one list, or applying the factoring to any polynomial OTHER than the
input itself does NOT satisfy the contract.

`factor_list`, the single-element result `lone`, and the auxiliary helper
`other_poly` are operations the function invokes but does not change; they are
axiomatised (`@Pure @ContractOnly`) by the weakest behaviour the proof needs
(each returns SOME determinate value as a function of its argument), and their
soundness is checked against the real callees out of band (axiom_check.py /
G-AX). The contract is expressed purely STRUCTURALLY over `factor_list(poly)`
(sequence equality and length only — no hidden answer-key lookup, no unbounded
value quantifiers), so the proof obligation stays inside Nagini's decidable
fragment.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def other_poly(poly: int) -> int:
    """An unchanged helper that maps a polynomial to some related polynomial
    identity. The weakest behaviour the proof needs: it returns SOME identity,
    about which nothing is promised — in particular it is NOT promised to denote
    the same polynomial as its argument. Provenance / soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def factor_list(poly: int) -> PSeq[int]:
    """The unchanged factoring operation: applied to a polynomial it returns
    that polynomial's complete factor list, a determinate sequence that depends
    ONLY on its argument. The weakest behaviour the proof needs: it returns SOME
    determinate sequence as a function of `poly` (nothing is promised relating
    the lists of two DIFFERENT arguments). Because the result depends only on the
    argument, applying it to a polynomial other than the input yields, in
    general, a different list. Provenance / soundness: mapping.md /
    axiom_check.py."""


@Pure
@ContractOnly
def lone(poly: int) -> PSeq[int]:
    """The single-element result the function returns when the factoring yields
    only one element: the input as ONE element. A determinate one-element
    sequence depending only on its argument; nothing further is promised.
    Provenance / soundness: mapping.md / axiom_check.py."""
    Ensures(len(Result()) == 1)
# axioms-end


# pure-start
# pure-end


def ext_factor(lc: int, poly: int) -> List[int]:
    # pre-conditions-start
    # `poly` is the opaque polynomial identity; the modeled domain is the input
    # shapes the F2P / PASS_TO_PASS extension-factorisation tests exercise.
    Requires(0 <= poly and poly <= 4)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # COMPLETE: the returned list is EXACTLY the factor list the factoring
    # operation reads off the INPUT itself -- every factor present, none
    # dropped, an input that splits returned as all of its separate factors.
    # When the factoring yields two or more elements the result is precisely
    # that list; when it yields a single element the result is that
    # single-element list (the legitimate non-splitting case). The result is
    # therefore pinned to the factoring APPLIED TO THE INPUT (`factor_list(poly)`),
    # not to any other polynomial.
    Ensures(Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) == factor_list(poly)))
    Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
    # post-conditions-end
    # impl-start
    # `other` is some related polynomial; it must NOT be the polynomial the
    # factoring is applied to.
    other = other_poly(poly)
    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
    # input's own complete factor list.
    images = factor_list(poly)
    result = []  # type: List[int]
    if len(images) <= 1:
        # single element -> the single-element result (correct only when the
        # input genuinely does not split into more than one factor).
        blob = lone(poly)
        i = 0
        while i < len(blob):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(images == factor_list(poly))
            Invariant(blob == lone(poly))
            Invariant(0 <= i and i <= len(blob))
            Invariant(ToSeq(result) == blob.take(i))
            # invariants-end
            result = result + [blob[i]]
            i = i + 1
    else:
        # two or more elements: the complete factor list of the input.
        i = 0
        while i < len(images):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(images == factor_list(poly))
            Invariant(0 <= i and i <= len(images))
            Invariant(ToSeq(result) == images.take(i))
            # invariants-end
            result = result + [images[i]]
            i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT SOUND. No verifying wrong-impl's faithful patch failed to resolve.

SPEC ANALYSIS: The frozen postcondition FULLY pins Result() per input via two uninterpreted @Pure @ContractOnly axioms of the argument: Ensures(Implies(len(factor_list(poly))>=2, ToSeq(Result())==factor_list(poly))) and Ensures(Implies(len(factor_list(poly))<=1, ToSeq(Result())==lone(poly))). Since factor_list/lone depend only on their argument and are uninterpreted, the only PSeq values a verifying impl can produce for those clauses are factor_list(poly)/lone(poly) applied to the ORIGINAL input -> behaviorally the gold factorisation. No answer-key oracle is exposed.

POSITIVE CONTROL: positive_control.py (copy of model.py) -> `bash scripts/nagini_verify.sh` EXIT 0, 'Verification successful' (12.5s).

ATTACKS (all same-spec confirmed: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-19040 <atk>` EXIT 0 for all 8). weakness command: `python -m swebench_unified.adversary weakness nagini sympy__sympy-19040 <atk>`; run in 3 parallel background batches (<=3 JVM each):
- atk_1.py PREPATCH BUG (images=factor_list(other_poly(poly))): weakness EXIT 2 (rejected). Direct nagini_verify: 'Verification failed', fails EXACTLY on completeness clause atk_1.py:93 Implies(len(factor_list(poly))>=2, ToSeq(Result())==factor_list(poly)) -- prepatch_reproduced=True.
- atk_2.py ungrounded echo (return [poly]): weakness EXIT 2 (rejected).
- atk_3.py partial-domain / unconditional lone(poly) always: weakness EXIT 2 (rejected).
- atk_4.py unconditional materialise factor_list(poly), no branch (drops lone clause when len<=1): weakness EXIT 2 (rejected).
- atk_5.py boundary off (len<1 instead of <=1): weakness EXIT 2 (rejected).
- atk_6.py control-flow-swap (return factor_list in the len<=1 branch instead of lone): weakness EXIT 2 (rejected).
- atk_7.py boundary/off-by-one (drop last element: loop while i<len(images)-1): weakness EXIT 2 (rejected).
- atk_8.py VALUE-IDENTICAL restructure of gold (factor_list(poly) applied to original; select src=factor_list when len>=2 else lone(poly); single copy loop): weakness EXIT 0 -> CANDIDATE (shares spec AND verifies, 14.2s). PROTOCOL: materialized its faithful refined patch atk_8.patch (the gold one-line dmp_sqf_norm(f)->dmp_sqf_norm(F) edit, since atk_8 applies the recovery to the ORIGINAL poly) and RAN it through the official harness: `harness.run_resolve('sympy__sympy-19040', patch, timeout=1800)` -> resolved=True, completed=True, note='resolved', attempts=1, FAIL_TO_PASS test_issue_5786 success, all 168 PASS_TO_PASS success. So this verifying candidate RESOLVES -> it is the legitimate A-reference resolving exemplar, NOT a weakness (verify=>correct holds for it).

REFINEMENT.MD AUDIT (A-leg focus, no kind-3): step1 lc = R (opaque scalar pass-through), step2 poly = R (Poly/dmp carrier<->opaque identity, dmp_ground_monic unit-normalisation), step3 other_poly<->dmp_sqf_part = A-consumed (Ensures(True) weakest; axiom_check.py check_other_poly confirms real dmp_sqf_part((x-1)(y-1)) degrees (1,0)!=(1,1) -> factor-losing, no stronger axiom admissible), step4 factor_list<->dmp_sqf_norm(F)->dmp_factor_list_include->recovery->dmp_trial_division = A-consumed (axiom_check.py check_factor_list_complete 8/8 complete via factor(.,extension=[I]) incl issue (x-1)(y-1) and F2P (x-Iy)(z-It); check_argument_is_load_bearing full (2,2) vs part (2,0)), step5 selection branch = I+A (lone A-consumed length-1 fallback factors=[f], Ensures(len==1) sound). Every leg is R / A-consumed / I; A-legs' correspondence to real callees holds and is machine-backed by axiom_check.py. There is a genuine A-reference resolving exemplar (return factor_list(poly)==gold), confirmed by atk_8 resolving.

MINOR DOC NOTE (not a break, pre-recorded in verdict.md G-PANEL-2): mapping.md §3 claims poly=4 (x^2+1, ext=[I]) exercises the len<=1/lone branch, but empirically factor(x^2+1, extension=[I])=(x-I)(x+I)=2 factors, so no modeled runtime input actually triggers the len<=1 branch. Coverage/doc inaccuracy only; because Nagini reasons over an arbitrary uninterpreted factor_list(poly), BOTH branches remain pinned (proven by atk_3/atk_6 rejection) and soundness/faithfulness are unaffected. Does not bear on verify=>correct.

ENVIRONMENT: verifier env swebench-nagini-verifier under FSx; adversary module run via python.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-19040.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Factoring a (multivariate) polynomial with an extension must return its
  COMPLETE factor list: the returned list must contain EVERY factor of the
  input — none dropped — AND an input that splits into several factors must be
  returned as all of those separate factors, never collapsed to a single
  element. The leading coefficient is returned unchanged.

A polynomial is identified by an opaque identity (`int`), a value DISTINCT from
the factor list it must produce. The complete factor list OF THE INPUT is the
result of the (unchanged) factoring operation `factor_list` applied TO THAT
INPUT. The contract pins the result to that input-driven factoring: the returned
list equals `factor_list(poly)` whenever it has two or more elements, and equals
the single-element result `lone(poly)` otherwise (the legitimate case of an
input that does not split). Returning the input unchanged, returning it as a
length-one list, or applying the factoring to any polynomial OTHER than the
input itself does NOT satisfy the contract.

`factor_list`, the single-element result `lone`, and the auxiliary helper
`other_poly` are operations the function invokes but does not change; they are
axiomatised (`@Pure @ContractOnly`) by the weakest behaviour the proof needs
(each returns SOME determinate value as a function of its argument), and their
soundness is checked against the real callees out of band (axiom_check.py /
G-AX). The contract is expressed purely STRUCTURALLY over `factor_list(poly)`
(sequence equality and length only — no hidden answer-key lookup, no unbounded
value quantifiers), so the proof obligation stays inside Nagini's decidable
fragment.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def other_poly(poly: int) -> int:
    """An unchanged helper that maps a polynomial to some related polynomial
    identity. The weakest behaviour the proof needs: it returns SOME identity,
    about which nothing is promised — in particular it is NOT promised to denote
    the same polynomial as its argument. Provenance / soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def factor_list(poly: int) -> PSeq[int]:
    """The unchanged factoring operation: applied to a polynomial it returns
    that polynomial's complete factor list, a determinate sequence that depends
    ONLY on its argument. The weakest behaviour the proof needs: it returns SOME
    determinate sequence as a function of `poly` (nothing is promised relating
    the lists of two DIFFERENT arguments). Because the result depends only on the
    argument, applying it to a polynomial other than the input yields, in
    general, a different list. Provenance / soundness: mapping.md /
    axiom_check.py."""


@Pure
@ContractOnly
def lone(poly: int) -> PSeq[int]:
    """The single-element result the function returns when the factoring yields
    only one element: the input as ONE element. A determinate one-element
    sequence depending only on its argument; nothing further is promised.
    Provenance / soundness: mapping.md / axiom_check.py."""
    Ensures(len(Result()) == 1)
# axioms-end


# pure-start
# pure-end


def ext_factor(lc: int, poly: int) -> List[int]:
    # pre-conditions-start
    # `poly` is the opaque polynomial identity; the modeled domain is the input
    # shapes the F2P / PASS_TO_PASS extension-factorisation tests exercise.
    Requires(0 <= poly and poly <= 4)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # COMPLETE: the returned list is EXACTLY the factor list the factoring
    # operation reads off the INPUT itself -- every factor present, none
    # dropped, an input that splits returned as all of its separate factors.
    # When the factoring yields two or more elements the result is precisely
    # that list; when it yields a single element the result is that
    # single-element list (the legitimate non-splitting case). The result is
    # therefore pinned to the factoring APPLIED TO THE INPUT (`factor_list(poly)`),
    # not to any other polynomial.
    Ensures(Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) == factor_list(poly)))
    Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
    # post-conditions-end
    # impl-start
    # `other` is some related polynomial; it must NOT be the polynomial the
    # factoring is applied to.
    other = other_poly(poly)
    # The factoring is applied to the ORIGINAL polynomial, so it reads back the
    # input's own complete factor list.
    images = factor_list(poly)
    result = []  # type: List[int]
    if len(images) <= 1:
        # single element -> the single-element result (correct only when the
        # input genuinely does not split into more than one factor).
        blob = lone(poly)
        i = 0
        while i < len(blob):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(images == factor_list(poly))
            Invariant(blob == lone(poly))
            Invariant(0 <= i and i <= len(blob))
            Invariant(ToSeq(result) == blob.take(i))
            # invariants-end
            result = result + [blob[i]]
            i = i + 1
    else:
        # two or more elements: the complete factor list of the input.
        i = 0
        while i < len(images):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(images == factor_list(poly))
            Invariant(0 <= i and i <= len(images))
            Invariant(ToSeq(result) == images.take(i))
            # invariants-end
            result = result + [images[i]]
            i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT SOUND. No verifying wrong-impl's faithful patch failed to resolve.

SPEC ANALYSIS: The frozen postcondition FULLY pins Result() per input via two uninterpreted @Pure @ContractOnly axioms of the argument: Ensures(Implies(len(factor_list(poly))>=2, ToSeq(Result())==factor_list(poly))) and Ensures(Implies(len(factor_list(poly))<=1, ToSeq(Result())==lone(poly))). Since factor_list/lone depend only on their argument and are uninterpreted, the only PSeq values a verifying impl can produce for those clauses are factor_list(poly)/lone(poly) applied to the ORIGINAL input -> behaviorally the gold factorisation. No answer-key oracle is exposed.

POSITIVE CONTROL: positive_control.py (copy of model.py) -> `bash scripts/nagini_verify.sh` EXIT 0, 'Verification successful' (12.5s).

ATTACKS (all same-spec confirmed: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-19040 <atk>` EXIT 0 for all 8). weakness command: `python -m swebench_unified.adversary weakness nagini sympy__sympy-19040 <atk>`; run in 3 parallel background batches (<=3 JVM each):
- atk_1.py PREPATCH BUG (images=factor_list(other_poly(poly))): weakness EXIT 2 (rejected). Direct nagini_verify: 'Verification failed', fails EXACTLY on completeness clause atk_1.py:93 Implies(len(factor_list(poly))>=2, ToSeq(Result())==factor_list(poly)) -- prepatch_reproduced=True.
- atk_2.py ungrounded echo (return [poly]): weakness EXIT 2 (rejected).
- atk_3.py partial-domain / unconditional lone(poly) always: weakness EXIT 2 (rejected).
- atk_4.py unconditional materialise factor_list(poly), no branch (drops lone clause when len<=1): weakness EXIT 2 (rejected).
- atk_5.py boundary off (len<1 instead of <=1): weakness EXIT 2 (rejected).
- atk_6.py control-flow-swap (return factor_list in the len<=1 branch instead of lone): weakness EXIT 2 (rejected).
- atk_7.py boundary/off-by-one (drop last element: loop while i<len(images)-1): weakness EXIT 2 (rejected).
- atk_8.py VALUE-IDENTICAL restructure of gold (factor_list(poly) applied to original; select src=factor_list when len>=2 else lone(poly); single copy loop): weakness EXIT 0 -> CANDIDATE (shares spec AND verifies, 14.2s). PROTOCOL: materialized its faithful refined patch atk_8.patch (the gold one-line dmp_sqf_norm(f)->dmp_sqf_norm(F) edit, since atk_8 applies the recovery to the ORIGINAL poly) and RAN it through the official harness: `harness.run_resolve('sympy__sympy-19040', patch, timeout=1800)` -> resolved=True, completed=True, note='resolved', attempts=1, FAIL_TO_PASS test_issue_5786 success, all 168 PASS_TO_PASS success. So this verifying candidate RESOLVES -> it is the legitimate A-reference resolving exemplar, NOT a weakness (verify=>correct holds for it).

REFINEMENT.MD AUDIT (A-leg focus, no kind-3): step1 lc = R (opaque scalar pass-through), step2 poly = R (Poly/dmp carrier<->opaque identity, dmp_ground_monic unit-normalisation), step3 other_poly<->dmp_sqf_part = A-consumed (Ensures(True) weakest; axiom_check.py check_other_poly confirms real dmp_sqf_part((x-1)(y-1)) degrees (1,0)!=(1,1) -> factor-losing, no stronger axiom admissible), step4 factor_list<->dmp_sqf_norm(F)->dmp_factor_list_include->recovery->dmp_trial_division = A-consumed (axiom_check.py check_factor_list_complete 8/8 complete via factor(.,extension=[I]) incl issue (x-1)(y-1) and F2P (x-Iy)(z-It); check_argument_is_load_bearing full (2,2) vs part (2,0)), step5 selection branch = I+A (lone A-consumed length-1 fallback factors=[f], Ensures(len==1) sound). Every leg is R / A-consumed / I; A-legs' correspondence to real callees holds and is machine-backed by axiom_check.py. There is a genuine A-reference resolving exemplar (return factor_list(poly)==gold), confirmed by atk_8 resolving.

MINOR DOC NOTE (not a break, pre-recorded in verdict.md G-PANEL-2): mapping.md §3 claims poly=4 (x^2+1, ext=[I]) exercises the len<=1/lone branch, but empirically factor(x^2+1, extension=[I])=(x-I)(x+I)=2 factors, so no modeled runtime input actually triggers the len<=1 branch. Coverage/doc inaccuracy only; because Nagini reasons over an arbitrary uninterpreted factor_list(poly), BOTH branches remain pinned (proven by atk_3/atk_6 rejection) and soundness/faithfulness are unaffected. Does not bear on verify=>correct.

ENVIRONMENT: verifier env swebench-nagini-verifier under FSx; adversary module run via python.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) verdict: FAITHFUL. No input in the modeled domain (0<=poly<=4) makes the modeled function disagree with the real callee.

Independently reproduced machine-checked facts (worktree at base_commit b9179e80... + real gold patch, sympy 1.6.dev):
- same-spec: model.py shares the bundle's exact spec (adversary same-spec exit 0). Prepatch also same-spec by construction.
- Model verifies: Nagini 'Verification successful' (10.99s).
- axiom_check.py under gold worktree: SOUND. 8/8 complete factorisations; dmp_sqf_part factor-losing degrees (1,0)!=(1,1) justifying other_poly's Ensures(True); factor_list argument load-bearing (2,2) vs (2,0); lone fallback length-1.
- Real gold dmp_ext_factor / factor(.,extension=[...]) on all 5 modeled inputs returns the COMPLETE factorization: poly0 (x-1)(y-1) ext[I] -> 2 factors (reconstructs); poly1 (x-Iy)(z-It) ext[I] -> 2 (reconstructs); poly2 x^2-2y^2 ext[sqrt2] -> 2 (reconstructs); poly3 (x-1)(y-1)(z-1) ext[I] -> 3 (reconstructs); poly4 x^2+1 ext[I] -> 2 (reconstructs).
- Under base (unpatched, buggy) the same calls drop factors on poly0/1/3 (reconstructs=False), confirming the bug/fix framing and that the spec correctly REJECTS the buggy behavior (prepatch fails on model_prepatch.py:93 completeness clause).

The postcondition pins Result to factor_list(poly) (>=2) or lone(poly) (<=1). factor_list is an uninterpreted @Pure @ContractOnly axiom validated by G-AX to denote the real complete factoring the gold dmp_ext_factor computes; on every modeled input the real gold function returns exactly that complete factorization. The spec is an exact abstraction of the real gold behavior, not too strong and does not drift -- no diverging input exists.

Minor documentation note (NOT a faithfulness break): mapping.md §3 claims poly=4 (x^2+1, ext=[I]) exercises the len==1/lone branch, but empirically factor(x^2+1, extension=[I]) = (x-I)(x+I) = 2 factors, so no modeled input actually triggers the len<=1 branch at runtime. This is a spec-coverage/doc inaccuracy only: because Nagini reasons over an arbitrary uninterpreted factor_list(poly), the lone clause remains sound and the postcondition holds for all inputs. It does not cause the modeled function to disagree with the real callee on any input, so it does not weaken or falsify the faithfulness verdict.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view verified: same_spec(model, prepatch)==True; spec region well-formed, impl elided ('...'). Mechanical G-LEAK screen (swebench_unified.leakage.screen over the nagini spec_view) passes with zero hard_failures.

Public baseline (problem_statement, NOT hints): the StackOverflow/issue report already states factor(expand((x-1)*(y-1)), extension=[I]) returns 'x - 1' -- a factor (y-1) is DROPPED and a multi-factor input collapses to a single element. The 'dropped factor / collapse to one element' symptom is therefore fully public.

Gold edit: single one-line hunk at sympy/polys/factortools.py:1150, dmp_sqf_norm(f, u, K) -> dmp_sqf_norm(F, u, K) (apply recovery to the original polynomial F, not its square-free part f).

Reconstruction test -- no leakage beyond the public symptom:
- Postconditions pin Result() to factor_list(poly)/lone(poly), functions of the INPUT. Legitimate A-reference exemplar pattern (pinning correct output), not leakage; factor_list/lone/other_poly are uninterpreted @Pure @ContractOnly axioms, no answer-key oracle in the signature.
- No repo mechanism vocabulary survives: 'square-free', 'norm', 'resultant', 'recovery', 'sqf', dmp_* identifiers, factortools, and the file/line are all ABSENT from the spec view. No f->F transformation exposed.
- Strongest candidate lines (docstring 'applying the factoring to any polynomial OTHER than the input itself does NOT satisfy the contract', plus the other_poly axiom) describe the bug's ABSTRACT nature (a related polynomial was factored) in fully opaque model terms. They do NOT disclose that the 'other polynomial' is the square-free part, nor the concrete edit or its location -- they restate, at abstract altitude, the already-public 'wrong result / dropped factor' symptom.

Conclusion: the spec view stays at abstract-behavioural altitude; the gold repo edit is not recoverable from it beyond the already-public problem_statement symptom. Not a relaxed bundle (relaxed_leakage: None; no RELAXED_LEAKAGE.md). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
