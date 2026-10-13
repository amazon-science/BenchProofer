# P2 adversarial audit — sympy__sympy-15599

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.py`, `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -91,6 +89,9 @@
         [[Result()[k]]])))
     # post-conditions-end
     # impl-start
+    # PRE-PATCH SKELETON: the factor-by-factor reduction is absent, so every
+    # factor's value passes through unchanged (no integer coefficient is ever
+    # shrunk into the residue range).
     n = len(value)
     result = []  # type: List[int]
     k = 0
@@ -105,25 +106,17 @@
         Invariant(0 <= k and k <= n)
         Invariant(len(result) == k)
         Invariant(Forall(int, lambda b: (
-            Implies(0 <= b and b < k,
-                    result[b] == reduced_factor(is_int[b], value[b], m)),
+            Implies(0 <= b and b < k, result[b] == value[b]),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if is_int[k] == 1 and residue(value[k], m) != 0:
-            v = residue(value[k], m)
-        else:
-            v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
+        v = value[k]
         old_result = result
         result = result + [v]
         Assert(len(result) == k + 1)
         Assert(Forall(int, lambda b: (
             Implies(0 <= b and b < k, result[b] == old_result[b]),
             [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
+        Assert(result[k] == value[k])
         k = k + 1
     return result
     # impl-end
```

Attack 2 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -105,25 +103,11 @@
         Invariant(0 <= k and k <= n)
         Invariant(len(result) == k)
         Invariant(Forall(int, lambda b: (
-            Implies(0 <= b and b < k,
-                    result[b] == reduced_factor(is_int[b], value[b], m)),
+            Implies(0 <= b and b < k, result[b] == value[b]),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if is_int[k] == 1 and residue(value[k], m) != 0:
-            v = residue(value[k], m)
-        else:
-            v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
-        old_result = result
+        v = value[k]
         result = result + [v]
-        Assert(len(result) == k + 1)
-        Assert(Forall(int, lambda b: (
-            Implies(0 <= b and b < k, result[b] == old_result[b]),
-            [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
         k = k + 1
     return result
     # impl-end
```

Attack 3 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -108,22 +106,12 @@
             Implies(0 <= b and b < k,
                     result[b] == reduced_factor(is_int[b], value[b], m)),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if is_int[k] == 1 and residue(value[k], m) != 0:
+        if is_int[k] == 1:
             v = residue(value[k], m)
         else:
             v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
-        old_result = result
         result = result + [v]
-        Assert(len(result) == k + 1)
-        Assert(Forall(int, lambda b: (
-            Implies(0 <= b and b < k, result[b] == old_result[b]),
-            [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
         k = k + 1
     return result
     # impl-end
```

Attack 4 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -108,22 +106,12 @@
             Implies(0 <= b and b < k,
                     result[b] == reduced_factor(is_int[b], value[b], m)),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if is_int[k] == 1 and residue(value[k], m) != 0:
+        if residue(value[k], m) != 0:
             v = residue(value[k], m)
         else:
             v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
-        old_result = result
         result = result + [v]
-        Assert(len(result) == k + 1)
-        Assert(Forall(int, lambda b: (
-            Implies(0 <= b and b < k, result[b] == old_result[b]),
-            [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
         k = k + 1
     return result
     # impl-end
```

Attack 5 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -108,22 +106,12 @@
             Implies(0 <= b and b < k,
                     result[b] == reduced_factor(is_int[b], value[b], m)),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if is_int[k] == 1 and residue(value[k], m) != 0:
+        if m == 2 and is_int[k] == 1 and residue(value[k], m) != 0:
             v = residue(value[k], m)
         else:
             v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
-        old_result = result
         result = result + [v]
-        Assert(len(result) == k + 1)
-        Assert(Forall(int, lambda b: (
-            Implies(0 <= b and b < k, result[b] == old_result[b]),
-            [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
         k = k + 1
     return result
     # impl-end
```

Attack 6 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -94,7 +92,7 @@
     n = len(value)
     result = []  # type: List[int]
     k = 0
-    while k < n:
+    while k < n - 1:
         # invariants-start
         Invariant(Acc(list_pred(is_int), 1 / 2))
         Invariant(Acc(list_pred(value), 1 / 2))
@@ -108,22 +106,12 @@
             Implies(0 <= b and b < k,
                     result[b] == reduced_factor(is_int[b], value[b], m)),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         if is_int[k] == 1 and residue(value[k], m) != 0:
             v = residue(value[k], m)
         else:
             v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
-        old_result = result
         result = result + [v]
-        Assert(len(result) == k + 1)
-        Assert(Forall(int, lambda b: (
-            Implies(0 <= b and b < k, result[b] == old_result[b]),
-            [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
         k = k + 1
     return result
     # impl-end
```

Attack 7 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(m >= 2)
     Requires(len(is_int) == len(value))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_int), 1 / 2))
@@ -108,22 +106,12 @@
             Implies(0 <= b and b < k,
                     result[b] == reduced_factor(is_int[b], value[b], m)),
             [[result[b]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if is_int[k] == 1 and residue(value[k], m) != 0:
+        if is_int[k] != 1 and residue(value[k], m) != 0:
             v = residue(value[k], m)
         else:
             v = value[k]
-        # v is exactly the per-factor reduction for factor k.
-        Assert(v == reduced_factor(is_int[k], value[k], m))
-        old_result = result
         result = result + [v]
-        Assert(len(result) == k + 1)
-        Assert(Forall(int, lambda b: (
-            Implies(0 <= b and b < k, result[b] == old_result[b]),
-            [[result[b]]])))
-        Assert(result[k] == v)
-        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
         k = k + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-15599.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A modulo-by-an-integer of a product is simplified factor by factor. The
  product is given as a list of factors; some factors are concrete integer
  constants, the rest are opaque (symbolic) factors that the operation must
  leave untouched. The divisor is a given integer modulus m with m >= 2.

  Reducing the product modulo m rewrites each factor independently:

    - a concrete-integer factor whose value is NOT a multiple of m is replaced
      by its least non-negative residue modulo m (the value r with 0 <= r < m
      and value - r a multiple of m);
    - every other factor -- an opaque factor, or an integer factor that already
      is a multiple of m -- is kept exactly as it stands.

  Thus the factor list shrinks each integer coefficient into the residue range
  [0, m): a coefficient of 3 against modulus 2 becomes 1, a coefficient of 8
  against modulus 4 becomes 0, while a coefficient already inside [0, m) and an
  opaque symbolic factor are unchanged.

The product's factors are modelled by two parallel `List[int]`: a 0/1 tag
saying whether each factor is a concrete integer, and the integer value carried
by such a factor (irrelevant for opaque factors). Whether a factor is integral
is never altered by the rewrite, so the operation returns the new list of factor
values; the specification is carried by `PSeq[int]` via `ToSeq`.

The least-non-negative-residue primitive of the unchanged numeric layer is the
single axiomatized callee (`residue`), value-preserving and total for m >= 2;
its soundness is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def residue(value: int, m: int) -> int:
    """The unchanged numeric remainder primitive: the least non-negative residue
    of `value` modulo `m` for m >= 2. Total, deterministic and value-preserving
    in the sense that it lands in [0, m) and differs from `value` by a multiple
    of `m`.  Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(m >= 2)
    Ensures(0 <= Result() and Result() < m)
    Ensures((value - Result()) % m == 0)
    # being a residue is idempotent on values already in range
    Ensures(Implies(0 <= value and value < m, Result() == value))
# axioms-end


# pure-start
@Pure
def reduced_factor(is_int: int, value: int, m: int) -> int:
    """Value carried by one factor after reduction modulo m (m >= 2):
      integer factor not divisible by m -> its residue in [0, m)
      otherwise (opaque factor, or integer multiple of m) -> unchanged value.
    The integer-ness of a factor is never changed; only its carried value is."""
    Requires(m >= 2)
    if is_int == 1 and residue(value, m) != 0:
        return residue(value, m)
    return value
# pure-end


def reduce_coefficients(is_int: List[int], value: List[int],
                        m: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(is_int), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(m >= 2)
    Requires(len(is_int) == len(value))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_int), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(len(is_int) == len(value))
    Ensures(Acc(list_pred(Result())))
    # The reduced product keeps one value per original factor.
    Ensures(len(Result()) == len(value))
    # Every factor value is rewritten exactly by the per-factor reduction.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(value),
                Result()[k] == reduced_factor(is_int[k], value[k], m)),
        [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    n = len(value)
    result = []  # type: List[int]
    k = 0
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(is_int), 1 / 2))
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(m >= 2)
        Invariant(len(is_int) == len(value))
        Invariant(n == len(value))
        Invariant(0 <= k and k <= n)
        Invariant(len(result) == k)
        Invariant(Forall(int, lambda b: (
            Implies(0 <= b and b < k,
                    result[b] == reduced_factor(is_int[b], value[b], m)),
            [[result[b]]])))
        # invariants-end
        if is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]
        # v is exactly the per-factor reduction for factor k.
        Assert(v == reduced_factor(is_int[k], value[k], m))
        old_result = result
        result = result + [v]
        Assert(len(result) == k + 1)
        Assert(Forall(int, lambda b: (
            Implies(0 <= b and b < k, result[b] == old_result[b]),
            [[result[b]]])))
        Assert(result[k] == v)
        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
        k = k + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-15599 (nagini). VERDICT: SOUND. All commands run with python -m swebench_unified.adversary and scripts/nagini_verify.sh; resolve via swebench_unified.harness.run_resolve.

SPEC SHAPE: reduce_coefficients' postcondition is a TOTAL, DETERMINISTIC functional pin: len(Result())==len(value) AND Forall k in [0,len): Result()[k]==reduced_factor(is_int[k],value[k],m), with reduced_factor frozen in the @Pure `pure` region and residue in the frozen `axioms` region. This leaves NO room for a value-divergent impl to verify.

VALUE-REFINEMENT ATTACK SUITE (9 total; all confirmed same-spec via `adversary same-spec`): each built by editing ONLY the impl region of model.py.
- atk_prepatch.py (shipped model_prepatch.py, passthrough) -> weakness exit 2, NOT-A-COUNTEREXAMPLE (fails postcond: invariant result[b]==value[b] not preserved). This IS the prepatch bug (G-DIFF), reproduced.
- atk_1.py (passthrough variant) -> REJECTED (does not verify).
- atk_2.py (boundary: drop the `residue!=0` guard, always residue integer factors; diverges on multiples of m e.g. 8 mod 4 -> 0 vs kept 8) -> REJECTED.
- atk_3.py (control-flow-effect: drop the is_int guard, residue opaque factors too) -> REJECTED.
- atk_4.py (partial-domain: reduce only when m==2, passthrough for m>=3) -> REJECTED (spec is universal over m).
- atk_5.py (off-by-one: while k<n-1, short output list) -> REJECTED (len(Result())!=len(value)).
- atk_9.py (ungrounded-oracle/swapped branch: residue opaque factors, keep integer factors) -> REJECTED.
Every value-level wrong impl is caught by the postcondition. Positive control (unmodified model.py, pos_control.py) VERIFIES (43.3s) and is same-spec. Attacks run <=3 concurrently as background jobs (each Nagini check spawns JVM+Z3).

TWO VERIFYING CANDIDATES FOUND, BOTH SOUNDNESS ESCAPE-HATCHES (NOT refinement-fidelity defects of this bundle) — investigated, materialized, and resolve-run per protocol; NEITHER submitted as an attack because neither is an admissible/fair counterexample:

1) atk_6b.py (`Assume(False); return value`): `adversary weakness` = CANDIDATE (same-spec AND verifies, 14.7s). I MATERIALIZED its faithful refined patch patch_6b.diff (reduction block absent = prepatch behavior, since the postcondition is discharged vacuously) and RAN it: run_resolve -> resolved=False, completed=True (EXECUTED, not speculated; gold sanity-resolved=True in the same harness). SO its faithful patch genuinely does NOT resolve. HOWEVER atk_6b relies on `Assume(`, which is a BANNED TOKEN for the nagini backend (backends/nagini.py banned_tokens=('Assume(','Refute(')); gates/hygiene.py `_banned_calls` FAILS any model containing it. The real model.py is hygiene-clean (verified: ast scan shows zero banned calls). An Assume(False) model is INADMISSIBLE — it would trivially 'break' EVERY nagini bundle and can never be an accepted model. The runner's check_attack does NOT re-screen G-HYGIENE, so submitting atk_6b would mechanically flip the gate to BROKEN spuriously; I deliberately do NOT submit it. This is a runner-coverage gap (eq/panel_1 candidate path omits the hygiene screen), NOT a spec-too-weak / refinement-infidelity defect of sympy__sympy-15599.

2) atk_8.py (`k = k`, loop counter never advances; NO banned token, hygiene-clean): `adversary weakness` = CANDIDATE (same-spec AND verifies, 19.2s). It verifies by PARTIAL CORRECTNESS: the post-loop return is reachable only when k>=n which, with the invariant len(result)==k==0, forces n==0; for n>0 the loop diverges so the postcondition is vacuous. I MATERIALIZED its faithful patch patch_8.diff (gold reduction block rewritten as a while-loop that never increments -> infinite loop in Mod.eval's Mul branch) and RAN run_resolve(timeout=300): completed=False (harness produced no report / hang under contention) — i.e. it does NOT complete, which the official runner treats as INCONCLUSIVE, never BROKEN (only completed AND not resolved => BROKEN). No completed non-resolve could be exhibited. More fundamentally, non-termination is a documented, methodology-WIDE property: prompts/nagini/quickref.md states 'Termination proofs are NOT required by default (no Decreases needed)'; there is NO MustTerminate requirement anywhere in the unified pipeline (grep clean); 420/500 verified nagini bundles carry no MustTerminate. A non-terminating vacuous verifier is a universal partial-correctness escape hatch, not a model<->patch correspondence weakness specific to THIS bundle's refinement.md. Not a fair G-EQ counterexample.

REFINEMENT.MD A-LEG AUDIT (deep model / axiom references, plan §4): 6 legs, all R / A-reference / I, NO kind-3, NO A-consumed. A1=R (List[int] parallel carriers <-> non_mod_l), A2=R (m>=2 <-> q.is_Integer and q is not S.One), A3=I (while loop <-> for i in non_mod_l), A4=A-reference (per-factor rewrite modeled DEEPLY by reduced_factor; residue <-> Integer.__mod__; proof uses only @Pure determinism, not Ensures), A5=I (append), A6=R (return list <-> non_mod_l=_; p=Mul(*(non_mod_l+mod_l))). A-leg CORRESPONDENCE VALIDATED: ran benchmark-verified/.../axiom_check.py with real sympy 1.14.0 -> exit 0 ('residue axiom == sympy Integer % sound on 162 boundary + 50000 fuzz pairs; reduced_factor deep model == sympy factor rewrite on boundary + 20000 fuzz factors'). No double-mask: axiom_check asserts is_int-tag-level equivalence and preserves opaque factors, not a value-membership proxy.

CONCLUSION: every VALUE-refinement attack (the class G-EQ targets) is rejected by the frozen spec; the positive control verifies; the prepatch bug is reproduced; the two verifying impls are backend-wide soundness escape hatches screened by G-HYGIENE (Assume) or excluded by the methodology (non-termination), neither a refinement-fidelity break of this bundle; A-legs correspond to the real callees (G-AX green). verify => correct holds on the tested/modeled domain. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.py`, `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-15599.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A modulo-by-an-integer of a product is simplified factor by factor. The
  product is given as a list of factors; some factors are concrete integer
  constants, the rest are opaque (symbolic) factors that the operation must
  leave untouched. The divisor is a given integer modulus m with m >= 2.

  Reducing the product modulo m rewrites each factor independently:

    - a concrete-integer factor whose value is NOT a multiple of m is replaced
      by its least non-negative residue modulo m (the value r with 0 <= r < m
      and value - r a multiple of m);
    - every other factor -- an opaque factor, or an integer factor that already
      is a multiple of m -- is kept exactly as it stands.

  Thus the factor list shrinks each integer coefficient into the residue range
  [0, m): a coefficient of 3 against modulus 2 becomes 1, a coefficient of 8
  against modulus 4 becomes 0, while a coefficient already inside [0, m) and an
  opaque symbolic factor are unchanged.

The product's factors are modelled by two parallel `List[int]`: a 0/1 tag
saying whether each factor is a concrete integer, and the integer value carried
by such a factor (irrelevant for opaque factors). Whether a factor is integral
is never altered by the rewrite, so the operation returns the new list of factor
values; the specification is carried by `PSeq[int]` via `ToSeq`.

The least-non-negative-residue primitive of the unchanged numeric layer is the
single axiomatized callee (`residue`), value-preserving and total for m >= 2;
its soundness is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def residue(value: int, m: int) -> int:
    """The unchanged numeric remainder primitive: the least non-negative residue
    of `value` modulo `m` for m >= 2. Total, deterministic and value-preserving
    in the sense that it lands in [0, m) and differs from `value` by a multiple
    of `m`.  Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(m >= 2)
    Ensures(0 <= Result() and Result() < m)
    Ensures((value - Result()) % m == 0)
    # being a residue is idempotent on values already in range
    Ensures(Implies(0 <= value and value < m, Result() == value))
# axioms-end


# pure-start
@Pure
def reduced_factor(is_int: int, value: int, m: int) -> int:
    """Value carried by one factor after reduction modulo m (m >= 2):
      integer factor not divisible by m -> its residue in [0, m)
      otherwise (opaque factor, or integer multiple of m) -> unchanged value.
    The integer-ness of a factor is never changed; only its carried value is."""
    Requires(m >= 2)
    if is_int == 1 and residue(value, m) != 0:
        return residue(value, m)
    return value
# pure-end


def reduce_coefficients(is_int: List[int], value: List[int],
                        m: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(is_int), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(m >= 2)
    Requires(len(is_int) == len(value))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_int), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(len(is_int) == len(value))
    Ensures(Acc(list_pred(Result())))
    # The reduced product keeps one value per original factor.
    Ensures(len(Result()) == len(value))
    # Every factor value is rewritten exactly by the per-factor reduction.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(value),
                Result()[k] == reduced_factor(is_int[k], value[k], m)),
        [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    n = len(value)
    result = []  # type: List[int]
    k = 0
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(is_int), 1 / 2))
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(m >= 2)
        Invariant(len(is_int) == len(value))
        Invariant(n == len(value))
        Invariant(0 <= k and k <= n)
        Invariant(len(result) == k)
        Invariant(Forall(int, lambda b: (
            Implies(0 <= b and b < k,
                    result[b] == reduced_factor(is_int[b], value[b], m)),
            [[result[b]]])))
        # invariants-end
        if is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]
        # v is exactly the per-factor reduction for factor k.
        Assert(v == reduced_factor(is_int[k], value[k], m))
        old_result = result
        result = result + [v]
        Assert(len(result) == k + 1)
        Assert(Forall(int, lambda b: (
            Implies(0 <= b and b < k, result[b] == old_result[b]),
            [[result[b]]])))
        Assert(result[k] == v)
        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
        k = k + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-15599 (nagini). VERDICT: SOUND. All commands run with python -m swebench_unified.adversary and scripts/nagini_verify.sh; resolve via swebench_unified.harness.run_resolve.

SPEC SHAPE: reduce_coefficients' postcondition is a TOTAL, DETERMINISTIC functional pin: len(Result())==len(value) AND Forall k in [0,len): Result()[k]==reduced_factor(is_int[k],value[k],m), with reduced_factor frozen in the @Pure `pure` region and residue in the frozen `axioms` region. This leaves NO room for a value-divergent impl to verify.

VALUE-REFINEMENT ATTACK SUITE (9 total; all confirmed same-spec via `adversary same-spec`): each built by editing ONLY the impl region of model.py.
- atk_prepatch.py (shipped model_prepatch.py, passthrough) -> weakness exit 2, NOT-A-COUNTEREXAMPLE (fails postcond: invariant result[b]==value[b] not preserved). This IS the prepatch bug (G-DIFF), reproduced.
- atk_1.py (passthrough variant) -> REJECTED (does not verify).
- atk_2.py (boundary: drop the `residue!=0` guard, always residue integer factors; diverges on multiples of m e.g. 8 mod 4 -> 0 vs kept 8) -> REJECTED.
- atk_3.py (control-flow-effect: drop the is_int guard, residue opaque factors too) -> REJECTED.
- atk_4.py (partial-domain: reduce only when m==2, passthrough for m>=3) -> REJECTED (spec is universal over m).
- atk_5.py (off-by-one: while k<n-1, short output list) -> REJECTED (len(Result())!=len(value)).
- atk_9.py (ungrounded-oracle/swapped branch: residue opaque factors, keep integer factors) -> REJECTED.
Every value-level wrong impl is caught by the postcondition. Positive control (unmodified model.py, pos_control.py) VERIFIES (43.3s) and is same-spec. Attacks run <=3 concurrently as background jobs (each Nagini check spawns JVM+Z3).

TWO VERIFYING CANDIDATES FOUND, BOTH SOUNDNESS ESCAPE-HATCHES (NOT refinement-fidelity defects of this bundle) — investigated, materialized, and resolve-run per protocol; NEITHER submitted as an attack because neither is an admissible/fair counterexample:

1) atk_6b.py (`Assume(False); return value`): `adversary weakness` = CANDIDATE (same-spec AND verifies, 14.7s). I MATERIALIZED its faithful refined patch patch_6b.diff (reduction block absent = prepatch behavior, since the postcondition is discharged vacuously) and RAN it: run_resolve -> resolved=False, completed=True (EXECUTED, not speculated; gold sanity-resolved=True in the same harness). SO its faithful patch genuinely does NOT resolve. HOWEVER atk_6b relies on `Assume(`, which is a BANNED TOKEN for the nagini backend (backends/nagini.py banned_tokens=('Assume(','Refute(')); gates/hygiene.py `_banned_calls` FAILS any model containing it. The real model.py is hygiene-clean (verified: ast scan shows zero banned calls). An Assume(False) model is INADMISSIBLE — it would trivially 'break' EVERY nagini bundle and can never be an accepted model. The runner's check_attack does NOT re-screen G-HYGIENE, so submitting atk_6b would mechanically flip the gate to BROKEN spuriously; I deliberately do NOT submit it. This is a runner-coverage gap (eq/panel_1 candidate path omits the hygiene screen), NOT a spec-too-weak / refinement-infidelity defect of sympy__sympy-15599.

2) atk_8.py (`k = k`, loop counter never advances; NO banned token, hygiene-clean): `adversary weakness` = CANDIDATE (same-spec AND verifies, 19.2s). It verifies by PARTIAL CORRECTNESS: the post-loop return is reachable only when k>=n which, with the invariant len(result)==k==0, forces n==0; for n>0 the loop diverges so the postcondition is vacuous. I MATERIALIZED its faithful patch patch_8.diff (gold reduction block rewritten as a while-loop that never increments -> infinite loop in Mod.eval's Mul branch) and RAN run_resolve(timeout=300): completed=False (harness produced no report / hang under contention) — i.e. it does NOT complete, which the official runner treats as INCONCLUSIVE, never BROKEN (only completed AND not resolved => BROKEN). No completed non-resolve could be exhibited. More fundamentally, non-termination is a documented, methodology-WIDE property: prompts/nagini/quickref.md states 'Termination proofs are NOT required by default (no Decreases needed)'; there is NO MustTerminate requirement anywhere in the unified pipeline (grep clean); 420/500 verified nagini bundles carry no MustTerminate. A non-terminating vacuous verifier is a universal partial-correctness escape hatch, not a model<->patch correspondence weakness specific to THIS bundle's refinement.md. Not a fair G-EQ counterexample.

REFINEMENT.MD A-LEG AUDIT (deep model / axiom references, plan §4): 6 legs, all R / A-reference / I, NO kind-3, NO A-consumed. A1=R (List[int] parallel carriers <-> non_mod_l), A2=R (m>=2 <-> q.is_Integer and q is not S.One), A3=I (while loop <-> for i in non_mod_l), A4=A-reference (per-factor rewrite modeled DEEPLY by reduced_factor; residue <-> Integer.__mod__; proof uses only @Pure determinism, not Ensures), A5=I (append), A6=R (return list <-> non_mod_l=_; p=Mul(*(non_mod_l+mod_l))). A-leg CORRESPONDENCE VALIDATED: ran benchmark-verified/.../axiom_check.py with real sympy 1.14.0 -> exit 0 ('residue axiom == sympy Integer % sound on 162 boundary + 50000 fuzz pairs; reduced_factor deep model == sympy factor rewrite on boundary + 20000 fuzz factors'). No double-mask: axiom_check asserts is_int-tag-level equivalence and preserves opaque factors, not a value-membership proxy.

CONCLUSION: every VALUE-refinement attack (the class G-EQ targets) is rejected by the frozen spec; the positive control verifies; the prepatch bug is reproduced; the two verifying impls are backend-wide soundness escape hatches screened by G-HYGIENE (Assume) or excluded by the methodology (non-termination), neither a refinement-fidelity break of this bundle; A-legs correspond to the real callees (G-AX green). verify => correct holds on the tested/modeled domain. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/spec-drift check for the nagini bundle sympy__sympy-15599 (modeled function reduce_coefficients / reduced_factor / residue vs. the real repo per-factor integer-coefficient rewrite in Mod.eval's Mul branch).

Method: (1) same-spec command confirms the spec region is intact (SAME). Built a base_commit (5e17a90c) worktree, applied the gold patch, and extracted the REAL rewrite conditional from the patched Mod.eval via AST (the unique `if q.is_Integer...` block with a for-loop over non_mod_l), then executed the real statement object directly. (3) Differential-compared the model against the real block.

Modeled domain: m >= 2, factors as parallel List[int] with 0/1 integer-ness tag. reduced_factor: integer factor (is_int==1) with value%m != 0 -> value%m; otherwise (opaque, or integer multiple of m) -> unchanged. This is the least-non-negative residue (Python floored mod), which matches sympy Integer.__mod__ for positive divisors.

Coverage of the differential: integer factors straddling residue boundaries (v near 0, +/-m, +/-2m) at moduli 2..59, 100, 1000, 65536, 2**31, 10**18; extreme magnitudes (+/-10**18, +/-2**63); opaque factors (i, x, i*x, x**2, Rational 7/2, 1/3) which must be left identically unchanged; and 20000 random fuzz inputs (m in 2..10**6, v in +/-10**9). Result: ZERO disagreements. Multiples of m correctly map to 'unchanged' matching the real `i % q is not S.Zero` identity guard; opaque objects are returned as the identical object.

Note on domain: the real guard `q.is_Integer and q is not S.One` is broader than the model's m>=2 (it also admits negative integer divisors), but mapping.md explicitly excludes negative/zero divisors from the modeled domain and they are not tested. This is under-modeling (narrower domain), NOT a spec-too-strong divergence: on every input within the modeled domain the modeled function agrees with the real callee. No diverging input where the spec disagrees with real behavior was found. Recorded gates (G-EQ, G-AX, G-CONF, G-DIFF, all panels) are consistent with this conclusion.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen PASSES (no hard failures, no warnings): no diff markers, no gold-patch line reproduced (len>=8 normalized), no patched file path (sympy/core/mod.py) or dotted module, no spec-view identifier embedding a patched repo symbol (only patched def is 'doit', which appears nowhere), no bug/fix/patch narration in comments/docstrings. All model identifiers (reduce_coefficients, reduced_factor, residue, is_int, value, m) are model-local carriers, not repo symbols (the repo internals non_mod_l / Mod.eval / doit / cls do not appear in the spec view).

Semantic check: the public problem_statement is unusually revealing already — it contains a suggested diff (`non_mod_l = [cls(x, q) for x in non_mod_l]`), the target behavior `Mod(3*i, 2) == Mod(i, 2)`, and the added test. The spec view describes exactly this behavior at a behavioral-abstraction altitude: reduce each product factor independently, replacing an integer factor not divisible by m with its least-non-negative residue in [0,m) and leaving opaque/multiple factors unchanged. The worked example '3 mod 2 -> 1' is the public Mod(3*i,2)->Mod(i,2) case; '8 mod 4 -> 0' is the natural generalization derivable from the general rule, not an edit-specific secret. Nothing in the spec view localizes the edit (function/file/line) beyond what problem_statement already discloses. hints_text was not used for the judgment.

Verified the spec/pure/axiom regions are the frozen model regions; impl is elided in the view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
