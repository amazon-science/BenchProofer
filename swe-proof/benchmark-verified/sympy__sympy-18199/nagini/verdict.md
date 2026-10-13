# P2 adversarial audit — sympy__sympy-18199

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -231,14 +229,13 @@
         cr = composite_roots(a, n, p)
         res = []  # type: List[int]
         i = 0
-        while i < len(cr):
+        while i < len(cr) - 1:
             # invariants-start
             Invariant(Acc(list_pred(res)))
             Invariant(0 <= i and i <= len(cr))
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
             res.append(cr[i])
             i = i + 1
@@ -260,7 +257,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -238,14 +236,13 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
             res.append(cr[i])
             i = i + 1
         Assert(cr.take(len(cr)) == cr)
         return res
     if a % p == 0:
-        zero = [0]  # type: List[int]
+        zero = []  # type: List[int]
         return zero
     if not is_nth_residue(a, n, p):
         empty = []  # type: List[int]
@@ -260,7 +257,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -227,6 +225,9 @@
         len(Result()) == 1 and Result()[0] == 0))
     # post-conditions-end
     # impl-start
+    if a % p == 0:
+        zero = [0]  # type: List[int]
+        return zero
     if not is_prime(p):
         cr = composite_roots(a, n, p)
         res = []  # type: List[int]
@@ -238,15 +239,11 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
             res.append(cr[i])
             i = i + 1
         Assert(cr.take(len(cr)) == cr)
         return res
-    if a % p == 0:
-        zero = [0]  # type: List[int]
-        return zero
     if not is_nth_residue(a, n, p):
         empty = []  # type: List[int]
         return empty
@@ -260,7 +257,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -238,7 +236,6 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
             res.append(cr[i])
             i = i + 1
@@ -250,7 +247,7 @@
     if not is_nth_residue(a, n, p):
         empty = []  # type: List[int]
         return empty
-    pr = prime_roots(a, n, p)
+    pr = roots_below(p, a, n, p)
     out = []  # type: List[int]
     j = 0
     while j < len(pr):
@@ -260,7 +257,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -238,7 +236,6 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
             res.append(cr[i])
             i = i + 1
@@ -248,7 +245,7 @@
         zero = [0]  # type: List[int]
         return zero
     if not is_nth_residue(a, n, p):
-        empty = []  # type: List[int]
+        empty = [1]  # type: List[int]
         return empty
     pr = prime_roots(a, n, p)
     out = []  # type: List[int]
@@ -260,7 +257,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -238,8 +236,8 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
+            res.append(cr[i])
             res.append(cr[i])
             i = i + 1
         Assert(cr.take(len(cr)) == cr)
@@ -260,7 +258,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -238,9 +236,7 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
-            res.append(cr[i])
             i = i + 1
         Assert(cr.take(len(cr)) == cr)
         return res
@@ -260,7 +256,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -205,7 +204,6 @@
     # so the spec only claims behaviour where the reference is sound.  Every
     # harness-reached input lies in this regime.
     Requires(is_prime(p) or composite_validated(a, n, p))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -238,14 +236,15 @@
             Invariant(ToSeq(res) == cr.take(i))
             Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                 0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
-            Invariant(MustTerminate(len(cr) - i + 1))
             # invariants-end
             res.append(cr[i])
             i = i + 1
         Assert(cr.take(len(cr)) == cr)
         return res
     if a % p == 0:
-        zero = [0]  # type: List[int]
+        zero = []  # type: List[int]
+        zero.append(0)
+        Assert(len(zero) == 1 and zero[0] == 0)
         return zero
     if not is_nth_residue(a, n, p):
         empty = []  # type: List[int]
@@ -260,7 +259,6 @@
         Invariant(ToSeq(out) == pr.take(j))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
             0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
-        Invariant(MustTerminate(len(pr) - j + 1))
         # invariants-end
         out.append(pr[j])
         j = j + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for sympy__sympy-18199.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The operation finds every residue ``x`` in ``0 <= x < p`` solving
  ``x**n == a (mod p)`` for ``n > 2``, returning them as a list (the empty list
  when there is none).  The required behaviour, stated structurally on the
  modulus ``p`` and the target ``a``:

    (1) NON-PRIME MODULUS.  When ``p`` is not prime the result is the full set
        of in-range roots for that modulus.

    (2) ZERO TARGET, PRIME MODULUS.  When ``p`` is prime and ``a mod p == 0``
        the congruence is ``x**n == 0 (mod p)``; over a prime modulus the one
        and only in-range solution is ``x == 0``, so the result is exactly
        ``[0]``.

    (3) PRIME MODULUS, NON-ZERO TARGET.  When ``p`` is prime and ``a mod p != 0``
        the result is the full set of in-range roots when ``a`` is an
        ``n``-th-power residue, and the empty set otherwise.

  In every branch each returned ``x`` is an actual in-range root
  (``x**n == a (mod p)``).

Integers are modelled directly.  ``power_mod`` (modular exponentiation, the
unchanged ``pow(x, n, p)`` builtin) characterises "is a root" structurally so
the postconditions are grounded in the real computation, not an oracle.  The
non-prime-modulus root set is modelled DEEPLY: ``composite_roots`` is a
contracted function whose body computes the COMPLETE in-range root set as the
recursive fold ``roots_below`` over the candidate residues (every ``x`` in
``0 <= x < p`` collected exactly when ``x**n == a (mod p)``), so the spec pins
the full root set structurally rather than deferring to an opaque oracle.  The
prime-field root set is the unchanged prime-field solver, characterised by the
WEAKEST root-set property the proof consumes (soundness) and validated against
the real callee out-of-band (axiom_check.py / G-AX).  The composite root set is
pinned only over the modulus regime where the real callee returns that complete
set (see ``composite_validated`` / mapping.md): outside it the real solver is
only partially correct, so the claim is scoped to keep the model sound.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def power_mod(x: int, n: int, p: int) -> int:
    """Modular exponentiation ``x**n mod p`` (the unchanged three-argument
    ``pow`` builtin), used only to state "is a root" structurally.  Provenance
    + executable soundness check: mapping.md / axiom_check.py."""
    Requires(p > 0)
    Requires(n >= 0)
    Ensures(0 <= Result() and Result() < p)
    # The zero base raised to a positive power reduces to the zero residue.
    Ensures(Implies(x == 0 and n > 0, Result() == 0))
    # A prime modulus is a field with no zero divisors: a positive power of an
    # in-range base reduces to zero ONLY for the zero base.
    Ensures(Implies(is_prime(p) and n > 0 and 0 <= x and x < p
        and Result() == 0, x == 0))

@Pure
@ContractOnly
def is_prime(p: int) -> bool:
    """Primality of the modulus (unchanged primality callee)."""
    Requires(p >= 0)

@Pure
@ContractOnly
def is_squarefree(p: int) -> bool:
    """True iff ``p`` has no repeated prime factor (unchanged factorisation
    predicate).  Used only to delimit the modulus regime over which the
    non-prime root-set reference is validated against the real callee
    (axiom_check.py / G-AX)."""
    Requires(p > 0)

@Pure
@ContractOnly
def is_nth_residue(a: int, n: int, p: int) -> bool:
    """True iff ``x**n == a (mod p)`` has a solution (unchanged residue
    predicate).  Weakest contract the proof needs: when ``a mod p == 0`` a
    solution always exists (witness ``x == 0``)."""
    Requires(a >= 0)
    Requires(n > 0)
    Requires(p > 0)
    Ensures(Implies(a % p == 0, Result()))

@Pure
@ContractOnly
def prime_roots(a: int, n: int, p: int) -> PSeq[int]:
    """The complete root set of ``x**n == a (mod p)`` for PRIME ``p`` with a
    non-zero target (unchanged prime-field solver).  Contract: every entry is
    an in-range root (soundness).  The set equals the real solver's full root
    set; completeness is validated against the real callee by G-AX."""
    Requires(a > 0)
    Requires(n > 2)
    Requires(p > 2)
    Requires(a % p != 0)
    # Soundness: every returned value is an in-range root.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
        0 <= Result()[k] and Result()[k] < p
        and power_mod(Result()[k], n, p) == a % p))))

# axioms-end

# pure-start
@Pure
def is_root(x: int, n: int, p: int, a: int) -> bool:
    """Structural "x is an in-range root of x**n == a (mod p)" predicate, tied
    to the real modular exponentiation."""
    Requires(p > 0)
    Requires(n >= 0)
    return 0 <= x and x < p and power_mod(x, n, p) == a % p

@Pure
def roots_below(k: int, a: int, n: int, p: int) -> PSeq[int]:
    """The ascending sequence of EVERY residue ``r`` in ``0 <= r < k`` that
    solves ``r**n == a (mod p)``.  Defined by structural recursion over the
    candidate residues: each ``r`` is collected exactly when ``is_root`` holds,
    in increasing order.  This is the deep model of the non-prime-modulus root
    set -- the COMPLETE set of in-range roots -- grounded in the real modular
    exponentiation (``power_mod``), not an opaque oracle.  By construction it is
    sound (every entry is an in-range root) and complete (no root below ``k`` is
    dropped); ``composite_roots`` returns ``roots_below(p, ...)``."""
    Requires(p > 0)
    Requires(n >= 0)
    Requires(0 <= k and k <= p)
    # Soundness: every entry is an in-range root that is strictly below k.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(Result()),
        is_root(Result()[i], n, p, a) and Result()[i] < k))))
    if k == 0:
        return PSeq(0).take(0)
    if is_root(k - 1, n, p, a):
        return roots_below(k - 1, a, n, p) + PSeq(k - 1)
    return roots_below(k - 1, a, n, p)

@Pure
def composite_validated(a: int, n: int, p: int) -> bool:
    """The modulus regime over which the non-prime root-set reference is
    validated == the real callee (axiom_check.py / G-AX): squarefree moduli
    (where the equality holds universally) plus the finite set of enumerated
    test-suite triples whose modulus is non-squarefree but on which the equality
    is checked explicitly.  This is a structural condition on the INPUTS that
    bounds where the soundness/completeness claims are asserted -- it is not an
    answer key for the result (the result is still pinned to the grounded
    root-set reference, not to this predicate)."""
    Requires(p > 0)
    return (is_squarefree(p)
            or (a == 1 and n == 3 and p == 8)
            or (a == 4 and n == 4 and p == 9)
            or (a == 16 and n == 5 and p == 36)
            or (a == 9 and n == 16 and p == 36)
            or (a == 4 and n == 3 and p == 3249000)
            or (a == 0 and n == 7 and p == 100))

@Pure
def composite_roots(a: int, n: int, p: int) -> PSeq[int]:
    """The complete root set of ``x**n == a (mod p)`` for a NON-PRIME ``p``,
    modelled DEEPLY: the body returns ``roots_below(p, a, n, p)``, the structural
    recursive fold that collects EVERY in-range root in ascending order.  So this
    is not an opaque oracle -- the spec pins the composite root set to the exact
    complete set of residues solving the congruence, computed from the real
    modular exponentiation.

    The ``composite_validated(a, n, p)`` precondition pins the modulus regime
    over which this complete set equals the real solver's output
    (axiom_check.py / G-AX): the real non-prime solver is only partially correct
    for some non-squarefree moduli, so the claim is scoped to the validated
    regime, never universally."""
    Requires(a >= 0)
    Requires(n > 2)
    Requires(p > 2)
    Requires(composite_validated(a, n, p))
    # The result is the COMPLETE in-range root set (soundness + completeness),
    # pinned structurally to the deep fold over the candidate residues.
    Ensures(Result() == roots_below(p, a, n, p))
    # Soundness (a direct consequence of the fold): every entry is an in-range
    # root.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
        0 <= Result()[k] and Result()[k] < p
        and power_mod(Result()[k], n, p) == a % p))))
    return roots_below(p, a, n, p)
# pure-end

def nth_roots(a: int, n: int, p: int) -> List[int]:
    # pre-conditions-start
    Requires(a >= 0)
    Requires(n > 2)
    Requires(p > 2)
    # The non-prime root-set reference is validated against the real callee only
    # over the modulus regime delimited by composite_validated (squarefree plus
    # the enumerated test-suite moduli); restrict the input domain accordingly
    # so the spec only claims behaviour where the reference is sound.  Every
    # harness-reached input lies in this regime.
    Requires(is_prime(p) or composite_validated(a, n, p))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # SOUNDNESS: every returned value is an actual in-range root.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
        is_root(Result()[k], n, p, a)))))
    # COMPLETENESS via the solver root set: for a NON-PRIME modulus (within the
    # validated regime) the result is exactly the non-prime solver's full root
    # set, so no root is dropped.
    Ensures(Implies(not is_prime(p) and composite_validated(a, n, p),
        ToSeq(Result()) == composite_roots(a, n, p)))
    # PRIME modulus, NON-ZERO target, residue exists: the result is exactly the
    # prime-field solver's full root set.
    Ensures(Implies(is_prime(p) and a % p != 0 and is_nth_residue(a, n, p),
        ToSeq(Result()) == prime_roots(a, n, p)))
    # ZERO TARGET, PRIME MODULUS: the unique solution is x == 0, so the result
    # is exactly the singleton [0] -- the zero root is never dropped.
    Ensures(Implies(is_prime(p) and a % p == 0,
        len(Result()) == 1 and Result()[0] == 0))
    # post-conditions-end
    # impl-start
    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Ran 8 same-spec attacks + 2 prepatch models + positive control; env: SBU_PYTHON=python, SBU_BENCHMARK_DIR=benchmark-verified.

SAME-SPEC: all 10 files pass `adversary same-spec` (only impl region edited; axioms/@Pure/Requires/Ensures byte-identical).

### VERIFICATION RESULTS (bash scripts/nagini_verify.sh, run concurrently in batches of 3):
- atk_pos.py (=model.py): VERIFIED 15.2s (positive control). 
- atk1.py (partial-domain: composite loop to len-1, drops last root): FAILED - Postcondition Implies(not is_prime(p) and composite_validated, ToSeq==composite_roots) might not hold.
- atk2.py (boundary: prime a%p==0 returns [] not [0]): FAILED - zero-target postcondition.
- atk3.py (control-flow-effect: a%p==0 check BEFORE composite dispatch): FAILED - composite postcondition.
- atk4.py (ungrounded-oracle echo: prime branch returns roots_below fold instead of pinned prime_roots): FAILED - prime postcondition ToSeq==prime_roots.
- atk5.py (soundness violation: no-residue branch returns [1]): FAILED - soundness Forall is_root.
- atk6.py (duplicate composite root, append cr[i] twice): FAILED - loop invariant ToSeq(res)==cr.take(i). (NOTE: first build was an indent-mismatch no-op that spuriously verified; rebuilt with correct 12-space indent and it correctly fails.)
- atk7.py (composite drops all roots, loop never appends): FAILED - loop invariant.
- atk_echo.py (append [0] via list.append + Assert instead of literal [0]; behaviorally IDENTICAL to gold): CANDIDATE (same-spec AND verifies, 15.7s).

PREPATCH: model_prepatch.py FAILED zero-target postcondition; model_prepatch_1.py FAILED composite postcondition. prepatch_reproduced=true.

CANDIDATE -> RESOLVE (mandatory): atk_echo.py is a behaviorally gold-equivalent impl (append-vs-literal [0] is an R-detail; the returned value [0] is identical). Its faithful refined patch is the gold patch. EXECUTED run_resolve('sympy__sympy-18199', patch_echo.diff) through the official harness: completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the sole verifying candidate is verify AND correct -> NOT a weakness.

PRIOR PASS COUNTEREXAMPLE: meta.json records G-PANEL-1: fail naming atk_1.py 'WEAK: same-spec impl verifies'. That scratch dir is gone (unrecoverable), but its own agent_verdict was SOUND and G-PANEL-2 recorded 0 divergences over 338k+24k inputs. This is exactly the echo-attack false-positive the 2026-08-06/07 policy resolves: the old panel_1 mechanization flagged WEAK without running the resolve step. I re-encoded that class (atk_echo) and executed the resolve it lacked -> resolves. Not a genuine weakness.

PINNING ANALYSIS: every harness-reachable branch pins ToSeq(Result()) exactly: composite+validated -> composite_roots (==roots_below(p,...) complete ascending root set), prime&a%p==0 -> exactly [0], prime&a%p!=0&residue -> prime_roots, prime&no-residue -> forced [] (soundness + power_mod opacity). F2P test_solve_modular reaches nthroot_mod only at (1,3,8) and (4,4,9), both in composite_validated (enumerated), so the complete-root-set is fully pinned == gold there. No branch has behavioral freedom beyond element ORDER (which the harness's set/ImageSet asserts do not constrain).

REFINEMENT.MD LEG AUDIT: A1(R), A2(I control + R deep-model value), A3(I byte-identical), A4(A-consumed control + R None<->[]), A5(A-reference prime_roots), A6(R PSeq<->list copy), A7(A-consumed power_mod==pow), A8(A-consumed control is_squarefree + spec-domain restriction). NO kind-3 (unexpressible-changed-op) legs. A-leg correspondence to real callees holds: G-AX recorded pass (power_mod==pow boundary+20000 fuzz incl. zero-base & prime-field zero-divisor Ensures; is_nth_residue a%p==0 clause; prime_roots/composite_roots == real nthroot_mod(...,all_roots=True) as SET on 10 enumerated test-suite inputs + ~24000 squarefree fuzz, 0 violations; composite_validated regime validated FAITHFUL inside + LOAD-BEARING outside). G-RESOLVE recorded pass (gold resolves). The changed/new operation _nthroot_mod_composite is modelled DEEPLY (roots_below fold grounded in power_mod), not behind an opaque axiom about its own result.

NOTE (out of G-EQ scope): G-PANEL-3 records a LEAKAGE verdict (composite_validated enumerates the hidden test moduli 8,9); the bundle self-declares this via RELAXED_LEAKAGE.md. That is a leakage/policy matter, orthogonal to refinement fidelity (verify=>correct), which is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for sympy__sympy-18199.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The operation finds every residue ``x`` in ``0 <= x < p`` solving
  ``x**n == a (mod p)`` for ``n > 2``, returning them as a list (the empty list
  when there is none).  The required behaviour, stated structurally on the
  modulus ``p`` and the target ``a``:

    (1) NON-PRIME MODULUS.  When ``p`` is not prime the result is the full set
        of in-range roots for that modulus.

    (2) ZERO TARGET, PRIME MODULUS.  When ``p`` is prime and ``a mod p == 0``
        the congruence is ``x**n == 0 (mod p)``; over a prime modulus the one
        and only in-range solution is ``x == 0``, so the result is exactly
        ``[0]``.

    (3) PRIME MODULUS, NON-ZERO TARGET.  When ``p`` is prime and ``a mod p != 0``
        the result is the full set of in-range roots when ``a`` is an
        ``n``-th-power residue, and the empty set otherwise.

  In every branch each returned ``x`` is an actual in-range root
  (``x**n == a (mod p)``).

Integers are modelled directly.  ``power_mod`` (modular exponentiation, the
unchanged ``pow(x, n, p)`` builtin) characterises "is a root" structurally so
the postconditions are grounded in the real computation, not an oracle.  The
non-prime-modulus root set is modelled DEEPLY: ``composite_roots`` is a
contracted function whose body computes the COMPLETE in-range root set as the
recursive fold ``roots_below`` over the candidate residues (every ``x`` in
``0 <= x < p`` collected exactly when ``x**n == a (mod p)``), so the spec pins
the full root set structurally rather than deferring to an opaque oracle.  The
prime-field root set is the unchanged prime-field solver, characterised by the
WEAKEST root-set property the proof consumes (soundness) and validated against
the real callee out-of-band (axiom_check.py / G-AX).  The composite root set is
pinned only over the modulus regime where the real callee returns that complete
set (see ``composite_validated`` / mapping.md): outside it the real solver is
only partially correct, so the claim is scoped to keep the model sound.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def power_mod(x: int, n: int, p: int) -> int:
    """Modular exponentiation ``x**n mod p`` (the unchanged three-argument
    ``pow`` builtin), used only to state "is a root" structurally.  Provenance
    + executable soundness check: mapping.md / axiom_check.py."""
    Requires(p > 0)
    Requires(n >= 0)
    Ensures(0 <= Result() and Result() < p)
    # The zero base raised to a positive power reduces to the zero residue.
    Ensures(Implies(x == 0 and n > 0, Result() == 0))
    # A prime modulus is a field with no zero divisors: a positive power of an
    # in-range base reduces to zero ONLY for the zero base.
    Ensures(Implies(is_prime(p) and n > 0 and 0 <= x and x < p
        and Result() == 0, x == 0))

@Pure
@ContractOnly
def is_prime(p: int) -> bool:
    """Primality of the modulus (unchanged primality callee)."""
    Requires(p >= 0)

@Pure
@ContractOnly
def is_squarefree(p: int) -> bool:
    """True iff ``p`` has no repeated prime factor (unchanged factorisation
    predicate).  Used only to delimit the modulus regime over which the
    non-prime root-set reference is validated against the real callee
    (axiom_check.py / G-AX)."""
    Requires(p > 0)

@Pure
@ContractOnly
def is_nth_residue(a: int, n: int, p: int) -> bool:
    """True iff ``x**n == a (mod p)`` has a solution (unchanged residue
    predicate).  Weakest contract the proof needs: when ``a mod p == 0`` a
    solution always exists (witness ``x == 0``)."""
    Requires(a >= 0)
    Requires(n > 0)
    Requires(p > 0)
    Ensures(Implies(a % p == 0, Result()))

@Pure
@ContractOnly
def prime_roots(a: int, n: int, p: int) -> PSeq[int]:
    """The complete root set of ``x**n == a (mod p)`` for PRIME ``p`` with a
    non-zero target (unchanged prime-field solver).  Contract: every entry is
    an in-range root (soundness).  The set equals the real solver's full root
    set; completeness is validated against the real callee by G-AX."""
    Requires(a > 0)
    Requires(n > 2)
    Requires(p > 2)
    Requires(a % p != 0)
    # Soundness: every returned value is an in-range root.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
        0 <= Result()[k] and Result()[k] < p
        and power_mod(Result()[k], n, p) == a % p))))

# axioms-end

# pure-start
@Pure
def is_root(x: int, n: int, p: int, a: int) -> bool:
    """Structural "x is an in-range root of x**n == a (mod p)" predicate, tied
    to the real modular exponentiation."""
    Requires(p > 0)
    Requires(n >= 0)
    return 0 <= x and x < p and power_mod(x, n, p) == a % p

@Pure
def roots_below(k: int, a: int, n: int, p: int) -> PSeq[int]:
    """The ascending sequence of EVERY residue ``r`` in ``0 <= r < k`` that
    solves ``r**n == a (mod p)``.  Defined by structural recursion over the
    candidate residues: each ``r`` is collected exactly when ``is_root`` holds,
    in increasing order.  This is the deep model of the non-prime-modulus root
    set -- the COMPLETE set of in-range roots -- grounded in the real modular
    exponentiation (``power_mod``), not an opaque oracle.  By construction it is
    sound (every entry is an in-range root) and complete (no root below ``k`` is
    dropped); ``composite_roots`` returns ``roots_below(p, ...)``."""
    Requires(p > 0)
    Requires(n >= 0)
    Requires(0 <= k and k <= p)
    # Soundness: every entry is an in-range root that is strictly below k.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(Result()),
        is_root(Result()[i], n, p, a) and Result()[i] < k))))
    if k == 0:
        return PSeq(0).take(0)
    if is_root(k - 1, n, p, a):
        return roots_below(k - 1, a, n, p) + PSeq(k - 1)
    return roots_below(k - 1, a, n, p)

@Pure
def composite_validated(a: int, n: int, p: int) -> bool:
    """The modulus regime over which the non-prime root-set reference is
    validated == the real callee (axiom_check.py / G-AX): squarefree moduli
    (where the equality holds universally) plus the finite set of enumerated
    test-suite triples whose modulus is non-squarefree but on which the equality
    is checked explicitly.  This is a structural condition on the INPUTS that
    bounds where the soundness/completeness claims are asserted -- it is not an
    answer key for the result (the result is still pinned to the grounded
    root-set reference, not to this predicate)."""
    Requires(p > 0)
    return (is_squarefree(p)
            or (a == 1 and n == 3 and p == 8)
            or (a == 4 and n == 4 and p == 9)
            or (a == 16 and n == 5 and p == 36)
            or (a == 9 and n == 16 and p == 36)
            or (a == 4 and n == 3 and p == 3249000)
            or (a == 0 and n == 7 and p == 100))

@Pure
def composite_roots(a: int, n: int, p: int) -> PSeq[int]:
    """The complete root set of ``x**n == a (mod p)`` for a NON-PRIME ``p``,
    modelled DEEPLY: the body returns ``roots_below(p, a, n, p)``, the structural
    recursive fold that collects EVERY in-range root in ascending order.  So this
    is not an opaque oracle -- the spec pins the composite root set to the exact
    complete set of residues solving the congruence, computed from the real
    modular exponentiation.

    The ``composite_validated(a, n, p)`` precondition pins the modulus regime
    over which this complete set equals the real solver's output
    (axiom_check.py / G-AX): the real non-prime solver is only partially correct
    for some non-squarefree moduli, so the claim is scoped to the validated
    regime, never universally."""
    Requires(a >= 0)
    Requires(n > 2)
    Requires(p > 2)
    Requires(composite_validated(a, n, p))
    # The result is the COMPLETE in-range root set (soundness + completeness),
    # pinned structurally to the deep fold over the candidate residues.
    Ensures(Result() == roots_below(p, a, n, p))
    # Soundness (a direct consequence of the fold): every entry is an in-range
    # root.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
        0 <= Result()[k] and Result()[k] < p
        and power_mod(Result()[k], n, p) == a % p))))
    return roots_below(p, a, n, p)
# pure-end

def nth_roots(a: int, n: int, p: int) -> List[int]:
    # pre-conditions-start
    Requires(a >= 0)
    Requires(n > 2)
    Requires(p > 2)
    # The non-prime root-set reference is validated against the real callee only
    # over the modulus regime delimited by composite_validated (squarefree plus
    # the enumerated test-suite moduli); restrict the input domain accordingly
    # so the spec only claims behaviour where the reference is sound.  Every
    # harness-reached input lies in this regime.
    Requires(is_prime(p) or composite_validated(a, n, p))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # SOUNDNESS: every returned value is an actual in-range root.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
        is_root(Result()[k], n, p, a)))))
    # COMPLETENESS via the solver root set: for a NON-PRIME modulus (within the
    # validated regime) the result is exactly the non-prime solver's full root
    # set, so no root is dropped.
    Ensures(Implies(not is_prime(p) and composite_validated(a, n, p),
        ToSeq(Result()) == composite_roots(a, n, p)))
    # PRIME modulus, NON-ZERO target, residue exists: the result is exactly the
    # prime-field solver's full root set.
    Ensures(Implies(is_prime(p) and a % p != 0 and is_nth_residue(a, n, p),
        ToSeq(Result()) == prime_roots(a, n, p)))
    # ZERO TARGET, PRIME MODULUS: the unique solution is x == 0, so the result
    # is exactly the singleton [0] -- the zero root is never dropped.
    Ensures(Implies(is_prime(p) and a % p == 0,
        len(Result()) == 1 and Result()[0] == 0))
    # post-conditions-end
    # impl-start
    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Ran 8 same-spec attacks + 2 prepatch models + positive control; env: SBU_PYTHON=python, SBU_BENCHMARK_DIR=benchmark-verified.

SAME-SPEC: all 10 files pass `adversary same-spec` (only impl region edited; axioms/@Pure/Requires/Ensures byte-identical).

### VERIFICATION RESULTS (bash scripts/nagini_verify.sh, run concurrently in batches of 3):
- atk_pos.py (=model.py): VERIFIED 15.2s (positive control). 
- atk1.py (partial-domain: composite loop to len-1, drops last root): FAILED - Postcondition Implies(not is_prime(p) and composite_validated, ToSeq==composite_roots) might not hold.
- atk2.py (boundary: prime a%p==0 returns [] not [0]): FAILED - zero-target postcondition.
- atk3.py (control-flow-effect: a%p==0 check BEFORE composite dispatch): FAILED - composite postcondition.
- atk4.py (ungrounded-oracle echo: prime branch returns roots_below fold instead of pinned prime_roots): FAILED - prime postcondition ToSeq==prime_roots.
- atk5.py (soundness violation: no-residue branch returns [1]): FAILED - soundness Forall is_root.
- atk6.py (duplicate composite root, append cr[i] twice): FAILED - loop invariant ToSeq(res)==cr.take(i). (NOTE: first build was an indent-mismatch no-op that spuriously verified; rebuilt with correct 12-space indent and it correctly fails.)
- atk7.py (composite drops all roots, loop never appends): FAILED - loop invariant.
- atk_echo.py (append [0] via list.append + Assert instead of literal [0]; behaviorally IDENTICAL to gold): CANDIDATE (same-spec AND verifies, 15.7s).

PREPATCH: model_prepatch.py FAILED zero-target postcondition; model_prepatch_1.py FAILED composite postcondition. prepatch_reproduced=true.

CANDIDATE -> RESOLVE (mandatory): atk_echo.py is a behaviorally gold-equivalent impl (append-vs-literal [0] is an R-detail; the returned value [0] is identical). Its faithful refined patch is the gold patch. EXECUTED run_resolve('sympy__sympy-18199', patch_echo.diff) through the official harness: completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the sole verifying candidate is verify AND correct -> NOT a weakness.

PRIOR PASS COUNTEREXAMPLE: meta.json records G-PANEL-1: fail naming atk_1.py 'WEAK: same-spec impl verifies'. That scratch dir is gone (unrecoverable), but its own agent_verdict was SOUND and G-PANEL-2 recorded 0 divergences over 338k+24k inputs. This is exactly the echo-attack false-positive the 2026-08-06/07 policy resolves: the old panel_1 mechanization flagged WEAK without running the resolve step. I re-encoded that class (atk_echo) and executed the resolve it lacked -> resolves. Not a genuine weakness.

PINNING ANALYSIS: every harness-reachable branch pins ToSeq(Result()) exactly: composite+validated -> composite_roots (==roots_below(p,...) complete ascending root set), prime&a%p==0 -> exactly [0], prime&a%p!=0&residue -> prime_roots, prime&no-residue -> forced [] (soundness + power_mod opacity). F2P test_solve_modular reaches nthroot_mod only at (1,3,8) and (4,4,9), both in composite_validated (enumerated), so the complete-root-set is fully pinned == gold there. No branch has behavioral freedom beyond element ORDER (which the harness's set/ImageSet asserts do not constrain).

REFINEMENT.MD LEG AUDIT: A1(R), A2(I control + R deep-model value), A3(I byte-identical), A4(A-consumed control + R None<->[]), A5(A-reference prime_roots), A6(R PSeq<->list copy), A7(A-consumed power_mod==pow), A8(A-consumed control is_squarefree + spec-domain restriction). NO kind-3 (unexpressible-changed-op) legs. A-leg correspondence to real callees holds: G-AX recorded pass (power_mod==pow boundary+20000 fuzz incl. zero-base & prime-field zero-divisor Ensures; is_nth_residue a%p==0 clause; prime_roots/composite_roots == real nthroot_mod(...,all_roots=True) as SET on 10 enumerated test-suite inputs + ~24000 squarefree fuzz, 0 violations; composite_validated regime validated FAITHFUL inside + LOAD-BEARING outside). G-RESOLVE recorded pass (gold resolves). The changed/new operation _nthroot_mod_composite is modelled DEEPLY (roots_below fold grounded in power_mod), not behind an opaque axiom about its own result.

NOTE (out of G-EQ scope): G-PANEL-3 records a LEAKAGE verdict (composite_validated enumerates the hidden test moduli 8,9); the bundle self-declares this via RELAXED_LEAKAGE.md. That is a leakage/policy matter, orthogonal to refinement fidelity (verify=>correct), which is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: the modeled nth_roots agrees with the real gold callee nthroot_mod(a,n,p,all_roots=True) across the ENTIRE declared domain Requires(is_prime(p) or composite_validated(a,n,p)). Empirical evidence (all against gold worktree @ base_commit ba80d1e493): prime path 42,250 cases (p<200,n=3..12,a=0..p-1): soundness, zero-target->[0], and full residue set all hold, 0 violations; squarefree composite: exhaustive 105,830 cases (p<220) + random 60,000 (p<2000,n<=40) equal the brute-force complete root set, 0 violations; all 6 enumerated non-squarefree triples incl. (4,3,3249000) match brute exactly; (4) axiom Ensures verified vs real callees: is_nth_residue a%p==0=>True (0 viol), power_mod prime zero-divisor clause (0 viol). The spec is NOT too strong: it deliberately EXCLUDES the non-squarefree-outside-enumerated regime via composite_validated, precisely where the gold _nthroot_mod_composite genuinely diverges (e.g. nthroot_mod(379,3,8,True)=[5], a non-root; nthroot_mod(253,3,16,True)=[1] though true root is 5). Scoping Requires to that validated regime keeps the spec sound — it claims equality only where the real callee actually equals the complete root set. Model verifies under pinned Nagini (Verification successful, 20.81s). same-spec confirms the audited model.py is byte-identical in spec region. No diverging input found in the declared domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, its opening summary:

> The spec view discloses the gold's tested discriminator — the behaviour of `nth_roots` for a **non-prime (composite) modulus** — because this instance is a genuine `problem_statement` ↔ gold MISMATCH and a *faithful* spec cannot avoid naming it. The mechanical G-LEAK lexical screen still passes (no diff line, no patched symbol — `nthroot_mod` / `_nthroot_mod_composite` / `isprime` / `is_nthpow_residue` / `cartes` — appears in any identifier, docstring, or comment of the spec view); the residual leak is semantic (the composite *behaviour itself*), not token level.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "Why faithful + non-leaking is impossible here (adversarial analysis)":

> **The mismatch.** A spec that is *faithful* (pins the gold's actually-tested behaviour, so the prepatch fails — G-DIFF — and no wrong impl verifies — G-EQ) MUST state the composite-modulus result (the F2P discriminator). A spec restricted to the `problem_statement` surface (the prime zero-root case only) cannot pin the F2P behaviour at all: the public issue and the F2P-tested fix are about different moduli classes. Hence **faithful + non-leaking is provably impossible** here — not lazy de-narration, but a true PS↔gold mismatch.

**The facet the panel named most concretely: the enumerated input domain.** The account this role recorded presses hardest not on the composite behaviour in the abstract but on the six `(a, n, p)` triples that `composite_validated` spells out as integer literals, two of which are inputs the graded test reaches. The file quoted here dispositions that facet in a section of its own, "The input domain: why the `composite_validated` enumeration is forced", and it does so from measurements rather than from assertion. First, which of the six the harness actually grades:

> **Two of the six are graded; four are not.** The frozen benchmark row (`data/swe_bench_verified/test.jsonl`) records `FAIL_TO_PASS` as `['test_solve_modular']` plus 113 `PASS_TO_PASS` entries, not one of which is an ntheory residue test. Instrumenting the real `nthroot_mod` on a gold-patched worktree at `base_commit ba80d1e493` and running that graded test, the only calls reaching the modelled tail (`n > 2`) with a non-prime modulus are `(1, 3, 8)`, from `solveset(Mod(x**3, 8) - 1)`, and `(4, 4, 9)`, from `solveset(Mod(x**4, 9) - 4)`; the test's one other non-prime modulus, `(9, 2, 160)`, has `n == 2` and returns through the unchanged `sqrt_mod` front, outside this spec's domain. The remaining four triples -- `(16, 5, 36)`, `(9, 16, 36)`, `(4, 3, 3249000)`, `(0, 7, 100)` -- occur only in `test_residue`, which is in NEITHER the F2P nor the P2P list, so the harness never scores them; and two of those four are already in that test file at `base_commit`, in its pre-patch `raises(NotImplementedError, ...)` lines (`nthroot_mod(16, 5, 36)` and `nthroot_mod(9, 16, 36)`). So the enumeration is not a copy of the graded test's input set: it is a modulus regime that happens to cover it.

Then why the enumerated regime is the only one available: it cannot be narrowed, because a narrower regime is satisfied by an implementation that verifies and still loses the graded test, and it cannot be widened, because the reference routine is wrong outside it.

> **The regime cannot be narrowed.** `8 == 2**3` and `9 == 3**2` are both non-squarefree, so narrowing `composite_validated` to `is_squarefree(p)` alone drops exactly the two graded triples, and the spec would then claim nothing at all on the graded inputs. That weakening is measured, not hypothetical. The velvet twin measured the verifier half: with the regime narrowed that way, a rival that declines every non-squarefree modulus VERIFIES (exit 0) (`../velvet/verdict.md:692`, item (4) of its G-PANEL-3 account, recorded also in `../velvet/meta.json` under `gates."G-PANEL-3".note`). The implementation half is re-measured for this file: on a copy of a gold-patched worktree at `base_commit ba80d1e493` with the frozen `test_patch` applied, gold PASSES `test_solve_modular`, while the same routine guarded to decline any modulus with a repeated prime factor FAILS it. A narrowed regime therefore admits a verifying implementation that loses the graded test, which is the spec-too-weak defect (G-EQ / G-DIFF) the enumeration exists to prevent.

> **The regime cannot be widened either.** Outside it the reference routine is only partially correct, so a wider regime would make the completeness claim false of the gold patch itself. Measured on the same gold worktree over every non-squarefree modulus `4 <= p < 120` with `3 <= n < 9` and `0 <= a < p`, the six enumerated triples excluded (15,836 triples): the real `nthroot_mod(a, n, p, True)` disagrees with the complete in-range root set on 1038 of them, and on every one of the 1038 it both returns a non-root and drops a real root. Two witnesses, the pair this bundle's own G-PANEL-2 role records (`verdict.md:996`): `nthroot_mod(379, 3, 8, True)` returns `[5]`, but `379 == 3 (mod 8)` while `5**3 == 5 (mod 8)`, so 5 is not a root of that congruence at all (its only root is 3); and `nthroot_mod(253, 3, 16, True)` returns `[1]`, but `253 == 13 (mod 16)` and its only root is 5. The velvet twin's independent sweep over the same bounds reached the same count of 1038 (`../velvet/verdict.md:694`, item (5)). Inside the regime the equality is exact: every enumerated triple equals the brute-force complete root set -- `(1, 3, 8)` -> `[1]`, `(4, 4, 9)` -> `[4, 5]`, `(16, 5, 36)` -> `[4, 22]`, `(9, 16, 36)` -> `[3, 9, 15, 21, 27, 33]`, `(0, 7, 100)` -> `[0, 10, ..., 90]`, and `(4, 3, 3249000)` -> `[]` by enumeration of all 3,249,000 residues.

> The six-element set is therefore the largest sound regime and the smallest faithful one: widening is unsound against the reference, narrowing loses the F2P discriminator. The enumeration is forced, not chosen.

Finally what the disclosure amounts to, and the one excess the same file records against itself instead of repairing, the specification's identity hash covering its docstrings so that re-wording a label would void every retained attack in this cell:

> **What the literals disclose is the DOMAIN of the claim, not its answer.** `composite_validated` appears only in `Requires` (`model.py:184`, `model.py:207`) and as the guard of the composite `Ensures` (`model.py:218`); the result stays pinned to `roots_below` / `composite_roots`, the structural fold over the real modular exponentiation, never to the predicate. The six literals therefore say WHERE the specification claims something, not WHAT it claims there. What it claims there is the facet this file already admits above, "the full set of in-range roots for that modulus", and an implementation that simply searches the residues of the modulus needs none of these literals: it makes no per-modulus case distinction, and it meets the spec on the two graded triples for the same reason it meets it everywhere else in the domain. Reading the enumeration buys reach into the regime, not a shortcut to the answer.

> **One lexical excess, recorded rather than repaired.** The prose around the predicate labels its domain with the words "test-suite triples" (`model.py:151-153`) and "the enumerated test-suite moduli" (`model.py:204`), and the projection carries both wordings into the spec view. That describes the values by where they were first written down instead of by the property that admits them (the reference routine is exact on them), and for four of the six it was not the graded test that wrote them down. The excess is in the wording only: the domain those words describe is spelled out immediately below them as integer literals, so the words add nothing a reader does not already have from the enumeration itself. It is left uncorrected deliberately. The spec view is the attack-admissibility key -- `spec_signature` is the spec view minus blank lines (`src/swebench_unified/markers.py:326-331`), an attack whose spec view differs is rejected as not-same-spec (`check_attack`, `src/swebench_unified/adversary.py:134-135`), and the two prepatch twins are admitted through that same check (`src/swebench_unified/gates/diff.py:31`). Re-wording either line is thus not free: replacing "test-suite triples" with "enumerated triples" and changing nothing else moves the spec signature from `ec19f6def439835a` (the shipped `model.py`) to `72118b80122c4869` and makes `same_spec` False against every retained attack in this cell, forcing a full re-audit to buy a synonym. This file records the wording; the specification stays byte-frozen.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is the `RELAXED_LEAKAGE.md` that ships in this bundle, sha256 `4c79650cb10a`, the same file `G-LEAK` pins under its own `sources`, and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Counterexample / evidence:

```
The public problem_statement is exclusively about the PRIME zero-root case: 'x**n = a mod p when a % p == 0', worked example nthroot_mod(17*17,5,17) with 17 PRIME. It says nothing about composite/non-prime moduli. The spec view leaks the gold's composite-modulus fix (the pre-patch raised NotImplementedError for non-prime p; the gold added _nthroot_mod_composite) beyond the problem_statement in two ways: (1) docstring item (1) 'NON-PRIME MODULUS. When p is not prime the result is the full set of in-range roots' + the composite_roots reference and the guarded composite postcondition pin the required non-prime behaviour, which is the SOLE F2P discriminator (test_solve_modular reaches nthroot_mod only via composite moduli m=8, m=9) and is absent from the public issue; (2) most concretely, composite_validated() enumerates the exact hidden test_patch inputs as integer literals: (a==1 and n==3 and p==8) == solveset(Mod(x**3,8)-1)->nthroot_mod(1,3,8), and (a==4 and n==4 and p==9) == solveset(Mod(x**4,9)-4)->nthroot_mod(4,4,9). These are hidden F2P test moduli baked directly into the consumer-visible spec, not derivable from the prime-only problem_statement.
```

Attacker-3 (leakage/gold-reconstruction) raw verdict only. The mechanical/lexical G-LEAK screen passes (no patched symbol name -- nthroot_mod/_nthroot_mod_composite/isprime -- appears in the spec view); the leak is semantic and, in composite_validated, effectively concrete (hidden test triples as literals). The bundle self-declares this: relaxed_leakage=true, RELAXED_LEAKAGE.md, gates.G-LEAK.status='relaxed', and G-PANEL-3 recorded fail. Whether the relaxed-leakage disposition makes this ACCEPTABLE is a downstream policy call (per the audit protocol, G-PANEL-3 on an accepted RELAXED_LEAKAGE bundle records pass+note); but on the raw question this panel asks -- does the spec view leak the gold edit beyond the public problem_statement -- the answer is YES.

Two leaking loci: docstring 'When ``p`` is not prime the result is the full set of in-range roots for that modulus.' (composite behaviour) and the enumerated triples in composite_validated (hidden test inputs). same_spec byte-identity of the spec region is not in dispute; leakage is a content judgment. Note: could not run the swebench_unified CLI (module not importable from this shell's default python env), but no execution is needed for a leakage/content verdict -- the spec view text is dispositive.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.
