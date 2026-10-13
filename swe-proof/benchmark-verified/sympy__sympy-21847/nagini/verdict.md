# P2 adversarial audit — sympy__sympy-21847

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -64,19 +64,21 @@
     Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
     # post-conditions-end
     # impl-start
-    total = 0
+    running = 0
     i = len(powers)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(powers), 1 / 2))
         Invariant(0 <= i and i <= len(powers))
-        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
+        Invariant(running >= 0)
+        Invariant(Forall(int, lambda j: (Implies(i <= j and j < len(powers),
+                                                 powers[j] <= running),
+                                         [[powers[j]]])))
         # invariants-end
-        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
-        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
-        total = powers[i - 1] + total
+        if powers[i - 1] >= running:
+            running = powers[i - 1]
         i = i - 1
-    return total >= min_degree
+    return running >= min_degree
     # impl-end
 
 
@@ -95,17 +97,19 @@
     Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
     # post-conditions-end
     # impl-start
-    total = 0
+    running = 0
     i = len(powers)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(powers), 1 / 2))
         Invariant(0 <= i and i <= len(powers))
-        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
+        Invariant(running >= 0)
+        Invariant(Forall(int, lambda j: (Implies(i <= j and j < len(powers),
+                                                 powers[j] <= running),
+                                         [[powers[j]]])))
         # invariants-end
-        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
-        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
-        total = powers[i - 1] + total
+        if powers[i - 1] >= running:
+            running = powers[i - 1]
         i = i - 1
-    return total >= min_degree
+    return running >= min_degree
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
         Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
         total = powers[i - 1] + total
         i = i - 1
-    return total >= min_degree
+    return total > min_degree
     # impl-end
 
 
@@ -107,5 +107,5 @@
         Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
         total = powers[i - 1] + total
         i = i - 1
-    return total >= min_degree
+    return total > min_degree
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
         Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
         total = powers[i - 1] + total
         i = i - 1
-    return total >= min_degree
+    return total >= min_degree and len(powers) > 0
     # impl-end
 
 
@@ -107,5 +107,5 @@
         Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
         total = powers[i - 1] + total
         i = i - 1
-    return total >= min_degree
+    return total >= min_degree and len(powers) > 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
         Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
         total = powers[i - 1] + total
         i = i - 1
-    return total >= min_degree
+    return total + 1 >= min_degree
     # impl-end
 
 
@@ -107,5 +107,5 @@
         Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
         total = powers[i - 1] + total
         i = i - 1
-    return total >= min_degree
+    return total + 1 >= min_degree
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -66,10 +66,10 @@
     # impl-start
     total = 0
     i = len(powers)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(powers), 1 / 2))
-        Invariant(0 <= i and i <= len(powers))
+        Invariant(1 <= i and i <= len(powers))
         Invariant(total == deg_sum(ToSeq(powers).drop(i)))
         # invariants-end
         Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
@@ -97,10 +97,10 @@
     # impl-start
     total = 0
     i = len(powers)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(powers), 1 / 2))
-        Invariant(0 <= i and i <= len(powers))
+        Invariant(1 <= i and i <= len(powers))
         Invariant(total == deg_sum(ToSeq(powers).drop(i)))
         # invariants-end
         Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -64,19 +64,7 @@
     Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
     # post-conditions-end
     # impl-start
-    total = 0
-    i = len(powers)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(powers), 1 / 2))
-        Invariant(0 <= i and i <= len(powers))
-        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
-        # invariants-end
-        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
-        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
-        total = powers[i - 1] + total
-        i = i - 1
-    return total >= min_degree
+    return True
     # impl-end
 
 
@@ -95,17 +83,5 @@
     Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
     # post-conditions-end
     # impl-start
-    total = 0
-    i = len(powers)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(powers), 1 / 2))
-        Invariant(0 <= i and i <= len(powers))
-        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
-        # invariants-end
-        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
-        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
-        total = powers[i - 1] + total
-        i = i - 1
-    return total >= min_degree
+    return True
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -70,11 +70,10 @@
         # invariants-start
         Invariant(Acc(list_pred(powers), 1 / 2))
         Invariant(0 <= i and i <= len(powers))
-        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
+        Invariant(total >= 0)
         # invariants-end
-        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
-        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
-        total = powers[i - 1] + total
+        if powers[i - 1] > 0:
+            total = total + 1
         i = i - 1
     return total >= min_degree
     # impl-end
@@ -101,11 +100,10 @@
         # invariants-start
         Invariant(Acc(list_pred(powers), 1 / 2))
         Invariant(0 <= i and i <= len(powers))
-        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
+        Invariant(total >= 0)
         # invariants-end
-        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
-        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
-        total = powers[i - 1] + total
+        if powers[i - 1] > 0:
+            total = total + 1
         i = i - 1
     return total >= min_degree
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21847.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A candidate term over a set of variables is described by its exponent vector
  `powers` (one non-negative integer per variable: how many times that variable
  occurs in the term). The TOTAL DEGREE of the term is the arithmetic sum of the
  exponents across all variables.

  When enumerating terms subject to a single lower bound `min_degree` on the
  total degree, a candidate is RETAINED exactly when its total degree is at
  least `min_degree`. The documented contract is
  `min_degree <= total_degree(term)`: the threshold is compared against the
  whole term's total degree, i.e. the arithmetic sum of the per-variable
  exponents. So a multi-variable term such as one with exponent vector `[2, 1]`
  (total degree 3) must be retained at `min_degree = 3`.

  The same retention rule governs both the case where the variables commute and
  the case where they do not — the lower-bound test is on the total degree of
  the enumerated term in either case.

Modelling: the exponent vector is `powers: List[int]` of non-negative integers;
the total degree is spelled out deeply as the front-recursive fold `deg_sum`
(the arithmetic sum over the vector), the canonical sequence-fold pattern (one
unfold per loop step). The specification is carried by `PSeq[int]` via `ToSeq`.
No callee is axiomatized: the modelled reduction is spelled out deeply, not
hidden behind an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the reduction is modelled deeply as the fold deg_sum below; no
# unchanged opaque callee is consumed by the proof.)
# axioms-end

# pure-start
@Pure
def deg_sum(p: PSeq[int]) -> int:
    """Total degree: the arithmetic sum of the per-variable exponents.
    Front-recursive (one unfold per loop step — the canonical fold pattern)."""
    if len(p) == 0:
        return 0
    return p[0] + deg_sum(p.drop(1))
# pure-end

def keep_comm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree
    # impl-end

def keep_noncomm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-21847 (nagini). Spec is a TIGHT equality postcondition Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree)) at both keep_comm and keep_noncomm, where deg_sum is the deeply-modeled @Pure front-recursive arithmetic sum of the exponent vector. Gold patch changes max(powers.values())->sum(powers.values()) in both itermonomials branches (monomials.py:130,142).

PROTOCOL: 7 DISTINCT same-spec wrong impls, all editing ONLY the impl regions (axioms/@Pure/Requires/Ensures byte-identical). same-spec check: ALL 7 returned exit 0 (SAME - byte-identical spec). Positive control = model.py verbatim: bash scripts/nagini_verify.sh -> exit 0, 'Verification successful' (14.66s).

Weakness runs (python -m swebench_unified.adversary weakness nagini sympy__sympy-21847 <atk>), run concurrently in batches of 3 (JVM+Z3 each):
  atk_1 = MAX reduction (the actual prepatch bug re-encoded as running-max loop, invariant forall j in [i,len): powers[j] <= running) -> w1.log: NOT-A-COUNTEREXAMPLE (does not verify).
  atk_2 = boundary: strict '>' instead of '>=' -> w2.log: NOT-A-COUNTEREXAMPLE.
  atk_3 = partial-domain: 'total >= min_degree and len(powers) > 0' (wrong on empty vector at min_degree 0) -> w3.log: NOT-A-COUNTEREXAMPLE.
  atk_4 = off-by-one: 'total + 1 >= min_degree' -> w4.log: NOT-A-COUNTEREXAMPLE.
  atk_5 = control-flow effect: loop 'while i > 1' skips index 0 (drops first exponent from the fold) -> w5.log: NOT-A-COUNTEREXAMPLE.
  atk_6 = ungrounded-oracle echo: 'return True' constant -> w6.log: NOT-A-COUNTEREXAMPLE.
  atk_7 = count nonzero exponents instead of summing them -> w7.log: exit 2, NOT-A-COUNTEREXAMPLE.

Every attack was REJECTED by the frozen spec (none verified) -> NO CANDIDATE arose, so there is no verifying-wrong-impl faithful patch to materialize/resolve (patches={} legitimately empty; verify=>correct not falsified). prepatch_reproduced=true: model_prepatch.py (running-max) is exactly atk_1's shape and fails the frozen postcondition, matching the shipped differential witness.

REFINEMENT.MD / A-LEG AUDIT: axioms-start/end region is EMPTY; mapping.md §3 = 'None'; axiom_check.py confirms NO @ContractOnly axiom. Therefore ZERO A-consumed and ZERO A-reference legs to audit — the only changed operation (max->sum reduction) is modeled DEEPLY by the @Pure fold deg_sum, consumed directly by the postcondition and computed by the impl loop, matching gold sum(powers.values()) >= min_degree. All 4 refinement legs are R or I; NO kind-3 (unexpressible-changed-op) leg. deg_sum<->sum and (prepatch) deg_max<->max correspondence is total side-effect-free integer arithmetic, independently exercised by axiom_check.py part 1 (exhaustive small + 20000 fuzz) and part 2 (real gold-patched itermonomials, sum-vs-max discriminator, guarded to skip cleanly at base_commit). Correspondence holds. No axiom trust point exists. VERDICT: SOUND — >=5 (7) distinct attacks run, none broke the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
"""Twin-artifact model for sympy__sympy-21847.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A candidate term over a set of variables is described by its exponent vector
  `powers` (one non-negative integer per variable: how many times that variable
  occurs in the term). The TOTAL DEGREE of the term is the arithmetic sum of the
  exponents across all variables.

  When enumerating terms subject to a single lower bound `min_degree` on the
  total degree, a candidate is RETAINED exactly when its total degree is at
  least `min_degree`. The documented contract is
  `min_degree <= total_degree(term)`: the threshold is compared against the
  whole term's total degree, i.e. the arithmetic sum of the per-variable
  exponents. So a multi-variable term such as one with exponent vector `[2, 1]`
  (total degree 3) must be retained at `min_degree = 3`.

  The same retention rule governs both the case where the variables commute and
  the case where they do not — the lower-bound test is on the total degree of
  the enumerated term in either case.

Modelling: the exponent vector is `powers: List[int]` of non-negative integers;
the total degree is spelled out deeply as the front-recursive fold `deg_sum`
(the arithmetic sum over the vector), the canonical sequence-fold pattern (one
unfold per loop step). The specification is carried by `PSeq[int]` via `ToSeq`.
No callee is axiomatized: the modelled reduction is spelled out deeply, not
hidden behind an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the reduction is modelled deeply as the fold deg_sum below; no
# unchanged opaque callee is consumed by the proof.)
# axioms-end

# pure-start
@Pure
def deg_sum(p: PSeq[int]) -> int:
    """Total degree: the arithmetic sum of the per-variable exponents.
    Front-recursive (one unfold per loop step — the canonical fold pattern)."""
    if len(p) == 0:
        return 0
    return p[0] + deg_sum(p.drop(1))
# pure-end

def keep_comm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree
    # impl-end

def keep_noncomm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-21847 (nagini). Spec is a TIGHT equality postcondition Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree)) at both keep_comm and keep_noncomm, where deg_sum is the deeply-modeled @Pure front-recursive arithmetic sum of the exponent vector. Gold patch changes max(powers.values())->sum(powers.values()) in both itermonomials branches (monomials.py:130,142).

PROTOCOL: 7 DISTINCT same-spec wrong impls, all editing ONLY the impl regions (axioms/@Pure/Requires/Ensures byte-identical). same-spec check: ALL 7 returned exit 0 (SAME - byte-identical spec). Positive control = model.py verbatim: bash scripts/nagini_verify.sh -> exit 0, 'Verification successful' (14.66s).

Weakness runs (python -m swebench_unified.adversary weakness nagini sympy__sympy-21847 <atk>), run concurrently in batches of 3 (JVM+Z3 each):
  atk_1 = MAX reduction (the actual prepatch bug re-encoded as running-max loop, invariant forall j in [i,len): powers[j] <= running) -> w1.log: NOT-A-COUNTEREXAMPLE (does not verify).
  atk_2 = boundary: strict '>' instead of '>=' -> w2.log: NOT-A-COUNTEREXAMPLE.
  atk_3 = partial-domain: 'total >= min_degree and len(powers) > 0' (wrong on empty vector at min_degree 0) -> w3.log: NOT-A-COUNTEREXAMPLE.
  atk_4 = off-by-one: 'total + 1 >= min_degree' -> w4.log: NOT-A-COUNTEREXAMPLE.
  atk_5 = control-flow effect: loop 'while i > 1' skips index 0 (drops first exponent from the fold) -> w5.log: NOT-A-COUNTEREXAMPLE.
  atk_6 = ungrounded-oracle echo: 'return True' constant -> w6.log: NOT-A-COUNTEREXAMPLE.
  atk_7 = count nonzero exponents instead of summing them -> w7.log: exit 2, NOT-A-COUNTEREXAMPLE.

Every attack was REJECTED by the frozen spec (none verified) -> NO CANDIDATE arose, so there is no verifying-wrong-impl faithful patch to materialize/resolve (patches={} legitimately empty; verify=>correct not falsified). prepatch_reproduced=true: model_prepatch.py (running-max) is exactly atk_1's shape and fails the frozen postcondition, matching the shipped differential witness.

REFINEMENT.MD / A-LEG AUDIT: axioms-start/end region is EMPTY; mapping.md §3 = 'None'; axiom_check.py confirms NO @ContractOnly axiom. Therefore ZERO A-consumed and ZERO A-reference legs to audit — the only changed operation (max->sum reduction) is modeled DEEPLY by the @Pure fold deg_sum, consumed directly by the postcondition and computed by the impl loop, matching gold sum(powers.values()) >= min_degree. All 4 refinement legs are R or I; NO kind-3 (unexpressible-changed-op) leg. deg_sum<->sum and (prepatch) deg_max<->max correspondence is total side-effect-free integer arithmetic, independently exercised by axiom_check.py part 1 (exhaustive small + 20000 fuzz) and part 2 (real gold-patched itermonomials, sum-vs-max discriminator, guarded to skip cleanly at base_commit). Correspondence holds. No axiom trust point exists. VERDICT: SOUND — >=5 (7) distinct attacks run, none broke the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) audit for sympy__sympy-21847 nagini bundle. No diverging input exists — model spec faithfully matches the gold-patched repo behavior.

Modeled callee: the changed retention predicate of itermonomials (commutative hunk monomials.py:130 + non-commutative hunk :142, textually identical). Gold-patched real behavior: `if sum(powers.values()) >= min_degree:`. Model postcondition (both keep_comm/keep_noncomm): `Result() == (deg_sum(ToSeq(powers)) >= min_degree)` where deg_sum is the arithmetic front-recursive fold = sum over the exponent vector.

Verification:
1. scripts/nagini_verify.sh model.py => 'Verification successful' RC=0 (19.9s).
2. same-spec nagini => RC=0 (model shares bundle's exact spec).
3. at base_commit d9b18c518d... reads `max(powers.values()) >= min_degree`; reads `sum(powers.values()) >= min_degree` (the gold patch) at both :130 and :142.
4. Differential fuzz: model predicate deg_sum(powers)>=md vs real sum(powers.values())>=md over 300000 random inputs (n in 0..6, values 0..5, md 0..15, including empty vectors) => 0 mismatches. sum/max are order-independent so the dict-values <-> List[int] carrier is faithful.

Precondition faithfulness (spec not too strong): Requires(min_degree>=0) and Requires(all powers[i]>=0) are both GUARANTEED at the real call site — min_degree validated non-negative and <=max_degree upstream (monomials.py:104-115); each powers[v] is initialised to 0 and only incremented (+=1), so is always >=0. No reachable real input is excluded by the preconditions. The empty-vector case (deg_sum==0) is consistent with the documented min_degree<=total_degree contract.

Conclusion: the modeled function agrees with the real callee on all inputs in the callee's real domain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = max(powers.values()) >= min_degree -> sum(powers.values()) >= min_degree in the commutative and non-commutative retention tests of itermonomials (2 identical hunks). Reviewed the consumer spec view produced by markers.spec_view (docstring + deg_sum @Pure fold + pre/post-conditions of keep_comm/keep_noncomm; impl regions elided to '...'). Mechanical leakage.screen() PASSES (no hard failures): no diff markers, no gold-patch line reproduced, no patched file path/module (sympy/polys/monomials.py absent), no spec-view identifier or comment naming a patched repo symbol (itermonomials, monomials, powers.values all absent), no narration terms.

Semantic check beyond the lexical screen: the spec view encodes ONLY the desired behavior — total degree = arithmetic SUM of per-variable exponents, and 'retain iff min_degree <= total_degree(term)'. This is fully public in problem_statement, which (a) states monomials like x1*x2**2 with total degree 3 SHOULD be returned, and (b) quotes the documented contract verbatim: 'min_degree <= total_degree(monom) <= max_degree'. The spec-view example [2,1] (total degree 3) retained at min_degree=3 is the same case as the problem statement's x1*x2**2. Critically, the spec view reveals NOTHING about the buggy mechanism: no 'max'/'maximum', no pre-patch reduction, no fix-narration.

The pre-patch running-max reduction lives only in model_prepatch.py and the reference deg_max only in axiom_check.py — deliberately excluded from the consumer view (mapping.md documents this removal 'to fix the fix-mechanism leak'). The 'sum(' token in the view is the helper name deg_sum expressing the public total-degree contract, not the edit. No line discloses the max->sum edit or the pre-patch state beyond what the public problem_statement already provides. Recorded G-PANEL-3 agent_verdict NO-LEAKAGE and G-LEAK pass are consistent with this review.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
